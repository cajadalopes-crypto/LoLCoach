"""B7. Objectives (O1-O12)."""
from __future__ import annotations

from ...bewertung import abstand
from .. import rechner, regeln
from ..kommando import Kommando, sek
from ..lage import GRUBEN, MakroLage
from . import entscheidung
from ._hilfe import LANE_DE, MONSTER_DAT, MONSTER_DE, gegner_bei, grube, monster_nah, name, tu_aus_option


def zahl_am(lage: MakroLage, ort, T: float) -> rechner.Zahl:
    """Wer ist in T s am Ort: wir (mit dir) gegen sie - Tote ueber Respawn, Unbekannte als moeglich."""
    wir = [rechner.Einheit(ankunft_s=rechner.ankunft(lage.ich.pos, ort, lage.ich.tempo) if lage.ich.pos else None,
                           lebt=lage.ich.lebt, respawn=lage.ich.respawn)]
    for m in lage.mitspieler:
        wir.append(rechner.Einheit(lebt=m.lebt, respawn=m.respawn,
                                   ankunft_s=rechner.ankunft(m.pos, ort) if m.pos else None))
    geg = []
    for g in lage.gegner:
        bekannt = g.gesehen_vor is not None and g.gesehen_vor <= 10
        geg.append(rechner.Einheit(lebt=g.lebt, respawn=g.respawn, bekannt=bekannt or not g.lebt,
                                   ankunft_s=(max(0.0, rechner.ankunft(g.pos, ort) - (g.gesehen_vor or 0)) if g.pos else None)))
    return rechner.ueberzahl(T, wir, geg)


@entscheidung("O1", "Drache: bestreiten, geben oder tauschen", "D,Re", ("monster_timer", "mitspieler_positionen",
              "gegner_sichtungen", "scoreboard"), ("Re:ueberzahl", "D:wert"))
def o1(lage: MakroLage):
    m = monster_nah(lage, 30, ("drache",))
    if m is None or m.seele:
        return None
    z = zahl_am(lage, grube(m), m.spawn_in + 15)
    if z.vorteil <= -2:
        tausch = f"{LANE_DE.get(lage.lane or 'top', 'Top')}-Turm"
        return Kommando("O1", "Gib den Drachen", f"ihr seid {z.wir} gegen {z.gegner_moeglich} und spaet dran",
                        f"nimm dafuer den {tausch}", klasse="objective", wert=2.0)
    wert = lage.hirn.wert("Objective", "Drache")
    if z.vorteil < 0:
        return Kommando("O1", "Drache nur mit Sicht und allen dort", f"ihr seid {z.wir} gegen {z.gegner_moeglich}",
                        "sonst geben und tauschen", klasse="objective", wert=1.0)
    return Kommando("O1", "Drache bestreiten", f"{z.wir} gegen {z.gegner_moeglich}"
                    + (f", er bringt {wert:.1f} Punkte Siegchance" if wert else ""), klasse="objective", wert=wert or 2.0)


@entscheidung("O2", "Larven", "D,Re", ("monster_timer", "scoreboard", "welle_eigen"), ("Re:ueberzahl", "D:wert"))
def o2(lage: MakroLage):
    m = monster_nah(lage, 30, ("larven",))
    lg, uj = lage.lane_gegner, lage.unser_jungler
    if m is None or uj is None:
        return None
    prio = lage.welle().stand in ("gecrasht", "bei_ihnen") or (lg is not None and (not lg.lebt or lg.backt))
    if not prio:
        return None
    return Kommando("O2", f"Larven mit {name(uj)}", "du hast Prio" + (f", {name(lg)} ist weg" if lg and (not lg.lebt or lg.backt) else ""),
                    klasse="objective", wert=1.5)


@entscheidung("O3", "Herold: nehmen und wo einsetzen", "D,R", ("ereignisse", "platten"), ("R:O3",))
def o3(lage: MakroLage):
    if not lage.ereignis("herold", "wir", 60):
        return None
    if not lage.gegner_platten:
        return None
    lane, platten = min(lage.gegner_platten.items(), key=lambda kv: kv[1])
    rest = f"{platten} Platte" if platten == 1 else f"{platten} Platten"
    return Kommando("O3", f"Herold in {LANE_DE.get(lane, lane)} einsetzen",
                    f"der Turm dort hat nur noch {rest} - der Herold allein ist wenig wert, der Turm danach viel",
                    klasse="objective", wert=1.0)


@entscheidung("O4", "Baron: Bedingungen", "D", ("monster_timer", "scoreboard"), ("D:wert", "D:ketten"))
def o4(lage: MakroLage):
    m = lage.mon("baron")
    if m is None or m.spawn_in > 0:
        return None
    tote = [g for g in lage.tote(lage.gegner) if g.respawn >= 30]
    wert = lage.hirn.wert("Objective", "Baron")
    if len(tote) >= 2 or (wert is not None and wert >= 1.0 and lage.hirn.klarheit == "klar"):
        warum = f"{len(tote)} von ihnen mindestens 30 s tot" if len(tote) >= 2 else "ihr seid klar vorn"
        return Kommando("O4", "Baron jetzt", warum, "Seitenwellen und Tuerme", klasse="objective", wert=wert or 4.0)
    return None


@entscheidung("O5", "Baron abbrechen", "Re,M", ("gegner_sichtungen", "mitspieler_hud"), ("Re:ueberzahl",))
def o5(lage: MakroLage):
    if lage.plan.get("objective") != "baron":
        return None
    kommen = gegner_bei(lage, GRUBEN["baron"], 4000)
    if len(kommen) < 3:
        return None
    return Kommando("O5", "Baron abbrechen", f"{len(kommen)} kommen", "raus Richtung eurer Seite", klasse="gefahr", wert=5.0)


