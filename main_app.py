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


# --- Streamlit setup ---
st.set_page_config(layout="wide", page_title="Smart Option Selling — Gemini Pro")

st.title("🤖 Smart Option Selling Dashboard (Gemini Pro)")
st.caption("AI-driven short volatility strategies with NSE live data, IV ranks, and Greeks.")

# --- Sidebar configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")

    # Store persistent state
    if "filters" not in st.session_state:
        st.session_state.filters = {}

    # Gemini API Key input
    gemini_key = st.text_input("🔑 Gemini API Key", type="password", placeholder="Paste your Gemini key here")
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        st.session_state.filters["gemini_key"] = gemini_key
        st.success("Gemini API Key set ✅")
    else:
        st.warning("Enter your Gemini API Key to enable AI features")

    # Universe dropdown
    default_universe = ["BANKNIFTY", "NIFTY", "RELIANCE", "HDFCBANK", "ICICIBANK", "TCS", "TATAMOTORS"]
    universe = st.multiselect("📊 Select Universe", default_universe, default=default_universe[:5])
    st.session_state.filters["universe"] = universe

    # Strategy dropdown
    strategy_options = ["AI-Auto", "Iron Condor", "Credit Spread", "Calendar Spread"]
    strategy_choice = st.selectbox("🎯 Strategy Focus", strategy_options, index=0)
    st.session_state.filters["strategy"] = strategy_choice

    # Other params
    capital = st.number_input("💰 Portfolio Capital (₹)", 100000, 10000000, 200000, step=50000)
    risk_pct = st.slider("Risk % per Trade", 0.5, 5.0, 1.5)
    rfr = st.number_input("Risk-Free Rate (annual)", 0.0, 0.2, 0.07, step=0.005, format="%.3f")
    expiry_days = st.slider("Days to expiry (estimate)", 1, 30, 7)

    # Apply filter button
    if st.button("🔄 Apply Filters"):
        st.experimental_rerun()

st.markdown("---")

# --- Use filter data ---
filters = st.session_state.get("filters", {})
selected_symbols = filters.get("universe", [])
strategy_focus = filters.get("strategy", "AI-Auto")

if not selected_symbols:
    st.warning("Please select symbols from the sidebar to continue.")
    st.stop()

# --- Main workflow trigger ---
if st.button("🚀 Run AI Selection + Analytics + Backtest", key="run_ai"):
    with st.spinner("Running AI analysis and fetching NSE data..."):
        # Step 1 — Gemini AI Selection (respect strategy filter)
        selection = ai_select_stocks_gemini(selected_symbols)

        # Filter by strategy if user specified (non-AI mode)
        if strategy_focus != "AI-Auto":
            for item in selection:
                item["strategy"] = strategy_focus
                item["rationale"] = f"User-selected focus on {strategy_focus}"

        st.subheader("📈 Selected Symbols and Strategies")
        st.json(selection)

        # Step 2 — Analytics and charts
        for row in selection:
            symbol = row.get("symbol")
            st.header(f"📊 {symbol} — {row.get('strategy')} ({row.get('bias')})")

            oc = fetch_option_chain(symbol)
            indices = fetch_indices_nse()
            spot = indices.get(symbol)
            vix = indices.get("INDIA VIX")

            metrics = compute_core_metrics(symbol=symbol, spot=spot, vix=vix, oc=oc, r=rfr, days=expiry_days)

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

            # Charts
            st.pyplot(plot_iv_rank_history())
            st.pyplot(plot_expected_move_chart(spot, metrics))

            # Strategy Generation
            strategies = build_strategies(symbol, oc, capital, risk_pct, metrics, r=rfr, days=expiry_days)
            st.subheader("🧮 Generated Strategies")
            st.dataframe(pd.DataFrame(strategies))

            # Backtest
            st.subheader("📊 Backtest (Simulated)")
            bt = run_backtest_for_symbol(symbol, strategies)
            st.dataframe(bt)

            # Broker buttons (unique keys)
            cA, cB = st.columns(2)
            with cA:
                if st.button(f"🚀 Send {symbol} to Groww (dry-run)", key=f"groww_{symbol}"):
                    st.success(place_order_groww(strategies))
            with cB:
                if st.button(f"🚀 Send {symbol} to Zerodha (dry-run)", key=f"zerodha_{symbol}"):
                    st.success(place_order_zerodha(strategies))

        # Final AI summary
        st.markdown("### 🧠 AI Market Summary")
        st.write(ai_market_summary_gemini(selection))

st.caption("Disclaimer: Educational/analysis only. Not financial advice.")
