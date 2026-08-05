# Handoff — Fase 7: Web UI forms & dashboard — 2026-08-05

## Stato

Fase 7 completata e verificata via curl sul docker stack: login → form →
enqueue → polling HTMX → dashboard con KPI, grafici Plotly e tabella annuale.
Lascia in DB una simulazione demo (id 4) per verifica manuale dal browser.
Pronto per la Fase 8 (Optimizer & battery scenarios).

## Completato

- [x] **Auth password singola** (`src/web/auth.py`, `src/web/routes/auth.py`):
  cookie firmato HMAC-SHA256 (stdlib, niente itsdangerous — non è
  installato) con TTL 24h; `GET/POST /login`, `POST /logout`; middleware in
  `main.py` che protegge tutto tranne `/login`, `/health`, `/static/`; API
  senza cookie → 401 JSON, richieste HTMX → redirect a `/login`.
- [x] **SPA shell** (`templates/base.html`): topbar con nav, HTMX 2.0.4,
  Alpine.js 3.14.8, plotly.js 2.35.2 via CDN, helper `renderPlots()` che
  renderizza i grafici da `<script type="application/json">` embeddati
  (su DOMContentLoaded e `htmx:afterSwap`).
- [x] **Form parametri** (`templates/new_simulation.html`, route
  `GET /new` in `routes/pages.py`): sezioni Luogo / FV / Carico (sintetica
  o profilo reale) / Batteria (toggle) / Tariffe / Economia. Submit via
  fetch a `POST /api/simulations` con conversione numerica e null per i
  campi disattivati; redirect a `/simulations/{id}` al 202.
- [x] **Dashboard** (`templates/simulation_status.html` +
  `status_fragment.html`): pagina che polla `/simulations/{id}/status`
  ogni 2s (spinner in running, errore in failed); a job completato mostra
  KPI card (NPV, IRR, payback, autoconsumo/autosufficienza medi), grafici
  Plotly e tabella annuale (25 righe).
- [x] **Grafici server-side** (`src/web/charts.py`):
  - `daily_curves_figure`: FV e carico su giorno tipo inverno (15/01) e
    estate (15/07), 4 trace × 96 punti, x = ora del giorno.
  - `cashflow_figure`: barre netto annuo + linea cumulativo su asse secondario.
  - `read_curves`: ricostruisce le Series 15-min dai JSON persistiti.
- [x] **Persistenza curve** (`src/worker/jobs.py`): `_run_pipeline` ora
  restituisce `PipelineResult(economic, pv_year1, load_year1)`; `run_simulation`
  scrive `data/simulation_data/{id}/pv_year1.json` + `load_year1.json`
  (formato `{start, freq, tz, values}`, tz nominativa per correttezza DST).
- [x] **Config/deploy**: `simulation_data_dir` in `src/web/config.py`
  (default `/data/simulation_data`); volume condiviso web+worker in
  docker-compose; mount statico con path assoluto.
- [x] Roadmap aggiornata (Fase 7 done).

## Decisioni prese in questa sessione

- Curse year-1 persistite su disco (non in DB): coerente con la regola
  "curves on disk, DB = metadata" e con "no JSONB per l'MVP". 35037 punti
  (TMY non-leap) per serie, file ~400-700 KB.
- Cookie firmato HMAC con stdlib invece di itsdangerous (non installato):
  zero nuove dipendenze; TTL 24h, `HttpOnly`, `SameSite=Lax`.
- Grafici generati server-side a job completato e embeddati come JSON nel
  frammento (non nel payload API): il polling si ferma a completamento,
  quindi le figure sono costruite una sola volta.
- Form: submit client-side via fetch (non HTMX) per la conversione dei tipi
  numerici e il redirect programmatico; `POST /simulations` server-side non
  necessario.
- `/` reindirizza a `/new` (la lista simulazioni è rimandata a un
  miglioramento futuro, non nel perimetro della milestone).

## Verifiche eseguite

```bash
# auth
curl -s -o /dev/null -w "%{http_code} %{redirect_url}" http://localhost:8000/new        # 303 /login?next=/new
curl -s -X POST -d "password=wrong" .../login                                            # 303 /login?error=1
curl -s -c cookies.txt -X POST -d "password=change-me" .../login                         # 303 /
curl -s -b cookies.txt .../new                                                           # 200
curl -s -X POST .../api/simulations senza cookie                                         # 401
# round-trip
curl -s -b cookies.txt -X POST .../api/simulations -d '{...}'                            # {"id":4,"status":"queued"}
curl -s -b cookies.txt .../simulations/4/status                                          # completed
#   KPI: NPV/IRR/Payback/Autoconsumo medio/Autosufficienza media
#   charts: data-plotly=chart-daily (4 trace×96), chart-cashflow (bar+line, 25 anni)
#   table: 25 righe dati
docker compose exec web ls /data/simulation_data/4/    # pv_year1.json, load_year1.json
```

## Domande aperte / blocchi

- Playwright senza browser installato (`npx playwright install chrome` fallisce
  per Chromium non presente): UI verificata via curl sul rendering HTML/JSON,
  non con un browser reale. Consiglio una verifica manuale su
  `http://localhost:8000` (password `change-me`).
- LSP: pyright segnala "import not resolved" su `sqlalchemy`, `plotly`, `arq`
  ecc. — artefatti del server non riavviato (import verificati via `uv run`).
- `battery_cycles_total` resta NULL (Fase 8 potrà computarlo).

## Comandi di verifica

```bash
uv run python -c "from src.web.main import app; from src.web.charts import read_curves; from src.worker.jobs import run_simulation; print('OK')"
docker compose build web worker && docker compose up -d web worker
curl -s http://localhost:8000/health
git log --oneline -1
```

## Prossimi passi

1. **Fase 8 — Optimizer & battery scenarios**:
   - `src/engine/optimizer.py` (attualmente stub): sweep della capacità
     batteria, sceglie max IRR/NPV.
   - Confronto manuale di più scenari in UI (capacità multiple).
   - Milestone: pulsante "ottimizza" che ritorna capacità ottimale + metriche.
2. Vedere `docs/roadmap.md` per le Fasi 8-10 (e 11-13 sul branch `desktop`).
