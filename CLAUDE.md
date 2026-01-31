# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
# Install dependencies (requires uv package manager)
uv sync --all-extras          # All dependencies including dev
uv sync                       # Production only

# Code quality (or use: make format, make lint, make check)
uv run ruff format src tests  # Format code
uv run ruff check --fix src tests  # Lint and auto-fix
uv run ruff check src tests   # Lint only (no fix)

# Testing (or use: make test)
uv run pytest                 # Run all tests with coverage
uv run pytest tests/test_factors.py::TestRSI  # Run specific test class
uv run pytest -k "test_calculate"  # Run tests matching pattern
```

## Code Style

- Line length: 100 characters
- Python 3.12+ required

## Architecture

This is a quantitative investment analysis library for Korean stock markets (KOSPI, KOSDAQ).

### Data Layer (`src/quant/data/`)
- `DataFetcher`: Unified interface for stock data from FinanceDataReader (Korean markets) and yfinance (global markets)
- `Kospi200`: KOSPI 200 index constituent management

### Factor Layer (`src/quant/factors/`)
All factors inherit from `BaseFactor` which enforces two abstract methods:
- `calculate(df: DataFrame) -> DataFrame`: Compute indicator values, returns original data plus new columns
- `get_signal(df: DataFrame) -> Series`: Generate trading signals (1=buy, -1=sell, 0=hold)

Input DataFrames must have lowercase OHLCV columns: `open`, `high`, `low`, `close`, `volume`

**Momentum Factors** (`factors/momentum/`):
- `RSI`: Relative Strength Index with overbought/oversold thresholds
- `BollingerBands`: Volatility bands with configurable standard deviation
- `Stochastic`: %K/%D crossover signals
- `MACD`: Moving Average Convergence Divergence
- `ADX`: Average Directional Index for trend strength
- `CCI`: Commodity Channel Index
- `WilliamsR`: Williams %R oscillator
- `ROC`: Rate of Change momentum
- `MFI`: Money Flow Index (volume-weighted RSI)
- `VolumeMA`: Volume Moving Average analysis
- `OBV`: On-Balance Volume

**Composite Factor** (`factors/momentum_factor.py`):
- `MomentumFactor`: Weighted composite score (0-100) combining all 11 indicators

### Adding New Factors

1. Create new file in appropriate category folder (e.g., `factors/momentum/macd.py`)
2. Inherit from `BaseFactor`, implement `calculate()` and `get_signal()`
3. Use `pandas-ta` library for indicator calculations
4. Export in `factors/momentum/__init__.py` and `factors/__init__.py`

## Key Libraries

- **pandas-ta**: Primary library for technical indicator calculations
- **FinanceDataReader**: Korean market data (use stock codes like "005930" for Samsung)
- **yfinance**: Global market data (Korean stocks need ".KS" suffix)
