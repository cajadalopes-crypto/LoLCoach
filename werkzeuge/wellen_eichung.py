"""Wellen-Eichung (Buch 1, 1.4): stimmt der Wellenzustand des Kerns mit dem, was auf der Minimap zu sehen ist?

Rechnet die Welle deiner Lane aus den behaltenen Minimap-Ausschnitten einer Aufnahme NEU - mit dem aktuellen
welle.py (Icons samt Ring ausgeblendet, Farben relativ) und dem WellenPuffer des Kerns -, waehlt Zeitpunkte der
Lane-Phase, an denen du auf deiner Lane stehst, und legt eine Bildtafel an (Ausschnitt deiner Lane, vergroessert)
samt einer Beschriftungsdatei `buecher/wellen_eichung/<stamm>.json` ("wahr" von Hand eintragen: ein Zustand aus
Buch 1 1.4 oder "unklar"). Mit `--auswerten` die Trefferquote (Abnahme: >= 80 %, GECRASHT_BEI_IHM >= 90 %).

    python werkzeuge/wellen_eichung.py <aufnahme> [--anzahl 20] [--tafel <datei-ohne-endung>]
    python werkzeuge/wellen_eichung.py <aufnahme> --auswerten
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cv2  # noqa: E402
import numpy as np  # noqa: E402

from lolcoach import aufzeichnung, bewertung, welle, zustand  # noqa: E402
from lolcoach.kern import konfig  # noqa: E402
from lolcoach.kern.merkmale import WellenPuffer  # noqa: E402

WURZEL = Path(__file__).resolve().parent.parent
ABLAGE = WURZEL / "buecher" / "wellen_eichung"
AUSSCHNITT = {"Top": (0.0, 0.0, 0.62, 0.62), "Mid": (0.15, 0.15, 0.85, 0.85), "Bot": (0.38, 0.38, 1.0, 1.0)}
RECALL_S = 9.0      # Recall kanalisiert 8 s: taucht dein Icon so bald im Brunnen auf, ohne dass du stirbst, recallst du


def _im_brunnen(pos, mein: str) -> bool:
    if pos is None:
        return False
    x, y = pos
    return (x < 0.12 and y > 0.88) if mein == "ORDER" else (x > 0.88 and y < 0.12)


def _recall_markieren(aus: list[dict], mein: str) -> None:
    """F1.5 (Qualitaetsrunde 1): kein Zeitpunkt, an dem du recallst (Leuchtring ueber der Lane, 144655 4:56, 133930
    6:07) - erkannt daran, dass dein Icon binnen RECALL_S im Brunnen auftaucht, ohne dass du dazwischen stirbst."""
    for i, z in enumerate(aus):
        z["recall"] = False
        if z["tot"] or _im_brunnen(z["pos_karte"], mein):
            continue
        for w in aus[i + 1:]:
            if w["zeit"] - z["zeit"] > RECALL_S or w["tot"]:
                break
            if _im_brunnen(w["pos_karte"], mein):
                z["recall"] = True
                break


def _uhr(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


def _live_punkte(ordner: Path) -> list[tuple[float, list]]:
    """Die live erkannten Vasallen-Punkte (ereignisse.jsonl.gz, art "wellen") - fuer Aufnahmen, deren Bilder schon
    aufgeraeumt sind (lage.bilder_aufraeumen: nur die letzten drei Partien; 133930 verlor sie am 27.09. um 17:26).
    Erkannt mit dem Leser von DAMALS (ohne spaetere Verbesserungen am Bild), gezaehlt mit dem Kern von heute."""
    aus = []
    try:
        with gzip.open(ordner / "ereignisse.jsonl.gz", "rt", encoding="utf-8") as f:
            for z in f:
                try:
                    d = json.loads(z)
                except ValueError:
                    break
                if d.get("art") == "wellen":
                    aus.append((d["w"], [tuple(q) for q in d["p"]]))
    except (OSError, EOFError):
        pass
    return aus


def durchrechnen(pfad: Path) -> tuple[list[dict], str]:
    """Je Minimap-Ausschnitt: Spielzeit, Bild, deine Lane, ob du dort stehst, Lane-Phase, Wellenstand des Kerns."""
    schnappschuesse = []
    for w, d in aufzeichnung.lies_mit_zeit(pfad):
        p = zustand.partie(d)
        if p.ich:
            schnappschuesse.append((w, p))
    if not schnappschuesse:
        return [], ""
    wand = np.array([w for w, _ in schnappschuesse])
    ich = schnappschuesse[-1][1].ich
    mein = schnappschuesse[-1][1].mein_team
    lane = bewertung.LANE_DER_ROLLE.get(ich.rolle, "Top")
    ordner = pfad.with_name(pfad.name.removesuffix(".jsonl.gz") + "_bilder")
    sicht = []
    with gzip.open(ordner / "sichtungen.jsonl.gz", "rt", encoding="utf-8") as f:
        try:
            for z in f:
                try:
                    d = json.loads(z)
                except ValueError:
                    break
                sicht.append((d["w"], d["s"]))
        except EOFError:
            pass
    sw = np.array([w for w, _ in sicht])
    leser, puffer = welle.Wellenleser(), WellenPuffer(konfig())
    aus = []
    bilder = aufzeichnung.bilder(pfad)
    quelle = [(t, b, None) for t, b in bilder] or [(t, None, q) for t, q in _live_punkte(ordner)]
    for t_bild, bild, live in quelle:
        i = int(np.argmin(np.abs(wand - t_bild)))
        j = int(np.argmin(np.abs(sw - t_bild))) if len(sw) else None
        if j is None or abs(sw[j] - t_bild) > 0.5 or abs(wand[i] - t_bild) > 3:
            continue
        p = schnappschuesse[i][1]
        zeit = p.zeit + (t_bild - wand[i])
        s = sicht[j][1]
        if live is not None:
            punkte = live
        else:
            karte = cv2.imread(str(bild))
            if karte is None:
                continue
            punkte = leser.punkte(karte, [(x[2], x[3]) for x in s])
            if not leser.bereit:
                continue
        z = welle.zustaende(punkte, mein).get(lane)
        # Punkte deiner Lane aus deiner Sicht (Farben relativ: blau = wir), fuer die Fehlersuche
        lp = sorted((("wir" if f == "blau" else "die"), round(pr[1] if mein == "ORDER" else 1 - pr[1], 3))
                    for f, x, y in punkte if (pr := welle._projektion(x, y)) and pr[0] == lane)
        puffer.lesen(zeit, z, zeit, mein)
        meins = next((x for x in s if x[0] == ich.champion_id and (x[1] in (None, mein))), None)
        pos = bewertung.einheiten(meins[2], meins[3]) if meins else None
        auf_lane = bool(meins and (pr := welle._projektion(meins[2], meins[3])) and pr[0] == lane and pr[2] < 0.06)
        stehen = bewertung.stehende_tuerme(p)
        lane_phase = zeit < 840 and all((t, lane, "aussen") in stehen for t in ("ORDER", "CHAOS"))
        st = puffer.stand(zeit, lane, mein, pos, stehen)
        aus.append({"zeit": zeit, "bild": None if bild is None else str(bild), "lane": lane, "auf_lane": auf_lane, "lane_phase": lane_phase,
                    "tot": bool(p.ich.tot), "lane_punkte": lp, "dein": round(float(st.turm_dein), 3),
                    "ihr": round(float(st.turm_ihr), 3), "pos_karte": (meins[2], meins[3]) if meins else None,
                    "naechste": None if st.naechste_dein is None else round(float(st.naechste_dein), 2),
                    "kern": st.zustand, "unsere": st.unsere, "ihre": st.ihre,
                    "front": None if st.front is None else round(float(st.front), 2),
                    "trend": None if st.trend is None else round(float(st.trend), 3)})
    _recall_markieren(aus, mein)
    return aus, mein


def spielmodus(pfad: Path) -> str:
    """gameData.gameMode der Aufnahme - die Eichung weist die Modi getrennt aus (Qualitaetsrunde 2, G6)."""
    for _, d in aufzeichnung.lies_mit_zeit(pfad):
        if (m := zustand.partie(d).modus) not in (None, "", "?"):
            return m
    return "?"


def tafel(pfad: Path, anzahl: int, ziel: str | None, mit: tuple = ()) -> Path:
    stamm = pfad.name.removesuffix(".jsonl.gz")
    zeilen, mein = durchrechnen(pfad)
    kand = [z for z in zeilen if z["auf_lane"] and z["lane_phase"] and not z["tot"] and not z["recall"]]
    gewaehlt = []
    for z in kand:                                     # hoechstens alle 20 s einer, dann gleichmaessig verteilt
        if not gewaehlt or z["zeit"] - gewaehlt[-1]["zeit"] >= 20:
            gewaehlt.append(z)
    schritt = max(1, len(gewaehlt) // anzahl)
    gewaehlt = gewaehlt[::schritt][:anzahl]
    # feste Zeitpunkte (Abnahme F1: 144655 3:13, 5:17, 5:38) kommen dazu, wenn sie gueltig sind
    da = {_uhr(z["zeit"]) for z in gewaehlt}
    gewaehlt += [z for z in kand if _uhr(z["zeit"]) in mit and _uhr(z["zeit"]) not in da
                 and not da.add(_uhr(z["zeit"]))]
    gewaehlt.sort(key=lambda z: z["zeit"])
    kacheln = []
    for n, z in enumerate(gewaehlt, 1):
        if z["bild"] is None:                       # nur live erkannte Punkte, kein Bild mehr
            continue
        karte = cv2.imread(z["bild"])
        s = karte.shape[0]
        a, b, c, d = AUSSCHNITT[z["lane"]]
        teil = cv2.resize(karte[int(b * s):int(d * s), int(a * s):int(c * s)], (420, 420), interpolation=cv2.INTER_AREA)
        cv2.putText(teil, str(n), (6, 28), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        kacheln.append(teil)
    ziel = ziel or str(ABLAGE / stamm)
    Path(ziel).parent.mkdir(parents=True, exist_ok=True)
    for t in range(0, len(kacheln) if kacheln else 0, 10):
        reihe = kacheln[t:t + 10]
        while len(reihe) < 10:
            reihe.append(np.zeros_like(kacheln[0]))
        cv2.imwrite(f"{ziel}_{t // 10 + 1}.png", np.vstack([np.hstack(reihe[:5]), np.hstack(reihe[5:])]))
    datei = ABLAGE / f"{stamm}.json"
    ABLAGE.mkdir(parents=True, exist_ok=True)
    alt = json.loads(datei.read_text(encoding="utf-8")) if datei.exists() else {}
    wahr = {e["zeit"]: e.get("wahr") for e in alt.get("punkte", [])}
    notiz = {e["zeit"]: e.get("notiz") for e in alt.get("punkte", [])}
    datei.write_text(json.dumps({"aufnahme": stamm, "mein_team": mein, "spielmodus": spielmodus(pfad),
                                 "welle_py": "Icon+Ring ausgeblendet, relativ, Front statt Summe (F1)",
                                 "punkte": [{"nr": n, "zeit": _uhr(z["zeit"]), "kern": z["kern"],
                                             "unsere": z["unsere"], "ihre": z["ihre"], "front": z["front"],
                                             "trend": z["trend"], "naechste": z["naechste"],
                                             "wahr": wahr.get(_uhr(z["zeit"])), "notiz": notiz.get(_uhr(z["zeit"]))}
                                            for n, z in enumerate(gewaehlt, 1)]},
                                ensure_ascii=False, indent=1), encoding="utf-8")
    for n, z in enumerate(gewaehlt, 1):
        print(f"{n:2d} {_uhr(z['zeit'])} Kern {z['kern']:17} {z['unsere']}:{z['ihre']} Front {z['front']} "
              f"Trend {z['trend']} naechste {z['naechste']}")
    print(f"Tafel: {ziel}_1.png ...  Beschriftung: {datei}")
    return datei


def auswerten(pfad: Path) -> None:
    stamm = pfad.name.removesuffix(".jsonl.gz")
    d = json.loads((ABLAGE / f"{stamm}.json").read_text(encoding="utf-8"))
    klar = [e for e in d["punkte"] if e.get("wahr") and e["wahr"] != "unklar"]
    treffer = sum(e["kern"] == e["wahr"] for e in klar)
    print(f"{stamm} [{d.get('spielmodus', '?')}]: {len(klar)} von {len(d['punkte'])} eindeutig beschriftet, {treffer} richtig"
          + (f" ({100 * treffer / len(klar):.0f} %; Abnahme >= 80 %)" if klar else ""))
    gib = [e for e in klar if e["wahr"] == "GECRASHT_BEI_IHM" or e["kern"] == "GECRASHT_BEI_IHM"]
    if gib:
        print(f"GECRASHT_BEI_IHM (wahr oder Kern): {sum(e['kern'] == e['wahr'] for e in gib)} / {len(gib)} (>= 90 %)")
    for e in klar:
        if e["kern"] != e["wahr"]:
            print(f"   {e['nr']:2d} {e['zeit']}: Kern {e['kern']}, wahr {e['wahr']}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("aufnahme")
    ap.add_argument("--anzahl", type=int, default=20)
    ap.add_argument("--tafel", help="Bildtafel an diesen Ort (ohne Endung)")
    ap.add_argument("--auswerten", action="store_true")
    ap.add_argument("--mit", default="", help="feste Zeitpunkte, z. B. 3:13,5:17")
    a = ap.parse_args()
    pfad = Path(a.aufnahme) if Path(a.aufnahme).exists() else aufzeichnung.ORDNER / f"{a.aufnahme}.jsonl.gz"
    if a.auswerten:
        auswerten(pfad)
    else:
        tafel(pfad, a.anzahl, a.tafel, tuple(x for x in a.mit.split(",") if x))


if __name__ == "__main__":
    main()
