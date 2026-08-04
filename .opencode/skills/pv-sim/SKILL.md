---
name: pv-sim
description: Domain and architecture skill for the PV-Sim project — a solar PV economic simulation tool. Use when working on the simulation engine (weather, PV model, battery, economics), the FastAPI web app, the arq worker, the Docker deployment, or the load-profile archive. Covers the domain glossary, module layout, conventions, and how the plan→build workflow is run.
---

# PV-Sim

PV-Sim simulates grid-connected photovoltaic plants for economic investment
analysis. It models PV production (pvlib), battery storage, load curves, and
20/25/30-year cashflow projections.

## Plan → Build workflow

This project works in two opencode modes:

- **plan** (read-only, pro model): complex reasoning, architecture, decisions.
- **build** (read-write, light model): implementation.

Always end a plan session with a concrete plan and ask the user to switch to
build mode. In build mode, implement step by step, verify with `/test` and
`/lint`, and finish with a `/commit` and an optional `/handoff`.

## Domain glossary

Canonical terms live in `CONTEXT.md` at the repo root. Read it before touching
domain logic. Key terms: autoconsumo, autosufficienza, C-rate, clipping,
curva di carico, degradamento, RCPV.

## Architecture in one paragraph

`web` (FastAPI + HTMX + Alpine.js, SPA) receives simulation parameters and
enqueues jobs to Redis. A single `worker` (arq) consumes the queue and runs the
simulation engine (`src/engine/`). Results and metadata persist in PostgreSQL;
raw load curves are CSV files under `data/load_profiles/` referenced by the DB.
The engine is a sequence of pure-ish modules: weather → PV → load → battery →
economics, plus an optimizer that sweeps battery capacity.

## Module layout

```
src/
├── web/        FastAPI app: routes, templates (Jinja2 + HTMX), static, auth
├── worker/     arq entry point and job definitions (single worker process)
└── engine/     simulation core (shared, no web/worker imports)
    ├── weather.py          PVGIS-SARAH3 fetch + 15min interpolation
    ├── pv_model.py         ModelChain, inverter clipping, degradation, losses
    ├── load_model.py       CSV loader + synthetic generator from archive
    ├── battery_model.py    C-rate constrained, efficiency, degradation
    ├── economic_model.py   per-year cashflow, NPV, IRR, payback
    ├── optimizer.py        battery capacity sweep
    └── report.py           PDF report generation
```

## Conventions

- Python ≥3.12, typed with pyright. Keep `engine/` free of web/worker imports
  so it stays testable in isolation.
- No tests/lint are configured yet; before adding pytest, ruff, or pyright CI,
  confirm with the user first (see `docs/roadmap.md`).
- Package manager is `uv`. Never convert to pip/poetry.
- Config via environment variables, centralized in `src/web/config.py`.
- SQLAlchemy models live in `src/web/models.py`; schema managed by Alembic.
- Data files (CSV load curves) live under `data/`, gitignored except `.gitkeep`.

## Commands

- `/dev` start docker-compose, `/db` migrations/seed, `/test` pytest,
  `/sim` run engine from CLI, `/lint` ruff+pyright, `/build` docker build,
  `/handoff` write handoff doc, `/commit` conventional commit.

## Docs

Long-form documentation lives in `docs/`: architecture, roadmap, development,
api, database, simulation-engine, adr/, handoffs/. ADRs use the format from the
`domain-modeling` skill (`docs/adr/NNNN-slug.md`).
