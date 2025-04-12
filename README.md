# Profit-Mask: Decentralized Trading Terminal

**Profit-Mask** is a high-performance, GUI-based trading terminal tailored for MetaMask-enabled decentralized finance (DeFi) operations. It interfaces with Uniswap and integrates live profit tracking, strategy switching, and full backtesting capabilities. Designed with efficiency, security, and usability in mind.

---

## Features

- **Sci-Fi PyQt5 GUI** with modular tabs and real-time state feedback  
- **Dynamic Strategy Mode**: Switch between `signal` and `profit` logic  
- **Wallet Validation**: Live MetaMask address parsing and ETH balance checks  
- **Oracle Integration**: Chainlink-compatible querying for token price accuracy  
- **Live Profit Charting**: Real-time estimated returns visualized over time  
- **Robust Logging**: All trade and price activity stored in SQLite and log files  
- **Configurable Runtime**: Adjustable router, slippage, token pairs, and RPC endpoints  
- **Export Options**: Manual and automated data export for analysis and audit  

---

## Interface Preview

**Credential Configuration**  
![Wallet Input](IMG_0921.jpeg)

**Live Tactical Logs**  
![Console Log Output](IMG_0922.jpeg)

**Real-Time Profit Chart**  
![Profit Chart](IMG_0923.jpeg)

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

## Setup Guide

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Launch the Application

```bash
python main_gui.py
```

---

## Configuration

- `config/config.ini`: Default token, RPC, slippage, and address settings  
- `runtime_config.ini`: Auto-generated and rewritten during runtime  
- GUI fields directly override config values and persist on "Save"

---

## Logging & Backtesting

- SQLite database file: `data/trading_log.db`  
- Table: `profits` with estimated ETH gain/loss over time

Export Options:
- **Automatic**: CSV/JSON export every 10 cycles  
- **Manual**: Via GUI export tab  
- **CLI-Compatible**: Stub functions extendable in `strategy.py` for backtesting logic

---

## Enhancements Over Prior Version

- Modularized directory structure  
- Checksum-corrected token validation  
- Automatic ABI-based decimal detection  
- TTL-based price caching to reduce RPC load  
- GUI-controlled config and export  
- Initial profit history seed logic for boot chart  


## License

BSD 3-Clause License

Copyright (c) 2025, Profit-Mask Contributors  
All rights reserved.
