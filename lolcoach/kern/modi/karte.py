"""Die Karten-Rechnung nach der Lane-Phase (Buch 5, Kapitel 2 und 8): ein Ziel waehlen.

    EV(z) = gewinn(z) * p_erfolg - weg(z) * zeitwert - p_tod(weg + dauer) * todeskosten + folgewert(z)

Gemeinsam fuer SEITE, GRUPPE, UNTERWEGS und VERTEIDIGEN: Tuerme druecken (DRUECKEN allein, MIT_GRUPPE mit dem
Team), Seitenwellen holen, zur Gruppe / per TP in einen Kampf, Welle rein und rotieren, Umwandeln nach einem
gewonnenen Kampf. Ob ein Turm erreichbar ist, sagt die Ankunft der Verteidiger (Tote: Respawn + Weg aus ihrem
Brunnen; gesehen <= 15 s: Weg / Tempo - seit; aelter: unbekannt) - wie bewertung.verteidiger_ab, aber je Gegner."""
from __future__ import annotations

from dataclasses import dataclass

from ... import bewertung
from ...bewertung import BRUNNEN, TIER, TURM_DE, TUERME, WEGFAKTOR, abstand
from ...zustand import BLAU, ROT, gegenteam, struktur
from .. import wert
from ..handlung import Handlung, Ziel
from . import OBJ_NAME, liste, puenktlich, uhr, welle_name

ZUM = {"drache": "zum Drachen", "baron": "zum Baron", "herold": "zum Herold", "larven": "zu den Larven",
       "aeltester": "zum Ältesten"}
GRUBE_WORT = {"grube:drache": "zum Drachen", "grube:baron": "zum Baron"}


@dataclass
class TurmZiel:
    team: str
    lane: str
    stufe: str               # aussen / innen / Inhib
    pos: tuple[float, float]
    name: str                # "den inneren Top-Turm"
    weg: float
    ankunft: list            # [(GegnerLage, Sekunden bis dort)] - bekannte Verteidiger
    unbekannt: int


def _teams(m) -> tuple[str, str]:
    mein = m.p.mein_team if m.p is not None else "ORDER"
    return mein, gegenteam(mein)


def verteidiger(m, ziel: tuple[float, float]) -> tuple[list, int]:
    """Je Gegner die Ankunft an `ziel` (Buch 0 4.2 `fenster_gegner`, je Gegner): [(GegnerLage, s)], Unbekannte."""
    _, feind = _teams(m)
    aus, unbekannt = [], 0
    for g in m.b.gegner:
        if g.s.tot:
            aus.append((g, g.s.respawn + abstand(BRUNNEN[feind], ziel) * WEGFAKTOR / 380.0))
        elif g.pos is None or g.seit is None or g.seit > 15:
            unbekannt += 1
        else:
            aus.append((g, max(0.0, abstand(g.pos, ziel) * WEGFAKTOR / (g.tempo or 350.0) - g.seit)))
    return sorted(aus, key=lambda x: x[1]), unbekannt


def turm_ziele(m) -> list[TurmZiel]:
    """Ihr vorderster stehender Turm je Lane, mit deinem Weg und den Verteidigern."""
    if m.p is None or m.pos is None:
        return []
    _, feind = _teams(m)
    stehen = bewertung.stehende_tuerme(m.p)
    aus = []
    for lane in ("Top", "Mid", "Bot"):
        k = next(((feind, lane, st) for st in TIER if (feind, lane, st) in stehen), None)
        if k is None:
            continue
        pos = TUERME[k]
        ank, unb = verteidiger(m, pos)
        aus.append(TurmZiel(feind, lane, k[2], pos, TURM_DE[k[2]].format(lane=lane), m.weg(pos) or 0.0, ank, unb))
    return aus


# Hinter den Inhibitor-Tuermen (Kapitel 8, Punkte 1 und 2) - Spiel-Einheiten der Karte, wie TUERME
INHIBITOREN = {(BLAU, "Top"): (1171, 3571), (BLAU, "Mid"): (3203, 3208), (BLAU, "Bot"): (3452, 1236),
               (ROT, "Top"): (11261, 13676), (ROT, "Mid"): (11598, 11667), (ROT, "Bot"): (13604, 11316)}
NEXUS_TUERME = {BLAU: ((1748, 2270), (2177, 1807)), ROT: ((12611, 13084), (13052, 12612))}
NEXUS = {BLAU: (1551, 1660), ROT: (13604, 13566)}
NEXUS_TURM_ZURUECK = 180.0     # s: Nexus-Tuerme stehen wieder auf (saison2026.md: mit 40 % Leben)
HINTEN = ("Inhibitor", "Nexus-Turm", "Nexus")


