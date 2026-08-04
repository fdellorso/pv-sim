# Handoff — Fase 0: Setup & documentazione — 2026-08-04

## Stato

Fase 0 completata e committata (`9934b9e`). L'ambiente opencode è configurato,
le skills sono nel progetto, la documentazione è completa. Pronto per la
Fase 1 (infrastruttura Docker + scheletro del progetto).

## Completato

- [x] Skills remote installate e spostate nel progetto
      (`.opencode/skills/`: domain-modeling, tdd,
      supabase-postgres-best-practices) + skill custom `pv-sim`
- [x] Rimosse le copie globali (`~/.agents/skills/` e symlink rotti in
      `~/.claude/skills/`); resta solo `find-skills` globale di sistema
- [x] 8 comandi in `.opencode/commands/`: dev, db, test, sim, lint, build,
      handoff, commit
- [x] `opencode.json` aggiornato: LSP pyright + ruff, `skills.paths`,
      `instructions: [AGENTS.md, CONTEXT.md]`, permission ripristinate
      (deny su commands, skills, opencode.json, tui.json)
- [x] `AGENTS.md` e `CONTEXT.md` riscritti; `README.md` riscritto
- [x] `docs/`: architecture, roadmap, development, api, database,
      simulation-engine, adr (0001-stack, 0002-pvgis, 0003-battery),
      handoffs/template
- [x] `.gitignore` esteso (`.env*`, `data/load_profiles/*.csv`)
- [x] `data/load_profiles/.gitkeep` creato

## In corso / da completare

- [ ] Riavvio opencode per caricare la nuova config (skills paths, LSP ruff)
- [ ] Nessun codice dell'app ancora scritto: `main.py` è placeholder,
      `pvlib_autoconsumo_simulazione.py` è il prototipo da sostituire

## Decisioni prese in questa sessione

- Stack: FastAPI + HTMX + Alpine.js, PostgreSQL, Redis + arq (ADR-0001)
- Meteo: PVGIS-SARAH3 via pvlib, TMY (ADR-0002)
- Batteria: C-rate vincolato 0.1C–1C, degrado lineare, sostituzione anno 12
  (ADR-0003)
- Skills per-progetto (non globali)
- Permission edit su config/skills/commands ripristinate dopo la Fase 0

## Domande aperte / blocchi

- Nessuno. Le permission bloccano l'editing di `.opencode/commands/*`,
  `.opencode/skills/*`, `opencode.json`, `tui.json`: per modifiche future a
  questi file va chiesta all'utente una rimozione temporanea.

## Comandi di verifica

```bash
git log --oneline -3        # deve mostrare 9934b9e (Fase 0)
git status --short          # working tree pulito
python3 -m json.tool opencode.json > /dev/null && echo "config valida"
ls .opencode/skills/ .opencode/commands/   # skills e comandi presenti
```

## Prossimi passi

1. **Fase 1 — Infrastruttura & skeleton**:
   - `docker-compose.yml` (web, worker, redis, postgres) + Dockerfile
   - `pyproject.toml`: fastapi, uvicorn, sqlalchemy, alembic, redis, arq,
     jinja2, pydantic-settings, plotly, weasyprint
   - Scheletro `src/web/`, `src/worker/`, `src/engine/`
   - Prima migrazione Alembic (tabelle `simulations`, `load_profiles`,
     `simulation_results`)
   - Milestone: `docker compose up` avvia tutto e web risponde su :8000
2. **Fase 2** — weather.py + pv_model.py con CLI smoke test
   (confrontare produzione anno-1 con `pvlib_autoconsumo_simulazione.py`)
3. Vedere `docs/roadmap.md` per la sequenza completa 1-10.
