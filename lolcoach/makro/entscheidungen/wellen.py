"""B3. Wellen (W1-W14)."""
from __future__ import annotations

from .. import rechner, regeln
from ..kommando import Kommando, sek
from ..lage import MakroLage
from . import entscheidung
from ._hilfe import MONSTER_DE, LANE_DE, monster_nah, name


@entscheidung("W1", "Freeze oder Push", "M,R,D", ("welle_eigen", "gegner_sichtungen", "mitspieler_positionen"),
              ("R:W1", "Re:ankunft"))
def w1(lage: MakroLage):
    w = lage.welle()
    if w.stand == "bei_uns" and w.groesse <= 0 and not lage.plan.get("back"):
        uj = lage.unser_jungler
        warum = "er muss nach vorn, um zu farmen"
        if uj and uj.pos and lage.ich.pos and rechner.ankunft(uj.pos, lage.ich.pos) <= 25:
            warum += f", {name(uj)} kommt in {sek(rechner.ankunft(uj.pos, lage.ich.pos))}"
        return Kommando("W1", "Freeze an deinem Turm: nur letzte Treffer", warum)
    if lage.plan.get("back") or lage.plan.get("roam") or lage.plan.get("objective"):
        if w.stand in ("mitte", "bei_uns"):
            return Kommando("W1", "Push jetzt", "du willst weg und die Welle soll in ihren Turm laufen", "dann gehen")
    return None


@entscheidung("W2", "Langsam aufbauen, dann crashen vor dem Back", "M,Re", ("welle_eigen",), ("R:W2", "Re:wellentakt"))
def w2(lage: MakroLage):
    w = lage.welle()
    if not lage.plan.get("back") or w.stand != "mitte" or w.kanone_in is None or w.kanone_in < 25:
        return None
    n = regeln.regel("W2")["aufbau_wellen"]
    return Kommando("W2", f"{n} Wellen aufbauen, mit der Kanone crashen", "dann verlierst du beim Back nichts",
                    "Back")


@entscheidung("W3", "Crash -> Back", "M,D", ("welle_eigen", "eigene_items", "kaufplan"), ("D:back", "R:back_gruende"))
def w3(lage: MakroLage):
    if lage.welle().stand != "gecrasht":
        return None
    r = regeln.regel("back_gruende")
    gold_ok = lage.spike_fehlt is not None and lage.spike_fehlt <= 0 or \
        lage.gold >= r["spike_gold"].get(lage.ich.rolle, 900)
    if not (gold_ok or lage.ich.leben < r["leben_unter"]):
        return None
    warum = f"{lage.gold} Gold" if gold_ok else f"{int(lage.ich.leben * 100)} % Leben"
    return Kommando("W3", "Welle ist drin: jetzt Back", warum, "Kauf-Kette")


@entscheidung("W4", "Crash -> Fenster nutzen", "M,Re", ("welle_eigen",), ("Re:fenster_welle",))
def w4(lage: MakroLage):
    if lage.welle().stand != "gecrasht" or w3(lage) is not None:
        return None
    t = rechner.fenster_welle("gecrasht")
    return Kommando("W4", f"Deine Welle prallt in {sek(t)} zurueck", f"{sek(t)} fuer Ward oder Mid")


@entscheidung("W5", "Warten auf die zurueckprallende Welle", "M,Re", ("welle_eigen",), ("Re:fenster_welle",))
def w5(lage: MakroLage):
    w = lage.welle()
    if not lage.plan.get("tp") or w.stand != "bei_uns" or w.groesse >= 0:
        return None
    return Kommando("W5", "Warte 10 s am Turm", "die Welle kommt zu dir", "erst dann TP")


@entscheidung("W6", "Welle vor dem Objective", "D,M", ("welle_eigen", "monster_timer"), ("D:ketten", "Re:rueckwaerts"))
def w6(lage: MakroLage):
    m = monster_nah(lage, 90)
    if m is None or m.spawn_in < 60 or lage.welle().stand in ("gecrasht", "bei_ihnen"):
        return None
    return Kommando("W6", f"{MONSTER_DE[m.art]} in {sek(m.spawn_in)}: Welle jetzt rein", "damit du frei bist",
                    klasse="objective", wert=2.0)


@entscheidung("W7", "Welle vor TP oder Roam crashen", "M,Re", ("welle_eigen",), ("Re:crash_dauer", "Re:wellenkosten"))
def w7(lage: MakroLage):
    w = lage.welle()
    if not (lage.plan.get("tp") or lage.plan.get("roam")) or w.stand not in ("mitte", "bei_uns") or w.groesse < 0:
        return None
    gold, _ = rechner.wellenkosten(30, lage.zeit, w.stand)
    wohin = "TP" if lage.plan.get("tp") else "Roam"
    return Kommando("W7", f"Erst crashen ({sek(rechner.crash_dauer())}), dann {wohin}",
                    f"sonst frisst ihr Turm deine Welle (etwa {gold:.0f} Gold)")


@entscheidung("W8", "Welle retten oder Objective", "Re,D", ("welle_eigen", "monster_timer"),
              ("Re:wellenkosten", "Re:punkte_je_1000_gold", "D:wert"))
