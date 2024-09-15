from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, 
    QTableWidget, QTableWidgetItem, QLabel, QLineEdit
)
from PyQt5 import QtCore
from Database import Database
from AddProductWindow import AddProductWindow


class EditOrderDialog(QDialog):
    def __init__(self, user, password, order_id, parent=None):
        super().__init__(parent)
        self.order_id = order_id
        self.user = user
        self.password = password
        self.setWindowTitle("Изменение заказа")
        self.setGeometry(600, 200, 800, 600)

        self.changes = []  # Для отслеживания изменений

        layout = QVBoxLayout()

        # Кнопка для добавления товаров
        self.add_button = QPushButton("Добавить товары")
        self.add_button.clicked.connect(self.open_add_product_window)
        layout.addWidget(self.add_button)

        # Раздел для поиска товаров
        search_layout = QHBoxLayout()
        self.search_label = QLabel("Поиск товара:")
        search_layout.addWidget(self.search_label)
        self.search_box = QLineEdit()
        search_layout.addWidget(self.search_box)
        self.search_button = QPushButton("Поиск")
        self.search_button.clicked.connect(self.search_items)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # Таблица для отображения товаров в заказе
        self.table_widget = QTableWidget()
        layout.addWidget(self.table_widget)

        # Кнопки для удаления товаров и подтверждения изменений
        button_layout = QHBoxLayout()

        self.delete_button = QPushButton("Удалить товары из заказа")
        self.delete_button.clicked.connect(self.delete_item)
        button_layout.addWidget(self.delete_button)

        self.confirm_button = QPushButton("Подтвердить")
        self.confirm_button.clicked.connect(self.save_changes)
        button_layout.addWidget(self.confirm_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.update_table()

    def update_table(self):
        try:
            with Database(self.user, self.password) as db:
                products = db.get_products_by_order(self.order_id)
                self.table_widget.setRowCount(len(products))
                self.table_widget.setColumnCount(5)
                headers = ['Product ID', 'Product Name', 'Amount', 'Price', 'Warehouse ID']
                self.table_widget.setHorizontalHeaderLabels(headers)
                for i, (id, name, amount, price, warehouse_id) in enumerate(products):
                    self.table_widget.setItem(i, 0, QTableWidgetItem(str(id)))
                    self.table_widget.setItem(i, 1, QTableWidgetItem(str(name)))
                    self.table_widget.setItem(i, 2, QTableWidgetItem(str(amount)))
                    self.table_widget.setItem(i, 3, QTableWidgetItem(str(price)))
                    self.table_widget.setItem(i, 4, QTableWidgetItem(str(warehouse_id)))
                self.make_table_read_only()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении таблицы: {e}")

    def open_add_product_window(self):
        try:
            self.add_product_window = AddProductWindow(self.order_id, self.user, self.password, parent=self)
            self.add_product_window.show()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при открытии окна добавления товара: {e}')

    def save_changes(self):
        try:
            with Database(self.user, self.password) as db:
                for change in self.changes:
                    change_type, product_id, order_id, warehouse_id, amount = change
                    if change_type == 'delete':
                        db.cursor.execute(
                            'DELETE FROM Order_Items WHERE product_id = %s AND order_id = %s AND warehouse_id = %s',
                            (product_id, order_id, warehouse_id))
                        db.cursor.execute('SELECT * FROM ProductInWarehouse WHERE product_id = %s and warehouse_id = %s', (product_id, warehouse_id))
                        result = db.cursor.fetchall()
                        if result:
                            db.cursor.execute('UPDATE ProductInWarehouse SET amount = amount + %s WHERE product_id = %s and warehouse_id = %s',
                                              (amount, product_id, warehouse_id))
                        else:
                            db.cursor.execute('INSERT INTO ProductInWarehouse (warehouse_id, product_id, amount) VALUES (%s, %s, %s)', (warehouse_id, product_id, amount))
                db.conn.commit()
                self.changes.clear()
                QMessageBox.information(self, 'Успех', 'Изменения успешно сохранены!')
        except Exception as e:
            if db.conn:
                db.conn.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка при сохранении: {e}')

    def make_table_read_only(self):
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)

    def delete_item(self):
        selected_row = self.table_widget.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, выберите элемент для удаления.')
            return

        id_item = self.table_widget.item(selected_row, 0).text()
        warehouse_id = self.table_widget.item(selected_row, 4).text()
        amount = int(self.table_widget.item(selected_row, 2).text())

        self.changes.append(('delete', id_item, self.order_id, warehouse_id, amount))
        self.table_widget.removeRow(selected_row)
        QMessageBox.information(self, 'Успех', 'Элемент подготовлен к удалению. Нажмите "Подтвердить" для сохранения изменений.')

    def search_items(self):
        search_text = self.search_box.text().lower()  # Получение текста из поля ввода

        try:
            with Database(self.user, self.password) as db:
                db.cursor.execute("""
                SELECT p.id, p.name, oi.amount, oi.price, oi.warehouse_id
                FROM Order_items oi 
                JOIN Products p ON oi.product_id = p.id 
                WHERE oi.order_id = %s AND LOWER(p.name) LIKE %s
                """, (self.order_id, '%' + search_text + '%'))
                products = db.cursor.fetchall()

                self.table_widget.setRowCount(len(products))
                self.table_widget.setColumnCount(5)

                headers = ['Product ID', 'Product Name', 'Amount', 'Price', 'Warehouse ID']
                self.table_widget.setHorizontalHeaderLabels(headers)

                for i, product in enumerate(products):
                    for j in range(len(product)):
                        self.table_widget.setItem(i, j, QTableWidgetItem(str(product[j])))

                self.make_table_read_only()  # Делает таблицу доступной только для чтения
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка при поиске: {e}')