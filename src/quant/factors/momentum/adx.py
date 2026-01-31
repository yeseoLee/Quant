"""ADX (Average Directional Index) indicator."""

import pandas as pd
import pandas_ta as ta

from quant.factors.base import BaseFactor


class ADX(BaseFactor):
    """
    Average Directional Index (ADX) trend strength indicator.

    ADX measures trend strength regardless of direction.
    - ADX > 25: Strong trend
    - ADX < 20: Weak trend or ranging
    - +DI > -DI: Bullish trend
    - -DI > +DI: Bearish trend

    Signals are based on DI crossovers when trend is strong.
    """

    def __init__(
        self,
        period: int = 14,
        trend_threshold: float = 25.0,
    ):
        """
        Initialize ADX indicator.

        Args:
            period: Lookback period for ADX calculation
            trend_threshold: ADX threshold for strong trend
        """
        super().__init__(name="ADX")
        self.period = period
        self.trend_threshold = trend_threshold

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate ADX values."""
        self._validate_ohlcv(df)
        result = df.copy()

        adx = ta.adx(
            result["high"],
            result["low"],
            result["close"],
            length=self.period,
        )

        if adx is not None:
            result["adx"] = adx.iloc[:, 0]  # ADX
            result["adx_di_plus"] = adx.iloc[:, 1]  # +DI
            result["adx_di_minus"] = adx.iloc[:, 2]  # -DI

        return result

    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on ADX and DI crossovers.

        Returns:
            1 when +DI crosses above -DI with strong ADX (buy)
            -1 when -DI crosses above +DI with strong ADX (sell)
            0 otherwise (hold)
        """
        if "adx" not in df.columns:
            df = self.calculate(df)

        signals = pd.Series(0, index=df.index)

        adx = df["adx"]
        di_plus = df["adx_di_plus"]
        di_minus = df["adx_di_minus"]

        di_plus_prev = di_plus.shift(1)
        di_minus_prev = di_minus.shift(1)

        strong_trend = adx > self.trend_threshold

        # Buy signal: +DI crosses above -DI with strong trend
        buy_condition = (di_plus > di_minus) & (di_plus_prev <= di_minus_prev) & strong_trend
        signals[buy_condition] = 1

        # Sell signal: -DI crosses above +DI with strong trend
        sell_condition = (di_minus > di_plus) & (di_minus_prev <= di_plus_prev) & strong_trend
        signals[sell_condition] = -1

        return signals

    def get_momentum_score(self, df: pd.DataFrame) -> float:
        """
        Calculate momentum score from ADX (0-100).

        Score is based on:
        - ADX strength (trend strength)
        - DI direction (+DI vs -DI)
        """
        if "adx" not in df.columns:
            df = self.calculate(df)

        latest = df.iloc[-1]
        if pd.isna(latest.get("adx")):
            return 50.0  # Neutral

        adx = latest["adx"]
        di_plus = latest.get("adx_di_plus", 0) or 0
        di_minus = latest.get("adx_di_minus", 0) or 0

        # Score based on trend direction
        if di_plus > di_minus:
            # Bullish trend - score 50-100 based on ADX strength
            direction_factor = min(1.0, adx / 50)  # Normalize to 0-1
            score = 50 + (direction_factor * 50)
        elif di_minus > di_plus:
            # Bearish trend - score 0-50 based on ADX strength
            direction_factor = min(1.0, adx / 50)
            score = 50 - (direction_factor * 50)
        else:
            score = 50  # Neutral

        return max(0, min(100, score))
