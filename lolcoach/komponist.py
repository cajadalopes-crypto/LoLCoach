"""Der Komponist: aus der Lagebewertung eine Anweisung - keine Vorlage, sondern gerechnet.

Carlos 26.09.: "keine vorgefertigten Saetze ... wirklich Sachen addieren, berechnen und eine
korrekte Anweisung geben. Es muss sehr viel spezifischer sein."

Die Regeln sagen, WAS passiert ist (Jungler aufgetaucht, Lane-Gegner weg, Level 6 ...). Der
Komponist entscheidet, was DAS fuer dich JETZT heisst, und nimmt dafuer alles zusammen, was die
Bewertung kennt: dein Leben, dein Flash, wie weit du vorn stehst, wie schnell jeder Gegner bei dir
sein kann, wer tot ist, Level und Items gegen deinen Lane-Gegner, dein Gold, deine Welle, das
naechste Objective. Jeder Satz: die Lage in einem Halbsatz, dann die Handlung mit dem Grund, der
sie entscheidet.

Stil: knapp wie ein Coach im Ohr - jedes Wort kostet Sprechzeit (14 Zeichen/s), und waehrend ein
Satz laeuft, wartet alles andere. Ziel unter 90 Zeichen.

Grundsatz Gefahr vor Chance: kann dich jemand in wenigen Sekunden erreichen, den du nicht siehst,
wird keine Chance angesagt, die dich nach vorn schickt.
"""
from __future__ import annotations

from .bewertung import Bewertung, GegnerLage

GEFAHR_SEKUNDEN = 8.0        # so schnell bei dir = akute Gefahr
RUHE_SEKUNDEN = 20.0         # so lange mindestens weg = ein Fenster, das sich lohnt
JUNGLER_ZAEHLT_AB = 115.0    # Spielzeit: vorher raeumt jeder Jungler seine ersten Camps (Level-3-Gank ab ~2:00)
RECALL_GOLD = 1100
OBJ_NAME = {"drache": "Drache", "baron": "Baron", "herold": "Herold", "larven": "Larven"}


def lebt(schl: str) -> str:
    """'lebt' / 'leben' (die Larven sind drei)."""
    return "leben" if schl == "larven" else "lebt"


def sek(s: float) -> str:
    s = max(1, int(round(s)))
    if s < 90:
        return f"{s} Sekunde" + ("" if s == 1 else "n")
    if s >= 240:     # lange Zeiten: halbe Minuten reichen
        m, r = divmod(s, 60)
        return f"{m} Minuten" if r < 15 else (f"{m} Minuten 30" if r < 45 else f"{m + 1} Minuten")
    m, r = divmod(int(round(s / 5) * 5), 60)    # 1:45 -> "1 Minute 45" (auf 5 s)
    return f"{m} Minute{'n' if m > 1 else ''}" + (f" {r}" if r else "")


def wohin(ort: str) -> str:
    """minimap.ort -> Richtung: 'im oberen Fluss' -> 'Richtung oberer Fluss'."""
    fest = {"im oberen Fluss": "Richtung oberer Fluss", "im unteren Fluss": "Richtung unterer Fluss",
            "in der Flussmitte": "Richtung Flussmitte", "auf der Mid-Lane": "Richtung Mid",
            "in seiner Basis": "Richtung seiner Basis", "in eurer Basis": "Richtung eurer Basis",
            "oben": "nach oben", "unten": "nach unten"}
    if ort in fest:
        return fest[ort]
    if ort.startswith("in seinem "):
        return "in seinen " + ort[len("in seinem "):]
    if ort.startswith("in eurem "):
        return "in euren " + ort[len("in eurem "):]
    return ort


def _namen(liste: list[str]) -> str:
    return liste[0] if len(liste) == 1 else ", ".join(liste[:-1]) + " und " + liste[-1]


def _ist(g: GegnerLage) -> str:
    """'Vi im oberen Fluss', 'Vi oben' -> 'Vi ist oben'."""
    return f"{g.champion} ist {g.ort}" if g.ort in ("oben", "unten") else f"{g.champion} {g.ort}"


