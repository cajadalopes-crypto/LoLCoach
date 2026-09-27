"""Das eine Kampfurteil (Buch 7, Kapitel 3): `p_gewinn` entscheidet Duell, Objective-Kampf (Buch 6), Gefahr (Buch 0,
7.5 ueber `gefahr.p_verliere`) und Todesrueckblick.

    kraft_i  = 1,10^(Level-1) * (1 + Item-Gold/2500) * Leben (unbekannt 0,9)
               * ult_faktor_weg (bekannt weg, Level >= 6, BEIDE Seiten) * flash_faktor_weg (bekannt weg)
               * faehigkeiten_faktor_weg (nur du: Kern-Faehigkeiten laut HUD weg, Riven E und W)
    K        = Summe wir kraft * anteil / Summe die kraft * gewicht,  * turm_faktor an eurem Turm, / an ihrem
    p_gewinn = K^k / (1 + K^k)

Unbekannt ist neutral (Faktor 1), nie schlimmster Fall. Gegnerwerte der Live-API sind der Stand der letzten Sichtung
(Level UND Items, gemessen 27.09. - Qualitaetsrunde 2, G7): wer seit > unsichtbar_s nicht gesehen wurde, geht mit
max(API, Median eures Teams - level_abschlag) bzw. max(API, Median-Item-Gold eures Teams * item_anteil) ein."""
from __future__ import annotations

import statistics

from ..bewertung import TUERME, TURM_REICHWEITE, WEGFAKTOR, abstand, stehende_tuerme
from ..zustand import gegenteam

MITSPIELER_TEMPO = 380.0


def cfg_kampf(cfg: dict) -> dict:
    return cfg["kampf"]


def champion_werte(cfg: dict, champion_id: str | None) -> dict:
    ch = cfg["kampf"].get("champion", {})
    return ch.get(champion_id or "", ch.get("standard", {}))


def _grund(level: int, gold: float, leben: float | None) -> float:
    return 1.10 ** (max(1, level) - 1) * (1.0 + gold / 2500.0) * (0.9 if leben is None else max(0.05, min(1.0, leben)))


def gegner_werte(g, m, c: dict) -> tuple[int, float, bool]:
    """(Level, Item-Gold, geschaetzt?) - lange nicht gesehen: nachgeschaetzt aus eurem Team (G7)."""
    level, gold = g.s.level, float(g.s.item_gold)
    if (g.seit is None or g.seit > c["unsichtbar_s"]) and m.p is not None and m.p.ich is not None:
        team = m.p.team(m.p.mein_team)
        if team:
            lv = statistics.median(x.level for x in team) - c["level_abschlag"]
            it = statistics.median(x.item_gold for x in team) * c["item_anteil"]
            neu_lv, neu_it = max(level, int(round(lv))), max(gold, it)
            return neu_lv, neu_it, (neu_lv, neu_it) != (level, gold)
    return level, gold, False


def kraft_gegner(g, m, c: dict) -> float:
    level, gold, _ = gegner_werte(g, m, c)
    leben = g.leben if g.leben is not None and (g.leben_alter is None or g.leben_alter <= 2.5) else None
    k = _grund(level, gold, leben)
    if g.ult is not None and g.ult > 0 and level >= 6:
        k *= c["ult_faktor_weg"]
    if g.flash is not None and g.flash > 0:
        k *= c["flash_faktor_weg"]
    return k


def kraft_ich(m, cfg: dict) -> float:
    c, b = cfg["kampf"], m.b
    k = _grund(b.ich.level, b.ich.item_gold, b.leben)
    if b.ult is False and b.ich.level >= 6:
        k *= c["ult_faktor_weg"]
    if b.flash is not None and b.flash > 0:
        k *= c["flash_faktor_weg"]
    kern = champion_werte(cfg, b.ich.champion_id).get("kern", [])
    if kern and b.bereit and any(b.bereit.get(t) is False for t in kern):
        k *= c["faehigkeiten_faktor_weg"]
    return k


