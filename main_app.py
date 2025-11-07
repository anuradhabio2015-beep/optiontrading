import streamlit as st
import pandas as pd
import os

from modules.ai_selector_gemini import ai_select_stocks_gemini
from modules.ai_explainer_gemini import ai_market_summary_gemini
from modules.data_fetcher import fetch_option_chain, fetch_indices_nse
from modules.analytics import compute_core_metrics
from modules.strategy_engine import build_strategies
from modules.backtester import run_backtest_for_symbol
from modules.order_executor import place_order_groww, place_order_zerodha
from modules.charts import plot_iv_rank_history, plot_expected_move_chart

# --------------------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------------------
st.set_page_config(layout="wide", page_title="Smart Option Trading App")
st.title("🤖 Smart Option Selling Dashboard — Gemini Pro (Single Symbol)")

# --------------------------------------------------------------
# SIDEBAR CONFIGURATION
# --------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")

    # --- Gemini API Key ---
    gemini_key = st.text_input("🔑 Gemini API Key", type="password", placeholder="Paste your Gemini key here")
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        st.session_state["gemini_key"] = gemini_key
        st.success("Gemini API Key set ✅")
    else:
        st.warning("Enter your Gemini API Key to enable AI selection")

    # --- Universe Dropdown (Single selection only) ---
    default_universe = [
        "BANKNIFTY", "NIFTY", "RELIANCE", "HDFCBANK",
        "ICICIBANK", "INFY", "SBIN", "TCS",
        "TATAMOTORS", "AXISBANK", "LT", "HINDUNILVR"
    ]
    selected_symbol = st.selectbox(
        "📊 Select Index or Stock (Single)",
        options=default_universe,
        index=0,
        help="Choose one symbol for option analysis"
    )
    st.session_state["selected_symbol"] = selected_symbol

    # --- Strategy Focus ---
    strategy_focus = st.selectbox(
        "🎯 Strategy Focus",
        ["AI-Auto", "Iron Condor", "Credit Spread", "Calendar Spread"],
        index=0
    )
    st.session_state["strategy_focus"] = strategy_focus

    # --- Risk Parameters ---
    capital = st.number_input("💰 Portfolio Capital (₹)", 100000, 10000000, 200000, step=50000)
    risk_pct = st.slider("Risk % per Trade", 0.5, 5.0, 1.5)
    rfr = st.number_input("Risk-Free Rate (annual)", 0.0, 0.2, 0.07, step=0.005, format="%.3f")
    expiry_days = st.slider("Days to expiry (estimate)", 1, 30, 7)

    st.session_state.update({
        "capital": capital,
        "risk_pct": risk_pct,
        "rfr": rfr,
        "expiry_days": expiry_days
    })

    st.markdown("---")
    run_ai = st.button("🚀 Run Gemini AI Selection", use_container_width=True)

# --------------------------------------------------------------
# VALIDATION
# --------------------------------------------------------------
if not gemini_key:
    st.stop()

if not selected_symbol:
    st.warning("⚠️ Please select one symbol to continue.")
    st.stop()

# --------------------------------------------------------------
# AI SELECTION
# --------------------------------------------------------------
if run_ai or "ai_selection" not in st.session_state:
    with st.spinner(f"🤖 Running Gemini AI selection for {selected_symbol}..."):
        st.session_state["ai_selection"] = ai_select_stocks_gemini([selected_symbol])
        st.session_state["ai_summary"] = ai_market_summary_gemini(st.session_state["ai_selection"])

# --------------------------------------------------------------
# DISPLAY ANALYTICS (ONE SYMBOL)
# --------------------------------------------------------------
selection = st.session_state["ai_selection"][0]
symbol = selection.get("symbol")

st.markdown(f"## 📈 {symbol} — {selection.get('strategy')} ({selection.get('bias')})")

# --- Fetch Data ---
oc = fetch_option_chain(symbol)
indices = fetch_indices_nse()
spot = indices.get(symbol)
vix = indices.get("INDIA VIX")

# --- Compute Metrics ---
metrics = compute_core_metrics(symbol, spot, vix, oc, r=rfr, days=expiry_days)

# --- Display Summary Metrics ---
c1, c2, c3 = st.columns(3)
c1.metric("Spot", f"{spot or '-'}")
c2.metric("India VIX", f"{round(vix,2) if vix else '-'}")
c3.metric("PCR (OI)", f"{round(metrics.get('pcr'),2) if metrics.get('pcr') else '-'}")

st.write("**IV Rank / Percentile (ATM / VIX)**:",
         f"{metrics.get('atm_iv_rank')} / {metrics.get('vix_rank')} |",
         f"{metrics.get('atm_iv_percentile')}% / {metrics.get('vix_percentile')}%")

st.write("**Expected Move**: 1D ±{} ({}%), 3D ±{} ({}%)".format(
    *(round(x,1) if x is not None else '-' for x in [
        metrics.get('expected_move_1d', (None,None))[0],
        metrics.get('expected_move_1d', (None,None))[1],
        metrics.get('expected_move_3d', (None,None))[0],
        metrics.get('expected_move_3d', (None,None))[1],
    ])
))
st.write("**Max Pain**:", metrics.get("max_pain"))

greeks = metrics.get("atm_greeks", (None,None,None))
st.write("**ATM Greeks (approx)**: Δ {}, Θ {}, Vega {}".format(
    *(round(x,3) if x is not None else '-' for x in greeks)
))

# --- Charts ---
st.pyplot(plot_iv_rank_history())
st.pyplot(plot_expected_move_chart(spot, metrics))

# --- Strategies ---
strategies = build_strategies(symbol, oc, capital, risk_pct, metrics, r=rfr, days=expiry_days)
st.subheader("🧮 Suggested Strategies")
st.dataframe(pd.DataFrame(strategies))

# --- Backtest ---
st.subheader("📊 Backtest (Toy Simulation)")
bt = run_backtest_for_symbol(symbol, strategies)
st.dataframe(bt)

# --- Order Buttons ---
cA, cB = st.columns(2)
with cA:
    if st.button(f"🚀 Send {symbol} to Groww (dry-run)", key=f"groww_{symbol}"):
        st.success(place_order_groww(strategies))
with cB:
    if st.button(f"🚀 Send {symbol} to Zerodha (dry-run)", key=f"zerodha_{symbol}"):
        st.success(place_order_zerodha(strategies))

# --- Market Summary ---
st.markdown("### 🧭 AI Market Summary")
st.write(st.session_state.get("ai_summary", "—"))

st.caption("Disclaimer: Educational/analysis only. Not financial advice.")
