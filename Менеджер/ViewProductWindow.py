import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit,
)
from PyQt5 import QtCore, QtGui, QtWidgets
from psycopg2 import OperationalError, sql
from Database import Database

class ViewProductWindow(QMainWindow):
    def __init__(self, user, password, warehouseid):
        super().__init__()
        self.user = user
        self.password = password
        self.warehouseid = warehouseid

        layout = QVBoxLayout()

        self.setWindowTitle("Товары на складе")
        self.setGeometry(600, 200, 800, 600)

        self.tableWidget = QTableWidget()
        layout.addWidget(self.tableWidget)

        self.db = Database(user, password)
        self.load_products()

    def load_products(self):
        self.table_data = self.db.get_product_in_warehouse(self.warehouseid)
        if self.table_data:
            self.tableWidget.setRowCount(len(self.table_data))
            self.tableWidget.setColumnCount(len(self.columns))
            self.tableWidget.setHorizontalHeaderLabels(self.columns)

            for i in range(len(self.table_data)):
                for j in range(len(self.table_data[i])):
                    item = QtWidgets.QTableWidgetItem(str(self.table_data[i][j]))
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                    self.tableWidget.setItem(i, j, item)
