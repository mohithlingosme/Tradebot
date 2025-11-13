"""
Streamlit Dashboard Application

Responsibilities:
- Display trading dashboard with P&L, positions, performance
- Provide strategy management interface
- Show real-time updates and alerts
- Allow configuration of strategies and risk parameters

Features:
- Portfolio overview with charts
- Position monitoring
- Strategy status and controls
- Risk metrics display
- Log viewer
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import time
import logging

logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000"  # FastAPI backend URL

# Page configuration
st.set_page_config(
    page_title="Finbot Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
    }
    .positive { color: #28a745; }
    .negative { color: #dc3545; }
    .neutral { color: #6c757d; }
</style>
""", unsafe_allow_html=True)

def api_request(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """
    Make API request to backend.

    Args:
        endpoint: API endpoint
        method: HTTP method
        data: Request data for POST

    Returns:
        API response dictionary
    """
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return {}

def display_portfolio_overview():
    """Display portfolio overview with key metrics."""
    st.header("📊 Portfolio Overview")

    # Fetch portfolio data
    portfolio_data = api_request("/portfolio")

    if not portfolio_data:
        st.warning("Unable to fetch portfolio data")
        return

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Value",
            f"₹{portfolio_data.get('total_value', 0):,.2f}",
            delta=f"₹{portfolio_data.get('total_pnl', 0):+,.2f}"
        )

    with col2:
        st.metric(
            "Cash",
            f"₹{portfolio_data.get('cash', 0):,.2f}"
        )

    with col3:
        st.metric(
            "Positions Value",
            f"₹{portfolio_data.get('positions_value', 0):,.2f}"
        )

    with col4:
        pnl = portfolio_data.get('total_pnl', 0)
        pnl_class = "positive" if pnl >= 0 else "negative"
        st.metric(
            "Total P&L",
            f"₹{pnl:+,.2f}",
            delta=f"{pnl/portfolio_data.get('total_value', 1)*100:+.2f}%"
        )

    # Risk status
    risk_status = portfolio_data.get('risk_status', {})
    if not risk_status.get('overall_status', True):
        st.error("⚠️ Risk limits breached! Check positions and reduce exposure.")

def display_positions():
    """Display current positions table."""
    st.header("📋 Current Positions")

    positions_data = api_request("/positions")

    if not positions_data:
        st.info("No positions data available")
        return

    if positions_data:
        df = pd.DataFrame(positions_data)

        # Format columns
        if not df.empty:
            df['average_price'] = df['average_price'].round(2)
            df['current_price'] = df['current_price'].round(2)
            df['unrealized_pnl'] = df['unrealized_pnl'].round(2)
            df['total_pnl'] = df['total_pnl'].round(2)

            # Color coding for P&L
            def color_pnl(val):
                color = 'green' if val >= 0 else 'red'
                return f'color: {color}'

            st.dataframe(
                df.style.applymap(color_pnl, subset=['unrealized_pnl', 'total_pnl']),
                use_container_width=True
            )

            # Position summary chart
            if len(df) > 0:
                fig = px.pie(df, values='quantity', names='symbol',
                           title='Position Distribution by Quantity')
                st.plotly_chart(fig, use_container_width=True)

def display_strategy_management():
    """Display strategy management interface."""
    st.header("🎯 Strategy Management")

    strategies_data = api_request("/strategies")

    if not strategies_data:
        st.warning("Unable to fetch strategies data")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Available Strategies")
        available = strategies_data.get('available', [])
        if available:
            for strategy in available:
                st.write(f"• {strategy}")
        else:
            st.info("No strategies loaded")

    with col2:
        st.subheader("Active Strategies")
        active = strategies_data.get('active', [])
        if active:
            for strategy in active:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"• {strategy}")
                with col_b:
                    if st.button("Deactivate", key=f"deactivate_{strategy}"):
                        result = api_request(f"/strategies/deactivate?strategy_name={strategy}", "POST")
                        if result:
                            st.success(f"Deactivated {strategy}")
                            st.rerun()
        else:
            st.info("No active strategies")

    # Strategy controls
    st.subheader("Strategy Controls")
    with st.form("strategy_form"):
        strategy_name = st.selectbox("Select Strategy", available if available else ["None"])
        action = st.selectbox("Action", ["activate", "deactivate"])

        submitted = st.form_submit_button("Execute")
        if submitted and strategy_name != "None":
            result = api_request(f"/strategies/{action}?strategy_name={strategy_name}", "POST")
            if result:
                st.success(f"Strategy {strategy_name} {action}d")
                st.rerun()

def display_logs():
    """Display recent logs."""
    st.header("📝 System Logs")

    logs_data = api_request("/logs?lines=50")

    if not logs_data:
        st.info("No logs available")
        return

    logs = logs_data.get('logs', [])
    if logs:
        for log in logs[-20:]:  # Show last 20 logs
            st.text(log)
    else:
        st.info("No recent logs")

def display_system_status():
    """Display system status."""
    st.sidebar.header("🔧 System Status")

    status_data = api_request("/status")

    if status_data:
        status = status_data.get('status', 'unknown')
        status_color = "🟢" if status == 'running' else "🔴"

        st.sidebar.metric("Status", f"{status_color} {status.upper()}")

        services = status_data.get('services', {})
        for service, state in services.items():
            icon = "✅" if state == 'active' else "❌"
            st.sidebar.write(f"{icon} {service.replace('_', ' ').title()}: {state}")

        st.sidebar.write(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")

def main():
    """Main dashboard function."""
    st.title("🤖 Finbot Trading Dashboard")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Overview", "Positions", "Strategies", "Logs"]
    )

    # System status in sidebar
    display_system_status()

    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=True)

    # Main content
    if page == "Overview":
        display_portfolio_overview()
    elif page == "Positions":
        display_positions()
    elif page == "Strategies":
        display_strategy_management()
    elif page == "Logs":
        display_logs()

    # Auto-refresh
    if auto_refresh:
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()
