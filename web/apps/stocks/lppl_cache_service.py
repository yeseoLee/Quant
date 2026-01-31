"""LPPL Cache Service for storing and retrieving LPPL analysis results."""

import time
from datetime import date

import pandas as pd

from quant.models import LPPL

from .models import LPPLAnalysisResult, LPPLWindowResult, StockCache


class LPPLCacheService:
    """Service for caching LPPL analysis results in the database."""

    DEFAULT_MIN_WINDOW = 125
    DEFAULT_MAX_WINDOW = 750
    DEFAULT_STEP = 5  # Changed from 25 to 5 for finer granularity

    def get_or_compute(
        self,
        symbol: str,
        prices_df: pd.DataFrame,
        step: int | None = None,
        min_window: int | None = None,
        max_window: int | None = None,
        force_recompute: bool = False,
    ) -> dict:
        """
        Get cached LPPL result or compute new one.

        Args:
            symbol: Stock ticker symbol
            prices_df: DataFrame with OHLCV data (must have 'close' column)
            step: Window step size (default: 5)
            min_window: Minimum window size (default: 125)
            max_window: Maximum window size (default: 750)
            force_recompute: If True, bypass cache and recompute

        Returns:
            LPPL analysis result dict with 'cached' flag
        """
        step = step or self.DEFAULT_STEP
        min_window = min_window or self.DEFAULT_MIN_WINDOW
        max_window = max_window or self.DEFAULT_MAX_WINDOW

        # Get the latest price date from the data
        current_date = prices_df.index[-1].date()
        if isinstance(current_date, pd.Timestamp):
            current_date = current_date.date()

        # Try to get valid cache
        if not force_recompute:
            cached_result = self._get_valid_cache(symbol, current_date, step)
            if cached_result:
                return self._format_cached_result(cached_result, cached=True)

        # Compute new result
        start_time = time.time()
        result = self._compute_lppl(prices_df, min_window, max_window, step)
        computation_time = time.time() - start_time

        # Save to database
        self._save_result(symbol, current_date, result, step, min_window, max_window, computation_time)

        # Format response
        formatted = self._format_computed_result(result)
        formatted["cached"] = False
        formatted["computation_time"] = round(computation_time, 2)

        return formatted

    def _get_valid_cache(
        self,
        symbol: str,
        current_date: date,
        step: int,
    ) -> LPPLAnalysisResult | None:
        """
        Get valid cached result for the given symbol and date.

        Cache is valid if analysis_date matches current price date.
        """
        try:
            return LPPLAnalysisResult.objects.select_related("stock").prefetch_related(
                "window_results"
            ).get(
                stock_id=symbol,
                analysis_date=current_date,
                step=step,
            )
        except LPPLAnalysisResult.DoesNotExist:
            return None

    def _compute_lppl(
        self,
        prices_df: pd.DataFrame,
        min_window: int,
        max_window: int,
        step: int,
    ) -> dict:
        """Compute LPPL multi-window analysis."""
        prices = prices_df["close"]
        lppl = LPPL()
        return lppl.fit_multi_window(
            prices,
            min_window=min_window,
            max_window=max_window,
            step=step,
            max_iter=1500,
        )

    def _save_result(
        self,
        symbol: str,
        analysis_date: date,
        result: dict,
        step: int,
        min_window: int,
        max_window: int,
        computation_time: float,
    ) -> LPPLAnalysisResult:
        """Save LPPL result to database."""
        # Ensure stock exists
        stock, _ = StockCache.objects.get_or_create(
            symbol=symbol,
            defaults={"name": symbol, "market": "KOSPI"},
        )

        # Delete old cache for same date and step
        LPPLAnalysisResult.objects.filter(
            stock=stock,
            analysis_date=analysis_date,
            step=step,
        ).delete()

        # Create master record
        stats = result["statistics"]
        analysis = LPPLAnalysisResult.objects.create(
            stock=stock,
            min_window=min_window,
            max_window=max_window,
            step=step,
            analysis_date=analysis_date,
            confidence_indicator=result["confidence_indicator"],
            state=result["state"],
            message=result["message"],
            total_windows=stats["total_windows"],
            successful_fits=stats["successful_fits"],
            bubble_windows=stats["bubble_windows"],
            success_rate=stats["success_rate"],
            computation_time=computation_time,
        )

        # Create window result records
        window_records = []
        for window_result in result["detailed_results"]:
            window_record = LPPLWindowResult(
                analysis=analysis,
                window_size=window_result["window_size"],
                success=window_result["success"],
                is_bubble=window_result.get("is_bubble", False),
            )

            if window_result["success"] and "params" in window_result:
                params = window_result["params"]
                window_record.param_tc = params.get("tc")
                window_record.param_b = params.get("B")
                window_record.param_m = params.get("m")
                window_record.param_omega = params.get("omega")
                window_record.residual_error = params.get("error")
            elif "error" in window_result:
                window_record.error_message = window_result["error"]

            window_records.append(window_record)

        LPPLWindowResult.objects.bulk_create(window_records)

        return analysis

    def _format_cached_result(self, analysis: LPPLAnalysisResult, cached: bool = True) -> dict:
        """Format cached result for API response."""
        # Build detailed results from window records
        detailed_results = []
        for window in analysis.window_results.all():
            window_dict = {
                "window_size": window.window_size,
                "success": window.success,
                "is_bubble": window.is_bubble,
            }

            if window.success:
                window_dict["params"] = {
                    "tc": window.param_tc,
                    "B": window.param_b,
                    "m": window.param_m,
                    "omega": window.param_omega,
                    "error": window.residual_error,
                }
            elif window.error_message:
                window_dict["error"] = window.error_message

            detailed_results.append(window_dict)

        return {
            "confidence_indicator": analysis.confidence_indicator,
            "state": analysis.state,
            "message": analysis.message,
            "statistics": {
                "total_windows": analysis.total_windows,
                "successful_fits": analysis.successful_fits,
                "bubble_windows": analysis.bubble_windows,
                "success_rate": analysis.success_rate,
            },
            "window_range": {
                "min": analysis.min_window,
                "max": analysis.max_window,
                "step": analysis.step,
            },
            "detailed_results": detailed_results,
            "cached": cached,
            "computation_time": analysis.computation_time,
            "cached_at": analysis.created_at.isoformat(),
        }

    def _format_computed_result(self, result: dict) -> dict:
        """Format newly computed result for API response."""
        return {
            "confidence_indicator": result["confidence_indicator"],
            "state": result["state"],
            "message": result["message"],
            "statistics": result["statistics"],
            "window_range": result["window_range"],
            "detailed_results": result["detailed_results"],
        }

    def invalidate_cache(self, symbol: str) -> int:
        """
        Invalidate all cached LPPL results for a symbol.

        Returns:
            Number of deleted records
        """
        deleted_count, _ = LPPLAnalysisResult.objects.filter(stock_id=symbol).delete()
        return deleted_count

    def get_cache_info(self, symbol: str) -> dict | None:
        """
        Get cache information for a symbol.

        Returns:
            Dict with cache info or None if no cache exists
        """
        try:
            latest = LPPLAnalysisResult.objects.filter(stock_id=symbol).latest("analysis_date")
            return {
                "analysis_date": latest.analysis_date.isoformat(),
                "state": latest.state,
                "confidence_indicator": latest.confidence_indicator,
                "step": latest.step,
                "total_windows": latest.total_windows,
                "computation_time": latest.computation_time,
                "created_at": latest.created_at.isoformat(),
            }
        except LPPLAnalysisResult.DoesNotExist:
            return None
