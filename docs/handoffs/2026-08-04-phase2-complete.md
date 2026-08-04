# Handoff — Fase 2: Weather & PV model — 2026-08-04

## Stato

Fase 2 completata e committata (`c151e11`). Il motore calcola la produzione FV
annuale da PVGIS-SARAH3 a 15 minuti e il profilo è bit-identico al prototipo
per gli stessi parametri. Pronto per la Fase 3 (load model).

## Completato

- [x] `src/engine/weather.py`: `get_weather(lat, lon, tz, year=2020)` — fetch
      PVGIS TMY (SARAH3) con `lru_cache` su `(lat, lon)`, reindex orario,
      resample+interpolazione a 15 minuti, indice `DatetimeIndex` tz-aware
- [x] `src/engine/pv_model.py`: dataclass `PVSystemParams` + `run_pv_model()`
      con `PVSystem`/`ModelChain` (aoi/spectral no_loss, temperature sapm,
      identici al prototipo), clipping inverter `min(ac, inverter_kw)`,
      perdite di sistema (`system_losses_pct`, default 14%)
- [x] `src/engine/cli.py`: smoke test `/sim` con argomenti CLI
      (`uv run python -m src.engine.cli`)
- [x] Roadmap aggiornata (Fase 2 done)

## In corso / da completare

- [ ] Load, battery, economics, optimizer, report: ancora solo stub con
      docstring
- [ ] Job worker `run_simulation` solleva `NotImplementedError`
- [ ] Degrado annuale non ancora esposto (si applicherà nel pipeline engine,
      Fasi 4-5)
- [ ] Test/lint non configurati (Fase 10, da confermare con l'utente)

## Decisioni prese in questa sessione

- `weather.py` espone `get_weather(...) -> pd.DataFrame` completo di
  interpolazione; il cache raw (`_fetch_pvgis_tmy`) è separato per non
  rifare il fetch se cambiano tz/year
- `PVSystemParams` dataclass frozen: parametri PV raggruppati e passati
  esplicitamente a `run_pv_model`
- `system_losses_pct` nel CLI default 0.0 per confronto 1:1 col prototipo;
  il default di `PVSystemParams` resta 14% (come da `docs/simulation-engine.md`)
- Il prototipo `pvlib_autoconsumo_simulazione.py` resta in repo finché la Fase
  3 non lo sostituisce (per confronto benchmark)

## Domande aperte / blocchi

- Nota importante sul confronto col prototipo: il modello PV del motore è
  **bit-identico** (max diff 0.0), ma il CLI stampa `7426.7 kWh` mentre il
  prototipo stampa `7406.7`. La differenza NON è nel modello PV: il generatore
  di carico sintetico del prototipo tronca l'anno a 364 giorni
  (`35037 // 96 = 364`), tagliando ~4h di produzione. Da correggere in Fase 3.
- Pyright/ruff non installati globalmente: gli errori LSP "import not
  resolved" sono artefatti del server LSP non riavviato; import verificati
  funzionanti via `uv run`. Lint/typecheck restano in Fase 10.

## Comandi di verifica

```bash
uv run python -m src.engine.cli                          # Produzione FV (kWh): 7426.7
uv run python -m src.engine.cli --lat 41.9 --lon 12.5 --power-kw 6 --tilt 35 --system-losses-pct 14
uv run python -c "import src.engine.weather, src.engine.pv_model, src.engine.cli"
git log --oneline -1                                      # c151e11 (Fase 2)
git status --short                                        # working tree pulito
```

## Prossimi passi

1. **Fase 3 — Load model**:
   - `src/engine/load_model.py`: carica curva CSV reale (formato
     `timestamp,power_kw`) + modello metadata `load_profiles`
   - Generatore sintetico: profilo archivio "simile", scalato sul consumo
     annuo; correggere il bug del prototipo (anno completo 365 giorni)
   - Upload flow in web: salva CSV in `data/load_profiles/`, riga metadata
   - Milestone: una simulazione gira con curva reale o sintetica
2. Vedere `docs/roadmap.md` per la sequenza completa (Fasi 3-10).
