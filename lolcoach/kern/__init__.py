"""Der Entscheidungskern (buecher/00_entscheidungskern.md). Ein Objekt je Partie.

Schritt 2: Merkmale und Modus. Der Kern spricht noch nicht - er bestimmt den Modus (Regelwerk.pruefe ruft
`modus_bestimmen`, sobald die Bewertung des Takts steht), sperrt damit die alten Regeln (kern/sperre.py), sammelt
die INFO-Zeilen fuers Dashboard und schreibt je Takt `<stamm>_kern.jsonl` (Zeit, Modus, Bereich, ...).
Plan, Wert und Sprechen folgen ab Schritt 3."""
from __future__ import annotations

import json
from collections import deque
from functools import lru_cache
from pathlib import Path

from .. import wissen
from .merkmale import MerkmalBau, Merkmale
from .modus import Modus, bereich_worte


@lru_cache(maxsize=1)
def konfig() -> dict:
    """wissen/kern.toml (einmal je Prozess gelesen)."""
    return wissen.lade("kern")


class Kern:
    def __init__(self, ablage: Path | None = None, cfg: dict | None = None):
        self.cfg = cfg or konfig()
        self.bau = MerkmalBau(self.cfg)
        self.modus = Modus(self.cfg)
        self.m: Merkmale | None = None
        self.info: deque = deque(maxlen=12)       # (Spielzeit, Text) - INFO nur fuers Dashboard (Kapitel 9.1)
        self._datei = None
        if ablage is not None:
            try:
                self._datei = open(ablage, "a", encoding="utf-8")
            except OSError:
                self._datei = None

    # --- vom Regelwerk gerufen ---------------------------------------------------------

    def modus_bestimmen(self, p, b, lagebild) -> str | None:
        """Merkmale dieses Takts (aus der Bewertung, die das Regelwerk schon gerechnet hat) und der Modus."""
        self.m = self.bau.neu(p, b, lagebild)
        return self.modus.neu(self.m)

    def info_dazu(self, zeit: float, text: str) -> None:
        self.info.append((zeit, text))

    # --- je Takt, nach dem Regelwerk ---------------------------------------------------

    def takt(self, p, lagebild=None) -> list:
        """Schritt 2: nur Protokoll. Rueckgabe: Ansagen des Kerns (noch keine)."""
        m = self.m
        if self._datei is not None and m is not None:
            try:
                self._datei.write(json.dumps({
                    "t": round(p.zeit, 2), "modus": self.modus.aktuell, "grund": self.modus.grund,
                    "bereich": m.bereich, "lane_phase": m.lane_phase, "kampf": m.im_kampf,
                    "frisch": m.daten_frisch}, ensure_ascii=False) + "\n")
            except (OSError, ValueError):
                pass
        return []

    def stand(self) -> dict:
        """Fuer Dashboard und Claude: Modus, Bereich, seit wann, warum, die letzten INFO-Zeilen."""
        m = self.m
        return {"modus": self.modus.aktuell, "seit": self.modus.seit, "grund": self.modus.grund,
                "bereich": bereich_worte(m.bereich if m else None),
                "info": [{"zeit": t, "text": x} for t, x in list(self.info)[-6:]][::-1]}

    def kopfzeile(self) -> str | None:
        """Erste Zeile jeder Claude-Frage (Kapitel 5.2): "MODUS: BASIS - du stehst in eurer Basis"."""
        if self.modus.aktuell is None:
            return None
        return f"MODUS: {self.modus.aktuell} - du stehst {bereich_worte(self.m.bereich if self.m else None)}"

    def schliessen(self) -> None:
        if self._datei is not None:
            try:
                self._datei.close()
            except OSError:
                pass
            self._datei = None
