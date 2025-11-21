import os
import google.generativeai as genai

def ai_market_summary_gemini(selection: list):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Set GEMINI_API_KEY to enable AI summary."
    genai.configure(api_key=api_key)
    # model = genai.GenerativeModel("gemini-pro-latest") # gemini-3-pro-preview
    model = genai.GenerativeModel("gemini-3-pro-preview")  
    prompt = f"""Summarize the market bias and risk outlook for option selling
based on these AI‑selected opportunities (JSON): {selection}.
Keep to 6–8 bullet points, neutral tone, include IV/VIX cautions and event risk.
"""
    return model.generate_content(prompt).text
