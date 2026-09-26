"""Eichung der Lebensbalken: der eigene Balken im Spielbild gegen die Live-API (currentHealth/maxHealth).

Die API kennt nur DEIN Leben - aber dein Balken hat dieselbe Form wie die der Gegner. Stimmt er, stimmen sie.
Liest alle schirm_*.jpg einer Aufnahme (alle 5 s), sucht die zwei API-Proben um jedes Bild und meldet, wie weit
der gelesene Anteil ausserhalb dieser Spanne liegt (2 % Spielraum). Einige Sekunden, kein Nachspielen.

    python werkzeuge/balken_eichen.py 2026-09-26_212105
"""
import bisect
import statistics
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import aufzeichnung, lebensbalken  # noqa: E402

A = Path(__file__).resolve().parent.parent / "aufnahmen"


def eichen(name: str) -> None:
    proben = []
    for w, d in aufzeichnung.lies_mit_zeit(A / f"{name}.jsonl.gz"):
        st = (d.get("activePlayer") or {}).get("championStats") or {}
        if st.get("maxHealth"):
            proben.append((w, st["currentHealth"] / st["maxHealth"], (d.get("gameData") or {}).get("gameTime", 0)))
    zeiten = [p[0] for p in proben]
    fehler, ohne, feind, mehrere, aus = [], 0, 0, 0, []
    for bild in sorted((A / f"{name}_bilder").glob("schirm_*.jpg")):
        w = int(bild.stem.split("_")[1]) / 1000
        i = bisect.bisect_left(zeiten, w)
        nah = [proben[j] for j in (i - 1, i) if 0 <= j < len(proben)]
        if not nah:
            continue
        b = lebensbalken.finde(cv2.imread(str(bild)))
        ich = [x for x in b if x.team == "ich"]
        feind += sum(1 for x in b if x.team == "feind")
        mehrere += len(ich) > 1
        if not ich:
            ohne += 1
            continue
        lo, hi = min(p[1] for p in nah), max(p[1] for p in nah)
        # mehrere gruene: der naechste an der API zaehlt (Gras, Ringe unter Champions sind auch gruen)
        a = min((x.anteil for x in ich), key=lambda v: min(abs(v - lo), abs(v - hi)))
        e = 0.0 if lo - 0.02 <= a <= hi + 0.02 else min(abs(a - lo), abs(a - hi))
        fehler.append(e)
        t = min(nah, key=lambda p: abs(p[0] - w))[2]
        aus.append((e, f"{int(t) // 60}:{int(t) % 60:02d} gelesen {a:.2f} API {lo:.2f}-{hi:.2f} {bild.name}"))
    print(f"== {name}: {len(fehler)} Bilder mit eigenem Balken, {ohne} ohne, {mehrere} mit mehreren gruenen, "
          f"{feind} Gegner-Balken")
    if fehler:
        print(f"   ausserhalb der API-Spanne: Median {statistics.median(fehler):.3f}, "
              f"90 % {sorted(fehler)[int(len(fehler) * 0.9)]:.3f}, max {max(fehler):.3f}; ueber 5 %: "
              f"{sum(e > 0.05 for e in fehler)}")
    for e, t in sorted(aus, reverse=True)[:6]:
        if e > 0:
            print(f"   {e:.2f} {t}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for n in sys.argv[1:]:
        eichen(n)
