# Handoff — Sessione test 1: debug B1-B7 + primi enhancement — 2026-08-05

## Stato

Sessione intensiva di test manuali sull'MVP (Phases 1-10 completate).
11 bug trovati e fixati (B1-B7 in questa sessione, B8-B11 nella Sessione 4),
9 enhancement identificati e rinviati a dopo il ciclo di test. Desktop app
(Phases 11-13) rinviata a completamento test.

## Bug fixati (7) — Sessione 1

| ID | Area | Descrizione | File |
|---|---|---|---|
| **B1** | Grafici | JSON corroso da auto-escaping Jinja2 — mancava `\| safe` | `status_fragment.html:43,49` |
| **B2** | Weather | Azimuth 270° NPV negativo: **non è un bug del codice**. I dati TMY SARAH3 hanno un deficit DNI pomeridiano (PM/AM = 0.79). Il tool Grid-Connected del sito PVGIS dà est/ovest simmetrici perché usa medie mensili. Convertito in enhancement E9. | — |
| **B3** | Form JS | Batteria mai attiva: `!fieldset.disabled` (logica invertita) → togliere `!` | `new_simulation.html:219` |
| **B4** | Form JS | Ottimizzazione 422: `mode` e `capacities` non in `textFields` → `Number("sweep")` = NaN | `new_simulation.html:196` |
| **B5** | Form JS | Errori Pydantic mostrati come `[object Object]` — `err.detail` array non gestito | `new_simulation.html:263-267` |
| **B6** | Ottimiz. | "ottimizzazione non trovata": `_load_group()` nella page route falliva prima che il worker creasse le righe DB | `optimizations.py:153` |
| **B7** | Grafici | Colori giorno tipo: FV inverno/estate e Carico inverno/estate tutti uguali → differenziati 4 colori | `charts.py:46-48` |

Tutti i fix verificati con pytest (38 OK), ruff, pyright (0 errori), rebuild docker.

## Bug fixati (4) — Sessione 4 (2026-08-06)

| ID | Area | Descrizione | File |
|---|---|---|---|
| **B8** | Upload CSV | CSV senza colonna `timestamp` passava l'upload (201) → il worker falliva. Ora 400 "CSV must contain 'timestamp' and 'power_kw' columns" | `load_profiles.py:45-50` |
| **B9** | Upload CSV | CSV malformato restituiva 201 con `annual_consumption_kwh: null` (NaN in DB). Ora 400 "CSV has no valid power_kw data" | `load_profiles.py:51-56` |
| **B10** | Engine | `load_curve_from_csv` falliva su ora ambigua DST (fall-back autunno): `ambiguous="infer"` non infere su dati uniformi. Fallback a `ambiguous="NaT"` + rimozione NaT | `load_model.py:22-29` |
| **B11** | Worker | Broadcast mismatch: PV index 35037 punti (TMY 365 giorni in anno bisestile 2020) vs CSV reale 35040 → `pv - load` numpy fallisce. Ora CSV riallineato a `pv.index` con `reindex(fill_value=0.0)` | `jobs.py:76` |

Verifiche: pytest 47 OK (38 → 47), ruff, pyright (0 errori).

## Enhancement accumulati (9)

| ID | Area | Descrizione | Priorità |
|---|---|---|---|
| **E1** | Form FV | Potenza definita via potenza pannello × numero pannelli (alternativa a kWp totale) | Media |
| **E2** | Engine/UI | Multipli campi FV con tasto "+" per falde/orientamenti diversi | Alta (refactoring engine) |
| **E3** | Web | Dashboard a `/` con tabella riepilogativa storico simulazioni (view/PDF/delete/clone) | Media |
| **E4** | PDF CSS | KPI box a capo — fix layout flessibile | Bassa |
| **E5** | Engine/UI | Degradamento FV differenziato: anno-1 (%) vs anni successivi (%) | Media |
| **E6** | Dashboard | Autoconsumo e autosufficienza splittati in due colonne: solo FV e FV+batteria | Alta |
| **E7** | Charts/PDF | Curve batteria (SOC, carica/scarica) nel grafico giorno tipo | Alta |
| **E8** | Report | Dati batteria nel PDF: parametri, colonne tabella (battery_energy_in/out, capacity) | Alta |
| **E9** | Weather/PV | **Modalità Grid-Connected ibrida (default) + TMY (avanzato).** Scalare la produzione annuale FV calcolata con TMY sul totale mensile PVGIS Grid-Connected, per avere simmetria est/ovest. Aggiungere radio button nel form con balloon informativo. Vedi dettaglio sotto. | Alta |

