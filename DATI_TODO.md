# Note per verifica e completamento dati – tourism-dashboard

Data: 2026-07-28  
Autore: Claude (sessione di verifica dati vs ISTAT/Eurostat)

---

## Stato attuale

Tutti i valori hardcoded nella sezione **Sintesi Italia** (pre-2012, post-2012, pre-COVID, post-COVID) sono stati convertiti in calcoli dinamici da `rawData`. Nessun valore stringa fissa rimane in quei blocchi.

---

## Problema aperto: `preExt` regionale = +0.0 per tutte le 20 regioni

### Dove si trova
In `regionalDataFull` (index.html, righe ~702-721), ogni regione ha questo campo nel sotto-oggetto `reg`:

```js
"Abruzzo": { reg: { preArr: +15.2, prePre: +20.3, preExt: +0.0, ... } }
```

`preExt` è la variazione percentuale Extra-Alberghiero **2004 vs 2012** per ogni regione.  
Il valore `+0.0` è un **placeholder**: **non è un dato reale**, è identico per tutte le 20 regioni.

### Perché è +0.0
Nella sessione di verifica abbiamo cercato di ricalcolarlo e scoperto che:

1. **`regioni.json`** (nella cartella `/data/`) ha dati regionali dal 2008 in poi, ma solo `arr` e `pre` totali – **nessuna suddivisione alb/ext**.
2. **`serie/*.json`** (5.324 file, uno per comune) hanno la suddivisione `pre_alb` / `pre_ext`, ma partono dal **2014** – impossibile usarli per il confronto 2004 vs 2012.
3. **`italia.json`** ha la serie storica nazionale alb/ext dal 1956, ma è **solo nazionale** – niente per regione.
4. L'API ISTAT `esploradati.istat.it` (dataset `122_54_DF_DCSC_TUR_7`) ha la suddivisione HOTELLIKE/OTHER ma solo per **REF_AREA=IT** (Italia totale), non per regioni.
5. L'API Eurostat `tour_occ_nin2` (pernottamenti NUTS2) **non** fornisce la suddivisione alberghiero/extra-alberghiero – aggrega tutto in NACE I551-I553.

### Origine dei valori preArr / prePre già presenti
I valori `preArr` e `prePre` (variazione 2004 vs 2012 per arrivi e presenze totali) **non corrispondono** a nessun anno di `regioni.json` confrontato con 2012. Esempio Abruzzo: il JSON dà +3.0% (2008 vs 2012), ma il dato hardcoded è +15.2%. Questo suggerisce che vennero calcolati da un **download ISTAT "serie storiche" separato**, probabilmente da I.Stat (dati.istat.it) con serie pre-2012 per regione, che **non è più nel repository**.

### Come recuperare il dato
L'approccio corretto è quello che aveva usato l'utente in origine: **scaricare le serie storiche ISTAT a livello comunale con split alb/ext** e aggregare per regione. Fonti da usare:

- **I.Stat / esploradati.istat.it** → cerca dataset "Movimento clienti negli esercizi ricettivi" con breakout comunale o provinciale che includa anni pre-2012 e la suddivisione alberghiero/extra-alberghiero.
- Il dataset cercato è probabilmente accessibile via il portale ISTAT con download CSV/Excel, non tramite l'API SDMX (che per le regioni sembra limitata alla serie dal 2014 o non fornire il breakout tipologia).
- Una volta scaricato: sommare `pre_ext` dei comuni della stessa regione per gli anni 2004 e 2012, poi calcolare `(val2004 / val2012 - 1) * 100`, arrotondare a 1 decimale.

### Fix temporaneo da applicare intanto
Finché il dato non c'è, **la riga Extra-Alb pre-2012 nelle schede regionali mostra "+0.0%" per tutte le regioni**, che è fuorviante. Opzioni:

**A) Nascondere la riga** quando `preExt === 0` (o meglio `preExt === null` dopo averlo impostato):
```js
// In regionalDataFull cambiare preExt: +0.0 in preExt: null
// In showRegionalReport, riga 882 di index.html:
${data.reg.preExt === null ? '' : `<div class="data-row" ...><span>Extra-Alb</span><span class="value">${data.reg.preExt}%</span></div>`}
```

**B) Lasciare com'è** e completare il dato non appena scaricato il file ISTAT.

---

## Altri dati verificati e corretti nella sessione

### volumeData (donut charts)
Corretti i valori `post` (anno 2024, in Milioni) per le seguenti regioni – erano sbagliati rispetto a Eurostat `tour_occ_nin2`:
- **Italia**: era [269, 172], corretto in [284, 182]
- **Lombardia**: era [24, 14], corretto in [29, 16]
- **Molise**: era [1, 1], corretto in [0.3, 0.2]
- (e altre minori)

### regionalDataFull – alb/ext regionali post-2014
Corretti `reg.alb`, `reg.ext`, `reg.covid.alb`, `reg.covid.ext` per tutte le 20 regioni verso i valori Eurostat NUTS2. Errori più gravi trovati:
- **Molise** `covid.alb`: era -30.2%, corretto in -5.6%
- **Friuli** `covid.alb`: era +15.4%, corretto in +22.6%
- **Calabria** `alb`/`ext`: erano 110.9/128.1, corretti in 101.6/118.1
- **Lazio** `alb`/`ext` e `covid.alb`/`covid.ext`: varie correzioni

### Sezione Italia pre-2012 / post-2012
Convertiti da stringhe hardcoded a calcoli dinamici da `rawData`:
- **Pre-2012**: `+17.1%` (Arrivi), `+9.2%` (Presenze), `+10.8%` (Extra-Alb) → ora `${sgn(100-rawData.itArr[0])}%` ecc.
- **Post-2012**: `+34.6%` (Arrivi), `+22.4%` (Presenze), `+45.7%` (Extra-Alb) → ora `${sgn(rawData.itArr[20]-100)}%` ecc.
- **Bug fix** Alb pre-2012: era `${sgn(itAlb[0]-100)}%` (dava -8.4%), corretto in `${sgn(100-itAlb[0])}%` (+8.4%)

### Popup INFO
Aggiornati 6 testi per riflettere la soglia >=500.000 presenze per la selezione Top City (usata da `buildLeaderboard()`).

---

## Fonte dati
I dati post-2012 e post-COVID usano **Eurostat `tour_occ_nin2`** (pernottamenti NUTS2) e **`tour_occ_arn2`** (arrivi NUTS2), identici ai dati ISTAT che vengono trasmessi a Eurostat. La fonte rimane citata come "ISTAT" nell'interfaccia – corretto.

---

## File di riferimento
- `index.html` – tutto il codice e i dati sono inline
- `data/regioni.json` – serie regionale 2008-2024, solo arr/pre totali
- `data/serie/*.json` – 5.324 comuni, 2014-2024, con split alb/ext
- `data/italia.json` – serie nazionale 1956-2024, con split alb/ext
