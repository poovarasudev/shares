"""
ScanX Trade Company Details Page.

Provides detailed analysis view for a specific company from ScanX Trade
including financial metrics, analyst ratings, and key information.
"""

import streamlit as st
import pandas as pd
import json
from typing import Any, Optional

from data_sources.registry import DataSourceRegistry, load_cached_data

# ============================================
# Page Configuration
# ============================================
st.set_page_config(page_title="ScanX Company Details", page_icon="🏛️", layout="wide")

DATA_SOURCE_NAME = "scanx_trade"


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


def _get_company_id() -> Optional[str]:
    """Get company ID from query params or session state."""
    # Check query params first
    sid = st.query_params.get("sid")

    if sid:
        st.session_state["selected_scanx_sid"] = sid
        return sid

    # Fallback to session state
    return st.session_state.get("selected_scanx_sid")


def _go_back():
    """Navigate back to market overview."""
    if "sid" in st.query_params:
        del st.query_params["sid"]
    if "selected_scanx_sid" in st.session_state:
        del st.session_state["selected_scanx_sid"]
    st.switch_page("pages/4_📊_ScanX_Market_Overview.py")


# ============================================
# Main Content
# ============================================
def main():
    # Load data first to enable company selection
    source = DataSourceRegistry.get(DATA_SOURCE_NAME)
    if not source:
        st.error("❌ Data source not configured.")
        return

    with st.spinner("Loading data..."):
        df = load_cached_data(DATA_SOURCE_NAME, source)

    if df.empty:
        st.error("❌ Data could not be loaded.")
        return

    # Get company ID
    sid = _get_company_id()

    if not sid or sid in ["None", "nan", ""]:
        st.info("📋 No company selected. Please select a company to view details.")

        # Create searchable company list
        company_options = df[["disp_sym", "sid"]].copy()
        company_options["display"] = (
            company_options["disp_sym"]
            + " ("
            + company_options["sid"].astype(str)
            + ")"
        )
        company_dict = dict(zip(company_options["display"], company_options["sid"]))

        col1, col2 = st.columns([3, 1])
        with col1:
            selected_company = st.selectbox(
                "Search and select a company:",
                options=[""] + list(company_dict.keys()),
                index=0,
                placeholder="Type to search...",
                key="scanx_company_search",
            )

        with col2:
            if st.button("← Back to Market Overview", width="stretch"):
                _go_back()

        if selected_company and selected_company != "":
            selected_sid = company_dict[selected_company]
            st.session_state["selected_scanx_sid"] = str(selected_sid)
            st.query_params["sid"] = str(selected_sid)
            st.rerun()

        st.stop()

    if df.empty:
        st.error("❌ Data could not be loaded.")
        return

    # Find company
    company_data = df[df["sid"].astype(str) == str(sid)]

    if company_data.empty:
        st.error(f"❌ Company with ID '{sid}' not found.")
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
        st.markdown(f"# {data.get('disp_sym', 'Unknown Company')}")
        sym = data.get("sym", "")
        sector = data.get("sector", "N/A")
        sub_sector = data.get("sub_sector", "N/A")
        st.caption(f"📌 {sym} • 📁 {sector} • 🏭 {sub_sector}")

    with col_status:
        status = data.get("status", "Unknown")
        status_color = "🟢" if status == "Synced" else "🟡"
        st.markdown(f"### {status_color} {status}")

    with col_link:
        if data.get("url"):
            st.link_button("🔗 ScanX Trade", data.get("url"), width="stretch")

    st.divider()

    # ==========================================
    # Price Section
    # ==========================================
    st.markdown("## 💰 Current Price")

    price_col1, price_col2, price_col3 = st.columns([0.3, 0.4, 0.3])

    ltp = data.get("ltp")
    pchange = data.get("pchange")
    p_perchange = data.get("p_perchange")

    with price_col1:
        if ltp and str(ltp) not in ["-", "None", "nan"]:
            # Determine color based on change
            if pchange is not None and not pd.isna(pchange):
                price_color = "#ef4444" if float(pchange) < 0 else "#22c55e"
            else:
                price_color = "#22c55e"
            st.markdown(
                f"<h1 style='color:{price_color}; margin:0;'>₹{ltp}</h1>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<h1 style='color:#6b7280;'>--</h1>", unsafe_allow_html=True)

    with price_col2:
        if pchange is not None and not pd.isna(pchange):
            change_val = float(pchange)
            change_icon = "📉" if change_val < 0 else "📈"
            change_color = "#ef4444" if change_val < 0 else "#22c55e"
            st.markdown(
                f"<h2 style='color:{change_color};'>{change_icon} {change_val:.2f}%</h2>",
                unsafe_allow_html=True,
            )

    with price_col3:
        mcap = data.get("mcap")
        if mcap and not pd.isna(mcap):
            st.markdown(f"**Market Cap:** {_format_mcap(mcap)}")

    st.divider()

    # ==========================================
    # Key Metrics Section
    # ==========================================
    st.markdown("## 📊 Key Financial Metrics")

    cols = st.columns(6)
    metrics = [
        (
            "LTP",
            f"₹{data.get('ltp', '-')}" if data.get("ltp") else "-",
            "Last Traded Price",
        ),
        ("PE", _format_metric(data.get("pe")), "Price to Earnings"),
        ("P/B", _format_metric(data.get("pb")), "Price to Book"),
        ("EPS", _format_metric(data.get("yearly_earning_per_share")), "Yearly EPS"),
        ("M-Cap", _format_mcap(data.get("mcap")), "Market Capitalization"),
        ("Exchange", data.get("exch", "-") or "-", "Stock Exchange"),
    ]

    for col, (label, value, help_text) in zip(cols, metrics):
        col.metric(label=label, value=value, help=help_text)

    st.divider()

    # ==========================================
    # Sector Comparison Section
    # ==========================================
    st.markdown("## 📈 Sector Comparison")

    sector_cols = st.columns(4)
    sector_metrics = [
        ("Sector PE", _format_metric(data.get("ind_pe")), "Industry PE"),
        ("Sector P/B", _format_metric(data.get("ind_pb")), "Industry P/B"),
        ("Sector EPS", _format_metric(data.get("ind_eps")), "Industry EPS"),
        (
            "PE/Sector PE Ratio",
            _format_metric(data.get("p_e_sec_p_e_ratio")),
            "Company PE vs Sector PE",
        ),
    ]

    for col, (label, value, help_text) in zip(sector_cols, sector_metrics):
        col.metric(label=label, value=value, help=help_text)

    st.divider()

    # ==========================================
    # Deep Dive Content
    # ==========================================
    col_left, col_right = st.columns([2, 1])

    with col_left:
        # Additional Information
        st.markdown("### 📋 Company Information")

        info_data = {
            "ISIN": data.get("isin", "-") or "-",
            "Symbol": data.get("sym", "-") or "-",
            "SEO Symbol": data.get("seosym", "-") or "-",
            "Exchange": data.get("exch", "-") or "-",
            "Instrument": data.get("inst", "-") or "-",
        }

        for key, value in info_data.items():
            st.markdown(f"**{key}:** {value}")

    with col_right:
        # Analyst Ratings
        st.markdown("### 🎯 Analyst Ratings")

        analyst_final_rating = data.get("analyst_final_rating", "-")
        analyst_count = data.get("total_analyst_count", 0)

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
                    st.write(f"• {name}: {value}%")

            try:
                ratings_df = pd.DataFrame(analyst_ratings)
                if (
                    not ratings_df.empty
                    and "name" in ratings_df.columns
                    and "value" in ratings_df.columns
                ):
                    # Convert value to numeric
                    ratings_df["value"] = pd.to_numeric(
                        ratings_df["value"], errors="coerce"
                    )
                    st.markdown("#### 📊 Distribution")
                    st.bar_chart(ratings_df, x="name", y="value")
            except (ValueError, TypeError, KeyError):
                pass
        else:
            st.caption("No detailed analyst ratings available.")


if __name__ == "__main__":
    main()
