import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit
)
from psycopg2 import OperationalError, sql

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class GlobalData:
    username = None
    password = None

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('PostgreSQL Login')
        self.setGeometry(700, 400, 300, 150)

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
        GlobalData.username = self.username_input.text()
        GlobalData.password = self.password_input.text()
        try:
            self.main_window = MainWindow()
            self.main_window.show()
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
                host=self.host,
                port=self.port
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
            print(f"An error occurred: {exc_val}")
        return False

    def get_orders(self):
        try:
            with self as db:
                query = """
                SELECT o.id, c.name 
                FROM Orders o 
                JOIN Clients c ON o.client_id = c.id
                """
                db.cursor.execute(query)
                result = db.cursor.fetchall()
                return result
        except Exception as e:
            print(f"Error fetching orders: {e}")
            return []

    def get_products_by_order(self, order_id):
        try:
            with self as db:
                query = """
                SELECT p.name, oi.amount, oi.price 
                FROM Order_items oi 
                JOIN Products p ON oi.product_id = p.id 
                WHERE oi.order_id = %s
                """
                db.cursor.execute(query, (order_id,))
                result = db.cursor.fetchall()
                return result
        except Exception as e:
            print(f"Error fetching products by order: {e}")
            return []

    def get_warehouses(self):
        try:
            with self as db:
                db.cursor.execute("SELECT id, name FROM Warehouses")
                result = db.cursor.fetchall()
                return result
        except Exception as e:
            print(f"Error fetching warehouses: {e}")
            return []

    def get_warehouse_id_by_name(self, name):
        try:
            with self as db:
                db.cursor.execute("SELECT id FROM Warehouses WHERE name = %s", (name,))
                result = db.cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Ошибка при получении ID склада: {e}")
            return None

