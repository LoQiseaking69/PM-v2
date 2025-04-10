# strategy.py
import random
import numpy as np
from decimal import Decimal
from scipy.stats import zscore
from web3 import Web3
import logging

class SignalStrategy:
    def __init__(self, config):
        self.token_address = config.get('TRADING', 'token_address')
        self.amount_eth = float(config.get('TRADING', 'amount_eth'))
        self.max_history = int(config.get('TRADING', 'price_history_length'))
        self.buy_slope = float(config.get('TRADING', 'buy_slope_threshold'))
        self.buy_zscore = float(config.get('TRADING', 'buy_zscore_threshold'))
        self.sell_slope = float(config.get('TRADING', 'sell_slope_threshold'))
        self.sell_zscore = float(config.get('TRADING', 'sell_zscore_threshold'))
        self.price_history = []

    def fetch_latest_price(self):
        return round(random.uniform(0.4, 1.8), 5)

    def evaluate_market(self):
        price = self.fetch_latest_price()
        self.price_history.append(price)
        if len(self.price_history) > self.max_history:
            self.price_history.pop(0)

        if len(self.price_history) < 6:
            return {"action": "hold"}

        prices = np.array(self.price_history)
        slope = np.mean(prices[-3:]) - np.mean(prices[:3])
        price_z = zscore(prices)[-1]
        std_dev = np.std(prices)

        if slope > self.buy_slope and price_z > self.buy_zscore and std_dev < 0.5:
            return {"action": "buy", "token_address": self.token_address, "amount_eth": self.amount_eth}
        elif slope < self.sell_slope and price_z < self.sell_zscore and std_dev > 0.4:
            return {"action": "sell", "token_address": self.token_address, "amount_eth": self.amount_eth}
        else:
            return {"action": "hold"}

class ProfitStrategy:
    def __init__(self, w3, router, wallet_address, private_key, oracle):
        self.w3 = w3
        self.router = router
        self.wallet_address = wallet_address
        self.private_key = private_key
        self.oracle = oracle
        self.base_token = Web3.to_checksum_address("0xA0b86991C6218b36c1d19D4a2e9Eb0cE3606eB48")  # USDC
        self.tokens = [
            Web3.to_checksum_address("0x6B175474E89094C44Da98b954EedeAC495271d0F"),  # DAI
            Web3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7"),  # USDT
        ]
        self.growth_factor = Decimal("1.05")

    def scan_opportunities(self):
        opportunities = []
        for token in self.tokens:
            price = self.oracle.get_price(token, self.base_token)
            fair_value = self.oracle.estimate_fair_value(token, self.base_token)
            delta = (price - fair_value) / fair_value if fair_value != 0 else Decimal("0.0")
            logging.info(f"Scanned {token}: price={price}, fair={fair_value}, delta={delta}")
            if delta <= -0.03:
                opportunities.append((token, 'buy', delta))
            elif delta >= 0.03:
                opportunities.append((token, 'sell', delta))
        return sorted(opportunities, key=lambda x: abs(x[2]), reverse=True)

    def should_trade(self, gas_cost_eth, profit_eth):
        logging.debug(f"Gas cost: {gas_cost_eth}, Estimated profit: {profit_eth}")
        return profit_eth > gas_cost_eth * Decimal("1.2")

class StrategyManager:
    def __init__(self, config, runtime_options):
        self.mode = runtime_options.get("mode", "signal")
        self.strategy = None
        if self.mode == "signal":
            self.strategy = SignalStrategy(config)
        elif self.mode == "profit":
            self.strategy = ProfitStrategy(
                runtime_options["w3"],
                runtime_options["router"],
                runtime_options["wallet_address"],
                runtime_options["private_key"],
                runtime_options["oracle"]
            )
        else:
            raise ValueError(f"Unsupported strategy mode: {self.mode}")

    def run_cycle(self, *args, **kwargs):
        if self.mode == "signal":
            return self.strategy.evaluate_market()
        elif self.mode == "profit":
            return self.strategy.scan_opportunities()
