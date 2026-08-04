# PV-Sim Agent Instructions

## Project Overview

PV-Sim is a solar PV self-consumption simulation and economic-investment
analysis tool. It models PV production (pvlib), battery storage, and load
curves to compute autoconsumo, autosufficienza, and return on investment over
configurable horizons (20/25/30 years), including degradation, financing,
maintenance, and grid-management costs.

## Workflow: plan → build

- **plan** mode: read-only, pro model. Use for complex reasoning, architecture,
  and design decisions. Always end by proposing a concrete plan.
- **build** mode: read-write, light model. Implement step by step, verify with
  `/test` and `/lint`, then `/commit`. Write a `/handoff` at phase boundaries.

The user will explicitly switch modes. In build mode, do not make sweeping
changes without a prior plan or explicit request.

## Session start (riprendere una sessione)

Quando l'utente dice "ripartiamo", "riprendiamo", "riapriamo" o avvia una
nuova sessione sul progetto, esegui questo rituale PRIMA di qualsiasi lavoro:

1. **Contesto** (già caricato via `instructions`): `AGENTS.md` + `CONTEXT.md`.
2. **Stato progressivo**:
   - Leggi l'handoff più recente in `docs/handoffs/`
     (`YYYY-MM-DD-<slug>.md`, ordinati per data desc).
   - Leggi `docs/roadmap.md` e verifica quali fasi sono marcate done.
   - `git log --oneline -5` e `git status --short` per lo stato del repo.
3. **Riepiloga** all'utente: fase corrente, cosa è stato completato, cosa è
   in corso, prossimi passi, eventuali blocchi/domande aperte dall'handoff.
4. **Chiedi conferma** prima di iniziare qualsiasi lavoro: proponi il prossimo
   passo (dalla roadmap) e aspetta l'ok dell'utente.

Non riassumere la documentazione: usa gli handoff e la roadmap come fonte di
verità dello stato. Se non trovi handoff, usa la roadmap e lo stato di git.

## Stack

| Layer | Choice |
|---|---|
| Language | Python ≥ 3.12 (uv) |
| Web UI | FastAPI + Jinja2 + HTMX + Alpine.js (SPA, no heavy JS framework) |
| Charts | Plotly (server-rendered JSON → plotly.js) |
| Worker | arq (async job queue, Redis), single worker process |
| DB | PostgreSQL (SQLAlchemy + Alembic) |
| Weather | PVGIS-SARAH3 via `pvlib.iotools.get_pvgis_tmy` |
| Deploy | docker-compose (web, worker, redis, postgres) |
| PDF report | WeasyPrint or ReportLab |

## Running the Project

```bash
# Install dependencies (host, for engine-only work)
uv sync

# Full stack in Docker
docker compose up --build

# Run the current standalone prototype
python pvlib_autoconsumo_simulazione.py

# Run the engine from CLI (fast debug, no web)
uv run python -m src.engine.cli  # once implemented (see docs/roadmap.md)
```

Note: `main.py` is a placeholder. The real logic lives under `src/engine/`.
The old prototype script `pvlib_autoconsumo_simulazione.py` will be superseded
during Phase 1 (see `docs/roadmap.md`).

## Commands

- `/dev` — start `docker compose up`
- `/db` — Alembic migrations, reset, seed
- `/test` — run pytest (introduced in roadmap; confirm before enabling)
- `/sim` — run a simulation from CLI for fast debugging
- `/lint` — ruff check + pyright (introduced in roadmap; confirm before enabling)
- `/build` — docker build images
- `/handoff` — write a handoff document under `docs/handoffs/`
- `/commit` — conventional git commit

## Directory Layout

```
src/
├── web/        FastAPI app (routes, templates, static, auth)
├── worker/     arq entry point + jobs (exactly one worker process)
└── engine/     simulation core: weather, pv_model, load_model,
                battery_model, economic_model, optimizer, report
docs/           architecture, roadmap, development, api, database,
                simulation-engine, adr/, handoffs/
data/load_profiles/   archived load curves (CSV), gitignored
.opencode/      commands/, skills/, agent/
CONTEXT.md      domain glossary (read before domain work)
```

## Key Conventions

- `engine/` must not import from `web/` or `worker/` — keep it testable.
- Package manager is `uv`. Never convert to pip/poetry.
- Python ≥3.12, fully typed (pyright). No untyped public functions.
- Config via environment variables, centralized in `src/web/config.py`.
- No test/lint infrastructure exists yet. **Before adding pytest, ruff, or
  pyright CI, confirm with the user first** (see `docs/roadmap.md`).
- Load curves live as CSV on disk; the DB stores metadata only.
- Simulation jobs run in the worker; the web layer only enqueues and polls.

## Documentation

Long-form docs live in `docs/`. ADRs in `docs/adr/NNNN-slug.md` following the
`domain-modeling` skill format. Read `CONTEXT.md` for the domain language and
`docs/` before making architectural decisions.

## References

- `docs/architecture.md` — services, data flow, job lifecycle
- `docs/roadmap.md` — phases 1-10 with milestones
- `docs/simulation-engine.md` — module specs, formulas, degradation, economics
- `docs/database.md` — schema
- `docs/development.md` — full setup guide
