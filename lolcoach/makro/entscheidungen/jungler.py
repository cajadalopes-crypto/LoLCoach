"""B2. Gegner-Jungler, fehlende Gegner, Warnungen (J1-J14)."""
from __future__ import annotations

from ...bewertung import abstand
from .. import rechner, regeln
from ..kommando import Kommando, sek
from ..lage import MakroLage
from . import entscheidung
from ._hilfe import KRABBLER, lane_der_seite, name, seite, unsere_seite


@entscheidung("J1", "Startseite ableiten", "D", ("gegner_sichtungen", "scoreboard", "uhr"), ("D:jungler",))
def j1(lage: MakroLage):
    j = lage.gegner_jungler
    if lage.zeit > 150 or j is None or j.pos is None or j.gesehen_vor is None or j.gesehen_vor > 30:
        return None
    s = seite(j.pos)
    lage.plan["jungler_start"] = s
    return Kommando("J1", f"Er ist {'oben' if s == 'oben' else 'unten'} gesehen worden",
                    f"Start auf der {'oberen' if s == 'oben' else 'unteren'} Seite, erster Gank eher {lane_der_seite(s)}")


@entscheidung("J2", "Gank-Fenster vorwarnen", "D,M", ("uhr", "gegner_sichtungen", "welle_eigen"),
              ("R:S2", "D:jungler"))
def j2(lage: MakroLage):
    g = regeln.patch("gank")
    j = lage.gegner_jungler
    if not (g["fenster_ab_s"] <= lage.zeit <= 420) or j is None or not j.lebt:
        return None
    if j.gesehen_vor is not None and j.gesehen_vor <= 20:
        return None
    if lage.welle().stand not in ("bei_ihnen", "gecrasht") or lage.tief():
        return None
    return Kommando("J2", "Gank-Fenster jetzt: Welle zurueckziehen lassen", "ihr Jungler ist unbekannt und deine Welle steht vorn",
                    "erst wieder nach vorn, wenn er gesehen wird", klasse="gefahr", wert=3.0)


@entscheidung("J3", "Freifenster nutzen", "D,Re", ("gegner_sichtungen", "eigene_position"), ("Re:fenster_jungler",))
def j3(lage: MakroLage):
    j = lage.gegner_jungler
    if j is None or not j.lebt or j.pos is None or j.gesehen_vor is None or j.gesehen_vor > 10 or lage.ich.pos is None:
        return None
    t = rechner.fenster_jungler(j.pos, j.gesehen_vor, lage.ich.pos)
    if t is None or t < 25:
        return None
    return Kommando("J3", f"Er ist {lane_der_seite(seite(j.pos)) or 'weit weg'}: {sek(t)} Ruhe",
                    "so lange braucht er zu dir", "Welle rein, Platte holen")


@entscheidung("J4", "Jungler unbekannt und du weit vorn", "D,M", ("gegner_sichtungen", "eigene_position"),
              ("D:gefahr", "Re:fenster_jungler"))
def j4(lage: MakroLage):
    j = lage.gegner_jungler
    if j is None or not j.lebt or lage.zeit < regeln.patch("gank")["fenster_ab_s"] or not lage.tief():
        return None
    if j.gesehen_vor is not None and j.gesehen_vor <= 30:
        return None
    wie = "nie gesehen" if j.gesehen_vor is None else f"seit {sek(j.gesehen_vor)} weg"
    return Kommando("J4", "Zurueck zur Mitte der Lane", f"ihr Jungler ist {wie} und du stehst tief", klasse="gefahr", wert=4.0)


@entscheidung("J5", "Mehrere fehlen (MIA)", "D,M", ("gegner_sichtungen", "scoreboard"), ("D:gefahr",))
def j5(lage: MakroLage):
    fehlen = [g for g in lage.unbekannt(15) if g.rolle != lage.ich.rolle]
    if len(fehlen) < 2:
        return None
    namen = " und ".join(name(g) for g in fehlen[:2])
    return Kommando("J5", "Zurueck zum Turm", f"{namen} fehlen seit mindestens 15 s", "Bot anpingen",
                    klasse="gefahr", wert=3.5)


@entscheidung("J6", "Lane-Gegner fehlt (Roam oder Back)", "M,D", ("gegner_sichtungen", "welle_eigen"), ("Re:fenster_gegner",))
def j6(lage: MakroLage):
    lg = lage.lane_gegner
    if lg is None or not lg.lebt or lg.gesehen_vor is None or not (6 <= lg.gesehen_vor <= 30):
        return None
    return Kommando("J6", f"{name(lg)} ist weg: Ping Mid", "er roamt oder backt", "Welle crashen und die Platte holen")


@entscheidung("J7", "Gegner-TP genutzt", "M,R", ("tp_sprung", "uhr"), ("R:J7", "Re:tp_abklingzeit"))
def j7(lage: MakroLage):
    e = lage.ereignis("tp", "gegner", 30)
    if e is None:
        return None
    lg = lage.lane_gegner
    cd = rechner.tp_abklingzeit(lage.zeit, lg.level if lg else 9) - e[2]
    return Kommando("J7", f"{name(lg, 'Ihr Top')} hat TP benutzt", f"fuer {sek(cd)} kein Flank von ihm",
                    "jetzt kannst du auf der anderen Seite helfen")


