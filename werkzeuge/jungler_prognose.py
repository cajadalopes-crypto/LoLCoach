"""Stimmt 'der Jungler bleibt auf seiner Seite' (jungle.Jungletracker.wahrscheinlich)? Je Luecke zwischen zwei
Sichtungen des gegnerischen Junglers: Seite davor, Seite danach, Dauer. Dazu die Trefferquote der Prognose.

Gemessen 27.09. an 5 Partien, 60 Luecken: bis 60 s taucht er zu 79-80 % auf derselben Seite wieder auf, danach
Muenzwurf (43-50 %). Prognose zur Luecken-Mitte 44/60 richtig, Brier 0,183 (Raten 0,250) - gut kalibriert.

    python werkzeuge/jungler_prognose.py 2026-09-26_212105 2026-09-26_194524 ...
"""
from pathlib import Path
import bisect
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
from lolcoach import aufzeichnung, jungle, zustand  # noqa: E402

A = Path(__file__).resolve().parent.parent / "aufnahmen"
eimer = defaultdict(lambda: [0, 0])      # dt-Klasse -> [gleiche Seite, andere Seite]
prognose = [0, 0, 0.0]                   # [treffer, gesamt, brier-summe]
for name in sys.argv[1:]:
    paare, jn, tot_zeiten = [], None, []
    letzte = None
    for w, d in aufzeichnung.lies_mit_zeit(A / f"{name}.jsonl.gz"):
        paare.append((w, (d.get("gameData") or {}).get("gameTime", 0)))
        letzte = d
    p = zustand.partie(letzte, None)
    j = p.jungler(zustand.gegenteam(p.mein_team))
    if j is None:
        continue
    for e in p.ereignisse:
        if e.art == "ChampionKill" and e.opfer is not None and e.opfer.name == j.name:
            tot_zeiten.append(e.zeit)
    ws = [x[0] for x in paare]
    st = lambda w: paare[min(len(paare) - 1, bisect.bisect_left(ws, w))][1]    # noqa: E731
    sicht = []
    with gzip.open(A / f"{name}_bilder" / "sichtungen.jsonl.gz", "rt", encoding="utf-8") as f:
        try:
            for z in f:
                try:
                    d = json.loads(z)
                except ValueError:
                    continue
                for s in d["s"]:
                    if s[0] == j.champion_id and (len(s) < 5 or s[4] > 0):
                        sicht.append((st(d["w"]), s[2], s[3]))
        except (EOFError, OSError):
            pass
    sicht.sort()
    for (t0, x0, y0), (t1, x1, y1) in zip(sicht, sicht[1:]):
        dt = t1 - t0
        if dt < 15 or t0 < 90 or any(t0 <= tz <= t1 for tz in tot_zeiten):
            continue                            # Tod dazwischen: Brunnen, zaehlt nicht
        s0, s1 = jungle.seite(x0, y0), jungle.seite(x1, y1)
        k = "15-30" if dt < 30 else "30-60" if dt < 60 else "60-90" if dt < 90 else "90+"
        eimer[k][0 if s0 == s1 else 1] += 1
        # Prognose zur Mitte der Luecke
        tr = jungle.Jungletracker(sichtungen=[(t0, x0, y0)])
        w = tr.wahrscheinlich(t0 + dt / 2)
        tipp = max(w, key=w.get)
        prognose[0] += tipp == s1
        prognose[1] += 1
        prognose[2] += (1 - w.get(s1, 0.5)) ** 2
for k in ("15-30", "30-60", "60-90", "90+"):
    g, a = eimer[k]
    print(f"Luecke {k} s: gleiche Seite {g}, andere Seite {a}  ({g / max(1, g + a):.0%} gleich)")
print(f"Prognose zur Luecken-Mitte: {prognose[0]}/{prognose[1]} richtig, Brier {prognose[2] / max(1, prognose[1]):.3f} "
      f"(50/50 waere 0,250)")