def inhibs_offen(p, team: str) -> list[str]:
    """Lanes, deren Inhibitor von `team` gerade fehlt (300 s, bewertung.INHIB_ZURUECK)."""
    return [st.lane for e in p.kills_von("InhibKilled")
            if (st := struktur(e.daten.get("InhibKilled", ""))) and st.team == team
            and p.zeit - e.zeit < bewertung.INHIB_ZURUECK]


def nexus_tuerme_weg(p, team: str) -> int:
    """Wie viele Nexus-Tuerme von `team` gerade fehlen (die API nennt beide Mid, Stufe P4/P5)."""
    return min(2, sum(1 for e in p.kills_von("TurretKilled")
                      if (st := struktur(e.daten.get("TurretKilled", ""))) and st.team == team
                      and st.stufe == "Nexus" and p.zeit - e.zeit < NEXUS_TURM_ZURUECK))


def hinten_ziele(m) -> list[TurmZiel]:
    """Kapitel 8, Punkte 1 und 2: der Inhibitor, dessen Turm gefallen ist; die Nexus-Tuerme, wenn ein Inhibitor offen
    ist; der Nexus, wenn beide fehlen."""
    if m.p is None or m.pos is None:
        return []
    _, feind = _teams(m)
    stehen = bewertung.stehende_tuerme(m.p)
    offen = inhibs_offen(m.p, feind)
    orte = [(lane, "Inhibitor", INHIBITOREN[(feind, lane)], f"den {lane}-Inhibitor") for lane in ("Top", "Mid", "Bot")
            if (feind, lane, "Inhib") not in stehen and lane not in offen]
    if offen:
        if nexus_tuerme_weg(m.p, feind) < 2:
            orte.append(("Mid", "Nexus-Turm", min(NEXUS_TUERME[feind], key=lambda q: m.weg(q) or 0.0), "den Nexus-Turm"))
        else:
            orte.append(("Mid", "Nexus", NEXUS[feind], "den Nexus"))
    aus = []
    for lane, stufe, pos, name in orte:
        ank, unb = verteidiger(m, pos)
        aus.append(TurmZiel(feind, lane, stufe, pos, name, m.weg(pos) or 0.0, ank, unb))
    return aus


def steht(m, turm: tuple, vorher: int = 0) -> bool:
    """Steht diese Struktur noch? (Bestaetigung \"Sauber umgewandelt\"; `vorher`: fehlende Nexus-Tuerme beim Plan.)"""
    team, lane, stufe = turm
    if stufe == "Inhibitor":
        return lane not in inhibs_offen(m.p, team)
    if stufe == "Nexus-Turm":
        return nexus_tuerme_weg(m.p, team) <= vorher
    if stufe == "Nexus":
        return True           # faellt er, ist die Partie vorbei
    return turm in bewertung.stehende_tuerme(m.p)


def turm_dauer(z: TurmZiel, c: dict, mit: int = 0) -> float:
    """Wie lange der Turm steht: grob je Stufe allein (turm_dauer_s), mit Mitspielern schneller. Inhibitor und Nexus
    (nicht im Buch) wie ein Nexus-Turm."""
    stufe = "nexus" if z.stufe in HINTEN else z.stufe
    return c["turm_dauer_s"][stufe] * (c["gruppe_turm_faktor"] ** mit)


