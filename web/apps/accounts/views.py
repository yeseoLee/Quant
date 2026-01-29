"""Views for accounts app."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView

from .forms import LoginForm, RegisterForm
from .models import Watchlist


class UserLoginView(LoginView):
    """User login view."""

    template_name = "accounts/login.html"
    form_class = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        # Clear guest session if exists
        if "is_guest" in self.request.session:
            del self.request.session["is_guest"]
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    """User logout view."""

    next_page = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        # Clear guest session if exists
        if "is_guest" in request.session:
            del request.session["is_guest"]
        return super().dispatch(request, *args, **kwargs)


class UserRegisterView(CreateView):
    """User registration view."""

    template_name = "accounts/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("stocks:dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("stocks:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Clear guest session if exists
        if "is_guest" in self.request.session:
            del self.request.session["is_guest"]
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "회원가입이 완료되었습니다.")
        return response


class WatchlistView(LoginRequiredMixin, ListView):
    """User's watchlist view."""

    template_name = "accounts/watchlist.html"
    context_object_name = "watchlist"

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)


class WatchlistDeleteView(LoginRequiredMixin, DeleteView):
    """Delete item from watchlist."""

    model = Watchlist
    success_url = reverse_lazy("accounts:watchlist")

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "관심종목에서 삭제되었습니다.")
        return super().delete(request, *args, **kwargs)


def guest_login(request):
    """Guest login view - allows users to use the site without an account."""
    # Set guest session flag
    request.session["is_guest"] = True
    messages.info(request, "게스트로 이용 중입니다. 관심종목 기능은 로그인 후 이용 가능합니다.")
    return redirect("stocks:dashboard")
