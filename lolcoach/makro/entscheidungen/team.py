"""B11. Team und Kommunikation - Carlos pingt, der Coach sagt, was (P1-P4)."""
from __future__ import annotations

from .. import rechner
from ..kommando import Kommando, sek
from ..lage import MakroLage
from . import entscheidung
from ._hilfe import MONSTER_DE, lane_der_seite, monster_nah, name, seite, unsere_seite


@entscheidung("P1", "Ping-Vorschlag", "M,D", ("gegner_sichtungen",), ("D:jungler",))
def p1(lage: MakroLage):
    j = lage.gegner_jungler
    if j is None or not j.lebt or j.pos is None or j.gesehen_vor is None or j.gesehen_vor > 5:
        return None
    s = seite(j.pos)
    if s is None or s == unsere_seite(lage):
        return None
    return Kommando("P1", f"Ping {lane_der_seite(s)}: Jungler auf dem Weg", f"{name(j)} ist eben auf ihrer Seite aufgetaucht")


@entscheidung("P2", "Mitspieler Go/No-Go", "M", ("mitspieler_hud", "mitspieler_zauber", "monster_timer"), ("D:gefahr",))
def p2(lage: MakroLage):
    m = monster_nah(lage, 60)
    if m is None:
        return None
    schwach = next((s for s in lage.mitspieler if s.lebt and (s.leben < 0.4 or (s.flash_in or 0) > 30)), None)
    if schwach is None:
        return None
    warum = f"{int(schwach.leben * 100)} % Leben" if schwach.leben < 0.4 else "ohne Flash"
    return Kommando("P2", f"{MONSTER_DE[m.art]} erst nach dem Back von {name(schwach)}", f"{name(schwach)} {warum}",
                    klasse="objective", wert=1.5)


@entscheidung("P3", "Hilfe fuer einen Mitspieler", "Re,D", ("kampf", "mitspieler_positionen", "eigene_position"),
              ("Re:ankunft", "Re:ueberzahl"))
def p3(lage: MakroLage):
    k = lage.kampf
    if k is None or not k.bei or lage.ich.pos is None:
        return None
    t = rechner.ankunft(lage.ich.pos, k.pos, lage.ich.tempo)
    if t > 8 or k.wir + 1 < k.gegner:
        return None
    return Kommando("P3", "Geh", f"{k.bei} kaempft, du bist in {sek(t)} da: {k.wir + 1} gegen {k.gegner}", klasse="objective", wert=3.0)


@entscheidung("P4", "Mitspieler tot", "D", ("scoreboard",), ("D:gefahr",))
def p4(lage: MakroLage):
    tote = lage.tote(lage.mitspieler)
    if len(tote) < 2:
        return None
    return Kommando("P4", "Kein Objective, sicher halten", f"{len(tote)} von euch sind tot",
                    f"in {sek(max(t.respawn for t in tote))} seid ihr wieder komplett", klasse="gefahr", wert=3.0)
