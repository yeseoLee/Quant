"""
LPPL (Log-Periodic Power Law) Model for Bubble Detection.

Based on the work of Didier Sornette and colleagues.
Reference: Sornette, D. (2003). "Why Stock Markets Crash: Critical Events in Complex Financial Systems"
"""

import warnings
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize


class LPPL:
    """
    Log-Periodic Power Law model for detecting financial bubbles.

    The LPPL model equation:
    ln(p(t)) = A + B * (tc - t)^m + C * (tc - t)^m * cos(ω * ln(tc - t) + φ)

    Where:
    - p(t): price at time t
    - tc: critical time (predicted crash/peak time)
    - A: log price at critical time
    - B: amplitude (typically B < 0 for bubble)
    - C: amplitude of log-periodic oscillations
    - m: power law exponent (0 < m < 1)
    - ω: angular frequency of oscillations
    - φ: phase shift
    """

    def __init__(self):
        """Initialize LPPL model."""
        self.params: Optional[Dict[str, float]] = None
        self.fit_success = False
        self.observations = 0

    @staticmethod
    def lppl_function(t: np.ndarray, tc: float, A: float, B: float, C: float,
                      m: float, omega: float, phi: float) -> np.ndarray:
        """
        LPPL model equation.

        Args:
            t: Time array
            tc: Critical time
            A: Log price at critical time
            B: Amplitude
            C: Oscillation amplitude
            m: Power law exponent
            omega: Angular frequency
            phi: Phase shift

        Returns:
            Predicted log prices
        """
        dt = tc - t
        # Avoid numerical issues
        dt = np.maximum(dt, 1e-10)

        return A + B * (dt ** m) + C * (dt ** m) * np.cos(omega * np.log(dt) + phi)

    def fit(self, prices: pd.Series, max_iter: int = 5000) -> Dict[str, float]:
        """
        Fit LPPL model to price data using differential evolution.

        Args:
            prices: Time series of prices (index should be datetime)
            max_iter: Maximum iterations for optimization

        Returns:
            Dictionary of fitted parameters
        """
        # Prepare data
        t = np.arange(len(prices))
        log_prices = np.log(prices.values)

        # Remove NaN values
        valid_idx = ~np.isnan(log_prices)
        t = t[valid_idx]
        log_prices = log_prices[valid_idx]

        if len(t) < 30:
            raise ValueError("Need at least 30 data points for LPPL fitting")

        self.observations = len(t)

        # Dynamic parameter bounds based on data
        price_range = log_prices.max() - log_prices.min()

        tc_min = t[-1] + 5
        tc_max = min(t[-1] + 252 * 2, t[-1] + len(t))  # Up to 2 years or data length

        bounds = [
            (tc_min, tc_max),  # tc: critical time
            (log_prices.min() - price_range, log_prices.max() + price_range),  # A
            (-2, 0),  # B (negative for bubble)
            (-1, 1),  # C
            (0.1, 0.9),  # m
            (2, 25),  # omega
            (-np.pi, np.pi),  # phi
        ]

        # Objective function to minimize
        def objective(params):
            tc, A, B, C, m, omega, phi = params
            try:
                predicted = self.lppl_function(t, tc, A, B, C, m, omega, phi)
                residuals = log_prices - predicted
                mse = np.sum(residuals ** 2) / len(residuals)
                return mse
            except (RuntimeWarning, FloatingPointError, ValueError):
                return 1e10

        # Suppress warnings during optimization
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # Use differential evolution for global optimization
            result = differential_evolution(
                objective,
                bounds,
                maxiter=max_iter,
                seed=42,
                workers=1,
                polish=True,
                atol=1e-4,  # More relaxed tolerance
                tol=1e-3,   # More relaxed tolerance
                strategy='best1bin',
                popsize=15,
                mutation=(0.5, 1.5),
                recombination=0.7,
            )

        # More lenient success criteria
        normalized_error = result.fun

        if result.success or normalized_error < 0.1:  # Accept if MSE < 0.1
            self.fit_success = True
            tc, A, B, C, m, omega, phi = result.x

            self.params = {
                "tc": tc,
                "A": A,
                "B": B,
                "C": C,
                "m": m,
                "omega": omega,
                "phi": phi,
                "residual_error": normalized_error,
            }

            return self.params
        else:
            self.fit_success = False
            raise RuntimeError(
                f"LPPL fitting failed: {result.message}. "
                f"Error: {normalized_error:.4f}. "
                f"Try with more data or different time period."
            )

    def predict(self, t: np.ndarray) -> np.ndarray:
        """
        Predict log prices at given time points.

        Args:
            t: Time array

        Returns:
            Predicted log prices
        """
        if self.params is None:
            raise ValueError("Model not fitted yet. Call fit() first.")

        return self.lppl_function(
            t,
            self.params["tc"],
            self.params["A"],
            self.params["B"],
            self.params["C"],
            self.params["m"],
            self.params["omega"],
            self.params["phi"],
        )

    def diagnose_bubble(
        self, prices: pd.Series, current_index: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Diagnose if there's a bubble using LPPL indicators.

        Args:
            prices: Price time series
            current_index: Current time index (defaults to last index)

        Returns:
            Dictionary with bubble diagnosis results
        """
        if self.params is None:
            raise ValueError("Model not fitted yet. Call fit() first.")

        if current_index is None:
            current_index = len(prices) - 1

        tc = self.params["tc"]
        B = self.params["B"]
        m = self.params["m"]
        omega = self.params["omega"]

        # Calculate days until critical time
        days_to_tc = tc - current_index

        # Bubble indicators (convert to native Python bool for JSON serialization)
        indicators = {
            # Critical time is in reasonable future (5 days to 2 years)
            "tc_in_range": bool(5 <= days_to_tc <= 504),
            # B should be negative for bubble
            "B_negative": bool(B < 0),
            # m should be in valid range
            "m_valid": bool(0.1 <= m <= 0.9),
            # omega should indicate oscillations
            "omega_valid": bool(2 <= omega <= 25),
        }

        # Calculate bubble confidence score (0-100)
        confidence = float(sum(indicators.values()) / len(indicators) * 100)

        # Classify bubble state
        if confidence >= 75 and days_to_tc < 60:
            state = "CRITICAL"
            message = "강한 버블 신호 - 임박한 조정 가능성"
        elif confidence >= 75:
            state = "WARNING"
            message = "버블 경고 - 주의 필요"
        elif confidence >= 50:
            state = "WATCH"
            message = "버블 가능성 있음 - 모니터링 필요"
        else:
            state = "NORMAL"
            message = "정상 범위"

        # Calculate expected crash date
        crash_date = None
        if isinstance(prices.index, pd.DatetimeIndex) and days_to_tc > 0:
            crash_date = prices.index[-1] + pd.Timedelta(days=int(days_to_tc))

        return {
            "state": str(state),
            "confidence": float(round(confidence, 2)),
            "message": str(message),
            "days_to_critical": float(round(days_to_tc, 1)),
            "critical_date": crash_date.strftime("%Y-%m-%d") if crash_date else None,
            "indicators": indicators,
            "parameters": {
                "tc": float(round(tc, 2)),
                "A": float(round(self.params["A"], 4)),
                "B": float(round(B, 4)),
                "C": float(round(self.params["C"], 4)),
                "m": float(round(m, 4)),
                "omega": float(round(omega, 4)),
                "phi": float(round(self.params["phi"], 4)),
            },
            "fit_quality": {
                "residual_error": float(round(self.params["residual_error"], 4)),
                "observations": int(self.observations),
            },
        }

    def get_fitted_prices(self, prices: pd.Series) -> pd.Series:
        """
        Get fitted prices for the original data.

        Args:
            prices: Original price series

        Returns:
            Series of fitted prices
        """
        if self.params is None:
            raise ValueError("Model not fitted yet. Call fit() first.")

        t = np.arange(len(prices))
        log_fitted = self.predict(t)
        fitted_prices = np.exp(log_fitted)

        return pd.Series(fitted_prices, index=prices.index)

    def forecast(
        self, prices: pd.Series, forecast_days: int = 60
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Forecast future prices using fitted LPPL model.

        Args:
            prices: Original price series
            forecast_days: Number of days to forecast

        Returns:
            Tuple of (historical fitted prices, forecasted prices)
        """
        if self.params is None:
            raise ValueError("Model not fitted yet. Call fit() first.")

        # Fitted prices
        fitted = self.get_fitted_prices(prices)

        # Forecast
        last_t = len(prices) - 1
        future_t = np.arange(last_t + 1, last_t + 1 + forecast_days)

        # Ensure we don't go past tc
        tc = self.params["tc"]
        future_t = future_t[future_t < tc - 0.1]  # Stop 0.1 days before tc

        if len(future_t) > 0:
            log_forecast = self.predict(future_t)
            forecast_prices = np.exp(log_forecast)

            # Create date index for forecast
            if isinstance(prices.index, pd.DatetimeIndex):
                forecast_index = pd.date_range(
                    start=prices.index[-1] + pd.Timedelta(days=1),
                    periods=len(future_t),
                    freq="D",
                )
            else:
                forecast_index = range(len(prices), len(prices) + len(future_t))

            forecast_series = pd.Series(forecast_prices, index=forecast_index)
        else:
            forecast_series = pd.Series(dtype=float)

        return fitted, forecast_series
