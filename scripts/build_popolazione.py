#!/usr/bin/env python3
"""Rigenera gli anni 2014-2019 di data/popolazione.json dalla ricostruzione ISTAT.

Prima quegli anni erano una retta: il 2019 da POSAS e il 2014-2018 estrapolati all'indietro
dal trend 2019-2024, per 7.867 comuni su 7.987. ISTAT pubblica pero la ricostruzione
intercensuaria della popolazione al 1° gennaio 2002-2019, che riallinea l'anagrafe ai
censimenti: e quella che sta in data/PIL/PopolazioneEta-SingolaArea-Comuni/.

Il 2020-2024 resta quello di POSAS gia nel file: in repo non c'e un'altra fonte per
quegli anni. I comuni senza ricostruzione (istituiti o fusi dopo il 2019) restano vuoti
per il 2014-2019, invece di ricevere un valore inventato.

Uso:  python3 scripts/build_popolazione.py
"""
import glob, json, os

BASE = os.path.join(os.path.dirname(__file__), "..")
DIR_RIC = os.path.join(BASE, "data", "PIL", "PopolazioneEta-SingolaArea-Comuni")
DEST = os.path.join(BASE, "data", "popolazione.json")
ANNI_RIC = list(range(2014, 2020))


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


def main():
    pop = json.load(open(DEST, encoding="utf-8"))
    anni = pop["anni"]
    ric = ricostruzione()
    cambiati = svuotati = 0
    for cod, serie in pop["comuni"].items():
        r = ric.get(cod)
        for a in ANNI_RIC:
            i = anni.index(a)
            nuovo = r.get(a) if r else None
            if nuovo != serie[i]:
                if nuovo is None:
                    svuotati += 1
                else:
                    cambiati += 1
                serie[i] = nuovo
    out = {
        "_fonte": "ISTAT — popolazione residente al 1° gennaio. 2014-2019: ricostruzione della "
                  "popolazione intercensuaria (data/PIL/PopolazioneEta-SingolaArea-Comuni). "
                  "2020-2024: POSAS.",
        "_nota": "Fino al 2019 la serie e la ricostruzione ISTAT, non l'anagrafe: fra il 2019 e il "
                 "2020 puo esserci un piccolo scalino dovuto al cambio di fonte. I comuni senza "
                 "ricostruzione hanno il 2014-2019 vuoto.",
        "_rigenera": "python3 scripts/build_popolazione.py",
        "anni": anni,
        "comuni": pop["comuni"],
    }
    json.dump(out, open(DEST, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("scritto data/popolazione.json: %d valori sostituiti, %d svuotati (comuni senza ricostruzione)"
          % (cambiati, svuotati))
    print("  Cefalù:", dict(zip(anni, pop["comuni"]["082027"])))


if __name__ == "__main__":
    main()
