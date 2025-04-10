import logging
from web3 import Web3

# Minimal ERC20 ABI for balanceOf
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

def load_wallet(config, w3=None, check_token_balance=False):
    """
    Load and validate wallet configuration from configparser instance.
    Optionally checks ETH and token balances using provided Web3 instance.
    """
    try:
        private_key = config.get("WALLET", "private_key").strip()
        raw_address = config.get("WALLET", "wallet_address").strip()
        amount_eth = float(config.get("TRADING", "amount_eth", fallback="0.01"))
        base_token_raw = config.get("TRADING", "token_address").strip()

        # Validate and checksum wallet address
        if not Web3.is_checksum_address(raw_address):
            if Web3.is_address(raw_address):
                logging.warning(f"[Wallet] Address not checksummed. Auto-correcting: {raw_address}")
                address = Web3.to_checksum_address(raw_address)
            else:
                raise ValueError(f"Invalid wallet address: {raw_address}")
        else:
            address = raw_address

        # Validate and checksum token address
        if not Web3.is_checksum_address(base_token_raw):
            if Web3.is_address(base_token_raw):
                logging.warning(f"[Wallet] Base token not checksummed. Auto-correcting: {base_token_raw}")
                base_token = Web3.to_checksum_address(base_token_raw)
            else:
                raise ValueError(f"Invalid base token address: {base_token_raw}")
        else:
            base_token = base_token_raw

        # Validate private key
        if not private_key or not all(c in '0123456789abcdefABCDEF' for c in private_key) or len(private_key) != 64:
            raise ValueError("Private key must be a 64-character hex string (without 0x prefix).")

        # Package wallet
        wallet = {
            "private_key": private_key,
            "address": address,
            "amount": amount_eth,
            "base_token": base_token
        }

        logging.info(f"[Wallet] Loaded wallet: {address}")

        # Optional: verify balances using Web3
        if w3 and w3.is_connected():
            # ETH balance check
            try:
                eth_balance = w3.eth.get_balance(address)
                eth_balance_eth = Web3.from_wei(eth_balance, 'ether')
                logging.debug(f"[Wallet] ETH Balance: {eth_balance_eth} ETH")
                if eth_balance_eth < amount_eth:
                    logging.warning(f"[Wallet] ETH balance ({eth_balance_eth}) is below trade amount ({amount_eth})")
            except Exception as e:
                logging.warning(f"[Wallet] Failed to fetch ETH balance: {e}")

            # Token balance check
            if check_token_balance:
                try:
                    token_contract = w3.eth.contract(address=base_token, abi=ERC20_ABI)
                    token_balance = token_contract.functions.balanceOf(address).call()
                    token_balance_fmt = Web3.from_wei(token_balance, 'ether')  # assumes 18 decimals
                    logging.debug(f"[Wallet] Token Balance: {token_balance_fmt}")
                    if token_balance < w3.to_wei(amount_eth, 'ether'):
                        logging.warning(f"[Wallet] TOKEN balance too low: {token_balance_fmt} < {amount_eth}")
                except Exception as e:
                    logging.warning(f"[Wallet] Failed to fetch token balance: {e}")

        return wallet

    except Exception as e:
        logging.error(f"[Wallet] load_wallet error: {e}")
        raise