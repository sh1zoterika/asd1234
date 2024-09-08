from PyQt5.QtWidgets import QDialog, QFormLayout, QDateEdit, QSpinBox, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import QDate, QRegExp
from PyQt5.QtGui import QRegExpValidator
import logging


class ProductEditDialog(QDialog):
    def __init__(self, table_widget, row=None):
        super().__init__()
        self.setWindowTitle("Изменение данных о товаре")
        self.table_widget = table_widget
        self.row = row
        
        layout = QFormLayout()
        
        self.inputs = []
        self.widgets = {}
        for col in range(table_widget.columnCount()):
            label = table_widget.horizontalHeaderItem(col).text()
            if label == 'id':
                continue  # Пропускаю поле id
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
        
        self.reject_button = QPushButton("Отмена")
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
            'price': 'REAL'
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
            reg_exp = QRegExp(r'^\d+(\.\d{1,4})?$')  # Регулярное выражение для проверки ввода с плавающей точкой
            validator = QRegExpValidator(reg_exp)
            widget.setValidator(validator)  # Ограничение по символам и только цифры с точкой
        elif data_type == 'VARCHAR' and label == 'article':
            widget = QLineEdit()
            reg_exp = QRegExp(r'^\d+$')  # Регулярное выражение для проверки ввода только цифр
            validator = QRegExpValidator(reg_exp)
            widget.setValidator(validator)  # Ограничение по символам и только цифры
        else:
            widget = QLineEdit()
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
        # Проверка на пустые строки и корректность данных
        for item in data:
            if item is None or item.strip() == "":
                return False
        return True
