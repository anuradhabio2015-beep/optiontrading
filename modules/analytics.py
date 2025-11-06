import math, json, os
from .greeks import greeks

def extract_atm_strike(spot: float, step: int = 100):
    if not spot: return None
    return int(round(spot/step)*step)

def parse_chain(oc:dict):
    if not oc: return {"pcr":None,"max_pain":None,"strike_iv":{},"top_oi":[]}
    data = oc.get("records",{}).get("data",[])
    ce_oi=pe_oi=0; strike_oi={}; strike_iv={}
    for row in data:
        k=row.get("strikePrice")
        ce=row.get("CE") or {}; pe=row.get("PE") or {}
        if ce:
            ce_oi += ce.get("openInterest",0) or 0
            strike_oi.setdefault(k,{"CE":0,"PE":0})
            strike_oi[k]["CE"] += ce.get("openInterest",0) or 0
            if ce.get("impliedVolatility") is not None:
                strike_iv.setdefault(k,{}); strike_iv[k]["CE"]=ce.get("impliedVolatility")
        if pe:
            pe_oi += pe.get("openInterest",0) or 0
            strike_oi.setdefault(k,{"CE":0,"PE":0})
            strike_oi[k]["PE"] += pe.get("openInterest",0) or 0
            if pe.get("impliedVolatility") is not None:
                strike_iv.setdefault(k,{}); strike_iv[k]["PE"]=pe.get("impliedVolatility")
    pcr = (pe_oi/ce_oi) if ce_oi else None
    max_pain = None; max_tot=-1
    for k,v in strike_oi.items():
        tot = (v.get("CE",0) or 0)+(v.get("PE",0) or 0)
        if tot>max_tot: max_tot=tot; max_pain=k
    top_oi = sorted(strike_oi.items(), key=lambda kv: (kv[1]["CE"]+kv[1]["PE"]), reverse=True)[:5]
    return {"pcr":pcr,"max_pain":max_pain,"strike_iv":strike_iv,"top_oi":top_oi}

def compute_atm_iv(strike_iv:dict, spot:float, step:int=100):
    if not strike_iv or not spot: return None
    atm = extract_atm_strike(spot, step)
    row = strike_iv.get(atm) or {}
    ivs = []
    if "CE" in row: ivs.append(row["CE"])
    if "PE" in row: ivs.append(row["PE"])
    if not ivs: return None
    return sum(ivs)/len(ivs)/100.0

def expected_move(spot, iv, days):
    if not spot or not iv or iv<=0 or days<=0: return None, None
    move = spot*iv*math.sqrt(days/365.0); pct=(move/spot)*100
    return move, pct

def update_iv_history_and_rank(path, vix=None, atm_iv=None):
    try:
        hist = json.load(open(path,"r"))
    except Exception:
        hist={"vix":[],"atm_iv": []}
    if vix is not None: hist["vix"].append(vix)
    if atm_iv is not None: hist["atm_iv"].append(atm_iv*100 if atm_iv<5 else atm_iv)
    for k in hist: hist[k]=hist[k][-180:]
    def rank(vals, cur):
        if not vals or cur is None: return None, None
        lo,hi=min(vals),max(vals)
        r = (cur-lo)/(hi-lo)*100 if hi>lo else 50.0
        p = sum(1 for v in vals if v<=cur)/len(vals)*100.0
        return round(r,1), round(p,1)
    vr, vp = rank(hist["vix"], vix)
    ir, ip = rank(hist["atm_iv"], (atm_iv*100 if atm_iv and atm_iv<5 else atm_iv))
    try: json.dump(hist, open(path,"w"))
    except Exception: pass
    return {"vix_rank":vr,"vix_percentile":vp,"atm_iv_rank":ir,"atm_iv_percentile":ip}

def compute_core_metrics(symbol, spot, vix, oc, r=0.07, q=0.0, days=7):
    base = parse_chain(oc)
    atm_iv = compute_atm_iv(base.get("strike_iv"), spot, 100)
    em1,em1p = expected_move(spot, atm_iv, 1) if atm_iv else (None,None)
    em3,em3p = expected_move(spot, atm_iv, 3) if atm_iv else (None,None)
    # ATM Greeks (approx): T=days/365
    T = max(days,1)/365.0
    atmK = extract_atm_strike(spot, 100) if spot else None
    if atm_iv and spot and atmK:
        delta_c, theta_c, vega_c = greeks(spot, atmK, r, q, atm_iv, T, call=True)
        atm_greeks = (delta_c, theta_c, vega_c)
    else:
        atm_greeks = (None, None, None)
    base.update({"atm_iv":atm_iv,"expected_move_1d":(em1,em1p),"expected_move_3d":(em3,em3p),"atm_greeks":atm_greeks})
    # IV rank store
    ranks = update_iv_history_and_rank(os.path.join("data","iv_history.json"), vix=vix, atm_iv=atm_iv)
    base.update(ranks)
    return base
