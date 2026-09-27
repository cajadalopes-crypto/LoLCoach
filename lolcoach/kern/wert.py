"""Wert: alles in einer Waehrung (Buch 0, Kapitel 7; Welle: Buch 1, Kapitel 2).

    EV(h) = p_erfolg * gewinn - p_tod * todeskosten - dauer * zeitwert - kosten + folgewert

GE = Gold-Aequivalent: Gold 1:1, Erfahrung mal `xp_ge`, Zeit mal `zeitwert(phase)`. Es geht um Rangfolgen, nicht um
exakte Betraege. `kosten` sind sichere Verluste neben der Zeit (Wellen, die waehrend deiner Abwesenheit an deinem
Turm sterben - Buch 1, Kapitel 2)."""
from __future__ import annotations

from functools import lru_cache

from .. import bewertung, wissen
from . import gefahr
from .handlung import Handlung


@lru_cache(maxsize=1)
def _mechanik() -> dict:
    return wissen.lade("mechanik")


def zeitwert(zeit: float, cfg: dict) -> float:
    c = cfg["zeitwert"]
    return c["bis_14"] if zeit < 840 else c["bis_25"] if zeit < 1500 else c["danach"]


def wellentakt(zeit: float) -> float:
    """Sekunden zwischen zwei Wellen (mechanik.toml [wellen] takt)."""
    takt = 30.0
    for stufe in _mechanik()["wellen"]["takt"]:
        if zeit >= stufe["ab"]:
            takt = float(stufe["s"])
    return takt


