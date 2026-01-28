"""KOSPI 200 index constituents management."""

import FinanceDataReader as fdr
import pandas as pd


class Kospi200:
    """Manage KOSPI 200 index constituents."""

    def __init__(self):
        self._constituents: pd.DataFrame | None = None

    def get_constituents(self, refresh: bool = False) -> pd.DataFrame:
        """
        Get KOSPI 200 constituent stocks.

        Args:
            refresh: Force refresh from source

        Returns:
            DataFrame with stock code, name, and other info
        """
        if self._constituents is None or refresh:
            self._constituents = fdr.StockListing("KOSPI200")
        return self._constituents

    def get_symbols(self, refresh: bool = False) -> list[str]:
        """
        Get list of KOSPI 200 stock symbols.

        Args:
            refresh: Force refresh from source

        Returns:
            List of stock ticker symbols
        """
        df = self.get_constituents(refresh)
        # Column name may vary: 'Code', 'Symbol', or '종목코드'
        code_col = None
        for col in ["Code", "Symbol", "종목코드"]:
            if col in df.columns:
                code_col = col
                break

        if code_col is None:
            raise ValueError(f"Cannot find code column. Available columns: {df.columns.tolist()}")

        return df[code_col].tolist()

    def get_stock_info(self, symbol: str) -> pd.Series | None:
        """
        Get information for a specific stock.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Series with stock information or None if not found
        """
        df = self.get_constituents()
        code_col = None
        for col in ["Code", "Symbol", "종목코드"]:
            if col in df.columns:
                code_col = col
                break

        if code_col is None:
            return None

        matches = df[df[code_col] == symbol]
        if len(matches) == 0:
            return None
        return matches.iloc[0]
