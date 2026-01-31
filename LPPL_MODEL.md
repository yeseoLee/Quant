# LPPL 모델 버블 진단 가이드

## 개요

LPPL(Log-Periodic Power Law) 모델은 디디에 소르네트(Didier Sornette) 교수가 개발한 금융 버블 탐지 모델입니다. 이 모델은 시장의 임계점(critical time) 근처에서 나타나는 로그-주기적 진동(log-periodic oscillations) 패턴을 포착하여 버블의 형성과 붕괴를 예측합니다.

## 이론적 배경

### 소르네트 교수의 연구

디디에 소르네트(Didier Sornette)는 스위스 취리히 연방공과대학(ETH Zurich)의 교수로, 복잡계 물리학과 금융시장 위기 예측 분야의 권위자입니다. 그의 대표 저서 "Why Stock Markets Crash: Critical Events in Complex Financial Systems" (2003)에서 LPPL 모델의 이론적 기초를 제시했습니다.

**핵심 통찰**:
- 금융 버블은 투자자들의 모방 행동(herding behavior)으로 인한 양의 피드백 루프
- 가격이 기하급수적으로 상승하면서 동시에 로그-주기적 진동 발생
- 임계점(tc)에 도달하면 시스템이 붕괴(crash) 또는 방향 전환

### LPPL 모델 수식

```
ln(p(t)) = A + B(tc - t)^m + C(tc - t)^m * cos(ω * ln(tc - t) + φ)
```

**파라미터 설명**:

| 파라미터 | 의미 | 일반적 범위 | 버블 조건 |
|---------|------|------------|----------|
| **tc** | 임계 시간 (Critical Time) | 현재 ~ 미래 | 합리적 미래 시점 |
| **A** | 임계점에서의 로그 가격 | - | - |
| **B** | 진폭 (Amplitude) | 음수 | B < 0 (버블) |
| **m** | 멱법칙 지수 (Power Law Exponent) | 0.1 ~ 0.9 | 0.1 ≤ m ≤ 0.9 |
| **C** | 진동 진폭 (Oscillation Amplitude) | -1 ~ 1 | - |
| **ω** | 각 주파수 (Angular Frequency) | 2 ~ 25 | 6 ~ 13 (전형적) |
| **φ** | 위상 (Phase) | -π ~ π | - |

### 물리적 해석

1. **멱법칙 항** `B(tc - t)^m`:
   - 임계점으로 다가갈수록 가격이 급격히 상승
   - B < 0: 버블 (하락을 앞둔 상승)
   - m: 가속도의 정도

2. **로그-주기적 진동** `C(tc - t)^m * cos(...)`:
   - 투자자들의 집단 심리가 만드는 주기적 패턴
   - 로그 스케일에서 주기적으로 반복되는 진동
   - ω: 진동의 빈도 (높을수록 빠른 진동)

3. **임계점** `tc`:
   - 버블이 최고조에 달하는 시점
   - 이후 붕괴(crash) 또는 급격한 조정 가능성

---

## 구현 세부사항

### 최적화 알고리즘

본 구현은 `scipy.optimize.differential_evolution`을 사용하여 LPPL 파라미터를 최적화합니다:

**선택 이유**:
- 전역 최적화(Global Optimization): 여러 지역 최솟값을 피하고 전역 최솟값 탐색
- 파라미터 공간이 복잡하고 비선형적인 LPPL 모델에 적합
- 초기값에 덜 민감함

**최적화 프로세스**:
```python
목적 함수: minimize Σ(log(실제 가격) - log(LPPL 예측))²
제약 조건:
  - tc: 현재 + 5일 ~ 현재 + 2년
  - B: -2 ~ 0
  - m: 0.1 ~ 0.9
  - ω: 2 ~ 25
  - 기타 파라미터 범위
```

### 데이터 요구사항

**최소 요구사항**:
- 최소 30개 데이터 포인트 (약 1개월)
- 권장: 500개 이상 데이터 포인트 (약 2년)

