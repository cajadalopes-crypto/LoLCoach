"""Flash-Erkennung bei 15 Bildern/s am Pruefstand (werkzeuge/flash_pruefstand.py).

Gemessen 26.09.2026 nach der Korrektur des Stillstands-Schutzes: 3 von 4 Flashes,
0 Fehlalarme (Dashes: Riven E/Q, Vi Q, Lee Sin Q2) - sauber, mit 10 % Bildaussetzern
und mit Rauschen. Nicht erkannt: Flash mitten in einer Gruppe uebereinanderliegender
Icons (dafuer gibt es die Chat-Pings).

    python tests/test_flash.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "werkzeuge"))
import flash_pruefstand  # noqa: E402

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    erg = flash_pruefstand.pruefe(ausfall=0.1)
    gefunden = sum(e[1] for e in erg.values())
    fehl = sum(e[2] for e in erg.values())
    for name in ("laufen + Flash", "stehen + Flash", "E + Flash (Riven)"):
        assert erg[name][1] == erg[name][0], (name, erg[name])
    for name in ("Riven E", "Riven Q x3", "Vi Q", "Lee Sin Q2", "Verdeckung"):
        assert erg[name][2] == 0, (name, erg[name])
    assert fehl == 0, erg
    print(f"Flash {gefunden}/{sum(e[0] for e in erg.values())}, Fehlalarme {fehl}, OK")
