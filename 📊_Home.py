"""
Money Control Stock Analyzer - Main Entry Point.

A Streamlit multipage application for analyzing stock data from
various sources including Google Sheets, databases, and APIs.
"""

import streamlit as st
from data_sources import init_data_sources

# ============================================
# Page Configuration
# ============================================
st.set_page_config(
    page_title="Stock Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================
# Initialize Data Sources
# ============================================
# Initialize all data sources at application startup
init_data_sources()

# ============================================
# Main Page Content (Home)
# ============================================
st.markdown("# 👋 Welcome to Stock Analysis Dashboard")

st.markdown(
    """
### Your Comprehensive Stock Analysis Tool

This application provides powerful tools for analyzing stock market data, 
tracking company performance, and making informed investment decisions.

**👈 Select a page from the sidebar** to get started!

---

### 📊 Available Features

| Feature | Description |
|---------|-------------|
| **MC Market Overview** | Browse and filter Money Control companies with advanced search and export capabilities |
| **MC Company Details** | Detailed analysis including financials, metrics, and analyst ratings from Money Control |
| **MC Corporate Events** | Track upcoming stock splits, dividends, and bonus issues from Money Control |
| **ScanX Market Overview** | Browse and filter ScanX Trade companies with market cap, PE, and sector filters |
| **ScanX Company Details** | Detailed company view with sector comparisons and analyst ratings from ScanX Trade |

---

### 🔜 Coming Soon

- **Portfolio Tracker** - Track and monitor your investment portfolio
- **Stock Screener** - Find stocks matching your investment criteria  
- **Watchlist** - Keep an eye on your favorite stocks
- **Real-time Data** - Live market data and price updates
- **Technical Analysis** - Charts and technical indicators
- **Comparison Tool** - Compare multiple stocks side-by-side

---

### 💡 Key Features

✨ **Advanced Filtering** - Filter by sector, industry, PE ratio, analyst ratings and more  
📊 **Visual Analytics** - Interactive cards and tables for easy data exploration  
📈 **Financial Metrics** - M-Score, PE ratios, EPS, and comprehensive company metrics  
📥 **Data Export** - Export filtered data to CSV for further analysis  
🔍 **Smart Search** - Quickly find companies by name or ID

"""
)

# Footer
st.markdown("---")
st.caption(
    "💡 **Tip:** Use the filters in the Market Overview page to narrow down companies based on your criteria. Data is cached for better performance."
)
