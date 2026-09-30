#!/usr/bin/env python3
"""Rigenera data/popolazione.json e il reddito pro capite di data/irpef_cefalu.json.

Popolazione residente al 1° gennaio, per comune, da due pubblicazioni ISTAT che si
raccordano senza scalini:

- 2014-2019: ricostruzione della popolazione intercensuaria, in
  data/PIL/PopolazioneEta-SingolaArea-Comuni/ (una tabella per comune);
- 2020-2024: POSAS, "Popolazione residente per eta, sesso e stato civile al 1° gennaio",
  file nazionali per comune scaricati da demo.istat.it.

Prima del 2014-2019 c'era una retta estrapolata dal trend, e il 2020-2024 veniva da un
rilascio POSAS superato: ISTAT ha ripubblicato quegli anni il 18 dicembre 2025, e per
Cefalu i valori vecchi erano circa il 3% piu alti (14.314 contro 13.861 nel 2024).

I file POSAS vengono scaricati in data/fonti/posas/ (esclusa da git) solo se mancano.
URL, Last-Modified e SHA-256 finiscono nel campo _fonti del JSON.

Il reddito pro capite di irpef_cefalu.json e reddito imponibile / popolazione dello
stesso anno: cambiando la popolazione va ricalcolato, altrimenti i due file divergono.

Uso:  python3 scripts/build_popolazione.py
"""
import csv, glob, hashlib, io, json, os, urllib.request, zipfile

BASE = os.path.join(os.path.dirname(__file__), "..")
DIR_RIC = os.path.join(BASE, "data", "PIL", "PopolazioneEta-SingolaArea-Comuni")
DIR_POSAS = os.path.join(BASE, "data", "fonti", "posas")
URL_POSAS = "https://demo.istat.it/data/posas/POSAS_{anno}_it_Comuni.zip"
DEST = os.path.join(BASE, "data", "popolazione.json")
IRPEF = os.path.join(BASE, "data", "irpef_cefalu.json")
CEFALU = "082027"
ANNI = list(range(2014, 2025))
ANNI_RIC = list(range(2014, 2020))
ANNI_POSAS = list(range(2020, 2025))


def ricostruzione():
    """Totale al 1° gennaio per comune, dalla prima tabella del file: tutte le cittadinanze."""
    out = {}
    for f in glob.glob(os.path.join(DIR_RIC, "*.csv")):
        righe = open(f, encoding="utf-8", errors="replace").read().splitlines()
        cod = righe[0].split("Comune: ")[1][:6]
        anni = [int(a) for a in righe[4].split(";")[1:]]
        tot = next(r for r in righe[5:] if r.startswith("Totale;")).split(";")[1:]
        out[cod] = {a: int(v) for a, v in zip(anni, tot) if v}
    return out


def scarica_posas(anno):
    """Scarica il file nazionale se manca; restituisce percorso e metadati della fonte."""
    os.makedirs(DIR_POSAS, exist_ok=True)
    url = URL_POSAS.format(anno=anno)
    path = os.path.join(DIR_POSAS, os.path.basename(url))
    ua = {"User-Agent": "tourism-dashboard/1.0"}
    if not os.path.exists(path):
        with urllib.request.urlopen(urllib.request.Request(url, headers=ua), timeout=300) as r, \
                open(path + ".part", "wb") as out:
            out.write(r.read())
        os.replace(path + ".part", path)
        print("scaricato", os.path.basename(path))
    # La data di pubblicazione si legge sempre dalla fonte, anche col file gia in cache:
    # se ISTAT ripubblica, il JSON lo registra e l'hash non torna piu con quello nuovo
    with urllib.request.urlopen(urllib.request.Request(url, headers=ua, method="HEAD"), timeout=60) as r:
        last_modified = r.headers.get("Last-Modified")
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    return path, {"url": url, "lastModified": last_modified, "sha256": sha}


def posas(path):
    """Totale per comune: la riga con eta 999, verificata contro la somma delle eta."""
    with zipfile.ZipFile(path) as z:
        (nome,) = z.namelist()
        rd = csv.reader(io.TextIOWrapper(z.open(nome), encoding="utf-8-sig"), delimiter=";")
        next(rd)                               # titolo
        if next(rd)[-1] != "Totale":
            raise SystemExit(path + ": l'ultima colonna non e 'Totale'")
        tot, somma = {}, {}
        for r in rd:
            if len(r) < 3 or not r[0].isdigit():
                continue
            if r[2] == "999":
                tot[r[0]] = int(r[-1])
            else:
                somma[r[0]] = somma.get(r[0], 0) + int(r[-1])
    diversi = [c for c in tot if tot[c] != somma.get(c)]
    if diversi:
        raise SystemExit(path + ": totale diverso dalla somma delle eta per " + ", ".join(diversi[:5]))
    return tot


def main():
    pop = json.load(open(DEST, encoding="utf-8"))
    assert pop["anni"] == ANNI, "popolazione.json: anni inattesi"
    ric = ricostruzione()
    fonti, per_anno = [], {}
    for anno in ANNI_POSAS:
        path, meta = scarica_posas(anno)
        per_anno[anno] = posas(path)
        fonti.append(dict(meta, anno=anno))

    for cod, serie in pop["comuni"].items():
        for i, anno in enumerate(ANNI):
            fonte = ric.get(cod, {}) if anno in ANNI_RIC else per_anno[anno]
            serie[i] = fonte.get(anno) if anno in ANNI_RIC else fonte.get(cod)

    out = {
        "_fonte": "ISTAT — popolazione residente al 1° gennaio. 2014-2019: ricostruzione della "
                  "popolazione intercensuaria (data/PIL/PopolazioneEta-SingolaArea-Comuni). "
                  "2020-2024: POSAS, file nazionali per comune da demo.istat.it.",
        "_nota": "Le due fonti si raccordano: il rapporto POSAS 2020 / ricostruzione 2019 ha la stessa "
                 "distribuzione di una normale variazione annua. Un comune senza dato in una fonte "
                 "resta vuoto per quell'anno, invece di ricevere un valore stimato.",
        "_fonti": fonti,
        "_rigenera": "python3 scripts/build_popolazione.py",
        "anni": ANNI,
        "comuni": pop["comuni"],
    }
    json.dump(out, open(DEST, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    cef = dict(zip(ANNI, pop["comuni"][CEFALU]))
    print("scritto data/popolazione.json — Cefalù:", cef)

    # Reddito pro capite di Cefalù: stessa popolazione, stesso anno
    irpef = json.load(open(IRPEF, encoding="utf-8"))
    for anno, p in cef.items():
        irpef["popolazione"][str(anno)] = p
        d = irpef["dati"].get(str(anno))
        if d and p:
            d["popolazione"] = p
            d["reddito_pro_capite"] = round(d["reddito_imponibile"] / p)
    json.dump(irpef, open(IRPEF, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("aggiornato data/irpef_cefalu.json — reddito pro capite:",
          {a: irpef["dati"][str(a)]["reddito_pro_capite"] for a in ANNI if str(a) in irpef["dati"]})


if __name__ == "__main__":
    main()
