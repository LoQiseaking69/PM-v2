import random
import numpy as np
from decimal import Decimal
from scipy.stats import zscore
from web3 import Web3
import logging
from typing import List, Dict, Any


class SignalStrategy:
    """
    Strategy based on trend (slope), z-score, and volatility.
    It evaluates price trends and makes decisions to buy/sell/hold based on thresholds.
    """
    def __init__(self, config):
        self.token_address = config.get('TRADING', 'token_address')
        self.amount_eth = float(config.get('TRADING', 'amount_eth'))
        self.max_history = int(config.get('TRADING', 'price_history_length'))
        self.buy_slope = float(config.get('TRADING', 'buy_slope_threshold'))
        self.buy_zscore = float(config.get('TRADING', 'buy_zscore_threshold'))
        self.sell_slope = float(config.get('TRADING', 'sell_slope_threshold'))
        self.sell_zscore = float(config.get('TRADING', 'sell_zscore_threshold'))
        self.price_history: List[float] = []

    def fetch_latest_price(self) -> float:
        """
        Simulated price fetch; replace with real source in production.
        """
        return round(random.uniform(0.4, 1.8), 5)

    def evaluate_market(self) -> Dict[str, Any]:
        """
        Evaluates the current market condition and returns a trading signal.
        """
        try:
            price = self.fetch_latest_price()
            self.price_history.append(price)
            if len(self.price_history) > self.max_history:
                self.price_history.pop(0)

            min_required = min(6, self.max_history)
            if len(self.price_history) < min_required:
                return {"action": "hold"}

            prices = np.array(self.price_history)
            price_z = zscore(prices)[-1]
            std_dev = np.std(prices)

            x = np.arange(len(prices))
            slope = np.polyfit(x, prices, 1)[0]

            logging.debug(f"[SignalStrategy] price={price:.5f}, slope={slope:.5f}, zscore={price_z:.2f}, std={std_dev:.3f}")

            if slope > self.buy_slope and price_z > self.buy_zscore and std_dev < 0.5:
                return {
                    "action": "buy",
                    "token_address": self.token_address,
                    "amount_eth": self.amount_eth
                }
            elif slope < self.sell_slope and price_z < self.sell_zscore and std_dev > 0.4:
                return {
                    "action": "sell",
                    "token_address": self.token_address,
                    "amount_eth": self.amount_eth
                }
            else:
                return {"action": "hold"}

        except Exception as e:
            logging.error(f"[SignalStrategy] Evaluation error: {e}")
            return {"action": "hold"}

    def clear_history(self):
        """
        Clears the stored price history for fresh evaluation.
        """
        self.price_history.clear()
        logging.info("[SignalStrategy] Price history cleared")


class ProfitStrategy:
    """
    Arbitrage-style strategy that compares real-time token prices to oracle-based fair values.
    """
    def __init__(self, w3, router, wallet_address: str, private_key: str, oracle, growth_factor=Decimal("1.05")):
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
        self.growth_factor = growth_factor  # Affects sensitivity and trade size

    def scan_opportunities(self) -> List[Dict[str, Any]]:
        """
        Scans for arbitrage opportunities between real prices and fair value estimates.
        Adjusts sensitivity and trade size based on growth_factor.
        """
        opportunities = []
        try:
            buy_threshold = -0.03 * float(self.growth_factor)
            sell_threshold = 0.03 * float(self.growth_factor)

            for token in self.tokens:
                price = self.oracle.get_price(token, self.base_token)
                fair_value = self.oracle.estimate_fair_value(token, self.base_token)

                if fair_value == 0:
                    logging.warning(f"[ProfitStrategy] Skipping {token[:6]}... due to invalid fair value")
                    continue

                delta = (price - fair_value) / fair_value

                logging.info(
                    f"[ProfitStrategy] {token[:6]}...: price={price:.6f}, fair={fair_value:.6f}, "
                    f"delta={delta:.4f} (buy>{buy_threshold:.4f}, sell<{sell_threshold:.4f})"
                )

                if delta <= buy_threshold or delta >= sell_threshold:
                    # Calculate trade size based on delta and growth factor
                    base_amount_eth = Decimal("0.1")
                    scaling = abs(Decimal(delta)) * self.growth_factor
                    trade_size = float(base_amount_eth * scaling)

                    opportunities.append({
                        "token": token,
                        "action": "buy" if delta <= buy_threshold else "sell",
                        "delta": float(delta),
                        "trade_size_eth": round(trade_size, 6)
                    })

        except Exception as e:
            logging.error(f"[ProfitStrategy] Error during scan: {e}")

        return sorted(opportunities, key=lambda x: abs(x["delta"]), reverse=True)

    def should_trade(self, gas_cost_eth: Decimal, profit_eth: Decimal) -> bool:
        """
        Decides whether the trade is worth executing based on gas cost and expected profit.
        """
        try:
            logging.debug(f"[ProfitStrategy] Gas={gas_cost_eth}, Profit={profit_eth}")
            return profit_eth > gas_cost_eth * Decimal("1.2")
        except Exception as e:
            logging.error(f"[ProfitStrategy] should_trade error: {e}")
            return False


class StrategyManager:
    """
    Manages which strategy to execute depending on runtime mode (signal or profit).
    """
    def __init__(self, config, runtime_options: Dict[str, Any]):
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

    def run_cycle(self, *args, **kwargs) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Executes a single evaluation cycle for the selected strategy.
        """
        try:
            if self.mode == "signal":
                return self.strategy.evaluate_market()
            elif self.mode == "profit":
                return self.strategy.scan_opportunities()
        except Exception as e:
            logging.error(f"[StrategyManager] run_cycle error: {e}")
            return {"action": "hold"} if self.mode == "signal" else []