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
from BaseWindow import BaseWindow



class WarehouseWindow(BaseWindow):
    def __init__(self, user, password):
        self.db = Database(user, password)
        column_names = self.db.get_column_names('warehouses')
        super().__init__('Склады', column_names, user, password)

        self.view_products_button = QPushButton('Посмотреть товары на выбранном складе')
        self.view_products_button.clicked.connect(self.view_products)
        layout = self.centralWidget().layout()
        layout.addWidget(self.view_products_button)

    def view_products(self):
        pass

    def get_select_query(self):
        return """
            SELECT id, name, address, geo_text, geo_coordinates
            FROM Warehouses
        """

    def get_insert_query(self):
        return """
            INSERT INTO Warehouses (name, address, geo_text, geo_coordinates)
            VALUES (%s, %s, %s, %s)
        """

    def get_delete_query(self):
        return "DELETE FROM Warehouses WHERE id = %s"

    def get_update_query(self):
        return """
            UPDATE Warehouses SET name = %s, address = %s, geo_text = %s, geo_coordinates = %s
            WHERE id = %s
        """