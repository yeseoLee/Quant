"""Management command for syncing stock data."""

from django.core.management.base import BaseCommand

from apps.stocks.sync_service import StockSyncService


class Command(BaseCommand):
    """Sync stock data from external APIs to database."""

    help = "Sync KOSPI200/KOSDAQ150 stock price data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--full",
            action="store_true",
            help="Perform full sync (10 years of history)",
        )
        parser.add_argument(
            "--constituents-only",
            action="store_true",
            help="Only update constituent list (no price data)",
        )
        parser.add_argument(
            "--symbol",
            type=str,
            help="Sync only a specific stock symbol",
        )
        parser.add_argument(
            "--market",
            type=str,
            choices=["KOSPI", "KOSDAQ", "ALL"],
            default="ALL",
            help="Market to sync: KOSPI, KOSDAQ, or ALL (default: ALL)",
        )

    def handle(self, *args, **options):
        service = StockSyncService()
        market = options["market"]

        if options["constituents_only"]:
            if market in ("KOSPI", "ALL"):
                self.stdout.write("Updating KOSPI200 constituents...")
                count = service.sync_kospi200_constituents()
                self.stdout.write(self.style.SUCCESS(f"Updated {count} KOSPI200 constituents"))
            if market in ("KOSDAQ", "ALL"):
                self.stdout.write("Updating KOSDAQ150 constituents...")
                count = service.sync_kosdaq150_constituents()
                self.stdout.write(self.style.SUCCESS(f"Updated {count} KOSDAQ150 constituents"))
            return

        if options["symbol"]:
            symbol = options["symbol"]
            self.stdout.write(f"Syncing stock {symbol}...")
            new_records = service.sync_stock_prices(symbol, full_sync=options["full"])
            self.stdout.write(self.style.SUCCESS(f"Synced {new_records} new records for {symbol}"))
            return

        # Full or incremental sync
        sync_type = "full" if options["full"] else "incremental"

        if market in ("KOSPI", "ALL"):
            self.stdout.write(f"Starting {sync_type} sync for KOSPI200 stocks...")
            sync_log = service.sync_all_kospi200(full_sync=options["full"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"KOSPI200 sync completed: {sync_log.processed_stocks} stocks, "
                    f"{sync_log.new_records} new records"
                )
            )

        if market in ("KOSDAQ", "ALL"):
            self.stdout.write(f"Starting {sync_type} sync for KOSDAQ150 stocks...")
            sync_log = service.sync_all_kosdaq150(full_sync=options["full"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"KOSDAQ150 sync completed: {sync_log.processed_stocks} stocks, "
                    f"{sync_log.new_records} new records"
                )
            )
