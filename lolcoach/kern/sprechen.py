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
| TECHNIK      | SOFORT   | ja                | frei          |
| INFO_FLASH   | WICHTIG  | Unterbrechbares   | frei, eigene Grenze (Auftrag 016: jeder Flash, 1 je 8 s) |
| INFO_JUNGLER | WICHTIG  | Unterbrechbares   | frei (Auftrag 016, 1.2: Jungler nach >= 20 s wieder gesehen) |
| INFO_LANE    | WICHTIG  | Unterbrechbares   | frei (Auftrag 016, 1.3: Lane-Gegner weit weg, mit Folge) |
| WENDEPUNKT   | WICHTIG  | Unterbrechbares   | frei, hoechstens 1 je 8 s (Buch 11, 4) |
| FENSTER      | WICHTIG  | Unterbrechbares   | ja (zaehlt als PLAN) |
| VORSCHAU     | WICHTIG  | Unterbrechbares   | ja, hoechstens 1 je 60 s |
| VORSICHT     | WICHTIG  | Unterbrechbares   | frei, hoechstens 1 je 90 s (Auftrag 008, A1) |
| LAGEBILD     | HINWEIS  | nein              | ja, hoechstens 1 je 90 s (Auftrag 008, A4) |
| MAKRO        | WICHTIG  | Unterbrechbares   | ja, hoechstens 1 je 45 s mit FENSTER und VORSCHAU (Buch 4, 5) |"""
from __future__ import annotations

from ..regeln import HINWEIS, SOFORT, WICHTIG, Ansage

PRIO = {"GEFAHR": SOFORT, "PLAN": WICHTIG, "ERINNERUNG": HINWEIS, "BESTAETIGUNG": HINWEIS, "TECHNIK": SOFORT,
        "INFO_FLASH": WICHTIG, "WENDEPUNKT": WICHTIG, "FENSTER": WICHTIG, "VORSCHAU": WICHTIG,
        "VORSICHT": WICHTIG, "LAGEBILD": HINWEIS, "MAKRO": WICHTIG, "INFO_JUNGLER": WICHTIG, "INFO_LANE": WICHTIG,
        "INFO_VORLAUF": WICHTIG}
# zaehlen nicht zum Budget (INFO_FLASH: eigene Grenze, Auftrag 002; WENDEPUNKT: hoechstens 1 je 8 s, Buch 11, 4;
# Auftrag 016, 1: die Informationspflicht - Flash, Jungler, Lane-Gegner weg - kommt immer, als WICHTIG)
FREI = ("GEFAHR", "TECHNIK", "INFO_FLASH", "WENDEPUNKT", "VORSICHT", "INFO_JUNGLER", "INFO_LANE", "INFO_VORLAUF")


def zaehlt(a: Ansage) -> bool:
    """Zaehlt eine gesprochene Ansage zum Budget (9.2)? Nicht: GEFAHR (Thema gefahr / SOFORT), Briefing, TECHNIK."""
    return not (a.prio >= SOFORT or a.thema in ("gefahr", "wendepunkt")
                or a.schluessel in ("briefing", "kern:technik", "tod", "kern:VORSICHT")
                or a.schluessel.startswith("kern:INFO_"))


class Sprecher:
    def __init__(self, cfg: dict):
        self.c = cfg["sprechen"]
        self.bc = cfg["bestaetigung"]
        self.wartet: tuple | None = None   # (Kategorie, Art, Text, Pruefung, danach) - Budget voll
        self.bestaetigt_zuletzt = -1e9
        self.kategorien: dict[str, int] = {"GEFAHR": 0, "PLAN": 0, "ERINNERUNG": 0, "BESTAETIGUNG": 0,
                                           "INFO_FLASH": 0, "WENDEPUNKT": 0, "FENSTER": 0, "VORSCHAU": 0,
                                           "VORSICHT": 0, "LAGEBILD": 0, "MAKRO": 0, "INFO_JUNGLER": 0, "INFO_LANE": 0,
                                           "INFO_VORLAUF": 0}

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
                      sperre=0.0, thema={"GEFAHR": "gefahr", "WENDEPUNKT": "wendepunkt"}.get(kategorie, ""),
                      pruefe=pruefe,
                      unterbrechbar=kategorie in ("ERINNERUNG", "BESTAETIGUNG"))

    def bestaetigung_frei(self, zeit: float, gesagt: list, modus: str | None, gefahr: bool) -> bool:
        """Buch 3, 5: hoechstens 1 je abstand_s (180 s), nie in KAMPF oder GEFAHR, nie bei vollem Budget."""
        return (zeit - self.bestaetigt_zuletzt >= self.bc["abstand_s"] and modus != "KAMPF" and not gefahr)


def woerter(text: str) -> int:
    return len(text.split())
