# ===============================================
# SMART OPTION DASHBOARD — TABBED UI LAYOUT
# ===============================================
import streamlit as st
import pandas as pd
from modules.ai_trade_levels import ai_trade_levels
from modules.charts import plot_iv_rank_history, plot_expected_move_chart
from modules.backtester import run_detailed_backtest
from modules.order_executor import place_order_groww, place_order_zerodha

import time

# --- Safe retry-based data fetch function ---
def try_fetch_data(symbol, retries=3, delay=2):
    """Attempt to fetch market data with retries and unified return structure."""
    status = st.empty()  # placeholder for single-line updates

    for attempt in range(retries):
        try:
            status.info(f"🔄 Attempt {attempt+1}/{retries}: Fetching live market data for {symbol}...")

            indices = fetch_indices_nse()
            spot = indices.get(symbol.upper()) or fetch_spot_price(symbol)
            vix = indices.get("INDIAVIX") or indices.get("INDIA VIX") or 14.0
            oc = fetch_option_chain(symbol)
            metrics = compute_core_metrics(symbol, spot, vix, oc, r=rfr, days=expiry_days)
            pcr = metrics.get("pcr") if metrics else None

            # if all key values exist, return immediately
            if spot and vix and pcr:
                status.success(f"✅ Data fetched successfully (Spot={spot:.2f}, VIX={vix:.2f}, PCR={round(pcr, 2)})")
                return spot, vix, pcr, oc, metrics

            status.warning(
                f"⚠️ Attempt {attempt+1}/{retries} failed: Missing (Spot={spot}, VIX={vix}, PCR={pcr})"
            )
            time.sleep(delay)

        except Exception as e:
            status.error(f"⚠️ Attempt {attempt+1}/{retries} failed: {str(e)[:100]}")
            time.sleep(delay)

    status.error("❌ Failed to fetch Spot, India VIX, or PCR after multiple retries.")
    return None, None, None, None, None


# --- Initialize variables safely ---
spot = None
vix = None
pcr = None
oc = None
metrics = {}

# --- Fetch the data ---
spot, vix, pcr, oc, metrics = try_fetch_data(symbol)

# --- If still missing, stop further execution ---
if not spot or not vix or not pcr:
    st.error("❌ Critical data missing: Unable to fetch Spot, India VIX, or PCR (OI). Please retry later.")
    if st.button("🔁 Retry Fetch Data"):
        st.rerun()
    st.stop()


# Tabs (like Groww)
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Market Overview",
    "💡 AI Strategy",
    "📊 Backtest",
    "📉 IV / Expected Move Charts",
    "⚙️ Orders & Summary"
])

# ---------------------------------------------
# TAB 1 — MARKET OVERVIEW
# ---------------------------------------------
with tab1:
    st.header("📈 Market Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Spot", f"{spot or '-'}")
    c2.metric("India VIX", f"{round(vix, 2) if vix else '-'}")
    c3.metric("PCR (OI)", f"{round(metrics.get('pcr'), 2) if metrics.get('pcr') else '-'}")

    st.write("**IV Rank / Percentile:**", 
             f"{metrics.get('atm_iv_rank')} / {metrics.get('atm_iv_percentile')}%")
    st.write("**Expected Move (1D ±):**", 
             f"{metrics.get('expected_move_1d', (0, 0))[0]:,.0f} pts | (3D ±): {metrics.get('expected_move_3d', (0, 0))[0]:,.0f} pts")
    st.success("✅ Data successfully fetched and verified.")

# ---------------------------------------------
# TAB 2 — AI STRATEGY LEVELS
# ---------------------------------------------
with tab2:
    st.header("💡 AI Entry / Exit / Stop-Loss Recommendations")
    strategies = build_strategies(symbol, oc, capital, risk_pct, metrics, r=rfr, days=expiry_days, focus=strategy_focus)

    ai_levels = []
    for strat in strategies:
        ai_level = ai_trade_levels(
            symbol,
            spot,
            metrics.get("atm_iv_rank", 50),
            metrics.get("pcr", 1.0),
            strategy=strat["Strategy"]
        )
        ai_levels.append(ai_level)

    ai_df = pd.DataFrame(ai_levels)
    st.dataframe(ai_df, use_container_width=True)
    st.caption("These levels are AI-estimated based on IV Rank, PCR, and live option data trends.")

# ---------------------------------------------
# TAB 3 — BACKTEST
# ---------------------------------------------
with tab3:
    st.header("📊 Backtest Simulation (AI-Driven)")
    bt = run_detailed_backtest(symbol, strategies)
    st.dataframe(bt, use_container_width=True)

    st.markdown(f"**Total P/L:** ₹{bt['P/L (₹)'].sum():,.0f} | "
                f"Avg Return: {bt['Return (%)'].mean():.2f}% | "
                f"Avg POP: {bt['POP (%)'].mean():.1f}%")

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.plot(bt["Total Profit (₹)"], marker="o", color="#00b386")
    ax.set_title(f"{symbol} Cumulative Profit Curve", fontsize=11, weight="bold")
    ax.set_xlabel("Trades")
    ax.set_ylabel("Cumulative Profit (₹)")
    st.pyplot(fig)

# ---------------------------------------------
# TAB 4 — IV HISTORY / EXPECTED MOVE CHARTS
# ---------------------------------------------
with tab4:
    st.header("📉 Volatility & Expected Move Analysis")
    st.pyplot(plot_iv_rank_history())
    st.pyplot(plot_expected_move_chart(spot, metrics))
    st.caption("Charts styled like Groww: minimal, clear, and data-rich.")

# ---------------------------------------------
# TAB 5 — ORDERS & SUMMARY
# ---------------------------------------------
with tab5:
    st.header("⚙️ Orders & Market Summary")

    cA, cB = st.columns(2)
    with cA:
        if st.button(f"🚀 Send {symbol} Orders to Groww (Dry-Run)", key=f"groww_{symbol}"):
            st.success(place_order_groww(strategies))
    with cB:
        if st.button(f"🚀 Send {symbol} Orders to Zerodha (Dry-Run)", key=f"zerodha_{symbol}"):
            st.success(place_order_zerodha(strategies))

    st.markdown("### 🧭 AI Market Summary")
    st.write(st.session_state.get("ai_summary", "—"))
    st.caption("Disclaimer: Educational/analysis only. Not financial advice.")
