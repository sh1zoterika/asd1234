import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit, QDialog, QSpinBox
)
from psycopg2 import OperationalError, sql
from Database import Database
from BaseProductWindow import BaseProductWindow
from EditDialog import EditDialog
from documentcreator import DocumentCreator

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


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
        headers = ['Имя товара', 'ID товара', 'Количество в наличии', 'Количество списания']
        super().__init__('Списание товаров', (600, 200, 1000, 600), headers, self.query, user, password)

        self.order_table.cellDoubleClicked.connect(self.edit_item)

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

        self.write_off_data = []  # To store write-off data

        self.update_warehouse_table()

    def update_warehouse_table(self):
        warehouse_id = self.combo_box.currentData()
        if warehouse_id is not None:
            try:
                with Database(self.user, self.password) as db:
                    db.cursor.execute(self.query['select'], (warehouse_id,))
                    products = db.cursor.fetchall()

                self.warehouse_table.setRowCount(len(products))
                self.order_table.setRowCount(len(products))

                for i, product in enumerate(products):
                    for j, value in enumerate(product):
                        self.warehouse_table.setItem(i, j, QTableWidgetItem(str(value)))
                    spin_box = QSpinBox()
                    spin_box.setMaximum(999999999)  # Устанавливаем большое максимальное значение
                    self.order_table.setCellWidget(i, 0, spin_box)
                self.make_table_read_only()
            except Exception as e:
                logging.error(f"Error updating warehouse table: {e}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка обновления таблицы склада: {e}")

    def write_off_products(self):
        self.warehouse_id = self.combo_box.currentData()
        if self.warehouse_id:
            try:
                self.write_off_data.clear()  # Clear previous write-off data
                for i in range(self.warehouse_table.rowCount()):
                    product_id = self.warehouse_table.item(i, 1).text()
                    write_off_amount = self.order_table.cellWidget(i, 0).value()
                    available_amount = int(self.warehouse_table.item(i, 2).text())
                    if write_off_amount > available_amount:
                        QMessageBox.warning(self, 'Ошибка', f'Недостаточно товара на складе для списания {write_off_amount} единиц. Доступно: {available_amount} единиц.')
                    elif write_off_amount > 0:
                        self.write_off_data.append((write_off_amount, self.warehouse_id, product_id, write_off_amount))
                if self.write_off_data:
                    QMessageBox.information(self, 'Успех', 'Товары подготовлены к списанию. Нажмите "Сохранить" для подтверждения.')
            except ValueError as ve:
                logging.error(f"ValueError: {ve}")
                QMessageBox.critical(self, 'Ошибка', f'Ошибка подготовки данных для списания: {ve}')
            except Exception as e:
                logging.error(f"Error preparing write-off data: {e}")
                QMessageBox.critical(self, 'Ошибка', f'Ошибка подготовки данных для списания: {e}')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, выберите склад.')

    def cancel_changes(self):
        self.update_warehouse_table()
        self.write_off_data.clear()
        QMessageBox.information(self, 'Успех', 'Изменения успешно откатаны')

    def save_changes(self):
        try:
            with Database(self.user, self.password) as db:
                for write_off_amount, warehouse_id, product_id, _ in self.write_off_data:
                    db.cursor.execute(self.query['insert'], (write_off_amount, warehouse_id, product_id, write_off_amount))
                    db.cursor.execute('SELECT name FROM Products WHERE id = %s', (product_id,))
                    product_name = db.cursor.fetchone()
                    data = {'{warehouse_id}': str(warehouse_id),
                            '{product_id}': str(product_id),
                            '{product_name}': str(product_name[0]),
                            '{amount}': str(write_off_amount)}
                    doc = DocumentCreator('writeoffpreset.docx', data)
                    doc.exec_()
                db.conn.commit()
                self.write_off_data.clear()
                QMessageBox.information(self, 'Успех', 'Изменения успешно сохранены!')
        except OperationalError as oe:
            logging.error(f"OperationalError: {oe}")
            QMessageBox.critical(self, 'Ошибка', f'Ошибка сохранения изменений: {oe}')
        except Exception as e:
            if db.conn:
                db.conn.rollback()
            logging.error(f"Error saving changes: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Ошибка сохранения изменений: {e}')
        finally:
            if db.conn:
                db.conn.close()
                logging.debug("Database connection closed.")

    def edit_item(self, row, column):
        logging.debug(f"Opening EditDialog for row {row}, column {column}")
        dialog = EditDialog(self.order_table, row, column)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            logging.debug(f"Collected data for update: {data}")
            self.order_table.setItem(row, 0, QTableWidgetItem(data[0]))  # Обновляем данные в таблице
