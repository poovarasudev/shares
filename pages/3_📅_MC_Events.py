"""
Events Dashboard Page.

Displays upcoming corporate events (Splits, Dividends, Bonus) with filtering,
sorting, and export functionality.
"""

import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
from typing import List, Tuple

from data_sources import DataSourceRegistry, ensure_data_source
from data_sources.registry import load_cached_data, clear_source_cache

# ============================================
# Page Configuration
# ============================================
st.set_page_config(
    page_title="Money Control Corporate Events", page_icon="📅", layout="wide"
)

# ============================================
# Constants
# ============================================
ITEMS_PER_PAGE = 20
CARDS_PER_ROW = 3

# Event type color mapping
EVENT_COLORS = {
    "Splits": "#FFB3B3",  # soft pink
    "Dividend": "#9FE6D8",  # soft teal
    "Bonus": "#CDEEDC",  # soft green
}

EVENT_ICONS = {
    "Splits": "🔄",
    "Dividend": "💰",
    "Bonus": "🎁",
}


# ============================================
# Helper Functions
# ============================================
def _to_snake(s: str) -> str:
    """Convert string to snake_case."""
    s = str(s).strip()
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", s)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower().replace(" ", "_")
    return s2.replace("__", "_")


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object."""
    if pd.isna(date_str) or not date_str:
        return None
    try:
        # Try DD/MM/YYYY format
        return datetime.strptime(str(date_str).strip(), "%d/%m/%Y")
    except:
        try:
            # Try other formats
            return pd.to_datetime(date_str)
        except:
            return None


def format_date(date_str: str, format_str: str = "%d %b %Y") -> str:
    """Format date string for display."""
    dt = parse_date(date_str)
    if dt:
        return dt.strftime(format_str)
    return str(date_str) if date_str else "-"


def get_days_until(date_str: str) -> int:
    """Get number of days until the event date."""
    dt = parse_date(date_str)
    if dt:
        delta = dt - datetime.now()
        return delta.days
    return None


def get_event_status(days_until: int) -> Tuple[str, str]:
    """Get event status and color based on days until event."""
    # Return (label, hex_color) with softer palette
    if days_until is None:
        return "Unknown", "#6b7280"
    elif days_until < 0:
        return "Past", "#6b7280"
    elif days_until == 0:
        return "Today", "#f87171"
    elif days_until <= 7:
        return f"In {days_until} days", "#f7b267"
    elif days_until <= 30:
        return f"In {days_until} days", "#60a5fa"
    else:
        return f"In {days_until} days", "#34d399"


def extract_price_value(price_str: str) -> str:
    """Extract numeric price from string like '344.05 (-0.79%)'."""
    if pd.isna(price_str) or not price_str:
        return "-"
    # Extract the first number before any parentheses
    match = re.match(r"([0-9,.]+)", str(price_str).strip())
    if match:
        return f"₹{match.group(1)}"
    return str(price_str)


def extract_price_change(price_str: str) -> Tuple[str, str]:
    """Extract price change and determine color."""
    if pd.isna(price_str) or not price_str:
        return "", "gray"
    # Look for percentage in parentheses
    match = re.search(r"\(([+-]?[0-9.]+%)\)", str(price_str))
    if match:
        pct = match.group(1)
        if pct.startswith("-"):
            return pct, "red"
        elif pct.startswith("+"):
            return pct, "green"
        else:
            return pct, "green" if float(pct.replace("%", "")) > 0 else "red"
    return "", "gray"


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply filters to dataframe."""
    filtered_df = df.copy()

    # Event Type filter
    if filters.get("event_types"):
        filtered_df = filtered_df[
            filtered_df["event_type"].isin(filters["event_types"])
        ]

    # Notification Status filter
    if filters.get("notification_status"):
        filtered_df = filtered_df[
            filtered_df["notification_status"].isin(filters["notification_status"])
        ]

    # Date range filter
    if filters.get("date_range"):
        days = filters["date_range"]
        if days != "All":
            today = datetime.now()
            if days == "Past":
                filtered_df = filtered_df[filtered_df["_days_until"] < 0]
            elif days == "Today":
                filtered_df = filtered_df[filtered_df["_days_until"] == 0]
            elif days == "This Week":
                filtered_df = filtered_df[
                    (filtered_df["_days_until"] >= 0)
                    & (filtered_df["_days_until"] <= 7)
                ]
            elif days == "This Month":
                filtered_df = filtered_df[
                    (filtered_df["_days_until"] >= 0)
                    & (filtered_df["_days_until"] <= 30)
                ]
            elif days == "Next 3 Months":
                filtered_df = filtered_df[
                    (filtered_df["_days_until"] >= 0)
                    & (filtered_df["_days_until"] <= 90)
                ]

    # Search filter
    if filters.get("search"):
        search_term = filters["search"].lower()
        filtered_df = filtered_df[
            filtered_df["stock_name"].str.lower().str.contains(search_term, na=False)
            | filtered_df["sc_id"].str.lower().str.contains(search_term, na=False)
        ]

    return filtered_df


