"""B9. Mitte und Spaetphase: Seiten, Gruppe, Split, Schluss (M1-M10)."""
from __future__ import annotations

from .. import rechner, regeln
from ..kommando import Kommando, sek
from ..lage import LANE_MITTE, MakroLage
from . import entscheidung
from ._hilfe import INHIB, LANE_DE, MONSTER_DE, NEXUS, monster_nah, name


@entscheidung("M1", "Lane-Zuordnung nach Plattenende oder Tuermen", "D", ("uhr", "ereignisse"), ("D:rotation",))
def m1(lage: MakroLage):
    if not (840 <= lage.zeit <= 900) or lage.lane is None:
        return None
    b = lage.hirn.beste()
    if b and b[0] == "Rotation" and b[1]:
        seite = {"oben": "Top-Seite", "mid": "Mid", "unten": "Bot-Seite"}.get(b[1], b[1])
        return Kommando("M1", f"Plattenende: du nimmst {seite}", "so verteilen sich High-Elo-Teams hier am haeufigsten")
    return Kommando("M1", f"Plattenende: du bleibst {LANE_DE[lage.lane]}-Seite", "die Seitenwelle dort gehoert dir, der ADC geht Mid")


@entscheidung("M2", "Split: ob, welche Seite, wie tief", "D", ("gegner_sichtungen", "eigene_zauber", "scoreboard"),
              ("D:wert", "D:gefahr", "R:split"))
def m2(lage: MakroLage):
    if lage.zeit < 1200:
        return None
    split = lage.hirn.option("Split")
    beste = lage.hirn.beste()
    if split is None or beste is None or split[2] < beste[2] - 0.5 or len(lage.unbekannt()) >= 3:
        return None
    tp = ", TP bereit fuer den Baron" if lage.ich.tp_hat and lage.ich.tp_in == 0 else ""
    return Kommando("M2", "Drück die Seitenwelle bis zu ihrem Turm, nicht weiter", f"sie muessen dir jemanden schicken{tp}",
                    "sofort weg, wenn drei fehlen")


@entscheidung("M3", "Split verlassen", "D,Re", ("monster_timer", "eigene_position", "kampf"), ("Re:ankunft",))
def m3(lage: MakroLage):
    if not lage.plan.get("split"):
        return None
    m = monster_nah(lage, 45, ("baron", "drache", "elder"))
    if m is None and (lage.kampf is None or lage.kampf.in_s > 10):
        return None
    was = f"{MONSTER_DE[m.art]} in {sek(m.spawn_in)}" if m else "dein Team kaempft gleich"
    return Kommando("M3", "Split abbrechen, lauf jetzt", was, klasse="objective", wert=3.0)


@entscheidung("M4", "Gruppe Mid", "D", ("mitspieler_positionen", "welle_eigen"), ("D:wert",))
def m4(lage: MakroLage):
    if lage.zeit < 1200:
        return None
    mid = lage.mitspieler_bei(LANE_MITTE["mid"], 3000)
    if len(mid) < 3:
        return None
    split, gruppe = lage.hirn.wert("Split"), lage.hirn.wert("Gruppe")
    if split is not None and gruppe is not None and split > gruppe:
        return Kommando("M4", f"Zu {len(mid)} Mid, du bleibst Seite", "das zieht zwei von ihnen zu dir")
    return Kommando("M4", "Geh Mid zur Gruppe", f"{len(mid)} von euch stehen dort, allein bist du das leichtere Ziel")


@entscheidung("M5", "1-3-1 oder 1-4", "D,R", ("scoreboard", "eigene_wards"), ("R:M5",))
def m5(lage: MakroLage):
    if lage.zeit < 1500 or not lage.plan.get("aufstellung"):
        return None
    lg = lage.lane_gegner
    stark = lg is not None and lage.ich.level >= lg.level + 1
    sicht = any("Flanke" in w.ort for w in lage.wards)
    if stark and sicht:
        return Kommando("M5", "1-3-1, du Top", "du bist staerker als dein Gegner und hast Sicht an der Flanke")
    return Kommando("M5", "1-4: alle zusammen", "fuer 1-3-1 fehlt dir " + ("die Staerke" if not stark else "die Sicht an der Flanke"))


