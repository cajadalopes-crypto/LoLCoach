"""Buch 15, Teil 0 (Auftrag 025, 0): Events - Erkennung und Erahnung, jeden Takt.

Ein Event ist alles, was im Spiel stattfindet (erkannt) oder gleich stattfinden kann (erahnt). Jede Erkennung ist eine
kleine Funktion `_<gruppe>(...) -> list[Event]`; der Katalog ist offen - ein neuer Typ ist eine neue Funktion in
`ERKENNER`. Quellen: API (Tod, Respawn, Kills, Strukturen, Level, Gold), Minimap (Orte, Sprünge), HUD (Leben,
Zauber), und die Unterschiede zwischen zwei Takten.

Erahnte Events (Typ "ERAHNT_...") tragen `p` und `eta` in den Daten. `p` ist die gemessene Eintrittsquote je Typ aus
wissen/events.toml (werkzeuge/pakete_messen.py eicht sie an den Aufnahmen); ein Typ unter `still_unter` (0,6) bleibt
still - er wird gefuehrt und gemessen, aber nie gesagt und nie abgewogen.
"""
from __future__ import annotations

import tomllib
from collections import deque
from functools import lru_cache
from pathlib import Path

from ..bewertung import abstand
from .ereignisquellen import Event, LaneQuelle, TodQuelle, ZauberQuelle

WISSEN = Path(__file__).resolve().parent.parent.parent / "wissen" / "events.toml"
GRUPPE = {"TOD": "Tod", "RESPAWN": "Tod", "FLASH_WEG": "Zauber", "FLASH_BEREIT": "Zauber", "TP_WEG": "Zauber",
          "TP_BEREIT": "Zauber", "QUEST_TP_WEG": "Zauber", "QUEST_TP_BEREIT": "Zauber", "KAMPF": "Kampf",
          "OBJ_BALD": "Objective", "OBJ_DA": "Objective", "OBJ_GENOMMEN": "Objective", "TURM_FAELLT": "Struktur",
          "INHIB_FAELLT": "Struktur", "PLATTEN_ENDE_BALD": "Zeit", "WELLE": "Welle", "KANONE_BALD": "Welle",
          "GESEHEN": "Position", "IN_DEINEM_JUNGLE": "Position", "LANE_WEG": "Position", "LANE_ZURUECK": "Position",
          "GOLD_SPIKE": "Ressourcen", "LEVEL_SPIKE": "Ressourcen", "MITSPIELER_BACK": "Team",
          "ERAHNT_KAMPF": "Kampf", "ERAHNT_GANK": "Position", "ERAHNT_LANE_BACK": "Position",
          "ERAHNT_RUECKKEHR": "Tod"}
KAMPF_BEI = 1200.0          # ein sichtbarer Gegner so nah an einem Mitspieler: dort wird gekaempft (welt.KAMPF_BEI)
GESEHEN_NACH_S = 20.0       # ein Gegner, der so lange weg war, "taucht auf"
OBJ_BALD_S = 60.0
ERAHNT_HALTEN_S = 20.0     # so lange muss die Bedingung einer Erahnung fehlen, bis sie neu gelten darf
PLATTEN_ENDE = 14 * 60.0    # Plattenzeit endet (Buch 15, 2.2; wissen/wellen.toml)
STRUKTUR = {"TurretKilled": "TURM_FAELLT", "InhibKilled": "INHIB_FAELLT", "DragonKill": "OBJ_GENOMMEN",
            "HeraldKill": "OBJ_GENOMMEN", "BaronKill": "OBJ_GENOMMEN", "HordeKill": "OBJ_GENOMMEN"}
OBJ_VON = {"DragonKill": "drache", "HeraldKill": "herold", "BaronKill": "baron", "HordeKill": "larven"}


