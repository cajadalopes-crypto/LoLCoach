"""B6. Roams und Rotationen zu Fuss (R1-R10)."""
from __future__ import annotations

from ...bewertung import abstand
from .. import rechner, regeln
from ..kommando import Kommando, sek
from ..lage import LANE_MITTE, MakroLage
from . import entscheidung
from ._hilfe import KRABBLER, MONSTER_DE, grube, monster_nah, name, seite, unsere_seite


@entscheidung("R1", "Roam Mid", "Re,D", ("welle_eigen", "gegner_flash", "scoreboard", "eigene_position"),
              ("Re:roam_wert", "Re:ankunft", "D:wert"))
def r1(lage: MakroLage):
    if lage.lane == "mid" or lage.welle().stand != "gecrasht" or lage.ich.pos is None:
        return None
    mid = lage.rolle(lage.gegner, "MIDDLE")
    if mid is None or not mid.lebt or not ((mid.flash_in or 0) > 0 or mid.leben < 0.4):
        return None
    weg = rechner.ankunft(lage.ich.pos, LANE_MITTE["mid"], lage.ich.tempo)
    gewinn = lage.hirn.wert("Unterwegs", "Midlane")
    gewinn = gewinn if gewinn is not None else 1.5
    if rechner.roam_wert(2 * weg, lage.zeit, "gecrasht", gewinn) <= 0:
        return None
    warum = f"{name(mid)} ohne Flash" if (mid.flash_in or 0) > 0 else f"{name(mid)} hat wenig Leben"
    return Kommando("R1", f"Ueber den Fluss Mid ({sek(weg)})", f"Welle drin, {warum}")


@entscheidung("R2", "Zum Fluss oder Krabbler fuer den eigenen Jungler", "Re,D", ("mitspieler_positionen", "welle_eigen"),
              ("Re:ankunft",))
def r2(lage: MakroLage):
    s = unsere_seite(lage)
    uj = lage.unser_jungler
    if s is None or uj is None or uj.pos is None or lage.zeit < 190 or lage.welle().stand not in ("gecrasht", "bei_ihnen"):
        return None
    if abstand(uj.pos, KRABBLER[s]) > 2500 or (195 <= lage.zeit <= 240):     # 3:15-4:00 macht J13
        return None
    t = rechner.ankunft(lage.ich.pos, KRABBLER[s]) if lage.ich.pos else 15
    return Kommando("R2", f"Zum Fluss ({sek(t)})", f"{name(uj)} ist dort und braucht dich", "dann zurueck an die Welle")


@entscheidung("R3", "Zu den Larven oder zum Herold", "D,Re", ("monster_timer", "welle_eigen"), ("D:ketten", "Re:ankunft"))
def r3(lage: MakroLage):
    m = monster_nah(lage, 45, ("larven", "herold"))
    if m is None or lage.welle().stand not in ("gecrasht", "bei_ihnen", "mitte"):
        return None
    t = rechner.ankunft(lage.ich.pos, grube(m)) if lage.ich.pos else 20
    vorher = "Welle rein, dann " if lage.welle().stand == "mitte" else ""
    return Kommando("R3", f"{vorher}an den Eingang der {MONSTER_DE[m.art]} ({sek(t)})", f"{MONSTER_DE[m.art]} in {sek(m.spawn_in)}",
                    klasse="objective", wert=1.5)


@entscheidung("R4", "Zum Drachen zu Fuss", "Re,D", ("monster_timer", "eigene_position"), ("Re:ankunft",))
def r4(lage: MakroLage):
    m = monster_nah(lage, 60, ("drache", "elder"))
    if m is None or lage.ich.pos is None or not lage.ich.lebt:
        return None
    t = rechner.ankunft(lage.ich.pos, grube(m), lage.ich.tempo)
    if t > m.spawn_in + 10 or lage.abstand_zu(grube(m)) < 3000:
        return None
    return Kommando("R4", "Zum Drachen, los", f"zu Fuss schaffst du es in {sek(t)}, er startet in {sek(m.spawn_in)}",
                    klasse="objective", wert=2.0)


@entscheidung("R5", "Roam abbrechen", "M,Re", ("gegner_sichtungen", "welle_eigen"), ("Re:fenster_welle",))
def r5(lage: MakroLage):
    ziel = lage.plan.get("roam")
    if not ziel:
        return None
    opfer = next((g for g in lage.gegner if g.champion == ziel), None)
    if opfer and (not opfer.lebt or opfer.backt or opfer.im_brunnen):
        return Kommando("R5", "Abbrechen", f"{name(opfer)} ist nicht mehr da", "zurueck an deine Welle")
    if lage.welle().stand == "bei_uns":
        return Kommando("R5", "Abbrechen", "deine Welle laeuft zu dir", "zurueck an deine Welle")
    return None


