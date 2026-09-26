"""Jungler-Tracking: wo der gegnerische Jungler angefangen hat, wo er jetzt wahrscheinlich ist,
und wann er zu dir kommt.

Reasoning (Carlos, Reasoning/LoL Reasoning.txt, Abschnitt 5): "Welche Position muss der
gegnerische Jungler wahrscheinlich einnehmen, damit sein naechster sinnvoller Play moeglich
wird? Das ist wesentlich staerker als bloss 'Jungler zuletzt Bot gesehen'."

Was wir wissen koennen (nur Minimap + API):
  - Sichtungen des Junglers (Zeit, Ort) - selten, aber jede zaehlt,
  - wann die gegnerischen Laner zuerst in ihrer Lane auftauchen: wer spaet kommt, hat
    geleasht, und der Jungler hat auf dieser Kartenseite angefangen,
  - die Spielzeit: 2026 spawnen die Camps um 0:55 (Buffs, Woelfe, Raptoren) bzw. 1:07.

Faustregeln 2026 (grundlagen.md, Jungler-Tracking; [Schaetzung aus 26.1-Spawns]):
  - 3 Camps fertig ~1:55-2:10, Full Clear ~2:55-3:15, Scuttle 2:55.
  - Start auf einer Seite -> der 3-Camp-Clear endet auf der ANDEREN: Level-3-Gank dort 2:00-2:40.
  - Full Clear endet ebenfalls auf der anderen Seite (~3:00-3:15, danach Scuttle/Gank dort);
    die Startseite ist bis ~3:30 ruhig.
Die Seite heisst hier wie auf der Karte: "oben" (Top, Larven/Herold/Baron) oder "unten"
(Bot, Drache) - fuer beide Teams gleich.

Camp-Positionen aus den Kartendaten, am 26.09.2026 auf ein Minimap-Bild gelegt: alle zwoelf
sitzen auf den Camp-Markern.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .zustand import BLAU, ROT, Partie, Spieler, gegenteam

BREITE, HOEHE = 14820.0, 14881.0

# Camps in Spiel-Einheiten, je Team (wessen Jungle)
CAMPS = {
    BLAU: {"Blau-Buff": (3821, 8101), "Gromp": (2288, 8448), "Wölfe": (3783, 6495),
           "Raptoren": (6823, 5508), "Rot-Buff": (7765, 4020), "Krugs": (8394, 2641)},
    ROT: {"Blau-Buff": (10984, 6960), "Gromp": (12671, 6306), "Wölfe": (11008, 8387),
          "Raptoren": (7986, 9471), "Rot-Buff": (7101, 10900), "Krugs": (6317, 12146)},
}
DREI_CAMPS = (115, 130)       # Spielzeit: 3 Camps fertig (1:55-2:10)
FULL_CLEAR = (175, 195)       # 2:55-3:15
START_BIS = 100               # Sichtungen bis 1:40 verraten die Startseite
LEASH_SPAET = 68              # Laner zuerst nach 1:08 in der Lane gesehen: hat vermutlich geleasht


def seite(x: float, y: float) -> str:
    """Minimap-Anteile -> 'oben' / 'unten' (Kartenseite, Trennung an der Mid-Lane)."""
    return "oben" if x + y < 1.0 else "unten"


def anders(s: str) -> str:
    return "unten" if s == "oben" else "oben"


LANE_SEITE = {"TOP": "oben", "BOTTOM": "unten", "UTILITY": "unten"}


@dataclass
class Jungletracker:
    sichtungen: list[tuple[float, float, float]] = field(default_factory=list)   # (Zeit, x, y) des Junglers
    start: str | None = None          # "oben"/"unten"
    start_grund: str = ""
    zuerst_in_lane: dict[str, float] = field(default_factory=dict)   # Rolle -> Spielzeit der ersten Sichtung
    _name: str | None = None

    def neu(self, p: Partie, lagebild) -> None:
        """Einmal je Takt: Sichtungen sammeln, Startseite schliessen."""
        if not p.ich or lagebild is None or not getattr(lagebild, "aktiv", False):
            return
        feind = gegenteam(p.mein_team)
        j = p.jungler(feind)
        if j is None:
            return
        self._name = j.champion
        if lagebild.sichtbar(j) and (g := lagebild.gesehen(j)):
            if not self.sichtungen or g[0] - self.sichtungen[-1][0] >= 1.0:
                self.sichtungen.append(g)
            if self.start is None and g[0] <= START_BIS and _im_eigenen_jungle(g[1], g[2], feind):
                self.start = seite(g[1], g[2])
                self.start_grund = f"bei {int(g[0] // 60)}:{int(g[0] % 60):02d} {self.start} gesehen"
        # Leash-Erkennung: welcher gegnerische Laner kam spaet in die Lane?
        for s in p.team(feind):
            if s.rolle in ("TOP", "BOTTOM", "UTILITY") and s.rolle not in self.zuerst_in_lane \
                    and lagebild.sichtbar(s) and (g := lagebild.gesehen(s)) and p.zeit >= 40:
                if _in_lane(g[1], g[2], s.rolle):
                    self.zuerst_in_lane[s.rolle] = g[0]
        if self.start is None and p.zeit <= 150:
            top, bot = self.zuerst_in_lane.get("TOP"), self.zuerst_in_lane.get("BOTTOM")
            if top is not None and bot is not None:
                if top >= LEASH_SPAET and bot < LEASH_SPAET - 10:
                    self.start, self.start_grund = "oben", "sein Toplaner kam spät"
                elif bot >= LEASH_SPAET and top < LEASH_SPAET - 10:
                    self.start, self.start_grund = "unten", "seine Botlane kam spät"

    def zuletzt(self) -> tuple[float, float, float] | None:
        return self.sichtungen[-1] if self.sichtungen else None

    def erste_gank_seite(self) -> str | None:
        """Die Kartenseite, auf der der erste Gank (Level 3 / nach dem Full Clear) droht."""
        return anders(self.start) if self.start else None

    def wahrscheinlich(self, zeit: float) -> dict[str, float]:
        """Wahrscheinlichkeit je Kartenseite ('oben'/'unten'), grob. Aus der letzten Sichtung
        (verblasst ueber ~90 s, er raeumt auf seiner Seite weiter) oder, vor der ersten Sichtung,
        aus der Startseite und den Clear-Zeiten."""
        z = self.zuletzt()
        if z is not None and zeit - z[0] < 90:
            dort = seite(z[1], z[2])
            bleibt = max(0.35, 1.0 - (zeit - z[0]) / 90)
            return {dort: bleibt, anders(dort): 1 - bleibt}
        if self.start and zeit <= 240:
            gank = anders(self.start)
            if zeit < DREI_CAMPS[0] - 20:
                return {self.start: 0.75, gank: 0.25}
            return {gank: 0.7, self.start: 0.3}
        return {"oben": 0.5, "unten": 0.5}

    def text(self, zeit: float, rolle: str) -> str:
        """Fuer Claude: was ueber den Jungler bekannt ist und was daraus folgt."""
        if not self._name:
            return ""
        teile = []
        if self.start:
            teile.append(f"Start {self.start} ({self.start_grund}) -> erster Gank wahrscheinlich {anders(self.start)}")
        if z := self.zuletzt():
            teile.append(f"zuletzt gesehen vor {int(zeit - z[0])} s {seite(z[1], z[2])}")
        w = self.wahrscheinlich(zeit)
        teile.append("jetzt wahrscheinlich " + ", ".join(f"{s} {int(p * 100)} %" for s, p in sorted(w.items(), key=lambda x: -x[1])))
        return f"JUNGLER {self._name}: " + "; ".join(teile)


def _im_eigenen_jungle(x: float, y: float, team: str) -> bool:
    """Jungle-Haelfte des Teams (Fluss: x = y auf der Minimap; blau unten links)."""
    return (y > x + 0.04) if team == BLAU else (x > y + 0.04)


def _in_lane(x: float, y: float, rolle: str) -> bool:
    if rolle == "TOP":
        return x < 0.14 or y < 0.14
    return x > 0.86 or y > 0.86
