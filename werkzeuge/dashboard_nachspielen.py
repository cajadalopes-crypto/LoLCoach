"""Dashboard im Nachspielen: eine Aufnahme bis zu einer Spielzeit durchlaufen und das Dashboard mit genau diesem
Stand ausliefern - auf einem eigenen Port, neben einem laufenden Coach (der hat 8790).

Wozu (Qualitaetsrunde 1, F2.4): "Das Dashboard zeigt jeden erkannten Flash mit Restzeit" pruefen, ohne live zu
spielen. Dazu mit Brainstone/werkzeuge/browserprobe.py ein Bild machen:

    python werkzeuge/dashboard_nachspielen.py <aufnahme> --bis 2:30 [--port 8799] [--halten 40]
    python ../Brainstone/werkzeuge/browserprobe.py http://127.0.0.1:8799/ flash 3
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import aufzeichnung, dashboard, lage, zustand  # noqa: E402


def _sekunden(uhr: str) -> float:
    m, s = uhr.split(":")
    return int(m) * 60 + float(s)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("aufnahme")
    ap.add_argument("--bis", required=True, help="Spielzeit m:ss")
    ap.add_argument("--port", type=int, default=8799)
    ap.add_argument("--halten", type=float, default=40.0, help="so viele Sekunden ausliefern, dann Ende")
    a = ap.parse_args()
    if a.port == dashboard.PORT:
        sys.exit(f"Port {dashboard.PORT} gehoert dem Coach")
    pfad = Path(a.aufnahme) if Path(a.aufnahme).exists() else aufzeichnung.ORDNER / f"{a.aufnahme}.jsonl.gz"
    bis = _sekunden(a.bis)
    sicht, lb = lage.sicht_fuer(pfad), lage.Lagebild()
    letzte = None
    for w, d in aufzeichnung.lies_mit_zeit(pfad):
        p = zustand.partie(d)
        if not p.ich:
            continue
        if p.zeit > bis:
            break
        if sicht:
            for wb, s in sicht.zwischen(w, lage.champions(p)):
                lb.neu(p.zeit - (w - wb), s, p)
            lb.ereignisse(lambda wb, p=p, w=w: p.zeit - (w - wb), sicht.ereignisse(), p)
        letzte = p
    if letzte is None:
        sys.exit("keine Daten bis zu dieser Zeit")
    db = dashboard.Dashboard(a.port)
    db.aktualisiere(letzte, lb)
    z = dashboard.zustand_json(letzte, lb)
    weg = [(s["name"], x["name"], x["rest"]) for s in z["spieler"] for x in s.get("zauber_weg", [])]
    print(f"{db.url} - Stand {int(letzte.zeit // 60)}:{int(letzte.zeit % 60):02d}, Zauber weg: {weg}", flush=True)
    time.sleep(a.halten)


if __name__ == "__main__":
    main()
