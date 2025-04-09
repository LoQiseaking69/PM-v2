
# Profit-Mask Enhanced

**Profit-Mask** is an advanced, GUI-powered decentralized trading terminal designed for MetaMask-integrated environments using Uniswap. It supports signal-based and oracle-based trading strategies, real-time profit tracking, and backtest-ready logging.

---

## Features

- PyQt5 Sci-Fi GUI Terminal
- Dynamic strategy switching (signal vs profit)
- Wallet integrity and balance checks
- Chainlink/Uniswap-compatible Oracle abstraction
- Live chart of trading performance
- Full SQLite logging for backtesting and audit
- Configurable Infura / token / slippage / fee settings
- TTL price caching for high efficiency

---

## Project Structure

```
Profit-Mask/
├── core/                 # Backend engine and strategy logic
│   ├── controller.py
│   ├── strategy.py
│   ├── wallet.py
│   ├── oracle.py
│   ├── utils.py
│   └── logging.py
├── interface/            # GUI system and styling
│   ├── gui.py
│   ├── styles.py
│   └── dashboard.py
├── config/               # Configuration and ABI contracts
│   ├── config.ini
│   ├── runtime_config.ini
│   └── abi/
│       ├── erc20.abi.json
│       └── uniswap_router.abi.json
├── data/                 # Persistent SQLite logs
│   └── trading_log.db
├── logs/                 # Rolling log output
│   └── activity.log
├── main_gui.py           # App launcher
├── requirements.txt
└── README.md
```

---

## Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Launch GUI

```bash
python main_gui.py
```

---

## Configuration

- **`config/config.ini`** stores default settings (read at GUI start)
- **`runtime_config.ini`** is rewritten when bot launches

Edit token, wallet, or RPC defaults directly or via GUI fields.

---

## Backtesting

Historical profit data is stored in:

```
data/trading_log.db (table: profits)
```

Export via:
- Automatic CSV (every 10 cycles)
- Manual script for backtest CLI integration (`strategy.py` stub ready)

---

## Enhancements Over Beta

- Modular folder layout
- Dynamic ERC20 decimal detection
- Token/address checksum auto-correction
- TTL-cached price queries
- Secure logging with no private key exposure
- Auto-seed profit history on first boot

---

## License

MIT — use freely with attribution.