def todespreis(b: Bewertung) -> str:
    """Ab ~30 s Todeszeit (Reasoning #27 "Death Value"): was ein Tod JETZT kostet - mit dem
    Objective, das in dieser Zeit kommt. '' wenn es nicht zaehlt."""
    if b.tod_kostet < 30:
        return ""
    satz = f"ein Tod kostet jetzt {sek(b.tod_kostet)}"
    ob = b.objective
    if ob and ob[1] <= b.tod_kostet + 10:
        satz += f", {OBJ_NAME[ob[0]]} " + (lebt(ob[0]) if ob[1] <= 0 else f"in {sek(ob[1])}")
    return satz


def verwundbar(b: Bewertung) -> list[str]:
    """Warum du gerade nicht nach vorn gehoerst - das Wichtigste zuerst, kurz."""
    aus = []
    if b.leben is not None and b.leben < 0.45:
        aus.append(f"{int(b.leben * 100)} Prozent Leben")
    if b.flash is not None and b.flash > 15:
        aus.append("Flash weg")
    if b.unter_gegnerturm:
        aus.append("du stehst unter seinem Turm")
    elif b.tiefe is not None and b.tiefe >= 0.6:
        aus.append("du stehst weit vorn")
    return aus


def gefahr(b: Bewertung, ausser: GegnerLage | None = None) -> list[GegnerLage]:
    """Wer dich in GEFAHR_SEKUNDEN erreichen kann und nicht zu sehen ist (die Sichtbaren siehst
    du selbst) - ohne `ausser`."""
    return [g for g in b.bedrohung(GEFAHR_SEKUNDEN)
            if not g.sichtbar and (ausser is None or g.s.name != ausser.s.name)]


def jungler_offen(b: Bewertung) -> GegnerLage | None:
    """Der gegnerische Jungler, wenn er lebt, lange nicht zu sehen war und es schon zaehlt."""
    j = b.jungler
    if j and not j.s.tot and j.unbekannt and b.zeit >= JUNGLER_ZAEHLT_AB:
        return j
    return None


def _wann(g: GegnerLage) -> str:
    """'in 6 Sekunden da' - oder, wenn er nur deshalb 'sofort' da sein kann, weil er lange nicht
    zu sehen war: 'seit 40 Sekunden weg, kann schon da sein'."""
    weg_zeit = g.abstand * 1.15 / g.tempo if g.abstand is not None else 0.0
    if g.ankunft is not None and g.ankunft < 2:
        return f"seit {sek(g.seit)} weg, kann schon da sein" if weg_zeit > 4 and g.seit else "kann schon da sein"
    return f"kann in {sek(g.ankunft or 0)} da sein"


def _platten(b: Bewertung) -> str:
    """'Platten' - mit Zahl, wenn die Minimap sie zeigt: 'noch 3 Platten'."""
    n = b.platten_gegner
    return "Platten" if n is None else ("letzte Platte" if n == 1 else f"Platten, noch {n}")


def _prio_satz(b: Bewertung, lanes: tuple[str, ...]) -> str:
    """'Mid und Bot haben Prio' / 'Mid hat Prio, Bot nicht' / '' (unbekannt)."""
    bekannt = [(l, b.prio.get(l)) for l in lanes if l in b.prio]
    if not bekannt:
        return ""
    ja = [l for l, v in bekannt if v == "ihr"]
    nein = [l for l, v in bekannt if v == "er"]
    if ja and not nein:
        return f"{_namen(ja)} {'hat' if len(ja) == 1 else 'haben'} Prio"
    if nein and not ja:
        return f"{_namen(nein)} {'hat' if len(nein) == 1 else 'haben'} keine Prio"
    if ja and nein:
        return f"{_namen(ja)} hat Prio, {_namen(nein)} nicht"
    return ""


