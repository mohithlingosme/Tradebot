import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000"  # Make sure this matches your FastAPI port

# --- THEME ---
# Primary Colors: White, Silver, Light Grey, Sky Blue
# Indicators: Red (negative), Green (positive)
st.set_page_config(
    page_title="FinBot",
    layout="wide",
    page_icon="🤖"
)

# Custom CSS for the theme
st.markdown("""
<style>
    /* Main background */
    .main {
        background-color: #f0f2f5; /* Light Grey */
    }
    /* Sidebar */
    .css-1d391kg {
        background-color: #ffffff; /* White */
        border-right: 1px solid #silver;
    }
    /* Text */
    body {
        color: #333;
    }
    h1, h2, h3 {
        color: #2196F3; /* Sky Blue */
    }
    /* Buttons */
    .stButton>button {
        background-color: #2196F3;
        color: white;
        border-radius: 4px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1976D2;
    }
    /* Buy/Sell Buttons */
    .buy-button {
        background-color: #4CAF50 !important; /* Green */
        color: white !important;
    }
    .sell-button {
        background-color: #F44336 !important; /* Red */
        color: white !important;
    }
    /* Positive/Negative indicators */
    .positive { color: #4CAF50; }
    .negative { color: #F44336; }
</style>
""", unsafe_allow_html=True)


# --- SESSION STATE ---
if 'token' not in st.session_state:
    st.session_state.token = None

# --- API FUNCTIONS ---
def login(email, password):
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"username": email, "password": password}
        )
        if response.status_code == 200:
            st.session_state.token = response.json()["access_token"]
            return True
        else:
            st.sidebar.error(f"Login failed: {response.json().get('detail', 'Unknown error')}")
            return False
    except requests.exceptions.ConnectionError:
        st.sidebar.error("Cannot connect to the backend.")
        return False

def get_portfolio():
    if not st.session_state.token:
        return None
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        response = requests.get(f"{API_URL}/portfolio", headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_price(symbol):
    try:
        response = requests.get(f"{API_URL}/price/{symbol}")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None
        
def get_candles(symbol):
    try:
        response = requests.get(f"{API_URL}/candles?symbol={symbol}&limit=100")
        if response.status_code == 200:
            return response.json()['data']
        return None
    except:
        return None

def place_trade(symbol, side, quantity):
    if not st.session_state.token:
        return None
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    payload = {"symbol": symbol, "side": side, "quantity": quantity}
    try:
        response = requests.post(f"{API_URL}/trades", json=payload, headers=headers)
        return response
    except:
        return None


# --- UI COMPONENTS ---

def login_sidebar():
    st.sidebar.title("FinBot Login")
    email = st.sidebar.text_input("Email", value="test@example.com")
    password = st.sidebar.text_input("Password", type="password", value="password")
    if st.sidebar.button("Log In"):
        if login(email, password):
            st.rerun()

def main_dashboard():
    st.sidebar.title("FinBot Pro")
    st.sidebar.write(f"Welcome, user!")
    if st.sidebar.button("Log Out"):
        st.session_state.token = None
        st.rerun()

    st.title("Trading Dashboard")

    # Fetch data
    portfolio = get_portfolio()
    
    # --- HEADER METRICS ---
    if portfolio:
        pnl_class = "positive" if portfolio['pnl'] >= 0 else "negative"
        col1, col2 = st.columns(2)
        col1.metric("Portfolio Equity", f"${portfolio['equity']:.2f}")
        col2.markdown(f'**Total P/L:** <span class="{pnl_class}" style="font-size: 1.2em;">${portfolio["pnl"]:.2f}</span>', unsafe_allow_html=True)
    else:
        st.warning("Could not load portfolio data.")
    
    st.divider()

    # --- TABS: Market Data & Positions ---
    tab1, tab2 = st.tabs(["📊 Market Data & Trade", "💼 Positions"])

    with tab1:
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader("Market Data")
            symbol = st.text_input("Enter Symbol (e.g., AAPL)", value="AAPL").upper()
            
            # Chart
            candles = get_candles(symbol)
            if candles:
                df = pd.DataFrame(candles)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                fig = go.Figure(data=[go.Candlestick(x=df['timestamp'],
                                open=df['open'], high=df['high'],
                                low=df['low'], close=df['close'])])
                fig.update_layout(
                    title=f'{symbol} Candlestick Chart',
                    xaxis_title='Time',
                    yaxis_title='Price (USD)',
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font_color='black',
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"Could not fetch chart data for {symbol}.")


        with c2:
            st.subheader("Place Trade")
            
            price_data = get_price(symbol)
            if price_data:
                st.metric(f"Current Price of {symbol}", f"${price_data['price']:.2f}")
            
            with st.form("trade_form"):
                side = st.radio("Action", ["buy", "sell"], horizontal=True)
                quantity = st.number_input("Quantity", min_value=1, value=1)
                
                # Dynamic button color
                button_class = "buy-button" if side == "buy" else "sell-button"
                submit_label = "Execute Buy" if side == "buy" else "Execute Sell"

                submitted = st.form_submit_button(submit_label)
                
                if submitted:
                    res = place_trade(symbol, side, quantity)
                    if res and res.status_code == 201:
                        st.success(f"Trade executed successfully!")
                        # Optionally, refresh portfolio data
                    elif res:
                        st.error(f"Trade failed: {res.json().get('detail', 'Unknown error')}")
                    else:
                        st.error("Failed to connect to the trade execution endpoint.")

    with tab2:
        st.subheader("Current Positions")
        if portfolio and portfolio['positions']:
            positions_df = pd.DataFrame(
                portfolio['positions'].items(), 
                columns=['Symbol', 'Quantity']
            )
            st.dataframe(positions_df, use_container_width=True)
        else:
            st.info("No open positions.")


# --- MAIN APP LOGIC ---
if not st.session_state.token:
    login_sidebar()
    st.title("Welcome to FinBot")
    st.info("Please log in using the sidebar to access your dashboard.")
else:
    main_dashboard()
