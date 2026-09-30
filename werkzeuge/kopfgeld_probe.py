"""Auftrag 033: Goldrand um Turm-Symbole der Minimap - ist das das Objective-Kopfgeld?

Kopfgeld liegt auf den Zielen des FUEHRENDEN Teams (das zurueckliegende bekommt Extragold). Dann muss gelten: Goldrand
an euren Tuermen <=> ihr fuehrt, Goldrand an ihren Tuermen <=> ihr liegt zurueck. Gemessen wird der Vorsprung aus dem
Wert der Items beider Teams (Live-API, zuletzt gesehen) plus 300 je Kill-Vorsprung als grobe Schaetzung.

Nur Sehen (Buch 17): die Aufnahmen liefern Bilder und die Wahrheit ueber den Spielstand zum Pruefen des Lesers.

    python werkzeuge/kopfgeld_probe.py [n] [seed]     -> buecher/challenger/sehen/kopfgeld_proben.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "werkzeuge"))
import sehen_eichung as se  # noqa: E402
from lolcoach import ddragon, sehen  # noqa: E402


def vorsprung(d: dict, team: str) -> int:
    wert = {"ORDER": 0, "CHAOS": 0}
    kills = {"ORDER": 0, "CHAOS": 0}
    for p in d["allPlayers"]:
        wert[p["team"]] += sum(ddragon.item_preis(it["itemID"], it.get("price", 0)) * it.get("count", 1)
                               for it in p["items"])
        kills[p["team"]] += p["scores"]["kills"]
    andere = "CHAOS" if team == "ORDER" else "ORDER"
    return wert[team] - wert[andere] + 300 * (kills[team] - kills[andere])


def proben(n: int = 60, seed: int = 3340) -> list[dict]:
    out = []
    for s, w, p in se.stichprobe(n, seed=seed, ab=840):
        team = se.mein_team(s) or "ORDER"
        d = se.schnappschuss(s, w)
        k = sehen.kopfgeld(se.lade_bgr(p), team)
        out.append({"stamm": s, "w": w, "pfad": str(p), "zeit": round(se.spielzeit(s, w)), "team": team,
                    "vorsprung": vorsprung(d, team), "gold_eigene": k["eigene"], "gold_gegner": k["gegner"]})
    return out


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 3340
    pr = proben(n, seed)
    (se.ABLAGE / "kopfgeld_proben.json").write_text(json.dumps(pr, indent=0), encoding="utf-8")
    for e in pr:
        print(e["stamm"][-6:], se.uhr(e["zeit"]), e["team"][0], "vorsprung", e["vorsprung"], "gold eigene/gegner",
              e["gold_eigene"], e["gold_gegner"])
