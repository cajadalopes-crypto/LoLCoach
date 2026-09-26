"""Die Mitspieler-Leiste ueber der Minimap: Leben und Ult-Bereitschaft der vier Mitspieler.

Die Live-API kennt das Leben der Mitspieler nicht - das Bild schon (Partie 3,
25:27: "Baron jetzt", waehrend zwei Mitspieler kaum noch Leben hatten).

Vermessen am 26.09.2026 an Carlos' Einstellungen (4K, Fensterhoehe 2160,
unten rechts): vier Kaesten ueber der Minimap. In Pixeln, gemessen vom
Ausschnitt "unten rechts, 907 x 907" (= 0,42 x Hoehe): Lebensbalken x 342-451,
naechster Kasten +145 px, Zeilen 226-241; Ult-Kreis ueber dem Portraet, Mitte
x 397 (+145 je Kasten), y 114: gruen-tuerkis = bereit, Tortenstueck/schwarz = nicht bereit. Alles skaliert mit der Fensterhoehe.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

REF = 2160
ECKE = 907                  # Seitenlaenge des Bezugsausschnitts bei 2160
BALKEN_X, BALKEN_BREITE, ABSTAND = 342, 110, 145
BALKEN_Y = (228, 240)
ULT = (397, 114, 13)        # Mitte x, Mitte y, Radius (innen, ohne Goldrand)


@dataclass(frozen=True)
class Mitspieler:
    leben: float            # 0..1 (Anteil des Lebensbalkens)
    ult_bereit: bool | None  # None: nicht erkennbar


def bereich(breite: int, hoehe: int) -> tuple[int, int, int, int]:
    """(links, oben, rechts, unten) der Leiste im Spielfenster."""
    s = hoehe / REF
    x0 = breite - round(ECKE * s) + round((BALKEN_X - 20) * s)
    y0 = hoehe - round(ECKE * s) + round((ULT[1] - ULT[2] - 10) * s)
    x1 = breite - round(ECKE * s) + round((BALKEN_X + 3 * ABSTAND + BALKEN_BREITE + 10) * s)
    y1 = hoehe - round(ECKE * s) + round((BALKEN_Y[1] + 4) * s)
    return x0, y0, x1, y1


def lies(leiste: np.ndarray, hoehe: int = REF) -> list[Mitspieler]:
    """`leiste`: BGR-Ausschnitt genau `bereich(...)`. Gibt vier Mitspieler von links nach rechts."""
    s = hoehe / REF
    ox = BALKEN_X - 20
    oy = ULT[1] - ULT[2] - 10
    hsv = cv2.cvtColor(leiste, cv2.COLOR_BGR2HSV)
    ergebnis = []
    for i in range(4):
        x0 = round((BALKEN_X + i * ABSTAND - ox) * s)
        x1 = round((BALKEN_X + i * ABSTAND + BALKEN_BREITE - ox) * s)
        y0, y1 = round((BALKEN_Y[0] - oy) * s), round((BALKEN_Y[1] - oy) * s)
        streifen = hsv[y0:y1, x0:x1]
        gruen = cv2.inRange(streifen, (40, 110, 90), (85, 255, 255)).mean(axis=0) > 127
        # Balken fuellt von links: der rechteste gruene Punkt ist der Stand
        spalten = np.nonzero(gruen)[0]
        leben = (spalten.max() + 1) / len(gruen) if len(spalten) else 0.0
        cx, cy, r = round((ULT[0] + i * ABSTAND - ox) * s), round((ULT[1] - oy) * s), round(ULT[2] * s)
        kreis = hsv[max(0, cy - r):cy + r, max(0, cx - r):cx + r]
        ult = None
        if kreis.size:
            anteil_gruen = (cv2.inRange(kreis, (40, 90, 90), (90, 255, 255)) > 0).mean()
            ult = anteil_gruen > 0.25
        ergebnis.append(Mitspieler(round(float(leben), 2), ult))
    return ergebnis
