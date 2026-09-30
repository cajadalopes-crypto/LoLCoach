"""B1. Sicht und Information (S1-S14)."""
from __future__ import annotations

from .. import rechner, regeln
from ..kommando import Kommando, sek
from ..lage import GRUBEN, MakroLage
from . import entscheidung
from ._hilfe import GRUBE_DE, MONSTER_DE, grube, monster_nah, name, seite

UNSERE_SEITE_MONSTER = {"top": ("herold", "larven", "baron"), "mid": ("drache", "herold", "larven", "baron", "elder"),
                        "bot": ("drache", "elder"), None: ("drache", "herold", "larven", "baron", "elder")}


def _jungler_start(lage: MakroLage) -> str | None:
    """Startseite des Gegner-Junglers: aus J1 (plan) oder erster Sichtung vor 2:30."""
    if lage.plan.get("jungler_start"):
        return lage.plan["jungler_start"]
    j = lage.gegner_jungler
    if j and j.pos and j.gesehen_vor is not None and lage.zeit - j.gesehen_vor <= 150:
        return seite(j.pos)
    return None


@entscheidung("S1", "Erster Trinket: welcher Busch", "D,R", ("uhr", "gegner_sichtungen", "scoreboard"),
              ("D:jungler", "R:S1"))
def s1(lage: MakroLage):
    if lage.zeit >= regeln.patch("gank")["fenster_ab_s"] + 60 or lage.trinket != "gelb" or lage.lane not in ("top", "bot"):
        return None
    start = _jungler_start(lage) or lage.hirn.jungler_seite()
    if start is None:
        return None
    r = regeln.regel("S1")
    unsere = "oben" if lage.lane == "top" else "unten"
    busch, warum = (r["tri_busch"], "er hat auf deiner Seite begonnen und kommt aus seinem Jungle") if start == unsere \
        else (r["fluss_busch"], "er hat auf der anderen Seite begonnen und kommt ueber den Fluss")
    return Kommando("S1", f"Trinket in den {busch}", warum)


@entscheidung("S2", "Trinket halten statt sofort setzen", "D,R", ("uhr", "eigene_items"), ("R:S2", "Re:rueckwaerts"))
def s2(lage: MakroLage):
    r = regeln.regel("S2")
    if not (60 <= lage.zeit < r["halten_bis_s"]) or lage.trinket != "gelb" or lage.wards:
        return None
    return Kommando("S2", f"Halte den Trinket bis {sek(r['halten_bis_s'])} Spielzeit",
                    "vorher kommt der erste Gank praktisch nie (unter 5 % der Faelle)",
                    "setz ihn in den Busch, aus dem er kommt")


@entscheidung("S3", "Welle schieben, um warden zu koennen", "M,Re", ("welle_eigen", "gegner_sichtungen", "uhr"),
              ("Re:crash_dauer", "Re:wellenkosten"))
def s3(lage: MakroLage):
    w = lage.welle()
    j = lage.gegner_jungler
    unbekannt = j is None or j.gesehen_vor is None or j.gesehen_vor > 20
    will_ward = lage.plan.get("ward") or (unbekannt and lage.zeit >= regeln.patch("gank")["fenster_ab_s"] and not lage.wards)
    if not will_ward or w.stand in ("gecrasht", "bei_ihnen", None):
        return None
    t = rechner.crash_dauer() + 14
    gold, _ = rechner.wellenkosten(20, lage.zeit, w.stand)
    return Kommando("S3", f"Drueck die Welle in den naechsten {sek(t)} rein", "sonst kostet dich der Ward Farm"
                    + (f" (etwa {gold:.0f} Gold)" if gold > 20 else ""), "Ward in den Tri-Busch")


@entscheidung("S4", "Tiefer Ward zum Jungler-Tracken", "D,M,R", ("welle_eigen", "scoreboard", "gegner_sichtungen"),
              ("Re:fenster_jungler", "R:S4"))
def s4(lage: MakroLage):
    lg = lage.lane_gegner
    if lage.welle().stand != "gecrasht" or lg is None or (lg.lebt and not lg.backt):
        return None
    j = lage.gegner_jungler
    ziel = lage.gegner_turm() or lage.ich.pos
    t = rechner.fenster_jungler(j.pos if j else None, j.gesehen_vor if j else None, ziel) if j and j.lebt else 99.0
    if t is None or t < regeln.regel("S4")["jungler_mind_s"]:
        return None
    grund = f"{name(lg)} ist {'tot' if not lg.lebt else 'back'} und ihr Jungler ist weit weg"
    return Kommando("S4", "5 s rein, Ward an ihren Krug-Eingang", grund, "sofort raus")


@entscheidung("S5", "Umweg fuer Info", "D,Re", ("gegner_sichtungen", "eigene_position"), ("Re:ankunft", "D:jungler"))
def s5(lage: MakroLage):
    if not lage.plan.get("unterwegs"):
        return None
    j = lage.gegner_jungler
    if j is None or not j.lebt or (j.gesehen_vor is not None and j.gesehen_vor <= 30):
        return None
    return Kommando("S5", "Lauf durch ihren Raptoren-Eingang, 3 s Umweg", "dann weisst du, ob ihr Jungler oben ist")


