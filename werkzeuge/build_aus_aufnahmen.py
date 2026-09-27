"""Carlos' eigener Build je Champion - aus seinen Aufnahmen, nicht aus dem Lexikon (Pruefung 27.09.c, R3).

Je Partie: seine fertigen Items (keine Bauteile, keine Stiefel, keine Verbrauchsgueter, kein Schmuckstueck) in der
Reihenfolge ihres ersten Auftauchens. Uebungsmodus zaehlt nicht (dort wird zum Ausprobieren gekauft: 001155 hatte
fuenf Items in Minute 8).

Daraus je Champion die Schritte:
- Gleichwertige Items werden EIN Schritt ("Gefraessige oder Gottlose Hydra", "Eklipse oder Endloser Hunger"):
  dieselbe Gruppe (kaufplan.gruppe: nur eine Hydra, nur ein Letztes Fluestern) oder dasselbe Rezept (Eklipse und
  Endloser Hunger: Caulfields + Spitzhacke + Langschwert), und hoechstens in einem Viertel der Partien zusammen im
  Inventar. Jedes Paar eines Schritts muss das erfuellen. (Ein gemeinsames Bauteil allein reicht NICHT - Caulfields
  steckt in der halben Liste, erster Versuch warf Gefraessige Hydra und Gespaltenen Himmel zusammen.)
- Die Reihenfolge der Schritte: paarweise Mehrheit (in wie vielen Partien kam A vor B - Copeland), bei Gleichstand
  die mittlere Position. Das ist die haeufigste Reihenfolge, auch wenn keine zwei Partien ganz gleich waren.
- Ein Schritt braucht mindestens zwei Partien (bei nur einer Partie: eine).
Stiefel stehen gesondert (die haeufigsten).

    python werkzeuge/build_aus_aufnahmen.py            -> schreibt wissen/build_carlos.toml
    python werkzeuge/build_aus_aufnahmen.py --zeigen   -> nur zeigen
"""
from __future__ import annotations

import datetime
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
from lolcoach import aufzeichnung, ddragon, kaufplan, zustand  # noqa: E402

ZIEL = WURZEL / "wissen" / "build_carlos.toml"
NICHT = {"PRACTICETOOL", "TUTORIAL"}
ZUSAMMEN_HOECHSTENS = 0.25


def _fertig(i: int, it: dict) -> bool:
    e = it.get(i)
    if not e or i >= 100000 or {"Boots", "Trinket", "Consumable"} & set(e.get("tags", [])):
        return False
    return not e.get("into") and bool(e.get("from"))


def partie_lesen(pfad: Path, it: dict) -> tuple[str, str, list[int], Counter] | None:
    """(Champion, Modus, fertige Items in Reihenfolge, Stiefel-Zaehler) - None ohne eigenen Spieler."""
    folge, stiefel, champ, modus = [], Counter(), None, None
    for n, (_, d) in enumerate(aufzeichnung.lies_mit_zeit(pfad)):
        if n % 10:
            continue          # jede zehnte Zeile reicht: ein Item liegt Sekunden bis Minuten im Inventar
        p = zustand.partie(d)
        if p.ich is None:
            continue
        champ, modus = p.ich.champion_id, p.modus
        for i in p.ich.items:
            if _fertig(i, it) and i not in folge:
                folge.append(i)
            elif "Boots" in it.get(i, {}).get("tags", []) and it[i].get("from"):
                stiefel[i] += 1
    return (champ, modus, folge, stiefel) if champ else None


def _ersetzbar(a: int, b: int, it: dict) -> bool:
    """Dieselbe Gruppe (nur eins davon geht) oder dasselbe Rezept."""
    ga = kaufplan.gruppe(a)
    return (ga is not None and ga == kaufplan.gruppe(b)) or sorted(it[a].get("from") or []) == sorted(it[b].get("from") or [])


