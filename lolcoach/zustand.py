"""Spielzustand: ein Schnappschuss der Live-API als Objekt.

`partie(daten)` haengt NUR vom Schnappschuss ab. Die API schickt die
Ereignisliste jedes Mal ganz, also laesst sich alles (Objectives, Timer,
Seelen) daraus neu ableiten. Was "neu seit dem letzten Mal" ist, entscheidet
der Aufrufer ueber `Ereignis.id`.

Namen: die Anzeige-Namen (Champion, Zauber) kommen in der Sprache des
Clients. Fuer Vergleiche nimmt der Code die stabilen Schluessel aus den
`raw...`-Feldern ("MonkeyKing", "SummonerFlash").
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import ddragon, wissen

BLAU, ROT = "ORDER", "CHAOS"
ROLLEN = ("TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY")
ROLLE_DE = {"TOP": "Top", "JUNGLE": "Jungle", "MIDDLE": "Mid", "BOTTOM": "ADC",
            "UTILITY": "Support", "": "?"}
DRACHE_DE = {"Fire": "Hoellen", "Earth": "Berg", "Water": "Ozean", "Air": "Wolken",
             "Hextech": "Hextech", "Chemtech": "Chemtech", "Elder": "Aeltester"}


def gegenteam(team: str | None) -> str | None:
    return {BLAU: ROT, ROT: BLAU}.get(team)


@dataclass(frozen=True)
class Spieler:
    name: str
    champion: str          # Anzeige, Client-Sprache
    champion_id: str       # stabil, wie Data Dragon
    team: str
    rolle: str             # TOP/JUNGLE/MIDDLE/BOTTOM/UTILITY oder ""
    level: int
    kills: int
    tode: int
    assists: int
    cs: int
    ward_score: float
    tot: bool
    respawn: float         # Sekunden bis zum Wiedereinstieg, 0 wenn lebendig
    items: tuple[int, ...]
    item_gold: int         # Summe der Nicht-Verbrauchsgueter, Data-Dragon-Preise
    zauber: tuple[str, ...]  # stabile Schluessel, z. B. ("SummonerFlash", "SummonerTeleport")
    namen: frozenset[str] = field(repr=False)

    @property
    def hat_flash(self) -> bool:
        return "SummonerFlash" in self.zauber


@dataclass(frozen=True)
class Ereignis:
    id: int
    zeit: float
    art: str               # EventName der API
    daten: dict
    team: str | None       # wer davon profitiert (Killer-Team, bei Tuermen das Gegenteam des Besitzers)
    taeter: Spieler | None = None
    opfer: Spieler | None = None


@dataclass
class Partie:
    zeit: float
    modus: str
    spieler: list[Spieler]
    ich: Spieler | None
    gold: float | None     # nur das eigene; fremdes Gold liefert die API nicht
    ereignisse: list[Ereignis]
    zuschauer: bool

    @property
    def mein_team(self) -> str | None:
        return self.ich.team if self.ich else None

    def team(self, team: str) -> list[Spieler]:
        return [s for s in self.spieler if s.team == team]

    def gegner(self) -> list[Spieler]:
        return self.team(gegenteam(self.mein_team)) if self.ich else []

    def gegenueber(self, sp: Spieler | None = None) -> Spieler | None:
        """Lane-Gegner: gleiche Rolle im anderen Team."""
        sp = sp or self.ich
        if not sp or not sp.rolle:
            return None
        return next((s for s in self.team(gegenteam(sp.team)) if s.rolle == sp.rolle), None)

    def jungler(self, team: str) -> Spieler | None:
        return next((s for s in self.team(team) if s.rolle == "JUNGLE"), None)

    def item_gold(self, team: str) -> int:
        return sum(s.item_gold for s in self.team(team))

    def kills(self, team: str) -> int:
        return sum(s.kills for s in self.team(team))

    # --- Objectives ---------------------------------------------------------

    def kills_von(self, art: str) -> list[Ereignis]:
        return [e for e in self.ereignisse if e.art == art]

    def drachen(self, team: str) -> list[str]:
        return [e.daten.get("DragonType", "?") for e in self.kills_von("DragonKill")
                if e.team == team and e.daten.get("DragonType") != "Elder"]

    def seele(self) -> str | None:
        for t in (BLAU, ROT):
            if len(self.drachen(t)) >= 4:
                return t
        return None

    def naechster_spawn(self, schluessel: str) -> float | None:
        """Spielzeit des naechsten Spawns; None = kommt nicht (mehr).

        Liegt der Wert in der Vergangenheit, lebt das Objective gerade.
        """
        obj = wissen.objektive()
        if schluessel == "drache":
            kills = self.kills_von("DragonKill")
            if not kills:
                return obj["drache"]["erster"]
            letzter = kills[-1]
            if letzter.daten.get("DragonType") == "Elder":
                return letzter.zeit + obj["aeltester"]["respawn"]
            if self.seele():
                return letzter.zeit + obj["aeltester"]["erster"]
            return letzter.zeit + obj["drache"]["respawn"]
        eintrag = obj[schluessel]
        kills = self.kills_von(eintrag.get("event", ""))
        if len(kills) >= eintrag.get("anzahl", 1):
            return kills[-1].zeit + eintrag["respawn"] if "respawn" in eintrag else None
        if "weg" in eintrag and self.zeit >= eintrag["weg"]:
            return None
        return eintrag.get("erster")


# --- Aufbau aus den Rohdaten --------------------------------------------------

_ZAUBER = re.compile(r"SummonerSpell_(\w+?)_DisplayName")
# Gemessen (Partie 26.09.2026): "Turret_TChaos_L2_P3_2521511112_0", "Inhib_TChaos_L2_P1_..."
# L2 = Top, L1 = Mid, L0 = Bot; P3 aussen, P2 innen, P1 Inhib-Turm, P4/P5 Nexus
_STRUKTUR = re.compile(r"^(Turret|Inhib)_T(Order|Chaos)_L(\d)_P(\d)")
_VASALL = re.compile(r"^Minion_T(100|200)")
LANE = {"2": "Top", "1": "Mid", "0": "Bot"}
STUFE = {"3": "aussen", "2": "innen", "1": "Inhib", "4": "Nexus", "5": "Nexus"}


@dataclass(frozen=True)
class Struktur:
    art: str               # "Turret" oder "Inhib"
    team: str              # Besitzer
    lane: str              # Top/Mid/Bot
    stufe: str             # aussen/innen/Inhib/Nexus


def struktur(name: str) -> Struktur | None:
    m = _STRUKTUR.match(name or "")
    if not m:
        return None
    art, team, lane, stufe = m.groups()
    return Struktur(art, BLAU if team == "Order" else ROT, LANE.get(lane, "?"),
                    "Inhib" if art == "Inhib" else STUFE.get(stufe, stufe))


def _zauber_schluessel(z: dict) -> str:
    m = _ZAUBER.search(z.get("rawDisplayName", ""))
    return m.group(1) if m else z.get("displayName", "?")


def _champion_id(roh: dict) -> str:
    raw = roh.get("rawChampionName", "")
    return raw.rsplit("_", 1)[-1] if raw else roh.get("championName", "?")


def _spieler(roh: dict) -> Spieler:
    namen = {roh[k] for k in ("summonerName", "riotId", "riotIdGameName") if roh.get(k)}
    if roh.get("isBot") or not namen:
        # Bots haben keinen Riot-Namen; Ereignisse nennen sie vermutlich beim Champion
        namen |= {roh[k] for k in ("championName", "rawChampionName") if roh.get(k)}
    namen = frozenset(namen)
    sc = roh.get("scores", {})
    zauber = tuple(_zauber_schluessel(z) for z in (roh.get("summonerSpells") or {}).values())
    items = roh.get("items", [])
    rolle = roh.get("position", "") or ("JUNGLE" if "SummonerSmite" in zauber else "")
    return Spieler(
        name=roh.get("riotIdGameName") or roh.get("summonerName") or roh.get("championName", "?"),
        champion=roh.get("championName", "?"),
        champion_id=_champion_id(roh),
        team=roh.get("team", ""),
        rolle=rolle,
        level=int(roh.get("level", 0)),
        kills=int(sc.get("kills", 0)),
        tode=int(sc.get("deaths", 0)),
        assists=int(sc.get("assists", 0)),
        cs=int(sc.get("creepScore", 0)),
        ward_score=float(sc.get("wardScore", 0.0)),
        tot=bool(roh.get("isDead", False)),
        respawn=float(roh.get("respawnTimer", 0.0)),
        items=tuple(int(i["itemID"]) for i in items),
        item_gold=sum(ddragon.item_preis(int(i["itemID"]), i.get("price", 0))
                      for i in items if not i.get("consumable")),
        zauber=zauber,
        namen=namen,
    )


def _team_des_namens(name: str, nach_name: dict[str, Spieler | None]) -> str | None:
    if name in nach_name:
        s = nach_name[name]
        return s.team if s else None  # None: Name doppelt (zwei "Varus-Bot")
    if s := struktur(name):
        return s.team
    if m := _VASALL.match(name):
        return BLAU if m.group(1) == "100" else ROT
    return None


def _namensbuch(spieler: list[Spieler]) -> dict[str, Spieler | None]:
    """Name -> Spieler. Ein Name, der mehrfach vorkommt (Bot-Partien: zwei
    gleiche Champions), zeigt auf None: lieber keine Zuordnung als eine falsche."""
    buch: dict[str, Spieler | None] = {}
    for s in spieler:
        for n in s.namen:
            buch[n] = None if n in buch and buch[n] is not s else s
    return buch


def _ereignis(roh: dict, nach_name: dict[str, Spieler | None]) -> Ereignis:
    art = roh.get("EventName", "?")
    taeter = nach_name.get(roh.get("KillerName", ""))
    opfer = nach_name.get(roh.get("VictimName", ""))
    if art in ("TurretKilled", "InhibKilled"):
        # {"TurretKilled": "Turret_TChaos_..."} - gehoerte Rot, also profitiert Blau
        team = gegenteam(_team_des_namens(roh.get(art, ""), nach_name))
    elif "KillerName" in roh:
        team = _team_des_namens(roh["KillerName"], nach_name)
        if team is None and opfer:
            team = gegenteam(opfer.team)
        if team is None:  # Killer mehrdeutig: die Helfer verraten das Team
            teams = {h.team for h in map(nach_name.get, roh.get("Assisters", [])) if h}
            team = teams.pop() if len(teams) == 1 else None
    elif art == "Ace":
        team = roh.get("AcingTeam")
    else:
        team = None
    return Ereignis(id=int(roh.get("EventID", -1)), zeit=float(roh.get("EventTime", 0.0)),
                    art=art, daten=roh, team=team, taeter=taeter, opfer=opfer)


def partie(daten: dict, ich: str | None = None) -> Partie:
    """Baut den Zustand. `ich` (Champion oder Name) ersetzt den aktiven
    Spieler - noetig im Replay, wo die API keinen hat."""
    spieler = [_spieler(r) for r in daten.get("allPlayers", [])]
    nach_name = _namensbuch(spieler)

    aktiv = daten.get("activePlayer") or {}
    zuschauer = "error" in aktiv or not aktiv
    selbst = None
    if ich:
        klein = ich.lower()
        selbst = next((s for s in spieler if klein in (s.champion.lower(), s.champion_id.lower(), s.name.lower())), None)
    elif not zuschauer:
        kennung = {aktiv.get(k) for k in ("riotId", "summonerName", "riotIdGameName")} - {None}
        selbst = next((s for s in spieler if s.namen & kennung), None)

    ereignisse = [_ereignis(e, nach_name) for e in (daten.get("events") or {}).get("Events", [])]
    spiel = daten.get("gameData", {})
    return Partie(
        zeit=float(spiel.get("gameTime", 0.0)),
        modus=spiel.get("gameMode", "?"),
        spieler=spieler,
        ich=selbst,
        gold=None if zuschauer else aktiv.get("currentGold"),
        ereignisse=ereignisse,
        zuschauer=zuschauer,
    )
