import os
import csv
import json
import time
import logging
import sqlite3
import configparser
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal

from core.strategy import StrategyManager
from core.wallet import load_wallet
from core.utils import (
    init_web3, load_oracle, estimate_gas_price, execute_swap
)
from interface.dashboard import update_dashboard


class TradingThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, config_path, mode_override=None):
        super().__init__()
        self.config_path = config_path
        self.mode_override = mode_override
        self.running = True
        self.db_path = os.path.abspath("data/trading_log.db")
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_db()
        self.export_every_n_cycles = 10
        self._cycle_count = 0

    def _init_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT,
                action TEXT,
                delta REAL,
                gas_price INTEGER,
                tx_hash TEXT,
                success INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT,
                result TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS profits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT,
                estimated_profit REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def _log_trade(self, token, action, delta, gas_price, tx_hash, success):
        try:
            self.cursor.execute('''
                INSERT INTO trades (token, action, delta, gas_price, tx_hash, success)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (token, action, delta, gas_price, str(tx_hash), int(success)))
            self.conn.commit()
        except Exception as e:
            self.log_signal.emit(f"[DB ERROR] Failed to log trade: {e}")

    def _log_signal(self, mode, result):
        try:
            self.cursor.execute('''
                INSERT INTO signals (mode, result)
                VALUES (?, ?)
            ''', (mode, json.dumps(result)))
            self.conn.commit()
        except Exception as e:
            self.log_signal.emit(f"[DB ERROR] Failed to log signal: {e}")

    def _log_profit(self, token, estimated_profit):
        try:
            self.cursor.execute('''
                INSERT INTO profits (token, estimated_profit)
                VALUES (?, ?)
            ''', (token, estimated_profit))
            self.conn.commit()
        except Exception as e:
            self.log_signal.emit(f"[DB ERROR] Failed to log profit: {e}")

    def export_table_to_csv(self, table_name, file_path):
        try:
            self.cursor.execute(f"SELECT * FROM {table_name}")
            rows = self.cursor.fetchall()
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([desc[0] for desc in self.cursor.description])
                writer.writerows(rows)
            self.log_signal.emit(f"[EXPORT SUCCESS] {table_name} → {file_path}")
        except Exception as e:
            self.log_signal.emit(f"[EXPORT ERROR] {e}")

    def export_table_to_json(self, table_name, file_path):
        try:
            self.cursor.execute(f"SELECT * FROM {table_name}")
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            data = [dict(zip(columns, row)) for row in rows]
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            self.log_signal.emit(f"[EXPORT SUCCESS] {table_name} → {file_path}")
        except Exception as e:
            self.log_signal.emit(f"[EXPORT ERROR] {e}")

    def export_all_with_timestamp(self):
        os.makedirs("exports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.export_table_to_csv("trades", f"exports/trades_{timestamp}.csv")
        self.export_table_to_json("trades", f"exports/trades_{timestamp}.json")
        self.export_table_to_csv("signals", f"exports/signals_{timestamp}.csv")
        self.export_table_to_json("signals", f"exports/signals_{timestamp}.json")
        self.export_table_to_csv("profits", f"exports/profits_{timestamp}.csv")
        self.export_table_to_json("profits", f"exports/profits_{timestamp}.json")

    def run(self):
        try:
            config = configparser.ConfigParser()
            config.read(self.config_path)

            mode = self.mode_override or config.get("GENERAL", "mode").strip().lower()
            config.set("GENERAL", "mode", mode)
            cycle = int(config.get("GENERAL", "cycle_interval", fallback="5"))

            if mode not in ["signal", "profit"]:
                raise ValueError(f"Unsupported strategy mode: {mode}")

            runtime_options = {"mode": mode}

            if mode == "profit":
                w3 = init_web3(config)
                wallet = load_wallet(config)
                oracle = load_oracle(w3, config)

                abi_path = "config/abi/uniswap_router.abi.json"
                if not os.path.exists(abi_path):
                    raise FileNotFoundError(f"ABI file missing: {abi_path}")

                with open(abi_path) as f:
                    router_abi = json.load(f)

                router_address = config.get("DEX", "router_address")
                router = w3.eth.contract(address=router_address, abi=router_abi)

                slippage = float(config.get("TRADING", "slippage", fallback="0.01"))
                fee = int(config.get("TRADING", "fee_tier", fallback="3000"))

                runtime_options.update({
                    "w3": w3,
                    "wallet": wallet,
                    "wallet_address": wallet["address"],
                    "private_key": wallet["private_key"],
                    "oracle": oracle,
                    "router": router,
                    "slippage": slippage,
                    "fee": fee
                })

            manager = StrategyManager(config, runtime_options)

            while self.running:
                try:
                    result = manager.run_cycle()
                    self.log_signal.emit(str(result))
                    update_dashboard(result)
                    self._log_signal(mode, result)

                    if mode == "profit" and isinstance(result, list):
                        for token, action, delta in result:
                            gas = estimate_gas_price(runtime_options["w3"])
                            if manager.strategy.should_trade(gas, delta):
                                tx = execute_swap(
                                    runtime_options["w3"],
                                    runtime_options["wallet"],
                                    runtime_options["router"],
                                    token,
                                    action,
                                    gas,
                                    runtime_options["fee"],
                                    runtime_options["slippage"]
                                )
                                self._log_trade(token, action, delta, gas, tx, success=bool(tx))

                                if hasattr(manager.strategy, "estimate_profit"):
                                    try:
                                        estimated = manager.strategy.estimate_profit(token, delta)
                                        self._log_profit(token, estimated)
                                    except Exception as ep:
                                        self.log_signal.emit(f"[PROFIT ERROR] {ep}")

                                self.log_signal.emit(f"EXECUTED {action.upper()} {token[:6]} → TX {tx}")

                    elif mode == "signal" and isinstance(result, dict) and result.get("action") != "hold":
                        self.log_signal.emit(f"Signal Decision: {result}")

                    self._cycle_count += 1
                    if self.export_every_n_cycles > 0 and self._cycle_count % self.export_every_n_cycles == 0:
                        self.export_all_with_timestamp()

                    time.sleep(cycle)

                except Exception as e_inner:
                    self.log_signal.emit(f"[CYCLE ERROR] {str(e_inner)}")
                    logging.exception("[CYCLE ERROR]")
                    time.sleep(3)

        except Exception as e_init:
            self.log_signal.emit(f"[INIT ERROR] {str(e_init)}")
            logging.exception("[INIT ERROR]")

    def stop(self):
        self.running = False
        self.quit()
        self.wait()
        self.conn.close()