@entscheidung("O6", "Elder oder Seele: alles darauf", "D,R", ("monster_timer", "ereignisse"), ("R:O6", "D:siegchance"))
def o6(lage: MakroLage):
    m = monster_nah(lage, 60, ("elder", "drache"))
    if m is None or not (m.art == "elder" or m.seele):
        return None
    was = "Elder" if m.art == "elder" else "Seelen-Drache"
    sc = lage.hirn.siegchance
    if m.art != "elder" and sc is not None and sc < 0.35:
        return Kommando("O6", f"{was}: nur mit sauberem Setup", "ihr liegt hinten - nach der Seele kommt der Elder",
                        klasse="objective", wert=2.0)
    return Kommando("O6", f"{was} in {sek(m.spawn_in)}: alles dahin", "das entscheidet die Partie", klasse="objective", wert=8.0)


@entscheidung("O7", "Setup-Kette 90/60/30 s", "D,R", ("monster_timer", "uhr"), ("Re:rueckwaerts", "R:O7"))
def o7(lage: MakroLage):
    m = monster_nah(lage, 100)
    if m is None or m.spawn_in <= 0:
        return None
    jetzt, naechst, bis = rechner.rueckwaerts(m.spawn_in)
    if jetzt in ("frei", "Grube"):
        return None
    tu = {"Welle": "Welle rein", "Back": "Back", "Sicht": "Sicht an der Grube"}[jetzt]
    return Kommando("O7", f"{MONSTER_DE[m.art]} in {sek(m.spawn_in)}: {tu}", "so bist du rechtzeitig und voll da",
                    f"in {sek(bis)} {naechst}" if naechst else "", klasse="objective", wert=2.0)


@entscheidung("O8", "Steal-Gefahr", "M,R", ("gegner_sichtungen", "mitspieler_hud"), ("R:O8",))
def o8(lage: MakroLage):
    ziel = lage.plan.get("objective")
    uj, gj = lage.unser_jungler, lage.gegner_jungler
    if not ziel or uj is None or gj is None or not gj.lebt:
        return None
    ort = GRUBEN.get(ziel, GRUBEN["drache"])
    lauert = gj.gesehen_vor is None or gj.gesehen_vor > 15 or (gj.pos and abstand(gj.pos, ort) <= regeln.regel("O8")["smite_bereich"])
    if not lauert or uj.smite_bereit is not False:
        return None
    return Kommando("O8", f"Nicht unter 1500 kloppen ohne {name(uj)}s Smite", "ihr Jungler lauert", klasse="gefahr", wert=3.0)


@entscheidung("O9", "Nach dem Objective: naechstes Ziel", "D", ("ereignisse", "mitspieler_positionen"), ("D:umwandlung",))
def o9(lage: MakroLage):
    e = next((e for e in lage.ereignisse if e[0] in ("drache", "baron", "herold", "larven", "elder") and e[1] == "wir" and e[2] <= 10), None)
    if e is None:
        return None
    b = lage.hirn.beste()
    ziel = tu_aus_option(b) if b and b[0] not in ("Back", "Lane", "Warten") else "auf ihren naechsten Turm"
    return Kommando("O9", f"{MONSTER_DE.get(e[0], e[0])} drin: jetzt {ziel}", "bis einer von ihnen zurueck ist",
                    klasse="objective", wert=2.0)


@entscheidung("O10", "Cross-Map-Tausch", "D", ("gegner_sichtungen", "monster_timer"), ("D:tausch", "Re:ueberzahl"))
def o10(lage: MakroLage):
    m = monster_nah(lage, 15, ("drache", "baron", "herold"))
    if m is None or len(gegner_bei(lage, grube(m), 3000)) < 3:
        return None
    z = zahl_am(lage, grube(m), m.spawn_in + 10)
    if z.vorteil > -2:
        return None
    return Kommando("O10", f"Sie sind am {MONSTER_DAT[m.art]}: Turm auf der anderen Seite",
                    "ein Tausch rettet das meiste (ohne Tausch verliert ihr im Schnitt 439 Gold, mit 25)", klasse="objective", wert=1.5)


@entscheidung("O11", "Aufgeben und sicher zurueck", "D", ("mitspieler_positionen", "gegner_sichtungen"), ("D:gefahr", "Re:ueberzahl"))
def o11(lage: MakroLage):
    ziel = lage.plan.get("objective")
    m = lage.mon(ziel) if ziel else None
    if m is None:
        return None
    z = zahl_am(lage, grube(m), m.spawn_in + 10)
    if z.vorteil > -2:
        return None
    return Kommando("O11", "Zu spaet, nicht reinlaufen", f"{z.wir} gegen {z.gegner_moeglich}", "Welle holen, naechstes Monster",
                    klasse="gefahr", wert=3.0)


@entscheidung("O12", "Objective-Kopfgeld", "D,M", ("kopfgeld", "monster_timer"), ("R:O12",))
def o12(lage: MakroLage):
    m = next((m for m in lage.monster if m.kopfgeld), None)
    if m is None:
        return None
    return Kommando("O12", f"Ihr habt Kopfgeld auf dem {MONSTER_DAT[m.art]}", "das ist euer Weg zurueck (bis 1000 Gold extra)",
                    klasse="objective", wert=2.0)
