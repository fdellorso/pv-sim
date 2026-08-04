# PV-Sim

Analisi economica di investimenti in impianti fotovoltaici con accumulo.

PV-Sim simula la produzione di un impianto FV con la libreria
[pvlib](https://pvlib-python.readthedocs.io/), la confronta con curve di
carico (reali o sintetiche) e batterie con vincoli C-rate, e calcola
autoconsumo, autosufficienza e ritorno sull'investimento su orizzonti di
20/25/30 anni — includendo degradamento, finanziamento bancario, manutenzione
ordinaria e straordinaria, e costi di gestione rete (RCPV).

## Funzionalità

- **Produzione FV**: dati meteo PVGIS-SARAH3, orientamento/inclinazione
  configurabili, clipping dell'inverter e perdite di sistema.
- **Accumulo**: batterie con C-rate (0.1C–1C), efficienza round-trip e
  degradamento della capacità.
- **Curve di carico**: import di profili reali (CSV) salvati in archivio, o
  generazione sintetica a partire da profili archiviati simili.
- **Ottimizzazione**: sweep automatico della capacità batteria e confronto
  manuale di scenari.
- **Analisi economica**: NPV, IRR, payback; prestito bancario, manutenzione,
  sostituzione inverter (anno 10) e batteria (anno 12), costi contatore/RCPV.
- **Tariffe**: monoraria per acquisto e vendita energia.
- **Interfaccia web**: dashboard SPA (FastAPI + HTMX + Alpine.js) con grafici
  Plotly e report PDF scaricabile.
- **Deploy**: stack `docker-compose` (web, worker, redis, postgres) con un
  singolo processo worker.

## Avvio rapido

```bash
# Stack completo in Docker
docker compose up --build
# Web: http://localhost:8000
```

Setup completo: [docs/development.md](docs/development.md).

## Struttura

```
src/web/        FastAPI app (SPA HTMX, auth, routes)
src/worker/     arq worker (un solo processo)
src/engine/     simulazione: weather, pv_model, load_model,
                battery_model, economic_model, optimizer, report
docs/           architecture, roadmap, development, api, database,
                simulation-engine, adr/, handoffs/
data/load_profiles/   archivio curve di carico (CSV)
```

## Documentazione

- [Architettura](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Guida sviluppo](docs/development.md)
- [Simulation engine](docs/simulation-engine.md)
- [Database](docs/database.md)
- [API](docs/api.md)
- [Decisioni (ADR)](docs/adr/)

## Sviluppo

```bash
uv sync                       # dipendenze host
docker compose up --build -d  # stack completo
python pvlib_autoconsumo_simulazione.py  # prototipo standalone (sarà sostituito)
```

Per le convenzioni dell'agente e il workflow plan→build, vedi
[AGENTS.md](AGENTS.md) e il glossario in [CONTEXT.md](CONTEXT.md).
