"""Models for stocks app."""

from django.db import models


class StockCache(models.Model):
    """Cache for KOSPI200 stock information."""

    SYNC_STATUS_CHOICES = [
        ("pending", "대기중"),
        ("syncing", "동기화중"),
        ("completed", "완료"),
        ("failed", "실패"),
    ]

    symbol = models.CharField(max_length=20, primary_key=True, verbose_name="종목코드")
    name = models.CharField(max_length=100, verbose_name="종목명")
    market = models.CharField(max_length=20, default="KOSPI", verbose_name="시장")
    sector = models.CharField(max_length=100, blank=True, verbose_name="업종")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="갱신일시")

    # KOSPI200 sync fields
    is_kospi200 = models.BooleanField(default=False, verbose_name="KOSPI200 여부")
    last_price_date = models.DateField(null=True, blank=True, verbose_name="최종 가격 날짜")
    last_sync_at = models.DateTimeField(null=True, blank=True, verbose_name="마지막 동기화 시간")
    sync_status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default="pending",
        verbose_name="동기화 상태",
    )

    class Meta:
        verbose_name = "종목 캐시"
        verbose_name_plural = "종목 캐시"
        ordering = ["symbol"]

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class StockPrice(models.Model):
    """Daily OHLCV price data for stocks."""

    stock = models.ForeignKey(
        StockCache,
        on_delete=models.CASCADE,
        related_name="prices",
        verbose_name="종목",
    )
    date = models.DateField(verbose_name="날짜")
    open = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="시가")
    high = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="고가")
    low = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="저가")
    close = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="종가")
    volume = models.BigIntegerField(verbose_name="거래량")

    class Meta:
        verbose_name = "주가 데이터"
        verbose_name_plural = "주가 데이터"
        unique_together = ["stock", "date"]
        indexes = [
            models.Index(fields=["stock", "-date"]),
        ]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.stock.symbol} - {self.date}"


class SyncLog(models.Model):
    """Log of stock data synchronization operations."""

    SYNC_TYPE_CHOICES = [
        ("full", "전체 동기화"),
        ("incremental", "증분 동기화"),
        ("constituents", "구성종목 업데이트"),
    ]

    STATUS_CHOICES = [
        ("started", "시작됨"),
        ("running", "진행중"),
        ("completed", "완료"),
        ("failed", "실패"),
    ]

    sync_type = models.CharField(
        max_length=20,
        choices=SYNC_TYPE_CHOICES,
        verbose_name="동기화 유형",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="started",
        verbose_name="상태",
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="시작 시간")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="완료 시간")
    total_stocks = models.IntegerField(default=0, verbose_name="전체 종목 수")
    processed_stocks = models.IntegerField(default=0, verbose_name="처리된 종목 수")
    new_records = models.IntegerField(default=0, verbose_name="신규 레코드 수")
    error_message = models.TextField(blank=True, verbose_name="오류 메시지")

    class Meta:
        verbose_name = "동기화 로그"
        verbose_name_plural = "동기화 로그"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.get_sync_type_display()} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"


class LPPLAnalysisResult(models.Model):
    """LPPL 분석 결과 (마스터) - 캐싱용."""

    STATE_CHOICES = [
        ("CRITICAL", "위험"),
        ("WARNING", "경고"),
        ("WATCH", "주의"),
        ("NORMAL", "정상"),
    ]

    stock = models.ForeignKey(
        StockCache,
        on_delete=models.CASCADE,
        related_name="lppl_results",
        verbose_name="종목",
    )
    min_window = models.IntegerField(default=125, verbose_name="최소 윈도우")
    max_window = models.IntegerField(default=750, verbose_name="최대 윈도우")
    step = models.IntegerField(default=5, verbose_name="윈도우 간격")
    analysis_date = models.DateField(verbose_name="분석 기준일")

    # 결과 요약
    confidence_indicator = models.FloatField(verbose_name="LPPLS 신뢰도 지표")
    state = models.CharField(
        max_length=20,
        choices=STATE_CHOICES,
        verbose_name="상태",
    )
    message = models.CharField(max_length=200, verbose_name="메시지")

    # 통계
    total_windows = models.IntegerField(verbose_name="전체 윈도우 수")
    successful_fits = models.IntegerField(verbose_name="성공한 피팅 수")
    bubble_windows = models.IntegerField(verbose_name="버블 윈도우 수")
    success_rate = models.FloatField(verbose_name="피팅 성공률")

    computation_time = models.FloatField(null=True, blank=True, verbose_name="계산 시간(초)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")

    class Meta:
        verbose_name = "LPPL 분석 결과"
        verbose_name_plural = "LPPL 분석 결과"
        unique_together = ["stock", "analysis_date", "step"]
        indexes = [
            models.Index(fields=["stock", "-analysis_date"]),
        ]
        ordering = ["-analysis_date"]

    def __str__(self):
        return f"{self.stock.symbol} - {self.analysis_date} ({self.state})"


class LPPLWindowResult(models.Model):
    """개별 윈도우 결과 (디테일)."""

    analysis = models.ForeignKey(
        LPPLAnalysisResult,
        on_delete=models.CASCADE,
        related_name="window_results",
        verbose_name="분석 결과",
    )
    window_size = models.IntegerField(verbose_name="윈도우 크기")
    success = models.BooleanField(verbose_name="피팅 성공 여부")
    is_bubble = models.BooleanField(default=False, verbose_name="버블 조건 충족")

    # LPPL 파라미터 (피팅 성공시에만 값 존재)
    param_tc = models.FloatField(null=True, blank=True, verbose_name="tc (임계시점)")
    param_b = models.FloatField(null=True, blank=True, verbose_name="B (진폭)")
    param_m = models.FloatField(null=True, blank=True, verbose_name="m (지수)")
    param_omega = models.FloatField(null=True, blank=True, verbose_name="omega (각주파수)")
    residual_error = models.FloatField(null=True, blank=True, verbose_name="잔차 오차")

    error_message = models.TextField(blank=True, verbose_name="오류 메시지")

    class Meta:
        verbose_name = "LPPL 윈도우 결과"
        verbose_name_plural = "LPPL 윈도우 결과"
        unique_together = ["analysis", "window_size"]
        ordering = ["window_size"]

    def __str__(self):
        status = "버블" if self.is_bubble else ("성공" if self.success else "실패")
        return f"윈도우 {self.window_size}일 - {status}"
