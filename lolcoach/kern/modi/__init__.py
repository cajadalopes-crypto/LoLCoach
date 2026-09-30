"""Je Modus: Kandidaten erzeugen (Buch 0, Kapitel 6.3; Feinheiten aus Buch 1 und 3).

Gemeinsam: die Back-Gruende (Buch 3, Kapitel 1), was ein Back gewinnt und was die Abwesenheit kostet (Buch 1,
Kapitel 2), wann nie gebackt wird (Buch 3, 2.2), der Rueckzug (ZURUECK, Kapitel 7.5) und Satzbausteine."""
from __future__ import annotations

from dataclasses import dataclass

from ... import bewertung, komponist
from .. import gefahr, wert
from ..handlung import Handlung, Ziel
from ..merkmale import recall_schwellen

OBEN = ("larven", "herold", "baron")
OBJ_NAME = {"drache": "Drache", "baron": "Baron", "herold": "Herold", "larven": "Larven", "aeltester": "Ältester"}
UNTEN = ("drache", "aeltester")
KONTROLLAUGE = 2055


@dataclass
class BackGrund:
    art: str          # GOLD_STUFE, GOLD_HORTEN, LEBEN, OBJECTIVE_VORLAUF, GEGNER_ZURUECK
    gewinn: float
    text: str         # der Grund mit Zahl, fuer den Satz


def liste(teile: list[str]) -> str:
    teile = [t for t in teile if t]
    # Auftrag 027, 2 (183125 4:10: "Kauf Langschwert und Langschwert"): Gleiches einmal, mit der Anzahl
    zahl = {2: "zweimal", 3: "dreimal", 4: "viermal"}
    teile = [f"{zahl[teile.count(t)]} {t}" if teile.count(t) in zahl else t for i, t in enumerate(teile)
             if t not in teile[:i]]
    return "" if not teile else teile[0] if len(teile) == 1 else ", ".join(teile[:-1]) + " und " + teile[-1]


def uhr(t: float) -> str:
    return komponist.uhr_gesprochen(t)


PUENKTLICH_S = 5.0      # so viel Vorsprung heisst "pünktlich", darunter "knapp" (E8)


def puenktlich(puffer: float) -> str:
    """E8 (Qualitaetsrunde 1): die Folge statt zwei Zahlen zum Rechnen ("naechste Welle in 28 Sekunden, du brauchst
    25"). `puffer`: Sekunden, die du vor dem Ereignis dort bist."""
    if puffer >= PUENKTLICH_S:
        return "du bist pünktlich da"
    if puffer >= 0:
        return "lauf direkt, sonst kommst du zu spät"
    return "du kommst zu spät"


def lane_von(m) -> str:
    return m.meine_lane or "Top"


def lanes_besetzt(m) -> dict[str, list[str]]:
    """Auftrag 017, 0.6 (192113 19:25 "Geh nach Top: dort kommt ihre naechste Welle", ADC und Support farmten sie):
    Lane -> lebende Mitspieler, die gerade (frisch gesehen) auf dieser Lane stehen."""
    from ...bewertung import BREITE, HOEHE
    from ..merkmale import bereich_aus
    aus: dict[str, list[str]] = {}
    ich = m.p.ich if getattr(m, "p", None) is not None else None
    for s, wo in getattr(m, "mitspieler", None) or []:
        if wo is None or s.tot or (ich is not None and s.name == ich.name):
            continue
        be = bereich_aus(wo[0] / BREITE, 1.0 - wo[1] / HOEHE, m.p.mein_team if m.p is not None else "ORDER", None)
        if be and be.startswith("lane:"):
            aus.setdefault(be.split(":", 1)[1], []).append(s.champion)
    return aus


def welle_name(m, lane: str) -> str:
    """"deine Top-Welle" nur auf deiner eigenen Lane - auf einer anderen "die Bot-Welle" (Buch 5, 3.2)."""
    return f"deine {lane}-Welle" if lane == lane_von(m) else f"die {lane}-Welle"


