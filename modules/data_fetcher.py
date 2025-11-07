import requests, json, time, re, os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/121.0 Safari/537.36",
    "accept-language": "en-US,en;q=0.9",
}

NSE_BASE = "https://www.nseindia.com"

def _session():
    s = requests.Session()
    s.headers.update(HEADERS)
    s.get("https://www.nseindia.com", timeout=10)
    return s

# -------------------------------------------------------------
# Index and VIX
# -------------------------------------------------------------
def fetch_indices_nse():
    try:
        s = _session()
        r = s.get(f"{NSE_BASE}/api/allIndices", timeout=10)
        data = r.json()
        mapping = {}
        for i in data.get("data", []):
            name = i.get("index", "").upper().replace(" ", "")
            mapping[name] = float(i.get("last", 0))
        if "NIFTY50" in mapping:
            mapping["NIFTY"] = mapping["NIFTY50"]
        if "NIFTYBANK" in mapping:
            mapping["BANKNIFTY"] = mapping["NIFTYBANK"]
        if "INDIAVIX" not in mapping:
            mapping["INDIAVIX"] = 14.0
        return mapping
    except Exception as e:
        print(f"[WARN] fetch_indices_nse failed: {e}")
        return {"INDIAVIX": 14.0}

# -------------------------------------------------------------
# Spot Price (Stock or Index)
# -------------------------------------------------------------
def fetch_spot_price(symbol: str):
    try:
        s = _session()
        # For indices
        if symbol.upper() in ["NIFTY", "BANKNIFTY"]:
            r = s.get(f"{NSE_BASE}/api/option-chain-indices?symbol={symbol.upper()}", timeout=10)
            data = r.json()
            return float(data["records"]["underlyingValue"])
        # For equities
        r = s.get(f"{NSE_BASE}/api/quote-equity?symbol={symbol.upper()}", timeout=10)
        data = r.json()
        return float(data["priceInfo"]["lastPrice"])
    except Exception as e:
        print(f"[WARN] fetch_spot_price failed for {symbol}: {e}")
        # TradingView fallback
        try:
            r = requests.get(f"https://in.tradingview.com/symbols/NSE-{symbol}/", timeout=10)
            m = re.search(r'"regularMarketPrice":([0-9]+\.[0-9]+)', r.text)
            if m:
                return float(m.group(1))
        except Exception as ee:
            print(f"[WARN] TradingView fallback failed: {ee}")
    return None

# -------------------------------------------------------------
# Option Chain (with local fallback)
# -------------------------------------------------------------
def fetch_option_chain(symbol: str):
    s = _session()
    try:
        url = f"{NSE_BASE}/api/option-chain-indices?symbol={symbol.upper()}"
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            url = f"{NSE_BASE}/api/option-chain-equities?symbol={symbol.upper()}"
        r = s.get(url, timeout=10)
        data = r.json()
        if "records" in data and "data" in data["records"]:
            return data
    except Exception as e:
        print(f"[WARN] NSE OC fetch failed for {symbol}: {e}")

    # Fallback to local sample if NSE fails
    sample_path = os.path.join(os.path.dirname(__file__), "sample_oc.json")
    if os.path.exists(sample_path):
        return json.load(open(sample_path))
    return {"records": {"data": []}}
