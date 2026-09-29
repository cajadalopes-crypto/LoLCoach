"""Speicher aufraeumen (Auftrag 022) - Regeln in lolcoach/aufraeumen.py.

    python werkzeuge/aufraeumen.py          # Trockenlauf: zeigt, was ginge
    python werkzeuge/aufraeumen.py --ja     # loescht
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import aufraeumen  # noqa: E402

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    tp = aufraeumen.testpartien()
    print(f"Testpartien ({len(tp)}): " + ", ".join(tp))
    print(f"Letzte Partien: {', '.join(sorted(aufraeumen._letzte()))}")
    aufraeumen.aufraeumen(ja="--ja" in sys.argv)
