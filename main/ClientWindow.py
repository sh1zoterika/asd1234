import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit
)
from psycopg2 import OperationalError, sql
from BaseWindow import BaseWindow
from Database import Database


class ClientWindow(BaseWindow):
    def __init__(self, user, password):
        self.db = Database(user, password)
        column_names = self.db.get_column_names('clients')
        super().__init__('Клиенты', column_names, user, password)

        self.view_orders_button = QPushButton('Посмотреть заказы')
        self.view_orders_button.clicked.connect(self.view_orders)
        layout = self.centralWidget().layout()
        layout.addWidget(self.view_orders_button)

    def view_orders(self):
        pass

    def get_select_query(self):
        return """
            SELECT id, name, orders, info, phonenumber, address
            FROM Clients
        """

    def get_insert_query(self):
        return """
            INSERT INTO Clients (name, orders, info, phonenumber, address)
            VALUES (%s, %s, %s, %s, %s)
        """

    def get_delete_query(self):
        return "DELETE FROM Clients WHERE id = %s"

    def get_update_query(self):
        return """
            UPDATE Clients SET name = %s, orders = %s, info = %s, phonenumber = %s, address = %s
            WHERE id = %s
        """