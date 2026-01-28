# Quant - 한국 주식 퀀트 투자 분석

한국 주식 시장(KOSPI, KOSDAQ)을 대상으로 한 퀀트 투자 분석 프로젝트입니다.
FinanceDataReader와 yfinance를 활용하여 데이터를 수집하고, 다양한 기술적 지표와 팩터를 분석합니다.

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
| 라이브러리 | 용도 |
|-----------|------|
| [FinanceDataReader](https://github.com/FinanceData/FinanceDataReader) | 한국 주식 데이터 수집 |
| [yfinance](https://github.com/ranaroussi/yfinance) | 글로벌 주식 데이터 수집 |

### 데이터 처리
| 라이브러리 | 용도 |
|-----------|------|
| [pandas](https://pandas.pydata.org/) | 데이터 처리 및 분석 |
| [numpy](https://numpy.org/) | 수치 계산 |

### 기술적 분석
| 라이브러리 | 용도 |
|-----------|------|
| [ta](https://github.com/bukosabino/ta) | 기술적 분석 지표 |
| [pandas-ta](https://github.com/twopirllc/pandas-ta) | pandas 기반 기술적 분석 |

### 시각화
| 라이브러리 | 용도 |
|-----------|------|
| [matplotlib](https://matplotlib.org/) | 기본 차트 |
| [seaborn](https://seaborn.pydata.org/) | 통계 시각화 |
| [plotly](https://plotly.com/) | 인터랙티브 차트 |

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

| 지표 | 설명 | 매개변수 |
|------|------|----------|
| **RSI** | 상대강도지수 - 과매수/과매도 판단 | period, overbought, oversold |
| **Bollinger Bands** | 변동성 밴드 - 가격 밴드 이탈 신호 | period, std_dev |
| **Stochastic** | 스토캐스틱 - %K, %D 교차 신호 | k_period, d_period, smooth_k |

## 향후 계획

- [ ] MACD 지표 추가
- [ ] 이동평균 크로스오버 전략
- [ ] 가치 팩터 (PER, PBR, ROE)
- [ ] 품질 팩터 (수익성, 안정성)
- [ ] KOSPI, KOSDAQ 전체 종목 지원
- [ ] 백테스팅 프레임워크
- [ ] 포트폴리오 최적화

## 라이선스

MIT License
