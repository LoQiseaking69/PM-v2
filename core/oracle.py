import logging
import time
import random
from decimal import Decimal
from web3 import Web3
import configparser

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
    # Extendable...
}

class Oracle:
    def __init__(self, config_file: str, address=None, ttl=60):
        """
        Initializes the Oracle class using Infura as the Ethereum provider.
        
        :param config_file: Path to the configuration file (e.g., 'config.ini').
        :param address: Optional address of the token on the Ethereum network.
        :param ttl: Time-to-live for the cache (default: 60 seconds).
        """
        # Load the configuration file
        config = configparser.ConfigParser()
        config.read(config_file)
        
        # Get Infura URL from the config file
        infura_url = config.get('NETWORK', 'infura_url')
        
        # Initialize Web3 instance with Infura
        self.w3 = Web3(Web3.HTTPProvider(infura_url))  # Using Infura HTTP provider
        if not self.w3.isConnected():
            raise ValueError("[Oracle] Failed to connect to Infura.")
        
        self.address = address
        self.ttl = ttl  # Time-to-live for cached data
        self.cache = {}
        self.last_updated = {}

    def get_price(self, token, base_token, refresh=False):
        """
        Returns the price of `token` relative to `base_token`.
        Fetches the price from Chainlink or uses the cached value if it is fresh.
        """
        try:
            key = (token.lower(), base_token.lower())
            now = time.time()

            # Use cache if fresh and not forced to refresh
            if not refresh and key in self.cache and now - self.last_updated.get(key, 0) < self.ttl:
                logging.debug(f"[Oracle] Using cached price for {token}->{base_token}")
                return self.cache[key]

            price = self._fetch_chainlink_price(token, base_token)

            # Fallback if no price available
            if price is None:
                price = Decimal(str(round(random.uniform(0.95, 1.05), 5)))  # Simulated price fallback
                logging.warning(f"[Oracle] Fallback to simulated price: {token[:6]}->{base_token[:6]} = {price}")

            self.cache[key] = price
            self.last_updated[key] = now

            logging.debug(f"[Oracle] Price {token[:6]}->{base_token[:6]}: {price}")
            return price

        except Exception as e:
            logging.error(f"[Oracle] get_price error: {e}")
            return Decimal("0")

    def _fetch_chainlink_price(self, token, base_token):
        """
        Fetches the latest price from the Chainlink aggregator for the given pair.
        """
        try:
            key = (token.lower(), base_token.lower())
            feed_address = CHAINLINK_FEEDS.get(key)
            if not feed_address:
                logging.warning(f"[Oracle] No Chainlink feed available for {token}->{base_token}")
                return None

            aggregator = self.w3.eth.contract(
                address=self.w3.to_checksum_address(feed_address),
                abi=CHAINLINK_AGGREGATOR_ABI
            )
            data = aggregator.functions.latestRoundData().call()
            answer = data[1]

            if not isinstance(answer, int) or answer <= 0:
                logging.warning(f"[Oracle] Invalid Chainlink answer for {token}->{base_token}: {answer}")
                return None

            return Decimal(str(answer)) / Decimal("1e8")  # Adjust for Chainlink decimal places

        except Exception as e:
            logging.error(f"[Oracle] Chainlink fetch failed for {token}->{base_token}: {e}")
            return None

    def estimate_fair_value(self, token, base_token):
        """
        Estimates the fair value of a token relative to a base token.
        Uses Chainlink or a fallback mechanism if Chainlink data is unavailable.
        """
        try:
            fair_value = self.get_price(token, base_token)
            logging.debug(f"[Oracle] Fair value {token[:6]}->{base_token[:6]}: {fair_value}")
            return fair_value
        except Exception as e:
            logging.error(f"[Oracle] estimate_fair_value error: {e}")
            return Decimal("0")

    def clear_cache(self):
        """
        Clears the cached prices and refreshes the data.
        """
        self.cache.clear()
        self.last_updated.clear()
        logging.info("[Oracle] Cache cleared")

    def refresh_price(self, token, base_token):
        """
        Manually refreshes the price of a specific token pair.
        """
        try:
            key = (token.lower(), base_token.lower())
            price = self._fetch_chainlink_price(token, base_token)

            if price is None:
                price = Decimal(str(round(random.uniform(0.95, 1.05), 5)))  # Simulated fallback price

            self.cache[key] = price
            self.last_updated[key] = time.time()

            logging.info(f"[Oracle] Manually refreshed price for {token}->{base_token}: {price}")
            return price

        except Exception as e:
            logging.error(f"[Oracle] Error during price refresh for {token}->{base_token}: {e}")
            return Decimal("0")