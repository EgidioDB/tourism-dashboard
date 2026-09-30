#!/usr/bin/env python3
"""Genera data/soggiorno_mensile.json e data/soggiorno_comuni.json dagli incassi SIOPE.

soggiorno_mensile.json: l'imposta di soggiorno incassata da Cefalu, mese per mese.
soggiorno_comuni.json:  l'imposta incassata in un anno da ogni comune, con le sue presenze
                        ISTAT, per confrontare quanto rende una notte da un comune all'altro.

Fonte: SIOPE, gli incassi di cassa di ogni ente pubblico registrati dal tesoriere, pubblicati
da RGS e Banca d'Italia su siope.it. Ogni riga dei file annuali e (ente, anno, mese, codice
gestionale, importo in centesimi). L'imposta di soggiorno ha due codici:

  1.01.01.41.001  riscossa con l'attivita ordinaria di gestione
  1.01.01.41.002  riscossa a seguito di verifica e controllo

La serie parte dal 2020. Fino al 2019 Cefalu non usava questi codici: l'imposta finiva nella
voce generica 1.01.01.99.001 "Altre imposte, tasse e proventi n.a.c.", insieme ad altro, e non
si puo separare. Nel 2020, quando compare il codice proprio, quella voce scende da 1,7 milioni
a 174.000 euro.

Sono incassi di cassa, non accertamenti: il mese e quello in cui i soldi arrivano al Comune,
che segue le scadenze di versamento delle strutture e non il mese del soggiorno. Sugli anni
completi il totale torna con gli accertamenti di bilancio.json: 2023 al centesimo, 2024 +0,2%,
2021 e 2022 entro il 2%. Il 2020 e sotto del 12%.

I file vengono scaricati in data/fonti/siope/ (esclusa da git) solo se mancano; la data di
pubblicazione si rilegge sempre dalla fonte.

Uso:  python3 scripts/build_siope_soggiorno.py
"""
import csv, glob, hashlib, io, json, os, re, unicodedata, urllib.request, zipfile

BASE = os.path.join(os.path.dirname(__file__), "..")
DIR = os.path.join(BASE, "data", "fonti", "siope")
URL = "https://www.siope.it/documenti/siope2/open/last/"
DEST = os.path.join(BASE, "data", "soggiorno_mensile.json")
DEST_COMUNI = os.path.join(BASE, "data", "soggiorno_comuni.json")
ANNI_CHIUSI = list(range(2020, 2026))   # il confronto fra comuni usa solo anni completi
CF_CEFALU = "00110740826"
CODICI = ("1.01.01.41.001", "1.01.01.41.002")
ANNI = list(range(2020, 2027))
UA = {"User-Agent": "tourism-dashboard/1.0"}


def scarica(nome):
    """Scarica il file se manca; restituisce percorso e metadati della fonte."""
    os.makedirs(DIR, exist_ok=True)
    url, path = URL + nome, os.path.join(DIR, nome)
    if not os.path.exists(path):
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=900) as r, \
                open(path + ".part", "wb") as out:
            while True:
                blocco = r.read(1 << 20)
                if not blocco:
                    break
                out.write(blocco)
        os.replace(path + ".part", path)
        print("scaricato", nome)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA, method="HEAD"), timeout=60) as r:
        last_modified = r.headers.get("Last-Modified")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blocco in iter(lambda: f.read(1 << 20), b""):
            h.update(blocco)
    return path, {"url": url, "lastModified": last_modified, "sha256": h.hexdigest()}


def righe(path, prefisso):
    with zipfile.ZipFile(path) as z:
        (membro,) = [n for n in z.namelist() if os.path.basename(n).startswith(prefisso)]
        yield from csv.reader(io.TextIOWrapper(z.open(membro), encoding="latin-1", newline=""))


def codice_ente(anagrafiche):
    """Il Comune si individua dal codice fiscale, non dal nome: con lo stesso codice fiscale
    esiste anche la GESTIONE COMMISSARIALE DI CEFALU' (2015-2021), che non incassa l'imposta."""
    trovati = [r[0] for r in righe(anagrafiche, "ANAG_ENTI_SIOPE") if r[3] == CF_CEFALU and r[8] == "COMUNE"]
    if len(trovati) != 1:
        raise SystemExit("anagrafica SIOPE: atteso un solo Comune con CF %s, trovati %r" % (CF_CEFALU, trovati))
    return trovati[0]


