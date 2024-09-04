import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit, QDialog
)
from psycopg2 import OperationalError, sql
from BaseWindow import BaseWindow
from Database import Database
from EditDialog import EditDialog  # Импортируем EditDialog

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ClientWindow(BaseWindow):
    def __init__(self, user, password):
        self.db = Database(user, password)
        column_names = self.db.get_column_names('clients')
        super().__init__('Клиенты', column_names, user, password, 'clients')

        self.view_orders_button = QPushButton('Посмотреть заказы')
        self.view_orders_button.clicked.connect(self.view_orders)
        layout = self.centralWidget().layout()
        layout.addWidget(self.view_orders_button)

        self.table_widget.cellDoubleClicked.connect(self.edit_item)  # Добавляем обработчик двойного клика

    def view_orders(self):
        pass

    def get_select_query(self):
        return """
            SELECT id, name, orders, info, phonenumber, address
            FROM Clients
        """

    def get_insert_query(self):
        return """
            INSERT INTO Clients (id, name, orders, info, phonenumber, address)
            VALUES (%s, %s, %s, %s, %s, %s)
        """


    def get_delete_query(self):
        return "DELETE FROM Clients WHERE id = %s"

    def get_update_query(self):
        return """
            UPDATE Clients SET name = %s, orders = %s, info = %s, phonenumber = %s, address = %s
            WHERE id = %s
        """

    def edit_item(self, row, column):
        logging.debug(f"Opening EditDialog for row {row}, column {column}")
        dialog = EditDialog(self.table_widget, row)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            for col, value in enumerate(data):
                self.table_widget.setItem(row, col + 1, QTableWidgetItem(value))  # Обновляем данные в таблице
            self.save_changes(row, data)

    def save_changes(self, row, data):
        try:
            with Database(self.user, self.password) as db:
                row_id = self.table_widget.item(row, 0).text()
                logging.debug(f"Updating row {row_id} with data: {data}")
                db.cursor.execute(self.get_update_query(), (*data, row_id))
                db.conn.commit()
                QMessageBox.information(self, 'Успех', 'Изменения успешно сохранены!')
        except Exception as e:
            logging.error(f"Error saving changes: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка при сохранении: {e}')

