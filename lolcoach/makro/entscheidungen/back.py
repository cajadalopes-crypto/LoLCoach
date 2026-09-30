"""B4. Back und Einkauf, Makro-Teil (B1-B9). Back nur mit Grund (Entscheidung zu Stufe 2, Punkt 2)."""
from __future__ import annotations

import tomllib

from .. import rechner, regeln
from ..kommando import Kommando, sek
from ..lage import MakroLage
from ..regeln import WISSEN
from . import entscheidung
from ._hilfe import MONSTER_DAT, MONSTER_DE, grube, monster_nah, name


def back_gruende(lage: MakroLage) -> list[str]:
    """Die Gruende aus wissen/makro/regeln.toml [back_gruende] - ohne einen davon kein Back-Kommando."""
    r = regeln.regel("back_gruende")
    g = []
    if lage.welle().stand == "gecrasht":
        g.append("Welle drin")
    if lage.ich.leben < r["leben_unter"]:
        g.append(f"{int(lage.ich.leben * 100)} % Leben")
    if (lage.spike_fehlt is not None and lage.spike_fehlt <= 0) or lage.gold >= r["spike_gold"].get(lage.ich.rolle, 900):
        g.append(f"{lage.gold} Gold fuer dein naechstes Bauteil")
    lo, hi = r["objective_takt_s"]
    m = monster_nah(lage, hi)
    if m and m.spawn_in >= lo:
        g.append(f"{MONSTER_DE[m.art]} in {sek(m.spawn_in)}")
    lg = lage.lane_gegner
    if lg and lg.backt:
        g.append(f"{name(lg)} backt auch")
    return g


def _kauf_ohne_back(champion: str) -> bool:
    try:
        d = tomllib.loads((WISSEN / "sonderregeln.toml").read_text(encoding="utf-8"))
    except OSError:
        return False
    return bool(d.get(champion, {}).get("kauf_ohne_back"))


@entscheidung("B1", "Wann Back", "D,M", ("welle_eigen", "eigene_items", "kaufplan", "mitspieler_hud"),
              ("D:back", "R:back_gruende"))
def b1(lage: MakroLage):
    if lage.ich.im_brunnen or not lage.ich.lebt or lage.lane_gegner is not None and not lage.lane_gegner.lebt:
        return None
    gruende = back_gruende(lage)
    beste = lage.hirn.beste()
    hirn_back = beste is not None and beste[0] == "Back"
    if not gruende or not (hirn_back or len(gruende) >= 2):
        return None
    return Kommando("B1", "Back jetzt", ", ".join(gruende[:2]))


@entscheidung("B2", "Back im Takt des Objectives", "D", ("monster_timer", "eigene_position", "eigene_items"),
              ("D:ketten", "Re:ankunft_ab_brunnen", "R:O7"))
def b2(lage: MakroLage):
    m = monster_nah(lage, 120)
    if m is None or m.spawn_in < 60 or lage.ich.im_brunnen or not lage.ich.lebt:
        return None
    if lage.gold < 500 and lage.ich.leben >= 0.7:
        return None
    r = regeln.patch("recall")
    zurueck = r["kanal_s"] + r["einkauf_s"] + rechner.ankunft_ab_brunnen(lage.team, grube(m), lage.ich.tempo)
    reserve = m.spawn_in - zurueck
    if reserve < 10:
        return None
    return Kommando("B2", "Back jetzt", f"dann bist du {sek(reserve)} vor dem {MONSTER_DAT[m.art]} voll da",
                    "direkt zur Grube", klasse="objective", wert=2.0)


@entscheidung("B3", "Back verschieben", "D,M", ("scoreboard", "welle_eigen"), ("D:back", "Re:fenster_gegner"))
def b3(lage: MakroLage):
    if not lage.plan.get("back"):
        return None
    lg = lage.lane_gegner
    if lg and not lg.lebt and lg.respawn >= 15:
        return Kommando("B3", "Noch nicht back", f"{name(lg)} ist {sek(lg.respawn)} tot", "erst Welle und Platten, dann Back")
    w = lage.welle()
    if w.kanone_in is not None and w.kanone_in <= 10 and w.stand in ("mitte", "bei_uns"):
        return Kommando("B3", "Noch nicht back", "die Kanone ist gleich da", "erst die Kanone, dann Back")
    return None


