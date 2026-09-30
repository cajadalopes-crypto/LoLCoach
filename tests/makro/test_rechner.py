"""Makro-Rechner (lolcoach/makro/rechner.py): jede Funktion mit Soll-Werten und Grenzfaellen.

    python tests/makro/test_rechner.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lolcoach.bewertung import BRUNNEN, TUERME  # noqa: E402
from lolcoach.makro import rechner as r  # noqa: E402

TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def nah(a, b, tol=0.51):
    return abs(a - b) <= tol


@test
def ankunft():
    # 3650 Einheiten x 1,15 / 365 = 11,5 s; doppeltes Tempo = halbe Zeit; 0 fuer denselben Ort
    assert nah(r.ankunft((0, 0), (3650, 0)), 11.5)
    assert nah(r.ankunft((0, 0), (3650, 0), tempo=730), 5.75)
    assert r.ankunft((5, 5), (5, 5)) == 0
    assert r.ankunft_ab_brunnen("ORDER", BRUNNEN["ORDER"], respawn=12) == 12


@test
def brunnen_lane_aus_kern():
    # benutzt kern/uhren.brunnen_lane (nicht nachgebaut): Top blau ~ 32 s bei 365
    assert 25 < r.brunnen_lane("top", "ORDER") < 40


@test
def todes_kosten():
    assert r.todes_kosten(18, 2400) > r.todes_kosten(6, 600) > 0


@test
def wellen():
    g5, x5 = r.wellenwert(300)          # vor 14:00 jede 3. Welle Kanone
    g20, x20 = r.wellenwert(1600)       # ab 25:00 jede Welle
    assert 110 < g5 < 130 and g20 > g5 and x20 > x5
    assert r.wellentakt(300) == 30 and r.wellentakt(1000) == 25 and r.wellentakt(2000) == 20
    # gecrasht: die ersten 25 s kosten nichts; bei_uns: sofort
    assert r.wellenkosten(20, 600, "gecrasht") == (0.0, 0.0)
    assert r.wellenkosten(40, 600, "bei_uns")[0] > r.wellenkosten(40, 600, "gecrasht")[0] > 0
    assert r.fenster_welle("gecrasht") == 25 and r.fenster_welle("bei_uns") == 0 and r.fenster_welle(None) is None
    assert r.crash_dauer() == 6


@test
def ueberzahl():
    wir = [r.Einheit(ankunft_s=5), r.Einheit(ankunft_s=30), r.Einheit(lebt=False, respawn=5)]
    geg = [r.Einheit(ankunft_s=3), r.Einheit(ankunft_s=None, bekannt=False), r.Einheit(lebt=False, respawn=60)]
    z = r.ueberzahl(10, wir, geg, team_brunnen_weg=40)
    assert (z.wir, z.gegner_sicher, z.gegner_moeglich) == (1, 1, 2) and z.vorteil == -1
    z = r.ueberzahl(50, wir, geg, team_brunnen_weg=40)          # Toter mit 5 s Respawn + 40 s Weg ist da
    assert z.wir == 3


@test
def fenster():
    assert r.fenster_gegner(respawn=20, weg_zur_lane=30) == 50
    assert r.fenster_gegner(backt=True, weg_zur_lane=30) == 8 + 3 + 30
    assert r.fenster_gegner() is None
    assert r.fenster_jungler(None, None, (0, 0)) is None
    t = r.fenster_jungler((0, 0), 5, (3650, 0))                   # 11,5 s Weg, vor 5 s gesehen -> 6,5 s
    assert nah(t, 6.5) and r.fenster_jungler((0, 0), 60, (3650, 0)) == 0


@test
def tp():
    assert r.tp_abklingzeit(300) == 300
    assert r.tp_abklingzeit(900, 1) == 330 and r.tp_abklingzeit(900, 18) == 240
    assert r.tp_abklingzeit(300, top_quest=True) == 390 and r.tp_abklingzeit(900, 18, top_quest=True) == 210
    # Kanal 3 s + Anflug 0,5 s am selben Ort; weit weg laenger, nach 10:00 kuerzer (max 4 statt 5)
    assert nah(r.tp_ankunft((0, 0), (0, 0), (0, 0), 300), 3.5)
    assert r.tp_ankunft((0, 0), (14000, 14000), (14000, 14000), 300) > r.tp_ankunft((0, 0), (14000, 14000), (14000, 14000), 900)
    u = r.tp_urteil(kampf_in=5, kampf_dauer=5, ankunft_s=12, welle_stand="gecrasht", gegner_tp_bereit=None)
    assert not u.tpen and "zu spaet" in u.grund
    u = r.tp_urteil(kampf_in=10, kampf_dauer=10, ankunft_s=8, welle_stand="mitte", gegner_tp_bereit=False)
    assert u.tpen and u.crash_zuerst and u.ankunft_s == 14 and "kein TP" in u.grund
    u = r.tp_urteil(10, 10, 8, "gecrasht", None, wert_tp=1.0, wert_bleiben=2.0)
    assert not u.tpen


@test
def roam_und_gold():
    assert r.punkte_je_1000_gold(600) == 8.73 and r.punkte_je_1000_gold(1500) == 4.85
    assert 7.3 < r.punkte_je_1000_gold(750) < 8.73                 # zwischen 10 und 15 min linear
    assert r.roam_wert(20, 600, "gecrasht", 1.0) == 1.0            # im Rueckprall-Fenster kostet es nichts
    assert r.roam_wert(90, 600, "bei_uns", 0.2) < 0                # lange weg, Welle am Turm: lohnt nicht


@test
def rueckwaerts():
    assert r.rueckwaerts(120) == ("frei", "Welle", 30)
    assert r.rueckwaerts(75) == ("Welle", "Back", 15)
    assert r.rueckwaerts(45) == ("Back", "Sicht", 15)
    assert r.rueckwaerts(20) == ("Sicht", "Grube", 20)
    assert r.rueckwaerts(0) == ("Grube", None, 0.0)


@test
def schluss():
    ok, reserve = r.schluss_moeglich(15, "nexus", [30, 40])      # 15 + 10 <= 30
    assert ok and reserve == 5
    ok, reserve = r.schluss_moeglich(25, "inhib", [30])           # 25 + 8 > 30
    assert not ok and reserve < 0


@test
def karte_aus_bewertung():
    # die Rechner benutzen die Turmorte aus lolcoach/bewertung.py
    assert ("ORDER", "Top", "aussen") in TUERME


def main() -> int:
    rot = 0
    for t in TESTS:
        try:
            t()
            print(f"OK  {t.__name__}")
        except AssertionError as e:
            rot += 1
            print(f"ROT {t.__name__}: {e}")
    print(f"{len(TESTS) - rot}/{len(TESTS)} gruen")
    return 1 if rot else 0


if __name__ == "__main__":
    sys.exit(main())
