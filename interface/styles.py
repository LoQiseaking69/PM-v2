SCIFI_STYLE = """
/* === Base QWidget === */
QWidget {
    background-color: #0e0e0e;
    color: #00ffee;
    font-family: 'Consolas', monospace;
    font-size: 16px;
}

/* === Labels === */
QLabel {
    color: #00ffcc;
    font-weight: bold;
    font-size: 16px;
    padding: 2px 0;
    margin: 4px 0;
}

/* === Text Inputs === */
QLineEdit, QComboBox, QSpinBox {
    background-color: #1a1a1a;
    border: 1px solid #00ffaa;
    padding: 6px 10px;
    color: #ffffff;
    border-radius: 6px;
    font-size: 16px;
    min-height: 38px;
    min-width: 320px;
    selection-background-color: #004c4c;
}

QTextEdit {
    background-color: #111111;
    border: 1px solid #00ffaa;
    padding: 8px 10px;
    font-size: 15px;
    line-height: 1.5em;
    min-height: 240px;
}

/* === Buttons === */
QPushButton {
    background-color: #002222;
    color: #00ffaa;
    border: 1px solid #00ffaa;
    padding: 8px 16px;
    font-weight: bold;
    border-radius: 6px;
    font-size: 16px;
    min-width: 180px;
    margin-top: 6px;
}

QPushButton:hover {
    background-color: #004444;
    border: 1px solid #00ffff;
    color: #00ffff;
}

/* === Group Boxes === */
QGroupBox {
    border: 1px solid #00ffaa;
    margin-top: 16px;
    margin-bottom: 12px;
    padding: 14px;
    border-radius: 6px;
    background-color: #111111;
}

QGroupBox:title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    color: #00ffff;
    font-size: 15px;
}

/* === Scrollbars === */
QScrollBar:vertical, QScrollBar:horizontal {
    background: #1a1a1a;
    border: 1px solid #00ffaa;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #00ffaa;
    border-radius: 3px;
}

QScrollBar::handle:hover {
    background: #00ffff;
}

/* === Dialogs === */
QDialog {
    background-color: #0e0e0e;
    border: 2px solid #00ffaa;
    padding: 16px;
}
"""