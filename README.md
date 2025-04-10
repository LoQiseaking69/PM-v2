# Profit-Mask v2

**Profit-Mask v2** -is a GUI-powered, real-execution trading terminal for Uniswap that uses a MetaMask wallet address. Built for high-efficiency swap execution, it performs real ERC-20 approvals and swaps using ABI-encoded RPC calls
---
![img](https://github.com/LoQiseaking69/PM-v2/blob/main/IMG_0655.jpeg)

*UI is slightly different 😅 but backend logic should be 
still entact and connected properly...*
___

## Features

- Real ERC20 trading with MetaMask wallet address and private key
- Dynamic strategy: `profit` or `signal` mode
- Configurable slippage, token override, fee tier, Infura URL
- Auto-generated `runtime_config.ini` from GUI inputs
- Live chart of profit deltas
- Threaded trade execution with safe stop/start
- Floating debug console for real-time logs
- GUI-controlled export (CSV, JSON) of any log table
- Periodic auto-export with interval control
- Full trade logging in SQLite

---

## Strategy Modes

- `profit`: Execute trades only when projected profit exceeds cost
- `signal`: Execute trades based on direct token override or signal feed

---

## Project Structure

```plaintext
PM-v2/
+-- main_gui.py                  # Launches GUI, binds thread, intercepts logs
+-- config/
|   +-- config.ini               # Default static config
|   +-- runtime_config.ini       # Generated from GUI inputs
|   \-- abi/
|       +-- erc20.abi.json       # Standard ERC20 ABI
|       \-- uniswap_router.abi.json  # Router ABI
+-- core/
|   +-- controller.py            # Threaded strategy logic, price check, swap exec
|   +-- wallet.py                # Balance checks, private key signing
|   +-- strategy.py              # Mode-specific logic
|   +-- oracle.py                # Price fetcher using DEX and/or Chainlink
|   +-- utils.py                 # RPC handling, caching, helpers
|   \-- logging.py               # SQLite + signal-based log system
+-- interface/
|   +-- gui.py                   # Main GUI layout and wiring
|   +-- dashboard.py             # Live chart and status display
|   +-- debug_console.py         # Floating log output window
|   \-- styles.py                # Visual styling
\-- data/
    \-- trading_log.db           # Local SQLite database with all logs
```

---

## Requirements

- Python 3.10+
- PyQt5
- requests, pycryptodome, matplotlib, sqlite3

Install with:

```bash
pip install -r requirements.txt
```

---

## Usage

```bash
python main_gui.py
```

1. Launch GUI
2. Enter wallet, token override, strategy mode, slippage, etc.
3. Click “Start” to begin strategy execution
4. Monitor logs and live profit chart
5. Export logs via button or interval trigger

---

## Logging and Export

- Profits, prices, trades, errors logged into SQLite
- Export any table to CSV/JSON on demand or every N cycles
- All export filenames timestamped
- Debug console shows live log output

---

## License

BSD 3-Clause License

---

## Note

This tool performs actual trades. All actions are signed and sent live via direct RPC using the specified wallet.
