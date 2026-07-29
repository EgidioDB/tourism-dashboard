#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rigenera data/italia.json dalla serie storica nazionale ISTAT.

Recupera anche 1986, 1996 e 1999, che nella versione precedente mancavano: nel
foglio ISTAT quelle celle non contengono un anno pulito ma "1986(a)", "1996(b)" e
"1999(c)", con il richiamo alla nota che segnala un cambio di definizione. Un
parser che legge l'anno come intero le scarta in silenzio.

Uso:  python3 scripts/build_italia.py
"""
import json, os, re, sys
import openpyxl

BASE = os.path.join(os.path.dirname(__file__), "..")
XLSX = os.path.join(BASE, "DCSC_Occupancy_in_collective_accommodation", "1. Serie storiche.xlsx")

# colonna -> campo. Arrivi 1-9, presenze 11-19; dentro ogni blocco: totale, alberghiero, extra.
COLONNE = {
    1: "arr_tot_res",  2: "arr_tot_nres",  3: "arr_tot",
    4: "arr_alb_res",  5: "arr_alb_nres",  6: "arr_alb",
    7: "arr_ext_res",  8: "arr_ext_nres",  9: "arr_ext",
    11: "pre_tot_res", 12: "pre_tot_nres", 13: "pre_tot",
    14: "pre_alb_res", 15: "pre_alb_nres", 16: "pre_alb",
    17: "pre_ext_res", 18: "pre_ext_nres", 19: "pre_ext",
}

# Le note a pie' di pagina del foglio: sono cambi di definizione, non anni anomali.
DISCONTINUITA = {
    1986: "Le residenze turistiche alberghiere passano dall'extra-alberghiero all'alberghiero.",
    1996: "Gli agriturismi entrano nell'extra-alberghiero.",
    1999: "I bed and breakfast entrano nell'extra-alberghiero.",
}


def main():
    ws = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)["IT 1956-2024"]
    anni, dati = [], {c: [] for c in COLONNE.values()}
    for r in ws.iter_rows(min_row=7, values_only=True):
        et = r[0]
        if et is None:
            continue
        m = re.match(r"^\s*(\d{4})", str(et))      # "1986(a)" -> 1986
        if not m:
            continue
        anni.append(int(m.group(1)))
        for col, campo in COLONNE.items():
            v = r[col] if col < len(r) else None
            dati[campo].append(round(v) if isinstance(v, (int, float)) else None)

    if not anni:
        sys.exit("Nessun anno letto dal foglio")
    buchi = [y for y in range(anni[0], anni[-1] + 1) if y not in anni]

    out = {
        "_fonte": "ISTAT — serie storica nazionale del movimento nelle strutture ricettive.",
        "_rigenera": "python3 scripts/build_italia.py",
        "note_unita": "migliaia",
        "_discontinuita": {str(k): v for k, v in DISCONTINUITA.items()},
        "_nota_discontinuita": "Anni in cui ISTAT ha cambiato il perimetro dell'extra-alberghiero: "
                               "le quote prima e dopo non sono direttamente confrontabili.",
        "anni": anni,
    }
    out.update(dati)

    dest = os.path.join(BASE, "data", "italia.json")
    json.dump(out, open(dest, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("scritto data/italia.json — %d anni, %d-%d" % (len(anni), anni[0], anni[-1]))
    print("  anni mancanti nella serie:", buchi or "nessuno")
    print("  discontinuita segnalate:", ", ".join(str(k) for k in DISCONTINUITA))


if __name__ == "__main__":
    main()