def _rueckzug(b: Bewertung) -> str:
    if b.leben is not None and b.leben < 0.2:
        return "Hinter den Turm und back"      # mit 5 Prozent "bleib am Turm" hilft nichts (Camille-Partie 13:21)
    if b.unter_eigenem_turm:
        return "Bleib am Turm"
    if b.zum_turm is not None and b.zum_turm >= 6:
        return f"Zurück zum Turm, {sek(b.zum_turm)} Weg"
    return "Zurück zum Turm"


def _objective_erreichbar(b: Bewertung) -> tuple[str, float] | None:
    """Das naechste Objective, wenn du es rechtzeitig schaffst: zu Fuss unter 30 s, oder
    Teleport ist bereit."""
    ob = b.objective
    if not ob or ob[1] > 90:
        return None
    tp = b.zweiter is not None and b.zweiter[0] == "SummonerTeleport" and b.zweiter[1] <= 0
    # 20 s zu Fuss: Top-Aussenturm -> Drachengrube sind ~33 s - ein Toplaner gehoert nicht zu Fuss zum
    # Drachen (Test 26.09., 7:19: "Welle rein, dann Drache" an Riven oben)
    if (b.zum_objective is not None and b.zum_objective <= 20) or tp:
        return ob
    return None


def chance(b: Bewertung, platten: bool) -> str | None:
    """Was du mit einem ruhigen Moment machst - aus Kraefteverhaeltnis, Flash des Gegners, Welle,
    Gold und Objective. None, wenn nichts davon traegt."""
    g = b.lane
    wert, _ = b.kraefte()
    leben_ok = b.leben is None or b.leben >= 0.5
    lebt = g is not None and not g.s.tot
    if lebt and leben_ok and wert >= 1 and g.seit is not None and g.seit < 3:
        return f"Geh auf {g.champion}, {b.vorsprung_satz()}" + (f" - {b.trade}" if b.trade else "")
    if lebt and leben_ok and g.flash and g.flash > 30 and wert > -1:
        return f"Spiel aggressiv, {g.champion} ohne Flash"
    if ob := _objective_erreichbar(b):
        return f"Welle rein, dann {OBJ_NAME[ob[0]]}" + (f" in {sek(ob[1])}" if ob[1] > 0
                                                         else f", {'sie leben' if ob[0] == 'larven' else 'er lebt'}")
    welle = b.welle
    schiebt_ihr = welle is not None and welle[0] >= welle[1] + 2
    if b.gold >= RECALL_GOLD and (schiebt_ihr or not lebt):
        return f"Welle in den Turm und back, {b.gold // 100 * 100} Gold"
    if platten and (schiebt_ihr or not lebt):
        return f"Welle in den Turm, {_platten(b)}"
    if b.gold >= RECALL_GOLD + 300:
        return f"Welle crashen und back, {b.gold // 100 * 100} Gold"
    return None


# --- je Anlass ------------------------------------------------------------------

def jungler_gesehen(b: Bewertung, j: GegnerLage, art: str, platten: bool) -> str:
    """art: 'gefahr' (nah / auf deiner Seite), 'seite' (seine Seite, aber deine Kartenhaelfte), 'sicher'."""
    if art in ("gefahr", "seite"):
        an = j.ankunft
        wann = "direkt bei dir" if an is not None and an < 2 else (f"{sek(an)} zu dir" if an is not None else "")
        gruende = verwundbar(b)
        if an is not None and an < 2 and b.zum_turm is not None and b.zum_turm >= 12:
            # direkt bei dir, der Turm ist weit: der Weg dorthin rettet nicht - raus, mit dem, was du hast
            tun = ("Raus da, Flash bereit halten" if b.flash is not None and b.flash <= 0
                   else "Raus da, dein Flash ist weg - nicht in ihn laufen" if b.flash else "Raus da")
        elif art == "gefahr" or gruende:
            tun = _rueckzug(b) + (f", {gruende[0]}" if gruende else "")
        else:
            tun = "Bleib hinter deiner Welle"
        return f"{_ist(j)}, {wann}. {tun}." if wann else f"{_ist(j)}. {tun}."
    # sicher: er ist weit weg - wie lange hast du, und was machst du damit?
    ruhe = j.ankunft
    satz = _ist(j) + (f", frühestens in {sek(ruhe)} bei dir" if ruhe and ruhe >= 10 else "")
    andere = gefahr(b, ausser=j)
    if andere:
        return satz + f". Aber {_namen([g.champion for g in andere])} fehlt - vorsichtig."
    if tun := chance(b, platten):
        return f"{satz}. {tun}."
    return satz + "."


