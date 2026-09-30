"""Je Entscheidung (Buch 17, Teil B) eine konstruierte Lage, in der sie feuern MUSS, und eine, in der sie schweigen MUSS.

FAELLE[id] = (feuert, schweigt) - beides Funktionen ohne Argument, die eine MakroLage bauen.
"""
from __future__ import annotations

from bau import Kampf, L, Ward, geg, hirn, ich, mit, monster, welle


def _unbekannt(lage, *rollen):
    for r in rollen:
        geg(lage, r, gesehen_vor=None)
    return lage


def _alle_gesehen(lage, alter=0.0):
    for g in lage.gegner:
        g.gesehen_vor = alter
    return lage


FAELLE = {
    # ---------------------------------------------------------------- B1 Sicht
    "S1": (lambda: geg(L(zeit=100), "JUNGLE", pos=(10000, 4000), gesehen_vor=10), lambda: L(zeit=400)),
    "S2": (lambda: L(zeit=100), lambda: L(zeit=200)),
    "S3": (lambda: geg(welle(L(zeit=300), stand="mitte"), "JUNGLE", gesehen_vor=40),
           lambda: geg(welle(L(zeit=300), stand="gecrasht"), "JUNGLE", gesehen_vor=40)),
    "S4": (lambda: geg(geg(welle(L(), stand="gecrasht"), "TOP", lebt=False, respawn=20), "JUNGLE", pos=(12000, 3000), gesehen_vor=2),
           lambda: geg(geg(welle(L(), stand="gecrasht"), "TOP", lebt=False, respawn=20), "JUNGLE", pos=(4500, 12000), gesehen_vor=2)),
    "S5": (lambda: geg(L(plan={"unterwegs": True}), "JUNGLE", gesehen_vor=60),
           lambda: geg(L(plan={"unterwegs": True}), "JUNGLE", gesehen_vor=5)),
    "S6": (lambda: ich(L(gold=500), im_brunnen=True), lambda: ich(L(gold=500, kontrollauge_inventar=True), im_brunnen=True)),
    "S7": (lambda: monster(ich(L(zeit=900), im_brunnen=True), "herold", 100), lambda: ich(L(zeit=600), im_brunnen=True)),
    "S8": (lambda: monster(L(), "larven", 70), lambda: monster(L(), "larven", 150)),
    "S9": (lambda: monster(L(trinket="linse"), "drache", 35), lambda: monster(L(), "drache", 35)),
    "S10": (lambda: L(plan={"split": True}), lambda: L(plan={"split": True}, wards=[Ward("Flanke Blau-Eingang")])),
    "S11": (lambda: _unbekannt(L(gesehen_busch=True), "JUNGLE", "MIDDLE"), lambda: _unbekannt(L(gesehen_busch=False), "JUNGLE", "MIDDLE")),
    "S12": (lambda: L(ward_verloren="Tri-Busch"), lambda: L()),
    "S13": (lambda: L(trinket_ladungen=2), lambda: L(trinket_ladungen=1)),
    "S14": (lambda: mit(monster(L(), "larven", 40), "JUNGLE", pos=(5000, 10000)),
            lambda: mit(monster(L(), "larven", 40), "JUNGLE", pos=(12000, 2000))),
    # ---------------------------------------------------------------- B2 Jungler
    "J1": (lambda: geg(L(zeit=100), "JUNGLE", pos=(4000, 9000), gesehen_vor=5), lambda: L(zeit=400)),
    "J2": (lambda: geg(welle(L(zeit=250), stand="bei_ihnen"), "JUNGLE", gesehen_vor=40),
           lambda: geg(welle(L(zeit=250), stand="bei_ihnen"), "JUNGLE", gesehen_vor=5)),
    "J3": (lambda: geg(L(), "JUNGLE", pos=(12000, 3000), gesehen_vor=2), lambda: geg(L(), "JUNGLE", pos=(3000, 11000), gesehen_vor=2)),
    "J4": (lambda: geg(ich(L(), pos=(3600, 13600)), "JUNGLE", gesehen_vor=50), lambda: geg(ich(L(), pos=(3600, 13600)), "JUNGLE", gesehen_vor=10)),
    "J5": (lambda: _unbekannt(L(), "JUNGLE", "MIDDLE"), lambda: L()),
    "J6": (lambda: geg(L(), "TOP", gesehen_vor=15), lambda: geg(L(), "TOP", gesehen_vor=2)),
    "J7": (lambda: L(ereignisse=[("tp", "gegner", 10)]), lambda: L()),
    "J8": (lambda: geg(L(), "MIDDLE", flash_in=200), lambda: L()),
    "J9": (lambda: geg(ich(L(), pos=(3600, 13600)), "MIDDLE", champion="Pantheon", level=7, gesehen_vor=20),
           lambda: geg(ich(L(), pos=(3600, 13600)), "MIDDLE", champion="Pantheon", level=5, gesehen_vor=20)),
    "J10": (lambda: geg(L(), "TOP", spike_neu=True), lambda: L()),
    "J11": (lambda: L(zeit=80), lambda: _alle_gesehen(L(zeit=80))),
    "J12": (lambda: geg(mit(L(), "JUNGLE", pos=(1800, 12000)), "JUNGLE", pos=(3000, 11500), gesehen_vor=2),
            lambda: geg(mit(L(), "JUNGLE", pos=(1800, 12000)), "JUNGLE", gesehen_vor=30)),
    "J13": (lambda: mit(L(zeit=210), "JUNGLE", pos=(4400, 9800)), lambda: mit(L(zeit=300), "JUNGLE", pos=(4400, 9800))),
    "J14": (lambda: welle(geg(geg(ich(L(), leben=0.3), "TOP", pos=(2000, 12800), gesehen_vor=1), "JUNGLE", pos=(1800, 12000), gesehen_vor=1), stand="bei_uns"),
            lambda: welle(geg(geg(ich(L(), leben=0.9), "TOP", pos=(2000, 12800), gesehen_vor=1), "JUNGLE", pos=(1800, 12000), gesehen_vor=1), stand="bei_uns")),
    # ---------------------------------------------------------------- B3 Wellen
    "W1": (lambda: welle(L(), stand="bei_uns", groesse=-2), lambda: L()),
    "W2": (lambda: welle(L(plan={"back": True}), stand="mitte", kanone_in=40), lambda: welle(L(plan={"back": True}), stand="mitte", kanone_in=10)),
    "W3": (lambda: welle(L(gold=1000), stand="gecrasht"), lambda: welle(L(gold=200), stand="gecrasht")),
    "W4": (lambda: ich(welle(L(gold=200), stand="gecrasht"), leben=0.9), lambda: L()),
    "W5": (lambda: welle(L(plan={"tp": True}), stand="bei_uns", groesse=-2), lambda: L(plan={"tp": True})),
    "W6": (lambda: monster(L(), "drache", 80), lambda: monster(L(), "drache", 40)),
    "W7": (lambda: L(plan={"roam": "Brand"}), lambda: welle(L(plan={"roam": "Brand"}), stand="gecrasht")),
    "W8": (lambda: hirn(welle(monster(L(), "drache", 20), stand="bei_uns"), [("Objective", "Drache", 3.0, 0.3, 0.1, "klar", [])]),
           lambda: monster(L(), "drache", 20)),
    "W9": (lambda: geg(welle(L(), stand="bei_ihnen"), "JUNGLE", gesehen_vor=40), lambda: geg(welle(L(), stand="bei_ihnen"), "JUNGLE", gesehen_vor=5)),
    "W10": (lambda: geg(L(gegner_platten={"top": 3}), "TOP", lebt=False, respawn=25), lambda: L()),
    "W11": (lambda: welle(L(zeit=1000), "bot", stand="bei_uns"), lambda: welle(L(zeit=600), "bot", stand="bei_uns")),
    "W12": (lambda: geg(L(gegner_platten={"top": 1}), "TOP", lebt=False, respawn=20),
            lambda: geg(L(gegner_platten={"top": 5}), "TOP", lebt=False, respawn=20)),
    "W13": (lambda: monster(L(), "drache", 15), lambda: L()),
    "W14": (lambda: welle(monster(L(), "drache", 40), "bot", stand="bei_uns"), lambda: monster(L(), "drache", 40)),
    # ---------------------------------------------------------------- B4 Back
    "B1": (lambda: welle(L(gold=1000), stand="gecrasht"), lambda: ich(L(gold=200), leben=0.9)),
    "B2": (lambda: monster(L(gold=800), "drache", 100), lambda: monster(L(gold=800), "drache", 40)),
    "B3": (lambda: geg(L(plan={"back": True}), "TOP", lebt=False, respawn=20), lambda: geg(L(), "TOP", lebt=False, respawn=20)),
    "B4": (lambda: ich(L(), leben=0.2), lambda: L()),
    "B5": (lambda: geg(L(), "TOP", backt=True), lambda: L()),
    "B6": (lambda: monster(ich(L(), im_brunnen=True, tp_in=0), "drache", 120), lambda: ich(L(), im_brunnen=True, tp_in=0)),
    "B7": (lambda: ich(L(gold=1200), im_brunnen=True), lambda: ich(L(gold=100), im_brunnen=True)),
    "B8": (lambda: ich(L(), lebt=False, respawn=8), lambda: ich(L(), lebt=False, respawn=30)),
    "B9": (lambda: ich(L(gold=1000), champion="Ornn"), lambda: L(gold=1000)),
    # ---------------------------------------------------------------- B5 TP
    "T1": (lambda: welle(ich(L(), im_brunnen=True, tp_in=0), stand="bei_uns", groesse=-4),
           lambda: welle(ich(L(), im_brunnen=True, tp_in=0), stand="bei_uns", groesse=0)),
    "T2": (lambda: ich(L(kampf=Kampf((10000, 4500), in_s=10, dauer_s=15, wir=3, gegner=3)), tp_in=0),
           lambda: ich(L(kampf=Kampf((2500, 12000), in_s=10, dauer_s=15, wir=1, gegner=1)), tp_in=0)),
    "T3": (lambda: monster(ich(L(plan={"tp": "lane"}), tp_in=0), "drache", 90), lambda: monster(ich(L(), tp_in=0), "drache", 90)),
    "T4": (lambda: ich(L(zeit=1600, kampf=Kampf((5000, 10400), in_s=3, bei="Baron"), wards=[Ward("Flanke hinter Baron")]), tp_in=0),
           lambda: ich(L(zeit=1600, kampf=Kampf((5000, 10400), in_s=3, bei="Baron")), tp_in=0)),
    "T5": (lambda: ich(L(plan={"verteidigen": ("mid", 15)}), tp_in=0), lambda: ich(L(plan={"verteidigen": ("mid", 60)}), tp_in=0)),
    "T6": (lambda: ich(L(ereignisse=[("tp", "gegner", 2)], kampf=Kampf((10000, 4500), wir=3, gegner=3)), tp_in=0),
           lambda: ich(L(kampf=Kampf((10000, 4500), wir=3, gegner=3)), tp_in=0)),
    "T7": (lambda: geg(L(plan={"tp": True, "tp_ziele": [("den Vasallen hinten", (9000, 2000)), ("den Ward im Fluss", (9800, 4600))]}),
                       "UTILITY", pos=(9800, 4700), gesehen_vor=2),
           lambda: L(plan={"tp": True, "tp_ziele": [("den Vasallen hinten", (9000, 2000))]})),
    "T8": (lambda: ich(L(kampf=Kampf((10000, 4500), in_s=0, dauer_s=3, wir=2, gegner=3)), tp_in=0),
           lambda: ich(L(kampf=Kampf((2500, 12000), in_s=0, dauer_s=3, wir=2, gegner=3)), tp_in=0)),
    "T9": (lambda: geg(ich(L(), tp_in=0), "TOP", tp_in=200), lambda: ich(L(), tp_in=0)),
    # ---------------------------------------------------------------- B6 Roams
    "R1": (lambda: geg(welle(L(), stand="gecrasht"), "MIDDLE", flash_in=200), lambda: welle(L(), stand="gecrasht")),
    "R2": (lambda: mit(welle(L(zeit=300), stand="gecrasht"), "JUNGLE", pos=(4400, 9700)), lambda: mit(L(zeit=300), "JUNGLE", pos=(4400, 9700))),
    "R3": (lambda: welle(monster(L(), "larven", 30), stand="gecrasht"), lambda: welle(L(), stand="gecrasht")),
    "R4": (lambda: monster(ich(L(), pos=(7000, 6000)), "drache", 45), lambda: monster(L(), "drache", 10)),
    "R5": (lambda: geg(L(plan={"roam": "Brand"}), "MIDDLE", lebt=False, respawn=20), lambda: geg(L(), "MIDDLE", lebt=False, respawn=20)),
    "R6": (lambda: L(tuerme_weg=[("ORDER", "Top", "aussen")], turm_gefallen_vor=10), lambda: L(tuerme_weg=[("ORDER", "Top", "aussen")], turm_gefallen_vor=100)),
    "R7": (lambda: _unbekannt(L(plan={"unterwegs": True}), "JUNGLE", "MIDDLE"), lambda: L(plan={"unterwegs": True})),
    "R8": (lambda: welle(L(plan={"roam": "Brand", "roam_gewinn": 0.1}), stand="bei_uns"),
           lambda: welle(L(plan={"roam": "Brand", "roam_gewinn": 5.0}), stand="bei_uns")),
    "R9": (lambda: welle(mit(geg(L(), "JUNGLE", pos=(11000, 4000), gesehen_vor=2), "JUNGLE", pos=(2000, 12000)), stand="gecrasht"),
           lambda: welle(mit(geg(L(), "JUNGLE", pos=(4000, 11000), gesehen_vor=2), "JUNGLE", pos=(2000, 12000)), stand="gecrasht")),
    "R10": (lambda: welle(geg(geg(L(zeit=400), "TOP", lebt=False, respawn=20), "JUNGLE", pos=(12000, 3000), gesehen_vor=2), stand="gecrasht"),
            lambda: geg(geg(L(zeit=400), "TOP", lebt=False, respawn=20), "JUNGLE", pos=(12000, 3000), gesehen_vor=2)),
    # ---------------------------------------------------------------- B7 Objectives
    "O1": (lambda: monster(L(), "drache", 20), lambda: L()),
    "O2": (lambda: welle(monster(L(), "larven", 20), stand="gecrasht"), lambda: monster(L(), "larven", 20)),
    "O3": (lambda: L(ereignisse=[("herold", "wir", 10)], gegner_platten={"top": 4, "mid": 1}), lambda: L(gegner_platten={"top": 4, "mid": 1})),
    "O4": (lambda: geg(geg(monster(L(zeit=1500), "baron", 0), "MIDDLE", lebt=False, respawn=40), "BOTTOM", lebt=False, respawn=40),
           lambda: monster(L(zeit=1500), "baron", 0)),
    "O5": (lambda: geg(geg(geg(L(plan={"objective": "baron"}), "MIDDLE", pos=(5200, 10200), gesehen_vor=2), "BOTTOM", pos=(5300, 10000),
                           gesehen_vor=2), "UTILITY", pos=(5400, 10100), gesehen_vor=2),
           lambda: geg(geg(geg(L(), "MIDDLE", pos=(5200, 10200), gesehen_vor=2), "BOTTOM", pos=(5300, 10000), gesehen_vor=2),
                       "UTILITY", pos=(5400, 10100), gesehen_vor=2)),
    "O6": (lambda: monster(L(), "elder", 30), lambda: monster(L(), "drache", 30)),
    "O7": (lambda: monster(L(), "drache", 75), lambda: monster(L(), "drache", 200)),
    "O8": (lambda: mit(geg(L(plan={"objective": "drache"}), "JUNGLE", gesehen_vor=None), "JUNGLE", smite_bereit=False),
           lambda: mit(geg(L(plan={"objective": "drache"}), "JUNGLE", gesehen_vor=None), "JUNGLE", smite_bereit=True)),
    "O9": (lambda: L(ereignisse=[("drache", "wir", 5)]), lambda: L()),
    "O10": (lambda: _drache_verloren(), lambda: mit(mit(monster(L(), "drache", 5), "BOTTOM", lebt=False, respawn=30), "UTILITY", lebt=False, respawn=30)),
    "O11": (lambda: _drache_verloren(plan={"objective": "drache"}), lambda: _drache_verloren()),
    "O12": (lambda: monster(L(), "drache", 60, kopfgeld=True), lambda: monster(L(), "drache", 60)),
    # ---------------------------------------------------------------- B8 Kaempfe
    "K1": (lambda: L(kampf=Kampf((7400, 7400), in_s=5)), lambda: L()),
    "K2": (lambda: L(kampf=Kampf((7400, 7400), in_s=10)), lambda: L(kampf=Kampf((9866, 4414), in_s=10))),
    "K3": (lambda: L(kampf=Kampf((10000, 4500), in_s=0, dauer_s=10)), lambda: L(kampf=Kampf((10000, 4500), in_s=5, dauer_s=10))),
    "K4": (lambda: geg(geg(monster(L(ereignisse=[("kampf", "gewonnen", 3)]), "baron", 0), "MIDDLE", lebt=False, respawn=30), "BOTTOM", lebt=False, respawn=30),
           lambda: geg(geg(monster(L(), "baron", 0), "MIDDLE", lebt=False, respawn=30), "BOTTOM", lebt=False, respawn=30)),
    "K5": (lambda: L(ereignisse=[("kampf", "verloren", 3)]), lambda: L()),
    "K6": (lambda: geg(ich(L(), pos=(4000, 5000)), "BOTTOM", pos=(6000, 3000), gesehen_vor=1), lambda: _alle_gesehen(L(), 10)),
    "K7": (lambda: _unbekannt(ich(L(zeit=1700), level=16), "JUNGLE", "MIDDLE", "BOTTOM"),
           lambda: _unbekannt(ich(L(zeit=1000), level=16), "JUNGLE", "MIDDLE", "BOTTOM")),
    # ---------------------------------------------------------------- B9 Spaetphase
    "M1": (lambda: L(zeit=850), lambda: L(zeit=1000)),
    "M2": (lambda: hirn(L(zeit=1300), [("Gruppe", "", 1.2, 0.4, 0.05, "geteilt", []), ("Split", "", 1.0, 0.2, 0.2, "geteilt", [])]),
           lambda: L(zeit=1300)),
    "M3": (lambda: monster(L(plan={"split": True}), "baron", 40), lambda: monster(L(), "baron", 40)),
    "M4": (lambda: mit(mit(mit(L(zeit=1300), "JUNGLE", pos=(7300, 7300)), "BOTTOM", pos=(7500, 7200)), "UTILITY", pos=(7200, 7500)),
           lambda: L(zeit=1300)),
    "M5": (lambda: geg(ich(L(zeit=1600, plan={"aufstellung": True}, wards=[Ward("Flanke")]), level=12), "TOP", level=10),
           lambda: geg(ich(L(zeit=1600, wards=[Ward("Flanke")]), level=12), "TOP", level=10)),
    "M6": (lambda: welle(monster(L(zeit=1300), "baron", 50), "bot", stand="mitte"), lambda: welle(L(zeit=1300), "bot", stand="mitte")),
    "M7": (lambda: L(inhib_offen_gegner=["bot"]), lambda: L()),
    "M8": (lambda: _tote(ich(L(zeit=1800), pos=(10500, 10500)), 40, "MIDDLE", "BOTTOM", "UTILITY"),
           lambda: _tote(ich(L(zeit=1800), pos=(10500, 10500)), 40, "MIDDLE", "BOTTOM")),
    "M9": (lambda: L(ereignisse=[("baron", "gegner", 60)]), lambda: L()),
    "M10": (lambda: monster(ich(L(zeit=1700), level=16), "baron", 30), lambda: monster(ich(L(zeit=1000), level=16), "baron", 30)),
    # ---------------------------------------------------------------- B10 Spielstand
    "V1": (lambda: L(zeit=800, wir_skalieren=True), lambda: L(zeit=800)),
    "V2": (lambda: hirn(L(), siegchance=0.72), lambda: L()),
    "V3": (lambda: hirn(L(), siegchance=0.25), lambda: L()),
    "V4": (lambda: L(spike_wir=True), lambda: L()),
    "V5": (lambda: L(spike_gegner=True), lambda: L()),
    # ---------------------------------------------------------------- B11 Team
    "P1": (lambda: geg(L(), "JUNGLE", pos=(11000, 4000), gesehen_vor=2), lambda: geg(L(), "JUNGLE", pos=(4000, 11000), gesehen_vor=2)),
    "P2": (lambda: mit(monster(L(), "drache", 40), "BOTTOM", leben=0.3), lambda: monster(L(), "drache", 40)),
    "P3": (lambda: L(kampf=Kampf((2500, 12000), in_s=0, wir=1, gegner=1, bei="Vi")), lambda: L(kampf=Kampf((2500, 12000), in_s=0, wir=1, gegner=1))),
    "P4": (lambda: mit(mit(L(), "BOTTOM", lebt=False, respawn=20), "UTILITY", lebt=False, respawn=20), lambda: L()),
    # ---------------------------------------------------------------- B12 Warten
    "Z1": (lambda: mit(monster(L(), "drache", 40), "BOTTOM", lebt=False, respawn=8), lambda: L()),
    "Z2": (lambda: geg(L(), "TOP", lebt=False, respawn=30), lambda: L()),
    "Z3": (lambda: hirn(L(), [("Lane", "", 0.2, 0.4, 0.05, "unklar", [])]), lambda: L()),
}


def _drache_verloren(**kw):
    """Drache in 5 s, drei Gegner an der Grube, euer Bot und Support tot."""
    lage = monster(L(**kw), "drache", 5)
    for r in ("MIDDLE", "BOTTOM", "UTILITY"):
        geg(lage, r, pos=(9800, 4500), gesehen_vor=2)
    mit(lage, "BOTTOM", lebt=False, respawn=30)
    mit(lage, "UTILITY", lebt=False, respawn=30)
    return lage


def _tote(lage, respawn, *rollen):
    for r in rollen:
        geg(lage, r, lebt=False, respawn=respawn)
    return lage
