"""Neue Wahrnehmung fuer das Makro-Gehirn (Auftrag 033): eigene Wards, Trinket-Ladungen, Objective-Kopfgeld.

Nur Lesen - der Coach drueckt nichts (CLAUDE.md). Jeder Leser ist eine reine Funktion eines Bildes (Minimap oder
Spielfenster, BGR) und wurde an beschrifteten Bildern aus Carlos' Aufnahmen gemessen (werkzeuge/sehen_eichung.py,
buecher/challenger/phase3b_bericht.md). Was dort nicht verlaesslich war, ist in lolcoach/makro/wahrnehmung.py als
"nicht verlaesslich" vermerkt - die Entscheidung schweigt dann ohne die Eingabe.

Minimap-Masse als Anteil der Kante (die Minimap waechst mit MinimapScale; Bezug 570 px wie welle.REF).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

REF = 570

# ---------------------------------------------------------------- Wards des Teams (Minimap)
# Drei Symbole in Teamfarbe (dein Team ist auf der Minimap immer blau), je 25 x 25 px bei 570, als Vorlagen in
# wissen/ward_vorlagen.png (Median aus 79 beschrifteten Funden, 30.09.):
#   "hell"      Raute ueber Y, hell (Helligkeit ~215) - so erscheint jedes frisch gesetzte Ward
#   "matt"      dasselbe Y, matt (Helligkeit ~145)
#   Hell/matt heisst NICHT eigenes/fremdes Ward (erst vermutet, dann gemessen: von 135 hellen tauchten nur 8 neben
#   Carlos' Icon auf, werkzeuge/ward_spur_probe.py) - wem ein Ward gehoert, sagt die Wardspur (Ort + Trinket-Ladung).
#   "kontrolle" Oval mit Schraegstrich: Kontrollauge (steht bis 28 min am selben Ort; in 101426 ohne blauen Trinket
#               im Team)
#   "blass"     das Y nur noch als Umriss: ein Ward wird so und bleibt danach noch ueber eine Minute am selben Ort
#               (vier Verlaeufe, Stichprobe 3) - es ist also noch da; wem es gehoert, weiss nur die Spur davor
# Erst gesucht wurde mit Farbschwellen: im Fluss verschmilzt das Ward mit dem Flussblau und der Kopf des Y zerfaellt
# vom Koerper (Treffer 75 %). Der Vorlagenabgleich (normierte Korrelation, nur auf den Pixeln des Symbols) trennt:
# echte Wards 0,6-0,95, Vasallen und Champion-Ringe hoechstens 0,53 (buecher/challenger/sehen/, phase3b_bericht.md).
VORLAGEN_DATEI = Path(__file__).resolve().parent.parent / "wissen" / "ward_vorlagen.png"
WARD_ARTEN = ("hell", "matt", "kontrolle", "blass")
WARD_SCHWELLE = 0.60
WARD_ABSTAND = 10 / REF          # zwei Funde naeher als das sind ein Ward
BASEN = ((0.0, 0.76, 0.24, 1.0), (0.76, 0.0, 1.0, 0.24))   # dort liegen Nexus-/Inhibitor-/Turm-Symbole


@dataclass(frozen=True)
class Ward:
    x: float                      # Anteil der Minimap-Kante (Mitte des Symbols)
    y: float
    art: str = "hell"             # hell / matt / kontrolle / blass
    guete: float = 1.0            # Korrelation mit der Vorlage


_VORLAGEN: list | None = None


def _vorlagen() -> list:
    global _VORLAGEN
    if _VORLAGEN is None:
        tafel = cv2.imread(str(VORLAGEN_DATEI))
        k = tafel.shape[0]
        _VORLAGEN = []
        for i, art in enumerate(WARD_ARTEN):
            t = tafel[:, i * k:(i + 1) * k]
            blau = cv2.inRange(cv2.cvtColor(t, cv2.COLOR_BGR2HSV), (95, 120, 90), (115, 255, 255))
            _VORLAGEN.append((art, t.astype(np.float32), cv2.dilate(blau, np.ones((3, 3), np.uint8))))
    return _VORLAGEN


def wards(karte: np.ndarray, schwelle: float = WARD_SCHWELLE) -> list[Ward]:
    """Wards deines Teams auf der Minimap (BGR, beliebige Kante - wird auf 570 gebracht)."""
    k = karte if karte.shape[0] == REF else cv2.resize(karte, (REF, REF), interpolation=cv2.INTER_AREA)
    # der weisse Kamerarahmen (1-2 px) zerschneidet ein Symbol, das er kreuzt: durch die Umgebung ersetzen
    weiss = k.min(axis=2) > 200
    if weiss.any():
        k = k.copy()
        k[weiss] = cv2.medianBlur(k, 5)[weiss]
    k = k.astype(np.float32)
    kand = []
    for art, t, m in _vorlagen():
        r = np.nan_to_num(cv2.matchTemplate(k, t, cv2.TM_CCOEFF_NORMED, mask=m), nan=0, posinf=0, neginf=0)
        h = t.shape[0] // 2
        ys, xs = np.nonzero(r >= schwelle)
        kand += [(float(r[y, x]), (x + h) / REF, (y + h) / REF, art) for y, x in zip(ys, xs)]
    aus: list[Ward] = []
    for g, x, y, art in sorted(kand, reverse=True):
        if any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in BASEN):
            continue
        if all((x - w.x) ** 2 + (y - w.y) ** 2 > WARD_ABSTAND ** 2 for w in aus):
            aus.append(Ward(round(float(x), 4), round(float(y), 4), art, round(float(g), 3)))
    return aus


# ---------------------------------------------------------------- Trinket-Ladungen (HUD)
# Das Trinket-Feld oben rechts im Item-Raster, die Ladungszahl klein unten rechts darin (vermessen 30.09. an
# Schirmbildern 134020: Symbol-Mitte (984, 837) bei 1600 x 900). Wie hud.QUEST: (Mitte x relativ zur Fenstermitte,
# Mitte y als Abstand vom unteren Rand, halbe Kante) bei 2160.
TRINKET = (442, 146, 34)
REF_HOEHE = 2160
# Die Ladungszahl (x 16-27, y 17-28 im auf 28 px gebrachten Feld - so klein wie in den Schirmbildern 1600 x 900) wird
# per Korrelation mit drei Klassenmitteln verglichen: 0 (blaue/dunkle Aufladung, Uhr in der Mitte), 1, 2.
# Vorlagen aus 80 beschrifteten Schirmbildern (buecher/challenger/sehen/trinket_labels.json).
TRINKET_VORLAGEN = Path(__file__).resolve().parent.parent / "wissen" / "trinket_ziffern.png"
TRINKET_ROI = (16, 17, 28, 28)       # x0, y0, x1, y1 im 28er-Feld
TRINKET_MIN = 0.5                    # darunter: nicht lesbar
_TRINKET: list | None = None


def trinket_feld(breite: int, hoehe: int) -> tuple[int, int, int, int]:
    s = hoehe / REF_HOEHE
    cx, cy, r = breite / 2 + TRINKET[0] * s, hoehe - TRINKET[1] * s, TRINKET[2] * s
    return round(cx - r), round(cy - r), round(cx + r), round(cy + r)


def _trinket_roi(fenster: np.ndarray) -> np.ndarray:
    x0, y0, x1, y1 = trinket_feld(fenster.shape[1], fenster.shape[0])
    feld = cv2.resize(fenster[y0:y1, x0:x1], (28, 28), interpolation=cv2.INTER_AREA)
    a, b, c, d = TRINKET_ROI
    return cv2.cvtColor(feld[b:d, a:c], cv2.COLOR_BGR2GRAY).astype(np.float32)


def trinket(fenster: np.ndarray) -> int | None:
    """Ladungen des gelben Trinkets (0/1/2) aus dem Spielbild (16:9-Mitte, BGR); None, wenn nicht lesbar."""
    global _TRINKET
    if _TRINKET is None:
        t = cv2.imread(str(TRINKET_VORLAGEN), cv2.IMREAD_GRAYSCALE).astype(np.float32)
        k = t.shape[1] // 3
        _TRINKET = [t[:, i * k:(i + 1) * k] for i in range(3)]
    roi = _trinket_roi(fenster)
    r = roi - roi.mean()
    werte = []
    for v in _TRINKET:
        w = v - v.mean()
        werte.append(float((r * w).sum() / (np.sqrt((r * r).sum() * (w * w).sum()) + 1e-6)))
    beste = int(np.argmax(werte))
    return beste if werte[beste] >= TRINKET_MIN else None


# ---------------------------------------------------------------- Objective-Kopfgeld (Minimap)
# Turm-Symbole mit goldenem Rand (vermessen 30.09.: Farbton 15-32, erst nach der Plattenzeit). Ob das das
# Kopfgeld ist, prueft werkzeuge/kopfgeld_probe.py gegen den Spielstand - Urteil in wahrnehmung.py.
GOLD = ((15, 120, 170), (32, 255, 255))
GOLD_AB = 25                     # Goldpixel (bei 570) im Kasten um ein Turm-Symbol


def _tuerme() -> dict:
    from .bewertung import BREITE, HOEHE, TUERME
    return {k: (x / BREITE, 1 - y / HOEHE) for k, (x, y) in TUERME.items()}


def kopfgeld(karte: np.ndarray, mein_team: str) -> dict:
    """Tuerme mit Goldrand: {"eigene": [(Lane, Stufe)], "gegner": [...]}."""
    k = karte if karte.shape[0] == REF else cv2.resize(karte, (REF, REF), interpolation=cv2.INTER_AREA)
    g = cv2.inRange(cv2.cvtColor(k, cv2.COLOR_BGR2HSV), *GOLD)
    aus = {"eigene": [], "gegner": []}
    for (team, lane, stufe), (x, y) in _tuerme().items():
        cx, cy = int(x * REF), int(y * REF)
        if int(g[max(0, cy - 14):cy + 15, max(0, cx - 14):cx + 15].sum() / 255) >= GOLD_AB:
            aus["eigene" if team == mein_team else "gegner"].append((lane, stufe))
    return aus


# ---------------------------------------------------------------- Ward-Spur (Ort, Alter, weg)
# Blaue Pings (Rueckzug, "bin unterwegs") treffen die Vorlage knapp ueber der Schwelle, stehen aber hoechstens ~4 s
# und flackern (Stichprobe 3, B14); ein Ward steht mindestens eine Minute. Darum zaehlt ein Fund erst, wenn er nach
# BESTAETIGT_NACH s noch da ist. Weg ist ein Ward, wenn es WEG_NACH s nicht mehr gesehen wurde und kein Champion-Icon
# auf der Stelle liegt (das verdeckt es nur).
# Gemessen an 50 zufaelligen "weg" (buecher/challenger/sehen/ward_weg_labels.json): 7 falsch, fast alle unter einem
# Champion-Icon, das halb auf dem Ward stand - daher VERDECKT = Icon-Radius + halbe Ward-Kante, und vor "weg" wird die
# Stelle selbst mit niedrigerer Schwelle nachgesehen (ein halb verdecktes Ward trifft die Vorlage noch mit ~0,5).
BESTAETIGT_NACH = 6.0
WEG_NACH = 7.0
GLEICH = 0.02                    # Anteil: so nah = dasselbe Ward
VERDECKT = 0.065                 # Champion-Icon (Radius ~0,042) + halbes Ward: naeher als das = nicht sichtbar
NOCH_DA = 0.45                   # Nachsehen an der Stelle vor "weg"


@dataclass
class Spurward:
    x: float
    y: float
    art: str                      # hell / matt / kontrolle (blass aendert die Art nicht)
    seit: float                   # erster Fund (Wanduhr)
    zuletzt: float
    blass: bool = False
    gesehen: int = 1
    bestaetigt: bool = False


def _noch_da(karte: np.ndarray, s: "Spurward") -> bool:
    """Steht an der Stelle noch etwas, das der Vorlage aehnelt (halb verdeckt, von einer Linie geschnitten)?"""
    k = karte if karte.shape[0] == REF else cv2.resize(karte, (REF, REF), interpolation=cv2.INTER_AREA)
    cx, cy, r = int(round(s.x * REF)), int(round(s.y * REF)), 20
    stueck = k[max(0, cy - r):cy + r + 1, max(0, cx - r):cx + r + 1].astype(np.float32)
    for art, t, m in _vorlagen():
        if stueck.shape[0] < t.shape[0] or stueck.shape[1] < t.shape[1]:
            return False
        v = np.nan_to_num(cv2.matchTemplate(stueck, t, cv2.TM_CCOEFF_NORMED, mask=m), nan=0, posinf=0, neginf=0)
        if float(v.max()) >= NOCH_DA:
            return True
    return False


class Wardspur:
    """Fuehrt die Funde von `wards()` ueber die Zeit: `neu()` liefert Ereignisse ("gesetzt"/"weg", Spurward)."""

    def __init__(self) -> None:
        self.wards: list[Spurward] = []

    def neu(self, zeit: float, funde: list[Ward], champions: list[tuple[float, float]] = (),
            karte: np.ndarray | None = None) -> list[tuple]:
        ereignisse = []
        frei = list(funde)
        for s in self.wards:
            f = min(frei, key=lambda w: (w.x - s.x) ** 2 + (w.y - s.y) ** 2, default=None)
            if f is not None and (f.x - s.x) ** 2 + (f.y - s.y) ** 2 <= GLEICH ** 2:
                frei.remove(f)
                s.zuletzt, s.gesehen = zeit, s.gesehen + 1
                if f.art == "blass":
                    s.blass = True
                elif not s.blass:
                    s.art = f.art
                if not s.bestaetigt and zeit - s.seit >= BESTAETIGT_NACH:
                    s.bestaetigt = True
                    ereignisse.append(("gesetzt", s))
            elif any((s.x - a) ** 2 + (s.y - b) ** 2 <= VERDECKT ** 2 for a, b in champions):
                s.zuletzt = zeit          # verdeckt, nicht weg
        bleiben = []
        for s in self.wards:
            if zeit - s.zuletzt >= WEG_NACH and s.bestaetigt and karte is not None and _noch_da(karte, s):
                s.zuletzt = zeit
            if zeit - s.zuletzt < (WEG_NACH if s.bestaetigt else 3.5):
                bleiben.append(s)
            elif s.bestaetigt:
                ereignisse.append(("weg", s))
        self.wards = bleiben + [Spurward(w.x, w.y, w.art, zeit, zeit, blass=w.art == "blass") for w in frei]
        return ereignisse

    def stehen(self) -> list[Spurward]:
        return [s for s in self.wards if s.bestaetigt]
