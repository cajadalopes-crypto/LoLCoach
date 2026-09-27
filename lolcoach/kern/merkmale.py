"""Merkmale: was der Kern liest (Buch 0, Kapitel 4). Duenn - rechnet nur, was die Bewertung nicht schon hat.

Schritt 2: Bereich, Lane-Phase, Verlauf (20 s), Leben-Trend, im Kampf, alle Objectives mit eigener Laufzeit und
Mitspielern an der Grube, Fenster der Gegner (bewertung.verteidiger_ab), Bedrohung eigener Strukturen, frische
Daten. Schritt 3: die geglaettete Welle deiner Lane (`WellenStand`, Buch 1 Kapitel 1), die Kanonen-Uhr, die Seite
des gegnerischen Junglers (fuer das Gefahr-Modell, kern/gefahr.py), TP und Kaufplan. Jedes Merkmal darf None sein
(Kapitel 4.3)."""
from __future__ import annotations

import statistics
from collections import deque
from dataclasses import dataclass, field
from functools import lru_cache

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


ZUSTAENDE = ("UNBEKANNT", "LEER", "GECRASHT_BEI_IHM", "GECRASHT_BEI_DIR", "GROSS_ZU_IHM", "GROSS_ZU_DIR",
             "GEHALTEN_BEI_DIR", "ZU_IHM", "ZU_DIR", "MITTE")


@dataclass
class WellenStand:
    """Buch 1, 1.2: die Welle deiner Lane aus deiner Sicht (front 0 = deine Basis, 1 = seine), geglaettet."""
    lane: str
    unsere: int | None        # Median der letzten 6 s (Lesungen mit Front)
    ihre: int | None          # dito; None, wenn ihre Welle im Nebel liegt (front > nebel_ab, du weit weg)
    front: float | None
    trend: float | None       # Steigung der Front in s je 10 s ueber 20 s; > 0 = zu ihm
    zustand: str
    seit: float
    frisch: bool
    turm_dein: float = 0.35   # vorderster stehender Turm deiner Seite auf dieser Lane (s aus deiner Sicht)
    turm_ihr: float = 0.65


@dataclass
class KaufInfo:
    """Was dein Gold jetzt kauft (kaufplan / denker.kauf) - der Kern erfindet keine Items (Buch 3, Kapitel 3)."""
    kaufen: list                # Namen (Data Dragon), hoechstens was das Gold kauft
    kosten: int
    lohnt: bool                 # denker.kauf: fertiges Item oder Bauteile ab KAUF_LOHNT_AB
    kern_fertig: bool           # ein Kern-Item wird fertig (spike_bonus)
    satz: str = ""              # "den Brutalisierer, und wenn du den Trank verkaufst, auch Stiefel"
    verkaufen: str | None = None    # Inventar voll: erst dieses Item verkaufen (kaufplan)


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
    # Schritt 3
    b: object = None             # die Bewertung des Takts (der Kern liest sie, Kapitel 4.1)
    p: object = None             # die Partie
    welle: WellenStand | None = None
    welle_vorher: WellenStand | None = None   # deine Welle, als du die Lane zuletzt verlassen hast (TP, WOHIN)
    kanone_in: float | None = None            # s, bis die naechste Kanone in deiner Lane ist (Wellen-Uhr)
    p_jungler: float | None = None            # gegnerischer Jungler auf deiner Kartenseite (jungle.wahrscheinlich)
    tp_in: float | None = None                # s bis Teleport bereit (0 = bereit), None = keins / unbekannt
    kauf: KaufInfo | None = None
    respawn: float = 0.0
    lane_im_brunnen: bool = False           # dein Lane-Gegner ist gebackt oder nach dem Tod im Brunnen
    fokus: str | None = None                 # Fokus des Tages (profil.fokus) - Kontroll-Auge zuerst

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


def lane_punkt(lane: str, s_blau: float) -> tuple[float, float]:
    """Der Punkt auf der Lane (welle.LANES, Minimap-Anteile) bei s (0 = blaue Basis, 1 = rote)."""
    import math
    from ..welle import LANES
    punkte = LANES[lane]
    laengen = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(punkte, punkte[1:])]
    ziel, bis = max(0.0, min(1.0, s_blau)) * sum(laengen), 0.0
    for (a, b), l in zip(zip(punkte, punkte[1:]), laengen):
        if bis + l >= ziel:
            t = (ziel - bis) / l if l else 0.0
            return a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
        bis += l
    return punkte[-1]


