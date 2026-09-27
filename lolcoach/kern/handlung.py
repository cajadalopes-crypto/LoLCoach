"""Handlungen (Buch 0, Kapitel 6): eine konkrete Option mit Ziel, Wert und Grund.

Die Modi (kern/modi/) erzeugen Kandidaten, wert.py setzt p_tod, EV und die sechs Fragen, plan.py waehlt und haelt
einen davon. `satz` ist der gesprochene Satz beim Ansagen (Form Kapitel 9.3), `schritte` die Folge, die der Plan
abarbeitet ("Welle rein", "back", ...); `schritt_saetze` sagt, was beim Erreichen eines Schritts neu zu tun ist."""
from __future__ import annotations

from dataclasses import dataclass, field

# Kehrtwenden (Kapitel 9.4 Punkt 5): vor / zurueck; alles andere (FARMEN, STAPELN, UNTER_TURM_FARMEN, WELLE_HALTEN,
# WELLE_REIN_UND_BACK, KAUFEN, WOHIN ...) ist neutral (Buch 1, Kapitel 3)
VOR = frozenset(("TRADE", "ALL_IN", "PLATTEN", "DRUECKEN", "MIT_GRUPPE", "ANLAUFEN", "NEHMEN", "BESTREITEN", "REIN",
                 "ANNEHMEN", "DREHEN"))          # Buch 7, 4: ANNEHMEN und DREHEN sind "vor" (9.4 Punkt 5)
ZURUECK = frozenset(("ZURUECK", "RAUS", "BACK_JETZT", "WELLE_UND_RAUS", "HALTEN_UNTER_TURM", "ABGEBEN_TAUSCHEN"))
# Grundplaene: werden gehalten, aber nicht angesagt (Kapitel 3.1 Buch 1, "Schweigen ist ein Rat")
STUMM = frozenset(("FARMEN", "HALTEN"))
# "eine sicherere Handlung" (Kapitel 7.5 und 8.2 Punkt 2)
SICHER = frozenset(("ZURUECK", "BACK_JETZT", "WELLE_UND_RAUS"))


def richtung(art: str | None) -> str | None:
    if art in VOR:
        return "vor"
    if art in ZURUECK:
        return "zurueck"
    return None


@dataclass
class Ziel:
    art: str                 # "turm" | "objective" | "gegner" | "ort" | "lane" | "gruppe" | "basis"
    name: str                # gesprochen: "den Mid-Inhibitor-Turm", "den Drachen", "Sett", "deine Top-Welle"
    pos: tuple[float, float] | None = None
    weg: float | None = None  # deine Laufzeit in s


@dataclass
class Handlung:
    art: str                 # Katalog 6.3 (+ Buch 1/3), z. B. "WELLE_REIN_UND_BACK"
    ziel: Ziel | None        # Pflicht, ausser bei FARMEN/HALTEN
    modus: str
    dauer: float             # s, bis die Handlung erledigt ist
    gewinn: float = 0.0      # GE bei Erfolg
    p_erfolg: float | None = None   # None: 1 - p_tod
    p_tod: float = 0.0
    verlust: float = 0.0     # GE bei Tod (Todeskosten, Kapitel 7.3)
    kosten: float = 0.0      # sichere Kosten neben der Zeit: verlorene Wellen, Abwesenheit (Buch 1, Kapitel 2)
    folgewert: float = 0.0   # was sie fuer die naechsten 60 s freischaltet
    ev: float = 0.0          # von wert.py gesetzt
    grund: str = ""          # der eine entscheidende Grund, mit Zahl
    fragen: dict = field(default_factory=dict)   # die sechs Fragen (7.6)
    braucht: frozenset = frozenset()
    abbruch: list = field(default_factory=list)  # Funktionen (m, plan) -> str|None (Grund, warum ungueltig)
    schritte: list[str] = field(default_factory=list)
    satz: str = ""           # die Ansage (9.3)
    schritt_saetze: dict = field(default_factory=dict)   # Schritt-Index -> Satz, wenn er eine neue Taetigkeit verlangt
    erfuellt: object = None  # (m, plan) -> bool: aktueller Schritt erledigt?
    gefahr_t: float | None = None   # Fenster, ueber das p_tod gerechnet wird (Standard: dauer)
    schutz: float = 1.0      # Faktor auf p_tod (Rueckzug, am eigenen Turm)
    daten: dict = field(default_factory=dict)    # fuer Satz, Bestaetigung, Protokoll

    @property
    def stumm(self) -> bool:
        return self.art in STUMM

    def kurz(self) -> str:
        """Fuer Dashboard und Protokoll: "WELLE_REIN_UND_BACK -> deine Top-Welle"."""
        return self.art + (f" -> {self.ziel.name}" if self.ziel is not None else "")
