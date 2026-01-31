"""Service layer wrapping the quant library for web application."""

from datetime import date, datetime, timedelta

import pandas as pd

from quant.data import DataFetcher, Kospi200
from quant.factors import RSI, BollingerBands, MomentumFactor, Stochastic
from quant.models import LPPL

from .lppl_cache_service import LPPLCacheService
from .models import MomentumFactorScore, StockCache, StockPrice
from .sync_service import StockSyncService


class StockService:
    """Service class for stock data operations."""

    def __init__(self):
        self._fetcher = DataFetcher()
        self._kospi200 = Kospi200()
        self._sync_service = StockSyncService()
        self._lppl_cache = LPPLCacheService()
        self._factors = {
            "RSI": RSI,
            "BB": BollingerBands,
            "STOCH": Stochastic,
        }

    def get_stock_data(
        self,
        symbol: str,
        start_date: str | datetime | None = None,
        end_date: str | datetime | None = None,
    ) -> pd.DataFrame:
        """
        Get OHLCV data for a stock.

        First tries to get data from database, falls back to external API.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date (default: 1 year ago)
            end_date: End date (default: today)

        Returns:
            DataFrame with OHLCV data
        """
        # Try to get from database first
        if self._sync_service.has_stock_data(symbol):
            return self._get_stock_data_from_db(symbol, start_date, end_date)

        # Fall back to external API
        return self._fetcher.get_stock_data(symbol, start_date, end_date)

    def _get_stock_data_from_db(
        self,
        symbol: str,
        start_date: str | datetime | date | None = None,
        end_date: str | datetime | date | None = None,
    ) -> pd.DataFrame:
        """Get OHLCV data from database."""
        # Parse dates
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()

        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        elif isinstance(end_date, datetime):
            end_date = end_date.date()

        today = date.today()
        if start_date is None:
            start_date = today - timedelta(days=365)
        if end_date is None:
            end_date = today

        prices = StockPrice.objects.filter(
            stock_id=symbol,
            date__gte=start_date,
            date__lte=end_date,
        ).order_by("date")

        if not prices.exists():
            return pd.DataFrame()

        # Convert to DataFrame
        data = []
        for price in prices:
            data.append(
                {
                    "date": price.date,
                    "open": float(price.open),
                    "high": float(price.high),
                    "low": float(price.low),
                    "close": float(price.close),
                    "volume": price.volume,
                }
            )

        df = pd.DataFrame(data)
        df.set_index("date", inplace=True)
        df.index = pd.to_datetime(df.index)
        return df

    def get_ohlcv_json(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        """
        Get OHLCV data formatted for Lightweight Charts.

        Returns:
            List of dicts with time, open, high, low, close, volume
        """
        # If data exists in DB, use optimized query
        if self._sync_service.has_stock_data(symbol):
            return self._sync_service.get_stock_prices_from_db(symbol, start_date, end_date)

        # Fall back to external API
        df = self.get_stock_data(symbol, start_date, end_date)

        # Convert to the format expected by Lightweight Charts
        result = []
        for idx, row in df.iterrows():
            timestamp = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)
            result.append(
                {
                    "time": timestamp,
                    "open": float(row["open"]) if pd.notna(row["open"]) else None,
                    "high": float(row["high"]) if pd.notna(row["high"]) else None,
                    "low": float(row["low"]) if pd.notna(row["low"]) else None,
                    "close": float(row["close"]) if pd.notna(row["close"]) else None,
                    "volume": float(row["volume"]) if pd.notna(row.get("volume", 0)) else 0,
                }
            )
        return result

    def get_indicator_data(
        self,
        symbol: str,
        indicator: str,
        params: dict | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """
        Calculate indicator values for a stock.

        Args:
            symbol: Stock ticker symbol
            indicator: Indicator type (RSI, BB, STOCH)
            params: Indicator parameters
            start_date: Start date
            end_date: End date

        Returns:
            Dict with indicator data formatted for charting
        """
        if indicator not in self._factors:
            raise ValueError(f"Unknown indicator: {indicator}")

        df = self.get_stock_data(symbol, start_date, end_date)
        params = params or {}

        factor_class = self._factors[indicator]
        factor = factor_class(**params)
        df_with_indicator = factor.calculate(df)

        return self._format_indicator_data(df_with_indicator, indicator)

    def _format_indicator_data(self, df: pd.DataFrame, indicator: str) -> dict:
        """Format indicator data for frontend charting."""
        result = {"indicator": indicator, "data": {}}

        if indicator == "RSI":
            rsi_data = []
            for idx, row in df.iterrows():
                timestamp = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)
                if pd.notna(row.get("rsi")):
                    rsi_data.append({"time": timestamp, "value": float(row["rsi"])})
            result["data"]["rsi"] = rsi_data

        elif indicator == "BB":
            upper_data = []
            middle_data = []
            lower_data = []
            for idx, row in df.iterrows():
                timestamp = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)
                if pd.notna(row.get("bb_upper")):
                    upper_data.append({"time": timestamp, "value": float(row["bb_upper"])})
                    middle_data.append({"time": timestamp, "value": float(row["bb_middle"])})
                    lower_data.append({"time": timestamp, "value": float(row["bb_lower"])})
            result["data"]["bb_upper"] = upper_data
            result["data"]["bb_middle"] = middle_data
            result["data"]["bb_lower"] = lower_data

        elif indicator == "STOCH":
            k_data = []
            d_data = []
            for idx, row in df.iterrows():
                timestamp = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)
                if pd.notna(row.get("stoch_k")):
                    k_data.append({"time": timestamp, "value": float(row["stoch_k"])})
                    d_data.append({"time": timestamp, "value": float(row["stoch_d"])})
            result["data"]["stoch_k"] = k_data
            result["data"]["stoch_d"] = d_data

        return result

    def get_signals(
        self,
        symbol: str,
        indicator: str,
        params: dict | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        """
        Get trading signals for a stock.

        Returns:
            List of signal dicts with time, signal (1=buy, -1=sell), price
        """
        if indicator not in self._factors:
            raise ValueError(f"Unknown indicator: {indicator}")

        df = self.get_stock_data(symbol, start_date, end_date)
        params = params or {}

        factor_class = self._factors[indicator]
        factor = factor_class(**params)
        df_with_indicator = factor.calculate(df)
        signals = factor.get_signal(df_with_indicator)

        result = []
        for idx, signal in signals.items():
            if signal != 0:
                timestamp = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)
                price = float(df_with_indicator.loc[idx, "close"])
                result.append(
                    {
                        "time": timestamp,
                        "signal": int(signal),
                        "signal_type": "buy" if signal == 1 else "sell",
                        "price": price,
                    }
                )

        return result

    def get_kospi200_list(self) -> list[dict]:
        """
        Get list of KOSPI200 constituent stocks.

        First tries to get from database, falls back to external API.

        Returns:
            List of dicts with symbol, name, and other info
        """
        # Try database first
        stocks = StockCache.objects.filter(is_kospi200=True).order_by("symbol")
        if stocks.exists():
            return [{"symbol": s.symbol, "name": s.name} for s in stocks]

        # Fall back to external API
        df = self._kospi200.get_constituents()

        # Find the code and name columns
        code_col = None
        name_col = None

        for col in ["Code", "Symbol", "종목코드"]:
            if col in df.columns:
                code_col = col
                break

        for col in ["Name", "종목명", "회사명"]:
            if col in df.columns:
                name_col = col
                break

        if code_col is None:
            raise ValueError("Cannot find stock code column")

        result = []
        for _, row in df.iterrows():
            item = {
                "symbol": row[code_col],
                "name": row[name_col] if name_col else row[code_col],
            }
            result.append(item)

        return result

    def get_stock_info(self, symbol: str) -> dict | None:
        """
        Get information for a specific stock.

        Returns:
            Dict with stock info or None if not found
        """
        # Try database first
        try:
            stock = StockCache.objects.get(symbol=symbol)
            return {"symbol": stock.symbol, "name": stock.name}
        except StockCache.DoesNotExist:
            pass

        # Fall back to external API
        info = self._kospi200.get_stock_info(symbol)
        if info is None:
            return None

        # Find the name column
        name_col = None
        for col in ["Name", "종목명", "회사명"]:
            if col in info.index:
                name_col = col
                break

        return {
            "symbol": symbol,
            "name": info[name_col] if name_col else symbol,
        }

    def search_stocks(self, query: str) -> list[dict]:
        """
        Search stocks by symbol or name.

        Args:
            query: Search query

        Returns:
            List of matching stocks
        """
        stocks = self.get_kospi200_list()
        query_lower = query.lower()

        results = []
        for stock in stocks:
            if query_lower in stock["symbol"].lower() or query_lower in stock["name"].lower():
                results.append(stock)

        return results

    def run_screener(
        self,
        indicator: str,
        params: dict | None = None,
        signal_filter: int | None = None,
    ) -> list[dict]:
        """
        Run screener on KOSPI200 stocks.

        Args:
            indicator: Indicator to use (RSI, BB, STOCH)
            params: Indicator parameters
            signal_filter: Filter by signal (1=buy, -1=sell, None=all)

        Returns:
            List of stocks with their latest signals
        """
        if indicator not in self._factors:
            raise ValueError(f"Unknown indicator: {indicator}")

        stocks = self.get_kospi200_list()
        params = params or {}

        factor_class = self._factors[indicator]
        factor = factor_class(**params)

        results = []
        for stock in stocks:
            try:
                df = self.get_stock_data(stock["symbol"])
                if df.empty:
                    continue

                df_with_indicator = factor.calculate(df)
                signals = factor.get_signal(df_with_indicator)

                # Get the latest non-zero signal
                latest_signal = 0
                latest_signal_date = None
                for idx in reversed(signals.index):
                    if signals[idx] != 0:
                        latest_signal = int(signals[idx])
                        latest_signal_date = (
                            idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)
                        )
                        break

                # Apply signal filter
                if signal_filter is not None and latest_signal != signal_filter:
                    continue

                # Get latest indicator values
                latest_row = df_with_indicator.iloc[-1]
                indicator_values = self._get_latest_indicator_values(latest_row, indicator)

                results.append(
                    {
                        "symbol": stock["symbol"],
                        "name": stock["name"],
                        "price": float(latest_row["close"]),
                        "signal": latest_signal,
                        "signal_date": latest_signal_date,
                        **indicator_values,
                    }
                )
            except Exception:
                # Skip stocks that fail to load
                continue

        return results

    def _get_latest_indicator_values(self, row: pd.Series, indicator: str) -> dict:
        """Extract latest indicator values from a row."""
        values = {}

        if indicator == "RSI":
            if pd.notna(row.get("rsi")):
                values["rsi"] = round(float(row["rsi"]), 2)

        elif indicator == "BB":
            if pd.notna(row.get("bb_upper")):
                values["bb_upper"] = round(float(row["bb_upper"]), 0)
                values["bb_middle"] = round(float(row["bb_middle"]), 0)
                values["bb_lower"] = round(float(row["bb_lower"]), 0)
                if pd.notna(row.get("bb_percent")):
                    values["bb_percent"] = round(float(row["bb_percent"]), 2)

        elif indicator == "STOCH":
            if pd.notna(row.get("stoch_k")):
                values["stoch_k"] = round(float(row["stoch_k"]), 2)
                values["stoch_d"] = round(float(row["stoch_d"]), 2)

        return values

    def run_momentum_screener(
        self,
        signal_filter: int | None = None,
        min_score: float | None = None,
        max_score: float | None = None,
        state_filter: str | None = None,
        force_recompute: bool = False,
    ) -> list[dict]:
        """
        Run momentum factor screener on KOSPI200 stocks.

        Calculates composite momentum score using 11 technical indicators
        and saves results to database.

        Args:
            signal_filter: Filter by signal (1=buy, -1=sell, None=all)
            min_score: Minimum momentum score filter
            max_score: Maximum momentum score filter
            state_filter: Filter by momentum state (e.g., 'BULLISH', 'BEARISH')
            force_recompute: If True, recompute even if cached

        Returns:
            List of stocks with momentum scores, sorted by score descending
        """
        stocks = self.get_kospi200_list()
        momentum_factor = MomentumFactor()
        today = date.today()

        results = []
        for stock in stocks:
            try:
                symbol = stock["symbol"]

                # Check for cached score if not forcing recompute
                if not force_recompute:
                    cached = self._get_cached_momentum_score(symbol, today)
                    if cached:
                        # Apply filters to cached result
                        if self._passes_momentum_filters(
                            cached, signal_filter, min_score, max_score, state_filter
                        ):
                            results.append(cached)
                        continue

                # Get stock data (at least 60 days for reliable indicators)
                df = self.get_stock_data(symbol)
                if df.empty or len(df) < 60:
                    continue

                # Calculate momentum score
                score_result = momentum_factor.calculate(df)

                # Get latest price
                latest_price = float(df["close"].iloc[-1])

                # Save to database
                self._save_momentum_score(symbol, today, score_result, latest_price)

                # Format result
                result_item = {
                    "symbol": symbol,
                    "name": stock["name"],
                    "price": latest_price,
                    "total_score": score_result["total_score"],
                    "signal": score_result["signal"],
                    "state": score_result["state"],
                    "trend_score": score_result["category_scores"]["trend"],
                    "oscillator_score": score_result["category_scores"]["oscillator"],
                    "volume_score": score_result["category_scores"]["volume"],
                    "indicator_scores": score_result["indicator_scores"],
                }

                # Apply filters
                if self._passes_momentum_filters(
                    result_item, signal_filter, min_score, max_score, state_filter
                ):
                    results.append(result_item)

            except Exception:
                # Skip stocks that fail to load
                continue

        # Sort by total score descending
        results.sort(key=lambda x: x.get("total_score") or 0, reverse=True)

        return results

    def _get_cached_momentum_score(self, symbol: str, analysis_date: date) -> dict | None:
        """Get cached momentum score if available."""
        try:
            cached = MomentumFactorScore.objects.get(
                stock_id=symbol,
                analysis_date=analysis_date,
            )
            stock = cached.stock
            return {
                "symbol": symbol,
                "name": stock.name,
                "price": float(cached.latest_price) if cached.latest_price else None,
                "total_score": cached.total_score,
                "signal": cached.signal,
                "state": cached.state,
                "trend_score": cached.trend_score,
                "oscillator_score": cached.oscillator_score,
                "volume_score": cached.volume_score,
                "indicator_scores": {
                    "RSI": cached.rsi_score,
                    "MACD": cached.macd_score,
                    "ADX": cached.adx_score,
                    "ROC": cached.roc_score,
                    "Stochastic": cached.stochastic_score,
                    "CCI": cached.cci_score,
                    "WilliamsR": cached.williams_r_score,
                    "BollingerBands": cached.bb_score,
                    "MFI": cached.mfi_score,
                    "OBV": cached.obv_score,
                    "VolumeMA": cached.volume_ma_score,
                },
                "cached": True,
            }
        except MomentumFactorScore.DoesNotExist:
            return None

    def _save_momentum_score(
        self,
        symbol: str,
        analysis_date: date,
        score_result: dict,
        latest_price: float,
    ) -> MomentumFactorScore:
        """Save momentum score to database."""
        # Ensure stock exists
        stock, _ = StockCache.objects.get_or_create(
            symbol=symbol,
            defaults={"name": symbol, "market": "KOSPI"},
        )

        indicator_scores = score_result.get("indicator_scores", {})

        score, _ = MomentumFactorScore.objects.update_or_create(
            stock=stock,
            analysis_date=analysis_date,
            defaults={
                "total_score": score_result.get("total_score"),
                "signal": score_result.get("signal", 0),
                "state": score_result.get("state", "NEUTRAL"),
                "trend_score": score_result["category_scores"].get("trend"),
                "oscillator_score": score_result["category_scores"].get("oscillator"),
                "volume_score": score_result["category_scores"].get("volume"),
                "rsi_score": indicator_scores.get("RSI"),
                "macd_score": indicator_scores.get("MACD"),
                "adx_score": indicator_scores.get("ADX"),
                "roc_score": indicator_scores.get("ROC"),
                "stochastic_score": indicator_scores.get("Stochastic"),
                "cci_score": indicator_scores.get("CCI"),
                "williams_r_score": indicator_scores.get("WilliamsR"),
                "bb_score": indicator_scores.get("BollingerBands"),
                "mfi_score": indicator_scores.get("MFI"),
                "obv_score": indicator_scores.get("OBV"),
                "volume_ma_score": indicator_scores.get("VolumeMA"),
                "latest_price": latest_price,
            },
        )
        return score

    def _passes_momentum_filters(
        self,
        item: dict,
        signal_filter: int | None,
        min_score: float | None,
        max_score: float | None,
        state_filter: str | None,
    ) -> bool:
        """Check if item passes all momentum filters."""
        # Signal filter
        if signal_filter is not None and item.get("signal") != signal_filter:
            return False

        # Score range filter
        total_score = item.get("total_score")
        if total_score is not None:
            if min_score is not None and total_score < min_score:
                return False
            if max_score is not None and total_score > max_score:
                return False

        # State filter
        if state_filter is not None and item.get("state") != state_filter:
            return False

        return True

    def get_momentum_score(self, symbol: str, force_recompute: bool = False) -> dict:
        """
        Get momentum factor score for a single stock.

        Args:
            symbol: Stock ticker symbol
            force_recompute: If True, recompute even if cached

        Returns:
            Dict with momentum score and details
        """
        today = date.today()

        # Check cache first
        if not force_recompute:
            cached = self._get_cached_momentum_score(symbol, today)
            if cached:
                return cached

        # Get stock data
        df = self.get_stock_data(symbol)
        if df.empty or len(df) < 60:
            raise ValueError(
                f"Insufficient data for momentum analysis. "
                f"Need at least 60 days, got {len(df)} days."
            )

        # Calculate momentum score
        momentum_factor = MomentumFactor()
        score_result = momentum_factor.calculate(df)

        # Get latest price
        latest_price = float(df["close"].iloc[-1])

        # Save to database
        self._save_momentum_score(symbol, today, score_result, latest_price)

        # Get stock info
        stock_info = self.get_stock_info(symbol) or {"symbol": symbol, "name": symbol}

        return {
            "symbol": symbol,
            "name": stock_info["name"],
            "price": latest_price,
            "total_score": score_result["total_score"],
            "signal": score_result["signal"],
            "state": score_result["state"],
            "description": momentum_factor.get_score_description(score_result["total_score"]),
            "category_scores": score_result["category_scores"],
            "indicator_scores": score_result["indicator_scores"],
            "cached": False,
        }

    def analyze_bubble(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        force_recompute: bool = False,
    ) -> dict:
        """
        Analyze stock for bubble using LPPL multi-window analysis.

        Implements LPPLS Confidence Indicator by fitting LPPL on multiple
        time windows (125-750 days) and calculating the proportion of fits
        that satisfy bubble conditions.

        Results are cached in the database and reused when the analysis date
        matches the latest price date. Use force_recompute=True to bypass cache.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date (default: 3 years ago for multi-window)
            end_date: End date (default: today)
            force_recompute: If True, bypass cache and recompute

        Returns:
            Dict with LPPLS confidence indicator and detailed results
        """
        # Get at least 3 years of data for multi-window analysis
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=1095)).strftime("%Y-%m-%d")

        df = self.get_stock_data(symbol, start_date, end_date)

        if df.empty or len(df) < 125:
            raise ValueError(
                f"Insufficient data for LPPL multi-window analysis. "
                f"Need at least 125 days, got {len(df)} days."
            )

        # Extract closing prices
        prices = df["close"]

        try:
            # Use cache service for multi-window analysis (step=5 for finer granularity)
            confidence_result = self._lppl_cache.get_or_compute(
                symbol=symbol,
                prices_df=df,
                step=5,  # Changed from 25 to 5 for finer granularity
                force_recompute=force_recompute,
            )

            # Also fit on full data for visualization
            lppl = LPPL()
            try:
                lppl.fit(prices, max_iter=2000)
                fitted, forecast = lppl.forecast(prices, forecast_days=60)
                has_fit = True
            except Exception:
                # If full fit fails, don't fail the entire analysis
                fitted = pd.Series(dtype=float)
                forecast = pd.Series(dtype=float)
                has_fit = False

        except ValueError as e:
            raise ValueError(f"데이터 부족: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"분석 중 오류 발생: {str(e)}") from e

        # Format for JSON response
        result = {
            "symbol": symbol,
            "analysis_period": {
                "start": prices.index[0].strftime("%Y-%m-%d"),
                "end": prices.index[-1].strftime("%Y-%m-%d"),
                "days": len(prices),
            },
            "confidence_indicator": confidence_result,
            "fitted_prices": self._series_to_chart_data(fitted) if has_fit else [],
            "forecast_prices": self._series_to_chart_data(forecast) if has_fit else [],
        }

        return result

    def _series_to_chart_data(self, series: pd.Series) -> list[dict]:
        """Convert pandas Series to chart data format."""
        data = []
        for idx, value in series.items():
            if pd.notna(value):
                timestamp = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)
                data.append({"time": timestamp, "value": float(value)})
        return data
