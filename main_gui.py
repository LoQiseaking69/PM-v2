import configparser
import random
import sqlite3
import sys
import os

from PyQt5.QtWidgets import QApplication
from interface.gui import SciFiGUI
from core.controller import TradingThread

DB_PATH = "data/trading_log.db"

def load_profit_history(gui):
    try:
        if not os.path.exists(DB_PATH):
            gui.log("[INIT] No DB found; skipping profit history.")
            return
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT estimated_profit FROM profits ORDER BY id ASC")
        for row in cursor.fetchall():
            val = row[0]
            if isinstance(val, (int, float)):
                gui.update_chart(val)
        conn.close()
        gui.log("[INIT] Loaded historical profit data into chart.")
    except Exception as e:
        gui.log(f"[INIT ERROR] Could not load profit history: {e}")

def resolve_infura_url(network, current_url, project_id):
    if current_url and "https" in current_url:
        return current_url.strip()
    if not project_id:
        raise ValueError("Missing Infura project_id in config.ini under [WEB3]")
    chain_map = {
        "mainnet": "mainnet",
        "goerli": "goerli",
        "sepolia": "sepolia",
        "testnet": "goerli"
    }
    chain = chain_map.get(network, "mainnet")
    return f"https://{chain}.infura.io/v3/{project_id}"

def main():
    app = QApplication(sys.argv)
    window = SciFiGUI()
    thread = None
    load_profit_history(window)

    def log_intercept(msg):
        window.log(msg)
        if "PROFIT" in msg.upper():
            try:
                val = float(msg.split()[-1])
                if -1000 < val < 1000:
                    window.update_chart(val)
            except Exception:
                window.update_chart(random.uniform(-0.05, 0.05))

    def launch_trading(payload):
        nonlocal thread
        config = configparser.ConfigParser()
        config_path = "config/config.ini"
        runtime_path = "config/runtime_config.ini"

        if not os.path.exists(config_path):
            window.log("[ERROR] config/config.ini not found.")
            return
        config.read(config_path)

        config.set("GENERAL", "mode", payload.get("mode", "profit"))
        config.set("TRADING", "slippage", str(payload.get("slippage", 0.01)))
        config.set("TRADING", "fee_tier", str(payload.get("fee", 3000)))

        if payload.get("token_override"):
            config.set("TRADING", "token_address", payload["token_override"])

        config.set("WALLET", "private_key", payload.get("private_key", ""))
        config.set("WALLET", "wallet_address", payload.get("wallet_address", ""))

        network = payload.get("network", "mainnet")
        project_id = config.get("WEB3", "project_id", fallback="").strip()

        try:
            infura_url = resolve_infura_url(network, payload.get("infura_url", ""), project_id)
        except ValueError as e:
            window.log(f"[CONFIG ERROR] {e}")
            return

        config.set("WEB3", "infura_url", infura_url)
        config.set("DEX", "router_address", payload.get("router_address", ""))
        config.set("ORACLE", "address", payload.get("oracle_address", ""))
        config["NETWORK"] = {"chain": network}

        os.makedirs(os.path.dirname(runtime_path), exist_ok=True)
        with open(runtime_path, "w") as f:
            config.write(f)

        if thread:
            thread.stop()
            window.thread_alive = False

        thread = TradingThread(runtime_path)
        thread.log_signal.connect(log_intercept)
        thread.start()
        window.thread_alive = True

        window.log(f"Started {payload['mode']} strategy on {network}...")

        window.export_requested.connect(
            lambda table, ftype: thread.export_table_to_csv(table, f"{table}_export.csv")
            if ftype == "csv" else thread.export_table_to_json(table, f"{table}_export.json")
        )
        window.export_all.connect(thread.export_all_with_timestamp)
        window.set_export_interval.connect(lambda n: setattr(thread, "export_every_n_cycles", n))

    window.start_trading.connect(launch_trading)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()