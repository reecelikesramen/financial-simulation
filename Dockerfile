FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies first (cached layer - only re-runs when lockfile changes)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy application code and data
COPY src/ ./src/
COPY data/ ./data/
COPY alembic/ ./alembic/
COPY alembic.ini ./

EXPOSE 3000

CMD ["uv", "run", "pywire", "dev", "--no-tui", "--host", "0.0.0.0"]
