# Handoff — Fase 3: Load model — 2026-08-04

## Stato

Fase 3 completata e committata (`3cfbdf9`). Il motore carica curve di carico
reali da CSV e genera curve sintetiche scalate sul consumo annuo; il web espone
l'upload delle curve con persistenza metadata su PostgreSQL. Pronto per la
Fase 4 (battery model).

## Completato

- [x] `src/engine/load_model.py`:
  - `load_curve_from_csv(file_path, tz)`: CSV `timestamp,power_kw`,
    localizzazione tz-aware con gestione DST (`ambiguous="infer"`,
    `nonexistent="shift_forward"`), resample a 15 minuti, dedup index
  - `scale_curve_to_annual(curve, target_kwh)`: scala `sum*dt = target_kwh`
    con validazioni su target/energia
  - `generate_synthetic_curve(index, annual_consumption_kwh, seed=42)`:
    profilo 96-step (picchi 07-09 e 18-22, base 0.2, rumore gaussiano seed
    fisso), anno completo senza troncamento
- [x] `src/engine/cli.py`: opzioni `--load-csv FILE`, `--load-synthetic`,
      `--annual-consumption` (default 4000); stampa anche `Consumo (kWh)`
- [x] `src/web/routes/load_profiles.py`: `POST /api/load-profiles/upload`
      (multipart CSV, profile_type, description) → salva in
      `data/load_profiles/`, inserisce riga `LoadProfile`, ritorna `{id, ...}`
- [x] `src/web/main.py`: registrato il router
- [x] `pyproject.toml`: aggiunto `python-multipart` (serve a FastAPI per upload)
- [x] Roadmap aggiornata (Fase 3 done)

## In corso / da completare

- [ ] Battery, economics, optimizer, report: ancora solo stub con docstring
- [ ] Job worker `run_simulation` solleva `NotImplementedError`
- [ ] Upload senza autenticazione (l'auth arriva in Fase 7)
- [ ] Selezione profilo "simile" da archivio (worker, Fase 6): il motore
      riceve già solo `file_path`
- [ ] Test/lint non configurati (Fase 10, da confermare con l'utente)

## Decisioni prese in questa sessione

- Il web NON importa `src.engine` (vincolo architetturale): il calcolo di
  `annual_consumption_kwh` nell'upload usa pandas inline, non `load_model`
- File CSV archiviati con nome uuid (`<hex>.csv`) per evitare collisioni e
  sanitizzazione percorsi; `file_path` assoluto salvato nel DB
- Il bug del prototipo (anno troncato a 364 giorni) è risolto nel generatore
  sintetico; CLI e generatore usano l'indice completo (35037 step)
- `python-multipart` aggiunto come dipendenza esplicita

## Domande aperte / blocchi

- Nessuno. Nota: il CLI ora stampa `Produzione FV (kWh): 7426.7` e
  `Consumo (kWh): 4000.0` — coerente con l'anno completo (il prototipo con
  troncamento dava 7406.7, vedi handoff Fase 2).
- LSP: pyright attivo e funzionante (ha rilevato 2 errori di tipo in
  `load_model.py`, corretti). Gli errori "import not resolved" residui sono
  artefatti di server LSP non riavviato; import verificati via `uv run`.

## Comandi di verifica

```bash
uv run python -m src.engine.cli --load-synthetic --annual-consumption 4000
uv run python -m src.engine.cli --load-csv data/load_profiles/test_load_4000.csv
uv run python -c "import src.engine.load_model, src.engine.cli"
# Upload via Docker (stack già avviato):
curl -F "file=@data/load_profiles/test_load_4000.csv" -F "profile_type=residential" \
     http://localhost:8000/api/load-profiles/upload
docker compose exec postgres psql -U pvsim -d pvsim -c "SELECT * FROM load_profiles;"
git log --oneline -1                                      # 3cfbdf9 (Fase 3)
```

## Prossimi passi

1. **Fase 4 — Battery model**:
   - `src/engine/battery_model.py`: carica/scarica con C-rate, efficienza
     round-trip (default 95%), SOC clamp `[soc_min, soc_max]`, degrado annuo
     2%
   - Wired nel pipeline: surplus FV → batteria → carico; calcolo
     autoconsumo/autosufficienza
   - Estendere CLI con flag batteria e output autoconsumo/autosufficienza
   - Milestone: autoconsumo/autosufficienza calcolati con batteria per un anno
2. Vedere `docs/roadmap.md` per la sequenza completa (Fasi 4-10).
