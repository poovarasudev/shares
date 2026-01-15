"""
Aionion Capital Baskets Alerts - Market Overview Page.

Displays investment basket recommendations from Aionion Capital with filtering,
sorting, and export functionality. Each basket contains recommended stocks
for long-term investment.
"""

import streamlit as st
from streamlit_js_eval import streamlit_js_eval
import pandas as pd
import json
from datetime import datetime
import zoneinfo
from typing import List, Tuple, Dict

from data_sources import DataSourceRegistry, ensure_data_source
from data_sources.registry import load_cached_data, clear_source_cache
from utils.ui_components import apply_custom_css

# ============================================
# Page Configuration
# ============================================
st.set_page_config(page_title="Aionion Capital Baskets", page_icon="📦", layout="wide")

# Apply custom CSS
apply_custom_css()

# ============================================
# Constants
# ============================================
ITEMS_PER_PAGE = 12
CARDS_PER_ROW = 3
DATA_SOURCE_NAME = "aionion_baskets"
TIMEZONE = zoneinfo.ZoneInfo("Asia/Kolkata")

# Column definitions: (display_name, column_key, is_visible_by_default, width)
COLUMN_DEFINITIONS = [
    ("Basket Name", "basket_name", True, "large"),
    ("Status", "status", True, "small"),
    ("Basket Value", "basket_value", True, "small"),
    ("Validity", "validity", True, "small"),
    ("Created", "insertion_time", True, "small"),
    ("Stocks", "_stock_count", True, "small"),
    ("Attachment", "attachment_url", True, "small"),
]


# ============================================
# Helper Functions
# ============================================
def _format_value(value) -> str:
    """Format value for display."""
    if value is None or pd.isna(value):
        return "-"
    val_str = str(value)
    return val_str if val_str not in ["nan", "None", ""] else "-"


def _format_date(value) -> str:
    """Format date value for display."""
    if value is None or pd.isna(value):
        return "-"
    try:
        val_str = str(value)
        # Try parsing common formats
        for fmt in ["%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%Y-%m-%d %H:%M:%S"]:
            try:
                dt = datetime.strptime(val_str.split(".")[0], fmt)
                return dt.strftime("%d %b %Y")
            except ValueError:
                continue
        return val_str[:10] if len(val_str) > 10 else val_str
    except Exception:
        return str(value)[:10] if value else "-"


def _parse_date_object(value) -> datetime:
    """Parse date string to datetime object."""
    if value is None or pd.isna(value):
        return datetime.min.replace(tzinfo=TIMEZONE)

    try:
        val_str = str(value)
        # Try parsing common formats
        for fmt in [
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]:
            try:
                dt = datetime.strptime(val_str.split(".")[0], fmt)
                return dt.replace(tzinfo=TIMEZONE)
            except ValueError:
                continue
        return datetime.min.replace(tzinfo=TIMEZONE)
    except Exception:
        return datetime.min.replace(tzinfo=TIMEZONE)


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


def _count_stocks(row) -> int:
    """Count number of stocks in basket."""
    scrips = _parse_basket_scrips(row.get("basket_scrips"))
    return len(scrips)


def _calculate_basket_value(row) -> float:
    """Calculate total basket value from lasttradedprice * quantity."""
    scrips = _parse_basket_scrips(row.get("basket_scrips"))
    total = 0.0
    for scrip in scrips:
        try:
            # User check: SUM(lasttradedprice * quantity)
            price_val = scrip.get("lasttradedprice", 0)
            qty_val = scrip.get("quantity", 0)

            price = float(price_val if price_val else 0)
            qty = int(qty_val if qty_val else 0)

            total += price * qty
        except (ValueError, TypeError):
            continue
    return round(total)


def _format_currency(value) -> str:
    """Format currency value without decimals."""
    if value is None or pd.isna(value):
        return "-"
    try:
        val = float(value)
        if val >= 10000000:  # 1 Cr
            return f"₹{round(val/10000000)} Cr"
        elif val >= 100000:  # 1 Lakh
            return f"₹{round(val/100000)} L"
        else:
            return f"₹{val:,.0f}"
    except (ValueError, TypeError):
        return str(value)


