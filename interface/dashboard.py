import os
import sys

# ANSI color codes
COLOR_RESET = "\033[0m"
COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_MAGENTA = "\033[95m"

def clear_console():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

def colorize_action(action):
    action_upper = action.upper()
    if action_upper == "BUY":
        return f"{COLOR_GREEN}{action_upper}{COLOR_RESET}"
    elif action_upper == "SELL":
        return f"{COLOR_RED}{action_upper}{COLOR_RESET}"
    return f"{COLOR_YELLOW}{action_upper}{COLOR_RESET}"

def update_dashboard(data):
    clear_console()
    print(f"{COLOR_CYAN}\n[DASHBOARD]{COLOR_RESET}")

    if isinstance(data, dict):  # SIGNAL MODE
        action = colorize_action(data.get("action", "unknown"))
        print(f"  Action       : {action}")
        token = data.get("token_address", "N/A")
        amount = data.get("amount_eth", "N/A")
        print(f"  Token        : {COLOR_MAGENTA}{token[:10]}...{COLOR_RESET}")
        print(f"  Amount (ETH) : {amount}")

    elif isinstance(data, list):  # PROFIT MODE
        if not data:
            print("  No trade signals.")
        else:
            for i, (token, action, delta) in enumerate(data, 1):
                action_str = colorize_action(action)
                print(f"  [{i}] {action_str:7} {COLOR_MAGENTA}{token[:10]}...{COLOR_RESET} | Δ: {delta:+.5f}")

    else:
        print(f"{COLOR_RED}  Unrecognized format: {data}{COLOR_RESET}")