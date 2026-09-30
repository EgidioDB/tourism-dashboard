#!/usr/bin/env python3
"""Ricuce le serie comunali spezzate da un cambio di provincia.

ISTAT identifica il comune col codice provincia + comune. Quando un comune passa ad altra
provincia il codice cambia, e le serie di data/serie/ lo trattano come due comuni: il
2014-2016 sotto il codice vecchio, il 2017-2024 sotto il nuovo. Succede soprattutto in
Sardegna, con la riforma delle province del 2016: Olbia e 104017 fino al 2016 e 090047 dal
2017. Con la serie spezzata non c'e una crescita 2014-2024, quindi questi comuni restavano
fuori dalla classifica crescita, dalla scelta della Top City e dal gruppo dei comuni simili.

Una coppia si ricuce solo se:
  - stesso nome e stessa regione;
  - anni che non si sovrappongono, il vecchio codice tutto prima del nuovo;
  - provincia diversa. Stessa provincia e codice nuovo vuol dire fusione: il comune nuovo
    ha un territorio diverso (Montalcino con San Giovanni d'Asso, Cassano Spinola con
    Gavazzana) e le due serie non vanno unite.

I cambi di regione restano separati e vengono solo segnalati (Sappada dal Veneto al Friuli,
Montecopiolo dalle Marche all'Emilia-Romagna): con la regione cambia anche chi raccoglie i
dati, e Sappada al passaggio perde il 39% delle notti in un anno.

La serie unita prende il codice nuovo. Il file del codice vecchio viene rimosso, l'indice
ricalcolato con le stesse formule, e la coppia registrata in data/serie_ricucite.json, che
build_flag_istat.py usa per spostare sul codice nuovo le note ISTAT degli anni vecchi.

Lo script e idempotente: una coppia gia ricucita non si ritrova, perche il codice vecchio
non c'e piu. Dopo averlo eseguito vanno rigenerati i file che leggono le serie:
  python3 scripts/build_flag_istat.py
  python3 scripts/build_confronti.py
  python3 scripts/build_siope_soggiorno.py

Uso:  python3 scripts/ricuci_serie.py
"""
import json, os, re, unicodedata

BASE = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(BASE, "data")
INDICE = os.path.join(DATA, "comuni_index.json")
RICETTIVA = os.path.join(DATA, "ricettiva_index.json")
REGISTRO = os.path.join(DATA, "serie_ricucite.json")


def norm(nome):
    nome = unicodedata.normalize("NFKD", nome.upper()).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z]", "", nome)


def serie(cod):
    return json.load(open(os.path.join(DATA, "serie", cod + ".json"), encoding="utf-8"))


def anni_con_dati(s):
    return [a for a, p, r in zip(s["anni"], s["pre_tot"], s["arr_tot"]) if p is not None or r is not None]


def campi_indice(s):
    """Le stesse formule con cui e costruito comuni_index.json, verificate su tutti i comuni."""
    pre, arr = s["pre_tot"], s["arr_tot"]
    vp, va = [v for v in pre if v is not None], [v for v in arr if v is not None]
    return {
        "max_arr": max(va) if va else None,
        "growth_pre": round((pre[-1] / pre[0] - 1) * 100, 1) if pre[0] and pre[-1] is not None else None,
        "max_pre": max(vp) if vp else None,
    }


def unisci(vecchio, nuovo, chiavi):
    """Riempie i buchi del nuovo coi valori del vecchio; due valori nello stesso anno = errore."""
    for k in chiavi:
        for i, (v, n) in enumerate(zip(vecchio[k], nuovo[k])):
            if v is not None and n is not None:
                raise SystemExit("sovrapposizione su %s indice %d: %r e %r" % (k, i, v, n))
            if n is None:
                nuovo[k][i] = v


def main():
    indice = json.load(open(INDICE, encoding="utf-8"))
    per_cod = {c["cod"]: c for c in indice}
    gruppi = {}
    for c in indice:
        if not c["cod"].endswith("777"):          # gli aggregati "Altri comuni" non sono comuni
            gruppi.setdefault((norm(c["nome"]), c["regione"]), []).append(c["cod"])

    coppie, fusioni = [], []
    for (_, regione), cods in sorted(gruppi.items()):
        if len(cods) != 2:
            continue
        a, b = sorted(cods, key=lambda c: min(anni_con_dati(serie(c)) or [9999]))
        ya, yb = anni_con_dati(serie(a)), anni_con_dati(serie(b))
        if not ya or not yb or max(ya) >= min(yb):
            continue
        (fusioni if a[:3] == b[:3] else coppie).append((a, b))

    registro = json.load(open(REGISTRO, encoding="utf-8")) if os.path.exists(REGISTRO) else {
        "_fonte": "Coppie di codici ISTAT dello stesso comune, prima e dopo un cambio di provincia, "
                  "ricucite da scripts/ricuci_serie.py.",
        "_nota": "vecchio = codice fino all'ultimo anno di anni_vecchio, nuovo = codice dal primo anno "
                 "di anni_nuovo. La serie unita sta sotto il codice nuovo.",
        "_rigenera": "python3 scripts/ricuci_serie.py",
        "coppie": [],
    }
    ricettiva = json.load(open(RICETTIVA, encoding="utf-8"))
    for a, b in coppie:
        sa, sb = serie(a), serie(b)
        chiavi = [k for k, v in sb.items() if isinstance(v, list) and k != "anni"]
        if sa["anni"] != sb["anni"] or chiavi != [k for k, v in sa.items() if isinstance(v, list) and k != "anni"]:
            raise SystemExit("%s e %s: struttura diversa" % (a, b))
        ya, yb = anni_con_dati(sa), anni_con_dati(sb)
        unisci(sa, sb, chiavi)
        json.dump(sb, open(os.path.join(DATA, "serie", b + ".json"), "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
        os.remove(os.path.join(DATA, "serie", a + ".json"))
        per_cod[b].update(campi_indice(sb))
        del per_cod[a]
        # Capacita ricettiva: stessa spaccatura, 2010-2016 sul vecchio codice
        if a in ricettiva["comuni"]:
            if b in ricettiva["comuni"]:
                unisci(ricettiva["comuni"][a], ricettiva["comuni"][b], list(ricettiva["comuni"][b]))
            else:
                ricettiva["comuni"][b] = ricettiva["comuni"][a]
            del ricettiva["comuni"][a]
        registro["coppie"].append({
            "vecchio": a, "nuovo": b, "nome": sb["nome"], "regione": sb["regione"],
            "provincia_vecchia": sa["provincia"], "provincia_nuova": sb["provincia"],
            "anni_vecchio": [min(ya), max(ya)], "anni_nuovo": [min(yb), max(yb)],
        })

    if coppie:
        json.dump([c for c in indice if c["cod"] in per_cod], open(INDICE, "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
        json.dump(ricettiva, open(RICETTIVA, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        registro["coppie"].sort(key=lambda c: (c["regione"], c["nome"]))
        json.dump(registro, open(REGISTRO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ricucite %d serie (registro: %d coppie in tutto)" % (len(coppie), len(registro["coppie"])))
    for a, b in fusioni:
        print("  non ricucita, fusione nella stessa provincia: %s %s -> %s" % (per_cod[a]["nome"], a, b))


if __name__ == "__main__":
    main()
