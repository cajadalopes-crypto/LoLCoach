"""Die Makro-Lage: alles, was die 111 Entscheidungen lesen. Reine Daten - gefuellt live (Stufe 4) oder im Test.

Koordinaten in Spiel-Einheiten (wie lolcoach/bewertung.py). Zeiten in Sekunden. Rollen wie die Live-API
(TOP JUNGLE MIDDLE BOTTOM UTILITY). "Unbekannt" ist None, nie ein geratener Wert.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..bewertung import BRUNNEN, TUERME, abstand

LANE_DER_ROLLE = {"TOP": "top", "MIDDLE": "mid", "BOTTOM": "bot", "UTILITY": "bot", "JUNGLE": None}
GRUBEN = {"drache": (9866, 4414), "elder": (9866, 4414), "baron": (5007, 10471), "herold": (5007, 10471),
          "larven": (5007, 10471)}
LANE_MITTE = {"top": (1800, 12900), "mid": (7400, 7400), "bot": (12900, 1800)}


@dataclass
class Spieler:
    champion: str = ""
    rolle: str = ""
    lebt: bool = True
    respawn: float = 0.0                  # s bis zur Wiederbelebung (API respawnTimer)
    pos: tuple[float, float] | None = None   # Mitspieler/ich: jetzt; Gegner: zuletzt gesehen
    gesehen_vor: float | None = 0.0       # Gegner: s seit zuletzt gesehen (0 = sichtbar, None = nie)
    level: int = 1
    leben: float = 1.0                    # Anteil
    flash_in: float | None = 0.0          # s bis Flash bereit (0 = bereit, None = unbekannt)
    ult_bereit: bool | None = True
    tp_hat: bool = False
    tp_in: float | None = None            # s bis TP bereit (0 = bereit, None = unbekannt)
    im_brunnen: bool = False
    backt: bool = False                   # Recall gesehen bzw. Richtung Basis verschwunden
    spike_neu: bool = False               # gerade Level 6 oder Item fertig
    tempo: float = 365.0
    smite_bereit: bool | None = None

    @property
    def bekannt(self) -> bool:
        return not self.lebt or (self.gesehen_vor is not None and self.gesehen_vor <= 8)


@dataclass
class Welle:
    stand: str | None = None              # "bei_uns", "mitte", "bei_ihnen", "gecrasht" (eben in ihren Turm); None = unbekannt
    groesse: int = 0                      # Vasallen-Vorteil: + = unsere Welle groesser
    kanone_in: float | None = None        # s bis die naechste Kanone in dieser Lane ist


@dataclass
class Monster:
    art: str                              # drache, elder, larven, herold, baron
    spawn_in: float                       # s bis Spawn, 0 = steht
    seele: bool = False                   # Seelen-Drache
    kopfgeld: bool = False                # Objective-Kopfgeld fuer uns aktiv


@dataclass
class Ward:
    ort: str
    pos: tuple[float, float] | None = None
    rest_s: float = 90.0
    art: str = "gelb"


@dataclass
class Kampf:
    pos: tuple[float, float]
    in_s: float = 0.0                     # 0 = laeuft
    dauer_s: float = 10.0
    wir: int = 0                          # eigene Champions dort (ohne dich)
    gegner: int = 0
    bei: str = ""                         # "Baron", "Drache", Mitspieler ...


@dataclass
class Hirn:
    """Ergebnis von werkzeuge/challenger/gehirn.py: bewerte() und lage_info()."""
    optionen: list = field(default_factory=list)   # (aktion, ziel, wert, p_highelo, gefahr, klarheit, grund)
    siegchance: float | None = None
    jungler: dict = field(default_factory=dict)    # Bereich -> Wahrscheinlichkeit
    jungler_unsicher: float | None = None

    @property
    def klarheit(self) -> str | None:
        return self.optionen[0][5] if self.optionen else None

    def option(self, aktion: str, ziel: str | None = None):
        for o in self.optionen:
            if o[0] == aktion and (ziel is None or o[1] == ziel):
                return o
        return None

    def wert(self, aktion: str, ziel: str | None = None) -> float | None:
        o = self.option(aktion, ziel)
        return None if o is None else o[2]

    def beste(self):
        return self.optionen[0] if self.optionen else None

    def jungler_seite(self) -> str | None:
        """'oben' / 'unten', wenn die Jungler-Karte klar ist (>= 60 %)."""
        oben = sum(p for b, p in self.jungler.items() if "oben" in b or b == "Toplane")
        unten = sum(p for b, p in self.jungler.items() if "unten" in b or b == "Botlane")
        if oben >= 0.6:
            return "oben"
        if unten >= 0.6:
            return "unten"
        return None


@dataclass
class MakroLage:
    zeit: float = 600.0
    team: str = "ORDER"
    ich: Spieler = field(default_factory=lambda: Spieler(champion="Ambessa", rolle="TOP", pos=(2200, 12000)))
    gold: int = 0
    trinket: str = "gelb"                 # gelb, linse, blau
    trinket_ladungen: int | None = None   # HUD - fehlt heute
    kontrollauge_inventar: bool = False
    kontrollauge_gesetzt: bool = False
    spike_fehlt: int | None = None        # Gold, das zum naechsten Spike-Bauteil fehlt (0 = kaufbar; Kaufplan)
    mitspieler: list[Spieler] = field(default_factory=list)
    gegner: list[Spieler] = field(default_factory=list)
    wellen: dict[str, Welle] = field(default_factory=dict)
    monster: list[Monster] = field(default_factory=list)
    wards: list[Ward] = field(default_factory=list)
    ward_verloren: str | None = None      # eigener Ward eben verschwunden (Ort)
    tuerme_weg: list[tuple[str, str, str]] = field(default_factory=list)   # (team, lane, stufe) gefallen, neueste zuerst
    turm_gefallen_vor: float | None = None  # s seit dem letzten gefallenen Turm
    gegner_platten: dict[str, int] = field(default_factory=dict)   # Lane -> Platten am gegnerischen Aussenturm
    inhib_offen_gegner: list[str] = field(default_factory=list)
    inhib_offen_wir: list[str] = field(default_factory=list)
    ereignisse: list[tuple[str, str, float]] = field(default_factory=list)  # (art, wer, vor_s): ace/kampf/kill/tod/objective/tp/turm
    kampf: Kampf | None = None
    hirn: Hirn = field(default_factory=Hirn)
    plan: dict = field(default_factory=dict)   # was andere Entscheidungen vorhaben: back, split, tp, roam, objective
    wir_skalieren: bool | None = None      # Siegbedingung aus der Aufstellung
    spike_wir: bool = False
    spike_gegner: bool = False
    gesehen_busch: bool | None = None      # der Busch vor dir ist unbekannt (Face-Check-Lage)

    # ---- abgeleitet
    @property
    def minute(self) -> float:
        return self.zeit / 60

    @property
    def lane(self) -> str | None:
        return LANE_DER_ROLLE.get(self.ich.rolle)

    @property
    def gegnerteam(self) -> str:
        return "CHAOS" if self.team == "ORDER" else "ORDER"

    def welle(self, lane: str | None = None) -> Welle:
        return self.wellen.get(lane or self.lane or "", Welle())

    def rolle(self, liste: list[Spieler], rolle: str) -> Spieler | None:
        return next((s for s in liste if s.rolle == rolle), None)

    @property
    def lane_gegner(self) -> Spieler | None:
        return self.rolle(self.gegner, self.ich.rolle)

    @property
    def gegner_jungler(self) -> Spieler | None:
        return self.rolle(self.gegner, "JUNGLE")

    @property
    def unser_jungler(self) -> Spieler | None:
        return self.rolle(self.mitspieler, "JUNGLE")

    def unbekannt(self, alter: float = 15.0) -> list[Spieler]:
        """Lebende Gegner, die seit mehr als `alter` s nicht gesehen wurden (oder nie)."""
        return [g for g in self.gegner if g.lebt and (g.gesehen_vor is None or g.gesehen_vor > alter)]

    def tote(self, liste: list[Spieler]) -> list[Spieler]:
        return [s for s in liste if not s.lebt]

    def mon(self, art: str) -> Monster | None:
        return next((m for m in self.monster if m.art == art), None)

    def naechstes_monster(self) -> Monster | None:
        return min(self.monster, key=lambda m: m.spawn_in, default=None)

    def ereignis(self, art: str, wer: str | None = None, max_alter: float = 30.0):
        return next((e for e in self.ereignisse if e[0] == art and (wer is None or e[1] == wer) and e[2] <= max_alter), None)

    def abstand_zu(self, pos) -> float | None:
        return None if self.ich.pos is None or pos is None else abstand(self.ich.pos, pos)

    def mitspieler_bei(self, pos, r: float = 2500) -> list[Spieler]:
        return [s for s in self.mitspieler if s.lebt and s.pos and abstand(s.pos, pos) <= r]

    def gegner_nah(self, r: float = 1500, alter: float = 5.0) -> list[Spieler]:
        if self.ich.pos is None:
            return []
        return [g for g in self.gegner if g.lebt and g.pos and g.gesehen_vor is not None and g.gesehen_vor <= alter
                and abstand(g.pos, self.ich.pos) <= r]

    @property
    def brunnen(self):
        return BRUNNEN[self.team]

    def eigener_turm(self, lane: str | None = None, stufe: str = "aussen"):
        l = (lane or self.lane or "top").capitalize()
        return TUERME.get((self.team, l, stufe))

    def gegner_turm(self, lane: str | None = None, stufe: str = "aussen"):
        l = (lane or self.lane or "top").capitalize()
        return TUERME.get((self.gegnerteam, l, stufe))

    def tief(self) -> bool:
        """Steht vor der Mitte der eigenen Lane (Richtung Gegner)."""
        if self.ich.pos is None or self.lane is None:
            return False
        t_eig, t_geg = self.eigener_turm(), self.gegner_turm()
        return t_eig is not None and t_geg is not None and abstand(self.ich.pos, t_geg) < abstand(self.ich.pos, t_eig)
