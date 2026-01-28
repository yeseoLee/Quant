"""Tests for factor calculations."""

import numpy as np
import pandas as pd
import pytest

from quant.factors.momentum import RSI, BollingerBands, Stochastic


@pytest.fixture
def sample_ohlcv():
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    n = 100
    dates = pd.date_range("2026-01-01", periods=n, freq="D")

    close = 100 + np.cumsum(np.random.randn(n) * 2)
    high = close + np.abs(np.random.randn(n))
    low = close - np.abs(np.random.randn(n))
    open_ = (high + low) / 2 + np.random.randn(n) * 0.5

    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.random.randint(1000000, 10000000, n),
        },
        index=dates,
    )


class TestRSI:
    def test_calculate(self, sample_ohlcv):
        rsi = RSI(period=14)
        result = rsi.calculate(sample_ohlcv)

        assert "rsi" in result.columns
        # RSI should be between 0 and 100
        valid_rsi = result["rsi"].dropna()
        assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()

    def test_signal(self, sample_ohlcv):
        rsi = RSI(period=14)
        result = rsi.calculate(sample_ohlcv)
        signals = rsi.get_signal(result)

        assert len(signals) == len(sample_ohlcv)
        # Signals should be -1, 0, or 1
        assert signals.isin([-1, 0, 1]).all()


class TestBollingerBands:
    def test_calculate(self, sample_ohlcv):
        bb = BollingerBands(period=20, std_dev=2.0)
        result = bb.calculate(sample_ohlcv)

        assert "bb_lower" in result.columns
        assert "bb_middle" in result.columns
        assert "bb_upper" in result.columns

        # Upper band should be above middle, middle above lower
        valid_idx = result["bb_middle"].dropna().index
        assert (result.loc[valid_idx, "bb_upper"] >= result.loc[valid_idx, "bb_middle"]).all()
        assert (result.loc[valid_idx, "bb_middle"] >= result.loc[valid_idx, "bb_lower"]).all()

    def test_signal(self, sample_ohlcv):
        bb = BollingerBands(period=20, std_dev=2.0)
        result = bb.calculate(sample_ohlcv)
        signals = bb.get_signal(result)

        assert len(signals) == len(sample_ohlcv)
        assert signals.isin([-1, 0, 1]).all()


class TestStochastic:
    def test_calculate(self, sample_ohlcv):
        stoch = Stochastic(k_period=14, d_period=3)
        result = stoch.calculate(sample_ohlcv)

        assert "stoch_k" in result.columns
        assert "stoch_d" in result.columns

        # Stochastic should be between 0 and 100
        valid_k = result["stoch_k"].dropna()
        assert (valid_k >= 0).all() and (valid_k <= 100).all()

    def test_signal(self, sample_ohlcv):
        stoch = Stochastic(k_period=14, d_period=3)
        result = stoch.calculate(sample_ohlcv)
        signals = stoch.get_signal(result)

        assert len(signals) == len(sample_ohlcv)
        assert signals.isin([-1, 0, 1]).all()
