---
description: Avvia lo stack di sviluppo completo (web, worker, redis, postgres) con docker compose.
---

Avvia l'ambiente di sviluppo completo.

1. Verifica che `docker-compose.yml` esista alla radice del progetto.
2. Se non esiste ancora (Fase 0 in corso), informa l'utente che verrà creato in
   Fase 1 e non eseguire nulla.
3. Verifica la presenza di `.env` (referenzia `docs/development.md`); se
   manca, avvisa l'utente.
4. Esegui `docker compose up --build -d`.
5. Mostra `docker compose ps` e riporta l'URL web (default
   http://localhost:8000).

Se l'utente ha aggiunto argomenti (es. `logs`), passali al comando
`docker compose` rilevante.
