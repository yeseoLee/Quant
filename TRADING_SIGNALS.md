# 매매신호 로직 가이드

이 문서는 Korean Stock Quant 시스템에서 사용하는 기술적 지표 기반 매매신호 생성 로직을 설명합니다.

## 개요

모든 매매신호는 다음 세 가지 값 중 하나를 반환합니다:
- **1**: 매수 신호 (Buy)
- **-1**: 매도 신호 (Sell)
- **0**: 관망 신호 (Hold)

각 기술적 지표는 `BaseFactor` 클래스를 상속받아 두 가지 핵심 메서드를 구현합니다:
- `calculate()`: 지표 값을 계산
- `get_signal()`: 매매신호를 생성

---

## 1. RSI (Relative Strength Index)

### 지표 설명
RSI는 가격 변동의 속도와 크기를 측정하는 모멘텀 지표입니다.
- 0~100 사이의 값을 가집니다
- 일반적으로 14일 기간을 사용합니다

### 매개변수
```python
period: int = 14          # RSI 계산 기간
overbought: float = 70.0  # 과매수 기준선
oversold: float = 30.0    # 과매도 기준선
```

### 매매신호 로직

#### 매수 신호 (1)
```
조건: RSI가 과매도 수준을 상향 돌파
- 현재 RSI > oversold (30)
- 이전 RSI <= oversold (30)
```

**해석**: RSI가 과매도 구간(30 이하)에서 벗어나면서 상승 반전을 시도하는 시점입니다. 과매도 상태가 해소되면서 매수 압력이 증가할 가능성이 있습니다.

#### 매도 신호 (-1)
```
조건: RSI가 과매수 수준을 하향 돌파
- 현재 RSI < overbought (70)
- 이전 RSI >= overbought (70)
```

**해석**: RSI가 과매수 구간(70 이상)에서 하락하기 시작하는 시점입니다. 과매수 상태가 해소되면서 조정 가능성이 높아집니다.

### 코드 위치
`src/quant/factors/momentum/rsi.py`

---

## 2. Bollinger Bands (볼린저 밴드)

### 지표 설명
가격의 변동성을 측정하는 지표로, 이동평균선을 중심으로 표준편차 배수만큼 상하단 밴드를 그립니다.

**구성 요소**:
- **상단 밴드**: 중간선 + (표준편차 × 배수)
- **중간 밴드**: 이동평균선 (SMA)
- **하단 밴드**: 중간선 - (표준편차 × 배수)

### 매개변수
```python
period: int = 20        # 이동평균 계산 기간
std_dev: float = 2.0    # 표준편차 배수
```

### 매매신호 로직

#### 매수 신호 (1)
```
조건: 가격이 하단 밴드 이하로 하락
- close <= bb_lower
```

**해석**: 가격이 통계적으로 과도하게 낮은 수준(하단 밴드 이하)에 도달했습니다. 평균 회귀(mean reversion) 관점에서 반등 가능성이 있습니다.

#### 매도 신호 (-1)
```
조건: 가격이 상단 밴드 이상으로 상승
- close >= bb_upper
```

**해석**: 가격이 통계적으로 과도하게 높은 수준(상단 밴드 이상)에 도달했습니다. 평균 회귀 관점에서 조정 가능성이 있습니다.

### 추가 정보
볼린저 밴드는 다음과 같은 추가 지표도 제공합니다:
- **bb_bandwidth**: 밴드 폭 (변동성 측정)
- **bb_percent**: 현재 가격이 밴드 내에서 차지하는 상대적 위치 (0~1)

### 코드 위치
`src/quant/factors/momentum/bollinger.py`

---

## 3. Stochastic Oscillator (스토캐스틱)

### 지표 설명
일정 기간 동안의 최고가와 최저가 범위 내에서 현재 종가의 상대적 위치를 나타냅니다.

**구성 요소**:
- **%K**: 빠른 스토캐스틱 라인 (Fast line)
- **%D**: 느린 스토캐스틱 라인 (%K의 이동평균, Slow line)

### 매개변수
```python
k_period: int = 14        # %K 계산 기간
d_period: int = 3         # %D 평활 기간
smooth_k: int = 3         # %K 평활 기간
overbought: float = 80.0  # 과매수 기준선
oversold: float = 20.0    # 과매도 기준선
```

### 매매신호 로직

#### 매수 신호 (1)
```
조건: %K가 %D를 상향 교차하면서 과매도 구간
- 현재 %K > %D
- 이전 %K <= %D (교차 확인)
- 현재 %K < oversold (20)
```

**해석**:
1. 과매도 구간(20 미만)에서 발생하는 신호만 채택
2. %K가 %D를 상향 돌파하면서 반등 모멘텀 확인
3. 강한 매수 신호로 간주

