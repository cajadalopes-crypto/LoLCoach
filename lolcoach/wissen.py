"""Die gepflegte Wissensbasis: `wissen/*.toml`.

Alles, was mit dem Patch veraltet, steht dort und nicht im Code. Jede
Datei traegt ihren `stand`, damit sichtbar bleibt, was geprueft ist.
"""
from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path

ORDNER = Path(__file__).resolve().parent.parent / "wissen"


@lru_cache(maxsize=None)
def lade(name: str) -> dict:
    with open(ORDNER / f"{name}.toml", "rb") as f:
        return tomllib.load(f)


def objektive() -> dict[str, dict]:
    """Nur die Objective-Eintraege, ohne `stand`."""
    return {k: v for k, v in lade("objektive").items() if isinstance(v, dict)}
