#!/usr/bin/env python3
"""Rigenera data/eurostat_regioni.json dall'API Eurostat.

Scarica i pernottamenti NUTS2 (tour_occ_nin2) per alberghiero (NACE I551) ed
extra-alberghiero (I552 + I553) negli anni che servono alla dashboard, e li
salva come JSON versionato nel repo. La dashboard non chiama Eurostat a runtime:
resta un file statico apribile anche offline.

Uso:  python3 scripts/fetch_eurostat.py
"""
import json, urllib.request, urllib.parse, os, sys

BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tour_occ_nin2"
ANNI = [2012, 2014, 2019, 2024]
ALB, EXT = ["I551"], ["I552", "I553"]

# Nome in regionalDataFull -> codici NUTS2 (Trentino somma le due province autonome)
NUTS = {
    "Piemonte": ["ITC1"], "Valle d'Aosta": ["ITC2"], "Liguria": ["ITC3"], "Lombardia": ["ITC4"],
    "Trentino": ["ITH1", "ITH2"], "Veneto": ["ITH3"], "Friuli": ["ITH4"], "Emilia-Romagna": ["ITH5"],
    "Toscana": ["ITI1"], "Umbria": ["ITI2"], "Marche": ["ITI3"], "Lazio": ["ITI4"],
    "Abruzzo": ["ITF1"], "Molise": ["ITF2"], "Campania": ["ITF3"], "Puglia": ["ITF4"],
    "Basilicata": ["ITF5"], "Calabria": ["ITF6"], "Sicilia": ["ITG1"], "Sardegna": ["ITG2"],
    "Italia": ["IT"],
}


def fetch(geos, naces):
    """Ritorna {(geo, nace, anno): valore} decodificando il formato JSON-stat."""
    q = [("format", "JSON"), ("lang", "EN"), ("c_resid", "TOTAL"), ("unit", "NR")]
    q += [("geo", g) for g in geos] + [("nace_r2", n) for n in naces]
    q += [("time", str(a)) for a in ANNI]
    url = BASE + "?" + urllib.parse.urlencode(q)
    with urllib.request.urlopen(url, timeout=120) as r:
        d = json.load(r)
    dim, size = d["id"], d["size"]
    cats = {k: d["dimension"][k]["category"]["index"] for k in dim}
    inv = {k: {v: kk for kk, v in c.items()} for k, c in cats.items()}
    out = {}
    for flat, val in d["value"].items():
        rem, coord = int(flat), {}
        for k, s in reversed(list(zip(dim, size))):
            coord[k] = inv[k][rem % s]
            rem //= s
        out[(coord["geo"], coord["nace_r2"], int(coord["time"]))] = val
    return out


def main():
    geos = sorted({g for v in NUTS.values() for g in v})
    print(f"Scarico {len(geos)} aree x {len(ALB + EXT)} categorie x {len(ANNI)} anni...")
    raw = fetch(geos, ALB + EXT)
    if not raw:
        sys.exit("Nessun dato ricevuto da Eurostat.")

    regioni, mancanti = {}, []
    for nome, codes in NUTS.items():
        rec = {}
        for anno in ANNI:
            alb = sum(raw.get((c, n, anno), 0) for c in codes for n in ALB)
            ext = sum(raw.get((c, n, anno), 0) for c in codes for n in EXT)
            if not alb or not ext:
                mancanti.append(f"{nome} {anno}")
                continue
            rec[str(anno)] = {"alb": alb, "ext": ext, "pre": alb + ext}
        regioni[nome] = rec

    out = {
        "_fonte": "Eurostat tour_occ_nin2 — pernottamenti negli esercizi ricettivi per regione NUTS2.",
        "_nota": "alb = NACE I551 (alberghi e simili); ext = I552 + I553 (alloggi per vacanze e campeggi). "
                 "Trentino somma le province autonome ITH1 e ITH2.",
        "_rigenera": "python3 scripts/fetch_eurostat.py",
        "anni": ANNI,
        "regioni": regioni,
    }
    dest = os.path.join(os.path.dirname(__file__), "..", "data", "eurostat_regioni.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"Scritto {os.path.normpath(dest)} — {len(regioni)} aree")
    if mancanti:
        print("ATTENZIONE, valori mancanti: " + ", ".join(mancanti))


if __name__ == "__main__":
    main()
