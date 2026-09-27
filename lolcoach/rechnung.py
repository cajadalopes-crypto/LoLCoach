"""Spielmechanik als Rechnung: Leben, Zuenden, Turmschuesse - die Zahlen aus wissen/mechanik.toml (Wiki, Patch 26.1)
und Data Dragon, damit das Kampf-Urteil mit Werten rechnet statt mit "viel" und "wenig".

Reasoning #1 ("Reicht mein Full-Combo-Schaden jetzt fuer den Kill?") und #37 (Turm: Schaden, Dive-Potenzial).
Was hier NICHT steht: Faehigkeitsschaden der Champions (haengt an Raengen, Items, Resistenzen) - dafuer fehlen
die Rohdaten in verlaesslicher Form; der Coach nennt deshalb nur, was sicher zu rechnen ist.
"""
from __future__ import annotations

from . import ddragon, wissen
from .zustand import Spieler


def wachstum(basis: float, je_level: float, level: int) -> float:
    """Riots Wachstumsformel fuer Grundwerte: basis + je_level * (L-1) * (0,7025 + 0,0175 * (L-1))."""
    n = max(1, level) - 1
    return basis + je_level * n * (0.7025 + 0.0175 * n)


def max_leben(s: Spieler) -> float:
    """Maximales Leben: Grundwert nach Level (Data Dragon) + Leben aus Items + die Leben-Rune (10 je Level).
    Gemessen 27.09. am eigenen Champion (API maxHealth, 5 Partien): ohne Rune fehlten genau 10 x Level in 3 von 5
    Partien (die skalierende Leben-Scherbe, 10-180), 65 flach in einer, 0 in einer. Ohne Stapel (Herzstahl, Seelen)
    - eher zu niedrig, also eher zu optimistisch fuer einen Kill; deshalb nur mit Abschlag benutzen."""
    st = (ddragon.champions().get(s.champion_id) or {}).get("stats", {})
    leben = wachstum(float(st.get("hp", 600)), float(st.get("hpperlevel", 100)), s.level)
    it = ddragon.items()
    return leben + sum(float(it.get(i, {}).get("stats", {}).get("FlatHPPoolMod", 0.0)) for i in s.items) \
        + LEBEN_RUNE_JE_LEVEL * max(1, min(18, s.level))


LEBEN_RUNE_JE_LEVEL = 10.0   # skalierende Leben-Scherbe (10 auf Level 1 .. 180 auf 18)


def zuenden_schaden(level: int) -> float:
    """Wahrer Schaden von Zuenden ueber 5 s (Wiki Ignite): 70 + 20 je Level bis 5 + 25 je Level danach."""
    z = wissen.lade("mechanik")["zuenden"]
    return z["schaden_basis"] + z["pro_level_frueh"] * (min(level, 5) - 1) + z["pro_level_spaet"] * max(0, level - 5)


# Gemessen 27.09. (werkzeuge/turm_schaden.py): die sauberen ersten Treffer auf Riven (191, 213, 203, 202 - kein
# Gegner nah, Turm kalt) lagen innerhalb 5 % bei Wiki-Wert x 1,15 nach Ruestung; ohne Ruestung war jeder Schuss
# 30-75 % zu hoch gerechnet ("du haeltst 2 Schuesse aus", wo es 3 waren).
TURM_KORREKTUR = 1.15


def turm_schaden(stufe: str, zeit: float, ruestung: float | None = None) -> float:
    """Schaden des ersten Turmschusses an Champions (Wiki Turret): stufe 'aussen', 'innen', 'Inhib'. Mit `ruestung`
    (eigene, aus der API): der Treffer, der bei dir ankommt."""
    t = wissen.lade("mechanik")["tuerme"]
    s = t.get({"aussen": "schaden_aussen", "innen": "schaden_innen", "Inhib": "schaden_inhib"}.get(stufe, "schaden_aussen"))
    minute = zeit / 60
    roh = min(s["max"], s["start"] + s["pro_min"] * max(0.0, minute - s["ab_min"]))
    if ruestung is None:
        return roh
    return roh * TURM_KORREKTUR * 100 / (100 + max(0.0, ruestung))


def ruestung(p) -> float | None:
    """Die eigene Ruestung aus der Live-API (activePlayer.championStats.armor), sonst None."""
    try:
        r = p.werte.get("armor") if p is not None else None
        return float(r) if r is not None else None
    except (TypeError, ValueError):
        return None


def turm_schuesse(leben: float, stufe: str, zeit: float, ruestung: float | None = None) -> int:
    """Wie viele Turmschuesse haelt man mit `leben` aus? Jeder Schuss auf denselben Champion waermt um +50 %
    auf, hoechstens +150 % (Wiki Turret). Ohne Ruestung gerechnet - eher einer zu wenig als einer zu viel."""
    t = wissen.lade("mechanik")["tuerme"]
    erst, n, summe = turm_schaden(stufe, zeit, ruestung), 0, 0.0
    while True:
        summe += erst * (1 + min(t["aufwaermen_max"], t["aufwaermen_je_schuss"] * n))
        if summe >= leben:
            return n
        n += 1
        if n > 20:
            return n
