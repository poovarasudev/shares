"""
Configuration constants for the Money Control Streamlit Application.

This module houses all constant values used across the application including:
- Application sizing and layout settings
- Data source configurations (Google Sheets)
- Data structure definitions (Columns, Filters)
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==========================================
# Data Source Configuration
# ==========================================
# Google Sheets Connection Details
GOOGLE_SHEET_URL = os.getenv("STOCK_GOOGLE_SHEET_URL", "")
GOOGLE_SHEET_TAB = "Money Control Stocks List"
GOOGLE_SHEET_EVENTS_TAB = "Money Control Events"

# ==========================================
# Data Structure & Columns
# ==========================================

# Columns to parse as JSON (if data contains structured fields)
JSON_COLUMNS = [
    "financial_metrics",
    "technical_indicators",
    "seasonality_analysis",
    "analyst_ratings",
]

# Columns to display in the main List View table (default visible)
TABLE_COLUMNS = [
    "Company Name", 
    "Sector", 
    "Industry", 
    "Cost",
    "M-Score",
    "TTM PE",
    "Analyst Rating",
    "Company URL"
]

# Numeric columns for type conversion
NUMERIC_COLUMNS = [
    "m_score",
    "cost", 
    "ttm_eps",
    "ttm_pe",
    "p_b",
    "sector_pe",
    "analyst_count"
]

# ==========================================
# Filter Configurations
# ==========================================

# Columns to use for categorical dropdown filters
FILTER_COLUMNS = ["sector", "industry", "status"]


# ==========================================
# Derived metrics / thresholds (tunable)
# ==========================================
# M-Score thresholds (lower is better in this dataset)
M_SCORE_THRESHOLD = 20
BAD_M_SCORE_THRESHOLD = 60

# PE comparison thresholds (percent)
# Companies more than this % below sector considered 'cheap'
PE_CHEAP_PCT = 20
# Symmetric delta to mark meaningful over/under valuation
PE_DELTA_PCT = 20

# Price-to-Book threshold
PB_THRESHOLD = 3.0

# Analyst confidence settings
ANALYST_COUNT_THRESHOLD = 3
ANALYST_COUNT_CAP = 10
ANALYST_SCORE_WEIGHTS = {
    'Strong Buy': 1.0,
    'Buy': 0.8,
    'Outperform': 0.8,
    'Hold': 0.5,
    'Underperform': 0.2,
    'Sell': 0.0
}
ANALYST_CONFIDENCE_BUCKETS = {'high': 70, 'medium': 40}


# ==========================================
# Events Configuration
# ==========================================
# Event columns (for Money Control Events sheet)
# Note: These will be converted to snake_case by data source
EVENT_COLUMNS = [
    "stock_name",
    "event_type",
    "announcement_date",
    "ex_date",
    "details",
    "last_trade_price",
    "description",
    "url"
]

# Event filter columns
EVENT_FILTER_COLUMNS = ["event_type", "notification_status"]

# Event search columns
EVENT_SEARCH_COLUMNS = ["stock_name", "sc_id"]
