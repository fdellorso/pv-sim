---
description: Esegue la suite di test pytest (infrastruttura da abilitare — vedi roadmap).
---

Esegue la suite di test con pytest.

1. **Prima di procedere**: l'infrastruttura di test deve essere confermata
   dall'utente (vedi `docs/roadmap.md`). Se `pyproject.toml` non contiene la
   config pytest o la directory `tests/` non esiste, segnala che i test non
   sono ancora configurati e chiedi conferma prima di introdurli.
2. Esegui `uv run pytest tests/ -v`.
3. Se presenti, aggiungi `--cov=src --cov-report=term-missing`.
4. Riporta sintesi dei risultati (passed/failed).

Eventuali argomenti aggiuntivi (`$@`) vengono passati a pytest.
