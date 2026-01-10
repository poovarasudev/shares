"""
Base classes for data sources.

Provides abstract base class and configuration dataclass that all
data source implementations must follow.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import pandas as pd


@dataclass
class DataSourceConfig:
    """Configuration for a data source."""
    name: str
    source_type: str  # 'google_sheets', 'database', 'api', 'file'
    connection_params: Dict[str, Any] = field(default_factory=dict)
    cache_ttl: int = 900  # 15 minutes default
    enabled: bool = True
    
    # Column configuration
    id_column: str = "scId"
    display_columns: List[str] = field(default_factory=list)
    hidden_columns: List[str] = field(default_factory=list)
    json_columns: List[str] = field(default_factory=list)
    numeric_columns: List[str] = field(default_factory=list)
    
    # Filter configuration
    filter_columns: List[str] = field(default_factory=list)
    search_columns: List[str] = field(default_factory=list)
    
    # Derived columns: list of callables that take a DataFrame and return a DataFrame
    # Each callable adds computed columns specific to this data source
    derived_column_processors: List[Callable[[pd.DataFrame], pd.DataFrame]] = field(default_factory=list)


class DataSourceBase(ABC):
    """
    Abstract base class for all data sources.
    
    All data source implementations must inherit from this class
    and implement the required abstract methods.
    """
    
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self._df: Optional[pd.DataFrame] = None
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the data source.
        
        Returns:
            True if connection successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def fetch_data(self) -> pd.DataFrame:
        """
        Fetch raw data from the source.
        
        Returns:
            Raw DataFrame from the source.
        """
        pass
    
    def load_data(self) -> pd.DataFrame:
        """
        Load and process data from the source.
        
        Returns:
            Processed DataFrame ready for use.
        """
        df = self.fetch_data()
        if df.empty:
            return df
        return self.process_data(df)
    
    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process raw data (normalize columns, convert types, etc.).
        
        Args:
            df: Raw DataFrame
            
        Returns:
            Processed DataFrame
        """
        # Make a copy to avoid SettingWithCopyWarning
        df = df.copy()
        
        # Normalize column names
        df.columns = [self._to_snake_case(col) for col in df.columns]
        
        # Remove duplicate columns
        df = df.loc[:, ~df.columns.duplicated(keep='last')]
        
        # Ensure ID column exists
        id_col = self._to_snake_case(self.config.id_column)
        if id_col in df.columns:
            df['scId'] = df[id_col].astype(str)
        elif 'scid' in df.columns:
            df['scId'] = df['scid'].astype(str)
        elif 'scId' not in df.columns:
            df['scId'] = df.index.astype(str)
        
        # Convert numeric columns
        for col in self.config.numeric_columns:
            snake_col = self._to_snake_case(col)
            if snake_col in df.columns:
                df[snake_col] = pd.to_numeric(df[snake_col], errors='coerce')
        
        # Handle JSON columns
        for col in self.config.json_columns:
            snake_col = self._to_snake_case(col)
            if snake_col in df.columns:
                df[snake_col] = df[snake_col].apply(self._parse_json_safe)
        
        # Replace NaN with None
        df = df.where(pd.notnull(df), None)

        # Apply source-specific derived column processors
        for processor in self.config.derived_column_processors:
            try:
                df = processor(df)
            except Exception as e:
                # Log but don't fail on derived column errors
                import logging
                logging.warning(f"Derived column processor failed: {e}")

        return df
    
    def get_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get summary statistics for the data.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with statistics
        """
        if df.empty:
            return {'total': 0, 'sectors': 0, 'industries': 0}
        
        stats = {'total': len(df)}
        
        if 'sector' in df.columns:
            stats['sectors'] = df['sector'].nunique()
        if 'industry' in df.columns:
            stats['industries'] = df['industry'].nunique()
        if 'status' in df.columns:
            stats['synced'] = len(df[df['status'] == 'Synced'])
        
        return stats
    
    @staticmethod
    def _to_snake_case(name: str) -> str:
        """Convert string to snake_case."""
        import re
        s = str(name).replace('\ufeff', '').strip()
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower().replace(" ", "_")
    
    @staticmethod
    def _parse_json_safe(json_str: Any) -> Any:
        """Safely parse JSON string."""
        import json
        
        if not json_str or pd.isna(json_str):
            return None
        if isinstance(json_str, (dict, list)):
            return json_str
        try:
            if isinstance(json_str, str):
                return json.loads(json_str)
            return None
        except (json.JSONDecodeError, TypeError):
            return None
