"""Quest-TP der Toplane ohne Teleport (kern/quest_tp.py, kern.toml [quest_tp]) -> m.tp_in.

Die Faelle stammen aus Carlos' Riven-Partien vom 27.09.2026 (Minimap-Sichtungen, Quest-Slot V im Schirmbild):
Teleport aus dem Brunnen (164326 18:55), Recall und Herauslaufen (164326 7:46-7:51, war ein Fehlalarm), ein
falsch zugeordnetes Einzelbild, die Regel "bereit ab 13:35".

    python tests/test_quest_tp.py
"""
import sys
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach.kern import konfig  # noqa: E402
from lolcoach.kern.merkmale import TP_ZAUBER  # noqa: E402
from lolcoach.kern.quest_tp import QuestTP  # noqa: E402

CFG = konfig()["quest_tp"]
LANE, BRUNNEN, LANDUNG = (0.15, 0.15), (0.96, 0.04), (0.50, 0.09)


def lage(rolle="TOP", zauber=("SummonerDot", "SummonerFlash"), modus="CLASSIC"):
    p = NS(ich=NS(name="Nevir#EXIL", team="CHAOS", rolle=rolle, zauber=zauber, tot=False), modus=modus)
    return p, NS(verlauf={("Nevir#EXIL", "CHAOS"): []})     # wie Lagebild.verlauf: nur echte Sichtungen


def fahre(q, p, lb, bilder, bis):
    """bilder: [(Spielzeit, (x, y))]; Takt 0,25 s wie der Kern; gibt tp_in bei `bis` zurueck."""
    t, i, tp = bilder[0][0], 0, None
    while t <= bis:
        while i < len(bilder) and bilder[i][0] <= t:
            lb.verlauf[("Nevir#EXIL", "CHAOS")].append((bilder[i][0], *bilder[i][1]))
            i += 1
        tp = q.tp_in(p, lb, t)
        t += 0.25
    return tp


def test_regel():
    p, lb = lage()
    q = QuestTP(CFG)
    assert q.tp_in(p, lb, 700.0) is None                  # Quest vielleicht noch nicht fertig: unbekannt
    assert q.tp_in(p, lb, CFG["quest_ende_s"]) == 0.0      # spaetestens 13:35 fertig: bereit
    for kw in ({"zauber": ("SummonerTeleport", "SummonerFlash")}, {"rolle": "MIDDLE"}, {"modus": "SWIFTPLAY"}):
        p, lb = lage(**kw)
        assert QuestTP(CFG).tp_in(p, lb, 900.0) is None, kw
    assert "S12_SummonerTeleportUpgrade" in TP_ZAUBER      # gewaehltes TP nach der Quest (133930 ab 8:02)


def test_teleport_aus_dem_brunnen():
    p, lb = lage()
    q = QuestTP(CFG)
    bilder = [(1130.0 + k * 0.5, BRUNNEN) for k in range(9)] + [(1135.1, LANDUNG)]   # danach verliert ihn die Minimap
    assert fahre(q, p, lb, bilder, 1140.0) == 1135.1 + CFG["abklingzeit_s"] - 1140.0
    assert q.tp_in(p, lb, 1135.1 + CFG["abklingzeit_s"]) == 0.0


def test_recall_ist_kein_teleport():
    p, lb = lage()
    q = QuestTP(CFG)
    raus = [(468.0 + k, (0.96 - 0.04 * k, 0.04 + 0.006 * k)) for k in range(6)]       # zuletzt (0.76, 0.07)
    bilder = [(455.0 + k, LANE) for k in range(11)] + [(465.4, BRUNNEN)] + raus      # ohne den Brunnen: 1140/s
    assert fahre(q, p, lb, bilder, 480.0) is None and q.benutzt is None


def test_einzelbild_ist_kein_teleport():
    p, lb = lage()
    q = QuestTP(CFG)
    bilder = [(900.0 + k * 0.1, LANE) for k in range(20)] + [(902.0, LANDUNG), (902.1, LANE), (902.2, LANE)]
    assert fahre(q, p, lb, bilder, 910.0) == 0.0 and q.benutzt is None


def test_quest_ende_aus_dem_hud():
    """Auftrag 006, W2: das violette V im HUD macht das Quest-TP bereit - vor 13:35; ohne Lesung gilt die Regel."""
    import cv2
    import numpy as np
    from lolcoach import hud
    bild = np.zeros((900, 1600, 3), np.uint8)
    assert hud.quest(bild) == "dunkel"
    cv2.circle(bild, (1020, 852), 9, (230, 70, 200), -1)          # violett (BGR)
    assert hud.quest(bild) == "bereit", hud.quest(bild)
    bild[:] = 0
    cv2.circle(bild, (1020, 852), 10, (200, 190, 30), 3)          # tuerkiser Ring
    assert hud.quest(bild) == "laeuft", hud.quest(bild)
    p, lb = lage()
    q = QuestTP(CFG)
    lb.quest = ("laeuft", 600.0, 700.0)
    assert q.tp_in(p, lb, 700.0) is None
    lb.quest = ("bereit", 706.0, 706.0)
    assert q.tp_in(p, lb, 707.0) == 0.0                              # 11:47, nicht erst 13:35


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for f in (test_regel, test_teleport_aus_dem_brunnen, test_recall_ist_kein_teleport, test_einzelbild_ist_kein_teleport,
              test_quest_ende_aus_dem_hud):
        f()
    print("Quest-TP OK")
