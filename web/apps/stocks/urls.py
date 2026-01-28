"""URL configuration for stocks app."""

from django.urls import path

from . import views

app_name = "stocks"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("stock/<str:symbol>/", views.StockDetailView.as_view(), name="stock_detail"),
    path("screener/", views.ScreenerView.as_view(), name="screener"),
    path(
        "stock/<str:symbol>/watchlist/add/",
        views.add_to_watchlist,
        name="add_to_watchlist",
    ),
    path(
        "stock/<str:symbol>/watchlist/remove/",
        views.remove_from_watchlist,
        name="remove_from_watchlist",
    ),
    path("search/", views.search_stocks, name="search"),
]