def objectives_meine_seite(m, lane: str | None = None) -> list:
    """Top: Larven, Herold, Baron; Bot: Drache; Mid: alle (Buch 1 3.3: "auf deiner Kartenseite"). `lane`: die Lane,
    auf der du gerade stehst (Seitenlane nach der Lane-Phase), sonst deine."""
    lane = lane or lane_von(m)
    if lane == "Top":
        return [o for o in m.objectives if o.schl in OBEN]
    if lane == "Bot":
        return [o for o in m.objectives if o.schl in UNTEN]
    return list(m.objectives)


def objective_wert(o, cfg: dict) -> float:
    return float(cfg["objective_wert"].get(o.schl, 0))


def max_hp(b) -> float:
    if b.leben_abs and b.leben:
        return b.leben_abs / b.leben
    return 600.0 + 100.0 * b.ich.level


def heil_wert(m, cfg: dict) -> float:
    b = m.b
    if b.leben is None:
        return 0.0
    return (1.0 - b.leben) * max_hp(b) * cfg["kauf"]["heil_faktor"]


def lane_im_brunnen(m) -> bool:
    return bool(getattr(m, "lane_im_brunnen", False))


def zurueck_dauer(m, cfg: dict) -> float:
    """Kanal + Einkauf + Rueckweg zur Lane (Buch 1, Kapitel 2: Abwesenheit)."""
    c = cfg["recall"]
    return c["kanal_s"] + c["einkauf_s"] + c["rueckweg_s"]


