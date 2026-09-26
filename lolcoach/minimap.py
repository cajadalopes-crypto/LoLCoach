"""Minimap: wo steht wer - so, wie der Spieler es selbst auf der Minimap sieht.

Erkennung per Bildvergleich: fuer die zehn Champions der Partie (die API
nennt sie) das Riot-Portraet aus Data Dragon, kreisfoermig maskiert, gegen
den Minimap-Ausschnitt. Gegner im Nebel sind auf der Minimap nicht zu sehen
- also auch fuer den Coach nicht. Genau das ist die Grenze.

Vermessen am 26.09.2026 an Carlos' Einstellungen (4K, MinimapScale 1.5,
unten rechts): Minimap 570 px im Quadrat, 27 px vom rechten und 29 px vom
unteren Fensterrand, Portraet 48 px. Alles skaliert mit der Fensterhoehe.
Gemessen: sichtbare Champions 0,93-0,98 Uebereinstimmung, unsichtbare
unter 0,80.

Kartenkoordinaten: (x, y) in 0..1, (0, 0) oben links. Blau (ORDER) hat
seine Basis unten links, Rot oben rechts.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from . import ddragon

STAND = 1                          # erhoehen, wenn sich die Erkennung aendert (verwirft Caches)
REFERENZ_HOEHE = 2160
KARTE = 570 / REFERENZ_HOEHE
RAND_RECHTS = 27 / REFERENZ_HOEHE
RAND_UNTEN = 29 / REFERENZ_HOEHE
PORTRAET = 48 / REFERENZ_HOEHE     # ganzes Portraet auf der Minimap
AUSSCHNITT = 40 / REFERENZ_HOEHE   # davon verglichen: die Mitte (Ring und Rand stoeren)
SCHWELLE = 0.85


@dataclass(frozen=True)
class Sichtung:
    champion_id: str
    team: str | None       # aus der Ringfarbe, falls der Champion doppelt ist; sonst None
    x: float
    y: float
    guete: float


def kartenrechteck(fenster_breite: int, fenster_hoehe: int) -> tuple[int, int, int, int]:
    """(links, oben, rechts, unten) der Minimap im Fenster."""
    h = fenster_hoehe
    r, u = fenster_breite - round(RAND_RECHTS * h), fenster_hoehe - round(RAND_UNTEN * h)
    s = round(KARTE * h)
    return r - s, u - s, r, u


def _champion_bild(champion_id: str) -> np.ndarray | None:
    v = ddragon.version()
    if v is None:
        return None
    pfad = ddragon.ABLAGE / v / "champion" / f"{champion_id}.png"
    if not pfad.exists():
        import urllib.request
        pfad.parent.mkdir(parents=True, exist_ok=True)
        try:
            urllib.request.urlretrieve(f"{ddragon.CDN}/cdn/{v}/img/champion/{champion_id}.png", pfad)
        except OSError:
            return None
    return cv2.imread(str(pfad))


@lru_cache(maxsize=64)
def _vorlage(champion_id: str, hoehe: int) -> tuple[np.ndarray, np.ndarray] | None:
    bild = _champion_bild(champion_id)
    if bild is None:
        return None
    ganz, d = round(PORTRAET * hoehe), round(AUSSCHNITT * hoehe)
    klein = cv2.resize(bild, (ganz, ganz), interpolation=cv2.INTER_AREA)
    o = (ganz - d) // 2
    vorlage = np.ascontiguousarray(klein[o:o + d, o:o + d])
    maske = np.zeros((d, d), np.uint8)
    cv2.circle(maske, (d // 2, d // 2), d // 2 - 1, 255, -1)
    return vorlage, maske


def _ringfarbe(karte: np.ndarray, cx: int, cy: int, radius: int) -> str | None:
    """Blau oder Rot, aus den Pixeln knapp ausserhalb des Portraets."""
    winkel = np.linspace(0, 2 * np.pi, 48, endpoint=False)
    xs = np.clip((cx + radius * np.cos(winkel)).astype(int), 0, karte.shape[1] - 1)
    ys = np.clip((cy + radius * np.sin(winkel)).astype(int), 0, karte.shape[0] - 1)
    b, _, r = karte[ys, xs].astype(float).mean(axis=0)
    if abs(r - b) < 25:
        return None
    return "ORDER" if b > r else "CHAOS"


@lru_cache(maxsize=64)
def _grobvorlage(champion_id: str, hoehe: int) -> np.ndarray | None:
    """Inneres Quadrat des Portraets in halber Aufloesung - unmaskiert und
    damit etwa zehnmal schneller als der maskierte Vergleich."""
    v = _vorlage(champion_id, hoehe)
    if v is None:
        return None
    d = v[0].shape[0]
    q = round(d * 0.66)
    o = (d - q) // 2
    return cv2.resize(v[0][o:o + q, o:o + q], (q // 2, q // 2), interpolation=cv2.INTER_AREA)


GROB_SCHWELLE = 0.45
KANDIDATEN = 3


def finde(karte: np.ndarray, champions: list[tuple[str, str]], hoehe: int = REFERENZ_HOEHE) -> list[Sichtung]:
    """`karte`: BGR-Ausschnitt der Minimap. `champions`: (champion_id, team) der Partie.
    Gibt je sichtbarem Champion eine Sichtung; doppelte Champions (Bot-Partien)
    werden ueber die Ringfarbe getrennt.

    Zwei Stufen: grob (halbe Aufloesung, inneres Quadrat, ein paar Kandidaten),
    dann fein (maskiertes Portraet in voller Aufloesung, nur um die Kandidaten)."""
    seite = karte.shape[0]
    halb = cv2.resize(karte, (seite // 2, seite // 2), interpolation=cv2.INTER_AREA)
    anzahl: dict[str, int] = {}
    for cid, _ in champions:
        anzahl[cid] = anzahl.get(cid, 0) + 1
    sichtungen = []
    for cid, n in anzahl.items():
        v, grob = _vorlage(cid, hoehe), _grobvorlage(cid, hoehe)
        if v is None or grob is None:
            continue
        vorlage, maske = v
        d, g = vorlage.shape[0], grob.shape[0]
        roh = cv2.matchTemplate(halb, grob, cv2.TM_CCOEFF_NORMED)
        treffer = []
        for _ in range(KANDIDATEN + n - 1):
            _, wert, _, (gx, gy) = cv2.minMaxLoc(roh)
            if wert < GROB_SCHWELLE:
                break
            cv2.rectangle(roh, (gx - g, gy - g), (gx + g, gy + g), -1.0, -1)
            # Mitte der Grobfundstelle in voller Aufloesung, dann fein im Fenster +-4 px
            cx, cy = gx * 2 + g, gy * 2 + g
            x0, y0 = max(0, cx - d // 2 - 4), max(0, cy - d // 2 - 4)
            fenster = karte[y0:min(seite, cy + d // 2 + 5), x0:min(seite, cx + d // 2 + 5)]
            if fenster.shape[0] < d or fenster.shape[1] < d:
                continue
            fein = cv2.matchTemplate(fenster, vorlage, cv2.TM_CCOEFF_NORMED, mask=maske)
            fein = np.nan_to_num(fein, nan=-1.0, posinf=-1.0, neginf=-1.0)
            _, guete, _, (fx, fy) = cv2.minMaxLoc(fein)
            if guete >= SCHWELLE:
                treffer.append((guete, x0 + fx + d // 2, y0 + fy + d // 2))
        treffer.sort(reverse=True)
        genommen: list[tuple[int, int]] = []
        for guete, cx, cy in treffer:
            if len(genommen) >= n or any(abs(cx - a) < d and abs(cy - b) < d for a, b in genommen):
                continue
            genommen.append((cx, cy))
            team = _ringfarbe(karte, cx, cy, round(PORTRAET * hoehe / 2) + 2) if n > 1 else None
            sichtungen.append(Sichtung(cid, team, cx / seite, cy / seite, float(guete)))
    return sichtungen


# --- Orte in Worten ------------------------------------------------------------

def ort(x: float, y: float, aus_sicht: str | None = None) -> str:
    """Grobe Beschreibung wie ein Coach sie sagt. `aus_sicht`: eigenes Team,
    dann heisst der Jungle 'dein'/'sein'."""
    if x < 0.22 and y > 0.78:
        return "in der blauen Basis" if aus_sicht is None else ("in eurer Basis" if aus_sicht == "ORDER" else "in seiner Basis")
    if x > 0.78 and y < 0.22:
        return "in der roten Basis" if aus_sicht is None else ("in eurer Basis" if aus_sicht == "CHAOS" else "in seiner Basis")
    if x < 0.13 or y < 0.13:
        return "oben"
    if x > 0.87 or y > 0.87:
        return "unten"
    oben = x + y < 1.0                      # oberhalb der Mid-Lane
    d_mid, d_fluss = abs(x + y - 1.0), abs(x - y)   # Mid-Lane: x+y=1, Fluss: x=y
    if d_mid < 0.07 and d_fluss < 0.07:
        return "in der Flussmitte"
    if d_fluss < 0.08 and d_fluss <= d_mid:  # Partie 3: "Mid-Lane und oberer Fluss unterscheiden"
        return "im oberen Fluss" if oben else "im unteren Fluss"
    if d_mid < 0.08:
        return "auf der Mid-Lane"
    blau = y > x                            # unterhalb des Flusses = blaue Seite
    haelfte = "oberen" if oben else "unteren"
    if aus_sicht is None:
        return f"im {haelfte} {'blauen' if blau else 'roten'} Jungle"
    eigen = (blau and aus_sicht == "ORDER") or (not blau and aus_sicht == "CHAOS")
    return f"in {'eurem' if eigen else 'seinem'} {haelfte} Jungle"


def seite_der_karte(x: float, y: float) -> str:
    """'oben' (Top-Seite: Larven, Herold, Baron) oder 'unten' (Drache, Bot)."""
    return "oben" if x + y < 1.0 else "unten"
