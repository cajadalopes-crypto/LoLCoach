"""Entscheidungen zu Stufe 2 in werkzeuge/challenger/gehirn.py (Auftrag 032, Abschnitt 0):
Back nur mit Grund; Klarheit 'unklar' gibt die haeufigste High-Elo-Aktion (nie 'nichts').

Ohne echte Modelle: werte() wird durch feste Zahlen ersetzt, damit der Test genau die Regel prueft.
    python tests/makro/test_gehirn_korrektur.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "werkzeuge" / "challenger"))

import gehirn as gh  # noqa: E402

MERKMALE = ["leben_anteil", "rolle", "gold_tasche", "drache_bis", "baron_bis", "herold_bis", "larven_bis"]


class FestesHirn(gh.Gehirn):
    def __init__(self, q, p, schluessel=("Back", "Lane", "Gruppe")):
        self.schluessel = list(schluessel)
        self.merkmale = MERKMALE
        self.idx = {n: i for i, n in enumerate(MERKMALE)}
        self.schwellen = {"delta": 0.005, "p_klar": 0.15, "p_geteilt": 0.08}
        self._q, self._p = np.array(q, float), np.array(p, float)

    def werte(self, v):
        return self._q, self._p, np.full(len(self._q), 0.05)


def lage(leben=0.9, gold=100.0, drache_bis=300.0):
    return {"leben_anteil": leben, "rolle": 0, "gold_tasche": gold, "drache_bis": drache_bis, "baron_bis": 900,
            "herold_bis": -1, "larven_bis": -1}


def test_back_ohne_grund_rutscht():
    h = FestesHirn(q=[0.03, 0.01, 0.0], p=[0.5, 0.3, 0.2])            # Back klar vorn, aber kein Grund
    r = h.bewerte(lage(), mit_grund=False)
    assert r[0][0] == "Lane", r
    back = next(x for x in r if x[0] == "Back")
    assert "ohne Back-Grund" in back[6]


def test_back_mit_grund_bleibt():
    for l, grund in ((lage(leben=0.2), "Leben niedrig"), (lage(gold=1200), "Gold"), (lage(drache_bis=90), "Objective-Takt")):
        h = FestesHirn(q=[0.03, 0.01, 0.0], p=[0.5, 0.3, 0.2])
        r = h.bewerte(l, mit_grund=False)
        assert r[0][0] == "Back", (grund, r)
        assert any(grund in g for g in r[0][6]), (grund, r[0][6])


def test_back_grund_aus_kontext():
    h = FestesHirn(q=[0.03, 0.01, 0.0], p=[0.5, 0.3, 0.2])
    assert h.bewerte(lage(), mit_grund=False, kontext={"welle_gecrasht": True})[0][0] == "Back"
    assert h.bewerte(lage(), mit_grund=False, kontext={"lane_gegner_backt": True})[0][0] == "Back"
    assert h.bewerte(lage(gold=5000), mit_grund=False, kontext={"spike_fehlt": 300})[0][0] == "Lane"   # Kaufplan zaehlt vor Gold


def test_unklar_gibt_policy():
    # Werte fast gleich (unter delta), Policy klar bei Gruppe -> Gruppe zuerst, mit Hinweis; nie leer
    h = FestesHirn(q=[0.011, 0.012, 0.010], p=[0.05, 0.05, 0.9], schluessel=("Back", "Lane", "Gruppe"))
    r = h.bewerte(lage(), mit_grund=False)
    assert r and r[0][5] == "unklar" and r[0][0] == "Gruppe", r
    assert "am haeufigsten" in r[0][6][0]


def main() -> int:
    rot = 0
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            try:
                f()
                print(f"OK  {n}")
            except AssertionError as e:
                rot += 1
                print(f"ROT {n}: {e}")
    return 1 if rot else 0


if __name__ == "__main__":
    sys.exit(main())
