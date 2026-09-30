"""Sparprotokoll (Buch 16, 5): was die Entwicklung seit Auftragsbeginn verbraucht hat - fuer die erste Berichtszeile
"Guthaben: X $ (Abo-Aufrufe: N)".

- Guthaben: alle `*_kosten.json` unter `buecher/` (Nachspiele, Proben), die seit `--seit` entstanden sind. Carlos'
  echte Partien (`aufnahmen/*_kosten.json`) zaehlen nicht - das Guthaben ist fuer sie da.
- Abo-Aufrufe: Zeilen in `daten/abo_aufrufe.jsonl` (lolcoach/llm.py) seit `--seit`, ohne die des Live-Coachs.

    python werkzeuge/guthaben.py --seit 2026-09-30T14:40      (oder --seit-datei buecher/auftraege/028_in_arbeit)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent


def rechnen(seit: float) -> tuple[float, int, list[tuple[str, float]]]:
    dollar, einzeln = 0.0, []
    for f in (WURZEL / "buecher").rglob("*_kosten.json"):
        if f.stat().st_mtime < seit:
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        b = float(d.get("summe_dollar", 0.0) or 0.0)
        if b:
            einzeln.append((str(f.relative_to(WURZEL)), b))
        dollar += b
    abo = 0
    try:
        for z in (WURZEL / "daten" / "abo_aufrufe.jsonl").read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(z)
            except ValueError:
                continue
            abo += e.get("t", 0) >= seit and not e.get("live")
    except OSError:
        pass
    return dollar, abo, einzeln


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    seit = 0.0
    if "--seit" in args:
        seit = datetime.fromisoformat(args[args.index("--seit") + 1]).timestamp()
    elif "--seit-datei" in args:
        seit = (WURZEL / args[args.index("--seit-datei") + 1]).stat().st_mtime
    dollar, abo, einzeln = rechnen(seit)
    print(f"Guthaben: {dollar:.2f} $ (Abo-Aufrufe: {abo})".replace(".", ",", 1))
    for f, b in einzeln:
        print(f"  {f}: {b:.2f} $")


if __name__ == "__main__":
    main()
