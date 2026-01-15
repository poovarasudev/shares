"""
Company Details Page.

Provides detailed analysis view for a specific company including
financial metrics, analyst ratings, and historical data.
"""

import streamlit as st
import pandas as pd
import json
from typing import Any, Optional

from data_sources.registry import DataSourceRegistry, load_cached_data

# ============================================
# Page Configuration
# ============================================
st.set_page_config(
    page_title="Money Control Company Details", page_icon="🏢", layout="wide"
)


# ============================================
# Helper Functions
# ============================================
def _parse_json_data(data: Any) -> Optional[Any]:
    """Safely parse JSON data."""
    if data is None:
        return None
    if isinstance(data, (dict, list)):
        return data
    if isinstance(data, str):
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return None
    return None


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


def _get_company_id() -> Optional[str]:
    """Get company ID from query params or session state."""
    # Check query params first
    sc_id = st.query_params.get("sc_id")

    if sc_id:
        st.session_state["selected_sc_id"] = sc_id
        return sc_id

    # Fallback to session state
    return st.session_state.get("selected_sc_id")


def _go_back():
    """Navigate back to market overview."""
    if "sc_id" in st.query_params:
        del st.query_params["sc_id"]
    if "selected_sc_id" in st.session_state:
        del st.session_state["selected_sc_id"]
    st.switch_page("pages/1_📈_Money_Control_Market_Overview.py")


