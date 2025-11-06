import os, json, re
import google.generativeai as genai

def _call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro-latest")
    # "model_signals": "gemini-flash-latest"
    # "model_sentiment": "gemini-pro-latest",
    
    resp = model.generate_content(prompt)
    return resp.text

def ai_select_stocks_gemini(symbols: list):
    prompt = f"""You are an expert option-seller in Indian markets.
Given this universe: {', '.join(symbols)},
pick the best 5 for short volatility (iron condor/credit spread/calendar).
Return STRICT JSON list with keys: symbol, bias, strategy, rationale.
Example:
[{{"symbol":"BANKNIFTY","bias":"neutral","strategy":"Iron Condor","rationale":"..."}}]
"""
    text = _call_gemini(prompt)
    if not text:
        return [{"symbol": s, "bias": "neutral", "strategy": "Iron Condor", "rationale": "Fallback"} for s in symbols[:5]]
        # return [{{"symbol": s, "bias":"neutral", "strategy":"Iron Condor", "rationale":"Fallback"}} for s in symbols[:5]]
    try:
        m = re.search(r"\[.*\]", text, re.S)
        if m:
            return json.loads(m.group(0))
    except Exception:
        pass
    # return [{{"symbol": s, "bias":"neutral", "strategy":"Iron Condor", "rationale":"Parse fallback"}} for s in symbols[:5]]
    return [{"symbol": s, "bias": "neutral", "strategy": "Iron Condor", "rationale": "Parse fallback"} for s in symbols[:5]]

