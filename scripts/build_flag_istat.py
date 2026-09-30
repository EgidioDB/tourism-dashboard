#!/usr/bin/env python3
"""Genera data/flag_istat.json: le note ISTAT attaccate ai singoli comuni-anno.

Nel file comunale ISTAT la colonna "flag" dice quando un dato non e quello che sembra:
(a) una rottura di serie, (d) il 2015 non trasmesso e sostituito dall'anno prima, (e) un
dato stimato. Le serie in data/serie/*.json portano solo i numeri, quindi senza questo
file la dashboard mostrerebbe una copia del 2014 come se fosse il 2015, o un cambio di
rilevazione come se fosse crescita.

I codici vecchi delle serie ricucite (data/serie_ricucite.json, vedi ricuci_serie.py) vengono
portati sul codice nuovo: le note del 2014-2016 di Olbia stanno sotto 104017 nel file ISTAT,
ma la serie oggi e 090047. Le coppie finiscono anche in "ricuciti", per dirlo nella dashboard.

Uso:  python3 scripts/build_flag_istat.py
"""
import json, os, re
import openpyxl

BASE = os.path.join(os.path.dirname(__file__), "..")
XLSX_COM = os.path.join(BASE, "DCSC_Occupancy_in_collective_accommodation", "2. Dati comunali 2014-2024.xlsx")
ANNI = list(range(2014, 2025))
REGISTRO = os.path.join(BASE, "data", "serie_ricucite.json")
NOTA = re.compile(r"^\s*'?\(([a-z])\)\s*(.*)$")


def main():
    wb = openpyxl.load_workbook(XLSX_COM, read_only=True, data_only=True)
    coppie = json.load(open(REGISTRO, encoding="utf-8"))["coppie"] if os.path.exists(REGISTRO) else []
    nuovo_di = {c["vecchio"]: c["nuovo"] for c in coppie}
    comuni, legenda = {}, {}
    for anno in ANNI:
        for r in wb[str(anno)].iter_rows(min_row=7, values_only=True):
            cod, flag = r[5], r[6]
            if cod and str(cod).isdigit():
                m = re.match(r"^\(([a-z])\)$", str(flag or "").strip())
                if m:
                    cod = str(cod).zfill(6)
                    comuni.setdefault(nuovo_di.get(cod, cod), {})[str(anno)] = m.group(1)
            elif isinstance(r[0], str):
                # Le note in fondo al foglio: si tiene solo la parte italiana
                m = NOTA.match(r[0])
                if m:
                    legenda[m.group(1)] = m.group(2).split(" / ")[0].strip()
    usati = sorted({f for d in comuni.values() for f in d.values()})
    out = {
        "_fonte": "ISTAT — Movimento dei clienti negli esercizi ricettivi, dati comunali 2014-2024: "
                  "colonna flag dei fogli annuali.",
        "_rigenera": "python3 scripts/build_flag_istat.py",
        "legenda": {k: legenda[k] for k in usati},
        "comuni": dict(sorted(comuni.items())),
        "ricuciti": {c["nuovo"]: {"vecchio": c["vecchio"], "fino_al": c["anni_vecchio"][1],
                                  "provincia_vecchia": c["provincia_vecchia"],
                                  "provincia_nuova": c["provincia_nuova"]} for c in coppie},
    }
    dest = os.path.join(BASE, "data", "flag_istat.json")
    json.dump(out, open(dest, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("scritto data/flag_istat.json:", len(comuni), "comuni con almeno un flag")
    for k in usati:
        n = sum(1 for d in comuni.values() for f in d.values() if f == k)
        print("  (%s) %4d comuni-anno  %s" % (k, n, legenda[k]))


if __name__ == "__main__":
    main()
