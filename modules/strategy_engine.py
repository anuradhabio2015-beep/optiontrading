def build_strategies(symbol, oc, capital, risk_pct, metrics, r=0.07, days=7):
    lot_risk = int(capital*(risk_pct/100.0))
    em = metrics.get("expected_move_1d",(400,None))[0] or 400
    return [
        {
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
