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
import time

from .regeln import HINWEIS, SOFORT, WICHTIG, Ansage

ZEICHEN_PRO_SEKUNDE = 13.0   # Killian (edge-tts, +8 %) gemessen 26.09.: 11-12 Zeichen/s; live fragt der Plan die Stimme
PAUSE = 1.5                  # zwischen zwei Saetzen (2,0 bis 26.09.; die Schaetzung ist jetzt ehrlicher)
RUHE_VOR_HINWEIS = 8.0       # Hinweise nur, wenn es so lange still war
THEMA_SPERRE = 30.0          # zwei Ansagen zum selben Thema (back, druck, gefahr, objective) nicht so kurz hintereinander
THEMA_SPERRE_JE = {"gefahr": 12.0,   # Gefahr aendert sich schnell: eine neue Warnung darf eher kommen
                   "druck": 8.0}     # ein Kampf-Fenster auch: aus "trade hart" wird mit seinem Flash ein Kill
# Nach einer Warnung kein "geh rein" (Camille-Partie 15:37/15:39: "rein" und "zurueck" in 2 s). Umgekehrt
# nicht: eine Gefahr darf immer kommen, auch direkt nach einem Druck-Satz.
WIDERSPRUCH = {"druck": ("gefahr", 15.0), "seite": ("gefahr", 15.0)}
# Live 26.09. 21:21: Flash-Meldungen warteten 9-17 s hinter langen Plaenen. Diese Ansagen sind lang und nicht eilig -
# eine wichtige, die es nicht ist (Flash, Gefahr, Jungler), darf sie abbrechen.
UNTERBRECHBAR = ("briefing", "midgame", "cs", "lane_tot", "aufbruch", "plan:back", "gold", "recallfenster",
                 "vorwarnung", "spike", "wiedereinstieg", "kontrollauge", "ward:")
# ... und bist du tot, ist jede Lane-Anweisung ueberholt (Live 21:21, 6:11: "Schieb die Welle in seinen Turm" -
# Carlos: "Warum sagst du mir das, obwohl ich selber tot war?")
NUR_LEBEND = ("lane_tot", "fenster", "plan:", "gold", "recallfenster", "anlauf", "jungler_sicht", "tief", "leben",
              "lane_fehlt", "lane_recall", "ohneflash", "ward:", "aufbruch", "kontrollauge", "level")


GESAGT_NACH = 4.0      # Sekunden: so lange laeuft eine Ansage mindestens, bevor eine gleich wichtige sie abbricht

# Sprechbudget: Nachlauf 21:21 nach allen Umbauten - der Coach sprach 88 % der Spielzeit, alles Neue musste warten
# oder abbrechen ("geisteskrank zu spaet"). Hat er in der letzten Minute schon mehr als die Haelfte geredet, wartet
# das Beiwerk (Kauf, Objective-Vorlauf, Wards, Spikes, Aufbruch ...) und verfaellt, wenn es zu alt wird. Gefahr,
# Flash, Kampf-Fenster, Jungler kommen immer durch.
BUDGET_FENSTER = 60.0
BUDGET_ANTEIL = 0.5
BEIWERK = ("gold", "plan:back", "objstart", "objgegner", "vorwarnung", "cs", "aufbruch", "spike", "kontrollauge",
           "ward:", "wiedereinstieg", "recallfenster", "tipp", "wardplan", "item:", "jungler6", "lane_tot")


def unterbrechbar(a: Ansage) -> bool:
    """Lange Saetze (ueber ~14 s) duerfen immer von etwas Wichtigem abgebrochen werden - sonst wartet alles."""
    return a.unterbrechbar or a.schluessel.startswith(UNTERBRECHBAR) or len(a.text) > 180 or a.prio == HINWEIS


def _stimmt(a: Ansage) -> bool:
    """Stimmt die Ansage noch (regeln.Regelwerk._noch_wahr)? Eine kaputte Pruefung laesst sie gelten."""
    if a.pruefe is None:
        return True
    try:
        return bool(a.pruefe())
    except Exception:
        return True


