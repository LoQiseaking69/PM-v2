from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QFormLayout, QComboBox,
    QTextEdit, QLineEdit, QGroupBox, QHBoxLayout, QTabWidget,
    QGridLayout, QSizePolicy, QFrame, QApplication
)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from interface.styles import SCIFI_STYLE
from interface.debug_console import DebugConsole
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from web3 import Web3
import configparser
import os
import logging

# Configure logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

log = logging.getLogger("ProfitMask")
log.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(os.path.join(LOG_DIR, "activity.log"))
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

log.addHandler(file_handler)
log.addHandler(console_handler)

class SciFiGUI(QWidget):
    start_trading = pyqtSignal(dict)
    export_requested = pyqtSignal(str, str)
    export_all = pyqtSignal()
    set_export_interval = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProfitMask - SciFi Ops Console")
        self.setStyleSheet(SCIFI_STYLE)
        self.resize(720, 540)
        self._center_window()
        self.chart_data = []
        self.cycles = []
        self.creds_visible = True
        self.thread_alive = False
        self.debug_console = DebugConsole(self)
        self._init_ui()
        self._init_status_polling()

    def _center_window(self):
        frame = self.frameGeometry()
        center = QApplication.desktop().availableGeometry().center()
        frame.moveCenter(center)
        self.move(frame.topLeft())

    def _init_ui(self):
        tabs = QTabWidget()
        tabs.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        tabs.addTab(self._build_strategy_tab(), "🧠 Strategy")
        tabs.addTab(self._build_credentials_tab(), "🛡️ Credentials")
        tabs.addTab(self._build_export_tab(), "🧾 Export")
        tabs.addTab(self._build_debug_tab(), "🛠 Console")
        tabs.addTab(self._build_log_tab(), "📋 Log")
        tabs.addTab(self._build_chart_tab(), "📈 Live Profit Chart")

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addWidget(self._build_status_bar())
        layout.addWidget(tabs)
        self.setLayout(layout)

    def _standard_input(self, placeholder="", is_password=False):
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setMinimumWidth(160)
        field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if is_password:
            field.setEchoMode(QLineEdit.Password)
        return field

    def _build_strategy_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        strategy_group = QGroupBox("🚀 Strategy Configuration")
        strategy_layout = QFormLayout()

        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["signal", "profit"])
        strategy_layout.addRow(QLabel("Mode:"), self.mode_selector)

        self.slippage_selector = QComboBox()
        self.slippage_selector.addItems(["0.001", "0.005", "0.01", "0.02"])
        strategy_layout.addRow(QLabel("Slippage:"), self.slippage_selector)

        self.fee_selector = QComboBox()
        self.fee_selector.addItems(["500", "3000", "10000"])
        strategy_layout.addRow(QLabel("Fee Tier (gwei):"), self.fee_selector)

        self.network_selector = QComboBox()
        self.network_selector.addItems(["mainnet", "goerli", "sepolia", "testnet"])
        strategy_layout.addRow(QLabel("Network:"), self.network_selector)

        self.token_entry = self._standard_input("Override Token Address (optional)")
        strategy_layout.addRow(QLabel("Token Override:"), self.token_entry)

        strategy_group.setLayout(strategy_layout)
        layout.addWidget(strategy_group)

        self.start_btn = QPushButton("🔥 ENGAGE STRATEGY")
        self.start_btn.clicked.connect(self.start_clicked)
        layout.addWidget(self.start_btn)

        tab.setLayout(layout)
        return tab
        
    def _build_credentials_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.creds_group = QGroupBox("🔐 Wallet & Node Credentials")
        creds_layout = QGridLayout()

        self.pk_input = self._standard_input("Enter Private Key", is_password=True)
        self.wallet_input = self._standard_input("Enter Wallet Address")
        self.infura_input = self._standard_input("Enter Infura HTTPS URL")
        self.router_input = self._standard_input("Uniswap Router Address")
        self.oracle_input = self._standard_input("Oracle Contract Address")

        toggle_btn = QPushButton("👁 Show")
        toggle_btn.setFixedWidth(55)
        toggle_btn.clicked.connect(self._toggle_private_key_visibility)

        creds_layout.addWidget(QLabel("Private Key:"), 0, 0)
        creds_layout.addWidget(self.pk_input, 0, 1)
        creds_layout.addWidget(toggle_btn, 0, 2)

        creds_layout.addWidget(QLabel("Wallet Address:"), 1, 0)
        creds_layout.addWidget(self.wallet_input, 1, 1, 1, 2)

        creds_layout.addWidget(QLabel("Infura URL:"), 2, 0)
        creds_layout.addWidget(self.infura_input, 2, 1, 1, 2)

        creds_layout.addWidget(QLabel("Router Address:"), 3, 0)
        creds_layout.addWidget(self.router_input, 3, 1, 1, 2)

        creds_layout.addWidget(QLabel("Oracle Address:"), 4, 0)
        creds_layout.addWidget(self.oracle_input, 4, 1, 1, 2)

        self.creds_group.setLayout(creds_layout)
        layout.addWidget(self.creds_group)

        cred_btns = QHBoxLayout()
        creds_toggle = QPushButton("Hide Credentials")
        autofill_btn = QPushButton("Load from config.ini")
        save_btn = QPushButton("Save to config.ini")
        creds_toggle.clicked.connect(self._toggle_creds_visibility)
        autofill_btn.clicked.connect(self._load_config_to_fields)
        save_btn.clicked.connect(self._save_config_from_fields)
        cred_btns.addWidget(creds_toggle)
        cred_btns.addWidget(autofill_btn)
        cred_btns.addWidget(save_btn)
        layout.addLayout(cred_btns)

        tab.setLayout(layout)
        return tab

    def _build_export_tab(self):
        tab = QWidget()
        layout = QHBoxLayout()

        export_all_btn = QPushButton("📁 Export All")
        export_csv_btn = QPushButton("📄 Export CSV")
        export_json_btn = QPushButton("🧾 Export JSON")

        export_all_btn.clicked.connect(lambda: self.export_all.emit())
        export_csv_btn.clicked.connect(lambda: self.export_requested.emit("profits", "csv"))
        export_json_btn.clicked.connect(lambda: self.export_requested.emit("profits", "json"))

        layout.addWidget(export_all_btn)
        layout.addWidget(export_csv_btn)
        layout.addWidget(export_json_btn)

        tab.setLayout(layout)
        return tab

    def _build_debug_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        open_btn = QPushButton("🛠 Open Debug Console")
        open_btn.clicked.connect(lambda: self.debug_console.show())
        layout.addWidget(open_btn)
        tab.setLayout(layout)
        return tab

    def _build_log_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("📋 Tactical Log Output:"))
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)
        tab.setLayout(layout)
        return tab

    def _build_chart_tab(self):
        self.chart_tab = QWidget()
        chart_layout = QVBoxLayout()
        self.chart_fig = Figure()
        self.chart_canvas = FigureCanvas(self.chart_fig)
        self.chart_ax = self.chart_fig.add_subplot(111)
        chart_layout.addWidget(self.chart_canvas)
        self.chart_tab.setLayout(chart_layout)
        return self.chart_tab

    def _init_status_polling(self):
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._refresh_status_bar)
        self._status_timer.start(5000)

    def _build_status_bar(self):
        self.status_wallet = QLabel("Wallet: [Not Set]")
        self.status_network = QLabel("Network: [Unknown]")
        self.status_balance = QLabel("ETH: ?")
        self.status_thread = QLabel("Thread: 🔴 Stopped")

        for widget in [self.status_wallet, self.status_network, self.status_balance, self.status_thread]:
            widget.setFrameStyle(QFrame.Panel | QFrame.Sunken)
            widget.setStyleSheet("padding: 5px; font-weight: bold;")
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self.status_wallet)
        layout.addWidget(self.status_network)
        layout.addWidget(self.status_balance)
        layout.addWidget(self.status_thread)

        container = QWidget()
        container.setLayout(layout)
        return container

    def _refresh_status_bar(self):
        addr = self.wallet_input.text().strip()
        provider = self.infura_input.text().strip()
        chain = self.network_selector.currentText()
        self.status_network.setText(f"Network: {chain}")

        if Web3.is_address(addr):
            self.status_wallet.setText(f"Wallet: {Web3.to_checksum_address(addr)}")
        else:
            self.status_wallet.setText("Wallet: ❌ Invalid")

        try:
            w3 = Web3(Web3.HTTPProvider(provider))
            eth = w3.eth.get_balance(addr)
            self.status_balance.setText(f"ETH: {w3.fromWei(eth, 'ether'):.4f}")
        except Exception:
            self.status_balance.setText("ETH: ❌")

        self.status_thread.setText("Thread: 🟢 Running" if self.thread_alive else "Thread: 🔴 Stopped")

    def _toggle_private_key_visibility(self):
        self.pk_input.setEchoMode(
            QLineEdit.Normal if self.pk_input.echoMode() == QLineEdit.Password else QLineEdit.Password
        )

    def _toggle_creds_visibility(self):
        self.creds_visible = not self.creds_visible
        self.pk_input.setVisible(self.creds_visible)
        self.wallet_input.setVisible(self.creds_visible)
        self.infura_input.setVisible(self.creds_visible)
        self.router_input.setVisible(self.creds_visible)
        self.oracle_input.setVisible(self.creds_visible)

    def _save_config_from_fields(self):
        config = configparser.ConfigParser()
        config.read('config.ini')

        config['Wallet'] = {
            'PrivateKey': self.pk_input.text(),
            'WalletAddress': self.wallet_input.text(),
            'InfuraURL': self.infura_input.text(),
            'RouterAddress': self.router_input.text(),
            'OracleAddress': self.oracle_input.text(),
        }

        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    def _load_config_to_fields(self):
        config = configparser.ConfigParser()
        config.read('config.ini')

        self.pk_input.setText(config.get('Wallet', 'PrivateKey'))
        self.wallet_input.setText(config.get('Wallet', 'WalletAddress'))
        self.infura_input.setText(config.get('Wallet', 'InfuraURL'))
        self.router_input.setText(config.get('Wallet', 'RouterAddress'))
        self.oracle_input.setText(config.get('Wallet', 'OracleAddress'))

    def start_clicked(self):
        config = {
            'mode': self.mode_selector.currentText(),
            'slippage': self.slippage_selector.currentText(),
            'fee': self.fee_selector.currentText(),
            'network': self.network_selector.currentText(),
            'token_override': self.token_entry.text(),
        }
        self.start_trading.emit(config)
        
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = SciFiGUI()
    window.show()
    sys.exit(app.exec_())
