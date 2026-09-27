"""Modus OBJECTIVE und die Objective-Handlungen (Buch 6, Kapitel 4, 5 und 8) - in allen Modi aus derselben Rechnung
(kern/objective.py).

- `VORBEREITEN_OBJECTIVE` (4.2): spawnt in abfahrt_s bis objective_vorlauf_s und `objective_zieht`. Einmal Plan, haelt
  es bis Spawn + 10 s (dann NEHMEN, ohne neue Ansage) - abgebrochen nur mit p_erfolg < abbruch_p, totem Jungler, Leben
  < leben_min ohne Back-Schritt, oder wenn das Objective dich nicht mehr zieht.
- `NEHMEN` (4.3, Alias ANLAUFEN): lebt oder spawnt in <= Weg + ankunft_vorlauf_s, p_erfolg >= nehmen_p_min, EV > 0.
- `BESTREITEN` (4.4): lebt, sie sind zuerst dort oder P_kampf >= bestreiten_kampf_ab, p_gewinn >= bestreiten_p_min.
- `ABGEBEN_TAUSCHEN` (4.5): sie nehmen es, BESTREITEN ist kein Kandidat - der beste Turm der Karten-Rechnung, der
  Tausch zuerst im Satz. Ohne Tausch kein Satz (dann ZURUECK oder der stille Plan).

Die Handlungen tragen daten["objective"] (Schluessel), ["spawn"] (Spielzeit), ["zieht"], ["p_erfolg_obj"],
["anteil"] - fuer die Sprechregel "einmal je Spawn" (Kapitel 9), _kern.jsonl und die Kennzahl (Kapitel 14)."""
from __future__ import annotations

from .. import objective as obj
from .. import wert
from ..handlung import Handlung, Ziel
from . import OBJ_NAME, karte

OBJ_ARTEN = frozenset(("VORBEREITEN_OBJECTIVE", "NEHMEN", "BESTREITEN"))
URTEIL_ARTEN = OBJ_ARTEN | {"ABGEBEN_TAUSCHEN"}
# Kapitel 5: Objective-Plaene gelten in diesen Modi (ein Wechsel zwischen ihnen verwirft sie nicht)
OBJ_MODI = frozenset(("UNTERWEGS", "GRUPPE", "SEITE", "OBJECTIVE"))
ZUM = {"drache": "zum Drachen", "baron": "zum Baron", "herold": "zum Herold", "larven": "zu den Larven",
       "aeltester": "zum Ältesten"}
AM = {"drache": "am Drachen", "baron": "am Baron", "herold": "am Herold", "larven": "an den Larven",
      "aeltester": "am Ältesten"}
ZAHL = {2: "zu zweit", 3: "zu dritt", 4: "zu viert", 5: "zu fünft"}
# Buch 6, 8 (aendert Buch 5, 8 und karte.ORDNUNG): Platz der Objectives in der Umwandel-Reihenfolge
ORDNUNG = {"baron": 2.5, "aeltester": 2.5, "drache": 1.5}


def ankunft_vorlauf(o, u, cfg: dict) -> float:
    av = cfg["objective"]["ankunft_vorlauf_s"]
    return float(av["gross"] if u.gross else av.get(o.schl, av["drache"]))


def _weg(m, o) -> float:
    if m.tot or o.weg is None:
        from ...bewertung import BRUNNEN, WEGFAKTOR, abstand
        mein = m.p.mein_team if m.p is not None else "ORDER"
        return (m.respawn if m.tot else 0.0) + abstand(BRUNNEN[mein], o.pos) * WEGFAKTOR / (m.mein_tempo or 345.0)
    return o.weg


def spawn_zeit(m, o) -> int:
    """Die Spielzeit dieses Spawns - auch wenn es schon lebt (fuer "einmal je Spawn", Kapitel 9)."""
    if m.p is not None:
        try:
            t = m.p.naechster_spawn("drache" if o.schl == "aeltester" else o.schl)
        except Exception:
            t = None
        if t is not None:
            return round(t)
    return round(m.zeit + o.spawn_in)


