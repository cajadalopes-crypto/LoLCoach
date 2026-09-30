"""Riot-Partien fuer die Kampf-Eichung laden (Buch 14, Schritt B / Auftrag 020).

Laeuft fuer sich allein, nur mit der Standardbibliothek, parallel zu allem anderen:
    python werkzeuge\riot_download.py            (Ziel 2000 Partien)
    python werkzeuge\riot_download.py 500        (anderes Ziel)
    python werkzeuge\riot_download.py 20000      (Makro-Daten, 30.09.: etwa 1500 Partien je Stunde)

- Schluessel aus geheim/riot_key.txt (wird nie ausgegeben).
- EUW Solo-Queue: Spieler aus Challenger, Grandmaster, Master -> deren letzte Ranked-Partien -> je Partie
  Match + Zeitleiste nach daten/riot/matches/ und daten/riot/timelines/ (gz-JSON).
- Grenzen des Entwickler-Schluessels: 20 je 1 s, 100 je 120 s; bei 429 wird Retry-After abgewartet.
- Fortsetzbar: vorhandene Dateien werden uebersprungen. Abbruch mit Strg+C jederzeit moeglich.
- Schluessel abgelaufen (401/403): klare Meldung, Ende. Neuen Schluessel eintragen, Skript neu starten.
"""
from __future__ import annotations

import gzip
import http.client
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
ZIEL = WURZEL / "daten" / "riot"
PLATTFORM = "https://euw1.api.riotgames.com"
REGION = "https://europe.api.riotgames.com"
QUEUE = 420  # Ranked Solo/Duo
JE_SPIELER = 100  # Match-IDs je Spieler (30.09.: fuer 20.000 Partien von 20 auf 100)
SEIT = int(time.time()) - 28 * 24 * 3600  # nur Partien der letzten 4 Wochen (aktuelle Patches)


class SchluesselUngueltig(Exception):
    pass


GRUND = {"text": ""}


def schluessel() -> str:
    p = WURZEL / "geheim" / "riot_key.txt"
    if not p.exists():
        sys.exit(f"Kein Schluessel: {p} fehlt.")
    k = p.read_text(encoding="utf-8-sig").strip()
    if not k.startswith("RGAPI-"):
        sys.exit("geheim/riot_key.txt enthaelt keinen Riot-Schluessel (beginnt mit RGAPI-).")
    return k


class Takt:
    """Gleitende Fenster: hoechstens 19 je 1 s und 98 je 120 s (etwas Luft unter den Grenzen)."""

    def __init__(self):
        self.fenster = [(1.0, 19, deque()), (120.0, 98, deque())]

    def warten(self):
        while True:
            jetzt = time.monotonic()
            pause = 0.0
            for dauer, n, q in self.fenster:
                while q and jetzt - q[0] >= dauer:
                    q.popleft()
                if len(q) >= n:
                    pause = max(pause, dauer - (jetzt - q[0]) + 0.05)
            if pause <= 0:
                for _, _, q in self.fenster:
                    q.append(jetzt)
                return
            time.sleep(pause)


TAKT = Takt()
KEY = ""