def turm_gewinn(z: TurmZiel, m, cfg: dict) -> float:
    """Platten (bis zum Turmfall) + Turmgold fuer das Team + Kartenzugang; der Inhibitor-Turm oeffnet den Inhibitor
    (halber Wert)."""
    g = wert._mechanik()["gold"]
    c = cfg["mitte"]
    ow = cfg["objective_wert"]
    if z.stufe in HINTEN:
        # nicht im Buch: ein Nexus-Turm ist einer von zwei Riegeln vor dem Nexus - ein Viertel davon plus Kartenzugang
        return {"Inhibitor": ow["inhibitor"], "Nexus-Turm": ow["turm_extra"] + 0.25 * ow["nexus"],
                "Nexus": ow["nexus"]}[z.stufe]
    # Platten 2026 an jedem Turm, auch innen und am Inhibitor (saison2026.md, Patch 26.1); die aeusseren hat die
    # Lane-Phase angeknabbert, die hinteren stehen meist noch ganz
    platten = g["platten_je_turm"]
    if z.stufe == "aussen":
        platten = (m.b.platten_gegner if z.lane == m.meine_lane and m.b.platten_gegner is not None
                   else c["platten_annahme"])
    global_ = {"aussen": g["turm_aussen"], "innen": g["turm_innen"], "Inhib": g["turm_inhib"]}[z.stufe] * 5
    extra = cfg["objective_wert"]["turm_extra"] + (0.5 * cfg["objective_wert"]["inhibitor"] if z.stufe == "Inhib" else 0)
    gewinn = platten * wert.platte_gold(m.zeit) + global_ + extra
    # unberuehrte Tuerme bauen Kristalle auf (Kapitel 1, 2026): sichtbar nur am aeusseren Turm deiner Lane - alle
    # Platten stehen noch; sonst weiss der Coach es nicht und rechnet ohne
    if z.stufe == "aussen" and z.lane == m.meine_lane and m.b.platten_gegner == 5:
        gewinn *= c["kristall_faktor"]
    return gewinn


def rechtzeitig(z: TurmZiel, bis: float) -> list:
    return [g for g, t in z.ankunft if t <= bis]


def ernste(m, gegen: list, ort, bis: float) -> list:
    """Die, die wahrscheinlich wirklich kommen: sichtbar dort oder p_da >= 0,5 bis `bis` an `ort` (Schritt 5)."""
    from .. import gefahr, konfig
    return [g for g in gegen if gefahr.p_da_am(g, bis, m, konfig()["gefahr"], ort) >= 0.5]


def schlaegt(m, gegen: list, c: dict, ort=None, bis: float | None = None) -> bool:
    """Du (mit Mitspielern) schlaegst die, die rechtzeitig kommen. Ist es genau die Antwort der Seite, zaehlt ihre
    gemessene Kraft (Buch 5, 3.1). Mit `ort` (seit Schritt 5): kommen ZWEI oder mehr wahrscheinlich (sichtbar dort
    oder p_da >= 0,5 bis `bis`), entscheidet kampf.p_gewinn dort mit dem Turm - EIN Kampfmodell (Buch 7, 1.4), alle,
    die bis zum Ende dort sein koennen (Buch 6, 1.2) - statt kraft_gegen gegen den ersten (102112 34:51: "Geh auf den
    Mid-Inhibitor-Turm", waehrend Sett, Kai'Sa und Fiddlesticks dort respawnten). Kommt nur einer, gilt Buch 5 wie
    bisher. Die Schwelle bleibt split_kraft_min, als Kraftverhaeltnis in p umgerechnet (1,2 -> 0,59)."""
    if not gegen:
        return True
    if ort is not None and len(gegen) >= 2:
        from .. import kampf, konfig
        cfg = konfig()
        T = bis if bis is not None else cfg["kampf"]["fenster_s"]
        ernst = ernste(m, gegen, ort, T)
        if len(ernst) >= 2:
            k = cfg["kampf"]["k"]
            p_min = c["split_kraft_min"] ** k / (1.0 + c["split_kraft_min"] ** k)
            # gewichtet wie ueberall (sichtbar dort 1, sonst p_da); auf eurer Seite "du, mit Mitspielern in 1500" wie in
            # Buch 5 - nicht jeder, der in weg + dauer irgendwo hinkaeme (102112 25:25: "Top-Inhibitor-Turm jetzt: du
            # schlaegst die drei", 39 s ueber die Karte, gezaehlt mit dem ganzen Team)
            nah = {s.name for s in (getattr(m.b, "mitspieler_nah", None) or [])}
            p, _ = kampf.p_gewinn(m, ort, T, cfg=cfg, mitspieler_nur=nah)
            return p >= p_min
        gegen = ernst[:1] or gegen[:1]
    gegen = gegen[:1] if ort is not None else gegen
    if len(gegen) == 1 and m.antwort is not None and gegen[0].s.name == m.antwort.s.name and m.antwort_kraft is not None:
        return m.antwort_kraft >= c["split_kraft_min"]
    return m.b.kraft_gegen(gegen) >= c["split_kraft_min"]


