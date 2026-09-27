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
import time
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
        eintrag = {"name": s.name, "id": s.champion_id, "team": s.team, "champion": s.champion,
                   "rolle": ROLLE_DE.get(s.rolle, ""),
                   "freund": s.team == wir, "ich": s is p.ich, "tot": s.tot, "respawn": round(s.respawn),
                   "level": s.level, "cs": s.cs, "kda": f"{s.kills}/{s.tode}/{s.assists}", "itemgold": s.item_gold,
                   "gesehen": None}
        if lagebild is not None and (g := lagebild.gesehen(s)) and not s.tot:
            eintrag["gesehen"] = {"vor": round(max(0.0, p.zeit - g[0]), 1), "x": g[1], "y": g[2],
                                  "jetzt": lagebild.sichtbar(s), "ort": minimap.ort(g[1], g[2], wir)}
        if lagebild is not None and hasattr(lagebild, "leben") and s.team == wir and s is not p.ich:
            eintrag["leben"] = lagebild.leben(s, p.zeit)
            eintrag["ult"] = lagebild.ult_bereit(s, p.zeit)
        timer = getattr(lagebild, "zauber", None)
        # die Beschwoererzauber UND die Ult (Chat "gp no ult", globale Ults von der Minimap) - bis 27.09. zeigte der
        # Kasten nur die Beschwoererzauber, eine bekannte Ult kam nie an
        eintrag["zauber_weg"] = [{"name": NAME_DE.get(z, z), "rest": round(r)}
                                 for z in (*s.zauber, "R") if timer and (r := timer.fehlt(s, z, p.zeit))]
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
        "jetzt": _jetzt(p, lagebild),
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
        "wellen": {l: z.worte(wir) for l in ("Top", "Mid", "Bot")
                   if lagebild is not None and hasattr(lagebild, "welle") and (z := lagebild.welle(l, p.zeit))} if wir else {},
        "ansagen": [{"zeit": uhr(a.gesprochen or a.zeit), "text": a.text, "prio": a.prio} for a in list(ansagen)[-7:]][::-1],
        "kern": _kern(lagebild),
    }


def _kern(lagebild) -> dict | None:
    """Buch 0: Modus (was gerade dein Job ist), ab Schritt 3 der Plan des Kerns mit Grund und die Top-3 mit EV (9.5),
    dazu die INFO-Zeilen, die nicht mehr gesprochen werden (Flash, Items, Level, CS - Kapitel 9.1)."""
    k = getattr(lagebild, "kern", None)
    if k is None:
        return None
    s = k.stand()
    return {"modus": s["modus"], "bereich": s["bereich"], "grund": s["grund"], "plan": s.get("plan"),
            "top": s.get("top", []), "gefahr": s.get("gefahr", False),
            "info": [{"zeit": uhr(i["zeit"]), "text": i["text"]} for i in s["info"]],
            # Buch 11, Kapitel 2 und 3: was nach dem Plan kommt, und was in den naechsten Minuten ansteht
            # (ein aelterer Kern hat beides nicht - dann None und leer, die Seite zeigt nichts davon)
            "danach": s.get("danach"),
            "zeitleiste": [{"uhr": e.get("uhr", ""), "in_s": e.get("in_s"), "text": e.get("text", ""),
                            "art": e.get("art", "")} for e in (s.get("zeitleiste") or [])]}


def _jetzt(p: Partie, lagebild) -> dict | None:
    """Der Kasten "Jetzt": Plan des Entscheiders, wer wie schnell bei dir sein kann, Fenster, Platten,
    Kauf, Todespreis - dieselben Zahlen, aus denen die Ansagen gebaut werden."""
    if lagebild is None or not getattr(lagebild, "aktiv", False) or not p.ich or p.ich.tot:
        return None
    try:
        from . import bewertung
        b = bewertung.bewerte(p, lagebild)
    except Exception:
        return None
    if b is None:
        return None
    e = getattr(lagebild, "entscheider", None)
    gefahr = [{"champion": g.champion, "id": g.s.champion_id, "sek": round(g.ankunft), "sichtbar": g.sichtbar,
               "seit": round(g.seit) if g.seit else None, "leben": g.leben}
              for g in sorted((g for g in b.gegner if not g.s.tot and g.ankunft is not None and not g.unbekannt
                               and b.plausibel(g)), key=lambda g: g.ankunft)[:4]]
    return {
        "plan": e.aktuell.satz if e is not None and e.aktuell is not None else None,
        "gefahr": gefahr,
        "unbekannt": [g.champion for g in b.unbekannte() if not g.s.tot],
        "fenster": [f"{t} ({int(s)} s)" for s, t in b.fenster()],
        "platten": b.platten_gegner,
        "kauf": b.kauf.satz() if b.kauf is not None else "",
        "tod": round(b.tod_kostet) if b.tod_kostet else None,
        "kraefte": b.vorsprung_satz(),
    }


class Dashboard:
    def __init__(self, port: int = PORT):
        self._json = b'{"warte": true}'
        self._schloss = threading.Lock()
        self._beobachter = None
        dashboard = self

        class Anfrage(BaseHTTPRequestHandler):
            def do_GET(self):
                pfad = self.path.split("?")[0]
                if pfad == "/":
                    self._sende(SEITE.read_bytes(), "text/html; charset=utf-8")
                elif pfad == "/zustand.json":
                    with dashboard._schloss:
                        self._sende(dashboard._json, "application/json")
                elif pfad == "/positionen.json":
                    # die Minimap mit 15 Bildern/s, direkt vom Beobachter - der Rest kommt je Sekunde
                    # (Carlos, Partie 4: "du refreshst doch richtig oft - warum zeigt die Seite 1/s?")
                    b = dashboard._beobachter
                    zeit, sichtungen = b.aktuell if b is not None else (0.0, [])
                    self._sende(json.dumps({"alter": round(time.time() - zeit, 2) if zeit else None, "s": [
                        [s.champion_id, s.team, round(s.x, 4), round(s.y, 4)] for s in sichtungen]}).encode(),
                        "application/json")
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

    def gehirn_setzen(self, gehirn) -> None:
        self._gehirn = gehirn

    def beobachter_setzen(self, beobachter) -> None:
        """Der Minimap-Leser der laufenden Partie (None danach) - Quelle fuer /positionen.json."""
        self._beobachter = beobachter

    def aktualisiere(self, p: Partie, lagebild=None, ansagen=()) -> None:
        z = zustand_json(p, lagebild, ansagen)
        # der Fokus aus dem letzten Review - die ganze Partie sichtbar, wie ein Zettel am Monitor
        if g := getattr(self, "_gehirn", None):
            z["fokus"] = g.fokus
            z["laneplan"] = list(getattr(g, "laneplan", []) or [])
        daten = json.dumps(z, ensure_ascii=False).encode("utf-8")
        with self._schloss:
            self._json = daten
