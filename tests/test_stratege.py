"""Stratege: situative Fassung ersetzt den Standardsatz - oder der Standardsatz
kommt, wenn Claude zu lange braucht. Ohne echte Claude-Aufrufe (Gehirn ersetzt).

    python tests/test_stratege.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import aufzeichnung, regeln, sprechplan, stimme, stratege, zustand  # noqa: E402


class GehirnAttrappe:
    def __init__(self, dauer, text="Schieb jetzt die Welle rein und geh zum Drachen."):
        self.dauer, self.text, self.akte, self.anfragen = dauer, text, "Akte", []

    def frage(self, system, anlass, p, lage_text, timeout=40):
        self.anfragen.append(anlass)
        time.sleep(self.dauer)
        return self.text

    def akte_anlegen(self, p, fertig=None):
        pass


def fall(dauer):
    plan = sprechplan.Sprechplan(stimme.Stumm())
    s = stratege.Stratege(plan)
    s.gehirn = GehirnAttrappe(dauer)
    p = zustand.partie(list(aufzeichnung.lies(Path(__file__).parent / "botspiel_riven_1.jsonl.gz"))[240])
    s.aktualisiere(p)
    a = regeln.Ansage("Drache in einer Minute.", regeln.WICHTIG, "vorwarnung:drache", zeit=p.zeit,
                      gueltig=25, situativ=True)
    s.veredle(a)
    ende = time.time() + 3
    while time.time() < ende:
        plan.neu([])
        if plan.takt(p.zeit + 1):
            break
        time.sleep(0.05)
    return plan.gesagt, s.gehirn


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    stratege.VEREDELN_HOECHSTENS = 1.0
    gesagt, g = fall(0.1)
    assert [a.text for a in gesagt] == [g.text], gesagt
    assert "Standardsatz" in g.anfragen[0]
    gesagt, _ = fall(2.0)   # Claude zu langsam -> Standardsatz
    assert [a.text for a in gesagt] == ["Drache in einer Minute."], gesagt
    print("Stratege OK")
