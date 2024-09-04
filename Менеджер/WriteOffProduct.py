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
        query = {
            'select': """SELECT product_name, amount, price FROM ProductInWarehouse WHERE warehouse_id = %s""",
            'insert': """UPDATE ProductInWarehouse SET amount = amount - %s WHERE warehouse_id = %s AND product_name = %s AND amount >= %s"""
        }
        headers = ['Товар', 'Количество в наличии', 'Цена', 'Количество списания']
        super().__init__('Списание товаров', (600, 200, 1000, 600), headers, query, user, password)

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
        warehouse_id = self.combo_box.currentData()
        if warehouse_id:
            try:
                connection = self.connect_db()
                cursor = connection.cursor()
                connection.autocommit = False

                for i in range(self.warehouse_table.rowCount()):
                    product_name = self.warehouse_table.item(i, 0).text()
                    write_off_amount = int(self.order_table.item(i, 0).text())
                    if write_off_amount > 0:
                        cursor.execute(self.query['insert'], (write_off_amount, warehouse_id, product_name, write_off_amount))

                connection.commit()
                connection.close()
                QMessageBox.information(self, 'Успех', 'Товары списаны со склада.')
            except Exception as e:
                if connection:
                    connection.rollback()
                print(f"Error writing off products: {e}")
                QMessageBox.critical(self, 'Ошибка', f'Ошибка списания товаров: {e}')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, выберите склад.')

    def cancel_changes(self):
        self.update_warehouse_table()
        QMessageBox.information(self, 'Успех', 'Изменения успешно откатаны')

    def save_changes(self):
        try:
            connection = self.connect_db()
            cursor = connection.cursor()
            connection.autocommit = False

            for i in range(self.warehouse_table.rowCount()):
                product_name = self.warehouse_table.item(i, 0).text()
                write_off_amount = int(self.order_table.item(i, 0).text())
                if write_off_amount > 0:
                    cursor.execute(self.query['insert'], (write_off_amount, warehouse_id, product_name, write_off_amount))

            connection.commit()
            connection.close()
            QMessageBox.information(self, 'Успех', 'Изменения успешно сохранены!')
        except Exception as e:
            if connection:
                connection.rollback()
            print(f"Error saving changes: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Ошибка сохранения изменений: {e}')