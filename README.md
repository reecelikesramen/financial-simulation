# Financial Simulation

A financial simulation web application that visualizes historical stock market performance, inflation data, and provides tools for retirement planning and medical expense tracking.

## Features

- **Global Market** — Historical stock market performance across 84+ countries using S&P Global Equity Indices
- **Contributions** — Retirement contribution simulator with projected growth charts
- **Withdrawals** — Retirement withdrawal planner with asset allocation across stocks, bonds, and bills
- **Medical Receipts** — HSA receipt tracking tool

## Quick Start

```bash
# Install dependencies
uv sync

# Run development server (hot-reload, http://localhost:8000)
uv run pywire dev
```

## Tech Stack

- **[PyWire](https://nightly.pywire.dev/docs)** — Python web framework with `.wire` files (Python + HTML in one file), path-based routing, and PJAX navigation
- **[yfinance](https://github.com/ranaroussi/yfinance)** — Stock market data (S&P 500, US total market)
- **[Chart.js](https://www.chartjs.org/)** — Interactive charts
- **[Pico CSS](https://picocss.com/)** — Minimal classless CSS framework
- **SQLAlchemy** — ORM for user and subscription models
- **Stripe** — Subscription billing integration

## Routes

| Path | Description |
| ---- | ----------- |
| `/` | Landing page with feature cards |
| `/globalmarket` | Country stock market data and comparisons |
| `/contributions` | Retirement contributions simulator |
| `/withdrawals` | Retirement withdrawals planner |
| `/medicalreceipts` | HSA medical receipt tracker |
| `/pricing` | Pricing page |
| `/login` | Authentication |
| `/dashboard/*` | Protected dashboard area |

## Project Structure

```text
src/
├── pages/              # Route pages (.wire files)
│   ├── __layout__.wire # Root layout with navigation
│   ├── index.wire
│   ├── globalmarket.wire
│   ├── contributions.wire
│   ├── withdrawals.wire
│   └── medicalreceipts.wire
├── financial_data.py   # yfinance data fetching utilities
├── worldbank_data.py   # World Bank CSV data loader
├── models.py           # SQLAlchemy User and Subscription models
└── main.py             # Application entry point
data/
└── API_CM.MKT.INDX.ZG_DS2_en_csv_v2_10345.csv  # S&P Global Equity Indices (1960–2024)
```
