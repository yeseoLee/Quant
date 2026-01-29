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


class UserLogoutView(LogoutView):
    """User logout view."""

    next_page = reverse_lazy("accounts:login")


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
