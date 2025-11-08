def build_strategies(symbol, oc, capital, risk_pct, metrics, r=0.07, days=7, focus="AI-Auto"):
    """
    Build option-selling strategies based on selected focus.
    :param symbol: str
    :param oc: dict (option chain data)
    :param capital: float
    :param risk_pct: float (% of portfolio risk per trade)
    :param metrics: dict (analytics data like expected move, IV rank)
    :param r: risk-free rate
    :param days: days to expiry
    :param focus: selected strategy focus ("Iron Condor", etc.)
    :return: list of dict strategies
    """

    spot = metrics.get("spot") or metrics.get("underlying") or 0
    expected_move = 0
    if isinstance(metrics.get("expected_move_3d"), tuple):
        expected_move = metrics["expected_move_3d"][0] or 200

    strategies = []

    # 1️⃣ Iron Condor
    if focus in ["AI-Auto", "Iron Condor"]:
        strategies.append({
            "Strategy": "Iron Condor",
            "Contracts": f"{symbol} ±{int(expected_move)} CE/PE",
            "Risk ₹": int(capital * (risk_pct / 100)),
            "Max Profit": "Credit received",
            "Max Loss": "Spread width - credit",
            "Win%": "≈65%",
            "Notes": "Neutral market, IV high"
        })

    # 2️⃣ Credit Spread
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

    # 3️⃣ Calendar Spread
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
