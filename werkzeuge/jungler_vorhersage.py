"""Auftrag 017, 1.1 (Buch 13, I2): trifft eine Jungler-Vorhersage die naechste Sichtung? An allen Aufnahmen.

Je Aufnahme: in jeder Episode, in der ihr Jungler >= 45 s ungesehen ist (frueh im Spiel, bis VORHERSAGE_BIS), hoechstens
einmal je 60 s eine Vorhersage je Verfahren; Wahrheit ist die Kartenseite der naechsten Sichtung in <= 60 s (ohne
Sichtung zaehlt die Vorhersage nicht). Verfahren:
  W  jungle.Jungletracker.wahrscheinlich (Seite mit p >= 0,65)
  A  die andere Seite als bei der letzten Sichtung
  G  dieselbe Seite wie bei der letzten Sichtung

    python werkzeuge/jungler_vorhersage.py            # alle Aufnahmen, 8 parallel -> stratege_probe_017/jungler.json
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(HIER.parent))

OHNE_S = 45.0
ABSTAND_S = 60.0
WAHRHEIT_S = 60.0
VORHERSAGE_BIS = 600.0
P_MIN = 0.65


def eine(stamm: str) -> dict:
    import nachspielen as ns
    from lolcoach import aufzeichnung
    from lolcoach.jungle import anders, seite
    vorher: list = []            # (Zeit, {Verfahren: Seite})
    letzte = {"t": -1e9}

    def beim_takt(p, werk, kern, plan):
        lb = getattr(kern, "_lagebild", None)
        jt = getattr(lb, "jungle", None)
        if jt is None or not p.ich or p.zeit > VORHERSAGE_BIS + WAHRHEIT_S:
            return
        z = jt.zuletzt()
        j = p.jungler(__import__("lolcoach.zustand", fromlist=["gegenteam"]).gegenteam(p.mein_team))
        if j is None or j.tot or z is None or p.zeit > VORHERSAGE_BIS:
            return
        ohne = p.zeit - z[0]
        if ohne < OHNE_S or p.zeit - letzte["t"] < ABSTAND_S:
            return
        letzte["t"] = p.zeit
        w = jt.wahrscheinlich(p.zeit)
        s, pw = max(w.items(), key=lambda x: x[1])
        zuletzt = seite(z[1], z[2])
        vorher.append((p.zeit, {"W": s if pw >= P_MIN else None, "A": anders(zuletzt), "G": zuletzt},
                       list(jt.sichtungen)))

    lauf = ns.durchspielen(ns.pfad_zu(stamm), beim_takt=beim_takt)
    jt = getattr(getattr(lauf.kern, "_lagebild", None), "jungle", None)
    sicht = list(jt.sichtungen) if jt is not None else []
    from lolcoach.jungle import seite as _seite
    aus = []
    for t, v, _ in vorher:
        naechste = next(((st, _seite(x, y)) for st, x, y in sicht if t < st <= t + WAHRHEIT_S), None)
        if naechste is None:
            continue
        aus.append({"zeit": round(t), "wahr": naechste[1], **{k: s for k, s in v.items()}})
    return {"stamm": stamm, "vorhersagen": aus}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    import nachspielen as ns
    staemme = [p.name.removesuffix(".jsonl.gz") for p in aufzeichnung.alle(ns.AUFNAHMEN)]
    alle = []
    with ProcessPoolExecutor(8) as ex:
        for r in ex.map(eine, staemme):
            alle.append(r)
            print(r["stamm"], len(r["vorhersagen"]), flush=True)
    quote = {}
    for k in ("W", "A", "G"):
        n = [x for r in alle for x in r["vorhersagen"] if x.get(k)]
        quote[k] = {"n": len(n), "treffer": sum(1 for x in n if x[k] == x["wahr"])}
        quote[k]["quote"] = round(quote[k]["treffer"] / len(n), 3) if n else None
    ziel = HIER.parent / "buecher" / "protokolle" / "proben" / "stratege_probe_017" / "jungler.json"
    ziel.parent.mkdir(exist_ok=True)
    ziel.write_text(json.dumps({"quote": quote, "aufnahmen": alle}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("QUOTE", json.dumps(quote), flush=True)


if __name__ == "__main__":
    main()
