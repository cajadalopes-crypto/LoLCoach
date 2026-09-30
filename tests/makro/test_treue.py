"""Auftrag 035, Teil 2: das Werkzeug der Challenger-Treue (werkzeuge/challenger/treue.py) - ohne die Riot-Daten,
ohne Modelle: konstruierte Momente (Zeilen wie phase1), feste Modellwerte, bekannte Antworten.

    python tests/makro/test_treue.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from types import SimpleNamespace

HIER = Path(__file__).resolve().parent
WZ = HIER.parents[1] / "werkzeuge" / "challenger"
sys.path.insert(0, str(WZ))
sys.path.insert(0, str(HIER.parents[1]))

import numpy as np  # noqa: E402

import gehirn as gh  # noqa: E402
import modelle as mo  # noqa: E402
import phase1 as f  # noqa: E402
import treue  # noqa: E402

KEYS = ["Back", "Lane", "Objective:Drache", "Rotation:mid", "Split"]


def zeile(**werte) -> np.ndarray:
    """Eine X-Zeile (phase1.NAMEN): Top-Laner, 10:00, blau, in der Lane, alle Gegner tot=0, nie gesehen."""
    x = np.full(len(f.NAMEN), np.nan, np.float32)
    grund = {"minute": 10.0, "x": 1500.0, "y": 12500.0, "tot": 0, "respawn_rest": 0, "level": 9, "leben_anteil": 0.8,
             "gold_tasche": 400, "hat_tp": 1, "abst_brunnen": 12000, "in_eigener_lane": 1, "mit_lebend": 4,
             "mit1_x": 4000, "mit1_y": 8000, "mit2_x": 7000, "mit2_y": 7000, "mit3_x": 12000, "mit3_y": 1800,
             "mit4_x": 12100, "mit4_y": 1700, "drache_da": 0, "drache_bis": 80, "baron_da": 0, "baron_bis": 600,
             "herold_bis": -1, "larven_bis": -1, "lg_nahe_sichtbar": 1, "lg_x": 2000, "lg_y": 12800}
    for i in range(5):
        grund[f"geg{i}_tot"] = 0
        grund[f"geg{i}_respawn"] = 0
    grund.update(werte)
    for n, v in grund.items():
        x[f.SP[n]] = v
    return x


def meta(rolle=0, team=0, zeit=600, sieg=1, liga=0, partie=1) -> np.ndarray:
    m = np.zeros(len(f.META), np.int32)
    for n, v in (("rolle", rolle), ("team", team), ("zeit", zeit), ("sieg", sieg), ("liga", liga), ("partie", partie)):
        m[f.MI[n]] = v
    return m


def lage_aus_moment():
    lage = treue.lage_aus_moment(zeile(), meta(), f.SP, f.MI)
    assert lage.team == "ORDER" and lage.ich.rolle == "TOP" and lage.zeit == 600 and lage.gold == 400
    assert lage.ich.pos == (1500.0, 12500.0) and abs(lage.ich.leben - 0.8) < 1e-6 and lage.ich.tp_hat
    assert lage.lane_gegner.pos == (2000.0, 12800.0) and lage.lane_gegner.gesehen_vor == 0.0   # nahe sichtbar
    assert lage.gegner_jungler.gesehen_vor is None and lage.gegner_jungler.pos is None           # nie gesehen
    assert [m.art for m in lage.monster] == ["drache", "baron"] and lage.monster[0].spawn_in == 80
    assert len(lage.mitspieler) == 4 and all(s.lebt for s in lage.mitspieler)
    assert "welle_eigen" not in lage.vorhanden and "eigene_wards" not in lage.vorhanden
    tot = treue.lage_aus_moment(zeile(mit2_x=np.nan, mit2_y=np.nan, drache_da=1), meta(team=1), f.SP, f.MI)
    assert tot.team == "CHAOS" and not tot.mitspieler[1].lebt and tot.monster[0].spawn_in == 0.0


def treffer_und_schluessel():
    assert treue.treffer(("Objective", "Drache"), "Objective:Drache")
    assert not treue.treffer(("Objective", "Baron"), "Objective:Drache")
    assert treue.treffer(("Objective", ""), "Objective:Drache")
    assert treue.treffer(("Lane", ""), "Lane") and not treue.treffer(("Lane", ""), "Back")
    assert not treue.treffer(None, "Lane")
    assert treue.treffer_flags(("Back", ""), 1 << treue.AKTIONEN.index("Back"))
    assert not treue.treffer_flags(("Lane", ""), 1 << treue.AKTIONEN.index("Back"))
    q = np.array([0.1, 0.2, 0.5, 0.3, 0.0])
    assert treue.key_fuer(("Objective", "Drache"), q, KEYS) == 2
    assert treue.key_fuer(("Objective", ""), q, KEYS) == 2
    assert treue.key_fuer(("Rotation", "oben"), q, KEYS) == 3          # keine Zone oben: die beste Rotation
    assert treue.key_fuer(("Jungle", ""), q, KEYS) is None


def coach_mit_momenthirn():
    """Die echte bewerte()-Logik mit vorberechneten Werten: klar Lane -> ein Kommando mit Aktion."""
    hirn = treue.MomentHirn(gh.Gehirn, KEYS, mo.BASIS_NAMEN, {"delta": 0.005, "p_klar": 0.15, "p_geteilt": 0.08})
    hirn.setzen(np.array([0.0, 0.02, -0.01, 0.0, 0.0]), np.array([0.1, 0.6, 0.1, 0.1, 0.1]), np.full(5, 0.05), 0.55)
    x = zeile()
    b = np.hstack([x[mo.X_SPALTEN], [0, 0, 0]]).astype(np.float64)
    u = treue.coach(treue.lage_aus_moment(x, meta(), f.SP, f.MI), b, hirn, "wert")
    assert u["id"] and u["form"] in ("klar", "gefahr", "geteilt", "unklar", "grund") and u["aktionen"]
    assert any(s in u["stumm"] for s in ("W1", "W3", "S10")), u["stumm"]     # Wellen/Wards fehlen: stumm, kein Fehler


def auswerten_bekannt():
    """Vier Momente, bekannte Antworten: Treffer, Sieger, Challenger, Wert (DR), Abdeckung, Warnungen."""
    n = 4
    k = np.array([1, 0, 2, 1])                      # gespielt: Lane, Back, Objective:Drache, Lane
    q = np.tile(np.array([0.00, 0.01, 0.02, 0.0, 0.0]), (n, 1))
    y = np.array([0.01, 0.00, 0.03, 0.01])
    flags = np.array([1 << treue.AKTIONEN.index("Lane"), 1 << treue.AKTIONEN.index("Back"),
                      (1 << treue.AKTIONEN.index("Objective")) | (1 << treue.AKTIONEN.index("Lane")),
                      1 << treue.AKTIONEN.index("Lane")])
    A = np.zeros((n, len(f.AKTION)), np.int32)
    A[:, f.AI["flags"]] = flags
    F = np.zeros((n, len(f.FOLGE)), np.float32)
    F[1, f.FI["tod_60"]] = 1
    M = np.stack([meta(sieg=1, liga=0, partie=1), meta(sieg=0, liga=2, partie=1), meta(sieg=1, liga=1, partie=2),
                  meta(sieg=0, liga=0, partie=3)])
    P = SimpleNamespace(M=M, A=A, F=F, k=k, y=y, q=q, X=np.stack([zeile()] * n), keys_liste=KEYS,
                        partie=M[:, f.MI["partie"]], MI=f.MI, AI=f.AI, FI=f.FI, SP=f.SP,
                        psi=lambda a: q[:, a] + np.where(k == a, (y - q[:, a]) / 0.5, 0.0))
    coach = [{"aktionen": [("Lane", "")], "g0": False, "form": "klar", "id": "W1", "text": "x", "stumm": []},
             {"aktionen": [("Lane", "")], "g0": False, "form": "gefahr", "id": "J4", "text": "x", "stumm": ["W1"]},
             {"aktionen": [("Lane", ""), ("Objective", "Drache")], "g0": False, "form": "geteilt", "id": "W6",
              "text": "x", "stumm": []},
             {"aktionen": [("Lane", "")], "g0": True, "form": "grund", "id": "G0", "text": "x", "stumm": []}]
    e = treue.auswerten(P, {"Coach": coach, "immer farmen": [{"aktionen": [("Lane", "")]}] * n}, beispiele=2)
    c, fa = e["politiken"]["Coach"], e["politiken"]["immer farmen"]
    assert c["treffer"] == 0.75 and fa["treffer"] == 0.5                   # geteilt zaehlt die zweite Option
    assert c["treffer_locker"] == 0.75 and fa["treffer_locker"] == 0.75
    assert c["treffer_sieger"] == 1.0 and c["treffer_challenger"] == 1.0 and c["treffer_sieger_challenger"] == 1.0
    assert c["abdeckung"] == 0.75 and c["warnungen"] == 0.25 and c["warnung_tod60"] == 1.0
    assert c["stumm_je_entscheidung"] == {"W1": 1}
    # Wert: Lane ueberall (erste Option) - DR: psi_Lane - y
    psi_lane = q[:, 1] + np.where(k == 1, (y - q[:, 1]) / 0.5, 0.0)
    assert math.isclose(fa["wert_dr"], 100 * treue.partie_se(psi_lane - y, P.partie)[0], rel_tol=1e-6)
    assert len(e["beispiele"]) == 2


def alter_kern_anlegen():
    e = treue.alte_lage(zeile(), meta(zeit=400), f.SP, f.MI)
    assert e is not None and e["modus"] == "LANE" and e["welle"]["zustand"] == "UNBEKANNT"
    assert treue.alte_lage(zeile(), meta(rolle=2), f.SP, f.MI) is None           # nicht Top: nicht anlegbar
    assert treue.alte_lage(zeile(), meta(zeit=1200), f.SP, f.MI) is None         # Mitte: nicht anlegbar
    a = treue.alter_kern(e)
    assert a is None or a[0] in treue.AKTIONEN


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for t in (lage_aus_moment, treffer_und_schluessel, coach_mit_momenthirn, auswerten_bekannt, alter_kern_anlegen):
        t()
        print(f"{t.__name__} OK")
