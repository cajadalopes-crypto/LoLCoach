"""Wie spaet kam jede Ansage live wirklich an? Liest nur `aufnahmen/<Partie>_ansagen.json` (kein Nachspielen).

Carlos, 26.09.: "der groesste Manko ... dass die Ansagen viel zu spaet kommen. Also geisteskrank zu spaet."
Je Ansage stehen dort drei Zeiten (Spielzeit): `zeit` (die Regel hat sie erzeugt), `gesprochen` (der Plan gab sie
an die Stimme), `ton` (der erste Ton klang - seit dem 26.09. abends) und `ganz` (zu Ende oder abgebrochen).
Gesamtverzoegerung = ton - zeit, aufgeteilt in Warten (Plan) und Stimme (Synthese + Schlange).

    python werkzeuge/verzoegerung_live.py                 # neueste Partie
    python werkzeuge/verzoegerung_live.py 2026-09-27_2014 # eine bestimmte
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

AUFNAHMEN = Path(__file__).resolve().parent.parent / "aufnahmen"
NAMEN = {3: "SOFORT", 2: "WICHTIG", 1: "HINWEIS"}


def uhr(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


def quantil(werte: list[float], q: float) -> float:
    w = sorted(werte)
    return w[min(len(w) - 1, int(len(w) * q))]


def auswerten(pfad: Path) -> None:
    ansagen = json.loads(pfad.read_text(encoding="utf-8"))
    mit_ton = [a for a in ansagen if a.get("ton") is not None and a.get("gesprochen") is not None]
    print(f"== {pfad.name}: {len(ansagen)} Ansagen, {len(mit_ton)} mit gemessenem ersten Ton")
    if not mit_ton:
        print("   (keine Ton-Zeiten - Partie vor dem 26.09. abends oder ohne Stimme)")
        return
    for prio in (3, 2, 1):
        gruppe = [a for a in mit_ton if a["prio"] == prio]
        if not gruppe:
            continue
        gesamt = [a["ton"] - a["zeit"] for a in gruppe]
        warten = [a["gesprochen"] - a["zeit"] for a in gruppe]
        stimme = [a["ton"] - a["gesprochen"] for a in gruppe]
        ab = sum(1 for a in gruppe if a.get("ganz") is False)
        print(f"   {NAMEN[prio]:8} {len(gruppe):3}: bis zum Ohr Median {statistics.median(gesamt):.1f} s, "
              f"90 % {quantil(gesamt, 0.9):.1f} s, max {max(gesamt):.1f} s | Warten 90 % {quantil(warten, 0.9):.1f} s, "
              f"Stimme Median {statistics.median(stimme):.2f} s, 90 % {quantil(stimme, 0.9):.2f} s | abgebrochen {ab}")
    spaet = sorted((a for a in mit_ton if a["prio"] >= 2 and a["ton"] - a["zeit"] > 3),
                   key=lambda a: a["ton"] - a["zeit"], reverse=True)
    for a in spaet[:12]:
        print(f"   spaet {uhr(a['zeit'])} +{a['ton'] - a['zeit']:.1f} s (Warten {a['gesprochen'] - a['zeit']:.1f}, "
              f"Stimme {a['ton'] - a['gesprochen']:.1f}) [{a['schluessel']}] {a['text'][:70]}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 1:
        pfade = [p for a in sys.argv[1:] for p in sorted(AUFNAHMEN.glob(f"{a}*_ansagen.json"))]
    else:
        pfade = sorted(AUFNAHMEN.glob("*_ansagen.json"))[-1:]
    for pfad in pfade:
        auswerten(pfad)
