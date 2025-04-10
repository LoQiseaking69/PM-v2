from decimal import Decimal
import random
import logging
import time

# Minimal Chainlink aggregator ABI
CHAINLINK_AGGREGATOR_ABI = [
    {
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {"internalType": "uint80", "name": "roundId", "type": "uint80"},
            {"internalType": "int256", "name": "answer", "type": "int256"},
            {"internalType": "uint256", "name": "startedAt", "type": "uint256"},
            {"internalType": "uint256", "name": "updatedAt", "type": "uint256"},
            {"internalType": "uint80", "name": "answeredInRound", "type": "uint80"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Add Chainlink pairs here
CHAINLINK_FEEDS = {
    ("eth", "usd"): "0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419",  # Mainnet ETH/USD
    ("link", "usd"): "0x2c1d072e956AFFC0D435Cb7AC38EF18d24d9127c",
    # Add more as needed
}


class Oracle:
    def __init__(self, w3, address=None, ttl=60):
        self.w3 = w3
        self.address = address
        self.cache = {}
        self.last_updated = {}
        self.ttl = ttl  # seconds

    def get_price(self, token, base_token, refresh=False):
        try:
            key = (token.lower(), base_token.lower())
            now = time.time()

            if not refresh and key in self.cache:
                if now - self.last_updated.get(key, 0) < self.ttl:
                    return self.cache[key]

            price = self._fetch_chainlink_price(token, base_token)

            if price is None:
                price = Decimal(str(round(random.uniform(0.95, 1.05), 5)))
                logging.warning(f"[Oracle] Fallback to simulated price: {token[:6]}->{base_token[:6]} = {price}")

            self.cache[key] = price
            self.last_updated[key] = now

            logging.debug(f"[Oracle] Price {token[:6]}->{base_token[:6]}: {price}")
            return price

        except Exception as e:
            logging.error(f"[Oracle] get_price error: {e}")
            return Decimal("0")

    def _fetch_chainlink_price(self, token, base_token):
        try:
            feed_key = (token.lower(), base_token.lower())
            feed_address = CHAINLINK_FEEDS.get(feed_key)
            if not feed_address:
                return None

            aggregator = self.w3.eth.contract(address=self.w3.to_checksum_address(feed_address), abi=CHAINLINK_AGGREGATOR_ABI)
            data = aggregator.functions.latestRoundData().call()
            answer = data[1]
            if answer <= 0:
                return None

            return Decimal(str(answer)) / Decimal("1e8")  # Chainlink feeds return 8 decimals
        except Exception as e:
            logging.error(f"[Oracle] Chainlink fetch failed for {token}->{base_token}: {e}")
            return None

    def estimate_fair_value(self, token, base_token):
        try:
            fair_value = self.get_price(token, base_token)
            logging.debug(f"[Oracle] Fair value {token[:6]}->{base_token[:6]}: {fair_value}")
            return fair_value
        except Exception as e:
            logging.error(f"[Oracle] estimate_fair_value error: {e}")
            return Decimal("0")

    def clear_cache(self):
        self.cache.clear()
        self.last_updated.clear()
        logging.info("[Oracle] Cache cleared")