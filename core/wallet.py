import logging
from web3 import Web3
from eth_keys import keys

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
    Load and validate wallet config, optionally check balances.
    """
    try:
        raw_pk = config.get("WALLET", "private_key").strip()
        private_key = raw_pk[2:] if raw_pk.startswith("0x") else raw_pk

        if not private_key or len(private_key) != 64 or not all(c in '0123456789abcdefABCDEF' for c in private_key):
            raise ValueError("Private key must be a 64-character hex string (without 0x prefix).")

        try:
            derived_address = keys.PrivateKey(bytes.fromhex(private_key)).public_key.to_checksum_address()
        except Exception as e:
            raise ValueError(f"Private key parsing failed: {e}")

        raw_address = config.get("WALLET", "wallet_address").strip()
        amount_eth = float(config.get("TRADING", "amount_eth", fallback="0.01"))
        raw_token = config.get("TRADING", "token_address").strip()

        # Validate and checksum wallet address
        if not Web3.is_address(raw_address):
            raise ValueError(f"Invalid wallet address: {raw_address}")
        address = Web3.to_checksum_address(raw_address)

        if address != derived_address:
            logging.warning(f"[Wallet] MISMATCH: Derived {derived_address} != Provided {address}")

        # Validate and checksum base token address
        if not Web3.is_address(raw_token):
            raise ValueError(f"Invalid token address: {raw_token}")
        token_address = Web3.to_checksum_address(raw_token)

        wallet = {
            "private_key": private_key,
            "address": address,
            "amount": amount_eth,
            "base_token": token_address
        }

        logging.info(f"[Wallet] Loaded wallet: {address}")

        if w3 and w3.is_connected():
            # ETH balance check
            try:
                eth_raw = w3.eth.get_balance(address)
                eth_balance = Web3.from_wei(eth_raw, 'ether')
                logging.debug(f"[Wallet] ETH Balance: {eth_balance} ETH")
                if eth_balance < amount_eth:
                    logging.warning(f"[Wallet] Low ETH: {eth_balance} < {amount_eth}")
            except Exception as e:
                logging.warning(f"[Wallet] ETH balance fetch failed: {e}")

            # Token balance check
            if check_token_balance:
                try:
                    token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
                    token_raw = token_contract.functions.balanceOf(address).call()
                    token_balance = Web3.from_wei(token_raw, 'ether')
                    logging.debug(f"[Wallet] Token Balance: {token_balance}")
                    if token_raw < w3.to_wei(amount_eth, 'ether'):
                        logging.warning(f"[Wallet] TOKEN balance too low: {token_balance} < {amount_eth}")
                except Exception as e:
                    logging.warning(f"[Wallet] Token balance fetch failed: {e}")

        return wallet

    except Exception as e:
        logging.error(f"[Wallet] load_wallet error: {e}")
        raise