**이유**:
- LPPL 모델은 7개의 파라미터를 가진 비선형 모델
- 과적합 방지를 위해 충분한 데이터 필요
- 로그-주기적 패턴을 포착하려면 여러 주기의 데이터 필요

---

## 버블 진단 지표

시스템은 다음 지표를 종합하여 버블을 진단합니다:

### 1. 임계 시간 (tc) 검증
```python
조건: 5일 ≤ (tc - 현재) ≤ 504일 (2년)
```
- **너무 가까움**: 신뢰도 낮음 (데이터 부족)
- **너무 멀음**: 버블 아님 (정상 성장)
- **적절한 범위**: 버블 가능성 있음

### 2. B 파라미터 (진폭)
```python
조건: B < 0
```
- **B < 0**: 버블 조건 (임계점 이후 하락 예상)
- **B > 0**: 버블 아님 (지속적 성장 패턴)

### 3. m 파라미터 (멱법칙 지수)
```python
조건: 0.1 ≤ m ≤ 0.9
```
- **m ≈ 0.3**: 전형적인 버블 패턴
- **범위 벗어남**: 모델 부적합

### 4. ω 파라미터 (각 주파수)
```python
조건: 2 ≤ ω ≤ 25
```
- **6 ~ 13**: 전형적인 금융 버블 주파수
- **범위 벗어남**: 로그-주기 패턴 미약

### 버블 상태 분류

| 상태 | 신뢰도 | 조건 | 의미 |
|------|--------|------|------|
| **CRITICAL** | ≥75% | tc가 60일 이내 | 매우 위험 - 임박한 조정 |
| **WARNING** | ≥75% | tc가 60일 이후 | 버블 경고 - 주의 필요 |
| **WATCH** | ≥50% | - | 버블 가능성 - 모니터링 |
| **NORMAL** | <50% | - | 정상 범위 |

---

## LPPLS Confidence Indicator

### 다중 윈도우 분석

단일 윈도우 대신 **126개 윈도우**(125일~750일, step=5)에서 LPPL을 피팅하여 신뢰도를 계산합니다.

```
LPPLS Confidence = (버블 조건 충족 윈도우 수 / 성공한 피팅 수) × 100
```

### 분석 결과 캐싱

분석 결과는 DB에 저장되어 재사용됩니다:

```
캐시 동작:
- analysis_date == 최신 가격일 → 캐시 반환 (빠름)
- analysis_date < 최신 가격일 → 재계산 + 저장
- force=true 파라미터 → 강제 재계산
```

**저장 데이터**:
- `LPPLAnalysisResult`: 분석 마스터 (신뢰도, 상태, 통계)
- `LPPLWindowResult`: 개별 윈도우 결과 (126개 윈도우의 파라미터)

---

## 사용 방법

### Python API

```python
from quant.models import LPPL
import pandas as pd

# 1. 가격 데이터 준비
prices = pd.Series([...], index=pd.DatetimeIndex([...]))

# 2. LPPL 모델 초기화 및 피팅
lppl = LPPL()
params = lppl.fit(prices)

# 3. 버블 진단
diagnosis = lppl.diagnose_bubble(prices)
print(f"상태: {diagnosis['state']}")
print(f"신뢰도: {diagnosis['confidence']}%")
print(f"예상 임계점: {diagnosis['critical_date']}")

# 4. 예측
fitted, forecast = lppl.forecast(prices, forecast_days=60)
```

### Web UI

1. 종목 상세 페이지 접속
2. 우측 "버블 진단 (LPPL)" 패널에서 "버블 분석 실행" 클릭
3. 약 10-30초 대기 (최적화 진행)
4. 결과 확인:
   - 버블 상태 및 신뢰도
   - 예상 임계 시점
   - LPPL 파라미터
   - 차트에 LPPL 피팅 라인 표시

---

## 해석 가이드

### 신뢰도 높은 버블 신호