def _handlung(art: str, m, cfg: dict, modus: str, o, u, satz: str, grund: str, schritte: list) -> Handlung:
    """EV nach 3.3: gewinn = anteil x wert_uns + folgewert; die Zeitkosten nur auf dem Weg; das Risiko an der Grube
    bis zum Ende der Toetungszeit, ohne den Objective-Anteil der Todeskosten (sonst zaehlt es doppelt)."""
    weg = _weg(m, o)
    rest = max(0.0, u.t1 - weg) if u.t1 else 0.0
    h = Handlung(art, Ziel("objective", OBJ_NAME[o.schl], o.pos, weg), modus, weg,
                 gewinn=u.anteil * u.wert_uns, folgewert=u.folgewert, p_erfolg=1.0,
                 gefahr_t=weg + max(u.dauer, rest), grund=grund, satz=satz, schritte=schritte)
    from ..merkmale import OBJ_GRUBE
    h.daten.update(objective=o.schl, ziel_pos=o.pos, spawn=spawn_zeit(m, o), zieht=u.zieht,
                   p_erfolg_obj=round(u.p_erfolg, 3), anteil=round(u.anteil, 3), an_objective=o.schl,
                   gefahr_am=(o.pos, max(0.0, weg + max(u.dauer, rest) - cfg["gefahr"]["fenster_s"]), False),
                   ev_min=0.0, P_kampf=round(u.P_kampf, 3), faellt_in=round(u.t1, 1),
                   in_grube=m.bereich == f"grube:{OBJ_GRUBE[o.schl]}")
    if karte.umwandeln(m, cfg) is not None and o.schl in ORDNUNG:
        h.folgewert += 200.0 * ORDNUNG[o.schl]      # wie turm_handlungen: die Reihenfolge aus Kapitel 8
    return h


def _satz(kopf: str, grund: str) -> str:
    return f"{kopf}: {grund}."


def vorbereiten(m, cfg: dict, modus: str, o, lane: str | None = None, welle_s: float = 0.0,
                plan=None) -> Handlung | None:
    """4.2. `plan`: der laufende Plan - ist er VORBEREITEN_OBJECTIVE fuer dieses Objective, gilt das
    Entstehungsfenster nicht mehr (nur die Abbrueche)."""
    c = cfg["objective"]
    u = obj.urteil_von(m, o, cfg)
    weg = _weg(m, o)
    laeuft = (plan is not None and plan.art == "VORBEREITEN_OBJECTIVE"
              and plan.handlung.daten.get("objective") == o.schl)
    if laeuft:
        if m.zeit > plan.handlung.daten.get("spawn", 0) + 10.0:
            return None                                   # danach NEHMEN
        if u.p_erfolg < c["abbruch_p"] or not u.gebraucht or u.anteil * u.wert_uns + u.folgewert <= 0:
            return None
        if m.b is not None and m.b.leben is not None and m.b.leben < c["leben_min"] and not m.tot:
            return None                                   # ohne Back-Schritt (den bringt BACK_JETZT/OBJECTIVE_VORLAUF)
    else:
        if o.lebt or not u.zieht:
            return None
        # abfahrt_s = ankunft_vorlauf + Weg + welle_s; passt der Welle-Schritt nicht mehr ins Fenster, geht es ohne ihn
        # (sonst fiele die Lage zwischen VORBEREITEN und NEHMEN durch - Abweichung, messungen.md Schritt 5)
        if not (ankunft_vorlauf(o, u, cfg) + weg <= o.spawn_in <= cfg["modus"]["objective_vorlauf_s"]):
            return None
        if o.spawn_in < ankunft_vorlauf(o, u, cfg) + weg + welle_s:
            welle_s = 0.0
    g = obj.grund(m, o, u, "VORBEREITEN_OBJECTIVE")
    zum = ZUM[o.schl]
    if lane is not None and welle_s > 0:
        kopf = f"{lane}-Welle rein, dann {zum}"
        schritte = ["Welle rein", zum]
    else:
        kopf = f"{zum[0].upper()}{zum[1:]}"
        schritte = [zum]
    return _handlung("VORBEREITEN_OBJECTIVE", m, cfg, modus, o, u, _satz(kopf, g), g, schritte)


