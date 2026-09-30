"""Challenger-Gehirn, Stufe 1 (Auftrag 030): alle gueltigen Partien -> Entscheidungsmomente Lage -> Aktion -> Folge.

    python werkzeuge/challenger/phase1.py           baut alle fehlenden Partien (fortsetzbar, neue Downloads inklusive)
    python werkzeuge/challenger/phase1.py --neu     baut alles neu
    python werkzeuge/challenger/phase1.py --merkmale    schreibt nur buecher/challenger/merkmale.md

Ablage daten/challenger/phase1/:
    teil_NNN.npz    je Teil ~150 Partien, unkomprimiert (np.load in Sekunden):
                    X (n, len(MERKMALE)) float32  - Lage, nur Wissbares
                    meta (n, len(META)) int32     - Partie, Spieler, Rolle, Liga, Zeit, Anlass, Aufteilung, Sieg
                    aktion (n, len(AKTION)) int16 - Aktion der naechsten 60 s + die drei danach + Ziel/TP/Flags
                    folge (n, len(FOLGE)) float32 - 30/60/120 s danach
                    obj (m, len(OBJ)) int32       - jedes Monster: Zeit, Art, Team, Zustand (frei/bestritten/umkaempft)
    partien.json    Partie-Nummer -> Match-ID
Laden: `lade()` unten.

Bauweise: je Partie ein Sekundenraster (Positionen zwischen den Minuten linear [G], Stufen aus Ereignissen [B]), dann
werden alle Momente einer Partie auf einmal aus dem Raster gelesen. KEIN MAPHACK: Gegnerpositionen aus den Minuten
werden fuer die Lage nur an EINER Stelle gelesen - fuer den Lane-Gegner, und nur wenn er <= 1200 neben dem Spieler
steht ("nahe sichtbar"). Alles andere ueber Gegner kommt aus dem Scoreboard (Level, Items, CS, tot) und aus allen
angesagten Ereignissen ("zuletzt gesehen"). Beweis: test_kein_maphack.py.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

import ableitungen as abl
import grundlage as g

ZIEL = g.ABLAGE / "phase1"
AUFTEILUNG = g.BUCH / "aufteilung.json"        # einmal festgelegt, nie mehr aendern (committet)
TEIL_GROESSE = 150
NAHE_SICHTBAR = 1200.0
MERGE = 5                                       # Zeitpunkte eines Spielers, die so eng liegen, werden einer

ROLLEN = list(g.ROLLEN)
LIGEN = ["Challenger", "Grandmaster", "Master", "unter Master"]
ANLAESSE = ["Minute", "Kill", "eigener Tod", "Respawn", "Back", "Gebaeude", "Monster", "Monster-Spawn"]
AUFTEILUNGEN = ["Training", "Pruefung Spieler", "Pruefung Zeit", "Pruefung beides"]
AKTIONEN = ["Tot", "Back", "Objective", "TP", "Rotation", "Split", "Gruppe", "Jungle", "Lane", "Warten", "Unterwegs"]
MONSTER = ["–", "Drache", "Baron", "Herold", "Larven", "Elder"]
ZUSTAENDE = ["frei", "bestritten", "umkaempft"]
BEREICHE = ["basis_blau", "basis_rot", "top", "mid", "bot", "fluss_oben", "fluss_unten", "jungle_blau_oben",
            "jungle_blau_unten", "jungle_rot_oben", "jungle_rot_unten"]
ZONEN = ["basis", "oben", "mid", "unten"]
LANE_DER_ROLLE = {"TOP": 2, "MIDDLE": 3, "BOTTOM": 4, "UTILITY": 4, "JUNGLE": -1}

# Objective-Timer: wissen/objektive.toml (Patch 26.x); an den Daten geprueft: fruehester Kill Drache 5:19,
# Larven 8:04 (letzter 14:51), Herold 15:11 (letzter 19:55), Baron 20:16.
DRACHE_ERST, DRACHE_RESPAWN, ELDER_RESPAWN = 300, 300, 360
LARVEN_VON, LARVEN_BIS = 480, 885
HEROLD_VON, HEROLD_BIS = 900, 1185
BARON_ERST, BARON_RESPAWN, BARON_BUFF, ELDER_BUFF = 1200, 360, 180, 150
INHIB_RESPAWN = 300

# ---------------------------------------------------------------- Verzeichnisse (Name, Bedeutung, Quelle, Marke)

META = [
    ("partie", "Nummer der Partie (partien.json)", "Datei", "B"),
    ("pid", "participantId 1-10", "Match", "B"),
    ("team", "0 = Blau, 1 = Rot", "Match", "B"),
    ("rolle", "0 Top, 1 Jungle, 2 Mid, 3 ADC, 4 Support", "teamPosition", "B"),
    ("liga", "0 Challenger, 1 GM, 2 Master, 3 unter Master (Ligalisten 30.09.)", "league-v4", "B"),
    ("zeit", "Spielsekunde des Moments", "Raster", "B"),
    ("anlass", "0 Minute, 1 Kill, 2 eigener Tod, 3 Respawn, 4 Back, 5 Gebaeude, 6 Monster, 7 Monster-Spawn", "Ereignisse", "B"),
    ("aufteilung", "0 Training, 1 Pruefung Spieler, 2 Pruefung Zeit, 3 beides", "aufteilung.json", "B"),
    ("sieg", "1 = sein Team gewinnt", "Match", "B"),
    ("dauer", "Partiedauer in s", "Match", "B"),
]

MERKMALE: list[tuple[str, str, str, str]] = [
    ("minute", "Spielzeit in Minuten", "Uhr", "B"),
    # Selbst
    ("x", "eigene Position x", "Minute, dazwischen linear", "G"),
    ("y", "eigene Position y", "Minute, dazwischen linear", "G"),
    ("bereich", "Kartenbereich (0-10, s. BEREICHE)", "aus x, y", "G"),
    ("zone", "0 Basis, 1 oben, 2 mid, 3 unten", "aus x, y", "G"),
    ("in_eigener_lane", "steht in der Lane seiner Rolle", "aus x, y", "G"),
    ("abst_brunnen", "Abstand zum eigenen Brunnen", "aus x, y", "G"),
    ("abst_eigener_turm", "Abstand zum naechsten stehenden eigenen Turm", "x, y + Gebaeude-Ereignisse", "G"),
    ("abst_gegner_turm", "Abstand zum naechsten stehenden gegnerischen Turm", "x, y + Gebaeude-Ereignisse", "G"),
    ("abst_drache", "Abstand zur Drachengrube", "aus x, y", "G"),
    ("abst_baron", "Abstand zur Baron-/Herold-/Larvengrube", "aus x, y", "G"),
    ("tot", "gerade tot", "Kills + Todeszeit-Formel", "B"),
    ("respawn_rest", "Sekunden bis zur Wiederbelebung (0 = lebt)", "Formel, an den Minuten (Leben 0/>0) gekappt", "G"),
    ("level", "eigenes Level", "LEVEL_UP", "B"),
    ("cs", "eigene CS (Vasallen + Monster)", "Minute, dazwischen linear", "G"),
    ("gold_tasche", "Gold in der Tasche", "Minute + verdientes Gold - Kaeufe", "G"),
    ("itemwert", "Wert der Items (Scoreboard)", "Kaeufe/Verkaeufe/Verbrauch + Preise Data Dragon", "B"),
    ("leben_anteil", "Leben / max. Leben", "letzte volle Minute", "G"),
    ("hat_tp", "Teleport als Beschwoererzauber", "Match", "B"),
    ("seit_back", "Sekunden seit dem letzten Ladenbesuch (Back oder Tod)", "Kaeufe", "B"),
    # Team
    ("mit_lebend", "lebende Mitspieler (ohne dich)", "Kills + Formel", "B"),
    ("mit_nah", "lebende Mitspieler <= 2500 bei dir", "Minimap", "G"),
    ("mit_abstand", "mittlerer Abstand der lebenden Mitspieler", "Minimap", "G"),
    *[(f"mit{i}_{k}", f"Mitspieler {i} (nach Rolle, ohne dich): {k} (NaN = tot)", "Minimap", "G")
      for i in range(1, 5) for k in ("x", "y")],
    # Scoreboard und angesagte Ereignisse
    *[(f"{k}_{s}", f"{b} ({'dein Team' if s == 'wir' else 'Gegner'})", q, m)
      for k, b, q, m in (("kills", "Kills", "Ereignis", "B"), ("tuerme", "zerstoerte Tuerme", "Ereignis", "B"),
                         ("inhibs_offen", "gerade offene gegnerische Inhibitoren", "Ereignis + 5 min", "B"),
                         ("platten", "Platten", "Ereignis", "B"), ("drachen", "Drachen (ohne Elder)", "Ereignis", "B"),
                         ("seele", "Drachenseele (4 Drachen)", "Ereignis", "B"), ("larven", "Larven", "Ereignis", "B"),
                         ("herold", "Herolde", "Ereignis", "B"), ("baron", "Barone", "Ereignis", "B"),
                         ("elder", "Elder", "Ereignis", "B"),
                         ("baron_buff", "Rest-Sekunden Baron-Buff", "Ereignis + 180 s", "G"),
                         ("elder_buff", "Rest-Sekunden Elder-Buff", "Ereignis + 150 s", "G"),
                         ("itemwert_team", "Item-Wert des Teams", "Scoreboard", "B"),
                         ("level_team", "Level-Summe des Teams", "Scoreboard", "B"),
                         ("cs_team", "CS-Summe des Teams", "Scoreboard (Minute, linear)", "G"),
                         ("tote", "gerade tote Spieler", "Scoreboard", "B"))
      for s in ("wir", "gegner")],
    # Unterschiede
    ("diff_itemwert_team", "Item-Wert wir - Gegner", "Scoreboard", "B"),
    ("diff_level_team", "Level-Summe wir - Gegner", "Scoreboard", "B"),
    ("diff_itemwert_lane", "dein Item-Wert - Lane-Gegner", "Scoreboard", "B"),
    ("diff_level_lane", "dein Level - Lane-Gegner", "Scoreboard", "B"),
    ("diff_cs_lane", "deine CS - Lane-Gegner", "Scoreboard (Minute, linear)", "G"),
    # Lane-Gegner nahe sichtbar (Entscheidung 1)
    ("lg_nahe_sichtbar", "Lane-Gegner lebt und steht <= 1200 neben dir (\"nahe sichtbar\")", "Minute, linear", "G"),
    ("lg_x", "Lane-Gegner x, nur wenn nahe sichtbar, sonst NaN", "Minute, linear", "G"),
    ("lg_y", "Lane-Gegner y, nur wenn nahe sichtbar, sonst NaN", "Minute, linear", "G"),
    # Gegner (nach Rolle): tot + Restzeit, zuletzt gesehen
    *[(f"geg{i}_{k}", f"Gegner {g.ROLLE_DE[r]}: {b}", q, m)
      for i, r in enumerate(g.ROLLEN)
      for k, b, q, m in (("tot", "tot", "Scoreboard", "B"), ("respawn", "Rest-Sekunden tot", "Formel", "G"),
                         ("gesehen_x", "zuletzt gesehen x (NaN = nie)", "angesagtes Ereignis mit Ort", "B"),
                         ("gesehen_y", "zuletzt gesehen y", "angesagtes Ereignis mit Ort", "B"),
                         ("gesehen_alter", "Sekunden seit zuletzt gesehen (NaN = nie)", "angesagtes Ereignis", "B"))],
    # Objective-Timer
    *[(f"{o}_{k}", f"{b}: {'steht jetzt' if k == 'da' else 'Sekunden bis zum Spawn (-1 = kommt nicht mehr)'}",
       "Timer (wissen/objektive.toml) + Kills", "G")
      for o, b in (("drache", "Drache/Elder"), ("larven", "Larven"), ("herold", "Herold"), ("baron", "Baron"))
      for k in ("da", "bis")],
    ("drache_ist_elder", "als Naechstes kommt der Elder", "Drachen-Kills", "B"),
]
NAMEN = [m[0] for m in MERKMALE]
SP = {n: i for i, n in enumerate(NAMEN)}
MI = {n[0]: i for i, n in enumerate(META)}

AKTION = [
    ("a0", "Aktion der naechsten 60 s (Code aus AKTIONEN, Vorrang in dieser Reihenfolge)", "Regeln Phase 0", "G"),
    ("a1", "Aktion 60-120 s", "Regeln Phase 0", "G"),
    ("a2", "Aktion 120-180 s", "Regeln Phase 0", "G"),
    ("a3", "Aktion 180-240 s", "Regeln Phase 0", "G"),
    ("flags", "Bit je Aktion, die in den naechsten 60 s zutrifft (mehrere moeglich)", "Regeln Phase 0", "G"),
    ("ziel", "bei Objective: 1 Drache, 2 Baron, 3 Herold, 4 Larven, 5 Elder; bei Rotation: Zielzone 1-3", "Regeln", "G"),
    ("ziel_zustand", "bei Objective-Kill: 0 frei, 1 bestritten, 2 umkaempft; -1 = Spawn/kein Kill", "Entscheidung 3", "G"),
    ("tp", "1 = TP sicher erkannt, -1 = TP unbekannt (hat TP), 0 = hat kein TP", "Positionssprung, Phase 0", "G"),
]
AI = {n[0]: i for i, n in enumerate(AKTION)}

FOLGE = []
for _dt in (30, 60, 120):
    FOLGE += [(f"gold_{_dt}", f"eigenes verdientes Gold in {_dt} s", "Minute, linear", "G"),
              (f"xp_{_dt}", f"eigene XP in {_dt} s", "Minute, linear", "G"),
              (f"teamgold_{_dt}", f"Aenderung Team-Gold-Abstand in {_dt} s", "Minute, linear", "G"),
              (f"tod_{_dt}", f"du stirbst in {_dt} s", "Kill", "B"),
              (f"kills_wir_{_dt}", f"Kills deines Teams in {_dt} s", "Kill", "B"),
              (f"kills_gegner_{_dt}", f"Kills des Gegners in {_dt} s", "Kill", "B"),
              (f"platten_wir_{_dt}", f"Platten deines Teams in {_dt} s", "Ereignis", "B"),
              (f"platten_gegner_{_dt}", f"Platten des Gegners in {_dt} s", "Ereignis", "B"),
              (f"gebaeude_wir_{_dt}", f"Tuerme/Inhibitoren deines Teams in {_dt} s", "Ereignis", "B"),
              (f"gebaeude_gegner_{_dt}", f"Tuerme/Inhibitoren des Gegners in {_dt} s", "Ereignis", "B"),
              (f"obj_wir_{_dt}", f"Monster deines Teams in {_dt} s (Larve einzeln)", "Ereignis", "B"),
              (f"obj_gegner_{_dt}", f"Monster des Gegners in {_dt} s", "Ereignis", "B")]
FI = {n[0]: i for i, n in enumerate(FOLGE)}
OBJ = [("partie", "Nummer", "", "B"), ("zeit", "Sekunde des Kills", "", "B"), ("art", "1-5 wie ziel", "", "B"),
       ("team", "0 Blau, 1 Rot, -1 neutral", "", "B"), ("zustand", "0 frei, 1 bestritten, 2 umkaempft", "Entscheidung 3", "G"),
       ("kills", "Kills +-30 s, <= 3000", "", "B"), ("gegner_nah", "Gegner des Nehmers <= 3000 (Position interpoliert)", "", "G")]


# ---------------------------------------------------------------- Aufteilung (fest)

def aufteilung() -> dict:
    """Einmal festgelegt: Salz fuer den Spieler-Hash und Stichtag. Existiert die Datei, wird NIE neu gerechnet."""
    if AUFTEILUNG.exists():
        return json.loads(AUFTEILUNG.read_text(encoding="utf-8"))
    starts = sorted(g.lade(m)["start"] for m in json.loads((g.ABLAGE / "gueltig.json").read_text(encoding="utf-8")))
    stichtag = starts[int(len(starts) * 0.8)]
    d = {"salz": "challenger-030", "pruefspieler": "sha1(salz + puuid) % 5 == 0 (20 %)",
         "stichtag_ms": stichtag, "stichtag": time.strftime("%d.%m.%Y %H:%M", time.localtime(stichtag / 1000)),
         "festgelegt": "30.09.2026, Auftrag 030 - nie mehr aendern; spaetere Partien liegen hinter dem Stichtag und sind Pruefung Zeit"}
    AUFTEILUNG.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d


def pruefspieler(puuid: str, salz: str) -> bool:
    return int(hashlib.sha1((salz + puuid).encode()).hexdigest(), 16) % 5 == 0


# ---------------------------------------------------------------- Karte (numpy)

def bereich_np(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    out = np.full(x.shape, -1, np.int16)
    frei = np.ones(x.shape, bool)

    def setze(maske, code):
        nonlocal frei
        m = maske & frei
        out[m] = code
        frei &= ~m
    setze(np.hypot(x - g.BRUNNEN[g.BLAU][0], y - g.BRUNNEN[g.BLAU][1]) < 4200, 0)
    setze(np.hypot(x - g.BRUNNEN[g.ROT][0], y - g.BRUNNEN[g.ROT][1]) < 4200, 1)
    setze((x < 2300) | (y > 12500), 2)
    setze((y < 2300) | (x > 12500), 4)
    setze(np.abs(x - y) < 1500, 3)
    s = x + y
    fluss = np.abs(s - 14800) < 1700
    setze(fluss & (y > x), 5)
    setze(fluss, 6)
    blau = s < 14800
    setze(blau & (y > x), 7)
    setze(blau, 8)
    setze(y > x, 9)
    setze(np.ones(x.shape, bool), 10)
    out[np.isnan(x)] = -1
    return out


ZONE_VON_BEREICH = np.array([0, 0, 1, 2, 3, 1, 3, 1, 3, 1, 3], np.int16)


def zone_np(ber):
    ber = np.asarray(ber)
    z = ZONE_VON_BEREICH[np.clip(ber, 0, 10)]
    return np.where(ber < 0, -1, z)


# ---------------------------------------------------------------- Raster je Partie

_PREISE = None


def preise() -> dict:
    global _PREISE
    if _PREISE is None:
        d = sorted((g.WURZEL / "daten" / "ddragon").glob("*/item.json"))
        data = json.loads(d[-1].read_text(encoding="utf-8"))["data"] if d else {}
        _PREISE = {int(k): v.get("gold", {}).get("total", 0) for k, v in data.items()}
    return _PREISE


def _stufe(zeiten, werte, S, start=0.0):
    """Stufenfunktion auf dem Sekundenraster: Wert gilt ab ceil(t). Bei gleicher Zeit gilt der LETZTE Wert in
    Ereignis-Reihenfolge (Kauf und Verbrauch der Bauteile haben denselben Zeitstempel) - nur nach t sortieren, stabil."""
    arr = np.full(S, start, np.float64)
    for t, w in sorted(zip(zeiten, werte), key=lambda tw: tw[0]):
        arr[min(S - 1, int(math.ceil(t))):] = w
    return arr


def _zaehler(zeiten, S):
    """Anzahl Ereignisse mit t <= s je Sekunde s."""
    z = np.sort(np.ceil(np.asarray(zeiten, float))) if len(zeiten) else np.zeros(0)
    return np.searchsorted(z, np.arange(S), side="right").astype(np.float64)


class Raster:
    def __init__(self, p: g.Partie, spiegel_gegner: np.ndarray | None = None):
        """`spiegel_gegner`: nur fuer den Maphack-Test - ersetzt die Minutenpositionen der Gegner."""
        self.p = p
        self.S = S = int(p.dauer) + 250
        self.sek = np.arange(S, dtype=np.float64)
        ft = np.array([f[0] / 1000.0 for f in p.frames])
        # Riot-Minuten liegen 0-0,4 s nach der vollen Minute: auf die Minute legen, damit ein Minuten-Moment genau die
        # Minutenwerte hat [B]; der letzte Frame (Spielende) bleibt, wo er ist
        voll = 60 * np.round(ft / 60)
        ft = np.where(np.abs(ft - voll) < 2, voll, ft)
        self.ft = ft
        pids = list(range(1, 11))
        self.team = np.array([0] + [0 if p.team(i) == g.BLAU else 1 for i in pids])
        F = np.full((11, len(ft), 11), np.nan)
        for j, (_, pf) in enumerate(p.frames):
            for pid, v in pf.items():
                F[pid, j] = [np.nan if a is None else a for a in v]
        if spiegel_gegner is not None:
            F[:, :, 0:2] = np.where(np.isnan(spiegel_gegner), F[:, :, 0:2], spiegel_gegner)
        self.F = F

        def interp(pid, k):
            return np.interp(self.sek, ft, F[pid, :, k])
        self.x = np.full((11, S), np.nan)
        self.y = np.full((11, S), np.nan)
        self.tg = np.zeros((11, S))
        self.xp = np.zeros((11, S))
        self.cs = np.zeros((11, S))
        self.jcs = np.zeros((11, S))
        self.hp = np.zeros((11, S))
        self.lebt = np.ones((11, S), bool)
        self.resp = np.zeros((11, S))
        self.level = np.ones((11, S))
        self.item = np.zeros((11, S))
        self.kauf_kosten = np.zeros((11, S))
        self.cg = np.zeros((11, S))
        self.seit_laden = np.full((11, S), np.nan)
        self.back_start: dict[int, list[int]] = {}
        fidx = np.clip(np.searchsorted(ft, self.sek, side="right") - 1, 0, len(ft) - 1)
        pr = preise()
        # Tode: Formel (mechanik.toml), an den Minuten gekappt - Leben 0 = noch tot, Leben > 0 = schon zurueck
        # (die Restzeit steht im Spiel auf dem Scoreboard; die Formel allein stimmt in 89 %, Phase 0)
        self.tode: dict[int, list[tuple[float, float]]] = {}
        for pid in pids:
            liste = []
            for td, tr in p.tode(pid):
                nach = [j for j in range(len(ft)) if ft[j] > td]
                lo = max([ft[j] for j in nach if F[pid, j, 9] == 0 and all(F[pid, k, 9] == 0 for k in nach if k <= j)],
                         default=td)
                hi = next((ft[j] for j in nach if F[pid, j, 9] > 0), None)
                tr = max(tr, lo + 1.0)
                if hi is not None:
                    tr = min(tr, hi)
                liste.append((td, tr))
            self.tode[pid] = liste
        for pid in pids:
            self.x[pid], self.y[pid] = interp(pid, 0), interp(pid, 1)
            self.tg[pid], self.xp[pid] = interp(pid, 2), interp(pid, 4)
            self.cs[pid] = interp(pid, 6) + interp(pid, 7)
            self.jcs[pid] = interp(pid, 7)
            hpq = F[pid, :, 9] / np.maximum(F[pid, :, 10], 1)
            self.hp[pid] = hpq[fidx]
            for td, tr in self.tode[pid]:
                a, b = int(math.ceil(td)), min(S, int(math.ceil(tr)))
                self.lebt[pid, a:b] = False
                self.resp[pid, a:b] = tr - self.sek[a:b]
            lv = [(e["t"], e["level"]) for e in p.events if e["typ"] == "LEVEL_UP" and e.get("participantId") == pid]
            self.level[pid] = _stufe([a for a, _ in lv], [b for _, b in lv], S, 1.0)
            # Inventar und Kaufkosten
            inv: list[int] = []
            wz, ww, kz, kw = [], [], [], []
            kosten = 0.0
            for e in p.events:
                if e.get("participantId") != pid or e["typ"] not in ("ITEM_PURCHASED", "ITEM_SOLD", "ITEM_DESTROYED",
                                                                     "ITEM_UNDO"):
                    continue
                if e["typ"] == "ITEM_PURCHASED":
                    inv.append(e["itemId"])
                    kosten += pr.get(e["itemId"], 0)
                elif e["typ"] in ("ITEM_SOLD", "ITEM_DESTROYED"):
                    if e.get("itemId") in inv:
                        inv.remove(e["itemId"])
                else:
                    if e.get("beforeId") in inv:
                        inv.remove(e["beforeId"])
                        kosten -= pr.get(e["beforeId"], 0)
                    if e.get("afterId"):
                        inv.append(e["afterId"])
                wz.append(e["t"])
                ww.append(sum(pr.get(i, 0) for i in inv))
                kz.append(e["t"])
                kw.append(kosten)
            self.item[pid] = _stufe(wz, ww, S)
            self.kauf_kosten[pid] = _stufe(kz, kw, S)
            # Gold in der Tasche: Minute + seither verdient - seither gekauft
            ft_s = np.minimum(np.ceil(ft[fidx]).astype(int), S - 1)
            cg_f = F[pid, fidx, 3]
            tg_f = F[pid, fidx, 2]
            self.cg[pid] = np.maximum(0, cg_f + (self.tg[pid] - tg_f) - (self.kauf_kosten[pid] - self.kauf_kosten[pid][ft_s]))
            # Ladenbesuche
            tode = self.tode[pid]
            besuche = abl.ladenbesuche(p, pid)
            starts = [int(math.ceil(b[0])) for b in besuche]
            letzte = np.full(S, np.nan)
            for s0 in starts:
                letzte[min(s0, S - 1):] = s0
            self.seit_laden[pid] = self.sek - letzte
            self.back_start[pid] = [int(math.ceil(b[0])) for b in besuche
                                    if not any(td <= b[0] <= tr + 45 for td, tr in tode)]
        # Zuletzt gesehen: angesagte Ereignisse mit Ort
        self.gesehen = {}
        for pid in pids:
            zs, xs, ys = [], [], []
            for e in p.events:
                pos = e.get("position")
                if not pos or e["typ"] not in ("CHAMPION_KILL", "BUILDING_KILL", "ELITE_MONSTER_KILL",
                                                "TURRET_PLATE_DESTROYED"):
                    continue
                if pid in {e.get("killerId"), e.get("victimId"), *(e.get("assistingParticipantIds") or [])}:
                    zs.append(e["t"])
                    xs.append(pos[0])
                    ys.append(pos[1])
            idx = np.searchsorted(np.ceil(np.array(zs)), self.sek, side="right") - 1 if zs else np.full(S, -1)
            gx = np.where(idx >= 0, np.array(xs + [np.nan])[idx], np.nan)
            gy = np.where(idx >= 0, np.array(ys + [np.nan])[idx], np.nan)
            ga = np.where(idx >= 0, self.sek - np.array(zs + [np.nan])[idx], np.nan)
            self.gesehen[pid] = (gx, gy, ga)
        self._team_zaehler()
        self._objectives()
        self.tp_sicher: dict[int, list[int]] = {}
        # an welchen Ereignissen mit Ort war der Spieler beteiligt (Sekunden) - fuer "Warten"
        self.beteiligt: dict[int, list[int]] = {}
        for e in p.events:
            if e["typ"] in ("CHAMPION_KILL", "BUILDING_KILL", "ELITE_MONSTER_KILL", "TURRET_PLATE_DESTROYED"):
                for q in {e.get("killerId"), e.get("victimId"), *(e.get("assistingParticipantIds") or [])}:
                    if q:
                        self.beteiligt.setdefault(q, []).append(int(math.ceil(e["t"])))

    # ---- Scoreboard je Team (Index 0 = Blau, 1 = Rot)
    def _team_zaehler(self):
        p, S = self.p, self.S
        T = {}
        ev = p.events
        tid = lambda team: 0 if team == g.BLAU else 1
        kills = [[], []]
        for e in ev:
            if e["typ"] == "CHAMPION_KILL":
                kills[1 - self.team[e["victimId"]]].append(e["t"])
        T["kills"] = [_zaehler(k, S) for k in kills]
        tuerme, geb, platten = [[], []], [[], []], [[], []]
        inhib_down = [np.zeros(S), np.zeros(S)]
        self.turm_steht = {k: np.ones(S, bool) for k in g.TUERME}
        for e in ev:
            if e["typ"] == "BUILDING_KILL" and e.get("teamId") in (g.BLAU, g.ROT):
                wer = 1 - tid(e["teamId"])          # der Zerstoerer
                geb[wer].append(e["t"])
                if e.get("buildingType") == "TOWER_BUILDING":
                    tuerme[wer].append(e["t"])
                    k = min(g.TUERME, key=lambda k: g.abstand(g.TUERME[k], e["position"]))
                    if g.abstand(g.TUERME[k], e["position"]) < 800:
                        self.turm_steht[k][int(math.ceil(e["t"])):] = False
                else:
                    a = int(math.ceil(e["t"]))
                    inhib_down[wer][a:a + INHIB_RESPAWN] += 1
            elif e["typ"] == "TURRET_PLATE_DESTROYED" and e.get("teamId") in (g.BLAU, g.ROT):
                platten[1 - tid(e["teamId"])].append(e["t"])
        T["tuerme"] = [_zaehler(k, S) for k in tuerme]
        T["gebaeude"] = [_zaehler(k, S) for k in geb]
        T["platten"] = [_zaehler(k, S) for k in platten]
        T["inhibs_offen"] = inhib_down
        mon = {k: [[], []] for k in ("drachen", "elder", "larven", "herold", "baron", "alle")}
        for e in ev:
            if e["typ"] != "ELITE_MONSTER_KILL" or e.get("killerTeamId") not in (g.BLAU, g.ROT):
                continue
            w = tid(e["killerTeamId"])
            art = {"DRAGON": "drachen", "HORDE": "larven", "RIFTHERALD": "herold", "BARON_NASHOR": "baron"}.get(e["monsterType"])
            if e.get("monsterSubType") == "ELDER_DRAGON":
                art = "elder"
            if art:
                mon[art][w].append(e["t"])
                mon["alle"][w].append(e["t"])
        for k, v in mon.items():
            T[k] = [_zaehler(z, S) for z in v]
        T["seele"] = [(T["drachen"][i] >= 4).astype(float) for i in (0, 1)]
        for k, dauer in (("baron", BARON_BUFF), ("elder", ELDER_BUFF)):
            buff = [np.zeros(S), np.zeros(S)]
            for i in (0, 1):
                for t in mon[k][i]:
                    a = int(math.ceil(t))
                    seg = np.arange(a, min(S, a + dauer))
                    buff[i][seg] = np.maximum(buff[i][seg], t + dauer - seg)
            T[f"{k}_buff"] = buff
        for k, arr in (("itemwert_team", self.item), ("level_team", self.level), ("cs_team", self.cs)):
            T[k] = [arr[[q for q in range(1, 11) if self.team[q] == i]].sum(0) for i in (0, 1)]
        T["tote"] = [(~self.lebt[[q for q in range(1, 11) if self.team[q] == i]]).sum(0).astype(float) for i in (0, 1)]
        T["gold"] = [self.tg[[q for q in range(1, 11) if self.team[q] == i]].sum(0) for i in (0, 1)]
        self.T = T

    # ---- Objective-Timer und -Tabelle
    def _objectives(self):
        p, S = self.p, self.S
        sek = self.sek
        ems = sorted((e for e in p.events if e["typ"] == "ELITE_MONSTER_KILL"), key=lambda e: e["t"])
        da = {k: np.zeros(S) for k in ("drache", "larven", "herold", "baron")}
        bis = {k: np.full(S, -1.0) for k in da}
        elder_naechst = np.zeros(S)
        self.spawns = []                          # (sekunde, art-code)
        # Drache/Elder
        naechst, ist_elder, zaehl = DRACHE_ERST, False, {g.BLAU: 0, g.ROT: 0}
        s_prev = 0
        for e in [x for x in ems if x["monsterType"] == "DRAGON"] + [None]:
            ende = S if e is None else int(math.ceil(e["t"]))
            seg = np.arange(s_prev, ende)
            da["drache"][seg] = (seg >= naechst)
            bis["drache"][seg] = np.maximum(0, naechst - seg)
            elder_naechst[seg] = ist_elder
            if naechst < ende:
                self.spawns.append((int(naechst), 5 if ist_elder else 1))
            if e is None:
                break
            if e.get("killerTeamId") in zaehl and e.get("monsterSubType") != "ELDER_DRAGON":
                zaehl[e["killerTeamId"]] += 1
            ist_elder = max(zaehl.values()) >= 4
            naechst = ende + (ELDER_RESPAWN if ist_elder else DRACHE_RESPAWN)
            s_prev = ende
        # Larven
        lk = [int(math.ceil(e["t"])) for e in ems if e["monsterType"] == "HORDE"]
        ende_l = min(LARVEN_BIS, lk[2]) if len(lk) >= 3 else LARVEN_BIS
        da["larven"][LARVEN_VON:min(S, ende_l)] = 1
        bis["larven"][:LARVEN_VON] = LARVEN_VON - sek[:LARVEN_VON]
        bis["larven"][LARVEN_VON:min(S, ende_l)] = 0
        self.spawns.append((LARVEN_VON, 4))
        # Herold
        hk = [int(math.ceil(e["t"])) for e in ems if e["monsterType"] == "RIFTHERALD"]
        ende_h = min(HEROLD_BIS, hk[0]) if hk else HEROLD_BIS
        da["herold"][HEROLD_VON:min(S, ende_h)] = 1
        bis["herold"][:HEROLD_VON] = HEROLD_VON - sek[:HEROLD_VON]
        bis["herold"][HEROLD_VON:min(S, ende_h)] = 0
        if p.dauer > HEROLD_VON:
            self.spawns.append((HEROLD_VON, 3))
        # Baron
        naechst, s_prev = BARON_ERST, 0
        for e in [x for x in ems if x["monsterType"] == "BARON_NASHOR"] + [None]:
            ende = S if e is None else int(math.ceil(e["t"]))
            seg = np.arange(s_prev, ende)
            da["baron"][seg] = seg >= naechst
            bis["baron"][seg] = np.maximum(0, naechst - seg)
            if naechst < min(ende, p.dauer):
                self.spawns.append((int(naechst), 2))
            if e is None:
                break
            naechst, s_prev = ende + BARON_RESPAWN, ende
        self.obj_da, self.obj_bis, self.elder_naechst = da, bis, elder_naechst
        # Tabelle: jedes Monster mit Zustand (Entscheidung 3)
        kills = [e for e in p.events if e["typ"] == "CHAMPION_KILL"]
        self.obj_tab = []
        for e in ems:
            art = {"DRAGON": 1, "BARON_NASHOR": 2, "RIFTHERALD": 3, "HORDE": 4}.get(e["monsterType"], 0)
            if e.get("monsterSubType") == "ELDER_DRAGON":
                art = 5
            team = {g.BLAU: 0, g.ROT: 1}.get(e.get("killerTeamId"), -1)
            nk = sum(1 for k in kills if abs(k["t"] - e["t"]) <= 30 and g.abstand(k["position"], e["position"]) <= 3000)
            s = min(self.S - 1, int(round(e["t"])))
            nah = 0
            if team >= 0:
                for q in range(1, 11):
                    if self.team[q] != team and self.lebt[q, s] and \
                            math.hypot(self.x[q, s] - e["position"][0], self.y[q, s] - e["position"][1]) <= 3000:
                        nah += 1
            zustand = 2 if nk else (1 if nah >= 3 else 0)
            self.obj_tab.append((int(math.ceil(e["t"])), art, team, zustand, nk, nah, e["position"],
                                 e.get("killerId"), e.get("assistingParticipantIds") or []))


# ---------------------------------------------------------------- Zeitpunkte

def zeitpunkte(R: Raster, pid: int):
    """[(sekunde, anlass)] eines Spielers: volle Minuten + angesagte Ereignisse + eigene Ereignisse; eng beieinander
    (<= 5 s) -> nur der letzte (die Lage nach dem Ereignis-Buendel), Anlass nach Vorrang."""
    p = R.p
    pkt = [(60 * m, 0) for m in range(1, int(p.dauer // 60) + 1)]
    for e in p.events:
        s = int(math.ceil(e["t"]))
        if e["typ"] == "CHAMPION_KILL":
            pkt.append((s, 2 if e["victimId"] == pid else 1))
        elif e["typ"] == "BUILDING_KILL":
            pkt.append((s, 5))
        elif e["typ"] == "ELITE_MONSTER_KILL":
            pkt.append((s, 6))
    pkt += [(s, 7) for s, _ in R.spawns]
    pkt += [(int(math.ceil(tr)), 3) for _, tr in R.tode[pid]]
    pkt += [(s, 4) for s in R.back_start[pid]]
    pkt = sorted((s, a) for s, a in pkt if 30 <= s <= p.dauer - 10)
    vorrang = {2: 0, 4: 1, 3: 2, 6: 3, 5: 4, 1: 5, 7: 6, 0: 7}
    out = []
    for s, a in pkt:
        if out and s - out[-1][0] <= MERGE:
            a_alt = out[-1][1]
            out[-1] = (s, a if vorrang[a] < vorrang[a_alt] else a_alt)
        else:
            out.append((s, a))
    return out


# ---------------------------------------------------------------- Lage

def lage(R: Raster, pid: int, sek: np.ndarray) -> np.ndarray:
    p = R.p
    n = len(sek)
    X = np.full((n, len(NAMEN)), np.nan, np.float32)
    ich = R.team[pid]
    wir, geg = ich, 1 - ich
    team_nr = g.BLAU if ich == 0 else g.ROT
    rolle = p.rolle(pid)
    x, y = R.x[pid, sek], R.y[pid, sek]
    ber = bereich_np(x, y)
    X[:, SP["minute"]] = sek / 60
    X[:, SP["x"]], X[:, SP["y"]] = x, y
    X[:, SP["bereich"]] = ber
    X[:, SP["zone"]] = zone_np(ber)
    X[:, SP["in_eigener_lane"]] = ber == LANE_DER_ROLLE.get(rolle, -1)
    bx, by = g.BRUNNEN[team_nr]
    X[:, SP["abst_brunnen"]] = np.hypot(x - bx, y - by)
    for k, pos in (("abst_drache", g.DRACHE), ("abst_baron", g.BARON)):
        X[:, SP[k]] = np.hypot(x - pos[0], y - pos[1])
    for k, t_ziel in (("abst_eigener_turm", team_nr), ("abst_gegner_turm", g.gegner(team_nr))):
        d = np.full(n, np.inf)
        for key, pos in g.TUERME.items():
            if key[0] != t_ziel:
                continue
            steht = R.turm_steht[key][sek]
            d = np.where(steht, np.minimum(d, np.hypot(x - pos[0], y - pos[1])), d)
        X[:, SP[k]] = np.where(np.isinf(d), np.hypot(x - g.BRUNNEN[t_ziel][0], y - g.BRUNNEN[t_ziel][1]), d)
    lebt = R.lebt[pid, sek]
    X[:, SP["tot"]] = ~lebt
    X[:, SP["respawn_rest"]] = R.resp[pid, sek]
    X[:, SP["level"]] = R.level[pid, sek]
    X[:, SP["cs"]] = R.cs[pid, sek]
    X[:, SP["gold_tasche"]] = R.cg[pid, sek]
    X[:, SP["itemwert"]] = R.item[pid, sek]
    X[:, SP["leben_anteil"]] = np.where(lebt, R.hp[pid, sek], 0)
    X[:, SP["hat_tp"]] = p.hat_tp(pid)
    X[:, SP["seit_back"]] = R.seit_laden[pid, sek]
    # Team (Minimap)
    mit = sorted((q for q in range(1, 11) if R.team[q] == ich and q != pid), key=lambda q: ROLLEN.index(p.rolle(q)))
    ml = np.stack([R.lebt[q, sek] for q in mit])
    mx = np.stack([np.where(R.lebt[q, sek], R.x[q, sek], np.nan) for q in mit])
    my = np.stack([np.where(R.lebt[q, sek], R.y[q, sek], np.nan) for q in mit])
    d = np.hypot(mx - x, my - y)
    X[:, SP["mit_lebend"]] = ml.sum(0)
    X[:, SP["mit_nah"]] = np.nansum(d <= 2500, 0)
    with np.errstate(invalid="ignore"), __import__("warnings").catch_warnings():
        __import__("warnings").simplefilter("ignore", RuntimeWarning)
        X[:, SP["mit_abstand"]] = np.nanmean(d, 0)
    for i in range(4):
        X[:, SP[f"mit{i + 1}_x"]], X[:, SP[f"mit{i + 1}_y"]] = mx[i], my[i]
    # Scoreboard
    T = R.T
    for k in ("kills", "tuerme", "inhibs_offen", "platten", "drachen", "seele", "larven", "herold", "baron", "elder",
              "baron_buff", "elder_buff", "itemwert_team", "level_team", "cs_team", "tote"):
        X[:, SP[f"{k}_wir"]] = T[k][wir][sek]
        X[:, SP[f"{k}_gegner"]] = T[k][geg][sek]
    X[:, SP["diff_itemwert_team"]] = T["itemwert_team"][wir][sek] - T["itemwert_team"][geg][sek]
    X[:, SP["diff_level_team"]] = T["level_team"][wir][sek] - T["level_team"][geg][sek]
    lg = next((q for q in range(1, 11) if R.team[q] == geg and p.rolle(q) == rolle), None)
    if lg:
        X[:, SP["diff_itemwert_lane"]] = R.item[pid, sek] - R.item[lg, sek]
        X[:, SP["diff_level_lane"]] = R.level[pid, sek] - R.level[lg, sek]
        X[:, SP["diff_cs_lane"]] = R.cs[pid, sek] - R.cs[lg, sek]
        # DIE EINZIGE STELLE, an der eine Gegnerposition aus den Minuten in die Lage kommt (Entscheidung 1)
        lx, ly = R.x[lg, sek], R.y[lg, sek]
        nah = lebt & R.lebt[lg, sek] & (np.hypot(lx - x, ly - y) <= NAHE_SICHTBAR)
        X[:, SP["lg_nahe_sichtbar"]] = nah
        X[:, SP["lg_x"]] = np.where(nah, lx, np.nan)
        X[:, SP["lg_y"]] = np.where(nah, ly, np.nan)
    for i, r in enumerate(g.ROLLEN):
        q = next((q for q in range(1, 11) if R.team[q] == geg and p.rolle(q) == r), None)
        if q is None:
            continue
        X[:, SP[f"geg{i}_tot"]] = ~R.lebt[q, sek]
        X[:, SP[f"geg{i}_respawn"]] = R.resp[q, sek]
        gx, gy, ga = R.gesehen[q]
        X[:, SP[f"geg{i}_gesehen_x"]] = gx[sek]
        X[:, SP[f"geg{i}_gesehen_y"]] = gy[sek]
        X[:, SP[f"geg{i}_gesehen_alter"]] = ga[sek]
    for o in ("drache", "larven", "herold", "baron"):
        X[:, SP[f"{o}_da"]] = R.obj_da[o][sek]
        X[:, SP[f"{o}_bis"]] = R.obj_bis[o][sek]
    X[:, SP["drache_ist_elder"]] = R.elder_naechst[sek]
    return X


# ---------------------------------------------------------------- Aktion

def aktion_flags(R: Raster, pid: int, sek: np.ndarray, spiegel: bool = False, fremde_lane: bool = False):
    """Je Moment: Bitmaske der Aktionen im Fenster (s, s+60], dazu ziel, ziel_zustand, tp.
    `spiegel` (Nullprobe): eigene Position an der Diagonale gespiegelt (Top <-> Bot, Drache <-> Baron).
    `fremde_lane` (Nullprobe): die Lane der Rolle wird durch die gegenueberliegende ersetzt."""
    p = R.p
    S = R.S
    n = len(sek)
    flags = np.zeros(n, np.int32)
    ziel = np.zeros(n, np.int16)
    zustand = np.full(n, -1, np.int16)
    rolle = p.rolle(pid)
    ich = R.team[pid]

    def pos(s):
        s = np.minimum(s, S - 1)
        x, y = R.x[pid, s], R.y[pid, s]
        return (y, x) if spiegel else (x, y)

    def setze(code, maske):
        nonlocal flags
        flags |= np.where(maske, 1 << code, 0).astype(np.int32)

    e30, e60, e120 = np.minimum(sek + 30, S - 1), np.minimum(sek + 60, S - 1), np.minimum(sek + 120, S - 1)
    # Tot: >= 30 s des Fensters tot
    tot_s = np.array([(~R.lebt[pid, s + 1:min(S, s + 61)]).sum() for s in sek])
    setze(0, (tot_s >= 30) | ~R.lebt[pid, np.minimum(sek, S - 1)])
    # Back: Ladenbesuch (nicht nach Tod) beginnt im Fenster
    bs = np.array(R.back_start[pid] or [-10 ** 6])
    i = np.searchsorted(bs, sek, side="right")
    setze(1, (i < len(bs)) & (bs[np.minimum(i, len(bs) - 1)] <= sek + 60))
    # Objective: Monster-Kill im Fenster, du <= 3000 an der Grube (oder beteiligt); oder Spawn im Fenster, du <= 3000
    for (s_k, art, team, zst, nk, nah, opos, killer, helfer) in R.obj_tab:
        imf = (sek < s_k) & (s_k <= sek + 60)
        if not imf.any():
            continue
        x, y = pos(np.full(n, s_k))
        dran = (np.hypot(x - opos[0], y - opos[1]) <= 3000)
        if not spiegel:
            dran |= pid in {killer, *helfer}
        m = imf & dran & R.lebt[pid, min(s_k, S - 1)]
        neu = m & (ziel == 0)
        ziel[neu] = art
        zustand[neu] = zst
        setze(2, m)
    grube = {1: g.DRACHE, 5: g.DRACHE, 2: g.BARON, 3: g.BARON, 4: g.BARON}
    for s_sp, art in R.spawns:
        imf = (sek < s_sp) & (s_sp <= sek + 60)
        if not imf.any():
            continue
        x, y = pos(np.full(n, s_sp))
        m = imf & (np.hypot(x - grube[art][0], y - grube[art][1]) <= 3000) & R.lebt[pid, min(s_sp, S - 1)]
        neu = m & (ziel == 0)
        ziel[neu] = art
        setze(2, m)
    # TP: nur sicher erkannte Spruenge
    tp = np.where(p.hat_tp(pid), -1, 0).astype(np.int16) * np.ones(n, np.int16)
    for s_tp in R.tp_sicher.get(pid, []):
        m = (sek < s_tp) & (s_tp <= sek + 60)
        tp[m] = 1
        setze(3, m)
    # Positionen im Fenster
    x0, y0 = pos(sek)
    x30, y30 = pos(e30)
    x60, y60 = pos(e60)
    x120, y120 = pos(e120)
    b0, b30, b60, b120 = bereich_np(x0, y0), bereich_np(x30, y30), bereich_np(x60, y60), bereich_np(x120, y120)
    z0, z60, z120 = zone_np(b0), zone_np(b60), zone_np(b120)
    lebt60 = R.lebt[pid, e60] & R.lebt[pid, sek]
    # Rotation: Zonenwechsel, der 2 min haelt; nicht Jungler, keine Basis, lebend (wie Phase 0)
    rot = (rolle != "JUNGLE") & (z0 > 0) & (z60 > 0) & (z0 != z60) & (z120 == z60) & lebt60 & (tot_s == 0)
    setze(4, rot)
    ziel[rot & (ziel == 0)] = z60[rot & (ziel == 0)]
    # Mitspieler
    mit = [q for q in range(1, 11) if R.team[q] == ich and q != pid]

    def mit_nah(s, xs, ys, r):
        c = np.zeros(n)
        for q in mit:
            c += R.lebt[q, s] & (np.hypot(R.x[q, s] - xs, R.y[q, s] - ys) <= r)
        return c

    def mit_min(s, xs, ys):
        d = np.full(n, np.inf)
        for q in mit:
            d = np.where(R.lebt[q, s], np.minimum(d, np.hypot(R.x[q, s] - xs, R.y[q, s] - ys)), d)
        return d

    def mit_draussen(s):
        c = np.zeros(n)
        for q in mit:
            c += R.lebt[q, s] & (bereich_np(R.x[q, s], R.y[q, s]) > 1)
        return c
    # Split: ab 14:00, bei +30 und +60 allein in einer Seitenlane (Mitspieler >= 5000, >= 3 draussen)
    seite = lambda b: (b == 2) | (b == 4)
    split = (sek >= 14 * 60) & lebt60
    for s_, xs, ys, b in ((e30, x30, y30, b30), (e60, x60, y60, b60)):
        split &= seite(b) & (mit_min(s_, xs, ys) >= 5000) & (mit_draussen(s_) >= 3)
    split &= b30 == b60
    setze(5, split)
    # Gruppe: bei +60 mind. 2 lebende Mitspieler <= 2500, nicht in der Basis
    setze(6, lebt60 & (mit_nah(e60, x60, y60, 2500) >= 2) & (b60 > 1))
    # Jungle: Monster-CS +2 im Fenster
    setze(7, (R.jcs[pid, e60] - R.jcs[pid, sek] >= 2) & lebt60)
    # Lane: bei +30 und +60 in der Lane der Rolle, CS +3 (Support: ohne CS)
    lane = LANE_DER_ROLLE.get(rolle, -1)
    if fremde_lane and lane > 0:
        lane = {2: 4, 4: 2, 3: 2}[lane]
    if lane > 0:
        cs_ok = np.ones(n, bool) if rolle == "UTILITY" else (R.cs[pid, e60] - R.cs[pid, sek] >= 3)
        setze(8, (b30 == lane) & (b60 == lane) & cs_ok & lebt60)
    # Warten (Phase 0): lebt, bleibt im Bereich (<= 2500 bewegt), an keinem Ereignis beteiligt, keine andere Regel
    lebt0 = R.lebt[pid, np.minimum(sek, S - 1)]
    dabei = np.zeros(n, bool)
    for t_e in R.beteiligt.get(pid, []):
        dabei |= (sek < t_e) & (t_e <= sek + 60)
    ruhig = (b60 == b0) & (np.hypot(x60 - x0, y60 - y0) <= 2500) & ~dabei
    setze(9, (flags == 0) & lebt0 & ruhig)
    # Unterwegs: lebt, keine Regel trifft (laeuft irgendwohin, kaempft ohne Objective, ...). Stirbt er im Fenster,
    # ist das Folge, nicht Aktion.
    setze(10, (flags == 0) & lebt0)
    return flags, ziel, zustand, tp


def primaer(flags: np.ndarray) -> np.ndarray:
    """Erste zutreffende Aktion in AKTIONEN-Reihenfolge; -1 = nichts (tot < 30 s und keine Regel)."""
    out = np.full(len(flags), -1, np.int16)
    for code in range(len(AKTIONEN) - 1, -1, -1):
        out[(flags >> code) & 1 == 1] = code
    return out


# ---------------------------------------------------------------- Folge

def folge(R: Raster, pid: int, sek: np.ndarray) -> np.ndarray:
    p = R.p
    n = len(sek)
    Fo = np.full((n, len(FOLGE)), np.nan, np.float32)
    wir, geg = R.team[pid], 1 - R.team[pid]
    T = R.T
    tode = np.sort(np.ceil([td for td, _ in R.tode[pid]])) if R.tode[pid] else np.zeros(0)
    for dt in (30, 60, 120):
        ende = sek + dt
        ok = ende <= p.dauer
        e = np.minimum(ende, R.S - 1)
        Fo[:, FI[f"gold_{dt}"]] = R.tg[pid, e] - R.tg[pid, sek]
        Fo[:, FI[f"xp_{dt}"]] = R.xp[pid, e] - R.xp[pid, sek]
        Fo[:, FI[f"teamgold_{dt}"]] = (T["gold"][wir][e] - T["gold"][geg][e]) - (T["gold"][wir][sek] - T["gold"][geg][sek])
        Fo[:, FI[f"tod_{dt}"]] = np.searchsorted(tode, e, side="right") > np.searchsorted(tode, sek, side="right")
        for k, kk in (("kills", "kills"), ("platten", "platten"), ("gebaeude", "gebaeude"), ("obj", "alle")):
            Fo[:, FI[f"{k}_wir_{dt}"]] = T[kk][wir][e] - T[kk][wir][sek]
            Fo[:, FI[f"{k}_gegner_{dt}"]] = T[kk][geg][e] - T[kk][geg][sek]
        Fo[~ok, FI[f"gold_{dt}"]:FI[f"obj_gegner_{dt}"] + 1] = np.nan     # Fenster laeuft ueber das Spielende
    return Fo


# ---------------------------------------------------------------- eine Partie

_LIGA, _AUFT = {}, {}


def _init(liga, auft):
    _LIGA.update(liga)
    _AUFT.update(auft)


def baue_partie(args):
    nr, mid = args
    liga, auft = _LIGA, _AUFT
    p = g.Partie(g.lade(mid))
    R = Raster(p)
    for x in abl.tps(p, "sicher"):
        R.tp_sicher.setdefault(x["pid"], []).append(int(math.ceil(x["t"])))
    spaet = p.k["start"] >= auft["stichtag_ms"]
    Xs, Ms, As, Fs = [], [], [], []
    for pid in range(1, 11):
        zp = zeitpunkte(R, pid)
        if not zp:
            continue
        sek = np.array([s for s, _ in zp], np.int64)
        X = lage(R, pid, sek)
        fl, ziel, zst, tp = aktion_flags(R, pid, sek)
        a = [primaer(fl)]
        for k in (60, 120, 180):
            s2 = np.minimum(sek + k, R.S - 1)
            f2, *_ = aktion_flags(R, pid, s2)
            a2 = primaer(f2)
            a2[sek + k > p.dauer - 10] = -1
            a.append(a2)
        A = np.stack(a + [fl.astype(np.int16), ziel, zst, tp], 1).astype(np.int16)
        s = p.sp[pid]
        pru = pruefspieler(s["puuid"], auft["salz"])
        M = np.zeros((len(sek), len(META)), np.int32)
        M[:, MI["partie"]] = nr
        M[:, MI["pid"]] = pid
        M[:, MI["team"]] = R.team[pid]
        M[:, MI["rolle"]] = ROLLEN.index(s["teamPosition"])
        M[:, MI["liga"]] = LIGEN.index(liga.get(s["puuid"], "unter Master"))
        M[:, MI["zeit"]] = sek
        M[:, MI["anlass"]] = [a_ for _, a_ in zp]
        M[:, MI["aufteilung"]] = int(pru) + 2 * int(spaet)
        M[:, MI["sieg"]] = int(bool(s["win"]))
        M[:, MI["dauer"]] = p.dauer
        Xs.append(X)
        Ms.append(M)
        As.append(A)
        Fs.append(folge(R, pid, sek))
    O = np.array([(nr, s_, art, team, zst, nk, nah) for (s_, art, team, zst, nk, nah, *_r) in R.obj_tab],
                 np.int32).reshape(-1, len(OBJ))
    return nr, np.concatenate(Xs), np.concatenate(Ms), np.concatenate(As), np.concatenate(Fs), O


# ---------------------------------------------------------------- alles

def merkmale_md() -> None:
    z = ["# Merkmals-Verzeichnis der Entscheidungsmomente (Auftrag 030)", "",
         "Erzeugt von `werkzeuge/challenger/phase1.py --merkmale`. Marke: **[B]** beobachtet (Ereignis oder volle "
         "Minute), **[G]** geschaetzt (zwischen den Minuten linear, Formel, Regel), **[U]** unbekannt (kommt nicht vor: "
         "was unbekannt ist, steht gar nicht in der Lage). Gegner: nur tot + Restzeit, zuletzt gesehen (angesagtes "
         "Ereignis) oder der Lane-Gegner nahe sichtbar (<= 1200) - sonst keine Gegnerposition.", ""]
    for titel, liste in (("meta (int32)", META), ("X – Lage (float32)", MERKMALE), ("aktion (int16)", AKTION),
                         ("folge (float32)", FOLGE), ("obj (int32)", OBJ)):
        z += [f"## {titel}", "", "| # | Name | Bedeutung | Quelle | |", "|---:|---|---|---|---|"]
        z += [f"| {i} | `{n}` | {b} | {q} | [{m}] |" for i, (n, b, q, m) in enumerate(liste)]
        z.append("")
    z += ["## Codes", "", f"- AKTIONEN: {', '.join(f'{i} {a}' for i, a in enumerate(AKTIONEN))} (-1 = keine Regel, "
          "z. B. kurz tot)", f"- BEREICHE: {', '.join(f'{i} {a}' for i, a in enumerate(BEREICHE))}",
          f"- ANLAESSE: {', '.join(f'{i} {a}' for i, a in enumerate(ANLAESSE))}",
          f"- MONSTER (ziel): {', '.join(f'{i} {a}' for i, a in enumerate(MONSTER))}",
          "", "## Aktionsregeln (Fenster = die naechsten 60 s)", "",
          "- **Tot:** jetzt tot oder mind. 30 s des Fensters tot.",
          "- **Back:** ein Ladenbesuch beginnt (Kauf, nicht bis 45 s nach dem Tod).",
          "- **Objective:** ein Monster faellt und du stehst <= 3000 an der Grube (oder bist beteiligt), oder es "
          "spawnt und du stehst <= 3000 dort. `ziel` = Monster, `ziel_zustand` = frei/bestritten/umkaempft.",
          "- **TP:** Positionssprung, der zu Fuss und per Recall nicht geht (Phase 0, Stufe sicher). Sonst `tp` = -1 "
          "(unbekannt), nie \"kein TP\", ausser der Spieler hat keinen TP.",
          "- **Rotation:** Zone (oben/mid/unten) bei +60 anders als jetzt und bei +120 noch dieselbe; nicht Jungler, "
          "nicht Basis, lebend. `ziel` = neue Zone.",
          "- **Split:** ab 14:00, bei +30 und +60 allein in derselben Seitenlane (Mitspieler >= 5000, >= 3 draussen).",
          "- **Gruppe:** bei +60 mind. zwei lebende Mitspieler <= 2500, nicht in der Basis.",
          "- **Jungle:** Monster-CS +2.",
          "- **Lane:** bei +30 und +60 in der Lane der Rolle und CS +3 (Support ohne CS).",
          "- **Warten:** lebt, bleibt im selben Bereich (<= 2500 bewegt), an keinem Kill/Gebaeude/Monster beteiligt, "
          "keine andere Regel.",
          "- **Unterwegs:** lebt, keine Regel trifft (laeuft, kaempft ohne Objective). Stirbt er im Fenster, ist das "
          "Folge, nicht Aktion.",
          "- `a0` = erste zutreffende in der Reihenfolge Tot, Back, Objective, TP, Rotation, Split, Gruppe, Jungle, "
          "Lane, Warten, Unterwegs; `flags` hat alle."]
    (g.BUCH / "merkmale.md").write_text("\n".join(z) + "\n", encoding="utf-8")


def bauen(neu: bool = False, prozesse: int = 20) -> int:
    ZIEL.mkdir(parents=True, exist_ok=True)
    g.verdichten(leise=True)
    import bestand
    bestand.pruefen()                             # schreibt nur daten/challenger/gueltig.json (neue Downloads)
    auft = aufteilung()
    liga = json.loads((g.ABLAGE / "liga.json").read_text(encoding="utf-8"))["spieler"]
    gueltig = json.loads((g.ABLAGE / "gueltig.json").read_text(encoding="utf-8"))
    pf = ZIEL / "partien.json"
    partien: list[str] = [] if neu or not pf.exists() else json.loads(pf.read_text(encoding="utf-8"))
    if neu:
        for f in ZIEL.glob("teil_*.npz"):
            f.unlink()
    bekannt = set(partien)
    offen = [m for m in gueltig if m not in bekannt]
    if not offen:
        return 0
    start_nr = len(partien)
    partien += offen
    teil = len(list(ZIEL.glob("teil_*.npz")))
    for a in range(0, len(offen), TEIL_GROESSE):
        stueck = offen[a:a + TEIL_GROESSE]
        jobs = [(start_nr + a + i, m) for i, m in enumerate(stueck)]
        with ProcessPoolExecutor(max_workers=prozesse, initializer=_init, initargs=(liga, auft)) as ex:
            res = sorted(ex.map(baue_partie, jobs, chunksize=2), key=lambda r: r[0])
        np.savez(ZIEL / f"teil_{teil:03d}.npz",
                 X=np.concatenate([r[1] for r in res]), meta=np.concatenate([r[2] for r in res]),
                 aktion=np.concatenate([r[3] for r in res]), folge=np.concatenate([r[4] for r in res]),
                 obj=np.concatenate([r[5] for r in res]))
        teil += 1
        pf.write_text(json.dumps(partien[:start_nr + a + len(stueck)]), encoding="utf-8")
        print(f"  Teil {teil}: {start_nr + a + len(stueck)} Partien", flush=True)
    return len(offen)


def lade(felder=("X", "meta", "aktion", "folge")):
    """Alle Teile als ein dict von Arrays (Reihenfolge = Partie-Nummer)."""
    teile = sorted(ZIEL.glob("teil_*.npz"))
    out = {f: [] for f in felder}
    for t in teile:
        with np.load(t) as d:
            for f in felder:
                out[f].append(d[f])
    return {f: np.concatenate(v) for f, v in out.items()}


if __name__ == "__main__":
    merkmale_md()
    if "--merkmale" not in sys.argv:
        n = bauen(neu="--neu" in sys.argv)
        print(f"neu gebaut: {n} Partien")
