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
from BaseWindow import BaseWindow
from ViewProductWindow import ViewProductWindow
from EditDialog import EditDialog

class WarehouseWindow(BaseWindow):
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.db = Database(user, password)
        column_names = self.db.get_column_names('warehouses')
        super().__init__('Склады', column_names, user, password, 'warehouses')

        self.view_products_button = QPushButton('Посмотреть товары на выбранном складе')
        self.view_products_button.clicked.connect(self.view_products)
        layout = self.centralWidget().layout()
        layout.addWidget(self.view_products_button)

    def view_products(self):
        # Получаем текущие выбранные элементы
        selected_items = self.table_widget.selectedItems()
        if selected_items:
            # Берем первую выбранную ячейку
            first_item = selected_items[0]
            # Получаем индекс строки этой ячейки
            row = first_item.row()
            # Получаем warehouseid из первой ячейки
            row_data = [self.table_widget.item(row, col).text() for col in range(self.table_widget.columnCount())]
            warehouseid = row_data[0]
            viewproduct = ViewProductWindow(self.user, self.password, warehouseid)
            viewproduct.exec_()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, выберите склад.')

    def get_select_query(self):
        return """
            SELECT id, name, address, geo_text, geo_coordinates
            FROM Warehouses
        """

    def get_insert_query(self):
        return """
            INSERT INTO Warehouses (id, name, address, geo_text, geo_coordinates)
            VALUES (%s, %s, %s, %s, %s)
        """

    def get_delete_query(self):
        return "DELETE FROM Warehouses WHERE id = %s"

    def get_update_query(self):
        return """
            UPDATE Warehouses SET name = %s, address = %s, geo_text = %s, geo_coordinates = %s
            WHERE id = %s
        """

    def add_item(self):
        dialog = EditDialog(self.table_widget)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            row_position = self.table_widget.rowCount()
            self.table_widget.insertRow(row_position)
            for col, value in enumerate(data):
                self.table_widget.setItem(row_position, col + 1, QTableWidgetItem(value))  # Обновляем данные в таблице
            self.update_ids()
            self.changes.append(('insert', None, data))
            QMessageBox.information(self, 'Успех', 'Элемент успешно добавлен!')

    def delete_item(self):
        selected_row = self.table_widget.currentRow()
        if selected_row >= 0:
            id_item = self.table_widget.item(selected_row, 0)
            if id_item:
                self.changes.append(('delete', id_item.text(), None))
            self.table_widget.removeRow(selected_row)
            self.update_ids()
            QMessageBox.information(self, 'Успех', 'Элемент успешно удалён!')

    def update_ids(self):
        for row in range(self.table_widget.rowCount()):
            self.table_widget.setItem(row, 0, QTableWidgetItem(str(row + 1)))

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
                        new_id = db.get_next_id('warehouses')
                        db.cursor.execute(self.get_insert_query(), (new_id, *row_data))
                    elif change_type == 'delete':
                        db.cursor.execute(self.get_delete_query(), (row_id,))
                    elif change_type == 'update':
                        db.cursor.execute(self.get_update_query(), row_data + [row_id])
                
                # Обновляем ID в базе данных
                for row in range(self.table_widget.rowCount()):
                    row_id = self.table_widget.item(row, 0).text()
                    db.cursor.execute("UPDATE Warehouses SET id = %s WHERE id = %s", (row + 1, row_id))

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
