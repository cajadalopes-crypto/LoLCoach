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
OBJ_NAME = {"drache": "Drache", "baron": "Baron", "herold": "Herold", "larven": "Larven"}
KONTROLLAUGE = 2055


@dataclass
class BackGrund:
    art: str          # GOLD_STUFE, GOLD_HORTEN, LEBEN, OBJECTIVE_VORLAUF, GEGNER_ZURUECK
    gewinn: float
    text: str         # der Grund mit Zahl, fuer den Satz


def liste(teile: list[str]) -> str:
    teile = [t for t in teile if t]
    return "" if not teile else teile[0] if len(teile) == 1 else ", ".join(teile[:-1]) + " und " + teile[-1]


def uhr(t: float) -> str:
    return komponist.uhr_gesprochen(t)


def lane_von(m) -> str:
    return m.meine_lane or "Top"


def objectives_meine_seite(m) -> list:
    """Top: Larven, Herold, Baron; Bot: Drache; Mid: alle (Buch 1 3.3: "auf deiner Kartenseite")."""
    lane = lane_von(m)
    if lane == "Top":
        return [o for o in m.objectives if o.schl in OBEN]
    if lane == "Bot":
        return [o for o in m.objectives if o.schl == "drache"]
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
    if nie_unter and gold < nie_unter and not (leben is not None and leben < (ausser or 0.0)):
        return []
    aus = []
    if k is not None and k.lohnt:
        teil = k.kaufen[0] if k.kaufen else "den nächsten Kauf"
        g = k.kosten * cfg["kauf"]["kauf_faktor"] + (c["spike_bonus"] if k.kern_fertig else 0.0)
        aus.append(BackGrund("GOLD_STUFE", g, f"{gold // 50 * 50} Gold für {_akk(teil)}"))
    if gold >= c["horten_ab"]:
        g = c["horten_zuschlag"] * (gold - c["horten_ab"]) / 500.0
        if k is None or not k.lohnt:
            g += min(gold, k.kosten if k else gold) * cfg["kauf"]["kauf_faktor"]
        aus.append(BackGrund("GOLD_HORTEN", g, f"{gold // 100 * 100} Gold im Beutel"))
    if leben is not None and leben < c["leben_back"]:
        aus.append(BackGrund("LEBEN", 0.0, f"{int(round(leben * 100))} Prozent Leben"))
    zurueck = zurueck_dauer(m, cfg)
    for o in objectives_meine_seite(m):
        if not o.lebt and 60 <= o.spawn_in <= 100 and zurueck <= o.spawn_in:
            aus.append(BackGrund("OBJECTIVE_VORLAUF", c["vorlauf_bonus"] * objective_wert(o, cfg),
                                 f"{OBJ_NAME[o.schl]} um {uhr(m.zeit + o.spawn_in)}"))
    # dein Gegner ist gebackt oder tot und deine Welle ist drin - oder laesst sich jetzt crashen (Buch 3, 4.3: "Sett ist
    # gebackt: Welle rein, Platte, dann back" - er verliert Vasallen am Turm, du backst danach ohne Verlust)
    g = b.lane
    if g is not None and (g.s.tot or lane_im_brunnen(m)) and m.welle is not None \
            and m.welle.zustand in ("GECRASHT_BEI_IHM", "ZU_IHM", "GROSS_ZU_IHM", "MITTE"):
        aus.append(BackGrund("GEGNER_ZURUECK", c["tempo_bonus"],
                             f"{g.champion} ist {'tot' if g.s.tot else 'gebackt'}"))
    # der tragende Grund zuerst: Leben, dann Gold, dann Tempo
    reihe = ("LEBEN", "GOLD_STUFE", "GOLD_HORTEN", "OBJECTIVE_VORLAUF", "GEGNER_ZURUECK")
    return sorted(aus, key=lambda x: reihe.index(x.art))


def _akk(name: str) -> str:
    from ...kaufplan import _akk as akk
    return akk(name)


def back_gewinn(m, cfg: dict, gruende: list[BackGrund]) -> float:
    """Was ein Back bringt: die Gruende + das Leben, das du im Brunnen zurueckbekommst."""
    return sum(x.gewinn for x in gruende) + heil_wert(m, cfg)


def back_grund_text(gruende: list[BackGrund], hoechstens: int = 2) -> str:
    """Die tragenden Gruende mit Zahl - Gold nur einmal ("1550 Gold fuer den Brutalisierer", nicht dazu noch
    "1500 Gold im Beutel")."""
    teile = [x for x in gruende if not (x.art == "GOLD_HORTEN" and any(y.art == "GOLD_STUFE" for y in gruende))]
    return ", ".join(x.text for x in teile[:hoechstens])


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


