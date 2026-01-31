"""
Momentum Factor Score Calculator.

Combines multiple technical indicators into a single composite momentum score.
"""

from dataclasses import dataclass

import pandas as pd

from quant.factors.momentum import (
    ADX,
    CCI,
    MACD,
    MFI,
    OBV,
    ROC,
    RSI,
    BollingerBands,
    Stochastic,
    VolumeMA,
    WilliamsR,
)


@dataclass
class IndicatorWeight:
    """Weight configuration for an indicator."""

    name: str
    weight: float
    category: str  # 'trend', 'momentum', 'volume'


class MomentumFactor:
    """
    Momentum Factor Score Calculator.

    Combines multiple technical indicators into a single normalized score (0-100).
    Each indicator contributes a weighted score based on its category and importance.

    Categories:
    - Trend: RSI, MACD, ADX, ROC
    - Oscillator: Stochastic, CCI, Williams %R, BB %B
    - Volume: MFI, OBV, VolumeMA

    Score interpretation:
    - 80-100: Very Strong Bullish Momentum
    - 60-80: Bullish Momentum
    - 40-60: Neutral
    - 20-40: Bearish Momentum
    - 0-20: Very Strong Bearish Momentum
    """

    # Default indicator weights (sum should be 1.0 or will be normalized)
    DEFAULT_WEIGHTS = [
        # Trend indicators (40% total)
        IndicatorWeight("RSI", 0.12, "trend"),
        IndicatorWeight("MACD", 0.10, "trend"),
        IndicatorWeight("ADX", 0.10, "trend"),
        IndicatorWeight("ROC", 0.08, "trend"),
        # Oscillator indicators (35% total)
        IndicatorWeight("Stochastic", 0.10, "oscillator"),
        IndicatorWeight("CCI", 0.08, "oscillator"),
        IndicatorWeight("WilliamsR", 0.08, "oscillator"),
        IndicatorWeight("BollingerBands", 0.09, "oscillator"),
        # Volume indicators (25% total)
        IndicatorWeight("MFI", 0.10, "volume"),
        IndicatorWeight("OBV", 0.08, "volume"),
        IndicatorWeight("VolumeMA", 0.07, "volume"),
    ]

    def __init__(self, weights: list[IndicatorWeight] | None = None):
        """
        Initialize MomentumFactor calculator.

        Args:
            weights: Custom indicator weights. If None, uses default weights.
        """
        self.weights = weights or self.DEFAULT_WEIGHTS

        # Normalize weights to sum to 1.0
        total_weight = sum(w.weight for w in self.weights)
        if total_weight != 1.0:
            for w in self.weights:
                w.weight = w.weight / total_weight

        # Initialize indicators
        self._indicators = {
            "RSI": RSI(),
            "MACD": MACD(),
            "ADX": ADX(),
            "ROC": ROC(),
            "Stochastic": Stochastic(),
            "CCI": CCI(),
            "WilliamsR": WilliamsR(),
            "BollingerBands": BollingerBands(),
            "MFI": MFI(),
            "OBV": OBV(),
            "VolumeMA": VolumeMA(),
        }

    def calculate(self, df: pd.DataFrame) -> dict:
        """
        Calculate momentum factor score and individual indicator scores.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Dict with:
            - total_score: Weighted average score (0-100)
            - category_scores: Scores by category (trend, oscillator, volume)
            - indicator_scores: Individual indicator scores
            - signal: Trading signal based on score
            - state: Momentum state description
        """
        if df.empty or len(df) < 30:
            return self._empty_result()

        indicator_scores = {}
        category_totals = {"trend": 0.0, "oscillator": 0.0, "volume": 0.0}
        category_weights = {"trend": 0.0, "oscillator": 0.0, "volume": 0.0}

        total_score = 0.0

        for weight_config in self.weights:
            name = weight_config.name
            weight = weight_config.weight
            category = weight_config.category

            try:
                indicator = self._indicators.get(name)
                if indicator is None:
                    continue

                # Calculate indicator on dataframe
                df_with_indicator = indicator.calculate(df)

                # Get momentum score
                score = indicator.get_momentum_score(df_with_indicator)
                indicator_scores[name] = round(score, 2)

                # Add to weighted total
                total_score += score * weight

                # Track category scores
                category_totals[category] += score * weight
                category_weights[category] += weight

            except Exception:
                # If indicator fails, use neutral score
                indicator_scores[name] = 50.0
                total_score += 50.0 * weight
                category_totals[category] += 50.0 * weight
                category_weights[category] += weight

        # Calculate category average scores
        category_scores = {}
        for category in ["trend", "oscillator", "volume"]:
            if category_weights[category] > 0:
                category_scores[category] = round(
                    category_totals[category] / category_weights[category], 2
                )
            else:
                category_scores[category] = 50.0

        # Determine signal and state
        total_score = round(total_score, 2)
        signal, state = self._get_signal_and_state(total_score)

        return {
            "total_score": total_score,
            "category_scores": category_scores,
            "indicator_scores": indicator_scores,
            "signal": signal,
            "state": state,
        }

    def _get_signal_and_state(self, score: float) -> tuple[int, str]:
        """
        Determine trading signal and momentum state from score.

        Returns:
            Tuple of (signal, state)
            signal: 1 (buy), -1 (sell), 0 (hold)
            state: Description of momentum state
        """
        if score >= 80:
            return 1, "VERY_STRONG_BULLISH"
        elif score >= 65:
            return 1, "BULLISH"
        elif score >= 55:
            return 0, "SLIGHTLY_BULLISH"
        elif score >= 45:
            return 0, "NEUTRAL"
        elif score >= 35:
            return 0, "SLIGHTLY_BEARISH"
        elif score >= 20:
            return -1, "BEARISH"
        else:
            return -1, "VERY_STRONG_BEARISH"

    def _empty_result(self) -> dict:
        """Return empty result for insufficient data."""
        return {
            "total_score": None,
            "category_scores": {
                "trend": None,
                "oscillator": None,
                "volume": None,
            },
            "indicator_scores": {},
            "signal": 0,
            "state": "INSUFFICIENT_DATA",
        }

    def get_score_description(self, score: float) -> str:
        """Get human-readable description of momentum score."""
        if score is None:
            return "데이터 부족"
        elif score >= 80:
            return "매우 강한 상승 모멘텀"
        elif score >= 65:
            return "상승 모멘텀"
        elif score >= 55:
            return "약한 상승 모멘텀"
        elif score >= 45:
            return "중립"
        elif score >= 35:
            return "약한 하락 모멘텀"
        elif score >= 20:
            return "하락 모멘텀"
        else:
            return "매우 강한 하락 모멘텀"
