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


class WriteOffProductWindow(BaseProductWindow):
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.query = {
            'select': """SELECT Products.name, ProductInWarehouse.product_id, ProductInWarehouse.amount
        FROM ProductInWarehouse
        JOIN Products ON Products.id = ProductInWarehouse.product_id
        WHERE ProductInWarehouse.warehouse_id = %s;""",
            'insert': """UPDATE ProductInWarehouse SET amount = amount - %s 
            WHERE warehouse_id = %s AND product_id = %s AND amount >= %s"""
        }
        headers = ['Товар', 'Количество в наличии', 'Цена', 'Количество списания']
        super().__init__('Списание товаров', (600, 200, 1000, 600), headers, self.query, user, password)

        # Create and configure buttons
        self.writeoff_button = QPushButton('Списать товары')
        self.writeoff_button.clicked.connect(self.write_off_products)

        self.cancel_button = QPushButton('Отменить')
        self.cancel_button.clicked.connect(self.cancel_changes)

        self.save_button = QPushButton('Сохранить')
        self.save_button.clicked.connect(self.save_changes)

        # Add buttons to layout
        layout = self.centralWidget().layout()
        layout.addWidget(self.writeoff_button)
        layout.addWidget(self.cancel_button)
        layout.addWidget(self.save_button)

    def write_off_products(self):
        self.warehouse_id = self.combo_box.currentData()
        if self.warehouse_id:
            try:
                with Database(self.user, self.password) as db:

                    for i in range(self.warehouse_table.rowCount()):
                        product_id = self.warehouse_table.item(i, 1).text()
                        write_off_amount = int(self.order_table.item(i, 0).text())
                        if write_off_amount > 0:
                            db.cursor.execute(self.query['insert'], (write_off_amount, self.warehouse_id, product_id, write_off_amount))
                    db.conn.commit()
                    QMessageBox.information(self, 'Успех', 'Товары списаны со склада.')
            except Exception as e:
                if db.conn:
                    db.conn.rollback()
                print(f"Error writing off products: {e}")
                QMessageBox.critical(self, 'Ошибка', f'Ошибка списания товаров: {e}')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, выберите склад.')

    def cancel_changes(self):
        self.update_warehouse_table()
        QMessageBox.information(self, 'Успех', 'Изменения успешно откатаны')

    def save_changes(self):
        try:
            with Database(self.user, self.password) as db:
                for i in range(self.warehouse_table.rowCount()):
                    product_name = self.warehouse_table.item(i, 0).text()
                    write_off_amount = int(self.order_table.item(i, 0).text())
                    if write_off_amount > 0:
                        db.cursor.execute(self.query['insert'], (write_off_amount, self.warehouse_id, product_name, write_off_amount))

                db.conn.commit()
            QMessageBox.information(self, 'Успех', 'Изменения успешно сохранены!')
        except Exception as e:
            if db.conn:
                db.conn.rollback()
            print(f"Error saving changes: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Ошибка сохранения изменений: {e}')