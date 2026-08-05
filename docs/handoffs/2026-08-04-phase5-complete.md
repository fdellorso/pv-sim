# Handoff — Fase 5: Economic model — 2026-08-04

## Stato

Fase 5 completata e committata (`826fd59`). Il motore produce il riepilogo
economico multi-anno completo (cashflow per anno, NPV, IRR, payback) con
prestito, manutenzione, sostituzioni, RCPV e tariffe monoraria. Pronto per la
Fase 6 (worker & job flow).

## Completato

- [x] `src/engine/economic_model.py`:
  - `EconomicParams` (frozen): `horizon_years`, `investment_cost_eur`,
    `purchase_eur_kwh`/`sell_eur_kwh`, `maintenance_annual_eur`,
    `inverter_replacement_cost_eur`/`inverter_replace_at_year` (10),
    `battery_replacement_cost_eur`/`battery_replace_at_year` (12),
    `grid_activation_eur` (one-time), `grid_annual_eur`,
    `loan_interest_pct`/`loan_years`, `pv_degradation_pct_year` (0.5),
    `discount_rate_pct` (4.5)
  - `AnnualCashflow` (per-anno, campi allineati alla tabella
    `simulation_results`), `EconomicResult` (npv, irr, payback, annual)
  - `compute_annuity()`: ammortamento francese
    `P·r·(1+r)^n / ((1+r)^n - 1)`; gestisce rate 0 e tasso 0
  - `compute_irr()`: bisezione su `[-0.999, 1]`; ritorna `None` se nessun
    root nel range (es. investimento sempre positivo)
  - `run_economics()`: per ogni anno `y` degrada PV (`(1-deg)^(y-1)`) e
    capacità batteria (`effective_capacity`), calcola flussi energia con
    `run_battery`, poi cashflow; NPV con discount sul flusso `[anno 0,
    1..n]`, payback sul cumulativo (incluso investimento)
- [x] `src/engine/cli.py`: 15 nuovi flag economici (`--horizon`,
      `--investment-cost-eur`, `--purchase/sell-eur-kwh`,
      `--maintenance-annual-eur`, `--inverter-replacement-cost`,
      `--inverter-replace-at-year`, `--battery-replacement-cost`,
      `--battery-replace-at-year`, `--grid-annual-eur`,
      `--grid-activation-eur`, `--loan-interest-pct`, `--loan-years`,
      `--pv-degradation`, `--discount-rate`); tabella annuale compatta +
      riepilogo NPV/IRR/payback
- [x] Roadmap aggiornata (Fase 5 done)

## In corso / da completare

- [ ] Optimizer, report: ancora solo stub con docstring
- [ ] Job worker `run_simulation` solleva `NotImplementedError` (Fase 6)
- [ ] Persistenza risultati in `simulation_results`/`simulation_metrics`
      (Fase 6)
- [ ] Test/lint non configurati (Fase 10, da confermare con l'utente)

## Decisioni prese in questa sessione

- Modello prestito: quando `loan_years > 0` l'investimento è finanziato → la
  rata annuity SOSTITUISCE l'esborso iniziale (niente doppio conteggio);
  anno 0 = solo `grid_activation`. Verifica: con `loan_rate == discount`
  l'NPV resta identico al caso senza prestito (matematicamente corretto);
  con `loan_rate > discount` l'NPV scende (es. 8% → 7665 €)
- IRR con leva finanziaria: con prestito al 4.5% e discount 4.5% l'IRR
  leveraged è alto (30.9%) perché l'esborso iniziale è solo l'attivazione
  (100 €); comportamento atteso, da mostrare con cautela nella UI
- NPV su `full_cashflows = [-investimento(0) , cf_1..cf_n]` dove
  `investimento(0)` include `grid_activation_eur`; payback cumulativo parte
  dallo stesso valore
- `compute_irr` usa confronto di segno (non prodotto) per evitare overflow
  a `lo=-0.999` con cashflow positivi grandi

## Domande aperte / blocchi

- Nessuno. Risultati di riferimento (5 kWp, 4000 kWh, 12000 €, 25 anni,
  0.30/0.12 €/kWh, batteria 10 kWh 0.5C):
  - senza batteria: NPV 974 €, IRR 5.3%, payback anno 16
  - con batteria: NPV 6831 €, IRR 9.8%, payback anno 9
  - con batteria + prestito 10y @4.5%: NPV 6831 €, IRR 30.9%, payback anno 13
- LSP: pyright attivo; errori "import not resolved" residui sono artefatti di
  server LSP non riavviato; import verificati via `uv run`.

## Comandi di verifica

```bash
uv run python -m src.engine.cli --load-synthetic --annual-consumption 4000 --battery-capacity 10 --horizon 25
uv run python -m src.engine.cli --load-synthetic --annual-consumption 4000 --battery-capacity 10 --horizon 25 --loan-interest-pct 4.5 --loan-years 10
uv run python -c "import src.engine.economic_model, src.engine.cli"
uv run python -c "from src.engine.economic_model import compute_annuity, compute_irr; print(compute_annuity(12000, 4.5, 10)); print(compute_irr([-100.0, 110.0]))"
git log --oneline -1                                      # 826fd59 (Fase 5)
```

## Prossimi passi

1. **Fase 6 — Worker & job flow**:
   - `src/worker/main.py` + `src/worker/jobs.py`: entry point arq, job
     functions, transizioni di stato nel DB (`queued` → `running` →
     `completed` | `failed`)
   - Il job deserializza i parametri, esegue il pipeline engine
     (weather → pv → load → battery → economics), persiste i risultati in
     `simulation_results` + `simulation_metrics` e aggiorna lo status
   - Web enqueues jobs (arq); endpoint HTMX per polling dello status
   - Milestone: round-trip completo web → redis → worker → postgres → web
2. Vedere `docs/roadmap.md` per la sequenza completa (Fasi 6-10).