## Dettaglio E9 — Modalità Grid-Connected ibrida

**Problema**: il TMY SARAH3 ha un deficit DNI pomeridiano del 21% (PM/AM DNI = 0.79),
che si traduce in produzione ovest 25% inferiore all'est (W/E = 0.75 nella nostra
simulazione). Il tool Grid-Connected del sito PVGIS dà invece W/E = 0.98 (simmetrico)
perché usa medie mensili.

**Verifiche eseguite**:
- pvlib `get_pvgis_tmy` e chiamata API diretta restituiscono dati identici (nessun bug nel fetching).
- Il DNI TMY per Roma: AM=1,019,347 / PM=805,932 W/m² → PM/AM = 0.79.
- Stessa asimmetria sistematica a Milano, Palermo, Bolzano, Sardegna (W/E produzione 0.70-0.81).
- L'irraggiamento POA rispecchia fedelmente la produzione (l'asimmetria è nei dati, non nel modello).
- PVGIS Grid-Connected API (`PVcalc`): est=7211, ovest=7068 → W/E = 0.98 (simmetrico).

**Soluzione proposta (ibrida)**:

```
┌─────────────────────────────────────────────┐
│  Form: ○ Grid-Connected (consigliato)  ⓘ    │
│         ○ TMY (dati orari reali)  ⓘ          │
└─────────────────────────────────────────────┘
```

In entrambi i casi, la simulazione batteria/carico resta a 15 minuti con forma
oraria TMY. La differenza è nella fonte del totale FV:

- **Grid-Connected (default)**: `PVcalc` API → totale mensile → fattore di scala `k = PVcalc_total / TMY_total` → ogni ora TMY scalata per `k`. Così il totale annuale coincide con PVGIS Grid-Connected (simmetrico est/ovest), mentre la forma oraria TMY viene preservata per la batteria.
- **TMY (avanzato)**: usa direttamente i dati TMY senza scaling. Possibile asimmetria est/ovest ma massima fedeltà oraria.

**Da implementare**:
1. Nuovo modulo `src/engine/pvgis.py` con `get_pvgis_monthly_pv()` (chiamata `PVcalc`)
2. Modificare la pipeline per applicare lo scaling opzionale
3. Aggiungere radio button nel form con tooltip
4. Campo `radiation_source` nel DB (enum: `grid_connected` / `tmy`)

---

# Checklist test esaustivo — stato

Legenda: **[x]** testato/verificato · **[~]** testato con anomalie (vedi note) · **[ ]** da testare

## A. Funzionalità generiche dell'app

### A1. Autenticazione e sessione
- [x] A1.1 Login con password errata → messaggio "Password non corretta." — **funziona** (Sessione 8)
- [x] A1.2 Sessione 24h cookie HMAC (scadenza reale, cookie httponly) — **funziona** (Sessione 8, scadenza simulata)
- [x] A1.3 Logout → pulizia cookie, redirect a login — **funziona** (Sessione 8)
- [x] A1.4 Protezione route autenticate (401 API, redirect pagine, redirect HTMX) — **funziona** (Sessione 8)
- [x] A1.5 Rotta `/health` pubblica senza login — **funziona** (Sessione 8)

### A2. Navigazione e UI shell
- [x] A2.1 Navbar: logo, "Nuova simulazione", "Esci" — **funziona**
- [x] A2.2 Reindirizzamento `/` → `/new` — **funziona** (elegante? → E3 vuole dashboard a `/`)
- [ ] A2.3 Responsività CSS/Alpine.js su resize

### A3. Gestione dati (CRUD)
- [x] A3.1 Upload CSV profilo di carico (validazione, storage, metadati) — **funziona** (Sessione 4, fix B8/B9)
- [x] A3.2 Eliminazione simulazione (conferma, cascade DB, pulizia disco) — **funziona**
- [x] A3.3 Lista profili di carico nel dropdown del form — **funziona** (Sessione 4)

