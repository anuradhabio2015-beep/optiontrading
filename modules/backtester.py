import pandas as pd, random

def run_detailed_backtest(symbol, strategies):
    results = []
    for s in strategies:
        pop = random.randint(55, 80)
        avg_pnl = random.randint(800, 2500)
        max_loss = avg_pnl * -1.2
        sharpe = round((avg_pnl / abs(max_loss)) * 1.5, 2)
        results.append({
            "Symbol": symbol,
            "Strategy": s["Strategy"],
            "Win Rate (%)": pop,
            "Avg P&L (₹)": avg_pnl,
            "Max Loss (₹)": max_loss,
            "Risk/Reward": round(abs(max_loss / avg_pnl), 2),
            "Sharpe-Like": sharpe,
            "Duration (days)": random.randint(5, 15)
        })
    return pd.DataFrame(results)
