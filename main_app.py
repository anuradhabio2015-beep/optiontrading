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


# ---------------------------------------------------------------------------
# 🌈 PAGE CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Smart Trading App",
    page_icon="💹",
    layout="wide"
)

# ---------------------------------------------------------------------------
# 🌈 GLOBAL CUSTOM UI / CSS
# ---------------------------------------------------------------------------
UI_STYLE = """
<style>

body {
    font-family: 'Inter', sans-serif !important;
}

/* FIX 1 — Do NOT override section.main because it breaks sidebar */
section.main > div {
    padding-top: 12px !important;
}

/* FIX 2 — Limit sticky header to the header only, not the whole container */
.custom-header {
  position: sticky;
  top: 0;
  z-index: 999;
}

/* FIX 3 — Sidebar padding fix */
[data-testid="stSidebar"] {
    background-color: #f6f7ff !important;
    padding-top: 20px !important;
}

/* Sidebar text and spacing */
[data-testid="stSidebar"] .block-container {
    padding: 20px 16px;
}

/* TABS STYLING */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
}

.stTabs [data-baseweb="tab"] {
    background-color: #f1f4ff !important;
    border-radius: 8px !important;
    padding: 6px 14px !important;
}

.stTabs [aria-selected="true"] {
    background-color: #2c6bed !important;
    color: white !important;
    font-weight: 600 !important;
}

/* Hide Streamlit default header/footer */
header {visibility: hidden !important;}
footer {visibility: hidden !important;}
[data-testid="stToolbar"] {display: none !important;}

</style>
"""