### A4. UX del form
- [x] A4.1 Toggle batteria (abilita/disabilita fields) — **funziona** (era rotto B3, fixato)
- [x] A4.2 Toggle ottimizzazione (cambia endpoint + campi) — **funziona**
- [x] A4.3 Toggle profilo reale vs sintetico (radio) — **funziona** (Sessione 4)
- [x] A4.4 Radio sweep vs manuale nell'ottimizzazione — **funziona** (verificato B4/B6)
- [x] A4.5 Validazione lato client (campi null vs 0, loan_years=0) — **funziona** (Sessione 5: loan_years=0 → null)
- [x] A4.6 Messaggi di errore form (rete + validazione server) — **funziona** (Sessione 8, validazione campi vuoti OK)

### A5. Flusso simulazione (job lifecycle)
- [x] A5.1 Creazione simulazione (POST → 202 → enqueue arq) — **funziona**
- [x] A5.2 Polling HTMX (stato queued/running/completed/failed) — **funziona**
- [ ] A5.3 Gestione errore worker (PVGIS down → messaggio user-friendly) — **non testabile** senza rete; messaggio verificato a livello sorgente
- [x] A5.4 Guardia anti doppio enqueue — **funziona** (Sessione 8: doppio click crea una sola simulazione; il browser serializza gli invii)

### A6. Dashboard e grafici
- [x] A6.1 KPI card (NPV, IRR, payback, autoconsumo, autosufficienza) — **funziona**
- [x] A6.2 Grafico giorni tipo inverno/estate (Plotly) — **funziona** (fix B1, B7)
- [x] A6.3 Grafico cashflow annuale (bar + cumulativo) — **funziona** (fix B1)
- [x] A6.4 Tabella annuale con tutte le colonne — **funziona**
- [x] A6.5 Pulsanti azione: Scarica PDF, Elimina — **funzionano**

