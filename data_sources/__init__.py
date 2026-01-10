"""
Data Sources Module.

This module provides a unified interface for loading data from various sources:
- Google Sheets
- Databases (PostgreSQL, MySQL, etc.)
- REST APIs
- Local files (CSV, Excel, JSON)

Each data source is implemented as a separate handler class that follows
a common interface for consistency.
"""

from .base import DataSourceBase, DataSourceConfig
from .google_sheets import GoogleSheetsSource, create_google_sheets_source
from .registry import DataSourceRegistry, get_data_source
from .processors import (
    compute_pe_vs_sector,
    compute_analyst_confidence,
    STOCK_ANALYSIS_PROCESSORS,
    NO_PROCESSORS,
)


def init_data_sources():
    """
    Initialize and register all data sources.
    
    This function should be called once at application startup (typically in Home.py).
    It registers all configured data sources with the DataSourceRegistry.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    from config import constants as const
    
    # Money Control Stocks - Google Sheets
    if const.GOOGLE_SHEET_URL:
        mc_source = create_google_sheets_source(
            name="money_control",
            sheet_url=const.GOOGLE_SHEET_URL,
            sheet_tab=const.GOOGLE_SHEET_TAB,
            json_columns=const.JSON_COLUMNS,
            numeric_columns=const.NUMERIC_COLUMNS,
            filter_columns=const.FILTER_COLUMNS,
            search_columns=['company_name', 'scId'],
            display_columns=const.TABLE_COLUMNS,
        )
        DataSourceRegistry.register("money_control", mc_source)
        
        # Money Control Events - Google Sheets
        mc_events_source = create_google_sheets_source(
            name="money_control_events",
            sheet_url=const.GOOGLE_SHEET_URL,
            sheet_tab=const.GOOGLE_SHEET_EVENTS_TAB,
            json_columns=[],
            numeric_columns=[],
            filter_columns=const.EVENT_FILTER_COLUMNS,
            search_columns=const.EVENT_SEARCH_COLUMNS,
            display_columns=const.EVENT_COLUMNS,
            derived_processors=NO_PROCESSORS,
        )
        DataSourceRegistry.register("money_control_events", mc_events_source)
    
    # TODO: Add more data sources here as needed
    # Example:
    # db_source = create_database_source(...)
    # DataSourceRegistry.register("database", db_source)
    
    return True


def ensure_data_source(source_name: str) -> bool:
    """
    Verify that a data source is available, initializing if necessary.
    
    This is a safety fallback for pages that might be accessed directly
    without going through Home.py first.
    
    Args:
        source_name: Name of the data source to check
        
    Returns:
        bool: True if source is available, False otherwise
    """
    if DataSourceRegistry.get(source_name):
        return True
    
    # Fallback: attempt initialization
    return init_data_sources()


__all__ = [
    'DataSourceBase',
    'DataSourceConfig', 
    'GoogleSheetsSource',
    'DataSourceRegistry',
    'get_data_source',
    'init_data_sources',
    'ensure_data_source',
]
