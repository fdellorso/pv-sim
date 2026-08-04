---
description: Esegue una simulazione rapida da CLI per debugging dell'engine.
---

Esegue una simulazione da riga di comando per debug rapido dell'engine.

1. Verifica che `src/engine/cli.py` esista (creato dalla Fase 2). Se non
   esiste, segnala che il CLI non è ancora implementato.
2. Se `$1` è un file di configurazione JSON, usalo; altrimenti usa il caso
   demo predefinito o i parametri passati come `$@` (key=value).
3. Esegui `uv run python -m src.engine.cli $@`.
4. Riporta il riepilogo: produzione annuale, autoconsumo %, autosufficienza %,
   NPV, IRR, payback.