def _init_session_state():
    """Initialize session state variables."""
    if "aionion_current_page" not in st.session_state:
        st.session_state.aionion_current_page = 1

    # Always update visible columns to match COLUMN_DEFINITIONS
    st.session_state.aionion_visible_columns = [
        col_key for _, col_key, visible, _ in COLUMN_DEFINITIONS if visible
    ]


def _get_column_config(visible_columns: List[str]) -> Dict:
    """Generate column configuration for dataframe display."""
    config = {}

    for display_name, col_key, _, _ in COLUMN_DEFINITIONS:
        if col_key not in visible_columns:
            continue

        if col_key == "attachment_url":
            config[col_key] = st.column_config.LinkColumn(
                display_name, help="Download attachment", display_text="📎 View"
            )
        elif col_key in ["insertion_time", "validity"]:
            config[col_key] = st.column_config.TextColumn(display_name)
        elif col_key == "_stock_count":
            config[col_key] = st.column_config.NumberColumn(
                display_name, format="%d 📊"
            )
        elif col_key == "basket_value":
            config[col_key] = st.column_config.NumberColumn(
                display_name, format="₹%.0f"
            )
        else:
            config[col_key] = st.column_config.Column(display_name)

    return config


def _get_status_badge(status: str) -> Tuple[str, str]:
    """Get status badge color and icon."""
    status_lower = str(status).lower() if status else ""
    if "open" in status_lower:
        return "🟢", "#22c55e"
    elif "closed" in status_lower or "expired" in status_lower:
        return "🔴", "#ef4444"
    elif "pending" in status_lower:
        return "🟡", "#f59e0b"
    return "⚪", "#9ca3af"


def _get_strategy_color(strategy: str) -> str:
    """Get color for investment strategy."""
    strategy_lower = str(strategy).lower() if strategy else ""
    if "aggressive" in strategy_lower:
        return "#ef4444"  # Red
    elif "moderate" in strategy_lower:
        return "#f59e0b"  # Amber
    elif "conservative" in strategy_lower or "value" in strategy_lower:
        return "#22c55e"  # Green
    return "#6366f1"  # Indigo default