#### 매도 신호 (-1)
```
조건: %K가 %D를 하향 교차하면서 과매수 구간
- 현재 %K < %D
- 이전 %K >= %D (교차 확인)
- 현재 %K > overbought (80)
```

**해석**:
1. 과매수 구간(80 초과)에서 발생하는 신호만 채택
2. %K가 %D를 하향 돌파하면서 조정 모멘텀 확인
3. 강한 매도 신호로 간주

### 특징
Stochastic은 **교차(crossover)** 전략을 사용하므로:
- 단순히 과매수/과매도 영역 진입만으로는 신호를 생성하지 않음
- 반드시 %K와 %D의 교차가 필요함
- 과매수/과매도 영역 내에서의 교차만 유효한 신호로 간주

### 코드 위치
`src/quant/factors/momentum/stochastic.py`

---

## 4. MACD (Moving Average Convergence Divergence)

### 지표 설명
MACD는 두 이동평균선의 차이와 그 신호선을 이용한 추세 추종 지표입니다.

**구성 요소**:
- **MACD Line**: 빠른 EMA - 느린 EMA
- **Signal Line**: MACD의 EMA
- **Histogram**: MACD - Signal

### 매개변수
```python
fast_period: int = 12    # 빠른 EMA 기간
slow_period: int = 26    # 느린 EMA 기간
signal_period: int = 9   # 신호선 기간
```

### 매매신호 로직

#### 매수 신호 (1)
```
조건: MACD가 Signal Line을 상향 돌파
- 현재 MACD > Signal
- 이전 MACD <= Signal
```

#### 매도 신호 (-1)
```
조건: MACD가 Signal Line을 하향 돌파
- 현재 MACD < Signal
- 이전 MACD >= Signal
```

### 코드 위치
`src/quant/factors/momentum/macd.py`

---

## 5. ADX (Average Directional Index)

### 지표 설명
ADX는 추세의 강도를 측정합니다. 방향과 관계없이 추세의 세기만 판단합니다.
- **ADX > 25**: 강한 추세
- **ADX < 20**: 약한 추세 또는 횡보

### 매개변수
```python
period: int = 14              # ADX 계산 기간
trend_threshold: float = 25.0 # 강한 추세 기준
```

### 매매신호 로직

#### 매수 신호 (1)
```
조건: +DI가 -DI를 상향 돌파하고 ADX가 강한 추세
- +DI > -DI
- 이전 +DI <= -DI
- ADX > trend_threshold (25)
```

#### 매도 신호 (-1)
```
조건: -DI가 +DI를 상향 돌파하고 ADX가 강한 추세
- -DI > +DI
- 이전 -DI <= +DI
- ADX > trend_threshold (25)
```

### 코드 위치
`src/quant/factors/momentum/adx.py`

---

## 6. CCI (Commodity Channel Index)

### 지표 설명
CCI는 가격이 통계적 평균에서 얼마나 벗어났는지 측정합니다.
- **CCI > 100**: 과매수 (강한 상승 추세)
- **CCI < -100**: 과매도 (강한 하락 추세)

### 매개변수
```python
period: int = 20              # CCI 계산 기간
overbought: float = 100.0     # 과매수 기준
oversold: float = -100.0      # 과매도 기준
```

### 매매신호 로직

#### 매수 신호 (1)
```
조건: CCI가 과매도 수준을 상향 돌파
- 현재 CCI > oversold (-100)
- 이전 CCI <= oversold (-100)
```

#### 매도 신호 (-1)
```
조건: CCI가 과매수 수준을 하향 돌파
- 현재 CCI < overbought (100)
- 이전 CCI >= overbought (100)
```

### 코드 위치
`src/quant/factors/momentum/cci.py`

---

## 7. Williams %R

### 지표 설명
Williams %R은 스토캐스틱과 유사하나 역전된 스케일(-100 ~ 0)을 사용합니다.
- **%R > -20**: 과매수
- **%R < -80**: 과매도

### 매개변수
```python
period: int = 14              # 계산 기간
overbought: float = -20.0     # 과매수 기준
oversold: float = -80.0       # 과매도 기준
```

### 매매신호 로직

#### 매수 신호 (1)
```
조건: %R이 과매도 수준을 상향 돌파
- 현재 %R > oversold (-80)
- 이전 %R <= oversold (-80)
```

#### 매도 신호 (-1)
```
조건: %R이 과매수 수준을 하향 돌파
- 현재 %R < overbought (-20)
- 이전 %R >= overbought (-20)
```

### 코드 위치
`src/quant/factors/momentum/williams_r.py`

---

