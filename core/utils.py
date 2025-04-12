import logging
import decimal
import time
from web3 import Web3
from web3.exceptions import TransactionNotFound

from core.oracle import Oracle

QUOTER_ADDRESS = Web3.to_checksum_address("0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6")

QUOTER_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenIn", "type": "address"},
            {"internalType": "address", "name": "tokenOut", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
        ],
        "name": "quoteExactInputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}],
        "name": "allowance",
        "outputs": [{"name": "remaining", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}],
        "name": "approve",
        "outputs": [{"name": "success", "type": "bool"}],
        "type": "function"
    }
]


def init_web3(config=None):
    try:
        infura_url = config.get("WEB3", "infura_url", fallback="").strip() if config else \
                     "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
        w3 = Web3(Web3.HTTPProvider(infura_url))
        if not w3.is_connected():
            raise ConnectionError("Web3 connection failed.")
        logging.info("[Web3] Connected to Ethereum network.")
        return w3
    except Exception as e:
        logging.error(f"[Web3] init_web3 error: {e}")
        raise


def load_oracle(w3, config):
    try:
        oracle_address = config.get("ORACLE", "address")
        return Oracle(w3, oracle_address)
    except Exception as e:
        logging.error(f"[Oracle] load_oracle error: {e}")
        raise


def estimate_gas_price(w3):
    try:
        gas_price_wei = w3.eth.gas_price
        gas_price_eth = decimal.Decimal(gas_price_wei) / decimal.Decimal(1e18)
        logging.debug(f"[Gas] Current gas price: {gas_price_eth:.9f} ETH")
        return gas_price_eth
    except Exception as e:
        logging.error(f"[Gas] estimate_gas_price error: {e}")
        return decimal.Decimal("0")


def get_min_out(w3, token_in, token_out, amount_in, fee=3000, slippage=0.01):
    try:
        quoter = w3.eth.contract(address=QUOTER_ADDRESS, abi=QUOTER_ABI)
        quoted = quoter.functions.quoteExactInputSingle(
            token_in, token_out, fee, amount_in, 0
        ).call()
        min_out = int(quoted * (1 - slippage))
        logging.info(f"[Quote] Expected={quoted}, MinOut (slippage)={min_out}")
        return min_out
    except Exception as e:
        logging.error(f"[Quote] Failed to fetch quote: {e}")
        return 0


def check_allowance_and_approve(w3, token, router_address, wallet, amount_in, gas_price, nonce):
    try:
        token_contract = w3.eth.contract(address=token, abi=ERC20_ABI)
        current_allowance = token_contract.functions.allowance(wallet["address"], router_address).call()
        if current_allowance >= amount_in:
            logging.info(f"[Allow] Current allowance sufficient: {current_allowance}")
            return nonce

        logging.info(f"[Allow] Approving {amount_in} for {token}...")
        approve_txn = token_contract.functions.approve(router_address, amount_in).build_transaction({
            'from': wallet["address"],
            'gas': 100000,
            'gasPrice': int(gas_price * 1e18),
            'nonce': nonce
        })
        signed = w3.eth.account.sign_transaction(approve_txn, private_key=wallet["private_key"])
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        logging.info(f"[Approve] TX sent: {tx_hash.hex()}")
        w3.eth.wait_for_transaction_receipt(tx_hash)
        return nonce + 1
    except Exception as e:
        logging.error(f"[Allow] Approval error: {e}")
        return nonce


def execute_swap(w3, wallet, router, token, action, gas_price, fee=3000, slippage=0.01):
    try:
        nonce = w3.eth.get_transaction_count(wallet["address"])
        deadline = int(time.time()) + 1200
        amount_in = w3.to_wei(wallet["amount"], 'ether')
        recipient = Web3.to_checksum_address(wallet["address"])

        if action == "buy":
            token_in = Web3.to_checksum_address(wallet["base_token"])
            token_out = Web3.to_checksum_address(token)
            min_out = get_min_out(w3, token_in, token_out, amount_in, fee, slippage)
            if min_out <= 0:
                logging.error("[Swap] Invalid minOut for BUY")
                return "buy-execution-failed"

            params = {
                'tokenIn': token_in,
                'tokenOut': token_out,
                'fee': fee,
                'recipient': recipient,
                'deadline': deadline,
                'amountIn': amount_in,
                'amountOutMinimum': min_out,
                'sqrtPriceLimitX96': 0
            }

            txn = router.functions.exactInputSingle(params).build_transaction({
                'from': recipient,
                'value': amount_in,
                'gas': 300000,
                'gasPrice': int(gas_price * 1e18),
                'nonce': nonce
            })

        elif action == "sell":
            token_in = Web3.to_checksum_address(token)
            token_out = Web3.to_checksum_address(wallet["base_token"])
            token_contract = w3.eth.contract(address=token_in, abi=ERC20_ABI)
            balance = token_contract.functions.balanceOf(wallet["address"]).call()
            if balance < amount_in:
                logging.warning(f"[Swap] Insufficient balance: {balance} < {amount_in}")
                return "sell-insufficient-balance"

            min_out = get_min_out(w3, token_in, token_out, amount_in, fee, slippage)
            if min_out <= 0:
                logging.error("[Swap] Invalid minOut for SELL")
                return "sell-execution-failed"

            nonce = check_allowance_and_approve(w3, token_in, router.address, wallet, amount_in, gas_price, nonce)

            params = {
                'tokenIn': token_in,
                'tokenOut': token_out,
                'fee': fee,
                'recipient': recipient,
                'deadline': deadline,
                'amountIn': amount_in,
                'amountOutMinimum': min_out,
                'sqrtPriceLimitX96': 0
            }

            txn = router.functions.exactInputSingle(params).build_transaction({
                'from': recipient,
                'gas': 300000,
                'gasPrice': int(gas_price * 1e18),
                'nonce': nonce
            })

        else:
            raise ValueError(f"Unsupported action: {action}")

        signed_txn = w3.eth.account.sign_transaction(txn, private_key=wallet["private_key"])
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        logging.info(f"[Swap] Executed {action.upper()} {token[:6]} => TX: {tx_hash.hex()}")
        return tx_hash.hex()

    except Exception as e:
        logging.error(f"[Swap] execute_swap error: {e}")
        return f"{action}-execution-failed"