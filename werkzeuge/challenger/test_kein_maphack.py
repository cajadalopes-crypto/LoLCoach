"""Auftrag 030, Pruefung "kein Maphack": keine Gegnerposition kommt in eine Lage, ausser tot, zuletzt gesehen (angesagtes
Ereignis) oder der Lane-Gegner nahe sichtbar (<= 1200).

    python werkzeuge/challenger/test_kein_maphack.py [anzahl_partien]

Verfahren: dieselbe Partie zweimal bauen - einmal echt, einmal mit ZUFAELLIGEN Minutenpositionen fuer ein Team. Aus
Sicht des anderen Teams muss jede Lage-Spalte gleich bleiben, ausser lg_nahe_sichtbar/lg_x/lg_y; und dort darf ein
Wert nur stehen, wenn der (verschobene) Lane-Gegner wirklich <= 1200 neben dem Spieler steht. Gegenprobe gegen einen
leeren Test: die Verschiebung muss bei den lg-Spalten tatsaechlich ankommen (sonst beweist der Test nichts).
"""
from __future__ import annotations

import json
import sys

import numpy as np

import grundlage as g
import phase1 as f

ERLAUBT = {f.SP["lg_nahe_sichtbar"], f.SP["lg_x"], f.SP["lg_y"]}


def pruefe_partie(mid: str, rnd: np.random.Generator) -> dict:
    p = g.Partie(g.lade(mid))
    R = f.Raster(p)
    out = {"momente": 0, "verletzt": 0, "lg_geaendert": 0, "lg_zu_weit": 0}
    for fremd in (0, 1):                               # dieses Team bekommt Zufallspositionen
        falsch = np.full((11, len(p.frames), 2), np.nan)
        for q in range(1, 11):
            if R.team[q] == fremd:
                falsch[q] = rnd.uniform(0, 14800, (len(p.frames), 2))
        R2 = f.Raster(p, spiegel_gegner=falsch)
        for pid in range(1, 11):
            if R.team[pid] == fremd:
                continue
            sek = np.array([s for s, _ in f.zeitpunkte(R, pid)], np.int64)
            a, b = f.lage(R, pid, sek), f.lage(R2, pid, sek)
            gleich = (a == b) | (np.isnan(a) & np.isnan(b))
            andere = [j for j in range(a.shape[1]) if j not in ERLAUBT]
            out["momente"] += len(sek)
            out["verletzt"] += int((~gleich[:, andere]).any(1).sum())
            out["lg_geaendert"] += int((~gleich[:, sorted(ERLAUBT)]).any(1).sum())
            # wo ein Lane-Gegner-Ort steht, muss er <= 1200 neben dem Spieler sein
            for X in (a, b):
                m = ~np.isnan(X[:, f.SP["lg_x"]])
                d = np.hypot(X[m, f.SP["lg_x"]] - X[m, f.SP["x"]], X[m, f.SP["lg_y"]] - X[m, f.SP["y"]])
                out["lg_zu_weit"] += int((d > f.NAHE_SICHTBAR + 1e-3).sum())
    return out


def main(n: int = 30) -> dict:
    gueltig = json.loads((g.ABLAGE / "gueltig.json").read_text(encoding="utf-8"))
    rnd = np.random.default_rng(30)
    summe = {"momente": 0, "verletzt": 0, "lg_geaendert": 0, "lg_zu_weit": 0}
    for mid in rnd.choice(gueltig, n, replace=False):
        for k, v in pruefe_partie(str(mid), rnd).items():
            summe[k] += v
    summe["partien"] = n
    summe["bestanden"] = summe["verletzt"] == 0 and summe["lg_zu_weit"] == 0 and summe["lg_geaendert"] > 0
    return summe


def sabotage(n: int = 5) -> dict:
    """Gegenprobe gegen einen blinden Test: schreibt die Minutenposition des gegnerischen Junglers in eine Spalte -
    der Test MUSS dann durchfallen."""
    alt = f.lage

    def leck(R, pid, sek):
        X = alt(R, pid, sek)
        q = next(q for q in range(1, 11) if R.team[q] != R.team[pid] and R.p.rolle(q) == "JUNGLE")
        X[:, f.SP["geg1_gesehen_x"]] = R.x[q, sek]
        return X
    f.lage = leck
    try:
        return main(n)
    finally:
        f.lage = alt


if __name__ == "__main__":
    r = main(int(sys.argv[1]) if len(sys.argv) > 1 else 30)
    s = sabotage()
    print(r)
    print("Sabotage (muss durchfallen):", s)
    sys.exit(0 if r["bestanden"] and not s["bestanden"] else 1)
