"""Views for stocks app."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.generic import TemplateView

from apps.accounts.models import Watchlist

from .services import StockService


class DashboardView(TemplateView):
    """Main dashboard view."""

    template_name = "stocks/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = StockService()

        # Get KOSPI200 stocks for quick access
        try:
            stocks = service.get_kospi200_list()[:20]  # Top 20
            context["popular_stocks"] = stocks
        except Exception:
            context["popular_stocks"] = []

        # Get user's watchlist if authenticated
        if self.request.user.is_authenticated:
            context["watchlist"] = Watchlist.objects.filter(user=self.request.user)[:5]

        return context


class StockDetailView(TemplateView):
    """Stock detail view with chart and indicators."""

    template_name = "stocks/stock_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        symbol = kwargs.get("symbol")
        context["symbol"] = symbol

        service = StockService()
        try:
            stock_info = service.get_stock_info(symbol)
            context["stock_info"] = stock_info
            context["stock_name"] = stock_info.get("name", symbol) if stock_info else symbol
        except Exception:
            context["stock_info"] = None
            context["stock_name"] = symbol

        # Check if in user's watchlist
        if self.request.user.is_authenticated:
            context["in_watchlist"] = Watchlist.objects.filter(
                user=self.request.user, symbol=symbol
            ).exists()

        return context


class ScreenerView(TemplateView):
    """KOSPI200 momentum factor screening view."""

    template_name = "stocks/screener.html"


class SearchResultsView(TemplateView):
    """Stock search results view."""

    template_name = "stocks/search_results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()
        context["query"] = query

        if query and len(query) >= 2:
            service = StockService()
            try:
                results = service.search_stocks(query)
                context["results"] = results
            except Exception as e:
                context["results"] = []
                context["error"] = str(e)
        else:
            context["results"] = []

        return context


@login_required
def add_to_watchlist(request, symbol):
    """Add stock to user's watchlist."""
    if request.method == "POST":
        service = StockService()
        try:
            stock_info = service.get_stock_info(symbol)
            name = stock_info.get("name", symbol) if stock_info else symbol
        except Exception:
            name = symbol

        _, created = Watchlist.objects.get_or_create(
            user=request.user,
            symbol=symbol,
            defaults={"name": name},
        )

        if created:
            messages.success(request, f"{name}이(가) 관심종목에 추가되었습니다.")
        else:
            messages.info(request, f"{name}은(는) 이미 관심종목에 있습니다.")

    return redirect("stocks:stock_detail", symbol=symbol)


@login_required
def remove_from_watchlist(request, symbol):
    """Remove stock from user's watchlist."""
    if request.method == "POST":
        deleted, _ = Watchlist.objects.filter(user=request.user, symbol=symbol).delete()

        if deleted:
            messages.success(request, "관심종목에서 삭제되었습니다.")

    return redirect("stocks:stock_detail", symbol=symbol)


def search_stocks(request):
    """Search stocks by symbol or name."""
    query = request.GET.get("q", "").strip()
    if not query or len(query) < 2:
        return JsonResponse({"results": []})

    service = StockService()
    try:
        results = service.search_stocks(query)
        return JsonResponse({"results": results[:10]})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
