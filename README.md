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
- Donut chart che si aggiorna con i volumi della regione (alberghiero vs extra-alberghiero, 2012 e 2024)

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

### Settant'anni di turismo italiano
Serie nazionale completa **1956–2024** in valore assoluto, alberghiero ed extra-alberghiero impilati. È l'unico grafico non indicizzato: su settant'anni interessa la scala della trasformazione, non il rapporto a un anno base.

Tre linee tratteggiate segnano i **cambi di definizione ISTAT** dell'extra-alberghiero: 1986 (le residenze turistiche alberghiere passano all'alberghiero), 1996 (entrano gli agriturismi), 1999 (entrano i bed and breakfast). Sono la ragione per cui **la quota di extra-alberghiero non è confrontabile a cavallo di quegli anni**: il 39,7% del 1958 e il 39,1% del 2024 sono numeri quasi identici che misurano cose diverse.

Il 1956 e il 1957 hanno il solo alberghiero, quindi l'indicatore di crescita parte dal 1958: 110 milioni di notti contro i 466 del 2024, **4,2 volte**. Confrontare il totale di oggi con i soli hotel del 1956 darebbe 9 volte.

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

### Provincia di Palermo — chi arriva e dove dorme
Due pannelli in una sezione **richiudibile, chiusa di default**: sono gli unici dati su base **provinciale** dentro una pagina che parla del comune di Cefalù, e sono una fotografia del 2024, non una serie storica. La sezione lo dichiara per non farli leggere come il resto.

- **Da dove arrivano** — i primi 12 mercati esteri o le prime 12 regioni italiane, con quota sul totale
- **Dove dormono** — le 4,2 milioni di notti provinciali per tipologia ricettiva, con la permanenza media di ciascuna

### Sezione Confronta
- Confronto diretto tra Cefalù e qualsiasi altro comune italiano (5.268 disponibili)
- Radar del profilo destinazione, posizione nel ranking nazionale, heatmap di stagionalità
- **Indice di pressione turistica** (notti per abitante) con anno selezionabile dal 2014 al 2024: presenze e popolazione dello stesso anno
- Capacità ricettiva 2010–2024, esercizi e posti letto
- Dataset scaricabile in CSV

---

## Struttura del progetto

