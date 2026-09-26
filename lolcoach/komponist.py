"""Der Komponist: aus der Lagebewertung eine Anweisung - keine Vorlage, sondern gerechnet.

Carlos 26.09.: "keine vorgefertigten Saetze ... wirklich Sachen addieren, berechnen und eine
korrekte Anweisung geben. Es muss sehr viel spezifischer sein." Und nach der Live-Partie am Abend:
"Der Coach muss in der Lage sein, zusammenhaengende Saetze zu formulieren!"

Die Regeln sagen, WAS passiert ist (Jungler aufgetaucht, Lane-Gegner weg, Level 6 ...). Der
Komponist entscheidet, was DAS fuer dich JETZT heisst, und nimmt dafuer alles zusammen, was die
Bewertung kennt: dein Leben, dein Flash, wie weit du vorn stehst, wie schnell jeder Gegner bei dir
sein kann, wer tot ist, Level und Items gegen deinen Lane-Gegner, dein Gold, deine Welle, das
naechste Objective. Das Kampf-Urteil gegen den Lane-Gegner rechnet denker.py.

Stil: ganze Saetze, wie ein Coach sie spricht - erst was ist, dann was du tust und warum
("Vi ist im oberen Fluss, in 12 Sekunden bei dir. Du stehst unter seinem Turm - geh
zurueck zu deinem, das sind 14 Sekunden."). Keine Telegramm-Fetzen ("Zurueck zum Turm, 14 s Weg").

Grundsatz Gefahr vor Chance: kann dich jemand in wenigen Sekunden erreichen, den du nicht siehst,
wird keine Chance angesagt, die dich nach vorn schickt.
"""
from __future__ import annotations

from .bewertung import GEGNER_TEMPO_RESERVE, Bewertung, GegnerLage
from .zustand import gegenteam

GEFAHR_SEKUNDEN = 8.0        # so schnell bei dir = akute Gefahr
RUHE_SEKUNDEN = 20.0         # so lange mindestens weg = ein Fenster, das sich lohnt
JUNGLER_ZAEHLT_AB = 115.0    # Spielzeit: vorher raeumt jeder Jungler seine ersten Camps (Level-3-Gank ab ~2:00)
RECALL_GOLD = 1100
OBJ_NAME = {"drache": "Drache", "baron": "Baron", "herold": "Herold", "larven": "Larven"}
OBJ_NOM = {"drache": "der Drache", "baron": "Baron Nashor", "herold": "der Herold", "larven": "die Larven"}
OBJ_AKK = {"drache": "den Drachen", "baron": "Baron Nashor", "herold": "den Herold", "larven": "die Larven"}


def lebt(schl: str) -> str:
    """'lebt' / 'leben' (die Larven sind drei)."""
    return "leben" if schl == "larven" else "lebt"


def kommt(schl: str) -> str:
    return "kommen" if schl == "larven" else "kommt"


def sek(s: float) -> str:
    s = max(1, int(round(s)))
    if s < 90:
        return f"{s} Sekunde" + ("" if s == 1 else "n")
    if s >= 240:     # lange Zeiten: halbe Minuten reichen
        m, r = divmod(s, 60)
        return f"{m} Minuten" if r < 15 else (f"{m} Minuten 30" if r < 45 else f"{m + 1} Minuten")
    m, r = divmod(int(round(s / 5) * 5), 60)    # 1:45 -> "1 Minute 45" (auf 5 s)
    return f"{m} Minute{'n' if m > 1 else ''}" + (f" {r}" if r else "")


def uhr_gesprochen(t: float) -> str:
    """Spielzeit fuer die Stimme: 6:45 -> '6 45' (die Stimme liest sonst 'sechs Uhr fuenfundvierzig')."""
    return f"{int(t // 60)} {int(t % 60):02d}"


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
    """'Vi ist oben', 'Vi ist im oberen Fluss'."""
    return f"{g.champion} ist {g.ort}" if g.ort else g.champion


ORTE = ("oben", "unten", "in der Flussmitte", "im oberen Fluss", "im unteren Fluss", "auf der Mid-Lane",
        "in eurem oberen Jungle", "in eurem unteren Jungle", "in seinem oberen Jungle", "in seinem unteren Jungle")


def anfaenge(p) -> list[str]:
    """Satzanfaenge, die in dieser Partie oft kommen - genau so, wie stimme.teilsaetze sie abtrennt. Zu Spielbeginn
    vorgewaermt, klingen sie ohne die ~0,45 s des Sprachdienstes. Zuerst der gegnerische Jungler (die haeufigsten
    Saetze: 21 % der Sprechzeit)."""
    if not p.ich:
        return []
    feind = gegenteam(p.mein_team)
    aus = ["Geh rein,", "das ist ein Kill:", "Noch nicht rein,", "Trade hart,", "Du stehst tief,", "Recall-Fenster:"]
    if (j := p.jungler(feind)) is not None:
        aus += [f"{j.champion} ist {o}," for o in ORTE]
    lane = {"TOP": "Top", "MIDDLE": "Mid", "BOTTOM": "Bot", "UTILITY": "Bot"}.get(p.ich.rolle)
    for turm in ([f"{lane}-Tier-1", f"{lane}-Tier-2"] if lane else []) + (["Mid-Tier-1"] if lane != "Mid" else []):
        aus += [f"Geh jetzt zurück zu deinem {turm}-Turm,", f"Geh erst zurück zu deinem {turm}-Turm und recall dort:"]
    aus += [f"{s.champion} hat Flash benutzt," for s in p.gegner()]
    if (g := p.gegenueber()) is not None:
        aus += [f"{g.champion} ist {o}," for o in ORTE[:6]]
    return aus


