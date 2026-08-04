# Handoff — Fase 1: Infrastruttura & skeleton — 2026-08-04

## Stato

Fase 1 completata. Stack Dockerizzato funzionante: `docker compose up` avvia
web, worker, postgres, redis e la migrazione iniziale; web risponde su `:8000`
(`/health` → 200). Pronto per la Fase 2 (modelli meteo e PV).

## Completato

- [x] `pyproject.toml` con dipendenze (fastapi, uvicorn, sqlalchemy[asyncio],
      asyncpg, alembic, redis, arq, jinja2, httpx, pydantic-settings, plotly,
      weasyprint) + `build-system` hatchling (`packages = ["src"]`)
- [x] Scheletro `src/`: `engine/` (7 stub), `web/` (config, database, models,
      main, templates/, static/), `worker/` (main + jobs)
- [x] `docker-compose.yml` (postgres, redis, migrate, web, worker) +
      `Dockerfile` (uv, multi-stage sync), `.dockerignore`, `.env.example`
- [x] Config centralizzata in `src/web/config.py` (Pydantic Settings, env vars)
- [x] Modelli SQLAlchemy in `src/web/models.py` (Simulation, LoadProfile,
      SimulationResult, SimulationMetrics)
- [x] Alembic async (`alembic.ini`, `env.py`, `script.py.mako`) + migrazione
      iniziale `0ed5fd4585f0` applicata
- [x] Rimosso `main.py` placeholder
- [x] Roadmap aggiornata (Fase 1 done)

## In corso / da completare

- [ ] Nessun codice di simulazione ancora scritto: `src/engine/*` sono solo
      stub con docstring; il job `run_simulation` solleva `NotImplementedError`
- [ ] `/sim` CLI non esiste ancora (previsto in Fase 2)
- [ ] Test/lint non configurati (Fase 10, da confermare con l'utente)

## Decisioni prese in questa sessione

- Migrazioni Alembic eseguite in un servizio one-shot `migrate`
  (`service_completed_successfully`) prima di web/worker
- Alembic usa il driver async (`async_engine_from_config`) sulla stessa
  `DATABASE_URL` asyncpg del web
- `src/worker/` importa da `src.web.config` e `src.web.models` (il vincolo di
  isolamento vale solo per `src/engine/`)
- `main.py` rimosso; il punto di ingresso web è `src.web.main:app`

## Domande aperte / blocchi

- Nessuno. Nota: pyright/ruff non installati globalmente — gli errori LSP
  "import not resolved" sono artefatti del server LSP non riavviato; gli
  import funzionano via `uv run`. Lint/typecheck restano in Fase 10.

## Comandi di verifica

```bash
docker compose up -d --build
curl -s http://localhost:8000/health        # {"status":"ok"}
docker compose ps                            # postgres/redis healthy, web/worker up
docker compose exec web python -c "import asyncio; from src.web.database import engine; from sqlalchemy import text; \
  async def m():\n    async with engine.connect() as c:\n        print((await c.execute(text('select count(*) from simulations'))).scalar())\n    await engine.dispose()\n\
  asyncio.run(m())"
uv run python -c "from src.web.main import app; from src.web.models import Base"
git log --oneline -1   # commit Fase 1
```

## Prossimi passi

1. **Fase 2 — Weather & PV model**:
   - `src/engine/weather.py`: `get_pvgis_tmy` (SARAH3) + interpolazione 15 min
   - `src/engine/pv_model.py`: `ModelChain` con tilt/azimuth, clipping inverter
     (`min(ac, inverter_kw)`), degrado, perdite di sistema
   - CLI smoke test (`/sim`) per produzione annua; confrontare l'anno 1 con
     `pvlib_autoconsumo_simulazione.py`
2. Vedere `docs/roadmap.md` per la sequenza completa (Fasi 2-10).
