import streamlit as st
import pandas as pd
import time
import os

from modules.ai_selector_gemini import ai_select_stocks_gemini
from modules.ai_explainer_gemini import ai_market_summary_gemini
from modules.data_fetcher import fetch_indices_nse, fetch_option_chain, fetch_spot_price
from modules.analytics import compute_core_metrics
from modules.strategy_engine import build_strategies
from modules.backtester import run_detailed_backtest
from modules.ai_trade_levels import ai_trade_levels
from modules.charts import plot_iv_rank_history, plot_expected_move_chart
from modules.order_executor import place_order_groww, place_order_zerodha

# ----------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------
st.set_page_config(
    page_title="Smart Trading App",
    page_icon="💹",
    layout="wide"
)

# ----------------------------------------------------------
# CLEAN, FIXED UI CSS
# ----------------------------------------------------------
UI_STYLE = """
<style>

body {
    font-family: 'Inter', sans-serif !important;
}

header {visibility: hidden;}
# header {visibility: visible !important;}
footer {visibility: hidden;}
[data-testid="stToolbar"] {display: none}

[data-testid="stSidebar"] {
    background-color: #f8f9ff !important;
    padding: 14px !important;
    border-right: 1px solid #e6e6e6;
}

.custom-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 26px;
  border-radius: 14px;
  margin-bottom: 14px;
  background: linear-gradient(90deg, #ffffff, #eef3ff);
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
}

.custom-header .title {
  font-size: 28px;
  font-weight: 800;
  margin: 0;
}

.custom-header .subtitle {
  font-size: 14px;
  color: #555;
  margin: 0;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
}

.stTabs [data-baseweb="tab"] {
    background-color: #f1f4ff !important;
    border-radius: 8px !important;
    padding: 6px 14px !important;
}

.stTabs [aria-selected="true"] {
    background-color: #2c6bed !important;
    color: white !important;
    font-weight: 600;
}

</style>
"""
st.markdown(UI_STYLE, unsafe_allow_html=True)

# ----------------------------------------------------------
# CUSTOM HEADER
# ----------------------------------------------------------
# LOGO_URL = "https://placehold.co/80x80/png?text=LOGO"
LOGO_URL = "data:image/svg+xml;utf8,\
<svg width='220' height='220' viewBox='0 0 220 220' xmlns='http://www.w3.org/2000/svg'>\
<defs>\
<linearGradient id='g1' x1='0%' y1='0%' x2='100%' y2='100%'>\
<stop offset='0%' stop-color='%2300B4D8'/>\
<stop offset='50%' stop-color='%2300D4A8'/>\
<stop offset='100%' stop-color='%2329E87C'/>\
</linearGradient>\
</defs>\
<circle cx='110' cy='110' r='95' fill='url(%23g1)'/>\
<!-- AI neural network nodes -->\
<circle cx='80' cy='80' r='8' fill='white'/>\
<circle cx='140' cy='70' r='8' fill='white'/>\
<circle cx='160' cy='120' r='8' fill='white'/>\
<circle cx='120' cy='150' r='8' fill='white'/>\
<circle cx='70' cy='140' r='8' fill='white'/>\
<!-- Network connections -->\
<line x1='80' y1='80' x2='140' y2='70' stroke='white' stroke-width='4' stroke-linecap='round'/>\
<line x1='140' y1='70' x2='160' y2='120' stroke='white' stroke-width='4' stroke-linecap='round'/>\
<line x1='160' y1='120' x2='120' y2='150' stroke='white' stroke-width='4' stroke-linecap='round'/>\
<line x1='120' y1='150' x2='70' y2='140' stroke='white' stroke-width='4' stroke-linecap='round'/>\
<line x1='70' y1='140' x2='80' y2='80' stroke='white' stroke-width='4' stroke-linecap='round'/>\
<!-- Candlestick chart -->\
<rect x='95' y='100' width='10' height='45' fill='white' rx='2'/>\
<rect x='115' y='85' width='10' height='65' fill='white' rx='2'/>\
<rect x='135' y='105' width='10' height='40' fill='white' rx='2'/>\
<line x1='100' y1='90' x2='100' y2='155' stroke='white' stroke-width='4' stroke-linecap='round'/>\
<line x1='120' y1='70' x2='120' y2='160' stroke='white' stroke-width='4' stroke-linecap='round'/>\
<line x1='140' y1='95' x2='140' y2='150' stroke='white' stroke-width='4' stroke-linecap='round'/>\
</svg>"