def dahinter(z: TurmZiel, m, cfg: dict, mit: int, ab: float) -> float:
    """folgewert eines Turms im Umwandel-Fenster (Kapitel 2 und 8): faellt er nach `ab` Sekunden, oeffnet er den
    naechsten derselben Lane - der zaehlt mit, wenn auch er vor seinem ersten Verteidiger faellt (36:32: erst der
    aeussere Mid-Turm vor dir, dann der innere, statt quer ueber die Karte zu einem inneren)."""
    if z.stufe not in TIER:
        return 0.0
    stufe = next((s for s, i in TIER.items() if i == TIER[z.stufe] + 1), None)
    k = (z.team, z.lane, stufe)
    if stufe is None or k not in bewertung.stehende_tuerme(m.p):
        return 0.0
    pos = TUERME[k]
    ank, unb = verteidiger(m, pos)
    z2 = TurmZiel(z.team, z.lane, stufe, pos, TURM_DE[stufe].format(lane=z.lane),
                  abstand(z.pos, pos) * WEGFAKTOR / m.mein_tempo, ank, unb)
    fertig = ab + z2.weg + turm_dauer(z2, cfg["mitte"], mit)
    return turm_gewinn(z2, m, cfg) if schlaegt(m, rechtzeitig(z2, fertig), cfg["mitte"], z2.pos, fertig) else 0.0


ZAHL_WORT = {3: "drei", 4: "vier", 5: "fünf"}
# Pruefung c, R2.2: wohin der Kampf ist (Bereich -> Richtung im Satz)
ORT_RICHTUNG = {"fluss_oben": "in den oberen Fluss", "fluss_unten": "in den unteren Fluss",
                "fluss_mitte": "in den Mid-Fluss", "grube:drache": "zum Drachen", "grube:baron": "zum Baron",
                "jungle_eigen_oben": "in euren oberen Jungle", "jungle_eigen_unten": "in euren unteren Jungle",
                "jungle_fremd_oben": "in ihren oberen Jungle", "jungle_fremd_unten": "in ihren unteren Jungle",
                "lane:Top": "auf die Top-Lane", "lane:Mid": "auf die Mid-Lane", "lane:Bot": "auf die Bot-Lane",
                "lane_eigen": "auf deine Lane", "basis_fremd": "in ihre Basis", "basis_eigen": "in eure Basis"}


def _zahl(n: int) -> str:
    return {1: "einer", 2: "zwei", 3: "drei", 4: "vier", 5: "fünf"}.get(n, str(n))


def fenster_grund(z: TurmZiel, m, bis: float, kommen: list) -> str:
    """Der Grund fuer einen Turm - er muss FUER die Handlung sprechen (Pruefung C3): ein genanntes Fenster ist
    >= `bis` (Weg + Dauer), sonst waere das Ziel falsch. `kommen`: wer vorher da ist (dann schlaegst du ihn).
    Vorher: "fruehestens in 0 Sekunden kann einer von ihnen dort sein", "3 von ihnen sind noch 3 Sekunden tot"."""
    teile = []
    tote = [(g.champion, g.s.respawn) for g, _ in z.ankunft if g.s.tot]
    erste = min((t for _, t in z.ankunft), default=None)
    if tote and min(t for _, t in tote) >= bis:
        n = min(t for _, t in tote)
        wer = f"{len(tote)} von ihnen sind" if len(tote) >= 3 else f"{liste([c for c, _ in tote])} {'ist' if len(tote) == 1 else 'sind'}"
        teile.append(f"{wer} noch {int(n)} Sekunden tot")
    elif not kommen and erste is not None and erste >= bis:
        teile.append(f"{int(erste)} Sekunden, bis einer kommt")      # Auftrag 002, S2.3 (vorher 10 Woerter)
    if kommen:
        # hoechstens zwei Namen, ab drei wird gezaehlt (Buch 6, 9). Pruefung c, R2: kein "du schlaegst X" mehr - ein
        # Ziel, das nur ueber den Kampf traegt, ist stumm (turm_handlungen: modell_stumm); hier steht nur, wer kommt
        namen = (liste([g.champion for g in kommen]) if len(kommen) <= 2
                 else f"{ZAHL_WORT.get(len(kommen), len(kommen))} von ihnen")
        teile.append(f"{namen} {'kommt' if len(kommen) == 1 else 'kommen'} vorher")
    if teile:
        return ", ".join(teile)
    if m.woanders >= 3:
        return f"{m.woanders} von ihnen sind woanders"
    return "keiner von ihnen ist in der Nähe"


