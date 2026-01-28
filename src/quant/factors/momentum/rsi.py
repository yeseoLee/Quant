"""RSI (Relative Strength Index) indicator."""

import pandas as pd
import pandas_ta as ta

from quant.factors.base import BaseFactor


class RSI(BaseFactor):
    """
    Relative Strength Index (RSI) momentum indicator.

    RSI measures the speed and magnitude of price movements.
    - RSI > 70: Overbought (potential sell signal)
    - RSI < 30: Oversold (potential buy signal)
    """

    def __init__(
        self,
        period: int = 14,
        overbought: float = 70.0,
        oversold: float = 30.0,
    ):
        """
        Initialize RSI indicator.

        Args:
            period: Lookback period for RSI calculation
            overbought: Threshold for overbought condition
            oversold: Threshold for oversold condition
        """
        super().__init__(name="RSI")
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI values."""
        self._validate_ohlcv(df)
        result = df.copy()

        # Use pandas_ta for RSI calculation
        result["rsi"] = ta.rsi(result["close"], length=self.period)

        return result

    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on RSI.

        Returns:
            1 when RSI crosses above oversold (buy)
            -1 when RSI crosses below overbought (sell)
            0 otherwise (hold)
        """
        if "rsi" not in df.columns:
            df = self.calculate(df)

        signals = pd.Series(0, index=df.index)

        # Buy signal: RSI crosses above oversold level
        signals[(df["rsi"] > self.oversold) & (df["rsi"].shift(1) <= self.oversold)] = 1

        # Sell signal: RSI crosses below overbought level
        signals[(df["rsi"] < self.overbought) & (df["rsi"].shift(1) >= self.overbought)] = -1

        return signals
