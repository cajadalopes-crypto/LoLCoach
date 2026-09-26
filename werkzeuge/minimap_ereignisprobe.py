"""Minimap-Positionen gegen die Wahrheit der Ereignisse: wer einen Drachen, Herold, Baron, Larven oder einen Turm
toetet, steht dort; wer einen Champion toetet, steht bei ihm. Die Live-API nennt den Taeter - die Minimap muss ihn
in den Sekunden davor an dieser Stelle gesehen haben. Liegt die Sichtung weit weg, ist sie falsch (Icon verwechselt
oder falsch verfolgt).

Je Ereignis: die Sichtungen des Taeters (Lagebild.verlauf) von 2 s vor bis 1 s nach dem Ereignis; gemessen wird die
naechste Sichtung zum Ort. Verbuendete sind immer auf der Minimap - bei ihnen zaehlt auch "nicht gesehen" als
Verfolgungsluecke; Gegner nur, wenn sie sichtbar waren.

    python werkzeuge/minimap_ereignisprobe.py 2026-09-26_194524 2026-09-26_212105 ...
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
from lolcoach import aufzeichnung, bewertung, lage, zustand  # noqa: E402

A = Path(__file__).resolve().parent.parent / "aufnahmen"
GRUBE = {"DragonKill": "drache", "HeraldKill": "herold", "BaronKill": "baron", "HordeKill": "larven"}
RADIUS = {"grube": 1600.0, "turm": 1600.0, "kill": 2500.0}   # Einheiten; Fernkaempfer und lange Ults eingerechnet


def pruefe(name: str) -> list[tuple]:
    pfad = A / f"{name}.jsonl.gz"
    sicht = lage.sicht_fuer(pfad)
    lb = lage.Lagebild()
    offen: list = []          # Ereignisse, die noch auf die Sichtungen danach warten
    erledigt: set[int] = set()
    aus = []
    p = None
    for w, d in aufzeichnung.lies_mit_zeit(pfad):
        p = zustand.partie(d, None)
        if p is None or not p.spieler:
            continue
        for wb, s in sicht.zwischen(w, lage.champions(p)):
            lb.neu(p.zeit - (w - wb), s, p)
        for e in p.ereignisse:
            if e.id in erledigt:
                continue
            erledigt.add(e.id)
            offen.append(e)
        for e in [e for e in offen if p.zeit >= e.zeit + 1.5]:
            offen.remove(e)
            aus.extend(_bewerte(e, p, lb, name))
    return aus


def _ort(e, p):
    """(Art, Ort in Einheiten, Taeter) oder None."""
    taeter = p.spieler_namens(e.daten.get("KillerName", "")) if e.daten.get("KillerName") else None
    if taeter is None:
        return None
    if e.art in GRUBE:
        return "grube", bewertung.einheiten(*bewertung.GRUBEN[GRUBE[e.art]]), taeter
    if e.art == "TurretKilled":
        st = zustand.struktur(e.daten.get("TurretKilled", ""))
        wo = bewertung.TUERME.get((st.team, st.lane, st.stufe)) if st else None
        return ("turm", wo, taeter) if wo else None
    return None


def _naechste(lb, sp, t, ziel):
    v = lb.verlauf.get((sp.name, sp.team)) or ()
    fenster = [(tt, x, y) for tt, x, y in v if t - 2.0 <= tt <= t + 1.0]
    if not fenster:
        return None
    return min(bewertung.abstand(bewertung.einheiten(x, y), ziel) for _, x, y in fenster)


def _bewerte(e, p, lb, name):
    uhr = f"{int(e.zeit) // 60}:{int(e.zeit) % 60:02d}"
    if e.art == "ChampionKill" and e.taeter is not None and e.opfer is not None:
        # Taeter bei seinem Opfer: beide Sichtungen um den Tod
        vo = lb.verlauf.get((e.opfer.name, e.opfer.team)) or ()
        fo = [(tt, x, y) for tt, x, y in vo if e.zeit - 2.0 <= tt <= e.zeit + 0.3]
        if not fo:
            return []
        wo = bewertung.einheiten(fo[-1][1], fo[-1][2])
        ab = _naechste(lb, e.taeter, e.zeit, wo)
        freund = e.taeter.team == p.mein_team
        return [(name, uhr, "kill", e.taeter.champion, freund, ab, e.opfer.champion)]
    o = _ort(e, p)
    if o is None:
        return []
    art, wo, taeter = o
    return [(name, uhr, art, taeter.champion, taeter.team == p.mein_team, _naechste(lb, taeter, e.zeit, wo),
             e.art if art == "grube" else e.daten.get("TurretKilled", "")[:22])]


if __name__ == "__main__":
    alle = []
    for n in sys.argv[1:]:
        alle.extend(pruefe(n))
    falsch = 0
    for name, uhr, art, champ, freund, ab, was in alle:
        wer = "eigen " if freund else "Gegner"
        if ab is None:
            urteil = "nicht gesehen" + (" (LUECKE)" if freund else "")
        elif ab > RADIUS[art]:
            urteil = f"FALSCH: {ab:.0f} Einheiten daneben"
            falsch += 1
        else:
            urteil = f"ok ({ab:.0f})"
        print(f"{name[-6:]} {uhr:>6} {art:5} {wer} {champ:12} {was:24} {urteil}")
    gesehen = [a for a in alle if a[5] is not None]
    luecken = [a for a in alle if a[5] is None and a[4]]
    print(f"\n{len(alle)} Ereignisse, {len(gesehen)} mit Sichtung: {falsch} falsch platziert; "
          f"{len(luecken)} Verfolgungsluecken bei Verbuendeten")
