# Roadmap

Phased plan from the standalone prototype to the full Dockerized PV-Sim.
Phase 0 is complete; Phases 1-10 build toward the MVP described in the plan
discussed with the user. Phases 1-8 are the "MVP completo ma shallow".
Phases 11-13 (branch `desktop`) add a standalone desktop variant via
pywebview (see `docs/adr/0004-desktop-pywebview.md`).

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

## Phase 1 — Infrastructure & skeleton (done)

- [x] Define `docker-compose.yml` (web, worker, redis, postgres) + Dockerfiles.
- [x] `pyproject.toml`: add fastapi, uvicorn, sqlalchemy, alembic, redis, arq,
      jinja2, httpx, pydantic-settings, plotly, weasyprint.
- [x] Project skeleton: `src/web/`, `src/worker/`, `src/engine/` packages with
      `__init__.py` and module stubs.
- [x] DB connection + first Alembic migration with core tables
      (`simulations`, `load_profiles`, `simulation_results`).
- [x] **Milestone:** `docker compose up` starts all services and web responds on
      port 8000.

## Phase 2 — Weather & PV model (done)

- [x] `src/engine/weather.py`: `get_pvgis_tmy` (SARAH3) + 15min interpolation.
- [x] `src/engine/pv_model.py`: `ModelChain` with tilt/azimuth, inverter clipping
      (`min(ac, inverter_kw)`), degradation parameter, system losses.
- [x] CLI smoke test script (`/sim`) computing one-year production.
- [x] **Milestone:** PV production profile matches prototype output for same
      params.

## Phase 3 — Load model (done)

- [x] `src/engine/load_model.py`: load a real CSV curve; metadata model for the
      archive (`load_profiles`).
- [x] Synthetic generator: pick an archived "similar" profile, scale to annual
      consumption.
- [x] Upload flow in web: save CSV to `data/load_profiles/`, insert metadata
      row.
- [x] **Milestone:** a simulation can run with a real or synthetic curve.

## Phase 4 — Battery model (done)

- [x] `src/engine/battery_model.py`: C-rate-limited charge/discharge, round-trip
      efficiency, per-year capacity degradation.
- [x] Wire battery into the engine pipeline (PV surplus → battery → load).
- [x] **Milestone:** autoconsumo/autosufficienza computed with battery for one
      year.

## Phase 5 — Economic model (done)

- [x] `src/engine/economic_model.py`: per-year cashflow for 20/25/30 years.
- [x] Loan (annuity) model, ordinary maintenance, extraordinary replacement
      (inverter at year 10, battery at year 12), RCPV costs
      (one-time activation + annual fee), monoraria purchase/sell tariffs.
- [x] Final metrics: NPV, IRR, payback.
- [x] **Milestone:** CLI simulation returns full economic summary for one
      scenario.

## Phase 6 — Worker & job flow (done)

- [x] `src/worker/jobs.py`: `run_simulation` job — status transitions in DB
      (`queued` → `running` → `completed` | `failed`), engine pipeline
      (weather → pv → load → battery → economics) offloaded to a thread,
      persistence in `simulation_results` + `simulation_metrics`.
- [x] `src/worker/main.py`: arq `WorkerSettings` with `on_startup`/`on_shutdown`
      wiring the async DB session into the job context.
- [x] Web enqueues jobs (`POST /api/simulations` via `create_pool`), JSON
      status endpoint (`GET /api/simulations/{id}`), HTMX polling fragment
      (`GET /simulations/{id}/status`).
- [x] **Milestone:** full job round-trip web → redis → worker → postgres → web.

## Phase 7 — Web UI: forms & dashboard (done)

- [x] SPA shell (`base.html`, Alpine.js, HTMX), navigazione, auth a password
      singola (cookie HMAC firmato, middleware).
- [x] Form parametri (`/new`) → crea simulazione + enqueue via
      `POST /api/simulations`.
- [x] Dashboard risultati: KPI card, grafici Plotly (produzione/carico su
      giorni tipo inverno/estate, cashflow netto+cumulativo), tabella annuale.
      Il worker persiste le curve year-1 su disco
      (`data/simulation_data/{id}/`) per i grafici.
- [x] **Milestone:** run end-to-end dal browser (login → form → job →
      polling HTMX → dashboard con grafici).

## Phase 8 — Optimizer & battery scenarios (done)

- [x] `src/engine/optimizer.py`: `sweep_capacities()` — per ogni capacità
      aggiusta investimento/sostituzione batteria (costo €/kWh) e ritorna gli
      scenari ordinati per NPV discendente.
- [x] `run_optimization` job: sweep in worker, una Simulation + full results
      per ogni capacità, righe `optimization_scenarios` per il confronto;
      curve scritte solo per lo scenario migliore.
