"""Kill-Gold (bewertung.kill_gold) gegen den echten Goldsprung des Spielers beim Kill (Live-API: currentGold
vor/nach). Passives Einkommen und Vasallen in der einen Sekunde sind klein (~2-40 g).

Gemessen 27.09. (72 Kills, 5 Partien): alte Rechnung (Level + Kopfgeld aus allen Kills) im Median 118 zu hoch;
mit den Serien aus den Ereignissen (bewertung.TODESSERIE_GOLD / KILLSERIE_GOLD) Median +2, 80 % innerhalb 65.

    python werkzeuge/kill_gold.py 2026-09-26_212105 ... [--neu]     (--neu: mit Serien aus den Ereignissen)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
from lolcoach import aufzeichnung, bewertung, zustand  # noqa: E402

A = Path(__file__).resolve().parent.parent / "aufnahmen"
alle = []
for name in [a for a in sys.argv[1:] if not a.startswith("--")]:
    stand = [p for p in map(lambda d: zustand.partie(d, None), aufzeichnung.lies(A / f"{name}.jsonl.gz")) if p.ich]
    ende = stand[-1]
    kills = [e for e in ende.ereignisse if e.art == "ChampionKill" and e.taeter is not None
             and e.taeter.name == ende.ich.name and e.opfer is not None]
    for e in kills:
        vor = max((p for p in stand if p.zeit < e.zeit - 0.3), key=lambda p: p.zeit, default=None)
        nach = min((p for p in stand if p.zeit > e.zeit + 0.8), key=lambda p: p.zeit, default=None)
        if vor is None or nach is None or nach.zeit - vor.zeit > 3 or vor.gold is None or nach.gold is None:
            continue
        if nach.gold < vor.gold:                  # dazwischen gekauft: nicht messbar
            continue
        opfer = next((s for s in vor.spieler if s.name == e.opfer.name), None)
        erst = not any(x.art == "FirstBlood" for x in vor.ereignisse)
        soll = bewertung.kill_gold(opfer, erstes_blut=erst, p=vor if "--neu" in sys.argv else None)
        ist = nach.gold - vor.gold
        alle.append((name, int(e.zeit), opfer.champion, opfer.level, opfer.kills, opfer.tode, soll, int(ist)))
for a in alle:
    print(f"{a[0][-6:]} {a[1] // 60}:{a[1] % 60:02d} {a[2]:12} L{a[3]:2} {a[4]}/{a[5]}  gerechnet {a[6]:4}  echt {a[7]:4}  "
          f"Diff {a[7] - a[6]:+5}")
if alle:
    d = sorted(a[7] - a[6] for a in alle)
    print(f"{len(d)} Kills: Abweichung echt - gerechnet Median {d[len(d) // 2]:+}, Spanne {d[0]:+} .. {d[-1]:+}")
