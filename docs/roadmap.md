# Roadmap

Phased plan from the standalone prototype to the full Dockerized PV-Sim.
Phase 0 is complete; Phases 1-10 build toward the MVP described in the plan
discussed with the user. Phases 1-8 are the "MVP completo ma shallow".

## Phase 0 — Setup & documentation (done)

- [x] Skills remote installate e spostate nel progetto sotto
      `.opencode/skills/` (`domain-modeling`, `tdd`,
      `supabase-postgres-best-practices`)
- [x] Skill custom `.opencode/skills/pv-sim/SKILL.md`
- [x] `CONTEXT.md` glossario, `AGENTS.md`, `README.md`
- [x] Documentazione in `docs/` (architecture, roadmap, development, api,
      database, simulation-engine, adr, handoffs)
- [x] Comandi `.opencode/commands/` (8) + aggiornamento `opencode.json`
      (LSP ruff, skills paths, instructions AGENTS.md)

## Phase 1 — Infrastructure & skeleton

- Define `docker-compose.yml` (web, worker, redis, postgres) + Dockerfiles.
- `pyproject.toml`: add fastapi, uvicorn, sqlalchemy, alembic, redis, arq,
  jinja2, httpx, pydantic-settings, plotly, weasyprint.
- Project skeleton: `src/web/`, `src/worker/`, `src/engine/` packages with
  `__init__.py` and module stubs.
- DB connection + first Alembic migration with core tables
  (`simulations`, `load_profiles`, `simulation_results`).
- **Milestone:** `docker compose up` starts all services and web responds on
  port 8000.

## Phase 2 — Weather & PV model

- `src/engine/weather.py`: `get_pvgis_tmy` (SARAH3) + 15min interpolation.
- `src/engine/pv_model.py`: `ModelChain` with tilt/azimuth, inverter clipping
  (`min(ac, inverter_kw)`), degradation parameter, system losses.
- CLI smoke test script (`/sim`) computing one-year production.
- **Milestone:** PV production profile matches prototype output for same params.

## Phase 3 — Load model

- `src/engine/load_model.py`: load a real CSV curve; metadata model for the
  archive (`load_profiles`).
- Synthetic generator: pick an archived "similar" profile, scale to annual
  consumption.
- Upload flow in web: save CSV to `data/load_profiles/`, insert metadata row.
- **Milestone:** a simulation can run with a real or synthetic curve.

## Phase 4 — Battery model

- `src/engine/battery_model.py`: C-rate-limited charge/discharge, round-trip
  efficiency, per-year capacity degradation.
- Wire battery into the engine pipeline (PV surplus → battery → load).
- **Milestone:** autoconsumo/autosufficienza computed with battery for one year.

## Phase 5 — Economic model

- `src/engine/economic_model.py`: per-year cashflow for 20/25/30 years.
- Loan (annuity) model, ordinary maintenance, extraordinary replacement
  (inverter at year 10, battery at year 12), RCPV costs
  (one-time activation + annual fee), monoraria purchase/sell tariffs.
- Final metrics: NPV, IRR, payback.
- **Milestone:** CLI simulation returns full economic summary for one scenario.

## Phase 6 — Worker & job flow

- `src/worker/main.py` + `src/worker/jobs.py`: arq entry point, job functions,
  status transitions in DB.
- Web enqueues jobs; HTMX polling endpoint for status.
- **Milestone:** full job round-trip web → redis → worker → postgres → web.

## Phase 7 — Web UI: forms & dashboard

- SPA shell (`base.html`, Alpine.js), navigation, single-password auth.
- Parameter form → creates simulation, enqueues job.
- Result dashboard: KPI cards, Plotly charts (production/load day-type,
  cashflow), annual table.
- **Milestone:** end-to-end run from browser.

## Phase 8 — Optimizer & battery scenarios

- `src/engine/optimizer.py`: sweep battery capacity, pick max IRR/NPV.
- Manual scenario comparison in UI (multiple capacities).
- **Milestone:** "ottimizza" button returns optimal capacity + metrics.

## Phase 9 — PDF report

- `src/engine/report.py`: generate PDF report (WeasyPrint) from results.
- Download link in dashboard.
- **Milestone:** report PDF downloadable.

## Phase 10 — Polish & hardening

- Tests (pytest) — **confirm with user before adding.**
- Lint/typecheck (ruff + pyright) — **confirm with user before adding.**
- Error handling, logging, edge cases (bad CSV, PVGIS outage).
- Deployment docs and `.env.example` finalization.

## Notes on scope

- Tariffs: monoraria only for the MVP (single purchase price, single sell
  price). Bioraria/trioraria deferred.
- Battery sizing: both automatic (optimizer) and manual scenario comparison.
- Reports: PDF only (Excel deferred).

## Future / deferred ideas

- Bioraria/trioraria tariffs (F1/F2/F3).
- Alternative weather sources (ERA5, NSRDB).
- Excel export of raw results.
- Multi-user support and per-user authentication.
