# Handoff — Fase 8: Optimizer & battery scenarios — 2026-08-05

## Stato

Fase 8 completata e verificata end-to-end sul docker stack. L'ottimizzazione
della capacità batteria funziona (sweep automatico e elenco manuale) con
pagina di confronto e scenario migliore evidenziato. Lascia in DB un gruppo
demo (`ad2ba059996e4235b204fcf97ba62fb4`, 5 scenari, sim 6-10). Pronto per
la Fase 9 (PDF report).

## Completato

- [x] **`src/engine/optimizer.py`**: `sweep_capacities(pv, load, economic,
      battery, capacities, cost_per_kwh, replace_per_kwh)` → `list[ScenarioResult]`
      ordinata per NPV discendente. `ScenarioResult` espone le metriche chiave
      + l'`EconomicResult` completo (serve al worker per la persistenza).
      L'investimento FV-only è recuperato con
      `investment - battery_base.capacity_kwh * cost_per_kwh`; ogni scenario
      investe `pv_only + capacity * cost_per_kwh` e sostituisce la batteria a
      `capacity * replace_per_kwh`.
- [x] **DB** (`src/web/models.py` + migrazione `526bc9b689fb`):
      tabella `optimization_scenarios` (id, optimization_group index,
      simulation_id FK CASCADE, capacity_kwh, metriche nullable). Nessuna
      modifica alle tabelle esistenti.
- [x] **`src/worker/jobs.py`**:
  - refactor: `_build_base_inputs(sim, load_profile)` estratta da
    `_run_pipeline` (riusabile per weather+PV+load+params base).
  - `run_optimization(ctx, payload)`: crea subito una Simulation per ogni
    capacità + le righe OptimizationScenario (per progress e gestione errori);
    builda base inputs una volta sola; `sweep_capacities` in thread; per ogni
    scenario persiste results+metrics, setta `sim.battery_capacity_kwh` e le
    metriche dello scenario; scrive le curve solo per il migliore.
- [x] **`src/worker/main.py`**: `run_optimization` registrato in `functions`.
- [x] **`src/web/routes/optimizations.py`**:
  - `POST /api/optimizations` (202): `OptimizationCreate` (estende
    `SimulationCreate`), genera UUID di gruppo, calcola capacities da
    `mode` (sweep via np.arange / manual da CSV), forza
    `battery_capacity_kwh=None`, enqueue `run_optimization`.
  - `GET /api/optimizations/{group}`: scenari + Simulation join, ordinati per
    NPV desc (completed prima, poi running/queued, poi failed); `best` =
    primo completed; flag `done`.
  - Pagine: `GET /optimizations/{group}` + frammento HTMX poll `every 3s`.
- [x] **UI form**: sezione "Ottimizza capacità batteria" (toggle Alpine,
    mode sweep/manual, range o elenco, costi €/kWh); JS instrada a
    `/api/optimizations` e redirect a `/optimizations/{group}` quando attivo,
    altrimenti flusso singolo invariato.
- [x] **Template**: `optimization_group.html` + `optimization_fragment.html`
    (tabella comparativa, badge "migliore", link dashboard per scenario,
    spinner con progress x/N durante il run). CSS `row-best`/`badge-best`.
- [x] Roadmap aggiornata (Fase 8 done).

## Decisioni prese in questa sessione

- **Riga scenario creata subito per ogni capacità** (Simulation + riga
  OptimizationScenario vuota) invece che a fine calcolo: dà progress
  (x/N completati) e gestione errori per-scenario (riga `failed`).
- **Niente tabella di gruppo**: lo stato è derivato dagli scenario; il titolo
  è ricavato dal nome della prima simulation con una regex che toglie il
  suffisso " — X kWh". Evita una tabella extra.
- **Investimento in modalità ottimizza = costo FV senza batteria**: il form
  lo spiega; `battery_capacity_kwh` è forzato a None nella route così
  `pv_only = investment_cost_eur`.
- **`is not none` (minuscolo) nei template Jinja**: `is not None` fallisce
  ("No test named 'None' found").
- **Criterio di scelta**: NPV massimo (il roadmap citava IRR/NPV; NPV più
  stabile con leva). IRn/Payback restano visibili in tabella.
- Curve scritte solo per lo scenario migliore (spazio su disco).

## Verifiche eseguite

```bash
# sweep 0-10 step 2.5 → 5 scenari (sim 6-10), best = 0 kWh NPV 5750
curl -s -b cookies.txt -X POST .../api/optimizations -H "Content-Type: application/json" -d '{...}'
#   → {"optimization_group":"ad2ba05...","scenarios":5}
curl -s -b cookies.txt .../api/optimizations/ad2ba05...
#   → done:true, best NPV 5749.6 (0 kWh), 5 scenari per NPV decrescente
curl -s -b cookies.txt .../optimizations/ad2ba05.../status
#   → tabella 6 <tr> (1 header + 5 righe), badge-best "migliore", link dashboard
curl -s -b cookies.txt .../api/simulations/7
#   → completed, 25 righe, NPV 5385.7 (coerente con la tabella)
docker compose exec postgres psql -c "SELECT ... optimization_scenarios"  # 5 righe
```

Nota: per le modifiche ai template serve `docker compose build web` (il codice
è baked nell'immagine, non montato). Il servizio `migrate` va ricostruito
(`docker compose build migrate`) dopo aver aggiunto una migrazione, altrimenti
fallisce con "Can't locate revision".

## Domande aperte / blocchi

- Playwright senza browser: UI verificata via curl sul rendering HTML.
  Verifica manuale consigliata su `http://localhost:8000/new` (toggle
  "Ottimizza") — password `change-me`.
- LSP: pyright segnala import "not resolved" su `sqlalchemy`/`arq`/`plotly` —
  artefatti del server non riavviato (import verificati via `uv run`).
- `battery_cycles_total` resta NULL (non nel perimetro Fase 8).

## Comandi di verifica

```bash
uv run python -c "from src.web.main import app; from src.web.routes.optimizations import OptimizationCreate; from src.engine.optimizer import sweep_capacities; from src.worker.jobs import run_optimization; print('OK')"
docker compose build web worker migrate && docker compose up -d web worker
DATABASE_URL=postgresql+asyncpg://pvsim:pvsim@localhost:5432/pvsim uv run alembic upgrade head
git log --oneline -1
```

## Prossimi passi

1. **Fase 9 — PDF report**:
   - `src/engine/report.py` (stub): generazione PDF (WeasyPrint) dai risultati
     (metriche, tabella annuale, grafici).
   - `GET /api/simulations/{id}/report.pdf` → download.
   - Milestone: report PDF scaricabile.
2. Vedere `docs/roadmap.md` per le Fasi 9-10 (e 11-13 sul branch `desktop`).
