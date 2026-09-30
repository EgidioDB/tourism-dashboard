# Contesto per Claude

Dashboard sul turismo italiano con focus su Cefalù. File unico `index.html`, nessun build step.
Il `README.md` documenta il progetto per chi lo usa; questo file serve a chi ci lavora dentro.

## Eseguire e verificare

La dashboard **non funziona col doppio click**: carica i dati via `fetch` e i browser lo bloccano su `file://`.
Serve un webserver.

```bash
python3 -m http.server 8000
```

Nel pannello browser dell'app il server avviato da `.claude/launch.json` può fallire con
`PermissionError` su `os.getcwd()`: macOS non dà a quel processo l'accesso alla Scrivania, dove sta il
progetto. Il terminale invece ce l'ha. In quel caso avviare il server dal terminale e agganciare il pannello
con la configurazione `dashboard-esistente`, che apre `http://localhost:8000` senza avviare nulla. La
soluzione definitiva è dare all'app l'accesso alla Scrivania in Impostazioni di sistema → Privacy e
sicurezza → File e cartelle: è una scelta dell'utente.

Verificare sempre a dashboard servita, non solo con `node --check`. La sintassi valida non dice nulla
sul comportamento: il 29 luglio un'eccezione a runtime ha azzerato metà pagina passando il check.

**Ogni scheda nuova va guardata anche su telefono (375 pixel), non solo su desktop.** Il 30 settembre la
scheda PNRR ha portato la sezione Cefalù a 10.325 pixel di altezza su mobile: le sezioni si rivelavano
quando ne era visibile l'8%, e 812 pixel di schermo su 10.325 sono il 7,9%, quindi da telefono la sezione
non compariva più. Su desktop era tutto a posto. Ora la rivelazione non dipende dall'altezza (`rootMargin`
invece di una soglia in percentuale), ma il controllo su telefono resta: le sezioni animate si vedono solo
dopo uno scroll vero, non con `scrollIntoView`.

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
- **Arrotonda solo per mostrare.** Le ciambelle arrotondavano i volumi a 0,1 milioni e poi ne calcolavano la
  variazione: il Molise usciva allo 0,0% invece di −15,5%. Il post-COVID derivato da indici già passati per `r1()`
  sbagliava l'ultima cifra. `volumeData`, `itBenchmark` e l'indice della Top City restano non arrotondati.
- **Un gap fra due indici è in punti, non in %.**
- **`itBenchmark` è base 2014, non 2012**, perché serve solo al gap con la Top City che è indicizzata al 2014.
  Non "correggerlo" a `rawData.it*[20]`: è già successo e falsava il gap.

## Trappole note

- **Aggregare i comuni non ricostruisce il dato regionale, ma il motivo dipende dall'anno.** Sui *totali* il
  2024 torna esatto: la somma di `serie/*.json` per regione fa il 100,0% di `regioni.json` in tutte le regioni,
  e la somma nazionale fa 466.158.045 notti, cioè il valore di `italia.json` costruito da un'altra fonte. È il
  **2014** a essere scoperto, dal 79% (Molise) al 99,9% (Umbria), ed è da lì che gli indici base 2014 risultano
  gonfiati fino a 28 punti. Sullo *split* alberghiero/extra invece non torna nemmeno il 2024: **1.933 delle
  5.014 serie con presenze nel 2024 hanno `pre_alb`/`pre_ext` a null** per segreto statistico, quindi alb+ext copre
  il 94,66% del totale nazionale, con uno scarto che va dallo 0,0% (Bolzano) al 17,2% (Piemonte). Non è
  riscalabile con un fattore unico, e i comuni oscurati sono i piccoli, dove l'extra pesa più della media.
  Per le regioni usa `regioni.json` ed `eurostat_regioni.json`, mai la somma dei comuni.
- **Nel file ISTAT circoscrizioni il totale 2004 è inaffidabile.** Alcune righe hanno la colonna Totale a zero
  con le componenti valorizzate (Catanzaro, Vibo Valentia). In `pre2012.json` i totali sono la somma di
  alberghiero + extra, non la colonna Totale. Nel 2012 le due letture coincidono.
- **Lazio e Marche hanno due valori 2012 diversi** fra le Circoscrizioni Turistiche e le serie regionali,
  0,8% e 3,4%. Sono due rilevazioni ISTAT distinte: ogni gruppo resta coerente al proprio interno e il popup
  del pre-2012 regionale lo spiega. Non tentare di "riconciliarle".
- **`DATA_PATH` e `comuniIndex` sono privati** all'IIFE dell'EXPLORER nel secondo blocco `<script>`. Il primo
  blocco ha le sue copie, `TOP_DATA_PATH` e `topComuniIndex`.
