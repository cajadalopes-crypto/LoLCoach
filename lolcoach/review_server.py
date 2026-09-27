"""Review-Oberflaeche nach dem Spiel: http://127.0.0.1:8791

Partie waehlen, Zeitleiste durchklicken, Minimap-Wiedergabe jedes Moments (aus den
gespeicherten Positionen), Momentkarten und Lektionen - und mit dem Coach reden.

    python -m lolcoach review
"""
from __future__ import annotations

import json
import threading
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class _EinServer(ThreadingHTTPServer):
    allow_reuse_address = False  # Windows liesse sonst zwei Server auf denselben Port
from pathlib import Path
from urllib.parse import unquote

from . import aufzeichnung, ddragon, minimap, profil, review, verlauf

SEITE = Path(__file__).resolve().parent.parent / "web" / "review.html"
PORT = 8791

_laufend: dict[str, str] = {}      # Stamm -> Status der Analyse ("laeuft", "fertig", "Fehler: ...")
ansicht: dict = {"stamm": None, "zeit": None}   # was die Seite gerade zeigt (fuer Fragen per Sprache)
_cache: dict[str, dict] = {}       # Stamm -> Partie-Daten fuer die Oberflaeche


def _aufnahme(stamm: str) -> Path | None:
    pfad = aufzeichnung.ORDNER / f"{stamm}.jsonl.gz"
    return pfad if pfad.exists() and "/" not in stamm and "\\" not in stamm else None


def partien() -> list[dict]:
    aus = []
    try:
        kennzahlen = {k.stamm: k for k in profil.partien(aufzeichnung.ORDNER)}
    except Exception:
        kennzahlen = {}
    for pfad in sorted(aufzeichnung.ORDNER.glob("*.jsonl.gz"), reverse=True):
        stamm = pfad.name.removesuffix(".jsonl.gz")
        eintrag = {"stamm": stamm, "datum": stamm[:10], "uhr": stamm[11:13] + ":" + stamm[13:15]}
        if k := kennzahlen.get(stamm):     # schnell und ohne Minimap - der Verlauf ergaenzt, wenn es ihn gibt
            eintrag.update(champion=k.champion, gegner=k.gegner, dauer=k.dauer, kda=k.kda, id=k.champion_id,
                           ergebnis=k.ergebnis if k.dauer >= profil.KURZ else f"Test ({int(k.dauer) // 60}:{int(k.dauer) % 60:02d})")
        v = review.pfade(pfad)["verlauf"]
        if v.exists():
            try:
                d = json.loads(v.read_text(encoding="utf-8"))
                ich = next((s for s in d["spieler"] if s["ich"]), {})
                eintrag.update(champion=d["champion"], gegner=d["gegner"], ergebnis=d["ergebnis"],
                               dauer=d["dauer"], kda=ich.get("kda"), id=ich.get("id"))
            except (ValueError, KeyError):
                pass
        eintrag["review"] = review.pfade(pfad)["review"].exists()
        aus.append(eintrag)
    return aus


def fortschritt() -> list[dict]:
    """Kennzahlen aller Partien (neueste zuerst) mit dem Fokus aus ihrem Review."""
    aus = []
    for k in profil.partien(aufzeichnung.ORDNER):
        if k.dauer < profil.KURZ:
            continue
        r = profil._review(aufzeichnung.ORDNER, k.stamm) or {}
        aus.append({**asdict(k), "zaehlt": k.zaehlt, "fokus": r.get("naechste_partie") or "",
                    "fokus_umgesetzt": r.get("fokus_umgesetzt") or ""})
    return aus


_verlaeufe: dict[str, verlauf.Verlauf] = {}


def bildschirm(stamm: str, zeit: float) -> Path | None:
    pfad = _aufnahme(stamm)
    if pfad is None:
        return None
    if stamm not in _verlaeufe:
        _verlaeufe[stamm] = verlauf.baue(pfad)
    return verlauf.bildschirm_bei(pfad, _verlaeufe[stamm], zeit, toleranz=4.0)


def partie(stamm: str) -> dict:
    pfad = _aufnahme(stamm)
    if pfad is None:
        raise FileNotFoundError(stamm)
    if stamm not in _cache:
        v = verlauf.baue(pfad)
        _verlaeufe[stamm] = v
        verlauf.speichern(v, review.pfade(pfad)["verlauf"])
        daten = asdict(v)
        daten["schirme"] = bool(aufzeichnung.bildschirme(pfad))
        # Positionen fuer die Wiedergabe: jede Sekunde, gerundet
        daten["sekunden"] = [{"t": round(s.zeit), "g": s.gold, "l": s.leben, "d": s.itemgold_diff, "k": s.kills,
                              "p": s.positionen, "x": s.tot} for s in v.sekunden]
        _cache[stamm] = daten
    daten = dict(_cache[stamm])
    p = review.pfade(pfad)
    daten["review"] = json.loads(p["review"].read_text(encoding="utf-8")) if p["review"].exists() else None
    daten["gespraech"] = json.loads(p["gespraech"].read_text(encoding="utf-8")) if p["gespraech"].exists() else []
    daten["status"] = _laufend.get(stamm)
    return daten


