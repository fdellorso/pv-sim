# Handoff Template

Use this template for handoff documents at phase boundaries. Save as
`docs/handoffs/YYYY-MM-DD-<slug>.md`.

```markdown
# Handoff — <Phase/Scope> — <Date>

## Stato

Breve riassunto: cosa è stato completato, cosa è funzionante.

## Completato

- [ ] item
- [ ] item

## In corso / da completare

- [ ] item con eventuale motivo del blocco

## Decisioni prese in questa sessione

- Decisione (riferimento ADR se presente)

## Domande aperte / blocchi

- Domanda, con contesto

## Comandi di verifica

```bash
# come verificare lo stato attuale
```

## Prossimi passi

1. Primo passo
2. Secondo passo
```

## Regole

- Scrivi un handoff alla fine di ogni fase (o quando richiesto con `/handoff`).
- Sii conciso ma completo: chi legge deve poter riprendere senza domande.
- Riferisci sempre ADR e file di documentazione rilevanti.
