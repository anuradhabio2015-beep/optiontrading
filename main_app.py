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

# -------------------------------------------------------
# REMOVE STREAMLIT DEFAULT HEADER/FOOTER
# -------------------------------------------------------
hide_default = """
    <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_default, unsafe_allow_html=True)


# ----------------------------------------------------------
# CLEAN, FIXED UI CSS
# ----------------------------------------------------------
UI_STYLE = """
 <style>
        .header {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 60px;
            background-color: #2c6bed;
            color: white;
            padding-left: 20px;
            display: flex;
            align-items: center;
            font-size: 22px;
            font-weight: 700;
            z-index: 999;
            box-shadow: 0px 2px 4px rgba(0,0,0,0.2);
        }
        .content {
            padding-top: 80px;
            padding-left: 200px;
        }
    </style>
    <div class="header">MES Application</div>
"""
st.markdown(UI_STYLE, unsafe_allow_html=True)

# ----------------------------------------------------------
# CUSTOM HEADER
# ----------------------------------------------------------
LOGO_URL = "https://placehold.co/80x80/png?text=LOGO"

header_html = f"""
<div class="custom-header">
  <img src="{LOGO_URL}" width="68" height="68" style="border-radius:12px;"/>
  <div>
    <p class="title">Smart Trading App</p>
    <p class="subtitle">AI-Powered Options Dashboard — Analysis, Strategies & Execution</p>
  </div>
</div>
"""

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

st.markdown(header_html, unsafe_allow_html=True)
st.write("### 👋 Welcome! Your AI-powered options trading assistant is ready.")

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