def back_gruende(m, cfg: dict) -> list[BackGrund]:
    """Buch 3, Kapitel 1: ohne Grund kein Back. Riven (Lexikon): nicht unter 800 Gold, ausser Leben unter 30 %."""
    b, c, k = m.b, cfg["recall"], m.kauf
    gold, leben = b.gold, b.leben
    schwelle, nie_unter, ausser = recall_schwellen(b.ich.champion_id)
    # Auftrag 027, 4: Welle gecrasht - Back, auch ohne Gold fuer ein ganzes Item, mit der Kauf-Kette (Bauteile);
    # nicht, wenn ein Objective in <= 20 s spawnt (ein Kampf-Event prueft der Kern, _back_vor_farmen)
    w = m.welle
    # (ist dein Gegner tot oder gebackt, sind erst die Platten dran - die Chance, Buch 15, 5)
    gecrasht = w is not None and w.zustand == "GECRASHT_BEI_IHM" and k is not None and bool(k.kaufen) \
        and not any(not o.lebt and o.spawn_in <= c.get("crash_objective_s", 20.0) for o in m.objectives or []) \
        and not (b.lane is not None and (b.lane.s.tot or lane_im_brunnen(m)))
    if nie_unter and gold < nie_unter and not (leben is not None and leben < (ausser or 0.0)) and not gecrasht:
        return []
    aus = []
    # Auftrag 028, 6.2 (134020 7:55, 12:56, 13:28, 14:01 "1000 Gold für Dornenpanzer" - das Gold kaufte mehr): der
    # Back-Ruf nennt die ganze Kette, die das Gold kauft
    kette = ""
    if k is not None and k.kaufen:
        from ...kaufplan import mit_ziel
        teile = [_akk(x) for x in k.kaufen]
        teile[0] = mit_ziel(k.kaufen[0], getattr(k, "item", None))      # Auftrag 009, 4: Bauteil mit Ziel
        kette = liste(teile)
    if gecrasht and not k.lohnt:
        aus.append(BackGrund("WELLE_GECRASHT", k.kosten * cfg["kauf"]["kauf_faktor"],
                             f"Welle ist drin, Kauf {kette}"))
    if k is not None and k.lohnt:
        g = k.kosten * cfg["kauf"]["kauf_faktor"] + (c["spike_bonus"] if k.kern_fertig else 0.0)
        aus.append(BackGrund("GOLD_STUFE", g, f"Kauf {kette}" if kette else
                             f"{gold // 50 * 50} Gold für den nächsten Kauf"))
    if gold >= c["horten_ab"]:
        g = c["horten_zuschlag"] * (gold - c["horten_ab"]) / 500.0
        if k is None or not k.lohnt:
            g += min(gold, k.kosten if k else gold) * cfg["kauf"]["kauf_faktor"]
        aus.append(BackGrund("GOLD_HORTEN", g, f"{gold // 100 * 100} Gold im Beutel"))
    if leben is not None and leben < c["leben_back"]:
        aus.append(BackGrund("LEBEN", 0.0, f"{int(round(leben * 100))} Prozent Leben"))
    zurueck = zurueck_dauer(m, cfg)
    from .. import objective as obj
    for o in objectives_meine_seite(m):
        # Buch 6, 4.1: nur ein Objective, das dich zieht, ist ein Back-Grund
        if not o.lebt and 60 <= o.spawn_in <= 100 and zurueck <= o.spawn_in and obj.zieht(m, o, cfg):
            aus.append(BackGrund("OBJECTIVE_VORLAUF", c["vorlauf_bonus"] * objective_wert(o, cfg),
                                 f"{OBJ_NAME[o.schl]} um {uhr(m.zeit + o.spawn_in)}"))
    # dein Gegner ist gebackt oder tot und deine Welle ist drin - oder laesst sich jetzt crashen (Buch 3, 4.3: "Sett ist
    # gebackt: Welle rein, Platte, dann back" - er verliert Vasallen am Turm, du backst danach ohne Verlust)
    g = b.lane
    if g is not None and (g.s.tot or lane_im_brunnen(m)) and m.welle is not None \
            and m.welle.zustand in ("GECRASHT_BEI_IHM", "ZU_IHM", "GROSS_ZU_IHM", "MITTE"):
        aus.append(BackGrund("GEGNER_ZURUECK", c["tempo_bonus"],
                             f"{g.champion} ist {'tot' if g.s.tot else 'gebackt'}"))
    # Pruefung c, R4: ein toter oder gebackter Lane-Gegner ist ein Grund fuer Platten oder Druecken - fuer einen Back
    # nur zusammen mit Gold oder Leben (173159 28:11: "Back ...: Cho'Gath ist tot")
    # Auftrag 028, 6.2: wer ohne Rueckruf kauft (Ornn, wissen/sonderregeln.toml), backt nur fuer Leben
    from ...sonderregeln import kauft_ohne_back
    if kauft_ohne_back(b.ich.champion_id):
        aus = [x for x in aus if x.art in ("LEBEN", "GEGNER_ZURUECK")]
    if not any(x.art in ("LEBEN", "GOLD_STUFE", "GOLD_HORTEN", "WELLE_GECRASHT") for x in aus):
        aus = [x for x in aus if x.art != "GEGNER_ZURUECK"]
    # der tragende Grund zuerst: Leben, dann Gold, dann Tempo
    reihe = ("LEBEN", "GOLD_STUFE", "WELLE_GECRASHT", "GOLD_HORTEN", "OBJECTIVE_VORLAUF", "GEGNER_ZURUECK")
    return sorted(aus, key=lambda x: reihe.index(x.art))


def _akk(name: str) -> str:
    from ...kaufplan import _akk as akk
    return akk(name)


def back_gewinn(m, cfg: dict, gruende: list[BackGrund]) -> float:
    """Was ein Back bringt: die Gruende + das Leben, das du im Brunnen zurueckbekommst."""
    return sum(x.gewinn for x in gruende) + heil_wert(m, cfg)


