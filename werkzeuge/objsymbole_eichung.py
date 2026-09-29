"""Auftrag 018, 1: die Objective-Symbole der Minimap gegen die Wahrheit aus den API-Ereignissen eichen und pruefen.

Je Aufnahme mit Minimap-Bildern: nachspielen (nur Kern), je Bild die Merkmale der zwei Gruben (lolcoach.objsymbole)
und die Wahrheit aus dem Objective-Modell des Kerns (Spawn-Regeln + API-Ereignisse) zur Spielzeit des Bildes.
Ausgabe: stratege_probe_018/objsymbole.json.gz und die Trefferquote je Grube und Zustand.

    python werkzeuge/objsymbole_eichung.py [--neu] [--eichen]
"""
from __future__ import annotations

import bisect
import gzip
import itertools
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(HIER.parent))
AUS = HIER.parent / "buecher" / "protokolle" / "proben" / "stratege_probe_018"
OBEN = ("larven", "herold", "baron")
UNTEN = ("drache", "aeltester")


def eine(stamm: str) -> dict:
    import numpy as np
    from PIL import Image
    import nachspielen as ns
    from lolcoach import objsymbole
    stand = []                                            # (wand, zeit, {schl: (lebt, spawn_in)})

    def bt(p, werk, kern, plan):
        m = kern.m
        if m is None or not p.ich:
            return
        if not stand or p.zeit - stand[-1][1] >= 0.5:
            stand.append((werk_wand[0], p.zeit, {o.schl: (bool(o.lebt), o.spawn_in) for o in m.objectives or []}))
    werk_wand = [0.0]
    import nachspielen
    alt = nachspielen.aufzeichnung.lies_mit_zeit

    def mit_wand(pfad):
        for w, d in alt(pfad):
            werk_wand[0] = w
            yield w, d
    nachspielen.aufzeichnung.lies_mit_zeit = mit_wand
    ns.durchspielen(ns.pfad_zu(stamm), beim_takt=bt)
    nachspielen.aufzeichnung.lies_mit_zeit = alt
    ordner = ns.AUFNAHMEN / f"{stamm}_bilder"
    wand = [s[0] for s in stand]
    aus = []
    for f in sorted(ordner.glob("*.jpg")):
        if not f.stem.isdigit():
            continue
        w = int(f.stem) / 1000
        i = bisect.bisect_left(wand, w)
        if i >= len(stand) or abs(stand[i][0] - w) > 1.5:
            continue
        _, zeit, obj = stand[i]
        karte = np.asarray(Image.open(f).convert("RGB"))
        wahr_oben = "symbol" if any(obj.get(s, (False, 0))[0] for s in OBEN) else \
            "timer" if any(not obj.get(s, (True, 0))[0] and (obj.get(s, (True, 999))[1] or 999) <= 60 for s in OBEN
                           if s in obj) else "leer"
        wahr_unten = "symbol" if any(obj.get(s, (False, 0))[0] for s in UNTEN) else "sonst"
        aus.append({"zeit": round(zeit, 1), "bild": f.stem, "wahr": {"oben": wahr_oben, "unten": wahr_unten},
                    "m": {g: objsymbole.merkmale(karte, g) for g in objsymbole.GRUBEN}})
    return {"stamm": stamm, "bilder": aus}


def quote(alle: list, schwellen: dict | None = None) -> dict:
    from lolcoach import objsymbole
    erg = {}
    for g in ("oben", "unten"):
        n = t = verdeckt = 0
        falsch_symbol = falsch_leer = 0
        for r in alle:
            for b in r["bilder"]:
                u = objsymbole.urteil(g, b["m"][g], schwellen)
                w = b["wahr"][g]
                if u == "verdeckt":
                    verdeckt += 1
                    continue
                n += 1
                lebt_u, lebt_w = u == "symbol", w == "symbol"
                t += lebt_u == lebt_w
                falsch_symbol += lebt_u and not lebt_w
                falsch_leer += lebt_w and not lebt_u
        erg[g] = {"bilder": n, "treffer": round(t / max(1, n), 4), "symbol_ohne_objective": falsch_symbol,
                  "objective_ohne_symbol": falsch_leer, "verdeckt": verdeckt}
    return erg


def eichen(alle: list) -> dict:
    """Schwellen je Merkmal auf einem Raster; bestes Mittel der beiden Gruben."""
    from lolcoach import objsymbole
    best = (0.0, None)
    for lila in (0.005, 0.01, 0.02, 0.03):
        for hell in (0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05):
            for ring, weiss in itertools.product((0.02, 0.03, 0.05, 1.0), (0.02, 0.04, 0.06, 0.08, 0.1)):
                s = dict(objsymbole.SCHWELLEN, lila=lila, hell=hell, ring=ring, weiss=weiss)
                q = quote(alle, s)
                wert = (q["oben"]["treffer"] + q["unten"]["treffer"]) / 2
                if wert > best[0]:
                    best = (wert, s)
    return best[1]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    import nachspielen as ns
    datei = AUS / "objsymbole.json.gz"
    if "--neu" in sys.argv or not datei.exists():
        staemme = [d.name.removesuffix("_bilder") for d in sorted(ns.AUFNAHMEN.glob("*_bilder"))
                   if sum(1 for _ in d.glob("1*.jpg")) > 100]
        with ProcessPoolExecutor(len(staemme)) as ex:
            alle = list(ex.map(eine, staemme))
        AUS.mkdir(exist_ok=True)
        with gzip.open(datei, "wt", encoding="utf-8") as f:
            json.dump(alle, f)
    with gzip.open(datei, "rt", encoding="utf-8") as f:
        alle = json.load(f)
    print("jetzt", json.dumps(quote(alle)))
    if "--eichen" in sys.argv:
        s = eichen(alle)
        print("geeicht", s, json.dumps(quote(alle, s)))


if __name__ == "__main__":
    main()
