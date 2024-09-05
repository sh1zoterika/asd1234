import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit, QDialog
)
from PyQt5 import QtCore, QtGui, QtWidgets
from psycopg2 import OperationalError, sql
from Database import Database
from EditDialog import EditDialog  # Импортируем EditDialog

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class BaseWindow(QMainWindow):
    def __init__(self, title, table_headers, user, password, table_name):
        super().__init__()
        self.table_name = table_name
        self.user = user
        self.password = password
        self.setWindowTitle(title)
        self.setGeometry(600, 200, 800, 600)

        layout = QVBoxLayout()

        self.table_widget = QTableWidget()
        layout.addWidget(self.table_widget)
        self.table_widget.cellDoubleClicked.connect(self.edit_item)  # Добавляем обработчик двойного клика

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

    def edit_item(self, row, column):
        logging.debug(f"Opening EditDialog for row {row}, column {column}")
        dialog = EditDialog(self.table_widget, row)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            logging.debug(f"Collected data: {data}")
            for col, value in enumerate(data):
                self.table_widget.setItem(row, col + 1, QTableWidgetItem(value))  # Обновляем данные в таблице
            self.changes.append(('update', row, data))
            QMessageBox.information(self, 'Успех', 'Данные успешно обновлены!')

    def update_table(self):
        try:
            with Database(self.user, self.password) as db:
                db.update_id(self.table_name)
                db.cursor.execute(self.get_select_query())
                items = db.cursor.fetchall()
                self.table_widget.setRowCount(len(items))
                self.table_widget.setColumnCount(len(self.table_headers))
                self.table_widget.setHorizontalHeaderLabels(self.table_headers)
                for i, item in enumerate(items):
                    for j, value in enumerate(item):
                        self.table_widget.setItem(i, j, QTableWidgetItem(str(value)))
        except Exception as e:
            logging.error(f"Error loading data: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке данных: {e}')

    def add_item(self):
        dialog = EditDialog(self.table_widget)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                with Database(self.user, self.password) as db:
                    new_id = db.get_next_id(self.table_name)
                    logging.debug(f"Inserting new row with ID {new_id} and data: {data}")
                    db.cursor.execute(self.get_insert_query(), (new_id, *data))
                    db.conn.commit()
                    self.update_table()
                    QMessageBox.information(self, 'Успех', 'Элемент успешно добавлен!')
            except Exception as e:
                logging.error(f"Error adding row: {e}")
                QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка при добавлении ряда: {e}')

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
            with Database(self.user, self.password) as db:
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
            logging.error(f"Error saving changes: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка при сохранении: {e}')
        finally:
            if db.conn:
                db.conn.close()
                logging.debug("Database connection closed.")

    def valid(self, new_text, column):
        return True

    def get_select_query(self):
        raise NotImplementedError

    def get_insert_query(self):
        raise NotImplementedError

    def get_delete_query(self):
        raise NotImplementedError

    def get_update_query(self):
        raise NotImplementedError
