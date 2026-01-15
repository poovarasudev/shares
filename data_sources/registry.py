"""
Data Source Registry.

Central registry for managing multiple data sources across the application.
Supports registering, retrieving, and caching data from various sources.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Optional, Type
from .base import DataSourceBase, DataSourceConfig
from .google_sheets import GoogleSheetsSource


class DataSourceRegistry:
    """
    Registry for managing multiple data sources.

    Provides centralized access to all configured data sources
    and handles caching of loaded data.
    """

    _sources: Dict[str, DataSourceBase] = {}
    _source_types: Dict[str, Type[DataSourceBase]] = {
        "google_sheets": GoogleSheetsSource,
    }

    @classmethod
    def register(cls, name: str, source: DataSourceBase) -> None:
        """
        Register a data source.

        Args:
            name: Unique name for the source
            source: DataSourceBase instance
        """
        cls._sources[name] = source

    @classmethod
    def register_type(cls, type_name: str, source_class: Type[DataSourceBase]) -> None:
        """
        Register a new data source type.

        Args:
            type_name: Type identifier (e.g., 'database', 'api')
            source_class: DataSourceBase subclass
        """
        cls._source_types[type_name] = source_class

    @classmethod
    def get(cls, name: str) -> Optional[DataSourceBase]:
        """
        Get a registered data source by name.

        Args:
            name: Source name

        Returns:
            DataSourceBase instance or None
        """
        return cls._sources.get(name)

    @classmethod
    def create(cls, config: DataSourceConfig) -> Optional[DataSourceBase]:
        """
        Create a data source from configuration.

        Args:
            config: DataSourceConfig instance

        Returns:
            Configured DataSourceBase instance
        """
        source_class = cls._source_types.get(config.source_type)
        if not source_class:
            raise ValueError(f"Unknown source type: {config.source_type}")

        source = source_class(config)
        cls._sources[config.name] = source
        return source

    @classmethod
    def list_sources(cls) -> Dict[str, DataSourceBase]:
        """Get all registered sources."""
        return cls._sources.copy()

    @classmethod
    def clear(cls) -> None:
        """Clear all registered sources."""
        cls._sources.clear()


def get_data_source(name: str) -> Optional[DataSourceBase]:
    """
    Convenience function to get a data source.

    Args:
        name: Source name

    Returns:
        DataSourceBase instance or None
    """
    return DataSourceRegistry.get(name)


@st.cache_data(ttl=86400, show_spinner=False)
def load_cached_data(source_name: str, _source: DataSourceBase) -> pd.DataFrame:
    """
    Load data from a source with caching.

    Args:
        source_name: Name of the source (used for cache key differentiation)
        _source: DataSourceBase instance (underscore prefix excludes from hash)

    Returns:
        Loaded DataFrame
    """
    # source_name is used by st.cache_data as part of the cache key
    _ = source_name  # Acknowledge parameter usage for linting
    return _source.load_data()


def clear_source_cache(_source_name: str = None) -> None:
    """Clear cache for data sources."""
    load_cached_data.clear()
