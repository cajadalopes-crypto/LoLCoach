"""Liest die recherchierten Makro-Regeln und Patch-Werte (wissen/makro/*.toml). Jede Regel nennt Quelle(n) mit Datum."""
from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path

WISSEN = Path(__file__).resolve().parents[2] / "wissen"


@lru_cache(maxsize=16)
def datei(name: str) -> dict:
    return tomllib.loads((WISSEN / "makro" / f"{name}.toml").read_text(encoding="utf-8"))


def regel(nr: str) -> dict:
    """Regel nach Nummer (S1, J9, O7, back_gruende ...) aus sicht.toml oder regeln.toml."""
    for d in ("sicht", "regeln"):
        r = datei(d).get(nr)
        if isinstance(r, dict):
            return r
    raise KeyError(nr)


def patch(bereich: str) -> dict:
    return datei("patchwerte")[bereich]


@lru_cache(maxsize=1)
def ults() -> dict:
    return {k: v for k, v in datei("ults").items() if isinstance(v, dict)}


def quellen() -> dict:
    return {k: v for k, v in datei("quellen").items() if isinstance(v, dict)}


def alle_regeln() -> dict[str, dict]:
    out = {}
    for d in ("sicht", "regeln"):
        out.update({k: v for k, v in datei(d).items() if isinstance(v, dict)})
    return out
