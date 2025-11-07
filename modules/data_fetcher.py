import requests
import json
import time
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36",
    "accept-language": "en,gu;q=0.9,hi;q=0.8",
    "accept-encoding": "gzip, deflate, br"
}

NSE_BASE = "https://www.nseindia.com"

def _get_session():
    """Create a session with valid NSE cookies."""
    s = requests.Session()
    s.headers.update(HEADERS)
    s.get("https://www.nseindia.com", timeout=10)
    return s


def fetch_indices_nse():
    """Fetch index prices (NIFTY, BANKNIFTY, INDIA VIX) from NSE API."""
    try:
        s = _get_session()
        url = f"{NSE_BASE}/api/allIndices"
        r = s.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        mapping = {}
        for idx in data.get("data", []):
            name = idx.get("index", "").upper().replace(" ", "")
            mapping[name] = float(idx.get("last", 0))
        # Standardize keys
        if "NIFTY50" in mapping:
            mapping["NIFTY"] = mapping["NIFTY50"]
        if "NIFTYBANK" in mapping:
            mapping["BANKNIFTY"] = mapping["NIFTYBANK"]
        if "INDIAVIX" not in mapping:
            mapping["INDIAVIX"] = fetch_vix_fallback()
        return mapping
    except Exception as e:
        print(f"[WARN] fetch_indices_nse failed: {e}")
        return {}


def fetch_vix_fallback():
    """Fallback VIX value from Investing.com (approx)."""
    try:
        r = requests.get("https://priceapi.moneycontrol.com/pricefeed/notapplicable/inidicesindia/inindiaVIX", timeout=10)
        if r.status_code == 200:
            return float(r.json().get("data", {}).get("price", 0))
    except Exception as e:
        print(f"[WARN] fetch_vix_fallback failed: {e}")
    return 14.0  # safe default


def fetch_spot_price(symbol):
    """Fetch spot price for a stock or index."""
    s = _get_session()
    try:
        url = f"{NSE_BASE}/api/quote-equity?symbol={symbol.upper()}"
        r = s.get(url, timeout=10)
        if r.status_code == 200:
            return float(r.json()["priceInfo"]["lastPrice"])
    except:
        # TradingView fallback
        try:
            r = requests.get(f"https://in.tradingview.com/symbols/NSE-{symbol}/", timeout=10)
            import re
            m = re.search(r'"regularMarketPrice":([0-9]+\.[0-9]+)', r.text)
            if m:
                return float(m.group(1))
        except Exception as e:
            print(f"[WARN] Spot fallback failed for {symbol}: {e}")
    return None


def fetch_option_chain(symbol):
    """Fetch option chain data for index or equity."""
    s = _get_session()
    if symbol.upper() in ["NIFTY", "BANKNIFTY"]:
        url = f"{NSE_BASE}/api/option-chain-indices?symbol={symbol.upper()}"
    else:
        url = f"{NSE_BASE}/api/option-chain-equities?symbol={symbol.upper()}"
    try:
        r = s.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[WARN] Option chain fetch failed for {symbol}: {e}")
        return {}
