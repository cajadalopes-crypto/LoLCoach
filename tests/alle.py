"""Alle Tests nacheinander (je eigener Prozess, damit keiner den anderen stoert).

    python tests/alle.py
"""
import subprocess
import sys
import time
from pathlib import Path

HIER = Path(__file__).parent
TESTS = ["test_grundlage", "test_regeln", "test_zauber", "test_stratege", "test_champions", "test_bausteine", "test_flash", "test_kern", "test_kaufplan", "test_quest_tp"]

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    fehler = []
    for name in TESTS:
        t = time.perf_counter()
        lauf = subprocess.run([sys.executable, str(HIER / f"{name}.py")], capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        ok = lauf.returncode == 0
        print(f"{'OK ' if ok else 'FEHLER'} {name} ({time.perf_counter() - t:.0f} s)")
        if not ok:
            fehler.append(name)
            print((lauf.stdout + lauf.stderr)[-2000:])
    sys.exit(1 if fehler else 0)
