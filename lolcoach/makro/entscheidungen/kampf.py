"""B8. Kaempfe als Makro - ob und wann, nicht wie (K1-K7)."""
from __future__ import annotations

from ...bewertung import abstand
from .. import rechner
from ..kommando import Kommando, sek
from ..lage import MakroLage
from . import entscheidung
from ._hilfe import gegner_bei, name
from .objectives import zahl_am


@entscheidung("K1", "Kampf annehmen oder ablehnen", "D", ("kampf", "scoreboard", "gegner_sichtungen"), ("Re:ueberzahl", "D:gefahr"))
def k1(lage: MakroLage):
    k = lage.kampf
    if k is None or k.in_s > 15:
        return None
    z = zahl_am(lage, k.pos, k.in_s + 5)
    bald = min((g for g in lage.gegner if not g.lebt and g.respawn <= k.in_s + 10), key=lambda g: g.respawn, default=None)
    if z.vorteil < 0:
        extra = f", {name(bald)} lebt in {sek(bald.respawn)}" if bald else ""
        return Kommando("K1", "Nicht kaempfen", f"{z.wir} gegen {z.gegner_moeglich}{extra}", klasse="gefahr", wert=4.0)
    return Kommando("K1", "Kampf annehmen", f"{z.wir} gegen {z.gegner_moeglich}", klasse="objective", wert=2.0)


@entscheidung("K2", "Warten auf den Mitspieler", "Re", ("kampf", "scoreboard", "mitspieler_positionen"), ("Re:ueberzahl", "Re:ankunft"))
def k2(lage: MakroLage):
    k = lage.kampf
    if k is None or k.in_s <= 0:
        return None
    jetzt = zahl_am(lage, k.pos, 0)
    kommt = [(m.respawn + 40 if not m.lebt else rechner.ankunft(m.pos, k.pos), m) for m in lage.mitspieler
             if (not m.lebt and m.respawn <= 20) or (m.lebt and m.pos and 3 < rechner.ankunft(m.pos, k.pos) <= 15)]
    if not kommt or jetzt.vorteil > 0:
        return None
    t, m = min(kommt, key=lambda x: x[0])
    spaeter = zahl_am(lage, k.pos, t)
    if spaeter.wir <= jetzt.wir or spaeter.vorteil < 0:       # auch danach Unterzahl: dann K1 (nicht kaempfen)
        return None
    return Kommando("K2", f"Warte {sek(t)} auf {name(m)}", f"dann {spaeter.wir} gegen {spaeter.gegner_moeglich}")


@entscheidung("K3", "Zum Kampf laufen oder nicht", "Re", ("kampf", "eigene_position"), ("Re:ankunft",))
def k3(lage: MakroLage):
    k = lage.kampf
    if k is None or lage.ich.pos is None or k.in_s > 0:
        return None
    t = rechner.ankunft(lage.ich.pos, k.pos, lage.ich.tempo)
    if t <= 4:
        return None
    if t > k.dauer_s:
        return Kommando("K3", "Nicht hinlaufen", f"du bist in {sek(t)} da, der Kampf dauert {sek(k.dauer_s)}",
                        "nimm stattdessen Welle oder Turm")
    return Kommando("K3", "Hin", f"du bist in {sek(t)} da, bevor der Kampf entschieden ist", klasse="objective", wert=2.0)


@entscheidung("K4", "Nach dem Sieg: umwandeln", "D", ("ereignisse", "monster_timer", "scoreboard"), ("D:umwandlung",))
def k4(lage: MakroLage):
    if not lage.ereignis("kampf", "gewonnen", 10):
        return None
    tote = lage.tote(lage.gegner)
    if len(tote) < 2:
        return None
    b = lage.mon("baron")
    d = lage.mon("drache") or lage.mon("elder")
    if b and b.spawn_in == 0 and min(g.respawn for g in tote) >= 25:
        ziel = "Baron jetzt"
    elif d and d.spawn_in == 0:
        ziel = f"{'Elder' if d.art == 'elder' else 'Drache'} jetzt"
    else:
        ziel = "den naechsten Turm jetzt"
    return Kommando("K4", f"{len(tote)} tot: {ziel}", "ein gewonnener Kampf ohne Gebaeude oder Monster ist verschenkt",
                    "Reset", klasse="objective", wert=4.0)


@entscheidung("K5", "Nach der Niederlage: retten", "D,M", ("ereignisse", "welle_eigen"), ("D:gefahr",))
def k5(lage: MakroLage):
    if not lage.ereignis("kampf", "verloren", 10):
        return None
    return Kommando("K5", "Nicht nachlaufen: Welle am naechsten Turm halten", "ihr habt den Kampf verloren, sie sind in Ueberzahl",
                    "warten, bis eure Toten zurueck sind", klasse="gefahr", wert=3.0)


@entscheidung("K6", "Pick-Chance melden", "M,D", ("gegner_sichtungen", "mitspieler_positionen"), ("Re:ankunft",))
def k6(lage: MakroLage):
    if lage.ich.pos is None:
        return None
    for g in lage.gegner:
        if not g.lebt or g.pos is None or g.gesehen_vor is None or g.gesehen_vor > 3:
            continue
        freunde = [x for x in gegner_bei(lage, g.pos, 3000) if x is not g]
        if freunde:
            continue
        t = rechner.ankunft(lage.ich.pos, g.pos, lage.ich.tempo)
        helfer = lage.mitspieler_bei(g.pos, 5000)
        if t <= 20 and helfer:
            return Kommando("K6", f"{name(g)} allein: Ping und mit {name(helfer[0])} hin", f"du bist in {sek(t)} da")
    return None


@entscheidung("K7", "Nicht allein sterben", "D", ("uhr", "mitspieler_positionen", "gegner_sichtungen"),
              ("Re:todes_kosten", "D:gefahr"))
def k7(lage: MakroLage):
    if lage.zeit < 1500 or lage.ich.pos is None:
        return None
    tz = rechner.todes_kosten(lage.ich.level, lage.zeit)
    if tz < 35 or lage.mitspieler_bei(lage.ich.pos, 3000) or len(lage.unbekannt()) < 3:
        return None
    return Kommando("K7", "Bleib diesseits der Flussmitte, nicht allein tiefer", f"{sek(tz)} Todeszeit und {len(lage.unbekannt())} fehlen",
                    klasse="gefahr", wert=4.0)
