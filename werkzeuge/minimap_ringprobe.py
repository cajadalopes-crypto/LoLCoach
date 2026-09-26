"""Minimap-Pruefung ohne Wahrheit von aussen: jede live erkannte Sichtung gegen die Ringfarbe im Minimap-Bild.

Eigenes Team blau, Gegner rot (egal welche Seite). Falsche Ringfarbe = Verdacht auf Fehlerkennung. Unter einem Icon
mitgefuehrte (erschlossene) Stellen zaehlen nicht, sobald die Aufnahme die Guete mitschreibt (ab 27.09.).
Gemessen 27.09. (Einzel-Champions): 21:21 0,17 %, 19:45 0,43 %; aeltere Partien ~3 % - dort v. a. erschlossene
Stellen und ueberlappende Ringe, keine Verwechslungen (Sichtprobe).

    python werkzeuge/minimap_ringprobe.py 2026-09-26_212105
"""
import bisect
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
from lolcoach import aufzeichnung, minimap, zustand  # noqa: E402

A = Path(__file__).resolve().parent.parent / "aufnahmen"
for name in sys.argv[1:]:
    team_von, mein, doppelt = {}, None, set()
    for d in aufzeichnung.lies(A / f"{name}.jsonl.gz"):
        p = zustand.partie(d, None)
        if p.spieler and p.ich:
            team_von = {s.champion_id: s.team for s in p.spieler}
            ids = [s.champion_id for s in p.spieler]
            doppelt = {c for c in ids if ids.count(c) > 1}
            mein = p.mein_team
    sicht = []
    try:
        with gzip.open(A / f"{name}_bilder" / "sichtungen.jsonl.gz", "rt", encoding="utf-8") as f:
            for z in f:
                try:
                    d = json.loads(z)
                except ValueError:
                    continue
                sicht.append((d["w"], d["s"]))
    except (EOFError, OSError):
        pass
    zeiten = [s[0] for s in sicht]
    bilder = sorted(p for p in (A / f"{name}_bilder").glob("*.jpg") if p.stem.isdigit())
    zaehler, verdacht = Counter(), []
    radius = round(minimap.PORTRAET * 2160 / 2) + 2
    for b in bilder:
        w = int(b.stem) / 1000
        i = bisect.bisect_left(zeiten, w)
        nah = [sicht[j] for j in (i - 1, i) if 0 <= j < len(sicht) and abs(sicht[j][0] - w) < 0.04]
        if not nah:
            continue
        img = cv2.imread(str(b))
        seite = img.shape[0]
        for cid, t_sicht, x, y, *guete in nah[0][1]:
            if guete and guete[0] <= 0:
                continue          # erschlossen (unter einem Icon mitgefuehrt), nicht gesehen
            team = t_sicht if cid in doppelt else team_von.get(cid)
            if team is None:
                continue
            farbe = minimap._ringfarbe(img, round(x * seite), round(y * seite), radius)
            soll = "ORDER" if team == mein else "CHAOS"     # Minimap: eigenes Team blau, Gegner rot - egal welche Seite
            if farbe is None:
                zaehler["unklar"] += 1
            elif farbe == soll:
                zaehler["passt"] += 1
            else:
                zaehler["falsch"] += 1
                zaehler["falsch_doppelt" if cid in doppelt else "falsch_einzeln"] += 1
                if cid not in doppelt:
                    verdacht.append((b.name, cid, round(x, 3), round(y, 3)))
    n = sum(zaehler.values())
    print(f"== {name} (du: {mein}): {n} Sichtungen in Bildern; passt {zaehler['passt']}, unklar {zaehler['unklar']}, "
          f"FALSCHE Ringfarbe {zaehler['falsch']} ({zaehler['falsch'] / max(1, n):.2%})")
    print(f"   davon Doppel-Champions {zaehler['falsch_doppelt']}, einzelne {zaehler['falsch_einzeln']} "
          f"({zaehler['falsch_einzeln'] / max(1, n):.2%}); Doppelte: {sorted(doppelt)}")
    for v in verdacht[:8]:
        print("   ", v)
