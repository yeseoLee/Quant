"""Management command for syncing KOSPI200 stock data."""

from django.core.management.base import BaseCommand

from apps.stocks.sync_service import StockSyncService


class Command(BaseCommand):
    """Sync KOSPI200 stock data from external APIs to database."""

    help = "Sync KOSPI200 stock price data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--full",
            action="store_true",
            help="Perform full sync (10 years of history)",
        )
        parser.add_argument(
            "--constituents-only",
            action="store_true",
            help="Only update KOSPI200 constituent list",
        )
        parser.add_argument(
            "--symbol",
            type=str,
            help="Sync only a specific stock symbol",
        )

    def handle(self, *args, **options):
        service = StockSyncService()

        if options["constituents_only"]:
            self.stdout.write("Updating KOSPI200 constituents...")
            count = service.sync_kospi200_constituents()
            self.stdout.write(self.style.SUCCESS(f"Updated {count} KOSPI200 constituents"))
            return

        if options["symbol"]:
            symbol = options["symbol"]
            self.stdout.write(f"Syncing stock {symbol}...")
            new_records = service.sync_stock_prices(symbol, full_sync=options["full"])
            self.stdout.write(self.style.SUCCESS(f"Synced {new_records} new records for {symbol}"))
            return

        # Full or incremental sync for all KOSPI200 stocks
        sync_type = "full" if options["full"] else "incremental"
        self.stdout.write(f"Starting {sync_type} sync for all KOSPI200 stocks...")

        sync_log = service.sync_all_kospi200(full_sync=options["full"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Sync completed: {sync_log.processed_stocks} stocks, "
                f"{sync_log.new_records} new records"
            )
        )
