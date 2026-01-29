"""User and related models for accounts app."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model extending Django's AbstractUser."""

    class Meta:
        verbose_name = "사용자"
        verbose_name_plural = "사용자들"

    def __str__(self):
        return self.username


class Watchlist(models.Model):
    """User's watchlist for favorite stocks."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="watchlist",
        verbose_name="사용자",
    )
    symbol = models.CharField(max_length=20, verbose_name="종목코드")
    name = models.CharField(max_length=100, verbose_name="종목명")
    notes = models.TextField(blank=True, verbose_name="메모")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="추가일시")

    class Meta:
        verbose_name = "관심종목"
        verbose_name_plural = "관심종목"
        unique_together = ["user", "symbol"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.symbol} ({self.name})"
