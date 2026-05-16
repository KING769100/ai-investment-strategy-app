import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- CONFIGURATION: YOUR REAL HOLDINGS (From Image) ---
MY_PORTFOLIO = ["MU", "WDC", "MRVL", "NVT", "STX", "VRT", "ASML", "ANET", "GEV"]

# --- CONFIGURATION: SCOUT LIST (Excluding what you already own to find NEW ideas) ---
AI_THEME_WATCHLIST = {
    "Compute (Chips)": ["NVDA", "AMD", "AVGO", "ARM"],
    "Equipment/Foundry": ["AMAT", "LRCX", "TSM"],
    "Power/Infrastructure": ["ETN", "GE", "PWR"],
    "Software/Edge AI": ["MSFT", "PLTR", "AAPL", "GOOGL"]
}

st.set_page_config(page_title="AI Strategy & Deployment", layout="wide")

# --- OPTIMIZED DATA FETCHING ---
@st.cache_data(ttl=3600)
def get_bulk_market_data(portfolio_tickers, watchlist_dict):
    all_watchlist_tickers = [item for sublist in watchlist_dict.values() for item in sublist]
    unique_tickers = list(set(portfolio_tickers + all_watchlist_tickers))
    # Batch download to prevent rate limits
    data = yf.download(unique_tickers, period="1mo", interval="1d", group_by='ticker')
    return data

def calculate_rsi(series, periods=14):
    if len(series) < periods: return 50
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- MOCK AUDIT SCORE (This pulls from your Audit App Logic) ---
def load_audit_results():
    return {
        "portfolio_risk_score": 42, # Logic from your Audit App
        "top_flagged_risk": "Concentration in Memory & Storage",
        "holdings": MY_PORTFOLIO
    }

# --- APP LOGIC ---
st.title("🤖 AI Strategy & Capital Deployment")
st.caption("Actioning the 'Investment & AI Risk Audit' Outcomes")

audit = load_audit_results()
all_data = get_bulk_market_data(audit['holdings'], AI_THEME_WATCHLIST)

# --- SIDEBAR ---
with st.sidebar:
    st.header("Audit Pulse")
    score = audit['portfolio_risk_score']
    st.metric("Portfolio Risk Score", f"{score}/100")
    st.info(f"Primary Flag: {audit['top_flagged_risk']}")
    st.divider()
    st.subheader("Deployment Settings")
    capital_to_deploy = st.number_input("New Capital Available ($)", value=5000)

# --- SECTION 1: PORTFOLIO COURSE CORRECTION ---
st.header("1. Existing Portfolio Strategy")
st.markdown("Evaluating current holdings based on Audit Risk and Market Overextension.")

action_data = []
for ticker in audit['holdings']:
    try:
        ticker_close = all_data[ticker]['Close']
        current_price = ticker_close.iloc[-1]
        rsi = calculate_rsi(ticker_close).iloc[-1]
        
        # Decision Logic
        if rsi > 75 and score > 60:
            rec, color = "🔴 Trim / Hedge", "Red"
            logic = "Overbought + High Audit Risk"
        elif rsi < 40:
            rec, color = "🟢 Add / Accumulate", "Green"
            logic = "Oversold - Strategic Entry"
        else:
            rec, color = "🟡 Hold", "Orange"
            logic = "Maintain Exposure"
            
        action_data.append({
            "Ticker": ticker, 
            "Current Price": f"${current_price:.2f}",
            "RSI (14d)": round(rsi, 2),
            "Action Move": rec, 
            "Strategic Logic": logic
        })
    except:
        continue

st.table(pd.DataFrame(action_data))

# --- SECTION 2: CAPITAL SCOUTING (NEW DEPLOYMENT) ---
st.header("2. New Capital Deployment Scout")
st.markdown("Searching for the best place to deploy capital in the AI/Semiconductor thematic.")

scout_results = []
for category, tickers in AI_THEME_WATCHLIST.items():
    for t in tickers:
        try:
            ticker_close = all_data[t]['Close']
            rsi = calculate_rsi(ticker_close).iloc[-1]
            price_start = ticker_close.iloc[0]
            price_end = ticker_close.iloc[-1]
            mom = ((price_end / price_start) - 1) * 100
            
            if rsi < 45:
                status = "🔥 Value Zone"
            elif rsi > 70:
                status = "❄️ Overheated"
            else:
                status = "✅ Balanced"
                
            scout_results.append({
                "Sector": category, "Ticker": t, "RSI": round(rsi, 2), 
                "MoM %": round(mom, 2), "Signal": status
            })
        except:
            continue

scout_df = pd.DataFrame(scout_results)

# Best Suggestion Logic
best_entry = scout_df.sort_values(by="RSI").iloc[0]

c1, c2 = st.columns([1, 2])
with c1:
    st.metric("Top Deployment Target", best_entry['Ticker'], help="Lowest RSI in Watchlist")
    st.write(f"**Sector:** {best_entry['Sector']}")
    st.write(f"**Reason:** RSI is at {best_entry['RSI']}, indicating it is the least 'overbought' in the AI thematic right now.")

with c2:
    st.dataframe(scout_df.sort_values(by="RSI"), use_container_width=True)

# --- SECTION 3: VISUAL MATRIX ---
st.header("3. Market Heatmap")
fig = px.scatter(scout_df, x="RSI", y="MoM %", text="Ticker", color="Sector",
                 title="AI Value Chain: Entry Points",
                 labels={"RSI": "RSI (Strength Index)", "MoM %": "Monthly Momentum"})
fig.add_vline(x=30, line_dash="dash", line_color="green", annotation_text="Oversold")
fig.add_vline(x=70, line_dash="dash", line_color="red", annotation_text="Overbought")
st.plotly_chart(fig, use_container_width=True)
