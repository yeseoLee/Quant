"""KOSDAQ 150 index constituents management."""

import FinanceDataReader as fdr
import pandas as pd


class Kosdaq150:
    """Manage KOSDAQ 150 index constituents."""

    def __init__(self):
        self._constituents: pd.DataFrame | None = None

    def get_constituents(self, refresh: bool = False) -> pd.DataFrame:
        """
        Get KOSDAQ 150 constituent stocks.

        Tries pykrx first for actual index constituents,
        falls back to top 150 KOSDAQ stocks by market cap from FinanceDataReader.

        Args:
            refresh: Force refresh from source

        Returns:
            DataFrame with stock code, name, and other info
        """
        if self._constituents is None or refresh:
            self._constituents = self._fetch_constituents()
        return self._constituents

    def _fetch_constituents(self) -> pd.DataFrame:
        """Fetch KOSDAQ 150 constituents from available sources."""
        # Try pykrx first
        df = self._from_pykrx()
        if df is not None and not df.empty:
            return df

        # Fallback: top 150 KOSDAQ stocks by market cap
        return self._from_fdr_top150()

    def _from_pykrx(self) -> pd.DataFrame | None:
        """Get KOSDAQ 150 constituents from pykrx."""
        try:
            from datetime import date, timedelta

            from pykrx import stock as pykrx_stock

            today = date.today()
            for days_back in range(0, 10):
                target_date = today - timedelta(days=days_back)
                date_str = target_date.strftime("%Y%m%d")

                for index_code in ["2203", "코스닥 150"]:
                    try:
                        tickers = pykrx_stock.get_index_portfolio_deposit_file(
                            index_code, date_str
                        )
                        if isinstance(tickers, pd.DataFrame):
                            if tickers.empty:
                                continue
                            ticker_list = tickers.index.tolist()
                        else:
                            ticker_list = list(tickers) if tickers else []

                        if ticker_list:
                            rows = []
                            for ticker in ticker_list:
                                try:
                                    name = pykrx_stock.get_market_ticker_name(ticker)
                                except Exception:
                                    name = ticker
                                rows.append({"Code": ticker, "Name": name})
                            return pd.DataFrame(rows)
                    except Exception:
                        continue
            return None
        except ImportError:
            return None
        except Exception:
            return None

    def _from_fdr_top150(self) -> pd.DataFrame:
        """Get top 150 KOSDAQ stocks by market cap from FinanceDataReader."""
        df = fdr.StockListing("KOSDAQ")
        if "Marcap" in df.columns and "Code" in df.columns:
            df_sorted = df.sort_values("Marcap", ascending=False)
            return df_sorted.head(150).reset_index(drop=True)
        return df.head(150).reset_index(drop=True)

    def get_symbols(self, refresh: bool = False) -> list[str]:
        """
        Get list of KOSDAQ 150 stock symbols.

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
