"""Auswertung des Makro-Protokolls (Auftrag 034, fuer den Messlauf in Stufe 5): <stamm>_makro.jsonl einer Partie
(live mit --kern makro geschrieben) - Laufzeit je Entscheidung, Formen, Gruende der Planwechsel, Sperre, fehlende
Wahrnehmung, was gesagt wurde und woher der Satz kam (Claude oder Vorlage).

    python werkzeuge/makro_protokoll.py aufnahmen/<stamm>_makro.jsonl [...]
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def lesen(pfad: Path) -> tuple[list[dict], list[dict]]:
    entscheidungen, ansagen = [], []
    for z in pfad.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(z)
        except ValueError:
            continue
        (ansagen if "ansage" in d else entscheidungen).append(d)
    return entscheidungen, ansagen


def _q(werte: list[float], q: float) -> float:
    w = sorted(werte)
    return w[min(len(w) - 1, int(len(w) * q))] if w else 0.0


def auswerten(pfad: Path) -> dict:
    e, a = lesen(pfad)
    ms = [x["ms"] for x in e if "ms" in x]
    hirn = [x.get("ms_hirn", 0.0) for x in e]
    return {
        "datei": pfad.name, "entscheidungen": len(e), "ansagen": len(a),
        "ms": {"median": _q(ms, 0.5), "p95": _q(ms, 0.95), "max": max(ms, default=0.0),
               "ueber_50": sum(m > 50 for m in ms)},
        "ms_hirn_median": _q(hirn, 0.5),
        "form": Counter(x["form"] for x in e), "grund": Counter(x["grund"] for x in e),
        "klarheit": Counter(x.get("klarheit") for x in e),
        "kommandos": Counter(x["id"] for x in a),
        "quelle": Counter(x["quelle"].split(" ", 1)[0] for x in a),
        "kategorie": Counter(x["kategorie"] for x in a),
        "gesperrt": Counter(g[0] for x in e for g in x.get("gesperrt", [])),
        "fehlt": Counter(f for x in e for f in x.get("fehlt", [])),
        "fehler": sum(1 for x in e if x.get("fehler")),
    }


def drucken(r: dict) -> None:
    n = max(1, r["entscheidungen"])
    print(f"== {r['datei']}: {r['entscheidungen']} Entscheidungen, {r['ansagen']} Ansagen")
    m = r["ms"]
    print(f"   Laufzeit je Entscheidung: Median {m['median']:.2f} ms, p95 {m['p95']:.2f} ms, max {m['max']:.2f} ms, "
          f"{m['ueber_50']} ueber 50 ms (Gehirn allein: Median {r['ms_hirn_median']:.2f} ms)")
    for k in ("form", "grund", "klarheit", "kategorie", "quelle", "kommandos", "gesperrt"):
        print(f"   {k}: " + ", ".join(f"{a} {b}" for a, b in r[k].most_common(12)))
    print("   fehlende Wahrnehmung (Anteil der Takte): "
          + ", ".join(f"{a} {100 * b / n:.0f} %" for a, b in r["fehlt"].most_common(12)))
    if r["fehler"]:
        print(f"   !! {r['fehler']} Entscheidungen mit Fehler in einer Entscheidung (Protokoll: 'fehler')")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for arg in sys.argv[1:]:
        drucken(auswerten(Path(arg)))
