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

class BaseProductWindow(QMainWindow):
    def __init__(self, title, geometry, headers, query, user=None, password=None, parent=None):
        self.user = user
        self.password = password
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(*geometry)

        self.query = query
        self.headers = headers

        layout = QVBoxLayout()

        # Combo_box для складов
        self.combo_box = QComboBox()
        self.load_warehouses()
        self.combo_box.currentIndexChanged.connect(self.update_warehouse_table)
        layout.addWidget(self.combo_box)

        # Создание элементов поиска
        search_layout = QHBoxLayout()
        self.search_label = QLabel('Поиск:')
        search_layout.addWidget(self.search_label)
        self.search_box = QLineEdit()
        search_layout.addWidget(self.search_box)
        self.search_button = QPushButton('Поиск')
        self.search_button.clicked.connect(self.search_products)
        search_layout.addWidget(self.search_button)

        layout.addLayout(search_layout)  # Добавление layout поиска в основной layout

        # Горизонтальный слой для двух таблиц
        tables_layout = QHBoxLayout()

        # Table for displaying products from the selected warehouse
        self.warehouse_table = QTableWidget()
        self.warehouse_table.setColumnCount(len(headers) - 1)
        self.warehouse_table.setHorizontalHeaderLabels(headers[:-1])
        tables_layout.addWidget(self.warehouse_table)

        # Table for showing quantities to be added to the order
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(1)
        self.order_table.setHorizontalHeaderLabels([headers[-1]])
        tables_layout.addWidget(self.order_table)

        layout.addLayout(tables_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.update_warehouse_table()

    def load_warehouses(self):
        try:
            with Database(self.user, self.password) as db:
                warehouses = db.get_warehouses()
                for warehouse in warehouses:
                    self.combo_box.addItem(warehouse[1], warehouse[0])
        except Exception as e:
            print(f"Error loading warehouses: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки складов: {e}")

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
                    self.order_table.setItem(i, 0, QTableWidgetItem('0'))
                self.make_table_read_only()
            except Exception as e:
                print(f"Error updating warehouse table: {e}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка обновления таблицы склада: {e}")

    def search_products(self):
        search_text = self.search_box.text().lower()  # Получаем текст из поля поиска
        warehouse_id = self.combo_box.currentData()
        if warehouse_id:
            try:
                with Database(self.user, self.password) as db:
                    db.cursor.execute(self.get_search_query(), (f'%{search_text}%', warehouse_id))
                    products = db.cursor.fetchall()

                self.warehouse_table.setRowCount(len(products))
                self.order_table.setRowCount(len(products))

                for i, product in enumerate(products):
                    for j, value in enumerate(product):
                        self.warehouse_table.setItem(i, j, QTableWidgetItem(str(value)))
                    self.order_table.setItem(i, 0, QTableWidgetItem('0'))
                self.make_table_read_only()
            except Exception as e:
                print(f"Error searching products: {e}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка поиска продуктов: {e}")

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

    def get_search_query(self):
        # Абстрактный метод для поиска продуктов
        raise NotImplementedError