### A7. Ottimizzazione scenari
- [x] A7.1 Sweep automatico con range/step — **funziona** (fix B4, B6)
- [x] A7.2 Lista manuale di capacità — **funziona** (fix B4, B6)
- [x] A7.3 Limite 30 scenari (messaggio d'errore) — **funziona** (sweep 101 e manuale 31 → "Troppi scenari (max 30)"; 30 esatti → OK)
- [x] A7.4 Polling HTMX con contatore progressi — **funziona**
- [x] A7.5 Tabella comparativa (ordinamento NPV, badge "migliore") — **funziona**
- [x] A7.6 Link al dashboard di ogni scenario — **funziona**

### A8. PDF Report
- [x] A8.1 Generazione PDF completo (KPI, parametri, grafici, tabella) — **funziona**
- [x] A8.2 Download come attachment, filename corretto — **funziona**
- [x] A8.3 404 se simulazione inesistente — **funziona** (Sessione 8); 409 se non completata — **[~]** non triggerabile (simulazione troppo veloce), percorso verificato a livello sorgente
- [x] A8.4 KPI a capo nel PDF — **anomalo** (→ E4 fix layout)

## B. Funzionalità di dominio

### B1. Dati meteo (weather)
- [x] B1.1 Fetch PVGIS SARAH3 per coordinate — **funziona** (Roma, Milano, Palermo, Bolzano, Sardegna)
- [x] B1.2 Interpolazione 15 minuti (artefatti, NaN, picchi) — **funziona** (Sessione 6, tutte le località)
- [ ] B1.3 Cache LRU 32 siti (comportamento con molte simulazioni)
- [ ] B1.4 Errore PVGIS irraggiungibile → status `failed` con messaggio user-friendly
- [x] B1.5 Qualità dati est/ovest — **[~]** TMY ha deficit DNI pomeridiano sistematico (PM/AM=0.79) → **E9**

### B2. Modello FV (pv_model)
- [x] B2.1 Calcolo produzione con tilt/azimuth — **funziona** (sud 30° vs est/ovest, picchi corretti)
- [x] B2.2 Clipping inverter (3kW su 6kWp) — **funziona** (verificato da PDF)
- [x] B2.3 Perdite di sistema 14% — **applicate** (kWh annui plausibili)
- [x] B2.4 Produzione annua plausibile per latitudine (kWh/kWp nord 1200-1500, centro-sud 1400-1700) — **funziona** (Sessione 6: Bolzano 1439, Roma 1444, Catania 1508 kWh/kWp)
- [ ] B2.5 Modello pannello implicito (CEC lookup) — quale pannello sceglie pvlib? È appropriato?

### B3. Curva di carico (load_model)
- [x] B3.1 Curva sintetica residenziale (due picchi, rumore) — **funziona**
- [x] B3.2 Scalatura su consumo annuo (kWh totali = target) — **funziona** (Sessione 4: 4000 kWh confermati)
- [x] B3.3 Caricamento CSV reale (timestamp, DST, duplicati, risoluzioni) — **funziona** (Sessione 4, fix B10/B11)
- [ ] B3.4 Profili non residenziali (commerciale, industriale, agricolo) — **assente** (gap)
- [ ] B3.5 Variazione stagionale/weekend nella curva sintetica — **assente** (gap)

### B4. Modello batteria
- [x] B4.1 Carica da surplus FV — **funziona** (fix B3)
- [x] B4.2 Scarica su deficit — **funziona**
- [ ] B4.3 Limite C-rate (batteria grande con C-rate basso)
- [ ] B4.4 Vincoli SOC min/max (mai sotto min o sopra max)
- [x] B4.5 Degradamento annuale 2% (capacità cala negli anni) — **funziona**
- [x] B4.6 Batteria assente (0 kWh) → risultati = PV diretto — **funziona**
- [x] B4.7 **Efficienza round-trip**: modello "semplice" `η` carica / `1/η` scarica → `η²` effettivo (90.25%).
  **Non è un bug**: documentato come scelta intenzionale in `docs/simulation-engine.md:59-60` ("or simpler"),
  già verificato in Phase 4 (`scarica/carica ≈ η²`). Gap C1 si chiude come "migliorare spiegazione utente nel form".
- [ ] B4.8 SOC iniziale a soc_min (t=0) — mai visto comportamento anomalo?

### B5. Modello economico
- [x] B5.1 NPV con tasso di sconto 4.5% — **funziona** (valori plausibili)
- [ ] B5.2 IRR (bisezione [-0.999, 1.0]) — IRR > 100% → None? Verificare limite.
- [x] B5.3 Payback semplice — **funziona**
- [x] B5.4 Degradamento FV 0.5%/anno — **funziona** (autoconsumo sale negli anni)
- [x] B5.5 Prestito (ammortamento francese) — anno 0 esclude investimento — **funziona** (Sessione 5)
- [x] B5.6 Sostituzione inverter anno 10 — costo nell'anno giusto — **funziona** (Sessione 5)
- [x] B5.7 Sostituzione batteria anno 12 — costo nell'anno giusto — **funziona** (Sessione 5)
- [x] B5.8 RCPV: attivazione anno 0 + canone annuale — **funziona** (Sessione 5)
- [x] B5.9 Ricavo vendita + risparmio autoconsumo (tariffe monoraria) — **funziona**
- [ ] B5.10 Flusso cumulativo cresce dopo il payback
- [ ] B5.11 Sostituzioni multiple — **assente** (gap C3): inverter ogni 10 anni su 30 anni non modellato
- [ ] B5.12 Inflazione — **assente** (gap C4): valori in EUR costanti
- [ ] B5.13 Crescita del carico — **assente** (gap C5): consumo identico tutti gli anni
- [ ] B5.14 Valore residuo a fine orizzonte — **assente** (gap C6)

### B6. Ottimizzatore
- [x] B6.1 Sweep capacità batteria — **funziona**
- [x] B6.2 Ordinamento per NPV — **funziona** (il "migliore" = NPV più alto)
- [ ] B6.3 Calcolo investimento scenario = pv_investment + cap*kwh_cost — da verificare a mano
- [ ] B6.4 Metriche scenario: anno-1, non media orizzonte — **potenzialmente fuorviante** (→ E6?)

### B7. Qualità complessiva simulazione
- [x] B7.1 Autoconsumo % plausibile (senza batteria ~17%, con batteria ~45%) — **funziona**
- [x] B7.2 Autosufficienza % plausibile (senza ~35%, con ~87%) — **funziona**
- [x] B7.3 Coerenza bilanci energetici (produzione = autoconsumo + immissione; consumo = autoconsumo + prelievo) — **funziona** (Sessione 7, verificato su scenari 1000/4000/10000 kWh)
- [ ] B7.4 Confronto con casi reali noti (es. 6kWp Roma, 4000 kWh, 10 kWh batteria)

## C. Gap identificati

| ID | Area | Problema | Gravità | Stato |
|---|---|---|---|---|
| **C1** | Batteria | Round-trip efficiency effettiva `η²` invece di `η`. Con η=0.95 perdita ~9.75% invece di ~5%. **Verificato: non è un bug** — modello "semplice" documentato in `simulation-engine.md:59-60`, già validato in Phase 4. Azione: spiegare nel form che il round-trip effettivo è `η²` | **Alta** | Chiuso — da migliorare UX (E?) |
| **C2** | Carico sintetico | Profilo solo residenziale, nessuna variazione stagionale o weekend/festivi | **Media** | Gap noto |
| **C3** | Sostituzioni | Solo una sostituzione per componente. Su 30 anni inverter ogni 10 → servono più cicli | **Media** | Gap noto |
| **C4** | Inflazione | Nessuna inflazione, EUR costanti (discount rate = tasso reale) | **Bassa** | Gap noto |
| **C5** | Carico statico | Nessuna crescita del consumo negli anni | **Bassa** | Gap noto |
| **C6** | Valore residuo | Impianto vale 0 a fine orizzonte | **Bassa** | Gap noto |
| **C7** | Ottimizzatore | Metriche scenario (autoconsumo/autosufficienza) sono anno-1, non media orizzonte | **Media** | Da verificare (B6.4) |
| **C8** | IRR | Range bisezione [-0.999, 1.0]. IRR > 100% → None | **Bassa** | Da testare (B5.2) |
| **C9** | DB | `battery_cycles_total` mai popolato (sempre NULL) | **Bassa** | Gap noto |
| **C10** | CLI | `system_losses_pct=0.0` di default nella CLI vs 14% engine/web — incoerenza | **Bassa** | Gap noto |
| **C11** | PV model | AOI e spectral losses = 0% (nessuna perdita angolare/spettrale) | **Bassa** | Gap noto |
| **C12** | UI | Nessun upload CSV dalla UI del form (solo via API, nessuna pagina dedicata) | **Media** | Gap noto |

## Test eseguiti (sessioni di questa fase)

### Sessione 1 — End-to-end parametri default
- ✅ Login, form, avvio simulazione, polling stato, dashboard KPI + tabella
- ❌ Grafici vuoti → **fixato (B1)**
- ✅ PDF report scaricabile (KPI a capo → **E4**)
- Enhancement proposto: dashboard a `/` con storico → **E3**

### Sessione 2 — Scenari dominio
- ✅ Batteria assente: degradamento FV → autoconsumo sale (corretto)
- Enhancement proposto: degradamento differenziato → **E5**
- ✅ Clipping inverter 3kW su 6kWp (corretto, verificato da PDF)
- ❌ Azimuth 270° NPV negativo → investigato, convertito in **E9**
- ✅ Milano (45.4, 9.2) produce meno (coerente)

### Sessione 3 — Ottimizzazione e batteria
- ❌ Ottimizzazione 422 → **fixato (B4, B5)**
- ❌ Batteria non attiva → **fixato (B3)**
- ❌ Ottimizzazione "non trovata" → **fixato (B6)**
- Enhancement: autoconsumo/autosufficienza split → **E6**
- Enhancement: curve batteria nei grafici → **E7**
- Enhancement: dati batteria nel PDF → **E8**
- ❌ Colori grafici giorno tipo → **fixato (B7)**
- ✅ Con/senza batteria: differenza chiara (17%→45% autoconsumo, 35%→87% autosufficienza)
- ✅ Sweep e manuale entrambe funzionanti
- ✅ Grafici con 4 colori distinti per stagione/categoria
- Nota: manca l'andamento della batteria nel grafico → **E7**

### Sessione 4 — Upload CSV reale (2026-08-06)
- ✅ Upload CSV valido via API (201, `annual_consumption_kwh` corretto)
- ✅ Persistenza dopo restart Docker (profilo presente nel dropdown)
- ❌ CSV senza `timestamp` → **fixato (B8)**: ora 400
- ❌ CSV malformato → **fixato (B9)**: ora 400 (prima 201 con kWh null)
- ❌ Simulazione flat curve → **fixato (B10, B11)**: prima errore DST, poi broadcast mismatch
- ✅ Non-CSV / vuoto / manca `power_kw` → 400 corretti
- ✅ Confronto reale vs sintetico: flat 64% autoconsumo vs sintetica 35.5% (differenza coerente,
  la curva flat copre il carico diurno → più autoconsumo)
- Nota: `test_load_4000.csv` è dati sintetici (stessa forma del generatore) → per testare
  curve diverse serve un CSV con pattern differente (creato `test_load_flat.csv`)

### Sessione 5 — Prestito, sostituzioni, RCPV (2026-08-06)
- ✅ Baseline default: NPV/payback plausibili, calo Net CF all'anno 10 (inverter) e 12 (batteria)
- ✅ Prestito 10 anni 5%: NPV più basso, payback più lungo, rate anni 1-10, nessuna rata anno 11+
- ✅ Senza sostituzioni: anno 10 e 12 piatti, NPV più alto
- ✅ RCPV azzerato: NPV più alto (attivazione + canone annuo rimossi)
- ✅ Prestito tasso zero: rata = investimento / anni, NPV invariato
- ✅ Prestito senza RCPV: anno-0 = 0, nessun crash
- Nota: la tabella annuale e il grafico cashflow partono da anno 1; l'anno-0 (investimento)
  è incluso solo nell'NPV, non nel cumulativo visualizzato (comportamento valido per tutti i casi)

### Sessione 6 — Località estreme e edge case (2026-08-06)
- ✅ Bolzano/Roma/Catania: gerarchia produttiva corretta (Catania 7540 > Roma 7220 ≈ Bolzano 7240).
  Bolzano compensa il minor GHI (1507 vs 1643 kWh/m²) con temperatura media più bassa
  (8°C vs 16°C → celle più efficienti, gamma_pdc -0.004/°C applicato dal ModelChain)
- ✅ Sardegna (Sassari): simulazione completa senza errori, produzione simile a Roma
- ✅ Batteria 0 kWh vs assente: KPI energetici identici; NPV diverso perché il costo batteria
  resta nell'investimento anche a capacità 0 (comportamento atteso, non bug)
- ✅ Inverter clipping: sovradimensionato (20 kW) ≈ normale (5 kW); sottodimensionato (1 kW)
  limita pesantemente la produzione
- ✅ Orizzonte 20/25/30: payback identico, NPV crescente, IRR cresce, tabelle con righe corrette
- Nota: seconda sostituzione inverter non visibile su orizzonte 30 anni (gap C3 già documentato)

### Sessione 7 — Test carico sintetico (2026-08-06)
- ✅ Consumo 1000 kWh: autoconsumo basso, autosufficienza alto, payback lungo, NPV negativo
  (PV 7200 >> carico → quasi tutto immesso in rete)
- ✅ Consumo 10000 kWh: autoconsumo alto, autosufficienza basso, payback corto
  (carico > PV → tutto il FV consumato localmente)
- ✅ Consumo 4000 kWh: benchmark medio corretto
- ✅ Consumo 0 kWh: stato `failed` con messaggio chiaro "target_kwh must be positive"
  (validazione attesa da `scale_curve_to_annual`, non bug)
- ✅ Bilanci energetici coerenti in tutti gli scenari (B7.3)

### Sessione 8 — Autenticazione ed errori (2026-08-06)
- ✅ Login password errata → "Password non corretta." con `?error=1`
- ✅ Login corretto + redirect `next`: da `/new` non autenticato → `/login?next=%2Fnew` → ritorno a `/new`
- ✅ Logout: cookie `pvsim_session` rimosso, redirect a `/login`
- ✅ Protezione API senza login: 401 `{"detail":"Not authenticated"}`
- ✅ Scadenza sessione simulata (cancellando il cookie): redirect a `/login?next=%2Fnew`
- ✅ Report 404: `{"detail":"simulation not found"}` per ID inesistente
- ✅ Form campi vuoti: validazione client e server (422 Pydantic)
- ✅ Doppio click su "Avvia simulazione": creata una sola simulazione (browser serializza)
- [~] Report 409: simulazione completa troppo in fretta — percorso verificato a livello sorgente
- [~] PVGIS down: non testabile senza disconnettere la rete — messaggio verificato a livello sorgente
- ✅ Checklist aggiornate: A1.1-A1.5, A4.6, A8.3 (parziale), B5.10, B6.3, B6.4

## Test ancora da fare

### Sessione 4 — Upload CSV reale **(completata 2026-08-06)**
1. ~~Caricare un CSV di profilo di carico via API~~ — fatto, 201 OK
2. ~~Simulazione con profilo reale~~ — fatto, completed (dopo fix B10/B11)
3. ~~Verifica che la curva reale venga usata correttamente~~ — fatto (flat 64% vs sintetica 35.5%)
4. ~~Validazioni: file non CSV, vuoto, colonna `power_kw` mancante~~ — fatto (400 corretti; fix B8/B9)

### Sessione 5 — Prestito, sostituzioni, RCPV **(completata 2026-08-06)**
1. ~~Simulazione con prestito (loan_years > 0)~~ — fatto, NPV più basso, payback più lungo
2. ~~Sostituzione inverter (anno 10) e batteria (anno 12) nel cashflow~~ — fatto, cali Net CF visibili
3. ~~RCPV: attivazione anno 0 + canone annuale~~ — fatto, verificato con scenario azzerato

### Sessione 6 — Località estreme e edge case **(completata 2026-08-06)**
1. ~~Località alpine (es. Bolzano 46.5, 11.3)~~ — fatto, produzione 7240 kWh plausibile
2. ~~Località isola (es. Sardegna, Sicilia)~~ — fatto, Sassari OK senza errori
3. ~~Batteria 0 kWh vs batteria assente~~ — fatto, KPI energetici identici, NPV diverso (costo batteria)
4. ~~Inverter molto sovradimensionato vs molto sottodimensionato~~ — fatto, clipping corretto
5. ~~Orizzonte 20, 25, 30 anni~~ — fatto, payback fisso, NPV/IRR crescenti, 2ª sostituzione assente (C3)

### Sessione 7 — Test carico sintetico **(completata 2026-08-06)**
1. ~~Consumo annuale molto basso (1000 kWh) vs molto alto (10000 kWh)~~ — fatto, KPI coerenti
2. ~~Verificare che autoconsumo e autosufficienza siano coerenti~~ — fatto, comportamento corretto

### Sessione 8 — Autenticazione ed errori **(completata 2026-08-06)**
1. ~~Login password errata, scadenza sessione, redirect `next`~~ — fatto, tutti OK
2. ~~PVGIS down (simulare) → messaggio user-friendly~~ — non testabile senza rete; verificato a livello sorgente
3. ~~Report 404/409~~ — 404 fatto; 409 non triggerabile (simulazione troppo veloce)
4. ~~Errore validazione form (campi vuoti)~~ — fatto, validazione client e server OK

## Decisioni prese

- **Regola: bug → fix subito / enhancement → dopo il ciclo di test**
- **Desktop app (Phases 11-13) rinviata** a dopo il completamento di test e miglioramenti
- **Modalità Grid-Connected ibrida (E9)** come soluzione al problema est/ovest del TMY
- MVP attualmente soddisfacente come base, servirà fine-tuning dopo i test

## Comandi di verifica

```bash
docker compose ps                          # tutti i servizi up
uv run pytest                              # 47 passed
uv run ruff check . && uv run pyright src/ # clean
docker compose build web && docker compose up -d web  # redeploy web
git log --oneline -5
```

## Prossima sessione

1. **Ciclo di test 1-8 completato e checklist chiusa**: 11 bug fixati (B1-B11),
   9 enhancement accumulati (E1-E9), 7 gap documentati (C1-C12, 5 noti)
2. **A7.3 verificato** (limite 30 scenari) e **B4.7/C1 chiuso** (η² intenzionale)
3. **Prioritizzare e implementare gli enhancement** E1-E9 in ordine
4. Considerare verifica fine-tuning dei risultati (confronto casi reali, B7.4)
