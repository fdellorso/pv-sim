# Handoff — Fase 6: Worker & job flow — 2026-08-05

## Stato

Fase 6 completata e verificata end-to-end. Il round-trip
web → redis → worker → postgres → web funziona con curva sintetica e curva
reale, con entrambi gli esiti (`completed` e `failed`). Pronto per la Fase 7
(Web UI: forms & dashboard).

## Completato

- [x] `src/worker/jobs.py`:
  - `run_simulation(ctx, simulation_id)`: transizioni di stato nel DB
    (`queued` → `running` → `completed` | `failed` con `error_message`);
    esegue il pipeline engine in thread (`asyncio.to_thread`) perché
    CPU-bound (pvlib + loop batteria); in caso di eccezione marca `failed`
    e rilancia (per il retry/registro arq)
  - `_run_pipeline(sim, load_profile)`: deserializza l'ORM `Simulation` in
    `PVSystemParams`, `BatteryParams`, `EconomicParams`, sceglie la curva
    reale (via `load_profile.file_path`) o sintetica
    (`generate_synthetic_curve` su `annual_consumption_kwh`)
  - `_to_result_rows()` / `_to_metrics()`: mappano `EconomicResult` nelle
    tabelle `simulation_results` (una riga per anno) e `simulation_metrics`
    (IRR `None` → 0.0 perché la colonna è NOT NULL; `battery_cycles_total`
    lasciato NULL — il modello batteria non espone i cicli)
- [x] `src/worker/main.py`: `WorkerSettings` con `on_startup`/`on_shutdown`
  come funzioni module-level (vedi decisione sotto) che iniettano
  `src.web.database.async_session` nel ctx e chiudono l'engine.
- [x] `src/web/routes/simulations.py`:
  - `POST /api/simulations` (202): valida `load_profile_id` XOR
    `annual_consumption_kwh`, crea la riga, enqueue via
    `request.app.state.arq.enqueue_job("run_simulation", id)`
  - `GET /api/simulations/{id}`: status + metrics + risultati annuali (JSON)
  - `GET /simulations/{id}` e `GET /simulations/{id}/status`: pagina minima
    e frammento HTMX con polling `every 2s` (si auto-arresta a job finito)
- [x] `src/web/main.py`: lifespan FastAPI che crea il pool arq con
  `create_pool` (disponibile in arq 0.28) e lo espone su `app.state.arq`.
- [x] `src/web/templates/simulation_status.html` + `status_fragment.html`
  (template minimi; la dashboard completa è della Fase 7).
- [x] Roadmap aggiornata (Fase 6 done).

## Decisioni prese in questa sessione

- Callback arq `on_startup`/`on_shutdown` devono essere **funzioni
  module-level**, non metodi di classe: `create_worker` passa
  `WorkerSettings.__dict__` al costruttore `Worker`, che poi chiama
  `self.on_shutdown(ctx)`. Un metodo di classe finiva unbound e falliva con
  `TypeError: missing 1 required positional argument: 'ctx'`.
- Il pool redis web usa `arq.connections.create_pool` (in arq 0.28
  `ArqRedis.create` non esiste più).
- Pipeline CPU-bound in thread per non bloccare l'event loop del worker;
  `max_jobs=1` già in place. L'ORM `Simulation` viene letto prima del thread
  (attributi già caricati), quindi nessun accesso concorrente alla sessione.
- Config: il worker riusa `src.web.database.engine`/`async_session`
  (creati all'import con `DATABASE_URL` dalle env di compose).
- Template path assoluto (`Path(__file__)...`) per robustezza alla CWD.

## Verifiche eseguite

Stack ricostruito (`docker compose build web worker`) e riavviato. Test:

```bash
# curva sintetica con batteria → completed, 25 righe + metriche
curl -s -X POST http://localhost:8000/api/simulations -H "Content-Type: application/json" -d '{...}'
curl -s http://localhost:8000/api/simulations/1
#   → status completed, NPV 4877, IRR 8.4%, payback anno 9, 25 risultati
# postgres: 25 righe in simulation_results + 1 riga simulation_metrics
# curva reale (load_profile_id=1) → completed (autoconsumo ~20%)
# load profile con file mancante → status failed, error_message=FileNotFoundError
docker compose exec postgres psql -U pvsim -d pvsim -c "SELECT ..."
```

Valori coi default del modello (system_losses 14%) → NPV 4877 €; il riferimento
della Fase 5 (NPV 6831 €) usava `--system-losses-pct 0` nel CLI: differenza
attesa, non un bug.

## Domande aperte / blocchi

- `battery_cycles_total` è sempre NULL (nessun calcolo cicli nel battery model).
  Da decidere in Fase 8 (optimizer) se computarlo come scarica/capacità.
- LSP: pyright segnala "import not resolved" su `sqlalchemy`, `arq` ecc. ma
  sono artefatti del server non riavviato (verificati via `uv run`).
- Nessun browser installato per Playwright (`npx playwright install chrome`
  fallisce): la UI è stata verificata via curl sui template.

## Comandi di verifica

```bash
uv run python -c "from src.worker.jobs import run_simulation; from src.web.main import app; print('OK')"
docker compose build web worker && docker compose up -d web worker
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/api/simulations -H "Content-Type: application/json" -d '{...}'
git log --oneline -1
```

## Prossimi passi

1. **Fase 7 — Web UI: forms & dashboard**:
   - SPA shell (`base.html`, Alpine.js), navigazione, auth a password singola
   - Form parametri → crea simulazione + enqueue (riusa `POST /api/simulations`)
   - Dashboard risultati: KPI card, grafici Plotly (produzione/carico,
     cashflow), tabella annuale; polling HTMX sul frammento già esistente
   - Milestone: run end-to-end dal browser
2. Vedere `docs/roadmap.md` per le Fasi 7-10.
