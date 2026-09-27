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


def _uhr(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


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
    for t_bild, bild in aufzeichnung.bilder(pfad):
        i = int(np.argmin(np.abs(wand - t_bild)))
        j = int(np.argmin(np.abs(sw - t_bild))) if len(sw) else None
        if j is None or abs(sw[j] - t_bild) > 0.5 or abs(wand[i] - t_bild) > 3:
            continue
        p = schnappschuesse[i][1]
        zeit = p.zeit + (t_bild - wand[i])
        karte = cv2.imread(str(bild))
        if karte is None:
            continue
        s = sicht[j][1]
        punkte = leser.punkte(karte, [(x[2], x[3]) for x in s])
        if not leser.bereit:
            continue
        z = welle.zustaende(punkte, mein).get(lane)
        puffer.lesen(zeit, z, zeit, mein)
        meins = next((x for x in s if x[0] == ich.champion_id and (x[1] in (None, mein))), None)
        pos = bewertung.einheiten(meins[2], meins[3]) if meins else None
        auf_lane = bool(meins and (pr := welle._projektion(meins[2], meins[3])) and pr[0] == lane and pr[2] < 0.06)
        stehen = bewertung.stehende_tuerme(p)
        lane_phase = zeit < 840 and all((t, lane, "aussen") in stehen for t in ("ORDER", "CHAOS"))
        st = puffer.stand(zeit, lane, mein, pos, stehen)
        aus.append({"zeit": zeit, "bild": str(bild), "lane": lane, "auf_lane": auf_lane, "lane_phase": lane_phase,
                    "kern": st.zustand, "unsere": st.unsere, "ihre": st.ihre,
                    "front": None if st.front is None else round(float(st.front), 2),
                    "trend": None if st.trend is None else round(float(st.trend), 3)})
    return aus, mein


def tafel(pfad: Path, anzahl: int, ziel: str | None) -> Path:
    stamm = pfad.name.removesuffix(".jsonl.gz")
    zeilen, mein = durchrechnen(pfad)
    kand = [z for z in zeilen if z["auf_lane"] and z["lane_phase"]]
    gewaehlt = []
    for z in kand:                                     # hoechstens alle 20 s einer, dann gleichmaessig verteilt
        if not gewaehlt or z["zeit"] - gewaehlt[-1]["zeit"] >= 20:
            gewaehlt.append(z)
    schritt = max(1, len(gewaehlt) // anzahl)
    gewaehlt = gewaehlt[::schritt][:anzahl]
    kacheln = []
    for n, z in enumerate(gewaehlt, 1):
        karte = cv2.imread(z["bild"])
        s = karte.shape[0]
        a, b, c, d = AUSSCHNITT[z["lane"]]
        teil = cv2.resize(karte[int(b * s):int(d * s), int(a * s):int(c * s)], (420, 420), interpolation=cv2.INTER_AREA)
        cv2.putText(teil, str(n), (6, 28), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        kacheln.append(teil)
    ziel = ziel or str(ABLAGE / stamm)
    Path(ziel).parent.mkdir(parents=True, exist_ok=True)
    for t in range(0, len(kacheln), 10):
        reihe = kacheln[t:t + 10]
        while len(reihe) < 10:
            reihe.append(np.zeros_like(kacheln[0]))
        cv2.imwrite(f"{ziel}_{t // 10 + 1}.png", np.vstack([np.hstack(reihe[:5]), np.hstack(reihe[5:])]))
    datei = ABLAGE / f"{stamm}.json"
    ABLAGE.mkdir(parents=True, exist_ok=True)
    alt = json.loads(datei.read_text(encoding="utf-8")) if datei.exists() else {}
    wahr = {e["zeit"]: e.get("wahr") for e in alt.get("punkte", [])}
    datei.write_text(json.dumps({"aufnahme": stamm, "mein_team": mein, "welle_py": "Icon+Ring ausgeblendet, relativ",
                                 "punkte": [{"nr": n, "zeit": _uhr(z["zeit"]), "kern": z["kern"],
                                             "unsere": z["unsere"], "ihre": z["ihre"], "front": z["front"],
                                             "trend": z["trend"], "wahr": wahr.get(_uhr(z["zeit"]))}
                                            for n, z in enumerate(gewaehlt, 1)]},
                                ensure_ascii=False, indent=1), encoding="utf-8")
    for n, z in enumerate(gewaehlt, 1):
        print(f"{n:2d} {_uhr(z['zeit'])} Kern {z['kern']:17} {z['unsere']}:{z['ihre']} Front {z['front']} Trend {z['trend']}")
    print(f"Tafel: {ziel}_1.png ...  Beschriftung: {datei}")
    return datei


def auswerten(pfad: Path) -> None:
    stamm = pfad.name.removesuffix(".jsonl.gz")
    d = json.loads((ABLAGE / f"{stamm}.json").read_text(encoding="utf-8"))
    klar = [e for e in d["punkte"] if e.get("wahr") and e["wahr"] != "unklar"]
    treffer = sum(e["kern"] == e["wahr"] for e in klar)
    print(f"{stamm}: {len(klar)} von {len(d['punkte'])} eindeutig beschriftet, {treffer} richtig"
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
    a = ap.parse_args()
    pfad = Path(a.aufnahme) if Path(a.aufnahme).exists() else aufzeichnung.ORDNER / f"{a.aufnahme}.jsonl.gz"
    if a.auswerten:
        auswerten(pfad)
    else:
        tafel(pfad, a.anzahl, a.tafel)


if __name__ == "__main__":
    main()