# Frisch statt vollstaendig (Carlos, Live 26.09. 23:20: "die Top-Aktualitaet ist das Wichtigste ueberhaupt"): so
# lange darf eine Ansage hoechstens warten, egal was die Regel wollte - das Briefing ausgenommen.
WARTEN_HOECHSTENS = {SOFORT: 6.0, WICHTIG: 10.0, HINWEIS: 20.0}
ACH_NEE = 8.0     # Sekunden: so lange nach einem widerrufenen Satz beginnt der neue zum selben Thema mit "Ach nee"


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
        self._laeuft: Ansage | None = None      # was gerade gesprochen wird (bis frei_ab)
        self._reden: list[tuple[float, float]] = []   # (Beginn, geschaetzte Dauer) - fuer das Sprechbudget
        self._ich_tot = False
        self._widerruf: tuple[float, str, str] | None = None   # (Wanduhr, Thema, Schluessel-Art) des abgebrochenen

    def _melder(self, a: Ansage, ab: float):
        """Die Stimme meldet ersten Ton und Ende in Wanduhr; umgerechnet auf Spielzeit ab dem Moment der Abgabe.
        'widerrufen': mitten im Satz stimmte er nicht mehr - die Sperren fallen, damit das Neue gleich kommt."""
        def melde(art: str, jetzt: float) -> None:
            if art == "ton":
                a.ton = round(a.gesprochen + (jetzt - ab), 2)
                return
            a.ganz = art == "ende"
            if art == "widerrufen":
                self.zuletzt.pop(a.schluessel, None)
                if a.thema:
                    self.thema_zuletzt.pop(a.thema, None)
                self._widerruf = (time.monotonic(), a.thema, a.schluessel.split(":")[0])
        return melde

    def _noch_wahr(self, a: Ansage):
        return lambda: _stimmt(a) and not (self._ich_tot and a.schluessel.startswith(NUR_LEBEND))

    def geredet(self, zeit: float) -> float:
        """Sekunden Sprechzeit in den letzten BUDGET_FENSTER Sekunden (abgebrochene zaehlen bis zum Abbruch)."""
        ab = zeit - BUDGET_FENSTER
        self._reden = [(t, d) for t, d in self._reden if t + d > ab]
        return sum(min(t + d, zeit) - max(t, ab) for t, d in self._reden if t < zeit)

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
            if a.schluessel != "briefing":
                a.gueltig = min(a.gueltig, WARTEN_HOECHSTENS.get(a.prio, 10.0))
            self.warte = [w for w in self.warte if w.schluessel != a.schluessel]  # die neuere gilt
            self.warte.append(a)

    def takt(self, zeit: float, ich_tot: bool = False) -> Ansage | None:
        # Dasselbe Thema eben erst gesagt ("2000 Gold: ... back" 9:47 und 9:53, Camille-Partie 26.09.):
        # die zweite faellt weg - ausser sie ist SOFORT (Gefahr darf immer)
        self.warte = [a for a in self.warte if zeit - a.zeit <= a.gueltig
                      and not (a.thema and a.prio < SOFORT
                               and zeit - self.thema_zuletzt.get(a.thema, -1e9) < THEMA_SPERRE_JE.get(a.thema, THEMA_SPERRE))
                      and not (a.thema in WIDERSPRUCH
                               and zeit - self.thema_zuletzt.get(WIDERSPRUCH[a.thema][0], -1e9) < WIDERSPRUCH[a.thema][1])]
        self._ich_tot = ich_tot
        if ich_tot:
            self.warte = [a for a in self.warte if not a.schluessel.startswith(NUR_LEBEND)]
        self.warte = [a for a in self.warte if _stimmt(a)]     # was nicht mehr stimmt, faellt weg
        if not self.warte:
            return None
        kandidaten = self.warte
        if self.geredet(zeit) > BUDGET_ANTEIL * BUDGET_FENSTER:
            kandidaten = [a for a in self.warte if not (a.prio == HINWEIS or a.schluessel.startswith(BEIWERK))]
            if not kandidaten:
                return None
        # bei gleichem Vorrang geht eine Gefahr vor (Pruefpartie 2, 19:39: "Du hast 5900 Gold ... recall" verdraengte
        # "Du stehst tief, Varus und Rakan seit 32 s weg" - 16 s vor dem Tod)
        a = max(kandidaten, key=lambda a: (a.prio, a.thema == "gefahr", a.zeit))
        frei = self.frei_ab + (RUHE_VOR_HINWEIS if a.prio == HINWEIS else 0.0)
        # Live 26.09. 21:21: das Briefing (~50 s) hielt "Gragas hat Flash benutzt" 9 s und Vaynes Flash 16 s auf.
        # Laeuft etwas Unterbrechbares, darf eine wichtige Ansage es abbrechen.
        laeuft = self._laeuft
        # Jede Ansage beginnt mit der Handlung - nach GESAGT_NACH Sekunden ist das Entscheidende heraus. Dann darf
        # eine gleich wichtige Neuigkeit den Rest abbrechen (Live 21:21: Sonas Flash wartete 17 s hinter zwei Saetzen).
        abbrechen = (laeuft is not None and zeit < self.frei_ab and a.prio >= WICHTIG and not unterbrechbar(a)
                     and (unterbrechbar(laeuft)
                          or (laeuft.gesprochen is not None and zeit - laeuft.gesprochen >= GESAGT_NACH
                              and a.prio >= laeuft.prio)))
        if zeit < frei and a.prio < SOFORT and not abbrechen:
            return None
        if a.prio < SOFORT and getattr(self.sprecher, "beschaeftigt", False) and not abbrechen:
            return None     # die Stimme spricht noch (live exakt statt geschaetzt)
        self.warte.remove(a)
        # "Ach nee - Ekko ist beim Drachen": der Satz davor wurde mitten drin widerrufen (Carlos' Wunsch 26.09.)
        w = self._widerruf
        if w is not None and time.monotonic() - w[0] <= ACH_NEE and (
                (a.thema and a.thema == w[1]) or a.schluessel.split(":")[0] == w[2]):
            a.text = "Ach nee - " + a.text      # Grossschreibung bleibt: meist beginnt der Satz mit einem Champion
            self._widerruf = None
        a.gesprochen = zeit
        self.zuletzt[a.schluessel] = zeit
        if a.thema:
            self.thema_zuletzt[a.thema] = zeit
        self.frei_ab = zeit + len(a.text) / ZEICHEN_PRO_SEKUNDE + PAUSE
        if abbrechen and self._reden:          # der abgebrochene zaehlt nur bis jetzt
            t0, _ = self._reden[-1]
            self._reden[-1] = (t0, max(0.0, zeit - t0))
        self._reden.append((zeit, len(a.text) / ZEICHEN_PRO_SEKUNDE))
        self.sprecher.sage(a.text, dringend=a.prio == SOFORT or abbrechen, melde=self._melder(a, time.monotonic()),
                           noch_wahr=self._noch_wahr(a))
        self._laeuft = a
        self.gesagt.append(a)
        return a
