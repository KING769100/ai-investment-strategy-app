import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import os
import re
import logging
from typing import Dict, List, Optional

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- SECURITY: ENVIRONMENT-BASED CONFIGURATION ---
def load_portfolio_from_env() -> List[str]:
    # We pre-set your Revolut stocks as the default if the environment variable isn't found
    default_portfolio = "MU,WDC,MRVL,NVT,STX,VRT,ASML,ANET,GEV"
    portfolio_str = os.getenv("PORTFOLIO_TICKERS", default_portfolio)
    return [t.strip().upper() for t in portfolio_str.split(",")]

MY_PORTFOLIO = load_portfolio_from_env()
CAPITAL_DEFAULT = float(os.getenv("CAPITAL_DEFAULT", "2500"))

# --- CONFIGURATION: SCOUT LIST ---
AI_THEME_WATCHLIST = {
    "Compute (Chips)": ["NVDA", "AMD", "AVGO", "ARM"],
    "Equipment/Foundry": ["AMAT", "LRCX", "TSM"],
    "Power/Infrastructure": ["ETN", "GE", "PWR"],
    "Software/Edge AI": ["MSFT", "PLTR", "AAPL", "GOOGL"]
}

st.set_page_config(page_title="AI Strategy & Deployment", layout="wide")

# --- SECURITY: INPUT VALIDATION ---
def validate_ticker(ticker: str) -> bool:
    return bool(re.match(r'^[A-Z]{1,5}$', ticker.strip().upper()))

def validate_tickers_list(tickers: List[str]) -> List[str]:
    return [t.strip().upper() for t in tickers if validate_ticker(t)]

# --- OPTIMIZED DATA FETCHING ---
@st.cache_data(ttl=3600)
def get_bulk_market_data(portfolio_tickers: List[str], watchlist_dict: Dict) -> Optional[pd.DataFrame]:
    try:
        all_watchlist_tickers = [item for sublist in watchlist_dict.values() for item in sublist]
        unique_tickers = list(set(validate_tickers_list(portfolio_tickers + all_watchlist_tickers)))
        
        if not unique_tickers:
            return None
        
        data = yf.download(unique_tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
        return data
    except Exception as e:
        st.error(f"Market Data Error: {str(e)}")
        return None

def calculate_rsi(series: pd.Series, periods: int = 14) -> pd.Series:
    if len(series) < periods:
        return pd.Series([50] * len(series), index=series.index)
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss.replace(0, float('inf'))
    return 100 - (100 / (1 + rs))

def load_audit_results(portfolio: List[str]) -> Dict:
    # Pulling the Risk Score from the Audit App logic
    risk_score = int(os.getenv("AUDIT_RISK_SCORE", "42"))
    top_flag = os.getenv("AUDIT_TOP_FLAG", "Concentration in Memory & Storage")
    return {"portfolio_risk_score": risk_score, "top_flagged_risk": top_flag, "holdings": portfolio}

# --- APP UI ---
st.title("🤖 AI Strategy & Capital Deployment")
st.caption("Actioning the 'Investment & AI Risk Audit' Outcomes")

audit = load_audit_results(MY_PORTFOLIO)
all_data = get_bulk_market_data(audit['holdings'], AI_THEME_WATCHLIST)

if all_data is None:
    st.error("Connection Error. Please refresh.")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    score = audit['portfolio_risk_score']
    risk_color = "🔴" if score > 70 else "🟡" if score > 40 else "🟢"
    st.metric("Portfolio Risk Score", f"{risk_color} {score}/100")
    st.info(f"Flag: {audit['top_flagged_risk']}")
    st.divider()
    capital_to_deploy = st.number_input("Capital Available ($)", value=CAPITAL_DEFAULT)

# --- SECTION 1: PORTFOLIO ---
st.header("1. Existing Portfolio Strategy")
action_data = []
for ticker in audit['holdings']:
    try:
        if ticker in all_data.columns:
            ticker_close = all_data[ticker]['Close']
            rsi = calculate_rsi(ticker_close).iloc[-1]
            price = ticker_close.iloc[-1]
            
            if rsi > 75 and score > 60:
                rec, logic = "🔴 Trim", "Overbought + High Risk"
            elif rsi < 40:
                rec, logic = "🟢 Add", "Oversold Opportunity"
            else:
                rec, logic = "🟡 Hold", "Neutral"
            
            action_data.append({"Ticker": ticker, "Price": f"${price:.2f}", "RSI": round(rsi, 1), "Action": rec, "Logic": logic})
    except: continue

st.table(pd.DataFrame(action_data))

# --- SECTION 2: SCOUT ---
st.header("2. New Capital Deployment Scout")
scout_results = []
for cat, tickers in AI_THEME_WATCHLIST.items():
    for t in tickers:
        try:
            if t in all_data.columns:
                px_close = all_data[t]['Close']
                rsi = calculate_rsi(px_close).iloc[-1]
                mom = ((px_close.iloc[-1] / px_close.iloc[0]) - 1) * 100
                scout_results.append({"Sector": cat, "Ticker": t, "RSI": round(rsi, 1), "MoM %": round(mom, 1)})
        except: continue

scout_df = pd.DataFrame(scout_results)
best_entry = scout_df.sort_values(by="RSI").iloc[0]

c1, c2 = st.columns([1, 2])
with c1:
    st.metric("Top Deployment Target", best_entry['Ticker'])
    st.write(f"**Sector:** {best_entry['Sector']}")
    st.write(f"**Reason:** RSI {best_entry['RSI']} (Most Oversold)")
with c2:
    st.dataframe(scout_df.sort_values(by="RSI"), use_container_width=True, hide_index=True)

# --- SECTION 3: HEATMAP ---
st.header("3. Market Heatmap")
fig = px.scatter(scout_df, x="RSI", y="MoM %", text="Ticker", color="Sector",
                 title="AI Value Chain: Entry Points")
fig.add_vline(x=30, line_dash="dash", line_color="green")
fig.add_vline(x=70, line_dash="dash", line_color="red")
st.plotly_chart(fig, use_container_width=True)