class BaseProductWindow(QMainWindow):
    def __init__(self, title, geometry, headers, query, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(*geometry)

        self.query = query
        self.headers = headers

        self.db = Database()  

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

    def closeEvent(self, event):
        print(f"Closing {self.windowTitle()}...")
        try:
            self.db.close()
        except Exception as e:
            print(f"Error closing database connection: {e}")
        event.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Warehouse Database")
        self.setGeometry(600, 200, 600, 400)

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
        self.sales_window = SalesWindow()
        self.sales_window.show()

    def open_receiving_window(self):
        self.receiving_window = ReceivingWindow()
        self.receiving_window.show()

    def open_transfer_window(self):
        self.transfer_window = TransferWindow()
        self.transfer_window.show()

    def open_write_off_window(self):
        self.write_off_window = WriteOffProductWindow()
        self.write_off_window.show()

    def open_clients_window(self):
        try:
            self.client_window = ClientWindow()
            self.client_window.show()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка открытия окна с клиентами: {e}')

    def open_warehouses_window(self):
        try:
            self.warehouse_window = WarehouseWindow()
            self.warehouse_window.show()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка открытия окна со складами: {e}')

    def open_documents_window(self):
        pass

    def open_templates_window(self):
        pass

class SalesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Продажа товаров")
        self.setGeometry(600, 200, 800, 600)

        self.db = Database()

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
            orders = self.db.get_orders()
            self.orders_combo.clear()  # Очистить старые элементы
            for order in orders:
                self.orders_combo.addItem(f"Order {order[0]} - {order[1]}", order[0])
        except Exception as e:
            print(f"Error loading orders: {e}")
            QMessageBox.critical(self, "Error", f"Error loading orders: {e}")

    def update_table(self):
        try:
            order_id = self.orders_combo.currentData()
            products = self.db.get_products_by_order(order_id)
            self.table_widget.setRowCount(len(products))
            self.table_widget.setColumnCount(3)
            self.table_widget.setHorizontalHeaderLabels(["Product", "Amount", "Price"])
            for i, (name, amount, price) in enumerate(products):
                self.table_widget.setItem(i, 0, QTableWidgetItem(name))
                self.table_widget.setItem(i, 1, QTableWidgetItem(str(amount)))
                self.table_widget.setItem(i, 2, QTableWidgetItem(str(price)))
        except Exception as e:
            print(f"Error updating table: {e}")
            QMessageBox.critical(self, "Error", f"Error updating table: {e}")

    def open_current_orders_window(self):
        try:
            self.current_orders_window = CurrentOrderWindow(self)  # Укажите родительское окно
            self.current_orders_window.show()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error opening current orders window: {e}')

    def open_add_product_window(self):
        try:
            order_id = self.orders_combo.currentData()
            self.add_product_window = AddProductWindow(order_id, self)  # Укажите родительское окно
            self.add_product_window.show()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error opening add product window: {e}')

    def save_changes(self):
        # Implement saving changes if needed
        pass

class AddProductWindow(BaseProductWindow):
    def __init__(self, order_id, parent=None):
        query = {
            'select': """SELECT product_name, amount, price FROM ProductInWarehouse WHERE warehouse_id = %s""",
            'insert': """INSERT INTO Order_items (order_id, product_name, quantity, price) VALUES (%s, %s, %s, %s)"""
        }
        headers = ['Товар', 'Количество', 'Цена', 'Количество в заказ']
        super().__init__('Добавить товары в заказ', (600, 200, 1000, 600), headers, query, parent)
        self.order_id = order_id

        # Button to add products to the order
        self.add_button = QPushButton('Добавить')
        self.add_button.clicked.connect(self.add_products_to_order)
        layout = self.centralWidget().layout()
        layout.addWidget(self.add_button)

    def add_products_to_order(self):
        warehouse_id = self.combo_box.currentData()
        if warehouse_id:
            try:
                connection = self.connect_db()
                cursor = connection.cursor()
                connection.autocommit = False

                for i in range(self.warehouse_table.rowCount()):
                    product_name = self.warehouse_table.item(i, 0).text()
                    quantity = int(self.order_table.item(i, 0).text())
                    price = float(self.warehouse_table.item(i, 2).text())
                    if quantity > 0:
                        cursor.execute(self.query['insert'], (self.order_id, product_name, quantity, price))

                connection.commit()
                connection.close()
                QMessageBox.information(self, 'Успех', 'Товары добавлены в заказ.')
            except Exception as e:
                if connection:
                    connection.rollback()
                print(f"Error adding products to order: {e}")
                QMessageBox.critical(self, 'Ошибка', f'Ошибка добавления товаров в заказ: {e}')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, выберите склад.')

class WriteOffProductWindow(BaseProductWindow):
    def __init__(self):
        query = {
            'select': """SELECT product_name, amount, price FROM ProductInWarehouse WHERE warehouse_id = %s""",
            'insert': """UPDATE ProductInWarehouse SET amount = amount - %s WHERE warehouse_id = %s AND product_name = %s AND amount >= %s"""
        }
        headers = ['Товар', 'Количество в наличии', 'Цена', 'Количество списания']
        super().__init__('Списание товаров', (600, 200, 1000, 600), headers, query)

        # Create and configure buttons
        self.writeoff_button = QPushButton('Списать товары')
        self.writeoff_button.clicked.connect(self.write_off_products)

        self.cancel_button = QPushButton('Отменить')
        self.cancel_button.clicked.connect(self.cancel_changes)

        self.save_button = QPushButton('Сохранить')
        self.save_button.clicked.connect(self.save_changes)

        # Add buttons to layout
        layout = self.centralWidget().layout()
        layout.addWidget(self.writeoff_button)
        layout.addWidget(self.cancel_button)
        layout.addWidget(self.save_button)

    def write_off_products(self):
        warehouse_id = self.combo_box.currentData()
        if warehouse_id:
            try:
                connection = self.connect_db()
                cursor = connection.cursor()
                connection.autocommit = False

                for i in range(self.warehouse_table.rowCount()):
                    product_name = self.warehouse_table.item(i, 0).text()
                    write_off_amount = int(self.order_table.item(i, 0).text())
                    if write_off_amount > 0:
                        cursor.execute(self.query['insert'], (write_off_amount, warehouse_id, product_name, write_off_amount))

                connection.commit()
                connection.close()
                QMessageBox.information(self, 'Успех', 'Товары списаны со склада.')
            except Exception as e:
                if connection:
                    connection.rollback()
                print(f"Error writing off products: {e}")
                QMessageBox.critical(self, 'Ошибка', f'Ошибка списания товаров: {e}')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, выберите склад.')

    def cancel_changes(self):
        self.update_warehouse_table()
        QMessageBox.information(self, 'Успех', 'Изменения успешно откатаны')

    def save_changes(self):
        try:
            connection = self.connect_db()
            cursor = connection.cursor()
            connection.autocommit = False

            for i in range(self.warehouse_table.rowCount()):
                product_name = self.warehouse_table.item(i, 0).text()
                write_off_amount = int(self.order_table.item(i, 0).text())
                if write_off_amount > 0:
                    cursor.execute(self.query['insert'], (write_off_amount, warehouse_id, product_name, write_off_amount))

            connection.commit()
            connection.close()
            QMessageBox.information(self, 'Успех', 'Изменения успешно сохранены!')
        except Exception as e:
            if connection:
                connection.rollback()
            print(f"Error saving changes: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Ошибка сохранения изменений: {e}')

class CurrentOrderWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
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

    def update_table(self):
        try:
            with Database() as db:
                db.cursor.execute("""
                    SELECT Orders.id, Clients.name 
                    FROM Orders
                    JOIN Clients ON Orders.client_id = Clients.id
                """)
                orders = db.cursor.fetchall()

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
            with Database() as db:
                for change in self.changes:
                    change_type, row_id, row_data = change
                    if change_type == 'insert':
                        db.cursor.execute(
                            "INSERT INTO Orders (client_name) VALUES (%s)",
                            (row_data[0],)
                        )
                    elif change_type == 'delete':
                        db.cursor.execute(
                            "DELETE FROM Orders WHERE id = %s",
                            (row_id,)
                        )
                    elif change_type == 'update':
                        db.cursor.execute(
                            "UPDATE Orders SET client_name = %s WHERE id = %s",
                            (row_data[0], row_id)
                        )

                db.conn.commit()
                self.changes.clear()
                QMessageBox.information(self, "Успех", "Изменения успешно сохранены!")
        except Exception as e:
            if db.conn:
                db.conn.rollback()
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
            with Database() as db:
                for change in self.changes:
                    change_type, from_warehouse, to_warehouse, product_name, quantity = change
                    if change_type == 'move':
                        # Move product from one warehouse to another
                        db.cursor.execute("""
                            UPDATE ProductInWarehouse
                            SET amount = amount - %s
                            WHERE warehouse_id = %s AND product_name = %s
                        """, (quantity, from_warehouse, product_name))

                        db.cursor.execute("""
                            INSERT INTO ProductInWarehouse (warehouse_id, product_name, amount, price)
                            VALUES (%s, %s, %s, (SELECT price FROM ProductInWarehouse WHERE warehouse_id = %s AND product_name = %s))
                            ON CONFLICT (warehouse_id, product_name)
                            DO UPDATE SET amount = ProductInWarehouse.amount + EXCLUDED.amount
                        """, (to_warehouse, product_name, quantity, from_warehouse, product_name))

                db.conn.commit()
                self.changes.clear()
                QMessageBox.information(self, "Успех", "Изменения успешно сохранены!")
        except Exception as e:
            if db.conn:
                db.conn.rollback()
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при сохранении: {e}")

class BaseWindow(QMainWindow):
    def __init__(self, title, table_headers):
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(600, 200, 800, 600)

        layout = QVBoxLayout()

        self.table_widget = QTableWidget()
        layout.addWidget(self.table_widget)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton('Добавить')
        self.add_button.clicked.connect(self.add_item)
        button_layout.addWidget(self.add_button)

        self.delete_button = QPushButton('Удалить')
        self.delete_button.clicked.connect(self.delete_item)
        button_layout.addWidget(self.delete_button)

        self.cancel_button = QPushButton('Отменить')
        self.cancel_button.clicked.connect(self.cancel_changes)
        button_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton('Сохранить')
        self.save_button.clicked.connect(self.save_changes)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)  # Добавляем button_layout в основной layout

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.table_headers = table_headers
        self.update_table()
        self.changes = []  # Для отслеживания изменений

    def update_table(self):
        try:
            with Database() as db:
                db.cursor.execute(self.get_select_query())
                items = db.cursor.fetchall()
                self.table_widget.setRowCount(len(items))
                self.table_widget.setColumnCount(len(self.table_headers))
                self.table_widget.setHorizontalHeaderLabels(self.table_headers)
                for i, item in enumerate(items):
                    for j, value in enumerate(item):
                        self.table_widget.setItem(i, j, QTableWidgetItem(str(value)))
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке данных: {e}')

    def add_item(self):
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)
        for i in range(len(self.table_headers)):
            self.table_widget.setItem(row_position, i, QTableWidgetItem(''))
        self.changes.append(('insert', None, ['' for _ in range(len(self.table_headers))]))
        QMessageBox.information(self, 'Успех', 'Элемент успешно добавлен!')

    def delete_item(self):
        selected_row = self.table_widget.currentRow()
        if selected_row >= 0:
            id_item = self.table_widget.item(selected_row, 0)
            if id_item:
                self.changes.append(('delete', id_item.text(), None))
            self.table_widget.removeRow(selected_row)
            QMessageBox.information(self, 'Успех', 'Элемент успешно удалён!')

    def cancel_changes(self):
        self.update_table()
        self.changes.clear()
        QMessageBox.information(self, 'Успех', 'Изменения успешно откатаны')

    def save_changes(self):
        try:
            with Database() as db:
                for change in self.changes:
                    change_type, row_id, row_data = change
                    if change_type == 'insert':
                        db.cursor.execute(self.get_insert_query(), row_data)
                    elif change_type == 'delete':
                        db.cursor.execute(self.get_delete_query(), (row_id,))
                    elif change_type == 'update':
                        db.cursor.execute(self.get_update_query(), row_data + [row_id])

                db.conn.commit()
                self.changes.clear()
                QMessageBox.information(self, 'Успех', 'Изменения успешно сохранены!')
        except Exception as e:
            if db.conn:
                db.conn.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка при сохранении: {e}')

    def edit_cell(self, row, column):
        old_item = self.table_widget.item(row, column)
        if old_item:
            old_value = old_item.text()
            new_value = self.table_widget.currentItem().text()

            if old_value != new_value:
                row_id_item = self.table_widget.item(row, 0)
                if row_id_item:
                    row_id = row_id_item.text()
                    item_data = [self.table_widget.item(row, i).text() for i in range(1, len(self.table_headers))]
                    self.changes.append(('update', row_id, item_data))

    def get_select_query(self):
        raise NotImplementedError

    def get_insert_query(self):
        raise NotImplementedError

    def get_delete_query(self):
        raise NotImplementedError

    def get_update_query(self):
        raise NotImplementedError

