"""API views for stock data."""

import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.models import AnalysisHistory
from apps.stocks.services import StockService


class OHLCVView(View):
    """API endpoint for OHLCV candlestick data."""

    def get(self, request, symbol):
        start_date = request.GET.get("start")
        end_date = request.GET.get("end")

        service = StockService()
        try:
            data = service.get_ohlcv_json(symbol, start_date, end_date)
            return JsonResponse({"symbol": symbol, "data": data})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class IndicatorView(View):
    """API endpoint for technical indicator data."""

    def get(self, request, symbol, indicator):
        start_date = request.GET.get("start")
        end_date = request.GET.get("end")

        # Parse indicator parameters from query string
        params = {}
        if indicator == "RSI":
            if request.GET.get("period"):
                params["period"] = int(request.GET.get("period"))
            if request.GET.get("overbought"):
                params["overbought"] = float(request.GET.get("overbought"))
            if request.GET.get("oversold"):
                params["oversold"] = float(request.GET.get("oversold"))
        elif indicator == "BB":
            if request.GET.get("period"):
                params["period"] = int(request.GET.get("period"))
            if request.GET.get("std_dev"):
                params["std_dev"] = float(request.GET.get("std_dev"))
        elif indicator == "STOCH":
            if request.GET.get("k_period"):
                params["k_period"] = int(request.GET.get("k_period"))
            if request.GET.get("d_period"):
                params["d_period"] = int(request.GET.get("d_period"))
            if request.GET.get("smooth_k"):
                params["smooth_k"] = int(request.GET.get("smooth_k"))

        service = StockService()
        try:
            data = service.get_indicator_data(
                symbol, indicator, params, start_date, end_date
            )
            return JsonResponse({"symbol": symbol, **data})
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class SignalsView(View):
    """API endpoint for trading signals."""

    def get(self, request, symbol, indicator):
        start_date = request.GET.get("start")
        end_date = request.GET.get("end")

        # Parse indicator parameters from query string
        params = {}
        if indicator == "RSI":
            if request.GET.get("period"):
                params["period"] = int(request.GET.get("period"))
            if request.GET.get("overbought"):
                params["overbought"] = float(request.GET.get("overbought"))
            if request.GET.get("oversold"):
                params["oversold"] = float(request.GET.get("oversold"))
        elif indicator == "BB":
            if request.GET.get("period"):
                params["period"] = int(request.GET.get("period"))
            if request.GET.get("std_dev"):
                params["std_dev"] = float(request.GET.get("std_dev"))
        elif indicator == "STOCH":
            if request.GET.get("k_period"):
                params["k_period"] = int(request.GET.get("k_period"))
            if request.GET.get("d_period"):
                params["d_period"] = int(request.GET.get("d_period"))
            if request.GET.get("smooth_k"):
                params["smooth_k"] = int(request.GET.get("smooth_k"))

        service = StockService()
        try:
            signals = service.get_signals(symbol, indicator, params, start_date, end_date)
            return JsonResponse({"symbol": symbol, "indicator": indicator, "signals": signals})
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class ScreenerView(View):
    """API endpoint for KOSPI200 screening."""

    def get(self, request):
        indicator = request.GET.get("indicator", "RSI")
        signal_filter = request.GET.get("signal")

        if signal_filter:
            signal_filter = int(signal_filter)

        # Parse indicator parameters
        params = {}
        if indicator == "RSI":
            if request.GET.get("period"):
                params["period"] = int(request.GET.get("period"))
        elif indicator == "BB":
            if request.GET.get("period"):
                params["period"] = int(request.GET.get("period"))
            if request.GET.get("std_dev"):
                params["std_dev"] = float(request.GET.get("std_dev"))
        elif indicator == "STOCH":
            if request.GET.get("k_period"):
                params["k_period"] = int(request.GET.get("k_period"))

        service = StockService()
        try:
            results = service.run_screener(indicator, params, signal_filter)
            return JsonResponse(
                {"indicator": indicator, "count": len(results), "results": results}
            )
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class Kospi200ListView(View):
    """API endpoint for KOSPI200 stock list."""

    def get(self, request):
        service = StockService()
        try:
            stocks = service.get_kospi200_list()
            return JsonResponse({"count": len(stocks), "stocks": stocks})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@require_GET
def search_stocks(request):
    """API endpoint for stock search."""
    query = request.GET.get("q", "").strip()
    if not query or len(query) < 2:
        return JsonResponse({"results": []})

    service = StockService()
    try:
        results = service.search_stocks(query)
        return JsonResponse({"results": results[:10]})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_POST
def save_analysis(request):
    """API endpoint to save analysis to history."""
    try:
        data = json.loads(request.body)
        symbol = data.get("symbol")
        name = data.get("name", symbol)
        indicator = data.get("indicator")
        parameters = data.get("parameters", {})
        signal = data.get("signal", 0)
        signal_date_str = data.get("signal_date")

        if not symbol or not indicator:
            return JsonResponse({"error": "symbol and indicator are required"}, status=400)

        if signal_date_str:
            signal_date = datetime.strptime(signal_date_str, "%Y-%m-%d").date()
        else:
            signal_date = datetime.now().date()

        history = AnalysisHistory.objects.create(
            user=request.user,
            symbol=symbol,
            name=name,
            indicator=indicator,
            parameters=parameters,
            signal=signal,
            signal_date=signal_date,
        )

        return JsonResponse({
            "success": True,
            "id": history.id,
            "message": "분석이 저장되었습니다.",
        })
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


class WatchlistAPIView(View):
    """API endpoint for watchlist operations."""

    @method_decorator(login_required)
    def get(self, request):
        """Get user's watchlist."""
        from apps.accounts.models import Watchlist

        watchlist = Watchlist.objects.filter(user=request.user)
        items = [
            {
                "id": item.pk,
                "symbol": item.symbol,
                "name": item.name,
                "notes": item.notes,
                "created_at": item.created_at.isoformat(),
            }
            for item in watchlist
        ]
        return JsonResponse({"watchlist": items})

    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Add stock to watchlist."""
        from apps.accounts.models import Watchlist

        try:
            data = json.loads(request.body)
            symbol = data.get("symbol")
            name = data.get("name", symbol)
            notes = data.get("notes", "")

            if not symbol:
                return JsonResponse({"error": "symbol is required"}, status=400)

            item, created = Watchlist.objects.get_or_create(
                user=request.user,
                symbol=symbol,
                defaults={"name": name, "notes": notes},
            )

            return JsonResponse({
                "success": True,
                "created": created,
                "id": item.pk,
            })
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def delete(self, request):
        """Remove stock from watchlist."""
        from apps.accounts.models import Watchlist

        try:
            data = json.loads(request.body)
            symbol = data.get("symbol")

            if not symbol:
                return JsonResponse({"error": "symbol is required"}, status=400)

            deleted, _ = Watchlist.objects.filter(
                user=request.user, symbol=symbol
            ).delete()

            return JsonResponse({
                "success": True,
                "deleted": deleted > 0,
            })
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
