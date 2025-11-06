# AI Options Trader — Gemini Pro (Full Code)

This is the **full** Streamlit + Python project wired to **Google Gemini API** for AI-driven
option-selling selection, with NSE fallback, Greeks, IV Rank, expected-move charts,
toy backtesting, and broker order stubs (Groww/Zerodha).

## Quick Start
```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export GEMINI_API_KEY=your_key_here    # https://aistudio.google.com/app/apikey
streamlit run main_app.py
```

## Notes
- Educational/analysis only — **not** financial advice.
- For live trading, replace stubs in `modules/order_executor.py` with broker SDK calls.
- For real backtests, connect an options history dataset (NSE Bhavcopy or vendor).

