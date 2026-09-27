"""Turmschaden (rechnung.turm_schaden, Wiki-Werte) gegen die Wahrheit: der eigene Lebenseinbruch (API currentHealth)
unter einem gegnerischen Turm, wenn kein Gegner-Champion in der Naehe ist. Der erste Treffer einer Folge (davor
>= 5 s kein Treffer, also nicht aufgewaermt) wird mit dem gerechneten Schuss verglichen - roh und nach Ruestung.

    python werkzeuge/turm_schaden.py 2026-09-26_194524 2026-09-26_212105 ...
"""
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
from lolcoach import aufzeichnung, bewertung, lage, rechnung, zustand  # noqa: E402

A = Path(__file__).resolve().parent.parent / "aufnahmen"


def lauf(name):
    pfad = A / f"{name}.jsonl.gz"
    sicht = lage.sicht_fuer(pfad)
    lb = lage.Lagebild()
    vorher = None
    letzter_treffer = -1e9
    aus = []
    for w, d in aufzeichnung.lies_mit_zeit(pfad):
        p = zustand.partie(d, None)
        if p is None or not p.ich:
            continue
        for wb, s in sicht.zwischen(w, lage.champions(p)):
            lb.neu(p.zeit - (w - wb), s, p)
        leben = p.werte.get("currentHealth")
        if vorher is not None and leben is not None and vorher[1] is not None and not p.ich.tot:
            abfall = vorher[1] - leben
            g = lb.gesehen(p.ich)
            if abfall >= 80 and g and p.zeit - g[0] < 1.0 and p.zeit - vorher[0] <= 0.6:
                pos = bewertung.einheiten(g[1], g[2])
                feind = zustand.gegenteam(p.mein_team)
                tuerme = bewertung.stehende_tuerme(p)
                naechst = min(((bewertung.abstand(pos, v), k) for k, v in tuerme.items() if k[0] == feind),
                              default=None)
                gegner_nah = any((sg := lb.gesehen(s)) and p.zeit - sg[0] < 1.5 and bewertung.abstand(
                    pos, bewertung.einheiten(sg[1], sg[2])) < 1200 for s in p.gegner() if not s.tot)
                if naechst and naechst[0] <= 900 and not gegner_nah:
                    kalt = p.zeit - letzter_treffer >= 5
                    letzter_treffer = p.zeit
                    if kalt:
                        roh = rechnung.turm_schaden(naechst[1][2], p.zeit)
                        ruestung = float(p.werte.get("armor") or 0)
                        nach = roh * 100 / (100 + ruestung)
                        aus.append((name, p.zeit, naechst[1], abfall, roh, nach, ruestung))
        vorher = (p.zeit, leben)
    return aus


if __name__ == "__main__":
    alle = []
    for n in sys.argv[1:]:
        alle += lauf(n)
    for name, t, turm, abfall, roh, nach, r in alle:
        print(f"{name[-6:]} {int(t) // 60}:{int(t) % 60:02d} {turm[1]}-{turm[2]:6} Einbruch {abfall:4.0f}  "
              f"gerechnet roh {roh:4.0f}, nach Ruestung ({r:.0f}) {nach:4.0f}")
    if alle:
        q_roh = statistics.median(a[3] / a[4] for a in alle)
        q_nach = statistics.median(a[3] / a[5] for a in alle)
        print(f"\n{len(alle)} erste Treffer: echt/gerechnet Median roh {q_roh:.2f}, nach Ruestung {q_nach:.2f}")
