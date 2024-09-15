import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox, QWidget, QPushButton, QApplication
)
from PyQt5 import QtCore
from Database import Database
from EditOrderWindow import EditOrderDialog
class ViewOrdersWindow(QDialog):
    def __init__(self, user, password, client_id):
        super().__init__()
        self.user = user
        self.password = password
        self.client_id = client_id

        self.setWindowTitle("Заказы клиента")
        self.setGeometry(400, 200, 600, 400)

        layout = QVBoxLayout()
        self.table_widget = QTableWidget()
        layout.addWidget(self.table_widget)
        self.sales_button = QPushButton('Перейти в продажи')
        self.sales_button.clicked.connect(self.gotosales)
        layout.addWidget(self.sales_button)
        self.setLayout(layout)

        self.load_orders()

    def load_orders(self):
        try:
            with Database(self.user, self.password) as db:
                db.cursor.execute("""
                    SELECT id, price, date, status
                    FROM Orders
                    WHERE client_id = %s
                """, (self.client_id,))
                orders = db.cursor.fetchall()
                self.table_widget.setRowCount(len(orders))
                self.table_widget.setColumnCount(4)
                self.table_widget.setHorizontalHeaderLabels(["ID", "price", "date", "status"])
                for i, order in enumerate(orders):
                    for j, value in enumerate(order):
                        item = QTableWidgetItem(str(value))
                        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                        self.table_widget.setItem(i, j, item)
        except Exception as e:
            logging.error(f"Error loading orders: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке заказов: {e}")

    def gotosales(self):
        try:
            selected_row = self.table_widget.currentRow()
            if selected_row != -1:  # Проверяем, что строка выбрана
                order_id = self.table_widget.item(selected_row, 0).text()
                editorder = EditOrderDialog(self.user, self.password, order_id)
                editorder.exec_()
            else:
                QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, выберите заказ.')
        except Exception as e:
            logging.error(f"Error opening EditOrderDialog: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при открытии окна продаж: {e}")