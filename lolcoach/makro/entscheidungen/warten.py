"""B12. Warten mit Grund und Zeitfenster (Z1-Z3). Warten ist ein Kommando; bei 'unklar' nie Schweigen."""
from __future__ import annotations

from .. import rechner
from ..kommando import Kommando, sek
from ..lage import MakroLage
from . import entscheidung
from ._hilfe import MONSTER_DE, monster_nah, name

AKTION_DE = {"Back": "Back", "Lane": "Bleib an der Welle", "Gruppe": "Geh zu deinem Team", "Jungle": "Nimm Camps",
             "Split": "Druck die Seitenwelle", "Warten": "Bleib, wo du bist", "TP": "Halte den TP bereit",
             "Rotation": "Wechsel die Seite", "Objective": "Geh zum Objective", "Unterwegs": "Geh"}


@entscheidung("Z1", "Warte X s auf Welle, Respawn, TP oder Sicht", "Re,D", ("scoreboard", "eigene_zauber", "welle_eigen"),
              ("Re:ueberzahl", "Re:tp_abklingzeit"))
def z1(lage: MakroLage):
    m = monster_nah(lage, 60)
    kommt = [m_ for m_ in lage.mitspieler if not m_.lebt and m_.respawn <= 12]
    if m is not None and kommt:
        x = max(k.respawn for k in kommt)
        return Kommando("Z1", f"Warte {sek(x)}", f"dann ist {name(kommt[0])} zurueck, erst dann {MONSTER_DE[m.art]}",
                        klasse="objective", wert=1.5)
    if lage.plan.get("tp") and lage.ich.tp_hat and lage.ich.tp_in and lage.ich.tp_in <= 10:
        return Kommando("Z1", f"Warte {sek(lage.ich.tp_in)}", "dann ist dein TP bereit")
    w = lage.welle()
    if w.kanone_in is not None and w.kanone_in <= 10 and w.stand in ("mitte", "bei_uns"):
        return Kommando("Z1", f"Warte {sek(w.kanone_in)} auf die Kanone", "sie ist das meiste Gold der Welle")
    return None


@entscheidung("Z2", "Fenster ansagen", "Re,D", ("scoreboard", "gegner_sichtungen"), ("Re:fenster_gegner",))
def z2(lage: MakroLage):
    lg = lage.lane_gegner
    if lg is None or (lg.lebt and not lg.backt):
        return None
    t = rechner.fenster_gegner(respawn=lg.respawn if not lg.lebt else None, backt=lg.backt,
                               weg_zur_lane=rechner.brunnen_lane(lage.lane or "top", lage.gegnerteam))
    if t is None or t < 20:
        return None
    return Kommando("Z2", f"Du hast {sek(t)}", f"{name(lg)} ist {'tot' if not lg.lebt else 'back'}", "Welle und Platten, dann Back")


@entscheidung("Z3", "Nichts tun ist richtig (Klarheit unklar)", "D", ("scoreboard", "gegner_sichtungen"), ("D:klarheit", "D:policy"))
def z3(lage: MakroLage):
    if lage.hirn.klarheit != "unklar" or not lage.hirn.optionen:
        return None
    akt, ziel = lage.hirn.optionen[0][0], lage.hirn.optionen[0][1]      # bei unklar: was High-Elo hier am haeufigsten tut
    tu = AKTION_DE.get(akt, akt) + (f" ({ziel})" if ziel else "")
    j = lage.gegner_jungler
    fehlt = f"bis {name(j)} auftaucht" if j and j.lebt and (j.gesehen_vor is None or j.gesehen_vor > 30) else "bis ihr mehr wisst"
    return Kommando("Z3", tu, f"keine Option ist klar besser, das tun High-Elo-Spieler hier am haeufigsten", fehlt)
