"""Challenger-Gehirn, Phase 0 (Auftrag 029): Partien laden, verdichten, Karte.

Die Riot-Partien in daten/riot/ sind gross (Zeitleiste mit Schadenslisten je Kill). Einmal verdichtet, liegt je
Partie eine kleine Pickle-Datei in daten/challenger/kompakt/ - fortsetzbar, der laufende Download bringt neue
Partien, `verdichten()` nimmt nur die fehlenden. Mit dabei: die Feldzaehlung fuer den Feldkatalog.

Nur Standardbibliothek. Liest nichts aus lolcoach/ (Koordinaten unten sind aus lolcoach/bewertung.py kopiert).
"""
from __future__ import annotations

import gzip
import json
import math
import os
import pickle
import sys
import tomllib
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
RIOT = WURZEL / "daten" / "riot"
ABLAGE = WURZEL / "daten" / "challenger"
KOMPAKT = ABLAGE / "kompakt"
BUCH = WURZEL / "buecher" / "challenger"

BLAU, ROT = 100, 200
BRUNNEN = {BLAU: (400, 400), ROT: (14340, 14390)}          # Q: lolcoach/bewertung.py
TUERME = {                                                 # (Team, Lane, Stufe) -> Ort; Q: lolcoach/bewertung.py
    (BLAU, "Top", 1): (981, 10441), (BLAU, "Top", 2): (1512, 6699), (BLAU, "Top", 3): (1169, 4287),
    (BLAU, "Mid", 1): (5846, 6396), (BLAU, "Mid", 2): (5048, 4812), (BLAU, "Mid", 3): (3651, 3696),
    (BLAU, "Bot", 1): (10504, 1029), (BLAU, "Bot", 2): (6919, 1483), (BLAU, "Bot", 3): (4281, 1253),
    (ROT, "Top", 1): (4318, 13875), (ROT, "Top", 2): (7943, 13411), (ROT, "Top", 3): (10481, 13650),
    (ROT, "Mid", 1): (8955, 8510), (ROT, "Mid", 2): (9767, 10113), (ROT, "Mid", 3): (11134, 11207),
    (ROT, "Bot", 1): (13866, 4505), (ROT, "Bot", 2): (13327, 8226), (ROT, "Bot", 3): (13624, 10572),
}
DRACHE = (9866, 4414)
BARON = (5007, 10471)          # auch Herold und Larven
WEGFAKTOR = 1.15               # Luftlinie -> Weg (Q: lolcoach/bewertung.py)
RECALL = 8.0                   # s Kanalisieren
TP_ID = 12                     # Beschwoererzauber Teleport (auch "Entfesselt")
ROLLEN = ("TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY")
ROLLE_DE = {"TOP": "Top", "JUNGLE": "Jungle", "MIDDLE": "Mid", "BOTTOM": "ADC", "UTILITY": "Support"}


