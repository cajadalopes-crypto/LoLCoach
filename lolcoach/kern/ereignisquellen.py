"""Event-Quellen (Buch 15, Teil 0; Auftrag 024, 1): kleine Objekte, deren `takt(...)` die Events dieses Takts liefert.
Jedes Event hat Typ, Ort, Beteiligte, Zeit und Sicherheit (1.0 = API, darunter Bild oder Schluss). 025 haengt die
Quellen in kern/events.py ein; bis dahin nutzen Stratege und Pruefung die Stand-Funktionen (`tot`, `anwesenheit`).

  - TodQuelle: Tod und Respawn aller zehn aus der API (`isDead`, `respawnTimer`) - die Anzeigetafel, keine eigene
    Uhr. 231200 2:57 "Jetzt, wo Xerath tot ist" (lebte seit 2:52) und 7:56 "Gragas tot" (lebte seit 7:41).
  - LaneQuelle: Lane-Gegner da / weg / zurueck. 231200 5:56 "Udyr ist weg": er war 25 s ungesehen, stand aber auf
    seiner Lane - Riven lief erst hoch und war 6700 Einheiten weg, sah die Lane also gar nicht.
  - ZauberQuelle: Flash und TP der Gegner verbraucht oder wieder bereit, dein Quest-TP verbraucht oder bereit.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..bewertung import abstand

WEG_S = 20.0        # so lange ungesehen, bevor "weg" ueberhaupt in Frage kommt
SICHT = 1200.0      # so nah siehst du einen Gegner selbst (Champion-Sicht)
LANE_HALTEN_S = 3.0     # so lange muss "weg" gelten, bis LANE_WEG kommt
VERDECKT = 400.0    # so nah verdeckt dein Icon seins auf der Minimap - dann ist "ungesehen" kein Beleg
LANE_ORT = {"TOP": ("oben",), "MIDDLE": ("auf der Mid-Lane", "in der Flussmitte"), "BOTTOM": ("unten",),
            "UTILITY": ("unten",)}
ZAUBER = {"SummonerFlash": "FLASH", "SummonerTeleport": "TP"}


@dataclass(frozen=True)
class Event:
    typ: str                       # "TOD", "RESPAWN", "LANE_WEG", "LANE_ZURUECK", "FLASH_WEG", "TP_BEREIT", ...
    ort: str | None
    beteiligte: tuple[str, ...]
    zeit: float
    sicherheit: float              # 1.0 = API; Bild/Schluss darunter
    daten: tuple = ()              # (Schluessel, Wert)-Paare, z. B. (("respawn_in", 12.0),)


# --- Tod und Respawn -------------------------------------------------------------------------------------------------

def tot(p, champion: str) -> bool | None:
    """Laut API tot? None: Champion nicht in der Partie."""
    for s in getattr(p, "spieler", ()) or ():
        if s.champion == champion:
            return bool(s.tot)
    return None


class TodQuelle:
    def __init__(self):
        self._tot: dict[str, bool] = {}

    def takt(self, p) -> list[Event]:
        aus = []
        for s in p.spieler:
            war = self._tot.get(s.name)
            if war is not None and bool(s.tot) != war:
                if s.tot:
                    aus.append(Event("TOD", None, (s.champion,), p.zeit, 1.0,
                                     (("respawn_in", float(s.respawn or 0.0)), ("team", s.team))))
                else:
                    aus.append(Event("RESPAWN", "Basis", (s.champion,), p.zeit, 1.0, (("team", s.team),)))
            self._tot[s.name] = bool(s.tot)
        return aus


# --- Lane-Gegner ------------------------------------------------------------------------------------------------------

def anwesenheit(b) -> str | None:
    """Wo der Lane-Gegner ist: 'da', 'vermutlich da', 'weg', 'tot' - None ohne Lane-Gegner.
    'weg' nur mit Beleg: zuletzt ausserhalb seiner Lane gesehen, oder >= WEG_S ungesehen, obwohl du dort stehst,
    wo du ihn sehen muesstest (naeher als SICHT, aber nicht so nah, dass dein Icon seins verdeckt)."""
    g = getattr(b, "lane", None)
    if g is None:
        return None
    if g.s.tot:
        return "tot"
    auf_lane = g.ort in LANE_ORT.get(g.s.rolle or "", ())
    if g.sichtbar:
        return "da"                  # zu sehen ist nicht weg - auch im Fluss neben der Lane (Messung 025)
    if g.seit is None or g.pos is None:
        return "vermutlich da"
    if not auf_lane:
        return "weg" if g.seit >= 5.0 else "da"
    if g.seit < WEG_S:
        return "da"
    d = abstand(b.pos, g.pos) if getattr(b, "pos", None) is not None else None
    if d is not None and VERDECKT < d <= SICHT:
        return "weg"
    return "vermutlich da"


class LaneQuelle:
    """LANE_WEG erst, wenn "weg" LANE_HALTEN_S lang gilt (Minimap-Flackern ist kein Roam)."""

    def __init__(self):
        self._war: str | None = None
        self._kand: tuple[str, float] | None = None

    def takt(self, b, zeit: float) -> list[Event]:
        roh = anwesenheit(b)
        if roh != self._war and roh in ("weg", "tot") and self._war not in ("weg", "tot") and roh != "tot":
            if self._kand is None or self._kand[0] != roh:
                self._kand = (roh, zeit)
            if zeit - self._kand[1] < LANE_HALTEN_S:
                return []
        self._kand = None
        jetzt = roh
        aus = []
        if jetzt is not None and self._war is not None:
            name = (b.lane.champion,)
            weg = jetzt in ("weg", "tot")
            if weg and self._war not in ("weg", "tot"):
                aus.append(Event("LANE_WEG", b.lane.ort or None, name, zeit, 1.0 if jetzt == "tot" else 0.7,
                                 (("wie", jetzt),)))
            elif jetzt == "da" and self._war in ("weg", "tot"):
                aus.append(Event("LANE_ZURUECK", b.lane.ort or None, name, zeit, 0.9))
        if jetzt is not None:
            self._war = jetzt
        return aus


# --- Zauber -----------------------------------------------------------------------------------------------------------

class ZauberQuelle:
    """Flash/TP der Gegner aus den Zaubertimern des Lagebilds (Chat oder Minimap), dein Quest-TP aus `m.tp_in`."""

    def __init__(self):
        self._gesehen: set = set()
        self._offen: dict = {}
        self._tp_bereit: bool | None = None

    def takt(self, lb, p, zeit: float, tp_in: float | None = None) -> list[Event]:
        aus = []
        z = getattr(lb, "zauber", None)
        feinde = {s.name for s in p.gegner()} if p is not None else set()
        for t in list(getattr(z, "timer", {}).values()):
            art = ZAUBER.get(t.zauber)
            schl = (t.name, t.zauber, round(t.seit))
            if art is None or t.name not in feinde or schl in self._gesehen:
                continue
            self._gesehen.add(schl)
            self._offen[schl] = t
            aus.append(Event(f"{art}_WEG", None, (t.champion,), t.seit, 0.9 if t.quelle == "Chat" else 0.7,
                             (("zurueck", t.zurueck), ("quelle", t.quelle))))
        for schl, t in list(self._offen.items()):
            if zeit >= t.zurueck:
                del self._offen[schl]
                aus.append(Event(f"{ZAUBER[t.zauber]}_BEREIT", None, (t.champion,), t.zurueck, 0.6))
        if tp_in is not None:
            bereit = tp_in <= 0
            if self._tp_bereit is not None and bereit != self._tp_bereit:
                ich = (p.ich.champion,) if p is not None and p.ich is not None else ()
                aus.append(Event("QUEST_TP_BEREIT" if bereit else "QUEST_TP_WEG", None, ich, zeit, 0.8,
                                 (("bereit_in", max(0.0, tp_in)),)))
            self._tp_bereit = bereit
        return aus
