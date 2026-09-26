"""Regelwerk + Sprechplan an einer echten Partie (Bot-Partie 26.09.2026,
Riven Top mit Zuenden statt Teleport, gegen Shen; Sieg nach 20:50).

    python tests/test_regeln.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import aufzeichnung, lage, regeln, sprechplan, stimme, zustand  # noqa: E402

PARTIE = Path(__file__).parent / "botspiel_riven_1.jsonl.gz"


PARTIE_2 = Path(__file__).parent / "botspiel_riven_2.jsonl.gz"   # mit Minimap-Sichtungen


def ansagen(pfad=PARTIE, sicht=None):
    werk, plan = regeln.Regelwerk(), sprechplan.Sprechplan(stimme.Stumm())
    lagebild = lage.Lagebild() if sicht else None
    for w, d in aufzeichnung.lies_mit_zeit(pfad):
        p = zustand.partie(d)
        if sicht:
            for wb, s in sicht.zwischen(w, lage.champions(p)):
                lagebild.neu(p.zeit - (w - wb), s, p)
        plan.neu(werk.pruefe(p, lagebild))
        plan.takt(p.zeit)
    return plan.gesagt


def mit_minimap():
    """Zweite Partie (Riven gegen Shen, 25 min) mit den Sichtungen der Minimap."""
    gesagt = ansagen(PARTIE_2, lage.SichtAusBildern.aus_cache(PARTIE_2.with_name("botspiel_riven_2_bilder")))
    um = [(a.gesprochen, a.text) for a in gesagt]
    weg = [t for t, x in um if "weg aus deiner Lane" in x]
    assert 1 <= len(weg) <= 4, weg                                        # vorher 10 Fehlalarme
    assert any(95 <= t <= 110 and "Vom Turm erwischt" in x for t, x in um)
    assert any(380 <= t <= 395 and "Vorsicht, Vi oben" in x for t, x in um)
    assert not any(t > 840 and "sicher pushen" in x for t, x in um)       # Lane-Sprache nur in der Lane-Phase
    assert not any("Kartenseite" in x and ("Mitte" in x or "Mid-Lane" in x) for _, x in um)
    print(f"Partie 2 mit Minimap: {len(gesagt)} Ansagen, OK")


def main():
    gesagt = ansagen()
    texte = [a.text for a in gesagt]
    um = {round(a.gesprochen): a.text for a in gesagt}

    def gesagt_bei(von, bis, teil):
        return any(von <= t <= bis and teil in x for t, x in um.items())

    assert 20 <= len(gesagt) <= 50, f"{len(gesagt)} Ansagen - zu still oder zu geschwaetzig"
    # Riven hatte Zuenden statt Teleport - bis die Top-Quest (spaetestens 13:35) Teleport gibt
    assert not any(a.gesprochen < 815 and "Teleport mitkämpfen" in a.text for a in gesagt), "vor der Quest kein TP"
    assert any(a.gesprochen > 815 and "Teleport mitkämpfen" in a.text for a in gesagt), "nach der Quest mit TP"
    assert gesagt_bei(230, 250, "Drache in einer Minute. Ohne Teleport")
    assert gesagt_bei(95, 105, "Shen ist Level 2")                       # Level-2-Rennen verloren
    assert gesagt_bei(310, 325, "Level 6 vor Shen")
    assert gesagt_bei(505, 520, "Ping Drache")                           # Vi tot, Drache weit weg
    assert gesagt_bei(1225, 1235, "Baron jetzt")
    assert sum("Baron jetzt" in t for t in texte) == 1                   # nicht doppelt
    assert not gesagt_bei(1170, 1200, "Herold jetzt")                    # verschwindet 19:45
    # nie zwei Saetze uebereinander (ausser SOFORT, das unterbrechen darf)
    for a, b in zip(gesagt, gesagt[1:]):
        dauer = len(a.text) / sprechplan.ZEICHEN_PRO_SEKUNDE
        assert b.gesprochen >= a.gesprochen + dauer or b.prio == regeln.SOFORT, (a.text, b.text)
    print(f"{len(gesagt)} Ansagen, OK")
    mit_minimap()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