@entscheidung("R6", "Rotation nach Turmverlust", "D", ("ereignisse", "scoreboard"), ("D:rotation",))
def r6(lage: MakroLage):
    if lage.turm_gefallen_vor is None or lage.turm_gefallen_vor > 30 or not lage.tuerme_weg:
        return None
    team, lane, stufe = lage.tuerme_weg[0]
    if lane.lower() != (lage.lane or "") or stufe != "aussen":
        return None
    mid = lage.rolle(lage.mitspieler, "MIDDLE")
    m = monster_nah(lage, 120, ("herold", "larven", "drache"))
    danach = f"dann {MONSTER_DE[m.art]}" if m else ""
    if team == lage.team:
        return Kommando("R6", f"Dein {lane.capitalize()}-Turm ist weg: Mid-Welle mit {name(mid, 'eurem Mid')}",
                        "in der Seitenlane druecken sie jetzt bis Turm 2", danach)
    return Kommando("R6", "Ihr Turm ist weg: rotier Mid", "oben ist nichts mehr zu holen", danach)


@entscheidung("R7", "Weg waehlen", "D,Re", ("gegner_sichtungen", "eigene_position"), ("D:gefahr", "Re:ankunft"))
def r7(lage: MakroLage):
    if not lage.plan.get("unterwegs") or len(lage.unbekannt()) < 2:
        return None
    return Kommando("R7", "Durch euren Jungle, nicht durch den Fluss", f"{len(lage.unbekannt())} Gegner fehlen", klasse="gefahr", wert=1.5)


@entscheidung("R8", "Roam-Kosten gegen Nutzen", "Re,D", ("welle_eigen", "eigene_position"),
              ("Re:roam_wert", "Re:wellenkosten", "D:wert"))
def r8(lage: MakroLage):
    ziel = lage.plan.get("roam")
    if not ziel or lage.ich.pos is None:
        return None
    weg = 2 * rechner.ankunft(lage.ich.pos, LANE_MITTE["mid"], lage.ich.tempo)
    gewinn = lage.plan.get("roam_gewinn", 0.5)
    netto = rechner.roam_wert(weg, lage.zeit, lage.welle().stand, gewinn)
    if netto >= 0:
        return None
    gold, _ = rechner.wellenkosten(weg, lage.zeit, lage.welle().stand)
    return Kommando("R8", "Nicht roamen", f"du verlierst etwa {gold:.0f} Gold an Wellen, der Gewinn ist kleiner")


@entscheidung("R9", "Mit dem Jungler invaden", "D,Re", ("gegner_sichtungen", "mitspieler_positionen", "welle_eigen"),
              ("Re:fenster_jungler",))
def r9(lage: MakroLage):
    gj, uj = lage.gegner_jungler, lage.unser_jungler
    s = unsere_seite(lage)
    if not (gj and uj and s) or gj.pos is None or uj.pos is None or lage.ich.pos is None:
        return None
    if gj.gesehen_vor is None or gj.gesehen_vor > 10 or seite(gj.pos) == s or abstand(uj.pos, lage.ich.pos) > 3000:
        return None
    if lage.welle().stand not in ("gecrasht", "bei_ihnen"):
        return None
    return Kommando("R9", f"Mit {name(uj)} in ihren {'oberen' if s == 'oben' else 'unteren'} Jungle",
                    f"ihr Jungler ist auf der anderen Seite", "Krug und Raptoren, dann zurueck")


@entscheidung("R10", "Gegner-Camp nehmen", "R,M", ("welle_eigen", "gegner_sichtungen"), ("R:R10", "Re:fenster_jungler"))
def r10(lage: MakroLage):
    r = regeln.regel("R10")
    lg, gj = lage.lane_gegner, lage.gegner_jungler
    if lage.welle().stand != "gecrasht" or lage.zeit < 150 or lage.lane not in ("top", "bot"):
        return None
    if lg and lg.lebt and not lg.backt and lg.gesehen_vor is not None and lg.gesehen_vor <= 5:
        return None
    ziel = lage.gegner_turm() or lage.ich.pos
    t = rechner.fenster_jungler(gj.pos, gj.gesehen_vor, ziel) if gj and gj.lebt and gj.pos else (99.0 if gj and not gj.lebt else None)
    if t is None or t < r["jungler_mind_s"]:
        return None
    return Kommando("R10", f"Ihre Krug: {r['dauer_s']} s, dann zurueck", "die Welle ist drin und ihr Jungler ist weit weg")
