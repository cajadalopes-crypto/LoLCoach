"""Sprechen (Buch 0, Kapitel 9; Bestaetigung: Buch 3, Kapitel 5 und Buch 1, Kapitel 4).

Der Kern liefert hoechstens eine Ansage je Takt, als normale regeln.Ansage mit `schluessel = "kern:<art>"` - der
Sprechplan laesst sie an Themen-, Widerspruchs- und Rueckzugssperre vorbei (9.6) und bleibt Transport (Unterbrechen,
"noch wahr", "Ach nee", Vorwaermen). Das Budget (9.2) prueft der Kern hier selbst: zwischen zwei Ansagen ausser GEFAHR
(und ANTWORT) >= abstand_s, hoechstens max_je_minute je 60 s. Ist es voll, wird ein PLAN nur angezeigt und gesagt,
sobald wieder Platz ist - wenn er dann noch gilt.

| Kategorie    | prio     | darf unterbrechen | Budget        |
|--------------|----------|-------------------|---------------|
| GEFAHR       | SOFORT   | ja                | frei          |
| PLAN         | WICHTIG  | Unterbrechbares   | ja            |
| ERINNERUNG   | HINWEIS  | nein              | ja            |
| BESTAETIGUNG | HINWEIS  | nein              | ja (nie voll) |
| TECHNIK      | SOFORT   | ja                | frei          |"""
from __future__ import annotations

from ..regeln import HINWEIS, SOFORT, WICHTIG, Ansage

PRIO = {"GEFAHR": SOFORT, "PLAN": WICHTIG, "ERINNERUNG": HINWEIS, "BESTAETIGUNG": HINWEIS, "TECHNIK": SOFORT}
FREI = ("GEFAHR", "TECHNIK")        # zaehlen nicht zum Budget


def zaehlt(a: Ansage) -> bool:
    """Zaehlt eine gesprochene Ansage zum Budget (9.2)? Nicht: GEFAHR (Thema gefahr / SOFORT), Briefing, TECHNIK."""
    return not (a.prio >= SOFORT or a.thema == "gefahr" or a.schluessel in ("briefing", "kern:technik"))


class Sprecher:
    def __init__(self, cfg: dict):
        self.c = cfg["sprechen"]
        self.bc = cfg["bestaetigung"]
        self.wartet: tuple | None = None   # (Kategorie, Art, Text, Pruefung, danach) - Budget voll
        self.bestaetigt_zuletzt = -1e9
        self.kategorien: dict[str, int] = {"GEFAHR": 0, "PLAN": 0, "ERINNERUNG": 0, "BESTAETIGUNG": 0}

    def platz(self, zeit: float, gesagt: list) -> bool:
        """Budget frei? (Kapitel 9.2) - gemessen an allem, was gesprochen wurde (auch den alten Regeln)."""
        zaehlend = [a for a in gesagt if a.gesprochen is not None and zaehlt(a)]
        if zaehlend and zeit - zaehlend[-1].gesprochen < self.c["abstand_s"]:
            return False
        return sum(1 for a in zaehlend[-self.c["max_je_minute"] - 1:] if zeit - a.gesprochen < 60.0) \
            < self.c["max_je_minute"]

    def ansage(self, kategorie: str, art: str, text: str, zeit: float, pruefe, gesagt: list,
               danach=None) -> Ansage | None:
        """Eine Ansage, wenn Budget und Kategorie es erlauben; ein PLAN bei vollem Budget wartet (9.2). `danach`: was
        der Kern sich merkt, wenn der Satz WIRKLICH kommt - ruft er selbst bei sofortiger Ansage, hier beim
        Nachholen (Qualitaetsrunde 2, G1: der Schutzplan kam nachgeholt achtmal, weil sein Merker nie gesetzt wurde)."""
        if kategorie not in FREI and not self.platz(zeit, gesagt):
            if kategorie == "PLAN":
                self.wartet = (kategorie, art, text, pruefe, danach)
            return None
        if kategorie == "PLAN":
            self.wartet = None
        return self._bauen(kategorie, art, text, zeit, pruefe)

    def nachholen(self, zeit: float, gesagt: list) -> Ansage | None:
        """Der wartende PLAN, sobald wieder Platz ist - und nur, wenn er noch gilt."""
        if self.wartet is None:
            return None
        kategorie, art, text, pruefe, danach = self.wartet
        if pruefe is not None and not pruefe():
            self.wartet = None
            return None
        if not self.platz(zeit, gesagt):
            return None
        self.wartet = None
        a = self._bauen(kategorie, art, text, zeit, pruefe)
        if danach is not None:
            danach(a)
        return a

    def _bauen(self, kategorie: str, art: str, text: str, zeit: float, pruefe) -> Ansage:
        if kategorie in self.kategorien:
            self.kategorien[kategorie] += 1
        schluessel = "kern:technik" if kategorie == "TECHNIK" else f"kern:{art}"
        return Ansage(text, PRIO[kategorie], schluessel, zeit=zeit, gueltig=8.0 if kategorie != "GEFAHR" else 5.0,
                      sperre=0.0, thema="gefahr" if kategorie == "GEFAHR" else "", pruefe=pruefe,
                      unterbrechbar=kategorie in ("ERINNERUNG", "BESTAETIGUNG"))

    def bestaetigung_frei(self, zeit: float, gesagt: list, modus: str | None, gefahr: bool) -> bool:
        """Buch 3, 5: hoechstens 1 je abstand_s (180 s), nie in KAMPF oder GEFAHR, nie bei vollem Budget."""
        return (zeit - self.bestaetigt_zuletzt >= self.bc["abstand_s"] and modus != "KAMPF" and not gefahr)


def woerter(text: str) -> int:
    return len(text.split())
