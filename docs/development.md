# Development Guide

Setup, build and run instructions for PV-Sim.

## Prerequisites

- Docker + Docker Compose v2
- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/) package manager
- Git

## Host environment (engine-only work)

```bash
# Create venv and install dependencies
uv sync

# Run the engine from CLI (once `src/engine/cli.py` exists, Phase 2+)
uv run python -m src.engine.cli
```

## Full stack in Docker

```bash
# Start services (build images on first run)
docker compose up --build

# Background
docker compose up --build -d

# Service URLs (defaults)
#   web:      http://localhost:8000
#   redis:    localhost:6379
#   postgres: localhost:5432 (user/pass from .env)

# Tear down
docker compose down
```

The web UI is a single-password SPA: set `APP_PASSWORD` in the environment.

## Environment variables

Create a `.env` file at the repo root. Reference values:

```env
# Web
APP_HOST=0.0.0.0
APP_PORT=8000
APP_PASSWORD=change-me
APP_SECRET_KEY=change-me

# Database (must match docker-compose service `postgres`)
POSTGRES_USER=pvsim
POSTGRES_PASSWORD=pvsim
POSTGRES_DB=pvsim
DATABASE_URL=postgresql+asyncpg://pvsim:pvsim@postgres:5432/pvsim

# Redis (must match docker-compose service `redis`)
REDIS_URL=redis://redis:6379/0

# Paths
LOAD_PROFILES_DIR=/data/load_profiles
```

All settings are centralized and validated in `src/web/config.py`
(Pydantic Settings).

## Database migrations

```bash
# Generate a new migration after model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Reset (drop + recreate + migrate + seed)
alembic downgrade base && alembic upgrade head
```

## Load profile archive

Real load curves are CSV files under `data/load_profiles/` (gitignored except
`.gitkeep`). Uploads from the web layer write new files here and insert a
metadata row into `load_profiles`. When a simulation has no real curve, the
engine picks a similar archived profile and scales it to the annual
consumption.

CSV format expected by the loader:

```
timestamp,power_kw
2024-01-01 00:00:00,1.25
...
```

- `timestamp`: ISO `YYYY-MM-DD HH:MM:SS`, local time (Europe/Rome preferred)
- `power_kw`: instantaneous power in kW at 15-minute resolution (1 year of data)

## Testing and linting

No test/lint infrastructure is configured yet. Before introducing pytest,
ruff, or pyright CI, **confirm with the user first** — see `docs/roadmap.md`.
Planned commands once enabled: `/test` (pytest), `/lint` (ruff + pyright).

## Gotchas

- `main.py` is a placeholder and will be removed during Phase 1.
- The old prototype `pvlib_autoconsumo_simulazione.py` is superseded in
  Phase 2; keep it until the engine reproduces its output.
- `engine/` must stay free of web/worker imports.
