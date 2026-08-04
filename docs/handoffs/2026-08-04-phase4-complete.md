# Handoff — Fase 4: Battery model — 2026-08-04

## Stato

Fase 4 completata e committata (`6f58c83`). Il motore simula la batteria a
passi di 15 minuti con vincoli C-rate, efficienza round-trip e degrado annuo;
il CLI calcola autoconsumo/autosufficienza con e senza batteria. Pronto per la
Fase 5 (economic model).

## Completato

- [x] `src/engine/battery_model.py`:
  - `BatteryParams` (frozen): `capacity_kwh`, `c_rate` (default 0.5),
    `efficiency` (default 0.95), `soc_min_pct`/`soc_max_pct` (10/90),
    `degradation_pct_year` (default 2)
  - `BatteryResult`: autoconsumo (kWh + %), autosufficienza %, grid export/import,
    battery charge/discharge
  - `run_battery(pv, load, params, dt=0.25)`: loop step 15min, power limit
    `c_rate × capacity`, SOC clamp `[soc_min, soc_max] × capacity`,
    carica `p*dt*η` / scarica `p*dt/η`, priorità carica da surplus dopo
    autoconsumo diretto e scarica sul deficit prima dell'import
  - `effective_capacity(params, year)`: `capacity × (1 - deg/100)^(year-1)`
- [x] `src/engine/cli.py`: flag `--battery-capacity` (default 10),
      `--battery-crate` (default 0.5), `--no-battery`; output
      `Autoconsumo (kWh)`, `Autoconsumo %`, `Autosufficienza %` e (con
      batteria) `Ricaricato/Scaricato batteria (kWh)`
- [x] Roadmap aggiornata (Fase 4 done)

## In corso / da completare

- [ ] Economics, optimizer, report: ancora solo stub con docstring
- [ ] Job worker `run_simulation` solleva `NotImplementedError`
- [ ] Degrado annuale applicato nel pipeline multi-anno (Fase 5): il helper
      `effective_capacity` c'è ma il pipeline non lo usa ancora
- [ ] Test/lint non configurati (Fase 10, da confermare con l'utente)

## Decisioni prese in questa sessione

- Efficienza asimmetrica per trip (come da `docs/simulation-engine.md`):
  carica stocca `p*dt*η`, scarica preleva `p*dt/η`. Verifica di coerenza:
  `scarica/carica ≈ η²` (0.902 vs 0.9025) — OK
- `capacity_kwh=0` equivale a niente batteria (autoconsumo diretto
  `min(pv, load)`), riusato dal CLI per il caso `--no-battery`
- Degrado non applicato dentro `run_battery` (che simula un solo anno); verrà
  gestito nel pipeline multi-anno che chiama `effective_capacity` per ogni
  anno (Fase 5)

## Domande aperte / blocchi

- Nessuno. Risultati di riferimento (sintetico 4000 kWh, 5 kWp, Zürich):
  senza batteria autoconsumo 17.1% / autosufficienza 31.8%; con batteria
  10 kWh 0.5C autoconsumo 50.5% / autosufficienza 87.7%.
- LSP: pyright attivo; errori "import not resolved" residui sono artefatti di
  server LSP non riavviato; import verificati via `uv run`.

## Comandi di verifica

```bash
uv run python -m src.engine.cli --load-synthetic --annual-consumption 4000 --no-battery
uv run python -m src.engine.cli --load-synthetic --annual-consumption 4000 --battery-capacity 10 --battery-crate 0.5
uv run python -c "import src.engine.battery_model, src.engine.cli"
uv run python -c "from src.engine.battery_model import BatteryParams, effective_capacity; p=BatteryParams(10.0); print(effective_capacity(p, 10))"
git log --oneline -1                                      # 6f58c83 (Fase 4)
```

## Prossimi passi

1. **Fase 5 — Economic model**:
   - `src/engine/economic_model.py`: cashflow per anno (savings, vendita,
     manutenzione, sostituzioni inverter anno 10 / batteria anno 12, RCPV,
     rata prestito), orizzonte 20/25/30 anni
   - Annuity (ammortamento francese), NPV con discount rate, IRR (numerico),
     payback (cumulativo ≥ 0)
   - Pipeline multi-anno: produzione anno 1 riusata con degrado PV, capacità
     batteria con `effective_capacity`
   - Estendere CLI con costi/economia e output NPV, IRR, payback
   - Milestone: CLI restituisce il riepilogo economico completo per uno
     scenario
2. Vedere `docs/roadmap.md` per la sequenza completa (Fasi 5-10).
