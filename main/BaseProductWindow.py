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

class BaseProductWindow(QMainWindow):
    def __init__(self, title, geometry, headers, query, parent=None, user=None, password=None):
        self.user = user
        self.password = password
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(*geometry)

        self.query = query
        self.headers = headers

        self.db = Database(self.user, self.password)

        layout = QVBoxLayout()

        # Combo_box для складов
        self.combo_box = QComboBox()
        self.load_warehouses()
        self.combo_box.currentIndexChanged.connect(self.update_warehouse_table)
        layout.addWidget(self.combo_box)

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
            warehouses = self.db.get_warehouses()
            for warehouse in warehouses:
                self.combo_box.addItem(warehouse[1], warehouse[0])
        except Exception as e:
            print(f"Error loading warehouses: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки складов: {e}")

    def update_warehouse_table(self):
        warehouse_id = self.combo_box.currentData()
        if warehouse_id is not None:
            try:
                with self.db as db:
                    db.cursor.execute(self.query['select'], (warehouse_id,))
                    products = db.cursor.fetchall()

                self.warehouse_table.setRowCount(len(products))
                self.order_table.setRowCount(len(products))

                for i, product in enumerate(products):
                    for j, value in enumerate(product):
                        self.warehouse_table.setItem(i, j, QTableWidgetItem(str(value)))
                    self.order_table.setItem(i, 0, QTableWidgetItem('0'))
            except Exception as e:
                print(f"Error updating warehouse table: {e}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка обновления таблицы склада: {e}")

    #def closeEvent(self, event):      ************
        #print(f"Closing {self.windowTitle()}...")
        #try:
        #    self.db.close()
        #except Exception as e:
            #print(f"Error closing database connection: {e}")
        #event.accept()
