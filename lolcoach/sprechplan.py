"""Der Sprechplan: wer redet wann.

Ein guter Coach redet wenig. Regeln liefern Ansagen, der Plan waehlt:
  - nie zwei Saetze uebereinander (geschaetzte Sprechdauer + Pause),
  - das Dringendste zuerst; was zu lange wartet, ist ueberholt und faellt weg,
  - derselbe Schluessel kommt erst nach seiner Sperrzeit wieder,
  - Hinweise (niedrigster Vorrang) nur nach einer laengeren Ruhe.
Alles in Spielzeit - so laeuft eine Aufnahme exakt wie das Live-Spiel.
"""
from __future__ import annotations

import threading

from .regeln import HINWEIS, SOFORT, Ansage

ZEICHEN_PRO_SEKUNDE = 14.0   # Windows-Stimme bei Rate 1, grob gemessen
PAUSE = 2.0                  # zwischen zwei Saetzen
RUHE_VOR_HINWEIS = 8.0       # Hinweise nur, wenn es so lange still war


class Sprechplan:
    def __init__(self, sprecher):
        self.sprecher = sprecher
        self.warte: list[Ansage] = []
        self.frei_ab = -1e9           # Spielzeit, ab der wieder gesprochen werden darf
        self.zuletzt: dict[str, float] = {}
        self.gesagt: list[Ansage] = []
        self._einwurf: list[Ansage] = []
        self._schloss = threading.Lock()

    def einwerfen(self, a: Ansage) -> None:
        """Aus einem anderen Thread (Stratege, Briefing): kommt beim naechsten Takt dran."""
        with self._schloss:
            self._einwurf.append(a)

    def neu(self, ansagen: list[Ansage]) -> None:
        with self._schloss:
            eingeworfen, self._einwurf = self._einwurf, []
        for a in [*eingeworfen, *ansagen]:
            if a.zeit - self.zuletzt.get(a.schluessel, -1e9) < a.sperre:
                continue
            self.warte = [w for w in self.warte if w.schluessel != a.schluessel]  # die neuere gilt
            self.warte.append(a)

    def takt(self, zeit: float) -> Ansage | None:
        self.warte = [a for a in self.warte if zeit - a.zeit <= a.gueltig]
        if not self.warte:
            return None
        a = max(self.warte, key=lambda a: (a.prio, a.zeit))
        frei = self.frei_ab + (RUHE_VOR_HINWEIS if a.prio == HINWEIS else 0.0)
        if zeit < frei and a.prio < SOFORT:
            return None
        self.warte.remove(a)
        a.gesprochen = zeit
        self.zuletzt[a.schluessel] = zeit
        self.frei_ab = zeit + len(a.text) / ZEICHEN_PRO_SEKUNDE + PAUSE
        self.sprecher.sage(a.text, dringend=a.prio == SOFORT)
        self.gesagt.append(a)
        return a
