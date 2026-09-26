"""Die Denkkette: aus allen Faktoren EINE zusammenhaengende Anweisung - Anlass, Gruende, Handlung, und was
danach kommt (Gold -> Kauf -> Weg -> Sicht).

Carlos, Live-Partie 26.09. gegen Heimerdinger ("eine Vollkatastrophe"): "Der muesste sowas sagen wie: du hast
jetzt Level 6 erreicht, Heimerdinger ist noch Level 5, du hast noch deinen Beschwoererzauber, genug Leben, deine
Ult, er nicht - geh rein, toete ihn, du kriegst 300 Gold, und mit dem Gold holst du den Brutalisierer; wenn du
den Trank verkaufst, reicht es fuer Schuhe. Dann gehst du nicht direkt zurueck in die Lane, sondern Richtung
Herold, wardest dort und am gegnerischen Red Buff, weil der Jungler da wahrscheinlich in einer Minute ist."
Und: "Der Coach muss in der Lage sein, zusammenhaengende Saetze zu formulieren!"

Deshalb zwei Schichten:
  1. Rechnen: jeder Faktor mit Gewicht (grob: ein Punkt ~ ein Level frueh im Spiel), die Summe entscheidet.
  2. Sprechen: die Faktoren werden nicht aufgezaehlt, sondern zu Saetzen gebaut - was sich geaendert hat,
     warum du staerker bist ("Dazu hat Heimerdinger kein Flash ..."), was dagegen spricht ("Aber ..."),
     was du tust ("Also ...") und was danach kommt ("Mit dem Kill hast du ...").

Alles ohne Claude: eine Ansage ist nach Millisekunden fertig. (Dieselbe Partie: die von Claude umformulierten
Saetze kamen 5 bis 21 Sekunden zu spaet - "die Ansagen kommen super, super spaet".)

Was der Coach weiss und was nicht - er nennt nur, was er weiss:
  - Level, Items, Gold, K/D (API); dein Leben (API), dein Flash, zweiter Zauber und Ult (HUD),
  - sein Leben (Lebensbalken im Spielbild, wenn er zu sehen ist), sein Flash und seine Ult (Pings, Minimap),
  - wo Jungler und die anderen zuletzt waren und wie schnell sie bei dir sein koennen (Minimap),
  - NICHT seine Grundfaehigkeiten: die Abklingzeiten von Q/W/E eines Gegners zeigt das Spiel nicht.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .bewertung import TURM_REICHWEITE, Bewertung, GegnerLage, abstand, stehende_tuerme
from .komponist import OBJ_NAME, _wann, gefahr, sek
from .zustand import BLAU, ROT, gegenteam

KILL_AB = 3.5          # Summe der Faktoren: All-in
TRADE_AB = 2.0         # harte Trades, All-in erst bei weniger Leben
WEG_UNTER = -2.5       # er ist klar staerker: nicht traden
TRAENKE = (2003, 2031, 2033)   # Heiltrank, Nachfuellbarer, Verderbender - verkaufbar fuer den naechsten Kauf
KAUF_LOHNT_AB = 850    # so viel muss ein Einkauf wert sein, damit sich ein Recall dafuer lohnt (Langschwert: nein)
KRAFT = ("level", "ult", "items", "matchup")
ZUSTAND = ("leben", "zuenden_kill", "combo_kill", "combo_knapp", "combo_zu_wenig", "combo_er", "flash", "flash_ich", "zuenden",
           "welle", "gold_offen", "mana", "mana_er")
UMFELD = ("jungler", "jungler_nah", "jungler_weg", "dritter", "hilfe", "zone")
ZONE_NAME = {"Heimerdinger": "Geschütze", "Zyra": "Pflanzen", "Azir": "Soldaten", "Illaoi": "Tentakel",
             "Yorick": "Ghule", "Teemo": "Pilze", "Shaco": "Boxen"}


@dataclass
class Faktor:
    wert: float      # > 0 spricht fuer dich
    art: str         # "level", "ult", "items", "leben", "flash", "zuenden", "welle", "turm", "jungler", ...
    subj: str        # Satzbau: Subjekt, Verb, Rest - damit "Dazu hat Heimerdinger kein Flash" geht
    verb: str
    rest: str

    @property
    def satz(self) -> str:
        return f"{self.subj} {self.verb} {self.rest}".strip()

    @property
    def invers(self) -> str:
        """Verb zuerst (nach "Dazu", "Ausserdem"): 'hat Heimerdinger kein Flash'."""
        return f"{self.verb} {self.subj} {self.rest}".strip()


@dataclass
class Urteil:
    art: str                  # "kill", "kill_schnell", "turm", "trade", "halten", "weg"
    wert: float
    faktoren: list[Faktor]

    @property
    def arten(self) -> set[str]:
        return {f.art for f in self.faktoren if f.wert > 0}

    @property
    def arten_alle(self) -> set[str]:
        return {f.art for f in self.faktoren}


# --- Rechnen: der Kampf gegen den Lane-Gegner ----------------------------------------------------------

def _gold(n: int) -> str:
    return f"{abs(n) // 100 * 100} Gold"


def kampf_faktoren(b: Bewertung) -> list[Faktor]:
    """Alles, was ein 1-gegen-1 mit deinem Lane-Gegner JETZT entscheidet, mit Gewicht. Negativ = gegen dich.
    Level und Items zaehlen relativ: 2 Level bei Level 3 sind mehr als bei Level 11, 1800 Gold bei 2400 mehr
    als bei 8000 (Live 26.09., 12:44: "Kill" an Riven L11 gegen Heimerdinger L9 - absolut gerechnet zu viel)."""
    g = b.lane
    if g is None or g.s.tot:
        return []
    f: list[Faktor] = []
    ich, er, n = b.ich, g.s, g.champion
    d = ich.level - er.level
    if d:
        hoch = max(ich.level, er.level)
        w = (1.2 if hoch <= 3 else 0.7) * d * 6 / max(6, hoch)
        f.append(Faktor(w, "level", "du", "bist", f"Level {ich.level}, {n} erst {er.level}") if d > 0
                 else Faktor(w, "level", n, "ist", f"Level {er.level}, du erst {ich.level}"))
    if ich.level >= 6 > er.level:
        if b.ult is not False:
            f.append(Faktor(1.8, "ult", "deine Ult", "ist", "da, seine noch nicht"))
        else:
            # zaehlt leicht, wird aber nicht gesagt (< 0.3): direkt nach dem Level-up ist R meist nur noch nicht
            # geskillt - "trade hart: deine Ult laedt noch" (Nachlauf Wukong 5:05) war kein Grund
            f.append(Faktor(0.25, "ult", "deine Ult", "lädt", "noch"))
    elif er.level >= 6 > ich.level:
        f.append(Faktor(-1.8, "ult", n, "hat", "schon die Ult, du noch nicht"))
    else:
        if ich.level >= 6 and b.ult is False:
            f.append(Faktor(-1.0, "ult", "deine Ult", "lädt", "noch"))
        if er.level >= 6 and g.ult and g.ult > 5:
            f.append(Faktor(1.2, "ult", "seine Ult", "ist", f"noch {sek(g.ult)} weg"))
    gd = ich.item_gold - er.item_gold
    if abs(gd) >= 400:
        w = max(-3.0, min(3.0, 3.5 * gd / (max(ich.item_gold, er.item_gold) + 1500)))
        f.append(Faktor(w, "items", "du", "hast", f"{_gold(gd)} mehr in Items") if gd > 0
                 else Faktor(w, "items", n, "hat", f"{_gold(gd)} mehr in Items"))
    # Leben: deins aus der API, seins aus dem Balken im Bild (nur frisch)
    if b.leben is not None and b.leben < 0.35:
        f.append(Faktor(-3.0, "leben", "du", "hast", f"nur {int(b.leben * 100)} Prozent Leben"))
    elif g.leben is not None:
        mein = b.leben if b.leben is not None else 0.8
        w = (mein - g.leben) * 5
        if g.leben <= 0.6:
            f.append(Faktor(w, "leben", n, "hat", f"nur noch {int(g.leben * 100)} Prozent Leben"))
        elif w <= -1:
            f.append(Faktor(w, "leben", n, "hat", "mehr Leben als du"))
        elif mein >= 0.85:
            f.append(Faktor(max(w, 0.3), "leben", "du", "hast", "volles Leben"))
    elif b.leben is not None and b.leben >= 0.85:
        f.append(Faktor(0.3, "leben", "du", "hast", "volles Leben"))
    elif b.leben is not None and b.leben < 0.55:
        f.append(Faktor(-1.2, "leben", "du", "hast", f"nur {int(b.leben * 100)} Prozent Leben"))
    if g.flash and g.flash > 10:
        f.append(Faktor(1.0, "flash", n, "hat", "kein Flash"))
    if b.flash is not None and b.flash > 10:
        f.append(Faktor(-0.8, "flash_ich", "dein Flash", "ist", "weg"))
    zuenden_bereit = bool(b.zweiter and b.zweiter[0] == "SummonerDot" and b.zweiter[1] <= 0)
    combo_faktor = _combo(b, g, zuenden_bereit)
    if combo_faktor is not None:
        f.append(combo_faktor)
    if (er_faktor := _combo_er(b, g)) is not None:
        f.append(er_faktor)
    if zuenden_bereit and combo_faktor is not None and combo_faktor.art == "combo_kill":
        pass                                  # Zuenden steckt in der Combo-Rechnung
    elif zuenden_bereit:
        # Reasoning #1 ("reicht mein Schaden fuer den Kill?"): sein Leben aus dem Balken x sein Max-Leben (Data
        # Dragon) gegen den wahren Schaden von Zuenden - mit 10 % Abschlag (Heilung, Schilde)
        from . import rechnung
        rest = g.leben * rechnung.max_leben(er) if g.leben is not None else None
        if rest is not None and rest <= 0.9 * rechnung.zuenden_schaden(ich.level):
            f.append(Faktor(1.8, "zuenden_kill", "dein Zünden", "tötet", f"{n} allein, {n} hat nur noch etwa "
                                                                        f"{int(rest) // 10 * 10} Leben"))
        else:
            f.append(Faktor(0.8, "zuenden", "dein Zünden", "ist", "bereit"))
    # deine Ressource (Reasoning #1/#2 "Mana Advantage", "Ressourcen fuer Combo"): Mana/Energie aus der API
    w = b.partie.werte if b.partie is not None else {}
    if w.get("resourceType") in ("MANA", "ENERGY") and (voll := float(w.get("resourceMax") or 0)) > 0:
        anteil = float(w.get("resourceValue") or 0) / voll
        was = "Mana" if w["resourceType"] == "MANA" else "Energie"
        if anteil < 0.25:
            f.append(Faktor(-1.0, "mana", f"dein {was}" if was == "Mana" else "deine Energie", "reicht",
                            "kaum für eine Combo"))
    # sein Mana (Reasoning #4 "Mana"): aus dem Balken unter seinem Lebensbalken - nur bei Mana-Champions
    if g.mana is not None and g.mana < 0.25 and _hat_mana(er.champion_id):
        f.append(Faktor(1.0, "mana_er", n, "hat", f"nur noch {int(g.mana * 100)} Prozent Mana"))
    # sein Item-Timing: traegt er viel Gold, ist er nach dem naechsten Back staerker - jetzt ist besser als gleich
    from .bewertung import gold_offen
    offen = gold_offen(er, b.zeit)
    if offen >= 900 and b.zeit >= 240:
        f.append(Faktor(0.3, "gold_offen", n, "trägt", f"geschätzt {offen // 100 * 100} Gold mit sich, nach seinem "
                                                        f"Back ist {n} stärker"))
    if b.welle:
        wir, die = b.welle[0], b.welle[1]
        if wir - die >= 3:
            f.append(Faktor(0.6, "welle", "deine Welle", "ist", "größer"))
        elif die - wir >= 3:
            f.append(Faktor(-0.8, "welle", "seine Welle", "ist", "größer"))
    # Turm: sperrt den Kampf (ein All-in dort ist ein Dive) - zaehlt nicht in die Summe, siehe urteil()
    if g.pos is not None and b.partie is not None:
        feind = gegenteam(b.partie.mein_team)
        if any(abstand(g.pos, v) <= TURM_REICHWEITE + 250 for (t, _, _), v in stehende_tuerme(b.partie).items()
               if t == feind):
            f.append(Faktor(-2.5, "turm", n, "steht", "an seinem Turm"))
    j = b.jungler
    if j is not None and b.zeit >= 115:
        if j.s.tot:
            f.append(Faktor(0.8, "jungler", j.champion, "ist", "tot"))
        elif j.seit is not None and j.seit <= 25 and j.ankunft is not None and j.ankunft >= 15:
            f.append(Faktor(0.6, "jungler", j.champion, "ist", f"{j.ort}, weit weg"))
        elif j.seit is not None and j.seit <= 25 and j.ankunft is not None and j.ankunft < 8:
            f.append(Faktor(-3.0, "jungler_nah", j.champion, "ist", "ganz in der Nähe"))
        elif j.unbekannt or (j.seit or 0) > 25:
            f.append(Faktor(-0.8, "jungler_weg", j.champion, "ist", f"seit {sek(j.seit or b.zeit)} nicht zu sehen"))
    for x in b.bedrohung(8):
        if x.s.name == g.s.name or (j is not None and x.s.name == j.s.name):
            continue
        wann = _wann(x)
        f.append(Faktor(-2.0, "dritter", x.champion, wann.split(" ", 1)[0], wann.split(" ", 1)[1]
                        if " " in wann else ""))
    for s in b.mitspieler_nah:
        f.append(Faktor(1.0, "hilfe", s.champion, "ist", "bei dir"))
    f += _matchup(b, g)
    return f


def _matchup(b: Bewertung, g: GegnerLage) -> list[Faktor]:
    """Reasoning #1/#23 (Matchup-Dynamik): wer ist in DIESER Phase der staerkere Champion - aus der Lane-Kurve
    (wissen/lane_kurve.toml: Level 1-5, beide mit Ult, spaet). Dazu die Zone: gegen Heimerdinger, Zyra, Azir ...
    ist ein Kampf auf ihrer Haelfte schlechter, als Level und Items sagen (Live 26.09.: 1:45 "Kill" an Riven L2
    gegen Heimerdinger L1 - Heimerdinger ist Level 1-3 mit Geschuetzen der Lane-Bully)."""
    from . import wissen
    try:
        daten = wissen.lade("lane_kurve")
    except Exception:
        return []
    kurve = daten.get("kurve", {})
    ich, er = kurve.get(b.ich.champion_id), kurve.get(g.s.champion_id)
    aus: list[Faktor] = []
    wr = siegquote(b.ich.champion_id, g.s)
    if wr is not None:
        # das konkrete Duell schlaegt die allgemeine Kurve (Live 26.09. 21:22: "dein Champion ist bis Level 5 der
        # staerkere gegen Gragas" - das Lexikon sagt Riven gegen Gragas 45,9 %, schwer; das Briefing sagte dasselbe)
        w = max(-1.5, min(1.5, (wr - 50) * 0.25))
        text = f"{wr:.1f}".replace(".", ",")
        if wr <= 48:
            aus.append(Faktor(w, "matchup", g.champion, "ist", f"ein schweres Matchup für dich, {text} Prozent Siegquote"))
        elif wr >= 52:
            aus.append(Faktor(w, "matchup", "das Matchup", "liegt", f"dir, {text} Prozent Siegquote"))
        ich = er = None             # die Kurve nicht zusaetzlich
    if ich and er:
        hoch, tief = max(b.ich.level, g.s.level), min(b.ich.level, g.s.level)
        if hoch <= 5:
            d, w_je, wann = ich[0] - er[0], 0.5, "bis Level 5"
        elif tief >= 6 and hoch <= 10:
            d, w_je, wann = ich[1] - er[1], 0.4, "mit beiden Ults"
        elif hoch >= 11:
            d, w_je, wann = ich[2] - er[2], 0.3, "ab jetzt"
        else:
            d, w_je, wann = 0, 0.0, ""          # einer hat die Ult, der andere nicht - das sagt der Ult-Faktor
        if d > 0:
            aus.append(Faktor(w_je * d, "matchup", "dein Champion", "ist", f"{wann} der stärkere gegen {g.champion}"))
        elif d < 0:
            aus.append(Faktor(w_je * d, "matchup", g.champion, "ist", f"{wann} der stärkere Champion"))
    if g.s.champion_id in daten.get("zone", []) and b.zeit < 840 and (b.tiefe or 0) >= 0.5:
        aus.append(Faktor(-1.2, "zone", "du", "kämpfst", f"in seiner Zone, dort stehen seine "
                                                        f"{ZONE_NAME.get(g.s.champion_id, 'Fallen')}"))
    return aus


def siegquote(champion_id: str, gegner) -> float | None:
    """Siegquote deines Champions gegen genau diesen Gegner aus dem Lexikon (Abschnitt Matchups, lolalytics
    Emerald+ - fuer Carlos' Champions Riven, Camille, Graves). None, wenn es keine Zeile gibt."""
    import re
    from .gehirn import matchup
    zeile = matchup(champion_id, gegner)
    m = re.search(r"\((\d+),(\d) %", zeile)
    return float(f"{m.group(1)}.{m.group(2)}") if m else None


def _hat_mana(champion_id: str) -> bool:
    from . import ddragon
    return (ddragon.champions().get(champion_id) or {}).get("partype") in ("Mana", "Mana ")


def _combo(b: Bewertung, g: GegnerLage, zuenden: bool) -> Faktor | None:
    """Reasoning #1: dein voller Combo (combo.py: Wiki-Werte, deine Raenge und dein AD aus der API, bereit laut
    HUD, seine Ruestung) plus Zuenden gegen sein Leben (Balken x Max-Leben). Nur mit seinem Leben im Bild.
    Riven, Camille, Graves von Hand geprueft - alle anderen aus den Spieldaten als Untergrenze (ein Treffer je
    Faehigkeit): die zaehlt nur, wenn sie schon reicht; "reicht nicht" sagt sie nicht (lieber stumm als falsch)."""
    from . import combo, rechnung
    if g.leben is None or b.partie is None or not combo.kann(b.ich.champion_id):
        return None
    dmg = combo.schaden(b.ich, b.partie.werte, b.partie.raenge, b.bereit, g.s, g.leben)
    if dmg is None or dmg <= 0:
        return None
    if zuenden:
        dmg += rechnung.zuenden_schaden(b.ich.level)
    rest = g.leben * rechnung.max_leben(g.s)
    n = g.champion
    zahl, leben = int(dmg) // 10 * 10, int(rest) // 10 * 10
    if dmg >= 1.1 * rest:     # 10 % Reserve: Heilung, Schilde, ein verfehlter Treffer
        if not combo.genau(b.ich.champion_id):
            return Faktor(2.2, "combo_kill", "dein Combo", "macht", f"mindestens {zahl} Schaden, {n} hat noch {leben} Leben")
        return Faktor(2.2, "combo_kill", "dein Combo", "macht", f"etwa {zahl}, {n} hat nur {leben} Leben")
    if not combo.genau(b.ich.champion_id):
        return None
    if dmg >= 0.8 * rest:
        return Faktor(0.6, "combo_knapp", "dein Combo", "macht", f"etwa {zahl}, {n} hat noch {leben} - das ist knapp")
    return Faktor(-1.0, "combo_zu_wenig", "dein Combo", "macht", f"nur etwa {zahl}, {n} hat noch {leben} Leben")


def _combo_er(b: Bewertung, g: GegnerLage) -> Faktor | None:
    """Reasoning #1 andersherum: toetet SEIN Combo dich? Untergrenze aus den Spieldaten (combo.gegner_schaden:
    ein Treffer je Faehigkeit, Raenge aus seinem Level und der Skill-Reihenfolge des Lexikons, seine Items, deine
    Ruestung und Magieresistenz aus der API) gegen dein Leben (API). Nur wenn schon die Untergrenze reicht."""
    from . import combo
    if b.leben_abs is None or b.leben_abs <= 0 or b.partie is None:
        return None
    dmg = combo.gegner_schaden(g.s, b.partie.werte, ult_bereit=not (g.ult and g.ult > 0), anteil=g.leben)
    if dmg is None or dmg < 1.05 * b.leben_abs:
        return None
    # ohne dein Leben als Zahl: der Leben-Faktor nennt es oft schon ("nur 20 Prozent Leben")
    return Faktor(-2.0, "combo_er", g.champion, "tötet", f"dich schon mit einem Combo, mindestens {int(dmg) // 10 * 10} Schaden")


def urteil(b: Bewertung) -> Urteil | None:
    """Summe der Faktoren -> was du gegen deinen Lane-Gegner jetzt tust."""
    f = kampf_faktoren(b)
    if not f:
        return None
    # Sein Turm macht ihn nicht staerker - er sperrt nur den Kampf. Er zaehlt nicht in die Summe, sonst hiess
    # "Shen steht an seinem Turm" = "Shen ist staerker, farm sicher". Einen Dive empfiehlt der Coach nicht:
    # Live 26.09., 11:00 haette er ihn empfohlen - 11:08 starb Riven genau dort an Heimerdinger und Turm.
    wert = sum(x.wert for x in f if x.art != "turm")
    arten = {x.art for x in f}
    ev = erwartung(b, wert)
    bedroht = bool({"jungler_nah", "dritter"} & arten)
    if "turm" in arten and wert >= TRADE_AB:
        art = "halten" if bedroht else "turm"
    elif wert >= KILL_AB:
        if bedroht:
            art = "halten"
        elif "jungler_weg" in arten and wert < KILL_AB + 1.0:
            art = "trade"
        elif "jungler_weg" in arten:
            art = "kill_schnell"
        else:
            art = "kill"
    elif wert >= TRADE_AB:
        art = "halten" if bedroht else "trade"
    elif wert <= WEG_UNTER:
        art = "weg"
    else:
        art = "halten"
    # Die Rechnung belegt den Kill mit Reserve (Combo + Zuenden >= 110 % seines Lebens): dann kein "trade hart, All-in
    # erst unter der Haelfte" (Nachlauf 21:21, 2:44: "dein Combo macht 510, Gragas hat noch 450 - trade hart")
    if "combo_kill" in arten and art in ("trade", "halten") and not bedroht:
        art = "kill_schnell" if "jungler_weg" in arten else "kill"
    # ... und umgekehrt: sagt die Rechnung "reicht nicht", ist es kein Kill, egal wie gut der Rest aussieht
    # (Nachlauf 194524, 10:59: combo_zu_wenig und trotzdem "kill" - 9 s vor Rivens Tod an Heimerdinger)
    if "combo_zu_wenig" in arten and art in ("kill", "kill_schnell"):
        art = "trade"
    # Risiko gegen Ertrag (Reasoning #27/#28): ein Kill, der zu 80 % aufgeht, ist trotzdem falsch, wenn dein Tod
    # (Kopfgeld + Todeszeit) mehr kostet, als der Kill bringt - "play not to throw".
    if art in ("kill", "kill_schnell") and ev is not None and ev[0] < 0:
        art = "trade"
        f.append(Faktor(-1.6, "kopfgeld", "auf dir", "liegen", f"{ev[2]} Gold Kopfgeld - ein Tod kostet mehr, "
                                                              f"als der Kill bringt"))
    return Urteil(art, wert, f)


def erwartung(b: Bewertung, wert: float) -> tuple[float, int, int] | None:
    """(Erwartungswert in Gold, Ertrag, dein Kopfgeld): Siegchance aus der Faktorsumme (logistisch, 50 % bei 2,
    84 % bei 3,5), Ertrag = Kill-Gold nach seinem Level + sein Kopfgeld, Verlust = dein Kopfgeld + Todeszeit x
    ~10 Gold/s (Farm und Erfahrung in der Lane) + seine Kill-Gold-Basis fuer den Gegner [Schaetzung]."""
    from .bewertung import kill_gold, kopfgeld
    g = b.lane
    if g is None:
        return None
    p = 1 / (1 + math.exp(-1.1 * (wert - 2.0)))
    ertrag = kill_gold(g.s, erstes_blut=_erstes_blut_offen(b), p=b.partie)
    mein = kopfgeld(b.ich, b.partie)
    verlust = mein + (b.tod_kostet or 15) * 10 + 300
    return p * ertrag - (1 - p) * verlust, ertrag, mein


def _erstes_blut_offen(b: Bewertung) -> bool:
    p = b.partie
    return p is not None and not any(e.art == "FirstBlood" for e in p.ereignisse)


# --- Sprechen: aus Faktoren Saetze ------------------------------------------------------------------------

def _gross(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _liste(teile: list[str]) -> str:
    teile = [t for t in teile if t]
    if not teile:
        return ""
    return teile[0] if len(teile) == 1 else ", ".join(teile[:-1]) + " und " + teile[-1]


def _haupt(fs: list[Faktor], dazu: bool, aber: bool = False) -> str:
    """Bis zu zwei Faktoren als ein Satz. `dazu`: nicht der erste Satz - "Dazu hat Heimerdinger kein Flash,
    und dein Zuenden ist bereit." Level und Ult gehoeren zusammen: "Du bist Level 6, Heimerdinger erst 5 -
    deine Ult ist da, seine noch nicht." """
    if not fs:
        return ""
    erst = ("Aber " + fs[0].satz) if aber else ("Dazu " + fs[0].invers) if dazu else _gross(fs[0].satz)
    if len(fs) == 1:
        return erst + "."
    verbinder = " - " if fs[0].art == "level" and fs[1].art == "ult" else ", und "
    return erst + verbinder + fs[1].satz + "."


def anlass_satz(b: Bewertung, f: Faktor) -> str:
    """Der Faktor, der eben dazukam, als erster Satz: 'Heimerdinger ist auf 40 Prozent', 'Vi ist tot'."""
    g = b.lane
    n = g.champion if g else ""
    if f.art == "leben" and g is not None and g.leben is not None and g.leben <= 0.6:
        return f"{n} ist auf {int(g.leben * 100)} Prozent"
    if f.art == "ult" and f.wert > 0 and g is not None and b.ich.level >= 6 > g.s.level:
        return f"Du bist jetzt Level {b.ich.level}, {n} erst {g.s.level}"
    if f.art == "jungler" and b.jungler is not None:
        return f"{b.jungler.champion} ist tot" if b.jungler.s.tot else f"{b.jungler.champion} zeigt sich {b.jungler.ort}"
    return _gross(f.satz)


HANDLUNG = {
    "kill": "geh rein, das ist ein Kill",
    "kill_schnell": "geh rein, aber schnell, bevor {j} auftaucht",
    "turm": "noch nicht rein, {n} steht an seinem Turm",
    "trade": "trade hart, All-in erst, wenn {n} unter der Hälfte ist",
    "halten": "nur kurze Trades, kein All-in",
    "weg": "nicht traden, farm sicher",
}


def fenster_satz(b: Bewertung, u: Urteil, anlass: str = "", ohne: set[str] = frozenset(),
                 danach: bool = False, anlass_gut: bool = True) -> str:
    """Handlung zuerst, dann die staerksten Gruende in einem Satz, dann das eine Aber:
    'Du bist jetzt Level 6, Gragas erst 4 - geh rein, das ist ein Kill: Gragas hat kein Flash, du hast 700 Gold
    mehr in Items und Tryndamere ist in seiner Basis.'
    Live 26.09. 21:21: mit Anlass, Kraft-, Zustands- und Umfeld-Satz, Aber, Handlung und Danach waren es ~300 Zeichen
    (25-30 s) - der Coach redete 74 % der Spielzeit, und alles Neue wartete ("die Ansagen kommen geisteskrank zu
    spaet"). Das Danach (Gold, Kauf, Weg) sagt jetzt der Satz, wenn der Gegner wirklich tot ist (lane_tot_plan).
    `ohne`: Faktor-Arten, die der Anlass schon sagt. `danach` bleibt fuer die Aufrufer, wird nicht mehr gesprochen."""
    n = b.lane.champion
    j = b.jungler.champion if b.jungler else "der Jungler"
    if "ult" in ohne:
        ohne = set(ohne) | {"level"}           # "Du bist jetzt Level 6, er erst 5" sagt beides
    if {"combo_kill", "combo_knapp", "combo_zu_wenig", "zuenden_kill"} & set(ohne):
        ohne = set(ohne) | {"leben"}           # "Gragas hat noch 350 Leben" sagt der Anlass schon
    # das Matchup (Siegquote) einmal je 5 Minuten - Live 21:21 hing "schweres Matchup, 45,9 Prozent" an jeder
    # Kampf-Ansage (60 Zeichen, fuenfmal)
    box = getattr(b, "matchup_box", None)
    if box is not None and b.zeit - box[0] < 300:
        ohne = set(ohne) | {"matchup"}
    fs = [x for x in u.faktoren if x.art not in ohne and abs(x.wert) >= 0.3]
    fuer_dich = u.art in ("kill", "kill_schnell", "turm", "trade") or (u.art == "halten" and u.wert >= TRADE_AB)
    haupt = sorted((x for x in fs if (x.wert > 0) == fuer_dich and x.art not in ("turm", "kopfgeld")),
                   key=lambda x: -abs(x.wert))
    gegen = sorted((x for x in fs if (x.wert > 0) != fuer_dich), key=lambda x: -abs(x.wert))
    if any(x.art in ("zuenden_kill", "combo_kill", "combo_knapp") for x in haupt):
        haupt = [x for x in haupt if x.art != "leben"]      # "...hat noch 540 Leben" sagt es schon
    if u.art == "halten" and {"jungler_nah", "dritter"} & u.arten_alle:
        # die Handlung nennt ihn schon: "kein All-in, solange Tryndamere in der Naehe ist: Tryndamere ist ganz in der
        # Naehe" (Probe 26.09. nachts)
        haupt = [x for x in haupt if x.art not in ("jungler_nah", "dritter")]
    gruende = haupt[:2]      # zwei, nicht drei: Nachlauf 21:21 - Fenster-Saetze im Schnitt 190 Zeichen, 19 % der Sprechzeit
    aber = []
    if fuer_dich and u.art != "kill_schnell":
        # was dagegen spricht - der Turm steckt schon in der Handlung
        aber = ([x for x in gegen if x.art in ("kopfgeld", "zone")]
                or [x for x in gegen if (abs(x.wert) >= 1.5 or x.art == "matchup") and x.art != "turm"])
    if u.art == "halten":
        aber = [x for x in aber if x.art not in ("jungler_nah", "dritter")]    # die Handlung nennt sie schon
    handlung = HANDLUNG[u.art].format(n=n, j=j)
    if u.art == "halten" and "jungler_nah" in u.arten_alle:
        handlung = f"kein All-in, solange {j} in der Nähe ist"
    elif u.art == "halten" and (dritte := [x for x in u.faktoren if x.art == "dritter"]):
        handlung = f"kein All-in, bis du weißt, ob {dritte[0].subj} kommt"
    if u.art == "weg" and ((b.leben is not None and b.leben < 0.35) or {"jungler_nah", "dritter"} & u.arten_alle):
        from .komponist import _rueckzug
        handlung = _rueckzug(b)[:1].lower() + _rueckzug(b)[1:]
    bedroht_halten = u.art == "halten" and bool({"jungler_nah", "dritter"} & u.arten_alle) and u.wert >= TRADE_AB
    if u.art == "turm":
        # Die Gruende FUER den Kampf erklaeren das Warten nicht ("noch nicht rein: du hast 1700 Gold mehr ..." -
        # Nachlauf 21:21, 8:05). Gesagt wird, was gilt, sobald er den Turm verlaesst.
        text = handlung + f" - kommt {n} raus, " + ("geh rein" if u.wert >= KILL_AB else "trade hart")
    elif bedroht_halten:
        # dasselbe beim Jungler in der Naehe (Camille-Partie 5:21: "kein All-in, solange Gragas in der Naehe ist:
        # deine Ult ist da, seine noch nicht"): was gilt, sobald er weg ist
        wer = j if "jungler_nah" in u.arten_alle else next(x.subj for x in u.faktoren if x.art == "dritter")
        text = handlung + f" - ohne {wer} " + ("wäre es ein Kill" if u.wert >= KILL_AB else "tradest du hart")
    else:
        text = handlung + (": " + _liste([x.satz for x in gruende]) if gruende else "")
    if aber and u.art == "kill":
        # nicht "Vi ist tot - geh trotzdem rein" (Nachlauf 194524, 4:11): das Trotzdem galt dem Aber am Satzende
        text += f". Einziger Haken: {aber[0].satz}"
    elif aber and u.art != "turm" and not bedroht_halten:
        text += f" - aber {aber[0].satz}"
    if anlass:
        # "Du bist zuerst Level 2, Wukong noch 1 - aber nur kurze Trades: du hast nur 49 Prozent Leben."
        text = f"{anlass} - {'aber ' if anlass_gut != fuer_dich else ''}{text}"
    satz = _gross(text) + "."
    if box is not None and "Matchup" in satz:
        box[0] = b.zeit
    if u.art == "turm" and (t := turm_satz(b)):
        satz += " " + t
    return satz


def turm_satz(b: Bewertung) -> str:
    """Reasoning #37 (Turm, Dive-Potenzial) in Zahlen: 'Sein Turm trifft dich mit etwa 270 pro Schuss - mit deinen
    900 Leben haeltst du 2 Schuesse aus.'"""
    from . import rechnung
    g = b.lane
    if g is None or g.pos is None or b.partie is None or b.leben_abs is None:
        return ""
    feind = gegenteam(b.partie.mein_team)
    naechst = min(((abstand(g.pos, v), k) for k, v in stehende_tuerme(b.partie).items() if k[0] == feind), default=None)
    if naechst is None or naechst[0] > TURM_REICHWEITE + 400:
        return ""
    stufe = naechst[1][2]
    schuss = rechnung.turm_schaden(stufe, b.zeit)
    n = rechnung.turm_schuesse(b.leben_abs, stufe, b.zeit)
    schuesse = "keinen Schuss" if n == 0 else ("einen Schuss" if n == 1 else f"{n} Schüsse")
    return f"Sein Turm trifft mit etwa {int(schuss) // 10 * 10}, du hältst {schuesse} aus."


# --- danach: Gold, Kauf, Weg -------------------------------------------------------------------------

def kill_gold(b: Bewertung) -> int:
    """Gold fuer den Kill an deinem Lane-Gegner: nach seinem Level, erstes Blut, sein Kopfgeld (bewertung)."""
    from .bewertung import kill_gold as kg
    return kg(b.lane.s, erstes_blut=_erstes_blut_offen(b), p=b.partie) if b.lane is not None else 300


def trank_wert(b: Bewertung) -> int:
    from . import ddragon
    it = ddragon.items()
    return sum(it.get(i, {}).get("gold", {}).get("sell", 0) for i in b.ich.items if i in TRAENKE)


def kauf(b: Bewertung, gold: int) -> tuple[str, bool]:
    """(was du kaufst, ob sich ein Recall dafuer lohnt). Mit Trank: 'den Brutalisierer, und wenn du den Trank
    verkaufst, auch Stiefel'. Ein Recall lohnt fuer ein fertiges Item oder Bauteile ab KAUF_LOHNT_AB."""
    from . import kaufplan
    from .kaufplan import _akk
    try:
        k = kaufplan.plan(b.ich.champion_id, b.ich.items, gold)
        trank = trank_wert(b)
        k2 = kaufplan.plan(b.ich.champion_id, b.ich.items, gold + trank) if trank else None
    except Exception:
        return "", False
    if k is None:
        return "", False
    if k.kaufen:
        satz = _liste([_akk(x) for x in k.kaufen])
        if k2 is not None and len(k2.kaufen) > len(k.kaufen):
            extra = [x for x in k2.kaufen if x not in k.kaufen]
            satz += f", und wenn du den Trank verkaufst, auch {' und '.join(_akk(x) for x in extra)}"
        return satz, k.item in k.kaufen or k.kosten >= KAUF_LOHNT_AB
    if k2 is not None and k2.kaufen:
        return (f"verkauf den Trank, dann reicht es für {' und '.join(_akk(x) for x in k2.kaufen)}",
                k2.item in k2.kaufen or k2.kosten >= KAUF_LOHNT_AB)
    return "", False


def _kauf_verb(was: str) -> str:
    """'den Brutalisierer' -> 'kauf den Brutalisierer'; 'verkauf den Trank, ...' bleibt."""
    return was if was.startswith("verkauf") else f"kauf {was}"


def nach_dem_kill(b: Bewertung) -> str:
    """Der Satz nach dem Kill-Satz: 'Mit dem Kill hast du 1450 Gold: Welle in seinen Turm, dann back und
    kauf den Brutalisierer.' Lohnt kein Recall, dann die Platten."""
    gold = b.gold + kill_gold(b)
    was, lohnt = kauf(b, gold)
    shutdown = ""
    if lohnt:
        return f"Mit dem Kill hast du {gold // 50 * 50} Gold{shutdown}: Welle in seinen Turm, dann back und {_kauf_verb(was)}."
    if b.platten_gegner:
        return f"Danach die Welle in seinen Turm und die Platten holen, {b.platten_gegner} stehen noch."
    return ""


# --- Weg und Sicht --------------------------------------------------------------------------------------

def meine_seite(b: Bewertung) -> str | None:
    return {"TOP": "oben", "BOTTOM": "unten", "UTILITY": "unten"}.get(b.ich.rolle)


def jungler_prognose(b: Bewertung, jungle) -> tuple[str, float | None]:
    """(Satz, Sekunden bis er auf deiner Seite sein kann) - aus der letzten Sichtung. Ein Jungler raeumt seine
    Seite und quert dann; ~40 s von einer Kartenseite zur anderen [Schaetzung aus Clear-Zeiten 2026]."""
    j = b.jungler
    seite = meine_seite(b)
    if j is None or seite is None:
        return "", None
    if j.s.tot:
        if j.s.respawn < 15:
            return "", None
        return f"{j.champion} ist noch {sek(j.s.respawn)} tot", j.s.respawn + 30
    z = jungle.zuletzt() if jungle is not None else None
    if z is None:
        return "", None
    from .jungle import seite as karten_seite
    vor = b.zeit - z[0]
    dort = karten_seite(z[1], z[2])
    if vor > 90:
        return f"{j.champion} ist seit {sek(vor)} nicht zu sehen", 0.0
    if dort == seite:
        return f"{j.champion} war vor {sek(vor)} auf deiner Seite", 0.0
    bis = max(10.0, 40.0 - vor)
    return f"{j.champion} war vor {sek(vor)} {dort} und kann in etwa {sek(bis)} {seite} sein", bis


BUFF_OBEN = {BLAU: "Blau-Buff", ROT: "Rot-Buff"}      # der Buff eines Teams auf der oberen Kartenseite
BUFF_UNTEN = {BLAU: "Rot-Buff", ROT: "Blau-Buff"}


def ward_plan(b: Bewertung, jungle, vorn: bool) -> str:
    """Wohin die Wards auf dem Weg, als Satzrest nach 'setzt du': an das Objective deiner Seite, wenn es bald
    kommt, und - bist du vorn - tief an seinen Buff auf deiner Seite, sonst an den Gank-Weg (Pixel/Tri);
    dazu, wann sein Jungler dort sein kann."""
    seite = meine_seite(b)
    if seite is None or b.partie is None:
        return ""
    feind = gegenteam(b.partie.mein_team)
    teile = []
    ob = b.objective
    if ob and 0 < ob[1] <= 150 and ((ob[0] == "drache") == (seite == "unten")):
        grube = "Drachengrube" if ob[0] == "drache" else "Baron-Grube"
        teile.append(f"ein Ward an die {grube}, denn {'die ' if ob[0] == 'larven' else 'der '}"
                     f"{OBJ_NAME[ob[0]]} {'kommen' if ob[0] == 'larven' else 'kommt'} in {sek(ob[1])}")
    buff = (BUFF_OBEN if seite == "oben" else BUFF_UNTEN)[feind]
    prog, bis = jungler_prognose(b, jungle)
    # sein Jungler war eben auf deiner Seite: nicht tief an seinen Buff (zweite Riven-Partie, 4:21 - "Ward an seinen
    # Rot-Buff: Vi war vor 1 Sekunde auf deiner Seite")
    tief_ok = vorn and not (bis == 0.0 and "auf deiner Seite" in prog)
    ziel = f"an seinen {buff}" if tief_ok else ("in den Pixel-Busch" if seite == "oben" else "in den Tri-Busch")
    teile.append(("eins " if teile else "ein Ward ") + ziel)
    satz = ", und ".join(teile)
    if prog and bis is not None and bis <= 60:
        satz += f": {prog}"
    return satz


def lane_tot_plan(b: Bewertung, jungle, sekunden: int, platten: bool) -> str:
    """Dein Lane-Gegner ist tot: Welle, Platten, back mit welchem Kauf (nur, wenn er sich lohnt), ob du vor ihm
    zurueck bist, und die Wards auf dem Rueckweg - oder, wer dich stattdessen erwischen kann."""
    n = b.lane.champion if b.lane else "Er"
    satz = f"{n} ist {sek(sekunden)} tot."
    if b.tiefe is None and b.pos is not None and b.partie is not None:
        # du bist nicht in deiner Lane (Live 21:21, 6:11: Carlos war mid) - lohnt der Weg zu deiner Welle?
        from .bewertung import LANE_DER_ROLLE, WEGFAKTOR
        lane = LANE_DER_ROLLE.get(b.ich.rolle)
        tuerme = stehende_tuerme(b.partie)
        eigene = [v for (t, l, _), v in tuerme.items() if t == b.partie.mein_team and l == lane]
        if lane and eigene:
            weg = min(abstand(b.pos, v) for v in eigene) * WEGFAKTOR / b.mein_tempo
            if weg > sekunden:
                return (f"{satz} Du bist {b.ort} - bis zu deiner Welle brauchst du {sek(weg)}, länger als er tot "
                        f"ist. Nutz die Zeit dort, wo du bist.")
            return f"{satz} Du bist {b.ort}: in {sek(weg)} bist du an deiner Welle - geh hin und schieb sie in seinen Turm."
    andere = gefahr(b)
    frisch = [x for x in andere if x.seit is not None and x.seit <= 15]
    if frisch:
        x = frisch[0]
        return f"{satz} Aber {x.champion} {_wann(x)}: schieb die Welle nur bis zum Turm."
    saetze = [satz, "Schieb die Welle in seinen Turm" + (" und nimm die Platte mit" if platten else "")]
    was, lohnt = kauf(b, b.gold)
    if lohnt:
        # Rueckweg: Welle ~10 s, Recall 8 s, Weg ~27 s - er braucht seine Todeszeit plus ~27 s
        saetze[-1] += f", dann geh back und {_kauf_verb(was)}" + (
            f" - du bist zurück, bevor {n} wieder in der Lane ist." if sekunden >= 15 else ".")
        # der Ward-Plan kommt als eigener, leiser Hinweis (rueckweg_hinweis) - sonst ~300 Zeichen am Stueck
    else:
        saetze[-1] += "."
        if andere:
            x = andere[0]
            saetze.append(f"{x.champion} ist seit {sek(x.seit or b.zeit)} nicht zu sehen - sobald {x.champion} "
                          f"auftaucht, raus.")
    return " ".join(saetze)


def rueckweg_hinweis(b: Bewertung, jungle) -> str:
    """Wohin die Wards auf dem Rueckweg - als eigener Hinweis nach dem Lane-tot-Plan, gesprochen in einer Pause."""
    vorn = b.lane is not None and b.kraft_gegen([b.lane], mit_verbuendeten=False) >= 1.3
    w = ward_plan(b, jungle, vorn)
    return f"Auf dem Rückweg setzt du {w}." if w else ""


def aufbruch(b: Bewertung, jungle, gekauft: list[str]) -> str:
    """Nach dem Einkauf im Brunnen: was die neuen Items gegen deinen Lane-Gegner bedeuten, das Kontroll-Auge,
    und wohin du gehst - zusammenhaengend statt drei einzelner Ansagen."""
    saetze = []
    g = b.lane
    if gekauft:
        was = f"{_liste(gekauft)} {'ist' if len(gekauft) == 1 else 'sind'} fertig"
        if g is not None and not g.s.tot:
            r = b.kraft_gegen([g], mit_verbuendeten=False)
            if r >= 1.6:
                was += f" - damit bist du {g.champion} klar überlegen, {kampf_kurz(b, g)}"
            elif r <= 0.75:
                was += f", aber {g.champion} ist noch stärker, {kampf_kurz(b, g)}"
        saetze.append(_gross(was) + ".")
    if 2055 not in b.ich.items and b.gold >= 75 and b.zeit >= 240:
        saetze.append("Nimm noch ein Kontroll-Auge mit.")
    lane = {"TOP": "Top", "MIDDLE": "Mid", "BOTTOM": "Bot", "UTILITY": "Bot"}.get(b.ich.rolle)
    if lane and b.prio.get(lane) == "er":
        saetze.append("Seine Welle läuft auf deinen Turm - geh direkt in die Lane.")
    else:
        vorn = g is not None and b.kraft_gegen([g], mit_verbuendeten=False) >= 1.3
        if w := ward_plan(b, jungle, vorn):
            saetze.append(f"Auf dem Weg setzt du {w}.")
    if len(saetze) < 2 and not gekauft:
        return ""
    return " ".join(saetze)


def kampf_kurz(b: Bewertung, g: GegnerLage) -> str:
    """'2 Level und 3000 Gold vorn' / '1 Level hinten' aus Level und Item-Gold."""
    lv = b.ich.level - g.s.level
    gd = b.ich.item_gold - g.s.item_gold
    vorn, hinten = [], []
    if lv:
        (vorn if lv > 0 else hinten).append(f"{abs(lv)} Level")
    if abs(gd) >= 400:
        (vorn if gd > 0 else hinten).append(_gold(gd))
    if vorn and not hinten:
        return f"{' und '.join(vorn)} vorn"
    if hinten and not vorn:
        return f"{' und '.join(hinten)} hinten"
    if vorn and hinten:
        return f"{' und '.join(vorn)} vorn, {' und '.join(hinten)} hinten"
    return "gleichauf"


# --- Champion-Wissen: der passende Konter-Tipp ----------------------------------------------------------------

TIPP_WOERTER = {
    "turm": ("Turm", "Dive", "Geschütz", "Zone"),
    "trade": ("kurz", "Trade", "ausweich", "köder", "Fenster", "CD", "Stapel", "verfehlt", "nach "),
    "jungler": ("Gank", "Kontroll", "Sicht", "R-Timer", "Tribush", "Fluss"),
    "items": ("Items:", "Heilungsreduktion", "Magieresistenz", "Rüstung"),
}


def _tipps(champion_id: str) -> list[str]:
    import re
    from pathlib import Path
    pfad = Path(__file__).resolve().parent.parent / "wissen" / "lexikon" / "champions" / f"{champion_id}.md"
    try:
        text = pfad.read_text(encoding="utf-8")
    except OSError:
        return []
    m = re.search(r"## Gegen diesen Champion\n(.*?)(\n## |\Z)", text, re.S)
    return [z[2:].strip() for z in (m.group(1) if m else "").splitlines() if z.startswith("- ")]


def tipp(champion_id: str, art: str, gesagt: set) -> str:
    """Der erste noch nicht gesagte Konter-Tipp aus dem Lexikon ("Gegen diesen Champion"), der zur Lage passt
    (Turm, Trade, Jungler, Items) - je Partie jeder nur einmal, sonst wird er zur Standardphrase."""
    woerter = TIPP_WOERTER.get(art, ())
    for t in _tipps(champion_id):
        if t in gesagt or len(t) > 170 or not any(w in t for w in woerter):
            continue
        if art != "items" and t.startswith("Items"):
            continue
        gesagt.add(t)
        return t
    return ""