class ReceivingWindow(BaseWindow):
    def __init__(self):
        try:
            self.db = Database()
            self.combo_box = QComboBox()  # Initialize combo_box here
            super().__init__('Приёмка товаров', ['Товар', 'Количество', 'Цена'])
            self.changes = []  # Для отслеживания изменений

            self.load_warehouses()
            self.combo_box.currentIndexChanged.connect(self.update_table)

            # Создаем отдельный layout для combo_box и таблицы
            combo_table_layout = QVBoxLayout()
            combo_table_layout.addWidget(self.combo_box)
            combo_table_layout.addWidget(self.table_widget)

            # Добавляем combo_table_layout в основной layout
            main_layout = self.centralWidget().layout()
            main_layout.insertLayout(0, combo_table_layout)  # Добавляем combo_table_layout в основной layout

            self.update_table()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при инициализации окна: {e}")

    def load_warehouses(self):
        try:
            warehouses = self.db.get_warehouses()
            for warehouse in warehouses:
                self.combo_box.addItem(warehouse[1], warehouse[0])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке складов: {e}")

    def update_table(self):
        try:
            warehouse_id = self.combo_box.currentData()
            if warehouse_id is not None:
                products = self.db.get_products_by_warehouse(warehouse_id)
                self.table_widget.setRowCount(len(products))
                self.table_widget.setColumnCount(len(self.table_headers))
                self.table_widget.setHorizontalHeaderLabels(self.table_headers)
                for i, product in enumerate(products):
                    self.table_widget.setItem(i, 0, QTableWidgetItem(product[0]))
                    self.table_widget.setItem(i, 1, QTableWidgetItem(str(product[1])))
                    self.table_widget.setItem(i, 2, QTableWidgetItem(str(product[2])))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении таблицы: {e}")

    def add_item(self):
        try:
            row_position = self.table_widget.rowCount()
            self.table_widget.insertRow(row_position)
            self.table_widget.setItem(row_position, 0, QTableWidgetItem('Новый товар'))
            self.table_widget.setItem(row_position, 1, QTableWidgetItem('0'))
            self.table_widget.setItem(row_position, 2, QTableWidgetItem('0'))
            self.changes.append(('insert', row_position, ['Новый товар', 0, 0]))
            QMessageBox.information(self, 'Успех', 'Товар успешно добавлен!')
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении товара: {e}")

    def delete_item(self):
        try:
            selected_row = self.table_widget.currentRow()
            if selected_row >= 0:
                self.changes.append(('delete', selected_row, None))
                self.table_widget.removeRow(selected_row)
                QMessageBox.information(self, "Успех", "Товар успешно удален!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении товара: {e}")

    def cancel_changes(self):
        try:
            self.update_table()
            self.changes.clear()
            QMessageBox.information(self, "Успех", "Изменения успешно отменены!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при отмене изменений: {e}")

    def save_changes(self):
        try:
            warehouse_id = self.combo_box.currentData()
            if warehouse_id is not None:
                connection = self.connect_db()
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

    def get_select_query(self):
        return "SELECT product_name, amount, price FROM ProductInWarehouse WHERE warehouse_id = %s"

    def get_insert_query(self):
        return "INSERT INTO ProductInWarehouse (warehouse_id, product_name, amount, price) VALUES (%s, %s, %s, %s)"

    def get_delete_query(self):
        return "DELETE FROM ProductInWarehouse WHERE warehouse_id = %s AND product_name = %s"

    def get_update_query(self):
        return "UPDATE ProductInWarehouse SET amount = %s, price = %s WHERE warehouse_id = %s AND product_name = %s"
                       
class ClientWindow(BaseWindow):
    def __init__(self):
        super().__init__('Клиенты', ['ID', 'Имя', 'Заказы', 'Инфо', 'Номер телефона', 'Адрес'])

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

class WarehouseWindow(BaseWindow):
    def __init__(self):
        super().__init__('Склады', ['ID', 'Название', 'Адрес', 'Геолокация', 'Координаты'])

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = LoginWindow()
    main_window.show()
    sys.exit(app.exec_())