header_html = f"""
<div class="custom-header">
  <img src="{LOGO_URL}" width="68" height="68" style="border-radius:12px;"/>
  <div>
    <p class="title">Smart Trading App</p>
    <p class="subtitle">AI-Powered Options Dashboard — Analysis, Strategies & Execution</p>
  </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

st.write("### 👋 Welcome! Your AI-powered options trading assistant is ready.")



# ----------------------------------------------------------
# SIDEBAR CONFIG  (FULLY FIXED & VISIBLE)
# ----------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration Settings")

    gemini_key = st.text_input("🔑 Gemini API Key", type="password")
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        st.success("Gemini Key Loaded")
    else:
        st.warning("Enter Gemini API Key")

    st.markdown("### 🏦 Broker Settings")
    broker = st.radio("Select Broker", ["None", "Zerodha", "Groww"], index=0)

    if broker == "Zerodha":
        zerodha_api_key = st.text_input("Zerodha API Key", type="password")
        zerodha_access_token = st.text_input("Access Token", type="password")

    elif broker == "Groww":
        st.info("Groww works in **paper mode** only.")

    st.markdown("### 📊 Trading Inputs")

    default_universe = ["BANKNIFTY", "NIFTY", "RELIANCE", "HDFCBANK", "ICICIBANK"]
    symbol = st.selectbox("Select Symbol / Index", default_universe)

    strategy_focus = st.selectbox("Strategy Type", ["AI-Auto", "Iron Condor", "Credit Spread", "Calendar Spread"])
    capital = st.number_input("Portfolio Capital (₹)", 100000, 20000000, 200000, step=50000)
    risk_pct = st.slider("Risk % per Trade", 0.5, 5.0, 1.5)
    rfr = st.number_input("Risk-Free Rate", 0.0, 0.2, 0.07)
    expiry_days = st.slider("Days to Expiry", 1, 45, 15)

    run_ai = st.button("🚀 Run Analysis", use_container_width=True)

# if not gemini_key: 
#     st.stop()

# ----------------------------------------------------------
# RUN GEMINI
# ----------------------------------------------------------
if run_ai:
    with st.spinner(f"🤖 Running Gemini for {symbol}..."):
        try:
            st.session_state["ai_selection"] = ai_select_stocks_gemini([symbol])
            st.session_state["ai_summary"] = ai_market_summary_gemini(st.session_state["ai_selection"])
        except Exception as e:
            st.error(f"Gemini Error: {e}")
            st.session_state["ai_selection"] = [{"symbol": symbol, "bias": "neutral", "strategy": "Iron Condor"}]
            st.session_state["ai_summary"] = "Fallback summary."

if "ai_selection" not in st.session_state:
    st.info("Click **Run Analysis** to start.")
    st.stop()

selection = st.session_state["ai_selection"][0]


# ----------------------------------------------------------
# SAFE DATA FETCH
# ----------------------------------------------------------
def try_fetch_data(symbol):
    status = st.empty()
    for attempt in range(3):
        try:
            status.info(f"Fetching data... Attempt {attempt+1}/3")
            indices = fetch_indices_nse()
            spot = indices.get(symbol.upper()) or fetch_spot_price(symbol)
            vix = indices.get("INDIAVIX")
            oc = fetch_option_chain(symbol)
            metrics = compute_core_metrics(symbol, spot, vix, oc, r=rfr, days=expiry_days)
            pcr = metrics.get("pcr") if metrics else None
            if spot and vix and pcr:
                status.success(f"✅ Market data fetched successfully (Spot={spot:.2f}, VIX={vix:.2f}, PCR={round(pcr, 2)})")
                return spot, vix, pcr, oc, metrics
        except:
            time.sleep(1)
    status.error("❌ Failed to load market data")
    return None, None, None, None, None

spot, vix, pcr, oc, metrics = try_fetch_data(symbol)

if not spot or not vix or not pcr:
    st.error("Missing essential data. Retry later.")
    st.stop()

# ----------------------------------------------------------
# TABS
# ----------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 Market Snapshot", "🎯 Strategies", "🧮 Backtest", "⚙️ AI Levels", "🧠 Summary"]
)

# TAB 1
with tab1:
    st.subheader(f"{symbol} — Market Snapshot")
    col1, col2, col3 = st.columns(3)
    col1.metric("Spot", f"{spot:,.2f}")
    col2.metric("India VIX", f"{vix:.2f}")
    col3.metric("PCR (OI)", f"{pcr:.2f}")

    st.pyplot(plot_iv_rank_history())
    st.pyplot(plot_expected_move_chart(spot, metrics))

# TAB 2
with tab2:
    st.subheader("🎯 Strategy Ideas")
    strategies = build_strategies(symbol, oc, capital, risk_pct, metrics, r=rfr, days=expiry_days, focus=strategy_focus)
    st.dataframe(pd.DataFrame(strategies), use_container_width=True)

    st.markdown("### 🧾 Place Order")
    if broker == "Zerodha" and "zerodha_api_key" in locals() and zerodha_api_key:
        for strat in strategies:
            if st.button(f"📤 Zerodha — {strat['Strategy']}"):
                msg = place_order_zerodha(zerodha_api_key, zerodha_access_token, symbol, 48700, "CE", "28NOV24", 25, 120)
                st.success(msg)
    elif broker == "Groww":
        st.info("Groww Paper Mode")
        for strat in strategies:
            if st.button(f"💹 Groww — {strat['Strategy']}"):
                msg = place_order_groww(symbol, 48700, "CE", "28NOV24", 25, 120)
                st.success(msg)

# TAB 3
with tab3:
    st.subheader("🧮 Backtest Results")
    bt = run_detailed_backtest(symbol, strategies)
    st.dataframe(bt, use_container_width=True)
    st.line_chart(bt["Total Profit (₹)"])

# TAB 4
with tab4:
    st.subheader("⚙️ AI Entry / Exit / Stop Loss")
    ai_levels = [
        ai_trade_levels(symbol, spot, metrics.get("atm_iv_rank", 50), metrics.get("pcr", 1.0), strat["Strategy"])
        for strat in strategies
    ]
    st.dataframe(pd.DataFrame(ai_levels), use_container_width=True)

# TAB 5
with tab5:
    st.subheader("🧠 AI Summary")
    st.write(st.session_state["ai_summary"])