def _gross(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def todespreis(b: Bewertung, mit_objective: bool = True) -> str:
    """Was ein Tod JETZT kostet (Reasoning #27 "Death Value"): Todeszeit ab 30 s, dein Kopfgeld, und das
    Objective, das in dieser Zeit kommt. '' wenn nichts davon zaehlt."""
    from .bewertung import kopfgeld
    teile = []
    if b.tod_kostet >= 30:
        teile.append(sek(b.tod_kostet))
    k = kopfgeld(b.ich, b.partie) if b.shutdown_ich else 0
    if k >= 100:
        teile.append(f"{k} Gold Kopfgeld")
    elif b.shutdown_ich:
        teile.append("deinen Shutdown")
    if not teile:
        return ""
    satz = "ein Tod kostet dich " + " und ".join(teile)
    ob = b.objective
    if mit_objective and b.tod_kostet >= 30 and ob and 0 < ob[1] <= b.tod_kostet + 10:
        satz += f", und {OBJ_NOM[ob[0]]} {kommt(ob[0])} in {sek(ob[1])}"
    return satz


def tod_turm(b: Bewertung | None) -> str:
    """Tod am Turm, gerechnet aus der letzten Sekunde davor statt des Standardsatzes (Nachlauf 21:21, 6:10: "Vom
    Turm erwischt. Unter seinen Turm nur mit genug Leben ..."): dein Leben, sein Schuss, wie viele du ausgehalten
    haettest, und wie viel Leben ein Dive braucht (drei Schuesse samt Aufwaermen). '' ohne Lage."""
    from . import rechnung, wissen
    from .bewertung import TURM_REICHWEITE, abstand, stehende_tuerme
    from .zustand import gegenteam
    if b is None or b.pos is None or b.partie is None or b.leben_abs is None:
        return ""
    feind = gegenteam(b.partie.mein_team)
    naechst = min(((abstand(b.pos, v), k) for k, v in stehende_tuerme(b.partie).items() if k[0] == feind), default=None)
    if naechst is None or naechst[0] > TURM_REICHWEITE + 600:
        return ""
    stufe = naechst[1][2]
    schuss = rechnung.turm_schaden(stufe, b.zeit)
    n = rechnung.turm_schuesse(b.leben_abs, stufe, b.zeit)
    t = wissen.lade("mechanik")["tuerme"]
    drei = sum(schuss * (1 + min(t["aufwaermen_max"], t["aufwaermen_je_schuss"] * i)) for i in range(3))
    satz = (f"Vom Turm erwischt: du hattest noch {b.leben_abs // 10 * 10} Leben, sein Turm trifft mit etwa "
            f"{int(schuss) // 10 * 10}" + ((" - das war nur ein Schuss" if n <= 1 else f" - das waren nur {n} Schüsse")
                                           if n <= 3 else ""))
    if b.welle is not None and b.welle[0] == 0:
        satz += ", und deine Welle war nicht da"
    return satz + f". Unter seinen Turm erst mit etwa {int(drei) // 100 * 100} Leben, und nur, wenn deine Vasallen vorn sind."


def tod_gank(b: Bewertung | None, champion: str) -> str:
    """Tod durch den gegnerischen Jungler, gerechnet: wie lange er ungesehen war, wo du standest, dein Flash."""
    j = b.jungler if b is not None else None
    teile = []
    if j is not None and j.seit and j.seit >= 15:
        teile.append(f"{champion} war {sek(j.seit)} nicht zu sehen")
    if b is not None and b.unter_gegnerturm:
        teile.append("du standst unter seinem Turm")
    elif b is not None and b.tiefe is not None and b.tiefe >= 0.6:
        teile.append("du standst weit vorn")
    if b is not None and b.flash is not None and b.flash > 0:
        teile.append("dein Flash war weg")
    satz = f"Gank von {champion}" + (": " + _namen(teile) if teile else "")
    if j is not None and j.seit is not None and j.seit < 5:
        return satz + f". {champion} war zu sehen - läuft {champion} auf dich zu, geh sofort zurück."
    return satz + ". Fehlt der Jungler länger als 20 Sekunden, bleib hinter deiner Welle."


def tod_ueberzahl(b: Bewertung | None, namen: list[str]) -> str:
    """Gegen mehrere gestorben: wer, und wer davon vorher nicht zu sehen war ("Gestorben gegen 2" war der alte Satz)."""
    if len(namen) < 2:
        return ""
    ungesehen = []
    if b is not None:
        for g in b.gegner:
            if g.champion in namen and not g.sichtbar and g.seit and g.seit >= 8:
                ungesehen.append(f"{g.champion} war {sek(g.seit)} nicht zu sehen")
    satz = f"Gestorben gegen {_namen(namen)}"
    if ungesehen:
        return satz + ": " + _namen(ungesehen[:2]) + ". Fehlen Gegner so lange, rechne damit, dass sie zu dir kommen."
    return satz + f", {'beide' if len(namen) == 2 else 'alle'} waren zu sehen - gegen mehrere nur mit Hilfe kämpfen."


def tod_solo(b: Bewertung | None, champion: str) -> str:
    """Solo verloren: was die Denkkette in der Sekunde davor gegen dich zaehlte (die zwei staerksten Faktoren).
    '' ohne Urteil oder ohne Gegen-Faktor - dann bleibt der Standardsatz."""
    from .denker import urteil
    if b is None or b.lane is None or b.lane.champion != champion:
        return ""
    u = urteil(b)
    # dein Leben kurz vor dem Tod ist immer niedrig - das ist die Folge, nicht der Grund
    gegen = sorted((x for x in u.faktoren if x.wert <= -0.8 and x.art != "leben"), key=lambda x: x.wert)[:2] if u else []
    if not gegen:
        return ""
    return f"Solo gegen {champion} verloren. In der Sekunde davor: " + _namen([x.satz for x in gegen]) + "."


def verwundbar(b: Bewertung) -> list[str]:
    """Warum du gerade nicht nach vorn gehoerst - das Wichtigste zuerst, als Satzteil."""
    aus = []
    if b.leben is not None and b.leben < 0.45:
        aus.append(f"du hast nur {int(b.leben * 100)} Prozent Leben")
    if b.flash is not None and b.flash > 15:
        aus.append("dein Flash ist weg")
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
    """Nach dem Namen: 'kann in 6 Sekunden da sein' - oder, wenn er nur deshalb 'sofort' da sein kann, weil er
    lange nicht zu sehen war: 'ist seit 40 Sekunden weg und kann schon da sein'."""
    weg_zeit = g.abstand / (g.tempo * GEGNER_TEMPO_RESERVE) if g.abstand is not None else 0.0
    if g.ankunft is not None and g.ankunft < 2:
        return (f"ist seit {sek(g.seit)} weg und kann schon da sein" if weg_zeit > 4 and g.seit
                else "kann schon da sein")
    return f"kann in {sek(g.ankunft or 0)} da sein"


def _platten(b: Bewertung) -> str:
    """'die Platten' - mit Zahl, wenn die Minimap sie zeigt: 'die Platten, es stehen noch 3'."""
    n = b.platten_gegner
    return "die Platten" if n is None else ("die letzte Platte" if n == 1 else f"die Platten, es stehen noch {n}")


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
    """Die Handlung als Satz: 'Geh zurück zu deinem Turm, das sind 14 Sekunden'."""
    turm = b.turm_name      # "deinem Top-Tier-1-Turm" (Carlos: "Was ist denn mein Tower?")
    if b.leben is not None and b.leben < 0.2:
        return f"Geh hinter {turm} und dann back"   # mit 5 Prozent "bleib am Turm" hilft nichts (13:21)
    if b.unter_eigenem_turm:
        return f"Bleib an {turm}"
    if b.zum_turm is not None and b.zum_turm >= 6:
        return f"Geh zurück zu {turm}, das sind {sek(b.zum_turm)}"
    return f"Geh zurück zu {turm}"


def _grund_und_rueckzug(b: Bewertung, gruende: list[str]) -> str:
    """'Du stehst unter seinem Turm - geh zurück zu deinem Turm, das sind 14 Sekunden.'"""
    r = _rueckzug(b)
    if gruende:
        return f"{_gross(gruende[0])} - {r[:1].lower() + r[1:]}."
    return r + "."


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


def back_eben(b: Bewertung) -> bool:
    """'Geh back' ist in der letzten Minute schon gesagt worden (Nachlauf 19:45, 12:52-14:12: fuenfmal "geh back, du
    hast 4400 Gold", angehaengt an Jungler-, Drachen- und Objective-Saetze - Carlos blieb trotzdem)."""
    box = getattr(b, "back_box", None)
    return box is not None and b.zeit - box[0] < 60


def chance(b: Bewertung, platten: bool) -> str | None:
    """Was du mit einem ruhigen Moment machst - aus Kampf-Urteil (denker.py), Flash des Gegners, Welle,
    Gold und Objective, als ganzer Satz (ohne Schlusspunkt). None, wenn nichts davon traegt."""
    g = b.lane
    wert, _ = b.kraefte()
    leben_ok = b.leben is None or b.leben >= 0.5
    lebt = g is not None and not g.s.tot
    # nur, wenn er nah ist: Live 21:21, 15:11 "Also geh rein - das ist ein Kill" - Carlos: "Wo soll ich reingehen?
    # Auf welcher Lane?"
    if lebt and leben_ok and g.seit is not None and g.seit < 3 and g.abstand is not None and g.abstand <= 1800:
        from . import denker
        u = denker.urteil(b)
        box = getattr(b, "fenster_box", None)
        if u is not None and u.art in ("kill", "kill_schnell", "trade", "turm"):
            if box is None or b.zeit - box[0] >= 60:     # sonst eben erst mit allen Gruenden gesagt
                if box is not None:
                    box[0] = b.zeit
                # der Jungler-Satz davor sagt schon, wo er ist
                return denker.fenster_satz(b, u, ohne={"jungler"}, danach=False).rstrip(".")
    # einmal je Flash-Abklingzeit, und nicht direkt nach einem Kampf-Urteil, das "kein Flash" schon sagt (Nachlauf
    # 19:45: 5:18, 9:41 und 10:12 "Heimerdinger hat kein Flash - spiel aggressiv", dazwischen die Fenster-Saetze)
    fbox, box = getattr(b, "flash_box", None), getattr(b, "fenster_box", None)
    if (lebt and leben_ok and g.flash and g.flash > 30 and wert > -1
            and (fbox is None or b.zeit - fbox[0] >= 150) and (box is None or b.zeit - box[0] >= 30)):
        if fbox is not None:
            fbox[0] = b.zeit
        return f"{g.champion} hat kein Flash - spiel aggressiv"
    if ob := _objective_erreichbar(b):
        return (f"Schieb die Welle rein und geh dann {ZUM[ob[0]]}"
                + (f", {'sie kommen' if ob[0] == 'larven' else 'er kommt'} in {sek(ob[1])}" if ob[1] > 0
                   else f", {'sie leben' if ob[0] == 'larven' else 'er lebt'}"))
    welle = b.welle
    schiebt_ihr = welle is not None and welle[0] >= welle[1] + 2
    if b.gold >= RECALL_GOLD and (schiebt_ihr or not lebt) and not back_eben(b):
        return f"Schieb die Welle in den Turm und geh back, du hast {b.gold // 100 * 100} Gold"
    if b.gold >= RECALL_GOLD and back_eben(b):
        # "geh back" steht noch (er hat das Gold noch): nicht dagegen "hol dir die Platten" (Nachlauf 194524, 14:02)
        return None
    if platten and (schiebt_ihr or not lebt):
        return f"Schieb die Welle in den Turm und hol dir {_platten(b)}"
    if b.gold >= RECALL_GOLD + 300 and not back_eben(b):
        return f"Lass die Welle crashen und geh back, du hast {b.gold // 100 * 100} Gold"
    return None


# --- je Anlass ------------------------------------------------------------------

KLAR_STAERKER = 2.0      # Kampfkraft-Verhaeltnis: er kann dich nicht toeten
STAERKER = 1.3


def _ankunft_satz(g: GegnerLage) -> str:
    """'Vi ist im oberen Fluss, in 12 Sekunden bei dir' / '..., direkt bei dir'."""
    an = g.ankunft
    if an is not None and an < 2:
        return f"{_ist(g)}, direkt bei dir"
    if an is not None:
        return f"{_ist(g)}, in {sek(an)} bei dir"      # kurz: "Vi ist im oberen Fluss, in 12 Sekunden bei dir"
    return _ist(g)


def jungler_gesehen(b: Bewertung, j: GegnerLage, art: str, platten: bool) -> str:
    """art: 'gefahr' (nah / auf deiner Seite), 'seite' (seine Seite, aber deine Kartenhaelfte), 'sicher'."""
    if art in ("gefahr", "seite"):
        an = j.ankunft
        # erst der Kampf: wer kommt mit (alle, die rechtzeitig da sein koennen - auch die sichtbaren, etwa
        # dein Lane-Gegner), und wer ist staerker? (Live 26.09., 7:13: Vi allein 2,3-fach schwaecher, mit
        # Heimerdinger und Kassadin zusammen staerker - der Satz muss beides sagen)
        gruppe = [j] + [x for x in b.bedrohung(GEFAHR_SEKUNDEN) if x.s.name != j.s.name]
        r = b.kraft_gegen(gruppe)
        r_allein = b.kraft_gegen([j])
        vorn = _ankunft_satz(j)
        # Kurz: Ort und Zeit, die Handlung, der EINE Grund (Nachlauf 21:21 nach allen Umbauten: der Coach sprach
        # 88 % der Spielzeit, Jungler-Saetze im Schnitt 162 Zeichen - "Allein wuerdest du ... Aber ... zusammen ...
        # Geh zurueck zu deinem Turm, das sind 22 Sekunden" waren 260)
        grund = b.ueberlegen_satz(gruppe).split(", ")[0]
        if r >= KLAR_STAERKER and (b.leben is None or b.leben >= 0.4):
            if an is not None and an > 10:     # "in 31 Sekunden bei dir - nimm den Kampf an" klang nach jetzt
                return f"{vorn}. Kommt {j.champion}, nimm den Kampf an" + (f": {grund}." if grund else ".")
            return f"{vorn} - nimm den Kampf an" + (f", {grund}." if grund else ".")
        if r >= STAERKER and (b.leben is None or b.leben >= 0.5):
            # "Bleib an deiner Welle", waehrend du in seinem Jungle stehst (Nachlauf 230520, 17:50)
            bleib = "Bleib an deiner Welle" if "Jungle" not in (b.ort or "") else "Halte deine Stellung"
            return f"{vorn}. {bleib}" + (f", {grund}" if grund else ", du bist stärker") + " - nur nicht zu tief."
        if len(gruppe) > 1 and r_allein >= STAERKER and (b.leben is None or b.leben >= 0.5):
            andere = [x.champion for x in gruppe[1:]]
            return f"{vorn}. {_rueckzug(b)} - mit {_namen(andere)} zusammen ist {j.champion} zu stark."
        gruende = verwundbar(b)
        if an is not None and an < 2 and b.zum_turm is not None and b.zum_turm >= 12:
            # direkt bei dir, der Turm ist weit: der Weg dorthin rettet nicht - raus, mit dem, was du hast
            grund = f"{_gross(gruende[0])}. " if gruende else ""
            tun = grund + ("Raus da, und halt dein Flash bereit." if b.flash is not None and b.flash <= 0
                           else f"Raus da - dein Flash ist weg, also lauf nicht in {j.champion} hinein." if b.flash
                           else "Raus da.")
        elif art == "gefahr" or gruende:
            tun = _grund_und_rueckzug(b, gruende)
        else:
            tun = "Bleib hinter deiner Welle."
        return f"{vorn}. {tun}"
    # sicher: er ist weit weg - wie lange hast du, und was machst du damit?
    ruhe = j.ankunft
    satz = _ist(j) + (f", frühestens in {sek(ruhe)} bei dir" if ruhe and ruhe >= 10 else "")
    andere = gefahr(b, ausser=j)
    if andere:
        n = [g.champion for g in andere]
        return satz + f". Aber {_namen(n)} {'fehlt' if len(n) == 1 else 'fehlen'} auf der Karte, also bleib vorsichtig."
    if tun := chance(b, platten):
        return f"{satz}. {tun}."
    return satz + "."


def lane_fehlt(b: Bewertung, g: GegnerLage, sekunden: int, platten: bool, richtung: str | None) -> str:
    """Der Lane-Gegner ist verschwunden: wohin er kann (Reasoning #12/#13: "Wo kann er sein, welche Wege,
    wie schnell?") - bis Mid, wenn er Richtung Fluss lief - und was du mit der Zeit machst."""
    n = g.champion
    satz = f"{n} fehlt seit {sekunden} Sekunden in deiner Lane" + (f", zuletzt {richtung}" if richtung else "")
    if g.pos is not None and b.ich.rolle in ("TOP", "BOTTOM", "UTILITY") and richtung and "Fluss" in richtung:
        from .bewertung import abstand, einheiten
        bis_mid = abstand(g.pos, einheiten(0.5, 0.5)) / (g.tempo * GEGNER_TEMPO_RESERVE) - sekunden
        if bis_mid >= 3:
            satz += f" - bis Mid braucht {n} von dort noch etwa {sek(bis_mid)}"
        else:
            satz += f" - {n} kann schon Mid sein"
    if j := jungler_offen(b):
        return satz + f", {j.champion} auch. Bleib hinter deiner Welle und ping es."
    j = b.jungler
    if j and (j.s.tot or (j.ankunft is not None and not j.unbekannt and j.ankunft >= RUHE_SEKUNDEN)):
        wo = "tot" if j.s.tot else j.ort
        tun = f"schieb die Welle in seinen Turm und hol dir {_platten(b)}" if platten else "schieb die Welle rein"
        return satz + f". {j.champion} ist {wo}: {tun} und ping es."
    gruende = verwundbar(b)
    if gruende:
        return satz + f". {_gross(gruende[0])} - bleib hinten und ping es."
    return satz + ". Bleib hinter deiner Welle und ping es."


def anlauf(b: Bewertung, kommen: list[tuple[GegnerLage, str]]) -> str:
    erster, woher = kommen[0]
    an = min((g.ankunft for g, _ in kommen if g.ankunft is not None), default=None)
    viele = len(kommen) > 1
    wann = (f" und {'sind' if viele else 'ist'} in {sek(an)} da") if an is not None and an >= 2 else ""
    # der Kampf entscheidet: die Kommenden plus wer sonst rechtzeitig da sein kann
    gruppe = [g for g, _ in kommen] + [x for x in gefahr(b) if x.s.name not in {g.s.name for g, _ in kommen}]
    r = b.kraft_gegen(gruppe)
    wer = _namen([g.champion for g, _ in kommen])
    kommt_satz = f"{wer} {'kommen' if viele else 'kommt'}{'' if viele else ' ' + woher} auf dich zu{wann}"
    if r >= KLAR_STAERKER and (b.leben is None or b.leben >= 0.4):
        return f"{kommt_satz}. Nimm den Kampf an: {b.ueberlegen_satz(gruppe).split(', ')[0]}."
    if r >= STAERKER and (b.leben is None or b.leben >= 0.5) and not viele:
        return f"{kommt_satz}. Halte deine Stellung: {b.ueberlegen_satz(gruppe).split(', ')[0]}."
    if viele:
        return f"{kommt_satz}. {_rueckzug(b)}."
    satz = kommt_satz + "."
    if b.mitspieler_nah:
        n = [s.champion for s in b.mitspieler_nah]
        return satz + f" {_namen(n)} {'ist' if len(n) == 1 else 'sind'} bei dir, also bleibt zusammen."
    ist_lane = b.lane is not None and erster.s.name == b.lane.s.name
    wert = b.kraefte()[0] if ist_lane else None
    andere = gefahr(b, ausser=erster)
    if wert is not None and wert >= 1.5 and not andere and (b.leben or 1) >= 0.6:
        return satz + f" Nimm den Kampf an, {b.vorsprung_satz()}."
    if wert is not None and wert >= 1.5 and andere:
        return satz + f" Du bist stärker, aber {andere[0].champion} {_wann(andere[0])} - geh lieber zurück."
    return satz + " " + _grund_und_rueckzug(b, verwundbar(b))


def leben(b: Bewertung, prozent: int) -> str:
    satz = f"Du hast nur noch {prozent} Prozent Leben"
    nah = [g for g in b.bedrohung(12) if not g.s.tot and g.seit is not None and g.seit <= 15]
    if nah:
        g = nah[0]
        return satz + f", und {g.champion} {_wann(g)}. {_rueckzug(b)}."
    if prozent < 15:
        return satz + " - geh sofort zurück, jeder Treffer kann dich töten."
    j = b.jungler
    niemand = (j is None or j.s.tot or (j.ankunft is not None and not j.unbekannt and j.ankunft >= RUHE_SEKUNDEN))
    offen = [g for g in b.unbekannte() if not g.s.tot]
    if niemand and len(offen) <= 1 and b.welle and b.welle[0] >= b.welle[1] + 2:
        return satz + ", aber niemand ist in Reichweite: schieb die Welle noch rein und geh dann back."
    if jo := jungler_offen(b):
        return satz + f", und {jo.champion} ist nicht zu sehen. Geh zurück."
    return satz + f". {_rueckzug(b)}, bevor dich jemand erwischt."


def lane_tot(b: Bewertung, champion: str, sekunden: int, platten: bool) -> str:
    satz = f"{champion} ist {sekunden} Sekunden tot"
    andere = gefahr(b)
    frisch = [x for x in andere if x.seit is not None and x.seit <= 15]
    if frisch:   # eben erst nah gesehen: der kommt wirklich
        return satz + f", aber {frisch[0].champion} {_wann(frisch[0])}. Schieb die Welle nur bis zum Turm."
    if andere:   # nur Worst Case (lange nicht gesehen): Platten ja, aber mit Blick auf den Fluss
        x = andere[0]
        return (satz + ". Schieb die Welle rein" + (f" und hol dir {_platten(b)}" if platten else "")
                + f" - aber {x.champion} ist seit {sek(x.seit or b.zeit)} nicht zu sehen, also raus, sobald "
                  f"{x.champion} auftaucht.")
    tun = "Schieb die Welle in seinen Turm" + (f" und hol dir {_platten(b)}" if platten else "")
    if ob := _objective_erreichbar(b):
        tun += f", dann geh {ZUM[ob[0]]}"
    elif b.gold >= RECALL_GOLD and not back_eben(b):
        tun += f", dann geh back, du hast {b.gold // 100 * 100} Gold"
    return f"{satz}. {tun}."


def level(b: Bewertung, stufe: int, ich_zuerst: bool, g: GegnerLage) -> str:
    """Rueckfall ohne Kampf-Urteil (denker.py)."""
    if not ich_zuerst:
        satz = f"{g.champion} ist Level {stufe}, du noch nicht"
        if b.leben is not None and b.leben < 0.5:
            return satz + f", und du hast nur {int(b.leben * 100)} Prozent Leben. Geh zurück, bis du nachziehst."
        return satz + ". Mach nur kurze Trades, bis du nachziehst."
    satz = f"Du bist zuerst Level {stufe}"
    if g.s.tot:
        return satz + "."
    if b.leben is not None and b.leben < 0.5:
        return satz + f", aber du hast nur {int(b.leben * 100)} Prozent Leben. Geh erst zurück."
    if j := jungler_offen(b):
        weg = f"seit {sek(j.seit)} weg" if j.seit else "nicht zu sehen"
        return satz + f", aber {j.champion} ist {weg}. Trade, aber ein All-in nur mit Sicht."
    tun = "Das ist dein Fenster für einen All-in" if stufe == 6 else "Das ist dein Fenster für einen Trade"
    return satz + f". {tun}" + (f" - {b.trade}." if b.trade else ".")


def recall(b: Bewertung, grund: str) -> str:
    """grund: 'welle' (deine Welle laeuft in seinen Turm), 'gold' oder 'viel' (mehr als ein Item)."""
    gold = b.gold // 100 * 100
    kauf = b.kauf.satz() if b.kauf is not None and b.kauf.kaufen else ""
    if grund == "welle":
        satz = "Recall-Fenster: deine Welle läuft in seinen Turm" + (f", und {gold} Gold {kauf}" if kauf else "")
    elif grund == "viel":
        satz = f"{gold} Gold in der Tasche, mehr als ein ganzes Item - schieb die Welle rein und geh sofort back"
    else:
        satz = f"Du hast {gold} Gold" + (f", das {kauf}" if kauf else "") + \
               ". Schieb die nächste Welle in den Turm und geh dann back"
    if (andere := gefahr(b)) and grund != "welle":
        # die Handlung zuerst: "geh erst zurueck" stand nach 130 Zeichen (Nachlauf 194524, 8:52)
        return (f"Geh erst zurück zu {b.turm_name} und recall dort: {andere[0].champion} {_wann(andere[0])}. "
                f"Du hast {gold} Gold" + (f", das {kauf}." if kauf else "."))
    ob = b.objective
    if ob and 45 <= ob[1] <= 150:
        return satz + f". {_gross(OBJ_NOM[ob[0]])} {kommt(ob[0])} in {sek(ob[1])}, bis dahin bist du zurück."
    if b.leben is not None and b.leben < 0.5:
        return satz + f", du hast auch nur {int(b.leben * 100)} Prozent Leben."
    return satz + "."


def zauber_neu(b: Bewertung, g: GegnerLage, zauber: str, dauer: float, quelle: str) -> str:
    """Ein Gegner hat Flash (oder Ult, Zuenden ...) benutzt - und was das fuer dich heisst."""
    ult = zauber == "Ult"
    bis = uhr_gesprochen(b.zeit + dauer)
    if ult:
        satz = f"{g.champion} hat die Ult benutzt, sie ist bis {bis} weg"
    else:
        satz = f"{g.champion} hat {zauber} benutzt, bis {bis}"
    ist_lane = b.lane is not None and g.s.name == b.lane.s.name
    if zauber == "Teleport":
        wo = f" und ist jetzt {g.ort}" if g.ort else ""
        if ist_lane:
            return (f"{g.champion} hat Teleport benutzt{wo}. Zurück kommt {g.champion} damit nicht - deine Lane "
                    f"gehört dir: schieb die Welle rein und geh auf den Turm.")
        return f"{g.champion} hat Teleport benutzt{wo}. Dort ist jetzt einer mehr."
    if ist_lane and not g.s.tot and (zauber == "Flash" or ult):
        wert, _ = b.kraefte()
        v = b.vorsprung_satz()
        if jo := jungler_offen(b):
            return satz + f". Das ist ein Fenster, aber {jo.champion} ist nicht zu sehen."
        if wert >= 0 and (b.leben is None or b.leben >= 0.5):
            return satz + ". Das ist dein Fenster" + (f", {v}" if v else "") + (f" - {b.trade}." if b.trade else ".")
        if wert <= -1:
            return satz + (f". Aber {v}, also nur kurze Trades." if v else ". Trotzdem nur kurze Trades.")
    return satz + "."


def kein_flash_nah(b: Bewertung, g: GegnerLage, rest: float) -> str:
    satz = f"{g.champion} hat kein Flash, noch {sek(rest)}"
    if andere := gefahr(b, ausser=g):   # zuerst: wer sonst dazukommen kann (Camille-Partie 15:37/15:39)
        return satz + f". Aber {andere[0].champion} {_wann(andere[0])} - lauf nicht rein."
    if b.lane and g.s.name == b.lane.s.name:
        wert, _ = b.kraefte()
        v = b.vorsprung_satz()
        if wert >= 0.5:
            return satz + (f", und {v}: geh rein, sobald {g.champion} in Reichweite ist." if v
                           else f": geh rein, sobald {g.champion} in Reichweite ist.")
        if wert <= -1:
            return satz + (f". Aber {v}, also nur kurze Trades." if v else ". Trotzdem nur kurze Trades.")
        return satz + " - nutz das Fenster."
    # nicht der Lane-Gegner (Nachlauf 194524, 10:50: "Vi hat kein Flash - nutz das Fenster" - welches?): der Kampf
    # gegen genau ihn, gerechnet
    r = b.kraft_gegen([g])
    grund = b.ueberlegen_satz([g]).split(", ")[0]
    if r >= STAERKER and (b.leben is None or b.leben >= 0.5):
        return satz + f" - kommt {g.champion}, nimm den Kampf an, entkommen kann {g.champion} nicht" \
            + (f": {grund}." if grund else ".")
    if r <= 1 / STAERKER:
        return satz + ", ist aber stärker als du - auch ohne Flash kein Kampf."
    return satz + f" - {g.champion} kann dir ohne Flash schlechter folgen."


def tief(b: Bewertung, namen: str, sind: str, sekunden: int, sie: str, fehlende: list | None = None) -> str:
    """'' = keine Warnung: du bist den Fehlenden zusammen klar ueberlegen (Live-Partie 26.09.: 'Du stehst tief,
    zurueck' an Riven Level 12 gegen Vi Level 6)."""
    weg = "noch nie zu sehen gewesen" if sekunden >= b.zeit - 5 else f"seit {sek(sekunden)} nicht zu sehen"
    satz = f"Du stehst tief, und {namen} {sind} {weg}."
    if fehlende:
        gl = [g for g in b.gegner if g.s.name in {s.name for s in fehlende}]
        r = b.kraft_gegen(gl, mit_verbuendeten=False) if gl else 0.0
        if gl and r >= KLAR_STAERKER and (b.leben is None or b.leben >= 0.5):
            return ""
        if gl and r >= STAERKER and (b.leben is None or b.leben >= 0.5):
            # Live 21:21, 14:30 - Carlos: "ich bin Level 12, Tryndamere 7, Sona 8 - ich nehme die beiden
            # auseinander". Stimmt: dann ist der Grund fuer Vorsicht das Kopfgeld, nicht der Kampf.
            preis = todespreis(b, mit_objective=False)
            wer = f"{namen} schlägt dich nicht" if len(gl) == 1 else "Auch zusammen schlagen sie dich nicht"
            return satz + f" {wer} - geh nur nicht tiefer" + (f", {preis}." if preis else ".")
    gruende = [x for x in verwundbar(b) if "weit vorn" not in x and "Turm" not in x]
    preis = todespreis(b, mit_objective=False)
    if preis:
        return satz + f" Geh zurück - {preis}."
    if b.zum_turm and b.zum_turm >= 6:
        ziel = f" Geh zurück, bis zu {b.turm_name} sind es {sek(b.zum_turm)}"
    else:
        ziel = f" Geh zurück, bis du {sie} siehst"
    return satz + ziel + (f" - {gruende[0]}." if gruende else ".")


def vorwarnung(b: Bewertung, schl: str, rolle: str, seele: bool, meine_seite: bool, tp_moeglich: bool) -> str:
    """Objective in einer Minute - und was DU in dieser Minute machst: Weg dorthin, Teleport (HUD),
    Welle, Leben, Gold. `meine_seite`: das Objective liegt auf der Kartenseite deiner Rolle.
    `tp_moeglich`: Teleport genommen oder aus der Top-Quest (die HUD-Abklingzeit, wenn bekannt, zaehlt)."""
    satz = _gross(f"{OBJ_NOM[schl]} {kommt(schl)} in einer Minute") + (" - und er entscheidet die Seele" if seele else "")
    if rolle == "JUNGLE":
        seite = "Bot" if schl == "drache" else "Top"
        prio = _prio_satz(b, ("Mid", seite))
        return satz + ". " + (f"{prio}, setz Sicht an die Grube." if prio
                              else f"Prüf, ob Mid und {seite} Prio haben, und setz Sicht an die Grube.")
    tp = b.zweiter if b.zweiter is not None and b.zweiter[0] == "SummonerTeleport" else None
    if tp is None and tp_moeglich:
        tp = ("SummonerTeleport", 0.0)     # Abklingzeit unbekannt (kein HUD): als bereit rechnen
    zu_fuss = b.zum_objective
    hin = meine_seite or (zu_fuss is not None and zu_fuss <= 25) or (tp is not None and tp[1] <= 50)
    if b.leben is not None and b.leben < 0.5 or (b.gold >= 1300 and not back_eben(b)):
        grund = f"du hast {b.gold // 100 * 100} Gold" if b.gold >= 1300 else f"du hast nur {int(b.leben * 100)} Prozent Leben"
        tun = f"Geh jetzt back, {grund}" + (", und dann hin." if hin else ", und mach danach Druck auf deiner Seite.")
    elif meine_seite or (zu_fuss is not None and zu_fuss <= 25):
        tun = "Schieb deine Welle rein und geh dann hin" + (f", das sind {sek(zu_fuss)}." if zu_fuss else ".")
    elif tp is not None:
        tun = ("Schieb deine Welle rein und teleportier dich dann hin." if tp[1] <= 50
               else f"Dein Teleport ist erst in {sek(tp[1])} bereit, das ist zu spät - mach lieber Druck auf der "
                    f"anderen Seite.")
    else:
        tun = "Für dich zu weit - mach Druck auf deiner Seite."
    return f"{satz}. {tun}"


def jungler_tot(b: Bewertung, sekunden: int, objective: str | None, nah: bool, platten: bool) -> str:
    """Der gegnerische Jungler ist tot. `objective`: Schluessel eines machbaren Objectives (oder None),
    `nah`: es liegt auf deiner Seite."""
    j = b.jungler.champion if b.jungler else "Der Jungler"
    satz = f"{j} ist für {sekunden} Sekunden tot"
    if objective:
        if nah:
            weg = f" - du bist {sek(b.zum_objective)} entfernt" if b.zum_objective and b.zum_objective >= 8 else ""
            return f"{satz}: nehmt jetzt {OBJ_AKK[objective]}, niemand kann kontern{weg}."
        tun = chance(b, platten)
        return f"{satz}: ping {OBJ_AKK[objective]} für dein Team." + (f" {tun}." if tun else "")
    tun = chance(b, platten)
    return f"{satz}, es kann also kein Gank kommen." + (f" {tun}." if tun else " Spiel nach vorn.")


def zahlen(b: Bewertung, tote: list[str], sekunden: int, objective: str | None, wir: int, die: int) -> str:
    """Zwei oder mehr Gegner tot: was jetzt - mit Namen, Zahl und ob DU es rechtzeitig schaffst."""
    satz = f"{_namen(tote)} {'ist' if len(tote) == 1 else 'sind'} für {sekunden} Sekunden tot, ihr seid {wir} gegen {die}"
    if objective:
        if b.zum_objective is not None and b.zum_objective > sekunden:
            return f"{satz}. Dein Team nimmt {OBJ_AKK[objective]} - du schaffst es nicht rechtzeitig hin, also drück deine Lane."
        return f"{satz}: nehmt jetzt {OBJ_AKK[objective]}."
    return f"{satz}: drückt jetzt die Türme, solange sie fehlen."


def zahlen_nachteil(b: Bewertung, tote: list[str], sekunden: int) -> str:
    n = 5 - len(tote)
    zu = {1: "allein", 2: "nur zu zweit", 3: "nur zu dritt", 4: "zu viert"}.get(n, f"zu {n}")
    satz = f"{_namen(tote)} {'ist' if len(tote) == 1 else 'sind'} für {sekunden} Sekunden tot, ihr seid {zu}"
    if b.unter_eigenem_turm:
        return satz + f". Bleib an {b.turm_name} und nimm keinen Kampf an."
    ob = b.objective
    if ob and ob[1] <= sekunden:      # es lebt oder kommt, bevor sie wieder da sind: welches, konkret
        return satz + f". Nimm keinen Kampf an und gib {OBJ_AKK[ob[0]]} lieber ab. {_rueckzug(b)}."
    return satz + f". Nimm keinen Kampf an, bis sie wieder da sind - {_rueckzug(b)[:1].lower() + _rueckzug(b)[1:]}."


def obj_dazu(b: Bewertung, nah: bool, tp_moeglich: bool, kl=None) -> str:
    """Dein Team faengt ein Objective an - was du tust. `kl`: bewertung.Kampflage an der Grube."""
    if nah:
        return "Du bist nah genug, geh hin" + (f" - das sind {sek(b.zum_objective)}." if b.zum_objective and b.zum_objective >= 5 else ".")
    # Kann keiner von ihnen es streitig machen, braucht das Team deinen Teleport nicht (Nachlauf 194524, 13:58:
    # "teleportier dich hinter die Grube" - Vi war seit 24 s tot, und 4 s spaeter hiess es "hol dir die Platten")
    if kl is not None:
        art, _ = kl.urteil()
        wir, die, offen = kl.zahlen()
        p = b.partie
        j = p.jungler(gegenteam(p.mein_team)) if p is not None and p.mein_team else None    # tot: nicht in b.gegner
        j_tot = j is not None and j.tot
        if art == "nehmen" and (j_tot or die + offen == 0):
            warum = f"{j.champion} ist tot" if j_tot else "keiner von ihnen ist rechtzeitig dort"
            return f"Das schafft dein Team ohne dich - {warum}. Mach du Druck auf deiner Seite."
    tp = b.zweiter if b.zweiter is not None and b.zweiter[0] == "SummonerTeleport" else None
    if tp is None and tp_moeglich:
        tp = ("SummonerTeleport", 0.0)
    if tp is not None and tp[1] <= 0:
        return "Dein Teleport ist bereit: teleportier dich hinter die Grube."
    if b.zum_objective is not None and b.zum_objective <= 25:
        return f"Du brauchst {sek(b.zum_objective)} dorthin, also geh hin."
    return "Für dich zu weit - mach Druck auf deiner Seite."


def lane_recall(b: Bewertung, champion: str, platten: bool) -> str:
    """Der Lane-Gegner recallt (stand still, dann weg): was du mit den ~15 s machst."""
    satz = f"{champion} recallt gerade"
    if frisch := [x for x in gefahr(b, ausser=b.lane) if x.seit is not None and x.seit <= 15]:
        return satz + f", aber {frisch[0].champion} {_wann(frisch[0])}. Schieb die Welle nur bis zum Turm."
    if platten:
        tun = f"Schieb die Welle in seinen Turm und hol dir {_platten(b)}"
    else:
        tun = "Schieb die Welle rein, dann hast du Zeit für deinen eigenen Recall"
    if b.gold >= RECALL_GOLD:
        tun += f", und geh danach selbst back, du hast {b.gold // 100 * 100} Gold"
    return f"{satz}. {tun}."


def gegner_am_objective(namen: str, grube: str, name: str, kl, weit: bool = False) -> str:
    """Die Gegner machen ein Objective: hin (contesten) oder tauschen - aus der Kampflage. `weit`: du bist zu weit
    weg, um mitzumachen (Live 26.09., 12:49, Graves top: "lauft nicht rein" - Carlos: "Ich bin doch gar nicht am
    Drachen, ich bin auf der Toplane. Was laberst du?")."""
    wir, die, offen = kl.zahlen()
    art, _ = kl.urteil()
    akk = OBJ_AKK.get(kl.schl, name)
    satz = f"{namen} machen gerade {akk}"
    if weit:
        return satz + " - zu weit für dich, nutz die Zeit auf deiner Seite."
    zahl = f"{wir} gegen {die}" + (f", {offen} weitere sind nicht zu sehen" if offen else "")
    if art == "nehmen":
        return satz + f". Ihr seid {zahl}: geht hin und macht es ihnen streitig."
    if art == "abgeben":
        return satz + f". Ihr seid nur {zahl}: lauft nicht rein, holt euch lieber woanders etwas."
    return satz + f". Es steht {zahl}: geht nur mit allen und mit Ults hin, sonst tauscht woanders."


def jungler_spaet(b: Bewertung, j: GegnerLage, seite: str) -> str:
    """Nach der Lane-Phase: der gegnerische Jungler zeigt sich auf `seite` ("oben"/"unten") - was die
    andere Seite jetzt hergibt: das Objective dort (mit Kampflage), sonst die Seitenwelle."""
    ruhe = j.ankunft
    satz = _ist(j) + (f", frühestens in {sek(ruhe)} bei dir" if ruhe and ruhe >= 10 else "")
    andere = "unten" if seite == "oben" else "oben"
    ob = b.objective
    ob_seite = None if not ob else ("unten" if ob[0] == "drache" else "oben")
    if ob and ob_seite == andere and ob[1] <= 30:
        if b.kampf is not None:
            art, _ = b.kampf.urteil()
            if art == "nehmen":
                return f"{satz}. Nehmt jetzt {OBJ_AKK[ob[0]]}, {j.champion} ist nicht rechtzeitig da."
            if art == "abgeben":
                return f"{satz}. {_gross(OBJ_AKK[ob[0]])} trotzdem nicht - zu wenige von euch sind in der Nähe."
        return f"{satz}. Das ist eine Chance auf {OBJ_AKK[ob[0]]}, aber nur, wenn dein Team in der Nähe ist."
    if andere_g := gefahr(b, ausser=j):
        x = andere_g[0]
        return f"{satz}. Aber {x.champion} {_wann(x)} - lauf nicht vor."
    if ruhe and ruhe >= 20:
        return f"{satz}. Drück deine Seitenwelle und geh auf den Turm, du hast mindestens {sek(ruhe)}."
    return satz + "."


def spike(b: Bewertung, items: str) -> str:
    """Eigenes Item fertig (ausserhalb des Brunnens, sonst denker.aufbruch): was es gegen deinen Lane-Gegner
    jetzt heisst - neuer Vorsprung, dazu der Trade-Hinweis aus der Spielakte."""
    satz = f"{items} ist fertig"
    g = b.lane
    if g is None or g.s.tot:
        return satz + " - das ist dein Powerspike, such den nächsten Kampf."
    wert, _ = b.kraefte()
    v = b.vorsprung_satz()
    if v.startswith("du bist "):
        v_nach = "bist du " + v[len("du bist "):]      # "damit bist du 2 Level vorn"
    else:
        v_nach = v
    if wert >= 1:
        return satz + (f", damit {v_nach}" if v else "") + f". Geh zurück in die Lane und spiel auf {g.champion}" \
            + (f" - {b.trade}." if b.trade else ".")
    if wert <= -1:
        return satz + (f", aber {v}" if v else "") + ". Noch kein All-in, erst mit dem nächsten Item."
    return satz + (f", {v}" if v else "") + f". Kurze Trades gegen {g.champion} gewinnst du jetzt."


def wiedereinstieg(b: Bewertung, sekunden: int, rolle: str) -> str:
    """Tot, gleich wieder da: Kauf (aus dem Kaufplan) und das erste Ziel danach - Objective, das bald
    kommt (ein lebendes nur, wenn die Kampflage 'nehmen' sagt), sonst die eigene Welle (drueckt sie auf
    deinen Turm, zuerst dorthin)."""
    from .kaufplan import _akk
    kauf = ("Kauf " + " und ".join(_akk(x) for x in b.kauf.kaufen)) if b.kauf is not None and b.kauf.kaufen else ""
    ob = b.objective
    lane = {"TOP": "Top", "MIDDLE": "Mid", "BOTTOM": "Bot", "UTILITY": "Bot"}.get(rolle)
    lohnt = ob is not None and (0 < ob[1] <= 60 or (ob[1] <= 0 and b.kampf is not None
                                                     and b.kampf.urteil()[0] == "nehmen"))
    if lohnt and not (rolle == "TOP" and ob[0] == "drache" and ob[1] > 0):
        ziel = (f"geh direkt {ZUM[ob[0]]}" + (", dein Team ist dort" if ob[1] <= 0
                                             else f", {OBJ_NOM[ob[0]]} {kommt(ob[0])} in {sek(ob[1])}"))
    elif lane and b.prio.get(lane) == "er":
        ziel = f"geh sofort {lane}, seine Welle drückt auf deinen Turm"
    elif rolle == "JUNGLE":
        ziel = "geh zu den Camps auf der Seite des nächsten Objectives"
    else:
        ziel = "geh zurück in die Lane"
        if not kauf:
            return ""      # nichts, was er nicht selbst weiss - schweigen
    return f"Noch {sekunden} Sekunden bis zum Wiedereinstieg. " + (f"{kauf}, und dann {ziel}." if kauf
                                                                    else f"{_gross(ziel)}.")


ZUM = {"drache": "zum Drachen", "baron": "zum Baron", "herold": "zum Herold", "larven": "zu den Larven"}


def kontrollauge(b: Bewertung, rolle: str) -> str:
    """Nach dem Einkauf ohne Kontroll-Auge: wofuer es JETZT zaehlt. '' = kein besonderer Grund (dann der
    allgemeine Satz)."""
    ob = b.objective
    meine = (b.zeit >= 840 or rolle in ("MIDDLE", "JUNGLE")
             or (ob is not None and (ob[0] == "drache") == (rolle in ("BOTTOM", "UTILITY"))))
    if ob and 0 < ob[1] <= 150 and meine:
        wo = "an die Drachengrube" if ob[0] == "drache" else "an die Baron-Grube"
        return (f"Nimm ein Kontroll-Auge mit, 75 Gold, und setz es {wo} - {OBJ_NOM[ob[0]]} {kommt(ob[0])} "
                f"in {sek(ob[1])}.")
    j = b.jungler
    if b.zeit < 840 and j and not j.s.tot and (j.unbekannt or (j.seit or 0) >= 30) and rolle != "JUNGLE":
        busch = {"TOP": "in den Fluss-Busch oben", "MIDDLE": "an deinen Seiten-Busch", "BOTTOM": "in den Tri-Busch",
                 "UTILITY": "in den Tri-Busch"}.get(rolle, "an den Gank-Weg")
        weg = "nicht zu sehen" if j.seit is None else f"seit {sek(j.seit)} weg"
        return f"Nimm ein Kontroll-Auge mit, 75 Gold, und setz es {busch} - {j.champion} ist {weg}."
    return ""
