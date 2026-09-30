"""Auftrag 023, 1: stabile Messung - eingefrorene Soll-Listen, drei frische Kritiker je Partie, gezaehlt wird die
Mehrheit; wo sie fehlt (1-1-1 oder ein Urteil fehlt), liest ein vierter nur diese Punkte.

    python werkzeuge/kritik_mehrheit.py vorbereiten <runde> <protokoll-ordner> <stamm> ...
        -> Anweisungen <runde>/auftrag_<stamm>_<k>.txt (k = 1..3) fuer die Kritiker-Agenten
    python werkzeuge/kritik_mehrheit.py vierter <runde> <stamm> ...
        -> auftrag_<stamm>_4.txt mit nur den strittigen Punkten (leer, wenn keine)
    python werkzeuge/kritik_mehrheit.py auswerten <runde> <stamm> ...
        -> <runde>/mehrheit.json: je Partie gesagt/teilweise/fehlt, Quote, Uebereinstimmung, Fuellsaetze und
           Widersprueche (Median der drei)
Ablage: buecher/protokolle/proben/stratege_probe_023/<runde>/. Soll-Listen: buecher/protokolle/proben/soll_023/.
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
PROBEN = WURZEL / "buecher" / "protokolle" / "proben"
SOLL = PROBEN / "soll_023"
AUS = PROBEN / "stratege_probe_023"
URTEILE = ("gesagt", "teilweise", "fehlt")

AUFTRAG = """Du bist ein strenger, blinder Challenger-Kritiker fuer einen LoL-Echtzeit-Coach (Kritiker {k} von 3, du
kennst die anderen nicht). So wenig wie moeglich, so viel wie noetig; so schnell wie es nur geht; Tokensparsamkeit.
Keine Rueckfragen, schreib nur die Ausgabedatei.

Eingaben (nur lesen, sonst nichts):
- Soll-Liste: {soll}  (Format {{"minuten": {{"<Minute>": ["Soll-Aussage", ...]}}}})
- Protokoll des Coachs: {proto}  (alles Gesprochene mit Spielzeit; Zeilen "*Soll:*" darin IGNORIEREN)

Aufgabe:
1. Fuer JEDEN Soll-Punkt: hat der Coach es in dieser Minute oder bis etwa 30 s danach gesagt (Antworten auf Fragen
   zaehlen)? Urteil "gesagt", "teilweise" (Kern stimmt, ein Teil fehlt) oder "fehlt"; Grund hoechstens 12 Woerter mit
   Uhrzeit. Nur was inhaltlich dasselbe raet oder meldet, zaehlt.
