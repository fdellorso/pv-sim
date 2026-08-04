# ADR-0002: Meteo — PVGIS-SARAH3 via pvlib

Usiamo i dati meteorologici PVGIS-SARAH3 recuperati attraverso
`pvlib.iotools.get_pvgis_tmy`. Il riferimento è l'anno meteorologico tipico
(TMY), gratuito, copertura globale e sufficiente per analisi di investimento.
La fonte è adatta al caso d'uso "FV connesso in rete".

Status: accepted

Considered options:

- **Chiamata diretta all'API PVGIS**: più controllo sui parametri ma duplica
  parsing e gestione errori già coperti da pvlib.
- **ERA5 / NSRDB / Solcast**: utili per anni reali specifici o risoluzioni
  maggiori, ma aggiungono credenziali/costi e complessità non necessari per
  l'MVP. Rimandati come opzione futura.

Consequence: PVGIS richiede connessione di rete al primo fetch; gestire il
fallimento con messaggio chiaro all'utente e possibilità di retry. I dati
vengono cache-ati per lat/lon per evitare fetch ripetuti.