- **Gli anni ISTAT possono avere una nota attaccata.** Nel file delle serie storiche il 1986, il 1996 e il 1999
  sono scritti `1986(a)`, `1996(b)`, `1999(c)`: un parser che cerca quattro cifre pulite li scarta e la serie
  sembra bucata. Non lo era. Sono le tre volte in cui ISTAT ha cambiato il perimetro dell'extra-alberghiero —
  RTA spostate all'alberghiero nel 1986, agriturismi nel 1996, B&B nel 1999 — per cui **la quota di
  extra-alberghiero non è confrontabile a cavallo di quegli anni**: il 39,7% del 1958 e il 39,1% del 2024
  sono numeri quasi identici che misurano cose diverse. `renderStorico` le segna con linee tratteggiate.
- **I donut non coprono un periodo, sono due annate.** Mostrano il 2012 (la base) e il 2024, non le ere
  pre/post-2012: le etichette dicevano il contrario e la prima ciambella sommava le notti dei due anni
  chiamando totale il risultato. Ora è `2012 VS 2024` con la variazione. Il pre-2012 vero non è ricostruibile:
  le serie comunali partono dal 2014 e per le regioni esistono solo i punti 2004 e 2012.
- **Le serie comunali perdono la colonna flag di ISTAT**, che sta in `data/flag_istat.json`. Il **2015 di Cefalù
  è una copia del 2014** (flag d, in tutti i 24 campi): non usarlo come dato vero. Il flag **a** è una rottura di
  serie: Fiumicino, Marsala e Pescara salgono in classifica anche per quella, e Marsala diventa Top City della
  Sicilia. La scelta è stata segnalare con ⚠, non escludere: `rottureDi()`, `conFlag()`, `segnoRottura()`.
- **`popolazione.json`: ricostruzione intercensuaria fino al 2019, POSAS dal 2020**, entrambe al 1° gennaio.
  Prima il 2014–2018 era una retta inventata e il 2020–2024 un rilascio POSAS superato (ISTAT l'ha ripubblicato il
  18/12/2025): Cefalù risultava a 14.314 abitanti invece di 13.861 nel 2024, circa il 3% in più. Le due fonti ora si
  raccordano senza scalino. `build_popolazione.py` aggiorna anche il reddito pro capite di `irpef_cefalu.json`,
  che divide per la stessa popolazione: se ne cambi una, rigenera entrambe.
- **Il reddito imponibile IRPEF non contiene gli affitti brevi con cedolare secca**, né i forfettari: per il MEF
  *"reddito imponibile = reddito complessivo al netto della cedolare secca – deduzioni"*. Il reddito complessivo
  invece li comprende. Non attribuire agli affitti brevi la crescita del reddito imponibile, e ricorda che è
  nominale: 2014–2024 +36% nominale, +11% reale con l'IPCA Eurostat.
- **Le chiavi dei popup si sbagliano facilmente.** Due gruppi post-COVID aprivano i testi del post-2012.
  Verifica sempre gruppo per gruppo, non solo che la chiave esista.
- **L'imposta di soggiorno SIOPE è cassa, non competenza, e parte dal 2020.** Il mese è quello dell'incasso, che
  segue i versamenti delle strutture, non quello del soggiorno: non dividerla mese per mese per le presenze. Fino al
  2019 Cefalù la registrava in «Altre imposte n.a.c.» (1.01.01.99.001) mescolata ad altro. Un anno con incassi
  «da regolarizzare» (codici `0.`) non è chiuso: nel 2026 l'estate mancava perché 2,66 milioni erano ancora lì.
  Il codice ente si cerca per codice fiscale e comparto COMUNE: lo stesso CF ha anche la gestione commissariale.
- **Nei file SIOPE un comune assente non ha incassato zero: manca.** Nel 2023 non ci sono righe per 378 comuni,
  quasi tutta la Sardegna. `soggiorno_comuni.json` mette `null`, e la dashboard dice «assente da SIOPE».
- **Il mensile per comune esiste solo per il 2022–2024**, nel foglio *Dati Mensili* del file comunale: è la fonte di
  `stagionalita.json`, e il motivo per cui il grafico mensile dell'imposta non ha presenze nel 2020–2021. Nella
  banca dati ISTAT il mensile arriva alla provincia (`122_54_DF_DCSC_TUR_3`, dal 2016); la Regione Siciliana ha solo
  file provinciali non validati. La stima di Cefalù per quote provinciali regge (errore entro il 13% da aprile a
  ottobre) ed è nel README come analisi: l'utente l'ha voluta fuori dalla dashboard.
