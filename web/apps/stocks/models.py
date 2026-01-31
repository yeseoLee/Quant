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


class MomentumFactorScore(models.Model):
    """모멘텀 팩터 점수 저장."""

    STATE_CHOICES = [
        ("VERY_STRONG_BULLISH", "매우 강한 상승"),
        ("BULLISH", "상승"),
        ("SLIGHTLY_BULLISH", "약한 상승"),
        ("NEUTRAL", "중립"),
        ("SLIGHTLY_BEARISH", "약한 하락"),
        ("BEARISH", "하락"),
        ("VERY_STRONG_BEARISH", "매우 강한 하락"),
        ("INSUFFICIENT_DATA", "데이터 부족"),
    ]

    stock = models.ForeignKey(
        StockCache,
        on_delete=models.CASCADE,
        related_name="momentum_scores",
        verbose_name="종목",
    )
    analysis_date = models.DateField(verbose_name="분석 기준일")

    # 종합 점수
    total_score = models.FloatField(null=True, blank=True, verbose_name="종합 점수")
    signal = models.IntegerField(default=0, verbose_name="매매 신호")  # 1=buy, -1=sell, 0=hold
    state = models.CharField(
        max_length=30,
        choices=STATE_CHOICES,
        default="NEUTRAL",
        verbose_name="모멘텀 상태",
    )

    # 카테고리별 점수
    trend_score = models.FloatField(null=True, blank=True, verbose_name="추세 점수")
    oscillator_score = models.FloatField(null=True, blank=True, verbose_name="오실레이터 점수")
    volume_score = models.FloatField(null=True, blank=True, verbose_name="거래량 점수")

    # 개별 지표 점수 (JSON으로 저장)
    rsi_score = models.FloatField(null=True, blank=True, verbose_name="RSI 점수")
    macd_score = models.FloatField(null=True, blank=True, verbose_name="MACD 점수")
    adx_score = models.FloatField(null=True, blank=True, verbose_name="ADX 점수")
    roc_score = models.FloatField(null=True, blank=True, verbose_name="ROC 점수")
    stochastic_score = models.FloatField(null=True, blank=True, verbose_name="Stochastic 점수")
    cci_score = models.FloatField(null=True, blank=True, verbose_name="CCI 점수")
    williams_r_score = models.FloatField(null=True, blank=True, verbose_name="Williams %R 점수")
    bb_score = models.FloatField(null=True, blank=True, verbose_name="BB 점수")
    mfi_score = models.FloatField(null=True, blank=True, verbose_name="MFI 점수")
    obv_score = models.FloatField(null=True, blank=True, verbose_name="OBV 점수")
    volume_ma_score = models.FloatField(null=True, blank=True, verbose_name="VolumeMA 점수")

    # 메타데이터
    latest_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="최신 종가"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "모멘텀 팩터 점수"
        verbose_name_plural = "모멘텀 팩터 점수"
        unique_together = ["stock", "analysis_date"]
        indexes = [
            models.Index(fields=["stock", "-analysis_date"]),
            models.Index(fields=["-total_score"]),
            models.Index(fields=["state"]),
        ]
        ordering = ["-total_score"]

    def __str__(self):
        score_str = f"{self.total_score:.1f}" if self.total_score else "N/A"
        return f"{self.stock.symbol} - {self.analysis_date} (점수: {score_str})"
