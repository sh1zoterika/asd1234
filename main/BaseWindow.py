import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit
)
from PyQt5 import QtCore, QtGui, QtWidgets
from psycopg2 import OperationalError, sql
from Database import Database
from ChangeDialog import ChangeDialog


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
        self.table_widget.cellDoubleClicked.connect(self.changer)

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
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке данных: {e}')

    def add_item(self):
        try:
            with Database(self.user, self.password) as db:
                row_count = self.table_widget.rowCount()
                self.table_widget.insertRow(row_count)
                new_id = db.get_next_id(self.table_name)
                new_id_item = QtWidgets.QTableWidgetItem(str(new_id))
                self.table_widget.setItem(row_count, 0, new_id_item)
                for column in range(self.table_widget.columnCount()):
                    item = self.table_widget.item(row_count, column)
                    if item is None:
                        item = QtWidgets.QTableWidgetItem()
                        self.table_widget.setItem(row_count, column, item)
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                query_list = []
                query_list.append(int(new_id))
                for _ in range(len(self.table_headers) - 1):
                    query_list.append('')
                self.changes.append(('insert', None, query_list))
                QMessageBox.information(self, 'Успех', 'Элемент успешно добавлен!')
        except Exception as e:
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
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка при сохранении: {e}')

    '''def edit_cell(self, row, column):         Заменено на changer
        old_item = self.table_widget.item(row, column)
        if old_item:
            old_value = old_item.text()
            new_value = self.table_widget.currentItem().text()

            if old_value != new_value:
                row_id_item = self.table_widget.item(row, 0)
                if row_id_item:
                    row_id = row_id_item.text()
                    item_data = [self.table_widget.item(row, i).text() for i in range(1, len(self.table_headers))]
                    self.changes.append(('update', row_id, item_data))'''

    def changer(self, row, column):
        if column != 0:
            item = self.table_widget.item(row, column)
            text = item.text() if item else ''
            dialog = ChangeDialog(text)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                new_text = str(dialog.get_text())
                if self.valid(new_text, column):
                    item_data = QtWidgets.QTableWidgetItem(new_text)
                    item_data.setFlags(item_data.flags() & ~QtCore.Qt.ItemIsEditable)
                    self.table_widget.setItem(row, column, item_data)
                    self.changes.append(('update', row, item_data))
                else:
                    QMessageBox.warning(self, 'Ошибка', 'Текст не валиден')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Нельзя менять ID.')


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