@entscheidung("B4", "Back wegen Leben oder Mana", "D", ("eigene_zauber", "gegner_sichtungen", "scoreboard"),
              ("D:gefahr", "R:back_gruende"))
def b4(lage: MakroLage):
    if lage.ich.im_brunnen or lage.ich.leben >= 0.3:
        return None
    lg = lage.lane_gegner
    if not lage.gegner_nah(2000) and not (lg and lg.lebt and lg.gesehen_vor is not None and lg.gesehen_vor <= 5):
        return None
    return Kommando("B4", "Back", f"mit {int(lage.ich.leben * 100)} % Leben und Gegnern in der Naehe ist jeder Moment ein Risiko",
                    klasse="gefahr", wert=4.0)


@entscheidung("B5", "Back zusammen mit dem Lane-Gegner", "M,R", ("gegner_recall", "welle_eigen"), ("R:B5",))
def b5(lage: MakroLage):
    lg = lage.lane_gegner
    if lg is None or not lg.backt or lage.welle().stand == "bei_uns" or lage.ich.im_brunnen:
        return None
    return Kommando("B5", "Du auch, sofort", f"{name(lg)} backt: dann verliert keiner eine Welle")


@entscheidung("B6", "Rueckweg: zu Fuss oder TP", "Re,D", ("eigene_zauber", "monster_timer", "welle_eigen"),
              ("Re:brunnen_lane", "Re:tp_abklingzeit"))
def b6(lage: MakroLage):
    if not lage.ich.im_brunnen or not lage.ich.tp_hat or lage.ich.tp_in != 0:
        return None
    m = monster_nah(lage, 180)
    if m is None:
        return None
    t = rechner.brunnen_lane(lage.lane or "top", lage.team, lage.ich.tempo)
    return Kommando("B6", f"Zu Fuss zurueck ({sek(t)}), halte den TP", f"der {MONSTER_DE[m.art]} kommt in {sek(m.spawn_in)}",
                    klasse="objective", wert=1.0)


@entscheidung("B7", "Kauf-Kette", "D,R", ("eigene_items", "kaufplan"), ("R:B7",))
def b7(lage: MakroLage):
    if not (lage.ich.im_brunnen or not lage.ich.lebt) or lage.gold < 300:
        return None
    r = regeln.regel("B7")
    teile = list(lage.plan.get("kauf") or ["dein naechstes Bauteil"])
    if not lage.kontrollauge_inventar and not lage.kontrollauge_gesetzt and lage.gold >= r["kontrollauge"] + 300:
        teile.append("Kontroll-Auge")
    return Kommando("B7", "Kauf " + " und ".join(teile), f"du hast {lage.gold} Gold", "zurueck in die Lane")


@entscheidung("B8", "Nach Respawn: Kauf und Ziel", "D,Re", ("scoreboard", "monster_timer"), ("D:ziel", "Re:ankunft_ab_brunnen"))
def b8(lage: MakroLage):
    if lage.ich.lebt or lage.ich.respawn > 12:
        return None
    ziel = None
    m = monster_nah(lage, 90)
    if m:
        ziel = f"zum {MONSTER_DAT[m.art]}"
    elif lage.hirn.beste():
        b = lage.hirn.beste()
        ziel = f"nach {b[1]}" if b[1] else ("in die Lane" if b[0] == "Lane" else "zur Gruppe")
    ziel = ziel or "in die Lane"
    return Kommando("B8", f"Du lebst in {sek(lage.ich.respawn)}: Kauf-Kette", f"dann direkt {ziel}")


@entscheidung("B9", "Sonderregeln je Champion", "R", ("eigene_items",), ("R:B9",))
def b9(lage: MakroLage):
    if not _kauf_ohne_back(lage.ich.champion) or lage.gold < 800 or lage.ich.im_brunnen:
        return None
    return Kommando("B9", "Kauf direkt in der Lane", f"{lage.ich.champion} braucht dafuer keinen Back")
