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
from PyQt5 import QtCore


class ProductWindow(BaseWindow):
    def __init__(self, user, password):
        self.user = user
        self.password = password
        try:
            with Database(self.user, self.password) as db:
                self.combo_box = QComboBox()  # Initialize combo_box here
                column_names = db.get_column_names('products')
                super().__init__('Товары', column_names, self.user, self.password, 'products')
                self.changes = []  # Для отслеживания изменений

                # Добавляем элементы поиска
                self.search_label = QLabel("Поиск товара:")
                self.search_box = QLineEdit()
                self.search_button = QPushButton("Поиск")
                self.search_button.clicked.connect(self.search_products)

                # Добавляем элементы поиска в основной layout
                search_layout = QHBoxLayout()
                search_layout.addWidget(self.search_label)
                search_layout.addWidget(self.search_box)
                search_layout.addWidget(self.search_button)

                main_layout = self.centralWidget().layout()
                main_layout.addLayout(search_layout)
                main_layout.addWidget(self.table_widget)

                self.combo_box.currentIndexChanged.connect(self.update_table)

                self.update_table()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при инициализации окна: {e}")

    def update_table(self):
        try:
            with Database(self.user, self.password) as db:
                db.cursor.execute('SELECT * FROM Products')
                products = db.cursor.fetchall()
                self.table_widget.setRowCount(len(products))
                self.table_widget.setColumnCount(len(self.table_headers))
                self.table_widget.setHorizontalHeaderLabels(self.table_headers)
                for i, product in enumerate(products):
                    for j, value in enumerate(product):
                        self.table_widget.setItem(i, j, QTableWidgetItem(str(value)))
                self.make_table_read_only()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении таблицы: {e}")

    def search_products(self):
        search_text = self.search_box.text().lower()
        if not search_text:
            self.update_table()
            return

        try:
            with Database(self.user, self.password) as db:
                db.cursor.execute("""
                    SELECT *
                    FROM Products
                    WHERE LOWER(name) LIKE %s
                """, ('%' + search_text + '%',))
                products = db.cursor.fetchall()

                self.table_widget.setRowCount(len(products))
                self.table_widget.setColumnCount(len(self.table_headers))
                self.table_widget.setHorizontalHeaderLabels(self.table_headers)
                for i, product in enumerate(products):
                    for j, value in enumerate(product):
                        self.table_widget.setItem(i, j, QTableWidgetItem(str(value)))
                self.make_table_read_only()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при поиске: {e}")

    def add_item(self):
        dialog = ProductEditDialog(self.table_widget)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            row_position = self.table_widget.rowCount()
            self.table_widget.insertRow(row_position)
            for col, value in enumerate(data):
                self.table_widget.setItem(row_position, col + 1, QTableWidgetItem(value))  # Обновляем данные в таблице
            self.update_ids()
            self.changes.append(('insert', None, data))
            QMessageBox.information(self, 'Успех', 'Элемент успешно добавлен!')

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
                    logging.debug(f"Processing change: {change_type}, {row_id}, {row_data}")
                    if change_type == 'insert':
                        new_id = db.get_next_id('products')
                        logging.debug(f"Inserting new row with ID {new_id} and data: {row_data}")
                        db.cursor.execute(self.get_insert_query(), (new_id, *row_data))
                    elif change_type == 'delete':
                        logging.debug(f"Deleting row with ID {row_id}")
                        db.cursor.execute(self.get_delete_query(), (row_id,))
                    elif change_type == 'update':
                        logging.debug(f"Updating row with ID {row_id} and data: {row_data}")
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
            INSERT INTO Products (id, name, article, lifetime, description, category, png_url, price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

    def get_delete_query(self):
        return "DELETE FROM Products WHERE id = %s"

    def get_update_query(self):
        return """
            UPDATE Products SET name = %s, article = %s, lifetime = %s, description = %s, category = %s, png_url = %s, price = %s
            WHERE id = %s
        """

    def update_ids(self):
        for row in range(self.table_widget.rowCount()):
            self.table_widget.setItem(row, 0, QTableWidgetItem(str(row + 1)))

    def edit_item(self, row, column):
        logging.debug(f"Opening ProductEditDialog for row {row}, column {column}")
        dialog = ProductEditDialog(self.table_widget, row)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            logging.debug(f"Collected data for update: {data}")
            for col, value in enumerate(data):
                self.table_widget.setItem(row, col + 1, QTableWidgetItem(value))  # Обновляем данные в таблице
            self.changes.append(('update', self.table_widget.item(row, 0).text(), data))
            QMessageBox.information(self, 'Успех', 'Данные успешно обновлены!')

    def make_table_read_only(self):
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)