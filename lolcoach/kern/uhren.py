"""Buch 15, Teil 2 (Auftrag 025, 1): die vier Uhren - Zahlen, die der Kern jeden Takt exakt rechnet und Claude nur
bekommt.

  - Gefahr-Uhr: T_gefahr (fruehester Angriff und wer), T_flucht (sicherer Ort), sicheres Fenster = T_gefahr - T_flucht
    - Marge. Sichtbare und ungesehene Gegner ueber `GegnerLage.ankunft` (Untergrenze ab der letzten Sichtung), tote
    ueber `respawnTimer` plus Weg vom Brunnen, einer im Back ueber seinen Brunnen (bewertung._gegner_lage).
  - Wellen-Uhr: naechste Welle und Kanone (wissen/wellen.toml, beobachtet: m.kanone_in), Back-Frist = Ankunft der
    Kanonenwelle - (Recall-Kanal + Einkauf + Weg Brunnen -> Lane).
  - Objective-Uhr: Spawn, dein Weg, Fenster der Gegner, Prio (ihre Lanes tot oder im Brunnen).
  - Ressourcen-Uhr: Leben und Trend, Gold bis zum naechsten Kauf, Flash, TP, Tote (nur API).
Wege: wissen/wege.toml (gemessen an Aufnahmen), sonst Luftlinie x WEGFAKTOR.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from ..bewertung import BRUNNEN, WEGFAKTOR, abstand

WISSEN = Path(__file__).resolve().parent.parent.parent / "wissen"


@lru_cache(maxsize=4)
def _toml(name: str) -> dict:
    try:
        return tomllib.loads((WISSEN / name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def cfg() -> dict:
    return _toml("uhren.toml")


def brunnen_lane(lane: str | None, team: str = "ORDER", tempo: float | None = None) -> float | None:
    """Laufzeit Brunnen -> eigener aeusserer Turm dieser Lane: Karte (Weg = Luftlinie x WEGFAKTOR) und Tempo
    (wissen/wege.toml tempo_median, gemessen 365). Die gemessenen brunnen_lane-Werte in wege.toml zaehlen erst ab dem
    Basisrand (blau Top 13,3 s) - fuer die Back-Frist zaehlt der ganze Weg ab dem Brunnen."""
    from ..bewertung import TUERME
    turm = TUERME.get((team, (lane or "").capitalize(), "aussen"))
    if turm is None or team not in BRUNNEN:
        return None
    t = tempo or float(_toml("wege.toml").get("tempo_median", 365.0))
    return abstand(BRUNNEN[team], turm) * WEGFAKTOR / t


def lane_objective(lane: str | None, obj: str) -> float | None:
    w = _toml("wege.toml").get("lane_objective") or {}
    return w.get(f"{(lane or '').lower()}_{obj}")


def naechste_welle(zeit: float) -> tuple[float, bool]:
    """(Spawnzeit der naechsten Welle, Kanone?) nach dem Spawn-Plan (wissen/wellen.toml)."""
    w = _toml("wellen.toml")
    erste = float(w.get("erste_welle_s", 30))
    takte = w.get("takt") or [[0, 30]]
    kanonen = w.get("kanone_jede") or [[0, 3]]
    t, n = erste, 1
    while t <= zeit:
        schritt = next(s for ab, s in reversed(takte) if t >= ab)
        t += schritt
        n += 1
    jede = next(k for ab, k in reversed(kanonen) if t >= ab)
    return t, n >= int(w.get("kanone_ab_welle", 3)) and n % jede == 0


@dataclass
class Uhren:
    zeit: float
    t_gefahr: float | None = None       # s bis zum fruehesten Angriff
    wer: str | None = None              # wer die Gefahr ist
    t_flucht: float | None = None       # s bis zum sicheren Ort
    sicher_ort: str | None = None
    fenster: float | None = None        # sicheres Fenster in s (< 0: jetzt raus)
    kanone_in: float | None = None      # s bis die naechste Kanone in deiner Lane ist
    back_spaetestens: float | None = None   # Spielzeit
    objectives: list = field(default_factory=list)   # (schl, spawn_in, dein Weg, Fenster der Gegner, Prio)
    gold_bis: tuple | None = None       # (Item, fehlendes Gold) oder (Item, 0) = kaufbar
    leben: float | None = None
    leben_trend: float | None = None
    flash: float | None = None
    tp: float | None = None
    tote_gegner: list = field(default_factory=list)  # (Champion, Respawn in s) - API

    def satz_sicher(self) -> str | None:
        """"sicher noch N s" mit dem, der die Gefahr ist - fuer Pakete mit Zeitbudget."""
        if self.fenster is None or self.wer is None:
            return None
        return f"{int(max(0, self.fenster))} Sekunden sicher, dann {self.wer}"


def rechnen(m, kern_cfg: dict | None = None, lagebild=None) -> Uhren | None:
    b = m.b if m is not None else None
    if b is None:
        return None
    c = cfg()
    u = Uhren(zeit=m.zeit, leben=m.leben, leben_trend=m.leben_trend, flash=b.flash, tp=m.tp_in,
              kanone_in=m.kanone_in)
    # Gefahr-Uhr
    kandidaten = []
    tempo = m.mein_tempo or 340.0
    tp_weg = {}
    z = getattr(lagebild, "zauber", None)
    if z is not None:
        tp_weg = {t.name: True for t in z.aktiv(m.zeit) if t.zauber == "SummonerTeleport"}
    for g in b.gegner:
        if g.s.tot:
            u.tote_gegner.append((g.champion, float(g.s.respawn or 0.0)))
            if b.pos is not None:
                brunnen = BRUNNEN.get(g.s.team)
                if brunnen is not None:
                    kandidaten.append((float(g.s.respawn or 0.0) + abstand(brunnen, b.pos) * WEGFAKTOR / 380.0,
                                       g.champion))
            continue
        if g.ankunft is None:
            continue
        a = g.ankunft
        # Auftrag 026, 3 (Budget-Treue 13 %): wer lange ungesehen ist, kann nah sein - vorher zaehlte er gar nicht
        # (192113 20:59 Pantheon nach 46 s, 231200 24:29 Gragas nach 68 s); er zaehlt jetzt mit hoechstens
        # unbekannt_min_s. Und ein TP aus der Basis ist in tp_s da (164809 18:19 Xerath)
        if (g.seit or 0.0) > float(c.get("unbekannt_s", 45.0)):
            a = min(max(a, float(c.get("unbekannt_min_s", 5.0))), float(c.get("unbekannt_min_s", 5.0)))
        if g.ort and "Basis" in g.ort and not g.sichtbar and "SummonerTeleport" in (g.s.zauber or ()) \
                and not tp_weg.get(g.s.name):
            a = min(a, float(c.get("tp_s", 6.0)))
        kandidaten.append((a, g.champion))
    if kandidaten:
        u.t_gefahr, u.wer = min(kandidaten)
    ort, t = b.sicherer_ort()
    u.sicher_ort, u.t_flucht = ort, t
    if u.t_gefahr is not None and u.t_flucht is not None:
        u.fenster = u.t_gefahr - u.t_flucht - float(c.get("marge_s", 2.0))
    # Wellen-Uhr: Back-Frist vor der Kanonenwelle
    rc = (kern_cfg or {}).get("recall") or {}
    weg = brunnen_lane(m.meine_lane, m.p.ich.team if m.p is not None and m.p.ich is not None else "ORDER")
    if m.kanone_in is not None and weg is not None:
        u.back_spaetestens = m.zeit + m.kanone_in - (float(rc.get("kanal_s", 8)) + float(rc.get("einkauf_s", 3)) + weg)
    # Objective-Uhr
    lane_weg = sum(1 for g in b.gegner if g.s.tot or (g.ort and "Basis" in g.ort))
    for o in m.objectives or []:
        u.objectives.append((o.schl, o.spawn_in, o.weg, o.fenster, lane_weg))
    # Ressourcen-Uhr
    k = getattr(b, "kauf", None)
    if k is not None:
        u.gold_bis = (k.kaufen[0], 0) if k.kaufen else (k.naechstes if k.naechstes else None)
    return u
