# Tourism Dashboard — Analisi del Turismo Italiano

Dashboard interattiva per l'analisi delle presenze turistiche in Italia, con focus sul Comune di Cefalù e confronto con i benchmark regionali e nazionali. Copre il periodo **2004–2024** con dati ISTAT ed Eurostat.

---

## Come si apre

La dashboard carica i propri dati dai JSON in `data/` via `fetch`, quindi va servita via HTTP: online su GitHub Pages, oppure in locale con un webserver statico. Aprire `index.html` con un doppio click **non** funziona, perché i browser bloccano `fetch` sulle origini `file://`.

```bash
python3 -m http.server 8000
```

Poi apri `http://localhost:8000`. Nessuna dipendenza da installare.

---

## Funzionalità

### Mappa interattiva d'Italia
- Click su una regione per aprire il pannello di analisi regionale
- Zoom automatico sulla regione selezionata
- Donut chart che si aggiorna con i volumi della regione (alberghiero vs extra-alberghiero, pre/post 2012)

### Pannello regionale
Ogni regione mostra quattro gruppi, tutti con valori assoluti in accordion (click su ogni riga):

| Gruppo | Confronto | Metriche |
|--------|-----------|----------|
| Pre-2012 | 2004 → 2012 | Arrivi, Presenze, Alb, Extra-Alb |
| Post-2012 | 2012 → 2024 | Arrivi, Presenze, Alb, Extra-Alb |
| Pre-COVID | 2012 → 2019 | Arrivi, Presenze, Alb, Extra-Alb |
| Post-COVID | 2019 → 2024 | Arrivi, Presenze, Alb, Extra-Alb |

**Tutti i gruppi si leggono nello stesso verso**: positivo (verde) = cresciuto nel periodo, negativo (rosso) = calato. Gli accordion mostrano i conteggi reali — arrivi e notti — non gli indici. Segue il pannello della **Top City** della regione, anch'esso con accordion, e il gap rispetto alla media nazionale.

I pannelli Italia e Cefalù usano gli stessi quattro gruppi e la stessa base 2012, quindi le tre colonne sono direttamente confrontabili: si può dire che *Cefalù è cresciuta del 46,4% mentre l'Abruzzo è calato dell'1,1%* leggendo due numeri affiancati.

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
├── index.html                          # Applicazione: solo codice, nessun dato
│
├── data/
│   ├── italia.json                     # Serie storica nazionale 1956–2024 (66 anni; la
│   │                                   # dashboard ne usa 2004–2024, il resto non è esposto)
│   │                                   # Arrivi e presenze: totale, alb, ext, residenti/non-res
│   ├── regioni.json                    # Serie regionale 2008–2024 (20 regioni)
│   │                                   # Arrivi e presenze totali per anno
│   ├── pre2012.json                    # Volumi regionali 2004/2012 + serie Cefalù 2004–2013
│   │                                   # Copre gli anni che le serie comunali non hanno
│   ├── eurostat_regioni.json           # Split alberghiero/extra NUTS2: 2012, 2014, 2019, 2024
│   │                                   # Rigenerabile: python3 scripts/fetch_eurostat.py
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
│   ├── bilancio.json                   # Bilancio Cefalù 2005–2024: imposta di soggiorno,
│   │                                   # spesa turismo, entrate tributarie
│   ├── bilancio_cefalu_armonizzato.json
│   ├── bilancio_cefalu_consuntivo.json
│   ├── bilancio_cefalu_rendiconti_pdf.json
│   ├── irpef_cefalu.json               # Dati IRPEF Cefalù
│   └── PIL/                            # Dati PIL per area
│
├── scripts/
│   └── fetch_eurostat.py               # Riscarica eurostat_regioni.json dall'API Eurostat
│
└── DCSC_Occupancy_in_collective_accommodation/
    ├── 1. Serie storiche.xlsx          # Serie storica nazionale alb/ext 1954–2013
    ├── 2. Dati comunali 2014-2024.xlsx # Presenze comunali per tipo struttura
    ├── 3. Dati per circoscrizione turistica 2004-2013.xlsx
    │                                   # Presenze per circoscrizione turistica (pre-2014)
    │                                   # Fonte di pre2012.json
    └── 4. Dati per provenienza 2024.xlsx # Provenienza turisti per area 2024
