import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit, QDialog
)
from PyQt5 import QtCore, QtGui, QtWidgets
from psycopg2 import OperationalError, sql
from Database import Database


class ViewProductWindow(QDialog):
    def __init__(self, user, password, warehouseid):
        super().__init__()
        self.user = user
        self.password = password
        self.warehouseid = warehouseid

        # Создаем центральный виджет и устанавливаем его в качестве центрального виджета окна
        central_widget = QWidget()
        layout = QVBoxLayout()
        self.table_widget = QTableWidget()
        layout.addWidget(self.table_widget)
        central_widget.setLayout(layout)
        self.setLayout(layout)  # Устанавливаем layout в качестве основного для QDialog

        self.setWindowTitle("Товары на складе")
        self.setGeometry(400, 200, 600, 600)

        # Получаем имена колонок из базы данных и устанавливаем их в QTableWidget
        try:
            with Database(self.user, self.password) as db:
                column_names = db.get_column_names('productinwarehouse')
            self.table_widget.setColumnCount(len(column_names))
            self.table_widget.setHorizontalHeaderLabels(column_names)
        except Exception as e:
            print(f'Ошибка получения имен колонок: {e}')

        # Загружаем данные товаров в таблицу
        self.load_products()

    def load_products(self):
        try:
            with Database(self.user, self.password) as db:
                self.table_data = db.get_product_in_warehouse(self.warehouseid)
                if self.table_data:
                    self.table_widget.setRowCount(len(self.table_data))

                    for i in range(len(self.table_data)):
                        for j in range(len(self.table_data[i])):
                            item = QtWidgets.QTableWidgetItem(str(self.table_data[i][j]))
                            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                            self.table_widget.setItem(i, j, item)
        except Exception as e:
            print(f'Ошибка загрузки данных товаров: {e}')

