"""
Derived Column Processors.

Reusable functions that compute derived columns for data sources.
Each processor takes a DataFrame and returns a DataFrame with added columns.
These can be configured per data source to support different sheets/reports.
"""

import pandas as pd
from typing import Dict, Any
from config import constants as const


def compute_pe_vs_sector(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute PE vs Sector percentage and flag columns.
    
    Adds:
        - pe_vs_sector_pct: Percentage difference between TTM PE and Sector PE
        - pe_vs_sector_flag: Categorical label (Cheap/Fair/Expensive/Unknown)
    
    Args:
        df: DataFrame with 'ttm_pe' and 'sector_pe' columns
        
    Returns:
        DataFrame with derived columns added
    """
    df = df.copy()
    
    def _compute_pct(row):
        ttm = row.get('ttm_pe')
        sector = row.get('sector_pe')
        try:
            if ttm is None or sector is None:
                return None
            if sector == 0:
                return None
            return ((ttm - sector) / sector) * 100.0
        except Exception:
            return None

    df['pe_vs_sector_pct'] = df.apply(_compute_pct, axis=1)

    def _pe_flag(pct):
        if pct is None:
            return 'Unknown'
        try:
            pe_cheap = getattr(const, 'PE_CHEAP_PCT', 20)
            pe_delta = getattr(const, 'PE_DELTA_PCT', 20)
            if pct <= -abs(pe_cheap):
                return 'Cheap'
            if pct >= pe_delta:
                return 'Expensive'
            return 'Fair'
        except Exception:
            return 'Unknown'

    df['pe_vs_sector_flag'] = df['pe_vs_sector_pct'].apply(_pe_flag)
    
    return df


def compute_analyst_confidence(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute analyst confidence score and bucket columns.
    
    Adds:
        - analyst_confidence_score: Numeric score 0-100 based on analyst count and rating
        - analyst_confidence: Categorical bucket (High/Medium/Low/Unknown)
    
    Args:
        df: DataFrame with 'analyst_count' and 'analyst_final_rating' columns
        
    Returns:
        DataFrame with derived columns added
    """
    df = df.copy()
    
    def _compute_score(row):
        count = row.get('analyst_count')
        rating = row.get('analyst_final_rating')
        if count is None or pd.isna(count):
            return None
        try:
            count_val = float(count)
        except Exception:
            return None

        weights = getattr(const, 'ANALYST_SCORE_WEIGHTS', {})
        rating_key = str(rating).strip() if rating is not None else ''
        weight = float(weights.get(rating_key, weights.get(rating_key.title(), 0.5))) if weights else 0.5

        cap = getattr(const, 'ANALYST_COUNT_CAP', 10)
        try:
            capped = min(count_val, cap)
            score = weight * (capped / float(cap)) * 100.0
            return float(score)
        except Exception:
            return None

    df['analyst_confidence_score'] = df.apply(_compute_score, axis=1)

    def _bucket(score):
        if score is None:
            return 'Unknown'
        buckets = getattr(const, 'ANALYST_CONFIDENCE_BUCKETS', {'high': 70, 'medium': 40})
        high = buckets.get('high', 70)
        medium = buckets.get('medium', 40)
        try:
            s = float(score)
            if s >= high:
                return 'High'
            if s >= medium:
                return 'Medium'
            return 'Low'
        except Exception:
            return 'Unknown'

    df['analyst_confidence'] = df['analyst_confidence_score'].apply(_bucket)
    
    return df


# Pre-configured processor lists for common use cases
STOCK_ANALYSIS_PROCESSORS = [
    compute_pe_vs_sector,
    compute_analyst_confidence,
]

# Empty list for sheets that don't need derived columns
NO_PROCESSORS = []
