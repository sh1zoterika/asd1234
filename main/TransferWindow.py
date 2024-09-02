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



class TransferWindow(QMainWindow):
    def __init__(self, user, password):
        super().__init__()
        self.setWindowTitle('Перемещение товаров')
        self.setGeometry(600, 200, 800, 600)

        self.db = Database(user, password)
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
        self.warehouse_table.setColumnCount(4)
        column_names = self.db.get_column_names('productinwarehouse')
        self.warehouse_table.setHorizontalHeaderLabels(column_names)
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