def turm_s(lane: str, team: str, mein: str, stehen: dict, rueckfall: float) -> float:
    """Buch 1, 1.3: der vorderste stehende Turm von `team` auf dieser Lane, als s aus deiner Sicht - faellt der
    aeussere, rueckt der innere nach (102112, 13:15: eine Welle am inneren Turm, s ~ 0,80)."""
    from ..bewertung import BREITE, HOEHE, TIER
    from ..welle import _projektion
    k = next(((team, lane, st) for st in TIER if (team, lane, st) in stehen), None)
    if k is None:
        return rueckfall
    x, y = stehen[k]
    pr = _projektion(x / BREITE, 1.0 - y / HOEHE)
    if pr is None or pr[0] != lane:
        return rueckfall
    return float(pr[1] if mein == BLAU else 1.0 - pr[1])


class WellenPuffer:
    """Buch 1, 1.2/1.4: die Lesungen deiner Lane der letzten 20 s -> geglaettete Welle und ihr Zustand (Hysterese
    3 s, GECRASHT_BEI_IHM sofort - er ist ein Plan-Schritt)."""

    def __init__(self, cfg: dict):
        self.c = cfg["welle"]
        self.lesungen: deque = deque()        # (Spielzeit, unsere, ihre, front aus deiner Sicht)
        self._letzte = None
        self.zustand, self.seit = "UNBEKANNT", 0.0
        self.kandidat, self.kandidat_seit = None, 0.0
        self._leer_seit: float | None = None
        self._halt_seit: float | None = None

    def lesen(self, zeit: float, w, lz: float | None, mein: str) -> None:
        """Eine neue Lesung von welle.py (lz = ihre Zeit; dieselbe zaehlt nur einmal)."""
        if w is None or lz is None or lz == self._letzte:
            return
        self._letzte = lz
        blau = mein == BLAU
        wir, die = (w.blau, w.rot) if blau else (w.rot, w.blau)
        front = None if w.front is None else (w.front if blau else 1.0 - w.front)
        self.lesungen.append((lz, wir, die, front))

    def stand(self, zeit: float, lane: str, mein: str, pos, stehen: dict) -> WellenStand:
        c = self.c
        while self.lesungen and self.lesungen[0][0] < zeit - c["trend_fenster_s"]:
            self.lesungen.popleft()
        jung = [x for x in self.lesungen if x[0] >= zeit - c["median_s"]]
        mit = [x for x in jung if x[3] is not None]
        quelle = mit or jung
        unsere = int(statistics.median(x[1] for x in quelle)) if quelle else None
        ihre = int(statistics.median(x[2] for x in quelle)) if quelle else None
        front = statistics.median(x[3] for x in mit) if mit else None
        if front is not None and front > c["nebel_ab"] and pos is not None:
            punkt = lane_punkt(lane, front if mein == BLAU else 1.0 - front)
            if abstand(pos, bewertung.einheiten(*punkt)) > c["nebel_abstand"]:
                ihre = None           # ihre Welle liegt im Nebel - 0 hiesse nur "nicht gesehen"
        trend = None
        punkte = [(x[0], x[3]) for x in self.lesungen if x[3] is not None]
        # nur ueber den letzten zusammenhaengenden Abschnitt: stirbt eine Welle, springt die Front zur naechsten
        # (Buch 1, 1.1) - eine Regression ueber den Sprung ergab +-0,2..0,4 und damit fast immer ZU_IHM/ZU_DIR
        # (Eichung an der echten Partie 140253, messungen.md Schritt 3)
        for i in range(len(punkte) - 1, 0, -1):
            if abs(punkte[i][1] - punkte[i - 1][1]) > self.c["front_sprung"]:
                punkte = punkte[i:]
                break
        if len(punkte) >= 3 and punkte[-1][0] - punkte[0][0] >= 5.0:
            mt = sum(t for t, _ in punkte) / len(punkte)
            mf = sum(f for _, f in punkte) / len(punkte)
            nenner = sum((t - mt) ** 2 for t, _ in punkte)
            if nenner > 0:
                trend = 10.0 * sum((t - mt) * (f - mf) for t, f in punkte) / nenner
        dein = turm_s(lane, mein, mein, stehen, c["turm_dein"])
        ihr = turm_s(lane, gegenteam(mein), mein, stehen, c["turm_ihr"])
        frisch = len(jung) >= 3
        roh = self._roh(zeit, frisch, unsere, ihre, front, trend, dein, ihr)
        if roh == self.zustand:
            self.kandidat = None
        elif roh == "GECRASHT_BEI_IHM":
            self.zustand, self.seit, self.kandidat = roh, zeit, None
        else:
            if self.kandidat != roh:
                self.kandidat, self.kandidat_seit = roh, zeit
            if zeit - self.kandidat_seit >= c["zustand_hysterese_s"]:
                self.zustand, self.seit, self.kandidat = roh, zeit, None
        return WellenStand(lane, unsere, ihre, front, trend, self.zustand, self.seit, frisch, dein, ihr)

    def _roh(self, zeit, frisch, unsere, ihre, front, trend, dein, ihr) -> str:
        """Buch 1, 1.4 - von oben nach unten, die erste passende Zeile."""
        c = self.c
        r = c["turm_reichweite_s"]
        if not frisch or unsere is None:
            self._leer_seit = self._halt_seit = None
            return "UNBEKANNT"
        if unsere == 0 and ihre in (0, None):
            self._leer_seit = zeit if self._leer_seit is None else self._leer_seit
            if zeit - self._leer_seit >= c["leer_ab_s"]:
                return "LEER"
        else:
            self._leer_seit = None
        tr = trend if trend is not None else 0.0
        band = front is not None and dein + 0.03 <= front <= dein + 0.12
        if band and trend is not None and abs(trend) <= 0.01 and ihre is not None and ihre >= unsere + 2:
            self._halt_seit = zeit if self._halt_seit is None else self._halt_seit
        else:
            self._halt_seit = None
        if front is not None and front >= ihr - r and unsere >= 1 and (ihre is None or ihre <= 1):
            return "GECRASHT_BEI_IHM"
        if front is not None and front <= dein + r and ihre is not None and ihre >= 1 and unsere <= 1:
            return "GECRASHT_BEI_DIR"
        if unsere >= c["gross_ab"] and tr >= 0:
            return "GROSS_ZU_IHM"
        if ihre is not None and ihre >= c["gross_ab"] and tr <= 0:
            return "GROSS_ZU_DIR"
        if self._halt_seit is not None and zeit - self._halt_seit >= c["freeze_stabil_s"]:
            return "GEHALTEN_BEI_DIR"
        if tr >= c["trend_schwelle"] or (ihre is not None and unsere - ihre >= 2):
            return "ZU_IHM"
        if tr <= -c["trend_schwelle"] or (ihre is not None and ihre - unsere >= 2):
            return "ZU_DIR"
        return "MITTE"


