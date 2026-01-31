"""MFI (Money Flow Index) indicator."""

import pandas as pd
import pandas_ta as ta

from quant.factors.base import BaseFactor


class MFI(BaseFactor):
    """
    Money Flow Index (MFI) momentum indicator.

    MFI is a volume-weighted RSI that incorporates volume data.
    - Range: 0 to 100
    - MFI > 80: Overbought
    - MFI < 20: Oversold

    More reliable than RSI as it includes volume confirmation.
    """

    def __init__(
        self,
        period: int = 14,
        overbought: float = 80.0,
        oversold: float = 20.0,
    ):
        """
        Initialize MFI indicator.

        Args:
            period: Lookback period for MFI calculation
            overbought: Overbought threshold
            oversold: Oversold threshold
        """
        super().__init__(name="MFI")
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate MFI values."""
        self._validate_ohlcv(df)
        result = df.copy()

        result["mfi"] = ta.mfi(
            result["high"],
            result["low"],
            result["close"],
            result["volume"],
            length=self.period,
        )

        return result

    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on MFI.

        Returns:
            1 when MFI crosses above oversold level (buy)
            -1 when MFI crosses below overbought level (sell)
            0 otherwise (hold)
        """
        if "mfi" not in df.columns:
            df = self.calculate(df)

        signals = pd.Series(0, index=df.index)

        mfi = df["mfi"]
        mfi_prev = mfi.shift(1)

        # Buy signal: MFI crosses above oversold level
        buy_condition = (mfi > self.oversold) & (mfi_prev <= self.oversold)
        signals[buy_condition] = 1

        # Sell signal: MFI crosses below overbought level
        sell_condition = (mfi < self.overbought) & (mfi_prev >= self.overbought)
        signals[sell_condition] = -1

        return signals

    def get_momentum_score(self, df: pd.DataFrame) -> float:
        """
        Calculate momentum score from MFI (0-100).

        MFI is already in range 0-100, so we use it directly.
        """
        if "mfi" not in df.columns:
            df = self.calculate(df)

        latest = df.iloc[-1]
        if pd.isna(latest.get("mfi")):
            return 50.0  # Neutral

        mfi = latest["mfi"]
        return max(0, min(100, mfi))