def lane_fehlt(b: Bewertung, g: GegnerLage, sekunden: int, platten: bool, richtung: str | None) -> str:
    satz = f"{g.champion} seit {sekunden} Sekunden weg" + (f", zuletzt {richtung}" if richtung else "")
    if j := jungler_offen(b):
        return satz + f". {j.champion} auch nicht zu sehen - nicht vor die Welle, ping."
    j = b.jungler
    if j and (j.s.tot or (j.ankunft is not None and not j.unbekannt and j.ankunft >= RUHE_SEKUNDEN)):
        wo = "tot" if j.s.tot else j.ort
        tun = f"Welle in den Turm, {_platten(b)}" if platten else "Welle rein"
        return satz + f". {j.champion} {'ist ' if wo in ('tot', 'oben', 'unten') else ''}{wo}: {tun}, und ping."
    gruende = verwundbar(b)
    return satz + ". Ping" + (f" und bleib hinten, {gruende[0]}." if gruende else ", nicht vor die Welle.")


def anlauf(b: Bewertung, kommen: list[tuple[GegnerLage, str]]) -> str:
    erster, woher = kommen[0]
    an = min((g.ankunft for g, _ in kommen if g.ankunft is not None), default=None)
    wann = f", {sek(an)}" if an is not None and an >= 2 else ""
    if len(kommen) >= 2:
        return f"{_namen([g.champion for g, _ in kommen])} kommen auf dich zu{wann}. {_rueckzug(b)}."
    satz = f"{erster.champion} kommt {woher} auf dich zu{wann}."
    if b.mitspieler_nah:
        n = [s.champion for s in b.mitspieler_nah]
        return satz + f" {_namen(n)} {'ist' if len(n) == 1 else 'sind'} bei dir - zusammen bleiben."
    ist_lane = b.lane is not None and erster.s.name == b.lane.s.name
    wert = b.kraefte()[0] if ist_lane else None
    andere = gefahr(b, ausser=erster)
    if wert is not None and wert >= 1.5 and not andere and (b.leben or 1) >= 0.6:
        return satz + f" Nimm den Kampf, {b.vorsprung_satz()}."
    if wert is not None and wert >= 1.5 and andere:
        return satz + f" Du bist stärker, aber {andere[0].champion} {_wann(andere[0])}: {_rueckzug(b)}."
    gruende = verwundbar(b)
    return satz + f" {_rueckzug(b)}" + (f", {gruende[0]}." if gruende else ".")


def leben(b: Bewertung, prozent: int) -> str:
    satz = f"{prozent} Prozent Leben"
    nah = [g for g in b.bedrohung(12) if not g.s.tot and g.seit is not None and g.seit <= 15]
    if nah:
        g = nah[0]
        return satz + f", {g.champion} {_wann(g)}. Sofort zurück."
    if prozent < 15:
        return satz + ": sofort zurück, jeder Treffer tötet dich."
    j = b.jungler
    niemand = (j is None or j.s.tot or (j.ankunft is not None and not j.unbekannt and j.ankunft >= RUHE_SEKUNDEN))
    offen = [g for g in b.unbekannte() if not g.s.tot]
    if niemand and len(offen) <= 1 and b.welle and b.welle[0] >= b.welle[1] + 2:
        return satz + ", niemand in Reichweite: Welle noch rein, dann back."
    if jo := jungler_offen(b):
        return satz + f", {jo.champion} nicht zu sehen. Zurück."
    return satz + ". Zurück, bevor dich jemand erwischt."


