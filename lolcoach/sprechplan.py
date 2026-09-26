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

ZEICHEN_PRO_SEKUNDE = 12.0   # Killian (edge-tts, +8 %) gemessen 26.09.: 11-12 Zeichen/s; live fragt der Plan die Stimme
PAUSE = 1.5                  # zwischen zwei Saetzen (2,0 bis 26.09.; die Schaetzung ist jetzt ehrlicher)
RUHE_VOR_HINWEIS = 8.0       # Hinweise nur, wenn es so lange still war
THEMA_SPERRE = 30.0          # zwei Ansagen zum selben Thema (back, druck, gefahr, objective) nicht so kurz hintereinander
THEMA_SPERRE_JE = {"gefahr": 12.0}   # Gefahr aendert sich schnell: eine neue Warnung darf eher kommen
# Nach einer Warnung kein "geh rein" (Camille-Partie 15:37/15:39: "rein" und "zurueck" in 2 s). Umgekehrt
# nicht: eine Gefahr darf immer kommen, auch direkt nach einem Druck-Satz.
WIDERSPRUCH = {"druck": ("gefahr", 15.0), "seite": ("gefahr", 15.0)}


class Sprechplan:
    def __init__(self, sprecher):
        self.sprecher = sprecher
        self.warte: list[Ansage] = []
        self.frei_ab = -1e9           # Spielzeit, ab der wieder gesprochen werden darf
        self.zuletzt: dict[str, float] = {}
        self.gesagt: list[Ansage] = []
        self._einwurf: list[Ansage] = []
        self.thema_zuletzt: dict[str, float] = {}
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
        # Dasselbe Thema eben erst gesagt ("2000 Gold: ... back" 9:47 und 9:53, Camille-Partie 26.09.):
        # die zweite faellt weg - ausser sie ist SOFORT (Gefahr darf immer)
        self.warte = [a for a in self.warte if zeit - a.zeit <= a.gueltig
                      and not (a.thema and a.prio < SOFORT
                               and zeit - self.thema_zuletzt.get(a.thema, -1e9) < THEMA_SPERRE_JE.get(a.thema, THEMA_SPERRE))
                      and not (a.thema in WIDERSPRUCH
                               and zeit - self.thema_zuletzt.get(WIDERSPRUCH[a.thema][0], -1e9) < WIDERSPRUCH[a.thema][1])]
        if not self.warte:
            return None
        a = max(self.warte, key=lambda a: (a.prio, a.zeit))
        frei = self.frei_ab + (RUHE_VOR_HINWEIS if a.prio == HINWEIS else 0.0)
        if zeit < frei and a.prio < SOFORT:
            return None
        if a.prio < SOFORT and getattr(self.sprecher, "beschaeftigt", False):
            return None     # die Stimme spricht noch (live exakt statt geschaetzt)
        self.warte.remove(a)
        a.gesprochen = zeit
        self.zuletzt[a.schluessel] = zeit
        if a.thema:
            self.thema_zuletzt[a.thema] = zeit
        self.frei_ab = zeit + len(a.text) / ZEICHEN_PRO_SEKUNDE + PAUSE
        self.sprecher.sage(a.text, dringend=a.prio == SOFORT)
        self.gesagt.append(a)
        return a
