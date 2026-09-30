#!/usr/bin/env python3
"""Genera data/soggiorno_mensile.json: l'imposta di soggiorno incassata da Cefalu, mese per mese.

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
import csv, hashlib, io, json, os, urllib.request, zipfile

BASE = os.path.join(os.path.dirname(__file__), "..")
DIR = os.path.join(BASE, "data", "fonti", "siope")
URL = "https://www.siope.it/documenti/siope2/open/last/"
DEST = os.path.join(BASE, "data", "soggiorno_mensile.json")
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


def main():
    anag, meta_anag = scarica("SIOPE_ANAGRAFICHE.zip")
    ente = codice_ente(anag)
    fonti, mensile, da_regolarizzare, ultimo_mese = [], {}, {}, {}
    for anno in ANNI:
        path, meta = scarica("SIOPE_ENTRATE.%d.zip" % anno)
        cent = [0] * 12
        visti, reg, mesi_file = set(), 0, set()
        for codice, a, mese, gestionale, importo in righe(path, "ENTRATE_%d" % anno):
            if a != str(anno):
                raise SystemExit("%s: anno inatteso %r" % (path, a))
            m = int(mese)
            mesi_file.add(m)
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
    for a in ANNI:
        tot = sum(v for v in mensile[a] if v is not None)
        print("  %d: %12s euro, mesi 1-%d, da regolarizzare %s" % (a, "{:,.2f}".format(tot), ultimo_mese[a],
                                                                    "{:,.2f}".format(da_regolarizzare[a])))


if __name__ == "__main__":
    main()
