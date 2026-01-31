# Quant - 한국 주식 퀀트 투자 분석

한국 주식 시장(KOSPI, KOSDAQ)을 대상으로 한 퀀트 투자 분석 프로젝트입니다.
FinanceDataReader와 yfinance를 활용하여 데이터를 수집하고, 다양한 기술적 지표와 팩터를 분석합니다.

## 주요 기능

- **기술적 지표 분석**: RSI, 볼린저 밴드, 스토캐스틱 등 모멘텀 지표
- **LPPL 버블 진단**: 소르네트 교수의 LPPL 모델 기반 버블 탐지 및 임계점 예측
- **매매신호 생성**: 과매수/과매도, 교차 전략 기반 자동 신호 생성
- **한국 시장 특화**: KOSPI 200 종목 관리, FinanceDataReader 통합

## 프로젝트 구조

```
quant/
├── src/quant/              # 메인 패키지
│   ├── data/               # 데이터 수집 모듈
│   │   ├── fetcher.py      # FDR/yfinance 통합 데이터 수집
│   │   └── kospi200.py     # KOSPI 200 종목 관리
│   ├── factors/            # 팩터 분석 모듈
│   │   ├── base.py         # 팩터 기본 클래스
│   │   └── momentum/       # 모멘텀 팩터
│   │       ├── rsi.py      # RSI 지표
│   │       ├── bollinger.py # 볼린저 밴드
│   │       └── stochastic.py # 스토캐스틱
│   ├── models/             # 분석 모델
│   │   └── lppl.py         # LPPL 버블 진단 모델
│   └── utils/              # 유틸리티
├── tests/                  # 테스트
├── notebooks/              # Jupyter 노트북
├── pyproject.toml          # 프로젝트 설정
└── Makefile                # 개발 명령어
```

## 설치

### 요구사항

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) 패키지 매니저

### uv 설치

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 프로젝트 설치

```bash
# 개발 의존성 포함 설치
make install-dev

# 또는 프로덕션만 설치
make install
```

## 사용된 라이브러리

### 데이터 수집

