"""Flash-Messung (Qualitaetsrunde 1, Pruefung F2): wie viele Flash-Spruenge hat eine Aufnahme wirklich, wie viele
erkennt der Coach, und wo gehen sie verloren?

Carlos' erster Grund fuer den Abbruch am 27.09.: "keine Flash-Timer auf dem Dashboard". Der Weg zum Dashboard
stimmt (0a12ed3), aber die Erkennung fand in 9,5 min nur einen Flash. Erst messen, dann bauen.

Gemessen wird je Aufnahme:
  A. Spruenge (F2.1): dasselbe Icon springt zwischen zwei aufeinanderfolgenden Sichtungen (<= 0,25 s) um 300-450
     Einheiten (sichtungen.jsonl.gz, 15-60 Lesungen/s). Je Sprung: was die Live-Logik von heute daraus macht
     (minimap.Verfolger Schritt 3 + lage.ereignisse, hier auf den Sichtungen nachgerechnet) und wo er verloren geht.
  B. Was der Coach damals live als Sprung gemeldet hat (ereignisse.jsonl.gz, art "sprung").
  C. Dein eigenes Flash aus dem HUD (eigene: D/F) - die einzige sichere Wahrheit. Zeigt, ob die Sprung-Definition
     echte Flashs ueberhaupt sieht (die Minimap verfolgt dich wie jeden anderen).
  D. Chat-Zeilen "<Champion> hat Blitz benutzt" (Mitspieler klicken den Zauber in der Anzeigetafel an).
  E. Die Timer, die das Nachspielen heute eintraegt (lage.Lagebild.zauber, je Quelle).

    python werkzeuge/flash_messung.py <aufnahme> [--liste]
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np  # noqa: E402

from lolcoach import aufzeichnung, lage, minimap, zauber, zustand  # noqa: E402

E = minimap.KARTE_EINHEITEN
VON, BIS, LUECKE = 300.0, 450.0, 0.25          # F2.1
LIVE_LUECKE = 0.2                              # minimap.Verfolger: zwei Bilder hoechstens so weit auseinander
LIVE_VON, LIVE_BIS = 0.7 * minimap.FLASH_EINHEITEN, 1.45 * minimap.FLASH_EINHEITEN
RUHIG = 5 / 570 * E                            # "vorher ruhig": 5 px bei 570 (Referenz-Minimap)
BLEIBT = 6 / 570 * E                           # "bleibt am Landepunkt": 6 px
ZURUECK_S = 1.0                                # springt das Icon so bald zum Absprung zurueck: Verfolger-Fehler


def _zeilen(datei: Path):
    try:
        with gzip.open(datei, "rt", encoding="utf-8") as f:
            for z in f:
                try:
                    yield json.loads(z)
                except ValueError:
                    return
    except (OSError, EOFError):
        return


def _abstand(a, b) -> float:
    return math.hypot((a[0] - b[0]) * E, (a[1] - b[1]) * E)


def messen(pfad: Path) -> dict:
    stamm = pfad.name.removesuffix(".jsonl.gz")
    ordner = pfad.with_name(stamm + "_bilder")
    schnapp = [(w, p) for w, d in aufzeichnung.lies_mit_zeit(pfad) if (p := zustand.partie(d)).ich]
    wand = np.array([w for w, _ in schnapp])
    spiel = np.array([p.zeit for _, p in schnapp])

    def uhr(w: float) -> float:
        return float(np.interp(w, wand, spiel))

    def partie(w: float):
        return schnapp[min(len(schnapp) - 1, int(np.searchsorted(wand, w)))][1]

    letzte = schnapp[-1][1]
    ich, mein = letzte.ich, letzte.mein_team
    spieler = {s.champion_id: s for s in letzte.spieler}
    blinks = zauber.dash_champions()

    # --- A. Spruenge aus den Sichtungen -------------------------------------------------------------------------
    verlauf: dict[str, list] = {}
    for d in _zeilen(ordner / "sichtungen.jsonl.gz"):
        for cid, team, x, y, g in d["s"]:
            if g > 0:
                verlauf.setdefault(cid, []).append((d["w"], x, y))
    live = [(d["w"], d["champion_id"]) for d in _zeilen(ordner / "ereignisse.jsonl.gz") if d.get("art") == "sprung"]
    spruenge = []
    for cid, v in verlauf.items():
        sp = spieler.get(cid)
        for i in range(1, len(v)):
            (w0, x0, y0), (w1, x1, y1) = v[i - 1], v[i]
            weite = _abstand((x0, y0), (x1, y1))
            if w1 - w0 > LUECKE or not VON <= weite <= BIS:
                continue
            danach = [q for q in v[i + 1:] if q[0] - w1 <= ZURUECK_S]
            zurueck = any(_abstand((q[1], q[2]), (x0, y0)) <= BLEIBT for q in danach)
            halt = [q for q in danach if q[0] - w1 <= minimap.BESTAETIGT_NACH + 0.05]
            bleibt = bool(halt) and halt[-1][0] - w1 >= minimap.BESTAETIGT_NACH and \
                all(_abstand((q[1], q[2]), (x1, y1)) <= BLEIBT for q in halt)
            vor = v[max(0, i - 2):i]
            ruhig = len(vor) == 2 and vor[1][0] - vor[0][0] <= 0.45 and _abstand(vor[0][1:], vor[1][1:]) <= RUHIG
            p = partie(w1)
            s_jetzt = next((s for s in p.spieler if s.champion_id == cid), sp)
            # Wo geht er verloren? In der Reihenfolge der Live-Kette (Verfolger, dann lage.ereignisse)
            if zurueck:
                grund = "Verfolger-Fehler (Icon springt zurueck)"
            elif w1 - w0 > LIVE_LUECKE:
                grund = "Luecke > 0,2 s"
            elif not LIVE_VON <= weite <= LIVE_BIS:
                grund = "Weite"
            elif not ruhig:
                grund = "vorher nicht ruhig"
            elif not bleibt:
                grund = "nicht bestaetigt (bleibt nicht 0,2 s)"
            elif s_jetzt is None:
                grund = "Identitaet unbekannt"
            elif s_jetzt.team == mein:
                grund = "eigenes Team (kein Timer)"
            elif "SummonerFlash" not in s_jetzt.zauber:
                grund = "hat kein Flash"
            elif cid in blinks:
                grund = "Dash-Champion (ausgenommen)"
            elif s_jetzt.tot:
                grund = "tot"
            else:
                grund = "erkannt"
            spruenge.append({"w": w1, "zeit": uhr(w1), "cid": cid, "team": None if sp is None else sp.team,
                             "weite": round(weite), "grund": grund, "dash": cid in blinks,
                             "live": any(c == cid and abs(w - w1) <= 0.6 for w, c in live)})
    spruenge.sort(key=lambda s: s["w"])

    # --- C. Dein Flash aus dem HUD ------------------------------------------------------------------------------
    taste = "D" if ich.zauber and ich.zauber[0] == "SummonerFlash" else "F" if "SummonerFlash" in ich.zauber else None
    eigene_flash = []
    if taste:
        stand, kandidat = None, None
        for d in _zeilen(ordner / "ereignisse.jsonl.gz"):
            if d.get("art") != "eigene" or taste not in d["b"]:
                continue
            b = d["b"][taste]
            if stand is None:
                stand = b
            elif b != stand:
                if kandidat is not None and kandidat[0] == b:
                    if stand and not b:
                        eigene_flash.append(kandidat[1])
                    stand, kandidat = b, None
                else:
                    kandidat = (b, d["w"])
            else:
                kandidat = None
    eigene = []
    for w in eigene_flash:
        treffer = [s for s in spruenge if s["cid"] == ich.champion_id and -1.5 <= s["w"] - w <= 1.5]
        eigene.append({"zeit": uhr(w), "sprung": treffer[0]["grund"] if treffer else None,
                       "sichtbar": any(abs(q[0] - w) <= 1.0 for q in verlauf.get(ich.champion_id, []))})

    # --- D./E. Chat und die Timer des Nachspielens --------------------------------------------------------------
    chat = {}
    for d in _zeilen(ordner / "ereignisse.jsonl.gz"):
        if d.get("art") != "chat":
            continue
        p = partie(d["w"])
        for sp, schl, _ in zauber.aus_chat(d["text"], p):
            if schl == "SummonerFlash":
                stempel = zauber.chat_stempel(d["text"])
                chat.setdefault((sp.champion, stempel), (uhr(d["w"]), d["text"]))
    timer = []
    sicht = lage.sicht_fuer(pfad)
    if sicht:
        lb = lage.Lagebild()
        orig = lb.zauber.benutzt

        def benutzt(sp, z, zeit, quelle, zurueck=None):
            t = orig(sp, z, zeit, quelle, zurueck)
            if t is not None and z == "SummonerFlash":
                timer.append({"zeit": zeit, "champion": sp.champion, "quelle": quelle})
            return t
        lb.zauber.benutzt = benutzt
        for w, p in schnapp:
            for wb, s in sicht.zwischen(w, lage.champions(p)):
                lb.neu(p.zeit - (w - wb), s, p)
            lb.ereignisse(lambda wb, p=p, w=w: p.zeit - (w - wb), sicht.ereignisse(), p)
    return {"aufnahme": stamm, "dauer": float(spiel[-1]), "ich": ich.champion, "mein": mein, "spruenge": spruenge,
            "eigene": eigene, "chat": [{"zeit": t, "champion": c, "text": x} for (c, _), (t, x) in chat.items()],
            "timer": timer, "live_spruenge": len(live)}


def _uhr(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


def bericht(m: dict, liste: bool) -> None:
    from collections import Counter
    sp = m["spruenge"]
    gegner = [s for s in sp if s["team"] is not None and s["team"] != m["mein"]]
    print(f"== {m['aufnahme']} ({_uhr(m['dauer'])}, du: {m['ich']})")
    print(f"A. Spruenge 300-450 in <= 0,25 s: {len(sp)}  (Gegner: {len(gegner)}; live gemeldete Spruenge: "
          f"{m['live_spruenge']})")
    for g, n in Counter(s["grund"] for s in sp).most_common():
        print(f"     {n:3d}  {g}")
    ohne_fehler = [s for s in gegner if not s["grund"].startswith("Verfolger")]
    print(f"   Gegner ohne Verfolger-Fehler: {len(ohne_fehler)}, davon ohne eigenen Dash/Blink: "
          f"{sum(not s['dash'] for s in ohne_fehler)}; heute erkannt: {sum(s['grund'] == 'erkannt' for s in ohne_fehler)}")
    e = m["eigene"]
    print(f"C. Dein Flash (HUD): {len(e)} - davon als Sprung in den Sichtungen: {sum(x['sprung'] is not None for x in e)}, "
          f"die Live-Kette haette ihn bestaetigt: {sum(x['sprung'] in ('erkannt', 'eigenes Team (kein Timer)') for x in e)}")
    for x in e:
        print(f"     {_uhr(x['zeit'])}: {x['sprung'] or ('kein Sprung gesehen' if x['sichtbar'] else 'Icon verdeckt oder nicht gefunden')}")
    print(f"D. Chat 'hat Blitz benutzt': {len(m['chat'])}")
    for c in m["chat"]:
        print(f"     {_uhr(c['zeit'])} {c['champion']}: {c['text'][:70]}")
    print(f"E. Flash-Timer im Nachspielen: {len(m['timer'])} "
          + str(dict(Counter(t['quelle'] for t in m['timer']))))
    for t in m["timer"]:
        print(f"     {_uhr(t['zeit'])} {t['champion']} ({t['quelle']})")
    if liste:
        print("Spruenge:")
        for s in sp:
            print(f"     {_uhr(s['zeit'])} {s['cid']:12} {s['team'] or '?':5} {s['weite']:4d} {'Dash ' if s['dash'] else '     '}"
                  f"{'live ' if s['live'] else '     '}{s['grund']}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("aufnahme", nargs="+")
    ap.add_argument("--liste", action="store_true")
    a = ap.parse_args()
    for x in a.aufnahme:
        pfad = Path(x) if Path(x).exists() else aufzeichnung.ORDNER / f"{x}.jsonl.gz"
        bericht(messen(pfad), a.liste)


if __name__ == "__main__":
    main()
