"""Abdeckung der 111 Makro-Entscheidungen (Auftrag 032, Abschnitt 4) -> buecher/challenger/abdeckung.md

    python werkzeuge/challenger/abdeckung.py

Vier Haekchen je Entscheidung, alle GEMESSEN (nicht behauptet):
    erkannt    alle Live-Eingaben gibt es heute (lolcoach/makro/wahrnehmung.py); sonst "033" + was fehlt
    gerechnet  jede Rechnung zeigt auf einen Rechner, eine Regel mit Quelle+Datum oder ein Gehirn-Feld (test_register)
    gesagt     die feuernde Testlage ergibt ein Kommando ohne interne Begriffe (test_entscheidungen.sprache)
    getestet   feuert, wenn es soll, und schweigt, wenn es nicht soll (test_entscheidungen.pruefen)
"""
from __future__ import annotations

import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "tests" / "makro"))

import test_entscheidungen as te  # noqa: E402
import test_register as tr  # noqa: E402
from lolcoach.makro import wahrnehmung  # noqa: E402
from lolcoach.makro.entscheidungen import BEREICHE, laden  # noqa: E402


def main() -> dict:
    reg = laden()
    tests = te.pruefen()
    zeilen, summe = [], {"erkannt": 0, "gerechnet": 0, "gesagt": 0, "getestet": 0}
    fehlt_alle: dict[str, list[str]] = {}
    for id_ in sorted(reg, key=lambda i: (list(BEREICHE).index(i[0]), int(i[1:]))):
        e = reg[id_]
        ok_t, meldung, text = tests.get(id_, (False, "kein Test", ""))
        erkannt = not e.fehlt
        gerechnet = all(tr.rechnung_gueltig(r) is None for r in e.rechnung) and bool(e.rechnung)
        gesagt = bool(text) and te.sprache(text) is None
        for k, v in (("erkannt", erkannt), ("gerechnet", gerechnet), ("gesagt", gesagt), ("getestet", ok_t)):
            summe[k] += v
        for f in e.fehlt:
            fehlt_alle.setdefault(f, []).append(id_)
        haken = lambda b: "✔" if b else "✘"
        zeilen.append(f"| {id_} | {e.titel} | {e.grundlage} | {haken(erkannt) if erkannt else '033'} | {haken(gerechnet)} | "
                      f"{haken(gesagt)} | {haken(ok_t)} | {', '.join(e.fehlt) or '–'} | {text or meldung} |")
    n = len(reg)
    z = ["# Abdeckung der 111 Makro-Entscheidungen (Auftrag 032)", "",
         "Erzeugt von `werkzeuge/challenger/abdeckung.py` aus dem Register (`lolcoach/makro/entscheidungen/`) und den "
         "Tests (`tests/makro/`). Die Haekchen sind gemessen, nicht behauptet.", "",
         "| | erkannt | gerechnet | gesagt | getestet |", "|---|---:|---:|---:|---:|",
         f"| **Stand** | {summe['erkannt']}/{n} (+{n - summe['erkannt']} fuer 033) | **{summe['gerechnet']}/{n}** | "
         f"**{summe['gesagt']}/{n}** | **{summe['getestet']}/{n}** |", "",
         f"**Tor 3a** (gerechnet, gesagt, getestet je 111/111): "
         f"**{'ERREICHT' if summe['gerechnet'] == summe['gesagt'] == summe['getestet'] == 111 == n else 'NICHT ERREICHT'}**. "
         "'Erkannt' gilt fuer alle ausser den mit 033 markierten (Wahrnehmung fehlt).", "",
         "## Wahrnehmung fehlt -> Auftrag 033", ""]
    for f, ids in sorted(fehlt_alle.items(), key=lambda kv: -len(kv[1])):
        z.append(f"- **{f}** ({wahrnehmung.EINGABEN[f][0]}): {', '.join(ids)}")
    z += ["", "## Alle 111", "",
          "Spalten: Nr, Entscheidung, Grundlage (Buch 17), erkannt, gerechnet, gesagt, getestet, fehlende Wahrnehmung, "
          "Kommando der feuernden Testlage.", "",
          "| Nr | Entscheidung | Grundl. | erkannt | gerechnet | gesagt | getestet | Wahrnehmung fehlt | Kommando (Testlage) |",
          "|---|---|---|:-:|:-:|:-:|:-:|---|---|"] + zeilen
    (WURZEL / "buecher" / "challenger" / "abdeckung.md").write_text("\n".join(z) + "\n", encoding="utf-8")
    summe["n"] = n
    summe["fehlt"] = fehlt_alle
    return summe


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(main())