def nehmen(m, cfg: dict, modus: str, o) -> Handlung | None:
    c = cfg["objective"]
    u = obj.urteil_von(m, o, cfg)
    weg = _weg(m, o)
    if not (o.lebt or o.spawn_in <= weg + ankunft_vorlauf(o, u, cfg)):
        return None
    if u.n == 0 or u.p_erfolg < c["nehmen_p_min"] or not u.zieht:
        return None
    if _bestreiten_lage(m, o, u, cfg):
        return None                                        # dann ist es BESTREITEN, nicht NEHMEN
    g = obj.grund(m, o, u, "NEHMEN")
    if not o.lebt:
        kopf = f"{ZUM[o.schl][0].upper()}{ZUM[o.schl][1:]}"          # "Zu den Larven: ..." - es spawnt gleich
    else:
        kopf = f"{OBJ_NAME[o.schl]} {'allein' if u.n == 1 and len(u.auf.get('wir', [])) <= 1 else 'jetzt'}"
    if u.mit:
        # Buch 6, 3.3 Nachtrag: wer mit dir kommt, steht im Satz ("Drache mit Tryndamere: ...")
        from . import liste
        kopf = f"{kopf.rsplit(' ', 1)[0] if o.lebt else kopf} mit {liste(u.mit[:2])}"
    h = _handlung("NEHMEN", m, cfg, modus, o, u, _satz(kopf, g), g, ["hin", "nehmen"])
    # Pruefung c, R2.4: NEHMEN mit Kampf (P_kampf >= 0,1) haengt am ungeeichten p_gewinn - stumm
    h.daten["modell_stumm"] = u.P_kampf >= 0.1
    return h


def sie_dort(m, o, cfg: dict) -> int:
    """Wie viele von ihnen stehen an der Grube (sichtbar oder vor <= 10 s dort gesehen, grube_radius)?"""
    from ...bewertung import abstand
    r = cfg["modus"]["grube_radius"]
    return sum(1 for g in (m.b.gegner if m.b is not None else []) if not g.s.tot and g.pos is not None
               and abstand(g.pos, o.pos) <= r and (g.sichtbar or (g.seit is not None and g.seit <= 10.0)))


def _bestreiten_lage(m, o, u, cfg: dict) -> bool:
    """4.4: "sie sind zuerst dort, oder P_kampf >= bestreiten_kampf_ab" - beides nur, wenn mindestens einer von ihnen
    wirklich an der Grube steht. Die EV aus 4.4 rechnet gegen "sie bekommen es sicher"; ohne sie dort machte schon
    P_kampf (wer KOENNTE kommen) BESTREITEN zum Dauerplan (102112 24:36-38:36 "Baron bestreiten", keiner von ihnen am
    Baron; Abweichung, messungen.md Schritt 5)."""
    return o.lebt and sie_dort(m, o, cfg) >= 1 and (
        u.die_zuerst or u.P_kampf >= cfg["objective"]["bestreiten_kampf_ab"])


def _todeskosten_team(m, cfg: dict, u) -> float:
    """4.4: Summe der zwei hoechsten todeskosten_spieler unter euch Beteiligten; fuer dich die volle ohne das
    umkaempfte Objective."""
    from ... import bewertung
    p = m.p
    zw = wert.zeitwert(m.zeit, cfg)
    namen = {x[0] for x in u.auf.get("wir", [])}
    werte = []
    if p is not None:
        for s in p.team(p.mein_team):
            if s.champion not in namen:
                continue
            if s is p.ich:
                werte.append(wert.todeskosten(m, cfg, ohne=u.schl))
            else:
                werte.append(bewertung.kill_gold(s, p=p) + bewertung.todeszeit(s.level, m.zeit) * zw)
    return sum(sorted(werte, reverse=True)[:2])


def bestreiten(m, cfg: dict, modus: str, o) -> Handlung | None:
    c = cfg["objective"]
    u = obj.urteil_von(m, o, cfg)
    if not _bestreiten_lage(m, o, u, cfg) or not u.gebraucht:
        return None
    schwelle = c["bestreiten_p_min_gross"] if u.gross else c["bestreiten_p_min"]
    p_g, auf = obj.kampf_bei_ankunft(m, o, cfg, _weg(m, o))
    if p_g < schwelle:
        return None
    from dataclasses import replace
    u = replace(u, p_gewinn=p_g, auf=auf)      # Satz und EV aus dem Kampf bei deiner Ankunft
    g = obj.grund(m, o, u, "BESTREITEN")
    h = _handlung("BESTREITEN", m, cfg, modus, o, u, _satz(f"{OBJ_NAME[o.schl]} bestreiten", g), g,
                  ["hin", "kämpfen"])
    wert_sum = u.wert_uns + (u.wert_ihnen if c.get("verhindern", True) else 0.0)
    h.daten["ev_bestreiten"] = (u.p_gewinn, wert_sum, _todeskosten_team(m, cfg, u))
    return h


