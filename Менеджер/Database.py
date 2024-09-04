import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit
)
from psycopg2 import OperationalError, sql
from LoginWindowmain import GlobalData


class Database():
    def __init__(self, user, password):
        self.dbname = 'Warehouses'
        self.user = user
        self.password = password
        self.host = "127.0.0.1"
        self.port = "5432"
        self.conn = None
        self.cursor = None

    def __enter__(self):
        try:
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                options='-c client_encoding=UTF8'
            )
            self.cursor = self.conn.cursor()
            print("Database connection successful.")
        except OperationalError as e:
            print(f"Error connecting to the database: {e}")
            QMessageBox.critical(None, "Database Error", f"Error connecting to the database: {e}")
            sys.exit(1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        if exc_type:
            print(f"Ошибка закрытия соединения: {exc_val}")
        return False

    def get_orders(self):
        try:
            query = """
            SELECT o.id, c.name 
            FROM Orders o 
            JOIN Clients c ON o.client_id = c.id
            """
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(f"Error fetching orders: {e}")
            return []

    def get_products_by_order(self, order_id):
        try:
            query = """
            SELECT p.name, oi.amount, oi.price 
            FROM Order_items oi 
            JOIN Products p ON oi.product_id = p.id 
            WHERE oi.order_id = %s
            """
            self.cursor.execute(query, (order_id,))
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(f"Error fetching products by order: {e}")
            return []

    def get_warehouses(self):
        try:
            self.cursor.execute("SELECT id, name FROM Warehouses")
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(f"Error fetching warehouses: {e}")
            return []

    def get_warehouse_id_by_name(self, name):
        try:
            self.cursor.execute("SELECT id FROM Warehouses WHERE name = %s", (name,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Ошибка при получении ID склада: {e}")
            return None

    def get_column_names(self, tablename):
        try:
            with self as db:
                self.cursor.execute(f"SELECT * FROM {tablename} LIMIT 0;")
                column_names = [desc[0] for desc in self.cursor.description]
                return column_names
        except Exception as e:
            print(f"Ошибка при получении имён столбцов: {e}")
            return None

    def get_product_in_warehouse(self, warehouseid):
        try:
            self.cursor.execute(f"""SELECT * FROM productinwarehouse
            WHERE warehouse_id = {warehouseid}
            """)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(f"Ошибка при товаров на складе: {e}")
            return None

    def get_next_id(self, table_name):
        try:
            self.cursor.execute(f"SELECT MAX(id) FROM {table_name}")
            max_id = self.cursor.fetchone()[0]
            return (max_id or 0) + 1
        except Exception as e:
            print(f"Ошибка при нумерации: {e}")
            return None
    def update_id(self, table_name):
        try:
            self.cursor.execute(f"SELECT * FROM {table_name} ORDER BY id")
            rows = self.cursor.fetchall()
            for new_id, row in enumerate(rows, start=1):
                old_id = row[0]
                self.cursor.execute(f"UPDATE {table_name} SET id = %s WHERE id = %s", (new_id, old_id))
        except Exception as e:
            print(f"Ошибка при нумерации: {e}")
            return None