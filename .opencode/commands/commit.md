---
description: Crea un commit git con messaggio convenzionale (Conventional Commits).
---

Crea un commit git con messaggio convenzionale.

1. Esegui `git status` e `git diff --stat` per esaminare le modifiche.
2. Verifica che non ci siano segreti o file da non committare (`.env`,
   `data/load_profiles/*.csv`).
3. Se `$1` fornisce un messaggio, usalo; altrimenti chiedi all'utente uno
   scopo e ricava un messaggio convenzionale: `type(scope): description`
   (tipi: feat, fix, docs, chore, refactor, test, build, ci, perf).
4. Esegui `git add` dei file pertinenti e `git commit -m "<message>"`.
5. Non fare push a meno che l'utente lo chieda esplicitamente.
