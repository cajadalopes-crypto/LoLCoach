"""Text fuer die Konsole: Ereignisse als Saetze, Zustand als Kurzuebersicht.

Aus Sicht des eigenen Teams ("wir"/"Gegner"), im Replay ohne `--ich` aus
Sicht von Blau/Rot.
"""
from __future__ import annotations

from .zustand import BLAU, DRACHE_DE, ROLLE_DE, ROT, Ereignis, Partie, Spieler, gegenteam
from . import wissen


def uhr(sekunden: float) -> str:
    s = max(0, int(sekunden))
    return f"{s // 60}:{s % 60:02d}"


def seite(p: Partie, team: str | None) -> str:
    if team is None:
        return "?"
    if p.mein_team:
        return "wir" if team == p.mein_team else "Gegner"
    return "Blau" if team == BLAU else "Rot"


_LANE = {"L": "Top", "C": "Mid", "R": "Bot"}
_STUFE = {"03": "aussen", "02": "innen", "01": "Inhib", "05": "aussen", "04": "innen"}


def struktur(name: str) -> str:
    """Turret_T2_L_03_A -> "Top aussen"; Barracks_T2_R1 -> "Bot"."""
    teile = name.split("_")
    lane = _LANE.get(teile[2][:1], "?") if len(teile) > 2 else "?"
    if teile[0] == "Turret" and len(teile) > 3:
        stufe = "Nexus" if lane == "Mid" and teile[3] in ("01", "02") else _STUFE.get(teile[3], teile[3])
        return f"{lane} {stufe}"
    return lane


def wer(p: Partie, s: Spieler | None, roh: str = "") -> str:
    if s is None:
        if roh.startswith("Turret_T"):
            return f"Turm ({seite(p, BLAU if roh[8] == '1' else ROT)})"
        if roh.startswith("Minion_"):
            return "Vasallen"
        return roh or "?"
    if p.ich and s is p.ich:
        return f"du ({s.champion})"
    return f"{s.champion} ({seite(p, s.team)})"


def ereignis(p: Partie, e: Ereignis) -> str | None:
    d, t = e.daten, uhr(e.zeit)
    match e.art:
        case "ChampionKill":
            return f"{t}  {wer(p, e.taeter, d.get('KillerName', ''))} toetet {wer(p, e.opfer, d.get('VictimName', ''))}"
        case "DragonKill":
            art = DRACHE_DE.get(d.get("DragonType", ""), d.get("DragonType", "?"))
            geklaut = " - GEKLAUT" if d.get("Stolen") == "True" else ""
            return f"{t}  {seite(p, e.team)}: {art}-Drache{geklaut}"
        case "TurretKilled" | "InhibKilled":
            was = "Turm" if e.art == "TurretKilled" else "Inhibitor"
            besitzer = seite(p, gegenteam(e.team))
            return f"{t}  {was} faellt: {besitzer}, {struktur(d.get(e.art, ''))}"
        case "Ace":
            return f"{t}  ACE fuer {seite(p, e.team)}"
        case "FirstBlood" | "Multikill" | "MinionsSpawning" | "InhibRespawningSoon" | "InhibRespawned":
            return None  # kommt mit dem ChampionKill bzw. ist Rauschen
        case "GameStart":
            return f"{t}  Spielbeginn"
        case "GameEnd":
            return f"{t}  Spielende: {d.get('Result', '?')}"
        case _:
            name = next((v["name"] for v in wissen.objektive().values() if v.get("event") == e.art), None)
            if name:
                return f"{t}  {seite(p, e.team)}: {name}"
            return f"{t}  [{e.art}] {d}"  # unbekannt - sichtbar lassen, damit es auffaellt


def objective_zeile(p: Partie) -> str:
    teile = []
    for schl in ("drache", "larven", "herold", "atakhan", "baron"):
        n = p.naechster_spawn(schl)
        if n is None:
            continue
        name = wissen.objektive()[schl]["name"]
        if schl == "drache" and p.seele():
            name = "Aeltester"
        teile.append(f"{name} lebt" if n <= p.zeit else f"{name} {uhr(n)}")
    return " | ".join(teile)


def uebersicht(p: Partie) -> str:
    zeilen = [f"--- {uhr(p.zeit)} {p.modus}" + (" (Zuschauer)" if p.zuschauer and not p.ich else "")]
    unser, deren = (p.mein_team, gegenteam(p.mein_team)) if p.ich else (BLAU, ROT)
    diff = p.item_gold(unser) - p.item_gold(deren)
    zeilen.append(f"Kills {p.kills(unser)}:{p.kills(deren)}  Itemgold {diff:+d}  "
                  f"Drachen {len(p.drachen(unser))}:{len(p.drachen(deren))}")
    if p.ich:
        gold = f"  Gold {p.gold:.0f}" if p.gold is not None else ""
        zeilen.append(f"Du: {p.ich.champion} L{p.ich.level} {p.ich.kills}/{p.ich.tode}/{p.ich.assists} "
                      f"CS {p.ich.cs}{gold}")
        g = p.gegenueber()
        if g:
            zeilen.append(f"Lane: {g.champion} L{g.level} {g.kills}/{g.tode}/{g.assists} CS {g.cs}  "
                          f"Itemgold {p.ich.item_gold - g.item_gold:+d}"
                          + ("" if g.hat_flash else "  (spielt ohne Flash)"))
    tote = [s for s in p.spieler if s.tot and s.team == deren]
    if tote:
        zeilen.append("Gegner tot: " + ", ".join(f"{s.champion} {s.respawn:.0f}s" for s in tote))
    j = p.jungler(deren)
    if j:
        zeilen.append(f"Gegner-Jungler: {j.champion} L{j.level}" + (" (tot)" if j.tot else ""))
    zeilen.append(objective_zeile(p))
    return "\n".join(zeilen)


def rollen_tabelle(p: Partie) -> str:
    zeilen = []
    for team in (BLAU, ROT):
        zeilen.append(("Blau" if team == BLAU else "Rot") + ": " + ", ".join(
            f"{ROLLE_DE.get(s.rolle, s.rolle)} {s.champion}" for s in p.team(team)))
    return "\n".join(zeilen)
