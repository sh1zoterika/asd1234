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
from CurrentOrderWindow import CurrentOrderWindow
from AddProductWindow import AddProductWindow
from PyQt5 import QtCore


class SalesWindow(QMainWindow):
    def __init__(self, user=None, password=None, parent=None):
        self.user = user
        self.password = password
        super().__init__(parent)
        self.setWindowTitle("Продажа товаров")
        self.setGeometry(600, 200, 800, 600)


        layout = QVBoxLayout()

        # ComboBox для выбора заказа
        self.orders_combo = QComboBox()
        layout.addWidget(self.orders_combo)
        self.orders_combo.currentIndexChanged.connect(self.update_table)

        # Кнопка для открытия текущих заказов
        self.orders_button = QPushButton("Текущие заказы")
        self.orders_button.clicked.connect(self.open_current_orders_window)
        layout.addWidget(self.orders_button)

        # Кнопка для добавления товаров
        self.add_button = QPushButton("Добавить товары")
        self.add_button.clicked.connect(self.open_add_product_window)
        layout.addWidget(self.add_button)

        # Таблица для отображения товаров в заказе
        self.table_widget = QTableWidget()
        layout.addWidget(self.table_widget)

        # Кнопки для удаления товаров и подтверждения изменений
        button_layout = QHBoxLayout()

        self.delete_button = QPushButton("Удалить товары из заказа")
        self.delete_button.clicked.connect(self.delete_item)
        button_layout.addWidget(self.delete_button)

        self.confirm_button = QPushButton("Подтвердить")
        button_layout.addWidget(self.confirm_button)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.load_orders()
        self.update_table()

    def load_orders(self):
        try:
            with Database(self.user, self.password) as db:
                orders = db.get_orders()
                self.orders_combo.clear()  # Очистить старые элементы
                for order in orders:
                    self.orders_combo.addItem(f"Order {order[0]} - {order[1]}", order[0])
        except Exception as e:
            print(f"Error loading orders: {e}")
            QMessageBox.critical(self, "Error", f"Error loading orders: {e}")

    def update_table(self):
        try:
            with Database(self.user, self.password) as db:
                order_id = self.orders_combo.currentData()
                products = db.get_products_by_order(order_id)
                self.table_widget.setRowCount(len(products))
                self.table_widget.setColumnCount(4)
                headers = ['Product ID', 'Product Name', 'Amount', 'Price']
                self.table_widget.setHorizontalHeaderLabels(headers)
                for i, (id, name, amount, price) in enumerate(products):
                    self.table_widget.setItem(i, 0, QTableWidgetItem(str(id)))
                    self.table_widget.setItem(i, 1, QTableWidgetItem(str(name)))
                    self.table_widget.setItem(i, 2, QTableWidgetItem(str(amount)))
                    self.table_widget.setItem(i, 3, QTableWidgetItem(str(price)))
                self.make_table_read_only()
        except Exception as e:
            print(f"Error updating sales table: {e}")
            QMessageBox.critical(self, "Error", f"Error updating table: {e}")

    def open_current_orders_window(self):
        try:
            self.current_orders_window = CurrentOrderWindow(self, self.user, self.password)  # Укажите родительское окно
            self.current_orders_window.show()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error opening current orders window: {e}')

    def open_add_product_window(self):
        try:
            order_id = self.orders_combo.currentData()
            self.add_product_window = AddProductWindow(order_id, self.user, self.password, parent=self)  # Укажите родительское окно
            self.add_product_window.show()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error opening add product window: {e}')

    def save_changes(self):
        # Implement saving changes if needed
        pass
    
    def make_table_read_only(self):
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)

    def delete_item(self):
        with Database(self.user, self.password) as db:
            selected_row = self.table_widget.currentRow()
            if selected_row:
                id_item = self.table_widget.item(selected_row, 0).text()
                order_id = self.orders_combo.currentData()
                db.cursor.execute('DELETE FROM Order_Items WHERE product_id = %s AND order_id = %s', (id_item, order_id,))
                self.table_widget.removeRow(selected_row)
                db.conn.commit()
            QMessageBox.information(self, 'Успех', 'Элемент успешно удалён!')