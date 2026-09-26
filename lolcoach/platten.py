"""Turmplatten von der Minimap: jedes Turm-Icon traegt die Zahl der verbleibenden Platten (5 .. 1).

Die Live-API meldet Platten nicht; die Minimap zeigt sie (entdeckt 26.09.2026 beim Auflegen der
Turmpositionen: "5" in jedem Icon, in Partie 7 oben 5 -> 3, dann Turmfall). Seit 26.1 bleiben
Platten bis zum Turmfall, auch an inneren Tuermen (saison2026.md).

Lesen: Ausschnitt um den Turmpunkt, Pixel in Turmfarbe (rot/blau) als Maske, Vergleich mit den
Ziffer-Vorlagen (wissen/platten_ziffern.png, aus 4 Partien gesammelt) mit Verschiebung um ein paar
Pixel. Verdeckt ein Champion- oder Vasallen-Icon die Ziffer, passt keine Vorlage gut genug - dann
bleibt der alte Wert. Platten wachsen nie nach: ein hoeherer Wert als der bekannte zaehlt nicht,
ein niedrigerer erst, wenn ihn zwei Lesungen hintereinander zeigen.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .bewertung import BREITE, HOEHE, TUERME

VORLAGEN_DATEI = Path(__file__).resolve().parent.parent / "wissen" / "platten_ziffern.png"
REF = 570                    # Minimap-Kante, an der die Vorlagen entstanden (4K)
BOX = (-12, -15, 11, 9)      # um den Turmpunkt, bei REF: groesser als die Ziffer, damit sie verschoben passen darf
MINDEST = 0.72               # Korrelation der besten Vorlage (0,62 gab 85-101 Widersprueche je Partie, 0,72 keinen)
ABSTAND = 0.06               # ... und so viel besser als die zweitbeste


def _vorlagen() -> dict[int, np.ndarray]:
    tafel = cv2.imread(str(VORLAGEN_DATEI), cv2.IMREAD_GRAYSCALE)
    if tafel is None:
        return {}
    b = tafel.shape[1] // 5
    # oben (Zeilen 0-3) liegt der Schildrand, nicht die Ziffer
    return {z: (tafel[4:, (z - 1) * b:z * b] > 127).astype(np.float32) for z in range(1, 6)}


_V = _vorlagen()


def maske(karte: np.ndarray, team: str, gx: float, gy: float) -> np.ndarray | None:
    """Farbmaske um den Turmpunkt, auf REF-Massstab gebracht."""
    h, w = karte.shape[:2]
    k = w / REF
    x, y = gx / BREITE * w, (1 - gy / HOEHE) * h
    x0, y0 = int(round(x + BOX[0] * k)), int(round(y + BOX[1] * k))
    x1, y1 = int(round(x + BOX[2] * k)), int(round(y + BOX[3] * k))
    if x0 < 0 or y0 < 0 or x1 > w or y1 > h:
        return None
    c = karte[y0:y1, x0:x1].astype(np.int16)
    b, g, r = c[..., 0], c[..., 1], c[..., 2]
    if team == "CHAOS":
        m = (r > 170) & (r - g > 70) & (r - b > 70)
    else:
        m = (b > 170) & (g > 120) & (r < 140)
    m = m.astype(np.float32)
    if k != 1.0:
        m = cv2.resize(m, (BOX[2] - BOX[0], BOX[3] - BOX[1]), interpolation=cv2.INTER_AREA)
    return m


def lies(karte: np.ndarray, team: str, gx: float, gy: float) -> tuple[int | None, float]:
    """(Platten, Guete) eines Turms; (None, Guete) wenn nichts sicher passt."""
    m = maske(karte, team, gx, gy)
    if m is None or not _V or m.sum() < 8:
        return None, 0.0
    werte = []
    for z, v in _V.items():
        if v.shape[0] > m.shape[0] or v.shape[1] > m.shape[1]:
            continue
        werte.append((float(cv2.matchTemplate(m, v, cv2.TM_CCORR_NORMED).max()), z))
    if not werte:
        return None, 0.0
    werte.sort(reverse=True)
    beste, z = werte[0]
    zweite = werte[1][0] if len(werte) > 1 else 0.0
    if beste >= MINDEST and beste - zweite >= ABSTAND:
        return z, beste
    return None, beste


class Plattenleser:
    """Haelt je Turm den bestaetigten Stand; `lies_karte` einmal alle paar Sekunden."""

    def __init__(self):
        self.stand: dict[tuple[str, str, str], int] = {}
        self._kandidat: dict[tuple[str, str, str], int] = {}

    def lies_karte(self, karte: np.ndarray, stehend=None) -> dict[tuple[str, str, str], int]:
        """`stehend`: Schluessel der Tuerme, die noch stehen (sonst alle). Gibt den Stand zurueck."""
        for schl, (gx, gy) in TUERME.items():
            if stehend is not None and schl not in stehend:
                self.stand.pop(schl, None)
                continue
            z, _ = lies(karte, schl[0], gx, gy)
            if z is None:
                continue
            alt = self.stand.get(schl)
            if alt is None:
                self.stand[schl] = z
            elif z < alt:
                if self._kandidat.get(schl) == z:
                    self.stand[schl] = z
                    self._kandidat.pop(schl, None)
                else:
                    self._kandidat[schl] = z
            else:
                self._kandidat.pop(schl, None)
        return dict(self.stand)
