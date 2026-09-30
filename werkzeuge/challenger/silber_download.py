"""Silber- und Gold-Partien fuer den Kontrast (Auftrag 029, Schritt 5) - GEBAUT, NICHT GESTARTET. Das startet Carlos.

    python werkzeuge\\challenger\\silber_download.py            (Ziel 5000 Partien)
    python werkzeuge\\challenger\\silber_download.py 2000       (anderes Ziel)
    python werkzeuge\\challenger\\silber_download.py --trocken  (nur zaehlen, was schon da ist; kein Abruf)

- Spieler aus `league-exp-v4` (EUW, Solo/Duo): SILVER und GOLD, je Division I-IV, seitenweise; je Tier gleich viele.
- Je Spieler die letzten Ranked-Partien (Queue 420, letzte 4 Wochen), je Partie Match + Zeitleiste nach
  daten/riot_silbergold/matches/ und .../timelines/ (gz-JSON, wie daten/riot/). Eigener Ordner: die High-Elo-Daten
  bleiben rein.
- Liga je Spieler (Tier + Division beim Abruf) in daten/riot_silbergold/spieler.json - fuer "Silber macht X,
  Challenger macht Y".
- Eine Partie ist "Silber", wenn ihr Spieler aus der Liste Silber ist; die anderen neun koennen streuen (Matchmaking).
  Auswertungen nehmen deshalb die Liga je Spieler, nicht je Partie.
- Teilt sich den Schluessel und die Grenzen (100 je 120 s) mit `werkzeuge/riot_download.py`. Laufen beide
  gleichzeitig, bremsen sie sich gegenseitig (429 wird abgewartet, nichts geht kaputt) - besser nacheinander.
- Fortsetzbar, Strg+C jederzeit. Der Schluessel wird nie ausgegeben.
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))
import riot_download as rd  # noqa: E402  (nur benutzt, nicht geaendert: hole, Takt, schreibe_gz, schluessel)

ZIEL = rd.WURZEL / "daten" / "riot_silbergold"
TIERS = ("SILVER", "GOLD")
DIVISIONEN = ("I", "II", "III", "IV")
SEITEN_JE_DIVISION = 3      # ~205 Eintraege je Seite -> ~600 je Division, ~4900 Spieler gesamt
JE_SPIELER = 5              # wenige Partien je Spieler: viele verschiedene Spieler statt weniger Vielspieler


def spieler() -> dict:
    datei = ZIEL / "spieler.json"
    if datei.exists():
        return json.loads(datei.read_text(encoding="utf-8"))
    liste: dict[str, str] = {}
    for tier in TIERS:
        for div in DIVISIONEN:
            for seite in range(1, SEITEN_JE_DIVISION + 1):
                d = rd.hole(f"{rd.PLATTFORM}/lol/league-exp/v4/entries/RANKED_SOLO_5x5/{tier}/{div}?page={seite}") or []
                for e in d:
                    if e.get("puuid") and not e.get("inactive"):
                        liste.setdefault(e["puuid"], f"{tier} {div}")
                print(f"{tier} {div} Seite {seite}: {len(d)} Eintraege, gesamt {len(liste)}", flush=True)
                if len(d) == 0:
                    break
    ZIEL.mkdir(parents=True, exist_ok=True)
    datei.write_text(json.dumps(liste), encoding="utf-8")
    return liste


def main() -> None:
    ziel_n = next((int(a) for a in sys.argv[1:] if a.isdigit()), 5000)
    fertig = lambda m: (ZIEL / "matches" / f"{m}.json.gz").exists() and (ZIEL / "timelines" / f"{m}.json.gz").exists()
    ids_datei = ZIEL / "match_ids.json"
    ids: list[str] = json.loads(ids_datei.read_text(encoding="utf-8")) if ids_datei.exists() else []
    if "--trocken" in sys.argv:
        print(f"{sum(1 for m in ids if fertig(m))} Partien fertig, {len(ids)} IDs bekannt, Ziel {ziel_n}. Kein Abruf.")
        return
    (ZIEL / "matches").mkdir(parents=True, exist_ok=True)
    (ZIEL / "timelines").mkdir(parents=True, exist_ok=True)
    rd.KEY = rd.schluessel()
    gesehen = set(ids)
    seit = int(time.time()) - 28 * 24 * 3600
    start = time.time()
    try:
        liga = spieler()
        # je Tier abwechselnd, damit Silber und Gold gleich stark vertreten sind
        nach_tier = {t: [p for p, l in liga.items() if l.startswith(t)] for t in TIERS}
        for v in nach_tier.values():
            random.Random(29).shuffle(v)
        reihe = [p for paar in zip(*nach_tier.values()) for p in paar]
        i = 0
        while len(ids) < ziel_n * 1.1 and i < len(reihe):
            neu = rd.hole(f"{rd.REGION}/lol/match/v5/matches/by-puuid/{reihe[i]}/ids?queue={rd.QUEUE}&type=ranked"
                          f"&start=0&count={JE_SPIELER}&startTime={seit}") or []
            for m in neu:
                if m not in gesehen:
                    gesehen.add(m)
                    ids.append(m)
            i += 1
            if i % 20 == 0:
                ids_datei.write_text(json.dumps(ids), encoding="utf-8")
                print(f"IDs: {len(ids)} (aus {i} Spielern)", flush=True)
        ids_datei.write_text(json.dumps(ids), encoding="utf-8")
        offen = [m for m in ids if not fertig(m)]
        schon = len(ids) - len(offen)
        print(f"Partien: {schon} schon da, {len(offen)} offen, Ziel {ziel_n}", flush=True)
        geladen = 0
        for m in offen:
            if schon + geladen >= ziel_n:
                break
            mp, tp = ZIEL / "matches" / f"{m}.json.gz", ZIEL / "timelines" / f"{m}.json.gz"
            if not mp.exists():
                d = rd.hole(f"{rd.REGION}/lol/match/v5/matches/{m}")
                if d is None:
                    continue
                rd.schreibe_gz(mp, d)
            if not tp.exists():
                t = rd.hole(f"{rd.REGION}/lol/match/v5/matches/{m}/timeline")
                if t is None:
                    continue
                rd.schreibe_gz(tp, t)
            geladen += 1
            if geladen % 10 == 0:
                rate = geladen / max(1.0, time.time() - start)
                print(f"{schon + geladen}/{ziel_n} Partien · noch etwa "
                      f"{(ziel_n - schon - geladen) / max(rate, 1e-6) / 60:.0f} min", flush=True)
                (ZIEL / "status.json").write_text(json.dumps(
                    {"partien": schon + geladen, "ziel": ziel_n, "stand": time.strftime("%Y-%m-%d %H:%M")}),
                    encoding="utf-8")
        n = sum(1 for m in ids if fertig(m))
        (ZIEL / "status.json").write_text(json.dumps(
            {"partien": n, "ziel": ziel_n, "stand": time.strftime("%Y-%m-%d %H:%M"), "fertig": n >= ziel_n}),
            encoding="utf-8")
        print(f"Fertig: {n} Partien in {ZIEL}.", flush=True)
    except rd.SchluesselUngueltig:
        print(f"\nRiot-Schluessel abgelaufen oder ungueltig ({rd.GRUND['text']}). Neuen Schluessel in "
              "geheim/riot_key.txt eintragen und neu starten - es geht dort weiter.", flush=True)
    except KeyboardInterrupt:
        print("\nAbgebrochen. Neustart macht dort weiter.", flush=True)


if __name__ == "__main__":
    main()
