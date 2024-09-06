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
from EditDialog import EditDialog
from PyQt5 import QtCore


class CurrentOrderWindow(QMainWindow):
    def __init__(self, parent=None, user=None, password=None):
        self.user = user
        self.password = password
        super().__init__(parent)
        self.setWindowTitle('Текущие заказы')
        self.setGeometry(600, 200, 800, 600)

        layout = QVBoxLayout()

        self.table_widget = QTableWidget()
        layout.addWidget(self.table_widget)
        self.table_widget.cellDoubleClicked.connect(self.edit_item)  # Добавляем обработчик двойного клика

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
            with Database(self.user, self.password) as db:
                db.cursor.execute("""
                    SELECT Orders.id, Clients.name, Orders.price, Orders.date, Orders.status
                    FROM Orders
                    JOIN Clients ON Orders.client_id = Clients.id
                    WHERE Orders.status = 'В процессе'
                """)
                orders = db.cursor.fetchall()

            self.table_widget.setRowCount(len(orders))
            self.table_widget.setColumnCount(5)
            self.table_widget.setHorizontalHeaderLabels(["ID", "Клиент", "Цена", "Дата", "Статус"])
            for i, order in enumerate(orders):
                self.table_widget.setItem(i, 0, QTableWidgetItem(str(order[0])))
                self.table_widget.setItem(i, 1, QTableWidgetItem(order[1]))
                self.table_widget.setItem(i, 2, QTableWidgetItem(str(order[2])))
                self.table_widget.setItem(i, 3, QTableWidgetItem(order[3].strftime('%Y-%m-%d %H:%M:%S')))
                self.table_widget.setItem(i, 4, QTableWidgetItem(order[4]))
            self.make_table_read_only()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {e}")

    def add_order(self):
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)
        self.table_widget.setItem(row_position, 0, QTableWidgetItem(''))  # ID будет автоматически присвоен
        self.table_widget.setItem(row_position, 1, QTableWidgetItem('Новый клиент'))
        self.table_widget.setItem(row_position, 2, QTableWidgetItem('0'))  # Начальная цена
        self.table_widget.setItem(row_position, 3, QTableWidgetItem('2023-01-01 00:00:00'))  # Начальная дата
        self.table_widget.setItem(row_position, 4, QTableWidgetItem('В процессе'))  # Начальный статус
        self.changes.append(('insert', None, ['Новый клиент', '0', '2023-01-01 00:00:00', 'В процессе']))
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
            with Database(self.user, self.password) as db:
                for change in self.changes:
                    change_type, row_id, row_data = change
                    if change_type == 'insert':
                        db.cursor.execute(
                            "INSERT INTO Orders (client_id, price, date, status) VALUES (%s, %s, %s, %s)",
                            (row_data[0], row_data[1], row_data[2], row_data[3])
                        )
                    elif change_type == 'delete':
                        db.cursor.execute(
                            "DELETE FROM Orders WHERE id = %s",
                            (row_id,)
                        )
                    elif change_type == 'update':
                        db.cursor.execute(
                            "UPDATE Orders SET client_id = %s, price = %s, date = %s, status = %s WHERE id = %s",
                            (row_data[0], row_data[1], row_data[2], row_data[3], row_id)
                        )

                db.conn.commit()
                self.changes.clear()
                QMessageBox.information(self, "Успех", "Изменения успешно сохранены!")
        except Exception as e:
            if db.conn:
                db.conn.rollback()
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при сохранении: {e}")

    def edit_item(self, row, column):
        logging.debug(f"Opening EditDialog for row {row}, column {column}")
        dialog = EditDialog(self.table_widget, row)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            logging.debug(f"Collected data for update: {data}")
            for col, value in enumerate(data):
                self.table_widget.setItem(row, col + 1, QTableWidgetItem(value))  # Обновляем данные в таблице
            self.changes.append(('update', self.table_widget.item(row, 0).text(), data))
            QMessageBox.information(self, 'Успех', 'Данные успешно обновлены!')
    
    def make_table_read_only(self):
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)