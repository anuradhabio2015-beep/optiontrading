import random

def ai_trade_levels(symbol, spot, iv_rank, pcr, strategy="Iron Condor"):
    """
    AI-based entry, exit, and stop-loss generator.
    You can connect Gemini API here for more sophistication.
    """
    levels = {}

    # ---- Adjust logic based on strategy type ----
    if strategy == "Iron Condor":
        # Wider range, neutral bias
        entry = round(spot, -2)  # nearest 100
        stop = round(entry * 0.98, 2)
        target = round(entry * 1.02, 2)
        rationale = "Neutral view, sell premium near expected move band."
    elif strategy == "Bull Put Credit Spread":
        # Bullish bias
        entry = round(spot * 0.99, 2)
        stop = round(entry * 0.985, 2)
        target = round(entry * 1.01, 2)
        rationale = "Bullish bias, strong put OI support zone."
    elif strategy == "ATM Calendar":
        # Volatility play
        entry = round(spot, 2)
        stop = round(entry * 0.99, 2)
        target = round(entry * 1.01, 2)
        rationale = "Expect short-term stability with long-term IV mean reversion."
    else:
        entry = spot
        stop = round(spot * 0.985, 2)
        target = round(spot * 1.015, 2)
        rationale = "AI-generated default range based on spot trend."

    # Add AI-based adjustment factors (mocked for now)
    ai_confidence = random.randint(70, 95)
    iv_factor = "High IV — safer to sell options" if iv_rank > 60 else "Low IV — prefer buying premium"
    pcr_signal = "PCR > 1 → bullish bias" if pcr > 1 else "PCR < 1 → bearish bias"

    levels = {
        "Symbol": symbol,
        "Strategy": strategy,
        "Entry": entry,
        "Exit Target": target,
        "Stop Loss": stop,
        "AI Confidence (%)": ai_confidence,
        "Volatility Insight": iv_factor,
        "PCR Insight": pcr_signal,
        "Rationale": rationale
    }

    return levels
