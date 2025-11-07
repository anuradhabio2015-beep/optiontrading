import requests
import json
import time

NSE_BASE = "https://www.nseindia.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/"
}

def fetch_indices_nse():
    """Fetch index prices and major stock spots from NSE."""
    session = requests.Session()
    session.headers.update(HEADERS)
    indices_url = f"{NSE_BASE}/api/allIndices"

    try:
        r = session.get(indices_url, timeout=10)
        r.raise_for_status()
        data = r.json()
        mapping = {}

        # Capture Index Prices
        for idx in data.get("data", []):
            name = idx.get("index", "").upper().replace(" ", "")
            last = idx.get("last", None)
            if name and last:
                mapping[name] = float(last)

        # Add India VIX if missing
        if "INDIAVIX" not in mapping:
            mapping["INDIAVIX"] = fetch_vix(session)

        return mapping

    except Exception as e:
        print(f"[WARN] NSE index fetch failed: {e}")
        return {}

def fetch_vix(session=None):
    """Fetch India VIX level separately."""
    try:
        s = session or requests.Session()
        s.headers.update(HEADERS)
        r = s.get(f"{NSE_BASE}/api/allIndices", timeout=10)
        r.raise_for_status()
        data = r.json()
        for idx in data.get("data", []):
            if "VIX" in idx.get("index", "").upper():
                return float(idx.get("last", 0))
        return None
    except:
        return None

def fetch_spot_price(symbol):
    """Fetch live spot for stock/index symbol."""
    s = requests.Session()
    s.headers.update(HEADERS)
    url = f"{NSE_BASE}/api/quote-equity?symbol={symbol.upper()}"
    try:
        r = s.get(url, timeout=10)
        if r.status_code == 200:
            j = r.json()
            return j.get("priceInfo", {}).get("lastPrice", None)
    except Exception as e:
        print(f"[WARN] Spot fetch failed for {symbol}: {e}")
    return None

def fetch_option_chain(symbol):
    """Fetch option chain data."""
    s = requests.Session()
    s.headers.update(HEADERS)
    oc_url = f"{NSE_BASE}/api/option-chain-indices?symbol={symbol.upper()}"
    if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
        oc_url = f"{NSE_BASE}/api/option-chain-equities?symbol={symbol.upper()}"
    try:
        r = s.get(oc_url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[WARN] Option chain fetch failed for {symbol}: {e}")
        return {}
