# Architecture

This document describes the PV-Sim system architecture: services, data flow,
job lifecycle, and module responsibilities.

## Services

PV-Sim runs as a `docker-compose` stack with four services:

| Service | Technology | Role |
|---|---|---|
| `web` | FastAPI (uvicorn), Jinja2 + HTMX + Alpine.js, Plotly.js | SPA shell, parameter forms, result dashboard, PDF download |
| `worker` | arq (async job queue) | Executes simulation jobs sequentially. Exactly **one** worker process. |
| `redis` | Redis | Job queue transport between `web` and `worker` |
| `postgres` | PostgreSQL | Persistent storage: simulations, results, load-profile metadata |

Load curves (real CSV archives) live on the filesystem under
`data/load_profiles/`; the database stores only metadata pointing at them.

## Container topology

```
                        ┌────────────────────────────┐
                        │         docker-compose      │
                        │                            │
  browser ──── HTTP ───▶│  web ──enqueue──▶ redis ──▶│──── worker
   (HTMX SPA)           │  FastAPI        (queue)    │   (arq, x1)
                        │     │                      │
                        │     ▼                      │
                        │  postgres ◀───persist──────│
                        │                            │
                        │  data/load_profiles/       │
                        └────────────────────────────┘
```

## Data flow

1. The user fills a parameter form in the web SPA (location, PV field,
   battery, tariffs, costs, horizon).
2. The web layer persists the simulation row and enqueues a job id to Redis
   via arq.
3. The single worker picks up the job, runs the simulation engine, and writes
   results to PostgreSQL.
4. The web layer polls the job status (HTMX poll interval) and renders the
   dashboard when complete.

## Simulation engine pipeline

The engine is a sequence of modules, each transforming data for the next:

```
weather ──▶ pv_model ──▶ load_model ──▶ battery_model ──▶ economic_model
```

- `weather`: fetch PVGIS-SARAH3 TMY via pvlib, resample to 15 minutes.
- `pv_model`: `pvlib.ModelChain`, tilt/azimuth, inverter clipping, per-year
  panel degradation, configurable system losses.
- `load_model`: real CSV curve or synthetic curve derived from an archived
  similar profile, scaled to annual consumption.
- `battery_model`: C-rate-constrained charge/discharge, round-trip efficiency,
  per-year capacity degradation.
- `economic_model`: per-year cashflow (savings, grid sales, costs, loan
  installments, replacements), then NPV, IRR, payback.

The `optimizer` module wraps the engine to sweep battery capacity scenarios and
return the optimum. A battery capacity can also be selected manually.

## Job lifecycle

A simulation job moves through states: `queued` → `running` → `completed` |
`failed`. States are stored in the `simulations` table; the web layer exposes
them via a polling endpoint (HTMX `hx-trigger="every 2s"`).

## Module dependencies

- `src/engine/` is importable in isolation — it must never import from
  `src/web/` or `src/worker/`. This keeps it testable without the stack.
- `src/web/` talks to the engine **only** through the job queue (arq) — never
  by direct import.
- `src/worker/` is the thin glue: it deserializes job args, invokes the engine,
  and persists results.

## Configuration

All configuration is injected via environment variables and centralized in
`src/web/config.py` (Pydantic Settings). See `docs/development.md` for the
variable list and the `.env` template.