def back_grund_text(gruende: list[BackGrund], hoechstens: int = 2, vorn: str = "", woerter: int | None = None) -> str:
    """Die tragenden Gruende mit Zahl - Gold nur einmal ("1550 Gold fuer den Brutalisierer", nicht dazu noch
    "1500 Gold im Beutel"). Mit `woerter`: nur so viele Gruende, dass `vorn` + Gruende hineinpassen (Auftrag 002,
    S2.3: "Back jetzt: 850 Gold fuer den naechsten Kauf, Teemo ist tot." waren 11 Woerter) - mindestens einer."""
    teile = [x for x in gruende if not (x.art == "GOLD_HORTEN" and any(y.art == "GOLD_STUFE" for y in gruende))]
    n = hoechstens
    while woerter is not None and n > 1 and len(f"{vorn} {', '.join(x.text for x in teile[:n])}".split()) > woerter:
        n -= 1
    return ", ".join(x.text for x in teile[:n])


def kuerze(satz: str, woerter: int) -> str:
    """Auftrag 002, S2.3: ein Satz ueber der Grenze verliert zuerst den Grund hinter dem letzten Doppelpunkt ("Kauf X,
    dann zur Top-Welle: dort nimmt sie sonst niemand." -> "Kauf X, dann zur Top-Welle.") - das Wichtigste steht vorn.
    Nur, wenn davor mehr als ein Vorsatz bleibt ("Noch 8 Sekunden:" allein ist kein Satz)."""
    while len(satz.split()) > woerter and ": " in satz:
        kopf = satz.rsplit(": ", 1)[0]
        rest = kopf.split(": ", 1)[1] if kopf.startswith("Noch ") and ": " in kopf else kopf
        if kopf.startswith("Du lebst in "):          # Auftrag 027, 2: 091311 15:17 blieb nur "Du lebst in 3 Sekunden."
            rest = kopf.split(": ", 1)[1] if ": " in kopf else ""
        if len(rest.split()) < 3:
            break
        satz = kopf.rstrip(".,;") + "."
    return satz


def abwesenheit(m, cfg: dict, zustand: str) -> float:
    """Buch 1, Kapitel 2: Wellen, die waehrend deiner Abwesenheit an deinem Turm ankommen. Gecrasht: die erste zaehlt
    halb (Bounce); LEER: nichts; Mitte/zu ihm: voll; zu dir: voll, der Stapel mindestens, + gross_zuschlag."""
    w = m.welle
    ww = wert.wellenwert(m.zeit, cfg)
    n = zurueck_dauer(m, cfg) / wert.wellentakt(m.zeit)
    if zustand == "LEER":
        return 0.0
    if zustand == "GECRASHT_BEI_IHM":
        return ww * max(0.0, n - 0.5)
    if zustand in ("ZU_DIR", "GROSS_ZU_DIR", "GECRASHT_BEI_DIR"):
        ihre = (w.ihre if w is not None and w.ihre is not None else 6)
        return max(ww * n, ww * ihre / 6.0) + (cfg["welle"]["gross_zuschlag"] if ihre > 6 else 0.0)
    return ww * n


def kanal_reicht(rest_s: float, erster_s: float | None, rand_s: float = 1.0) -> bool:
    """Auftrag 009, 2.3 (Teil 0 aus 008): reicht der Recall-Kanal (noch `rest_s`), bevor der erste Gegner da ist
    (`erster_s`, None = keiner bekannt)? Gewarnt wird nur, wenn er vor Kanal-Ende + `rand_s` bei dir sein kann."""
    return erster_s is None or erster_s > rest_s + rand_s


