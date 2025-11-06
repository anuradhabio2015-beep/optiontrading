def place_order_groww(strategies):
    return {"broker":"Groww","mode":"dry‑run","orders_prepared": len(strategies)}

def place_order_zerodha(strategies):
    return {"broker":"Zerodha","mode":"dry‑run","orders_prepared": len(strategies)}
