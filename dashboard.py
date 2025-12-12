import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# CONFIGURATION
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Finbot Pro", layout="wide", page_icon="??")

# SESSION STATE (Stores your login token)
if 'token' not in st.session_state:
    st.session_state.token = None

# --- SIDEBAR: LOGIN & NAVIGATION ---
st.sidebar.title("?? Finbot Pro")

def login():
    st.sidebar.subheader("Login")
    email = st.sidebar.text_input("Email", value="admin@finbot.com")
    password = st.sidebar.text_input("Password", type="password", value="admin123")
    if st.sidebar.button("Log In"):
        try:
            response = requests.post(f"{API_URL}/auth/login", data={"username": email, "password": password})
            if response.status_code == 200:
                st.session_state.token = response.json()["access_token"]
                st.sidebar.success("Logged In!")
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials")
        except:
            st.sidebar.error("Cannot connect to Backend!")

def logout():
    if st.sidebar.button("Log Out"):
        st.session_state.token = None
        st.rerun()

# --- MAIN APP ---
if not st.session_state.token:
    login()
    st.title("?? Please Log In")
    st.info("Use the sidebar to access your trading terminal.")
else:
    logout()
    
    # AUTH HEADERS
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    # 1. FETCH DATA
    try:
        portfolio_res = requests.get(f"{API_URL}/portfolio", headers=headers)
        portfolio = portfolio_res.json()
    except:
        st.error("Failed to fetch portfolio. Is the backend running?")
        st.stop()

    # 2. HEADER METRICS
    st.title("?? Trading Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Cash Balance", f"")
    col2.metric("Portfolio Equity", f"")
    col3.metric("Buying Power", f"")

    st.divider()

    # 3. TRADING & MARKET DATA TABS
    tab1, tab2 = st.tabs(["?? Market Data & Trade", "?? Positions"])

    with tab1:
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader("Live Market Data")
            symbol = st.text_input("Enter Symbol (e.g. AAPL, BTC/USD)", value="AAPL").upper()
            
            if st.button("Get Price"):
                res = requests.get(f"{API_URL}/price/{symbol}", headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    st.metric(label=f"{symbol} Price", value=f"")
                    st.success(f"Last Updated: {data['time']}")
                else:
                    st.error("Symbol not found or API error.")

        with c2:
            st.subheader("Place Trade")
            with st.form("trade_form"):
                side = st.selectbox("Action", ["buy", "sell"])
                qty = st.number_input("Quantity", min_value=1, value=1)
                submitted = st.form_submit_button("?? Execute Trade")
                
                if submitted:
                    payload = {"symbol": symbol, "qty": qty, "side": side}
                    res = requests.post(f"{API_URL}/trades", json=payload, headers=headers)
                    if res.status_code == 200:
                        st.success(f"Order Placed! ID: {res.json()['order_id']}")
                    else:
                        st.error(f"Error: {res.text}")

    with tab2:
        st.subheader("Current Positions")
        # In a real app, you would call GET /positions here. 
        # Since our mock endpoint currently returns 'portfolio', we'll just show raw data for now.
        st.json(portfolio) 
