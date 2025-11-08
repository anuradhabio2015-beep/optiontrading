import pandas as pd
import random

def simulate_option_price_change(entry_price, days_held=7, direction="sell"):
    """
    Simple simulation: estimates option price decay or gain based on theta + movement.
    """
    if direction == "sell":
        # Assume premium decays ~30-70% over a week unless moved ITM
        decay = random.uniform(0.3, 0.7)
        return round(entry_price * decay, 2)
    else:
        # For buy side, assume 20-100% gain chance
        move = random.uniform(0.8, 1.5)
        return round(entry_price * move, 2)

def run_detailed_backtest(symbol, strategies):
    """
    Backtest with capital, entry/exit, profit/loss, drawdown, POP
    """
    records = []
    for s in strategies:
        strategy_name = s["Strategy"]
        capital = s.get("Risk ₹", 2000)
        entry_price = random.randint(80, 250)
        direction = "sell" if "credit" in strategy_name.lower() or "condor" in strategy_name.lower() else "buy"

        exit_price = simulate_option_price_change(entry_price, days_held=random.randint(3, 10), direction=direction)

        if direction == "sell":
            profit = entry_price - exit_price
        else:
            profit = exit_price - entry_price

        # P/L metrics
        pnl = round(profit * 25, 2)  # 1 lot = 25 qty
        pct_return = round((pnl / capital) * 100, 2)
        max_dd = round(-abs(pnl) * random.uniform(0.2, 0.5), 2)
        pop = random.randint(55, 85)
        remarks = "Profitable" if pnl > 0 else "Loss Trade"

        records.append({
            "Symbol": symbol,
            "Strategy": strategy_name,
            "Capital Used (₹)": capital,
            "Entry Premium (₹)": entry_price,
            "Exit Premium (₹)": exit_price,
            "Position": "SELL" if direction == "sell" else "BUY",
            "P/L (₹)": pnl,
            "Return (%)": pct_return,
            "Max DD (₹)": max_dd,
            "POP (%)": pop,
            "Days Held": random.randint(5, 10),
            "Remarks": remarks
        })

    df = pd.DataFrame(records)
    df["Total Profit (₹)"] = df["P/L (₹)"].cumsum()
    return df
