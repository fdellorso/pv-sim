# ADR-0003: Batteria — C-rate vincolato e degrado lineare annuale

Il modello batteria vincola la potenza di carica/scarica al C-rate
configurabile (0.1C–1C), applica un'efficienza round-trip e riduce la capacità
utilizzabile con un degrado lineare annuale (default 2%/anno). Le sostituzioni
sono modellate a livello economico (anno 12) e non come calo forzato della
capacità a fine vita.

Status: accepted

Considered options:

- **Degrado per ciclo (cycle aging)**: più fisico ma richiede un conteggio
  cicli aggiuntivo e parametri da datasheet raramente disponibili; il degrado
  lineare annuale è sufficiente per analisi economica.
- **SOC non vincolato (0–100%)**: più semplice ma irrealistico; manteniamo un
  SOC minimo/massimo configurabile (default 10–90%) per proteggere la batteria.
- **Sostituzione guidata dalla capacità effettiva (end-of-life)**: si
  allontana dal requisito esplicito dell'utente di sostituire a 12 anni.

Consequence: le stime annuali di energia (autoconsumo/autosufficienza)
dipendono dal degrado di capacità; i risultati economici sono sensibili al
C-rate, quindi va esposto chiaramente nel form.
