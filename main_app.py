import streamlit as st
import pandas as pd
import os

from modules.ai_selector_gemini import ai_select_stocks_gemini
from modules.ai_explainer_gemini import ai_market_summary_gemini
from modules.data_fetcher import fetch_option_chain, fetch_indices_nse, fetch_spot_price
from modules.analytics import compute_core_metrics
from modules.strategy_engine import build_strategies
from modules.backtester import run_detailed_backtest
from modules.order_executor import place_order_groww, place_order_zerodha
from modules.charts import plot_iv_rank_history, plot_expected_move_chart

st.set_page_config(layout="wide", page_title="Smart Option Selling Dashboard — Gemini Pro Final")
st.title("🤖 Smart Option Selling Dashboard — Gemini Pro (Final Detailed Version)")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")

    gemini_key = st.text_input("🔑 Gemini API Key", type="password", placeholder="Paste your Gemini key here")
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        st.session_state["gemini_key"] = gemini_key
        st.success("Gemini API Key set ✅")
    else:
        st.warning("Enter Gemini API Key to enable AI selection")

    default_universe = ["BANKNIFTY", "NIFTY", "RELIANCE", "HDFCBANK", "ICICIBANK"]
    selected_symbol = st.selectbox("📊 Select Index/Stock", options=default_universe, index=0)

    strategy_focus = st.selectbox(
        "🎯 Strategy Focus",
        ["AI-Auto", "Iron Condor", "Credit Spread", "Calendar Spread"],
        index=0
    )

    capital = st.number_input("💰 Portfolio Capital (₹)", 100000, 10000000, 200000, step=50000)
    risk_pct = st.slider("Risk % per Trade", 0.5, 5.0, 1.5)
    rfr = st.number_input("Risk-Free Rate (annual)", 0.0, 0.2, 0.07, step=0.005, format="%.3f")
    expiry_days = st.slider("Days to expiry (estimate)", 1, 45, 15)

    st.session_state.update({
        "symbol": selected_symbol,
        "strategy_focus": strategy_focus,
        "capital": capital,
        "risk_pct": risk_pct,
        "rfr": rfr,
        "expiry_days": expiry_days
    })

    st.markdown("---")
    run_ai = st.button("🚀 Run Analysis", use_container_width=True)

if not gemini_key:
    st.stop()

symbol = st.session_state["symbol"]
strategy_focus = st.session_state["strategy_focus"]

if run_ai:
    with st.spinner(f"🤖 Running Gemini for {symbol}..."):
        st.session_state["ai_selection"] = ai_select_stocks_gemini([symbol])
        st.session_state["ai_summary"] = ai_market_summary_gemini(st.session_state["ai_selection"])
elif "ai_selection" not in st.session_state:
    st.info("👆 Click **Run Analysis** to start Gemini AI processing.")


if "ai_selection" not in st.session_state:
    st.info("👆 Click **Run Analysis** to generate Gemini AI selection and strategies.")
    st.stop()

selection = st.session_state["ai_selection"][0]

st.markdown(f"## 📈 {symbol} — {strategy_focus}")

indices = fetch_indices_nse()
spot = indices.get(symbol.upper()) or fetch_spot_price(symbol)
vix = indices.get("INDIAVIX", 14.0)
oc = fetch_option_chain(symbol)

metrics = compute_core_metrics(symbol, spot, vix, oc, r=rfr, days=expiry_days)

c1, c2, c3 = st.columns(3)
c1.metric("Spot", f"{spot or '-'}")
c2.metric("India VIX", f"{round(vix,2)}")
c3.metric("PCR (OI)", f"{round(metrics.get('pcr'),2) if metrics.get('pcr') else '-'}")

st.write("**IV Rank:**", metrics.get("atm_iv_rank"), "| **Expected Move (1D):**", metrics.get("expected_move_1d"))
st.pyplot(plot_iv_rank_history())
st.pyplot(plot_expected_move_chart(spot, metrics))

strategies = build_strategies(symbol, oc, capital, risk_pct, metrics, r=rfr, days=expiry_days, focus=strategy_focus)
st.subheader("🧮 Generated Strategy")
st.dataframe(pd.DataFrame(strategies))

st.subheader("📊 Backtest Results (Detailed)")
bt = run_detailed_backtest(symbol, strategies)

st.subheader("📊 Backtest Results (Detailed)")
st.dataframe(bt, use_container_width=True)

st.markdown(f"**Total P/L:** ₹{bt['P/L (₹)'].sum():,.0f} | "
            f"Avg Return: {bt['Return (%)'].mean():.2f}% | "
            f"Average POP: {bt['POP (%)'].mean():.1f}%")

# Optional Chart
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot(bt["Total Profit (₹)"], marker="o")
ax.set_title(f"{symbol} Backtest P/L Curve")
ax.set_xlabel("Trades")
ax.set_ylabel("Cumulative Profit (₹)")
st.pyplot(fig)


cA, cB = st.columns(2)
with cA:
    if st.button(f"🚀 Send {symbol} to Groww (dry-run)", key=f"groww_{symbol}"):
        st.success(place_order_groww(strategies))
with cB:
    if st.button(f"🚀 Send {symbol} to Zerodha (dry-run)", key=f"zerodha_{symbol}"):
        st.success(place_order_zerodha(strategies))

st.markdown("### 🧭 AI Market Summary")
st.write(st.session_state.get("ai_summary", "—"))
st.caption("Disclaimer: Educational/analysis only. Not financial advice.")