```
tourism-dashboard/
│
├── index.html                          # Applicazione: solo codice, nessun dato
│
├── data/
│   ├── italia.json                     # Serie storica nazionale 1956–2024 (69 anni, nessun
│   │                                   # buco). Arrivi e presenze: totale, alb, ext, res/non-res
│   │                                   # Campo _discontinuita: i cambi di definizione ISTAT
│   │                                   # Rigenerabile: python3 scripts/build_italia.py
│   ├── regioni.json                    # Serie regionale 2008–2024 (20 regioni)
│   │                                   # Arrivi e presenze totali per anno
│   ├── pre2012.json                    # Volumi regionali 2004/2012 + serie Cefalù 2004–2013
│   │                                   # Copre gli anni che le serie comunali non hanno
│   ├── eurostat_regioni.json           # Split alberghiero/extra NUTS2: 2012, 2014, 2019, 2024
│   │                                   # Rigenerabile: python3 scripts/fetch_eurostat.py
│   ├── comuni_index.json               # Indice dei 5.268 comuni con dati
│   │                                   # Metadati: cod_istat, nome, provincia, regione
│   │                                   # Statistiche: max_arr, max_pre, growth_pre
│   ├── serie_ricucite.json             # 56 comuni sardi con due codici ISTAT, prima e dopo
│   │                                   # la riforma delle province: la serie sta sul nuovo
│   ├── serie/                          # 5.268 file JSON, uno per comune
│   │   └── {cod_istat}.json            # Serie 2014–2024: arr/pre × tot/alb/ext × res/nres
│   ├── peer_group.json                 # Panel bilanciato dei comuni della stessa categoria
│   │                                   # turistica di Cefalù, solo serie complete 2014–2024
│   ├── provenienza.json                # Provincia di Palermo 2024: 48 paesi esteri,
│   │                                   # 21 regioni italiane, 6 tipologie ricettive
│   ├── flag_istat.json                 # Note ISTAT per comune-anno: (a) rottura di serie,
│   │                                   # (d) 2015 non trasmesso, (e) stimato, (b), (c)
│   │                                   # Rigenerabile: python3 scripts/build_flag_istat.py
│   ├── stagionalita.json               # Dati di stagionalità
│   ├── popolazione.json                # Popolazione al 1° gennaio 2014–2024 per comune:
│   │                                   # ricostruzione intercensuaria ISTAT fino al 2019, POSAS dopo
│   │                                   # Rigenerabile: python3 scripts/build_popolazione.py
│   │                                   # (scarica i file POSAS in data/fonti/, esclusa da git)
│   ├── province.json                   # Anagrafica province
│   ├── ricettiva.json                  # Dati strutture ricettive
│   ├── ricettiva_index.json            # Indice strutture ricettive
│   ├── soggiorno_mensile.json          # Imposta di soggiorno incassata da Cefalù, mese per mese,
│   │                                   # 2020–2026 (SIOPE, cassa). Rigenerabile:
│   │                                   # python3 scripts/build_siope_soggiorno.py
│   ├── soggiorno_comuni.json           # Imposta incassata e presenze per comune, 2020–2025:
│   │                                   # stesso script, stessi file SIOPE
│   ├── bilancio.json                   # Bilancio Cefalù 2005–2024: imposta di soggiorno,
│   │                                   # spesa turismo, entrate tributarie
│   ├── bilancio_cefalu_armonizzato.json
│   ├── bilancio_cefalu_consuntivo.json
│   ├── bilancio_cefalu_rendiconti_pdf.json
│   ├── irpef_cefalu.json               # Dati IRPEF Cefalù
│   └── PIL/                            # Dati PIL per area
│
├── scripts/
│   ├── fetch_eurostat.py               # Riscarica eurostat_regioni.json dall'API Eurostat
│   ├── build_italia.py                 # Rigenera italia.json dal file XLS delle serie storiche
│   ├── build_flag_istat.py             # Rigenera flag_istat.json dal file comunale ISTAT
│   ├── build_popolazione.py            # Rigenera popolazione.json e il reddito pro capite IRPEF
│   ├── build_siope_soggiorno.py        # Rigenera soggiorno_mensile.json e soggiorno_comuni.json
│   ├── ricuci_serie.py                 # Unisce le serie dei comuni passati di provincia
│   └── build_confronti.py              # Rigenera peer_group.json e provenienza.json
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
| Presenze/Arrivi comunali | ISTAT | 2014–2024 | `serie/*.json` — 5.268 comuni, split completo |
| Volumi regionali 2004/2012 e Cefalù pre-2014 | ISTAT `DF_BULK_DCSC_TURISAREA` | 2004–2013 | `pre2012.json` — per circoscrizione turistica |
| Split alberghiero/extra regionale | Eurostat `tour_occ_nin2` | 2012, 2014, 2019, 2024 | `eurostat_regioni.json` — NUTS2 |
| Provenienza e tipologia ricettiva | ISTAT — arrivi e presenze per luogo di residenza dei clienti | 2024 | `provenienza.json` — dettaglio provinciale, non comunale |
| Comuni della stessa categoria turistica | ISTAT — classificazione per categoria turistica prevalente | 2014–2024 | `peer_group.json` — panel bilanciato |
| Imposta di soggiorno e spesa turismo | Consuntivi comunali, BDAP / RGS | 2005–2024 | `bilancio.json` |
| Note sui dati comunali | ISTAT — colonna flag del file comunale | 2014–2024 | `flag_istat.json` |
| Imposta di soggiorno mensile | SIOPE — incassi di cassa, RGS e Banca d'Italia | 2020–2026 | `soggiorno_mensile.json` |
| Imposta di soggiorno per comune | SIOPE — incassi di cassa, con presenze ISTAT | 2020–2025 | `soggiorno_comuni.json` |
| Popolazione residente al 1° gennaio | ISTAT — ricostruzione intercensuaria, poi POSAS | 2014–2024 | `popolazione.json` |

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
| `SOG_MESE` (imposta mese per mese) | `data/soggiorno_mensile.json` | `syncSoggiornoMensile()` |
| `sogComuniData` (imposta per notte, Confronta) | `data/soggiorno_comuni.json` | `renderSogCompare()`, `sogRiga()` |
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

### Aggregare i comuni: quando si può e quando no

Sommando i 5.268 file di `serie/` per regione, i **totali del 2024 tornano esatti al 100,0% in tutte le regioni** rispetto a `regioni.json`, e la somma nazionale fa 466.158.045 notti — cioè il valore di `italia.json`, che è prodotto da una fonte diversa. Il **2014** invece è scoperto, dal 79,4% del Molise al 99,9% dell'Umbria: è da lì che nascono gli indici gonfiati, non dall'aggregazione in sé.

Sullo **split alberghiero/extra** non torna nemmeno il 2024. **1.933 delle 5.014 serie con presenze nel 2024 hanno la ripartizione a `null`**, per segreto statistico: scatta dove le strutture sono poche. Alberghiero + extra copre quindi il 94,66% del totale nazionale, con uno scarto che va dallo 0,0% (Bolzano) al 17,2% (Piemonte).

| | notti 2024 | coperte dallo split | scoperto |
|---|---|---|---|
| Piemonte | 14.395.737 | 11.916.509 | 17,2% |
| Lombardia | 45.130.529 | 38.351.507 | 15,0% |
| Sicilia | 17.348.238 | 15.410.451 | 11,2% |
| Lazio | 51.753.567 | 51.449.144 | 0,6% |
| **Italia** | **466.158.045** | **441.266.245** | **5,34%** |

Non è correggibile con un fattore unico, e i comuni oscurati sono i piccoli, dove l'extra-alberghiero pesa più della media: riscalare al totale ufficiale significherebbe attribuire loro il mix dei grandi. Per lo split regionale resta quindi `eurostat_regioni.json`, che è completo.

### Residuo noto nel 2004

Nel 2004 il totale nazionale ISTAT è più alto della somma delle circoscrizioni: ~1,2M di presenze (0,36%) non risultano attribuite ad alcuna circoscrizione. **È un residuo presente nella fonte ISTAT stessa** — nel file 3 la riga "ITALIA" riporta 345.616.227 presenze contro 343.271.993 della somma delle righe — non un errore di estrazione. Nel 2012 il residuo non esiste.

Effetto sulle variazioni pre-2012 mostrate: essendo il 2004 leggermente sottostimato, i cali risultano sovrastimati di circa 0,2 pp (arrivi), 0,4 pp (presenze), 0,2 pp (alberghiero) e 0,8 pp (extra-alberghiero). Esempio: Piemonte extra-alberghiero è mostrato a −31,5% mentre il valore riconciliato al totale nazionale sarebbe circa −30,9%.

---

## Analisi: l'imposta di soggiorno sfugge?

Una stima del gettito teorico del 2024, fatta per capire se a Cefalù una parte dell'imposta non venga versata. Non è nella dashboard: le ipotesi pesano troppo per un numero da mostrare accanto ai dati.

**Le regole.** Il [regolamento dell'imposta](https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_at/download_lib.php?key=0900f2308055e2ae&nome=344769_CIMUNIC-15pa24c421AM.pdf) (testo modificato con delibera del Consiglio comunale n. 3 del 10 gennaio 2024, depositato sul portale del Dipartimento delle Finanze) stabilisce che l'imposta si paga solo dal 1° aprile al 31 ottobre, per al massimo cinque notti consecutive, e che sono esenti fra gli altri i minori fino a dodici anni. Le strutture versano a bimestri, entro il 15 di giugno, agosto, ottobre e dicembre: sono i picchi del grafico mensile. Le tariffe le fissa ogni anno il Sindaco; quelle del 2024, dalla [determina di gennaio 2024](https://www.madoniepress.it/2024/01/26/tassa-di-soggiorno-lamministrazione-di-cefalu-annuncia-le-nuove-tariffe/), sono 2 € per gli alberghi fino a 3 stelle, 2,50 € per 4 stelle e RTA, 4 € e 5 € per 5 stelle e 5 stelle lusso, 2 € per extra-alberghiero e affitti brevi, 1,50 € per i campeggi. Le tariffe degli anni precedenti non sono state trovate in fonti affidabili, quindi la stima vale solo per il 2024.

**Il calcolo.** Base: 885.128 notti ISTAT fra aprile e ottobre 2024 (il 95,3% dell'anno), l'82,8% in albergo. Tre cose non si conoscono e sono trattate come forbice: la ripartizione delle notti per stelle, la quota di bambini esenti (5–12%) e l'effetto del tetto delle cinque notti, che negli alberghi, con una permanenza media di 4,62 notti, può togliere dal 10 al 30% delle notti.

| scenario | imposta teorica | accertato 2024 / teorico |
|---|---|---|
| prudente | 1,14 milioni | 156% |
| centrale | 1,47 milioni | 121% |
| generoso | 1,85 milioni | 96% |

L'accertato 2024 è 1.783.223 €, cioè 2,01 € per ogni notte di stagione registrata da ISTAT: la tariffa base su tutte le notti, nonostante esenzioni e tetto.

**Cosa se ne ricava.** Nessuna evasione visibile, ma per un motivo che limita il metodo: si paga l'imposta anche su notti che ISTAT non conta. La spiegazione più probabile sono gli affitti brevi: dal febbraio 2024 [Airbnb riscuote e versa l'imposta in tutti i comuni che la applicano](https://news.airbnb.com/airbnb-to-collect-and-remit-tourist-taxes-across-italy/), [Cefalù compresa](https://www.airbnb.com/help/article/3676). La base ISTAT è più stretta di quella reale, quindi non può misurare quanto sfugge; e chi non si registra da nessuna parte resta invisibile a entrambe. Per misurarlo servono dati del Comune — notti dichiarate per struttura sul portale dell'imposta, confrontate con l'elenco delle strutture registrate — ottenibili con un accesso civico.

Un segnale diverso viene da SIOPE: l'imposta riscossa a seguito di verifica e controllo è zero dal 2020 al 2023, compare a ottobre 2024 e arriva a 95.443 € nel 2025. I recuperi sono partiti, quindi imposta non versata ce n'era; quanta ne resti non si sa.

## Stack tecnico

- **Nessun build step** — HTML/CSS/JS vanilla, nessun bundler né package manager
- **[Plotly.js](https://plotly.com/javascript/)** e **[Chart.js](https://www.chartjs.org/)** (CDN) — grafici desktop e mobile
- Mappa SVG inline delle regioni italiane
- Dati caricati da `data/` via `fetch`: serve un webserver, vedi *Come si apre*

---

## Sviluppi futuri

### Nuovi indicatori

- Durata media del soggiorno (presenze/arrivi) per regione e anno
- Split residenti/non-residenti per regione (turismo internazionale vs domestico)
- Indice di stagionalità regionale (dati mensili ISTAT disponibili)
- Tasso di occupazione alberghiera (Eurostat `tour_occ_occh2`, NUTS2)
- Benchmark europeo: confronto con regioni NUTS2 di Spagna, Francia, Grecia

### Fatto, con quello che si è imparato

- **Vista storica lunga** — realizzata: vedi *Settant'anni di turismo italiano*. I **tre anni che sembravano mancanti** — 1986, 1996, 1999 — non mancavano affatto: nel file XLS sono scritti `1986(a)`, `1996(b)`, `1999(c)` e un parser che cerca quattro cifre pulite li scarta. Sono esattamente le tre note metodologiche di ISTAT sui cambi di definizione dell'extra-alberghiero. `italia.json` è passato da 66 a 69 anni senza buchi.

- **Etichette dei donut** — dicevano *pre-2012* e *post-2012*, ma sono due singole annate: il 2012 e il 2024. La prima ciambella sommava le notti dei due anni e chiamava totale il risultato. Ora sono `2012 VS 2024` con la variazione, `Dettaglio 2012` e `Dettaglio 2024`. Un vero pre-2012 non è ricostruibile: le serie comunali partono dal 2014 e per le regioni esistono solo i punti 2004 e 2012.

- **Audit dei calcoli** — ogni numero dei pannelli Italia, Cefalù, delle 20 regioni e delle Top City è stato ricalcolato in modo indipendente dai JSON. Quattro errori trovati e corretti:
  - le ciambelle arrotondavano i volumi a 0,1 milioni *prima* di calcolare la variazione: il Molise risultava fermo allo 0,0% invece di calare del 15,5%;
  - il badge della classifica in Confronta era rovesciato, il primo comune leggeva "Top 100%";
  - il post-COVID regionale e della Top City partiva da indici già arrotondati e sbagliava l'ultima cifra in un valore su tre;
  - il KPI dell'imposta di soggiorno diceva 2013–2022 su un calcolo 2013–2024.

  I gap con la media nazionale sono differenze fra indici, quindi ora sono in **punti** e non in %, con segno e colore presi dal valore.

- **Le note ISTAT sui comuni** — il file comunale ha una colonna *flag* che le serie JSON perdevano. Ora è in `flag_istat.json` e la dashboard la usa:
  - **(d)** il **2015 di Cefalù non è un dato reale**: ISTAT non l'ha ricevuto e ripete il 2014 in tutti i campi (come per altri 54 comuni, quasi tutti siciliani). Ogni grafico di Cefalù lo segna con una fascia e un ⚠, e il dettaglio del 2015 lo dice.
  - **(a)** una **rottura di serie** separa un anno dal precedente. Fiumicino, Marsala e Pescara ne hanno una nel 2023–2024 e occupano posizioni alte in classifica, Marsala è persino la Top City della Sicilia, con le notti triplicate in due anni. Non sono esclusi: sono segnati con ⚠ nella classifica, nel pannello Top City e nei box di Confronta.

- **Popolazione** — il 2014–2018 era una retta estrapolata all'indietro dal 2019 per 7.867 comuni su 7.987; ora è la ricostruzione intercensuaria ISTAT, che era già nel repo in `data/PIL/`. Il 2020–2024 veniva da un rilascio POSAS superato: ISTAT l'ha ripubblicato il 18 dicembre 2025, e per Cefalù i valori vecchi erano circa il 3% più alti (14.314 abitanti nel 2024 invece di 13.861). Il confronto con la scheda ISTAT SITUAS usata da [DoveVannoINostriSoldi](https://www.dovevannoinostrisoldi.com/enti/c_c421) ha fatto emergere la differenza. Ora la serie si raccorda senza scalino, e con lei il reddito pro capite IRPEF: la crescita 2014–2024 passa da +32% a +36%, la pressione turistica 2024 da 64,9 a 67,0 notti per abitante.

- **Popup Reddito & Turismo riscritto sui dati** — diceva che reddito e presenze crescevano in parallelo fino al 2019 (+27% le presenze, +8% il reddito) e crollavano insieme nel 2020 (−62% contro −4%). Attribuiva l'accelerazione recente agli affitti brevi, che però con la cedolare secca restano fuori dal reddito imponibile IRPEF per definizione MEF. Non diceva che il reddito è nominale: +36% dal 2014, circa +11% al netto dell'inflazione.

- **Audit dei popup** — ricontrollati tutti gli 81 testi informativi contro i dati e il codice. Una ventina erano rimasti indietro o sbagliati: la mappa descriveva ancora tre gruppi a base 2014, il pre-2012 di Cefalù spiegava il segno al contrario, due popup regionali davano come fonte i comuni aggregati, la spesa turistica descriveva al contrario la trasparenza delle barre, la capacità ricettiva una linea verde che non esiste, l'imposta di soggiorno un 2022 "sopra il picco pre-COVID" che era sotto. Ogni grafico con il 2015 segnato ora lo spiega, e le classifiche spiegano il ⚠.

- **Imposta di soggiorno mese per mese** — dai file SIOPE, gli incassi di cassa di ogni ente pubblico registrati dal tesoriere. L'idea viene dal progetto [DoveVannoINostriSoldi](https://www.dovevannoinostrisoldi.com/enti/c_c421), che usa gli stessi file. Il grafico mette accanto gli incassi e le presenze dello stesso mese, e mostra che non coincidono: le notti crescono da marzo e toccano il massimo in agosto, l'imposta arriva a scatti a giugno, agosto e ottobre, secondo i versamenti delle strutture. Sugli anni chiusi la cassa torna con gli accertamenti di bilancio (2023 al centesimo, 2024 +0,2%), e aggiunge il 2025 che il bilancio non ha ancora: 1,98 milioni. La serie parte dal 2020: prima l'imposta finiva nella voce generica «Altre imposte n.a.c.» e non si può separare. Il 2026 è parziale: fino a settembre, con 2,66 milioni di incassi del Comune ancora da attribuire a una voce.

- **Imposta di soggiorno per notte, fra comuni** — gli stessi file SIOPE contengono tutti i comuni: 1.532 incassano l'imposta col suo codice. In Confronta ogni comune ha l'incasso diviso le presenze ISTAT dello stesso anno, dal 2020 al 2024, accanto alla mediana dei comuni con almeno 500.000 notti. Nel 2024 Cefalù incassa 1,92 € per notte, 69ª su 161; Taormina 4,11 €, sesta; la mediana è 1,63 €. Tre cose da sapere: le tariffe le fissa ogni Comune, quindi il valore dice quanto rende una notte e non quanto sia efficiente la riscossione; chi registra l'imposta nella voce generica, come Roma, risulta senza incassi e non si può distinguere da chi non la applica; nel 2023 SIOPE non ha righe per quasi tutta la Sardegna, e quell'anno per loro manca invece di valere zero.

- **Serie sarde ricucite** — con la riforma delle province del 2016 i comuni sardi hanno cambiato codice ISTAT, e le serie li trattavano come due comuni: Olbia era `104017` fino al 2016 e `090047` dopo. Senza il 2014 e il 2024 sullo stesso codice non c'era una crescita, quindi 56 comuni restavano fuori da classifica, Top City e comuni simili, fra cui 9 destinazioni oltre le 500.000 notti. `ricuci_serie.py` li unisce sul codice nuovo: 2.304 valori controllati contro il file ISTAT, nessuna differenza. Il passaggio 2016→2017 non mostra salti, +5,1% nel complesso, in linea coi comuni sardi rimasti sullo stesso codice, e ISTAT marca 51 dei nuovi codici come «modifica amministrativa». Effetti: la Top City della Sardegna diventa San Teodoro (+84,2%) al posto di Pula (+68,9%), con una discontinuità ISTAT nel 2024 che il pannello segnala; Cefalù scende dal 23° al 25° posto della classifica crescita; il gruppo dei comuni simili passa da 212 a 220. Restano separati, di proposito, le fusioni (Montalcino, Cassano Spinola: territori diversi) e i cambi di regione (Sappada, Montecopiolo: con la regione cambia chi rileva i dati, e Sappada al passaggio perde il 39% delle notti).

### Valutato e scartato

- **Treemap per la ripartizione ricettiva** — provato e rimosso. Con sei voci di cui due sotto il 3%, le tessere piccole restano senza etichetta comunque le si giri, e le tre categorie extra-alberghiere condividono la stessa famiglia di colore. Una legenda esterna non risolve: se il grafico ha bisogno di una legenda per dire cose che le barre dicono da sole, sono le barre la forma giusta.

- **Gruppo pre-2012 per la Top City** — ISTAT pubblica per *circoscrizione turistica* fino al 2013 e per *comune* dal 2014, come dichiara l'indice del suo stesso pacchetto. Solo 12 delle 20 Top City coincidono con una circoscrizione; le altre otto sono dentro aggregati troppo ampi per fare da proxy: Fiumicino finirebbe sommata a 119 altri comuni, San Teodoro a 20, Monopoli a 43. Cercare il dato presso gli osservatori regionali significherebbe mettere otto fonti diverse accanto a dodici ISTAT nello stesso gruppo, rendendo le percentuali non confrontabili fra loro — che è proprio il senso di quel confronto.