- **Il 2025 della banca dati ISTAT non è confrontabile col 2024 nell'extra-alberghiero.** Italia +14,9% (extra
  +35,7%, alberghiero +1,5%), Sicilia extra +136%, provincia di Palermo extra +200%. Il
  [comunicato ISTAT sul 2025](https://www.istat.it/wp-content/uploads/2026/03/Stat_Flash_IV_Trim_2025.pdf) dà le
  presenze a +2,3% e dichiara di escludere gli «Altri alloggi privati», cioè gli affitti brevi: con ogni probabilità
  la banca dati dal 2025 li comprende. Quando esce il 2025 comunale, verificarlo prima di aggiungerlo: se Cefalù
  fa lo stesso salto è una rottura di serie, da segnalare come il flag a.
- **Un comune che cambia provincia cambia codice ISTAT, e le serie lo spezzavano in due.** 56 comuni sardi (riforma
  del 2016) sono ricuciti sul codice nuovo da `ricuci_serie.py`; il codice vecchio non esiste più nei file, e il
  registro sta in `serie_ricucite.json`. Non ricucire le **fusioni** (stessa provincia, codice nuovo: il territorio è
  cambiato, es. Montalcino) né i **cambi di regione** (Sappada, Montecopiolo: cambia chi rileva i dati, Sappada
  perde il 39% al passaggio). Attenzione a «Valverde»: in Lombardia e in Sicilia sono due comuni diversi con anni
  complementari, un abbinamento solo per nome li unirebbe. Se ISTAT pubblica il 2025 con le province sarde del
  2025 (codici 113 e seguenti, già usati da SIOPE), la spaccatura si ripresenta: rieseguire lo script.
- **Il gettito teorico dell'imposta non si stima con le notti ISTAT.** Nel 2024 l'accertato (1,78 milioni, 2,01 € per
  notte di stagione) supera l'imposta teorica sulle notti ISTAT in quasi ogni scenario: si paga anche su notti che
  ISTAT non conta (affitti brevi via Airbnb dal febbraio 2024). Analisi e fonti nel README, sezione «Analisi». Le
  regole (1 aprile-31 ottobre, max 5 notti, esenti under 12, versamenti a bimestri entro il 15) vengono dal
  regolamento del 10/01/2024; le tariffe per anno le fissa il Sindaco, e prima del 2024 non sono state trovate.
- **I popup invecchiano in silenzio.** Contengono cifre, fonti e descrizioni dei grafici scritte a mano: quando
  cambi un calcolo, un dato o un grafico, cerca nell'oggetto `INFO` cosa lo cita. Il 30/09 ne sono emersi una
  ventina fuori sincrono: la mappa descriveva ancora la base 2014, il pre-2012 di Cefalù il verso di segno vecchio,
  la spesa turistica una trasparenza delle barre invertita, due fonti regionali "comuni aggregati", e l'imposta
  di soggiorno diceva "2022: superato il picco pre-COVID" con un valore sotto il 2019.

## Fonti dei dati

| Cosa | Dove | Note |
|------|------|------|
| Serie nazionale 1956–2024 | `data/italia.json` | valori in migliaia |
| Serie regionali 2008–2024 | `data/regioni.json` | solo arrivi e presenze totali |
| Serie comunali 2014–2024 | `data/serie/*.json` | 5.268 comuni, split completo; non c'è uno script che le generi |
| PNRR alberghi di Cefalù | `data/pnrr_turismo.json` | `python3 scripts/build_pnrr_turismo.py`, Italia Domani; importi assegnati, non pagati |
| Serie ricucite (cambio di provincia) | `data/serie_ricucite.json` | `python3 scripts/ricuci_serie.py`, poi flag, confronti e SIOPE |
| Pre-2014 regionale e Cefalù | `data/pre2012.json` | da XLS ISTAT circoscrizioni |
| Split alb/ext regionale | `data/eurostat_regioni.json` | `python3 scripts/fetch_eurostat.py` |
| Bilancio Cefalù 2005–2024 | `data/bilancio.json` | soggiorno, spesa turismo, entrate |
| Note ISTAT per comune-anno | `data/flag_istat.json` | `python3 scripts/build_flag_istat.py` |
| Imposta di soggiorno mensile 2020–2026 | `data/soggiorno_mensile.json` | `python3 scripts/build_siope_soggiorno.py`, cassa SIOPE |
| Imposta di soggiorno per comune 2020–2025 | `data/soggiorno_comuni.json` | stesso script; `p` è copia delle serie: rigenera se cambiano |
| Popolazione 2014–2024 | `data/popolazione.json` | `python3 scripts/build_popolazione.py`, scarica POSAS in `data/fonti/` |

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
