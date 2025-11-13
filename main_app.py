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
# UI CSS — HIDES SIDEBAR COMPLETELY for FULLSCREEN UI
# ----------------------------------------------------------
UI_STYLE = """
<style>
header {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stToolbar"] {display: none;}
[data-testid="stSidebar"] {display: none !important;}

body {font-family: 'Inter', sans-serif;}

.custom-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 18px;
  border-radius: 12px;
  margin-bottom: 14px;
  background: linear-gradient(90deg, #ffffff, #eef3ff);
  box-shadow: 0 6px 22px rgba(11,22,60,0.06);
}

.custom-header .title {
  font-size: 26px;
  font-weight: 800;
  margin: 0;
}

.custom-header .subtitle {
  font-size: 13px;
  color: #555;
  margin: 0;
}

/* Tab Styles */
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] {
    background-color: #f4f6ff !important;
    border-radius: 8px !important;
    padding: 6px 14px !important;
}
.stTabs [aria-selected="true"] {
    background-color: #2b6bed !important;
    color: white !important;
    font-weight: 600;
}
</style>
"""
st.markdown(UI_STYLE, unsafe_allow_html=True)

# ----------------------------------------------------------
# LOGO + HEADER
# ----------------------------------------------------------
LOGO_URL = "data:image/svg+xml;utf8,\
<svg width='220' height='220' viewBox='0 0 220 220' xmlns='http://www.w3.org/2000/svg'>\
<defs>\
<linearGradient id='g1' x1='0%' y1='0%' x2='100%' y2='100%'>\
<stop offset='0%' stop-color='%2300B4D8'/>\
<stop offset='50%' stop-color='%2300D4A8'/>\
<stop offset='100%' stop-color='%2329E87C'/>\
</linearGradient></defs>\
<circle cx='110' cy='110' r='95' fill='url(%23g1)'/>\
<circle cx='80' cy='80' r='8' fill='white'/>\
<circle cx='140' cy='70' r='8' fill='white'/>\
<circle cx='160' cy='120' r='8' fill='white'/>\
<circle cx='120' cy='150' r='8' fill='white'/>\
<circle cx='70' cy='140' r='8' fill='white'/>\
<line x1='80' y1='80' x2='140' y2='70' stroke='white' stroke-width='4'/>\
<line x1='140' y1='70' x2='160' y2='120' stroke='white' stroke-width='4'/>\
<line x1='160' y1='120' x2='120' y2='150' stroke='white' stroke-width='4'/>\
<line x1='120' y1='150' x2='70' y2='140' stroke='white' stroke-width='4'/>\
<line x1='70' y1='140' x2='80' y2='80' stroke='white' stroke-width='4'/>\
</svg>"

