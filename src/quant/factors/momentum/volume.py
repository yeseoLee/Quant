"""Volume-based momentum indicator."""

import pandas as pd
import pandas_ta as ta

from quant.factors.base import BaseFactor


class VolumeMA(BaseFactor):
    """
    Volume Moving Average momentum indicator.

    Compares current volume to its moving average to identify
    unusual trading activity.
    - Volume > MA * threshold: High volume (potential breakout signal)
    - Volume < MA / threshold: Low volume (potential consolidation)
    """

    def __init__(
        self,
        period: int = 20,
        threshold: float = 1.5,
    ):
        """
        Initialize Volume MA indicator.

        Args:
            period: Lookback period for volume moving average
            threshold: Multiplier for volume breakout detection
        """
        super().__init__(name="VolumeMA")
        self.period = period
        self.threshold = threshold

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Volume MA values."""
        self._validate_ohlcv(df)
        result = df.copy()

        # Calculate volume moving average
        result["volume_ma"] = ta.sma(result["volume"], length=self.period)

        # Calculate volume ratio (current volume / MA)
        result["volume_ratio"] = result["volume"] / result["volume_ma"]

        return result

    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on Volume MA.

        Returns:
            1 when volume spikes above threshold with price increase (buy)
            -1 when volume spikes above threshold with price decrease (sell)
            0 otherwise (hold)
        """
        if "volume_ratio" not in df.columns:
            df = self.calculate(df)

        signals = pd.Series(0, index=df.index)

        # Price change
        price_up = df["close"] > df["close"].shift(1)
        price_down = df["close"] < df["close"].shift(1)

        # High volume condition
        high_volume = df["volume_ratio"] > self.threshold

        # Buy signal: High volume with price increase
        signals[high_volume & price_up] = 1

        # Sell signal: High volume with price decrease
        signals[high_volume & price_down] = -1

        return signals


class OBV(BaseFactor):
    """
    On-Balance Volume (OBV) indicator.

    OBV is a cumulative indicator that adds volume on up days
    and subtracts volume on down days.
    - Rising OBV confirms uptrend
    - Falling OBV confirms downtrend
    - Divergence between price and OBV signals potential reversal
    """

    def __init__(
        self,
        signal_period: int = 20,
    ):
        """
        Initialize OBV indicator.

        Args:
            signal_period: Period for OBV signal line (moving average)
        """
        super().__init__(name="OBV")
        self.signal_period = signal_period

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate OBV values."""
        self._validate_ohlcv(df)
        result = df.copy()

        # Use pandas_ta for OBV calculation
        result["obv"] = ta.obv(result["close"], result["volume"])

        # Calculate OBV signal line (moving average)
        result["obv_signal"] = ta.sma(result["obv"], length=self.signal_period)

        return result

    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on OBV crossovers.

        Returns:
            1 when OBV crosses above signal line (buy)
            -1 when OBV crosses below signal line (sell)
            0 otherwise (hold)
        """
        if "obv" not in df.columns or "obv_signal" not in df.columns:
            df = self.calculate(df)

        signals = pd.Series(0, index=df.index)

        # Buy signal: OBV crosses above signal line
        signals[
            (df["obv"] > df["obv_signal"]) & (df["obv"].shift(1) <= df["obv_signal"].shift(1))
        ] = 1

        # Sell signal: OBV crosses below signal line
        signals[
            (df["obv"] < df["obv_signal"]) & (df["obv"].shift(1) >= df["obv_signal"].shift(1))
        ] = -1

        return signals
