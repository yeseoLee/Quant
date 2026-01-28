import logging
import os
import threading

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class StocksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.stocks"
    verbose_name = "Stocks"

    def ready(self):
        """Run daily sync check on server startup."""
        # Only run in the main process (not in migrations, shell, or management commands)
        # Also skip during runserver's auto-reloader to avoid double execution
        if os.environ.get("RUN_MAIN") != "true":
            return

        # Skip if running migrations or other management commands
        import sys

        if len(sys.argv) > 1 and sys.argv[1] in ["migrate", "makemigrations", "shell", "dbshell"]:
            return

        # Start sync in background thread to not block server startup
        def run_daily_sync():
            try:
                from .sync_service import StockSyncService

                service = StockSyncService()
                result = service.run_daily_sync_if_needed()
                if result:
                    logger.info(f"Daily sync completed: {result.new_records} new records")
                else:
                    logger.info("Daily sync skipped (already completed today)")
            except Exception as e:
                logger.error(f"Daily sync failed: {e}")

        thread = threading.Thread(target=run_daily_sync, daemon=True)
        thread.start()
        logger.info("Background sync thread started")