def recall_schwellen(champion_id: str) -> tuple[int | None, int | None, float | None]:
    """Buch 3, 1: aus dem Lexikon (Zeile "Recall-Schwellen"): (back_schwelle, back_nie_unter, ausser Leben unter).
    Riven: "1337 g (Der Brutalisierer) ... Nicht mit <800 g zurueck, ausser Leben <30 %." -> (1337, 800, 0.30)."""
    return _recall_schwellen(champion_id)


@lru_cache(maxsize=64)
def _recall_schwellen(champion_id: str):
    import re
    from pathlib import Path
    datei = Path(__file__).resolve().parent.parent.parent / "wissen" / "lexikon" / "champions" / f"{champion_id}.md"
    try:
        zeile = next((z for z in datei.read_text(encoding="utf-8").splitlines() if "Recall-Schwellen" in z), "")
    except OSError:
        zeile = ""
    zahlen = [int(x) for x in re.findall(r"(\d{3,4})\s*g\b", zeile)]
    nie = re.search(r"[Nn]icht mit\s*<\s*(\d{3,4})\s*g", zeile)
    leben = re.search(r"Leben\s*<\s*(\d{1,2})\s*%", zeile)
    schwelle = zahlen[0] if zahlen else None
    return (schwelle, int(nie.group(1)) if nie else None, int(leben.group(1)) / 100 if leben else None)