def lane_tot(b: Bewertung, champion: str, sekunden: int, platten: bool) -> str:
    satz = f"{champion} tot, {sekunden} Sekunden"
    andere = gefahr(b)
    frisch = [x for x in andere if x.seit is not None and x.seit <= 15]
    if frisch:   # eben erst nah gesehen: der kommt wirklich
        return satz + f". {frisch[0].champion} {_wann(frisch[0])} - Welle nur bis zum Turm."
    if andere:   # nur Worst Case (lange nicht gesehen): Platten ja, aber mit Blick auf den Fluss
        x = andere[0]
        return (satz + f": Welle rein" + (f", {_platten(b)}" if platten else "")
                + f" - aber {x.champion} seit {sek(x.seit or b.zeit)} nicht gesehen, raus, sobald {x.champion} auftaucht.")
    tun = "Welle in den Turm" + (f", {_platten(b)}" if platten else "")
    if ob := _objective_erreichbar(b):
        tun += f", dann {OBJ_NAME[ob[0]]}"
    elif b.gold >= RECALL_GOLD:
        tun += f", dann back mit {b.gold // 100 * 100} Gold"
    return f"{satz}: {tun}."


def level(b: Bewertung, stufe: int, ich_zuerst: bool, g: GegnerLage) -> str:
    if not ich_zuerst:
        satz = f"{g.champion} ist Level {stufe}, du nicht"
        if b.leben is not None and b.leben < 0.5:
            return satz + f". Mit {int(b.leben * 100)} Prozent Leben zurück, bis du nachziehst."
        return satz + ": nur kurze Trades, bis du nachziehst."
    satz = f"Du bist zuerst Level {stufe}"
    if g.s.tot:
        return satz + "."
    if b.leben is not None and b.leben < 0.5:
        return satz + f", aber nur {int(b.leben * 100)} Prozent Leben. Erst zurück."
    if j := jungler_offen(b):
        weg = f"seit {sek(j.seit)} weg" if j.seit else "nicht gesehen"
        return satz + f", aber {j.champion} {weg}: traden, All-in nur mit Sicht."
    gruende = []
    if g.flash and g.flash > 20:
        gruende.append(f"{g.champion} ohne Flash")
    j = b.jungler
    if j and b.zeit >= JUNGLER_ZAEHLT_AB and (j.s.tot or (j.ankunft or 0) >= RUHE_SEKUNDEN):
        gruende.append(f"{j.champion} {'tot' if j.s.tot else j.ort}")
    tun = "All-in jetzt" if stufe == 6 else "Trade jetzt"
    return satz + f". {tun}" + (f", {_namen(gruende)}" if gruende else "") + (f" - {b.trade}." if b.trade else ".")


def recall(b: Bewertung, grund: str) -> str:
    """grund: 'welle' (deine Welle laeuft in seinen Turm), 'gold' oder 'viel' (mehr als ein Item)."""
    if grund == "welle":
        satz = "Deine Welle läuft in seinen Turm: jetzt back"
    elif grund == "viel":
        satz = f"{b.gold // 100 * 100} Gold ungenutzt, mehr als ein Item: Welle rein und sofort back"
    else:
        kauf = b.kauf.satz() if b.kauf is not None and b.kauf.kaufen else ""
        satz = f"{b.gold // 100 * 100} Gold" + (f" {kauf}" if kauf else "") + ": nächste Welle in den Turm, dann back"
    if (andere := gefahr(b)) and grund != "welle":
        return satz + f", aber {andere[0].champion} {_wann(andere[0])}."
    ob = b.objective
    if ob and 45 <= ob[1] <= 150:
        return satz + f", {OBJ_NAME[ob[0]]} in {sek(ob[1])}."
    if b.leben is not None and b.leben < 0.5:
        return satz + f", {int(b.leben * 100)} Prozent Leben."
    return satz + "."