def umwandeln(m, cfg: dict) -> float | None:
    """Buch 5, 8: nach einem gewonnenen Kampf - >= 2 Gegner mehr tot als eigene, kuerzester Respawn >= 15 s, du lebst
    mit >= 30 %. Die 15 s braucht nur der Ausloeser: lief das Umwandeln schon, gilt es, "solange das Fenster reicht" -
    ob ein Turm noch vor seinem ersten Verteidiger faellt, rechnet turm_handlungen (36:32: Sona noch 14 s tot, du
    10 s vor dem Mid-Inhibitor-Turm). Rueckgabe: der kuerzeste Respawn (das Fenster), sonst None."""
    c = cfg["mitte"]
    if (baron := baron_fenster(m, cfg)) is not None:
        return baron
    if not m.tote_gegner or m.leben is None or m.leben < 0.3:
        return None
    if len(m.tote_gegner) - m.tote_eigene < c["umwandeln_ueberzahl"]:
        return None
    kuerzest = min(t for _, t in m.tote_gegner)
    return kuerzest if kuerzest >= c["umwandeln_fenster_min_s"] or (m.umwandeln_lief and kuerzest > 0) else None


def baron_fenster(m, cfg: dict) -> float | None:
    """Buch 6, 4.6: eigener Ausloeser fuers Umwandeln - euer BaronKill <= baron_fenster_s her und >= 3 von euch mit dem
    Buff leben (seit dem Kill nicht gestorben). Rueckgabe: der Rest des Buffs, sonst None."""
    p = m.p
    if p is None or m.tot or m.leben is None or m.leben < 0.3:
        return None
    c = cfg["objective"]
    barone = [e for e in p.kills_von("BaronKill") if e.team == p.mein_team]
    if not barone or m.zeit - barone[-1].zeit > c["baron_fenster_s"]:
        return None
    t0 = barone[-1].zeit
    gestorben = {e.opfer.name for e in p.kills_von("ChampionKill")
                 if e.opfer is not None and e.opfer.team == p.mein_team and e.zeit >= t0}
    mit_buff = sum(1 for s in p.team(p.mein_team) if not s.tot and s.name not in gestorben)
    if mit_buff < c["baron_umwandeln_mindestens"]:
        return None
    return c["baron_fenster_s"] - (m.zeit - t0)


def umwandeln_zuerst(m, cfg: dict, aus: list[Handlung]) -> list[Handlung]:
    """Kapitel 8: ist das Fenster nach einem Kampf offen und eine Struktur erreichbar, gibt es jetzt keinen Back.
    Buch 6, 8: Objectives haben einen Platz in der Reihenfolge (Baron/Aeltester 2,5, Drache 1,5) - ein erreichbares
    Objective verdraengt die Tuerme dahinter. Die 200 GE je Rang in turm_handlungen reichten dafuer nicht (102112 25:22:
    der aeussere Mid-Turm, 1048, gegen den freien Drachen, 221 - Buch 6 sagt dort NEHMEN)."""
    if umwandeln(m, cfg) is None:
        return aus
    from .objective import ORDNUNG as OBJ_ORDNUNG
    obj = [OBJ_ORDNUNG[h.daten["objective"]] for h in aus
           if h.art in ("NEHMEN", "BESTREITEN") and h.daten.get("objective") in OBJ_ORDNUNG]
    if obj:
        rang = max(obj)
        aus = [h for h in aus if not (h.daten.get("umwandeln") and h.daten.get("turm")
                                      and ORDNUNG.get(h.daten["turm"][2], 0) < rang)]
    if any(h.daten.get("umwandeln") for h in aus):
        return [h for h in aus if h.art not in ("BACK_JETZT", "WELLE_REIN_UND_BACK")]
    return aus


# Buch 5, 8: Nexus-Tuerme und Nexus vor Inhibitor-Turm und Inhibitor vor innerem vor aeusserem Turm
ORDNUNG = {"Nexus": 4, "Nexus-Turm": 4, "Inhibitor": 3, "Inhib": 3, "innen": 2, "aussen": 1}


