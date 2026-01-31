"""Williams %R indicator."""

import pandas as pd
import pandas_ta as ta

from quant.factors.base import BaseFactor


class WilliamsR(BaseFactor):
    """
    Williams %R momentum indicator.

    Williams %R shows the level of the close relative to the highest high
    over the lookback period.
    - Range: -100 to 0
    - %R > -20: Overbought
    - %R < -80: Oversold

    Similar to Stochastic but inverted and without smoothing.
    """

    def __init__(
        self,
        period: int = 14,
        overbought: float = -20.0,
        oversold: float = -80.0,
    ):
        """
        Initialize Williams %R indicator.

        Args:
            period: Lookback period
            overbought: Overbought threshold (closer to 0)
            oversold: Oversold threshold (closer to -100)
        """
        super().__init__(name="WilliamsR")
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Williams %R values."""
        self._validate_ohlcv(df)
        result = df.copy()

        result["williams_r"] = ta.willr(
            result["high"],
            result["low"],
            result["close"],
            length=self.period,
        )

        return result

    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on Williams %R.

        Returns:
            1 when %R crosses above oversold level (buy)
            -1 when %R crosses below overbought level (sell)
            0 otherwise (hold)
        """
        if "williams_r" not in df.columns:
            df = self.calculate(df)

        signals = pd.Series(0, index=df.index)

        willr = df["williams_r"]
        willr_prev = willr.shift(1)

        # Buy signal: %R crosses above oversold level
        buy_condition = (willr > self.oversold) & (willr_prev <= self.oversold)
        signals[buy_condition] = 1

        # Sell signal: %R crosses below overbought level
        sell_condition = (willr < self.overbought) & (willr_prev >= self.overbought)
        signals[sell_condition] = -1

        return signals

    def get_momentum_score(self, df: pd.DataFrame) -> float:
        """
        Calculate momentum score from Williams %R (0-100).

        Score is based on %R position in range [-100, 0].
        """
        if "williams_r" not in df.columns:
            df = self.calculate(df)

        latest = df.iloc[-1]
        if pd.isna(latest.get("williams_r")):
            return 50.0  # Neutral

        willr = latest["williams_r"]

        # Normalize from [-100, 0] to [0, 100]
        # -100 (oversold) = 0, 0 (overbought) = 100
        # Invert to make higher score = more bullish
        # When oversold (-100), it's actually bullish potential (high score)
        # When overbought (0), it's bearish potential (low score)
        # So we DON'T invert: oversold = low score (potential to buy)
        normalized = (willr + 100)  # Maps -100->0, 0->100
        return max(0, min(100, normalized))
