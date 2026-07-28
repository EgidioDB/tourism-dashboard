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

## Indicatori hardcoded e loro origine

Alcuni dati storici (2004–2013) sono necessariamente hardcoded perché le API ISTAT non restituiscono la serie regionale con split alb/ext per quel periodo.

| Campo | Significato | Fonte |
|-------|-------------|-------|
| `preArr` | Variazione arrivi 2004 vs 2012 per regione | ISTAT circoscrizioni |
| `prePre` | Variazione presenze 2004 vs 2012 per regione | ISTAT circoscrizioni |
| `preExt` | Variazione extra-alb 2004 vs 2012 per regione | ISTAT `DF_BULK_DCSC_TURISAREA` |
| `preAbs` | Presenze assolute 2004 e 2012 [alb, ext] per regione (Milioni) | ISTAT `DF_BULK_DCSC_TURISAREA` |
| `volumeData.pre` | Presenze 2012 [alb, ext] per regione (Milioni) | ISTAT (allineato a costanti base) |
| `volumeData.post` | Presenze 2024 [alb, ext] per regione (Milioni) | Eurostat NUTS2 |
| `rawData.cef*` | Indici Cefalù 2004–2024 (base 2012=100) | ISTAT comunale + serie storica |
| `rawData.it*` | Indici Italia 2004–2024 (base 2012=100) | `data/italia.json` |

---

## Stack tecnico

- **Zero dipendenze runtime** — HTML/CSS/JS vanilla, tutto inline in `index.html`
- **[Plotly.js](https://plotly.com/javascript/)** (CDN) — grafici interattivi e donut chart
- Mappa SVG inline delle regioni italiane
- Dati JSON caricati via `fetch` al primo render

---

## Sviluppi futuri

- Durata media del soggiorno (presenze/arrivi) per regione e anno
- Split residenti/non-residenti per regione (turismo internazionale vs domestico)
- Indice di stagionalità regionale (dati mensili ISTAT disponibili)
- Tasso di occupazione alberghiera (Eurostat `tour_occ_occh2`, NUTS2)
- Benchmark europeo: confronto con regioni NUTS2 di Spagna, Francia, Grecia
