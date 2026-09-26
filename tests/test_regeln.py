"""Regelwerk + Sprechplan an einer echten Partie (Bot-Partie 26.09.2026,
Riven Top mit Zuenden statt Teleport, gegen Shen; Sieg nach 20:50).

    python tests/test_regeln.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import aufzeichnung, regeln, sprechplan, stimme, zustand  # noqa: E402

PARTIE = Path(__file__).parent / "botspiel_riven_1.jsonl.gz"


def ansagen(pfad=PARTIE):
    werk, plan = regeln.Regelwerk(), sprechplan.Sprechplan(stimme.Stumm())
    for d in aufzeichnung.lies(pfad):
        p = zustand.partie(d)
        plan.neu(werk.pruefe(p))
        plan.takt(p.zeit)
    return plan.gesagt


def main():
    gesagt = ansagen()
    texte = [a.text for a in gesagt]
    um = {round(a.gesprochen): a.text for a in gesagt}

    def gesagt_bei(von, bis, teil):
        return any(von <= t <= bis and teil in x for t, x in um.items())

    assert 20 <= len(gesagt) <= 50, f"{len(gesagt)} Ansagen - zu still oder zu geschwaetzig"
    assert not any("Teleport mitkämpfen" in t for t in texte), "Riven hatte kein Teleport"
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


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
