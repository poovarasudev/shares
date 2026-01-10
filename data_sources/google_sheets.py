"""
Google Sheets Data Source.

Handles loading data from public Google Sheets via CSV export.
"""

import re
import time
import urllib.parse
import urllib.error
from typing import Callable, List, Optional
import pandas as pd
import streamlit as st

from .base import DataSourceBase, DataSourceConfig
from .processors import STOCK_ANALYSIS_PROCESSORS


class GoogleSheetsSource(DataSourceBase):
    """
    Data source for Google Sheets.
    
    Loads data from public Google Sheets using CSV export URL.
    """
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.sheet_url = config.connection_params.get('sheet_url', '')
        self.sheet_tab = config.connection_params.get('sheet_tab', 'Sheet1')
        self.max_retries = config.connection_params.get('max_retries', 3)
    
    def connect(self) -> bool:
        """Verify the sheet URL is valid."""
        return bool(self._build_csv_url())
    
    def _build_csv_url(self) -> Optional[str]:
        """Build CSV export URL from Google Sheets URL."""
        if not self.sheet_url:
            return None
        
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", self.sheet_url)
        if not match:
            return None
        
        sheet_key = match.group(1)
        encoded_sheet_name = urllib.parse.quote(self.sheet_tab)
        
        return f"https://docs.google.com/spreadsheets/d/{sheet_key}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"
    
    def fetch_data(self) -> pd.DataFrame:
        """Fetch data from Google Sheets with retry logic."""
        csv_url = self._build_csv_url()
        
        if not csv_url:
            st.error("❌ Invalid Google Sheet URL format.")
            return pd.DataFrame()
        
        for attempt in range(self.max_retries):
            try:
                df = pd.read_csv(csv_url, on_bad_lines='skip')
                
                if df.empty:
                    st.warning("⚠️ The worksheet is empty.")
                    return pd.DataFrame()
                
                return df
                
            except urllib.error.URLError:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                    
            except pd.errors.ParserError:
                st.error("❌ Failed to parse data from sheet.")
                return pd.DataFrame()
                
            except pd.errors.EmptyDataError:
                st.warning("⚠️ The worksheet is empty.")
                return pd.DataFrame()
        
        st.error(f"❌ Failed to load data after {self.max_retries} attempts.")
        return pd.DataFrame()


def create_google_sheets_source(
    name: str,
    sheet_url: str,
    sheet_tab: str,
    derived_processors: List[Callable[[pd.DataFrame], pd.DataFrame]] = None,
    **kwargs
) -> GoogleSheetsSource:
    """
    Factory function to create a Google Sheets data source.
    
    Args:
        name: Name identifier for this source
        sheet_url: Google Sheets URL
        sheet_tab: Sheet/tab name
        derived_processors: List of callables that compute derived columns.
                           Defaults to STOCK_ANALYSIS_PROCESSORS if None.
                           Pass empty list [] for no derived columns.
        **kwargs: Additional configuration options
        
    Returns:
        Configured GoogleSheetsSource instance
    """
    # Default to stock analysis processors if not specified
    if derived_processors is None:
        derived_processors = STOCK_ANALYSIS_PROCESSORS
    
    config = DataSourceConfig(
        name=name,
        source_type='google_sheets',
        connection_params={
            'sheet_url': sheet_url,
            'sheet_tab': sheet_tab,
            'max_retries': kwargs.get('max_retries', 3),
        },
        cache_ttl=kwargs.get('cache_ttl', 900),
        id_column=kwargs.get('id_column', 'scId'),
        display_columns=kwargs.get('display_columns', []),
        hidden_columns=kwargs.get('hidden_columns', []),
        json_columns=kwargs.get('json_columns', []),
        numeric_columns=kwargs.get('numeric_columns', []),
        filter_columns=kwargs.get('filter_columns', []),
        search_columns=kwargs.get('search_columns', []),
        derived_column_processors=derived_processors,
    )
    
    return GoogleSheetsSource(config)
