"""Back-Test (Buch 7, Nebenbefund): aendern sich die API-Items eines Gegners, waehrend er unsichtbar ist (Back, den
man nicht sieht), oder erst, wenn er wieder sichtbar wird?

Je Aufnahme das Nachspielen (nachspielen.durchspielen), je Takt je Gegner: Item-Gold und Level der Live-API,
sichtbar/seit aus der Bewertung (GegnerLage). Jede Aenderung wird nach dem Zustand im Takt der Aenderung eingeordnet:
  tot         - der Gegner ist tot (oder war es im Takt davor)
  nebel       - lebt, unsichtbar, und die naechste Sichtung ist > NAH_S entfernt (oder kommt nie)
  vor_sicht   - lebt, unsichtbar, naechste Sichtung <= NAH_S danach (Minimap erkennt ihn spaeter als die API)
  auftauchen  - sichtbar seit <= NAH_S, davor >= WEG_MIN_S unsichtbar
  sichtbar    - sichtbar, schon laenger (oder nur kurz weg)
  nie         - noch nie gesehen (seit None)

--proben <kampf_eichung --json>: je entschiedener Probe, ob ein naher Gegner mit veraltetem Item-Stand einging (sein
Item-Gold steigt in den 15 s nach der Probe, lebend) und ob er frisch aus dem Nebel kam (sichtbar seit <= 5 s, davor
>= 20 s ungesehen) - getrennt nach gewonnen / verloren.

    python werkzeuge/back_test.py 2026-09-27_133930 2026-09-27_140253 ... [--beispiele 6] [--proben <datei>]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import nachspielen as ns  # noqa: E402

from lolcoach import ddragon  # noqa: E402

NAH_S = 3.0
WEG_MIN_S = 5.0
ARTEN = ("tot", "nebel", "vor_sicht", "auftauchen", "sichtbar", "nie")


def reihen(stamm: str) -> dict[str, list[tuple]]:
    """Gegner -> [(zeit, item_gold, level, sichtbar, seit, tot, items)] je Takt."""
    aus: dict[str, list[tuple]] = defaultdict(list)

    def beim_takt(p, werk, kern, plan):
        b = werk.b
        if b is None:
            return
        for g in b.gegner:
            aus[g.champion].append((p.zeit, g.s.item_gold, g.s.level, g.sichtbar, g.seit, g.s.tot, g.s.items))

    ns.durchspielen(ns.pfad_zu(stamm), beim_takt=beim_takt)
    return aus


def einordnen(r: list[tuple], i: int) -> tuple[str, str]:
    z, _, _, vis, seit, tot, _ = r[i]
    if tot or r[i - 1][5]:
        return "tot", ""
    if seit is None:
        return "nie", ""
    if not vis:
        nxt = next((x[0] for x in r[i + 1:] if x[3]), None)
        bis = None if nxt is None else nxt - z
        art = "vor_sicht" if bis is not None and bis <= NAH_S else "nebel"
        return art, f"seit {seit:.0f} s ungesehen, wieder sichtbar " + ("nie" if bis is None else f"in {bis:.0f} s")
    j = i
    while j > 0 and r[j - 1][3]:
        j -= 1
    sichtbar_seit = z - r[j][0]
    k = j - 1
    while k > 0 and not r[k - 1][3]:
        k -= 1
    weg = r[j][0] - r[k][0] if j > 0 and not r[j - 1][3] else 0.0
    if sichtbar_seit <= NAH_S and weg >= WEG_MIN_S:
        return "auftauchen", f"sichtbar seit {sichtbar_seit:.0f} s, davor {weg:.0f} s weg"
    return "sichtbar", f"sichtbar seit {sichtbar_seit:.0f} s"


def name(i: int) -> str:
    return ddragon.items().get(i, {}).get("name", str(i))


def proben_pruefen(pfad: str, serien: dict) -> None:
    daten = json.loads(Path(pfad).read_text(encoding="utf-8"))
    daten = daten["proben"] if isinstance(daten, dict) else daten
    zaehl, faelle = Counter(), []
    for pr in daten:
        if pr["ausgang"] is None or pr["stamm"] not in serien:
            continue
        t0, aus = pr["zeit"], "gewonnen" if pr["ausgang"] else "verloren"
        veraltet, nebel = [], []
        for ch in pr["gegner"]:
            vor = [x for x in serien[pr["stamm"]].get(ch, []) if x[0] <= t0]
            if not vor:
                continue
            nach = [x for x in serien[pr["stamm"]][ch] if t0 < x[0] <= t0 + 15.0 and not x[5]]
            if any(x[1] > vor[-1][1] for x in nach):
                veraltet.append(f"{ch} {vor[-1][1]} -> {max(x[1] for x in nach)}")
            j = len(vor) - 1
            while j > 0 and vor[j - 1][3]:
                j -= 1
            k = j - 1
            while k > 0 and not vor[k - 1][3]:
                k -= 1
            if vor[-1][3] and j > 0 and t0 - vor[j][0] <= 5.0 and vor[j][0] - vor[k][0] >= 20.0:
                nebel.append(ch)
        zaehl[aus] += 1
        zaehl[aus, "veraltet"] += bool(veraltet)
        zaehl[aus, "nebel"] += bool(nebel)
        if veraltet or nebel:
            faelle.append(f"{pr['stamm'][-6:]} {ns.uhr(t0)} {aus}, gold_diff {pr.get('gold_diff') or 0:+.0f}: "
                          f"veraltet [{'; '.join(veraltet)}] aus dem Nebel [{', '.join(nebel)}]")
    print("Entschiedene Proben: naher Gegner mit veraltetem Item-Stand / frisch aus dem Nebel")
    for aus in ("gewonnen", "verloren"):
        print(f"  {aus:9}: {zaehl[aus]} Proben, veraltet {zaehl[aus, 'veraltet']}, aus dem Nebel {zaehl[aus, 'nebel']}")
    for z in faelle:
        print("  " + z)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("aufnahmen", nargs="+")
    ap.add_argument("--beispiele", type=int, default=6)
    ap.add_argument("--proben", help="kampf_eichung --json: Item-Stand der nahen Gegner an den entschiedenen Proben")
    a = ap.parse_args()
    zaehl = {"gold": Counter(), "gold+": Counter(), "level": Counter()}
    beispiele = defaultdict(list)
    serien = {}
    for stamm in a.aufnahmen:
        serien[stamm] = reihen(stamm)
        for champ, r in serien[stamm].items():
            for i in range(1, len(r)):
                dg, dl = r[i][1] - r[i - 1][1], r[i][2] - r[i - 1][2]
                if not dg and not dl:
                    continue
                art, info = einordnen(r, i)
                if dl:
                    zaehl["level"][art] += 1
                if dg:
                    zaehl["gold"][art] += 1
                    if dg > 0:
                        zaehl["gold+"][art] += 1
                    neu = Counter(r[i][6]) - Counter(r[i - 1][6])
                    beispiele[art].append(f"{stamm[-6:]} {ns.uhr(r[i][0])} {champ}: {dg:+d} Gold "
                                          f"({', '.join(name(x) for x in neu.elements()) or '-'}); {info}")
    print(f"Aenderungen je Einordnung (NAH_S {NAH_S:.0f} s, WEG_MIN_S {WEG_MIN_S:.0f} s):")
    print(f"  {'':10}" + "".join(f"{x:>11}" for x in ARTEN) + f"{'gesamt':>9}")
    for k, t in (("gold", "Item-Gold"), ("gold+", "davon +"), ("level", "Level")):
        print(f"  {t:10}" + "".join(f"{zaehl[k][x]:>11}" for x in ARTEN) + f"{sum(zaehl[k].values()):>9}")
    for art in ARTEN:
        if beispiele[art]:
            print(f"Beispiele {art} ({len(beispiele[art])}):")
            for z in beispiele[art][:a.beispiele]:
                print("  " + z)
    if a.proben:
        proben_pruefen(a.proben, serien)


if __name__ == "__main__":
    main()