def abgeben_tauschen(m, cfg: dict, modus: str, o, tuerme: list[Handlung]) -> Handlung | None:
    """4.5, nach der Lane-Phase: der beste Turm-Kandidat der Karten-Rechnung als Tausch, der Tausch zuerst im Satz."""
    if m.lane_phase or not obj.sie_nehmen_es(m, o, cfg):
        return None
    if bestreiten(m, cfg, modus, o) is not None:
        return None
    zw = wert.zeitwert(m.zeit, cfg)
    beste = max(tuerme, key=lambda h: h.gewinn + h.folgewert - h.dauer * zw, default=None)
    if beste is None:
        return None
    r = cfg["modus"]["grube_radius"]
    from ...bewertung import abstand
    n = sum(1 for g in m.b.gegner if not g.s.tot and g.pos is not None and abstand(g.pos, o.pos) <= r
            and (g.sichtbar or (g.seit is not None and g.seit <= 10.0)))
    name = beste.ziel.name[4:] if beste.ziel.name.startswith("den ") else beste.ziel.name
    erstes, _, rest = name.partition(" ")
    if erstes.endswith("eren") and rest:
        name = f"{erstes[:-1]}r {rest}"              # "äußeren Top-Turm" -> "äußerer Top-Turm" (der Tausch zuerst)
    grund = f"sie sind {ZAHL.get(n, 'zu viert')} {AM[o.schl]}"
    h = Handlung("ABGEBEN_TAUSCHEN", beste.ziel, modus, beste.dauer, gewinn=beste.gewinn, folgewert=beste.folgewert,
                 gefahr_t=beste.gefahr_t, grund=grund, satz=f"{name[0].upper()}{name[1:]} jetzt: {grund}.",
                 schritte=list(beste.schritte))
    h.daten.update(dict(beste.daten))
    h.daten.update(objective=o.schl, spawn=spawn_zeit(m, o), tausch=beste.art, zieht=False)
    beste.daten["ersetzt"] = True          # der Tausch IST dieser Turm - nicht zweimal in der Liste
    return h


def handlungen(m, cfg: dict, modus: str, plan=None, tuerme: list[Handlung] | None = None) -> list[Handlung]:
    """Alle Objective-Handlungen dieses Takts - in OBJECTIVE, UNTERWEGS, GRUPPE und SEITE dieselben (Kapitel 5)."""
    aus = []
    for o in m.objectives:
        if (h := vorbereiten(m, cfg, modus, o, plan=plan)) is not None:
            aus.append(h)
        if (h := nehmen(m, cfg, modus, o)) is not None:
            aus.append(h)
        if (h := bestreiten(m, cfg, modus, o)) is not None:
            aus.append(h)
        if tuerme and (h := abgeben_tauschen(m, cfg, modus, o, tuerme)) is not None:
            aus.append(h)
    return aus


def kandidaten(m, cfg: dict, plan=None) -> list[Handlung]:
    """Modus OBJECTIVE (Kapitel 5): die Objective-Handlungen, BACK_JETZT nach Buch 3, HALTEN als stiller Grundplan und
    alle Turm-Handlungen der Karten-Rechnung - eine Liste nach EV (Kapitel 8). ZURUECK kommt aus dem Kern."""
    from .gruppe import _back_ohne_lane
    aus = [karte.halten("OBJECTIVE")]
    tuerme = karte.turm_handlungen(m, cfg, "OBJECTIVE", "MIT_GRUPPE", split=False)
    tuerme += karte.turm_handlungen(m, cfg, "OBJECTIVE", "DRUECKEN", split=False)
    aus += tuerme
    aus += handlungen(m, cfg, "OBJECTIVE", plan=plan, tuerme=tuerme)
    aus = [h for h in aus if not h.daten.get("ersetzt")]
    if not any(h.art in OBJ_ARTEN for h in aus):
        aus += _back_ohne_lane(m, cfg, "OBJECTIVE")
    return karte.umwandeln_zuerst(m, cfg, aus)
