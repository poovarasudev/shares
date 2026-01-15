"""
ScanX Trade Market Overview Page.

Displays a comprehensive list of stocks from ScanX Trade with filtering, sorting,
column visibility controls, and export functionality.
"""

import streamlit as st
from streamlit_js_eval import streamlit_js_eval
import pandas as pd
import re
from datetime import datetime
from typing import List, Tuple, Dict

from data_sources import DataSourceRegistry, ensure_data_source
from data_sources.registry import load_cached_data, clear_source_cache

# ============================================
# Page Configuration
# ============================================
st.set_page_config(
    page_title="ScanX Trade Market Overview", page_icon="📊", layout="wide"
)

# ============================================
# Constants
# ============================================
ITEMS_PER_PAGE = 15
CARDS_PER_ROW = 3
DATA_SOURCE_NAME = "scanx_trade"

# Column definitions: (display_name, column_key, is_visible_by_default, width)
COLUMN_DEFINITIONS = [
    ("Company", "disp_sym", True, "medium"),
    ("Sector", "sector", True, "medium"),
    ("Sub-Sector", "sub_sector", True, "medium"),
    ("LTP (₹)", "ltp", True, "small"),
    ("PE", "pe", True, "small"),
    ("P/B", "pb", True, "small"),
    ("Sector PE", "ind__pe", True, "small"),
    ("Sector P/B", "ind__pb", True, "small"),
    ("Sector EPS", "ind__eps", True, "small"),
    ("PE vs Sec %", "pe_vs_sector_pct", True, "small"),
    ("PB vs Sec %", "pb_vs_sector_pct", True, "small"),
    ("PE/Sec PE", "pe_sec_pe_ratio", True, "small"),
    ("EPS (Yearly)", "yearly_earning_per_share", True, "small"),
    ("Current Ratio", "current_rto", True, "small"),
    ("Analyst Rating", "analyst_final_rating", True, "small"),
    ("Analyst Count", "total_analyst_count", True, "small"),
    ("M-Cap (Cr)", "mcap", True, "small"),
    ("Status", "status", True, "small"),
    ("ScanX Url", "url", True, "small"),
]


# ============================================
# Helper Functions
# ============================================
def _format_metric(value) -> str:
    """Format metric value for display."""
    if value is None or pd.isna(value):
        return "-"
    if isinstance(value, (int, float)):
        if value == 0:
            return "0"
        return f"{value:.2f}" if isinstance(value, float) else str(value)
    val_str = str(value)
    return val_str if val_str not in ["nan", "None", ""] else "-"


def _format_mcap(value) -> str:
    """Format market cap value for display."""
    if value is None or pd.isna(value):
        return "-"
    try:
        mcap = float(value)
        if mcap >= 100000:
            return f"₹{mcap/100000:.2f}L Cr"
        elif mcap >= 1000:
            return f"₹{mcap/1000:.2f}K Cr"
        else:
            return f"₹{mcap:.2f} Cr"
    except (ValueError, TypeError):
        return "-"


def _format_pe_with_highlight(pe, sector_pe) -> Tuple[str, str]:
    """
    Format PE value with color highlighting based on comparison with sector PE.

    Returns:
        Tuple of (formatted_value, css_color)
        - Green: PE significantly below sector (undervalued)
        - Red: PE significantly above sector (overvalued)
        - Default: PE within normal range
    """
    if pe is None or pd.isna(pe):
        return "-", "#9ca3af"  # gray for missing

    formatted = f"{float(pe):.2f}"

    if sector_pe is not None and not pd.isna(sector_pe) and float(sector_pe) > 0:
        pe_val = float(pe)
        sector_val = float(sector_pe)
        ratio = (pe_val - sector_val) / sector_val * 100

        if ratio <= -20:  # 20% cheaper than sector
            return formatted, "#22c55e"  # green - undervalued
        elif ratio >= 20:  # 20% more expensive than sector
            return formatted, "#ef4444"  # red - overvalued

    return formatted, "#f59e0b"  # amber - neutral/fair


