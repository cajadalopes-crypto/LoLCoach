"""Register der 111 Makro-Entscheidungen (Buch 17, Teil B: S1 ... Z3).

Jede Entscheidung ist eine reine Funktion `MakroLage -> Kommando | None` mit:
    grundlage   wie in Buch 17 (D, R, M, Re)
    eingaben    welche Live-Eingaben sie liest (wahrnehmung.EINGABEN) - fehlt eine, steht sie auf der Liste fuer 033
    rechnung    womit gerechnet wird: "D:<hirn-Feld>", "Re:<rechner-Funktion>", "R:<Regel-Nr>" (geprueft in der Abdeckung)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..kommando import Kommando
from ..lage import MakroLage
from .. import wahrnehmung

REGISTER: dict[str, "Entscheidung"] = {}
BEREICHE = {"S": "B1 Sicht", "J": "B2 Jungler", "W": "B3 Wellen", "B": "B4 Back", "T": "B5 TP", "R": "B6 Roams",
            "O": "B7 Objectives", "K": "B8 Kaempfe", "M": "B9 Spaetphase", "V": "B10 Spielstand", "P": "B11 Team",
            "Z": "B12 Warten"}


@dataclass
class Entscheidung:
    id: str
    titel: str
    grundlage: str
    eingaben: tuple[str, ...]
    rechnung: tuple[str, ...]
    fn: Callable[[MakroLage], Kommando | None]

    @property
    def bereich(self) -> str:
        return BEREICHE[self.id[0]]

    @property
    def fehlt(self) -> list[str]:
        return wahrnehmung.fehlt(self.eingaben)

    def pruefe(self, lage: MakroLage) -> Kommando | None:
        k = self.fn(lage)
        if k is not None:
            k.id = self.id
        return k


def entscheidung(id: str, titel: str, grundlage: str, eingaben: tuple[str, ...], rechnung: tuple[str, ...]):
    def deko(fn):
        assert id not in REGISTER, id
        REGISTER[id] = Entscheidung(id, titel, grundlage, eingaben, rechnung, fn)
        return fn
    return deko


def laden() -> dict[str, Entscheidung]:
    from . import sicht, jungler, wellen, back, tp, roam, objectives, kampf, spaet, spielstand, team, warten  # noqa: F401
    return REGISTER


def alle(lage: MakroLage) -> list[Kommando]:
    """Alle Entscheidungen, die in dieser Lage feuern (ungeordnet; Reihenfolge: vorrang.ordnen)."""
    out = []
    for e in laden().values():
        k = e.pruefe(lage)
        if k is not None:
            out.append(k)
    return out
