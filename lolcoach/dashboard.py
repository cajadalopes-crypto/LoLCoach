"""Live-Dashboard fuer den zweiten Monitor: http://127.0.0.1:8790

Zeigt, was der Coach weiss: Minimap mit den zuletzt bekannten Positionen
(verblassend, mit Alter in Sekunden), Objective-Timer, Todes-Timer, Lane-
Vergleich und die letzten Ansagen. Nur lesen, nichts steuern.

Ein kleiner HTTP-Server im Hintergrund; der Kern schiebt je Takt den
Zustand hinein (`aktualisiere`), die Seite fragt zweimal je Sekunde nach.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class _EinServer(ThreadingHTTPServer):
    allow_reuse_address = False  # Windows liesse sonst zwei Server auf denselben Port
from pathlib import Path

from . import ddragon, minimap, wissen
from .ansicht import uhr
from .zauber import NAME_DE
from .zustand import DRACHE_DE, ROLLE_DE, Partie, gegenteam

SEITE = Path(__file__).resolve().parent.parent / "web" / "dashboard.html"
PORT = 8790


def zustand_json(p: Partie, lagebild=None, ansagen=()) -> dict:
    wir = p.mein_team
    spieler = []
    for s in p.spieler:
        eintrag = {"name": s.name, "id": s.champion_id, "champion": s.champion, "rolle": ROLLE_DE.get(s.rolle, ""),
                   "freund": s.team == wir, "ich": s is p.ich, "tot": s.tot, "respawn": round(s.respawn),
                   "level": s.level, "cs": s.cs, "kda": f"{s.kills}/{s.tode}/{s.assists}", "itemgold": s.item_gold,
                   "gesehen": None}
        if lagebild is not None and (g := lagebild.gesehen(s)) and not s.tot:
            eintrag["gesehen"] = {"vor": round(max(0.0, p.zeit - g[0]), 1), "x": g[1], "y": g[2],
                                  "jetzt": lagebild.sichtbar(s), "ort": minimap.ort(g[1], g[2], wir)}
        timer = getattr(lagebild, "zauber", None)
        eintrag["zauber_weg"] = [{"name": NAME_DE.get(z, z), "rest": round(r)}
                                 for z in s.zauber if timer and (r := timer.fehlt(s, z, p.zeit))]
        spieler.append(eintrag)
    objectives = []
    for schl in ("drache", "larven", "herold", "baron"):
        n = p.naechster_spawn(schl)
        if n is None:
            continue
        name = "Ältester" if schl == "drache" and p.seele() else wissen.objektive()[schl]["name"]
        objectives.append({"name": name, "rest": round(n - p.zeit)})
    g = p.gegenueber()
    return {
        "zeit": uhr(p.zeit), "sekunden": round(p.zeit),
        "ich": p.ich.champion if p.ich else None,
        "bild": bool(lagebild is not None and lagebild.aktiv),
        "spieler": spieler,
        "objectives": objectives,
        "kills": [p.kills(wir), p.kills(gegenteam(wir))] if wir else None,
        "drachen": [[DRACHE_DE.get(d, d) for d in p.drachen(t)] for t in (wir, gegenteam(wir))] if wir else None,
        "itemgold": p.item_gold(wir) - p.item_gold(gegenteam(wir)) if wir else 0,
        "gold": round(p.gold) if p.gold is not None else None,
        "lane": None if not (g and p.ich) else {
            "gegner": g.champion, "cs": [p.ich.cs, g.cs], "level": [p.ich.level, g.level],
            "itemgold": p.ich.item_gold - g.item_gold},
        "ansagen": [{"zeit": uhr(a.gesprochen or a.zeit), "text": a.text, "prio": a.prio} for a in list(ansagen)[-7:]][::-1],
    }


class Dashboard:
    def __init__(self, port: int = PORT):
        self._json = b'{"warte": true}'
        self._schloss = threading.Lock()
        dashboard = self

        class Anfrage(BaseHTTPRequestHandler):
            def do_GET(self):
                pfad = self.path.split("?")[0]
                if pfad == "/":
                    self._sende(SEITE.read_bytes(), "text/html; charset=utf-8")
                elif pfad == "/zustand.json":
                    with dashboard._schloss:
                        self._sende(dashboard._json, "application/json")
                elif pfad == "/karte.png":
                    self._datei(ddragon.ABLAGE / str(ddragon.version()) / "map11.png")
                elif pfad.startswith("/icon/") and pfad.endswith(".png"):
                    cid = pfad[6:-4]
                    if cid.isalnum():
                        minimap._champion_bild(cid)  # laedt nach, falls noch nicht da
                        self._datei(ddragon.ABLAGE / str(ddragon.version()) / "champion" / f"{cid}.png")
                    else:
                        self.send_error(404)
                else:
                    self.send_error(404)

            def _datei(self, pfad: Path):
                if pfad.exists():
                    self._sende(pfad.read_bytes(), "image/png", cache=True)
                else:
                    self.send_error(404)

            def _sende(self, koerper: bytes, art: str, cache: bool = False):
                self.send_response(200)
                self.send_header("Content-Type", art)
                self.send_header("Cache-Control", "max-age=3600" if cache else "no-store")
                self.end_headers()
                self.wfile.write(koerper)

            def log_message(self, *a):
                pass

        self.server = _EinServer(("127.0.0.1", port), Anfrage)
        self.url = f"http://127.0.0.1:{port}/"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def aktualisiere(self, p: Partie, lagebild=None, ansagen=()) -> None:
        daten = json.dumps(zustand_json(p, lagebild, ansagen), ensure_ascii=False).encode("utf-8")
        with self._schloss:
            self._json = daten
