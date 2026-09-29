"""Objective-Symbole der Minimap (Auftrag 018, 1): lebt Herold/Baron/Larven (oben) oder der Drache (unten)?

Carlos, 183125 17:50: "Natuerlich sieht man ihn, das ist das lila Symbol." Solange ein Objective lebt, zeigt die
Minimap in seiner Grube ein Symbol (oben lila/pink: Larven, Herold, Baron, manchmal mit goldenem Rand; unten das
Drachen-Symbol in der Farbe der Art, hell auf dunkler Scheibe); vor dem Spawn eine weisse Uhr ("50", "1:52"); danach
ist die Grube leer: nur Fluss (r < 60) oder Nebel. Eigene Sicht, erlaubt.

`lies(karte)` gibt je Grube "symbol" / "timer" / "leer" / "verdeckt" (ein Champion-Portraet liegt darueber). Die
Schwellen sind Anteile am Fenster und an den Bildern von 8 Aufnahmen gegen die Ereignisse der API geeicht
(`werkzeuge/objsymbole_eichung.py`, Ergebnis in `buecher/messungen.md`, Auftrag 018).
"""
from __future__ import annotations

import numpy as np

# Mitte der Gruben in Anteilen der Minimap (570er Bild: oben 188/165, unten 385/402) und der Suchradius
GRUBEN = {"oben": (0.330, 0.290), "unten": (0.675, 0.705)}
RADIUS = 0.042
# Anteile am Fenster: lila (Symbol oben), hell (Drachen-Symbol: alle Kanaele >= 80 und getoent), weiss (Uhr, grau),
# ring (roter/blauer Rand eines Champion-Portraets)
SCHWELLEN = {"lila": 0.005, "hell": 0.015, "weiss": 0.06, "ring": 0.02}


def merkmale(karte: np.ndarray, grube: str) -> dict[str, float]:
    """Anteile der Pixel im Fenster der Grube. `karte`: RGB, uint8."""
    h, w = karte.shape[:2]
    fx, fy = GRUBEN[grube]
    r = max(6, int(RADIUS * w))
    cx, cy = int(fx * w), int(fy * h)
    f = karte[max(0, cy - r):cy + r, max(0, cx - r):cx + r].astype(np.int16)
    if f.size == 0:
        return {k: 0.0 for k in SCHWELLEN}
    n = f.shape[0] * f.shape[1]
    rr, gg, bb = f[..., 0], f[..., 1], f[..., 2]
    mx = np.maximum(np.maximum(rr, gg), bb)
    mn = np.minimum(np.minimum(rr, gg), bb)
    lila = (rr > 140) & (bb > 140) & (gg < 120) & (bb - gg > 50)
    weiss = (mn > 150) & (mx - mn < 30)                   # die Uhr ist grau-weiss, die Symbole sind getoent
    hell = (mn >= 80) & (mx - mn >= 30)
    ring = ((rr > 200) & (gg < 90) & (bb < 90)) | ((bb > 190) & (rr < 120) & (bb - rr > 100))
    return {"lila": round(float(lila.sum()) / n, 4), "hell": round(float(hell.sum()) / n, 4),
            "weiss": round(float(weiss.sum()) / n, 4), "ring": round(float(ring.sum()) / n, 4)}


def urteil(grube: str, m: dict[str, float], s: dict | None = None) -> str:
    s = s or SCHWELLEN
    if grube == "oben" and m["lila"] >= s["lila"]:
        return "symbol"
    if m["ring"] >= s["ring"]:
        return "verdeckt"
    if m["weiss"] >= s["weiss"]:                          # vor "hell": der Rand der Ziffern ist vom Fluss getoent
        return "timer"
    return "symbol" if grube == "unten" and m["hell"] >= s["hell"] else "leer"


def lies(karte: np.ndarray) -> dict[str, str]:
    return {g: urteil(g, merkmale(karte, g)) for g in GRUBEN}


class Grubenleser:
    """Stand je Grube, geglaettet: ein Wechsel gilt erst, wenn `bestaetigen` Lesungen hintereinander ihn zeigen;
    "verdeckt" aendert nichts. `lies_bgr` gibt den ganzen Stand zurueck, wenn sich etwas geaendert hat, sonst None."""

    def __init__(self, bestaetigen: int = 2):
        self.bestaetigen = bestaetigen
        self.stand: dict[str, str] = {}
        self._kandidat: dict[str, tuple[str, int]] = {}

    def lies_bgr(self, karte: np.ndarray) -> dict[str, str] | None:
        neu = False
        for g, z in lies(np.ascontiguousarray(karte[..., ::-1])).items():
            if z == "verdeckt" or z == self.stand.get(g):
                self._kandidat.pop(g, None)
                continue
            k, n = self._kandidat.get(g, (z, 0))
            n = n + 1 if k == z else 1
            self._kandidat[g] = (z, n)
            if n >= self.bestaetigen:
                self.stand[g] = z
                self._kandidat.pop(g, None)
                neu = True
        return dict(self.stand) if neu else None
