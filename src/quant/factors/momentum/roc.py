"""ROC (Rate of Change) indicator."""

import pandas as pd
import pandas_ta as ta

from quant.factors.base import BaseFactor


class ROC(BaseFactor):
    """
    Rate of Change (ROC) momentum indicator.

    ROC measures the percentage change in price over a period.
    - ROC > 0: Price is higher than n periods ago (bullish)
    - ROC < 0: Price is lower than n periods ago (bearish)
    - ROC crossing zero: Trend reversal

    Useful for:
    - Identifying momentum shifts
    - Divergence analysis
    - Trend confirmation
    """

    def __init__(
        self,
        period: int = 12,
        signal_period: int = 9,
    ):
        """
        Initialize ROC indicator.

        Args:
            period: Lookback period for ROC calculation
            signal_period: Period for ROC signal line (SMA)
        """
        super().__init__(name="ROC")
        self.period = period
        self.signal_period = signal_period

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate ROC values."""
        self._validate_ohlcv(df)
        result = df.copy()

        result["roc"] = ta.roc(result["close"], length=self.period)

        # Add signal line for crossover detection
        result["roc_signal"] = ta.sma(result["roc"], length=self.signal_period)

        return result

    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on ROC zero crossover.

        Returns:
            1 when ROC crosses above zero (buy)
            -1 when ROC crosses below zero (sell)
            0 otherwise (hold)
        """
        if "roc" not in df.columns:
            df = self.calculate(df)

        signals = pd.Series(0, index=df.index)

        roc = df["roc"]
        roc_prev = roc.shift(1)

        # Buy signal: ROC crosses above zero
        buy_condition = (roc > 0) & (roc_prev <= 0)
        signals[buy_condition] = 1

        # Sell signal: ROC crosses below zero
        sell_condition = (roc < 0) & (roc_prev >= 0)
        signals[sell_condition] = -1

        return signals

    def get_momentum_score(self, df: pd.DataFrame) -> float:
        """
        Calculate momentum score from ROC (0-100).

        Score is based on ROC value normalized to recent range.
        """
        if "roc" not in df.columns:
            df = self.calculate(df)

        latest = df.iloc[-1]
        if pd.isna(latest.get("roc")):
            return 50.0  # Neutral

        roc = latest["roc"]

        # Normalize ROC relative to recent range
        roc_series = df["roc"].dropna().tail(50)
        if len(roc_series) > 0:
            roc_min = roc_series.min()
            roc_max = roc_series.max()
            roc_range = roc_max - roc_min

            if roc_range > 0:
                normalized = (roc - roc_min) / roc_range * 100
                return max(0, min(100, normalized))

        # Fallback: normalize assuming typical ROC range of -20 to +20
        normalized = (roc + 20) / 40 * 100
        return max(0, min(100, normalized))
