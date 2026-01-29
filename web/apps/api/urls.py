"""URL configuration for API app."""

from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    # Stock data endpoints
    path("stock/<str:symbol>/ohlcv/", views.OHLCVView.as_view(), name="ohlcv"),
    path(
        "stock/<str:symbol>/indicator/<str:indicator>/",
        views.IndicatorView.as_view(),
        name="indicator",
    ),
    path(
        "stock/<str:symbol>/signals/<str:indicator>/",
        views.SignalsView.as_view(),
        name="signals",
    ),
    path(
        "stock/<str:symbol>/bubble/",
        views.BubbleAnalysisView.as_view(),
        name="bubble_analysis",
    ),
    # KOSPI200 endpoints
    path("kospi200/", views.Kospi200ListView.as_view(), name="kospi200"),
    path("screener/run/", views.ScreenerView.as_view(), name="screener"),
    # Search endpoint
    path("search/", views.search_stocks, name="search"),
    # User data endpoints
    path("watchlist/", views.WatchlistAPIView.as_view(), name="watchlist"),
]
