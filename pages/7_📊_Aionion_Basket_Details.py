"""
Aionion Capital Basket Details Page.

Displays detailed information about a specific investment basket including
all stocks with their target prices, quantities, and potential returns.
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Optional

from data_sources import DataSourceRegistry, ensure_data_source
from data_sources.registry import load_cached_data
from utils.ui_components import apply_custom_css

# ============================================
# Page Configuration
# ============================================
st.set_page_config(
    page_title="Basket Details - Aionion Capital", page_icon="📊", layout="wide"
)

# Apply custom CSS
apply_custom_css()

# ============================================
# Constants
# ============================================
DATA_SOURCE_NAME = "aionion_baskets"


# ============================================
# Helper Functions
# ============================================
def _format_value(value) -> str:
    """Format value for display."""
    if value is None or pd.isna(value):
        return "-"
    val_str = str(value)
    return val_str if val_str not in ["nan", "None", ""] else "-"


def _format_currency(value) -> str:
    """Format currency value."""
    if value is None or pd.isna(value):
        return "-"
    try:
        val = float(value)
        if val >= 10000000:  # 1 Cr
            return f"₹{val/10000000:.2f} Cr"
        elif val >= 100000:  # 1 Lakh
            return f"₹{val/100000:.2f} L"
        elif val >= 1000:
            return f"₹{val/1000:.2f} K"
        else:
            return f"₹{val:.2f}"
    except (ValueError, TypeError):
        return str(value)


def _format_date(value) -> str:
    """Format date value for display."""
    if value is None or pd.isna(value):
        return "-"
    try:
        val_str = str(value)
        for fmt in ["%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%Y-%m-%d %H:%M:%S"]:
            try:
                dt = datetime.strptime(val_str.split(".")[0], fmt)
                return dt.strftime("%d %b %Y, %I:%M %p")
            except ValueError:
                continue
        return val_str
    except Exception:
        return str(value) if value else "-"


def _parse_basket_scrips(value) -> List[Dict]:
    """Parse basket scrips JSON data."""
    if value is None:
        return []
    # Check if it's already a list
    if isinstance(value, list):
        return value
    # Check for pandas NA values (only for non-list types)
    try:
        if pd.isna(value):
            return []
    except (ValueError, TypeError):
        # pd.isna can fail on some types, continue
        pass
    # Try to parse as JSON string
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def _get_status_badge(status: str) -> tuple[str, str]:
    """Get status badge color and icon."""
    status_lower = str(status).lower() if status else ""
    if "open" in status_lower:
        return "🟢", "#22c55e"
    elif "closed" in status_lower or "expired" in status_lower:
        return "🔴", "#ef4444"
    elif "pending" in status_lower:
        return "🟡", "#f59e0b"
    return "⚪", "#9ca3af"


def _calculate_potential_return(ltp: float, target: float) -> Optional[float]:
    """Calculate potential return percentage."""
    try:
        if ltp and target and ltp > 0:
            return ((target - ltp) / ltp) * 100
        return None
    except (ValueError, TypeError):
        return None


def _get_return_color(return_pct: Optional[float]) -> str:
    """Get color based on potential return."""
    if return_pct is None:
        return "#9ca3af"
    if return_pct >= 50:
        return "#22c55e"  # Green - High potential
    elif return_pct >= 20:
        return "#84cc16"  # Lime - Good potential
    elif return_pct >= 0:
        return "#f59e0b"  # Amber - Moderate
    else:
        return "#ef4444"  # Red - Negative


def get_basket_by_id(df: pd.DataFrame, basket_id: str) -> Optional[pd.Series]:
    """Get basket data by ID."""
    try:
        basket_id_num = int(basket_id)
        matches = df[df["basket_id"] == basket_id_num]
        if not matches.empty:
            return matches.iloc[0]
    except (ValueError, TypeError):
        pass
    return None


# ============================================
# Stock Card Rendering
# ============================================
def render_stock_card(stock: Dict, index: int):
    """Render a single stock card."""
    with st.container(border=True):
        # Stock name and symbol
        script_desc = stock.get("ScriptDescription", "Unknown")
        trading_symbol = stock.get("tradingsymbol", "")
        exchange = stock.get("exchange", "NSE")

        st.markdown(
            f"<h4 style='margin:0; padding:0;'>{script_desc}</h4>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<p style='margin:2px 0; font-size:0.8rem; color:#6b7280;'>"
            f"📌 {trading_symbol} • {exchange}</p>",
            unsafe_allow_html=True,
        )

        st.divider()

        # Price info
        try:
            ltp = float(stock.get("lasttradedprice", 0) or 0)
            target = float(stock.get("targetprice", 0) or 0)
            quantity = int(stock.get("quantity", 0) or 0)
            rec_price = float(stock.get("price", 0) or 0)
        except (ValueError, TypeError):
            ltp, target, quantity, rec_price = 0, 0, 0, 0

        # LTP and Target
        potential_return = _calculate_potential_return(ltp, target)
        return_color = _get_return_color(potential_return)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f"<div style='text-align:center;'>"
                f"<p style='margin:0; font-size:0.75rem; color:#9ca3af;'>LTP</p>"
                f"<p style='margin:2px 0; font-size:1.2rem; font-weight:600;'>"
                f"₹{ltp:.2f}</p></div>",
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"<div style='text-align:center;'>"
                f"<p style='margin:0; font-size:0.75rem; color:#9ca3af;'>Target</p>"
                f"<p style='margin:2px 0; font-size:1.2rem; font-weight:600; "
                f"color:#22c55e;'>₹{target:.2f}</p></div>",
                unsafe_allow_html=True,
            )

        st.divider()

        # Quantity and Investment
        investment = ltp * quantity
        target_value = target * quantity
        potential_gain = target_value - investment

        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(
                f"<div style='text-align:center;'>"
                f"<p style='margin:0; font-size:0.7rem; color:#9ca3af;'>Qty</p>"
                f"<p style='margin:2px 0; font-size:1rem; font-weight:600;'>"
                f"{quantity}</p></div>",
                unsafe_allow_html=True,
            )
        with m2:
            st.markdown(
                f"<div style='text-align:center;'>"
                f"<p style='margin:0; font-size:0.7rem; color:#9ca3af;'>Invest</p>"
                f"<p style='margin:2px 0; font-size:0.9rem; font-weight:600;'>"
                f"₹{investment:.0f}</p></div>",
                unsafe_allow_html=True,
            )
        with m3:
            return_str = f"{potential_return:.1f}%" if potential_return else "-"
            st.markdown(
                f"<div style='text-align:center;'>"
                f"<p style='margin:0; font-size:0.7rem; color:#9ca3af;'>Return</p>"
                f"<p style='margin:2px 0; font-size:0.9rem; font-weight:600; "
                f"color:{return_color};'>📈 {return_str}</p></div>",
                unsafe_allow_html=True,
            )

        # Order details
        order_type = stock.get("ordertype", "MARKET")
        transaction = stock.get("transactiontype", "BUY")
        transaction_color = "#22c55e" if transaction == "BUY" else "#ef4444"

        st.markdown(
            f"<p style='margin:8px 0 0 0; font-size:0.75rem; color:#9ca3af;'>"
            f"<span style='color:{transaction_color};'>● {transaction}</span> • "
            f"{order_type}</p>",
            unsafe_allow_html=True,
        )


# ============================================
# Stock Table Rendering
# ============================================
def render_stock_table(stocks: List[Dict]):
    """Render stocks as a table."""
    if not stocks:
        st.info("No stocks in this basket.")
        return

    # Prepare data for table
    table_data = []
    for stock in stocks:
        try:
            ltp = float(stock.get("lasttradedprice", 0) or 0)
            target = float(stock.get("targetprice", 0) or 0)
            quantity = int(stock.get("quantity", 0) or 0)
            investment = ltp * quantity
            potential_return = _calculate_potential_return(ltp, target)
        except (ValueError, TypeError):
            ltp, target, quantity, investment, potential_return = 0, 0, 0, 0, None

        table_data.append(
            {
                "Stock": stock.get("ScriptDescription", "Unknown"),
                "Symbol": stock.get("tradingsymbol", ""),
                "Exchange": stock.get("exchange", "NSE"),
                "LTP (₹)": ltp,
                "Target (₹)": target,
                "Quantity": quantity,
                "Investment (₹)": investment,
                "Return %": potential_return,
                "Type": stock.get("transactiontype", "BUY"),
            }
        )

    df = pd.DataFrame(table_data)

    # Column config
    column_config = {
        "Stock": st.column_config.TextColumn("Stock", width="large"),
        "Symbol": st.column_config.TextColumn("Symbol", width="medium"),
        "Exchange": st.column_config.TextColumn("Exchange", width="small"),
        "LTP (₹)": st.column_config.NumberColumn("LTP (₹)", format="₹%.2f"),
        "Target (₹)": st.column_config.NumberColumn("Target (₹)", format="₹%.2f"),
        "Quantity": st.column_config.NumberColumn("Qty", format="%d"),
        "Investment (₹)": st.column_config.NumberColumn("Investment", format="₹%.0f"),
        "Return %": st.column_config.NumberColumn("Potential", format="%.1f%%"),
        "Type": st.column_config.TextColumn("Action", width="small"),
    }

    st.dataframe(
        df,
        column_config=column_config,
        hide_index=True,
        width="stretch",
    )


# ============================================
# Main
# ============================================
def main():
    # Get basket_id from query params or session state
    params = st.query_params
    basket_id = params.get("basket_id")

    if not basket_id and "basket_id" in st.session_state:
        basket_id = st.session_state.basket_id

    # Back button
    col1, col2 = st.columns([1, 5])
    with col1:
        st.page_link("pages/6_📦_Aionion_Baskets.py", label="⬅️ Back", width="stretch")

    if not basket_id:
        st.warning("⚠️ No basket ID provided. Please select a basket from the overview.")
        st.page_link("pages/6_📦_Aionion_Baskets.py", label="📦 Go to Baskets")
        return

    # Ensure data source
    if not ensure_data_source(DATA_SOURCE_NAME):
        st.error("❌ Failed to initialize data source.")
        return

    # Load data
    source = DataSourceRegistry.get(DATA_SOURCE_NAME)
    if not source:
        st.error("❌ Data source not configured.")
        return

    with st.spinner("Loading basket details..."):
        df = load_cached_data(DATA_SOURCE_NAME, source)

    if df.empty:
        st.error("❌ No data available.")
        return

    # Find the basket
    basket = get_basket_by_id(df, basket_id)

    if basket is None:
        st.error(f"❌ Basket with ID '{basket_id}' not found.")
        st.page_link("pages/6_📦_Aionion_Baskets.py", label="📦 Go to Baskets")
        return

    # ---- Header Section ----
    basket_name = basket.get("basket_name", "Unknown Basket")
    status = basket.get("status", "Unknown")
    status_icon, status_color = _get_status_badge(status)

    st.markdown(
        f"<h1 style='margin-bottom:0;'>📦 {basket_name}</h1>",
        unsafe_allow_html=True,
    )

    # Status and description
    description = basket.get("status_descreption", "")
    st.markdown(
        f"<p style='font-size:1.1rem;'>"
        f"<span style='color:{status_color};'>{status_icon} {status}</span>"
        f"{' • ' + description if description and str(description) not in ['nan', 'None'] else ''}"
        f"</p>",
        unsafe_allow_html=True,
    )

    st.divider()

    # ---- Metrics Row ----
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Category", _format_value(basket.get("category_name")))
    with col2:
        st.metric("Basket Type", _format_value(basket.get("basket_category")))
    with col3:
        st.metric("Strategy", _format_value(basket.get("investment_strategy")))
    with col4:
        st.metric("Amount Range", _format_value(basket.get("amount_range")))
    with col5:
        st.metric("Investment Type", _format_value(basket.get("investment_type")))

    # ---- Dates Row ----
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**📅 Created:** {_format_date(basket.get('insertion_time'))}")
    with col2:
        st.markdown(f"**⏰ Valid Till:** {_format_date(basket.get('validity'))}")
    with col3:
        attachment_url = basket.get("attachment_url")
        if attachment_url and str(attachment_url) not in ["nan", "None", ""]:
            attachment_name = basket.get("attachment_name", "Document")
            st.link_button(f"📎 {attachment_name}", attachment_url)

    st.divider()

    # ---- Stocks Section ----
    scrips = _parse_basket_scrips(basket.get("basket_scrips"))

    if not scrips:
        st.info("📭 No stocks in this basket.")
        return

    # Calculate totals
    total_investment = 0
    total_target_value = 0
    for stock in scrips:
        try:
            ltp = float(stock.get("lasttradedprice", 0) or 0)
            target = float(stock.get("targetprice", 0) or 0)
            qty = int(stock.get("quantity", 0) or 0)
            total_investment += ltp * qty
            total_target_value += target * qty
        except (ValueError, TypeError):
            continue

    potential_gain = total_target_value - total_investment
    overall_return = (
        (potential_gain / total_investment * 100) if total_investment > 0 else 0
    )

    # Summary metrics
    st.markdown("### 📊 Portfolio Summary")
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric("Total Stocks", f"{len(scrips)} 📊")
    with m2:
        st.metric("Total Investment", _format_currency(total_investment))
    with m3:
        st.metric("Target Value", _format_currency(total_target_value))
    with m4:
        return_color = _get_return_color(overall_return)
        st.metric(
            "Potential Return",
            f"{overall_return:.1f}%",
            delta=_format_currency(potential_gain),
        )

    st.divider()

    # View toggle
    st.markdown(f"### 📋 Stocks in Basket ({len(scrips)})")

    view_mode = st.radio(
        "View",
        ["🃏 Cards", "📋 Table"],
        horizontal=True,
        label_visibility="collapsed",
        key="stock_view_mode",
    )

    if "Table" in view_mode:
        render_stock_table(scrips)
    else:
        # Card view
        cols_per_row = 3
        for i in range(0, len(scrips), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, stock in enumerate(scrips[i : i + cols_per_row]):
                with cols[j]:
                    render_stock_card(stock, i + j)

    # ---- Additional Info ----
    st.divider()

    with st.expander("📝 Additional Information"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Basket ID:** {basket.get('basket_id')}")
            st.markdown(f"**Entry ID:** {basket.get('basket_call_entry_id')}")
            st.markdown(f"**User ID:** {basket.get('user_id')}")

        with col2:
            st.markdown(f"**Header:** {_format_value(basket.get('header'))}")
            st.markdown(f"**Send To:** {_format_value(basket.get('send_to'))}")
            st.markdown(
                f"**Active:** {'Yes' if basket.get('is_active') == 1 else 'No'}"
            )

        # Raw data
        if st.checkbox("Show raw basket data"):
            st.json(basket.to_dict())


if __name__ == "__main__":
    main()