def nie_back(m, cfg: dict) -> str | None:
    """Buch 3, 2.2: nie back in KAMPF, mit einem sichtbaren Gegner in 1500, der dich im Kanal erreicht, oder kurz vor
    einem Objective auf deiner Seite, wenn du voll bist. Rueckgabe: der Grund, sonst None."""
    b, c = m.b, cfg["recall"]
    if m.im_kampf:
        return "Kampf"
    for g in b.gegner:
        if g.sichtbar and not g.s.tot and g.abstand is not None and g.abstand <= c["nie_back_gegner_abstand"] \
                and (g.kommt_naeher or (g.ankunft is not None and g.ankunft <= c["kanal_s"])):
            return f"{g.champion} erreicht dich im Kanal"
    if b.leben is not None and b.leben >= c["voll_ab"]:
        for o in objectives_meine_seite(m):
            if not o.lebt and o.spawn_in < 40:
                return f"{OBJ_NAME[o.schl]} in {int(o.spawn_in)} Sekunden"
    return None


def wer_kommt(h: Handlung, schwelle: float = 0.05) -> list[str]:
    return [n for n, x in h.daten.get("wer", []) if x >= schwelle]


def zurueck(m, cfg: dict, modus: str, gruende: list[BackGrund]) -> list[Handlung]:
    """ZURUECK (Kapitel 7.5): zum sicheren Ort mit der kuerzesten Laufzeit - dein Turm, die Basis oder deine Gruppe.
    Zwei Fassungen: nur raus - und, mit einem Back-Grund, erst raus, dann back (Buch 3, 2.2); der Kern behaelt die
    bessere. Der Kanal danach am sicheren Ort zaehlt mit (`danach_kanal`)."""
    b, c = m.b, cfg["recall"]
    ort, weg = b.sicherer_ort()
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
        h = Handlung("ZURUECK", Ziel("ort", ort, None, weg), modus, dauer, gewinn=gew, kosten=kosten, gefahr_t=weg,
                     schutz=cfg["gefahr"]["rueckzug_faktor"], schritte=schritte)
        h.daten.update(nur_bei_gefahr=True, ort=ort, gruende=[x.text for x in gruende] if mit_back else [])
        if mit_back:
            h.schritt_saetze[1] = "Jetzt back: " + back_grund_text(gruende, 1) + "."
            h.daten.update(folge_art={1: "BACK_JETZT"}, danach_kanal=c["kanal_s"])
        h.erfuellt = _am_sicheren_ort
        aus.append(h)
    return aus


def _am_sicheren_ort(m, plan) -> bool:
    """ZURUECK, Schritt "zurueck": du bist am sicheren Ort (<= 3 s)."""
    if plan.schritt != 0 or m.b is None:
        return False
    _, weg = m.b.sicherer_ort()
    return weg is not None and weg <= 3.0


def zurueck_saetze(h: Handlung, m=None, bleiben: Handlung | None = None) -> None:
    """Satz fuer ZURUECK (GEFAHR: hoechstens 10 Woerter, die Handlung zuerst). Der Grund ist, wer dich toetet, wenn du
    BLEIBST (`bleiben` = FARMEN) - nicht das kleine Restrisiko des Rueckzugs selbst (094832, 4:54: "Raus ...: du hast
    100 Prozent Leben", waehrend Swain auf Riven zulief). Stehst du schon fast dort: "Bleib an ..."."""
    quelle = bleiben if bleiben is not None else h
    wer = wer_kommt(quelle) or wer_kommt(quelle, 0.01)[:2]
    ort = h.daten["ort"]
    leben = m.leben if m is not None else None
    if wer:
        h.grund = f"{liste(wer[:3])} {'kommt' if len(wer) == 1 else 'kommen'}"
    elif h.daten["gruende"]:
        h.grund = h.daten["gruende"][0]
    else:
        h.grund = f"du hast {int(round(leben * 100))} Prozent Leben" if leben is not None else "zu viel Risiko"
    h.daten["gefahr_von"] = wer[:3]
    weg = h.ziel.weg if h.ziel is not None else None
    if weg is not None and weg <= 4:
        praep = "an" if ort.startswith("deinem") else "in" if ort.startswith("deiner") else "bei"
        h.satz = f"Bleib {praep} {ort}: {h.grund}."
    else:
        h.satz = f"Raus zu {ort}: {h.grund}."


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


def turm_ihr_name(m) -> str:
    """'den äußeren Top-Turm' - sein vorderster stehender Turm deiner Lane."""
    lane = lane_von(m)
    p = m.p
    if p is not None and p.mein_team:
        from ...zustand import gegenteam
        st = bewertung.stehende_tuerme(p)
        feind = gegenteam(p.mein_team)
        k = next(((feind, lane, s) for s in bewertung.TIER if (feind, lane, s) in st), None)
        if k is not None:
            return bewertung.TURM_DE[k[2]].format(lane=lane)
    return bewertung.TURM_DE["aussen"].format(lane=lane)