# ============================================
# Main Content
# ============================================
def main():
    # Load data first to enable company selection
    source = DataSourceRegistry.get("money_control")
    if not source:
        st.error("❌ Data source not configured.")
        return

    with st.spinner("Loading data..."):
        df = load_cached_data("money_control", source)

    if df.empty:
        st.error("❌ Data could not be loaded.")
        return

    # Get company ID
    sc_id = _get_company_id()

    if not sc_id or sc_id in ["None", "nan", ""]:
        st.info("📋 No company selected. Please select a company to view details.")

        # Create searchable company list
        company_options = df[["company_name", "scId"]].copy()
        company_options["display"] = (
            company_options["company_name"]
            + " ("
            + company_options["scId"].astype(str)
            + ")"
        )
        company_dict = dict(zip(company_options["display"], company_options["scId"]))

        col1, col2 = st.columns([3, 1])
        with col1:
            selected_company = st.selectbox(
                "Search and select a company:",
                options=[""] + list(company_dict.keys()),
                index=0,
                placeholder="Type to search...",
                key="company_search",
            )

        with col2:
            if st.button("← Back to Market Overview", width="stretch"):
                _go_back()

        if selected_company and selected_company != "":
            selected_sc_id = company_dict[selected_company]
            st.session_state["selected_sc_id"] = str(selected_sc_id)
            st.query_params["sc_id"] = str(selected_sc_id)
            st.rerun()

        st.stop()

    if df.empty:
        st.error("❌ Data could not be loaded.")
        return

    # Find company
    company_data = df[df["scId"].astype(str) == str(sc_id)]

    if company_data.empty:
        st.error(f"❌ Company with ID '{sc_id}' not found.")
        if st.button("← Back to Market Overview"):
            _go_back()
        st.stop()

    data = company_data.iloc[0]

    # ==========================================
    # Header Section
    # ==========================================
    col_back, col_header, col_status, col_link = st.columns([0.08, 0.52, 0.2, 0.2])

    with col_back:
        if st.button("←", help="Back to Market Overview"):
            _go_back()

    with col_header:
        st.markdown(f"# {data.get('company_name', 'Unknown Company')}")
        st.caption(
            f"🆔 {data.get('scId')} • 📁 {data.get('sector', 'N/A')} • 🏭 {data.get('industry', 'N/A')}"
        )

    with col_status:
        status = data.get("status", "Unknown")
        status_color = "🟢" if status == "Synced" else "🟡"
        st.markdown(f"### {status_color} {status}")

    with col_link:
        if data.get("company_url"):
            st.link_button("🔗 MoneyControl", data.get("company_url"), width="stretch")

    st.divider()

    # ==========================================
    # Price Section
    # ==========================================
    st.markdown("## 💰 Current Price")

    price_col1, price_col2, price_col3 = st.columns([0.3, 0.4, 0.3])

    cost = data.get("cost")
    price_change_key = data.get("price_up_down_key", "")
    price_change_value = data.get("price_up_down_value", "")
    price_change_date = data.get("price_up_down_date", "")

    with price_col1:
        if cost and str(cost) not in ["-", "None", "nan"]:
            price_color = "#ef4444" if price_change_key == "Red" else "#22c55e"
            st.markdown(
                f"<h1 style='color:{price_color}; margin:0;'>₹{cost}</h1>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<h1 style='color:#6b7280;'>--</h1>", unsafe_allow_html=True)

    with price_col2:
        if price_change_value:
            change_icon = "📉" if price_change_key == "Red" else "📈"
            change_color = "#ef4444" if price_change_key == "Red" else "#22c55e"
            st.markdown(
                f"<h2 style='color:{change_color};'>{change_icon} {price_change_value}</h2>",
                unsafe_allow_html=True,
            )

    with price_col3:
        if price_change_date:
            st.caption(f"🕐 As on {price_change_date}")

    st.divider()

    # ==========================================
    # Key Metrics Section
    # ==========================================
    st.markdown("## 📊 Key Financial Metrics")

    cols = st.columns(6)
    metrics = [
        ("M-Score", _format_metric(data.get("m_score")), "Investment Score"),
        (
            "Cost",
            f"₹{data.get('cost', '-')}" if data.get("cost") else "-",
            "Current Price",
        ),
        ("TTM EPS", _format_metric(data.get("ttm_eps")), "Trailing 12M EPS"),
        ("TTM PE", _format_metric(data.get("ttm_pe")), "Price to Earnings"),
        ("P/B", _format_metric(data.get("p_b")), "Price to Book"),
        ("Sector PE", _format_metric(data.get("sector_pe")), "Sector Average PE"),
    ]

    for col, (label, value, help_text) in zip(cols, metrics):
        col.metric(label=label, value=value, help=help_text)

    st.divider()

    # ==========================================
    # Deep Dive Content
    # ==========================================
    col_left, col_right = st.columns([2, 1])

    with col_left:
        # Strengths
        st.markdown("### 💪 Strengths")
        strengths = data.get("strengths", "")
        if strengths and str(strengths) not in ["0", "", "None", "nan"]:
            st.info(strengths)
        else:
            st.caption("No strengths data available.")

        # Seasonality Analysis
        st.markdown("### 📅 Seasonality Analysis")
        seasonality = _parse_json_data(data.get("seasonality_analysis"))

        if seasonality:
            if isinstance(seasonality, list) and seasonality:
                try:
                    s_df = pd.DataFrame(seasonality)
                    st.dataframe(s_df, hide_index=True, width="stretch")
                except (ValueError, TypeError):
                    st.json(seasonality)
            elif isinstance(seasonality, dict):
                st.json(seasonality)
            else:
                st.write(seasonality)
        else:
            st.caption("No seasonality data available.")

    with col_right:
        # Analyst Ratings
        st.markdown("### 🎯 Analyst Ratings")

        analyst_final_rating = data.get("analyst_final_rating", "-")
        analyst_count = data.get("analyst_count", 0)

        st.metric("Consensus", analyst_final_rating or "-")

        if analyst_count and str(analyst_count) not in ["0", "", "nan", "None"]:
            st.caption(f"Based on {int(float(analyst_count))} analyst(s)")
        else:
            st.caption("No analyst data")

        # Ratings breakdown
        analyst_ratings = _parse_json_data(data.get("analyst_ratings"))

        if analyst_ratings and isinstance(analyst_ratings, list):
            st.markdown("**Ratings Breakdown:**")
            for rating in analyst_ratings:
                if isinstance(rating, dict):
                    name = rating.get("name", "Unknown")
                    value = rating.get("value", 0)
                    st.write(f"• {name}: {value}")

            try:
                ratings_df = pd.DataFrame(analyst_ratings)
                if (
                    not ratings_df.empty
                    and "name" in ratings_df.columns
                    and "value" in ratings_df.columns
                ):
                    st.markdown("#### 📊 Distribution")
                    st.bar_chart(ratings_df, x="name", y="value")
            except (ValueError, TypeError, KeyError):
                pass
        else:
            st.caption("No detailed analyst ratings available.")


if __name__ == "__main__":
    main()