def turm_handlungen(m, cfg: dict, modus: str, art: str, split: bool) -> list[Handlung]:
    """DRUECKEN (allein, `split`: die Split-Regel der Seite gilt) oder MIT_GRUPPE fuer jeden erreichbaren Turm."""
    c = cfg["mitte"]
    aus = []
    fenster_um = umwandeln(m, cfg)
    for z in turm_ziele(m) + (hinten_ziele(m) if fenster_um is not None else []):
        mit = m.team_nah(z.pos, 4000) if art == "MIT_GRUPPE" else 0
        if art == "MIT_GRUPPE" and mit == 0:
            continue              # "mit der Gruppe" nur, wo die Gruppe ist - allein ist es DRUECKEN (UNTERWEGS)
        dauer = turm_dauer(z, c, mit)
        # "nur, wenn der erste Verteidiger spaeter kommt als weg + dauer, oder du ihn schlaegst" (Kapitel 2) - seit
        # Schritt 5 alle, die bis weg + dauer kommen (Buch 6, 1.2), im Kampfmodell mit dem Turm (Buch 7, 1.4)
        kommen = rechtzeitig(z, z.weg + dauer)
        if not schlaegt(m, kommen, c, z.pos, z.weg + dauer):
            continue
        if split:
            if z.lane != m.lane_hier:
                continue          # auf der Seite: der Turm dieser Lane
            # Tiefe-Regel (3.1): hinter ihrem aeusseren Turm nur, wenn fast alle bekannt oder woanders sind
            if z.stufe != "aussen" and not (m.unbekannt_anzahl <= c["tiefe_unbekannt_max"]
                                            or m.woanders >= c["tiefe_woanders_min"]):
                continue
        else:
            # Gruppe / unterwegs: Ueberzahl - die Unbekannten koennen kommen, ihr muesst mehr sein
            wir = 1 + mit
            if fenster_um is None and z.unbekannt + len(kommen) >= wir:
                continue
        gewinn = turm_gewinn(z, m, cfg)
        folge = 0.0
        if fenster_um is not None:
            folge = 200.0 * ORDNUNG[z.stufe]        # die Reihenfolge aus Kapitel 8: das erste erreichbare gewinnt
            folge += dahinter(z, m, cfg, mit, z.weg + dauer)
        grund = fenster_grund(z, m, z.weg + dauer, ernste(m, kommen, z.pos, z.weg + dauer) or kommen[:1])
        name = z.name[4:] if z.name.startswith("den ") else z.name       # "inneren Top-Turm"
        if fenster_um is not None and z.stufe == "Inhib":
            satz = f"{z.lane}-Inhibitor-Turm jetzt: {grund}."
        elif fenster_um is not None and z.stufe in HINTEN:
            satz = f"{name[0].upper()}{name[1:]} jetzt: {grund}."
        elif art == "MIT_GRUPPE":
            satz = f"Mit der Gruppe zum {name}: {grund}."
        else:
            satz = f"Drück den {name}: {grund}."
        if fenster_um is not None and mit == 0 and art == "DRUECKEN" and len(m.tote_gegner) >= 3:
            satz = satz.rstrip(".") + ". Ruf dein Team."
        # Kapitel 2: EV = gewinn * p_erfolg - weg * zeitwert - p_tod(weg + dauer) * TK - am Turm arbeitest du, der Weg
        # ist die verlorene Zeit
        h = Handlung(art, Ziel("turm", z.name, z.pos, z.weg), modus, z.weg, gewinn=gewinn, folgewert=folge,
                     gefahr_t=z.weg + dauer, grund=grund, satz=satz,
                     schritte=[f"zu {z.name}", "Turm", "danach back" if fenster_um is not None else "weiter"])
        h.daten.update(turm=(z.team, z.lane, z.stufe), umwandeln=fenster_um is not None, ziel_pos=z.pos,
                       nexus_weg=nexus_tuerme_weg(m.p, z.team) if z.stufe == "Nexus-Turm" else 0,
                       # Pruefung c, R2.3: gesprochen nur, wenn das Ziel VOR dem ersten Verteidiger faellt - traegt es nur
                       # ueber den Kampf ("du schlaegst X"), ist es stumm, bis die Kampf-Eichung besteht
                       modell_stumm=bool(kommen))
        aus.append(h)
    return aus


