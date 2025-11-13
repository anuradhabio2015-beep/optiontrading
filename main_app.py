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


# Page config
st.set_page_config(page_title="My App", page_icon=":sparkles:", layout="wide")

# === Hide default Streamlit header/menu/footer ===
HIDE_STEAMLIT_STYLE = """
<style>
/* Hide the top header (Streamlit logo) */
header {visibility: hidden;}
/* Hide the hamburger menu and "Made with Streamlit" footer */
footer {visibility: hidden;}
/* Optional: hide the toolbar in newer Streamlit versions */
[data-testid="stToolbar"] {display: none}
</style>
"""
st.markdown(HIDE_STEAMLIT_STYLE, unsafe_allow_html=True)

# === Custom header ===
# You can replace the logo path with a URL or local file (e.g., "./assets/logo.png")
LOGO_PATH = "https://placehold.co/80x80/png?text=Logo"  # replace with your logo

CUSTOM_HEADER_STYLE = """
<style>
.custom-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 20px;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  background: linear-gradient(90deg, rgba(255,255,255,0.9), rgba(250,250,255,0.6));
}
.custom-header .title {
  font-size: 22px;
  font-weight: 700;
  margin: 0;
}
.custom-header .subtitle {
  font-size: 13px;
  color: #555;
  margin: 0;
}
/* Make header sticky at top (optional) */
.stApp > div:first-child {
  position: sticky;
  top: 8px;
  z-index: 999;
}
</style>
"""

st.markdown(CUSTOM_HEADER_STYLE, unsafe_allow_html=True)

header_html = f"""
<div class="custom-header">
  <img src="{LOGO_PATH}" width="64" height="64" style="border-radius:12px;"/>
  <div>
    <p class="title">Smart Trading App</p>
    <p class="subtitle">AI-Powered Options Trading Assistant for Smarter, Safer Decisions.</p>
  </div>
  <div style="margin-left:auto; display:flex; gap:8px; align-items:center;">
    <!-- Add small action buttons/links -->
    <a href="#" target="_self">Docs</a>
    <a href="#" target="_self">Support</a>
  </div>
</div>
"""

st.markdown(header_html, unsafe_allow_html=True)

# === Rest of app content ===
st.write("Welcome! Your AI-powered options trading assistant is ready. Analyze markets, explore strategies, and execute smarter trades — all in one place.")

# Add Code Here

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
    st.error("❌ Critical data missing: Unable to fetch Spot, India VIX, or PCR (OI). Please retry later.")
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
    
    from modules.order_executor import place_order_groww, place_order_zerodha
    st.markdown("### 🧾 Place Order")
    if broker == "Zerodha" and gemini_key and zerodha_api_key and zerodha_access_token:
        st.success("✅ Zerodha broker connected.")
        for strat in strategies:
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"📤 Place {strat['Strategy']} in Zerodha", key=f"zerodha_{strat['Strategy']}"):
                    msg = place_order_zerodha(
                        zerodha_api_key,
                        zerodha_access_token,
                        symbol,
                        48700,  # Example strike placeholder — can fetch dynamically
                        "CE",
                        "28NOV24",
                        25,
                        120.0,
                        "NRML"
                    )
                    st.success(msg)
            with col2:
                st.write(f"Strategy: {strat['Strategy']}")
    elif broker == "Groww":
        st.info("📈 Paper trade mode active (Groww)")
        for strat in strategies:
            if st.button(f"💹 Simulate {strat['Strategy']} in Groww", key=f"groww_{strat['Strategy']}"):
                msg = place_order_groww(symbol, 48700, "CE", "28NOV24", 25, 120.0)
                st.success(msg)
    else:
        st.warning("⚠️ Connect your broker in sidebar to enable live order placement.")


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


# Notes for customization (keep these comments in the file):
# - Replace LOGO_PATH with your logo file or URL. For a local file, use st.image('./assets/logo.png') instead.
# - Tweak CSS in CUSTOM_HEADER_STYLE to change colors, spacing, or make the header full-width.
# - If Streamlit updates its DOM structure, the CSS selectors (header, footer, [data-testid]) may need adjustment.
# - For accessibility, ensure alt text and semantic HTML if you expand the header.