st.markdown(UI_STYLE, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 🌟 CUSTOM HEADER WITH LOGO
# ---------------------------------------------------------------------------
LOGO_URL = "https://placehold.co/80x80/png?text=LOGO"

header_html = f"""
<div class="custom-header">
  <img src="{LOGO_URL}" width="68" height="68" style="border-radius:12px;"/>
  <div>
    <p class="title">Smart Trading App</p>
    <p class="subtitle">AI-Powered Options Trading Assistant for Smarter, Safer Decisions.</p>
  </div>
  <div style="margin-left:auto; display:flex; gap:14px; align-items:center;">
    <a href="#" style="text-decoration:none; font-size:14px;">📄 Docs</a>
    <a href="#" style="text-decoration:none; font-size:14px;">🆘 Support</a>
  </div>
</div>
"""

st.markdown(header_html, unsafe_allow_html=True)

st.write("### 👋 Welcome! Your AI-powered options trading assistant is ready.")


# ---------------------------------------------------------------------------
# ⚙️ SIDEBAR CONFIG
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")

    gemini_key = st.text_input("🔑 Gemini API Key", type="password", placeholder="Enter Gemini Key")    
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        st.session_state["gemini_key"] = gemini_key
        st.success("Gemini Key Loaded ✅")
    else:
        st.warning("Please enter Gemini API Key")

    st.markdown("### 🏦 Broker Settings")
    broker = st.radio("Select Broker", ["None", "Zerodha", "Groww"], index=0)

    if broker == "Zerodha":
        zerodha_api_key = st.text_input("🔑 Zerodha API Key", type="password")
        zerodha_access_token = st.text_input("🎟️ Zerodha Access Token", type="password")
    elif broker == "Groww":
        st.info("Groww integration is simulated (no live API). Orders will be logged as paper trades.")

    st.markdown("### 🎯 Trading Inputs")

    default_universe = ["BANKNIFTY", "NIFTY", "RELIANCE", "HDFCBANK", "ICICIBANK"]
    symbol = st.selectbox("📊 Select Universe", options=default_universe, index=0)

    strategy_focus = st.selectbox("🎯 Strategy Focus", ["AI-Auto", "Iron Condor", "Credit Spread", "Calendar Spread"])
    capital = st.number_input("💰 Portfolio Capital (₹)", 100000, 10000000, 200000, step=50000)
    risk_pct = st.slider("Risk % per Trade", 0.5, 5.0, 1.5)
    rfr = st.number_input("Risk-Free Rate (annual)", 0.0, 0.2, 0.07, step=0.005)
    expiry_days = st.slider("Days to Expiry", 1, 45, 15)

    st.markdown("---")
    run_ai = st.button("🚀 Run Analysis", use_container_width=True)

if not gemini_key:
    st.stop()

# ---------------------------------------------------------------------------
# 🤖 AI PROCESSING
# ---------------------------------------------------------------------------
if run_ai:
    with st.spinner(f"🤖 Running Gemini for {symbol}..."):
        try:
            st.session_state["ai_selection"] = ai_select_stocks_gemini([symbol])
            st.session_state["ai_summary"] = ai_market_summary_gemini(st.session_state["ai_selection"])
        except Exception as e:
            st.error(f"⚠️ Gemini API error: {str(e)[:100]}")
            st.session_state["ai_selection"] = [{"symbol": symbol, "bias": "neutral", "strategy": "Iron Condor"}]
            st.session_state["ai_summary"] = "⚠️ Fallback summary."

if "ai_selection" not in st.session_state:
    st.info("👆 Click **Run Analysis** to start.")
    st.stop()

selection = st.session_state["ai_selection"][0]


# ---------------------------------------------------------------------------
# 📡 SAFE RETRY DATA FETCH BLOCK
# ---------------------------------------------------------------------------
def try_fetch_data(symbol, retries=3, delay=2):
    status = st.empty()

    for attempt in range(retries):
        try:
            status.info(f"🔄 Attempt {attempt+1}/{retries}: Fetching live market data...")

            indices = fetch_indices_nse()
            spot = indices.get(symbol.upper()) or fetch_spot_price(symbol)
            vix = indices.get("INDIAVIX") or indices.get("INDIA VIX")
            oc = fetch_option_chain(symbol)
            metrics = compute_core_metrics(symbol, spot, vix, oc, r=rfr, days=expiry_days)
            pcr = metrics.get("pcr") if metrics else None

            if spot and vix and pcr:
                status.success(f"✅ Success (Spot={spot:.2f}, VIX={vix:.2f}, PCR={round(pcr,2)})")
                return spot, vix, pcr, oc, metrics

            status.warning(f"⚠️ Missing Data (Spot={spot}, VIX={vix}, PCR={pcr})")
            time.sleep(delay)

        except Exception as e:
            status.error(f"⚠️ {str(e)[:100]}")
            time.sleep(delay)

    status.error("❌ Critical data missing. Try again later.")
    return None, None, None, None, None


spot, vix, pcr, oc, metrics = try_fetch_data(symbol)

if not spot or not vix or not pcr:
    st.error("❌ Could not fetch required market data.")
    st.stop()


# ---------------------------------------------------------------------------
# 📌 TABS
# ---------------------------------------------------------------------------
tab_market, tab_strategy, tab_backtest, tab_ai_levels, tab_summary = st.tabs(
    ["📈 Market Snapshot", "🎯 Strategy Ideas", "🧮 Backtest", "⚙️ AI Entry/Exit/SL", "🧠 Summary"]
)

# ---------------------------------------------------------------------------
# 📈 TAB 1 — MARKET SNAPSHOT
# ---------------------------------------------------------------------------
with tab_market:
    st.subheader(f"📊 {symbol} — Market Snapshot")

    c1, c2, c3 = st.columns(3)
    c1.metric("Spot", f"{spot:,.2f}")
    c2.metric("India VIX", f"{vix:.2f}")
    c3.metric("PCR (OI)", f"{pcr:.2f}")

    st.write(f"**IV Rank:** {metrics.get('atm_iv_rank','–')}")

    st.pyplot(plot_iv_rank_history())
    st.pyplot(plot_expected_move_chart(spot, metrics))

# ---------------------------------------------------------------------------
# 🎯 TAB 2 — STRATEGY IDEAS + ORDER MODULE
# ---------------------------------------------------------------------------
with tab_strategy:
    st.subheader("🎯 AI-Generated Strategy Ideas")

    strategies = build_strategies(symbol, oc, capital, risk_pct, metrics, r=rfr, days=expiry_days, focus=strategy_focus)

    st.dataframe(pd.DataFrame(strategies), use_container_width=True)

    st.markdown("### 🧾 Place Order")

    if broker == "Zerodha":
        if zerodha_api_key and zerodha_access_token:
            st.success("Zerodha Connected")
            for strat in strategies:
                if st.button(f"📤 Place {strat['Strategy']} in Zerodha", key=f"order_z_{strat['Strategy']}"):
                    msg = place_order_zerodha(
                        zerodha_api_key, zerodha_access_token, symbol,
                        48700, "CE", "28NOV24", 15, 120.0
                    )
                    st.success(msg)
        else:
            st.error("Enter Zerodha API Key + Access Token")

    elif broker == "Groww":
        st.info("Groww Paper Trading Mode")
        for strat in strategies:
            if st.button(f"💹 Paper Trade {strat['Strategy']}", key=f"order_g_{strat['Strategy']}"):
                msg = place_order_groww(symbol, 48700, "CE", "28NOV24", 15, 120.0)
                st.success(msg)

# ---------------------------------------------------------------------------
# 🧮 TAB 3 — BACKTEST
# ---------------------------------------------------------------------------
with tab_backtest:
    st.subheader("🧮 Backtest Results")
    bt = run_detailed_backtest(symbol, strategies)
    st.dataframe(bt, use_container_width=True)
    st.line_chart(bt["Total Profit (₹)"])

# ---------------------------------------------------------------------------
# ⚙️ TAB 4 — AI ENTRY/EXIT/SL
# ---------------------------------------------------------------------------
with tab_ai_levels:
    st.subheader("⚙️ AI Entry, Exit & Stop-Loss Levels")
    ai_levels = []
    for strat in strategies:
        ai_levels.append(
            ai_trade_levels(symbol, spot, metrics.get("atm_iv_rank", 50), metrics.get("pcr", 1.0), strat["Strategy"])
        )
    st.dataframe(pd.DataFrame(ai_levels), use_container_width=True)

# ---------------------------------------------------------------------------
# 🧠 TAB 5 — MARKET SUMMARY
# ---------------------------------------------------------------------------
with tab_summary:
    st.subheader("🧠 AI Summary & Insights")
    st.write(st.session_state["ai_summary"])
    st.caption("⚠️ Educational use only. Not financial advice.")
