"""Eigene Position aus dem Kamerarahmen (minimap.ich_aus_rahmen) - geprueft genau dort, wo sie gebraucht wird: in
den Luecken, in denen das eigene Icon nicht erkannt wurde (verdeckt im Kampf). Wahrheit: die Position zwischen der
letzten Sichtung davor und der ersten danach (linear), fuer Luecken bis 5 s. Dazu, wie viele Lueckenbilder
ueberhaupt eine Position bekommen.

    python werkzeuge/rahmen_luecken.py 2026-09-26_235433:Riven 2026-09-26_212105:Riven ...
"""
import bisect
import gzip
import json
import statistics
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import minimap  # noqa: E402

A = Path(__file__).resolve().parent.parent / "aufnahmen"
KARTE = 14820.0


def lauf(name: str, ich: str):
    echt = []          # (Wanduhr, x, y) - nur echte Sichtungen (Guete > 0)
    zeilen = []
    try:
        with gzip.open(A / f"{name}_bilder" / "sichtungen.jsonl.gz", "rt", encoding="utf-8") as f:
            for z in f:
                try:
                    d = json.loads(z)
                except json.JSONDecodeError:
                    continue
                zeilen.append(d["w"])
                s = next((s for s in d["s"] if s[0] == ich and (len(s) < 5 or s[4] > 0)), None)
                if s:
                    echt.append((d["w"], s[2], s[3]))
    except EOFError:
        pass
    zeiten = [e[0] for e in echt]
    luecke, getroffen, fehler = 0, 0, []
    for b in sorted(p for p in (A / f"{name}_bilder").glob("*.jpg") if p.stem.isdigit()):
        w = int(b.stem) / 1000
        i = bisect.bisect_left(zeiten, w)
        if i < len(zeiten) and abs(zeiten[i] - w) < 0.15 or i > 0 and abs(zeiten[i - 1] - w) < 0.15:
            continue            # das Icon war zu sehen
        if i == 0 or i >= len(zeiten):
            continue
        vor, nach = echt[i - 1], echt[i]
        if nach[0] - vor[0] > 5.0:
            continue            # lange weg (Tod, Brunnen, Recall) - hier ohne Wahrheit
        luecke += 1
        pos = minimap.ich_aus_rahmen(minimap.kamerarahmen(cv2.imread(str(b))), vor, w)
        if pos is None:
            continue
        getroffen += 1
        a = (w - vor[0]) / (nach[0] - vor[0])
        wx, wy = vor[1] + a * (nach[1] - vor[1]), vor[2] + a * (nach[2] - vor[2])
        fehler.append(((pos[0] - wx) ** 2 + (pos[1] - wy) ** 2) ** 0.5 * KARTE)
    fehler.sort()
    q = (lambda a: f"{fehler[min(len(fehler) - 1, int(len(fehler) * a))]:.0f}") if fehler else (lambda a: "-")
    print(f"{name} {ich}: {luecke} Lueckenbilder (Icon nicht erkannt, Luecke <= 5 s), {getroffen} mit Position aus "
          f"dem Rahmen; Abstand zur Wahrheit Median {q(0.5)}, 90 % {q(0.9)}, max {q(1.0)} Einheiten")
    return fehler


if __name__ == "__main__":
    alle = []
    for arg in sys.argv[1:]:
        n, c = arg.split(":")
        alle += lauf(n, c)
    if alle:
        alle.sort()
        print(f"gesamt {len(alle)}: Median {statistics.median(alle):.0f}, 90 % {alle[int(len(alle) * 0.9)]:.0f}")
