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

# -------------------------------------------------------------------
# Streamlit page setup
# -------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="Smart Option Selling Dashboard — Gemini Pro")
st.title("🤖 Smart Option Selling Dashboard (Gemini Pro GUI+)")

# -------------------------------------------------------------------
# Sidebar Configuration Panel
# -------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration Panel")

    # Gemini API Key
    gemini_key = st.text_input("🔑 Gemini API Key", type="password", placeholder="Paste your Gemini key here")
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        st.session_state["gemini_key"] = gemini_key
        st.success("Gemini API Key set ✅")
    else:
        st.warning("Please enter your Gemini API Key to enable AI Selection")

    # Universe Selector
    default_universe = [
        "BANKNIFTY", "NIFTY", "RELIANCE", "HDFCBANK",
        "ICICIBANK", "INFY", "SBIN", "TCS",
        "TATAMOTORS", "AXISBANK", "LT", "HINDUNILVR"
    ]

    selected_universe = st.multiselect(
        "📊 Select Universe (indices or stocks)",
        options=default_universe,
        default=st.session_state.get("selected_universe", default_universe[:5]),
        help="Choose instruments for AI-based options analysis"
    )

    # Save universe to session_state to persist
    st.session_state["selected_universe"] = selected_universe

    # Strategy Selector
    strategy_choice = st.selectbox(
        "🎯 Strategy Focus",
        ["AI-Auto", "Iron Condor", "Credit Spread", "Calendar Spread"],
        index=0
    )
    st.session_state["strategy_choice"] = strategy_choice

    # Risk / Config parameters
    capital = st.number_input("💰 Portfolio Capital (₹)", 100000, 10000000, 200000, step=50000)
    risk_pct = st.slider("Risk % per Trade", 0.5, 5.0, 1.5)
    rfr = st.number_input("Risk-Free Rate (annual)", 0.0, 0.2, 0.07, step=0.005, format="%.3f")
    expiry_days = st.slider("Days to expiry (estimate)", 1, 30, 7)

    st.markdown("---")
    run_button = st.button("🚀 Run AI Selection + Analytics + Backtest", use_container_width=True)

    # Show debug info
    st.caption(f"🧩 Current Universe: {st.session_state['selected_universe']}")

# -------------------------------------------------------------------
# Input validation
# -------------------------------------------------------------------
if not gemini_key:
    st.stop()

if not st.session_state.get("selected_universe"):
    st.warning("⚠️ Please select at least one symbol from the Universe to continue.")
    st.stop()

# -------------------------------------------------------------------
# Run AI + Data Processing
# -------------------------------------------------------------------
if run_button:
    with st.spinner("🔍 Running AI selection and fetching market data..."):
        # Fetch Universe from session_state to ensure live values
        universe_live = st.session_state["selected_universe"]

        st.subheader("🧠 AI Stock/Index Selection Results")
        selection = ai_select_stocks_gemini(universe_live)
        st.json(selection)

        for row in selection:
            symbol = row.get("symbol")
            st.markdown(f"## 📈 {symbol} — {row.get('strategy')} ({row.get('bias')})")

            # Fetch option chain and indices
            oc = fetch_option_chain(symbol)
            indices = fetch_indices_nse()
            spot = indices.get(symbol)
            vix = indices.get("INDIA VIX")

            # Compute core metrics
            metrics = compute_core_metrics(symbol, spot, vix, oc, r=rfr, days=expiry_days)

            # Display summary metrics
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
            st.subheader("🧮 Suggested Strategies")
            strategies = build_strategies(symbol, oc, capital, risk_pct, metrics, r=rfr, days=expiry_days)
            st.dataframe(pd.DataFrame(strategies))

            # Backtest Results
            st.subheader("📊 Backtest (Toy Simulation)")
            bt = run_backtest_for_symbol(symbol, strategies)
            st.dataframe(bt)

            # Order Buttons (unique keys)
            cA, cB = st.columns(2)
            with cA:
                if st.button(f"🚀 Send {symbol} to Groww (dry-run)", key=f"groww_{symbol}"):
                    st.success(place_order_groww(strategies))
            with cB:
                if st.button(f"🚀 Send {symbol} to Zerodha (dry-run)", key=f"zerodha_{symbol}"):
                    st.success(place_order_zerodha(strategies))

        # AI Market Summary
        st.markdown("### 🧭 AI Market Summary")
        st.write(ai_market_summary_gemini(selection))

st.caption("Disclaimer: Educational/analysis only. Not financial advice.")
