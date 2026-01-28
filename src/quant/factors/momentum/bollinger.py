"""Bollinger Bands indicator."""

import pandas as pd
import pandas_ta as ta

from quant.factors.base import BaseFactor


class BollingerBands(BaseFactor):
    """
    Bollinger Bands volatility and momentum indicator.

    Consists of:
    - Middle Band: Simple Moving Average (SMA)
    - Upper Band: SMA + (std_dev * multiplier)
    - Lower Band: SMA - (std_dev * multiplier)
    """

    def __init__(self, period: int = 20, std_dev: float = 2.0):
        """
        Initialize Bollinger Bands.

        Args:
            period: Lookback period for moving average
            std_dev: Standard deviation multiplier for bands
        """
        super().__init__(name="BollingerBands")
        self.period = period
        self.std_dev = std_dev

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands."""
        self._validate_ohlcv(df)
        result = df.copy()

        # Use pandas_ta for Bollinger Bands
        bbands = ta.bbands(result["close"], length=self.period, std=self.std_dev)

        if bbands is not None:
            result["bb_lower"] = bbands.iloc[:, 0]  # BBL
            result["bb_middle"] = bbands.iloc[:, 1]  # BBM
            result["bb_upper"] = bbands.iloc[:, 2]  # BBU
            result["bb_bandwidth"] = bbands.iloc[:, 3]  # BBB
            result["bb_percent"] = bbands.iloc[:, 4]  # BBP

        return result

    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on Bollinger Bands.

        Returns:
            1 when price touches/crosses below lower band (buy)
            -1 when price touches/crosses above upper band (sell)
            0 otherwise (hold)
        """
        if "bb_lower" not in df.columns:
            df = self.calculate(df)

        signals = pd.Series(0, index=df.index)

        # Buy signal: Price crosses below lower band
        signals[df["close"] <= df["bb_lower"]] = 1

        # Sell signal: Price crosses above upper band
        signals[df["close"] >= df["bb_upper"]] = -1

        return signals
