import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit
)
from psycopg2 import OperationalError, sql
from SalesWindow import SalesWindow
from ProductWindow import ProductWindow
from TransferWindow import TransferWindow
from WriteOffProductWindow import WriteOffProductWindow
from ClientWindow import ClientWindow
from WarehouseWindow import WarehouseWindow
from ReceivingWindow import ReceivingWindow
import os
import subprocess


class MainWindow(QMainWindow):
    def __init__(self, user, password):
        super().__init__()
        self.setWindowTitle("Warehouse Database")
        self.setGeometry(600, 200, 600, 400)
        self.user = user
        self.password = password
        layout = QVBoxLayout()

        self.buttons = {}
        buttons = [
            ('Продажа товаров', self.open_sales_window),
            ('Товары', self.open_product_window),
            ('Приёмка товаров', self.open_receiving_window),
            ('Перемещение товаров', self.open_transfer_window),
            ('Списание товаров', self.open_write_off_window),
            ('Клиенты', self.open_clients_window),
            ('Склады', self.open_warehouses_window),
            ('Документы', self.open_documents_window),
            ('Шаблоны', self.open_templates_window)
        ]

        for btn_text, handler in buttons:
            button = QPushButton(btn_text)
            button.clicked.connect(handler)
            layout.addWidget(button)
            self.buttons[btn_text] = button

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def open_sales_window(self):
        self.sales_window = SalesWindow(self.user, self.password)
        self.sales_window.show()

    def open_product_window(self):
        self.productwindow = ProductWindow(self.user, self.password)
        self.productwindow.show()

    def open_receiving_window(self):
        self.receivingwindow = ReceivingWindow(self.user, self.password)
        self.receivingwindow.show()

    def open_transfer_window(self):
        self.transfer_window = TransferWindow(self.user, self.password)
        self.transfer_window.show()

    def open_write_off_window(self):
        self.write_off_window = WriteOffProductWindow(self.user, self.password)
        self.write_off_window.show()

    def open_clients_window(self):
        try:
            self.client_window = ClientWindow(self.user, self.password)
            self.client_window.show()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка открытия окна с клиентами: {e}')

    def open_warehouses_window(self):
        #try:
        self.warehouse_window = WarehouseWindow(self.user, self.password)
        self.warehouse_window.show()
        #except Exception as e:
            #QMessageBox.critical(self, 'Ошибка', f'Ошибка открытия окна со складами: {e}')

    def open_documents_window(self):
        project_root = os.path.dirname(os.path.abspath(__file__))
        folder_name = "docs"
        folder_path = os.path.join(project_root, folder_name)

        # Проверяем, существует ли папка
        if not os.path.isdir(folder_path):
            print(f"Папка '{folder_name}' не найдена в проекте.")
            return

        # Открываем папку с помощью проводника Windows
        subprocess.run(["explorer", folder_path])

    def open_templates_window(self):
        project_root = os.path.dirname(os.path.abspath(__file__))
        folder_name = "presets"
        folder_path = os.path.join(project_root, folder_name)

        # Проверяем, существует ли папка
        if not os.path.isdir(folder_path):
            print(f"Папка '{folder_name}' не найдена в проекте.")
            return

        # Открываем папку с помощью проводника Windows
        subprocess.run(["explorer", folder_path])