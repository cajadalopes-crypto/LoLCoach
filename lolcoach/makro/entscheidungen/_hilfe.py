"""Kleine Helfer fuer die Entscheidungen: Namen, Orte in Worten, Seiten."""
from __future__ import annotations

from ...bewertung import abstand
from ..lage import GRUBEN, MakroLage, Spieler

MONSTER_DE = {"drache": "Drache", "elder": "Elder", "larven": "Larven", "herold": "Herold", "baron": "Baron"}
MONSTER_DAT = {"drache": "Drachen", "elder": "Elder", "larven": "Larven", "herold": "Herold", "baron": "Baron"}   # am/vor dem/zum
GRUBE_DE = {"drache": "Drachengrube", "elder": "Drachengrube", "baron": "Barongrube", "herold": "Herold-Grube",
            "larven": "Larven-Grube"}
AKTION_TU = {"Back": "Back", "Lane": "zurueck an die Welle", "Gruppe": "mit der Gruppe weiter", "Jungle": "Camps nehmen",
             "Split": "Seitenwelle druecken", "Warten": "halten", "TP": "TP bereit halten", "Rotation": "Seite wechseln"}


def tu_aus_option(opt) -> str:
    """Eine Option aus dem Gehirn (Aktion, Ziel, ...) als Kommando-Teil."""
    if opt is None:
        return "ihren naechsten Turm"
    akt, ziel = opt[0], opt[1]
    if akt == "Objective" and ziel:
        return {"Drache": "zum Drachen", "Baron": "zum Baron", "Herold": "zum Herold", "Larven": "zu den Larven",
                "Elder": "zum Elder"}.get(ziel, ziel)
    if akt == "Unterwegs" and ziel:
        return f"Richtung {ziel}"
    if akt == "Rotation" and ziel:
        return {"oben": "auf die Top-Seite", "mid": "nach Mid", "unten": "auf die Bot-Seite"}.get(ziel, ziel)
    return AKTION_TU.get(akt, akt)


LANE_DE = {"top": "Top", "mid": "Mid", "bot": "Bot"}
# Krabbler (Fluss oben / unten) - grobe Orte
KRABBLER = {"oben": (4400, 9700), "unten": (10400, 5100)}
NEXUS = {"ORDER": (1748, 2270), "CHAOS": (13052, 12612)}
INHIB = {("ORDER", "top"): (1170, 3570), ("ORDER", "mid"): (3200, 3200), ("ORDER", "bot"): (3450, 1250),
         ("CHAOS", "top"): (11260, 13680), ("CHAOS", "mid"): (11600, 11600), ("CHAOS", "bot"): (13600, 11300)}


def name(s: Spieler | None, ersatz: str = "er") -> str:
    return s.champion if s and s.champion else ersatz


def seite(pos) -> str | None:
    """'oben' (Top-Seite der Karte) oder 'unten'."""
    if pos is None:
        return None
    return "oben" if pos[1] > pos[0] else "unten"


def lane_der_seite(s: str | None) -> str | None:
    return {"oben": "Top", "unten": "Bot"}.get(s or "")


def monster_nah(lage: MakroLage, bis: float, arten=("drache", "elder", "baron", "herold", "larven")):
    ms = [m for m in lage.monster if m.art in arten and m.spawn_in <= bis]
    return min(ms, key=lambda m: m.spawn_in, default=None)


def grube(m) -> tuple[float, float]:
    return GRUBEN[m.art]


def gegner_bei(lage: MakroLage, pos, r: float = 3000, alter: float = 8.0) -> list[Spieler]:
    return [g for g in lage.gegner if g.lebt and g.pos and g.gesehen_vor is not None and g.gesehen_vor <= alter
            and abstand(g.pos, pos) <= r]


def unsere_seite(lage: MakroLage) -> str | None:
    return {"top": "oben", "bot": "unten"}.get(lage.lane or "")
