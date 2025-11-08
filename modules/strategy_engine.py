def build_strategies(symbol, oc, capital, risk_pct, metrics, r=0.07, days=7):
    lot_risk = int(capital*(risk_pct/100.0))
    em = metrics.get("expected_move_1d",(400,None))[0] or 400
    return [
        {def build_strategies(symbol, oc, capital, risk_pct, metrics, r=0.07, days=7, focus="AI-Auto"):
    spot = metrics.get("spot") or metrics.get("underlying") or 0
    strategies = []

    if focus in ["AI-Auto", "Iron Condor"]:
        strategies.append({
            "Strategy": "Iron Condor",
            "Contracts": f"{symbol} ±{int(metrics.get('expected_move_3d', (200,))[0])} CE/PE",
            "Risk ₹": int(capital * (risk_pct / 100)),
            "Max Profit": "Credit received",
            "Max Loss": "Spread width - credit",
            "Win%": "≈65%",
            "Notes": "Neutral market, IV high"
        })
    if focus in ["AI-Auto", "Credit Spread"]:
        strategies.append({
            "Strategy": "Bull Put Credit Spread",
            "Contracts": f"{symbol} PE {int(spot - 200)}/{int(spot - 100)}",
            "Risk ₹": int(capital * (risk_pct / 100)),
            "Max Profit": "Credit",
            "Max Loss": "Width - credit",
            "Win%": "≈70%",
            "Notes": "Bullish bias, IV > 14"
        })
    if focus in ["AI-Auto", "Calendar Spread"]:
        strategies.append({
            "Strategy": "ATM Calendar",
            "Contracts": f"{symbol} ATM CE Calendar",
            "Risk ₹": int(capital * (risk_pct / 100)),
            "Max Profit": "Theta decay",
            "Max Loss": "Limited",
            "Win%": "≈55%",
            "Notes": "Low IV, stable vols"
        })
    return strategies

            "symbol": symbol, "name": "Income — Iron Condor",
            "contracts": f"Sell (ATM-{int(em)}) PE / Sell (ATM+{int(em)}) CE; Buy farther wings",
            "entry": "Net credit (limit)",
            "sl": "1.5× credit or delta breach",
            "t1": "50% credit", "t2": "75% credit",
            "lots": 1, "risk": lot_risk, "pop_est%": 62
        },
        {
            "symbol": symbol, "name": "Directional — Put Credit Spread",
            "contracts": f"Short OTM PE near −{int(0.8*em)}; Long PE −{int(1.5*em)}",
            "entry": "Net credit",
            "sl": "Credit × 2",
            "t1": "50% credit", "t2": "80% credit",
            "lots": 1, "risk": lot_risk, "pop_est%": 70
        },
        {
            "symbol": symbol, "name": "Volatility — ATM Calendar (CE)",
            "contracts": "Buy next‑month ATM CE / Sell weekly ATM CE",
            "entry": "Net debit",
            "sl": "Debit −30%",
            "t1": "25%", "t2": "50%",
            "lots": 1, "risk": "Limited to debit", "pop_est%": 58
        }
    ]