**예시 1: CRITICAL 상태**
```
상태: CRITICAL
신뢰도: 87.5%
예상 임계 시점: 2026-03-15 (45일 후)

파라미터:
  tc: 45.2
  B: -0.23
  m: 0.31
  ω: 8.5

✓ tc가 합리적 범위
✓ B가 음수
✓ m이 유효 범위
✓ ω가 전형적 범위
```

**해석**:
- 모든 지표가 버블 조건 만족
- 45일 내 조정 또는 방향 전환 가능성 높음
- 포지션 축소 또는 헤지 전략 고려 필요

### 신뢰도 낮은 신호

**예시 2: WATCH 상태**
```
상태: WATCH
신뢰도: 62.5%

파라미터:
  tc: 523.1 (범위 초과)
  B: -0.15
  m: 0.29
  ω: 18.7

✗ tc가 너무 멀리 떨어짐
✓ B가 음수
✓ m이 유효 범위
✗ ω가 다소 높음
```

**해석**:
- 일부 지표만 버블 조건 만족
- tc가 너무 먼 미래 (1.5년 후) - 신뢰도 낮음
- 현재는 정상 성장 패턴일 가능성
- 주기적 모니터링만으로 충분

---

## 한계점 및 주의사항

### 1. 모델의 한계

❌ **LPPL이 예측하지 못하는 것**:
- 정확한 붕괴 시점 (tc는 확률적 추정)
- 하락 폭의 크기
- 외부 충격 (뉴스, 정책 변화)
- 갑작스러운 시장 구조 변화

✅ **LPPL이 탐지할 수 있는 것**:
- 버블 형성 패턴
- 임계점 접근 신호
- 로그-주기적 진동 존재
- 과매수 상태의 지속성

### 2. False Positives (거짓 양성)

다음 경우 실제 버블이 아닌데 신호가 발생할 수 있습니다:

- **강한 추세**: 지속 가능한 성장을 버블로 오인
- **데이터 부족**: 30~100일 데이터로는 신뢰도 낮음
- **노이즈**: 변동성이 극심한 소형주
- **모멘텀**: 단기 급등을 버블로 판단

**대응 방안**:
- 여러 지표와 함께 사용
- 펀더멘털 분석 병행
- 신뢰도 < 75%는 참고용으로만 활용

### 3. 계산 비용

- **피팅 시간**: 10~30초 (데이터양에 따라)
- **최적화 복잡도**: 7차원 비선형 최적화
- **실시간 부적합**: 실시간 모니터링보다는 주기적 분석에 적합

---

## 실전 활용 전략

### 1. 리스크 관리

LPPL 신호를 리스크 관리 지표로 활용:

```
CRITICAL (60일 이내):
  → 포지션 50% 축소
  → 풋옵션 헤지
  → 손절 라인 상향 조정

WARNING (60일 이후):
  → 신규 매수 중단
  → 분할 익절 시작
  → 변동성 모니터링 강화

WATCH:
  → 주간 재분석
  → 다른 지표 교차 검증
  → 시장 뉴스 주시

NORMAL:
  → 정상 트레이딩
```

### 2. 다른 지표와의 결합

**복합 전략 예시**:
```
LPPL CRITICAL + RSI > 70 + 거래량 급증
→ 강한 매도 신호

LPPL WARNING + Bollinger Bands 상단 돌파
→ 경계 강화, 익절 고려

LPPL NORMAL + 기술적 지표 정상
→ 계속 보유
```

### 3. 섹터/시장 차원 활용

- **개별 종목**: 비정상적 급등 판단
- **섹터 지수**: 섹터 버블 탐지
- **시장 지수**: 전체 시장 과열 여부

---

## 역사적 사례

### 성공 사례

**2000년 닷컴 버블**:
- LPPL 모델이 2000년 3~4월을 임계점으로 예측
- 실제 나스닥은 2000년 3월 10일 정점 기록
- 이후 2년간 78% 하락

**2008년 금융위기**:
- 2007년 말 부동산 및 금융주에서 LPPL 신호
- S&P 500은 2007년 10월 정점 후 하락
- 2009년 3월까지 57% 하락

