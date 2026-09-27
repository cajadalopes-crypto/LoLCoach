"""Champion-Wissen aus Data Dragon (championFull.json, summoner.json).

Braucht den Data-Dragon-Stand auf der Platte (laedt ihn sonst einmal nach).

    python tests/test_champions.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import champions  # noqa: E402


def main():
    for cid in ("Riven", "Urgot", "Shen", "Ezreal"):
        lang, kurz = champions.steckbrief(cid), champions.steckbrief(cid, kurz=True)
        assert lang and kurz and len(kurz) < len(lang), cid
        assert "{{" not in lang and "<" not in lang, (cid, lang)  # Platzhalter/HTML bereinigt
        assert lang.count("\n") == 5 and kurz.count("\n") == 4, cid  # Kopf, Passiv, Q/W/E/R
        r = champions.ult_cooldown(cid)
        assert len(r) == 3 and all(20 <= x <= 300 for x in r) and r[0] >= r[-1], (cid, r)
        assert champions.hat_blink_oder_dash(cid), cid  # alle vier haben einen
    assert "R: Klinge des Exils - CD 120/90/60 s" in champions.steckbrief("Riven", kurz=True)
    assert "E: Arkaner Sprung" in champions.steckbrief("Ezreal") and "(Dash)" in champions.steckbrief("Ezreal")
    assert not champions.hat_blink_oder_dash("Annie") and not champions.hat_blink_oder_dash("Sivir")
    assert champions.steckbrief("Wukong") == champions.steckbrief("MonkeyKing")
    assert champions.steckbrief("GibtEsNicht") == "" and champions.ult_cooldown("GibtEsNicht") == []
    assert champions.zauber_cooldown("SummonerFlash") == 300
    assert champions.zauber_cooldown("GibtEsNicht") == 0
    # ALLE Champions durch die Kampfrechnung - als Gegner und als eigener Champion (werkzeuge/alle_champions.py)
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "werkzeuge"))
    import alle_champions
    befund = alle_champions.pruefen()
    assert not befund, befund
    print("Champions OK")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