def zauber_neu(b: Bewertung, g: GegnerLage, zauber: str, dauer: float, quelle: str) -> str:
    """Ein Gegner hat Flash (oder Ult, Zuenden ...) benutzt - und was das fuer dich heisst."""
    ult = zauber == "Ult"
    satz = (f"{g.champion} Ult weg, {sek(dauer)}" if ult
            else f"{g.champion} hat {zauber} benutzt, {sek(dauer)} weg" + (" - Minimap" if quelle == "Minimap" else ""))
    ist_lane = b.lane is not None and g.s.name == b.lane.s.name
    if ist_lane and not g.s.tot and (zauber == "Flash" or ult):
        wert, _ = b.kraefte()
        v = b.vorsprung_satz()
        if jo := jungler_offen(b):
            return satz + f". Fenster, aber {jo.champion} fehlt."
        if wert >= 0 and (b.leben is None or b.leben >= 0.5):
            return satz + ". Dein Fenster" + (f", {v}" if v else "") + (f" - {b.trade}." if b.trade else ".")
        if wert <= -1:
            return satz + (f", aber {v}: nur traden." if v else ": nur traden.")
    return satz + "."


def kein_flash_nah(b: Bewertung, g: GegnerLage, rest: float) -> str:
    satz = f"{g.champion} ohne Flash, noch {sek(rest)}"
    if andere := gefahr(b, ausser=g):   # zuerst: wer sonst dazukommen kann (Camille-Partie 15:37/15:39)
        return satz + f", aber {andere[0].champion} {_wann(andere[0])} - nicht reinlaufen."
    if b.lane and g.s.name == b.lane.s.name:
        wert, _ = b.kraefte()
        v = b.vorsprung_satz()
        if wert >= 0.5:
            return satz + (f", {v}: rein, wenn er in Reichweite kommt." if v else ": rein, wenn er in Reichweite kommt.")
        if wert <= -1:
            return satz + (f", aber {v}: nur traden." if v else ": nur traden.")
    return satz + ". Nutz das Fenster."


def tief(b: Bewertung, namen: str, sind: str, sekunden: int, sie: str) -> str:
    weg = "noch nie gesehen" if sekunden >= b.zeit - 5 else f"seit {sek(sekunden)} weg"
    satz = f"Du stehst tief, {namen} {weg}."
    gruende = [x for x in verwundbar(b) if "weit vorn" not in x and "Turm" not in x]
    if preis := todespreis(b):
        gruende.append(preis)
    ziel = (f" Zurück, {sek(b.zum_turm)} bis zum Turm" if b.zum_turm and b.zum_turm >= 6
            else f" Zurück, bis du {sie} siehst")
    return satz + ziel + (f", {gruende[0]}." if gruende else ".")


def vorwarnung(b: Bewertung, schl: str, rolle: str, seele: bool, meine_seite: bool, tp_moeglich: bool) -> str:
    """Objective in einer Minute - und was DU in dieser Minute machst: Weg dorthin, Teleport (HUD),
    Welle, Leben, Gold. `meine_seite`: das Objective liegt auf der Kartenseite deiner Rolle.
    `tp_moeglich`: Teleport genommen oder aus der Top-Quest (die HUD-Abklingzeit, wenn bekannt, zaehlt)."""
    name = OBJ_NAME[schl]
    satz = f"{name} in einer Minute" + (" - er entscheidet die Seele" if seele else "")
    if rolle == "JUNGLE":
        seite = "Bot" if schl == "drache" else "Top"
        return satz + ". " + (_prio_satz(b, ("Mid", seite)) or f"Prio von Mid und {seite} prüfen") + ", Sicht an die Grube."
    tp = b.zweiter if b.zweiter is not None and b.zweiter[0] == "SummonerTeleport" else None
    if tp is None and tp_moeglich:
        tp = ("SummonerTeleport", 0.0)     # Abklingzeit unbekannt (kein HUD): als bereit rechnen
    zu_fuss = b.zum_objective
    hin = meine_seite or (zu_fuss is not None and zu_fuss <= 25) or (tp is not None and tp[1] <= 50)
    teile = []
    if b.leben is not None and b.leben < 0.5 or b.gold >= 1300:
        grund = f"{b.gold // 100 * 100} Gold" if b.gold >= 1300 else f"{int(b.leben * 100)} Prozent Leben"
        teile.append(f"jetzt back, {grund}" + (", dann hin" if hin else ", dann Druck auf deiner Seite"))
    elif meine_seite or (zu_fuss is not None and zu_fuss <= 25):
        teile.append("Welle rein, dann hin" + (f", {sek(zu_fuss)} Weg" if zu_fuss else ""))
    elif tp is not None:
        teile.append("Welle rein, dann Teleport" if tp[1] <= 50 else f"Teleport erst in {sek(tp[1])}, zu spät: Druck auf der anderen Seite")
    else:
        teile.append("zu weit für dich: Welle rein, Platten, Druck auf der anderen Seite")
    return satz + ". " + teile[0][0].upper() + teile[0][1:] + "."


