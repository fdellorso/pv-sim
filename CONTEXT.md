# PV-Sim Context

Analisi economica di investimenti in impianti fotovoltaici: simulazione della
produzione FV, dell'accumulo e del confronto con il consumo per calcolare
autoconsumo, autosufficienza e ritorno sull'investimento su orizzonti
temporali configurabili.

## Language

**Autoconsumo**:
Quota di energia prodotta dall'impianto FV consumata direttamente in loco.
Espresso in kWh/anno o come percentuale della produzione totale.
_Avoid_: autoconsumo %, self-consumption rate

**Autosufficienza**:
Quota del consumo totale dell'utenza coperta dalla produzione propria
(diretta o da batteria). Percentuale del carico soddisfatto localmente.
_Avoid_: indipendenza, autarky

**Curva di carico**:
Profilo temporale del consumo di energia (tipicamente a risoluzione 15 minuti
per un anno). Può essere reale (CSV importato e archiviato) o sintetica
(derivata da curve reali simili e scalata sul consumo annuo).
_Avoid_: profilo di consumo, load profile

**Degradamento**:
Riduzione progressiva annua della capacità di un componente. Per i pannelli
riduce la produzione; per la batteria riduce la capacità utilizzabile.
_Avoid_: degrado, deterioration

**C-rate**:
Tasso di carica/scarica di una batteria espresso in multipli della capacità.
Es. 0.5C su una batteria da 10 kWh = potenza massima di 5 kW.
_Avoid_: tasso C

**Clipping**:
Limitazione della potenza di uscita dell'inverter alla sua potenza nominale.
Può essere imposto per vincoli di allacciamento alla rete, riducendo la
produzione immessa.
_Avoid_: power limiting, taglio di potenza

**RCPV**:
Referto/Raccolta costi di gestione per impianto fotovoltaico allacciato alla
rete dell'operatore elettrico. Include un costo una tantum di attivazione per
contatore e un costo annuale per contatore.
_Avoid_: costo gestione rete

**Profilo di consumo tipo**:
Identificazione di una curva di carico reale in archivio (tipo di utenza,
fonte, stagionalità) usata come modello per casi senza curva reale.
_Avoid_: tipo di profilo

**Costo evitato**:
Risparmio ottenuto non acquistando dalla rete l'energia autoconsumata,
calcolato al prezzo di acquisto.
_Avoid_: risparmio energia, savings

**Scenario batteria**:
Configurazione di capacità e C-rate di una batteria da confrontare in una
simulazione (manuale o risultato dell'ottimizzatore).
_Avoid_: caso batteria
