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

# --- MOCK DATA LOADER (In production, this reads from your Audit App) ---
def load_audit_results():
    # This simulates the output from your 'Investment & AI Risk Audit App'
    return {
        "portfolio_risk_score": 42,  # 0-100
        "top_flagged_risk": "Geopolitical Concentration (Taiwan)",
        "diversification_score": 65,
        "current_holdings": ["NVDA", "TSM", "MSFT"]
    }

def get_stock_data(tickers):
    data = yf.download(tickers, period="1mo", interval="1d")['Close']
    return data

def calculate_rsi(series, periods=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- UI HEADER ---
st.title("🤖 AI Strategy & Capital Deployment")
st.subheader("Translating Risk Audit into Market Action")

audit = load_audit_results()

# --- SIDEBAR: AUDIT SNAPSHOT ---
with st.sidebar:
    st.header("Audit Pulse")
    score = audit['portfolio_risk_score']
    st.metric("Risk Score", f"{score}/100", delta="-5% vs Last Week")
    st.warning(f"Major Risk: {audit['top_flagged_risk']}")
    
    st.divider()
    capital_to_deploy = st.number_input("New Capital Available ($)", min_value=0, value=10000)

# --- SECTION 1: ACTION ON EXISTING HOLDINGS ---
st.header("1. Portfolio Course Correction")
col1, col2 = st.columns([2, 1])

with col1:
    action_data = []
    for ticker in audit['current_holdings']:
        # Simple Logic: If risk is high and stock is at ATH, suggest trimming
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        current_price = hist['Close'].iloc[-1]
        
        if score > 70:
            rec = "🔴 Trim / Hedge"
            reason = "High Audit Risk + Market Saturation"
        elif score < 40:
            rec = "🟢 Core Hold / Add"
            reason = "Risk Levels Nominal"
        else:
            rec = "🟡 Hold"
            reason = "Maintain Position"
            
        action_data.append({"Ticker": ticker, "Action": rec, "Price": f"${current_price:.2f}", "Logic": reason})

    st.table(pd.DataFrame(action_data))

# --- SECTION 2: THEMATIC CAPITAL SCOUTING ---
st.header("2. Capital Deployment Scout")
st.info("Searching for the best entry points in the AI/Semiconductor Value Chain...")

all_tickers = [item for sublist in AI_THEME_WATCHLIST.values() for item in sublist]
prices = get_stock_data(all_tickers)

scout_results = []
for category, tickers in AI_THEME_WATCHLIST.items():
    for t in tickers:
        try:
            rsi = calculate_rsi(prices[t]).iloc[-1]
            price_change = ((prices[t].iloc[-1] / prices[t].iloc[0]) - 1) * 100
            
            # Recommendation Logic based on RSI (Overbought/Oversold)
            if rsi < 40:
                status = "🔥 Strong Buy (Oversold)"
            elif rsi > 70:
                status = "❄️ Avoid (Overextended)"
            else:
                status = "✅ Strategic Entry"
                
            scout_results.append({
                "Theme": category,
                "Ticker": t,
                "RSI (14d)": round(rsi, 2),
                "MoM Change": f"{price_change:.2f}%",
                "Deployment Signal": status
            })
        except:
            continue

scout_df = pd.DataFrame(scout_results)

# Filter UI
selected_theme = st.multiselect("Filter by AI Sub-Sector:", list(AI_THEME_WATCHLIST.keys()), default=list(AI_THEME_WATCHLIST.keys()))
filtered_df = scout_df[scout_df['Theme'].isin(selected_theme)]

st.dataframe(filtered_df.sort_values(by="RSI (14d)"), use_container_width=True)

# --- SECTION 3: TOP PICK VISUALIZATION ---
st.header("3. Momentum vs. Value Matrix")
fig = px.scatter(scout_df, x="RSI (14d)", y="MoM Change", text="Ticker", color="Theme",
                 title="AI Value Chain: Overbought vs. Value Zones",
                 labels={"RSI (14d)": "RSI (Lower = Better Entry)", "MoM Change": "Monthly Momentum %"})
fig.add_vline(x=30, line_dash="dash", line_color="green", annotation_text="Oversold")
fig.add_vline(x=70, line_dash="dash", line_color="red", annotation_text="Overbought")

st.plotly_chart(fig, use_container_width=True)

st.markdown(f"""
### 💡 Strategic Recommendation:
Based on your Audit Score of **{score}** and current market RSI levels, you should:
1. **Prioritize:** {scout_df.sort_values(by='RSI (14d)').iloc[0]['Ticker']} within the **{scout_df.sort_values(by='RSI (14d)').iloc[0]['Theme']}** sector.
2. **Limit Deployment:** Focus on high-conviction infrastructure plays like **VRT** or **ETN** if the chip sector (NVDA/TSM) shows RSI > 70.
""")
