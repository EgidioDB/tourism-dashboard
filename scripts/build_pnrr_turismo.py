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
import csv, hashlib, json, os, re, urllib.request

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


PICCOLE = {"di", "del", "della", "dello", "dei", "degli", "delle", "e", "al", "alla", "da", "in", "per"}
FORME = {"S.R.L.": "S.r.l.", "SRL": "S.r.l.", "S.R.L.S.": "S.r.l.s.", "SRLS": "S.r.l.s.", "S.P.A.": "S.p.A.", "SPA": "S.p.A."}


ACCENTI = {"a": "à", "e": "è", "i": "ì", "o": "ò", "u": "ù"}


def titolo(testo):
    """HOTEL LE CALETTE -> Hotel Le Calette; le sigle puntate (S.E.A.C.) restano come sono.
    La fonte scrive l'accento come apostrofo (CEFALU', SOCIETA') e la forma giuridica per esteso."""
    t = re.sub(r"SOCIETA'? A RESPONSABILITA'? LIMITATA SEMPLIFICATA", "S.r.l.s.", testo, flags=re.I)
    t = re.sub(r"SOCIETA'? A RESPONSABILITA'? LIMITATA", "S.r.l.", t, flags=re.I)
    t = re.sub(r"\s-(?=\S)|(?<=\S)-(?=\s|$)", " ", t)          # trattini spaiati: " -S.P.A.-"
    t = re.sub(r"\s+-\s+", " – ", t)                              # trattino separatore
    t = re.sub(r"([aeiou])'(?=\s|$)", lambda m: ACCENTI[m.group(1).lower()], t, flags=re.I)
    parole = []
    for i, p in enumerate(re.sub(r"\s+", " ", t.strip(" -")).split(" ")):
        pulita = p.strip("-,")
        if pulita.upper() in FORME:
            parole.append(p.replace(pulita, FORME[pulita.upper()]))
        elif re.fullmatch(r"(?:[A-Z]\.){2,}", pulita) or pulita in FORME.values() or p == "–":
            parole.append(p)
        elif i > 0 and p.lower() in PICCOLE:
            parole.append(p.lower())
        else:
            parole.append("'".join(x[:1].upper() + x[1:].lower() for x in p.split("'")))
    return " ".join(parole)


def struttura(intervento, impresa):
    """Il nome da mostrare: la struttura se la fonte la nomina, altrimenti l'impresa senza forma
    giuridica. Il testo originale resta in intervento e beneficiario."""
    m = re.search(r"hotel\s+(.+)$", intervento, re.I)
    if m:
        return "Hotel " + titolo(m.group(1))
    m = re.search(r"struttura\s+(.+?)\s+(?:srls|s\.r\.l|sita)", intervento, re.I)
    if m:
        return titolo(m.group(1))
    return titolo(re.split(r"\s+(?:S\.?R\.?L|S\.?P\.?A)", impresa, flags=re.I)[0])


def etichette(intervento):
    """Tipi di intervento citati nel testo della fonte, per leggerli a colpo d'occhio."""
    t = intervento.lower()
    return [nome for nome, chiave in (("Riqualificazione", "riqualific"), ("Efficienza energetica", "energetic"),
                                      ("Barriere architettoniche", "barriere"), ("Digitale", "digital"))
            if chiave in t]


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
        impresa = parti[0] if parti else ""
        intervento = parti[1] if len(parti) > 1 else r["Titolo Progetto"]
        progetti.append({
            "cup": r["CUP"],
            "struttura": struttura(intervento, impresa),
            "impresa": titolo(impresa),
            "tipi": etichette(intervento),
            "beneficiario": impresa,
            "intervento": intervento,
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
                 "carico dell'impresa. Stato e date sono quelli della data di estrazione. struttura, impresa "
                 "e tipi sono ricavati dal testo della fonte per leggerlo meglio; beneficiario e intervento "
                 "sono il testo originale.",
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