| 라이브러리                                                         | 용도                    |
| ------------------------------------------------------------------ | ----------------------- |
| [FinanceDataReader](https://github.com/FinanceData/FinanceDataReader) | 한국 주식 데이터 수집   |
| [yfinance](https://github.com/ranaroussi/yfinance)                    | 글로벌 주식 데이터 수집 |

### 데이터 처리

| 라이브러리                        | 용도                |
| --------------------------------- | ------------------- |
| [pandas](https://pandas.pydata.org/) | 데이터 처리 및 분석 |
| [numpy](https://numpy.org/)          | 수치 계산           |

### 기술적 분석

| 라이브러리                                       | 용도                    |
| ------------------------------------------------ | ----------------------- |
| [ta](https://github.com/bukosabino/ta)              | 기술적 분석 지표        |
| [pandas-ta](https://github.com/twopirllc/pandas-ta) | pandas 기반 기술적 분석 |

### 시각화

| 라이브러리                          | 용도            |
| ----------------------------------- | --------------- |
| [matplotlib](https://matplotlib.org/)  | 기본 차트       |
| [seaborn](https://seaborn.pydata.org/) | 통계 시각화     |
| [plotly](https://plotly.com/)          | 인터랙티브 차트 |

## 개발 명령어

```bash
# 코드 포맷팅
make format

# 린트 검사
make lint

# 포맷 & 린트 검사 (수정 없이)
make check

# 테스트 실행
make test

# 캐시 정리
make clean
```

## 사용 예시

### 데이터 수집

```python
from quant.data import DataFetcher, Kospi200

# KOSPI 200 종목 목록 조회
kospi200 = Kospi200()
symbols = kospi200.get_symbols()
print(f"KOSPI 200 종목 수: {len(symbols)}")

# 삼성전자 주가 데이터 수집
fetcher = DataFetcher()
df = fetcher.get_stock_data("005930", start_date="2026-01-01")
print(df.head())
```

### 기술적 분석

```python
from quant.factors import RSI, BollingerBands, Stochastic

# RSI 계산
rsi = RSI(period=14)
df_rsi = rsi.calculate(df)
signals = rsi.get_signal(df_rsi)

# 볼린저 밴드 계산
bb = BollingerBands(period=20, std_dev=2.0)
df_bb = bb.calculate(df)

# 스토캐스틱 계산
stoch = Stochastic(k_period=14, d_period=3)
df_stoch = stoch.calculate(df)
```

## 구현된 팩터

### 모멘텀 팩터

| 지표                  | 설명                              | 매개변수                     |
| --------------------- | --------------------------------- | ---------------------------- |
| **RSI**               | 상대강도지수 - 과매수/과매도 판단 | period, overbought, oversold |
| **Bollinger Bands**   | 변동성 밴드 - 가격 밴드 이탈 신호 | period, std_dev              |
| **Stochastic**        | 스토캐스틱 - %K, %D 교차 신호     | k_period, d_period, smooth_k |
| **MACD**              | 이동평균 수렴확산 - 추세 추종     | fast, slow, signal           |
| **ADX**               | 평균 방향성 지수 - 추세 강도      | period, trend_threshold      |
| **CCI**               | 상품 채널 지수 - 가격 편차        | period, overbought, oversold |
| **Williams %R**       | 윌리엄스 %R - 과매수/과매도       | period, overbought, oversold |
| **ROC**               | 변화율 - 모멘텀 측정              | period, signal_period        |
| **MFI**               | 자금 흐름 지수 - 볼륨 가중 RSI    | period, overbought, oversold |
| **VolumeMA**          | 거래량 이동평균 - 거래량 분석     | period, threshold            |
| **OBV**               | 누적 거래량 - 거래량 추세         | signal_period                |

### 모멘텀 팩터 종합 점수 (MomentumFactor)

11개 기술적 지표를 가중 평균하여 **0-100 점수**로 종합합니다:

| 카테고리      | 비중  | 포함 지표                        |
| ------------- | ----- | -------------------------------- |
| **Trend**     | 40%   | RSI, MACD, ADX, ROC              |
| **Oscillator**| 35%   | Stochastic, CCI, Williams %R, BB |
| **Volume**    | 25%   | MFI, OBV, VolumeMA               |

**점수 해석**:
- 80-100: 매우 강한 상승 모멘텀 (매수 신호)
- 65-80: 상승 모멘텀 (매수 신호)
- 45-65: 중립
- 20-45: 하락 모멘텀 (매도 신호)
- 0-20: 매우 강한 하락 모멘텀 (매도 신호)

> 📖 매매신호 로직에 대한 자세한 설명은 [TRADING_SIGNALS.md](./TRADING_SIGNALS.md)를 참조하세요.

---

## LPPL 버블 진단 모델

### 개요

LPPL(Log-Periodic Power Law) 모델은 디디에 소르네트(Didier Sornette) 교수가 개발한 금융 버블 탐지 모델입니다.
시장의 임계점(critical time) 근처에서 나타나는 로그-주기적 진동 패턴을 포착하여 버블의 형성과 붕괴를 예측합니다.

### 핵심 기능

- **버블 패턴 탐지**: 로그-주기적 진동(log-periodic oscillations) 패턴 분석
- **임계점 예측**: 버블이 최고조에 달하는 시점(tc) 추정
- **신뢰도 계산**: 파라미터 검증을 통한 버블 신뢰도 산출
- **LPPLS Confidence Indicator**: 다중 윈도우 분석을 통한 신뢰도 지표 (126개 윈도우)
- **결과 캐싱**: DB에 분석 결과 저장, 증분 업데이트 지원

### LPPL 수식

```
ln(p(t)) = A + B(tc - t)^m + C(tc - t)^m * cos(ω * ln(tc - t) + φ)
```

### 버블 상태 분류

| 상태               | 신뢰도 | 조건           | 의미                    |
| ------------------ | ------ | -------------- | ----------------------- |
| **CRITICAL** | ≥75%  | tc가 60일 이내 | 매우 위험 - 임박한 조정 |
| **WARNING**  | ≥75%  | tc가 60일 이후 | 버블 경고 - 주의 필요   |
| **WATCH**    | ≥50%  | -              | 버블 가능성 - 모니터링  |
| **NORMAL**   | <50%   | -              | 정상 범위               |

### 사용 예시

```python
from quant.models import LPPL
import pandas as pd

# 가격 데이터 준비
prices = pd.Series([...], index=pd.DatetimeIndex([...]))

# LPPL 모델 피팅
lppl = LPPL()
params = lppl.fit(prices)

# 버블 진단
diagnosis = lppl.diagnose_bubble(prices)
print(f"상태: {diagnosis['state']}")
print(f"신뢰도: {diagnosis['confidence']}%")
print(f"예상 임계점: {diagnosis['critical_date']}")

# 예측
fitted, forecast = lppl.forecast(prices, forecast_days=60)
```

> 📖 LPPL 모델에 대한 상세 이론과 해석 가이드는 [LPPL_MODEL.md](./LPPL_MODEL.md)를 참조하세요.

---

## 문서

| 문서                                    | 설명                                                          |
| --------------------------------------- | ------------------------------------------------------------- |
| [LPPL_MODEL.md](./LPPL_MODEL.md)           | LPPL 버블 진단 모델 상세 가이드 - 이론, 파라미터, 해석 방법   |
| [TRADING_SIGNALS.md](./TRADING_SIGNALS.md) | 매매신호 로직 가이드 - RSI, 볼린저 밴드, 스토캐스틱 신호 설명 |
| [CLAUDE.md](./CLAUDE.md)                   | Claude Code 개발 가이드 - 빌드, 테스트, 아키텍처              |

---

## 향후 계획

- [x] CCI (Commodity Channel Index)
- [x] Williams %R
- [x] MACD 지표 추가
- [x] MFI (Money Flow Index)
- [x] ADX (Average Directional Index)
- [x] ROC (Rate of Change)
- [x] 모멘텀 팩터 종합 점수 시스템
- [x] LPPL 분석 결과 캐싱
- [ ] 이동평균 크로스오버 전략
- [ ] 가치 팩터 (PER, PBR, ROE)
- [ ] 품질 팩터 (수익성, 안정성)
- [ ] KOSPI, KOSDAQ 전체 종목 지원
- [ ] 백테스팅 프레임워크
- [ ] 포트폴리오 최적화
- [ ] VIX Index Decomposition
- [ ] Gamma Exposure Calculation

## 라이선스

MIT License
