"""Admin configuration for accounts app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Watchlist


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
