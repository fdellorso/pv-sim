# ADR-0004: Variante desktop con pywebview, SQLite e esecuzione diretta

Su un branch `desktop` separato, PV-Sim diventa un'app standalone che gira in
una finestra nativa via pywebview, usando SQLite come database e FastAPI
BackgroundTasks al posto di Redis + arq. Il frontend HTMX + Alpine.js +
Plotly resta identico.

Status: accepted

Considered options:

- **Dual-mode configurabile**: un flag sceglie SQLite/PostgreSQL e
  esecuzione diretta/arq. Più elegante ma introduce astrazioni non necessarie
  per un MVP desktop; due branch puliti sono più manutenibili e il core
  `src/engine/` resta comunque identico e condiviso.
- **Sync SQLite**: refactoring completo a route sync per semplicità. Troppo
  lavoro: riscrivere tutte le route, le sessioni e la dependency injection;
  non giustificato per un'app single-user.
- **Elettron + Node.js backend**: introduce una toolchain JS estranea allo
  stack Python del progetto. Scartata.
- **Flask + webview**: inconsistente con lo stack esistente (FastAPI).
  Scartata.

Decisione (sul branch `desktop`):

- **Database**: SQLite via `aiosqlite` mantenendo SQLAlchemy async. Cambia
  solo `DATABASE_URL`; route, sessioni e engine restano async.
- **Esecuzione simulazioni**: FastAPI `BackgroundTasks` sostituisce la coda
  arq; il pipeline engine gira in `asyncio.to_thread` in-process, aprendo una
  propria sessione DB e persistendo i risultati. Niente Redis, niente worker.
- **Entry point**: `desktop.py` avvia uvicorn in un thread, apre la finestra
  pywebview su `http://localhost:8000` e gestisce lo shutdown ordinato.
- **Packaging**: PyInstaller compila l'app in un singolo eseguibile.
- Il branch `main` resta invariato (Docker, PostgreSQL, Redis, arq).

Consequence: SQLite non scala oltre il single-user (accettabile per design);
le migrazioni Alembic richiedono il batch mode (SQLite non supporta ALTER
TABLE nativo); la distribuzione diventa un singolo eseguibile senza dipendenze
runtime esterne. I due branch divergono solo in `src/web/` e nelle
configurazioni di deploy; il motore economico/simulazione rimane condiviso.
