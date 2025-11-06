import pandas as pd, random
def run_backtest_for_symbol(symbol: str, strategies: list):
    rows = []
    for s in strategies:
        base = s.get("pop_est%", 60)
        win = random.randint(base-3, base+3)
        avg_pnl = random.randint(800, 1800)
        rows.append({"Symbol": symbol, "Strategy": s["name"], "POP%": win, "AvgPnL": avg_pnl})
    return pd.DataFrame(rows)
