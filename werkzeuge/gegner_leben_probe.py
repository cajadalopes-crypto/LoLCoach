"""Gegner-Leben aus dem Spielbild (Lebensbalken ueber den Koepfen, per gelesenem Namen zugeordnet) gegen die
Wahrheit des Todes: stirbt ein Gegner, muss sein zuletzt gelesenes Leben in den Sekunden davor niedrig gewesen
sein. Ein hoher Wert kurz vor dem Tod heisst: Burst (moeglich) oder ein falsch zugeordneter Balken (ein Fehler, der
die Kill-Rechnung kippt). Dazu: wie oft lag ueberhaupt eine frische Lesung vor.

    python werkzeuge/gegner_leben_probe.py 2026-09-26_194524 2026-09-26_212105 ...
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
from lolcoach import aufzeichnung, lage, zustand  # noqa: E402

A = Path(__file__).resolve().parent.parent / "aufnahmen"


def pruefe(name: str) -> list[tuple]:
    pfad = A / f"{name}.jsonl.gz"
    sicht = lage.sicht_fuer(pfad)
    lb = lage.Lagebild()
    lesungen: dict[str, list[tuple[float, float]]] = {}
    erledigt: set[int] = set()
    aus = []
    for w, d in aufzeichnung.lies_mit_zeit(pfad):
        p = zustand.partie(d, None)
        if p is None or not p.ich:
            continue
        for wb, s in sicht.zwischen(w, lage.champions(p)):
            lb.neu(p.zeit - (w - wb), s, p)
        for _ in lb.ereignisse(lambda wb: p.zeit - (w - wb), sicht.ereignisse(), p):
            pass
        for sp_name, (t, anteil) in lb.gegner_leben.items():
            v = lesungen.setdefault(sp_name, [])
            if not v or v[-1][0] != t:
                v.append((t, anteil))
        for e in p.ereignisse:
            if e.id in erledigt or e.art != "ChampionKill" or e.opfer is None or e.opfer.team == p.mein_team:
                continue
            erledigt.add(e.id)
            davor = [(t, a) for t, a in lesungen.get(e.opfer.name, []) if e.zeit - 3.0 <= t <= e.zeit + 0.2]
            aus.append((name, e.zeit, e.opfer.champion, davor[-1] if davor else None))
    return aus


if __name__ == "__main__":
    alle = []
    for n in sys.argv[1:]:
        alle.extend(pruefe(n))
    for name, t, champ, letzte in alle:
        was = f"{letzte[1] * 100:3.0f} % ({t - letzte[0]:.1f} s vorher)" if letzte else "keine Lesung"
        print(f"{name[-6:]} {int(t) // 60}:{int(t) % 60:02d} {champ:12} {was}")
    mit = [a for a in alle if a[3] is not None]
    hoch = [a for a in mit if a[3][1] > 0.5]
    print(f"\n{len(alle)} Gegner-Tode, {len(mit)} mit Lesung in den 3 s davor; davon {len(hoch)} ueber 50 %")
