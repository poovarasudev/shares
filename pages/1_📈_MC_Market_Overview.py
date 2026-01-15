"""
Market Overview Page.

Displays a comprehensive list of stocks with filtering, sorting,
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
    page_title="Money Control Market Overview", page_icon="📈", layout="wide"
)

# ============================================
# Constants
# ============================================
ITEMS_PER_PAGE = 15
CARDS_PER_ROW = 3

# Column definitions: (display_name, column_key, is_visible_by_default, width)
COLUMN_DEFINITIONS = [
    ("Company Name", "company_name", True, "medium"),
    ("SC ID", "scId", False, "small"),
    ("Sector", "sector", True, "medium"),
    ("Industry", "industry", True, "medium"),
    ("Status", "status", False, "small"),
    ("Cost (₹)", "cost", True, "small"),
    ("M-Score", "m_score", True, "small"),
    ("TTM EPS", "ttm_eps", False, "small"),
    ("TTM PE", "ttm_pe", True, "small"),
    ("P/B", "p_b", False, "small"),
    ("Sector PE", "sector_pe", False, "small"),
    ("Analyst Rating", "analyst_final_rating", True, "small"),
    ("Analyst Count", "analyst_count", False, "small"),
    ("Price Change", "price_up_down_value", False, "small"),
    ("PE vs Sector %", "pe_vs_sector_pct", False, "small"),
    ("Analyst Confidence", "analyst_confidence", False, "small"),
    ("MC Url", "company_url", True, "small"),
]


# ============================================
# Helper Functions
# ============================================
def _to_snake(s: str) -> str:
    """Convert string to snake_case."""
    s = str(s).strip()
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", s)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower().replace(" ", "_")
    return s2.replace("__", "_")


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


def _format_pe_with_highlight(ttm_pe, sector_pe, pe_vs_sector_pct) -> Tuple[str, str]:
    """
    Format PE value with color highlighting based on comparison with sector PE.

    Returns:
        Tuple of (formatted_value, css_color)
        - Green: PE significantly below sector (undervalued)
        - Red: PE significantly above sector (overvalued)
        - Default: PE within normal range
    """
    if ttm_pe is None or pd.isna(ttm_pe):
        return "-", "#9ca3af"  # gray for missing

    formatted = f"{float(ttm_pe):.2f}"

    # Check pe_vs_sector_pct for highlighting
    if pe_vs_sector_pct is not None and not pd.isna(pe_vs_sector_pct):
        pct = float(pe_vs_sector_pct)
        if pct <= -20:  # 20% cheaper than sector
            return formatted, "#22c55e"  # green - undervalued
        elif pct >= 20:  # 20% more expensive than sector
            return formatted, "#ef4444"  # red - overvalued

    return formatted, "#f59e0b"  # amber - neutral/fair


def _init_session_state():
    """Initialize session state variables."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1

    if "visible_columns" not in st.session_state:
        # Show all columns by default
        st.session_state.visible_columns = [
            col_key for _, col_key, _, _ in COLUMN_DEFINITIONS
        ]


