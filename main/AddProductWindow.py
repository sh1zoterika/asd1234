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
from BaseProductWindow import BaseProductWindow


class AddProductWindow(BaseProductWindow):
    def __init__(self, order_id, user, password, parent=None):
        self.user = user
        self.password = password
        query = {
            'select': """SELECT product_name, amount, price FROM ProductInWarehouse WHERE warehouse_id = %s""",
            'insert': """INSERT INTO Order_items (order_id, product_name, quantity, price) VALUES (%s, %s, %s, %s)"""
        }
        headers = ['Товар', 'Количество', 'Цена', 'Количество в заказ']
        super().__init__('Добавить товары в заказ', (600, 200, 1000, 600), headers, query, parent, self.user, self.password)
        self.order_id = order_id

        # Button to add products to the order
        self.add_button = QPushButton('Добавить')
        self.add_button.clicked.connect(self.add_products_to_order)
        layout = self.centralWidget().layout()
        layout.addWidget(self.add_button)

    def add_products_to_order(self):
        warehouse_id = self.combo_box.currentData()
        if warehouse_id:
            try:
                connection = self.connect_db()
                cursor = connection.cursor()
                connection.autocommit = False

                for i in range(self.warehouse_table.rowCount()):
                    product_name = self.warehouse_table.item(i, 0).text()
                    quantity = int(self.order_table.item(i, 0).text())
                    price = float(self.warehouse_table.item(i, 2).text())
                    if quantity > 0:
                        cursor.execute(self.query['insert'], (self.order_id, product_name, quantity, price))

                connection.commit()
                connection.close()
                QMessageBox.information(self, 'Успех', 'Товары добавлены в заказ.')
            except Exception as e:
                if connection:
                    connection.rollback()
                print(f"Error adding products to order: {e}")
                QMessageBox.critical(self, 'Ошибка', f'Ошибка добавления товаров в заказ: {e}')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, выберите склад.')