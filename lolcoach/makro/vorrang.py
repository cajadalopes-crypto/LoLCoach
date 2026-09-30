"""Vorrang, wenn mehrere Entscheidungen feuern.

Zwei Reihenfolgen, umschaltbar (wissen/kern.toml [makro_gehirn] reihenfolge), gemessen in Auftrag 035, Teil 2
(werkzeuge/challenger/treue.py --reihenfolge fest|wert):
- "fest" (Auftrag 032): Gefahr, dann die Objective-Kette, dann der Rest - je Klasse nach dem festen Wert der
  Entscheidung. Der feste Wert ist eine Handregel.
- "wert" (Auftrag 035, Teil 0, Standard): Gefahr steht immer vorn; danach ordnet der Aktionswert des Gehirns
  (makro/aktionen.py: welche Aktion das Kommando meint, `hirn.wert`). Wo eine Entscheidung keine Aktion hat oder das
  Gehirn keinen Wert, gilt ihr fester Wert als Ersatz. Bei Gleichstand die Klasse, dann die Nummer.
"""
from __future__ import annotations

from .kommando import KLASSEN, Kommando

REIHENFOLGEN = ("wert", "fest")


def _klasse(k: Kommando) -> int:
    return KLASSEN.index(k.klasse) if k.klasse in KLASSEN else len(KLASSEN)


def effektiv(k: Kommando, hirn=None) -> float:
    """Der Wert, nach dem "wert" ordnet: Aktionswert des Gehirns, sonst der feste Wert."""
    if k.klasse != "gefahr" and hirn is not None:
        from .aktionen import wert
        w = wert(k, hirn)
        if w is not None:
            return w
    return k.wert


def ordnen(kommandos: list[Kommando], hirn=None, art: str = "fest") -> list[Kommando]:
    """Stabil. "fest": Klasse (gefahr < objective < rest), dann fester Wert absteigend, dann Nummer. "wert": Gefahr
    zuerst (nach festem Wert), danach nach `effektiv` absteigend, dann Klasse, dann Nummer."""
    if art == "wert":
        return sorted(kommandos, key=lambda k: (0 if k.klasse == "gefahr" else 1, -effektiv(k, hirn), _klasse(k), k.id))
    return sorted(kommandos, key=lambda k: (_klasse(k), -k.wert, k.id))


def erstes(kommandos: list[Kommando], hirn=None, art: str = "fest") -> Kommando | None:
    o = ordnen(kommandos, hirn, art)
    return o[0] if o else None
