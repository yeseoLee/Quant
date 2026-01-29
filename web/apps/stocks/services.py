"""Service layer wrapping the quant library for web application."""

from datetime import date, datetime, timedelta

import pandas as pd

from quant.data import DataFetcher, Kospi200
from quant.factors import RSI, BollingerBands, Stochastic
from quant.models import LPPL

from .models import StockCache, StockPrice
from .sync_service import StockSyncService


class StockService:
    """Service class for stock data operations."""

    def __init__(self):
        self._fetcher = DataFetcher()
        self._kospi200 = Kospi200()
        self._sync_service = StockSyncService()
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

    def analyze_bubble(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """
        Analyze stock for bubble using LPPL model.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date (default: 2 years ago for better fitting)
            end_date: End date (default: today)

        Returns:
            Dict with bubble diagnosis and LPPL model results
        """
        # Get at least 2 years of data for better LPPL fitting
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

        df = self.get_stock_data(symbol, start_date, end_date)

        if df.empty or len(df) < 30:
            raise ValueError("Insufficient data for LPPL analysis (need at least 30 days)")

        # Extract closing prices
        prices = df["close"]

        # Fit LPPL model
        lppl = LPPL()
        try:
            lppl.fit(prices)
        except Exception as e:
            raise RuntimeError(f"LPPL fitting failed: {str(e)}")

        # Get bubble diagnosis
        diagnosis = lppl.diagnose_bubble(prices)

        # Get fitted and forecasted prices
        fitted, forecast = lppl.forecast(prices, forecast_days=60)

        # Format for JSON response
        result = {
            "symbol": symbol,
            "analysis_period": {
                "start": prices.index[0].strftime("%Y-%m-%d"),
                "end": prices.index[-1].strftime("%Y-%m-%d"),
                "days": len(prices),
            },
            "diagnosis": diagnosis,
            "fitted_prices": self._series_to_chart_data(fitted),
            "forecast_prices": self._series_to_chart_data(forecast),
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
