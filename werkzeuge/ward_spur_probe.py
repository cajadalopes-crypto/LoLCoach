"""Auftrag 033: Ward-Spur an ganzen Aufnahmen nachspielen (3-s-Takt wie live).

Erste Frage (30.09.): sind helle Y Carlos' Wards? Nein - nur 8 von 135 tauchten nahe seinem Icon auf. Zweite Frage:
erkennt man SEINE Wards an zwei unabhaengigen Zeichen - Ward taucht nahe seinem Icon auf (Setzreichweite 600 Einheiten
~ 0,04, dazu bis 3 s Takt) UND seine Trinket-Ladung faellt (Schirmbild davor/danach, sehen.trinket)?

    python werkzeuge/ward_spur_probe.py [stamm ...]      Ergebnis nach buecher/challenger/sehen/ward_spur.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "werkzeuge"))
import sehen_eichung as se  # noqa: E402
from lolcoach import sehen  # noqa: E402

TAKT = 3.0


def ich(stamm: str) -> str | None:
    a = se.api(stamm)
    if not a:
        return None
    d = a[len(a) // 2][1]
    rid = d["activePlayer"].get("riotId")
    for p in d["allPlayers"]:
        if p.get("riotId") == rid:
            return p.get("rawChampionName", "").rsplit("_", 1)[-1] or p["championName"]
    return None


def trinket_um(stamm: str, wand: float) -> tuple | None:
    """(Ladungen im letzten Schirmbild bis 8 s vor dem ersten Fund, im ersten bis 8 s danach)."""
    sch = se.schirme(stamm)
    vor = [p for w, p in sch if wand - 8 <= w <= wand - 0.5]
    nach = [p for w, p in sch if wand <= w <= wand + 8]
    if not vor or not nach:
        return None
    return sehen.trinket(se.lade_bgr(vor[-1])), sehen.trinket(se.lade_bgr(nach[0]))


def lauf(stamm: str) -> dict:
    mein = ich(stamm)
    sicht = se._sichtungen(stamm)
    ws = np.array([w for w, _ in sicht]) if sicht else np.array([])
    spur = sehen.Wardspur()
    naechst = 0.0
    gesetzt, weg = [], []
    for w, p in se.minimaps(stamm):
        if w < naechst:
            continue
        naechst = w + TAKT
        z = se.spielzeit(stamm, w)
        if z is None or z < 60:
            continue
        s = sicht[int(np.clip(np.searchsorted(ws, w) - 1, 0, len(ws) - 1))][1] if len(ws) else []
        champs = [(e[2], e[3]) for e in s]
        meine = [(e[2], e[3]) for e in s if e[0] == mein and e[4] > 0]
        karte = se.lade_bgr(p)
        for art, sw in spur.neu(w, sehen.wards(karte), champs, karte):
            if art == "gesetzt":
                # Abstand zum eigenen Icon beim ERSTEN Fund (sw.seit), nicht bei der Bestaetigung
                i0 = int(np.clip(np.searchsorted(ws, sw.seit) - 1, 0, len(ws) - 1)) if len(ws) else 0
                m0 = [(e[2], e[3]) for e in sicht[i0][1] if e[0] == mein and e[4] > 0] if len(ws) else []
                d = min((float(np.hypot(a - sw.x, b - sw.y)) for a, b in m0), default=None)
                gesetzt.append({"zeit": round(se.spielzeit(stamm, sw.seit) or 0), "art": sw.art, "x": sw.x, "y": sw.y,
                                "abstand_ich": None if d is None else round(d, 3),
                                "trinket": trinket_um(stamm, sw.seit)})
            else:
                weg.append({"zeit": round(z), "art": sw.art, "x": sw.x, "y": sw.y, "blass": sw.blass,
                            "stand_s": round(sw.zuletzt - sw.seit)})
        del meine
    return {"stamm": stamm, "ich": mein, "gesetzt": gesetzt, "weg": weg}


if __name__ == "__main__":
    staemme = sys.argv[1:] or [s for s in se.aufnahmen_mit_bildern() if se.api(s)][:4]
    out = [lauf(s) for s in staemme]
    ziel = se.ABLAGE / "ward_spur.json"
    ziel.write_text(json.dumps(out, indent=1), encoding="utf-8")
    for r in out:
        g = r["gesetzt"]
        nah = [x for x in g if x["abstand_ich"] is not None and x["abstand_ich"] <= 0.09]
        tr = [x for x in g if x["trinket"] and None not in x["trinket"]]
        faellt = [x for x in tr if x["trinket"][1] < x["trinket"][0]]
        beides = [x for x in faellt if x in nah]
        print(r["stamm"][-6:], r["ich"], "gesetzt", len(g), "nah", len(nah), "Trinket lesbar", len(tr), "faellt", len(faellt),
              "nah+faellt", len(beides), "nah ohne Fall", sum(1 for x in nah if x in tr and x not in faellt),
              "Fall ohne nah", sum(1 for x in faellt if x not in nah))
        print("   weg", len(r["weg"]), "Standzeit s", sorted(x["stand_s"] for x in r["weg"]))