@entscheidung("J8", "Gegner-Flash weg", "M", ("gegner_flash",), ("Re:ankunft",))
def j8(lage: MakroLage):
    g = next((g for g in lage.gegner if g.lebt and g.flash_in is not None and g.flash_in >= 60), None)
    if g is None:
        return None
    return Kommando("J8", f"{name(g)} ohne Flash fuer {sek(g.flash_in)}: Ping", "Kill-Fenster fuer euren Jungler")


@entscheidung("J9", "Globale oder lange Ults der Gegner", "R,M", ("scoreboard", "gegner_sichtungen"), ("R:J9",))
def j9(lage: MakroLage):
    ults = regeln.ults()
    ab = regeln.regel("J9")["level_ab"]
    g = next((g for g in lage.gegner if g.lebt and g.champion in ults and g.level >= ab and g.ult_bereit is not False
              and (g.gesehen_vor is None or g.gesehen_vor > 3)), None)
    if g is None or not lage.tief():
        return None
    art = "globale" if ults[g.champion]["art"] == "global" else "weite"
    return Kommando("J9", "Nicht tief ohne Sicht", f"{name(g)} ist Level {g.level}: seine {art} Ult kann dich erreichen",
                    klasse="gefahr", wert=2.5)


@entscheidung("J10", "Gegner-Spike", "D,M", ("scoreboard", "gegner_items"), ("D:siegchance",))
def j10(lage: MakroLage):
    lg = lage.lane_gegner
    if lg is None or not lg.spike_neu:
        return None
    return Kommando("J10", f"{name(lg)} hat seinen Spike", "Level oder Item eben fertig",
                    "jetzt keinen Seitenkampf allein", klasse="gefahr", wert=2.0)


@entscheidung("J11", "Fruehes Invade", "D,R", ("uhr", "gegner_sichtungen"), ("R:J11",))
def j11(lage: MakroLage):
    r = regeln.regel("J11")
    if lage.zeit > r["bis_s"]:
        return None
    fehlen = lage.unbekannt(0)
    if len(fehlen) < r["fehlen_mind"]:
        return None
    return Kommando("J11", "Bleib am Busch bei eurem Buff", f"{len(fehlen)} von ihnen fehlen: sie koennten invaden",
                    "bis euer Jungler ihn hat", klasse="gefahr", wert=2.0)


@entscheidung("J12", "Konter-Gank", "Re,D", ("mitspieler_positionen", "gegner_sichtungen", "scoreboard"),
              ("Re:ueberzahl",))
def j12(lage: MakroLage):
    uj, gj, lg = lage.unser_jungler, lage.gegner_jungler, lage.lane_gegner
    if not (uj and gj and lg) or lage.ich.pos is None or uj.pos is None or gj.pos is None:
        return None
    if abstand(uj.pos, lage.ich.pos) > 2500 or gj.gesehen_vor is None or gj.gesehen_vor > 5 or abstand(gj.pos, lage.ich.pos) > 3500:
        return None
    wir = [rechner.Einheit(ankunft_s=0), rechner.Einheit(ankunft_s=rechner.ankunft(uj.pos, lage.ich.pos))]
    geg = [rechner.Einheit(ankunft_s=0 if lg.lebt else None, lebt=lg.lebt, respawn=lg.respawn),
           rechner.Einheit(ankunft_s=rechner.ankunft(gj.pos, lage.ich.pos))]
    z = rechner.ueberzahl(8, wir, geg)
    lv = (lage.ich.level + uj.level) - (lg.level + gj.level)
    if z.vorteil >= 0 and lv >= 0:
        return Kommando("J12", f"Bleib: {name(uj)} ist bei dir, ihr Jungler kommt",
                        f"{z.wir} gegen {z.gegner_moeglich}" + (" mit Level-Vorteil" if lv > 0 else ""))
    return Kommando("J12", "Zieh dich zurueck", f"ihr Jungler kommt und ihr seid {z.wir} gegen {z.gegner_moeglich}",
                    klasse="gefahr", wert=3.0)


@entscheidung("J13", "Krabbler", "D,Re", ("uhr", "mitspieler_positionen", "welle_eigen"), ("Re:ankunft",))
def j13(lage: MakroLage):
    s = unsere_seite(lage)
    uj = lage.unser_jungler
    if s is None or not (195 <= lage.zeit <= 240) or uj is None or uj.pos is None:
        return None
    if abstand(uj.pos, KRABBLER[s]) > 3500:
        return None
    t = rechner.ankunft(lage.ich.pos, KRABBLER[s]) if lage.ich.pos else 15
    return Kommando("J13", f"Krabbler {s}: Welle rein, dann hin ({sek(t)})", f"mit dir gewinnt {name(uj)} den Fluss")


@entscheidung("J14", "Dive-Gefahr", "D,Re", ("gegner_sichtungen", "welle_eigen", "eigene_zauber"), ("D:gefahr", "Re:ueberzahl"))
def j14(lage: MakroLage):
    nah = lage.gegner_nah(2500)
    if len(nah) < 2 or lage.ich.leben >= 0.5 or (lage.welle().groesse > 0 and lage.welle().stand != "bei_uns"):
        return None
    return Kommando("J14", "Raus hinter den Turm", f"{len(nah)} kommen und deine Welle ist weg",
                    "nicht ins Tor stellen", klasse="gefahr", wert=5.0)
