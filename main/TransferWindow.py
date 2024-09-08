import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit, QDialog
)
from psycopg2 import OperationalError, sql
from Database import Database
from PyQt5 import QtCore
from EditDialog import EditDialog


import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QSpinBox, QDialog
)
from psycopg2 import OperationalError, sql
from Database import Database
from PyQt5 import QtCore
from EditDialog import EditDialog


class TransferWindow(QMainWindow):
    def __init__(self, user, password):
        self.user = user
        self.password = password
        super().__init__()
        self.setWindowTitle('Перемещение товаров')
        self.setGeometry(600, 200, 800, 600)

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
        self.warehouse_table.setHorizontalHeaderLabels(['ID товара', 'Название товара', 'Количество'])
        main_layout.addWidget(self.warehouse_table)

        # Table for moving products
        self.move_table = QTableWidget()
        self.move_table.setColumnCount(2)
        self.move_table.setHorizontalHeaderLabels(['Количество', 'Склад назначения'])
        main_layout.addWidget(self.move_table)
        self.move_table.cellDoubleClicked.connect(self.edit_item)

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
        with Database(self.user, self.password) as db:
            warehouses = db.get_warehouses()
            for warehouse in warehouses:
                combo_box.addItem(warehouse[1], warehouse[0])

    def update_table(self):
        with Database(self.user, self.password) as db:
            from_warehouse_id = self.from_warehouse_combo_box.currentData()
            if from_warehouse_id is not None:
                db.cursor.execute("""
                    SELECT Products.id, Products.name, ProductInWarehouse.amount
                    FROM ProductInWarehouse
                    JOIN Products ON Products.id = ProductInWarehouse.product_id
                    WHERE ProductInWarehouse.warehouse_id = %s
                """, (from_warehouse_id,))
                products = db.cursor.fetchall()
                self.warehouse_table.setRowCount(len(products))
                self.move_table.setRowCount(len(products))
                for i, product in enumerate(products):
                    self.warehouse_table.setItem(i, 0, QTableWidgetItem(str(product[0])))
                    self.warehouse_table.setItem(i, 1, QTableWidgetItem(product[1]))
                    self.warehouse_table.setItem(i, 2, QTableWidgetItem(str(product[2])))

                    # Initialize move_table
                    quantity_spinbox = QSpinBox()
                    quantity_spinbox.setMaximum(999999999)
                    self.move_table.setCellWidget(i, 0, quantity_spinbox)
                    to_warehouse_combo = QComboBox()
                    to_warehouse_combo.addItem("Выберите склад", None)
                    self.load_warehouses(to_warehouse_combo)
                    self.move_table.setCellWidget(i, 1, to_warehouse_combo)
                self.make_table_read_only()

    def move_products(self):
        from_warehouse_id = self.from_warehouse_combo_box.currentData()
        if from_warehouse_id:
            for i in range(self.move_table.rowCount()):
                quantity_spinbox = self.move_table.cellWidget(i, 0)
                quantity = quantity_spinbox.value()
                to_warehouse_combo = self.move_table.cellWidget(i, 1)
                to_warehouse_id = to_warehouse_combo.currentData()
                product_id = self.warehouse_table.item(i, 0).text()

                if quantity > 0 and to_warehouse_id:
                    self.changes.append(('move', from_warehouse_id, to_warehouse_id, product_id, quantity))

            QMessageBox.information(self, 'Успех', 'Товары подготовлены к перемещению. Нажмите "Сохранить" для подтверждения.')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, выберите склад.')

    def cancel_changes(self):
        self.update_table()
        self.changes.clear()
        QMessageBox.information(self, 'Отменено', 'Изменения отменены!')

    def save_changes(self):
        try:
            with Database(self.user, self.password) as db:
                for change in self.changes:
                    change_type, from_warehouse, to_warehouse, product_id, quantity = change
                    if change_type == 'move':
                        # Move product from one warehouse to another
                        db.cursor.execute("""
                            UPDATE ProductInWarehouse
                            SET amount = amount - %s
                            WHERE warehouse_id = %s AND product_id = %s
                        """, (quantity, from_warehouse, product_id))

                        db.cursor.execute("""
                            SELECT amount FROM ProductInWarehouse
                            WHERE warehouse_id = %s AND product_id = %s
                        """, (to_warehouse, product_id))
                        result = db.cursor.fetchone()
                        if result:
                            db.cursor.execute("""
                                UPDATE ProductInWarehouse
                                SET amount = amount + %s
                                WHERE warehouse_id = %s AND product_id = %s
                            """, (quantity, to_warehouse, product_id))
                        else:
                            db.cursor.execute("""
                                INSERT INTO ProductInWarehouse (warehouse_id, product_id, amount)
                                VALUES (%s, %s, %s)
                            """, (to_warehouse, product_id, quantity))

                db.conn.commit()
                self.changes.clear()
                QMessageBox.information(self, "Успех", "Изменения успешно сохранены!")
        except Exception as e:
            if db.conn:
                db.conn.rollback()
            logging.error(f"Error saving changes: {e}")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при сохранении: {e}")

    def make_table_read_only(self):
        for row in range(self.warehouse_table.rowCount()):
            for col in range(self.warehouse_table.columnCount()):
                item = self.warehouse_table.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        for row in range(self.move_table.rowCount()):
            for col in range(self.move_table.columnCount()):
                item = self.move_table.item(row, 0)
                if item:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)

    def edit_item(self, row, column):
        logging.debug(f"Opening EditDialog for row {row}, column {column}")
        dialog = EditDialog(self.move_table, row, column)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.move_table.setItem(row, 0, item)  # Обновляем данные в таблице
            QMessageBox.information(self, 'Успех', 'Данные успешно обновлены!')