from PyQt5.QtWidgets import QDialog, QFormLayout, QDateEdit, QSpinBox, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import QDate, QRegExp
from PyQt5.QtGui import QRegExpValidator
import logging

class EditDialog(QDialog):
    def __init__(self, table_widget, row=None, column=None, max_value=None):
        super().__init__()
        self.setWindowTitle("Edit Data")
        self.table_widget = table_widget
        self.row = row
        self.column = column
        self.max_value = max_value

        layout = QFormLayout()

        self.inputs = []
        self.widgets = {}

        if column is not None:
            label = table_widget.horizontalHeaderItem(column).text()
            data_type = self.get_data_type(label)
            widget = self.create_widget(data_type, label)

            if row is not None:
                if isinstance(widget, QDateEdit):
                    widget.setDate(QDate.fromString(table_widget.item(row, column).text(), 'yyyy-MM-dd'))
                elif isinstance(widget, QSpinBox):
                    widget.setValue(int(table_widget.item(row, column).text()))
                else:
                    widget.setText(table_widget.item(row, column).text())

            layout.addRow(label, widget)
            self.inputs.append(widget)
            self.widgets[label] = widget
        else:
            for col in range(table_widget.columnCount()):
                label = table_widget.horizontalHeaderItem(col).text()
                if label == 'id':
                    continue
                data_type = self.get_data_type(label)
                widget = self.create_widget(data_type, label)
                if row is not None:
                    if isinstance(widget, QDateEdit):
                        widget.setDate(QDate.fromString(table_widget.item(row, col).text(), 'yyyy-MM-dd'))
                    elif isinstance(widget, QSpinBox):
                        widget.setValue(int(table_widget.item(row, col).text()))
                    else:
                        widget.setText(table_widget.item(row, col).text())

                layout.addRow(label, widget)
                self.inputs.append(widget)
                self.widgets[label] = widget

        self.setLayout(layout)

        self.accept_button = QPushButton("OK")
        self.accept_button.clicked.connect(self.validate_and_accept)
        layout.addWidget(self.accept_button)

        self.reject_button = QPushButton("Cancel")
        self.reject_button.clicked.connect(self.reject)
        layout.addWidget(self.reject_button)

    def get_data_type(self, column_name):
        data_types = {
            'id': 'INTEGER',
            'name': 'VARCHAR',
            'article': 'VARCHAR',
            'lifetime': 'INT',
            'description': 'TEXT',
            'category': 'VARCHAR',
            'png_url': 'BYTEA',
            'address': 'ADDRESS',
            'geo_text': 'TEXT',
            'geo_coordinates': 'GEO_COORDINATES',
            'warehouse_id': 'INT',
            'product_id': 'INT',
            'amount': 'INT',
            'orders': 'TEXT',
            'info': 'TEXT',
            'phonenumber': 'PHONE',
            'client_id': 'INT',
            'price': 'INT',
            'date': 'TIMESTAMP',
            'status': 'VARCHAR',
            'order_id': 'INT',
            'full_name': 'FULL_NAME'
        }
        return data_types.get(column_name, 'VARCHAR')

    def create_widget(self, data_type, label):
        logging.debug(f"Creating widget for data type: {data_type}")
        if data_type == 'DATE' or data_type == 'TIMESTAMP':
            widget = QDateEdit()
            widget.setCalendarPopup(True)
            widget.setDate(QDate.currentDate())
        elif data_type == 'INT':
            widget = QSpinBox()
            widget.setMaximum(999999999)
        elif data_type == 'REAL':
            widget = QLineEdit()
            reg_exp = QRegExp(r'^\d+(\.\d{1,4})?$')
            validator = QRegExpValidator(reg_exp)
            widget.setValidator(validator)
        elif data_type == 'PHONE':
            widget = QLineEdit()
            reg_exp = QRegExp(r'^\+?\d{10,15}$')  # Регулярное выражение для проверки номера телефона
            validator = QRegExpValidator(reg_exp)
            widget.setValidator(validator)
        elif data_type == 'GEO_COORDINATES':
            widget = QLineEdit()
            reg_exp = QRegExp(r'^-?\d{1,3}\.\d{1,6},\s*-?\d{1,3}\.\d{1,6}$')  # Регулярное выражение для проверки координат
            validator = QRegExpValidator(reg_exp)
            widget.setValidator(validator)
        elif data_type == 'ADDRESS':
            widget = QLineEdit()
            reg_exp = QRegExp(
                r'^[А-Яа-яЁё\w\s]+,\s*[А-Яа-яЁё\w\s]+,\s*[А-Яа-яЁё\w\s]+,\s*[А-Яа-яЁё\w\s\d]+$')  # Регулярное выражение для проверки адреса
            validator = QRegExpValidator(reg_exp)
            widget.setValidator(validator)
        elif data_type == 'FULL_NAME':
            widget = QLineEdit()
            reg_exp = QRegExp(r'^[А-Яа-яЁё\-]+(?:\s+[А-Яа-яЁё\-]+){1,2}$')  # Регулярное выражение для проверки ФИО
            validator = QRegExpValidator(reg_exp)
            widget.setValidator(validator)
        else:
            widget = QLineEdit()
            if self.max_value is not None:
                widget.setValidator(QRegExpValidator(QRegExp(r'^\d+$')))
        return widget

    def get_data(self):
        data = []
        for widget in self.inputs:
            if isinstance(widget, QDateEdit):
                data.append(widget.date().toString('yyyy-MM-dd'))
            elif isinstance(widget, QSpinBox):
                data.append(str(widget.value()))
            else:
                data.append(widget.text())
        logging.debug(f"Collected data: {data}")
        return data

    def validate_and_accept(self):
        data = self.get_data()
        if self.validate_data(data):
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "Некорректные данные! Попробуйте еще раз.")

    def validate_data(self, data):
        for i, item in enumerate(data):
            if item is None or item.strip() == "":
                return False
            if self.max_value is not None and int(item) > self.max_value:
                QMessageBox.warning(self, "Ошибка", f"Введенное количество превышает доступное на складе ({self.max_value}). Попробуйте еще раз.")
                return False
            
            # Проверка поля full_name
            if self.table_widget.horizontalHeaderItem(i).text() == 'full_name':
                if not re.match(r'^[А-Яа-яЁё\-]+(?:\s+[А-Яа-яЁё\-]+){1,2}$', item):
                    QMessageBox.warning(self, "Ошибка", "Некорректный формат ФИО. Ожидается: Фамилия Имя Отчество.")
                    return False
            
            # Проверка поля address
            if self.table_widget.horizontalHeaderItem(i).text() == 'address':
                if not re.match(r'^[А-Яа-яЁё\w\s]+,\s*[А-Яа-яЁё\w\s]+,\s*[А-Яа-яЁё\w\s]+,\s*[А-Яа-яЁё\w\s\d]+$', item):
                    QMessageBox.warning(self, "Ошибка", "Некорректный формат адреса. Ожидается: г.Город, ул.Улица, дом номер, квартира номер.")
                    return False

        return True