## 8. ROC (Rate of Change)

### 지표 설명
ROC는 현재 가격과 n일 전 가격의 백분율 변화를 측정합니다.
- **ROC > 0**: 상승 추세
- **ROC < 0**: 하락 추세

### 매개변수
```python
period: int = 12          # 계산 기간
signal_period: int = 9    # 신호선 기간
```

### 매매신호 로직

#### 매수 신호 (1)
```
조건: ROC가 0을 상향 돌파
- 현재 ROC > 0
- 이전 ROC <= 0
```

#### 매도 신호 (-1)
```
조건: ROC가 0을 하향 돌파
- 현재 ROC < 0
- 이전 ROC >= 0
```

### 코드 위치
`src/quant/factors/momentum/roc.py`

---

## 9. MFI (Money Flow Index)

### 지표 설명
MFI는 거래량을 가중한 RSI입니다. 가격과 거래량을 함께 분석합니다.
- **MFI > 80**: 과매수
- **MFI < 20**: 과매도

### 매개변수
```python
period: int = 14              # 계산 기간
overbought: float = 80.0      # 과매수 기준
oversold: float = 20.0        # 과매도 기준
```

### 매매신호 로직

#### 매수 신호 (1)
```
조건: MFI가 과매도 수준을 상향 돌파
- 현재 MFI > oversold (20)
- 이전 MFI <= oversold (20)
```

#### 매도 신호 (-1)
```
조건: MFI가 과매수 수준을 하향 돌파
- 현재 MFI < overbought (80)
- 이전 MFI >= overbought (80)
```

### 코드 위치
`src/quant/factors/momentum/mfi.py`

---

## 10. 모멘텀 팩터 종합 점수 (MomentumFactor)

### 개요
MomentumFactor는 11개 기술적 지표를 가중 평균하여 0-100 점수로 종합합니다.

### 카테고리별 가중치

| 카테고리 | 비중 | 포함 지표 |
|---------|------|----------|
| **Trend** | 40% | RSI(12%), MACD(10%), ADX(10%), ROC(8%) |
| **Oscillator** | 35% | Stochastic(10%), CCI(8%), Williams %R(8%), BB(9%) |
| **Volume** | 25% | MFI(10%), OBV(8%), VolumeMA(7%) |

### 점수 해석

| 점수 범위 | 상태 | 신호 | 의미 |
|----------|------|------|------|
| 80-100 | VERY_STRONG_BULLISH | 매수 | 매우 강한 상승 모멘텀 |
| 65-80 | BULLISH | 매수 | 상승 모멘텀 |
| 55-65 | SLIGHTLY_BULLISH | 관망 | 약한 상승 모멘텀 |
| 45-55 | NEUTRAL | 관망 | 중립 |
| 35-45 | SLIGHTLY_BEARISH | 관망 | 약한 하락 모멘텀 |
| 20-35 | BEARISH | 매도 | 하락 모멘텀 |
| 0-20 | VERY_STRONG_BEARISH | 매도 | 매우 강한 하락 모멘텀 |

### 사용 예시
```python
from quant.factors import MomentumFactor

momentum = MomentumFactor()
result = momentum.calculate(df)

print(f"종합 점수: {result['total_score']}")
print(f"상태: {result['state']}")
print(f"신호: {result['signal']}")
print(f"추세 점수: {result['category_scores']['trend']}")
print(f"오실레이터 점수: {result['category_scores']['oscillator']}")
print(f"거래량 점수: {result['category_scores']['volume']}")
```

### 코드 위치
`src/quant/factors/momentum_factor.py`

---

## 신호 해석 가이드

### 1. 신호 강도
각 지표의 신호는 다른 강도와 특성을 가집니다:

| 지표 | 신호 유형 | 장점 | 단점 |
|------|----------|------|------|
| RSI | 반전 신호 | 명확한 임계값, 구현 간단 | 횡보장에서 거짓 신호 |
| Bollinger Bands | 평균 회귀 | 변동성 적응적 | 추세장에서 지속적 신호 |
| Stochastic | 교차 신호 | 과매수/과매도 구간 필터링 | 지연 발생 가능 |
| MACD | 추세 추종 | 추세 방향 명확 | 횡보장에서 비효율적 |
| ADX | 추세 강도 | 추세 여부 판단 | 방향 제시 없음 |
| CCI | 평균 편차 | 변동성 감지 | 극단값 발생 가능 |
| Williams %R | 반전 신호 | 빠른 반응 | 잦은 신호 발생 |
| ROC | 모멘텀 | 추세 전환 감지 | 노이즈에 민감 |
| MFI | 볼륨 가중 | 거래량 반영 | 복잡한 해석 |
| MomentumFactor | 종합 점수 | 다중 지표 통합 | 계산 비용 높음 |

