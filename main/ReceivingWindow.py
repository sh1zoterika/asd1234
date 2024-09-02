import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit
)
from psycopg2 import OperationalError, sql
from Database import Database
from BaseWindow import BaseWindow


class ReceivingWindow(BaseWindow):
    def __init__(self, user, password):
        self.user = user
        self.password = password
        try:
            self.db = Database(self.user, self.password)
            self.combo_box = QComboBox()  # Initialize combo_box here
            super().__init__('Приёмка товаров', ['Товар', 'Количество', 'Цена'], self.user, self.password)
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

            self.update_table()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при инициализации окна: {e}")

    def load_warehouses(self):
        try:
            warehouses = self.db.get_warehouses()
            for warehouse in warehouses:
                self.combo_box.addItem(warehouse[1], warehouse[0])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке складов: {e}")

    def update_table(self):
        try:
            warehouse_id = self.combo_box.currentData()
            if warehouse_id is not None:
                products = self.db.get_products_by_warehouse(warehouse_id)
                self.table_widget.setRowCount(len(products))
                self.table_widget.setColumnCount(len(self.table_headers))
                self.table_widget.setHorizontalHeaderLabels(self.table_headers)
                for i, product in enumerate(products):
                    self.table_widget.setItem(i, 0, QTableWidgetItem(product[0]))
                    self.table_widget.setItem(i, 1, QTableWidgetItem(str(product[1])))
                    self.table_widget.setItem(i, 2, QTableWidgetItem(str(product[2])))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении таблицы: {e}")

    def add_item(self):
        try:
            row_position = self.table_widget.rowCount()
            self.table_widget.insertRow(row_position)
            self.table_widget.setItem(row_position, 0, QTableWidgetItem('Новый товар'))
            self.table_widget.setItem(row_position, 1, QTableWidgetItem('0'))
            self.table_widget.setItem(row_position, 2, QTableWidgetItem('0'))
            self.changes.append(('insert', row_position, ['Новый товар', 0, 0]))
            QMessageBox.information(self, 'Успех', 'Товар успешно добавлен!')
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении товара: {e}")

    def delete_item(self):
        try:
            selected_row = self.table_widget.currentRow()
            if selected_row >= 0:
                self.changes.append(('delete', selected_row, None))
                self.table_widget.removeRow(selected_row)
                QMessageBox.information(self, "Успех", "Товар успешно удален!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении товара: {e}")

    def cancel_changes(self):
        try:
            self.update_table()
            self.changes.clear()
            QMessageBox.information(self, "Успех", "Изменения успешно отменены!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при отмене изменений: {e}")

    def save_changes(self):
        try:
            warehouse_id = self.combo_box.currentData()
            if warehouse_id is not None:
                connection = self.connect_db()
                cursor = connection.cursor()
                connection.autocommit = False

                for change in self.changes:
                    change_type, row_index, row_data = change
                    if change_type == 'insert':
                        product_name = row_data[0]
                        quantity = int(row_data[1])
                        price = float(row_data[2])
                        cursor.execute("""
                            INSERT INTO ProductInWarehouse (warehouse_id, product_name, amount, price)
                            VALUES (%s, %s, %s, %s)
                        """, (warehouse_id, product_name, quantity, price))
                    elif change_type == 'delete':
                        product_name = self.table_widget.item(row_index, 0).text()
                        cursor.execute("""
                            DELETE FROM ProductInWarehouse
                            WHERE warehouse_id = %s AND product_name = %s
                        """, (warehouse_id, product_name))

                connection.commit()
                connection.close()
                self.changes.clear()
                QMessageBox.information(self, "Успех", "Изменения успешно сохранены!")
        except Exception as e:
            if connection:
                connection.rollback()
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при сохранении: {e}")

    def get_select_query(self):
        return "SELECT product_name, amount, price FROM ProductInWarehouse WHERE warehouse_id = %s"

    def get_insert_query(self):
        return "INSERT INTO ProductInWarehouse (warehouse_id, product_name, amount, price) VALUES (%s, %s, %s, %s)"

    def get_delete_query(self):
        return "DELETE FROM ProductInWarehouse WHERE warehouse_id = %s AND product_name = %s"

    def get_update_query(self):
        return "UPDATE ProductInWarehouse SET amount = %s, price = %s WHERE warehouse_id = %s AND product_name = %s"