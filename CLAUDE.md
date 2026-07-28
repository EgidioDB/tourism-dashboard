# Contesto per Claude

Dashboard sul turismo italiano con focus su Cefalù. File unico `index.html`, nessun build step.
Il `README.md` documenta il progetto per chi lo usa; questo file serve a chi ci lavora dentro.

## Eseguire e verificare

La dashboard **non funziona col doppio click**: carica i dati via `fetch` e i browser lo bloccano su `file://`.
Serve un webserver.

```bash
python3 -m http.server 8000
```

Verificare sempre a dashboard servita, non solo con `node --check`. La sintassi valida non dice nulla
sul comportamento: il 29 luglio un'eccezione a runtime ha azzerato metà pagina passando il check.

Controllo di sintassi sui blocchi inline, utile ma non sufficiente:

```bash
python3 - <<'EOF'
import re, subprocess, tempfile, os
html = open('index.html', encoding='utf-8').read()
for i, b in enumerate(re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S)):
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(b); p = f.name
    r = subprocess.run(['node', '--check', p], capture_output=True, text=True)
    if r.returncode: print(f"blocco {i}:\n{r.stderr[:800]}")
    os.unlink(p)
print("fatto")
EOF
```

## Principio architetturale

**In `index.html` non c'è nessun dato.** Le strutture partono vuote e vengono riempite dai JSON in `data/`
dentro il `Promise.all`. Non esistono valori di fallback nel codice: se un fetch fallisce il pannello mostra
*Caricamento dati…* invece di numeri stantii.

Conseguenza pratica: **niente si può disegnare al caricamento sincrono.** Esiste il flag `dataReady`, e le
funzioni che leggono `rawData` devono uscire subito se è falso, per poi essere richiamate da chi carica i dati.
Tre funzioni hanno questa guardia: `showTotalReport`, `showYearlyReport`, `showTotalRegionalReport`.

Se aggiungi una funzione che legge `rawData`, `preAbs`, `regVolumi` o `regionalDataFull`, **deve avere la
guardia e deve essere richiamata dopo i fetch.** Dimenticarlo è già costato una regressione: `showTotalRegionalReport`
veniva invocata a livello modulo, lanciava un `TypeError` su `rawData.itArr[0]` e questo **interrompeva
l'esecuzione dell'intero blocco `<script>`**. Tutto ciò che era dichiarato più sotto finiva in TDZ, quindi i nove
grafici inferiori restavano vuoti, il click sul grafico non rispondeva e l'auto-scale non si agganciava. Un solo
errore, quattro sintomi apparentemente scollegati.

## Convenzioni di lettura

Sono la fonte di errore più insidiosa del progetto: **un segno sbagliato non rompe niente, mostra solo il
contrario del vero.** Nessun test lo intercetta.

- **Base 2012 in tutti e tre i pannelli** (Italia, Cefalù, Regione), così sono affiancabili. Non è una scelta
  di comodo: il 2012 è l'arrivo delle piattaforme di affitto breve, e la quota di extra-alberghiero passa da
  +0,107 a +0,460 punti l'anno, un'accelerazione di 4,3 volte.
- **Tutti i gruppi periodo mostrano la variazione nel periodo**, stesso verso. Positivo = cresciuto, colore
  dal segno tramite `clr()`.
- **`indice − 100` è esatto**, non approssimato: l'indice è già un rapporto al 2012. È `100 − indice` a essere
  una scorciatoia sbagliata per il verso opposto. Per il pre-2012 usa `pre12()`, cioè `100/indice − 1`.
- **`showYearlyReport` è l'eccezione voluta**: mostra un anno rispetto alla base, che è una posizione e non una
  variazione. Lì `indice − 100` è la lettura giusta.
- **`itBenchmark` è base 2014, non 2012**, perché serve solo al gap con la Top City che è indicizzata al 2014.
  Non "correggerlo" a `rawData.it*[20]`: è già successo e falsava il gap.

## Trappole note

- **Aggregare i comuni non ricostruisce il dato regionale.** Sommando `serie/*.json` per regione la copertura
  2014 va dal 79% (Molise) al 100%, quindi gli indici risultano gonfiati fino a 28 punti. Per le regioni usa
  `regioni.json` ed `eurostat_regioni.json`, mai la somma dei comuni.
- **Nel file ISTAT circoscrizioni il totale 2004 è inaffidabile.** Alcune righe hanno la colonna Totale a zero
  con le componenti valorizzate (Catanzaro, Vibo Valentia). In `pre2012.json` i totali sono la somma di
  alberghiero + extra, non la colonna Totale. Nel 2012 le due letture coincidono.
- **Lazio e Marche hanno due valori 2012 diversi** fra le Circoscrizioni Turistiche e le serie regionali,
  0,8% e 3,4%. Sono due rilevazioni ISTAT distinte: ogni gruppo resta coerente al proprio interno e il popup
  del pre-2012 regionale lo spiega. Non tentare di "riconciliarle".
- **`DATA_PATH` e `comuniIndex` sono privati** all'IIFE dell'EXPLORER nel secondo blocco `<script>`. Il primo
  blocco ha le sue copie, `TOP_DATA_PATH` e `topComuniIndex`.
- **Le chiavi dei popup si sbagliano facilmente.** Due gruppi post-COVID aprivano i testi del post-2012.
  Verifica sempre gruppo per gruppo, non solo che la chiave esista.

## Fonti dei dati

| Cosa | Dove | Note |
|------|------|------|
| Serie nazionale 1956–2024 | `data/italia.json` | valori in migliaia |
| Serie regionali 2008–2024 | `data/regioni.json` | solo arrivi e presenze totali |
| Serie comunali 2014–2024 | `data/serie/*.json` | 5.324 comuni, split completo |
| Pre-2014 regionale e Cefalù | `data/pre2012.json` | da XLS ISTAT circoscrizioni |
| Split alb/ext regionale | `data/eurostat_regioni.json` | `python3 scripts/fetch_eurostat.py` |
| Bilancio Cefalù 2005–2024 | `data/bilancio.json` | soggiorno, spesa turismo, entrate |

Gli XLS ISTAT di origine sono in `DCSC_Occupancy_in_collective_accommodation/`. ISTAT pubblica per
**circoscrizione turistica** fino al 2013 e per **comune** dal 2014: è il motivo per cui il pre-2014 comunale
non esiste, e non è una lacuna del download.

## Cosa resta

Nulla di rotto. Le idee aperte sono nel README sotto *Sviluppi futuri*: durata media del soggiorno, split
residenti/non-residenti, stagionalità, tasso di occupazione, benchmark europeo.

Un dato curioso mai spiegato: **nel 2006 l'extra-alberghiero di Cefalù si è dimezzato** (155.934 → 73.086 notti),
con la permanenza media da 5,8 a 4,1 notti. Non è un errore — la Sicilia nello stesso anno è piatta, e due file
ISTAT indipendenti concordano. Sembra la chiusura o riclassificazione di una grande struttura a soggiorno lungo.
Se si trova la causa, vale una nota nel popup.

## Come lavora l'utente

Parla italiano, conosce bene i dati e nota le incongruenze prima che le noti io. Diverse volte oggi un suo
dubbio apparentemente ingenuo — *"mi sembra assurdo"*, *"secondo me non sono coerenti"* — ha portato a bug reali.
Vanno presi sul serio e verificati sui dati, non spiegati via.

Vuole capire il perché, non solo il risultato. Preferisce che si verifichi contro le fonti invece di rispondere
a memoria, e che si dica chiaramente quando qualcosa non torna o quando l'errore è mio.