### 2. 복합 전략
더 신뢰성 있는 매매 결정을 위해 여러 지표를 조합할 수 있습니다:

**예시: 강한 매수 신호**
```
RSI 매수 신호 (1) + Bollinger Bands 매수 신호 (1)
→ 두 지표가 동시에 매수를 제안하는 경우
```

**예시: 신호 필터링**
```
RSI가 과매도 구간(< 30)일 때만 Bollinger Bands 하단 돌파 신호를 채택
→ 거짓 신호 감소
```

### 3. 신호 빈도
각 지표의 특성상 신호 발생 빈도가 다릅니다:
- **RSI**: 중간 빈도 (임계값 돌파 시점에만)
- **Bollinger Bands**: 높은 빈도 (밴드 터치 시마다)
- **Stochastic**: 낮은 빈도 (교차 + 과매수/과매도 조건)

---

## 구현 세부사항

### 데이터 요구사항
모든 지표는 다음 OHLCV 컬럼을 필요로 합니다 (소문자):
- `open`: 시가
- `high`: 고가
- `low`: 저가
- `close`: 종가
- `volume`: 거래량

### 계산 라이브러리
모든 기술적 지표는 [pandas-ta](https://github.com/twopirllc/pandas-ta) 라이브러리를 사용하여 계산됩니다:
- `ta.rsi()`: RSI 계산
- `ta.bbands()`: Bollinger Bands 계산
- `ta.stoch()`: Stochastic Oscillator 계산
- `ta.macd()`: MACD 계산
- `ta.adx()`: ADX 계산
- `ta.cci()`: CCI 계산
- `ta.willr()`: Williams %R 계산
- `ta.roc()`: ROC 계산
- `ta.mfi()`: MFI 계산
- `ta.obv()`: OBV 계산
- `ta.sma()`: 이동평균 계산

### 신호 생성 흐름
```python
# 1. 데이터 준비
df = get_ohlcv_data(symbol)

# 2. 지표 초기화
rsi = RSI(period=14, overbought=70, oversold=30)

# 3. 지표 값 계산
df_with_indicator = rsi.calculate(df)

# 4. 매매신호 생성
signals = rsi.get_signal(df_with_indicator)
# signals: Series with values 1, -1, or 0
```

---

## 주의사항

### 1. 백테스팅 필요
- 모든 매매신호는 과거 데이터 기반 패턴입니다
- 실전 투자 전 반드시 백테스팅을 수행하세요
- 거래 비용, 슬리피지 등을 고려하세요

### 2. 리스크 관리
- 단일 지표에만 의존하지 마세요
- 손절매(stop-loss) 전략을 함께 사용하세요
- 포지션 크기를 적절히 관리하세요

### 3. 시장 상황 고려
- **추세장**: Stochastic 신호가 덜 유효할 수 있음
- **횡보장**: RSI, Bollinger Bands가 효과적
- **변동성 큰 장**: Bollinger Bands 밴드 폭이 넓어짐

### 4. 한계점
- 과거 가격만 사용하므로 미래를 보장하지 않음
- 뉴스, 펀더멘털 변화를 반영하지 못함
- 갑작스러운 시장 충격에 대응 불가

---

## 커스터마이징

### 파라미터 조정
각 지표의 매개변수는 종목 특성과 투자 기간에 따라 조정할 수 있습니다:

```python
# 단기 트레이딩
rsi_short = RSI(period=7, overbought=65, oversold=35)

# 장기 투자
rsi_long = RSI(period=21, overbought=75, oversold=25)

# 변동성이 큰 종목
bb_volatile = BollingerBands(period=20, std_dev=3.0)
```

### 새로운 지표 추가
`BaseFactor`를 상속받아 새로운 지표를 추가할 수 있습니다:

```python
from quant.factors.base import BaseFactor

class MyIndicator(BaseFactor):
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        # 지표 값 계산
        pass

    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        # 매매신호 생성
        pass
```

자세한 내용은 `CLAUDE.md`의 "Adding New Factors" 섹션을 참조하세요.

---

## 참고 자료

- [Technical Analysis Library (pandas-ta)](https://github.com/twopirllc/pandas-ta)
- [RSI 설명 (Investopedia)](https://www.investopedia.com/terms/r/rsi.asp)
- [Bollinger Bands 설명 (Investopedia)](https://www.investopedia.com/terms/b/bollingerbands.asp)
- [Stochastic Oscillator 설명 (Investopedia)](https://www.investopedia.com/terms/s/stochasticoscillator.asp)

---

**마지막 업데이트**: 2026-01-31
**버전**: 2.0.0
