"""Grundlage: Live-API -> Zustand -> Ansicht, gegen einen nachgebauten Client.

Der Nachbau folgt dem Aufbau der echten API. Er ersetzt NICHT die Pruefung
an einer echten Aufnahme - er faengt nur Brueche im eigenen Code.

    python tests/test_grundlage.py
"""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import ansicht, liveapi, zustand  # noqa: E402

AUFSTELLUNG = [  # (Name, Champion, Rolle, Team, Zauber)
    ("Carlos", "Riven", "TOP", "ORDER", ("Flash", "Teleport")),
    ("Blau2", "Graves", "JUNGLE", "ORDER", ("Flash", "Smite")),
    ("Blau3", "Ahri", "MIDDLE", "ORDER", ("Flash", "Dot")),
    ("Blau4", "Jinx", "BOTTOM", "ORDER", ("Flash", "Heal")),
    ("Blau5", "Janna", "UTILITY", "ORDER", ("Flash", "Exhaust")),
    ("Rot1", "Camille", "TOP", "CHAOS", ("Ghost", "Teleport")),
    ("Rot2", "Lee Sin", "JUNGLE", "CHAOS", ("Flash", "Smite")),
    ("Rot3", "Syndra", "MIDDLE", "CHAOS", ("Flash", "Teleport")),
    ("Rot4", "Kai'Sa", "BOTTOM", "CHAOS", ("Flash", "Heal")),
    ("Rot5", "Nautilus", "UTILITY", "CHAOS", ("Flash", "Dot")),
]
INTERN = {"Lee Sin": "LeeSin", "Kai'Sa": "Kaisa"}


def spieler(name, champ, rolle, team, zauber, **extra):
    zid = INTERN.get(champ, champ)
    return {
        "championName": champ, "rawChampionName": f"game_character_displayname_{zid}",
        "riotId": f"{name}#EUW", "riotIdGameName": name, "summonerName": f"{name}#EUW",
        "team": team, "position": rolle, "level": extra.get("level", 6),
        "isDead": extra.get("tot", False), "respawnTimer": extra.get("respawn", 0.0),
        "items": [{"itemID": 1055, "price": 450, "consumable": False, "count": 1, "slot": 0},
                  {"itemID": 2003, "price": 50, "consumable": True, "count": 1, "slot": 1}],
        "scores": {"kills": extra.get("kills", 0), "deaths": 0, "assists": 0,
                   "creepScore": extra.get("cs", 40), "wardScore": 3.0},
        "summonerSpells": {f"summonerSpell{i}": {
            "displayName": z, "rawDisplayName": f"GeneratedTip_SummonerSpell_Summoner{z}_DisplayName"}
            for i, z in zip(("One", "Two"), zauber)},
    }


def schnappschuss():
    alle = [spieler(*a) for a in AUFSTELLUNG]
    alle[0].update(level=7)
    alle[0]["scores"].update(kills=2, creepScore=71)
    alle[6].update(isDead=True, respawnTimer=17.5)
    ev = [
        {"EventID": 0, "EventName": "GameStart", "EventTime": 0.0},
        {"EventID": 1, "EventName": "ChampionKill", "EventTime": 401.0, "KillerName": "Carlos",
         "VictimName": "Rot1", "Assisters": []},
        {"EventID": 2, "EventName": "DragonKill", "EventTime": 420.0, "DragonType": "Fire",
         "Stolen": "False", "KillerName": "Blau2", "Assisters": []},
        {"EventID": 3, "EventName": "TurretKilled", "EventTime": 600.0,
         "TurretKilled": "Turret_TChaos_L2_P3_2521511112_0", "KillerName": "Minion_T100L0S01N0003", "Assisters": []},
        {"EventID": 4, "EventName": "ChampionKill", "EventTime": 650.0, "KillerName": "Turret_TOrder_L1_P3_2254202041_0",
         "VictimName": "Rot2", "Assisters": []},
    ]
    return {
        "activePlayer": {"riotId": "Carlos#EUW", "riotIdGameName": "Carlos", "summonerName": "Carlos#EUW",
                         "currentGold": 1234.5, "level": 7},
        "allPlayers": alle,
        "events": {"Events": ev},
        "gameData": {"gameMode": "CLASSIC", "gameTime": 660.0, "mapNumber": 11},
    }


