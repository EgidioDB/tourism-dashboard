# Tourism Dashboard — Analisi del Turismo Italiano

Dashboard interattiva per l'analisi delle presenze turistiche in Italia, con focus sul Comune di Cefalù e confronto con i benchmark regionali e nazionali. Copre il periodo **1956–2024** con dati ISTAT ed Eurostat.

---

## Demo

Apri `index.html` direttamente nel browser — nessun server necessario, nessuna dipendenza da installare.

---

## Funzionalità

### Mappa interattiva d'Italia
- Click su una regione per aprire il pannello di analisi regionale
- Zoom automatico sulla regione selezionata
- Donut chart che si aggiorna con i volumi della regione (alberghiero vs extra-alberghiero, pre/post 2012)

### Pannello regionale
Ogni regione mostra quattro gruppi di indicatori, tutti con popup nominali (click su ogni riga):

| Gruppo | Confronto | Metrica |
|--------|-----------|---------|
| Pre-2012 | 2004 vs 2012 | Arrivi, Presenze, Extra-Alb |
| Post-2012 | 2014 → 2024 | Arrivi, Presenze, Alb, Extra-Alb |
| Pre-COVID | 2014 → 2019 | Arrivi, Presenze, Alb, Extra-Alb |
| Post-COVID | 2019 → 2024 | Arrivi, Presenze, Alb, Extra-Alb |

I popup nominali mostrano i valori assoluti (es. `13.200.000 notti`) per presenze, alberghiero ed extra-alberghiero. Sono inclusi anche i dati della **Top City** della regione (comune con maggiore crescita) e il gap rispetto alla media nazionale.

### Sintesi Italia
Pannello fisso con gli stessi quattro gruppi temporali a livello nazionale, con valori assoluti derivati dinamicamente dai dati ISTAT (base 2012: 380.711.483 presenze totali).

### Grafico Evoluzione Storica
- Serie 2004–2024 per Cefalù vs media Italia
- Quattro metriche: Presenze, Arrivi, Alberghiero, Extra-Alberghiero
- Modalità pan/zoom, highlight per anno, linea di riferimento 2012
- Aggiornamento dinamico dal JSON del comune selezionato

### Classifica Crescita Comuni
- Top comuni italiani per crescita presenze 2014→2024
- Filtro per soglia minima presenze (>500k)
- Ordinabile per crescita totale, pre-COVID, post-COVID

### Sezione Confronta
- Confronto diretto tra Cefalù e qualsiasi altro comune italiano (5.324 disponibili)
- Dataset scaricabile in CSV

---

## Struttura del progetto

```
tourism-dashboard/
│
├── index.html                          # Applicazione completa (tutto inline)
│
├── data/
│   ├── italia.json                     # Serie storica nazionale 1956–2024
│   │                                   # Arrivi e presenze: totale, alb, ext, residenti/non-res
│   ├── regioni.json                    # Serie regionale 2008–2024 (20 regioni)
│   │                                   # Arrivi e presenze totali per anno
│   ├── comuni_index.json               # Indice dei 5.324 comuni con dati
│   │                                   # Metadati: cod_istat, nome, provincia, regione
│   │                                   # Statistiche: max_arr, max_pre, growth_pre
│   ├── serie/                          # 5.324 file JSON, uno per comune
│   │   └── {cod_istat}.json            # Serie 2014–2024: arr/pre × tot/alb/ext × res/nres
│   ├── stagionalita.json               # Dati di stagionalità
│   ├── popolazione.json                # Dati popolazione comunale
│   ├── province.json                   # Anagrafica province
│   ├── ricettiva.json                  # Dati strutture ricettive
│   ├── ricettiva_index.json            # Indice strutture ricettive
│   ├── bilancio.json                   # Bilancio comunale generico
│   ├── bilancio_cefalu_armonizzato.json
│   ├── bilancio_cefalu_consuntivo.json
│   ├── bilancio_cefalu_rendiconti_pdf.json
│   ├── irpef_cefalu.json               # Dati IRPEF Cefalù
│   └── PIL/                            # Dati PIL per area
│
└── DCSC_Occupancy_in_collective_accommodation/
    ├── 1. Serie storiche.xlsx          # Serie storica nazionale alb/ext 1954–2013
    ├── 2. Dati comunali 2014-2024.xlsx # Presenze comunali per tipo struttura
    ├── 3. Dati per circoscrizione turistica 2004-2013.xlsx
    │                                   # Presenze per circoscrizione turistica (pre-2014)
    │                                   # Usato per calcolo preExt regionale 2004 vs 2012
    └── 4. Dati per provenienza 2024.xlsx # Provenienza turisti per area 2024
```