@lru_cache(maxsize=1)
def eichung() -> dict:
    try:
        return tomllib.loads(WISSEN.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def p_von(typ: str) -> float | None:
    """Gemessene Eintrittsquote eines erahnten Typs (None: nicht geeicht)."""
    return (eichung().get("erahnung") or {}).get(typ, {}).get("quote")


def still(typ: str) -> bool:
    """Buch 15, 0.2: eine Erahnung, die an den Aufnahmen unter 60 % eintrat (oder nie geeicht wurde), bleibt still."""
    p = p_von(typ)
    return p is None or p < float(eichung().get("still_unter", 0.6))


def wert(e: Event, schl: str, vorgabe=None):
    return dict(e.daten).get(schl, vorgabe)


class EventErkenner:
    def __init__(self):
        self.tod, self.lane, self.zauber = TodQuelle(), LaneQuelle(), ZauberQuelle()
        self.liste: deque = deque(maxlen=300)          # die letzten Events (erkannt und erahnt)
        self.erahnt_offen: dict = {}                   # Typ+Ziel -> Event, solange die Erahnung gilt
        self._erahnt_zuletzt: dict = {}
        self._obj: dict = {}
        self._welle: str | None = None
        self._kanone: float | None = None
        self._gesehen: dict = {}
        self._jungle_zuletzt: dict = {}
        self._kampf: tuple | None = None
        self._kauf = False
        self._level: int | None = None
        self._ids: set = set()
        self._basis: dict = {}
        self._platten_gesagt = False

    def takt(self, m, p, lb) -> list[Event]:
        """Die Events dieses Takts (erkannt, dann erahnt)."""
        if m is None or m.b is None or p is None:
            return []
        aus: list[Event] = []
        for f in ERKENNER:
            try:
                aus += f(self, m, p, lb)
            except Exception:
                continue                               # eine kaputte Erkennung darf die anderen nicht mitreissen
        aus += self._erahnen(m, p)
        self.liste.extend(aus)
        return aus

    def seit(self, zeit: float, s: float = 15.0, gruppe: str | None = None) -> list[Event]:
        return [e for e in self.liste if zeit - s <= e.zeit <= zeit + 0.5
                and (gruppe is None or GRUPPE.get(e.typ) == gruppe)]

    # --- Erkennung -----------------------------------------------------------------------------------------------

    def _quellen(self, m, p, lb) -> list[Event]:
        return self.tod.takt(p) + self.lane.takt(m.b, m.zeit) + self.zauber.takt(lb, p, m.zeit, m.tp_in)

    def _kampf_ev(self, m, p, lb) -> list[Event]:
        """Ein Mitspieler kaempft (sichtbarer Gegner <= KAMPF_BEI an ihm) - neu, wenn vorher dort keiner war."""
        from .pakete import kampf_auffaellig            # Laning ist kein Kampf-Event (Messung 025)
        k = kampf_auffaellig(m)
        if k is None:
            return []
        weg, freunde, feinde, ort = k
        wo = next((w for s, w, *_ in m.b.mitspieler or [] if freunde and s.champion == freunde[0]), None)
        if wo is None:
            return []
        if self._kampf is not None and abstand(self._kampf[0], wo) <= 2500 and m.zeit - self._kampf[1] <= 10:
            self._kampf = (wo, m.zeit)
            return []
        self._kampf = (wo, m.zeit)
        return [Event("KAMPF", ort, (*freunde, *feinde), m.zeit, 0.8, (("weg", weg), ("pos", wo)))]

    def _objective(self, m, p, lb) -> list[Event]:
        aus = []
        for o in m.objectives or []:
            vorher = self._obj.get(o.schl)
            if vorher is not None:
                if not o.lebt and vorher[1] > OBJ_BALD_S >= o.spawn_in:
                    aus.append(Event("OBJ_BALD", o.schl, (o.schl,), m.zeit, 1.0, (("eta", o.spawn_in), ("weg", o.weg))))
                if o.lebt and not vorher[0]:
                    aus.append(Event("OBJ_DA", o.schl, (o.schl,), m.zeit, 1.0, (("weg", o.weg),)))
            self._obj[o.schl] = (o.lebt, o.spawn_in)
        return aus

    def _struktur(self, m, p, lb) -> list[Event]:
        aus = []
        for e in p.ereignisse:
            if e.id in self._ids or e.art not in STRUKTUR:
                continue
            self._ids.add(e.id)
            wir = e.team == p.mein_team
            was = OBJ_VON.get(e.art) or e.daten.get("TurretKilled") or e.daten.get("InhibKilled") or e.art
            aus.append(Event(STRUKTUR[e.art], was, (was,), e.zeit, 1.0, (("wir", wir),)))
        if not self._platten_gesagt and PLATTEN_ENDE - 30.0 <= m.zeit < PLATTEN_ENDE:
            self._platten_gesagt = True
            aus.append(Event("PLATTEN_ENDE_BALD", None, (), m.zeit, 1.0, (("eta", PLATTEN_ENDE - m.zeit),)))
        return aus

    def _welle_ev(self, m, p, lb) -> list[Event]:
        aus = []
        w = m.welle
        if w is not None and w.zustand != self._welle and w.frisch:
            if self._welle is not None:
                aus.append(Event("WELLE", w.lane, (w.lane,), m.zeit, 0.7, (("zustand", w.zustand),)))
            self._welle = w.zustand
        k = m.kanone_in
        if k is not None and self._kanone is not None and self._kanone > 20.0 >= k:
            aus.append(Event("KANONE_BALD", m.meine_lane, (), m.zeit, 0.9, (("eta", k),)))
        self._kanone = k
        return aus

    def _position(self, m, p, lb) -> list[Event]:
        aus = []
        for g in m.b.gegner:
            if g.s.tot:
                continue
            if g.sichtbar:
                zuletzt = self._gesehen.get(g.champion)
                if zuletzt is not None and m.zeit - zuletzt >= GESEHEN_NACH_S:
                    aus.append(Event("GESEHEN", g.ort, (g.champion,), m.zeit, 0.8, (("weg_s", m.zeit - zuletzt),)))
                self._gesehen[g.champion] = m.zeit
                if g.ort and "eurem" in g.ort and m.zeit - self._jungle_zuletzt.get(g.champion, -1e9) >= 30.0:
                    self._jungle_zuletzt[g.champion] = m.zeit
                    aus.append(Event("IN_DEINEM_JUNGLE", g.ort, (g.champion,), m.zeit, 0.8))
            elif g.champion not in self._gesehen and g.seit is not None:
                self._gesehen[g.champion] = m.zeit - g.seit
        return aus

    def _ressourcen(self, m, p, lb) -> list[Event]:
        aus = []
        k = getattr(m.b, "kauf", None)
        jetzt = bool(k is not None and k.kaufen)
        if jetzt and not self._kauf:
            aus.append(Event("GOLD_SPIKE", None, (p.ich.champion,), m.zeit, 1.0, (("item", k.kaufen[0]),)))
        self._kauf = jetzt
        lv = p.ich.level if p.ich is not None else None
        if lv is not None and self._level is not None and lv > self._level and lv in (6, 11, 16):
            aus.append(Event("LEVEL_SPIKE", None, (p.ich.champion,), m.zeit, 1.0, (("level", lv),)))
        self._level = lv
        return aus

    def _team(self, m, p, lb) -> list[Event]:
        aus = []
        for s, wo, le, ort in m.b.mitspieler or []:
            basis = bool(ort and "Basis" in ort) and not s.tot
            if basis and self._basis.get(s.champion) is False:
                aus.append(Event("MITSPIELER_BACK", ort, (s.champion,), m.zeit, 0.7))
            self._basis[s.champion] = basis if not s.tot else None
        return aus

    # --- Erahnung (Buch 15, 0.2) -----------------------------------------------------------------------------------

    def _erahnen(self, m, p) -> list[Event]:
        """Kandidaten dieses Takts; ein Event nur, wenn die Erahnung NEU gilt (steigende Flanke je Typ und Ziel)."""
        jetzt: dict = {}
        b = m.b
        for o in m.objectives or []:
            if (o.lebt or o.spawn_in <= 40.0) and o.team_nah + o.team_erreicht >= 2 and o.fenster is not None \
                    and o.fenster <= 25.0:
                jetzt[("ERAHNT_KAMPF", o.schl)] = Event("ERAHNT_KAMPF", o.schl, (o.schl,), m.zeit, 0.0,
                                                        (("eta", max(o.spawn_in, o.fenster)), ("pos", o.pos)))
        j = b.jungler
        w = m.welle
        if j is not None and not j.s.tot and not j.sichtbar and (j.seit or 0) >= 20.0 \
                and (m.p_jungler or 0.0) >= 0.5 and w is not None and w.front is not None and w.front >= 0.55 \
                and m.lane_phase:
            jetzt[("ERAHNT_GANK", j.champion)] = Event("ERAHNT_GANK", m.meine_lane, (j.champion,), m.zeit, 0.0,
                                                       (("eta", max(3.0, j.ankunft or 15.0)),))
        g = b.lane
        if g is not None and g.sichtbar and not g.s.tot and g.leben is not None and g.leben <= 0.35 \
                and not m.im_kampf:
            jetzt[("ERAHNT_LANE_BACK", g.champion)] = Event("ERAHNT_LANE_BACK", g.ort, (g.champion,), m.zeit, 0.0,
                                                            (("eta", 15.0),))
        if g is not None and g.s.tot and 0 < (g.s.respawn or 0) <= 15.0:
            from .uhren import brunnen_lane
            eta = g.s.respawn + (brunnen_lane(m.meine_lane, g.s.team) or 30.0)
            jetzt[("ERAHNT_RUECKKEHR", g.champion)] = Event("ERAHNT_RUECKKEHR", m.meine_lane, (g.champion,), m.zeit,
                                                            0.0, (("eta", eta),))
        neu = []
        for k, e in jetzt.items():
            if k not in self.erahnt_offen:
                q = p_von(e.typ)
                e = Event(e.typ, e.ort, e.beteiligte, e.zeit, q if q is not None else 0.0,
                          e.daten + (("p", q), ("still", still(e.typ))))
                neu.append(e)
                self.erahnt_offen[k] = e
            self._erahnt_zuletzt[k] = m.zeit
        # eine Erahnung gilt weiter, bis ihre Bedingung ERAHNT_HALTEN_S lang fehlt (kein Flackern, keine Doppelzaehlung)
        for k in [k for k in self.erahnt_offen if m.zeit - self._erahnt_zuletzt.get(k, -1e9) > ERAHNT_HALTEN_S]:
            del self.erahnt_offen[k]
        return neu


ERKENNER = (EventErkenner._quellen, EventErkenner._kampf_ev, EventErkenner._objective, EventErkenner._struktur,
            EventErkenner._welle_ev, EventErkenner._position, EventErkenner._ressourcen, EventErkenner._team)
