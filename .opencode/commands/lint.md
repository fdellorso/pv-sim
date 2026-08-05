---
description: Esegue lint e typecheck (ruff check + format, pyright).
---

Esegue linting, formattazione e typecheck sul progetto.

1. Esegui `uv run ruff check .`
2. Esegui `uv run ruff format --check .`
3. Esegui `uv run pyright src/`
4. Se ci sono violazioni, proponi e applica le correzioni (per le righe
   lunghe: `uv run ruff format .`; per il typecheck: cast o annotazioni
   mirate), poi rilancia i comandi per confermare che siano puliti.
5. Riporta errori e warning residui.

Eventuali argomenti aggiuntivi (`$@`) vengono passati a ruff/pyright.