def jungler_tot(b: Bewertung, sekunden: int, objective: str | None, nah: bool, platten: bool) -> str:
    """Der gegnerische Jungler ist tot. `objective`: Schluessel eines machbaren Objectives (oder None),
    `nah`: es liegt auf deiner Seite."""
    j = b.jungler.champion if b.jungler else "Der Jungler"
    satz = f"{j} tot, {sekunden} Sekunden"
    if objective:
        name = OBJ_NAME[objective]
        if nah:
            weg = f", du bist {sek(b.zum_objective)} weg" if b.zum_objective and b.zum_objective >= 8 else ""
            return f"{satz}: {name} jetzt, er kann nicht kontern{weg}."
        tun = chance(b, platten)
        return f"{satz}: ping {name}." + (f" Du: {tun}." if tun else "")
    tun = chance(b, platten)
    return f"{satz}: kein Gank möglich." + (f" {tun}." if tun else " Spiel nach vorn.")


def zahlen(b: Bewertung, tote: list[str], sekunden: int, objective: str | None, wir: int, die: int) -> str:
    """Zwei oder mehr Gegner tot: was jetzt - mit Namen, Zahl und ob DU es rechtzeitig schaffst."""
    satz = f"{_namen(tote)} tot, {sekunden} Sekunden, {wir} gegen {die}"
    if objective:
        name = OBJ_NAME[objective]
        if b.zum_objective is not None and b.zum_objective > sekunden:
            return f"{satz}: {name} jetzt - du schaffst es nicht hin, drück deine Lane."
        return f"{satz}: {name} jetzt."
    return f"{satz}: Türme drücken, solange sie fehlen."


def zahlen_nachteil(b: Bewertung, tote: list[str], sekunden: int) -> str:
    satz = f"{_namen(tote)} tot, {sekunden} Sekunden - ihr seid zu {5 - len(tote)}"
    if b.unter_eigenem_turm:
        return satz + ". Bleib am Turm, kein Kampf."
    return satz + f". Kein Kampf, Objective abgeben. {_rueckzug(b)}."


def obj_dazu(b: Bewertung, nah: bool, tp_moeglich: bool) -> str:
    """Dein Team faengt ein Objective an - was du tust."""
    if nah:
        return "Du bist nah genug: hin" + (f", {sek(b.zum_objective)}." if b.zum_objective and b.zum_objective >= 5 else ".")
    tp = b.zweiter if b.zweiter is not None and b.zweiter[0] == "SummonerTeleport" else None
    if tp is None and tp_moeglich:
        tp = ("SummonerTeleport", 0.0)
    if tp is not None and tp[1] <= 0:
        return "Teleport bereit: TP hinter die Grube."
    if b.zum_objective is not None and b.zum_objective <= 25:
        return f"{sek(b.zum_objective)} Weg: hin."
    return "Zu weit für dich: Welle rein, Druck auf deiner Seite."


