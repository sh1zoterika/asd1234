import sys
import psycopg2

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit
)
from psycopg2 import OperationalError, sql
class GlobalData:
    username = None
    password = None


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('PostgreSQL Login')
        self.setGeometry(100, 100, 300, 150)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()

        self.username_label = QLabel('Username:')
        self.username_input = QLineEdit()
        self.password_label = QLabel('Password:')
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton('Login')

        self.layout.addWidget(self.username_label)
        self.layout.addWidget(self.username_input)
        self.layout.addWidget(self.password_label)
        self.layout.addWidget(self.password_input)
        self.layout.addWidget(self.login_button)

        self.central_widget.setLayout(self.layout)

        self.login_button.clicked.connect(self.open_main_window)

    def open_main_window(self):
        try:
            self.main_window = MainWindow()
            self.main_window.show()
            GlobalData.username = self.username_input.text()
            GlobalData.password = self.password_input.text()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Main Window: {e}")



class Database():
    def __init__(self):
        self.dbname = 'Warehouses'
        self.user = GlobalData.username
        self.password = GlobalData.password
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
                host=self.host
            )
            self.cursor = self.conn.cursor()
            print("Database connection successful.")
        except OperationalError as e:
            print(f"Error connecting to the database: {e}")
            QMessageBox.critical(None, "Database Error", f"Error connecting to the database: {e}")
            sys.exit(1)


    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        if exc_type:
            print(f"An error occurred: {exc_val}")
        return False


    def get_orders(self):
        with self():
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
        with self:
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
        with self:
            try:
                self.cursor.execute("SELECT id, name FROM Warehouses")
                result = self.cursor.fetchall()
                return result
            except Exception as e:
                print(f"Error fetching warehouses: {e}")
                return []

    def get_warehouse_id_by_name(self, name):
        with self:
            try:
                self.cursor.execute("SELECT id FROM Warehouse WHERE name = %s", (name,))
                result = self.cursor.fetchone()
                self.__exit__()
                return result[0] if result else None
            except Exception as e:
                print(f"Ошибка при получении ID склада: {e}")
                return None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Warehouse Database")
        self.setGeometry(500, 200, 600, 400)

        layout = QVBoxLayout()

        self.buttons = {}
        buttons = [
            ('Продажа товаров', self.open_sales_window),
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
        try:
            self.sales_window = SalesWindow()
            self.sales_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Sales Window: {e}")

    def open_receiving_window(self):
        try:
            self.receiving_window = ReceivingWindow()
            self.receiving_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Receiving Window: {e}")

    def open_transfer_window(self):
        try:
            self.transfer_window = TransferWindow()
            self.transfer_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Transfer Window: {e}")

    def open_write_off_window(self):
        try:
            self.write_off_window = WriteOffProductWindow()
            self.write_off_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Write Off Window: {e}")

    def open_clients_window(self):
        QMessageBox.information(self, "Клиенты", "Функционал клиентов еще не реализован.")

    def open_warehouses_window(self):
        QMessageBox.information(self, "Склады", "Функционал складов еще не реализован.")

    def open_documents_window(self):
        QMessageBox.information(self, "Документы", "Функционал документов еще не реализован.")

    def open_templates_window(self):
        QMessageBox.information(self, "Шаблоны", "Функционал шаблонов еще не реализован.")

class SalesWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Продажа товаров")
        self.setGeometry(600, 200, 800, 600)

        layout = QVBoxLayout()

        self.combo_box = QComboBox()
        self.load_orders()
        self.combo_box.currentIndexChanged.connect(self.update_table)
        layout.addWidget(self.combo_box)

        self.orders_button = QPushButton("Текущие заказы")
        self.orders_button.clicked.connect(self.open_current_orders_window)
        layout.addWidget(self.orders_button)

        self.add_button = QPushButton("Добавить товары")
        layout.addWidget(self.add_button)

        self.table_widget = QTableWidget()
        layout.addWidget(self.table_widget)

        button_layout = QHBoxLayout()

        self.delete_button = QPushButton("Удалить товары из заказа")
        button_layout.addWidget(self.delete_button)

        self.confirm_button = QPushButton("Подтвердить")
        button_layout.addWidget(self.confirm_button)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.add_button.clicked.connect(self.open_add_product_window)

        self.update_table()

    def open_current_orders_window(self):
        try:
            self.current_orders_window = CurrentOrderWindow()
            self.current_orders_window.show()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка в открытии окна текущих заказов: {e}')

    def load_orders(self):
        db = Database()
        orders = db.get_orders()
        db.close()
        for order in orders:
            self.combo_box.addItem(order[1], order[0])

    def update_table(self):
        order_id = self.combo_box.currentData()
        db = Database()
        products = db.get_products_by_order(order_id)
        db.close()
        self.table_widget.setRowCount(len(products))
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["Товар", "Количество", "Цена"])
        for i, product in enumerate(products):
            self.table_widget.setItem(i, 0, QTableWidgetItem(product[0]))
            self.table_widget.setItem(i, 1, QTableWidgetItem(str(product[1])))
            self.table_widget.setItem(i, 2, QTableWidgetItem(str(product[2])))

    def open_add_product_window(self):
        order_id = self.combo_box.currentData()
        self.add_product_window = AddProductWindow(order_id)
        self.add_product_window.show()

