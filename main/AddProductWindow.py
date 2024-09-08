import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit, QDialog
)
from PyQt5 import QtCore
from psycopg2 import OperationalError, sql
from Database import Database
from BaseProductWindow import BaseProductWindow
from EditDialog import EditDialog


class AddProductWindow(BaseProductWindow):
    def __init__(self, order_id, user, password, parent=None):
        self.user = user
        self.password = password
        self.order_id = order_id
        self.session_changes = {}  # Для отслеживания изменений в текущей сессии
        query = {
            'select': """SELECT products.name, products.id, amount, products.price FROM ProductInWarehouse
            JOIN Products ON Products.id = ProductInWarehouse.product_id
            WHERE warehouse_id = %s""",
            'insert': """INSERT INTO Order_items (order_id, product_id, amount, price, warehouse_id) VALUES (%s, %s, %s, %s, %s)"""
        }
        headers = ['Товар', 'ID Товара', 'Количество', 'Цена', 'Количество в заказ']
        super().__init__('Добавить товары в заказ', (600, 200, 1000, 600), headers, query, self.user, self.password, parent)

        self.order_table.cellDoubleClicked.connect(self.edit_item)

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
                                # Обновляем количество в текущей сессии
                                if product_id in self.session_changes:
                                    self.session_changes[product_id] += quantity
                                else:
                                    self.session_changes[product_id] = quantity

                                db.cursor.execute(
                                    'UPDATE ProductInWarehouse SET amount = amount - %s WHERE product_id = %s AND warehouse_id = %s',
                                    (quantity, product_id, self.warehouse_id))
                                db.cursor.execute("""SELECT * FROM Order_Items 
                                                  WHERE product_id = %s AND order_id = %s AND warehouse_id = %s""",
                                                  (product_id, self.order_id, self.warehouse_id))
                                result = db.cursor.fetchall()
                                if result:
                                    db.cursor.execute("""UPDATE Order_Items SET amount = amount + %s 
                                                                        WHERE product_id = %s AND order_id = %s AND warehouse_id = %s""",
                                                      (quantity, product_id, self.order_id, self.warehouse_id))
                                else:
                                    db.cursor.execute(self.query['insert'],
                                                      (self.order_id, product_id, quantity, price, self.warehouse_id))
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

    def edit_item(self, row, column):
        logging.debug(f"Opening EditDialog for row {row}, column {column}")
        max_value = int(self.warehouse_table.item(row, 2).text())  # Получаем максимальное количество товаров на складе
        dialog = EditDialog(self.order_table, row, column, max_value)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            logging.debug(f"Collected data: {data}")
            value = QTableWidgetItem(data[0])
            value.setFlags(value.flags() & ~QtCore.Qt.ItemIsEditable)
            self.order_table.setItem(row, 0, value)  # Обновляем данные в таблице

    def delete_item(self):
        try:
            with Database(self.user, self.password) as db:
                selected_row = self.table_widget.currentRow()
                if selected_row == -1:
                    QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, выберите элемент для удаления.')
                    return

                id_item = self.table_widget.item(selected_row, 0).text()
                order_id = self.orders_combo.currentData()
                warehouse_id = self.table_widget.item(selected_row, 4).text()
                amount = int(self.table_widget.item(selected_row, 3).text())

                # Обновляем количество в текущей сессии
                if id_item in self.session_changes:
                    self.session_changes[id_item] -= amount
                else:
                    self.session_changes[id_item] = -amount

                # Execute the delete command
                db.cursor.execute(
                    'DELETE FROM Order_Items WHERE product_id = %s AND order_id = %s AND warehouse_id = %s',
                    (id_item, order_id, warehouse_id))
                db.cursor.execute('SELECT * FROM ProductInWarehouse WHERE product_id = %s and warehouse_id = %s', (id_item, warehouse_id))
                result = db.cursor.fetchall()
                if result:
                    db.cursor.execute('UPDATE ProductInWarehouse SET amount = amount + %s WHERE product_id = %s and warehouse_id = %s',
                                      (amount, id_item, warehouse_id))
                else:
                    db.cursor.execute('INSERT INTO ProductInWarehouse (warehouse_id, product_id, amount) VALUES (%s, %s, %s)', (warehouse_id, id_item, amount))
                # Check if the delete operation was successful
                if db.cursor.rowcount > 0:
                    self.table_widget.removeRow(selected_row)
                    db.conn.commit()
                    QMessageBox.information(self, 'Успех', 'Элемент успешно удалён!')
                else:
                    QMessageBox.warning(self, 'Ошибка', 'Не удалось удалить элемент. Возможно, он не существует.')

        except Exception as e:
            # Roll back in case of error
            db.conn.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка: {e}')
