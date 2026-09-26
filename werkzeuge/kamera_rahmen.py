"""Minimap-Pruefung ohne Wahrheit von aussen: das eigene Icon gegen den Kamerarahmen (weisses Rechteck).

Bei gesperrter Kamera steht dein Champion im Rahmen - die Live-API kennt keine Positionen, der Rahmen schon.
Weicht die erkannte Position ab, hat der Verfolger das falsche Icon, oder die Kamera war frei (Schwenk, Tod).
Ein Schwenk zeigt sich als ruhige Folge (Icon laeuft, Rahmen steht), eine Verwechslung als Sprung.
Gemessen 26.09.: 21:21 99,3 %, 19:45 99,7 % im Rahmen; die Ausreisser waren Schwenks zum Mid-Kampf.

    python werkzeuge/kamera_rahmen.py 2026-09-26_212105 Riven
"""
import bisect
import gzip
import json
import statistics
import sys
from pathlib import Path

import cv2
import numpy as np

A = Path(__file__).resolve().parent.parent / "aufnahmen"


def rahmen(img):
    """Kamerarahmen: duenne weisse Linien. (x0, y0, x1, y1) als Kartenanteil oder None."""
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    weiss = ((hsv[..., 1] < 40) & (hsv[..., 2] > 200)).astype(np.uint8) * 255
    waag = cv2.morphologyEx(weiss, cv2.MORPH_OPEN, np.ones((1, max(8, w // 12)), np.uint8))
    senk = cv2.morphologyEx(weiss, cv2.MORPH_OPEN, np.ones((max(6, h // 20), 1), np.uint8))
    ys, xs = np.nonzero(waag)
    ys2, xs2 = np.nonzero(senk)
    if len(xs) < 20 or len(ys2) < 10:
        return None
    x0, x1 = min(xs.min(), xs2.min()), max(xs.max(), xs2.max())
    y0, y1 = min(ys.min(), ys2.min()), max(ys.max(), ys2.max())
    if (x1 - x0) < w * 0.1 or (y1 - y0) < h * 0.05 or (x1 - x0) > w * 0.5:
        return None
    return x0 / w, y0 / h, x1 / w, y1 / h


def main(name, ich):
    sicht = []
    try:
        with gzip.open(A / f"{name}_bilder" / "sichtungen.jsonl.gz", "rt", encoding="utf-8") as f:
            for z in f:
                d = json.loads(z)
                pos = next(((s[2], s[3]) for s in d["s"] if s[0] == ich), None)
                sicht.append((d["w"], pos))
    except EOFError:
        pass
    zeiten = [s[0] for s in sicht]
    ab, weit = [], []
    ohne_rahmen = ohne_icon = 0
    bilder = sorted(p for p in (A / f"{name}_bilder").glob("*.jpg") if p.stem.isdigit())
    for b in bilder:
        w = int(b.stem) / 1000
        i = bisect.bisect_left(zeiten, w)
        nah = [sicht[j] for j in (i - 1, i) if 0 <= j < len(sicht) and abs(sicht[j][0] - w) < 0.1]
        img = cv2.imread(str(b))
        r = rahmen(img)
        if r is None:
            ohne_rahmen += 1
            continue
        pos = next((p for _, p in nah if p), None)
        if pos is None:
            ohne_icon += 1
            continue
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        dx, dy = pos[0] - cx, pos[1] - cy
        ab.append((dx, dy))
        drin = r[0] - 0.02 <= pos[0] <= r[2] + 0.02 and r[1] - 0.02 <= pos[1] <= r[3] + 0.02
        if not drin:
            weit.append((b.name, round(dx, 3), round(dy, 3)))
    if not ab:
        print(name, "nichts")
        return
    print(f"== {name} ({ich}): {len(ab)} Bilder mit Rahmen und Icon, {ohne_rahmen} ohne Rahmen, {ohne_icon} ohne Icon")
    print(f"   Versatz Icon - Rahmenmitte: dx Median {statistics.median(a for a, _ in ab):.3f}, "
          f"dy Median {statistics.median(b for _, b in ab):.3f}")
    print(f"   Icon ausserhalb des Rahmens: {len(weit)} ({len(weit) / len(ab):.1%})")
    for x in weit[:15]:
        print("  ", x)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1], sys.argv[2])