@entscheidung("M6", "Seitenwellen vor Baron oder Drache", "D,M", ("wellen_alle", "monster_timer"), ("D:ketten",))
def m6(lage: MakroLage):
    m = monster_nah(lage, 60, ("baron", "drache", "elder"))
    if m is None or lage.zeit < 1200:
        return None
    offen = [l for l in ("top", "bot") if lage.wellen.get(l) and lage.wellen[l].stand in ("bei_uns", "mitte")]
    if not offen:
        return None
    return Kommando("M6", f"{' und '.join(LANE_DE[l] for l in offen)}-Welle druecken", f"dann {MONSTER_DE[m.art]}: sie muessen die Wellen holen",
                    klasse="objective", wert=2.0)


@entscheidung("M7", "Inhibitor-Druck", "D,M", ("ereignisse",), ("D:siegchance",))
def m7(lage: MakroLage):
    if not lage.inhib_offen_gegner:
        return None
    lane = lage.inhib_offen_gegner[0]
    return Kommando("M7", f"Ihr {LANE_DE.get(lane, lane)}-Inhibitor ist weg: die andere Seite halten",
                    "die Super-Vasallen machen dort Druck fuer euch")


@entscheidung("M8", "Spiel beenden", "D,Re", ("ereignisse", "scoreboard", "eigene_position"),
              ("Re:schluss_moeglich", "Re:ankunft", "D:wert", "R:baron_nach_ace"))
def m8(lage: MakroLage):
    tote = lage.tote(lage.gegner)
    if len(tote) < 3 or lage.ich.pos is None:
        return None
    respawns = [g.respawn for g in tote]
    ziel, ort = ("nexus", NEXUS[lage.gegnerteam]) if lage.inhib_offen_gegner else \
        ("inhib", INHIB[(lage.gegnerteam, "mid")])
    weg = rechner.ankunft(lage.ich.pos, ort, lage.ich.tempo)
    ok, reserve = rechner.schluss_moeglich(weg, ziel, respawns)
    was = "Nexus" if ziel == "nexus" else "Mid-Inhibitor"
    if ok:
        return Kommando("M8", f"{len(tote)} tot: {was} jetzt", f"ihr seid {sek(reserve)} vor dem ersten Respawn fertig",
                        klasse="objective", wert=10.0)
    b = lage.mon("baron")
    if b and b.spawn_in == 0:
        return Kommando("M8", "Baron statt Basis", f"bis zum {was} reicht die Zeit nicht (erster Respawn in {sek(min(respawns))})",
                        klasse="objective", wert=5.0)
    return None


@entscheidung("M9", "Basis verteidigen", "D,M", ("ereignisse",), ("D:gefahr",))
def m9(lage: MakroLage):
    baron_gegner = lage.ereignis("baron", "gegner", 180)
    if not baron_gegner and not lage.inhib_offen_wir:
        return None
    warum = "sie haben den Baron" if baron_gegner else "euer Inhibitor ist offen"
    return Kommando("M9", "Nicht raus: Wellen im Tor clearen", warum, "auf ihren Fehler warten", klasse="gefahr", wert=3.0)


@entscheidung("M10", "Todes-Kosten beachten", "D", ("uhr", "monster_timer", "ereignisse"), ("Re:todes_kosten",))
def m10(lage: MakroLage):
    if lage.zeit < 1500:
        return None
    tz = rechner.todes_kosten(lage.ich.level, lage.zeit)
    m = monster_nah(lage, 60, ("baron", "elder"))
    if tz < 40 or (m is None and not lage.inhib_offen_wir):
        return None
    was = MONSTER_DE[m.art] if m else "euren Inhibitor"
    return Kommando("M10", "Sicher spielen", f"ein Tod jetzt kostet {sek(tz)} und {was}", klasse="gefahr", wert=2.0)