def schritte(partien: list[list[int]], it: dict) -> list[tuple[list[int], int]]:
    """[(Alternativen - haeufigste zuerst, Anzahl Partien)] in der haeufigsten Reihenfolge."""
    anzahl = Counter(i for f in partien for i in f)
    zusammen = Counter((a, b) for f in partien for a in f for b in f if a < b)
    gruppe = {i: {i} for i in anzahl}

    def gleichwertig(a, b):
        return _ersetzbar(a, b, it) and zusammen[min(a, b), max(a, b)] <= ZUSAMMEN_HOECHSTENS * min(anzahl[a], anzahl[b])

    paare = sorted(((zusammen[min(a, b), max(a, b)] / min(anzahl[a], anzahl[b]), -(anzahl[a] + anzahl[b]), a, b)
                    for a in anzahl for b in anzahl if a < b))
    for _, _, a, b in paare:
        ga, gb = gruppe[a], gruppe[b]
        if ga is not gb and all(gleichwertig(x, y) for x in ga for y in gb):
            neu = ga | gb
            for x in neu:
                gruppe[x] = neu
    liste = []
    for g in {id(g): g for g in gruppe.values()}.values():
        alt = sorted(g, key=lambda i: (-anzahl[i], i))
        pos = [min(f.index(i) for i in g if i in f) for f in partien if g & set(f)]
        if len(pos) >= min(2, len(partien)):
            liste.append((alt, pos, g))

    def erster(g, f):
        return min((f.index(i) for i in g if i in f), default=None)

    def punkte(s):
        p = 0.0
        for t in liste:
            if t is s:
                continue
            vor = nach = 0
            for f in partien:
                a, b = erster(s[2], f), erster(t[2], f)
                if a is not None and b is not None:
                    vor, nach = vor + (a < b), nach + (a > b)
            p += 1.0 if vor > nach else 0.5 if vor == nach else 0.0
        return p

    wert = {id(s): punkte(s) for s in liste}     # vorher: waehrend sort() ist die Liste fuer den Schluessel leer
    liste.sort(key=lambda s: (-wert[id(s)], sum(s[1]) / len(s[1])))
    return [(alt, len(pos)) for alt, pos, _ in liste]


def ableiten(pfade: list[Path]) -> dict[str, dict]:
    it = ddragon.items()
    je = defaultdict(lambda: {"partien": [], "aufnahmen": [], "stiefel": Counter()})
    for pfad in pfade:
        r = partie_lesen(pfad, it)
        if r is None or r[1] in NICHT or not r[2]:
            continue
        champ, _, folge, stiefel = r
        je[champ]["partien"].append(folge)
        je[champ]["aufnahmen"].append(pfad.name.removesuffix(".jsonl.gz"))
        je[champ]["stiefel"].update(stiefel)
    aus = {}
    for champ, d in sorted(je.items()):
        s = schritte(d["partien"], it)
        if not s:
            continue
        aus[champ] = {
            "partien": len(d["partien"]),
            "aufnahmen": d["aufnahmen"],
            "stiefel": it[d["stiefel"].most_common(1)[0][0]]["name"] if d["stiefel"] else "",
            "folge": [[it[i]["name"] for i in alt] for alt, _ in s],
            "belege": [n for _, n in s],
        }
    return aus


def toml_text(aus: dict[str, dict]) -> str:
    q = lambda s: json.dumps(s, ensure_ascii=False)   # noqa: E731 - TOML-Zeichenkette = JSON-Zeichenkette
    zeilen = ["# Carlos' eigener Build je Champion - aus seinen Aufnahmen abgeleitet, NICHT von Hand pflegen:",
              "#     python werkzeuge/build_aus_aufnahmen.py",
              "# folge: Schritte in der haeufigsten Reihenfolge; ein Schritt = gleichwertige Items (haeufigstes zuerst),",
              "# belege: in wie vielen Partien der Schritt vorkam. Genutzt von lolcoach/kaufplan.py (vor dem Lexikon).",
              f"stand = {q(datetime.date.today().isoformat())}", ""]
    for champ, d in aus.items():
        zeilen += [f"[{champ}]",
                   "quelle = " + q(str(d["partien"]) + " Partien ohne Uebungsmodus, aufnahmen/*.jsonl.gz"),
                   f"partien = {d['partien']}",
                   "aufnahmen = [" + ", ".join(q(a) for a in d["aufnahmen"]) + "]",
                   f"stiefel = {q(d['stiefel'])}",
                   "folge = [" + ", ".join("[" + ", ".join(q(n) for n in alt) + "]" for alt in d["folge"]) + "]",
                   "belege = [" + ", ".join(str(n) for n in d["belege"]) + "]", ""]
    return "\n".join(zeilen)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ergebnis = ableiten(sorted((WURZEL / "aufnahmen").glob("*.jsonl.gz")))
    text = toml_text(ergebnis)
    print(text)
    if "--zeigen" not in sys.argv:
        ZIEL.write_text(text, encoding="utf-8")
        print(f"-> {ZIEL}")
