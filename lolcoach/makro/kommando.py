"""Das Kommando: "Tu X: weil Y. Danach Z." - Warten ist ein Kommando. Keine internen Begriffe."""
from __future__ import annotations

from dataclasses import dataclass

KLASSEN = ("gefahr", "objective", "rest")      # Vorrang in dieser Reihenfolge (vorrang.py)
# "danach"-Teile, die schon selbst einen Anschluss haben: nicht noch "Danach" davor
EIGENE_ANFAENGE = ("danach", "dann", "erst", "jetzt", "bis", "in ", "tp ist", "sofort", "warten", "nicht", "direkt", "sonst")


@dataclass
class Kommando:
    id: str                 # Nummer aus Buch 17, Teil B (S1 ... Z3)
    tu: str                 # was
    weil: str               # warum
    danach: str = ""        # was danach
    klasse: str = "rest"    # gefahr / objective / rest
    wert: float = 0.0       # Siegchance-Punkte oder Gewicht fuer den Rest

    @property
    def text(self) -> str:
        trenner = " – " if ":" in self.tu else ": "
        s = f"{_gross(self.tu)}{trenner}{self.weil}."
        if self.danach:
            d = self.danach.strip()
            eigen = d.lower().startswith(EIGENE_ANFAENGE)
            s += f" {_gross(d)}." if eigen else f" Danach {d}."
        return s.replace("..", ".")


def _gross(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def sek(s: float | None) -> str:
    """Sekunden fuers Sprechen: '25 s', '1:30 min'."""
    if s is None:
        return "?"
    s = max(0, int(round(s)))
    return f"{s} s" if s < 90 else f"{s // 60}:{s % 60:02d} min"
