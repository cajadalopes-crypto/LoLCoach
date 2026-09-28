"""Die Mitspieler-Leiste ueber der Minimap: Leben und Ult-Bereitschaft der vier Mitspieler.

Die Live-API kennt das Leben der Mitspieler nicht - das Bild schon (Partie 3,
25:27: "Baron jetzt", waehrend zwei Mitspieler kaum noch Leben hatten).

Vermessen am 26.09.2026 an Carlos' Einstellungen (4K, Fensterhoehe 2160,
unten rechts): vier Kaesten ueber der Minimap. In Pixeln, gemessen vom
Ausschnitt "unten rechts, 907 x 907" (= 0,42 x Hoehe): Lebensbalken x 342-451,
naechster Kasten +145 px, Zeilen 226-241; Ult-Kreis ueber dem Portraet, Mitte
x 397 (+145 je Kasten), y 114: gruen-tuerkis = bereit, Tortenstueck/schwarz = nicht bereit. Alles skaliert mit der Fensterhoehe.

Die Leiste sitzt auf der Minimap und waechst mit ihr (MinimapScale, `minimap.faktor()` = k): gemessen 27.09. an
MinimapScale 2,91 - alles um k vergroessert, festgehalten an der Minimap-Ecke unten rechts (ANKER).
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
ANKER = (ECKE - 27, ECKE - 29)   # Minimap-Ecke unten rechts im Bezugsausschnitt (minimap.RAND_RECHTS/RAND_UNTEN)


@dataclass(frozen=True)
class Mitspieler:
    leben: float            # 0..1 (Anteil des Lebensbalkens)
    ult_bereit: bool | None  # None: nicht erkennbar


def _gewachsen(x: float, y: float, k: float) -> tuple[float, float]:
    """Ein Punkt der Leiste (Bezugsausschnitt) bei einer um k vergroesserten Minimap."""
    return ANKER[0] + k * (x - ANKER[0]), ANKER[1] + k * (y - ANKER[1])


def bereich(breite: int, hoehe: int, k: float = 1.0) -> tuple[int, int, int, int]:
    """(links, oben, rechts, unten) der Leiste im Spielfenster; `k` = `minimap.faktor()`."""
    s = hoehe / REF
    lx, oy = _gewachsen(BALKEN_X - 20, ULT[1] - ULT[2] - 10, k)
    rx, uy = _gewachsen(BALKEN_X + 3 * ABSTAND + BALKEN_BREITE + 10, BALKEN_Y[1] + 4, k)
    x0 = breite - round(ECKE * s) + round(lx * s)
    y0 = hoehe - round(ECKE * s) + round(oy * s)
    x1 = breite - round(ECKE * s) + round(rx * s)
    y1 = hoehe - round(ECKE * s) + round(uy * s)
    return x0, y0, x1, y1


# Eigene Faehigkeiten und Beschwoererzauber (Partie 6, Carlos' HUD bei 4K vermessen): unter jedem Feld
# steht der Tasten-Buchstabe - GELB, wenn bereit, weiss/grau, wenn in Abklingzeit oder nicht gelernt.
# (links-oben-x relativ zur Fenstermitte, Oberkante als Abstand vom unteren Rand, Breite, Hoehe) bei 2160.
TASTEN = {"Q": (-318, 116, 26, 24), "W": (-230, 116, 26, 24), "E": (-142, 116, 26, 24), "R": (-42, 116, 26, 24),
          "D": (55, 130, 22, 22), "F": (118, 130, 22, 22)}
GELB_AB = 8          # so viele gelbe Pixel im Buchstaben: bereit (gemessen: bereit 20-30, weg 0)


# Auftrag 006, W2: der Quest-Platz V rechts neben den Items - nur LESEN, der Coach drueckt V nie (CLAUDE.md).
# (Mitte x relativ zur Fenstermitte, Mitte y als Abstand vom unteren Rand, halbe Kantenlaenge) bei 2160, vermessen an
# den Schirmbildern (164326 12:10: violett um (1020, 852) bei 1600 x 900). Violett = Quest-TP bereit, tuerkis = die
# Quest laeuft (der Ring waechst, 164326: Anteil 0,19 um 10:00 bis 0,26 um 12:02), sonst dunkel (Abklingzeit).
QUEST = (528, 115, 26)
QUEST_ANTEIL = 0.08


def quest(fenster: np.ndarray) -> str | None:
    """Der Quest-Platz V: "bereit" (violettes TP-Symbol), "laeuft" (tuerkiser Ring) oder "dunkel"; None ohne Bild."""
    h, b = fenster.shape[:2]
    s = h / REF
    cx, cy, r = round(b / 2 + QUEST[0] * s), round(h - QUEST[1] * s), max(2, round(QUEST[2] * s))
    feld = fenster[max(0, cy - r):cy + r + 1, max(0, cx - r):cx + r + 1]
    if feld.size == 0:
        return None
    hsv = cv2.cvtColor(feld, cv2.COLOR_BGR2HSV)
    n = feld.shape[0] * feld.shape[1]
    violett = float((cv2.inRange(hsv, (125, 90, 120), (165, 255, 255)) > 0).sum()) / n
    tuerkis = float((cv2.inRange(hsv, (80, 90, 120), (100, 255, 255)) > 0).sum()) / n
    if violett >= QUEST_ANTEIL and violett >= tuerkis:
        return "bereit"
    if tuerkis >= QUEST_ANTEIL:
        return "laeuft"
    return "dunkel"


def eigene(fenster: np.ndarray) -> dict[str, bool] | None:
    """Q W E R D F: bereit (True) oder nicht (False), aus dem ganzen Spielfenster (BGR).
    None, wenn keiner der Buchstaben zu finden ist (z. B. HUD ausgeblendet)."""
    h, b = fenster.shape[:2]
    s = h / REF
    aus = {}
    for taste, (dx, oben, w, hh) in TASTEN.items():
        x0, y0 = round(b / 2 + dx * s), round(h - oben * s)
        feld = fenster[y0:y0 + round(hh * s), x0:x0 + round(w * s)].astype(int)
        if feld.size == 0:
            return None
        gelb = int(((feld[..., 2] > 170) & (feld[..., 1] > 130) & (feld[..., 0] < 110)).sum())
        aus[taste] = gelb >= GELB_AB * s * s
    return aus


def lies(leiste: np.ndarray, hoehe: int = REF, k: float = 1.0) -> list[Mitspieler]:
    """`leiste`: BGR-Ausschnitt genau `bereich(...)` mit demselben `k`. Gibt vier Mitspieler von links nach rechts."""
    s = hoehe / REF * k      # innerhalb der Leiste waechst jeder Abstand um k
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
            ult = bool(anteil_gruen > 0.25)   # echtes bool: numpy-Werte lassen sich nicht als JSON speichern
        ergebnis.append(Mitspieler(round(float(leben), 2), ult))
    return ergebnis