- [x] Tabella `optimization_scenarios` (migrazione Alembic).
- [x] Confronto manuale in UI: form con toggle "Ottimizza" (sweep automatico
      o elenco manuale di capacità, costi €/kWh), pagina
      `/optimizations/{group}` con tabella comparativa e badge "migliore".
- [x] **Milestone:** "ottimizza" restituisce capacità ottimale + metriche.

## Phase 9 — PDF report (done)

- [x] `src/web/report.py`: `build_report_pdf()` — HTML standalone renderizzato
      con Jinja2 → WeasyPrint; grafici giorni-tipo e cashflow come PNG via
      matplotlib (niente kaleido/Chrome). `src/engine/report.py` resta uno
      stub con rimando (il report è una web concern).
- [x] `GET /api/simulations/{id}/report.pdf` — PDF scaricabile (404 se
      inesistente, 409 se non completata).
- [x] Link "Scarica report PDF" nel dashboard; Dockerfile con le librerie di
      sistema di WeasyPrint (pango/cairo/glib/gdk-pixbuf + font DejaVu).
- [x] **Milestone:** report PDF scaricabile.

## Phase 10 — Polish & hardening (done)

- [x] **Test (pytest)** — confermato dall'utente. Dev deps: pytest,
      pytest-asyncio, pytest-cov, aiosqlite. Suite in `tests/` (engine unit,
      web API con httpx + app lifespan, worker helpers): 38 test verdi.
      `uv run pytest`.
- [x] **Lint/typecheck (ruff + pyright)** — confermato dall'utente.
      Config in `pyproject.toml`; `uv run ruff check .`, `uv run ruff format .`,
      `uv run pyright src/` (0 errori). Violazioni esistenti corrette.
- [x] Error handling: messaggio utente per PVGIS irraggiungibile, guardia
      anti doppio enqueue, `DELETE /api/simulations/{id}` con cleanup delle
      curve su disco + bottone "Elimina" nel dashboard.
- [x] Logging worker (start/end/durata, errori con stack trace).
- [x] `.env.example` completo (incl. `SIMULATION_DATA_DIR`).
- [x] **Milestone:** test, lint e typecheck verdi; deploy documentato.

**MVP completo**: Phases 1-10 terminano. Restano le Fasi 11-13 sul branch
`desktop` (pywebview, vedi ADR-0004).

## Phase 11 — Desktop: SQLite migration (branch `desktop`)

Vedi `docs/adr/0004-desktop-pywebview.md`. Il branch `desktop` diverge da
`main` (che resta web/Docker/PostgreSQL/Redis).

- [ ] Switch `DATABASE_URL`: `postgresql+asyncpg://...` → `sqlite+aiosqlite:///pvsim.db`
- [ ] Alembic: abilitare il batch mode (SQLite non supporta ALTER TABLE nativo)
- [ ] Verificare `alembic upgrade head` su un DB pulito
- [ ] Rimuovere `asyncpg`, `redis`, `arq` dalle dipendenze
- [ ] Rimuovere `docker-compose.yml` (non serve per desktop)
- [ ] **Milestone:** `uv run uvicorn src.web.main:app` parte con SQLite e
      `GET /health` risponde

## Phase 12 — Desktop: rimozione Redis/arq, esecuzione diretta

- [ ] `run_simulation_direct(simulation_id)`: apre una propria sessione DB,
      esegue il pipeline engine in `asyncio.to_thread`, persiste risultati,
      aggiorna lo status
- [ ] `POST /api/simulations`: sostituire
      `request.app.state.arq.enqueue_job(...)` con
      `background_tasks.add_task(run_simulation_direct, sim.id)`
- [ ] Rimuovere il lifespan arq da `src/web/main.py`
- [ ] Rimuovere il package `src/worker/`
- [ ] **Milestone:** il round-trip di una simulazione funziona senza Redis

## Phase 13 — Desktop: pywebview + PyInstaller

- [ ] Aggiungere `pywebview` e `pyinstaller` alle dipendenze
- [ ] Creare `desktop.py`: avvio uvicorn in thread, apertura finestra pywebview
- [ ] Configurare la finestra (titolo, dimensione 1200×800, icona)
- [ ] Gestire il lifecycle: shutdown ordinato (uvicorn si ferma alla chiusura
      della finestra)
- [ ] PyInstaller `.spec` per compilare in singolo eseguibile
- [ ] File `.desktop` (Linux), note per `.plist` (macOS) e `.exe` (Windows)
- [ ] **Milestone:** eseguibile standalone avvia l'app in una finestra nativa

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
