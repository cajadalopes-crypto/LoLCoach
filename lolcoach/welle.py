"""Wellen-Zustand aus den Vasallen-Punkten der Minimap.

Carlos: "Er soll mir immer situativ sagen, wie ich die Welle genau vorbereite." Dafuer
muss der Coach wissen, wo die Wellen stehen - die Live-API sagt es nicht, die Minimap
zeigt es: Vasallen sind kleine blaue und rote Punkte (~8 px bei 4K) entlang der Lanes.

Erkennung:
  - Farbe (Blau/Rot wie die Vasallen), kleine runde Flecken,
  - was ueber ~20 s an derselben Stelle leuchtet, ist ein Icon (Turm, Inhibitor) und
    wird ausgeblendet (gleitender Mittelwert je Pixel),
  - nichts in der Naehe eines Champion-Portraets (dessen Ring hat dieselben Farben),
  - jeder Punkt wird auf die naechste Lane projiziert: s = 0 an der blauen, 1 an der roten Basis.
Daraus je Lane: wo sich die Wellen treffen, wer wie viele hat, wer schiebt.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

# Lanes als Linienzuege in Kartenanteilen, von der blauen zur roten Basis
LANES = {
    "Top": [(0.07, 0.80), (0.07, 0.25), (0.15, 0.15), (0.25, 0.07), (0.80, 0.07)],
    "Mid": [(0.25, 0.75), (0.75, 0.25)],
    "Bot": [(0.20, 0.93), (0.75, 0.93), (0.85, 0.85), (0.93, 0.75), (0.93, 0.20)],
}
LANE_ABSTAND = 0.045          # weiter weg von der Lane: kein Lane-Vasall (Jungle, Fluss)
TURM_AUSSEN = (0.35, 0.65)    # grob: s der aeusseren Tuerme (blau, rot)
STATISCH_AB = 0.8             # Anteil der Zeit, ab dem ein Pixel als Icon gilt
GEDAECHTNIS = 0.06            # Gewicht eines neuen Bildes im gleitenden Mittel (~1 Bild/s -> ~16 s)
REF = 570                     # Minimap-Kante bei 4K; Flaechen skalieren mit (Kante/REF)^2


@dataclass(frozen=True)
class LaneZustand:
    lane: str
    blau: int                 # Vasallen je Seite (gezaehlt)
    rot: int
    front: float | None       # s, wo sich die Wellen treffen / die vorderste Welle steht
    schiebt: str | None       # "blau", "rot" oder None (steht)

    def worte(self, mein_team: str) -> str:
        """Aus Sicht des Spielers: 'eure 6 gegen seine 2, kurz vor seinem Turm'."""
        blau_ist_wir = mein_team == "ORDER"
        wir, die = (self.blau, self.rot) if blau_ist_wir else (self.rot, self.blau)
        if wir == 0 and die == 0:
            return "keine Welle zu sehen"
        s = self.front if blau_ist_wir else (1 - self.front if self.front is not None else None)
        if s is None:
            ort = "?"
        elif s >= 0.72:
            ort = "tief bei seinem Turm"
        elif s >= TURM_AUSSEN[1] - 0.06:
            ort = "an seinem Turm"
        elif s > 0.55:
            ort = "auf seiner Haelfte"
        elif s >= 0.45:
            ort = "in der Mitte der Lane"
        elif s > TURM_AUSSEN[0] + 0.06:
            ort = "auf deiner Haelfte"
        elif s > 0.28:
            ort = "an deinem Turm"
        else:
            ort = "tief bei deinem Turm"
        return f"eure {wir} gegen seine {die}, {ort}"


def _projektion(x: float, y: float) -> tuple[str, float, float] | None:
    """(Lane, s 0..1, Abstand) der naechsten Lane, oder None."""
    bestes = None
    for lane, punkte in LANES.items():
        laengen = [np.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(punkte, punkte[1:])]
        gesamt, bis = sum(laengen), 0.0
        for (a, b), l in zip(zip(punkte, punkte[1:]), laengen):
            dx, dy = b[0] - a[0], b[1] - a[1]
            t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / (l * l)))
            px, py = a[0] + t * dx, a[1] + t * dy
            d = np.hypot(x - px, y - py)
            if bestes is None or d < bestes[2]:
                bestes = (lane, (bis + t * l) / gesamt, d)
            bis += l
    return bestes if bestes and bestes[2] <= LANE_ABSTAND else None


class Wellenleser:
    def __init__(self):
        self._mittel: np.ndarray | None = None
        self.bilder = 0

    def punkte(self, karte: np.ndarray, champions: list[tuple[float, float]] = ()) -> list[tuple[str, float, float]]:
        """(team, x, y) je Vasall. Pflegt nebenbei die Icon-Maske (ein Aufruf je Sekunde reicht)."""
        seite = karte.shape[0]
        hsv = cv2.cvtColor(karte, cv2.COLOR_BGR2HSV)
        blau = cv2.inRange(hsv, (95, 120, 170), (112, 255, 255))
        rot = cv2.inRange(hsv, (0, 130, 150), (8, 255, 255)) | cv2.inRange(hsv, (172, 130, 150), (180, 255, 255))
        jetzt = ((blau | rot) > 0).astype(np.float32)
        if self._mittel is None or self._mittel.shape != jetzt.shape:
            self._mittel = jetzt.copy()
        else:
            self._mittel = (1 - GEDAECHTNIS) * self._mittel + GEDAECHTNIS * jetzt
        self.bilder += 1
        statisch = cv2.dilate((self._mittel > STATISCH_AB).astype(np.uint8), np.ones((5, 5), np.uint8))
        f = (seite / REF) ** 2
        aus = []
        for team, maske in (("blau", blau), ("rot", rot)):
            maske = maske.copy()
            maske[statisch > 0] = 0
            n, _, st, cen = cv2.connectedComponentsWithStats(maske)
            for s, (cx, cy) in zip(st[1:], cen[1:]):
                flaeche, fuell = s[4], s[4] / max(1, s[2] * s[3])
                if not (22 * f <= flaeche <= 75 * f and fuell >= 0.5 and max(s[2], s[3]) <= 13 * seite / REF):
                    continue
                x, y = cx / seite, cy / seite
                if any(abs(x - a) + abs(y - b) < 0.05 for a, b in champions):
                    continue
                aus.append((team, float(x), float(y)))
        return aus

    @property
    def bereit(self) -> bool:
        """Erst nach ~20 Bildern ist die Icon-Maske gelernt."""
        return self.bilder >= 20


def zustaende(punkte: list[tuple[str, float, float]]) -> dict[str, LaneZustand]:
    je_lane: dict[str, dict[str, list[float]]] = {l: {"blau": [], "rot": []} for l in LANES}
    for team, x, y in punkte:
        if pr := _projektion(x, y):
            je_lane[pr[0]][team].append(pr[1])
    aus = {}
    for lane, t in je_lane.items():
        b, r = sorted(t["blau"]), sorted(t["rot"])
        if b and r:
            front = (b[-1] + r[0]) / 2 if b[-1] <= r[0] + 0.05 else (b[-1] + r[0]) / 2
            schiebt = "blau" if len(b) >= len(r) + 2 else "rot" if len(r) >= len(b) + 2 else None
        elif b:
            front, schiebt = b[-1], "blau"
        elif r:
            front, schiebt = r[0], "rot"
        else:
            front, schiebt = None, None
        aus[lane] = LaneZustand(lane, len(b), len(r), None if front is None else round(front, 3), schiebt)
    return aus


LANE_DER_ROLLE = {"TOP": "Top", "MIDDLE": "Mid", "BOTTOM": "Bot", "UTILITY": "Bot"}
