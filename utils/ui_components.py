"""
UI Components and Styling Utilities.

Provides common UI components and custom CSS styling for the Streamlit application.
"""

import streamlit as st


def apply_custom_css():
    """
    Apply custom CSS styling to the Streamlit application.

    This function should be called at the beginning of each page to ensure
    consistent styling across the application.
    """
    st.markdown(
        """
        <style>
        .stToolbarActions {
            visibility: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
