"""CCI (Commodity Channel Index) indicator."""

import pandas as pd
import pandas_ta as ta

from quant.factors.base import BaseFactor


class CCI(BaseFactor):
    """
    Commodity Channel Index (CCI) momentum indicator.

    CCI measures price deviation from statistical mean.
    - CCI > 100: Overbought / Strong uptrend
    - CCI < -100: Oversold / Strong downtrend
    - CCI crossing zero: Trend change

    Can identify:
    - New trends
    - Overbought/oversold conditions
    - Divergences
    """

    def __init__(
        self,
        period: int = 20,
        overbought: float = 100.0,
        oversold: float = -100.0,
    ):
        """
        Initialize CCI indicator.

        Args:
            period: Lookback period for CCI calculation
            overbought: Overbought threshold
            oversold: Oversold threshold
        """
        super().__init__(name="CCI")
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate CCI values."""
        self._validate_ohlcv(df)
        result = df.copy()

        result["cci"] = ta.cci(
            result["high"],
            result["low"],
            result["close"],
            length=self.period,
        )

        return result

    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on CCI.

        Returns:
            1 when CCI crosses above oversold level (buy)
            -1 when CCI crosses below overbought level (sell)
            0 otherwise (hold)
        """
        if "cci" not in df.columns:
            df = self.calculate(df)

        signals = pd.Series(0, index=df.index)

        cci = df["cci"]
        cci_prev = cci.shift(1)

        # Buy signal: CCI crosses above oversold level
        buy_condition = (cci > self.oversold) & (cci_prev <= self.oversold)
        signals[buy_condition] = 1

        # Sell signal: CCI crosses below overbought level
        sell_condition = (cci < self.overbought) & (cci_prev >= self.overbought)
        signals[sell_condition] = -1

        return signals

    def get_momentum_score(self, df: pd.DataFrame) -> float:
        """
        Calculate momentum score from CCI (0-100).

        Score is based on CCI position in range [-200, 200].
        """
        if "cci" not in df.columns:
            df = self.calculate(df)

        latest = df.iloc[-1]
        if pd.isna(latest.get("cci")):
            return 50.0  # Neutral

        cci = latest["cci"]

        # Normalize CCI from [-200, 200] to [0, 100]
        # CCI can go beyond these bounds, so we clip
        normalized = (cci + 200) / 400 * 100
        return max(0, min(100, normalized))