def nie_back(m, cfg: dict) -> str | None:
    """Buch 3, 2.2: nie back in KAMPF, mit einem sichtbaren Gegner in 1500, der dich im Kanal erreicht, oder kurz vor
    einem Objective auf deiner Seite, wenn du voll bist. Rueckgabe: der Grund, sonst None."""
    b, c = m.b, cfg["recall"]
    if m.im_kampf:
        return "Kampf"
    for g in b.gegner:
        # eben noch gesehen zaehlt wie sichtbar (140253 8:04: Yasuo 935 entfernt, im Takt davor zu sehen - "Back jetzt",
        # dann kamen Brand und Yasuo; Pruefung D2)
        eben = g.sichtbar or (g.seit is not None and g.seit <= NIE_BACK_EBEN_S)
        if eben and not g.s.tot and g.abstand is not None and g.abstand <= c["nie_back_gegner_abstand"] \
                and (g.kommt_naeher or not g.sichtbar or (g.ankunft is not None and g.ankunft <= c["kanal_s"])):
            return f"{g.champion} erreicht dich im Kanal"
    return nie_back_objective(m, cfg)


def nie_back_objective(m, cfg: dict) -> str | None:
    """Der Objective-Teil von nie_back: du bist voll, und ein Objective, das dich zieht (Buch 6, 4.1), spawnt auf deiner
    Seite in < 40 s. Er gilt auch fuer WELLE_REIN_UND_BACK - der Back laege mitten im Objective."""
    b, c = m.b, cfg["recall"]
    if b.leben is not None and b.leben >= c["voll_ab"]:
        from .. import objective as obj
        for o in objectives_meine_seite(m):
            if not o.lebt and o.spawn_in < 40 and obj.zieht(m, o, cfg):
                return f"{OBJ_NAME[o.schl]} in {int(o.spawn_in)} Sekunden"
    return None


SICHER_DORT_S = 4.0     # so nah am sicheren Ort stehst du schon dort
NIE_BACK_EBEN_S = 3.0   # so lange nach der letzten Sichtung zaehlt ein naher Gegner fuer nie_back wie sichtbar


def am_sicheren_ort(m) -> bool:
    """Du stehst am sicheren Ort (<= SICHER_DORT_S). Pruefung A / Buch 0, 7.5 (Nachtrag Qualitaetsrunde 1): eine Gefahr,
    deren sicherer Ort dein aktueller Ort ist, wird nicht gesagt - der Plan haelt."""
    if m.b is None:
        return False
    _, weg = m.b.sicherer_ort()
    return weg is not None and weg <= SICHER_DORT_S


def lane_kraft(b) -> float:
    """Wer die Lane haelt, ohne das Leben dieses Moments: Level, Items (je 600 Gold ~ ein Level), Stufe 6 - die Teile
    von Bewertung.kraefte, die eine Minute halten. Qualitaetsrunde 2, G1: mit Leben und Ult sprang die Kraft beim
    Respawn von -4 auf +1,9, und der Plan fuer die verlorene Lane begann alle paar Sekunden neu (144655)."""
    g = b.lane if b is not None else None
    if g is None:
        return 0.0
    wert = float(-g.level_vorsprung)
    gd = -g.gold_vorsprung
    if abs(gd) >= 400:
        wert += gd / 600
    if b.ich.level >= 6 > g.s.level:
        wert += 1.5
    elif g.s.level >= 6 > b.ich.level:
        wert -= 1.5
    return wert


def lane_verloren(m) -> tuple[bool, int]:
    """Pruefung A: die Lane ist gegen dich - Kraft <= -1 gegen den Lane-Gegner oder zwei Tode gegen ihn. Kraft ohne
    das Leben dieses Moments (lane_kraft, Qualitaetsrunde 2). Rueckgabe: (verloren, Tode gegen ihn)."""
    b = m.b
    g = b.lane if b is not None else None
    if g is None or m.p is None or m.p.ich is None:
        return False, 0
    ich = m.p.ich.name
    tode = sum(1 for e in m.p.kills_von("ChampionKill")
               if e.opfer is not None and e.opfer.name == ich and e.taeter is not None and e.taeter.name == g.s.name)
    return lane_kraft(b) <= -1.0 or tode >= 2, tode


def wer_kommt(h: Handlung, schwelle: float = 0.05) -> list[str]:
    return [n for n, x in h.daten.get("wer", []) if x >= schwelle]


