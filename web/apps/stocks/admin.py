"""Admin configuration for stocks app."""

from django.contrib import admin

from .models import StockCache, StockPrice, SyncLog


@admin.register(StockCache)
class StockCacheAdmin(admin.ModelAdmin):
    """Stock cache admin."""

    list_display = [
        "symbol",
        "name",
        "market",
        "sector",
        "is_kospi200",
        "last_price_date",
        "sync_status",
        "updated_at",
    ]
    list_filter = ["market", "sector", "is_kospi200", "sync_status"]
    search_fields = ["symbol", "name"]
    readonly_fields = ["last_sync_at", "updated_at"]


@admin.register(StockPrice)
class StockPriceAdmin(admin.ModelAdmin):
    """Stock price admin."""

    list_display = ["stock", "date", "open", "high", "low", "close", "volume"]
    list_filter = ["stock__is_kospi200", "date"]
    search_fields = ["stock__symbol", "stock__name"]
    date_hierarchy = "date"
    ordering = ["-date"]


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    """Sync log admin."""

    list_display = [
        "id",
        "sync_type",
        "status",
        "started_at",
        "completed_at",
        "total_stocks",
        "processed_stocks",
        "new_records",
    ]
    list_filter = ["sync_type", "status"]
    readonly_fields = [
        "sync_type",
        "status",
        "started_at",
        "completed_at",
        "total_stocks",
        "processed_stocks",
        "new_records",
        "error_message",
    ]
    ordering = ["-started_at"]