def hole(url: str, versuche: int = 6):
    for v in range(versuche):
        TAKT.warten()
        req = urllib.request.Request(url, headers={"X-Riot-Token": KEY, "User-Agent": "LoLCoach-Eichung"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                try:
                    msg = json.loads(e.read().decode("utf-8")).get("status", {}).get("message", "")
                except Exception:
                    msg = ""
                GRUND["text"] = f"HTTP {e.code} {msg}".strip()
                raise SchluesselUngueltig()
            if e.code == 404:
                return None
            if e.code == 429:
                warte = float(e.headers.get("Retry-After") or 10)
                print(f"  Grenze erreicht, warte {warte:.0f} s …", flush=True)
                time.sleep(warte + 1)
                continue
            if 500 <= e.code < 600:
                time.sleep(2 * (v + 1))
                continue
            print(f"  HTTP {e.code} bei {url.split('?')[0].rsplit('/', 2)[-2:]} – uebersprungen", flush=True)
            return None
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError,
                http.client.IncompleteRead, http.client.HTTPException, json.JSONDecodeError, UnicodeDecodeError) as e:
            # abgerissene oder unvollstaendige Antwort: einfach noch einmal holen
            print(f"  Uebertragung unvollstaendig ({type(e).__name__}), neuer Versuch …", flush=True)
            time.sleep(3 * (v + 1))
    return None


def schreibe_gz(pfad: Path, daten) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    tmp = pfad.with_suffix(pfad.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(daten, f, separators=(",", ":"))
    os.replace(tmp, pfad)


def spieler() -> list[str]:
    """PUUIDs aus Challenger, Grandmaster, Master (gespeichert, damit ein Neustart nichts doppelt fragt)."""
    datei = ZIEL / "spieler.json"
    if datei.exists():
        return json.loads(datei.read_text(encoding="utf-8"))
    puuids: list[str] = []
    for liga in ("challengerleagues", "grandmasterleagues", "masterleagues"):
        d = hole(f"{PLATTFORM}/lol/league/v4/{liga}/by-queue/RANKED_SOLO_5x5")
        eintraege = (d or {}).get("entries", [])
        gruppe = []
        for e in eintraege:
            if e.get("puuid"):
                gruppe.append(e["puuid"])
            elif e.get("summonerId"):
                s = hole(f"{PLATTFORM}/lol/summoner/v4/summoners/{e['summonerId']}")
                if s and s.get("puuid"):
                    gruppe.append(s["puuid"])
            if liga == "masterleagues" and len(gruppe) >= 600:
                break
        random.shuffle(gruppe)
        puuids += gruppe
        print(f"{liga}: {len(gruppe)} Spieler", flush=True)
    ZIEL.mkdir(parents=True, exist_ok=True)
    datei.write_text(json.dumps(puuids), encoding="utf-8")
    return puuids


def main() -> None:
    global KEY
    KEY = schluessel()
    ziel_n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    (ZIEL / "matches").mkdir(parents=True, exist_ok=True)
    (ZIEL / "timelines").mkdir(parents=True, exist_ok=True)
    ids_datei = ZIEL / "match_ids.json"
    ids: list[str] = json.loads(ids_datei.read_text(encoding="utf-8")) if ids_datei.exists() else []
    gesehen = set(ids)
    fertig = lambda m: (ZIEL / "matches" / f"{m}.json.gz").exists() and (ZIEL / "timelines" / f"{m}.json.gz").exists()
    start = time.time()
    try:
        pu = spieler()
        # Match-IDs sammeln (etwas mehr als das Ziel)
        i = 0
        while len(ids) < ziel_n * 1.1 and i < len(pu):
            neu = hole(f"{REGION}/lol/match/v5/matches/by-puuid/{pu[i]}/ids?queue={QUEUE}&type=ranked&start=0&count={JE_SPIELER}"
                       f"&startTime={SEIT}") or []
            for m in neu:
                if m not in gesehen:
                    gesehen.add(m)
                    ids.append(m)
            i += 1
            if i % 10 == 0:
                ids_datei.write_text(json.dumps(ids), encoding="utf-8")
                print(f"IDs: {len(ids)} (aus {i} Spielern)", flush=True)
        ids_datei.write_text(json.dumps(ids), encoding="utf-8")
        # Matches + Zeitleisten
        offen = [m for m in ids if not fertig(m)]
        schon = len(ids) - len(offen)
        print(f"Partien: {schon} schon da, {len(offen)} offen, Ziel {ziel_n}", flush=True)
        geladen = 0
        for m in offen:
            if schon + geladen >= ziel_n:
                break
            mp = ZIEL / "matches" / f"{m}.json.gz"
            tp = ZIEL / "timelines" / f"{m}.json.gz"
            if not mp.exists():
                d = hole(f"{REGION}/lol/match/v5/matches/{m}")
                if d is None:
                    continue
                schreibe_gz(mp, d)
            if not tp.exists():
                t = hole(f"{REGION}/lol/match/v5/matches/{m}/timeline")
                if t is None:
                    continue
                schreibe_gz(tp, t)
            geladen += 1
            if geladen % 10 == 0:
                rate = geladen / max(1.0, time.time() - start)
                rest = (ziel_n - schon - geladen) / max(rate, 1e-6) / 60
                print(f"{schon + geladen}/{ziel_n} Partien · noch etwa {rest:.0f} min", flush=True)
                (ZIEL / "status.json").write_text(json.dumps(
                    {"partien": schon + geladen, "ziel": ziel_n, "stand": time.strftime("%Y-%m-%d %H:%M")}), encoding="utf-8")
        n = sum(1 for m in ids if fertig(m))
        (ZIEL / "status.json").write_text(json.dumps(
            {"partien": n, "ziel": ziel_n, "stand": time.strftime("%Y-%m-%d %H:%M"), "fertig": n >= ziel_n}), encoding="utf-8")
        print(f"Fertig: {n} Partien in daten/riot/.", flush=True)
    except SchluesselUngueltig:
        n = sum(1 for m in ids if fertig(m))
        (ZIEL / "status.json").write_text(json.dumps(
            {"partien": n, "ziel": ziel_n, "stand": time.strftime("%Y-%m-%d %H:%M"), "schluessel_abgelaufen": True}),
            encoding="utf-8")
        print(f"\nDer Riot-Schluessel ist abgelaufen oder ungueltig ({GRUND['text']}). Bisher {n} Partien gespeichert.\n"
              "Neuen Schluessel auf developer.riotgames.com erzeugen, in geheim/riot_key.txt eintragen und\n"
              "dieses Skript neu starten - es macht dort weiter, wo es aufgehoert hat.", flush=True)
    except KeyboardInterrupt:
        print("\nAbgebrochen. Neustart macht dort weiter.", flush=True)


if __name__ == "__main__":
    main()
