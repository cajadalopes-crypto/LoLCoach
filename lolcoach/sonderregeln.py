"""Sonderregeln je Champion, die Kauf, Back oder TP aendern (Auftrag 028, 6.2 - 134020: Ornn hoerte "Back jetzt: 1000
Gold fuer Dornenpanzer", obwohl er ohne Rueckruf kauft). Die Regeln stehen in wissen/sonderregeln.toml, mit der
Lexikon-Stelle als Quelle; hier werden sie gelesen."""
from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path

DATEI = Path(__file__).resolve().parent.parent / "wissen" / "sonderregeln.toml"


@lru_cache(maxsize=1)
def _alle() -> dict:
    try:
        return tomllib.loads(DATEI.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def regeln(champion_id: str | None) -> dict:
    return _alle().get(champion_id or "", {})


def kauft_ohne_back(champion_id: str | None) -> bool:
    """Kauft Items ohne Rueckruf (Ornn): kein Back fuer Gold - nur fuer Leben und Mana."""
    return bool(regeln(champion_id).get("kauf_ohne_back"))
