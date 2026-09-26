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


# --- Verfolgen von Bild zu Bild (10-20 Bilder/s) ---------------------------------

FLASH_EINHEITEN = 400
KARTE_EINHEITEN = 14820          # Kantenlaenge der Karte in Spiel-Einheiten (etwa)


@dataclass(frozen=True)
class Sprung:
    """Ein Champion ist zwischen zwei aufeinanderfolgenden Bildern um etwa
    Flash-Weite versetzt - vorher und nachher ruhig. Dashes laufen ueber
    mehrere Bilder, Flash ist sofort da."""
    champion_id: str
    team: str | None
    zeit: float              # Wanduhr des Bildes nach dem Sprung
    weite: float             # Kartenanteil
    x: float
    y: float


class Verfolger:
    """Sucht jeden bekannten Champion nur im Umkreis seiner letzten Position
    (~1 ms), die ganze Karte nur fuer verlorene und nur alle `vollsuche_alle`
    Sekunden. Damit reichen die Takte fuer 15 Bilder/s."""


    def __init__(self, champions: list[tuple[str, str]], hoehe: int = REFERENZ_HOEHE, vollsuche_alle: float = 0.5,
                 verloren_nach: float = 0.4):
        self.champions, self.hoehe, self.vollsuche_alle = champions, hoehe, vollsuche_alle
        self.verloren_nach = verloren_nach  # Aufnahmen mit 1 Bild/s brauchen mehr als live mit 15
        self.umkreis = round(30 * hoehe / REFERENZ_HOEHE)
        self.flash_px = FLASH_EINHEITEN / KARTE_EINHEITEN * round(KARTE * hoehe)
        self.pos: dict[tuple[str, int], tuple[float, int, int, str | None]] = {}  # -> (zeit, cx, cy, team)
        self.verlauf: dict[tuple[str, int], list[tuple[float, int, int]]] = {}
        self._kandidat: dict[tuple[str, int], tuple[float, int, int, int, int]] = {}
        self._letzte_vollsuche = -1e9

    def _lokal(self, karte: np.ndarray, cid: str, cx: int, cy: int) -> tuple[float, int, int] | None:
        v = _vorlage(cid, self.hoehe)
        if v is None:
            return None
        vorlage, maske = v
        d, r, seite = vorlage.shape[0], self.umkreis, karte.shape[0]
        x0, y0 = max(0, cx - d // 2 - r), max(0, cy - d // 2 - r)
        x1, y1 = min(seite, cx + d // 2 + r + 1), min(seite, cy + d // 2 + r + 1)
        fenster = karte[y0:y1, x0:x1]
        if fenster.shape[0] < d or fenster.shape[1] < d:
            return None
        erg = np.nan_to_num(cv2.matchTemplate(fenster, vorlage, cv2.TM_CCOEFF_NORMED, mask=maske),
                            nan=-1.0, posinf=-1.0, neginf=-1.0)
        _, guete, _, (fx, fy) = cv2.minMaxLoc(erg)
        return (guete, x0 + fx + d // 2, y0 + fy + d // 2) if guete >= SCHWELLE else None

    def bild(self, karte: np.ndarray, zeit: float) -> tuple[list[Sichtung], list[Sprung]] | None:
        """Ein neues Minimap-Bild. Gibt None, wenn es dem vorigen gleicht: ein stehendes
        Bild (Ruckler, Aufnahme mit 1 Bild/s in der Generalprobe) darf keine Zeit verstreichen
        lassen - sonst sieht jede Bewegung danach wie ein Flash-Sprung aus."""
        # Exakter Vergleich: ein verkleinerter "Stempel" hielt auch langsames Laufen (1 px je Bild)
        # fuer Stillstand (Flash-Pruefstand 26.09.) - stehende Bilder sind wirklich pixelgleich.
        vorher = getattr(self, "_vorher", None)
        if vorher is not None and vorher.shape == karte.shape and np.array_equal(vorher, karte):
            return None
        self._vorher = karte.copy()
        seite = karte.shape[0]
        gefunden: dict[tuple[str, int], tuple[float, int, int, str | None]] = {}
        # 1. Umkreissuche fuer alle frisch gesehenen
        for schl, (t, cx, cy, team) in list(self.pos.items()):
            if zeit - t > self.verloren_nach:
                continue
            if treffer := self._lokal(karte, schl[0], cx, cy):
                gefunden[schl] = (treffer[0], treffer[1], treffer[2], team)
        # 2. Vollsuche fuer die fehlenden, nicht jedes Bild
        if zeit - self._letzte_vollsuche >= self.vollsuche_alle:
            self._letzte_vollsuche = zeit
            schon = {}
            for k in gefunden:
                schon[k[0]] = schon.get(k[0], 0) + 1
            fehlend = []
            for cid, team in self.champions:  # nur, wer nicht schon per Umkreis gefunden ist
                if schon.get(cid, 0) > 0:
                    schon[cid] -= 1
                else:
                    fehlend.append((cid, team))
            zaehler: dict[str, int] = {}
            for s in finde(karte, fehlend, self.hoehe):
                n = zaehler.get(s.champion_id, 0)
                zaehler[s.champion_id] = n + 1
                cx, cy = round(s.x * seite), round(s.y * seite)
                # schon per Umkreis gefunden? dann nicht doppelt
                if any(k[0] == s.champion_id and abs(v[1] - cx) < 12 and abs(v[2] - cy) < 12
                       for k, v in gefunden.items()):
                    continue
                schl = next((k for k in self.pos if k[0] == s.champion_id and k not in gefunden
                             and (s.team is None or self.pos[k][3] in (None, s.team))), (s.champion_id, n))
                while schl in gefunden:
                    schl = (schl[0], schl[1] + 1)
                gefunden[schl] = (s.guete, cx, cy, s.team)
        # 3. Buch fuehren, Spruenge pruefen
        spruenge = []
        for schl, (guete, cx, cy, team) in gefunden.items():
            alt = self.pos.get(schl)
            v = self.verlauf.setdefault(schl, [])
            if (k := self._kandidat.pop(schl, None)) and abs(cx - k[3]) + abs(cy - k[4]) <= 5:
                # nach dem Sprung ruhig geblieben -> bestaetigt
                spruenge.append(Sprung(schl[0], team, k[0], (k[1] / seite), k[3] / seite, k[4] / seite))
            if alt and zeit - alt[0] <= 0.2:
                weite = ((cx - alt[1]) ** 2 + (cy - alt[2]) ** 2) ** 0.5
                vorher_ruhig = len(v) >= 2 and zeit - v[-2][0] <= 0.45 and \
                    ((v[-1][1] - v[-2][1]) ** 2 + (v[-1][2] - v[-2][2]) ** 2) ** 0.5 <= 5
                if 0.7 * self.flash_px <= weite <= 1.45 * self.flash_px and vorher_ruhig:
                    self._kandidat[schl] = (zeit, int(weite), 0, cx, cy)
            self.pos[schl] = (zeit, cx, cy, team or (alt[3] if alt else None))
            v.append((zeit, cx, cy))
            del v[:-6]
        sichtungen = [Sichtung(schl[0], team, cx / seite, cy / seite, float(g))
                      for schl, (g, cx, cy, team) in gefunden.items()]
        return sichtungen, spruenge


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


def woher(ort_text: str) -> str:
    """'im oberen Fluss' -> 'aus dem oberen Fluss', 'oben' -> 'von oben' - fuer 'kommt ... auf dich zu'."""
    for alt, neu in (("im ", "aus dem "), ("in der ", "aus der "), ("in seinem ", "aus seinem "),
                     ("in eurem ", "aus eurem "), ("in seiner ", "aus seiner "), ("in eurer ", "aus eurer "),
                     ("auf der ", "über die ")):
        if ort_text.startswith(alt):
            return neu + ort_text[len(alt):]
    return f"von {ort_text}" if ort_text in ("oben", "unten") else ort_text


def seite_der_karte(x: float, y: float) -> str:
    """'oben' (Top-Seite: Larven, Herold, Baron) oder 'unten' (Drache, Bot)."""
    return "oben" if x + y < 1.0 else "unten"
