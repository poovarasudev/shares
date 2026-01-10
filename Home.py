"""
Money Control Stock Analyzer - Main Entry Point.

A Streamlit multipage application for analyzing stock data from
various sources including Google Sheets, databases, and APIs.
"""

import streamlit as st
from config import constants as const
from data_sources import DataSourceRegistry, init_data_sources

# ============================================
# Page Configuration
# ============================================
st.set_page_config(
    page_title="Stock Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# Initialize Data Sources
# ============================================
# Initialize all data sources at application startup
init_data_sources()

# ============================================
# Global Styles
# ============================================
st.markdown("""
<style>
/* Global font improvements */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}

/* Main container */
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* Sidebar styling */
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {
    font-size: 1.3rem;
    padding: 0.5rem 0;
}

/* Navigation styling */
[data-testid="stSidebarNav"] {
    padding-top: 1rem;
}

[data-testid="stSidebarNavLink"] {
    border-radius: 8px;
    margin: 2px 0;
    padding: 0.5rem 1rem;
}

[data-testid="stSidebarNavLink"]:hover {
    background-color: rgba(151, 166, 195, 0.15);
}

[data-testid="stSidebarNavLink"][aria-selected="true"] {
    background-color: rgba(151, 166, 195, 0.25);
    font-weight: 600;
}

/* Header styling */
h1 { font-weight: 700 !important; letter-spacing: -0.02em; }
h2, h3 { font-weight: 600 !important; }

/* Metric styling */
[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
    font-weight: 600;
}

[data-testid="stMetricLabel"] {
    font-size: 0.85rem !important;
    color: #9ca3af !important;
}

/* Button styling */
.stButton > button {
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Table styling */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

[data-testid="stDataFrame"] th {
    background-color: rgba(151, 166, 195, 0.1) !important;
    font-weight: 600 !important;
}

/* Card hover effects */
.stContainer {
    transition: transform 0.2s ease;
}

/* Better scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.1);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: rgba(151, 166, 195, 0.5);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(151, 166, 195, 0.7);
}

/* Divider */
hr {
    margin: 0.8rem 0;
    opacity: 0.2;
}

/* Alert boxes */
[data-testid="stAlert"] {
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ============================================
# Sidebar Navigation Info
# ============================================
st.sidebar.title("📊 Navigation")
st.sidebar.info("👈 Select a page above to get started")

# ============================================
# Main Page Content (Home)
# ============================================
st.markdown("# 👋 Welcome to Stock Analysis Dashboard")

st.markdown("""
### Your Comprehensive Stock Analysis Tool

This application provides powerful tools for analyzing stock market data, 
tracking company performance, and making informed investment decisions.

**👈 Select a page from the sidebar** to get started!

---

### 📊 Available Features

| Feature | Description |
|---------|-------------|
| **Market Overview** | Browse and filter companies with advanced search and export capabilities |
| **Company Details** | Detailed analysis including financials, metrics, and analyst ratings |

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

""")

# Footer
st.markdown("---")
st.caption("💡 **Tip:** Use the filters in the Market Overview page to narrow down companies based on your criteria. Data is cached for better performance.")