def seitenwelle(m, cfg: dict, modus: str, lane: str, w) -> Handlung | None:
    """SEITENWELLE (Buch 5, 3.2/4): eine Welle laeuft auf euren Turm - hol sie. Erst nach der Lane-Phase (Buch 5 ist
    das Mid-Game; 144655, 0:58 auf dem Weg zur Lane: "Welle gerettet - kein Turm verloren")."""
    if w is None or m.lane_phase:
        return None
    c = cfg["mitte"]
    blau = m.p is None or m.p.mein_team == "ORDER"
    from ..merkmale import lane_punkt
    front = w.front if w.front is not None else w.turm_dein
    pos = bewertung.einheiten(*lane_punkt(lane, front if blau else 1.0 - front))
    weg = m.weg(pos) or 0.0
    ihre = w.ihre if w.ihre is not None else c["seitenwelle_min"]
    # Pruefung c, R7: erst ab welle_min Vasallen (oder Supervasallen, wenn euer Inhibitor dieser Lane fehlt) - 173159
    # 32:32 "1 Vasallen", 164326 33:02 "0 Vasallen" (die Zahl des Takts war 0, der Zustand kam aus dem Puffer)
    supervasallen = m.p is not None and lane in [l for l, _ in bewertung.eigene_inhibs_weg(m.p)]
    if ihre < cfg["schranken"]["welle_min"] and not supervasallen:
        return None
    ww = wert.wellenwert(m.zeit, cfg)
    gewinn = ww * min(3.0, ihre / 6.0) + c["seitenwelle_turmschutz"]
    name = welle_name(m, lane)
    grund = f"{ihre} Vasallen laufen in deinen Turm" if w.zustand != "GECRASHT_BEI_DIR" else \
        f"{ihre} Vasallen stehen an deinem Turm"
    satz = f"Hol {name}: {grund}."
    h = Handlung("SEITENWELLE", Ziel("lane", name, pos, weg), modus, weg + 10.0, gewinn=gewinn,
                 gefahr_t=min(weg + 10.0, 30.0), grund=grund, satz=satz, schritte=[f"zu {name}", "abräumen"])
    h.daten.update(lane=lane, ziel_pos=pos)
    return h


def kampf_kippt(k) -> bool:
    """Buch 5, 5: >= 2 eigene tot und keine Gegner-Tode - der Kampf ist verloren."""
    return k.tote_eigene >= 2 and k.tote_gegner == 0


def zur_gruppe(m, cfg: dict, modus: str) -> list[Handlung]:
    """ZUR_GRUPPE (zu Fuss) und TP_SPIEL (Buch 5, 3.2 und 5) - nur, wenn du rechtzeitig da bist und den Unterschied
    machst; nie in einen verlorenen Kampf."""
    c = cfg["mitte"]
    aus = []
    k = m.teamkampf
    if k is not None and not kampf_kippt(k) and k.eigene >= 2:
        ort = GRUBE_WORT.get(k.ort or "", "zum Kampf")
        zahlen = f"ihr seid {k.eigene} gegen {k.gegner}"
        wert_ = c["kampf_wert_je_gegner"] * k.gegner
        if k.dein_weg is not None and k.dein_weg <= c["tp_zu_fuss_ab_s"]:
            # Pruefung c, R2.2: "Zu Graves in den Mid-Fluss: mit dir drei gegen zwei." - Ort und Namen statt "Zum Kampf,
            # jetzt"; gesprochen nur mit >= zur_kampf_mehr_koepfe Koepfen mehr nach deiner Ankunft und genug Leben
            cs = cfg["schranken"]
            freunde = [s.champion for s, wo, *_ in (m.b.mitspieler if m.b is not None else [])
                       if wo is not None and not s.tot and abstand(wo, k.pos) <= c["teamkampf_radius"]]
            zu = f"Zu {liste(freunde[:2])}" if 1 <= len(freunde) <= 2 else "Zu deinem Team"
            richtung = ORT_RICHTUNG.get(k.ort or "", "")
            satz = f"{zu}{' ' + richtung if richtung else ''}: mit dir {_zahl(k.eigene + 1)} gegen {_zahl(k.gegner)}."
            h = Handlung("ZUR_GRUPPE", Ziel("gruppe", ort, k.pos, k.dein_weg), modus, k.dein_weg + 5, gewinn=wert_,
                         gefahr_t=min(k.dein_weg + 5, 30.0), grund=zahlen, satz=satz)
            h.daten["ziel_pos"] = k.pos
            h.daten["modell_stumm"] = (k.eigene + 1 - k.gegner < cs["zur_kampf_mehr_koepfe"]
                                       or m.leben is None or m.leben < cs["zur_kampf_leben_min"])
            aus.append(h)
        tp = m.tp_in == 0
        laeuft_noch = k.seit <= 3.0
        aendert = k.eigene + 1 >= k.gegner
        if aendert and k.ort in ("grube:drache", "grube:baron"):
            # Buch 6, 4.7: an einem Objective muss dein TP das Urteil aendern
            from .. import kampf
            mit, _ = kampf.p_gewinn(m, k.pos, cfg["objective"]["kampf_fenster_s"], cfg=cfg)
            ohne, _ = kampf.p_gewinn(m, k.pos, cfg["objective"]["kampf_fenster_s"], cfg=cfg, ohne_mich=True)
            # "muss dein TP das Urteil aendern": um >= tp_unterschied_min - oder es kippt (ohne dich verloren, mit dir
            # gewonnen). Mit k = 2 und mitspieler_anteil 0,8 hebt ein Spieler p_gewinn bei 4 gegen 4 nur um 0,147 - die
            # Schwelle allein liesse das Beispiel aus Buch 5 ("TP macht es 5 gegen 4") nie zu (Abweichung, messungen.md)
            aendert = mit - ohne >= cfg["objective"]["tp_unterschied_min"] or ohne < 0.5 <= mit
        if tp and (k.dein_weg or 0) > c["tp_zu_fuss_ab_s"] and laeuft_noch and aendert:
            gegen_tp = ""
            if m.tp_gegner_top is not None and m.tp_gegner_top > 0 and m.b.lane is not None:
                gegen_tp = f", {m.b.lane.champion} hat kein TP"
            h = Handlung("TP_SPIEL", Ziel("ort", ort, k.pos, 4.0), modus, 8.0, gewinn=wert_ * 1.2,
                         kosten=0.5 * wert.wellenwert(m.zeit, cfg), gefahr_t=4.0, grund=zahlen,
                         satz=f"TP {ort}, dann rein: {zahlen}{gegen_tp}.")
            h.daten["ziel_pos"] = k.pos
            aus.append(h)
    return aus


