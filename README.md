# Financial Simulation

A financial simulation web application that visualizes historical stock market performance, inflation data, and provides tools for retirement planning and medical expense tracking.

## Features

- **Global Market** — Historical stock market performance across 84+ countries using S&P Global Equity Indices
- **Contributions** — Retirement contribution simulator with projected growth charts
- **Withdrawals** — Retirement withdrawal planner with asset allocation across stocks, bonds, and bills
- **Medical Receipts** — HSA receipt tracking tool

## Quick Start

### Local (requires Python + uv)

```bash
# Install dependencies
uv sync

# Run development server (hot-reload, http://localhost:8000)
uv run pywire dev
```

### Docker

```bash
# Build
docker build -t financial-simulation .

# Run (http://localhost:3000)
docker run -p 3000:3000 financial-simulation
```

## Tech Stack

- **[PyWire](https://nightly.pywire.dev/docs)** — Python web framework with `.wire` files (Python + HTML in one file), path-based routing, and PJAX navigation
- **[yfinance](https://github.com/ranaroussi/yfinance)** — Stock market data (S&P 500, US total market)
- **[Chart.js](https://www.chartjs.org/)** — Interactive charts
- **[Pico CSS](https://picocss.com/)** — Minimal classless CSS framework
- **SQLAlchemy** — ORM for database models ([src/models.py](src/models.py))
- **Alembic** — Database schema migration tool ([alembic/](alembic/))
- **PostgreSQL** — Production database (runs as a Docker service)
- **Stripe** — Subscription billing integration

## Database

### How it fits together

- **SQLAlchemy** defines the schema as Python classes in [src/models.py](src/models.py). Each class maps to a table and each field maps to a column.
- **Alembic** compares those model definitions against the live database and generates versioned SQL migration scripts in [alembic/versions/](alembic/versions/). This means schema changes are tracked in git and can be applied or rolled back reliably.
- **PostgreSQL** runs as a separate Docker service (`db`) defined in [docker-compose.yml](docker-compose.yml). The app and database communicate over Docker's internal network using the hostname `db`. Port 5432 is also exposed to `localhost` so you can run migrations and inspect the database from your host machine.

### Setup

Source your local `.env` and fill in your credentials:

```bash
cp .env.example .env
# Edit .env with your credentials
source .env
```

Start the database:

```bash
docker compose up -d db
```

### Applying migrations

Run these from your host machine against the exposed port:

```bash
DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/financial_simulation uv run alembic upgrade head
```

### Updating the schema

1. Edit the models in [src/models.py](src/models.py)

2. Generate a migration:

   ```bash
   DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/financial_simulation uv run alembic revision --autogenerate -m "describe your change"
   ```

3. Review the generated file in `alembic/versions/` to confirm it looks correct

4. Apply it:

   ```bash
   DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/financial_simulation uv run alembic upgrade head
   ```

5. Commit both the updated `models.py` and the new migration file

### Inspecting the database

```bash
docker compose exec db psql -U $POSTGRES_USER -d financial_simulation
```

Useful psql commands: `\dt` (list tables), `\d <table>` (describe table), `\q` (quit).

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
├── models.py           # SQLAlchemy ORM models
└── main.py             # Application entry point
data/
└── API_CM.MKT.INDX.ZG_DS2_en_csv_v2_10345.csv  # S&P Global Equity Indices (1960–2024)
```
