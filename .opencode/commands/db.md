---
description: Gestisce il database: migrazioni Alembic, reset, seed.
---

Gestisce il database PostgreSQL tramite Alembic.

Sottocomandi (passati come `$1`):

- `upgrade` (default) — `alembic upgrade head`
- `revision <msg>` — genera nuova migrazione autogenerate
- `downgrade` — `alembic downgrade base`
- `reset` — downgrade base + upgrade head (drop & recreate schema)
- `seed` — inserisce dati di esempio (profilo di carico demo, se definito)
- `status` — `alembic current`

Prima di ogni comando verifica che `alembic.ini` e `migrations/` esistano e che
il database sia raggiungibile. Se Alembic non è ancora configurato (Fase 1),
segnalalo all'utente e non eseguire nulla.

Esegui sempre all'interno del container `postgres` raggiungibile o con
`DATABASE_URL` impostato (vedi `docs/development.md`).
