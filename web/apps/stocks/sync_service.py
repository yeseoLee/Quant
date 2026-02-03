"""Stock data synchronization service using pykrx and FinanceDataReader."""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

import FinanceDataReader as fdr
import pandas as pd
from django.utils import timezone

from .models import MarketIndex, StockCache, StockPrice, SyncLog

logger = logging.getLogger(__name__)


def _get_kospi200_from_pykrx() -> list[tuple[str, str]] | None:
    """Try to get KOSPI200 constituents from pykrx."""
    try:
        from pykrx import stock as pykrx_stock

        today = date.today()
        # Try today and previous business days
        for days_back in range(0, 10):
            target_date = today - timedelta(days=days_back)
            date_str = target_date.strftime("%Y%m%d")

            tickers = pykrx_stock.get_index_portfolio_deposit_file("1028", date_str)

            # pykrx returns DataFrame or list depending on version
            if isinstance(tickers, pd.DataFrame):
                if tickers.empty:
                    continue
                # DataFrame with tickers
                ticker_list = tickers.index.tolist()
            else:
                # List/Series of tickers
                ticker_list = list(tickers) if tickers else []

            if ticker_list:
                # Get names for each ticker
                result = []
                for ticker in ticker_list:
                    try:
                        name = pykrx_stock.get_market_ticker_name(ticker)
                    except Exception:
                        name = ticker
                    result.append((ticker, name))
                return result

        return None
    except Exception as e:
        logger.warning(f"pykrx failed: {e}")
        return None


def _get_kospi200_from_fdr() -> list[tuple[str, str]] | None:
    """Get top 200 KOSPI stocks by market cap from FinanceDataReader as fallback."""
    try:
        # Get all KOSPI stocks with market cap
        df = fdr.StockListing("KOSPI")

        # Sort by market cap and take top 200
        # Marcap column contains market capitalization
        if "Marcap" in df.columns and "Code" in df.columns and "Name" in df.columns:
            df_sorted = df.sort_values("Marcap", ascending=False)
            top_200 = df_sorted.head(200)
            return [(row["Code"], row["Name"]) for _, row in top_200.iterrows()]

        return None
    except Exception as e:
        logger.warning(f"FinanceDataReader fallback failed: {e}")
        return None


def _get_kosdaq150_from_pykrx() -> list[tuple[str, str]] | None:
    """Try to get KOSDAQ150 constituents from pykrx."""
    try:
        from pykrx import stock as pykrx_stock

        today = date.today()
        # Try today and previous business days
        for days_back in range(0, 10):
            target_date = today - timedelta(days=days_back)
            date_str = target_date.strftime("%Y%m%d")

            # Try different possible index codes for KOSDAQ 150
            # Common codes: "2203" for KOSDAQ 150, or Korean name
            for index_code in ["2203", "코스닥 150"]:
                try:
                    tickers = pykrx_stock.get_index_portfolio_deposit_file(index_code, date_str)

                    # pykrx returns DataFrame or list depending on version
                    if isinstance(tickers, pd.DataFrame):
                        if tickers.empty:
                            continue
                        ticker_list = tickers.index.tolist()
                    else:
                        ticker_list = list(tickers) if tickers else []

                    if ticker_list:
                        # Get names for each ticker
                        result = []
                        for ticker in ticker_list:
                            try:
                                name = pykrx_stock.get_market_ticker_name(ticker)
                            except Exception:
                                name = ticker
                            result.append((ticker, name))
                        return result
                except Exception:
                    continue

        return None
    except Exception as e:
        logger.warning(f"pykrx failed for KOSDAQ150: {e}")
        return None


def _get_kosdaq150_from_fdr() -> list[tuple[str, str]] | None:
    """Get top 150 KOSDAQ stocks by market cap from FinanceDataReader as fallback."""
    try:
        # Get all KOSDAQ stocks with market cap
        df = fdr.StockListing("KOSDAQ")

        # Sort by market cap and take top 150
        # Marcap column contains market capitalization
        if "Marcap" in df.columns and "Code" in df.columns and "Name" in df.columns:
            df_sorted = df.sort_values("Marcap", ascending=False)
            top_150 = df_sorted.head(150)
            return [(row["Code"], row["Name"]) for _, row in top_150.iterrows()]

        return None
    except Exception as e:
        logger.warning(f"FinanceDataReader fallback failed for KOSDAQ150: {e}")
        return None


