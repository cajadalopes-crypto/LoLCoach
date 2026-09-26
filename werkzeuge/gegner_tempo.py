"""Ist die Ankunftszeit (bewertung: Luftlinie x WEGFAKTOR / Lauftempo) eine sichere Untergrenze? Je Gegner und Paar
von Sichtungen 3-20 s auseinander (kein Tod dazwischen): Luftlinie / Zeit gegen das Modelltempo tempo(s)/WEGFAKTOR.
Verhaeltnis > 1 = der Gegner war schneller, als der Coach rechnet (gefaehrliche Richtung).

Gemessen 27.09. (5 Partien, ohne Doppel-Champions, 1647 Strecken) gegen Luftlinie x 1,15 / Tempo: Median 1,01,
90 % 1,28 - daraus bewertung.GEGNER_TEMPO_RESERVE = 1,1 (Luftlinie / (Tempo x 1,1) deckt 90 % ab).

    python werkzeuge/gegner_tempo.py 2026-09-26_212105 2026-09-26_194524 ...
"""
from pathlib import Path
import bisect
import gzip
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
from lolcoach import aufzeichnung, bewertung, zustand  # noqa: E402

A = Path(__file__).resolve().parent.parent / "aufnahmen"
alle = []
for name in sys.argv[1:]:
    paare, stand = [], []
    for w, d in aufzeichnung.lies_mit_zeit(A / f"{name}.jsonl.gz"):
        p = zustand.partie(d, None)
        if p.ich:
            paare.append((w, p.zeit))
            stand.append(p)
    ws = [x[0] for x in paare]

    def bei(w):
        i = min(len(paare) - 1, bisect.bisect_left(ws, w))
        return stand[i]
    p_end = stand[-1]
    gegner = {s.champion_id: s.name for s in p_end.gegner()}
    tode = {}
    for e in p_end.ereignisse:
        if e.art == "ChampionKill" and e.opfer is not None:
            tode.setdefault(e.opfer.name, []).append(e.zeit)
    spur = {c: [] for c in gegner}
    with gzip.open(A / f"{name}_bilder" / "sichtungen.jsonl.gz", "rt", encoding="utf-8") as f:
        try:
            for z in f:
                try:
                    d = json.loads(z)
                except ValueError:
                    continue
                for s in d["s"]:
                    if s[0] in spur and (len(s) < 5 or s[4] > 0):
                        spur[s[0]].append((d["w"], s[2] * 14820, (1 - s[3]) * 14881))
        except (EOFError, OSError):
            pass
    for c, pts in spur.items():
        pts.sort()
        # je Sichtung die naechste 3-20 s spaeter (nur jede Sekunde eine Stichprobe)
        tws = [x[0] for x in pts]
        letzte = -1e9
        for w0, x0, y0 in pts:
            if w0 - letzte < 1.0:
                continue
            letzte = w0
            j = bisect.bisect_left(tws, w0 + 3)
            if j >= len(pts) or pts[j][0] - w0 > 20:
                continue
            w1, x1, y1 = pts[j]
            p0 = bei(w0)
            t0, t1 = p0.zeit, bei(w1).zeit
            if any(t0 - 1 <= tz <= t1 + 1 for tz in tode.get(gegner[c], [])):
                continue
            s = next((q for q in p0.gegner() if q.champion_id == c), None)
            if s is None or s.tot:
                continue
            weg = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
            if weg < 800:                     # steht / kaempft: sagt nichts ueber das Tempo
                continue
            v = weg / (w1 - w0)
            modell = bewertung.tempo(s) / bewertung.WEGFAKTOR
            alle.append((v / modell, name, c, round(t0), round(v), round(modell)))
r = sorted(a[0] for a in alle)
print(f"{len(r)} Strecken; Verhaeltnis echt/Modell: Median {statistics.median(r):.2f}, 90 % {r[int(len(r) * 0.9)]:.2f}, "
      f"99 % {r[int(len(r) * 0.99)]:.2f}, max {r[-1]:.2f}; ueber 1,0: {sum(x > 1.0 for x in r)} "
      f"({sum(x > 1.0 for x in r) / max(1, len(r)):.1%}), ueber 1,2: {sum(x > 1.2 for x in r)}")
for a in sorted(alle, reverse=True)[:10]:
    print(f"   {a[0]:.2f}  {a[1]} {a[2]} bei {a[3] // 60}:{a[3] % 60:02d}  {a[4]} statt {a[5]} Einheiten/s")

# ohne Doppel-Champions (Bot-Partien: zwei Ashes tauschen die Identitaet)
doppelt = {("2026-09-26_164809", "Ashe"), ("2026-09-26_194524", "Vayne")}
r2 = sorted(a[0] for a in alle if (a[1], a[2]) not in doppelt)
print(f"ohne Doppelte: {len(r2)} Strecken; Median {statistics.median(r2):.2f}, 75 % {r2[int(len(r2) * 0.75)]:.2f}, "
      f"90 % {r2[int(len(r2) * 0.9)]:.2f}, 95 % {r2[int(len(r2) * 0.95)]:.2f}; ueber 1,0: {sum(x > 1.0 for x in r2) / len(r2):.0%}, "
      f"ueber 1,15: {sum(x > 1.15 for x in r2) / len(r2):.0%}, ueber 1,3: {sum(x > 1.3 for x in r2) / len(r2):.0%}")
