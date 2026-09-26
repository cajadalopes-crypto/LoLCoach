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
         "TurretKilled": "Turret_T2_L_03_A", "KillerName": "Minion_T100L0S01N0003", "Assisters": []},
        {"EventID": 4, "EventName": "ChampionKill", "EventTime": 650.0, "KillerName": "Turret_T1_C_05_A",
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
    print("\nOK")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