def zurueck(m, cfg: dict, modus: str, gruende: list[BackGrund]) -> list[Handlung]:
    """ZURUECK (Kapitel 7.5): zum sicheren Ort mit der kuerzesten Laufzeit - dein Turm, die Basis oder deine Gruppe.
    Zwei Fassungen: nur raus - und, mit einem Back-Grund, erst raus, dann back (Buch 3, 2.2); der Kern behaelt die
    bessere. Der Kanal danach am sicheren Ort zaehlt mit (`danach_kanal`)."""
    b, c = m.b, cfg["recall"]
    ort, weg = b.sicherer_ort()
    dort = weg is not None and weg <= SICHER_DORT_S     # stehst du schon dort, wird nichts gesagt (Pruefung A)
    weg = max(2.0, weg if weg is not None else 8.0)
    w = m.welle
    z = w.zustand if w is not None else "UNBEKANNT"
    vorn = z in ("ZU_IHM", "GROSS_ZU_IHM", "MITTE", "GECRASHT_BEI_IHM")
    aus = []
    for mit_back in ([False, True] if gruende else [False]):
        if mit_back:
            gew = back_gewinn(m, cfg, gruende)
            kosten = abwesenheit(m, cfg, z) if m.meine_lane and modus == "LANE" else 0.0
            schritte = [f"zurück zu {ort}", "back"]
            dauer = weg + c["kanal_s"] + c["einkauf_s"]
        else:
            gew, schritte, dauer = 0.0, [f"zurück zu {ort}"], weg
            kosten = 0.5 * wert.wellenwert(m.zeit, cfg) if vorn and modus == "LANE" else 0.0
        # stehst du schon dort ("Bleib an ..."), laeufst du nicht weg: das Risiko gilt ueber das normale Fenster
        dort = weg <= 4.0
        h = Handlung("ZURUECK", Ziel("ort", ort, None, weg), modus, dauer, gewinn=gew, kosten=kosten,
                     gefahr_t=max(weg, cfg["gefahr"]["fenster_s"]) if dort else weg,
                     schutz=1.0 if dort else cfg["gefahr"]["rueckzug_faktor"], schritte=schritte)
        h.daten.update(nur_bei_gefahr=True, ort=ort, gruende=[x.text for x in gruende] if mit_back else [],
                       dort=dort)
        if mit_back:
            h.schritt_saetze[1] = "Jetzt back: " + back_grund_text(gruende, 1) + "."
            h.daten.update(folge_art={1: "BACK_JETZT"}, danach_kanal=c["kanal_s"])
        h.erfuellt = _am_sicheren_ort
        aus.append(h)
    return aus


def _am_sicheren_ort(m, plan) -> bool:
    """ZURUECK, Schritt "zurueck": du bist am sicheren Ort (<= 3 s). Mit Back danach erst, wenn dich kein sichtbarer
    Gegner im Kanal erreicht (Buch 3, 2.2; Pruefung D: 140253 8:06 "Jetzt back", Brand und Yasuo kamen)."""
    if plan.schritt != 0 or m.b is None:
        return False
    _, weg = m.b.sicherer_ort()
    if weg is None or weg > 3.0:
        return False
    if plan.handlung.daten.get("folge_art"):
        from .. import konfig
        return nie_back(m, konfig()) is None
    return True


GEFAHR_WOERTER = 8          # Buch 0, 9.3 (Auftrag 002, S2.3) - wie [sprechen] max_woerter_gefahr
_ZAHL = {2: "zwei", 3: "drei"}