```

---

## Fonti dati

| Dato | Fonte | Periodo | File |
|------|-------|---------|------|
| Presenze/Arrivi nazionali | ISTAT | 1956–2024 | `italia.json` |
| Presenze/Arrivi regionali | ISTAT | 2008–2024 | `regioni.json` — solo totali, no split alb/ext |
| Presenze/Arrivi comunali | ISTAT | 2014–2024 | `serie/*.json` — 5.324 comuni, split completo |
| Volumi regionali 2004/2012 e Cefalù pre-2014 | ISTAT `DF_BULK_DCSC_TURISAREA` | 2004–2013 | `pre2012.json` — per circoscrizione turistica |
| Split alberghiero/extra regionale | Eurostat `tour_occ_nin2` | 2012, 2014, 2019, 2024 | `eurostat_regioni.json` — NUTS2 |
| Imposta di soggiorno e spesa turismo | Consuntivi comunali, BDAP / RGS | 2005–2024 | `bilancio.json` |

L'API Eurostat espone header CORS aperti, quindi sarebbe interrogabile direttamente dal browser. Il file resta comunque versionato nel repo: così la dashboard non dipende dalla disponibilità di un servizio esterno a ogni caricamento, e i dati mostrati sono riproducibili nel tempo.

### Perché il 2012 è l'anno zero

Il 2012 non è un punto di comodo: segna l'arrivo in Italia delle piattaforme di affitto breve. L'effetto non si vede subito nei volumi — i salti anno su anno arrivano dal 2015, come da curva di adozione — ma è netto nella **pendenza** della quota di extra-alberghiero sul totale delle presenze:

| periodo | quota extra | pendenza |
|---------|-------------|----------|
| 2004 → 2012 | 32,3% → 32,9% | +0,107 punti/anno |
| 2012 → 2019 | 32,9% → 35,7% | +0,460 punti/anno |
| 2012 → 2024 | 32,9% → 39,1% | +0,614 punti/anno |

**Un'accelerazione di 4,3 volte.** Tutti i pannelli usano il 2012 come base, così il confronto prima/dopo è la struttura portante della dashboard.

### Costanti di base (2012)
```
Presenze totali Italia 2012:        380.711.483
Presenze extra-alberghiero 2012:    125.101.340
Presenze alberghiero 2012:          255.610.143
Presenze totali Cefalù 2012:            634.776
Arrivi Cefalù 2012:                     132.746
```

---

## Come circolano i dati

**In `index.html` non c'è nessun dato.** Le strutture partono vuote e ogni valore arriva dai JSON in `data/`, o viene derivato da quelli a runtime. Aggiornare un JSON aggiorna tutta la dashboard, e non esistono copie parallele che possano disallinearsi.

### Chi riempie cosa

| Grandezza | Fonte | Funzione |
|-----------|-------|----------|
| `rawData.it*` (2004–2024) | `data/italia.json` | `syncItaliaFromJson()` |
| `rawData.cef*` (2004–2013) | `data/pre2012.json` | `syncPre2012FromJson()` |
| `rawData.cef*` (2014–2024) | `data/serie/082027.json` | patch nel `Promise.all` |
| `itAlb`, `itBenchmark`, `volumeData.Italia` | `rawData.it*` + basi 2012 | `syncItaliaDerived()` |
| `cefAlb` | `rawData.cef*` + basi Cefalù | ricalcolo in-place |
| `preAbs`, `volumeData[reg].pre` | `data/pre2012.json` | `syncPre2012FromJson()` |
| `reg.preArr/prePre/preAlb/preExt` | `preAbs` | `syncPre2012FromAbs()` |
| `reg.arr`, `reg.pre`, `reg.covid.arr/pre` | `data/regioni.json` | `syncRegionaliFromJson()` |
| `reg.alb`, `reg.ext`, `reg.covid.alb/ext`, `regVolumi`, `volumeData[reg].post` | `data/eurostat_regioni.json` | `syncEurostatRegioni()` |
| `top.*` (Top City), volumi inclusi | `data/comuni_index.json` + `data/serie/*.json` | `syncTopCity()` |
| `SOGGIORNO_DATA`, `SPESA_SOG_DATA` | `data/bilancio.json` | `syncBilancioFromJson()` |
| Classifica crescita comuni | `data/comuni_index.json` | `buildLeaderboard()` |

**Top City** — la città di ogni regione è scelta con lo stesso criterio della classifica crescita: massima crescita presenze 2014–2024 fra i comuni con almeno 500.000 presenze annue; dove nessuno raggiunge la soglia (Molise) si ripiega sul comune più grande. La sua serie comunale viene scaricata al primo click sulla regione e messa in cache, poi il pannello si ridisegna.

### Convenzioni di lettura

Sono la fonte di errore più frequente in questo progetto, perché un segno sbagliato non rompe nulla: mostra solo il contrario del vero.

- **Tutti i gruppi periodo esprimono la variazione nel periodo**, nello stesso verso. Positivo = cresciuto, e il colore segue il segno tramite `clr()`. Vale anche per il Pre-2012, che fino a oggi mostrava invece il livello del 2004 rispetto alla base: l'extra-alberghiero di Cefalù appariva a `+112,5%` in verde mentre in quegli anni si era dimezzato.
- **La base è il 2012 in tutti e tre i pannelli.** Italia, Cefalù e Regione sono quindi affiancabili. Il pannello regionale usava il 2014 fino a oggi, il che rendeva il confronto con Cefalù privo di significato.
- **`showYearlyReport` fa eccezione di proposito**: mostra un singolo anno rispetto alla base, che è una posizione e non una variazione. Lì l'indice meno 100 è la lettura giusta.
- **`indice − 100` è esatto**, non un'approssimazione, perché l'indice è già un rapporto al 2012. È `100 − indice` a essere una scorciatoia sbagliata per il verso opposto: per il pre-2012 si usa `pre12()`, cioè `100/indice − 1`.
- **Il gap Top City confronta due indici base 2014**, non 2012: `itBenchmark` è ricalcolato apposta su quella base.

### Conseguenze sul rendering

Siccome nulla è disponibile prima dei fetch, il disegno è governato da un flag `dataReady`:

- `showTotalReport()` e `showYearlyReport()` non disegnano finché `rawData` non è pieno; chi carica i dati le richiama
- il grafico storico nasce con tracce vuote e viene riempito con `Plotly.restyle`, che preserva layout e interazioni
- il pannello regionale mostra *Caricamento dati…*, con un caricamento separato per la Top City che ha un fetch proprio
- il grafico Chart.js mobile è costruito da `buildMobileChart()` a dati pronti

### Le uniche costanti rimaste

| Costante | Valore | Perché non è nei JSON |
|----------|--------|------------------------|
| `IT_PRE_BASE`, `IT_EXT_BASE` | 380.711.483 · 125.101.340 | Basi 2012 nazionali esatte; `italia.json` arrotonda alle migliaia |
| `CEF_PRE_BASE`, `CEF_EXT_BASE` | 634.776 · 80.447 | Idem per Cefalù |

Il 2012 è un anno chiuso e questi sono i valori ISTAT pieni. Entrambe le coppie sono verificate contro le rispettive fonti: coincidono con `italia.json` e con il 2012 di `pre2012.json`.

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

- **Nessun build step** — HTML/CSS/JS vanilla, nessun bundler né package manager
- **[Plotly.js](https://plotly.com/javascript/)** e **[Chart.js](https://www.chartjs.org/)** (CDN) — grafici desktop e mobile
- Mappa SVG inline delle regioni italiane
- Dati caricati da `data/` via `fetch`: serve un webserver, vedi *Come si apre*

---

## Sviluppi futuri

### Nuovi indicatori

- **Vista storica lunga** — `italia.json` contiene la serie nazionale dal 1956, 45 anni che la dashboard non espone. Basterebbe un grafico a parte per mostrare il turismo italiano dal dopoguerra, senza scaricare nulla di nuovo. Attenzione ai tre anni mancanti nel file: 1986, 1996 e 1999.

- Durata media del soggiorno (presenze/arrivi) per regione e anno
- Split residenti/non-residenti per regione (turismo internazionale vs domestico)
- Indice di stagionalità regionale (dati mensili ISTAT disponibili)
- Tasso di occupazione alberghiera (Eurostat `tour_occ_occh2`, NUTS2)
- Benchmark europeo: confronto con regioni NUTS2 di Spagna, Francia, Grecia

### Valutato e scartato

- **Gruppo pre-2012 per la Top City** — ISTAT pubblica per *circoscrizione turistica* fino al 2013 e per *comune* dal 2014, come dichiara l'indice del suo stesso pacchetto. Solo 12 delle 20 Top City coincidono con una circoscrizione; le altre otto sono dentro aggregati troppo ampi per fare da proxy: Fiumicino finirebbe sommata a 119 altri comuni, Pula a 68, Monopoli a 43. Cercare il dato presso gli osservatori regionali significherebbe mettere otto fonti diverse accanto a dodici ISTAT nello stesso gruppo, rendendo le percentuali non confrontabili fra loro — che è proprio il senso di quel confronto.