class _Client(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/liveclientdata/allgamedata":
            koerper, code = json.dumps(schnappschuss()).encode(), 200
        else:
            koerper, code = b'{"errorCode":"RESOURCE_NOT_FOUND","httpStatus":404}', 404
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(koerper)

    def log_message(self, *a):
        pass


def main():
    server = HTTPServer(("127.0.0.1", 0), _Client)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    basis = f"http://127.0.0.1:{server.server_port}"

    daten = liveapi.alles(basis)
    p = zustand.partie(daten)
    assert p.ich and p.ich.champion == "Riven" and p.mein_team == "ORDER", p.ich
    assert p.gold == 1234.5
    assert p.gegenueber().champion == "Camille"
    assert not p.gegenueber().hat_flash
    assert p.jungler("CHAOS").champion_id == "LeeSin"
    assert p.drachen("ORDER") == ["Fire"] and p.drachen("CHAOS") == []
    turm = next(e for e in p.ereignisse if e.art == "TurretKilled")
    assert turm.team == "ORDER", turm.team  # Rot hat den Turm verloren
    turmkill = [e for e in p.ereignisse if e.art == "ChampionKill"][-1]
    assert turmkill.team == "ORDER" and turmkill.opfer.champion == "Lee Sin"
    assert p.naechster_spawn("drache") == 420 + 300
    assert p.ich.item_gold > 0 and p.ich.item_gold == p.gegenueber().item_gold  # Trank zaehlt nicht

    # Replay: kein aktiver Spieler, Perspektive per --ich
    daten["activePlayer"] = {"error": "Spectator mode doesn't currently support this feature"}
    q = zustand.partie(daten)
    assert q.zuschauer and q.ich is None and q.gold is None
    assert zustand.partie(daten, ich="camille").mein_team == "CHAOS"

    try:
        liveapi.alles(basis.replace(str(server.server_port), "1"))
        raise AssertionError("kein Spiel haette KeinSpiel werfen muessen")
    except liveapi.KeinSpiel:
        pass

    print(ansicht.rollen_tabelle(p))
    for e in p.ereignisse:
        if s := ansicht.ereignis(p, e):
            print(s)
    print(ansicht.uebersicht(p))
    server.shutdown()
    echte_partie()
    print("\nOK")


def echte_partie():
    """Letzter Schnappschuss einer echten Bot-Partie (26.09.2026, Riven Top, Sieg).
    Faengt, was der Nachbau nicht kann: Riots wirkliche Namen und Formate."""
    daten = json.loads((Path(__file__).parent / "echt_botspiel_ende.json").read_text(encoding="utf-8"))
    p = zustand.partie(daten)
    assert p.ich and p.ich.champion == "Riven" and p.gegenueber().champion == "Shen"
    art = {}
    for e in p.ereignisse:
        art.setdefault(e.art, []).append(e)
    # alle zehn gefallenen Tuerme und beide Inhibs gehoerten Rot -> Blau profitiert
    assert len(art["TurretKilled"]) == 10 and all(e.team == "ORDER" for e in art["TurretKilled"])
    assert all(e.team == "ORDER" for e in art["InhibKilled"])
    assert [zustand.struktur(e.daten["TurretKilled"]).lane for e in art["TurretKilled"][:3]] == ["Top"] * 3
    # Larven: 1. Vi (Rot), 2. Riven geklaut, 3. Lee Sin (Blau)
    assert [e.team for e in art["HordeKill"]] == ["CHAOS", "ORDER", "ORDER"]
    assert p.drachen("ORDER") == ["Earth", "Air"]
    # jede Kill-Zuordnung steht, auch bei zwei "Varus-Bot" (dann ueber das Opfer)
    assert all(e.team in ("ORDER", "CHAOS") for e in art["ChampionKill"])
    assert p.kills("ORDER") == sum(1 for e in art["ChampionKill"] if e.team == "ORDER")
    assert art["GameEnd"][0].daten["Result"] == "Win"
    unbekannt = [e.art for e in p.ereignisse if ansicht.ereignis(p, e) and ansicht.ereignis(p, e).split()[1].startswith("[")]
    assert not unbekannt, unbekannt


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