def zurueck_saetze(h: Handlung, m=None, bleiben: Handlung | None = None) -> None:
    """Satz fuer ZURUECK (GEFAHR: hoechstens 8 Woerter, die Handlung zuerst). Der Grund ist, wer dich toetet, wenn du
    BLEIBST (`bleiben` = FARMEN) - nicht das kleine Restrisiko des Rueckzugs selbst (094832, 4:54: "Raus ...: du hast
    100 Prozent Leben", waehrend Swain auf Riven zulief). Stehst du schon fast dort: "Bleib an ..."."""
    quelle = bleiben if bleiben is not None else h
    wer = wer_kommt(quelle) or wer_kommt(quelle, 0.01)[:2]
    ort = h.daten["ort"]
    # Auftrag 008, A2: "Zurueck unter deinen Mid-Turm" - mit Besitzer, ohne "Tier" (vorher "Raus zum Mid-Tier-1-Turm",
    # 101426 32:07: "Raus zum Turm ist schwammig - zu meinem Tier 1?")
    from ..sprache import an, unter
    raus = f"Zurück {unter(ort)}"
    # Auftrag 010, 3 (101426 23:35, Kritik 009: "Zurueck unter deinen inneren Mid-Turm" auf der Bot-Lane las sich wie
    # ein Fehler): liegt der sichere Ort an einer anderen Lane, nennt der Satz den Ausgangspunkt
    import re as _re
    hier = getattr(m, "lane_hier", None) if m is not None else None
    ziel_lane = _re.search(r"\b(Top|Mid|Bot)-", ort)
    if hier and ziel_lane and ziel_lane.group(1) != hier:
        raus = f"Von der {hier}-Lane zurück zu {ort}"
    leben = m.leben if m is not None else None
    if wer:
        h.grund = f"{liste(wer[:3])} {'kommt' if len(wer) == 1 else 'kommen'}"
        # Auftrag 002, S2.3: GEFAHR hoechstens 8 Woerter - sonst wird gezaehlt ("Raus zu deinem Mid-Tier-1-Turm: Zac,
        # Gwen und Xin Zhao kommen." waren 10)
        n = min(len(wer), 3)
        for grund in (h.grund, f"{_ZAHL.get(n, n)} von ihnen kommen", f"{_ZAHL.get(n, n)} kommen"):
            h.grund = grund
            if len(f"{raus}: {grund}.".split()) <= GEFAHR_WOERTER or n == 1:
                break
    elif h.daten["gruende"]:
        h.grund = h.daten["gruende"][0]
    else:
        h.grund = f"du hast {int(round(leben * 100))} Prozent Leben" if leben is not None else "zu viel Risiko"
    h.daten["gefahr_von"] = wer[:3]
    weg = h.ziel.weg if h.ziel is not None else None
    if weg is not None and weg <= 4:
        h.satz = f"Bleib {an(ort)}: {h.grund}."
    else:
        h.satz = f"{raus}: {h.grund}."


def satz_kurz(text: str, woerter: int) -> str:
    """Hoechstens `woerter` Woerter (Kapitel 9.3) - schneidet am Komma, sonst hart."""
    teile = text.split()
    if len(teile) <= woerter:
        return text
    kurz = " ".join(teile[:woerter]).rstrip(",;:")
    return kurz if kurz.endswith((".", "!", "?")) else kurz + "."


def gegner_fenster(g, m) -> float | None:
    """Sekunden, bis dein Lane-Gegner zurueck sein kann: tot -> Respawn + Weg; im Brunnen / weit -> Ankunft."""
    if g is None:
        return None
    if g.s.tot:
        return g.s.respawn + gefahr._weg_vom_brunnen(g, m)
    return g.ankunft


def turm_ihr_name(m, lane: str | None = None) -> str:
    """'den äußeren Top-Turm' - sein vorderster stehender Turm dieser Lane (sonst deiner)."""
    lane = lane or lane_von(m)
    p = m.p
    if p is not None and p.mein_team:
        from ...zustand import gegenteam
        st = bewertung.stehende_tuerme(p)
        feind = gegenteam(p.mein_team)
        k = next(((feind, lane, s) for s in bewertung.TIER if (feind, lane, s) in st), None)
        if k is not None:
            return bewertung.TURM_DE[k[2]].format(lane=lane)
    return bewertung.TURM_DE["aussen"].format(lane=lane)