def lane_recall(b: Bewertung, champion: str, platten: bool) -> str:
    """Der Lane-Gegner recallt (stand still, dann weg): was du mit den ~15 s machst."""
    satz = f"{champion} recallt"
    if frisch := [x for x in gefahr(b, ausser=b.lane) if x.seit is not None and x.seit <= 15]:
        return satz + f", aber {frisch[0].champion} {_wann(frisch[0])} - Welle nur bis zum Turm."
    if platten:
        tun = f"Welle in seinen Turm, {_platten(b)}"
    else:
        tun = "Welle reinschieben, dann hast du Zeit für deinen Recall"
    if b.gold >= RECALL_GOLD:
        tun += f", danach selbst back mit {b.gold // 100 * 100} Gold"
    return f"{satz}: {tun}."


def gegner_am_objective(namen: str, grube: str, name: str, kl) -> str:
    """Die Gegner machen ein Objective: hin (contesten) oder tauschen - aus der Kampflage."""
    wir, die, offen = kl.zahlen()
    art, _ = kl.urteil()
    satz = f"{namen} an der {grube}, sie machen {name}"
    zahl = f"{wir} gegen {die}" + (f" und {offen} unbekannt" if offen else "")
    if art == "nehmen":
        return satz + f". Ihr seid in 15 Sekunden {zahl}: hin und streitig machen."
    if art == "abgeben":
        return satz + f". Nur {zahl}: nicht reinlaufen, auf der anderen Seite tauschen."
    return satz + f". {zahl}: nur mit allen und Ults hin, sonst tauschen."


def jungler_spaet(b: Bewertung, j: GegnerLage, seite: str) -> str:
    """Nach der Lane-Phase: der gegnerische Jungler zeigt sich auf `seite` ("oben"/"unten") - was die
    andere Seite jetzt hergibt: das Objective dort (mit Kampflage), sonst die Seitenwelle."""
    ruhe = j.ankunft
    satz = _ist(j) + (f", frühestens in {sek(ruhe)} bei dir" if ruhe and ruhe >= 10 else "")
    andere = "unten" if seite == "oben" else "oben"
    ob = b.objective
    ob_seite = None if not ob else ("unten" if ob[0] == "drache" else "oben")
    if ob and ob_seite == andere and ob[1] <= 30:
        name = OBJ_NAME[ob[0]]
        if b.kampf is not None:
            art, _ = b.kampf.urteil()
            if art == "nehmen":
                return f"{satz}. {name} jetzt, er kann nicht rechtzeitig da sein."
            if art == "abgeben":
                return f"{satz}. {name} trotzdem nicht: zu wenige von euch in der Nähe."
        return f"{satz}. Chance auf {name} - nur, wenn dein Team in der Nähe ist."
    if andere := gefahr(b, ausser=j):
        x = andere[0]
        return f"{satz}. Aber {x.champion} {_wann(x)} - nicht vorlaufen."
    if ruhe and ruhe >= 20:
        return f"{satz}. Seitenwelle drücken, Turm - du hast mindestens {sek(ruhe)}."
    return satz + "."


def spike(b: Bewertung, items: str) -> str:
    """Eigenes Item fertig (Rueckfall, wenn Claude nicht rechtzeitig formuliert): was es gegen deinen
    Lane-Gegner jetzt heisst - neuer Vorsprung, dazu der Trade-Hinweis aus der Spielakte."""
    satz = f"{items} fertig"
    g = b.lane
    if g is None or g.s.tot:
        return satz + " - dein Powerspike, such den nächsten Kampf."
    wert, _ = b.kraefte()
    v = b.vorsprung_satz()
    if wert >= 1:
        return satz + (f", {v}" if v else "") + f": zurück in die Lane und auf {g.champion} spielen" \
            + (f" - {b.trade}." if b.trade else ".")
    if wert <= -1:
        return satz + (f", aber {v}" if v else "") + ": noch kein All-in, erst mit dem nächsten Item."
    return satz + (f", {v}" if v else "") + f": jetzt gewinnst du kurze Trades gegen {g.champion}."
