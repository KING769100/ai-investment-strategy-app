import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION & THEMATIC WATCHLIST ---
AI_THEME_WATCHLIST = {
    "Compute": ["NVDA", "AMD", "AVGO", "ARM"],
    "Foundry/Equipment": ["TSM", "ASML", "AMAT"],
    "Memory": ["MU", "WDC"],
    "Infrastructure/Power": ["VRT", "ETN", "GE"],
    "Edge/Software": ["MSFT", "PLTR", "AAPL"]
}

st.set_page_config(page_title="AI Strategy & Deployment", layout="wide")

# --- OPTIMIZED DATA FETCHING (The Fix) ---
@st.cache_data(ttl=3600)  # Cache data for 1 hour to avoid rate limits
def get_bulk_market_data(portfolio_tickers, watchlist_dict):
    # Flatten all tickers into one list
    all_watchlist_tickers = [item for sublist in watchlist_dict.values() for item in sublist]
    unique_tickers = list(set(portfolio_tickers + all_watchlist_tickers))
    
    # Download everything in ONE batch request
    data = yf.download(unique_tickers, period="1mo", interval="1d", group_by='ticker')
    return data

def calculate_rsi(series, periods=14):
    if len(series) < periods: return 50 # Default if not enough data
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- MOCK DATA LOADER ---
def load_audit_results():
    return {
        "portfolio_risk_score": 42,
        "top_flagged_risk": "Geopolitical Concentration (Taiwan)",
        "current_holdings": ["NVDA", "TSM", "MSFT"]
    }

# --- APP LOGIC ---
st.title("🤖 AI Strategy & Capital Deployment")

audit = load_audit_results()
all_data = get_bulk_market_data(audit['current_holdings'], AI_THEME_WATCHLIST)

# --- SIDEBAR ---
with st.sidebar:
    st.header("Audit Pulse")
    score = audit['portfolio_risk_score']
    st.metric("Risk Score", f"{score}/100")
    st.divider()
    capital_to_deploy = st.number_input("Capital Available ($)", value=10000)

# --- SECTION 1: PORTFOLIO ACTION ---
st.header("1. Portfolio Course Correction")
col1, col2 = st.columns([2, 1])

with col1:
    action_data = []
    for ticker in audit['current_holdings']:
        try:
            # Extract price from the bulk data download (No new network call!)
            ticker_data = all_data[ticker]['Close']
            current_price = ticker_data.iloc[-1]
            
            if score > 70:
                rec, logic = "🔴 Trim / Hedge", "High Audit Risk"
            elif score < 40:
                rec, logic = "🟢 Core Hold / Add", "Risk Levels Nominal"
            else:
                rec, logic = "🟡 Hold", "Maintain Position"
                
            action_data.append({"Ticker": ticker, "Action": rec, "Price": f"${current_price:.2f}", "Logic": logic})
        except:
            continue
    st.table(pd.DataFrame(action_data))

# --- SECTION 2: CAPITAL SCOUTING ---
st.header("2. Capital Deployment Scout")
scout_results = []

for category, tickers in AI_THEME_WATCHLIST.items():
    for t in tickers:
        try:
            ticker_close = all_data[t]['Close']
            rsi = calculate_rsi(ticker_close).iloc[-1]
            price_start = ticker_close.iloc[0]
            price_end = ticker_close.iloc[-1]
            mom = ((price_end / price_start) - 1) * 100
            
            status = "✅ Strategic Entry"
            if rsi < 40: status = "🔥 Strong Buy (Oversold)"
            elif rsi > 70: status = "❄️ Avoid (Overextended)"
                
            scout_results.append({
                "Theme": category, "Ticker": t, "RSI (14d)": round(rsi, 2), 
                "MoM Change": f"{mom:.2f}%", "Signal": status, "RawMom": mom
            })
        except:
            continue

scout_df = pd.DataFrame(scout_results)
st.dataframe(scout_df.drop(columns=['RawMom']), use_container_width=True)

# --- SECTION 3: VISUALIZATION ---
st.header("3. Momentum vs. Value Matrix")
fig = px.scatter(scout_df, x="RSI (14d)", y="RawMom", text="Ticker", color="Theme",
                 labels={"RawMom": "Monthly Momentum %"})
fig.add_vline(x=30, line_dash="dash", line_color="green")
fig.add_vline(x=70, line_dash="dash", line_color="red")
st.plotly_chart(fig, use_container_width=True)
