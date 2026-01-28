"""URL configuration for Korean Stock Quant web application."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("api/", include("apps.api.urls")),
    path("", include("apps.stocks.urls")),
]