def norm(nome):
    """COMUNE DI CEFALU' e Cefalù diventano entrambi CEFALU."""
    nome = re.sub(r"^COMUNE DI ", "", nome.upper())
    nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z]", "", nome)


def collega_comuni(anagrafiche):
    """Ente SIOPE -> codice ISTAT delle nostre serie comunali.

    Di norma il codice coincide: provincia + comune dell'anagrafica SIOPE. Non coincide dove
    le province sono cambiate, soprattutto in Sardegna: SIOPE usa le province del 2025, le
    serie ISTAT quelle del 2017. Li si ripiega sul nome del comune dentro la stessa regione,
    scegliendo fra i codici omonimi quello che ha presenze nel 2020-2024: nelle serie lo
    stesso comune sardo puo comparire con due codici, uno per anni diversi."""
    regione_prov = {r[3]: r[2] for r in righe(anagrafiche, "ANAG_REG_PROV")}
    indice = json.load(open(os.path.join(BASE, "data", "comuni_index.json"), encoding="utf-8"))
    codici = {c["cod"] for c in indice}
    alias = {"TRENTINO-ALTO ADIGE": ("BOLZANO - BOZEN", "TRENTO")}
    per_nome = {}
    for c in indice:
        per_nome.setdefault((norm(c["nome"]), c["regione"]), []).append(c["cod"])

    def con_presenze(cod):
        s = json.load(open(os.path.join(BASE, "data", "serie", cod + ".json"), encoding="utf-8"))
        return sum(1 for a, v in zip(s["anni"], s["pre_tot"]) if 2020 <= a <= 2024 and v)

    ente_cod, modo = {}, {"codice": 0, "nome": 0}
    for r in righe(anagrafiche, "ANAG_ENTI_SIOPE"):
        if r[8] != "COMUNE":
            continue
        cod = r[6] + r[5]
        if cod in codici:
            ente_cod[r[0]] = cod
            modo["codice"] += 1
            continue
        regione = regione_prov.get(r[6], "")
        cand = [c for reg in alias.get(regione, (regione,)) for c in per_nome.get((norm(r[4]), reg), [])]
        cand = [c for c in cand if con_presenze(c)]
        if len(cand) == 1:
            ente_cod[r[0]] = cand[0]
            modo["nome"] += 1
    return ente_cod, modo