def _init_session_state():
    """Initialize session state variables."""
    if "scanx_current_page" not in st.session_state:
        st.session_state.scanx_current_page = 1

    # Always update visible columns to match COLUMN_DEFINITIONS
    # This ensures changes to default visibility are immediately reflected
    st.session_state.scanx_visible_columns = [
        col_key for _, col_key, visible, _ in COLUMN_DEFINITIONS if visible
    ]


def _get_column_config(visible_columns: List[str]) -> Dict:
    """Generate column configuration for dataframe display."""
    config = {}

    for display_name, col_key, _, _ in COLUMN_DEFINITIONS:
        if col_key not in visible_columns:
            continue

        if col_key == "url":
            config[col_key] = st.column_config.LinkColumn(
                display_name, help="Click to open in ScanX Trade", display_text="View"
            )
        elif col_key == "ltp":
            config[col_key] = st.column_config.NumberColumn(
                display_name, format="₹%.2f"
            )
        elif col_key == "mcap":
            config[col_key] = st.column_config.NumberColumn(display_name, format="%.2f")
        elif col_key in [
            "pe",
            "pb",
            "ind__pe",
            "ind__pb",
            "ind__eps",
            "yearly_earning_per_share",
        ]:
            config[col_key] = st.column_config.NumberColumn(display_name, format="%.2f")
        elif col_key == "pchange":
            config[col_key] = st.column_config.NumberColumn(
                display_name, format="%.2f%%"
            )
        elif col_key in ["pe_vs_sector_pct", "pb_vs_sector_pct"]:
            config[col_key] = st.column_config.NumberColumn(
                display_name, format="%.2f%%"
            )
        elif col_key == "pe_sec_pe_ratio":
            config[col_key] = st.column_config.NumberColumn(display_name, format="%.2f")
        elif col_key == "current_rto":
            config[col_key] = st.column_config.NumberColumn(display_name, format="%.2f")
        else:
            config[col_key] = st.column_config.Column(display_name)

    return config


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
            "Search Company",
            placeholder="e.g. Reliance, TCS...",
            key="scanx_search_input",
        )
        .strip()
        .lower()
    )

    if search_query:
        mask_name = (
            filtered_df["disp_sym"]
            .astype(str)
            .str.lower()
            .str.contains(search_query, na=False)
        )
        mask_sym = (
            filtered_df["sym"]
            .astype(str)
            .str.lower()
            .str.contains(search_query, na=False)
        )
        filtered_df = filtered_df[mask_name | mask_sym]

    # --- Category Filters ---
    def apply_multiselect(column_name: str, label: str, default_values: list = None):
        nonlocal filtered_df
        if column_name in df.columns:
            options = sorted(df[column_name].dropna().astype(str).unique().tolist())
            default = (
                default_values
                if default_values and all(v in options for v in default_values)
                else []
            )
            selected = st.sidebar.multiselect(
                label, options, default=default, key=f"scanx_filter_{column_name}"
            )
            if selected:
                filtered_df = filtered_df[filtered_df[column_name].isin(selected)]

    apply_multiselect("sector", "Sector")
    apply_multiselect("sub_sector", "Sub-Sector")
    apply_multiselect("analyst_final_rating", "Analyst Rating")

    # Helper for range filters
    def apply_range_filter(
        column_name: str,
        label: str,
        min_val: float = None,
        max_val: float = None,
        step: float = 0.1,
    ):
        nonlocal filtered_df
        if column_name in df.columns:
            if st.sidebar.checkbox(f"Filter by {label}", key=f"scanx_cb_{column_name}"):
                values = df[column_name].dropna()
                if not values.empty:
                    actual_min = float(values.min())
                    actual_max = float(values.max())

                    # Use provided min/max or actuals
                    low = min_val if min_val is not None else actual_min
                    high = max_val if max_val is not None else actual_max

                    # Ensure range is valid
                    if low < high:
                        selected_range = st.sidebar.slider(
                            f"{label} Range",
                            min_value=low,
                            max_value=high,
                            value=(low, high),
                            step=step,
                            key=f"scanx_slider_{column_name}",
                        )
                        filtered_df = filtered_df[
                            (filtered_df[column_name] >= selected_range[0])
                            & (filtered_df[column_name] <= selected_range[1])
                        ]

    # Apply existing filters using helper or original logic
    # Analyst Count
    if "total_analyst_count" in df.columns and st.sidebar.checkbox(
        "Filter by Analyst Count", key="scanx_filter_analyst_count_cb"
    ):
        analyst_values = df["total_analyst_count"].dropna()
        if not analyst_values.empty:
            count_min, count_max = int(analyst_values.min()), int(analyst_values.max())
            if count_min < count_max:
                selected_count_range = st.sidebar.slider(
                    "Analyst Count Range",
                    count_min,
                    count_max,
                    (count_min, count_max),
                    key="scanx_filter_analyst_count_range",
                )
                filtered_df = filtered_df[
                    filtered_df["total_analyst_count"].between(*selected_count_range)
                ]

    # PE Ratio
    apply_range_filter("pe", "PE Ratio", min_val=0.0, max_val=500.0)

    # PB Ratio
    apply_range_filter("pb", "PB Ratio", min_val=0.0, max_val=50.0)

    # Sector PE
    apply_range_filter("ind__pe", "Sector PE", min_val=0.0, max_val=200.0)

    # Sector PB
    apply_range_filter("ind__pb", "Sector PB", min_val=0.0, max_val=20.0)

    # PE vs Sector PE %
    apply_range_filter("pe_vs_sector_pct", "PE vs Sec %", min_val=-100.0, max_val=500.0)

    # PB vs Sector PB %
    apply_range_filter("pb_vs_sector_pct", "PB vs Sec %", min_val=-100.0, max_val=500.0)

    # Current Ratio
    apply_range_filter("current_rto", "Current Ratio", min_val=0.0, max_val=20.0)

    # Market Cap
    if "mcap" in df.columns and st.sidebar.checkbox(
        "Filter by Market Cap", key="scanx_filter_mcap_cb"
    ):
        mcap_values = df["mcap"].dropna()
        if not mcap_values.empty:
            mcap_min, mcap_max = float(mcap_values.min()), float(mcap_values.max())
            selected_mcap = st.sidebar.slider(
                "Market Cap Range (Cr)",
                mcap_min,
                mcap_max,
                (mcap_min, mcap_max),
                key="scanx_filter_mcap_range",
            )
            filtered_df = filtered_df[filtered_df["mcap"].between(*selected_mcap)]

    apply_multiselect("status", "Status", default_values=["Synced"])

    # --- Filter Actions ---
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Refresh", width="stretch", key="scanx_refresh_data"):
            clear_source_cache(DATA_SOURCE_NAME)
            st.rerun()

    with col2:
        if st.button("✖️ Clear", width="stretch", key="scanx_clear_filters"):
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

    if st.session_state.scanx_current_page > total_pages:
        st.session_state.scanx_current_page = 1

    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button(
            "⏮️",
            disabled=st.session_state.scanx_current_page == 1,
            width="stretch",
            help="First page",
            key="scanx_first_page",
        ):
            st.session_state.scanx_current_page = 1
            st.rerun()

    with col2:
        if st.button(
            "◀️",
            disabled=st.session_state.scanx_current_page == 1,
            width="stretch",
            help="Previous page",
            key="scanx_prev_page",
        ):
            st.session_state.scanx_current_page -= 1
            st.rerun()

    with col3:
        st.markdown(
            f"<div style='text-align:center; padding:8px;'>"
            f"Page <b>{st.session_state.scanx_current_page}</b> of <b>{total_pages}</b>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col4:
        if st.button(
            "▶️",
            disabled=st.session_state.scanx_current_page == total_pages,
            width="stretch",
            help="Next page",
            key="scanx_next_page",
        ):
            st.session_state.scanx_current_page += 1
            st.rerun()

    with col5:
        if st.button(
            "⏭️",
            disabled=st.session_state.scanx_current_page == total_pages,
            width="stretch",
            help="Last page",
            key="scanx_last_page",
        ):
            st.session_state.scanx_current_page = total_pages
            st.rerun()

    start_idx = (st.session_state.scanx_current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)

    return start_idx, end_idx


# ============================================
# Table View
# ============================================
def render_table_view(df: pd.DataFrame):
    """Render data table with configurable columns."""
    visible_cols = st.session_state.scanx_visible_columns

    # Filter to only existing columns
    existing_cols = [col for col in visible_cols if col in df.columns]

    if not existing_cols:
        st.warning("No columns selected. Please select at least one column.")
        return

    # Always include sid for navigation
    if "sid" not in existing_cols and "sid" in df.columns:
        display_cols = existing_cols + ["sid"]
    else:
        display_cols = existing_cols

    display_df = df[display_cols].copy()
    column_config = _get_column_config(existing_cols)

    # Add action column with detail button
    column_config["_action"] = st.column_config.LinkColumn(
        "Details", help="View company details", display_text="🔍 View"
    )

    # Add action links
    if "sid" in display_df.columns:
        display_df["_action"] = display_df["sid"].apply(
            lambda x: f"/ScanX_Company_Details?sid={x}" if pd.notna(x) else ""
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
        st.info("🗭 No companies match your filters.")
        return

    # Sort controls
    sort_column_map = {
        "Company Name": "disp_sym",
        "LTP": "ltp",
        "PE": "pe",
        "P/B": "pb",
        "Market Cap": "mcap",
        "Change %": "pchange",
        "Analyst Rating": "analyst_final_rating",
        "Analyst Count": "total_analyst_count",
        "Sector": "sector",
        "Sub-Sector": "sub_sector",
    }

    sort_col1, sort_col2 = st.columns([2, 0.8])

    with sort_col1:
        sort_column_display = st.selectbox(
            "Sort by",
            list(sort_column_map.keys()),
            index=0,
            label_visibility="collapsed",
            key="scanx_card_sort_column",
        )

    with sort_col2:
        sort_direction = st.selectbox(
            "Order",
            ["↑ Asc", "↓ Desc"],
            index=0,
            label_visibility="collapsed",
            key="scanx_card_sort_direction",
        )

    # Apply sorting
    sort_col = sort_column_map.get(sort_column_display, "disp_sym")
    ascending = "↑" in sort_direction
    if sort_col in df.columns:
        df = df.sort_values(by=sort_col, ascending=ascending, na_position="last")

    # Pagination
    start_idx, end_idx = render_pagination(len(df), ITEMS_PER_PAGE)
    st.caption(f"Showing {start_idx + 1}-{end_idx} of {len(df)} companies")

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
                _render_company_card(row_data)


def _render_company_card(row: pd.Series):
    """Render a single company card."""
    with st.container(border=True):
        # Header
        c1, c2 = st.columns([0.7, 0.3])
        c1.markdown(
            f"<h4 style='margin:0; padding:0;'>{row.get('disp_sym', 'Unknown')}</h4>",
            unsafe_allow_html=True,
        )

        status = row.get("status", "Unknown")
        status_color = "🟢" if status == "Synced" else "🟡"
        c2.markdown(
            f"<div style='text-align:right; padding:0; margin:0;'>{status_color}{status}</div>",
            unsafe_allow_html=True,
        )

        # Symbol
        sym = row.get("sym", "")
        if sym:
            st.markdown(
                f"<p style='margin:0; font-size:0.7rem; color:#6b7280;'>📌 {sym}</p>",
                unsafe_allow_html=True,
            )

        # Metadata
        sector = row.get("sector", "N/A") or "N/A"
        sub_sector = row.get("sub_sector", "N/A") or "N/A"
        st.markdown(
            f"<p style='margin:2px 0; font-size:0.8rem;'>📁 {sector} • {sub_sector}</p>",
            unsafe_allow_html=True,
        )

        # Price
        ltp = row.get("ltp")
        pchange = row.get("pchange")

        if ltp and str(ltp) not in ["-", "None", "nan"]:
            # Determine price color based on change
            if pchange is not None and not pd.isna(pchange):
                price_color = "#ef4444" if float(pchange) < 0 else "#22c55e"
            else:
                price_color = "#22c55e"

            st.markdown(
                f"<h3 style='color:{price_color}; margin:4px 0;'>₹{ltp}</h3>",
                unsafe_allow_html=True,
            )

            if pchange is not None and not pd.isna(pchange):
                change_val = float(pchange)
                change_icon = "📉" if change_val < 0 else "📈"
                st.markdown(
                    f"<p style='margin:0; font-size:0.75rem;'>{change_icon} {change_val:.2f}%</p>",
                    unsafe_allow_html=True,
                )

            # Market Cap
            mcap = row.get("mcap")
            if mcap and not pd.isna(mcap):
                st.markdown(
                    f"<p style='margin:4px 0; font-size:0.75rem;'>💰 MCap: {_format_mcap(mcap)}</p>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                "<h4 style='color:#6b7280; margin:4px 0;'>--</h4>",
                unsafe_allow_html=True,
            )

        st.divider()

        # Metrics - compact display with PE highlighting
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(
                f"<div style='text-align:center;'><p style='margin:0; font-size:0.75rem; color:#9ca3af;'>PE</p><p style='margin:2px 0; font-size:1rem; font-weight:600;'>{_format_metric(row.get('pe'))}</p></div>",
                unsafe_allow_html=True,
            )
        with m2:
            st.markdown(
                f"<div style='text-align:center;'><p style='margin:0; font-size:0.75rem; color:#9ca3af;'>P/B</p><p style='margin:2px 0; font-size:1rem; font-weight:600;'>{_format_metric(row.get('pb'))}</p></div>",
                unsafe_allow_html=True,
            )
        with m3:
            st.markdown(
                f"<div style='text-align:center;'><p style='margin:0; font-size:0.75rem; color:#9ca3af;'>Analyst</p><p style='margin:2px 0; font-size:1rem; font-weight:600;'>{row.get('analyst_final_rating', '-') or '-'}</p></div>",
                unsafe_allow_html=True,
            )

        st.divider()

        # Extra Metrics Grid
        e1, e2, e3 = st.columns(3)
        with e1:
            pe_sec_ratio = row.get("pe_sec_pe_ratio")
            val_str = _format_metric(pe_sec_ratio)
            color = "#f59e0b"  # Amber
            if pe_sec_ratio is not None and not pd.isna(pe_sec_ratio):
                if float(pe_sec_ratio) < 1.0:
                    color = "#22c55e"  # Green
                elif float(pe_sec_ratio) > 1.2:
                    color = "#ef4444"  # Red

            st.markdown(
                f"<div style='text-align:center;'><p style='margin:0; font-size:0.7rem; color:#9ca3af;'>PE / Sec PE</p><p style='margin:2px 0; font-size:0.9rem; font-weight:600; color:{color};'>{val_str}</p></div>",
                unsafe_allow_html=True,
            )
        with e2:
            curr_rto = row.get("current_rto")
            val_str = _format_metric(curr_rto)
            color = "#f59e0b"  # Amber
            if curr_rto is not None and not pd.isna(curr_rto):
                if float(curr_rto) > 1.5:
                    color = "#22c55e"  # Green
                elif float(curr_rto) < 1.0:
                    color = "#ef4444"  # Red

            st.markdown(
                f"<div style='text-align:center;'><p style='margin:0; font-size:0.7rem; color:#9ca3af;'>Curr Ratio</p><p style='margin:2px 0; font-size:0.9rem; font-weight:600; color:{color};'>{val_str}</p></div>",
                unsafe_allow_html=True,
            )
        with e3:
            sector_pe = row.get("ind__pe")
            st.markdown(
                f"<div style='text-align:center;'><p style='margin:0; font-size:0.7rem; color:#9ca3af;'>Sec PE</p><p style='margin:2px 0; font-size:0.9rem; font-weight:600;'>{_format_metric(sector_pe)}</p></div>",
                unsafe_allow_html=True,
            )

        st.divider()

        # Actions
        btn1, btn2 = st.columns(2, gap="small")
        with btn1:
            sid = str(row.get("sid", ""))
            if sid and sid not in ["nan", "None", ""]:
                detail_url = f"/ScanX_Company_Details?sid={sid}"
                st.link_button("📊 Details", detail_url, width="stretch")
        with btn2:
            if row.get("url"):
                st.link_button("🔗 ScanX", row.get("url"), width="stretch")


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
    st.markdown("# 📊 ScanX Trade Market Overview")

    # Load data
    source = DataSourceRegistry.get(DATA_SOURCE_NAME)
    if not source:
        st.error("❌ Data source not configured. Please check your settings.")
        return

    with st.spinner("Loading data..."):
        df = load_cached_data(DATA_SOURCE_NAME, source)

    if df.empty:
        st.warning("📭 No data available. Please check the data source.")
        return

    # --- Calculate New Columns ---
    # PE vs Sector PE %
    if "pe" in df.columns and "ind__pe" in df.columns:
        df["pe_vs_sector_pct"] = df.apply(
            lambda x: (
                ((x["pe"] - x["ind__pe"]) / x["ind__pe"] * 100)
                if pd.notna(x["pe"]) and pd.notna(x["ind__pe"]) and x["ind__pe"] != 0
                else None
            ),
            axis=1,
        )

    # PB vs Sector PB %
    if "pb" in df.columns and "ind__pb" in df.columns:
        df["pb_vs_sector_pct"] = df.apply(
            lambda x: (
                ((x["pb"] - x["ind__pb"]) / x["ind__pb"] * 100)
                if pd.notna(x["pb"]) and pd.notna(x["ind__pb"]) and x["ind__pb"] != 0
                else None
            ),
            axis=1,
        )

    # Debug: Show available vs expected columns
    expected_cols = [col_key for _, col_key, _, _ in COLUMN_DEFINITIONS]
    available_cols = df.columns.tolist()
    missing_cols = [col for col in expected_cols if col not in available_cols]

    if missing_cols:
        st.warning(f"⚠️ Missing columns in data: {', '.join(missing_cols)}")
        with st.expander("🔍 Debug: Available columns"):
            st.write(available_cols)

    # Sidebar filters
    filtered_df, total_count, filtered_count = render_filters(df)

    # Show company count in main area
    if filtered_count == total_count:
        st.info(f"📋 Showing all **{total_count:,}** companies")
    else:
        st.success(
            f"🎯 Showing **{filtered_count:,}** of **{total_count:,}** companies"
        )

    st.markdown("---")

    # View controls
    col1, col2 = st.columns([2, 1])

    with col1:
        view_mode = st.radio(
            "View",
            ["📋 Table", "🃏 Cards"],
            horizontal=True,
            label_visibility="collapsed",
            key="scanx_view_mode",
        )

    with col2:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            "📥 Export CSV",
            data=csv,
            file_name=f"scanx_stocks_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            width="stretch",
            key="scanx_export_csv",
        )

    st.markdown("---")

    # Render view
    if "Table" in view_mode:
        render_table_view(filtered_df)
    else:
        render_card_view(filtered_df)


if __name__ == "__main__":
    main()
