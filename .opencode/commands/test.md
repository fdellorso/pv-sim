---
description: Esegue la suite di test pytest.
---

Esegue la suite di test con pytest.

1. Esegui `uv run pytest tests/ -v`.
2. Se richiesto, aggiungi la copertura: `uv run pytest tests/ --cov=src --cov-report=term-missing`.
3. Riporta la sintesi dei risultati (passed/failed) e, in caso di failure,
   il primo errore con il file/riga interessato.

Eventuali argomenti aggiuntivi (`$@`) vengono passati a pytest.
