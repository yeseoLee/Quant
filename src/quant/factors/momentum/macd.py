"""MACD (Moving Average Convergence Divergence) indicator."""

import pandas as pd
import pandas_ta as ta

from quant.factors.base import BaseFactor


class MACD(BaseFactor):
    """
    Moving Average Convergence Divergence (MACD) momentum indicator.

    MACD shows the relationship between two EMAs of price.
    - MACD Line: fast EMA - slow EMA
    - Signal Line: EMA of MACD line
    - Histogram: MACD Line - Signal Line

    Signals:
    - MACD crosses above Signal: Bullish
    - MACD crosses below Signal: Bearish
    - Histogram positive and increasing: Strong bullish momentum
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ):
        """
        Initialize MACD indicator.

        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
        """
        super().__init__(name="MACD")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate MACD values."""
        self._validate_ohlcv(df)
        result = df.copy()

        macd = ta.macd(
            result["close"],
            fast=self.fast_period,
            slow=self.slow_period,
            signal=self.signal_period,
        )

        if macd is not None:
            result["macd"] = macd.iloc[:, 0]  # MACD line
            result["macd_histogram"] = macd.iloc[:, 1]  # Histogram
            result["macd_signal"] = macd.iloc[:, 2]  # Signal line

        return result

    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on MACD crossovers.

        Returns:
            1 when MACD crosses above signal line (buy)
            -1 when MACD crosses below signal line (sell)
            0 otherwise (hold)
        """
        if "macd" not in df.columns:
            df = self.calculate(df)

        signals = pd.Series(0, index=df.index)

        macd = df["macd"]
        signal = df["macd_signal"]
        macd_prev = macd.shift(1)
        signal_prev = signal.shift(1)

        # Buy signal: MACD crosses above signal line
        buy_condition = (macd > signal) & (macd_prev <= signal_prev)
        signals[buy_condition] = 1

        # Sell signal: MACD crosses below signal line
        sell_condition = (macd < signal) & (macd_prev >= signal_prev)
        signals[sell_condition] = -1

        return signals

    def get_momentum_score(self, df: pd.DataFrame) -> float:
        """
        Calculate momentum score from MACD (0-100).

        Score is based on:
        - MACD histogram direction and magnitude
        - MACD position relative to signal line
        """
        if "macd" not in df.columns:
            df = self.calculate(df)

        latest = df.iloc[-1]
        if pd.isna(latest.get("macd")) or pd.isna(latest.get("macd_signal")):
            return 50.0  # Neutral

        macd = latest["macd"]
        signal = latest["macd_signal"]
        histogram = latest["macd_histogram"]

        # Base score from MACD vs Signal position
        if macd > signal:
            base_score = 60
        elif macd < signal:
            base_score = 40
        else:
            base_score = 50

        # Adjust based on histogram (momentum strength)
        # Normalize histogram relative to recent range
        hist_series = df["macd_histogram"].dropna().tail(50)
        if len(hist_series) > 0:
            hist_range = hist_series.max() - hist_series.min()
            if hist_range > 0:
                normalized_hist = (histogram - hist_series.min()) / hist_range
                # Scale to add/subtract up to 30 points
                adjustment = (normalized_hist - 0.5) * 60
                base_score += adjustment

        return max(0, min(100, base_score))
