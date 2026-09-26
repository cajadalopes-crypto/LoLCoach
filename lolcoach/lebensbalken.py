"""Lebensbalken ueber den Koepfen: wie viel Leben hat der Gegner, den du gerade siehst?

Die Live-API kennt nur dein eigenes Leben. Fuer "reicht das fuer den Kill?" braucht der Coach das des
Gegners - und das steht auf dem Bildschirm (erlaubt: nur was du selbst siehst).

Aufbau eines Champion-Balkens (vermessen am eigenen Balken, Spielbild der Camille-Partie, auf 1600 px
Breite verkleinert, 4K-Spiel): links ein dunkles Level-Kaestchen (~16 x 16), rechts daneben der Balken,
78 px breit (geeicht, s. BALKEN) und 8 px hoch, mit Strichen je 100 Leben; darunter der Ressourcenbalken, darueber der Name.
Fuellfarbe: gruen = du, blau = Mitspieler, rot = Gegner. Anteil = Breite der Fuellung / 78.
Gegenprobe: Camille-Bild gelesen 65 %, HUD 617/955 = 65 %; 297 eigene Balken zweier Partien gegen die API: 90 %
innerhalb +-2 % (`werkzeuge/balken_eichen.py`).

Was hier NICHT geht und deshalb verworfen wird: Vasallen-Balken (duenner, kein Level-Kaestchen),
Turm-Balken (breiter als 85 px), rote Schadenszahlen (keine Balkenform). Welcher Gegner es ist, sagt der
Name ueber dem Balken (Windows-Texterkennung); ohne lesbaren Namen bleibt der Balken namenlos.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

BREITE_REF = 1600          # Bildbreite, an der vermessen wurde
# Breite des Lebensbalkens (volle 100 %). Geeicht am eigenen Balken gegen die Live-API (currentHealth/maxHealth):
# 245 Bilder aus zwei Partien (26.09. 19:45 und 21:21), Fuellung / API-Anteil = 78,1 und 78,2 px, Quartile
# 77,8-79,0. Mit den geschaetzten 80 las der Coach jeden Balken ~3 % zu leer - beim Gegner die gefaehrliche Richtung.
BALKEN = 78
# Das letzte Stueck der Fuellung ist oft blass (Saettigung 55-95 statt >110): Live 21:21, 9:30 las 66 % statt 72 %
BLASS = {"feind": ((0, 9), (171, 180)), "freund": ((96, 116),), "ich": ((45, 75),)}
HOEHE = (5, 10)            # Hoehe der Fuellung
KASTEN = (12, 22)          # Kantenlaenge des Level-Kaestchens


@dataclass(frozen=True)
class Balken:
    x: int                  # linke Kante der Fuellung (Bildpixel)
    y: int                  # obere Kante
    anteil: float           # 0..1
    team: str               # "feind", "freund", "ich"
    name: str | None = None


def _masken(bild: np.ndarray) -> dict[str, np.ndarray]:
    hsv = cv2.cvtColor(bild, cv2.COLOR_BGR2HSV)
    rot = cv2.inRange(hsv, (0, 120, 110), (9, 255, 255)) | cv2.inRange(hsv, (171, 120, 110), (180, 255, 255))
    blau = cv2.inRange(hsv, (96, 110, 110), (116, 255, 255))
    gruen = cv2.inRange(hsv, (45, 110, 110), (75, 255, 255))
    return {"feind": rot, "freund": blau, "ich": gruen}


def _kaestchen(bild: np.ndarray, x: int, y: int, k: float) -> bool:
    """Links vor der Fuellung ein dunkles Level-Kaestchen mit heller Ziffer (Vasallen- und Turmbalken
    haben keines)."""
    x0, x1 = int(x - 17 * k), int(x - 3 * k)
    y0, y1 = int(y - 2 * k), int(y + 12 * k)
    if x0 < 0 or y0 < 0 or y1 > bild.shape[0]:
        return False
    teil = bild[y0:y1, x0:x1]
    if teil.size == 0:
        return False
    hell = teil.max(axis=2)
    return float((hell < 90).mean()) >= 0.6 and int((hell > 150).sum()) >= 3


def _balkenform(bild: np.ndarray, x: int, y: int, w: int, h: int, k: float) -> bool:
    """Der ganze Balken (80 px) besteht aus der Fuellung und einem dunklen, leeren Rest - und direkt darueber
    und darunter liegt der dunkle Rahmen. Gras, Effekte und Icons haben diese Form nicht."""
    x1 = int(x + BALKEN * k)
    if x1 > bild.shape[1] or y < 2 or y + h + 2 > bild.shape[0]:
        return False
    rest = bild[y:y + h, x + w:x1]
    if rest.size and float((rest.max(axis=2) < 80).mean()) < 0.7:
        return False
    rahmen = np.concatenate([bild[y - 2:y - 1, x:x1], bild[y + h + 1:y + h + 2, x:x1]], axis=0)
    return float((rahmen.max(axis=2) < 110).mean()) >= 0.5


def _spielfeld(bild: np.ndarray, x: int, y: int) -> bool:
    """Nicht im HUD unten, nicht in der Minimap, nicht in der Leiste oben."""
    hh, ww = bild.shape[:2]
    if y > 0.8 * hh or y < 0.04 * hh:
        return False
    return not (x > 0.82 * ww and y > 0.62 * hh)


def _blasses_ende(hsv: np.ndarray, team: str, x: int, y: int, w: int, h: int, k: float) -> int:
    """Die Fuellung nach rechts verlaengern, solange die Mittelzeile im Farbton des Teams bleibt, nur blasser."""
    zeile, ende = y + h // 2, x + w
    grenze = min(hsv.shape[1], int(x + (BALKEN + 2) * k))

    def fuellung(i: int) -> bool:
        f, s, v = (int(c) for c in hsv[zeile, i])
        return s >= 40 and v >= 90 and any(lo <= f <= hi for lo, hi in BLASS[team])

    while ende < grenze:
        if fuellung(ende):
            ende += 1
            continue
        # der dunkle Strich je 100 Leben (1-2 px) trennt oft das blasse Ende ab (Live 21:21, 9:30)
        weiter = next((i for i in range(ende + 1, min(grenze, ende + 1 + max(2, int(3 * k)))) if fuellung(i)), None)
        if weiter is None:
            break
        ende = weiter + 1
    return ende - x


def finde(bild: np.ndarray) -> list[Balken]:
    """Alle Champion-Lebensbalken im Bild (ohne Namen)."""
    k = bild.shape[1] / BREITE_REF
    aus = []
    hsv = cv2.cvtColor(bild, cv2.COLOR_BGR2HSV)
    for team, m in _masken(bild).items():
        # Striche je 100 Leben trennen die Fuellung: waagrecht zusammenziehen
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((1, max(3, int(4 * k))), np.uint8))
        n, _, st, _ = cv2.connectedComponentsWithStats(m)
        for x, y, w, h, flaeche in st[1:]:
            if not (HOEHE[0] * k <= h <= HOEHE[1] * k) or w < 2 or w > (BALKEN + 5) * k:
                continue
            if flaeche < 0.6 * w * h or not _spielfeld(bild, x, y):
                continue
            w = _blasses_ende(hsv, team, int(x), int(y), int(w), int(h), k)
            if not _kaestchen(bild, x, y, k) or not _balkenform(bild, x, y, w, h, k):
                continue
            aus.append(Balken(int(x), int(y), round(min(1.0, float(w) / (BALKEN * k)), 2), team))
    return aus


def mana(bild: np.ndarray, b: Balken) -> float | None:
    """Mana unter dem Lebensbalken: ein duenner hellblauer Balken 10-11 px darunter (1600 px Bildbreite), gleiche
    linke Kante, 80 px = voll. None, wenn keiner da ist (Champion ohne Mana, oder gar kein Champion-Balken).
    Vermessen an 30 Gegner-Balken der Live-Partie 26.09.: Heimerdinger sichtbar ~96 %, gelesen 94 %."""
    k = bild.shape[1] / BREITE_REF
    hsv = cv2.cvtColor(bild[max(0, b.y):min(bild.shape[0], b.y + int(16 * k) + 1),
                            b.x:min(bild.shape[1], b.x + int(82 * k))], cv2.COLOR_BGR2HSV)
    for dy in range(int(8 * k), min(hsv.shape[0], int(15 * k) + 1)):
        zeile = hsv[dy]
        blau = (zeile[:, 0] >= 88) & (zeile[:, 0] <= 112) & (zeile[:, 1] >= 70) & (zeile[:, 2] >= 130)
        if blau[:max(1, int(4 * k))].any() and int(blau.sum()) >= 3:
            return round(min(1.0, (int(np.nonzero(blau)[0].max()) + 1) / (BALKEN * k)), 2)
    return None


def mit_namen(bild: np.ndarray, balken: list[Balken], namen: list[str], leser) -> list[Balken]:
    """Den Namen ueber jedem Balken lesen (Windows-Texterkennung) und einem der `namen` zuordnen."""
    import difflib
    k = bild.shape[1] / BREITE_REF
    aus = []
    klein = {n.lower().replace(" ", "").replace("'", ""): n for n in namen}
    for b in balken:
        x0, x1 = max(0, int(b.x - 20 * k)), min(bild.shape[1], int(b.x + (BALKEN + 10) * k))
        y0, y1 = max(0, int(b.y - 16 * k)), max(0, int(b.y - 2 * k))
        name = None
        if y1 > y0 and x1 > x0 and leser is not None:
            try:
                zeilen = leser.zeilen(bild[y0:y1, x0:x1], vergroessern=3.0)
            except Exception:
                zeilen = []
            for z in zeilen:
                wort = z.lower().replace(" ", "").replace("'", "")
                treffer = difflib.get_close_matches(wort, list(klein), n=1, cutoff=0.7)
                if treffer:
                    name = klein[treffer[0]]
                    break
        aus.append(Balken(b.x, b.y, b.anteil, b.team, name))
    return aus


def namen_lesen(bild: np.ndarray, balken: list[Balken], leser) -> list[tuple[Balken, str]]:
    """(Balken, gelesener Text ueber ihm) - roh, fuer die Zuordnung im Lagebild."""
    k = bild.shape[1] / BREITE_REF
    aus = []
    for b in balken:
        x0, x1 = max(0, int(b.x - 20 * k)), min(bild.shape[1], int(b.x + (BALKEN + 10) * k))
        y0, y1 = max(0, int(b.y - 16 * k)), max(0, int(b.y - 2 * k))
        text = ""
        if y1 > y0 and x1 > x0 and leser is not None:
            try:
                text = " ".join(leser.zeilen(bild[y0:y1, x0:x1], vergroessern=3.0))
            except Exception:
                text = ""
        aus.append((b, text))
    return aus


def zuordnen(text: str, spieler) -> object | None:
    """Gelesenen Namen einem Spieler zuordnen (Champion- oder Spielername)."""
    import difflib
    wort = text.lower().replace(" ", "").replace("'", "")
    if len(wort) < 3:
        return None
    namen = {}
    for s in spieler:
        for n in {s.champion, s.champion_id, s.name.split("#")[0]}:
            namen[n.lower().replace(" ", "").replace("'", "")] = s
    treffer = difflib.get_close_matches(wort, list(namen), n=1, cutoff=0.7)
    return namen[treffer[0]] if treffer else None


# --- Flash auf dem Spielbild ---------------------------------------------------------------------------------

@dataclass(frozen=True)
class SchirmSprung:
    zeit: float             # Wanduhr des Bildes, in dem er gelandet war
    team: str
    anteil: float           # sein Leben (erkennt ihn vor und nach dem Sprung wieder)
    von: tuple[int, int]
    nach: tuple[int, int]
    weite: float            # Anteil der Bildbreite


class Balkenspur:
    """Flash auf dem Spielbild: der Lebensbalken eines Gegners verschwindet an einer Stelle und steht im naechsten
    Bild (~80 ms spaeter) 250-600 px weiter - mit demselben Leben. So schnell ist kein Dash (die laufen ueber
    mehrere Bilder), und die Minimap sieht es im Kampf nicht: dort liegen die Icons uebereinander (gemessen 26.09.:
    von 12 eigenen Flashes erkannte die Minimap 1). Eine Kameradrehung verschiebt ALLE Balken - deshalb braucht
    es einen zweiten Balken, der ruhig bleibt (meist dein eigener). Bestaetigt, wenn er im Folgebild am Landepunkt
    bleibt und am Absprung keiner mehr steht."""

    SPRUNG_MIN = 0.16      # Anteil der Bildbreite in einem Bild (~250 px bei 1600)
    SPRUNG_MAX = 0.40
    RUHIG = 0.03           # so weit darf sich ein Bezugsbalken zwischen zwei Bildern bewegen
    LEBEN_TOL = 0.06
    BILD_MAX = 0.15        # Sekunden zwischen zwei Bildern, sonst kein Vergleich

    def __init__(self):
        self._vorher: tuple[float, list[Balken]] | None = None
        self._kandidat: list[tuple[float, str, float, tuple[int, int], tuple[int, int], float]] = []

    def neu(self, zeit: float, balken: list[Balken], breite: int) -> list[SchirmSprung]:
        aus = []
        for t0, team, anteil, von, nach, weite in self._kandidat:
            da = any(b.team == team and abs(b.x - nach[0]) + abs(b.y - nach[1]) <= 1.5 * self.RUHIG * breite
                     and abs(b.anteil - anteil) <= self.LEBEN_TOL for b in balken)
            zurueck = any(b.team == team and abs(b.x - von[0]) + abs(b.y - von[1]) <= self.RUHIG * breite
                          and abs(b.anteil - anteil) <= self.LEBEN_TOL for b in balken)
            if da and not zurueck:
                aus.append(SchirmSprung(t0, team, anteil, von, nach, weite))
        self._kandidat = []
        vor, self._vorher = self._vorher, (zeit, list(balken))
        if vor is None or not (0 < zeit - vor[0] <= self.BILD_MAX):
            return aus
        frei_alt, frei_neu, ruhig = list(vor[1]), list(balken), 0
        for a in vor[1]:
            b = min((b for b in frei_neu if b.team == a.team and abs(b.anteil - a.anteil) <= self.LEBEN_TOL),
                    key=lambda b: abs(b.x - a.x) + abs(b.y - a.y), default=None)
            if b is not None and abs(b.x - a.x) + abs(b.y - a.y) <= self.RUHIG * breite:
                frei_alt.remove(a)
                frei_neu.remove(b)
                ruhig += 1
        if not ruhig:
            return aus      # ohne ruhigen Bezug ist ein Sprung nicht von einer Kameradrehung zu trennen
        for a in (x for x in frei_alt if x.team == "feind"):
            kand = [b for b in frei_neu if b.team == "feind" and abs(b.anteil - a.anteil) <= self.LEBEN_TOL
                    and self.SPRUNG_MIN * breite <= ((b.x - a.x) ** 2 + (b.y - a.y) ** 2) ** 0.5 <= self.SPRUNG_MAX * breite]
            if len(kand) == 1:
                b = kand[0]
                weite = ((b.x - a.x) ** 2 + (b.y - a.y) ** 2) ** 0.5 / breite
                self._kandidat.append((zeit, "feind", b.anteil, (a.x, a.y), (b.x, b.y), round(weite, 3)))
        return aus
