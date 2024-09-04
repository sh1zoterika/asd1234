import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit, QDialog
)
from psycopg2 import OperationalError, sql
from Database import Database
from BaseWindow import BaseWindow
from ProductEditDialog import ProductEditDialog


class ReceivingWindow(BaseWindow):
    def __init__(self, user, password):
        self.user = user
        self.password = password
        try:
            with Database(self.user, self.password) as db:
                self.combo_box = QComboBox()  # Initialize combo_box here
                column_names = db.get_column_names('products')
                super().__init__('Приёмка товаров', column_names, self.user, self.password, 'products')
                self.changes = []  # Для отслеживания изменений

                self.load_warehouses()
                self.combo_box.currentIndexChanged.connect(self.update_table)

                # Создаем отдельный layout для combo_box и таблицы
                combo_table_layout = QVBoxLayout()
                combo_table_layout.addWidget(self.combo_box)
                combo_table_layout.addWidget(self.table_widget)

                # Добавляем combo_table_layout в основной layout
                main_layout = self.centralWidget().layout()
                main_layout.insertLayout(0, combo_table_layout)  # Добавляем combo_table_layout в основной layout

                self.add_button = QPushButton('Добавить')
                self.add_button.clicked.connect(self.add_item)
                main_layout.addWidget(self.add_button)

                self.update_table()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при инициализации окна: {e}")

    def load_warehouses(self):
        try:
            with Database(self.user, self.password) as db:
                warehouses = db.get_warehouses()
                for warehouse in warehouses:
                    self.combo_box.addItem(warehouse[1], warehouse[0])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке складов: {e}")

    def update_table(self):
        try:
            with Database(self.user, self.password) as db:
                warehouse_id = self.combo_box.currentData()
                if warehouse_id is not None:
                    products = db.get_products_by_warehouse(warehouse_id)
                    self.table_widget.setRowCount(len(products))
                    self.table_widget.setColumnCount(len(self.table_headers))
                    self.table_widget.setHorizontalHeaderLabels(self.table_headers)
                    for i, product in enumerate(products):
                        for j, value in enumerate(product):
                            self.table_widget.setItem(i, j, QTableWidgetItem(str(value)))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении таблицы: {e}")

    def add_item(self):
        dialog = ProductEditDialog(self.table_widget)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            row_position = self.table_widget.rowCount()
            self.table_widget.insertRow(row_position)
            for col, value in enumerate(data):
                self.table_widget.setItem(row_position, col, QTableWidgetItem(value))  # Обновляем данные в таблице
            self.changes.append(('insert', None, data))
            QMessageBox.information(self, 'Успех', 'Товар успешно добавлен!')

    def delete_item(self):
        selected_row = self.table_widget.currentRow()
        if selected_row >= 0:
            id_item = self.table_widget.item(selected_row, 0)
            if id_item:
                self.changes.append(('delete', id_item.text(), None))
            self.table_widget.removeRow(selected_row)
            QMessageBox.information(self, 'Успех', 'Товар успешно удалён!')

    def cancel_changes(self):
        self.update_table()
        self.changes.clear()
        QMessageBox.information(self, 'Успех', 'Изменения успешно откатаны')

    def save_changes(self):
        try:
            with Database(self.user, self.password) as db:
                for change in self.changes:
                    change_type, row_id, row_data = change
                    if change_type == 'insert':
                        new_id = db.get_next_id('products')
                        db.cursor.execute(self.get_insert_query(), (new_id, *row_data))
                    elif change_type == 'delete':
                        db.cursor.execute(self.get_delete_query(), (row_id,))
                    elif change_type == 'update':
                        db.cursor.execute(self.get_update_query(), row_data + [row_id])
                
                db.conn.commit()
                self.changes.clear()
                QMessageBox.information(self, 'Успех', 'Изменения успешно сохранены!')
        except Exception as e:
            logging.error(f"Error saving changes: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка при сохранении: {e}')
        finally:
            if db.conn:
                db.conn.close()
                logging.debug("Database connection closed.")

    def get_insert_query(self):
        return """
            INSERT INTO Products (id, name, article, lifetime, description, category, png_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

    def get_delete_query(self):
        return "DELETE FROM Products WHERE id = %s"

    def get_update_query(self):
        return """
            UPDATE Products SET name = %s, article = %s, lifetime = %s, description = %s, category = %s, png_url = %s
            WHERE id = %s
        """

    def get_insert_query(self):
        return "INSERT INTO ProductInWarehouse (warehouse_id, product_name, amount, price) VALUES (%s, %s, %s, %s)"

    def get_delete_query(self):
        return "DELETE FROM ProductInWarehouse WHERE warehouse_id = %s AND product_name = %s"

    def get_update_query(self):
        return "UPDATE ProductInWarehouse SET amount = %s, price = %s WHERE warehouse_id = %s AND product_name = %s"