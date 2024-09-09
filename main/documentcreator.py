import subprocess
import os
import datetime
from docx import Document
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel, QMessageBox

class DocumentCreator(QDialog):
    def __init__(self, template_name, data, parent=None):
        super().__init__(parent)
        self.template_name = template_name
        self.data = data

        self.setWindowTitle("Печать Документов")

        # Создание виджетов
        self.message_label = QLabel(
            f"Вы хотите напечатать документы?\n\nШаблон: {self.template_name}\nДанные: {self.data}")

        self.yes_button = QPushButton("Да")
        self.no_button = QPushButton("Нет")

        # Установка макетов
        layout = QVBoxLayout()
        layout.addWidget(self.message_label)
        layout.addWidget(self.yes_button)
        layout.addWidget(self.no_button)

        self.setLayout(layout)

        # Связывание кнопок с действиями
        self.yes_button.clicked.connect(self.onYes)
        self.no_button.clicked.connect(self.onNo)

    def fill_template(self):
        # Открываем шаблон документа
        doc = Document(self.template_name)

        # Проходим по всем параграфам в документе
        for paragraph in doc.paragraphs:
            # Проверяем наличие плейсхолдеров и заменяем их на данные
            for key, value in self.data.items():
                if key in paragraph.text:
                    paragraph.text = paragraph.text.replace(key, value)

        # Путь к папке для сохранения
        docs_folder = 'docs'
        if not os.path.exists(docs_folder):
            os.makedirs(docs_folder)

        output_path = os.path.join(docs_folder, self.generate_unique_filename(self.template_name))
        # Сохраняем заполненный документ
        doc.save(output_path)

        # Открываем документ с помощью системного приложения
        self.open_file(output_path)

    def generate_unique_filename(self, base_name):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name_without_extension = os.path.splitext(base_name)[0]
        return f"{base_name_without_extension}_{timestamp}.docx"

    def open_file(self, path):
        try:
            if os.name == 'nt':  # Для Windows
                os.startfile(path)
            elif os.name == 'posix':  # Для Unix-подобных систем
                subprocess.call(['xdg-open', path])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл: {e}")

    def onYes(self):
        self.fill_template()
        self.close()

    def onNo(self):
        self.close()