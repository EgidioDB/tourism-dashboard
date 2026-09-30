#!/usr/bin/env python3
"""Genera data/pnrr_turismo.json: i progetti PNRR per la ricettivita localizzati a Cefalu.

Fonte: open data di Italia Domani, il catalogo nazionale dei progetti PNRR. Due file:
PNRR_Progetti.csv (un progetto per riga, con importi e stato) e PNRR_Localizzazione.csv
(dove si trova ogni progetto). Si collegano per CUP e codice locale del progetto.

La sottomisura e M1C3I4.02.01, "Miglioramento delle infrastrutture di ricettivita
attraverso lo strumento del Tax credit": riqualificazione di alberghi, con il Ministero del
Turismo come soggetto attuatore. L'impresa beneficiaria sta nella sintesi del progetto, prima
del primo asterisco. Il finanziamento PNRR e quello assegnato, non necessariamente erogato;
la parte privata e a carico dell'impresa.

Serve anche il totale nazionale della sottomisura, per dire che quota va a Cefalu.

I file (circa 380 MB) vengono scaricati in data/fonti/pnrr/ (esclusa da git) solo se mancano;
data di pubblicazione e SHA-256 finiscono nel JSON.

Uso:  python3 scripts/build_pnrr_turismo.py
"""
import csv, hashlib, json, os, urllib.request

BASE = os.path.join(os.path.dirname(__file__), "..")
DIR = os.path.join(BASE, "data", "fonti", "pnrr")
URL = "https://www.italiadomani.gov.it/content/dam/sogei-ng/opendata/"
DEST = os.path.join(BASE, "data", "pnrr_turismo.json")
SUBMISURA = "M1C3I4.02.01"
CEFALU = ("019", "082", "027")   # regione, provincia, comune nel file delle localizzazioni
UA = {"User-Agent": "tourism-dashboard/1.0"}


def scarica(nome):
    os.makedirs(DIR, exist_ok=True)
    url, path = URL + nome, os.path.join(DIR, nome)
    if not os.path.exists(path):
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=1200) as r, \
                open(path + ".part", "wb") as out:
            for blocco in iter(lambda: r.read(1 << 20), b""):
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


def righe(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f, delimiter=";")


def euro(s):
    """1.234,56 -> 1234.56; vuoto -> 0."""
    return float(s.replace(".", "").replace(",", ".")) if s else 0.0


def main():
    p_loc, m_loc = scarica("PNRR_Localizzazione.csv")
    p_prog, m_prog = scarica("PNRR_Progetti.csv")

    a_cefalu = {}
    for r in righe(p_loc):
        if (r["Regione"], r["Provincia"], r["Comune"]) == CEFALU:
            a_cefalu[(r["CUP"], r["Codice Locale Progetto"])] = euro(r["Percentuale di Localizzazione"])

    progetti, n_italia, pnrr_italia, estrazioni, descrizione = [], 0, 0.0, set(), ""
    for r in righe(p_prog):
        if r["Codice Univoco Submisura"] != SUBMISURA:
            continue
        n_italia += 1
        pnrr_italia += euro(r["Finanziamento PNRR"])
        estrazioni.add(r["Data di Estrazione"])
        descrizione = r["Descrizione Submisura"]
        quota = a_cefalu.get((r["CUP"], r["Codice Locale Progetto"]))
        if quota is None:
            continue
        if quota != 100:
            raise SystemExit("%s: localizzato a Cefalu solo al %s%%, da gestire" % (r["CUP"], quota))
        # "IMPRESA*Intervento*Non definito": beneficiario e intervento completi stanno nella sintesi
        parti = [p.strip() for p in r["Sintesi Progetto"].split("*")]
        fine_eff = r["Data Fine Progetto Effettiva"]
        progetti.append({
            "cup": r["CUP"],
            "beneficiario": parti[0] if parti else "",
            "intervento": parti[1] if len(parti) > 1 else r["Titolo Progetto"],
            "pnrr": round(euro(r["Finanziamento PNRR"]), 2),
            "totale": round(euro(r["Finanziamento Totale"]), 2),
            "privato": round(euro(r["Finanziamento Privato"]), 2),
            "stato": r["Stato Avanzamento Progetto"],
            "inizio": r["Data Inizio Progetto Effettiva"] or r["Data Inizio Progetto Prevista"],
            "fine": fine_eff or r["Data Fine Progetto Prevista"],
            "fine_effettiva": bool(fine_eff),
        })

    progetti.sort(key=lambda p: -p["pnrr"])
    out = {
        "_fonte": "Italia Domani — catalogo open data dei progetti PNRR (PNRR_Progetti.csv e "
                  "PNRR_Localizzazione.csv), sottomisura %s." % SUBMISURA,
        "_nota": "pnrr = finanziamento PNRR assegnato, non necessariamente erogato; privato = parte a "
                 "carico dell'impresa. Stato e date sono quelli della data di estrazione.",
        "_rigenera": "python3 scripts/build_pnrr_turismo.py",
        "_fonti": [m_prog, m_loc],
        "estrazione": sorted(estrazioni),
        "submisura": {"codice": SUBMISURA, "descrizione": descrizione,
                      "progetti_italia": n_italia, "pnrr_italia": round(pnrr_italia, 2)},
        "progetti": progetti,
    }
    json.dump(out, open(DEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tot = sum(p["pnrr"] for p in progetti)
    print("scritto data/pnrr_turismo.json: %d progetti a Cefalu, PNRR %.0f euro (%.2f%% dell'Italia, %d progetti)"
          % (len(progetti), tot, tot / pnrr_italia * 100, n_italia))


if __name__ == "__main__":
    main()
