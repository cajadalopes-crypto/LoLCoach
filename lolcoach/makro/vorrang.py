"""Vorrang, wenn mehrere Entscheidungen feuern.

Zwei Reihenfolgen, umschaltbar (wissen/kern.toml [makro_gehirn] reihenfolge), gemessen in Auftrag 035, Teil 2
(werkzeuge/challenger/treue.py --reihenfolge fest|wert):
- "fest" (Auftrag 032): Gefahr, dann die Objective-Kette, dann der Rest - je Klasse nach dem festen Wert der
  Entscheidung. Der feste Wert ist eine Handregel.
- "wert" (Auftrag 035, Teil 0, Standard): Gefahr steht immer vorn; danach ordnet der Aktionswert des Gehirns
  (makro/aktionen.py: welche Aktion das Kommando meint, `hirn.wert`). Wo eine Entscheidung keine Aktion hat oder das
  Gehirn keinen Wert, gilt ihr fester Wert als Ersatz. Bei Gleichstand die Klasse, dann die Nummer.

Auftrag 036: Gefahr steht nur vorn, wenn das Gefahr-Modell sie bestaetigt (`bestaetigt`). Die Gefahr-Entscheidungen
aus 032 (J4, J5, J9 ...) sind Handregeln - in 035 waren 87 % aller Lagen Warnungen, und der Tod in 60 s nach einer
Warnung war mit 20,0 % so haeufig wie ohne (19,7 %). Jetzt ist die Handregel nur noch die Zusatzbedingung: gewarnt
wird, wenn sie feuert UND die Todeswahrscheinlichkeit der Lage (`Hirn.tod60`) mindestens `gefahr_schwelle` ist
(wissen/kern.toml [makro_gehirn], bestimmt mit werkzeuge/challenger/gefahr_schwelle.py). Ohne Modellwert warnt nur
`OHNE_MODELL` (B4: wenig Leben mit Gegnern in der Naehe - das R1 des alten Kerns). Nicht bestaetigte Warnungen fallen
weg, es spricht die beste andere Anweisung (nie Schweigen: G0).
"""
from __future__ import annotations

from .kommando import KLASSEN, Kommando

REIHENFOLGEN = ("wert", "fest")
OHNE_MODELL = ("B4",)             # Auftrag 036: ohne Modellwert warnt nur das (wenig Leben, Gegner nah)
SCHWELLE_VORGABE = 0.40           # Ersatz, wenn kern.toml fehlt: doppelte Grundrate (Tod in 60 s: 19,7 %, 035)


def schwelle() -> float:
    """gefahr_schwelle aus wissen/kern.toml [makro_gehirn] (werkzeuge/challenger/gefahr_schwelle.py schreibt sie)."""
    try:
        from .. import wissen
        return float(wissen.lade("kern").get("makro_gehirn", {}).get("gefahr_schwelle", SCHWELLE_VORGABE))
    except Exception:
        return SCHWELLE_VORGABE


def bestaetigt(k: Kommando, hirn=None, schwelle_: float = SCHWELLE_VORGABE,
               ohne_modell: tuple = OHNE_MODELL) -> bool:
    """Darf dieses Kommando als Gefahr gelten? Alles ausser Gefahr: ja. Gefahr: das Modell muss sie bestaetigen
    (`hirn.tod60 >= schwelle_`); ohne Modellwert nur `ohne_modell`."""
    if k.klasse != "gefahr":
        return True
    p = getattr(hirn, "tod60", None) if hirn is not None else None
    if p is None:
        return k.id in ohne_modell
    return p >= schwelle_


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