def _turm(m, ort) -> int:
    """+1: ort in Reichweite eures stehenden Turms, -1: ihres, 0: keiner."""
    p = m.p
    if p is None or ort is None:
        return 0
    mein = p.mein_team
    for (team, lane, stufe), pos in TUERME.items():
        if (team, lane, stufe) in stehende_tuerme(p) and abstand(pos, ort) <= TURM_REICHWEITE:
            return 1 if team == mein else -1
    return 0


def p_gewinn(m, ort, fenster_s: float, gewichte: dict | None = None, cfg: dict | None = None,
             ohne_mich: bool = False, mit_mir: bool = True, turm: int | None = None,
             mitspieler_nur: set | None = None) -> tuple[float, dict]:
    """Wahrscheinlichkeit, dass eure Seite einen Kampf um `ort` gewinnt, und die Aufschluesselung (wer auf welcher
    Seite mit welcher Kraft) fuer Satz, Protokoll und Todesrueckblick. `gewichte`: Champion-Name des Spielers -> Gewicht
    (ueberschreibt p_da; nicht genannte Gegner zaehlen 0). Ohne `gewichte`: sichtbar in kampf_radius um `ort` 1,
    sonst p_da(g, fenster_s, ort)."""
    from . import gefahr, konfig
    cfg = cfg or konfig()
    c = cfg["kampf"]
    b = m.b
    if b is None:
        return 0.5, {}
    ort = ort if ort is not None else b.pos
    wir, die = [], []
    if mit_mir and not ohne_mich and not m.tot:
        wir.append((b.ich.champion, kraft_ich(m, cfg), 1.0, b.ult is False and b.ich.level >= 6))
    ults = getattr(m, "ult_mitspieler", {}) or {}
    for s, wo, leben, *_ in b.mitspieler:
        if s.tot or wo is None or ort is None:
            continue
        if mitspieler_nur is not None and s.name not in mitspieler_nur:
            continue            # Buch 6: an einer Grube kaempft, wer hingeht
        if abstand(wo, ort) * WEGFAKTOR / MITSPIELER_TEMPO > fenster_s:
            continue
        k = _grund(s.level, s.item_gold, leben)
        ult_weg = ults.get(s.name) is False and s.level >= 6
        if ult_weg:
            k *= c["ult_faktor_weg"]
        wir.append((s.champion, k, c["mitspieler_anteil"], ult_weg))
    for g in b.gegner:
        # Tote zaehlen mit ihrem Gewicht - wer im Fenster respawnt und hinkommt, kaempft mit (p_da_am rechnet Respawn und
        # Weg; 102112 34:51: am Inhibitor zaehlten Sett, Kai'Sa und Fiddlesticks gar nicht, 11-19 s vor ihrem Respawn)
        if gewichte is not None:
            w = gewichte.get(g.s.name, 0.0)
        elif g.sichtbar and g.pos is not None and ort is not None and abstand(g.pos, ort) <= c["kampf_radius"]:
            w = 1.0
        else:
            w = gefahr.p_da_am(g, fenster_s, m, cfg["gefahr"], ort)
        if w > 0:
            die.append((g.champion, kraft_gegner(g, m, c), w, g.ult is not None and g.ult > 0 and g.s.level >= 6))
    s_wir = sum(x[1] * x[2] for x in wir)
    s_die = sum(x[1] * x[2] for x in die)
    turm = _turm(m, ort) if turm is None else turm
    if s_die <= 0:
        K = 99.0
    else:
        K = s_wir / s_die
        if turm > 0:
            K *= c["turm_faktor"]
        elif turm < 0:
            K /= c["turm_faktor"]
    kk = c["k"]
    p = 1.0 if K >= 99 else (K ** kk / (1.0 + K ** kk) if K > 0 else 0.0)
    return p, {"wir": wir, "die": die, "K": K, "turm": turm}
