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

    def frage(self, system, anlass, p, lage_text, timeout=40, bilder=None):
        self.anfragen.append(anlass)
        self.systeme = getattr(self, "systeme", []) + [system]
        self.lagen = getattr(self, "lagen", []) + [lage_text]
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



def todesanalyse():
    """Ein Tod mit langer Todeszeit: die Regel legt die Fakten aus dem Rueckblick bei, der
    Stratege fragt mit TOD_SYSTEM und diesen Fakten (nicht der Lage) und wartet `frist`."""
    from lolcoach import gehirn, lage
    datei = Path(__file__).parent / "botspiel_riven_2.jsonl.gz"
    sicht, lb, werk = lage.sicht_fuer(datei), lage.Lagebild(), regeln.Regelwerk()
    tode = []
    for w, d in aufzeichnung.lies_mit_zeit(datei):
        p = zustand.partie(d)
        if not p.ich:
            continue
        for wb, s in sicht.zwischen(w, lage.champions(p)):
            lb.neu(p.zeit - (w - wb), s, p)
        tode += [(p, a) for a in werk.pruefe(p, lb) if a.schluessel == "tod"]
    kurz, lang = tode[0][1], tode[-1][1]
    assert not kurz.situativ and not kurz.kontext            # 1:40, kurze Todeszeit: Standardsatz sofort
    assert lang.situativ and lang.frist == 25, lang
    assert "TOD um 19:55" in lang.kontext and "Wiedereinstieg in 49 s" in lang.kontext, lang.kontext
    assert "15 s vorher: dein Leben 96 %" in lang.kontext, lang.kontext
    plan = sprechplan.Sprechplan(stimme.Stumm())
    s = stratege.Stratege(plan)
    s.gehirn = GehirnAttrappe(0.1, "Du hast mit 6000 Gold weitergepusht. Erst kaufen, dann Mid.")
    s.aktualisiere(tode[-1][0])
    s.veredle(lang)
    ende = time.time() + 3
    while time.time() < ende and not plan.gesagt:
        plan.neu([])
        plan.takt(tode[-1][0].zeit + 1)
        time.sleep(0.05)
    assert [a.text for a in plan.gesagt] == [s.gehirn.text], plan.gesagt
    i = s.gehirn.systeme.index(gehirn.TOD_SYSTEM)     # daneben laeuft der Midgame-Plan (19:55 > 14:00)
    assert s.gehirn.lagen[i].startswith("FAKTEN:\nTOD um 19:55"), s.gehirn.lagen[i][:80]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    stratege.VEREDELN_HOECHSTENS = 1.0
    gesagt, g = fall(0.1)
    assert [a.text for a in gesagt] == [g.text], gesagt
    assert "Standardsatz" in g.anfragen[0]
    gesagt, _ = fall(2.0)   # Claude zu langsam -> Standardsatz
    assert [a.text for a in gesagt] == ["Drache in einer Minute."], gesagt
    print("Stratege OK")
    todesanalyse()
    print("Todesanalyse OK")
