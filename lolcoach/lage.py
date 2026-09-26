"""Lagebild: wer wurde zuletzt wo auf der Minimap gesehen.

Bilder kommen mit Wanduhrzeit (live vom Beobachter, im Nachspielen aus dem
Bilderordner einer Aufnahme). Der Aufrufer rechnet sie ueber den letzten
API-Schnappschuss in Spielzeit um - so laufen Live und Aufnahme gleich.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np

from . import minimap
from .zustand import Partie, Spieler

SICHTBAR_TOLERANZ = 1.6   # Sekunden: so alt darf eine Sichtung sein und gilt noch als "jetzt sichtbar"


VERLAUF = 15.0            # Sekunden Positionsverlauf je Spieler


class Lagebild:
    def __init__(self):
        self.zuletzt: dict[tuple[str, str], tuple[float, float, float]] = {}  # (name, team) -> (zeit, x, y)
        self.verlauf: dict[tuple[str, str], deque] = {}
        self.letztes_bild: float | None = None

    def neu(self, zeit: float, sichtungen: list[minimap.Sichtung], p: Partie) -> None:
        self.letztes_bild = zeit if self.letztes_bild is None else max(self.letztes_bild, zeit)
        for s in sichtungen:
            sp = zuordnen(s, p)
            if sp:
                schl = (sp.name, sp.team)
                self.zuletzt[schl] = (zeit, s.x, s.y)
                v = self.verlauf.setdefault(schl, deque())
                v.append((zeit, s.x, s.y))
                while v and v[0][0] < zeit - VERLAUF:
                    v.popleft()

    def stand_still(self, sp: Spieler, dauer: float = 5.5, toleranz: float = 0.015) -> bool:
        """Stand `sp` vor seiner letzten Sichtung mindestens `dauer` Sekunden auf
        der Stelle? So sieht ein Recall aus (8 s kanalisieren, dann weg)."""
        v = self.verlauf.get((sp.name, sp.team))
        if not v:
            return False
        ende, ex, ey = v[-1]
        punkte = [(t, x, y) for t, x, y in v if t >= ende - dauer - 1]
        return (ende - punkte[0][0] >= dauer
                and all(abs(x - ex) + abs(y - ey) <= toleranz for _, x, y in punkte))

    def gesehen(self, sp: Spieler) -> tuple[float, float, float] | None:
        return self.zuletzt.get((sp.name, sp.team))

    def sichtbar(self, sp: Spieler) -> bool:
        g = self.gesehen(sp)
        return bool(g and self.letztes_bild is not None and g[0] >= self.letztes_bild - SICHTBAR_TOLERANZ)

    @property
    def aktiv(self) -> bool:
        return self.letztes_bild is not None


def zuordnen(s: minimap.Sichtung, p: Partie) -> Spieler | None:
    kandidaten = [sp for sp in p.spieler if sp.champion_id == s.champion_id]
    if len(kandidaten) == 1:
        return kandidaten[0]
    return next((sp for sp in kandidaten if sp.team == s.team), None) if s.team else None


def champions(p: Partie) -> list[tuple[str, str]]:
    return [(s.champion_id, s.team) for s in p.spieler]


# --- live: der Beobachter ---------------------------------------------------------

class Beobachter(threading.Thread):
    """Fotografiert `takt`-mal je Sekunde die Minimap, erkennt die Champions und
    legt (Wanduhr, Sichtungen) bereit. Jedes `speichere_jedes`-te Bild landet
    zusaetzlich im Bilderordner der Aufnahme (Material fuers Nachspielen)."""

    def __init__(self, ordner: Path | None, takt: float = 0.5, speichere_jedes: int = 2):
        super().__init__(daemon=True)
        self.ordner, self.takt, self.speichere_jedes = ordner, takt, speichere_jedes
        if ordner:
            ordner.mkdir(parents=True, exist_ok=True)
        self.champions: list[tuple[str, str]] = []
        self.anzahl = 0
        self.fehler: str | None = None
        self._neu: list[tuple[float, list[minimap.Sichtung]]] = []
        self._schloss = threading.Lock()
        self._halt = threading.Event()

    def run(self) -> None:
        from PIL import ImageGrab
        from . import bild
        while not self._halt.is_set():
            start = time.time()
            try:
                f = bild.spielfenster()
                if f and self.champions:
                    l, o, r, u = f
                    kl, ko, kr, ku = minimap.kartenrechteck(r - l, u - o)
                    roh = ImageGrab.grab(bbox=(l + kl, o + ko, l + kr, o + ku), all_screens=True)
                    karte = cv2.cvtColor(np.asarray(roh), cv2.COLOR_RGB2BGR)
                    sichtungen = minimap.finde(karte, self.champions, hoehe=u - o)
                    with self._schloss:
                        self._neu.append((start, sichtungen))
                    if self.ordner and self.anzahl % self.speichere_jedes == 0:
                        cv2.imwrite(str(self.ordner / f"{int(start * 1000)}.jpg"), karte,
                                    [cv2.IMWRITE_JPEG_QUALITY, 85])
                    self.anzahl += 1
            except Exception as e:  # ein Bild weniger, nie die Partie verlieren
                self.fehler = f"{type(e).__name__}: {e}"
            self._halt.wait(max(0.0, self.takt - (time.time() - start)))

    def abholen(self) -> list[tuple[float, list[minimap.Sichtung]]]:
        with self._schloss:
            neu, self._neu = self._neu, []
        return neu

    def halt(self) -> None:
        self._halt.set()
        self.join(timeout=3)


# --- Nachspielen: Sichtungen aus dem Bilderordner ----------------------------------

def karte_aus_bild(pfad: Path, hoehe: int = minimap.REFERENZ_HOEHE) -> np.ndarray | None:
    """Neue Aufnahmen speichern genau die Minimap; die ersten (26.09.2026,
    12:00) die ganze Ecke - daraus wird die Minimap herausgeschnitten."""
    bild = cv2.imread(str(pfad))
    if bild is None:
        return None
    s = round(minimap.KARTE * hoehe)
    if abs(bild.shape[0] - s) <= 2:
        return bild
    ecke = bild.shape[0]
    x0 = ecke - round(minimap.RAND_RECHTS * hoehe) - s
    y0 = ecke - round(minimap.RAND_UNTEN * hoehe) - s
    return bild[y0:y0 + s, x0:x0 + s]


class SichtAusBildern:
    """Liefert fuer ein Wanduhr-Intervall die Sichtungen aus den gespeicherten Bildern.

    Die Erkennung laeuft beim ersten Mal parallel ueber alle Bilder und wird
    als `sichtungen.json` im Bilderordner abgelegt - danach dauert ein
    Nachspielen Sekunden. Der Cache haengt an Champions und Erkennungsstand
    (`minimap.STAND`); aendert sich eins, wird neu gerechnet."""

    def __init__(self, bilder: list[tuple[float, Path]]):
        self.bilder = bilder
        self.i = 0
        self._ergebnis: dict[str, list[minimap.Sichtung]] | None = None

    def _berechne(self, champions_: list[tuple[str, str]]) -> None:
        import json
        from concurrent.futures import ThreadPoolExecutor
        from dataclasses import asdict
        cache = self.bilder[0][1].parent / "sichtungen.json" if self.bilder else None
        kennung = {"stand": minimap.STAND, "champions": sorted(map(list, champions_))}
        if cache and cache.exists():
            gespeichert = json.loads(cache.read_text(encoding="utf-8"))
            if gespeichert.get("kennung") == kennung:
                self._ergebnis = {k: [minimap.Sichtung(**s) for s in v] for k, v in gespeichert["bilder"].items()}
                return

        def eins(pfad: Path):
            karte = karte_aus_bild(pfad)
            return pfad.name, ([] if karte is None else minimap.finde(karte, champions_))

        with ThreadPoolExecutor() as pool:
            self._ergebnis = dict(pool.map(eins, (p for _, p in self.bilder)))
        if cache:
            cache.write_text(json.dumps({"kennung": kennung, "bilder": {
                k: [asdict(s) for s in v] for k, v in self._ergebnis.items()}}), encoding="utf-8")

    def zwischen(self, bis: float, champions_: list[tuple[str, str]]) -> list[tuple[float, list[minimap.Sichtung]]]:
        if self._ergebnis is None and champions_:
            self._berechne(champions_)
        aus = []
        while self.i < len(self.bilder) and self.bilder[self.i][0] <= bis:
            w, pfad = self.bilder[self.i]
            self.i += 1
            if self._ergebnis is not None:
                aus.append((w, self._ergebnis.get(pfad.name, [])))
        return aus
