import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit
)
from PyQt5 import QtCore
from psycopg2 import OperationalError, sql
from Database import Database
from BaseProductWindow import BaseProductWindow


class AddProductWindow(BaseProductWindow):
    def __init__(self, order_id, user, password, parent=None):
        self.user = user
        self.password = password
        query = {
            'select': """SELECT products.name, products.id, amount, products.price FROM ProductInWarehouse
            JOIN Products ON Products.id = ProductInWarehouse.product_id
            WHERE warehouse_id = %s""",
            'insert': """INSERT INTO Order_items (order_id, product_id, amount, price) VALUES (%s, %s, %s, %s)"""
        }
        headers = ['Товар', 'ID Товара', 'Количество', 'Цена', 'Количество в заказ']
        super().__init__('Добавить товары в заказ', (600, 200, 1000, 600), headers, query, self.user, self.password, parent)
        self.order_id = order_id

        # Кнопка добавления товара в заказ
        self.add_button = QPushButton('Добавить')
        self.add_button.clicked.connect(self.add_products_to_order)
        layout = self.centralWidget().layout()
        layout.addWidget(self.add_button)

        # Делая ячейки таблицы доступными только для чтения
        self.make_table_read_only()

    def make_table_read_only(self):
        for row in range(self.warehouse_table.rowCount()):
            for col in range(self.warehouse_table.columnCount()):
                item = self.warehouse_table.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        for row in range(self.order_table.rowCount()):
            for col in range(self.order_table.columnCount()):
                item = self.order_table.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)

    def add_products_to_order(self):
        self.warehouse_id = self.combo_box.currentData()
        if self.warehouse_id:
            try:
                with Database(self.user, self.password) as db:
                    for i in range(self.warehouse_table.rowCount()):
                        product_id = self.warehouse_table.item(i, 1).text()
                        quantity = int(self.order_table.item(i, 0).text())
                        price = float(self.warehouse_table.item(i, 3).text())
                        amount = int(self.warehouse_table.item(i, 2).text())
                        if quantity > 0:
                            if amount >= quantity:
                                db.cursor.execute(
                                    'UPDATE ProductInWarehouse SET amount = amount - %s WHERE product_id = %s AND warehouse_id = %s',
                                    (quantity, product_id, self.warehouse_id))
                                db.cursor.execute(self.query['insert'], (self.order_id, product_id, quantity, price))
                            else:
                                QMessageBox.warning(self, 'Ошибка', 'На складе недостаточно товара')

                    db.conn.commit()
                QMessageBox.information(self, 'Успех', 'Товары добавлены в заказ.')
            except Exception as e:
                if db.conn:
                    db.conn.rollback()
                print(f"Error adding products to order: {e}")
                QMessageBox.critical(self, 'Ошибка', f'Ошибка добавления товаров в заказ: {e}')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, выберите склад.')