def render_event_card(event: pd.Series, col):
    """Render a single event card."""
    with col:
        event_type = event.get("event_type", "Unknown")
        color = EVENT_COLORS.get(event_type, "#CCCCCC")
        icon = EVENT_ICONS.get(event_type, "📋")

        # Calculate days until
        days_until = event.get("_days_until")
        status_text, status_color = get_event_status(days_until)

        # Price info
        price_value = extract_price_value(event.get("last_trade_price", "-"))
        price_change, change_color = extract_price_change(
            event.get("last_trade_price", "-")
        )

        with st.container():
            # Event type badge
            st.markdown(
                f"""
                <div style="background-color: {color}; padding: 8px; border-radius: 8px 8px 0 0; text-align: center;">
                    <h3 style="margin: 0; color: white;">{icon} {event_type}</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Card content
            with st.container():
                st.markdown(
                    f"### [{event.get('stock_name', 'N/A')}]({event.get('url', '#')})"
                )

                # Status badge
                st.markdown(
                    f"<span style='background-color: {status_color}; color: white; padding: 4px 12px; "
                    f"border-radius: 12px; font-size: 14px;'>{status_text}</span>",
                    unsafe_allow_html=True,
                )

                st.markdown("---")

                # Event details in columns
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Ex-Date**")
                    st.markdown(format_date(event.get("ex_date", "-")))

                    st.markdown("**Details**")
                    st.markdown(event.get("details", "-"))

                with col2:
                    st.markdown("**Announced**")
                    st.markdown(format_date(event.get("announcement_date", "-")))

                    st.markdown("**Price**")
                    if price_change:
                        st.markdown(
                            f"{price_value} <span style='color: {change_color};'>{price_change}</span>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(price_value)

                # Description
                if event.get("description"):
                    st.markdown("---")
                    st.caption(event.get("description"))

            st.markdown("<br>", unsafe_allow_html=True)


def render_table_view(df: pd.DataFrame):
    """Render events in table format."""
    # Prepare display dataframe
    display_df = df.copy()

    # Format dates
    display_df["ex_date"] = display_df["ex_date"].apply(lambda x: format_date(x))
    display_df["announcement_date"] = display_df["announcement_date"].apply(
        lambda x: format_date(x)
    )

    # Format price
    display_df["last_trade_price"] = display_df["last_trade_price"].apply(
        lambda x: extract_price_value(x)
    )

    # Select and rename columns for display
    display_cols = {
        "stock_name": "Stock",
        "event_type": "Event",
        "ex_date": "Ex-Date",
        "announcement_date": "Announced",
        "details": "Details",
        "last_trade_price": "LSP",
        "description": "Description",
        "sc_id": "SC ID",
        "url": "Action",
    }

    display_df = display_df[
        [col for col in display_cols.keys() if col in display_df.columns]
    ]
    display_df = display_df.rename(columns=display_cols)

    # Configure column display
    column_config = {
        "Stock": st.column_config.TextColumn("Stock", width="medium"),
        "Event": st.column_config.TextColumn("Event", width="small"),
        "Ex-Date": st.column_config.TextColumn("Ex-Date", width="small"),
        "Announced": st.column_config.TextColumn("Announced", width="small"),
        "Details": st.column_config.TextColumn("Details", width="medium"),
        "Description": st.column_config.TextColumn("Description", width="large"),
        "Price": st.column_config.TextColumn("Price", width="small"),
        "SC ID": st.column_config.TextColumn("SC ID", width="small"),
        "Action": st.column_config.LinkColumn(
            "Action", display_text="View 🔗", width="small"
        ),
    }

    st.dataframe(
        display_df,
        column_config=column_config,
        width="stretch",
        hide_index=True,
    )


# ============================================
# Main Page Logic
# ============================================
def main():
    """Main page logic."""

    # Ensure data source is initialized
    ensure_data_source("money_control_events")

    # Page header
    st.markdown("# 📅 Money Control Corporate Events")
    st.markdown("Track upcoming stock splits, dividends, and bonus issues")

    # Load data
    source = DataSourceRegistry.get("money_control_events")
    if not source:
        st.error("❌ Events data source not available")
        return

    with st.spinner("Loading events data..."):
        df = load_cached_data("money_control_events", source)

    if df is None or df.empty:
        st.warning("⚠️ No events data available")
        return

    # Add derived columns
    df["_days_until"] = df["ex_date"].apply(get_days_until)

    # Sidebar filters
    with st.sidebar:
        st.markdown("## 🔍 Filters")

        # Search box
        search_term = st.text_input(
            "🔎 Search Stock",
            placeholder="Enter stock name or SC ID...",
            key="search_events",
        )

        # Event type filter
        event_types = st.multiselect(
            "Event Type",
            options=sorted(df["event_type"].unique()),
            default=None,
            key="event_type_filter",
        )

        # Date range filter
        date_range = st.selectbox(
            "Date Range",
            options=[
                "All",
                "Past",
                "Today",
                "This Week",
                "This Month",
                "Next 3 Months",
            ],
            index=3,  # Default to "This Month"
            key="date_range_filter",
        )

        # Notification status filter
        notification_status = st.multiselect(
            "Notification Status",
            options=sorted(df["notification_status"].unique()),
            default=None,
            key="notification_filter",
        )

        # Reset filters
        if st.button("🔄 Reset Filters", key="reset_filters"):
            st.session_state.search_events = ""
            st.session_state.event_type_filter = []
            st.session_state.date_range_filter = "This Month"
            st.session_state.notification_filter = []
            st.rerun()

        st.markdown("---")

        # Refresh data
        if st.button("🔄 Refresh Data", key="refresh_events"):
            clear_source_cache("money_control_events")
            st.rerun()

    # Apply filters
    filters = {
        "search": search_term,
        "event_types": event_types,
        "date_range": date_range,
        "notification_status": notification_status,
    }

    filtered_df = apply_filters(df, filters)

    # Sort by ex-date (ascending - upcoming first)
    filtered_df = filtered_df.sort_values("_days_until", ascending=True)

    # Display results count and view toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 📊 {len(filtered_df)} Events Found")
    with col2:
        view_mode = st.radio(
            "View Mode",
            options=["Table", "Cards"],
            horizontal=True,
            key="view_mode",
            label_visibility="collapsed",
        )

    st.markdown("---")

    # Display events
    if filtered_df.empty:
        st.info("ℹ️ No events match the current filters")
        return

    if view_mode == "Cards":
        # Pagination for cards
        total_pages = (len(filtered_df) - 1) // ITEMS_PER_PAGE + 1

        if "events_current_page" not in st.session_state:
            st.session_state.events_current_page = 1

        # Pagination controls
        if total_pages > 1:
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

            with col1:
                if st.button(
                    "⏮️ First", disabled=(st.session_state.events_current_page == 1)
                ):
                    st.session_state.events_current_page = 1
                    st.rerun()

            with col2:
                if st.button(
                    "◀️ Prev", disabled=(st.session_state.events_current_page == 1)
                ):
                    st.session_state.events_current_page -= 1
                    st.rerun()

            with col3:
                st.markdown(
                    f"<div style='text-align: center; padding-top: 5px;'>"
                    f"Page {st.session_state.events_current_page} of {total_pages}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with col4:
                if st.button(
                    "Next ▶️",
                    disabled=(st.session_state.events_current_page == total_pages),
                ):
                    st.session_state.events_current_page += 1
                    st.rerun()

            with col5:
                if st.button(
                    "Last ⏭️",
                    disabled=(st.session_state.events_current_page == total_pages),
                ):
                    st.session_state.events_current_page = total_pages
                    st.rerun()

        # Calculate page slice
        start_idx = (st.session_state.events_current_page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_df = filtered_df.iloc[start_idx:end_idx]

        # Render cards in rows
        for i in range(0, len(page_df), CARDS_PER_ROW):
            cols = st.columns(CARDS_PER_ROW)
            for j in range(CARDS_PER_ROW):
                idx = i + j
                if idx < len(page_df):
                    event = page_df.iloc[idx]
                    render_event_card(event, cols[j])

    else:
        # Table view - show all results
        render_table_view(filtered_df)


# ============================================
# Entry Point
# ============================================
if __name__ == "__main__":
    main()
