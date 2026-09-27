"""Merkmale: was der Kern liest (Buch 0, Kapitel 4). Duenn - rechnet nur, was die Bewertung nicht schon hat.

Schritt 2: Bereich, Lane-Phase, Verlauf (20 s), Leben-Trend, im Kampf, alle Objectives mit eigener Laufzeit und
Mitspielern an der Grube, Fenster der Gegner (bewertung.verteidiger_ab), Bedrohung eigener Strukturen, frische
Daten. Das Gefahr-Modell (Kapitel 7.5) kommt in Schritt 3. Jedes Merkmal darf None sein (Kapitel 4.3)."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .. import bewertung, minimap
from ..bewertung import BRUNNEN, GRUBEN, TUERME, WEGFAKTOR, abstand, einheiten
from ..zustand import BLAU, ROT, gegenteam

OBJ_GRUBE = {"drache": "drache", "baron": "baron", "herold": "baron", "larven": "baron"}   # Grube je Objective
LANE_DER_ROLLE = bewertung.LANE_DER_ROLLE
NEXUS = {BLAU: (1700.0, 1700.0), ROT: (13100.0, 13100.0)}   # grob; Bedrohung wird mit 2500 Radius geprueft
VERLAUF_S = 20.0


@dataclass
class ObjectiveLage:
    schl: str                    # drache / baron / herold / larven
    lebt: bool
    spawn_in: float              # Sekunden bis zum Spawn (0, wenn es lebt)
    pos: tuple[float, float]
    weg: float | None            # deine Laufzeit zur Grube
    team_nah: int                # Mitspieler an der Grube (grube_radius)
    team_erreicht: int           # Mitspieler, die in objective_nah_s an der Grube sein koennen (Tempo 380)
    fenster: float | None        # bis der erste bekannte Gegner dort sein kann
    unbekannt: int               # Gegner, deren Ort niemand kennt


@dataclass
class Merkmale:
    zeit: float
    tot: bool
    pos: tuple[float, float] | None
    bereich: str | None          # lane_eigen, lane:<Top/Mid/Bot>, fluss_oben/unten/mitte, jungle_eigen_oben/unten,
    #                              jungle_fremd_oben/unten, basis_eigen, basis_fremd, grube:<drache/baron>
    meine_lane: str | None       # Top / Mid / Bot (aus der Rolle)
    lane_phase: bool
    leben: float | None
    leben_trend: float | None    # Aenderung deines Lebens in den letzten 3 s
    im_kampf: bool
    gegner_im_radius: bool = False   # ein lebender Gegner sichtbar in kampf_radius (ohne ihn ist ein Kampf entschieden)
    objectives: list[ObjectiveLage] = field(default_factory=list)
    mitspieler: list = field(default_factory=list)       # (Spieler, Spiel-Einheiten)
    bedrohung: list = field(default_factory=list)        # (Struktur in Worten, Position, deine Laufzeit)
    daten_frisch: bool = True
    mein_tempo: float = 340.0

    def team_nah(self, ziel: tuple[float, float] | None, radius: float) -> int:
        if ziel is None:
            return 0
        return sum(1 for _, wo in self.mitspieler if wo is not None and abstand(wo, ziel) <= radius)

    def weg(self, ziel: tuple[float, float]) -> float | None:
        """Deine Laufzeit (Luftlinie x WEGFAKTOR / dein Tempo), wie in der Bewertung."""
        return abstand(self.pos, ziel) * WEGFAKTOR / self.mein_tempo if self.pos is not None else None


def _bereich(b, p, lb, meine_lane: str | None) -> str | None:
    """Aus der Position: Lanes per Projektion (welle._projektion, wie `tiefe`), der Rest aus minimap.ort."""
    g = lb.gesehen(p.ich) if lb is not None else None
    if g is None or b is None or b.pos is None:
        return None
    for schl, (gx, gy) in (("drache", GRUBEN["drache"]), ("baron", GRUBEN["baron"])):
        if abstand(b.pos, einheiten(gx, gy)) <= 1200:
            return f"grube:{schl}"
    ort = minimap.ort(g[1], g[2], p.mein_team)
    if "eurer Basis" in ort:
        return "basis_eigen"
    if "seiner Basis" in ort:
        return "basis_fremd"
    from ..welle import _projektion
    pr = _projektion(g[1], g[2])
    if pr is not None and pr[2] < 0.06:
        return "lane_eigen" if pr[0] == meine_lane else f"lane:{pr[0]}"
    if "oberen Fluss" in ort:
        return "fluss_oben"
    if "unteren Fluss" in ort:
        return "fluss_unten"
    if "Flussmitte" in ort:
        return "fluss_mitte"
    if "Jungle" in ort:
        eigen = "eurem" in ort or ("blauen" in ort) == (p.mein_team == BLAU)
        return f"jungle_{'eigen' if eigen else 'fremd'}_{'oben' if 'oberen' in ort else 'unten'}"
    return {"oben": "lane:Top", "unten": "lane:Bot", "auf der Mid-Lane": "lane:Mid"}.get(ort)


class MerkmalBau:
    """Haelt den Verlauf der letzten 20 s und baut je Takt die Merkmale."""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.verlauf: deque = deque()       # (Zeit, dein Leben, deine Position, {Gegner: sein Balken})

    def neu(self, p, b, lb) -> Merkmale | None:
        c = self.cfg["modus"]
        zeit = p.zeit
        if b is None:
            return Merkmale(zeit, bool(p.ich and p.ich.tot), None, None, None, zeit < c["lane_phase_bis_s"],
                            None, None, False, daten_frisch=False)
        meine_lane = LANE_DER_ROLLE.get(p.ich.rolle)
        leben = b.leben
        nah = {g.champion: g.leben for g in b.gegner
               if g.sichtbar and not g.s.tot and g.abstand is not None and g.abstand <= 1200}
        self.verlauf.append((zeit, leben, b.pos, nah))
        while self.verlauf and self.verlauf[0][0] < zeit - VERLAUF_S:
            self.verlauf.popleft()
        vor3 = next((v for v in self.verlauf if v[0] >= zeit - 3.0), None)
        trend = (leben - vor3[1]) if (leben is not None and vor3 is not None and vor3[1] is not None
                                      and zeit - vor3[0] >= 1.0) else None
        # im Kampf: sichtbarer Gegner in kampf_radius UND (dein Leben faellt ODER sein Balken faellt)
        kampf = False
        naechste = [g for g in b.gegner if g.sichtbar and not g.s.tot and g.abstand is not None
                    and g.abstand <= c["kampf_radius"]]
        if naechste:
            if trend is not None and trend <= c["kampf_leben_trend"]:
                kampf = True
            elif vor3 is not None:
                for g in naechste:
                    alt = vor3[3].get(g.champion)
                    if alt is not None and g.leben is not None and alt - g.leben >= c["kampf_balken_faellt"]:
                        kampf = True
        # Lane-Phase: vor 14:00 und beide Aussentuerme deiner Lane stehen
        lane_phase = zeit < c["lane_phase_bis_s"]
        if lane_phase and meine_lane:
            stehen = bewertung.stehende_tuerme(p)
            lane_phase = all((t, meine_lane, "aussen") in stehen for t in (BLAU, ROT))
        mitspieler = [(s, wo) for s, wo, *_ in b.mitspieler]
        m = Merkmale(zeit, p.ich.tot, b.pos, _bereich(b, p, lb, meine_lane), meine_lane, lane_phase, leben, trend,
                     kampf, gegner_im_radius=bool(naechste), mitspieler=mitspieler, mein_tempo=b.mein_tempo or 340.0)
        # alle Objectives, die leben oder bald spawnen - je mit DEINER Laufzeit (Kapitel 1.3 Punkt 5)
        for schl in ("drache", "baron", "herold", "larven"):
            try:
                t = p.naechster_spawn(schl)
            except Exception:
                t = None
            if t is None or t - zeit > 180:
                continue
            obj = bewertung.einheiten(*GRUBEN[OBJ_GRUBE[schl]])
            weg = m.weg(obj)
            fenster, unbekannt, _ = bewertung.verteidiger_ab(b, obj, weg or 0.0)
            erreicht = sum(1 for _, wo in mitspieler if wo is not None
                           and abstand(wo, obj) * WEGFAKTOR / 380.0 <= c["objective_nah_s"])
            m.objectives.append(ObjectiveLage(schl, t <= zeit, max(0.0, t - zeit), obj, weg,
                                              m.team_nah(obj, c["grube_radius"]), erreicht, fenster, unbekannt))
        m.bedrohung = self._bedrohung(p, b, lb, m)
        frisch_bis = c["minimap_frisch_s"]
        m.daten_frisch = lb is not None and getattr(lb, "letztes_bild", None) is not None \
            and zeit - lb.letztes_bild <= frisch_bis
        return m

    def _bedrohung(self, p, b, lb, m: Merkmale) -> list:
        """Kapitel 5.1 VERTEIDIGEN: >= 2 Gegner sichtbar in 2500 um einen eigenen Turm/Nexus, oder die gegnerische
        Welle steht an eurem Inhibitor-Turm/Nexus einer Lane ohne Inhibitor und kein Mitspieler ist dort."""
        c = self.cfg["modus"]
        mein = p.mein_team
        aus = []
        stehen = bewertung.stehende_tuerme(p)
        strukturen = [(f"deinen {k[1]}-{'Inhibitor-' if k[2] == 'Inhib' else ''}Turm", v)
                      for k, v in stehen.items() if k[0] == mein] + [("euren Nexus", NEXUS[mein])]
        sichtbar = [g for g in b.gegner if g.sichtbar and not g.s.tot and g.pos is not None]
        for name, pos in strukturen:
            if sum(1 for g in sichtbar if abstand(g.pos, pos) <= c["verteidigen_radius"]) >= 2:
                aus.append((name, pos, m.weg(pos)))
        if lb is not None and hasattr(lb, "welle"):
            feind_farbe = "rot" if mein == BLAU else "blau"
            for lane, _ in bewertung.eigene_inhibs_weg(p):
                w = lb.welle(lane, p.zeit)
                if w is None or w.front is None or w.schiebt != feind_farbe:
                    continue
                front = w.front if mein == BLAU else 1 - w.front
                pos = TUERME.get((mein, lane, "Inhib")) or NEXUS[mein]
                if front <= c["verteidigen_welle_front"] and m.team_nah(pos, c["verteidigen_radius"]) == 0:
                    aus.append((f"die {lane}-Lane ohne Inhibitor", pos, m.weg(pos)))
        return aus
