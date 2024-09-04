import sys
import logging
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem,
    QLabel, QLineEdit,
)
from PyQt5.QtCore import pyqtSignal
from psycopg2 import OperationalError, sql

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class GlobalData:
    username = None
    password = None

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('PostgreSQL Login')
        self.setGeometry(700, 400, 300, 150)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()

        self.username_label = QLabel('Username:')
        self.username_input = QLineEdit()
        self.password_label = QLabel('Password:')
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton('Login')

        self.layout.addWidget(self.username_label)
        self.layout.addWidget(self.username_input)
        self.layout.addWidget(self.password_label)
        self.layout.addWidget(self.password_input)
        self.layout.addWidget(self.login_button)

        self.central_widget.setLayout(self.layout)

        self.login_button.clicked.connect(self.open_main_window)


    def open_main_window(self):
        user = self.username_input.text()
        password = self.password_input.text()
        GlobalData.username = user
        GlobalData.password = password
        try:
            from MainWindow import MainWindow
            self.main_window = MainWindow(user, password)
            self.main_window.show()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Main Window: {e}")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = LoginWindow()
    main_window.show()
    sys.exit(app.exec_())