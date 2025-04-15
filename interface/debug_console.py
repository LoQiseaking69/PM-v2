from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLineEdit, QHBoxLayout
from PyQt5.QtCore import Qt


class DebugConsole(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🛠 Debug Console")
        self.setMinimumSize(800, 400)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Log output area
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.layout.addWidget(self.log_output)

        # Command input + Send button
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command (e.g., start, stop, pause)...")
        self.command_input.returnPressed.connect(self.send_command)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_command)

        command_layout = QHBoxLayout()
        command_layout.addWidget(self.command_input)
        command_layout.addWidget(self.send_btn)
        self.layout.addLayout(command_layout)

        # Clear log button
        self.clear_btn = QPushButton("Clear Console")
        self.clear_btn.clicked.connect(self.log_output.clear)
        self.layout.addWidget(self.clear_btn)

        # Optional: assign a callback to handle commands
        self.on_command_entered = None

    def append_message(self, message: str):
        self.log_output.append(message)

    def send_command(self):
        command = self.command_input.text().strip()
        if command:
            self.append_message(f"> {command}")
            if self.on_command_entered:
                self.on_command_entered(command)
            else:
                self.append_message("No command handler attached.")
            self.command_input.clear()