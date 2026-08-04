---
description: Scrive un documento di handoff sotto docs/handoffs/ per passaggio di consegna tra fasi.
---

Scrive un documento di handoff per il passaggio di consegna a fine fase.

1. Se `$1` fornisce uno slug, usalo nel nome file; altrimenti genera uno slug
   dallo scope corrente.
2. Nome file: `docs/handoffs/YYYY-MM-DD-<slug>.md`.
3. Usa il template in `docs/handoffs/template.md`.
4. Contenuto minimo:
   - Stato: cosa è completato e funzionante
   - Elenco completato / da completare
   - Decisioni prese (con riferimenti ADR)
   - Domande aperte / blocchi
   - Comandi di verifica
   - Prossimi passi
5. Rileggi il documento e verifica che chi riprende possa continuare senza
   dover fare domande.
