import os, json, re
import google.generativeai as genai
from google.api_core import exceptions

def _call_gemini(prompt):
    try:
        model = genai.GenerativeModel("gemini-flash-lite-latest")
        resp = model.generate_content(prompt)
        return resp.text
    except exceptions.ResourceExhausted:
        return "[AI Error] Gemini API quota exhausted. Try again later or use cached analysis."
    except exceptions.GoogleAPIError as e:
        return f"[AI Error] Gemini API unavailable: {str(e)[:120]}"
    except Exception as e:
        return f"[AI Error] Unexpected: {str(e)[:120]}"
        
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

