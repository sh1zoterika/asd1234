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
from PyQt5 import QtCore


class ReceivingWindow(QMainWindow):
    def __init__(self, user, password):
        self.user = user
        self.password = password
        super().__init__()
        self.setWindowTitle('Перемещение товаров')
        self.setGeometry(600, 200, 800, 600)

        self.changes = []  # For tracking changes

        layout = QVBoxLayout()

        # Layout for combo boxes
        combo_layout = QHBoxLayout()

        # No combo box for right table, only columns
        # Adding a placeholder for consistency
        self.to_warehouse_label = QLabel('Склад назначения:')
        combo_layout.addWidget(self.to_warehouse_label)

        layout.addLayout(combo_layout)

        # Layout for tables
        main_layout = QHBoxLayout()

        # Table for products in the selected warehouse
        self.warehouse_table = QTableWidget()
        with Database(self.user, self.password) as db:
            column_names = db.get_column_names('products')
            self.warehouse_table.setColumnCount(len(column_names))
            self.warehouse_table.setHorizontalHeaderLabels(column_names)
        main_layout.addWidget(self.warehouse_table)

        # Table for moving products
        self.move_table = QTableWidget()
        self.move_table.setColumnCount(2)
        self.move_table.setHorizontalHeaderLabels(['Количество', 'Склад назначения'])
        main_layout.addWidget(self.move_table)

        layout.addLayout(main_layout)

        # Buttons for operations
        button_layout = QHBoxLayout()

        self.move_button = QPushButton('Переместить')
        self.move_button.clicked.connect(self.move_products)
        button_layout.addWidget(self.move_button)

        self.cancel_button = QPushButton('Отменить')
        self.cancel_button.clicked.connect(self.cancel_changes)
        button_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton('Сохранить')
        self.save_button.clicked.connect(self.save_changes)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Initial load
        self.update_table()

    def load_warehouses(self, combo_box):
        with Database(self.user, self.password) as db:
            warehouses = db.get_warehouses()
            for warehouse in warehouses:
                combo_box.addItem(warehouse[1], warehouse[0])

    def update_table(self):
        with Database(self.user, self.password) as db:
            db.cursor.execute("""
                SELECT *
                FROM Products""")
            products = db.cursor.fetchall()
            self.warehouse_table.setRowCount(len(products))
            self.move_table.setRowCount(len(products))
            self.warehouse_table.setColumnCount(len(products[0]))
            for i, product in enumerate(products):
                for j in range(len(products[0])):
                    self.warehouse_table.setItem(i, j, QTableWidgetItem(str(product[j])))
                    self.move_table.setItem(i, 0, QTableWidgetItem('0'))
                    to_warehouse_combo = QComboBox()
                    to_warehouse_combo.addItem("Выберите склад", None)
                    self.move_table.setCellWidget(i, 1, to_warehouse_combo)
                    self.load_warehouses(to_warehouse_combo)
    def move_products(self):
        for i in range(self.move_table.rowCount()):
            quantity = int(self.move_table.item(i, 0).text())
            to_warehouse_combo = self.move_table.cellWidget(i, 1)
            to_warehouse_id = to_warehouse_combo.currentData()
            product_id = self.warehouse_table.item(i, 0).text()
            if quantity > 0 and to_warehouse_id:
                self.changes.append(('move', to_warehouse_id, product_id, quantity))
        QMessageBox.information(self, 'Успех', 'Товары подготовлены к перемещению. Нажмите "Сохранить" для подтверждения.')


    def cancel_changes(self):
        self.update_table()
        self.changes.clear()
        QMessageBox.information(self, 'Отменено', 'Изменения отменены!')

    def save_changes(self):
        try:
            with Database(self.user, self.password) as db:
                if self.changes():
                    for change in self.changes:
                        change_type, to_warehouse, product_id, quantity = change
                        if change_type == 'move':
                            db.cursor.execute("""
                                SELECT amount FROM ProductInWarehouse
                                WHERE warehouse_id = %s AND product_id = %s
                            """, (to_warehouse, product_id))
                            result = db.cursor.fetchone()
                            if result:
                                db.cursor.execute("""
                                    UPDATE ProductInWarehouse
                                    SET amount = amount + %s
                                    WHERE warehouse_id = %s AND product_id = %s
                                """, (quantity, to_warehouse, product_id))
                            else:
                                db.cursor.execute("""
                                    INSERT INTO ProductInWarehouse (warehouse_id, product_id, amount)
                                    VALUES (%s, %s, %s)
                                """, (to_warehouse, product_id, quantity))

                db.conn.commit()
                self.changes.clear()
                QMessageBox.information(self, "Успех", "Изменения успешно сохранены!")
        except Exception as e:
            if db.conn:
                db.conn.rollback()
            logging.error(f"Error saving changes: {e}")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при сохранении: {e}")

    def make_table_read_only(self):
        for row in range(self.warehouse_table.rowCount()):
            for col in range(self.warehouse_table.columnCount()):
                item = self.warehouse_table.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        for row in range(self.move_table.rowCount()):
            for col in range(self.move_table.columnCount()):
                item = self.move_table.item(row, 0)
                if item:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)