def abstand(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def gegner(team: int) -> int:
    return ROT if team == BLAU else BLAU


def bereich(x: float, y: float) -> str:
    """Grober Kartenbereich: basis_blau/basis_rot, top/mid/bot (Lanes), fluss_oben/fluss_unten, jungle_<team>_<seite>.

    Die Lanes laufen an den Raendern (Top: links und oben, Bot: unten und rechts), Mid auf der Diagonale, der Fluss auf
    der Gegendiagonale x + y = 14800. Grenzen grob, fuer Auswertungen, nicht fuers Spiel."""
    if abstand((x, y), BRUNNEN[BLAU]) < 4200:
        return "basis_blau"
    if abstand((x, y), BRUNNEN[ROT]) < 4200:
        return "basis_rot"
    if x < 2300 or y > 12500:
        return "top"
    if y < 2300 or x > 12500:
        return "bot"
    if abs(x - y) < 1500:
        return "mid"
    s = x + y
    if abs(s - 14800) < 1700:
        return "fluss_oben" if y > x else "fluss_unten"
    team = "blau" if s < 14800 else "rot"
    return f"jungle_{team}_{'oben' if y > x else 'unten'}"


def lane_von(ber: str) -> str | None:
    return {"top": "Top", "mid": "Mid", "bot": "Bot"}.get(ber)


_MECH = None


def respawn(level: int, minute: float) -> float:
    """Todeszeit in s nach wissen/mechanik.toml (nur gelesen)."""
    global _MECH
    if _MECH is None:
        with open(WURZEL / "wissen" / "mechanik.toml", "rb") as f:
            m = tomllib.load(f)
        _MECH = next(v for v in m.values() if isinstance(v, dict) and "brw" in v)
    brw = _MECH["brw"][max(1, min(18, level)) - 1]
    tif = 0.0
    for s in _MECH["tif"]:
        if minute >= s["ab"]:
            tif = s["basis"] + math.ceil(2 * (minute - s["ab"])) * s["je_halbe_minute"]
    return brw * (1 + min(tif, 50.0) / 100)


# ---------------------------------------------------------------- Verdichten

EVENT_FELDER = {
    "CHAMPION_KILL": ("killerId", "victimId", "assistingParticipantIds", "position", "bounty", "shutdownBounty"),
    "ITEM_PURCHASED": ("participantId", "itemId"),
    "ITEM_SOLD": ("participantId", "itemId"),
    "ITEM_UNDO": ("participantId", "beforeId", "afterId"),
    "ITEM_DESTROYED": ("participantId", "itemId"),
    "WARD_PLACED": ("creatorId", "wardType"),
    "WARD_KILL": ("killerId", "wardType"),
    "BUILDING_KILL": ("killerId", "teamId", "buildingType", "laneType", "towerType", "position",
                      "assistingParticipantIds", "bounty"),
    "TURRET_PLATE_DESTROYED": ("killerId", "teamId", "laneType", "position"),
    "ELITE_MONSTER_KILL": ("killerId", "killerTeamId", "monsterType", "monsterSubType", "position",
                           "assistingParticipantIds", "bounty"),
    "DRAGON_SOUL_GIVEN": ("teamId", "name"),
    "LEVEL_UP": ("participantId", "level"),
    "CHAMPION_SPECIAL_KILL": ("killerId", "killType", "multiKillLength", "position"),
    "OBJECTIVE_BOUNTY_PRESTART": ("teamId", "actualStartTime"),
    "OBJECTIVE_BOUNTY_FINISH": ("teamId",),
    "GAME_END": ("winningTeam",),
    "FEAT_UPDATE": ("teamId", "featType", "featValue"),
    "CHAMPION_TRANSFORM": ("participantId", "transformType"),
}
SP_FELDER = ("participantId", "puuid", "teamId", "teamPosition", "individualPosition", "championName",
             "summoner1Id", "summoner2Id", "summoner1Casts", "summoner2Casts", "win", "kills", "deaths", "assists",
             "totalMinionsKilled", "neutralMinionsKilled", "goldEarned", "champLevel", "visionScore", "wardsPlaced",
             "wardsKilled", "detectorWardsPlaced", "visionWardsBoughtInGame", "damageDealtToBuildings",
             "damageDealtToTurrets", "totalTimeSpentDead", "gameEndedInEarlySurrender", "gameEndedInSurrender",
             "teamEarlySurrendered", "riotIdGameName", "item0", "item1", "item2", "item3", "item4", "item5", "item6",
             "allInPings", "assistMePings", "basicPings", "commandPings", "dangerPings", "enemyMissingPings",
             "enemyVisionPings", "getBackPings", "holdPings", "needVisionPings", "onMyWayPings", "pushPings",
             "retreatPings", "visionClearedPings", "timePlayed")
CH_FELDER = ("unseenRecalls", "visionScoreAdvantageLaneOpponent", "laneMinionsFirst10Minutes", "teleportTakedowns",
             "controlWardsPlaced", "wardTakedownsBefore20M", "turretPlatesTaken", "soloKills", "killParticipation",
             "maxCsAdvantageOnLaneOpponent", "maxLevelLeadLaneOpponent", "takedownsFirstXMinutes",
             "earliestDragonTakedown", "riftHeraldTakedowns", "epicMonsterSteals", "outnumberedKills",
             "killsNearEnemyTurret", "killsUnderOwnTurret", "pickKillWithAlly", "survivedSingleDigitHpCount",
             "getTakedownsInAllLanesEarlyJungleAsLaner", "gameLength")


def _zaehle(zaehler: Counter, bereich_: str, d: dict, tiefe: int = 0) -> None:
    """Feldzaehlung: (bereich, feld) -> [vorhanden, ungleich 0/leer]."""
    for k, v in d.items():
        name = f"{bereich_}.{k}"
        if isinstance(v, dict) and tiefe < 1 and k in ("challenges", "missions", "championStats", "damageStats",
                                                         "position", "objectives"):
            _zaehle(zaehler, name, v, tiefe + 1)
            continue
        zaehler[(name, "da")] += 1
        if v not in (None, 0, 0.0, "", [], {}, False):
            zaehler[(name, "wert")] += 1


def _verdichte_eine(mid: str):
    try:
        with gzip.open(RIOT / "matches" / f"{mid}.json.gz", "rt", encoding="utf-8") as f:
            m = json.load(f)
        with gzip.open(RIOT / "timelines" / f"{mid}.json.gz", "rt", encoding="utf-8") as f:
            t = json.load(f)
    except Exception as e:  # halbe Datei, kaputt
        return mid, None, f"{type(e).__name__}"
    i = m["info"]
    z: Counter = Counter()
    nenner: Counter = Counter()
    for k, v in i.items():
        if k not in ("participants", "teams"):
            z[(f"info.{k}", "da")] += 1
            if v not in (None, 0, "", [], {}):
                z[(f"info.{k}", "wert")] += 1
    nenner["info"] += 1
    sp = []
    for p in i["participants"]:
        _zaehle(z, "spieler", p)
        nenner["spieler"] += 1
        ch = p.get("challenges") or {}
        e = {k: p.get(k) for k in SP_FELDER}
        e["ch"] = {k: ch.get(k) for k in CH_FELDER}
        e["perks"] = [s.get("perk") for st in (p.get("perks") or {}).get("styles", []) for s in st.get("selections", [])]
        sp.append(e)
    teams = {}
    for tm in i["teams"]:
        _zaehle(z, "team", tm)
        nenner["team"] += 1
        teams[tm["teamId"]] = {"win": tm.get("win"), "obj": {k: v.get("kills") for k, v in tm.get("objectives", {}).items()},
                               "first": {k: v.get("first") for k, v in tm.get("objectives", {}).items()}}
    ti = t["info"]
    frames, events = [], []
    for fr in ti["frames"]:
        pf = {}
        for pid, d in fr["participantFrames"].items():
            _zaehle(z, "minute", d)
            nenner["minute"] += 1
            pos = d.get("position") or {}
            cs = d.get("championStats") or {}
            pf[int(pid)] = (pos.get("x"), pos.get("y"), d.get("totalGold"), d.get("currentGold"), d.get("xp"),
                            d.get("level"), d.get("minionsKilled"), d.get("jungleMinionsKilled"),
                            cs.get("movementSpeed"), cs.get("health"), cs.get("healthMax"))
        frames.append((fr["timestamp"], pf))
        for ev in fr["events"]:
            typ = ev.get("type")
            nenner[f"ereignis.{typ}"] += 1
            for k, v in ev.items():
                if k in ("type", "timestamp"):
                    continue
                z[(f"ereignis.{typ}.{k}", "da")] += 1
                if v not in (None, 0, "", [], {}):
                    z[(f"ereignis.{typ}.{k}", "wert")] += 1
            felder = EVENT_FELDER.get(typ)
            if felder is None:
                continue
            e = {"typ": typ, "t": ev["timestamp"] / 1000.0}
            for k in felder:
                if k in ev:
                    v = ev[k]
                    e[k] = (v["x"], v["y"]) if k == "position" else v
            events.append(e)
    kompakt = {
        "id": mid, "version": i.get("gameVersion", ""), "queue": i.get("queueId"), "dauer": i.get("gameDuration"),
        "start": i.get("gameCreation"), "ende": i.get("endOfGameResult"), "sp": sp, "teams": teams,
        "frames": frames, "events": events,
    }
    return mid, kompakt, (z, nenner)


def vorhandene_ids() -> list[str]:
    """Partien mit Match UND Zeitleiste (fertig geschrieben, .tmp zaehlt nicht)."""
    ms = {p.name[:-8] for p in (RIOT / "matches").glob("*.json.gz")}
    ts = {p.name[:-8] for p in (RIOT / "timelines").glob("*.json.gz")}
    return sorted(ms & ts)


def verdichten(prozesse: int = 6, leise: bool = False) -> int:
    """Alle noch nicht verdichteten Partien verdichten. Rueckgabe: Anzahl neu."""
    KOMPAKT.mkdir(parents=True, exist_ok=True)
    offen = [m for m in vorhandene_ids() if not (KOMPAKT / f"{m}.pkl").exists()]
    if not offen:
        return 0
    n = 0
    with ProcessPoolExecutor(max_workers=prozesse) as ex:
        for mid, k, zusatz in ex.map(_verdichte_eine, offen, chunksize=8):
            if k is None:
                print(f"  {mid}: nicht lesbar ({zusatz})", file=sys.stderr)
                continue
            tmp = KOMPAKT / f"{mid}.pkl.tmp"
            with open(tmp, "wb") as f:
                pickle.dump({"partie": k, "felder": zusatz[0], "nenner": zusatz[1]}, f, protocol=5)
            os.replace(tmp, KOMPAKT / f"{mid}.pkl")
            n += 1
            if not leise and n % 200 == 0:
                print(f"  verdichtet: {n}/{len(offen)}", flush=True)
    return n


def lade(mid: str, mit_feldern: bool = False):
    with open(KOMPAKT / f"{mid}.pkl", "rb") as f:
        d = pickle.load(f)
    return d if mit_feldern else d["partie"]


def alle(mit_feldern: bool = False):
    for p in sorted(KOMPAKT.glob("*.pkl")):
        yield lade(p.stem, mit_feldern)


# ---------------------------------------------------------------- Partie-Helfer

class Partie:
    """Bequemer Zugriff auf eine verdichtete Partie."""

    def __init__(self, k: dict):
        self.k = k
        self.id = k["id"]
        self.dauer = k["dauer"] or 0
        self.sp = {s["participantId"]: s for s in k["sp"]}
        self.frames = k["frames"]
        self.events = k["events"]
        self.sieger = next((t for t, v in k["teams"].items() if v["win"]), None)

    def team(self, pid: int) -> int:
        return self.sp[pid]["teamId"]

    def rolle(self, pid: int) -> str:
        return self.sp[pid]["teamPosition"] or ""

    def champ(self, pid: int) -> str:
        return self.sp[pid]["championName"]

    def pid_von(self, team: int, rolle: str) -> int | None:
        return next((p for p, s in self.sp.items() if s["teamId"] == team and s["teamPosition"] == rolle), None)

    def hat_tp(self, pid: int) -> bool:
        s = self.sp[pid]
        return TP_ID in (s["summoner1Id"], s["summoner2Id"])

    def tp_casts(self, pid: int) -> int:
        s = self.sp[pid]
        return (s["summoner1Casts"] if s["summoner1Id"] == TP_ID else 0) + \
               (s["summoner2Casts"] if s["summoner2Id"] == TP_ID else 0)

    def frame(self, minute: int):
        return self.frames[min(max(0, minute), len(self.frames) - 1)][1]

    def pos(self, pid: int, minute: int):
        f = self.frame(minute).get(pid)
        return (f[0], f[1]) if f and f[0] is not None else None

    def tempo(self, pid: int, minute: int) -> float:
        f = self.frame(minute).get(pid)
        return float(f[8] or 345) if f else 345.0

    def ev(self, *typen):
        return [e for e in self.events if e["typ"] in typen]

    def level_bei(self, pid: int, t: float) -> int:
        lv = 1
        for e in self.events:
            if e["typ"] == "LEVEL_UP" and e.get("participantId") == pid and e["t"] <= t:
                lv = max(lv, e["level"])
        return lv

    def tode(self, pid: int):
        """[(Todeszeit, Wiederbelebung)] aus Kills und Level."""
        if not hasattr(self, "_tode"):
            self._tode = {}
        if pid in self._tode:
            return self._tode[pid]
        out = self._tode[pid] = []
        for e in self.events:
            if e["typ"] == "CHAMPION_KILL" and e.get("victimId") == pid:
                out.append((e["t"], e["t"] + respawn(self.level_bei(pid, e["t"]), e["t"] / 60)))
        return out

    def tot_bei(self, pid: int, t: float) -> bool:
        return any(a <= t < b for a, b in self.tode(pid))


def uhr(t: float) -> str:
    t = max(0, int(round(t)))
    return f"{t // 60}:{t % 60:02d}"


if __name__ == "__main__":
    n = verdichten()
    print(f"neu verdichtet: {n}; gesamt {len(list(KOMPAKT.glob('*.pkl')))}")
