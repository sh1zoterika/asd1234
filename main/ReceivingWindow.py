import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QSpinBox, QLineEdit
)
from psycopg2 import OperationalError, sql
from Database import Database
from PyQt5 import QtCore
from documentcreator import DocumentCreator

class ReceivingWindow(QMainWindow):
    def __init__(self, user, password):
        self.user = user
        self.password = password
        super().__init__()
        self.setWindowTitle('Приёмка товаров')
        self.setGeometry(600, 200, 800, 600)

        self.changes = []  # For tracking changes

        layout = QVBoxLayout()

        # Search section
        search_layout = QHBoxLayout()
        self.search_label = QLabel("Поиск товара:")
        search_layout.addWidget(self.search_label)
        self.search_box = QLineEdit()
        search_layout.addWidget(self.search_box)
        self.search_button = QPushButton("Поиск")
        self.search_button.clicked.connect(self.search_products)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

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

        self.move_button = QPushButton('Принять')
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

    def load_warehouses(self):
        with Database(self.user, self.password) as db:
            warehouses = db.get_warehouses()
            return [(warehouse[1], warehouse[0]) for warehouse in warehouses]

    def update_table(self):
        warehouses = self.load_warehouses()
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
                quantity_spinbox = QSpinBox()
                quantity_spinbox.setMaximum(999999999)
                self.move_table.setCellWidget(i, 0, quantity_spinbox)
                to_warehouse_combo = QComboBox()
                to_warehouse_combo.addItem("Выберите склад", None)
                for name, id in warehouses:
                    to_warehouse_combo.addItem(name, id)
                self.move_table.setCellWidget(i, 1, to_warehouse_combo)

    def search_products(self):
        search_text = self.search_box.text().lower()
        if not search_text:
            self.update_table()
            return

        with Database(self.user, self.password) as db:
            db.cursor.execute("""
                SELECT *
                FROM Products
                WHERE LOWER(name) LIKE %s
            """, ('%' + search_text + '%',))
            products = db.cursor.fetchall()

            self.warehouse_table.setRowCount(len(products))
            self.move_table.setRowCount(len(products))
            self.warehouse_table.setColumnCount(len(products[0]) if products else 0)
            for i, product in enumerate(products):
                for j in range(len(product)):
                    self.warehouse_table.setItem(i, j, QTableWidgetItem(str(product[j])))
                quantity_spinbox = QSpinBox()
                quantity_spinbox.setMaximum(999999999)
                self.move_table.setCellWidget(i, 0, quantity_spinbox)
                to_warehouse_combo = QComboBox()
                to_warehouse_combo.addItem("Выберите склад", None)
                for name, id in self.load_warehouses():
                    to_warehouse_combo.addItem(name, id)
                self.move_table.setCellWidget(i, 1, to_warehouse_combo)

    def move_products(self):
        for i in range(self.move_table.rowCount()):
            quantity_spinbox = self.move_table.cellWidget(i, 0)
            quantity = quantity_spinbox.value()
            to_warehouse_combo = self.move_table.cellWidget(i, 1)
            to_warehouse_id = to_warehouse_combo.currentData()
            product_id = self.warehouse_table.item(i, 0).text()
            if quantity > 0 and to_warehouse_id:
                self.changes.append(('move', to_warehouse_id, product_id, quantity))
        QMessageBox.information(self, 'Успех', 'Товары подготовлены к приёмке. Нажмите "Сохранить" для подтверждения.')

    def cancel_changes(self):
        self.update_table()
        self.changes.clear()
        QMessageBox.information(self, 'Отменено', 'Изменения отменены!')

    def save_changes(self):
        try:
            with Database(self.user, self.password) as db:
                if self.changes:
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
                            db.cursor.execute('''SELECT name, article, lifetime, description, category, price 
                            FROM Products 
                            WHERE ID = %s''', (product_id))
                            res = db.cursor.fetchone()
                            data = {'{warehouse_id}': str(to_warehouse),
                                    '{name}': str(res[0]),
                                    '{art}': str(res[1]),
                                    '{lifetime}': str(res[2]),
                                    '{description}': str(res[3]),
                                    '{category}': str(res[4]),
                                    '{price}': str(res[5]),
                                    '{amount}': str(quantity)}
                            doc = DocumentCreator('receivingpreset.docx', data)
                            doc.exec_()

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