class AddProductWindow(QMainWindow):
    def __init__(self, order_id):
        super().__init__()
        self.order_id = order_id
        self.setWindowTitle('Добавить товары в заказ')
        self.setGeometry(600, 200, 1000, 600)  # Увеличил ширину окна для размещения обеих таблиц

        self.db = Database()  # Make sure this is the correct way to connect to your DB

        layout = QVBoxLayout()

        # ComboBox for selecting warehouse
        self.combo_box = QComboBox()
        self.load_warehouses()
        self.combo_box.currentIndexChanged.connect(self.update_warehouse_table)
        layout.addWidget(self.combo_box)

        # Horizontal layout for the two tables
        tables_layout = QHBoxLayout()

        # Table for displaying products from the selected warehouse
        self.warehouse_table = QTableWidget()
        self.warehouse_table.setColumnCount(3)
        self.warehouse_table.setHorizontalHeaderLabels(['Товар', 'Количество', 'Цена'])
        tables_layout.addWidget(self.warehouse_table)

        # Table for showing quantities to be added to the order
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(1)
        self.order_table.setHorizontalHeaderLabels(['Количество в заказ'])
        tables_layout.addWidget(self.order_table)

        layout.addLayout(tables_layout)

        # Button to add products to the order
        self.add_button = QPushButton('Добавить')
        self.add_button.clicked.connect(self.add_products_to_order)
        layout.addWidget(self.add_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.update_warehouse_table()

    def load_warehouses(self):
        warehouses = self.db.get_warehouses()
        for warehouse in warehouses:
            self.combo_box.addItem(warehouse[1], warehouse[0])

    def update_warehouse_table(self):
        warehouse_id = self.combo_box.currentData()
        if warehouse_id is not None:
            products = self.db.get_products_by_warehouse(warehouse_id)
            self.warehouse_table.setRowCount(len(products))
            self.order_table.setRowCount(len(products))

            for i, product in enumerate(products):
                self.warehouse_table.setItem(i, 0, QTableWidgetItem(product[0]))
                self.warehouse_table.setItem(i, 1, QTableWidgetItem(str(product[1])))
                self.warehouse_table.setItem(i, 2, QTableWidgetItem(str(product[2])))

                # Initialize order_table
                self.order_table.setItem(i, 0, QTableWidgetItem('0'))

    def add_products_to_order(self):
        warehouse_id = self.combo_box.currentData()
        if warehouse_id:
            products = self.db.get_products_by_warehouse(warehouse_id)
            for i, product in enumerate(products):
                quantity = int(self.order_table.item(i, 0).text())
                if quantity > 0:
                    self.db.cursor.execute("""
                        INSERT INTO order_items (order_id, product_name, quantity, price)
                        VALUES (%s, %s, %s, %s)
                    """, (self.order_id, product[0], quantity, product[2]))
                    self.db.conn.commit()
            QMessageBox.information(self, 'Успех', 'Товары добавлены в заказ.')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, выберите склад.')

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)

class CurrentOrderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Текущие заказы')
        self.setGeometry(600, 200, 800, 600)

        layout = QVBoxLayout()

        self.table_widget = QTableWidget()
        layout.addWidget(self.table_widget)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton('Добавить заказ')
        self.add_button.clicked.connect(self.add_order)
        button_layout.addWidget(self.add_button)

        self.delete_button = QPushButton('Удалить заказ')
        self.delete_button.clicked.connect(self.delete_order)
        button_layout.addWidget(self.delete_button)

        self.rollback_button = QPushButton('Откатить изменения')
        self.rollback_button.clicked.connect(self.rollback_changes)
        button_layout.addWidget(self.rollback_button)

        self.save_button = QPushButton('Сохранить изменения')
        self.save_button.clicked.connect(self.save_changes)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.update_table()
        self.changes = []  # To track changes

    def connect_db(self):
        return psycopg2.connect(
            dbname="Warehouses",
            user="shava",
            password="XsMyVs1420!?",
            host="127.0.0.1",
            port="5432"
        )

    def update_table(self):
        try:
            connection = self.connect_db()
            cursor = connection.cursor()
            cursor.execute("""
                SELECT Orders.id, Clients.name 
                FROM Orders
                JOIN Clients ON Orders.client_id = Clients.id
            """)
            orders = cursor.fetchall()
            connection.close()

            self.table_widget.setRowCount(len(orders))
            self.table_widget.setColumnCount(2)
            self.table_widget.setHorizontalHeaderLabels(["ID", "Клиент"])
            for i, order in enumerate(orders):
                self.table_widget.setItem(i, 0, QTableWidgetItem(str(order[0])))
                self.table_widget.setItem(i, 1, QTableWidgetItem(order[1]))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {e}")

    def add_order(self):
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)
        self.table_widget.setItem(row_position, 0, QTableWidgetItem(''))  # ID будет автоматически присвоен
        self.table_widget.setItem(row_position, 1, QTableWidgetItem('Новый клиент'))
        self.changes.append(('insert', None, ['Новый клиент']))
        QMessageBox.information(self, "Успех", "Заказ успешно добавлен!")

    def delete_order(self):
        selected_row = self.table_widget.currentRow()
        if selected_row >= 0:
            id_item = self.table_widget.item(selected_row, 0)
            if id_item:
                self.changes.append(('delete', id_item.text(), None))
            self.table_widget.removeRow(selected_row)
            self.update_ids()
            QMessageBox.information(self, "Успех", "Заказ успешно удален!")

    def update_ids(self):
        for row in range(self.table_widget.rowCount()):
            self.table_widget.setItem(row, 0, QTableWidgetItem(str(row + 1)))

    def rollback_changes(self):
        self.update_table()
        self.changes.clear()
        QMessageBox.information(self, "Успех", "Изменения успешно откатаны!")

    def save_changes(self):
        try:
            connection = self.connect_db()
            cursor = connection.cursor()
            connection.autocommit = False

            for change in self.changes:
                change_type, row_id, row_data = change
                if change_type == 'insert':
                    cursor.execute(
                        "INSERT INTO orders (client_name) VALUES (%s)",
                        (row_data[0],)
                    )
                elif change_type == 'delete':
                    cursor.execute(
                        "DELETE FROM orders WHERE id = %s",
                        (row_id,)
                    )
                elif change_type == 'update':
                    cursor.execute(
                        "UPDATE orders SET client_name = %s WHERE id = %s",
                        (row_data[0], row_id)
                    )

            connection.commit()
            connection.close()
            self.changes.clear()
            QMessageBox.information(self, "Успех", "Изменения успешно сохранены!")
        except Exception as e:
            if connection:
                connection.rollback()
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при сохранении: {e}")

    def edit_cell(self, row, column):
        # Implement if needed for inline cell editing
        pass

class TransferWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Перемещение товаров')
        self.setGeometry(600, 200, 800, 600)

        self.db = Database()
        self.changes = []  # For tracking changes

        layout = QVBoxLayout()

        # Layout for combo boxes
        combo_layout = QHBoxLayout()

        self.from_warehouse_combo_box = QComboBox()
        self.from_warehouse_combo_box.addItem("Выберите склад", None)
        self.load_warehouses(self.from_warehouse_combo_box)
        self.from_warehouse_combo_box.currentIndexChanged.connect(self.update_table)
        combo_layout.addWidget(self.from_warehouse_combo_box)

        # No combo box for right table, only columns
        # Adding a placeholder for consistency
        self.to_warehouse_label = QLabel('Склад назначения:')
        combo_layout.addWidget(self.to_warehouse_label)

        layout.addLayout(combo_layout)

        # Layout for tables
        main_layout = QHBoxLayout()

        # Table for products in the selected warehouse
        self.warehouse_table = QTableWidget()
        self.warehouse_table.setColumnCount(3)
        self.warehouse_table.setHorizontalHeaderLabels(['Товар', 'Количество', 'Цена'])
        main_layout.addWidget(self.warehouse_table)

        # Table for moving products
        self.move_table = QTableWidget()
        self.move_table.setColumnCount(2)
        self.move_table.setHorizontalHeaderLabels(['Количество', 'Склад назначения'])
        main_layout.addWidget(self.move_table)

        layout.addLayout(main_layout)

        # Buttons for operations
        button_layout = QHBoxLayout()

        self.move_button = QPushButton('Переместить')
        self.move_button.clicked.connect(self.move_products)
        button_layout.addWidget(self.move_button)

        self.cancel_button = QPushButton('Отменить')
        self.cancel_button.clicked.connect(self.cancel_changes)
        button_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton('Сохранить')
        self.save_button.clicked.connect(self.save_changes)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Initial load
        self.update_table()

    def load_warehouses(self, combo_box):
        warehouses = self.db.get_warehouses()
        for warehouse in warehouses:
            combo_box.addItem(warehouse[1], warehouse[0])

    def update_table(self):
        from_warehouse_id = self.from_warehouse_combo_box.currentData()
        if from_warehouse_id is not None:
            products = self.db.get_products_by_warehouse(from_warehouse_id)
            self.warehouse_table.setRowCount(len(products))
            self.move_table.setRowCount(len(products))
            for i, product in enumerate(products):
                self.warehouse_table.setItem(i, 0, QTableWidgetItem(product[0]))
                self.warehouse_table.setItem(i, 1, QTableWidgetItem(str(product[1])))
                self.warehouse_table.setItem(i, 2, QTableWidgetItem(str(product[2])))

                # Initialize move_table
                self.move_table.setItem(i, 0, QTableWidgetItem('0'))
                self.move_table.setItem(i, 1, QTableWidgetItem(self.from_warehouse_combo_box.currentText()))

    def move_products(self):
        from_warehouse_id = self.from_warehouse_combo_box.currentData()

        if from_warehouse_id:
            for i in range(self.move_table.rowCount()):
                quantity = self.move_table.item(i, 0).text()
                to_warehouse_name = self.move_table.item(i, 1).text()
                product_name = self.warehouse_table.item(i, 0).text()

                if quantity and to_warehouse_name:
                    to_warehouse_id = self.db.get_warehouse_id_by_name(to_warehouse_name)
                    if to_warehouse_id:
                        self.changes.append(('move', from_warehouse_id, to_warehouse_id, product_name, quantity))

            QMessageBox.information(self, 'Успех', 'Товары перемещены!')

    def cancel_changes(self):
        self.update_table()
        self.changes.clear()
        QMessageBox.information(self, 'Отменено', 'Изменения отменены!')

    def save_changes(self):
        try:
            connection = psycopg2.connect(
                dbname="Warehouses",
                user="shava",
                password="XsMyVs1420!?",
                host="127.0.0.1",
                port="5432"
            )
            cursor = connection.cursor()
            connection.autocommit = False

            for change in self.changes:
                change_type, from_warehouse, to_warehouse, product_name, quantity = change
                if change_type == 'move':
                    # Move product from one warehouse to another
                    cursor.execute("""
                        UPDATE ProductInWarehouse
                        SET amount = amount - %s
                        WHERE warehouse_id = %s AND product_name = %s
                    """, (quantity, from_warehouse, product_name))

                    cursor.execute("""
                        INSERT INTO ProductInWarehouse (warehouse_id, product_name, amount, price)
                        VALUES (%s, %s, %s, (SELECT price FROM ProductInWarehouse WHERE warehouse_id = %s AND product_name = %s))
                        ON CONFLICT (warehouse_id, product_name)
                        DO UPDATE SET amount = ProductInWarehouse.amount + EXCLUDED.amount
                    """, (to_warehouse, product_name, quantity, from_warehouse, product_name))

            connection.commit()
            connection.close()
            self.changes.clear()
            QMessageBox.information(self, "Успех", "Изменения успешно сохранены!")
        except Exception as e:
            if connection:
                connection.rollback()
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при сохранении: {e}")

class WriteOffProductWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Списание товаров')
        self.setGeometry(600, 200, 1000, 600)  # Set the window size

        self.db = Database()  # Connect to the database

        layout = QVBoxLayout()

        # ComboBox for selecting warehouse
        self.combo_box = QComboBox()
        self.load_warehouses()
        self.combo_box.currentIndexChanged.connect(self.update_warehouse_table)
        layout.addWidget(self.combo_box)

        # Horizontal layout for the two tables
        tables_layout = QHBoxLayout()

        # Table for displaying products from the selected warehouse
        self.warehouse_table = QTableWidget()
        self.warehouse_table.setColumnCount(3)
        self.warehouse_table.setHorizontalHeaderLabels(['Товар', 'Количество', 'Цена'])
        tables_layout.addWidget(self.warehouse_table)

        # Table for showing quantities to be written off
        self.writeoff_table = QTableWidget()
        self.writeoff_table.setColumnCount(1)
        self.writeoff_table.setHorizontalHeaderLabels(['Количество списания'])
        tables_layout.addWidget(self.writeoff_table)

        layout.addLayout(tables_layout)

        # Button to write off products from the warehouse
        self.writeoff_button = QPushButton('Списать товары')
        self.writeoff_button.clicked.connect(self.write_off_products)
        layout.addWidget(self.writeoff_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.update_warehouse_table()

    def load_warehouses(self):
        warehouses = self.db.get_warehouses()
        for warehouse in warehouses:
            self.combo_box.addItem(warehouse[1], warehouse[0])

    def update_warehouse_table(self):
        warehouse_id = self.combo_box.currentData()
        if warehouse_id is not None:
            products = self.db.get_products_by_warehouse(warehouse_id)
            self.warehouse_table.setRowCount(len(products))
            self.writeoff_table.setRowCount(len(products))

            for i, product in enumerate(products):
                self.warehouse_table.setItem(i, 0, QTableWidgetItem(product[0]))
                self.warehouse_table.setItem(i, 1, QTableWidgetItem(str(product[1])))
                self.warehouse_table.setItem(i, 2, QTableWidgetItem(str(product[2])))

                # Initialize writeoff_table
                self.writeoff_table.setItem(i, 0, QTableWidgetItem('0'))

    def write_off_products(self):
        warehouse_id = self.combo_box.currentData()
        if warehouse_id:
            products = self.db.get_products_by_warehouse(warehouse_id)
            for i, product in enumerate(products):
                quantity = int(self.writeoff_table.item(i, 0).text())
                if quantity > 0:
                    self.db.cursor.execute("""
                        UPDATE ProductInWarehouse
                        SET amount = amount - %s
                        WHERE warehouse_id = %s AND product_name = %s AND amount >= %s
                    """, (quantity, warehouse_id, product[0], quantity))
                    self.db.conn.commit()
            QMessageBox.information(self, 'Успех', 'Товары списаны со склада.')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, выберите склад.')

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)

class ReceivingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Приёмка товаров')
        self.setGeometry(600, 200, 800, 600)

        self.db = Database()
        self.changes = []  # For tracking changes

        layout = QVBoxLayout()

        self.combo_box = QComboBox()
        self.load_warehouses()
        self.combo_box.currentIndexChanged.connect(self.update_table)
        layout.addWidget(self.combo_box)

        # For displaying products in the selected warehouse
        self.table_widget = QTableWidget()
        layout.addWidget(self.table_widget)

        # Buttons for operations
        button_layout = QHBoxLayout()

        self.add_button = QPushButton('Добавить')
        self.add_button.clicked.connect(self.add_product)
        button_layout.addWidget(self.add_button)

        self.delete_button = QPushButton('Удалить')
        self.delete_button.clicked.connect(self.delete_product)
        button_layout.addWidget(self.delete_button)

        self.cancel_button = QPushButton('Отменить')
        self.cancel_button.clicked.connect(self.cancel_changes)
        button_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton('Сохранить')
        self.save_button.clicked.connect(self.save_changes)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.update_table()

    def load_warehouses(self):
        warehouses = self.db.get_warehouses()
        for warehouse in warehouses:
            self.combo_box.addItem(warehouse[1], warehouse[0])

    def update_table(self):
        warehouse_id = self.combo_box.currentData()
        if warehouse_id is not None:
            products = self.db.get_products_by_warehouse(warehouse_id)
            self.table_widget.setRowCount(len(products))
            self.table_widget.setColumnCount(3)
            self.table_widget.setHorizontalHeaderLabels(['Товар', 'Количество', 'Цена'])
            for i, product in enumerate(products):
                self.table_widget.setItem(i, 0, QTableWidgetItem(product[0]))
                self.table_widget.setItem(i, 1, QTableWidgetItem(str(product[1])))
                self.table_widget.setItem(i, 2, QTableWidgetItem(str(product[2])))

    def add_product(self):
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)
        self.table_widget.setItem(row_position, 0, QTableWidgetItem('Новый товар'))
        self.table_widget.setItem(row_position, 1, QTableWidgetItem('0'))
        self.table_widget.setItem(row_position, 2, QTableWidgetItem('0'))
        self.changes.append(('insert', row_position, ['Новый товар', 0, 0]))
        QMessageBox.information(self, 'Успех', 'Товар успешно добавлен!')

    def delete_product(self):
        selected_row = self.table_widget.currentRow()
        if selected_row >= 0:
            self.changes.append(('delete', selected_row, None))
            self.table_widget.removeRow(selected_row)
            QMessageBox.information(self, "Успех", "Товар успешно удален!")

    def cancel_changes(self):
        self.update_table()
        self.changes.clear()
        QMessageBox.information(self, "Успех", "Изменения успешно отменены!")

    def save_changes(self):
        try:
            warehouse_id = self.combo_box.currentData()
            if warehouse_id is not None:
                connection = psycopg2.connect(
                    dbname="Warehouses",
                    user="shava",
                    password="XsMyVs1420!?",
                    host="127.0.0.1",
                    port="5432"
                )
                cursor = connection.cursor()
                connection.autocommit = False

                for change in self.changes:
                    change_type, row_index, row_data = change
                    if change_type == 'insert':
                        product_name = row_data[0]
                        quantity = int(row_data[1])
                        price = float(row_data[2])
                        cursor.execute("""
                            INSERT INTO ProductInWarehouse (warehouse_id, product_name, amount, price)
                            VALUES (%s, %s, %s, %s)
                        """, (warehouse_id, product_name, quantity, price))
                    elif change_type == 'delete':
                        product_name = self.table_widget.item(row_index, 0).text()
                        cursor.execute("""
                            DELETE FROM ProductInWarehouse
                            WHERE warehouse_id = %s AND product_name = %s
                        """, (warehouse_id, product_name))

                connection.commit()
                connection.close()
                self.changes.clear()
                QMessageBox.information(self, "Успех", "Изменения успешно сохранены!")
        except Exception as e:
            if connection:
                connection.rollback()
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при сохранении: {e}")

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = LoginWindow()
    main_window.show()
    sys.exit(app.exec_())
