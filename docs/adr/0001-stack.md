# ADR-0001: Stack — FastAPI + HTMX + Alpine.js, PostgreSQL, Redis + arq

Decidiamo lo stack: web SPA con FastAPI + Jinja2 + HTMX + Alpine.js (nessun
framework JS pesante), grafici Plotly lato server, database PostgreSQL,
coda job Redis + arq con un singolo processo worker, deploy docker-compose
multi-servizio. Preferiamo uno stack Python leggero che copra tutto senza
doppio codebase frontend/backend.

Status: accepted

Considered options:

- **Streamlit**: sviluppo rapidissimo ma scarsa flessibilità per UI parametrica
  multi-schermata e stile professionale.
- **FastAPI + React/Vue**: flessibile ma aggiunge toolchain JS, build step e
  doppio codebase non necessari per un tool single-user.
- **Flask + Jinja + HTMX**: valido, ma FastAPI offre typing, async nativo e
  docs automatiche che tornano utili per API e integrazione con arq.