---

## Fonti dati

| Dato | Fonte | Periodo | Note |
|------|-------|---------|------|
| Presenze/Arrivi nazionali | ISTAT | 1956–2024 | Serie storica completa alb/ext |
| Presenze/Arrivi regionali | ISTAT | 2008–2024 | Solo totale, no split alb/ext |
| Presenze/Arrivi comunali | ISTAT | 2014–2024 | 5.324 comuni, split completo |
| Volumi regionali 2024 | Eurostat `tour_occ_nin2` | 2024 | NUTS2, alb/ext separati |
| Presenze regionali 2004/2012 | ISTAT `DF_BULK_DCSC_TURISAREA` | 2004–2013 | Per circoscrizione turistica |
| Spesa turistica pubblica | BDAP / RGS | 2019–2023 | Aggregata per ente |

### Costanti di base (2012)
```
Presenze totali Italia 2012:        380.711.483
Presenze extra-alberghiero 2012:    125.101.340
Presenze alberghiero 2012:          255.610.143
```

---

## Come circolano i dati

L'obiettivo è avere **una sola fonte di verità per ogni grandezza**: gli indicatori derivati vengono ricalcolati a runtime, mai memorizzati in parallelo. Aggiornare il JSON aggiorna tutta la dashboard.

### Derivati a runtime

| Grandezza | Derivata da | Funzione |
|-----------|-------------|----------|
| `rawData.it*` (2004–2024) | `data/italia.json` | `syncItaliaFromJson()` |
| `itAlb`, `itBenchmark`, `volumeData.Italia` | `rawData.it*` + costanti 2012 | `syncItaliaDerived()` |
| `rawData.cef*` (2014–2024) | `data/serie/082027.json` | patch nel `Promise.all` |
| `cefAlb` | `rawData.cef*` + costanti Cefalù | ricalcolo in-place |
| `reg.arr`, `reg.pre`, `reg.covid.arr/pre` | `data/regioni.json` | `syncRegionaliFromJson()` |
| `reg.preArr/prePre/preAlb/preExt` | `preAbs` | `syncPre2012FromAbs()` |
| `top.*` (Top City, 160 valori) | `data/comuni_index.json` + `data/serie/*.json` | `syncTopCity()` |
| Classifica crescita comuni | `data/comuni_index.json` | `buildLeaderboard()` |

**Top City** — la città di ogni regione è scelta con lo stesso criterio della classifica crescita: massima crescita presenze 2014–2024 fra i comuni con almeno 500.000 presenze annue; dove nessuno raggiunge la soglia (Molise) si ripiega sul comune più grande. La sua serie comunale viene scaricata al primo click sulla regione e messa in cache, poi il pannello si ridisegna.

I valori presenti nei letterali JS servono da **fallback** se un fetch fallisce, e vengono sovrascritti appena il JSON arriva.

### Ancora statici (e perché)

| Campo | Motivo |
|-------|--------|
| `preAbs` | Arrivi e presenze regionali 2004/2012 dal file XLS ISTAT: non esiste API né JSON per il pre-2014 con split alb/ext |
| `IT_PRE_BASE`, `IT_EXT_BASE` | Basi 2012 esatte; `italia.json` le arrotonda alle migliaia e il 2012 è un anno chiuso |
| `CEF_PRE_BASE`, `CEF_EXT_BASE` | Idem per Cefalù |
| `rawData.*` anni 2004–2013 di Cefalù | La serie comunale JSON parte dal 2014 |
| `reg.alb`, `reg.ext`, `covid.alb/ext` | Split alberghiero/extra da Eurostat NUTS2, non presente in `regioni.json` |
| `volumeData[regione].post` | Volumi 2024 regionali da Eurostat NUTS2 |

### Nota sui totali del file ISTAT circoscrizioni

In `preAbs` i totali arrivi e presenze sono calcolati come **alberghiero + extra-alberghiero**, non letti dalla colonna "Totale" del file. Nel 2004 quella colonna ha righe azzerate pur avendo le componenti valorizzate (es. Catanzaro, Vibo Valentia), il che sottostimava il totale di 8 regioni. Nel 2012 le due letture coincidono e il totale per regione combacia esattamente con `regioni.json`.