def _get_column_config(visible_columns: List[str]) -> Dict:
    """Generate column configuration for dataframe display."""
    config = {}

    for display_name, col_key, _, _ in COLUMN_DEFINITIONS:
        if col_key not in visible_columns:
            continue

        if col_key == "company_url":
            config[col_key] = st.column_config.LinkColumn(
                display_name, help="Click to open in MoneyControl", display_text="View"
            )
        elif col_key == "cost":
            config[col_key] = st.column_config.NumberColumn(
                display_name, format="₹%.2f"
            )
        elif col_key in ["m_score", "ttm_eps", "ttm_pe", "p_b", "sector_pe"]:
            config[col_key] = st.column_config.NumberColumn(display_name, format="%.2f")
        elif col_key == "pe_vs_sector_pct":
            config[col_key] = st.column_config.NumberColumn(
                display_name, format="%.2f%%"
            )
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
            "Search Company", placeholder="e.g. Reliance, TCS...", key="search_input"
        )
        .strip()
        .lower()
    )

    if search_query:
        mask_name = (
            filtered_df["company_name"]
            .astype(str)
            .str.lower()
            .str.contains(search_query, na=False)
        )
        mask_scid = (
            filtered_df["scId"]
            .astype(str)
            .str.lower()
            .str.contains(search_query, na=False)
        )
        filtered_df = filtered_df[mask_name | mask_scid]

    # --- Category Filters ---
    def apply_multiselect(column_name: str, label: str, default_values: list = None):
        nonlocal filtered_df
        if column_name in df.columns:
            options = sorted(df[column_name].dropna().astype(str).unique().tolist())
            # Set default value for status filter
            default = (
                default_values
                if default_values and all(v in options for v in default_values)
                else []
            )
            selected = st.sidebar.multiselect(
                label, options, default=default, key=f"filter_{column_name}"
            )
            if selected:
                filtered_df = filtered_df[filtered_df[column_name].isin(selected)]

    apply_multiselect("sector", "Sector")
    apply_multiselect("industry", "Industry")
    apply_multiselect("analyst_final_rating", "Analyst Rating")

    # Analyst Count range filter
    if "analyst_count" in df.columns and st.sidebar.checkbox(
        "Filter by Analyst Count", key="filter_analyst_count_cb"
    ):
        analyst_values = df["analyst_count"].dropna()
        if len(analyst_values) > 0:
            count_min = int(analyst_values.min())
            count_max = int(analyst_values.max())
            if count_min < count_max:
                selected_count_range = st.sidebar.slider(
                    "Analyst Count Range",
                    min_value=count_min,
                    max_value=count_max,
                    value=(count_min, count_max),
                    key="filter_analyst_count_range",
                )
                filtered_df = filtered_df[
                    (filtered_df["analyst_count"] >= selected_count_range[0])
                    & (filtered_df["analyst_count"] <= selected_count_range[1])
                ]

    # M-Score filter
    if "m_score" in df.columns and st.sidebar.checkbox(
        "Filter by M-Score", key="filter_mscore_cb"
    ):
        m_min, m_max = st.sidebar.slider(
            "M-Score Range",
            min_value=0.0,
            max_value=100.0,
            value=(0.0, 100.0),
            key="filter_mscore",
        )
        filtered_df = filtered_df[
            (filtered_df["m_score"] >= m_min) & (filtered_df["m_score"] <= m_max)
        ]

    # PE filter
    if "ttm_pe" in df.columns and st.sidebar.checkbox(
        "Filter by PE Ratio", key="filter_pe_cb"
    ):
        pe_min, pe_max = st.sidebar.slider(
            "PE Range",
            min_value=0.0,
            max_value=500.0,
            value=(0.0, 200.0),
            key="filter_pe",
        )
        filtered_df = filtered_df[
            (filtered_df["ttm_pe"] >= pe_min) & (filtered_df["ttm_pe"] <= pe_max)
        ]

    apply_multiselect("status", "Status", default_values=["Synced"])

    # --- Filter Actions ---

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Refresh", width="stretch", key="refresh_data"):
            clear_source_cache("money_control")
            st.rerun()

    with col2:
        # Hard reload the page to clear all filters
        if st.button("✖️ Clear", width="stretch", key="clear_filters"):
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

    if st.session_state.current_page > total_pages:
        st.session_state.current_page = 1

    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button(
            "⏮️",
            disabled=st.session_state.current_page == 1,
            width="stretch",
            help="First page",
        ):
            st.session_state.current_page = 1
            st.rerun()

    with col2:
        if st.button(
            "◀️",
            disabled=st.session_state.current_page == 1,
            width="stretch",
            help="Previous page",
        ):
            st.session_state.current_page -= 1
            st.rerun()

    with col3:
        st.markdown(
            f"<div style='text-align:center; padding:8px;'>"
            f"Page <b>{st.session_state.current_page}</b> of <b>{total_pages}</b>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col4:
        if st.button(
            "▶️",
            disabled=st.session_state.current_page == total_pages,
            width="stretch",
            help="Next page",
        ):
            st.session_state.current_page += 1
            st.rerun()

    with col5:
        if st.button(
            "⏭️",
            disabled=st.session_state.current_page == total_pages,
            width="stretch",
            help="Last page",
        ):
            st.session_state.current_page = total_pages
            st.rerun()

    start_idx = (st.session_state.current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)

    return start_idx, end_idx


# ============================================
# Table View
# ============================================
def render_table_view(df: pd.DataFrame):
    """Render data table with configurable columns."""
    visible_cols = st.session_state.visible_columns

    # Filter to only existing columns
    existing_cols = [col for col in visible_cols if col in df.columns]

    if not existing_cols:
        st.warning("No columns selected. Please select at least one column.")
        return

    # Always include scId for navigation
    if "scId" not in existing_cols and "scId" in df.columns:
        display_cols = existing_cols + ["scId"]
    else:
        display_cols = existing_cols

    display_df = df[display_cols].copy()
    column_config = _get_column_config(existing_cols)

    # Add action column with detail button
    column_config["_action"] = st.column_config.LinkColumn(
        "Details", help="View company details", display_text="🔍 View"
    )

    # Add action links
    if "scId" in display_df.columns:
        display_df["_action"] = display_df["scId"].apply(
            lambda x: f"/Money_Control_Company_Details?sc_id={x}" if pd.notna(x) else ""
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

    # Sort controls (only in card view)
    sort_column_map = {
        "Company Name": "company_name",
        "M-Score": "m_score",
        "Cost": "cost",
        "PE vs Sector %": "pe_vs_sector_pct",
        "TTM PE": "ttm_pe",
        "TTM EPS": "ttm_eps",
        "P/B": "p_b",
        "Analyst Confidence": "analyst_confidence_score",
        "Analyst Rating": "analyst_final_rating",
        "Analyst Count": "analyst_count",
        "Sector PE": "sector_pe",
        "Price Change": "price_up_down_value",
        "Sector": "sector",
        "Industry": "industry",
    }

    sort_col1, sort_col2 = st.columns([2, 0.8])

    with sort_col1:
        sort_column_display = st.selectbox(
            "Sort by",
            list(sort_column_map.keys()),
            index=0,
            label_visibility="collapsed",
            key="card_sort_column",
        )

    with sort_col2:
        sort_direction = st.selectbox(
            "Order",
            ["↑ Asc", "↓ Desc"],
            index=0,
            label_visibility="collapsed",
            key="card_sort_direction",
        )

    # Apply sorting
    sort_col = sort_column_map.get(sort_column_display, "company_name")
    ascending = "↑" in sort_direction  # Check for up arrow
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
        for col_idx, (row_data, global_idx) in enumerate(row_items):
            with cols[col_idx]:
                _render_company_card(row_data, global_idx)


def _render_company_card(row: pd.Series, index: int):
    """Render a single company card."""
    with st.container(border=True):
        # Header
        c1, c2 = st.columns([0.7, 0.3])
        c1.markdown(
            f"<h4 style='margin:0; padding:0;'>{row.get('company_name', 'Unknown')}</h4>",
            unsafe_allow_html=True,
        )

        status = row.get("status", "Unknown")
        status_color = "🟢" if status == "Synced" else "🟡"
        c2.markdown(
            f"<div style='text-align:right; padding:0; margin:0;'>{status_color}{status}</div>",
            unsafe_allow_html=True,
        )

        # Metadata
        sector = row.get("sector", "N/A") or "N/A"
        industry = row.get("industry", "N/A") or "N/A"
        st.markdown(
            f"<p style='margin:2px 0; font-size:0.8rem;'>📁 {sector} • {industry}</p>",
            unsafe_allow_html=True,
        )

        # Price
        cost = row.get("cost")
        price_change_key = row.get("price_up_down_key", "")
        price_change_value = row.get("price_up_down_value", "")

        if cost and str(cost) not in ["-", "None", "nan"]:
            price_color = "#ef4444" if price_change_key == "Red" else "#22c55e"
            st.markdown(
                f"<h3 style='color:{price_color}; margin:4px 0;'>₹{cost}</h3>",
                unsafe_allow_html=True,
            )
            if price_change_value:
                change_icon = "📉" if price_change_key == "Red" else "📈"
                st.markdown(
                    f"<p style='margin:0; font-size:0.75rem;'>{change_icon} {price_change_value}</p>",
                    unsafe_allow_html=True,
                )
            # PE vs Sector and Analyst confidence with highlighting
            pe_pct = row.get("pe_vs_sector_pct")
            analyst_conf = row.get("analyst_confidence")

            pe_line = None
            if pe_pct is not None and not pd.isna(pe_pct):
                pct_val = float(pe_pct)
                if pct_val <= -20:
                    pe_color = "#22c55e"  # green - cheap
                    pe_icon = "🟢"
                elif pct_val >= 20:
                    pe_color = "#ef4444"  # red - expensive
                    pe_icon = "🔴"
                else:
                    pe_color = "#f59e0b"  # amber - fair
                    pe_icon = "🟡"
                pe_line = f"<span style='color:{pe_color};'>{pe_icon} PE vs Sector: {pct_val:.1f}%</span>"

            conf_line = f"Analyst: {analyst_conf}" if analyst_conf else None
            if pe_line or conf_line:
                parts = [x for x in [pe_line, conf_line] if x]
                extras = " • ".join(parts)
                st.markdown(
                    f"<p style='margin:4px 0; font-size:0.75rem;'>{extras}</p>",
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
                f"<div style='text-align:center;'><p style='margin:0; font-size:0.75rem; color:#9ca3af;'>M-Score</p><p style='margin:2px 0; font-size:1rem; font-weight:600;'>{_format_metric(row.get('m_score'))}</p></div>",
                unsafe_allow_html=True,
            )
        with m2:
            # Highlight TTM PE based on comparison with sector
            pe_val, pe_color = _format_pe_with_highlight(
                row.get("ttm_pe"), row.get("sector_pe"), row.get("pe_vs_sector_pct")
            )
            st.markdown(
                f"<div style='text-align:center;'><p style='margin:0; font-size:0.75rem; color:#9ca3af;'>TTM PE</p><p style='margin:2px 0; font-size:1rem; font-weight:600; color:{pe_color};'>{pe_val}</p></div>",
                unsafe_allow_html=True,
            )
        with m3:
            st.markdown(
                f"<div style='text-align:center;'><p style='margin:0; font-size:0.75rem; color:#9ca3af;'>Analyst</p><p style='margin:2px 0; font-size:1rem; font-weight:600;'>{row.get('analyst_final_rating', '-') or '-'}</p></div>",
                unsafe_allow_html=True,
            )

        st.divider()

        # Actions
        btn1, btn2 = st.columns(2, gap="small")
        with btn1:
            # Open in new tab using link_button with local page
            sc_id = str(row.get("scId", ""))
            if sc_id:
                detail_url = f"/Money_Control_Company_Details?sc_id={sc_id}"
                st.link_button("📊 Details", detail_url, width="stretch")
        with btn2:
            if row.get("company_url"):
                st.link_button("🔗 MC", row.get("company_url"), width="stretch")


# ============================================
# Main
# ============================================
def main():
    _init_session_state()

    # Ensure data source is available (fallback initialization)
    if not ensure_data_source("money_control"):
        st.error("❌ Failed to initialize data source. Please check your settings.")
        return

    # Header
    st.markdown("# 📈 Money Control Market Overview")

    # Load data
    source = DataSourceRegistry.get("money_control")
    if not source:
        st.error("❌ Data source not configured. Please check your settings.")
        return

    with st.spinner("Loading data..."):
        df = load_cached_data("money_control", source)

    if df.empty:
        st.warning("📭 No data available. Please check the data source.")
        return

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
        )

    with col2:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            "📥 Export CSV",
            data=csv,
            file_name=f"stocks_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            width="stretch",
        )

    st.markdown("---")

    # Render view
    if "Table" in view_mode:
        render_table_view(filtered_df)
    else:
        render_card_view(filtered_df)


if __name__ == "__main__":
    main()