def wellenwert(zeit: float, cfg: dict, kanone: bool = False) -> float:
    """Eine Welle: 3 Nah- + 3 Fernkampf-Vasallen (+ Kanone) in Gold, dazu ihre Erfahrung x xp_ge (Buch 1, 2)."""
    g, x = _mechanik()["gold"], _mechanik()["xp"]
    gold = 3 * g["vasall_nah"] + 3 * g["vasall_fern"]
    xp = 3 * x["vasall_nah"] + 3 * x["vasall_fern"]
    if kanone:
        gold += min(g["vasall_kanone_max"], g["vasall_kanone"] + g["vasall_kanone_pro_stufe"] * int(zeit // 90))
        xp += x["vasall_kanone"]
    return gold + xp * cfg["zeitwert"]["xp_ge"]


def vasall_wert(zeit: float, cfg: dict) -> float:
    return wellenwert(zeit, cfg) / 6.0


def farm_rate(zeit: float, cfg: dict) -> float:
    """GE je Sekunde, die du auf deiner Lane farmst: eine Welle je Wellentakt + die Top-Rollenquest."""
    return wellenwert(zeit, cfg) / wellentakt(zeit) + cfg["welle"]["quest_je_s_lane"]


def platte_gold(zeit: float) -> float:
    g = _mechanik()["gold"]
    if zeit < g["platte_abzug_ab"]:
        return float(g["platte"])
    return max(float(g["platte_min"]), g["platte"] - g["platte_abzug_pro_min"] * (zeit - g["platte_abzug_ab"]) / 60)


def todeskosten(m, cfg: dict, ohne: str | None = None) -> float:
    """Kapitel 7.3: Kill-Gold fuer den Gegner (Basis + Kopfgeld) + Todeszeit x Zeitwert + eigene Wellen, die
    waehrenddessen in deinen Turm laufen + das naechste Objective x objective_risiko (lebt oder spawnt waehrend du
    tot bist). `ohne`: fuer eine Handlung AN diesem Objective zaehlt sein Anteil nicht (Buch 6, 3.3 - sonst doppelt)."""
    b = m.b
    if b is None:
        return 0.0
    try:
        from .. import denker
        erstes = denker._erstes_blut_offen(b) if b.partie is not None else False
    except Exception:
        erstes = False
    kg = bewertung.kill_gold(b.ich, erstes_blut=erstes, p=b.partie)
    tz = b.tod_kostet or bewertung.todeszeit(b.ich.level, m.zeit)
    zw = zeitwert(m.zeit, cfg)
    wellen = tz / wellentakt(m.zeit) * wellenwert(m.zeit, cfg)
    obj = 0.0
    werte = cfg["objective_wert"]
    for o in m.objectives:
        if o.schl == ohne:
            continue
        if o.lebt or o.spawn_in <= tz + 30:
            obj = max(obj, werte.get(o.schl, 0) * cfg["gefahr"]["objective_risiko"])
    return kg + tz * zw + wellen + obj


def bewerte(h: Handlung, m, cfg: dict, tk: float | None = None) -> Handlung:
    """p_tod (Gefahr-Modell ueber das Fenster der Handlung), EV und die sechs Fragen."""
    c = cfg["gefahr"]
    T = h.gefahr_t if h.gefahr_t is not None else h.dauer
    if (am := h.daten.get("gefahr_am")) is not None:
        # WOHIN aus Tod und Basis: die Gefahr am Ziel zur Ankunft, nicht hier (Pruefung E2)
        p, wer = gefahr.p_tod_am(m, am[0], am[1], c, am_turm=bool(am[2]))
    else:
        p, wer = gefahr.p_tod(max(T, 1.0), m, c, am_turm=bool(h.daten.get("am_turm")),
                              kampf_mit=h.daten.get("kampf_mit"))
    h.p_tod = min(1.0, p * h.schutz)
    if (kanal := h.daten.get("danach_kanal")):
        # erst raus, dann back (Buch 3, 2.2): der Kanal am sicheren Ort ist auch nicht umsonst - dort mit deinem Turm
        p2, _ = gefahr.p_tod(kanal, m, c, am_turm=True)
        h.p_tod = 1.0 - (1.0 - h.p_tod) * (1.0 - p2)
    if (an := h.daten.get("an_objective")) is not None:
        h.verlust = todeskosten(m, cfg, ohne=an)
    else:
        h.verlust = todeskosten(m, cfg) if tk is None else tk
    pe = h.p_erfolg if h.p_erfolg is not None else 1.0 - h.p_tod
    h.ev = pe * h.gewinn - h.p_tod * h.verlust - h.dauer * zeitwert(m.zeit, cfg) - h.kosten + h.folgewert
    if (eb := h.daten.get("ev_bestreiten")) is not None:
        # Buch 6, 4.4: gegen "abgeben" - p_gewinn x (wert_uns + wert_ihnen) - (1 - p_gewinn) x todeskosten_team - Weg
        pg, werte, tk_team = eb
        h.ev = pg * werte - (1.0 - pg) * tk_team - h.dauer * zeitwert(m.zeit, cfg) + h.folgewert
    h.daten["wer"] = wer[:3]
    h.fragen = fragen(h, m, wer)
    return h


def fragen(h: Handlung, m, wer: list) -> dict:
    """Die sechs Fragen (7.6) - Dashboard und Claude bekommen alle, gesprochen wird nur `grund`."""
    b = m.b
    aus = {}
    if b is not None and b.lane is not None:
        wert, gruende = b.kraefte()
        aus["staerker"] = (", ".join(gruende[:2]) or "gleichauf") + f" ({wert:+.1f})"
    if wer:
        aus["zuerst"] = ", ".join(f"{n} {int(x * 100)} %" for n, x in wer[:3]) + f" in {int(h.gefahr_t or h.dauer)} s"
    if b is not None:
        weg = [g for g in b.gegner if not g.s.tot and not g.sichtbar]
        if weg:
            aus["unsichtbar"] = ", ".join(f"{g.champion} {'nie gesehen' if g.seit is None else f'seit {int(g.seit)} s'}"
                                          for g in weg[:3])
    if h.kosten > 0:
        aus["welle_verlust"] = f"{int(h.kosten)} GE Wellen"
    if h.p_tod > 0:
        aus["gegner_bekommt"] = f"{int(h.p_tod * 100)} % Tod x {int(h.verlust)} GE"
    if h.schritte:
        aus["danach"] = " -> ".join(h.schritte)
    return aus
