import datetime
from kiteconnect import KiteConnect

# ---------------- Zerodha Order ----------------
def place_order_zerodha(api_key, access_token, symbol, strike, opt_type, expiry, qty, price, product="NRML"):
    """
    Places order on Zerodha via KiteConnect.
    """
    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        tradingsymbol = f"{symbol}{expiry}{strike}{opt_type}"

        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO,
            tradingsymbol=tradingsymbol,
            transaction_type=kite.TRANSACTION_TYPE_SELL,
            quantity=qty,
            product=product,
            order_type=kite.ORDER_TYPE_LIMIT,
            price=price,
            validity=kite.VALIDITY_DAY
        )
        return f"✅ Zerodha order placed successfully. Order ID: {order_id}"
    except Exception as e:
        return f"⚠️ Zerodha order failed: {str(e)[:100]}"


# ---------------- Groww Order (Simulated) ----------------
def place_order_groww(symbol, strike, opt_type, expiry, qty, price, product="NRML"):
    """
    Simulated Groww order (Groww does not expose a public API).
    Returns paper confirmation.
    """
    try:
        order_ref = f"GR-{symbol}-{strike}-{opt_type}-{datetime.datetime.now().strftime('%H%M%S')}"
        return f"✅ Simulated Groww order placed successfully for {symbol} {strike}{opt_type}. Ref: {order_ref}"
    except Exception as e:
        return f"⚠️ Groww order simulation failed: {str(e)[:100]}"
