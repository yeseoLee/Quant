"""Data fetching utilities using FinanceDataReader and yfinance."""

from datetime import datetime, timedelta

import FinanceDataReader as fdr
import pandas as pd
import yfinance as yf


class DataFetcher:
    """Unified data fetcher for Korean and international markets."""

    def __init__(self):
        self._cache: dict[str, pd.DataFrame] = {}

    def get_stock_data(
        self,
        symbol: str,
        start_date: str | datetime | None = None,
        end_date: str | datetime | None = None,
        source: str = "fdr",
    ) -> pd.DataFrame:
        """
        Fetch stock price data.

        Args:
            symbol: Stock ticker symbol (e.g., '005930' for Samsung Electronics)
            start_date: Start date for data (default: 1 year ago)
            end_date: End date for data (default: today)
            source: Data source - 'fdr' (FinanceDataReader) or 'yf' (yfinance)

        Returns:
            DataFrame with OHLCV data
        """
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d")
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d")

        if source == "fdr":
            return self._fetch_fdr(symbol, start_date, end_date)
        elif source == "yf":
            return self._fetch_yfinance(symbol, start_date, end_date)
        else:
            raise ValueError(f"Unknown source: {source}. Use 'fdr' or 'yf'.")

    def _fetch_fdr(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch data using FinanceDataReader."""
        df = fdr.DataReader(symbol, start_date, end_date)
        return self._normalize_columns(df)

    def _fetch_yfinance(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch data using yfinance."""
        # For Korean stocks, add .KS or .KQ suffix if needed
        if symbol.isdigit() and len(symbol) == 6:
            symbol = f"{symbol}.KS"

        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        return self._normalize_columns(df)

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to lowercase."""
        df.columns = [col.lower() for col in df.columns]
        return df

    def get_multiple_stocks(
        self,
        symbols: list[str],
        start_date: str | datetime | None = None,
        end_date: str | datetime | None = None,
        source: str = "fdr",
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch data for multiple stocks.

        Args:
            symbols: List of stock ticker symbols
            start_date: Start date for data
            end_date: End date for data
            source: Data source

        Returns:
            Dictionary mapping symbol to DataFrame
        """
        result = {}
        for symbol in symbols:
            try:
                result[symbol] = self.get_stock_data(symbol, start_date, end_date, source)
            except Exception as e:
                print(f"Failed to fetch {symbol}: {e}")
        return result