class StockSyncService:
    """Service for synchronizing KOSPI200 stock data."""

    DEFAULT_HISTORY_YEARS = 10

    def __init__(self):
        self._today = date.today()

    def _get_stock_name(self, symbol: str) -> str:
        """Get stock name from pykrx or return symbol as fallback."""
        try:
            from pykrx import stock as pykrx_stock

            return pykrx_stock.get_market_ticker_name(symbol)
        except Exception:
            return symbol

    def sync_kospi200_constituents(self) -> int:
        """
        Sync KOSPI200 constituent stocks.

        Tries pykrx first, falls back to FinanceDataReader top 200 by market cap.

        Returns:
            Number of stocks updated/created
        """
        logger.info("Starting KOSPI200 constituents sync")

        try:
            # Try pykrx first
            stocks = _get_kospi200_from_pykrx()

            # Fallback to FinanceDataReader
            if not stocks:
                logger.info("pykrx unavailable, using FinanceDataReader top 200 by market cap")
                stocks = _get_kospi200_from_fdr()

            if not stocks:
                logger.error("Could not fetch KOSPI200 constituents from any source")
                return 0

            # Reset all stocks to non-KOSPI200 first
            StockCache.objects.filter(is_kospi200=True).update(is_kospi200=False)

            updated_count = 0
            for symbol, name in stocks:
                StockCache.objects.update_or_create(
                    symbol=symbol,
                    defaults={
                        "name": name,
                        "market": "KOSPI",
                        "is_kospi200": True,
                    },
                )
                updated_count += 1

            logger.info(f"KOSPI200 constituents sync completed: {updated_count} stocks")
            return updated_count

        except Exception as e:
            logger.error(f"Error syncing KOSPI200 constituents: {e}")
            raise

    def sync_kosdaq150_constituents(self) -> int:
        """
        Sync KOSDAQ150 constituent stocks.

        Tries pykrx first, falls back to FinanceDataReader top 150 by market cap.

        Returns:
            Number of stocks updated/created
        """
        logger.info("Starting KOSDAQ150 constituents sync")

        try:
            # Try pykrx first
            stocks = _get_kosdaq150_from_pykrx()

            # Fallback to FinanceDataReader
            if not stocks:
                logger.info("pykrx unavailable, using FinanceDataReader top 150 by market cap")
                stocks = _get_kosdaq150_from_fdr()

            if not stocks:
                logger.error("Could not fetch KOSDAQ150 constituents from any source")
                return 0

            # Reset all stocks to non-KOSDAQ150 first
            StockCache.objects.filter(is_kosdaq150=True).update(is_kosdaq150=False)

            updated_count = 0
            for symbol, name in stocks:
                StockCache.objects.update_or_create(
                    symbol=symbol,
                    defaults={
                        "name": name,
                        "market": "KOSDAQ",
                        "is_kosdaq150": True,
                    },
                )
                updated_count += 1

            logger.info(f"KOSDAQ150 constituents sync completed: {updated_count} stocks")
            return updated_count

        except Exception as e:
            logger.error(f"Error syncing KOSDAQ150 constituents: {e}")
            raise

    def sync_stock_prices(
        self,
        symbol: str,
        full_sync: bool = False,
    ) -> int:
        """
        Sync OHLCV price data for a single stock.

        Args:
            symbol: Stock ticker symbol
            full_sync: If True, fetch full history (10 years). Otherwise incremental.

        Returns:
            Number of new price records created
        """
        logger.info(f"Syncing prices for {symbol} (full={full_sync})")

        try:
            stock = StockCache.objects.get(symbol=symbol)
        except StockCache.DoesNotExist:
            logger.warning(f"Stock {symbol} not found in cache, creating entry")
            name = self._get_stock_name(symbol)
            stock = StockCache.objects.create(symbol=symbol, name=name)

        # Determine start date
        if full_sync or stock.last_price_date is None:
            start_date = self._today - timedelta(days=365 * self.DEFAULT_HISTORY_YEARS)
        else:
            start_date = stock.last_price_date + timedelta(days=1)

        end_date = self._today

        if start_date > end_date:
            logger.info(f"Stock {symbol} is already up to date")
            return 0

        # Update sync status
        stock.sync_status = "syncing"
        stock.save(update_fields=["sync_status"])

        try:
            # Fetch data from FinanceDataReader
            df = fdr.DataReader(symbol, start_date, end_date)

            if df.empty:
                logger.info(f"No new data for {symbol}")
                stock.sync_status = "completed"
                stock.last_sync_at = timezone.now()
                stock.save(update_fields=["sync_status", "last_sync_at"])
                return 0

            # Normalize column names
            df.columns = df.columns.str.lower()

            # Prepare price records
            new_records = 0
            price_objects = []

            for idx, row in df.iterrows():
                price_date = idx.date() if hasattr(idx, "date") else idx

                # Check if record already exists
                if StockPrice.objects.filter(stock=stock, date=price_date).exists():
                    continue

                price_objects.append(
                    StockPrice(
                        stock=stock,
                        date=price_date,
                        open=Decimal(str(row["open"])),
                        high=Decimal(str(row["high"])),
                        low=Decimal(str(row["low"])),
                        close=Decimal(str(row["close"])),
                        volume=int(row["volume"]),
                    )
                )
                new_records += 1

            # Bulk create
            if price_objects:
                StockPrice.objects.bulk_create(price_objects, ignore_conflicts=True)

            # Update stock metadata
            latest_price = StockPrice.objects.filter(stock=stock).order_by("-date").first()
            stock.last_price_date = latest_price.date if latest_price else None
            stock.last_sync_at = timezone.now()
            stock.sync_status = "completed"
            stock.save(update_fields=["last_price_date", "last_sync_at", "sync_status"])

            logger.info(f"Synced {new_records} new records for {symbol}")
            return new_records

        except Exception as e:
            logger.error(f"Error syncing prices for {symbol}: {e}")
            stock.sync_status = "failed"
            stock.save(update_fields=["sync_status"])
            raise

    def sync_all_kospi200(self, full_sync: bool = False) -> SyncLog:
        """
        Sync price data for all KOSPI200 stocks.

        Args:
            full_sync: If True, fetch full history for all stocks

        Returns:
            SyncLog instance with sync results
        """
        sync_type = "full" if full_sync else "incremental"
        sync_log = SyncLog.objects.create(
            sync_type=sync_type,
            status="running",
        )

        try:
            # First sync constituents
            self.sync_kospi200_constituents()

            # Get all KOSPI200 stocks
            stocks = StockCache.objects.filter(is_kospi200=True)
            sync_log.total_stocks = stocks.count()
            sync_log.save(update_fields=["total_stocks"])

            total_new_records = 0
            processed = 0

            for stock in stocks:
                try:
                    new_records = self.sync_stock_prices(stock.symbol, full_sync=full_sync)
                    total_new_records += new_records
                    processed += 1

                    # Update progress periodically
                    if processed % 10 == 0:
                        sync_log.processed_stocks = processed
                        sync_log.new_records = total_new_records
                        sync_log.save(update_fields=["processed_stocks", "new_records"])
                        logger.info(f"Progress: {processed}/{sync_log.total_stocks} stocks")

                except Exception as e:
                    logger.error(f"Error syncing {stock.symbol}: {e}")
                    continue

            # Finalize
            sync_log.processed_stocks = processed
            sync_log.new_records = total_new_records
            sync_log.status = "completed"
            sync_log.completed_at = timezone.now()
            sync_log.save()

            logger.info(
                f"KOSPI200 sync completed: {processed} stocks, {total_new_records} new records"
            )
            return sync_log

        except Exception as e:
            sync_log.status = "failed"
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            logger.error(f"KOSPI200 sync failed: {e}")
            raise

    def sync_all_kosdaq150(self, full_sync: bool = False) -> SyncLog:
        """
        Sync price data for all KOSDAQ150 stocks.

        Args:
            full_sync: If True, fetch full history for all stocks

        Returns:
            SyncLog instance with sync results
        """
        sync_type = "full" if full_sync else "incremental"
        sync_log = SyncLog.objects.create(
            sync_type=sync_type,
            status="running",
        )

        try:
            # First sync constituents
            self.sync_kosdaq150_constituents()

            # Get all KOSDAQ150 stocks
            stocks = StockCache.objects.filter(is_kosdaq150=True)
            sync_log.total_stocks = stocks.count()
            sync_log.save(update_fields=["total_stocks"])

            total_new_records = 0
            processed = 0

            for stock in stocks:
                try:
                    new_records = self.sync_stock_prices(stock.symbol, full_sync=full_sync)
                    total_new_records += new_records
                    processed += 1

                    # Update progress periodically
                    if processed % 10 == 0:
                        sync_log.processed_stocks = processed
                        sync_log.new_records = total_new_records
                        sync_log.save(update_fields=["processed_stocks", "new_records"])
                        logger.info(f"Progress: {processed}/{sync_log.total_stocks} stocks")

                except Exception as e:
                    logger.error(f"Error syncing {stock.symbol}: {e}")
                    continue

            # Finalize
            sync_log.processed_stocks = processed
            sync_log.new_records = total_new_records
            sync_log.status = "completed"
            sync_log.completed_at = timezone.now()
            sync_log.save()

            logger.info(
                f"KOSDAQ150 sync completed: {processed} stocks, {total_new_records} new records"
            )
            return sync_log

        except Exception as e:
            sync_log.status = "failed"
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            logger.error(f"KOSDAQ150 sync failed: {e}")
            raise

    # Market indices: symbol -> (name, category)
    MARKET_INDICES = {
        # KRX
        "KS11": ("KOSPI", "KRX"),
        "KQ11": ("KOSDAQ", "KRX"),
        "KS200": ("KOSPI 200", "KRX"),
        # US
        "DJI": ("다우존스", "US"),
        "IXIC": ("나스닥", "US"),
        "S&P500": ("S&P 500", "US"),
        # Global
        "SSEC": ("상해종합", "GLOBAL"),
        "N225": ("니케이 225", "GLOBAL"),
        "HSI": ("항셍", "GLOBAL"),
        "FTSE": ("FTSE 100", "GLOBAL"),
        "GDAXI": ("DAX", "GLOBAL"),
    }

    def sync_market_indices(self) -> int:
        """
        Sync market index data for all tracked indices.

        Fetches last 1 year of data from FinanceDataReader.

        Returns:
            Total number of new records created
        """
        logger.info("Starting market index sync")
        start_date = self._today - timedelta(days=365)
        total_new = 0

        for symbol, (name, category) in self.MARKET_INDICES.items():
            try:
                df = fdr.DataReader(symbol, start_date, self._today)
                if df.empty:
                    logger.warning(f"No data for index {symbol}")
                    continue

                df.columns = df.columns.str.lower()
                records = []

                for idx, row in df.iterrows():
                    price_date = idx.date() if hasattr(idx, "date") else idx
                    records.append(
                        MarketIndex(
                            symbol=symbol,
                            name=name,
                            category=category,
                            date=price_date,
                            open=Decimal(str(row["open"])),
                            high=Decimal(str(row["high"])),
                            low=Decimal(str(row["low"])),
                            close=Decimal(str(row["close"])),
                            volume=int(row["volume"]) if pd.notna(row.get("volume")) else None,
                        )
                    )

                if records:
                    MarketIndex.objects.bulk_create(records, ignore_conflicts=True)
                    total_new += len(records)
                    logger.info(f"Synced {len(records)} records for index {symbol}")

            except Exception as e:
                logger.error(f"Error syncing index {symbol}: {e}")
                continue

        logger.info(f"Market index sync completed: {total_new} records")
        return total_new

    def needs_daily_sync(self) -> bool:
        """
        Check if daily sync is needed.

        Returns:
            True if no successful sync today
        """
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        last_successful_sync = (
            SyncLog.objects.filter(
                status="completed",
                sync_type__in=["full", "incremental"],
            )
            .order_by("-completed_at")
            .first()
        )

        if last_successful_sync is None:
            return True

        if last_successful_sync.completed_at is None:
            return True

        return last_successful_sync.completed_at < today_start

    def run_daily_sync_if_needed(self) -> SyncLog | None:
        """
        Run incremental sync if not already done today.

        Syncs both KOSPI200 and KOSDAQ150 stocks.

        Returns:
            SyncLog from KOSPI200 sync if sync was performed, None otherwise
        """
        if not self.needs_daily_sync():
            logger.info("Daily sync already completed, skipping")
            return None

        logger.info("Starting daily incremental sync")
        kospi_log = self.sync_all_kospi200(full_sync=False)

        try:
            self.sync_all_kosdaq150(full_sync=False)
        except Exception as e:
            logger.error(f"KOSDAQ150 daily sync failed: {e}")

        try:
            self.sync_market_indices()
        except Exception as e:
            logger.error(f"Market index daily sync failed: {e}")

        return kospi_log

    def get_stock_prices_from_db(
        self,
        symbol: str,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
    ) -> list[dict]:
        """
        Get OHLCV data from database.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date (default: 1 year ago)
            end_date: End date (default: today)

        Returns:
            List of dicts with date, open, high, low, close, volume
        """
        # Parse dates
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        if start_date is None:
            start_date = self._today - timedelta(days=365)
        if end_date is None:
            end_date = self._today

        prices = StockPrice.objects.filter(
            stock_id=symbol,
            date__gte=start_date,
            date__lte=end_date,
        ).order_by("date")

        return [
            {
                "time": price.date.strftime("%Y-%m-%d"),
                "open": float(price.open),
                "high": float(price.high),
                "low": float(price.low),
                "close": float(price.close),
                "volume": price.volume,
            }
            for price in prices
        ]

    def has_stock_data(self, symbol: str) -> bool:
        """Check if stock has data in database."""
        return StockPrice.objects.filter(stock_id=symbol).exists()
