"""Vorrang, wenn mehrere Entscheidungen feuern (Auftrag 032, Abschnitt 3):
Gefahr zuerst, dann die Objective-Kette, dann der Rest nach Wert. Die eine Stimme (was davon gesagt wird) baut
Stufe 4 (Auftrag 034) - hier nur die Reihenfolge."""
from __future__ import annotations

from .kommando import KLASSEN, Kommando


def ordnen(kommandos: list[Kommando]) -> list[Kommando]:
    """Stabil: Klasse (gefahr < objective < rest), dann Wert absteigend, dann Nummer."""
    return sorted(kommandos, key=lambda k: (KLASSEN.index(k.klasse) if k.klasse in KLASSEN else len(KLASSEN), -k.wert, k.id))


def erstes(kommandos: list[Kommando]) -> Kommando | None:
    o = ordnen(kommandos)
    return o[0] if o else None