def w8(lage: MakroLage):
    m = monster_nah(lage, 30)
    if m is None or lage.welle().stand != "bei_uns":
        return None
    gold, _ = rechner.wellenkosten(60, lage.zeit, "bei_uns")
    punkte_welle = gold / 1000 * rechner.punkte_je_1000_gold(lage.zeit)
    wert = lage.hirn.wert("Objective", MONSTER_DE[m.art])
    wert = wert if wert is not None else 2.0
    if wert <= punkte_welle:
        return Kommando("W8", "Rette die Welle", f"{gold:.0f} Gold sind hier mehr wert als der {MONSTER_DE[m.art]}")
    return Kommando("W8", "Lass die Welle", f"der {MONSTER_DE[m.art]} ist mehr wert: {gold:.0f} Gold gegen {wert:.1f} Punkte Siegchance",
                    klasse="objective", wert=wert)


@entscheidung("W9", "Nicht zu tief druecken", "D,M", ("welle_eigen", "gegner_sichtungen"), ("D:gefahr",))
def w9(lage: MakroLage):
    j = lage.gegner_jungler
    if lage.welle().stand != "bei_ihnen" or lage.plan.get("back") or j is None or not j.lebt:
        return None
    if j.gesehen_vor is not None and j.gesehen_vor <= 20:
        return None
    return Kommando("W9", "Stopp vor ihrem Turm", "ihr Jungler ist unbekannt und du willst nicht backen",
                    klasse="gefahr", wert=2.5)


@entscheidung("W10", "Nach Kill oder Tod des Lane-Gegners", "D,M", ("scoreboard", "welle_eigen", "platten"),
              ("Re:fenster_gegner", "D:umwandlung"))
def w10(lage: MakroLage):
    lg = lage.lane_gegner
    if lg is None or lg.lebt or lg.respawn < 15:
        return None
    t = rechner.fenster_gegner(respawn=lg.respawn, weg_zur_lane=rechner.brunnen_lane(lage.lane or "top", lage.gegnerteam))
    platten = lage.gegner_platten.get(lage.lane or "", 0)
    was = f"{min(2, platten)} Platten" if platten and lage.zeit < 840 else "den Turm anschlagen"
    return Kommando("W10", f"Er ist {sek(lg.respawn)} tot: Welle crashen, {was}", f"du hast {sek(t)}, bis er zurueck ist",
                    "Back")


@entscheidung("W11", "Seitenwelle holen (Mitte und Spaet)", "D,M", ("wellen_alle", "gegner_sichtungen"), ("D:gefahr",))
def w11(lage: MakroLage):
    if lage.zeit < 840:
        return None
    for lane in ("bot", "top"):
        if lane == lage.lane:
            continue
        w = lage.wellen.get(lane)
        if w and w.stand == "bei_uns":
            n = len(lage.unbekannt())
            grenze = "nur bis zur Flussmitte" if n >= 3 else "bis vor ihren Turm"
            return Kommando("W11", f"{LANE_DE[lane]}-Welle holen, {grenze}", f"{n} sind unbekannt" if n else "sie laeuft auf euren Turm")
    return None


@entscheidung("W12", "Grosse Welle stapeln fuer Turm oder Dive", "M,Re", ("welle_eigen", "platten", "mitspieler_positionen"),
              ("Re:wellentakt",))
def w12(lage: MakroLage):
    lg, uj = lage.lane_gegner, lage.unser_jungler
    if lg is None or uj is None or not (not lg.lebt or lg.backt) or lage.welle().stand not in ("mitte", "bei_ihnen"):
        return None
    if lage.gegner_platten.get(lage.lane or "", 5) > 2:
        return None
    return Kommando("W12", "Zwei Wellen stapeln", f"ihr Turm ist schwach und {name(lg)} ist weg", f"mit {name(uj)} auf den Turm")


@entscheidung("W13", "Welle aufgeben", "Re,D", ("monster_timer", "kampf"), ("Re:wellenkosten", "D:wert"))
def w13(lage: MakroLage):
    m = monster_nah(lage, 20)
    k = lage.kampf
    if m is None and (k is None or k.in_s > 20):
        return None
    if lage.welle().stand not in ("mitte", "bei_ihnen"):
        return None
    was = f"der {MONSTER_DE[m.art]}" if m else "der Kampf"
    t = m.spawn_in if m else k.in_s
    return Kommando("W13", "Lass die Welle und geh", f"{was} ist in {sek(t)}", klasse="objective", wert=2.0)


@entscheidung("W14", "Wellen der anderen Lanes fuer Prio", "M", ("wellen_alle", "monster_timer"), ("D:ketten",))
def w14(lage: MakroLage):
    m = monster_nah(lage, 60, ("drache", "elder"))
    w = lage.wellen.get("bot")
    if m is None or w is None or w.stand != "bei_uns" or lage.lane == "bot":
        return None
    return Kommando("W14", "Kein Drache jetzt", "die Bot-Welle laeuft auf euren Turm: euer Bot kann nicht weg",
                    "erst wenn Bot die Welle hat", klasse="objective", wert=1.0)
