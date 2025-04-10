from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton


class DebugConsole(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🛠 Debug Console")
        self.setMinimumSize(800, 400)

        self.layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        self.clear_btn = QPushButton("Clear Console")
        self.clear_btn.clicked.connect(self.log_output.clear)

        self.layout.addWidget(self.log_output)
        self.layout.addWidget(self.clear_btn)
        self.setLayout(self.layout)

    def append_message(self, message: str):
        self.log_output.append(message)
