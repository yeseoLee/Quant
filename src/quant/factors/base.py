"""Base class for all factors."""

from abc import ABC, abstractmethod

import pandas as pd


class BaseFactor(ABC):
    """Abstract base class for all factor calculations."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the factor values.

        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)

        Returns:
            DataFrame with original data plus calculated factor columns
        """
        pass

    @abstractmethod
    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on factor values.

        Args:
            df: DataFrame with calculated factor values

        Returns:
            Series with signals: 1 (buy), -1 (sell), 0 (hold)
        """
        pass

    def _validate_ohlcv(self, df: pd.DataFrame) -> None:
        """Validate that required OHLCV columns exist."""
        required = ["open", "high", "low", "close", "volume"]
        # Check with case-insensitive matching
        df_cols_lower = [col.lower() for col in df.columns]
        missing = [col for col in required if col not in df_cols_lower]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
