# Korean Stock Quant - Web Application

Django-based web GUI for the Korean Stock Quant library.

## Features

- **Stock Analysis**: View candlestick charts with technical indicators (RSI, Bollinger Bands, Stochastic)
- **Trading Signals**: Automatic buy/sell signal generation based on technical indicators
- **KOSPI 200 Screener**: Screen stocks based on indicator conditions
- **User Accounts**: Login, registration, watchlist management, analysis history

## Requirements

- Python 3.12+
- Dependencies in `pyproject.toml` (web extras)

## Installation

```bash
# Install dependencies with uv
uv sync --all-extras

# Or with pip
pip install -e ".[web]"
```

## Running the Development Server

```bash
cd web

# Run migrations (first time only)
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

## Project Structure

```
web/
├── manage.py              # Django management script
├── config/                # Project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/          # User authentication
│   │   ├── models.py      # User, Watchlist, AnalysisHistory
│   │   ├── views.py       # Login, Register, Watchlist views
│   │   └── urls.py
│   ├── stocks/            # Stock analysis
│   │   ├── services.py    # Quant library wrapper
│   │   ├── views.py       # Dashboard, StockDetail, Screener
│   │   └── urls.py
│   └── api/               # REST API
│       ├── views.py       # OHLCV, Indicator, Signal endpoints
│       └── urls.py
├── templates/             # HTML templates
│   ├── base.html
│   ├── accounts/
│   └── stocks/
└── static/
    ├── css/style.css
    └── js/chart.js        # Lightweight Charts integration
```

## URLs

| URL | Description |
|-----|-------------|
| `/` | Dashboard |
| `/stock/<symbol>/` | Stock detail with chart |
| `/screener/` | KOSPI 200 screener |
| `/accounts/login/` | Login |
| `/accounts/register/` | Register |
| `/accounts/watchlist/` | Watchlist |
| `/accounts/history/` | Analysis history |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stock/<symbol>/ohlcv/` | GET | OHLCV candlestick data |
| `/api/stock/<symbol>/indicator/<indicator>/` | GET | Indicator data (RSI, BB, STOCH) |
| `/api/stock/<symbol>/signals/<indicator>/` | GET | Trading signals |
| `/api/kospi200/` | GET | KOSPI 200 stock list |
| `/api/screener/run/` | GET | Run screener |
| `/api/search/` | GET | Search stocks |

## Technologies

- **Backend**: Django 5.0+
- **Frontend**: Bootstrap 5, Lightweight Charts (TradingView)
- **Database**: SQLite (development)
- **Styling**: django-crispy-forms with Bootstrap 5