def main():
    anag, meta_anag = scarica("SIOPE_ANAGRAFICHE.zip")
    ente = codice_ente(anag)
    ente_cod, modo = collega_comuni(anag)
    fonti, mensile, da_regolarizzare, ultimo_mese = [], {}, {}, {}
    per_comune = {}   # codice ISTAT -> {anno: centesimi}
    presenti = {}     # anno -> enti con almeno una riga, di qualunque voce
    for anno in ANNI:
        path, meta = scarica("SIOPE_ENTRATE.%d.zip" % anno)
        cent = [0] * 12
        visti, reg, mesi_file = set(), 0, set()
        presenti[anno] = set()
        for codice, a, mese, gestionale, importo in righe(path, "ENTRATE_%d" % anno):
            if a != str(anno):
                raise SystemExit("%s: anno inatteso %r" % (path, a))
            m = int(mese)
            mesi_file.add(m)
            if codice in ente_cod:
                presenti[anno].add(codice)
                if gestionale in CODICI:
                    c = per_comune.setdefault(ente_cod[codice], {})
                    c[anno] = c.get(anno, 0) + int(importo)
            if codice != ente:
                continue
            chiave = (m, gestionale)
            if chiave in visti:
                raise SystemExit("%s: movimento duplicato %r" % (path, chiave))
            visti.add(chiave)
            if gestionale in CODICI:
                cent[m - 1] += int(importo)
            elif gestionale.startswith("0."):
                reg += int(importo)
        ultimo = max(mesi_file)
        ultimo_mese[anno] = ultimo
        # I mesi non ancora pubblicati restano vuoti: zero vorrebbe dire "nessun incasso"
        mensile[anno] = [round(c / 100, 2) if i < ultimo else None for i, c in enumerate(cent)]
        da_regolarizzare[anno] = round(reg / 100, 2)
        fonti.append(dict(meta, anno=anno, ultimoMese=ultimo))

    out = {
        "_fonte": "SIOPE — incassi di cassa degli enti pubblici, RGS e Banca d'Italia (siope.it). "
                  "Codici gestionali 1.01.01.41.001 e 1.01.01.41.002, imposta di soggiorno.",
        "_nota": "Incassi di cassa, non accertamenti: il mese e quello in cui i soldi arrivano al "
                 "Comune, secondo le scadenze di versamento delle strutture, non quello del soggiorno. "
                 "Prima del 2020 l'imposta era registrata nella voce generica 'Altre imposte n.a.c.' "
                 "e non e separabile. Un anno con mesi mancanti o con incassi ancora da regolarizzare "
                 "non e confrontabile con gli anni chiusi.",
        "_rigenera": "python3 scripts/build_siope_soggiorno.py",
        "_fonti": [dict(meta_anag, file="anagrafiche")] + fonti,
        "ente": {"codice_siope": ente, "codice_fiscale": CF_CEFALU},
        "anni": ANNI,
        "ultimo_mese": {str(a): m for a, m in ultimo_mese.items()},
        "mensile": {str(a): v for a, v in mensile.items()},
        "da_regolarizzare": {str(a): v for a, v in da_regolarizzare.items()},
    }
    json.dump(out, open(DEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("scritto data/soggiorno_mensile.json, ente SIOPE", ente)
    scrivi_comuni(per_comune, presenti, ente_cod, modo, [dict(meta_anag, file="anagrafiche")] + fonti)
    for a in ANNI:
        tot = sum(v for v in mensile[a] if v is not None)
        print("  %d: %12s euro, mesi 1-%d, da regolarizzare %s" % (a, "{:,.2f}".format(tot), ultimo_mese[a],
                                                                    "{:,.2f}".format(da_regolarizzare[a])))



def scrivi_comuni(per_comune, presenti, ente_cod, modo, fonti):
    """Un comune entra se nel 2020-2025 ha incassato qualcosa col codice dell'imposta.
    Quelli collegati ma senza incassi vanno in 'senza_codice': non incassano l'imposta, oppure
    la registrano nella voce generica 'Altre imposte n.a.c.' come Cefalu fino al 2019. Dai
    dati non si distinguono, e la dashboard lo deve dire."""
    # Un comune assente dal file di un anno non ha incassato zero: manca il dato. Nel 2023
    # SIOPE non ha nessuna riga per 378 comuni, quasi tutta la Sardegna.
    enti_di = {}
    for e, cod in ente_cod.items():
        enti_di.setdefault(cod, []).append(e)
    comuni, senza, mancanti = {}, [], {}
    for cod in sorted(enti_di):
        s = json.load(open(os.path.join(BASE, "data", "serie", cod + ".json"), encoding="utf-8"))
        notti = [s["pre_tot"][s["anni"].index(a)] if a in s["anni"] else None for a in ANNI_CHIUSI]
        euro = []
        for a in ANNI_CHIUSI:
            if any(e in presenti[a] for e in enti_di[cod]):
                euro.append(round(per_comune.get(cod, {}).get(a, 0) / 100))
            else:
                euro.append(None)
                mancanti[a] = mancanti.get(a, 0) + 1
        if any(euro):
            comuni[cod] = {"e": euro, "p": notti}
        elif any(notti):
            senza.append(cod)
    out = {
        "_fonte": "SIOPE — incassi di cassa, codici 1.01.01.41.001 e 1.01.01.41.002, imposta di "
                  "soggiorno; presenze dalle serie comunali ISTAT in data/serie/.",
        "_nota": "e = euro incassati nell'anno (null se il comune non compare nel file SIOPE di "
                 "quell'anno), p = presenze ISTAT dello stesso anno (null dove ISTAT non le ha ancora "
                 "pubblicate). I comuni in senza_codice non hanno incassi col codice "
                 "proprio: o non applicano l'imposta, o la registrano nella voce generica. Rigenerare "
                 "anche dopo aver aggiornato le serie comunali, perche p ne e una copia.",
        "_rigenera": "python3 scripts/build_siope_soggiorno.py",
        "_collegamento": {"per_codice": modo["codice"], "per_nome": modo["nome"]},
        "_assenti_da_siope": {str(a): n for a, n in sorted(mancanti.items())},
        "_fonti": fonti,
        "anni": ANNI_CHIUSI,
        "comuni": comuni,
        "senza_codice": senza,
    }
    json.dump(out, open(DEST_COMUNI, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("scritto data/soggiorno_comuni.json: %d comuni con incassi, %d senza; collegati %d per codice, %d per nome"
          % (len(comuni), len(senza), modo["codice"], modo["nome"]))


if __name__ == "__main__":
    main()
