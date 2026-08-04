---
description: Esegue lint e typecheck (ruff check + pyright). Da abilitare — vedi roadmap.
---

Esegue linting e typecheck sul progetto.

1. **Prima di procedere**: lint/typecheck devono essere confermati dall'utente
   (vedi `docs/roadmap.md`). Se `ruff` o `pyright` non sono in
   `pyproject.toml` dev dependencies, segnalalo e chiedi conferma prima di
   aggiungerli.
2. Esegui `uv run ruff check src/` .
3. Esegui `uv run pyright src/`.
4. Riporta errori e warning; se presenti, proponi le correzioni.

Eventuali argomenti aggiuntivi (`$@`) vengono passati a ruff/pyright.