def analyse_starten(stamm: str, neu: bool = False) -> str:
    pfad = _aufnahme(stamm)
    if pfad is None:
        return "unbekannt"
    if _laufend.get(stamm) == "laeuft":
        return "laeuft"
    _laufend[stamm] = "laeuft"

    def lauf():
        try:
            review.erstelle(pfad, neu=neu)
            _laufend[stamm] = "fertig"
        except Exception as e:
            _laufend[stamm] = f"Fehler: {type(e).__name__}: {e}"

    threading.Thread(target=lauf, daemon=True).start()
    return "laeuft"


class _Anfrage(BaseHTTPRequestHandler):
    def do_GET(self):
        pfad = unquote(self.path.split("?")[0])
        try:
            if pfad == "/":
                self._sende(SEITE.read_bytes(), "text/html; charset=utf-8")
            elif pfad == "/api/partien":
                self._json(partien())
            elif pfad == "/api/profil":
                self._json(fortschritt())
            elif pfad.startswith("/schirm/"):
                # /schirm/<stamm>/<spielzeit>: der gesicherte Spielbildschirm, der der Zeit am naechsten liegt
                _, _, stamm, zeit = pfad.split("/", 3)
                bild = bildschirm(stamm, float(zeit))
                if bild is None:
                    self.send_error(404)
                else:
                    self._datei(bild, "image/jpeg")
            elif pfad.startswith("/api/partie/"):
                self._json(partie(pfad.split("/")[3]))
            elif pfad == "/karte.png":
                self._datei(ddragon.ABLAGE / str(ddragon.version()) / "map11.png", "image/png")
            elif pfad.startswith("/icon/") and pfad.endswith(".png") and pfad[6:-4].isalnum():
                minimap._champion_bild(pfad[6:-4])
                self._datei(ddragon.ABLAGE / str(ddragon.version()) / "champion" / pfad[6:], "image/png")
            else:
                self.send_error(404)
        except FileNotFoundError:
            self.send_error(404)
        except Exception as e:
            self._json({"fehler": f"{type(e).__name__}: {e}"}, 500)

    def do_POST(self):
        pfad = unquote(self.path.split("?")[0])
        laenge = int(self.headers.get("Content-Length", 0) or 0)
        daten = json.loads(self.rfile.read(laenge) or b"{}") if laenge else {}
        teile = pfad.split("/")
        try:
            if len(teile) == 5 and teile[1] == "api" and teile[2] == "partie" and teile[4] == "analyse":
                self._json({"status": analyse_starten(teile[3], neu=bool(daten.get("neu")))})
            elif pfad == "/api/ansicht":
                ansicht["stamm"] = str(daten.get("stamm") or "") or None
                ansicht["zeit"] = daten.get("zeit")
                self._json({"ok": True})
            elif len(teile) == 5 and teile[1] == "api" and teile[2] == "partie" and teile[4] == "frage":
                aufnahme = _aufnahme(teile[3])
                if aufnahme is None:
                    self.send_error(404)
                    return
                antwort = review.frage(aufnahme, str(daten.get("text", ""))[:2000], daten.get("zeit"))
                self._json({"antwort": antwort})
            else:
                self.send_error(404)
        except Exception as e:
            self._json({"fehler": f"{type(e).__name__}: {e}"}, 500)

    def _datei(self, pfad: Path, art: str):
        if pfad.exists():
            self._sende(pfad.read_bytes(), art, cache=True)
        else:
            self.send_error(404)

    def _json(self, daten, code: int = 200):
        self._sende(json.dumps(daten, ensure_ascii=False).encode("utf-8"), "application/json", code=code)

    def _sende(self, koerper: bytes, art: str, cache: bool = False, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", art)
        self.send_header("Cache-Control", "max-age=3600" if cache else "no-store")
        self.end_headers()
        self.wfile.write(koerper)

    def log_message(self, *a):
        pass


class Sprachfragen:
    """Push-to-Talk im Review: Frage ueber das Headset zur Partie und zum Zeitpunkt, die die
    Seite gerade zeigt; Antwort mit der Coach-Stimme, beides im Gespraechsverlauf."""

    def __init__(self, taste: str, sprecher):
        from . import sprache
        self.sprecher = sprecher
        self.erkenner = sprache.Erkenner()
        self.ptt = sprache.PushToTalk(taste, self._frage, beim_druecken=sprecher.pausiere,
                                      beim_loslassen=getattr(sprecher, "taste_los", None))
        self.ptt.start()

    def _frage(self, audio) -> None:
        try:
            stamm = ansicht.get("stamm")
            if not stamm or _aufnahme(stamm) is None:
                self.sprecher.antworte("Oeffne zuerst eine Partie im Review.")
                return
            text = self.erkenner.text(audio)
            if not text or len(text.split()) < 2:
                self.sprecher.freigeben()
                return
            print(f"  Du: {text}", flush=True)
            antwort = review.frage(_aufnahme(stamm), text, ansicht.get("zeit"))
            print(f"  Coach: {antwort}", flush=True)
            self.sprecher.antworte(antwort)
        except Exception as e:
            print(f"  Sprachfrage fehlgeschlagen: {type(e).__name__}: {e}", flush=True)
            self.sprecher.freigeben()


def starte(port: int = PORT) -> ThreadingHTTPServer:
    server = _EinServer(("127.0.0.1", port), _Anfrage)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
