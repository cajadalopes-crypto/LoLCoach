"""Alle 111 Makro-Entscheidungen: feuert, wenn sie soll; schweigt, wenn sie nicht soll; Kommando ohne interne Begriffe.

    python tests/makro/test_entscheidungen.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from faelle import FAELLE  # noqa: E402
from lolcoach.makro.entscheidungen import laden  # noqa: E402

# Woerter, die Carlos nie hoeren soll (interne Begriffe, Code-Reste)
VERBOTEN = [r"\bhirn\b", r"\bgehirn\b", r"\bpolicy\b", r"aktionswert", r"\bq\b", r"π", r"\bnone\b", r"\bnan\b",
            r"[{}_]", r"klarheit", r"p_highelo", r"\bplan\b", r"\blage\b", r"\bflags?\b", r"\bdr\b"]


def sprache(text: str) -> str | None:
    if ":" not in text or len(text) < 12:
        return "keine Form 'Tu X: weil Y'"
    for w in VERBOTEN:
        if re.search(w, text, flags=re.IGNORECASE):
            return f"interner Begriff ({w})"
    return None


def pruefen() -> dict[str, tuple[bool, str, str]]:
    """id -> (bestanden, Meldung, Kommando-Text der feuernden Lage)."""
    reg = laden()
    out = {}
    for id_, e in reg.items():
        if id_ not in FAELLE:
            out[id_] = (False, "kein Testfall", "")
            continue
        feuert, schweigt = FAELLE[id_]
        try:
            k = e.pruefe(feuert())
            s = e.pruefe(schweigt())
        except Exception as ex:          # noqa: BLE001 - jeder Fehler ist ein roter Test
            out[id_] = (False, f"Ausnahme: {type(ex).__name__}: {ex}", "")
            continue
        if k is None:
            out[id_] = (False, "feuert nicht, obwohl es soll", "")
        elif s is not None:
            out[id_] = (False, f"feuert, obwohl es schweigen soll: {s.text}", k.text)
        elif (fehler := sprache(k.text)) is not None:
            out[id_] = (False, fehler, k.text)
        elif k.id != id_:
            out[id_] = (False, f"falsche Nummer {k.id}", k.text)
        else:
            out[id_] = (True, "", k.text)
    return out


def main() -> int:
    r = pruefen()
    rot = {k: v for k, v in r.items() if not v[0]}
    for k, v in sorted(r.items(), key=lambda kv: (kv[0][0], int(kv[0][1:]))):
        print(f"{'OK ' if v[0] else 'ROT'} {k:4} {v[2] if v[0] else v[1]}")
    print(f"\n{len(r) - len(rot)}/{len(r)} gruen")
    return 1 if rot or len(r) != 111 else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