def welle_und_raus(m, cfg: dict, modus: str, lane: str, w) -> Handlung | None:
    """WELLE_UND_RAUS (Buch 5, 3.2): Objective auf der anderen Seite in 45-75 s, kein TP - Welle crashen, dann
    rotieren. Hat ihr Toplaner TP und du nicht: 15 s frueher (Kapitel 5)."""
    c, cr = cfg["mitte"], cfg["recall"]
    if m.tp_in == 0:
        return None
    frueher = 15.0 if (m.tp_gegner_top == 0 and m.tp_in != 0) else 0.0
    from . import objectives_meine_seite
    from .. import objective as obj
    meine = {o.schl for o in objectives_meine_seite(m, lane)}
    for o in sorted(m.objectives, key=lambda o: o.spawn_in):
        if o.schl in meine or o.lebt or not (45 <= o.spawn_in <= 75 + frueher) or not obj.zieht(m, o, cfg):
            continue
        weg = o.weg if o.weg is not None else 40.0
        ww = wert.wellenwert(m.zeit, cfg)
        name = welle_name(m, lane)
        kurz = name.split(" ", 1)[1]          # "Top-Welle"
        crash = 10.0
        grund = f"Spawn um {uhr(m.zeit + o.spawn_in)}, {puenktlich(o.spawn_in - crash - weg)}"
        h = Handlung("WELLE_UND_RAUS", Ziel("objective", OBJ_NAME[o.schl], o.pos, weg), modus, 10.0 + weg,
                     gewinn=cr["vorlauf_bonus"] * cfg["objective_wert"].get(o.schl, 0) + 0.5 * ww, gefahr_t=10.0,
                     grund=grund, satz=f"{kurz[0].upper()}{kurz[1:]} rein, dann {ZUM[o.schl]}: {grund}.",
                     schritte=[f"{kurz} rein", ZUM[o.schl]])
        h.daten.update(objective=o.schl, spawn=m.zeit + o.spawn_in, ziel_pos=o.pos)
        return h
    return None


def objective_ruft(m, cfg: dict, lane: str | None) -> bool:
    """Split-Regel 1 (3.1): ruft ein Objective dich? Ohne TP: eins spawnt in <= rotation_vorlauf_s (auf deiner Seite
    genauso - vorher Welle rein und hin). Mit TP bereit: erst, wenn es kaempft (dann TP_SPIEL)."""
    c = cfg["mitte"]
    if m.tp_in == 0:
        return False
    from .. import objective as obj
    vorlauf = c["rotation_vorlauf_s"] + (15.0 if m.tp_gegner_top == 0 else 0.0)
    # Buch 6, 4.1: ruft nur, was dich zieht
    return any(obj.zieht(m, o, cfg) and ((not o.lebt and o.spawn_in <= vorlauf) or (o.lebt and o.team_nah >= 2))
               for o in m.objectives)


def halten(modus: str) -> Handlung:
    """Der stille Grundplan ausserhalb der Lane: bleiben, wo du bist (fuer die Gefahr-Rechnung wie FARMEN)."""
    return Handlung("HALTEN", None, modus, 10.0)