---

## Validazione dei dati

I valori non sono solo internamente coerenti: sono stati verificati contro fonti indipendenti.

### 2012 — riconciliazione perfetta

La somma delle 20 regioni di `preAbs` combacia con i totali nazionali di `data/italia.json`, che è un file distinto e prodotto separatamente:

| Grandezza | Somma 20 regioni | `italia.json` | Scarto |
|-----------|------------------|---------------|--------|
| Arrivi | 103.733.157 | 103.733.000 | +0,00% |
| Presenze | 380.711.483 | 380.711.000 | +0,00% |
| Alberghiero | 255.610.143 | 255.610.000 | +0,00% |
| Extra-alberghiero | 125.101.340 | 125.101.000 | +0,00% |

Gli scarti di poche centinaia di unità sono l'arrotondamento alle migliaia di `italia.json`. Questo conferma anche che `IT_PRE_BASE` e `IT_EXT_BASE` sono cifre ISTAT autentiche.

### 2004 — verifica incrociata su due file ISTAT

I valori 2004 coincidono **all'unità** con la somma delle circoscrizioni del file `3. Dati per circoscrizione turistica 2004-2013.xlsx`, che è una pubblicazione ISTAT separata da quella usata per l'estrazione:

| | Estratto da `DF_BULK_DCSC_TURISAREA` | File 3 (indipendente) |
|---|---|---|
| Alberghiero 2004 | 233.626.738 | 233.626.738 |
| Extra-alberghiero 2004 | 110.754.336 | 110.754.336 |

### Residuo noto nel 2004

Nel 2004 il totale nazionale ISTAT è più alto della somma delle circoscrizioni: ~1,2M di presenze (0,36%) non risultano attribuite ad alcuna circoscrizione. **È un residuo presente nella fonte ISTAT stessa** — nel file 3 la riga "ITALIA" riporta 345.616.227 presenze contro 343.271.993 della somma delle righe — non un errore di estrazione. Nel 2012 il residuo non esiste.

Effetto sulle variazioni pre-2012 mostrate: essendo il 2004 leggermente sottostimato, i cali risultano sovrastimati di circa 0,2 pp (arrivi), 0,4 pp (presenze), 0,2 pp (alberghiero) e 0,8 pp (extra-alberghiero). Esempio: Piemonte extra-alberghiero è mostrato a −31,5% mentre il valore riconciliato al totale nazionale sarebbe circa −30,9%.

---

## Stack tecnico

- **Zero dipendenze runtime** — HTML/CSS/JS vanilla, tutto inline in `index.html`
- **[Plotly.js](https://plotly.com/javascript/)** (CDN) — grafici interattivi e donut chart
- Mappa SVG inline delle regioni italiane
- Dati JSON caricati via `fetch` al primo render

---

## Sviluppi futuri

### Da fare

- **Accordion per la Top City** — le righe della Top City sono le uniche del pannello regionale senza `toggleNominal`: mostrano solo percentuali, non i valori assoluti. La serie comunale è già in cache dopo il primo click (`topSerieCache`), quindi arrivi e notti 2014/2019/2024 sono disponibili senza fetch aggiuntivi. Serve solo aggiungere `onclick="toggleNominal(this)"` e `data-nominal` alle righe dei gruppi pre-COVID, post-COVID e crescita totale.

### Nuovi indicatori

- Durata media del soggiorno (presenze/arrivi) per regione e anno
- Split residenti/non-residenti per regione (turismo internazionale vs domestico)
- Indice di stagionalità regionale (dati mensili ISTAT disponibili)
- Tasso di occupazione alberghiera (Eurostat `tour_occ_occh2`, NUTS2)
- Benchmark europeo: confronto con regioni NUTS2 di Spagna, Francia, Grecia

### Valutato e scartato

- **Gruppo pre-2012 per la Top City** — solo 12 delle 20 Top City esistono come circoscrizione turistica autonoma nei dati ISTAT 2004–2013. Le altre otto (Ricadi, Fiumicino, Baveno, Monopoli, Pula, Marsala, Castagneto Carducci, Courmayeur) sono aggregate in aree più ampie e non separabili, quindi il gruppo resterebbe vuoto per il 40% delle regioni. Non esiste una fonte ISTAT comunale con split alberghiero/extra prima del 2014.
