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

st.set_page_config(page_title="Smart Option Selling Dashboard", layout="wide")
st.title("🤖 Smart Option Selling Dashboard — Gemini Pro (Tabs Edition)")

# ----------------------------------------------------------------
# Sidebar Configuration
# ----------------------------------------------------------------
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


    default_universe = ["BANKNIFTY", "NIFTY", "RELIANCE", "HDFCBANK", "ICICIBANK"]
    symbol = st.selectbox("📊 Select Universe (Index or Stock)", options=default_universe, index=0)

    strategy_focus = st.selectbox("🎯 Strategy Focus", ["AI-Auto", "Iron Condor", "Credit Spread", "Calendar Spread"])
    capital = st.number_input("💰 Portfolio Capital (₹)", 100000, 10000000, 200000, step=50000)
    risk_pct = st.slider("Risk % per Trade", 0.5, 5.0, 1.5)
    rfr = st.number_input("Risk-Free Rate (annual)", 0.0, 0.2, 0.07, step=0.005)
    expiry_days = st.slider("Days to Expiry (Estimate)", 1, 45, 15)

    st.markdown("---")
    run_ai = st.button("🚀 Run Analysis", use_container_width=True)

# ----------------------------------------------------------------
# AI Trigger & Market Data Fetch
# ----------------------------------------------------------------
if not gemini_key:
    st.stop()

# Only run Gemini when button pressed
if run_ai:
    with st.spinner(f"🤖 Running Gemini for {symbol}..."):
        try:
            st.session_state["ai_selection"] = ai_select_stocks_gemini([symbol])
            st.session_state["ai_summary"] = ai_market_summary_gemini(st.session_state["ai_selection"])
        except Exception as e:
            st.error(f"⚠️ Gemini API error: {str(e)[:100]}")
            st.session_state["ai_selection"] = [{"symbol": symbol, "bias": "neutral", "strategy": "Iron Condor"}]
            st.session_state["ai_summary"] = "⚠️ Fallback summary due to Gemini error"

if "ai_selection" not in st.session_state:
    st.info("👆 Click 'Run Analysis' to start Gemini AI analysis.")
    st.stop()

selection = st.session_state["ai_selection"][0]
# indices = fetch_indices_nse()
# spot = indices.get(symbol.upper()) or fetch_spot_price(symbol)
# vix = indices.get("INDIAVIX", 14.0)
# oc = fetch_option_chain(symbol)
# metrics = compute_core_metrics(symbol, spot, vix, oc, r=rfr, days=expiry_days)

import time

# --- Retry logic for critical market data ---
def try_fetch_data(symbol, retries=3, delay=2):
    status = st.empty()  # placeholder for single-line status updates

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
                status.success(f"✅ Market data fetched successfully (Spot={spot:.2f}, VIX={vix:.2f}, PCR={round(pcr, 2)})")
                return spot, vix, pcr, oc, metrics

            status.warning(
                f"⚠️ Attempt {attempt+1}/{retries} failed: Missing data "
                f"(Spot={spot}, VIX={vix}, PCR={pcr})"
            )
            time.sleep(delay)

        except Exception as e:
            status.error(f"⚠️ Attempt {attempt+1}/{retries} failed: {str(e)[:100]}")
            time.sleep(delay)

    status.error("❌ Failed to fetch Spot, India VIX, or PCR after multiple retries.")
    return None, None, None, None, None

# --- Run safe fetch ---
spot, vix, pcr, oc, metrics = try_fetch_data(symbol)

# --- Stop if still missing ---
if not spot or not vix or not pcr:
    # st.error("❌ Critical data missing: Unable to fetch Spot, India VIX, or PCR (OI). Please retry later.")
    if st.button("🔁 Retry Fetch Data"):
        st.rerun()
    st.stop()

# ----------------------------------------------------------------
# Create Tabs for Organized Layout
# ----------------------------------------------------------------
tab_market, tab_strategy, tab_backtest, tab_ai_levels, tab_summary = st.tabs(
    ["📈 Market Snapshot", "🎯 Strategy Ideas", "🧮 Backtest", "⚙️ AI Entry/Exit/SL", "🧠 Summary"]
)

# ----------------------------------------------------------------
# TAB 1: Market Snapshot
# ----------------------------------------------------------------
with tab_market:
    st.subheader(f"📊 {symbol} — Market Snapshot")
    c1, c2, c3 = st.columns(3)
    c1.metric("Spot", f"{spot:,.2f}")
    c2.metric("India VIX", f"{vix:.2f}")
    c3.metric("PCR (OI)", f"{pcr:.2f}")

    st.write(f"**IV Rank:** {metrics.get('atm_iv_rank', '–')} | **Expected Move (1D):** {metrics.get('expected_move_1d')}")
    st.pyplot(plot_iv_rank_history())
    st.pyplot(plot_expected_move_chart(spot, metrics))

# ----------------------------------------------------------------
# TAB 2: Strategy Ideas
# ----------------------------------------------------------------
with tab_strategy:
    st.subheader("🎯 AI-Generated Strategy Ideas")
    strategies = build_strategies(symbol, oc, capital, risk_pct, metrics, r=rfr, days=expiry_days, focus=strategy_focus)
    st.dataframe(pd.DataFrame(strategies), use_container_width=True)

# ----------------------------------------------------------------
# TAB 3: Backtest
# ----------------------------------------------------------------
with tab_backtest:
    st.subheader("🧮 Backtest Results")
    bt = run_detailed_backtest(symbol, strategies)
    st.dataframe(bt, use_container_width=True)
    st.line_chart(bt["Total Profit (₹)"], height=200)

# ----------------------------------------------------------------
# TAB 4: AI Entry/Exit/Stop-Loss
# ----------------------------------------------------------------
with tab_ai_levels:
    st.subheader("⚙️ AI Entry, Exit & Stop-Loss")
    ai_levels = []
    for strat in strategies:
        ai_level = ai_trade_levels(symbol, spot, metrics.get("atm_iv_rank", 50), metrics.get("pcr", 1.0), strat["Strategy"])
        ai_levels.append(ai_level)
    st.dataframe(pd.DataFrame(ai_levels), use_container_width=True)

# ----------------------------------------------------------------
# TAB 5: AI Market Summary
# ----------------------------------------------------------------
with tab_summary:
    st.subheader("🧠 AI Summary & Insights")
    st.write(st.session_state["ai_summary"])
    st.caption("⚠️ Educational use only. Not financial advice.")
