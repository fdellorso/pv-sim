# Handoff — Fase 9: PDF report — 2026-08-05

## Stato

Fase 9 completata e verificata su docker: `GET /api/simulations/{id}/report.pdf`
restituisce un PDF valido con parametri, KPI, grafici e tabella annuale.
Pronto per la Fase 10 (Polish & hardening).

## Completato

- [x] **`src/web/report.py`**: `build_report_pdf(sim, metrics, results,
      curves) -> bytes`.
  - Grafici renderizzati con **matplotlib** (Agg headless): `_daily_curves_png`
    (FV/carico inverno vs estate) e `_cashflow_png` (barre netto + linea
    cumulativa su asse secondario). PNG → base64 → `<img src="data:...">`.
  - HTML standalone dal template `templates/report.html` (Jinja2) → WeasyPrint
    `HTML(string=...).write_pdf()`.
- [x] **`templates/report.html`**: `@page A4`, footer, KPI card, tabella
  parametri, due grafici, tabella annuale (8 colonne). Font DejaVu.
- [x] **Route**: `GET /api/simulations/{id}/report.pdf` in
  `routes/simulations.py` — carica sim/metrics/results, legge le curve,
  esegue `build_report_pdf` in `asyncio.to_thread` (CPU-bound), restituisce
  `Response` con `Content-Disposition: attachment`. 404 se inesistente,
  409 se non `completed`.
- [x] **UI**: link "Scarica report PDF" sotto le KPI in
  `templates/status_fragment.html`.
- [x] **`src/engine/report.py`**: stub aggiornato con rimando a
  `src.web.report` (il report è una web concern: DB + curve + template).
- [x] **Dockerfile**: aggiunte le librerie di sistema di WeasyPrint
  (`libcairo2`, `libpango-1.0-0`, `libpangoft2-1.0-0`, `libpangocairo-1.0-0`,
  `libgdk-pixbuf-2.0-0`, `libglib2.0-0`, `shared-mime-info`,
  `fonts-dejavu-core`).
- [x] Roadmap aggiornata (Fase 9 done).

## Decisioni prese in questa sessione

- **matplotlib al posto di kaleido/plotly** per i grafici del PDF: kaleido
  v1+ richiede Chrome (`plotly_get_chrome`), troppo pesante per l'immagine
  Docker. matplotlib è già una dipendenza del progetto, funziona headless
  con backend Agg e produce PNG di qualità da stampa. I grafici web (plotly)
  restano invariati; c'è una leggera duplicazione delle due figure.
- Il modulo report vive in `src/web/` (non engine): usa DB, curve persistite
  e template Jinja2; il file `src/engine/report.py` è solo uno stub con
  docstring di rimando per non violare l'isolamento dell'engine.
- PDF generato on-demand (nessuna cache): per un MVP single-user è
  sufficiente; una cache/rigenerazione alla Fase 10 se servisse.

## Verifiche eseguite

```bash
curl -s -o report4.pdf -b cookies.txt http://localhost:8000/api/simulations/4/report.pdf
#   HTTP 200, type application/pdf, 108 KB, "PDF document, version 1.7"
pdftotext report4.pdf -   # contiene: Report simulazione, NPV, IRR, Payback,
                          # Parametri, Campo fotovoltaico, Cashflow annuale, Andamento annuale
# immagini nel PDF: 4 oggetti /Image (grafici embeddati)
curl .../api/simulations/999/report.pdf    # 404
curl .../api/simulations/{id-queued}/report.pdf   # 409 (sim non completata)
```

## Domande aperte / blocchi

- Il primo avvio di `web` è più lento (~2-3s in più) per l'import di
  WeasyPrint + matplotlib.
- LSP: pyright segnala "import not resolved" su `sqlalchemy`/`arq`/`plotly`
  ecc. — artefatti del server non riavviato (import verificati via `uv run`).
- Playwright senza browser: PDF verificato via curl + `pdftotext`, non con un
  browser reale.

## Comandi di verifica

```bash
uv run python -c "from src.web.report import build_report_pdf; from src.web.routes.simulations import download_report; print('OK')"
docker compose build web && docker compose up -d web
curl -s -o /tmp/report.pdf -b cookies.txt http://localhost:8000/api/simulations/4/report.pdf && file /tmp/report.pdf
git log --oneline -1
```

## Prossimi passi

1. **Fase 10 — Polish & hardening** (da confermare con l'utente prima di
   aggiungere tooling):
   - Test pytest, lint/typecheck (ruff + pyright) — **chiedere conferma**
   - Error handling, logging, edge cases (bad CSV, PVGIS outage)
   - Docs di deploy e `.env.example` finale
2. Vedere `docs/roadmap.md` per le Fasi 10 e 11-13 (branch `desktop`).