st.markdown(
    f"""
<div class="custom-header">
    <img src="{LOGO_URL}" width="64" height="64" style="border-radius:12px;">
    <div>
        <p class="title">Smart Trading App</p>
        <p class="subtitle">AI-Powered Options Dashboard — Analysis, Strategies & Execution</p>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# st.write("### 👋 Welcome! Your AI-powered options trading assistant is ready.")

# ----------------------------------------------------------
# TABS — NEW CONFIG TAB ADDED
# ----------------------------------------------------------
tab_config, tab_market, tab_strategy, tab_backtest, tab_ai_levels, tab_summary = st.tabs(
    [ "📈 Market Snapshot", "🎯 Strategy Ideas", "🧮 Backtest", "⚙️ AI Levels", "🧠 Summary","⚙️Configuration"]
)

# ==========================================================
# TAB 1 — MARKET SNAPSHOT
# ==========================================================
with tab_market:
    st.subheader(f"📈 Market Snapshot — {symbol}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Spot", f"{spot:,.2f}")
    c2.metric("India VIX", f"{vix:.2f}")
    c3.metric("PCR (OI)", f"{pcr:.2f}")

    st.pyplot(plot_iv_rank_history())
    st.pyplot(plot_expected_move_chart(spot, metrics))

# ==========================================================
# TAB 2 — STRATEGIES
# ==========================================================
with tab_strategy:
    st.subheader("🎯 AI Strategy Suggestions")
    strategies = build_strategies(symbol, oc, capital, risk_pct, metrics, days=expiry_days, focus=strategy_focus)
    st.dataframe(pd.DataFrame(strategies), use_container_width=True)

    st.markdown("### Order Execution")

    if broker == "Zerodha" and zerodha_api_key:
        st.success("Zerodha Connected")

        for i, strat in enumerate(strategies):
            if st.button(f"📤 Place {strat['Strategy']} (Zerodha)", key=f"ord_z_{i}"):
                msg = place_order_zerodha(
                    zerodha_api_key, zerodha_access_token, symbol,
                    48700, "CE", "28NOV24", 25, 120
                )
                st.success(msg)

    elif broker == "Groww":
        st.info("Groww Paper Trading Mode")
        for i, strat in enumerate(strategies):
            if st.button(f"💹 Paper Trade {strat['Strategy']}", key=f"ord_g_{i}"):
                msg = place_order_groww(symbol, 48700, "CE", "28NOV24", 25, 120)
                st.success(msg)

# ==========================================================
# TAB 3 — BACKTEST
# ==========================================================
with tab_backtest:
    st.subheader("🧮 Backtest Results")
    bt = run_detailed_backtest(symbol, strategies)
    st.dataframe(bt, use_container_width=True)
    if "Total Profit (₹)" in bt:
        st.line_chart(bt["Total Profit (₹)"])

# ==========================================================
# TAB 4 — AI LEVELS
# ==========================================================
with tab_ai_levels:
    st.subheader("⚙️ AI Entry / Exit / Stop-Loss Levels")
    ai_levels = [
        ai_trade_levels(symbol, spot, metrics.get("atm_iv_rank", 50), metrics.get("pcr", 1.0), strat["Strategy"])
        for strat in strategies
    ]
    st.dataframe(pd.DataFrame(ai_levels), use_container_width=True)

# ==========================================================
# TAB 5 — SUMMARY
# ==========================================================
with tab_summary:
    st.subheader("🧠 AI Summary & Insights")
    st.write(st.session_state["ai_summary"])
    st.caption("⚠️ Educational use only. Not financial advice.")


# ==========================================================
# TAB 6 — CONFIGURATION  (Replacing Sidebar Completely)
# ==========================================================
with tab_config:
    st.subheader("⚙️ Application & Trading Settings")

    col1, col2 = st.columns(2)

    # LEFT SIDE
    with col1:
        gemini_key = st.text_input("🔑 Gemini API Key", type="password")
        broker = st.selectbox("Broker", ["None", "Zerodha", "Groww"])

        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key
            st.session_state["gemini_key"] = gemini_key

        if broker == "Zerodha":
            zerodha_api_key = st.text_input("Zerodha API Key", type="password")
            zerodha_access_token = st.text_input("Zerodha Access Token", type="password")
        else:
            zerodha_api_key = None
            zerodha_access_token = None

    # RIGHT SIDE
    with col2:
        symbol = st.selectbox("Select Symbol/Index", ["BANKNIFTY", "NIFTY", "RELIANCE", "HDFCBANK", "ICICIBANK"])
        strategy_focus = st.selectbox("Strategy Focus", ["AI-Auto", "Iron Condor", "Credit Spread", "Calendar Spread"])
        capital = st.number_input("Portfolio Capital (₹)", 100000, 20000000, 200000, step=50000)
        risk_pct = st.slider("Risk % per Trade", 0.5, 5.0, 1.5)
        expiry_days = st.slider("Days to Expiry", 1, 45, 15)

    run_ai = st.button("🚀 Run AI Analysis", use_container_width=True)

# ==========================================================
# AI CALL
# ==========================================================
if run_ai:
    with st.spinner(f"🤖 Running Gemini for {symbol}..."):
        try:
            st.session_state["ai_selection"] = ai_select_stocks_gemini([symbol])
            st.session_state["ai_summary"] = ai_market_summary_gemini(st.session_state["ai_selection"])
        except Exception as e:
            st.error(f"Gemini API Error: {str(e)[:120]}")
            st.session_state["ai_selection"] = [{"symbol": symbol, "bias": "neutral", "strategy": "Iron Condor"}]
            st.session_state["ai_summary"] = "Fallback summary due to error."

if "ai_selection" not in st.session_state:
    st.stop()

selection = st.session_state["ai_selection"][0]

# ==========================================================
# MARKET DATA FETCH (Safe)
# ==========================================================
def try_fetch(symbol):
    status = st.empty()
    for attempt in range(3):
        try:
            status.info(f"Attempt {attempt+1}/3 — Fetching live data...")
            indices = fetch_indices_nse()
            spot = indices.get(symbol.upper()) or fetch_spot_price(symbol)
            vix = indices.get("INDIAVIX")
            oc = fetch_option_chain(symbol)
            metrics = compute_core_metrics(symbol, spot, vix, oc, days=expiry_days)
            pcr = metrics.get("pcr")

            if spot and vix and pcr:
                status.success("Live data loaded.")
                return spot, vix, pcr, oc, metrics
        except:
            time.sleep(1)

    status.error("❌ Failed to fetch data.")
    return None, None, None, None, None

spot, vix, pcr, oc, metrics = try_fetch(symbol)

if not spot: st.stop()

