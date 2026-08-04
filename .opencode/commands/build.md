---
description: Costruisce le immagini Docker dei servizi del progetto.
---

Costruisce le immagini Docker del progetto.

1. Verifica che `docker-compose.yml` (o i Dockerfile) esistano. Se non
   esistono ancora (Fase 0 in corso), segnalalo e non eseguire nulla.
2. Se `$1` specifica un servizio (es. `web`, `worker`), costruisci solo
   quello con `docker compose build <service>`; altrimenti `docker compose build`.
3. Riporta le immagini costruite con `docker images | grep pvsim`.