class MerkmalBau:
    """Haelt den Verlauf der letzten 20 s und baut je Takt die Merkmale."""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.verlauf: deque = deque()       # (Zeit, dein Leben, deine Position, {Gegner: sein Balken})
        self.wellen = WellenPuffer(cfg)
        self.welle_vorher: WellenStand | None = None
        self._auf_lane: WellenStand | None = None

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
            if t is None or t - zeit > 300:
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
        self._schritt3(m, p, b, lb)
        return m

    def _schritt3(self, m: Merkmale, p, b, lb) -> None:
        """Welle (Buch 1), Kanonen-Uhr, Jungler-Seite, TP, Kauf (Buch 3)."""
        m.b, m.p = b, p
        m.respawn = float(p.ich.respawn or 0.0) if p.ich.tot else 0.0
        mein = p.mein_team
        if m.meine_lane and lb is not None and hasattr(lb, "welle"):
            self.wellen.lesen(m.zeit, lb.welle(m.meine_lane, m.zeit), getattr(lb, "wellen_zeit", None), mein)
            m.welle = self.wellen.stand(m.zeit, m.meine_lane, mein, b.pos, bewertung.stehende_tuerme(p))
        # deine Welle beim Verlassen der Lane: fuer WOHIN und TP aus der Basis (Buch 3, 4.1)
        if m.bereich == "lane_eigen" and m.welle is not None and m.welle.zustand != "UNBEKANNT":
            self._auf_lane = m.welle
        elif m.bereich != "lane_eigen" and self._auf_lane is not None:
            self.welle_vorher, self._auf_lane = self._auf_lane, None
        m.welle_vorher = self.welle_vorher
        try:
            from ..entscheider import naechste_kanone
            k = naechste_kanone(m.zeit, p.ich.rolle)
            m.kanone_in = None if k is None else max(0.0, k - m.zeit)
        except Exception:
            m.kanone_in = None
        jungle = getattr(lb, "jungle", None) if lb is not None else None
        if jungle is not None:
            w = jungle.wahrscheinlich(m.zeit)
            seite = meine_seite(m)
            m.p_jungler = max(w.values()) if seite is None else w.get(seite, 0.5)
        if b.zweiter and b.zweiter[0] == "SummonerTeleport":
            m.tp_in = b.zweiter[1]
        m.kauf = kauf_info(b)
        g = b.lane
        m.lane_im_brunnen = bool(g is not None and not g.s.tot and not g.sichtbar and lb is not None
                                 and hasattr(lb, "brunnen_seit") and lb.brunnen_seit(g.s, m.zeit))

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


def meine_seite(m: Merkmale) -> str | None:
    """Deine Kartenseite fuer p_seite (7.5): 'oben'/'unten'; auf Mid, in der Flussmitte oder der Basis None
    (dann gilt das Maximum beider Seiten)."""
    if m.bereich in (None, "basis_eigen", "basis_fremd", "fluss_mitte", "lane:Mid") or (
            m.bereich == "lane_eigen" and m.meine_lane == "Mid"):
        return None
    if m.bereich == "lane_eigen":
        return {"Top": "oben", "Bot": "unten"}.get(m.meine_lane)
    if m.pos is None:
        return None
    from ..bewertung import BREITE, HOEHE
    from ..jungle import seite
    x, y = m.pos[0] / BREITE, 1.0 - m.pos[1] / HOEHE
    if abs(x + y - 1.0) < 0.08:
        return None
    return seite(x, y)


def kauf_info(b) -> KaufInfo | None:
    """kaufplan (b.kauf) + denker.kauf: was du kaufst und ob sich ein Recall dafuer lohnt."""
    k = getattr(b, "kauf", None)
    if k is None:
        return None
    try:
        from .. import denker
        satz, lohnt = denker.kauf(b, b.gold)
    except Exception:
        satz, lohnt = "", False
    return KaufInfo(list(k.kaufen), int(k.kosten), bool(lohnt), k.item in k.kaufen, satz,
                    getattr(k, "verkaufen", None))
