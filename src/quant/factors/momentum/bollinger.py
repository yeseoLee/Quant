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

    def get_momentum_score(self, df: pd.DataFrame) -> float:
        """
        Calculate momentum score from Bollinger Bands (0-100).

        Score is based on BB%B (percent B):
        - %B = (Price - Lower) / (Upper - Lower)
        - %B > 1: Price above upper band (overbought but strong momentum)
        - %B < 0: Price below lower band (oversold)
        - %B = 0.5: Price at middle band
        """
        if "bb_percent" not in df.columns:
            df = self.calculate(df)

        latest = df.iloc[-1]
        if pd.isna(latest.get("bb_percent")):
            return 50.0  # Neutral

        bb_percent = latest["bb_percent"]

        # bb_percent is typically in range -0.5 to 1.5
        # Normalize to 0-100
        # 0 -> 25, 0.5 -> 50, 1 -> 75
        normalized = bb_percent * 50 + 25
        return max(0, min(100, normalized))