@entscheidung("S6", "Kontroll-Auge: kaufen und wohin", "D,R", ("eigene_items", "eigene_position"), ("R:S6",))
def s6(lage: MakroLage):
    r = regeln.regel("S6")
    if not lage.ich.im_brunnen or lage.gold < r["preis"] or lage.kontrollauge_inventar or lage.kontrollauge_gesetzt:
        return None
    ort = r["orte"][0] if lage.lane == "top" else r["orte"][1]
    return Kommando("S6", "Kontroll-Auge mitnehmen", f"in den {ort}: von dort kommen die Ganks", "")


@entscheidung("S7", "Linse statt gelbem Trinket", "D,R", ("eigene_items", "uhr", "monster_timer"), ("R:S7",))
def s7(lage: MakroLage):
    r = regeln.regel("S7")
    if not lage.ich.im_brunnen or lage.trinket != "gelb":
        return None
    m = monster_nah(lage, 180)
    if lage.ich.rolle in r["rollen_frueh"] or (lage.zeit >= r["top_ab_s"] and m is not None):
        was = MONSTER_DE[m.art] if m else "das naechste Objective"
        return Kommando("S7", "Tausch beim Back auf Linse", f"{was} kommt, du raeumst die Grube")
    return None


@entscheidung("S8", "Sicht vor dem Objective", "D,R", ("monster_timer", "uhr"), ("R:S8", "D:ketten"))
def s8(lage: MakroLage):
    r = regeln.regel("S8")
    m = monster_nah(lage, r["von_s"], UNSERE_SEITE_MONSTER.get(lage.lane, UNSERE_SEITE_MONSTER[None]))
    if m is None or m.spawn_in < r["bis_s"]:
        return None
    return Kommando("S8", f"{MONSTER_DE[m.art]} in {sek(m.spawn_in)}: Ward den Eingang auf ihrer Seite",
                    "wer vorher Sicht hat, bekommt das Monster", "Welle", klasse="objective", wert=2.0)


@entscheidung("S9", "Raeumen vor dem Objective", "R", ("monster_timer", "eigene_items"), ("R:S9",))
def s9(lage: MakroLage):
    r = regeln.regel("S9")
    m = monster_nah(lage, r["von_s"])
    if m is None or m.spawn_in < r["bis_s"] or not (lage.trinket == "linse" or lage.kontrollauge_inventar):
        return None
    mit = "Linse" if lage.trinket == "linse" else "Kontroll-Auge"
    return Kommando("S9", f"{mit} jetzt an der {GRUBE_DE[m.art]}", "ihr Ward muss weg, bevor ihr startet",
                    klasse="objective", wert=1.5)


@entscheidung("S10", "Flanken-Ward vor dem Split", "D,R", ("eigene_wards", "eigene_position"), ("R:S10",))
def s10(lage: MakroLage):
    if not lage.plan.get("split") or any("Flanke" in w.ort for w in lage.wards):
        return None
    return Kommando("S10", "Bevor du drueckst: Ward an ihren Jungle-Eingang zu deiner Seite",
                    "sonst stirbst du ohne Warnung (allein splitten ohne Info endet oft tot)", klasse="gefahr", wert=3.0)


@entscheidung("S11", "Kein Face-Check", "D,M", ("busch_sicht", "gegner_sichtungen"), ("R:S11", "D:gefahr"))
def s11(lage: MakroLage):
    if not lage.gesehen_busch or len(lage.unbekannt()) < regeln.regel("S11")["unbekannt_mind"]:
        return None
    n = len(lage.unbekannt())
    return Kommando("S11", "Bleib vor dem Busch, erst Ward oder Linse", f"{n} fehlen", "dann rein", klasse="gefahr", wert=4.0)


@entscheidung("S12", "Sicht abgelaufen oder zerstoert", "M,R", ("eigene_wards", "ward_weg"), ("R:S12",))
def s12(lage: MakroLage):
    if not lage.ward_verloren:
        return None
    return Kommando("S12", f"Dein Ward im {lage.ward_verloren} ist weg: neu setzen", "ohne ihn siehst du keinen Gank",
                    "erst dann wieder vorgehen")


@entscheidung("S13", "Trinket-Ladungen nicht verfallen lassen", "M,R", ("trinket_ladungen",), ("R:S13",))
def s13(lage: MakroLage):
    if lage.trinket != "gelb" or lage.trinket_ladungen is None or lage.trinket_ladungen < regeln.regel("S13")["ladungen_max"]:
        return None
    return Kommando("S13", "Einen Ward jetzt in den Fluss", "beide Ladungen sind voll, sonst verfaellt eine")


@entscheidung("S14", "Ward fuer einen Mitspieler oder ein Objective", "M,R",
              ("mitspieler_positionen", "monster_timer", "eigene_wards"), ("R:S14",))
def s14(lage: MakroLage):
    m = monster_nah(lage, 60, ("larven", "herold", "baron") if lage.lane == "top" else ("drache", "elder"))
    j = lage.unser_jungler
    if m is None or j is None or not j.pos or any(m.art in w.ort.lower() for w in lage.wards):
        return None
    if lage.abstand_zu(grube(m)) is None or lage.abstand_zu(grube(m)) > 5000:
        return None
    from ...bewertung import abstand
    if abstand(j.pos, GRUBEN[m.art]) > 5000:
        return None
    return Kommando("S14", f"Setz den Ward an die {MONSTER_DE[m.art]}", f"{name(j)} geht gleich hin und hat dort keine Sicht",
                    klasse="objective", wert=1.0)
