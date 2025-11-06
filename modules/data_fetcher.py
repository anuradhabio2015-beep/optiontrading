import requests, time
BASE = "https://www.nseindia.com"
HDRS = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept":"application/json, text/plain, */*"
}
S = requests.Session()
S.headers.update(HDRS)
try:
    S.get(BASE, timeout=10)
except Exception:
    pass

def _get_json(url):
    for i in range(5):
        try:
            r = S.get(url, timeout=10)
            return r.json()
        except Exception:
            time.sleep(0.5+i*0.5)
    return {}

def fetch_option_chain(symbol="BANKNIFTY"):
    d = _get_json(BASE+f"/api/option-chain-indices?symbol={symbol}")
    if not d or "records" not in d:
        d = _get_json(BASE+f"/api/option-chain-equities?symbol={symbol}")
    return d

def fetch_indices_nse():
    data = _get_json(BASE+"/api/allIndices")
    out={}
    for row in data.get("data",[]):
        out[row.get("index")] = row.get("last")
    return out
