"""Stochastic Oscillator indicator."""

import pandas as pd
import pandas_ta as ta

from quant.factors.base import BaseFactor


class Stochastic(BaseFactor):
    """
    Stochastic Oscillator momentum indicator.

    Compares closing price to price range over a period.
    - %K: Fast stochastic line
    - %D: Slow stochastic line (SMA of %K)

    Signals:
    - %K > 80: Overbought
    - %K < 20: Oversold
    - %K crosses above %D: Buy signal
    - %K crosses below %D: Sell signal
    """

    def __init__(
        self,
        k_period: int = 14,
        d_period: int = 3,
        smooth_k: int = 3,
        overbought: float = 80.0,
        oversold: float = 20.0,
    ):
        """
        Initialize Stochastic Oscillator.

        Args:
            k_period: Lookback period for %K
            d_period: Smoothing period for %D
            smooth_k: Smoothing period for %K
            overbought: Overbought threshold
            oversold: Oversold threshold
        """
        super().__init__(name="Stochastic")
        self.k_period = k_period
        self.d_period = d_period
        self.smooth_k = smooth_k
        self.overbought = overbought
        self.oversold = oversold

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Stochastic Oscillator values."""
        self._validate_ohlcv(df)
        result = df.copy()

        # Use pandas_ta for Stochastic calculation
        stoch = ta.stoch(
            result["high"],
            result["low"],
            result["close"],
            k=self.k_period,
            d=self.d_period,
            smooth_k=self.smooth_k,
        )

        if stoch is not None:
            result["stoch_k"] = stoch.iloc[:, 0]  # %K
            result["stoch_d"] = stoch.iloc[:, 1]  # %D

        return result

    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on Stochastic Oscillator.

        Uses crossover signals in oversold/overbought zones.

        Returns:
            1 when %K crosses above %D in oversold zone (buy)
            -1 when %K crosses below %D in overbought zone (sell)
            0 otherwise (hold)
        """
        if "stoch_k" not in df.columns:
            df = self.calculate(df)

        signals = pd.Series(0, index=df.index)

        k = df["stoch_k"]
        d = df["stoch_d"]
        k_prev = k.shift(1)
        d_prev = d.shift(1)

        # Buy signal: %K crosses above %D in oversold zone
        buy_condition = (k > d) & (k_prev <= d_prev) & (k < self.oversold)
        signals[buy_condition] = 1

        # Sell signal: %K crosses below %D in overbought zone
        sell_condition = (k < d) & (k_prev >= d_prev) & (k > self.overbought)
        signals[sell_condition] = -1

        return signals
