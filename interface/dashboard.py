def update_dashboard(data):
    print("\n[DASHBOARD]")

    if isinstance(data, dict):  # SIGNAL MODE
        action = data.get("action", "unknown").upper()
        print(f"  Action       : {action}")
        token = data.get("token_address", "N/A")
        amount = data.get("amount_eth", "N/A")
        print(f"  Token        : {token[:10]}...")
        print(f"  Amount (ETH) : {amount}")

    elif isinstance(data, list):  # PROFIT MODE
        if not data:
            print("  No trade signals.")
        else:
            for i, (token, action, delta) in enumerate(data, 1):
                print(f"  [{i}] {action.upper():5} {token[:10]}... | Δ: {delta:+.5f}")

    else:
        print(f"  Unrecognized format: {data}")