**2015년 중국 주식시장**:
- 2015년 5~6월에 LPPL 경고 신호
- 상하이 종합지수 6월 12일 정점
- 3주만에 30% 급락

### 주의 사례 (False Alarms)

- **2013년 Bitcoin**: LPPL 신호 발생했으나 지속 상승
- **2017년 FAANG**: 버블 우려에도 장기 성장 지속
- **강한 추세 시장**: 정상 성장을 버블로 오인

→ **교훈**: LPPL은 보조 지표로 활용, 단독 판단 금물

---

## 참고 문헌

### 주요 논문

1. **Sornette, D., & Johansen, A. (2001)**
   "Significance of log-periodic precursors to financial crashes"
   *Quantitative Finance, 1(4), 452-471*

2. **Sornette, D., Woodard, R., & Zhou, W. (2009)**
   "The 2006-2008 oil bubble: Evidence of speculation, and prediction"
   *Physica A: Statistical Mechanics and its Applications, 388(8), 1571-1576*

3. **Filimonov, V., & Sornette, D. (2013)**
   "A stable and robust calibration scheme of the log-periodic power law model"
   *Physica A: Statistical Mechanics and its Applications, 392(17), 3698-3707*

### 책

- **Sornette, D. (2003)**
  *"Why Stock Markets Crash: Critical Events in Complex Financial Systems"*
  Princeton University Press

- **Sornette, D. (2017)**
  *"How We Can Predict the Next Financial Crisis"*
  TED Talk & Extended Research

### 온라인 자료

- [Financial Crisis Observatory (ETH Zurich)](https://www.er.ethz.ch/financial-crisis-observatory.html)
- [Sornette 교수 홈페이지](https://www.er.ethz.ch/people/sornette.html)
- [LPPL 모델 Python 구현 (lppls)](https://github.com/Boulder-Investment-Technologies/lppls)

---

## 코드 위치

- **모델 구현**: `src/quant/models/lppl.py`
- **캐시 서비스**: `web/apps/stocks/lppl_cache_service.py` - `LPPLCacheService`
- **DB 모델**: `web/apps/stocks/models.py` - `LPPLAnalysisResult`, `LPPLWindowResult`
- **서비스 레이어**: `web/apps/stocks/services.py` - `analyze_bubble()` 메서드
- **API 엔드포인트**: `web/apps/api/views.py` - `BubbleAnalysisView`
- **프론트엔드**: `web/static/js/chart.js` - `analyzeBubble()` 함수

---

## FAQ

**Q: LPPL 분석에 얼마나 시간이 걸리나요?**
A: 일반적으로 10~30초입니다. 비선형 최적화 과정이 포함되어 있어 실시간 분석은 어렵습니다.

**Q: 모든 종목에 적용 가능한가요?**
A: 아니요. 최소 30일 이상의 데이터가 필요하며, 급등 패턴이 뚜렷한 경우에만 의미있는 결과를 얻을 수 있습니다.

**Q: 신뢰도가 높으면 반드시 하락하나요?**
A: 아니요. LPPL은 확률적 모델이며, 높은 신뢰도는 '버블 패턴이 관찰됨'을 의미할 뿐 100% 하락을 보장하지 않습니다.

**Q: tc를 정확한 붕괴 시점으로 봐야 하나요?**
A: 아니요. tc는 '임계점 근처'의 추정치이며, 실제 조정은 tc 전후로 발생할 수 있습니다. 통계적으로 tc ± 20% 범위에서 발생합니다.

**Q: 왜 B는 항상 음수여야 하나요?**
A: B < 0은 버블의 수학적 특성입니다. 양수일 경우 정상적인 성장 패턴이며, 버블 진단에 적합하지 않습니다.

---

**마지막 업데이트**: 2026-01-31
**버전**: 1.1.0
**구현 기반**: Sornette et al. (2001, 2003, 2009, 2013)