2. Fuellsaetze: gesprochene Coach-Saetze ohne neue Info und ohne Handlung ("Notiert." zaehlt nicht). Zahl, Uhrzeiten,
   dazu die Zahl aller gesprochenen Coach-Saetze. Uebergaenge eines laufenden Auftrags sind KEINE Fuellsaetze, wenn
   sie eine neue Info oder Handlung enthalten: Countdown ("Noch 5 Sekunden."), Abbruch mit Grund ("Drache weg: nicht
   hin."), "Kampf vorbei" mit naechstem Ziel, "X kaempft: nicht hin" mit Grund. Nur leere Bestaetigungen zaehlen.
3. Widersprueche: zwei Coach-Saetze innerhalb von 30 s, die Gegenteiliges raten, ohne dass sich die Lage geaendert hat.
   Ein Planwechsel, der seinen Grund ausdruecklich nennt ("Jetzt, wo ...", "Stopp - ...", "Raus jetzt: X ist da"),
   oder eine Antwort auf eine Korrektur des Spielers ist KEIN Widerspruch. Zahl und Faelle (Uhrzeiten, je ein Stichwort).

Ausgabe (UTF-8): {aus}
{{"minuten": {{"<Minute>": [{{"soll": "...", "urteil": "gesagt|teilweise|fehlt", "grund": "..."}}]}}, "fuellsaetze":
{{"anzahl": n, "saetze_gesamt": n, "zeiten": [...]}}, "widersprueche": {{"anzahl": n, "faelle": [...]}}}}
Den Wortlaut jedes Soll-Punkts genau uebernehmen. Antworte am Ende nur mit einer Zeile: gesagt/teilweise/fehlt."""

VIERTER = """Du bist ein strenger, blinder Challenger-Kritiker fuer einen LoL-Echtzeit-Coach. So wenig wie moeglich, so viel
wie noetig; so schnell wie es nur geht; Tokensparsamkeit. Keine Rueckfragen.

Lies das Protokoll {proto} (Zeilen "*Soll:*" ignorieren) und beurteile NUR diese Soll-Punkte: hat der Coach es in der
genannten Minute oder bis etwa 30 s danach gesagt (Antworten zaehlen)? "gesagt", "teilweise" oder "fehlt", Grund
hoechstens 12 Woerter.
{punkte}
Ausgabe (UTF-8): {aus} als {{"urteile": [{{"minute": "...", "soll": "...", "urteil": "...", "grund": "..."}}]}}.
Antworte am Ende nur mit der Zahl der Urteile."""


def _soll(stamm: str) -> dict:
    return json.loads((SOLL / f"soll_{stamm}.json").read_text(encoding="utf-8"))["minuten"]


def vorbereiten(runde: str, proto: str, staemme: list[str]) -> None:
    d = AUS / runde
    d.mkdir(parents=True, exist_ok=True)
    for s in staemme:
        for k in (1, 2, 3):
            (d / f"auftrag_{s}_{k}.txt").write_text(AUFTRAG.format(
                k=k, soll=(SOLL / f"soll_{s}.json").as_posix(), proto=(Path(proto) / f"NACHSPIEL_{s}.md").as_posix(),
                aus=(d / f"kritik_{s}_{k}.json").as_posix()), encoding="utf-8")
        (d / "protokolle.txt").write_text(Path(proto).as_posix(), encoding="utf-8")
    print(d)


def _urteile(runde: str, s: str) -> list[dict]:
    """Je Kritiker: {(Minute, Soll): Urteil}."""
    aus = []
    for k in (1, 2, 3):
        f = AUS / runde / f"kritik_{s}_{k}.json"
        u = {}
        if f.exists():
            d = json.loads(f.read_text(encoding="utf-8"))
            for mi, xs in d.get("minuten", {}).items():
                for x in xs:
                    if x.get("urteil") in URTEILE:
                        u[(str(mi), x["soll"].strip())] = x["urteil"]
            u["_d"] = d
        aus.append(u)
    return aus


def _mehrheit(stimmen: list[str]) -> str | None:
    c = Counter(stimmen)
    w, n = c.most_common(1)[0] if c else (None, 0)
    return w if n >= 2 else None


def vierter(runde: str, staemme: list[str]) -> None:
    proto = (AUS / runde / "protokolle.txt").read_text(encoding="utf-8")
    for s in staemme:
        u = _urteile(runde, s)
        offen = [(mi, soll) for mi, xs in _soll(s).items() for soll in xs
                 if _mehrheit([x[(str(mi), soll.strip())] for x in u if (str(mi), soll.strip()) in x]) is None]
        f = AUS / runde / f"auftrag_{s}_4.txt"
        if not offen:
            f.unlink(missing_ok=True)
            print(s, "keine strittigen Punkte")
            continue
        punkte = "\n".join(f"- Minute {mi}: {soll}" for mi, soll in offen)
        f.write_text(VIERTER.format(proto=f"{proto}/NACHSPIEL_{s}.md", punkte=punkte,
                                    aus=(AUS / runde / f"kritik_{s}_4.json").as_posix()), encoding="utf-8")
        print(s, len(offen), "strittig ->", f)


def auswerten(runde: str, staemme: list[str]) -> dict:
    erg = {}
    for s in staemme:
        u = _urteile(runde, s)
        f4 = AUS / runde / f"kritik_{s}_4.json"
        vier = {}
        if f4.exists():
            for x in json.loads(f4.read_text(encoding="utf-8")).get("urteile", []):
                vier[(str(x["minute"]), x["soll"].strip())] = x["urteil"]
        zaehl, einig, zwei, strittig = Counter(), 0, 0, 0
        for mi, xs in _soll(s).items():
            for soll in xs:
                key = (str(mi), soll.strip())
                st = [x[key] for x in u if key in x]
                w = _mehrheit(st)
                if len(st) == 3 and len(set(st)) == 1:
                    einig += 1
                elif w is not None:
                    zwei += 1
                if w is None:
                    strittig += 1
                    w = vier.get(key) or (Counter(st).most_common(1)[0][0] if st else "fehlt")
                zaehl[w] += 1
        n = sum(zaehl.values())
        ds = [x["_d"] for x in u if "_d" in x]
        fs = [d.get("fuellsaetze", {}).get("anzahl", 0) for d in ds]
        ng = [d.get("fuellsaetze", {}).get("saetze_gesamt", 0) for d in ds]
        wi = [d.get("widersprueche", {}).get("anzahl", 0) for d in ds]
        erg[s] = {"punkte": n, **{k: zaehl[k] for k in URTEILE},
                  "quote": round((zaehl["gesagt"] + zaehl["teilweise"]) / max(1, n), 4),
                  "einig_3": einig, "mehrheit_2": zwei, "strittig": strittig,
                  "fuellsaetze": statistics.median(fs) if fs else None,
                  "saetze": statistics.median(ng) if ng else None,
                  "widersprueche": statistics.median(wi) if wi else None, "kritiker": len(ds)}
    gesamt = {k: sum(e[k] for e in erg.values()) for k in ("punkte", *URTEILE, "einig_3", "mehrheit_2", "strittig")}
    gesamt["quote"] = round((gesamt["gesagt"] + gesamt["teilweise"]) / max(1, gesamt["punkte"]), 4)
    ziel = AUS / runde / "mehrheit.json"
    alt = json.loads(ziel.read_text(encoding="utf-8")) if ziel.exists() else {}
    alt.update(erg)
    alt["_gesamt_" + "_".join(sorted(x[-6:] for x in staemme))] = gesamt
    ziel.write_text(json.dumps(alt, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({**erg, "gesamt": gesamt}, ensure_ascii=False, indent=1))
    return erg


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    was = sys.argv[1]
    if was == "vorbereiten":
        vorbereiten(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif was == "vierter":
        vierter(sys.argv[2], sys.argv[3:])
    else:
        auswerten(sys.argv[2], sys.argv[3:])
