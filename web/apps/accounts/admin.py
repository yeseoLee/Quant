"""Admin configuration for accounts app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AnalysisHistory, User, Watchlist


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom user admin."""

    list_display = ["username", "email", "is_staff", "date_joined"]


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    """Watchlist admin."""

    list_display = ["user", "symbol", "name", "created_at"]
    list_filter = ["user"]
    search_fields = ["symbol", "name"]


@admin.register(AnalysisHistory)
class AnalysisHistoryAdmin(admin.ModelAdmin):
    """Analysis history admin."""

    list_display = ["user", "symbol", "indicator", "signal", "signal_date", "created_at"]
    list_filter = ["user", "indicator", "signal"]
    search_fields = ["symbol", "name"]