# ============================================
# Filter Rendering
# ============================================
def render_filters(df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """Render sidebar filters and return filtered DataFrame with counts."""
    if df.empty:
        return df, 0, 0

    filtered_df = df.copy()

    st.sidebar.markdown("### 🔍 Filters")

    # --- Text Search ---
    search_query = (
        st.sidebar.text_input(
            "Search Basket",
            placeholder="e.g. October Basket, Diwali...",
            key="aionion_search_input",
        )
        .strip()
        .lower()
    )

    if search_query:
        mask_name = (
            filtered_df["basket_name"]
            .astype(str)
            .str.lower()
            .str.contains(search_query, na=False)
        )
        mask_header = (
            filtered_df["header"]
            .astype(str)
            .str.lower()
            .str.contains(search_query, na=False)
        )
        filtered_df = filtered_df[mask_name | mask_header]

    # --- Active/Expired Status Filter ---
    # Based on Validity column vs Current Time (Asia/Kolkata)

    status_filter = st.sidebar.radio(
        "Basket Status",
        ["Active", "Expired", "All"],
        index=0,  # Default to Active
        key="aionion_validity_filter",
    )

    if status_filter != "All":
        # Calculate validity objects
        current_time = datetime.now(TIMEZONE)

        # We need a proper column for comparison
        filtered_df["_validity_dt"] = filtered_df["validity"].apply(_parse_date_object)

        if status_filter == "Active":
            filtered_df = filtered_df[filtered_df["_validity_dt"] >= current_time]
        else:  # Expired
            filtered_df = filtered_df[filtered_df["_validity_dt"] < current_time]

    st.sidebar.caption(
        "ℹ️ 'Active' Status is based on Validity Date vs Current Time (IST)"
    )

    # --- Filter Actions ---
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Refresh", width="stretch", key="aionion_refresh_data"):
            clear_source_cache(DATA_SOURCE_NAME)
            st.rerun()

    with col2:
        if st.button("✖️ Clear", width="stretch", key="aionion_clear_filters"):
            streamlit_js_eval(js_expressions="parent.window.location.reload()")

    # Return filtered data with counts
    total = len(df)
    filtered = len(filtered_df)

    return filtered_df, total, filtered


# ============================================
# Pagination
# ============================================
def render_pagination(total_items: int, items_per_page: int) -> Tuple[int, int]:
    """Render pagination controls and return start/end indices."""
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)

    if st.session_state.aionion_current_page > total_pages:
        st.session_state.aionion_current_page = 1

    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button(
            "⏮️",
            disabled=st.session_state.aionion_current_page == 1,
            width="stretch",
            help="First page",
            key="aionion_first_page",
        ):
            st.session_state.aionion_current_page = 1
            st.rerun()

    with col2:
        if st.button(
            "◀️",
            disabled=st.session_state.aionion_current_page == 1,
            width="stretch",
            help="Previous page",
            key="aionion_prev_page",
        ):
            st.session_state.aionion_current_page -= 1
            st.rerun()

    with col3:
        st.markdown(
            f"<div style='text-align:center; padding:8px;'>"
            f"Page <b>{st.session_state.aionion_current_page}</b> of <b>{total_pages}</b>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col4:
        if st.button(
            "▶️",
            disabled=st.session_state.aionion_current_page == total_pages,
            width="stretch",
            help="Next page",
            key="aionion_next_page",
        ):
            st.session_state.aionion_current_page += 1
            st.rerun()

    with col5:
        if st.button(
            "⏭️",
            disabled=st.session_state.aionion_current_page == total_pages,
            width="stretch",
            help="Last page",
            key="aionion_last_page",
        ):
            st.session_state.aionion_current_page = total_pages
            st.rerun()

    start_idx = (st.session_state.aionion_current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)

    return start_idx, end_idx


# ============================================
# Table View
# ============================================
def render_table_view(df: pd.DataFrame):
    """Render data table with configurable columns."""
    visible_cols = st.session_state.aionion_visible_columns

    # Filter to only existing columns
    existing_cols = [col for col in visible_cols if col in df.columns]

    if not existing_cols:
        st.warning("No columns selected. Please select at least one column.")
        return

    # Always include basket_id for navigation
    if "basket_id" not in existing_cols and "basket_id" in df.columns:
        display_cols = existing_cols + ["basket_id"]
    else:
        display_cols = existing_cols

    display_df = df[display_cols].copy()
    column_config = _get_column_config(existing_cols)

    # Add action column with detail button
    column_config["_action"] = st.column_config.LinkColumn(
        "Details", help="View basket details", display_text="🔍 View"
    )

    # Add action links
    if "basket_id" in display_df.columns:
        display_df["_action"] = display_df["basket_id"].apply(
            lambda x: f"/Aionion_Basket_Details?basket_id={x}" if pd.notna(x) else ""
        )
        existing_cols.append("_action")

    # Display dataframe
    st.dataframe(
        display_df,
        column_order=existing_cols,
        column_config=column_config,
        width="stretch",
        hide_index=True,
        height=600,
    )


# ============================================
# Card View
# ============================================
def render_card_view(df: pd.DataFrame):
    """Render card view with pagination and sorting."""
    if df.empty:
        st.info("📭 No baskets match your filters.")
        return

    # Sort controls
    sort_column_map = {
        "Basket Name": "basket_name",
        "Created Date": "insertion_time",
        "Valid Till": "_validity_dt" if "_validity_dt" in df.columns else "validity",
        "Basket Value": "basket_value",
        "Stock Count": "_stock_count",
    }

    sort_col1, sort_col2 = st.columns([2, 0.8])

    with sort_col1:
        sort_column_display = st.selectbox(
            "Sort by",
            list(sort_column_map.keys()),
            index=1,  # Default to Created Date
            label_visibility="collapsed",
            key="aionion_card_sort_column",
        )

    with sort_col2:
        sort_direction = st.selectbox(
            "Order",
            ["↓ Desc", "↑ Asc"],
            index=0,
            label_visibility="collapsed",
            key="aionion_card_sort_direction",
        )

    # Apply sorting
    sort_col = sort_column_map.get(sort_column_display, "insertion_time")
    ascending = "↑" in sort_direction

    # Ensure _validity_dt is available if needed for sort
    if sort_col == "_validity_dt" and "_validity_dt" not in df.columns:
        df["_validity_dt"] = df["validity"].apply(_parse_date_object)

    if sort_col in df.columns:
        df = df.sort_values(by=sort_col, ascending=ascending, na_position="last")

    # Pagination
    start_idx, end_idx = render_pagination(len(df), ITEMS_PER_PAGE)
    st.caption(f"Showing {start_idx + 1}-{end_idx} of {len(df)} baskets")

    paginated_df = df.iloc[start_idx:end_idx]

    # Render grid
    rows = []
    current_row = []

    for i, (_, row) in enumerate(paginated_df.iterrows()):
        current_row.append((row, start_idx + i))
        if len(current_row) == CARDS_PER_ROW:
            rows.append(current_row)
            current_row = []

    if current_row:
        rows.append(current_row)

    for row_items in rows:
        cols = st.columns(CARDS_PER_ROW)
        for col_idx, (row_data, _) in enumerate(row_items):
            with cols[col_idx]:
                _render_basket_card(row_data)


def _render_basket_card(row: pd.Series):
    """Render a single basket card."""
    with st.container(border=True):
        # Header
        c1, c2 = st.columns([0.7, 0.3])
        basket_name = row.get("basket_name", "Unknown Basket")
        c1.markdown(
            f"<h4 style='margin:0; padding:0;'>{basket_name}</h4>",
            unsafe_allow_html=True,
        )

        status = row.get("status", "Unknown")
        status_icon, status_color = _get_status_badge(status)
        c2.markdown(
            f"<div style='text-align:right; padding:0; margin:0;'>"
            f"<span style='color:{status_color};'>{status_icon} {status}</span></div>",
            unsafe_allow_html=True,
        )

        # Description
        description = row.get("status_descreption", "")
        if description and str(description) not in ["nan", "None", ""]:
            st.markdown(
                f"<p style='margin:2px 0 6px 0; font-size:0.85rem; color:#6366f1; "
                f"font-weight:500;'>💰 {description}</p>",
                unsafe_allow_html=True,
            )

        # Script List (Replacing tags)
        scrips = _parse_basket_scrips(row.get("basket_scrips"))
        if scrips:
            script_names = [
                s.get("ScriptDescription", s.get("tradingsymbol", "")) for s in scrips
            ]
            # Join with pipe
            script_str = " | ".join(script_names)
            st.markdown(
                f"<p style='margin:0 0 8px 0; font-size:0.75rem; color:#6b7280; line-height:1.2;'>"
                f"📋 {script_str}</p>",
                unsafe_allow_html=True,
            )

        # Value and Count Row (Standard Style with Divider)
        st.divider()
        val_col1, val_col2 = st.columns(2)

        # Basket Value
        basket_value = row.get("basket_value", 0)
        formatted_val = _format_currency(basket_value)

        with val_col1:
            st.markdown(
                f"<div style='text-align:center;'>"
                f"<p style='margin:0; font-size:0.75rem; color:#9ca3af;'>Basket Value</p>"
                f"<p style='margin:2px 0; font-size:1.1rem; font-weight:600; color:#22c55e;'>"
                f"{formatted_val}</p></div>",
                unsafe_allow_html=True,
            )

        # Stock count
        stock_count = row.get("_stock_count", 0)
        with val_col2:
            st.markdown(
                f"<div style='text-align:center;'>"
                f"<p style='margin:0; font-size:0.75rem; color:#9ca3af;'>Stocks</p>"
                f"<p style='margin:2px 0; font-size:1.1rem; font-weight:600;'>"
                f"📊 {stock_count}</p></div>",
                unsafe_allow_html=True,
            )

        # Dates (Standard Style with Divider)
        st.divider()
        d1, d2 = st.columns(2)
        created = _format_date(row.get("insertion_time", ""))
        validity = _format_date(row.get("validity", ""))

        with d1:
            st.markdown(
                f"<div style='text-align:left;'>"
                f"<p style='margin:0; font-size:0.7rem; color:#9ca3af;'>Created</p>"
                f"<p style='margin:2px 0; font-size:0.85rem; font-weight:500;'>"
                f"{created}</p></div>",
                unsafe_allow_html=True,
            )
        with d2:
            st.markdown(
                f"<div style='text-align:right;'>"
                f"<p style='margin:0; font-size:0.7rem; color:#9ca3af;'>Valid Till</p>"
                f"<p style='margin:2px 0; font-size:0.85rem; font-weight:500;'>"
                f"{validity}</p></div>",
                unsafe_allow_html=True,
            )

        # Actions
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        btn1, btn2 = st.columns(2, gap="small")
        with btn1:
            basket_id = str(row.get("basket_id", ""))
            if st.button("📊 Details", key=f"btn_det_{row.name}", width="stretch"):
                st.session_state["basket_id"] = basket_id
                st.query_params["basket_id"] = basket_id
                st.switch_page("pages/7_📊_Aionion_Basket_Details.py")

        with btn2:
            attachment_url = row.get("attachment_url")
            if attachment_url and str(attachment_url) not in ["nan", "None", ""]:
                st.link_button("📎 PDF", attachment_url, width="stretch")


# ============================================
# Main
# ============================================
def main():
    _init_session_state()

    # Ensure data source is available (fallback initialization)
    if not ensure_data_source(DATA_SOURCE_NAME):
        st.error("❌ Failed to initialize data source. Please check your settings.")
        return

    # Header
    st.markdown("# 📦 Aionion Capital Baskets")
    st.markdown(
        "<p style='color:#6b7280;'>Investment basket recommendations for long-term growth</p>",
        unsafe_allow_html=True,
    )

    # Load data
    source = DataSourceRegistry.get(DATA_SOURCE_NAME)
    if not source:
        st.error("❌ Data source not configured. Please check your settings.")
        return

    with st.spinner("Loading baskets..."):
        df = load_cached_data(DATA_SOURCE_NAME, source)

    if df.empty:
        st.warning("📭 No data available. Please check the data source.")
        return

    # Add computed columns
    df["_stock_count"] = df.apply(_count_stocks, axis=1)
    df["basket_value"] = df.apply(_calculate_basket_value, axis=1)

    # Sidebar filters
    filtered_df, total_count, filtered_count = render_filters(df)

    # Show basket count
    if filtered_count == total_count:
        st.info(f"📋 Showing all **{total_count:,}** baskets")
    else:
        st.success(f"🎯 Showing **{filtered_count:,}** of **{total_count:,}** baskets")

    # Cache info
    st.sidebar.markdown("---")

    st.markdown("---")

    # View controls
    col1, col2 = st.columns([2, 1])

    with col1:
        view_mode = st.radio(
            "View",
            ["🃏 Cards", "📋 Table"],
            horizontal=True,
            label_visibility="collapsed",
            key="aionion_view_mode",
        )

    with col2:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            "📥 Export CSV",
            data=csv,
            file_name=f"aionion_baskets_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            width="stretch",
            key="aionion_export_csv",
        )

    st.markdown("---")

    # Render view
    if "Table" in view_mode:
        render_table_view(filtered_df)
    else:
        render_card_view(filtered_df)


if __name__ == "__main__":
    main()
