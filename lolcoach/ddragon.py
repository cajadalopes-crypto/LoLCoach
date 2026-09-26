"""Data Dragon - Riots oeffentliche Stammdaten (Items, Champions, Bilder) je Patch.

Wird einmal je Patch geladen und unter `daten/ddragon/<version>/` abgelegt.
Ohne Netz laeuft alles weiter mit dem neuesten Stand auf der Platte; ohne
irgendeinen Stand fallen die Item-Preise auf das zurueck, was die Live-API
selbst mitschickt.
"""
from __future__ import annotations

import json
import urllib.request
from functools import lru_cache
from pathlib import Path

CDN = "https://ddragon.leagueoflegends.com"
ABLAGE = Path(__file__).resolve().parent.parent / "daten" / "ddragon"
SPRACHE = "de_DE"


def _json_holen(url: str):
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.load(r)


def _lokale_versionen() -> list[str]:
    if not ABLAGE.exists():
        return []
    return sorted((p.name for p in ABLAGE.iterdir() if (p / "item.json").exists()),
                  key=lambda v: [int(x) if x.isdigit() else 0 for x in v.split(".")])


@lru_cache(maxsize=1)
def version() -> str | None:
    """Neueste Version; laedt sie nach, wenn noch nicht auf der Platte."""
    try:
        neu = _json_holen(f"{CDN}/api/versions.json")[0]
        ordner = ABLAGE / neu
        if not (ordner / "item.json").exists():
            ordner.mkdir(parents=True, exist_ok=True)
            for datei in ("item.json", "champion.json", "summoner.json"):
                daten = _json_holen(f"{CDN}/cdn/{neu}/data/{SPRACHE}/{datei}")
                (ordner / datei).write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
        return neu
    except OSError:
        lokal = _lokale_versionen()
        return lokal[-1] if lokal else None


def _lade(datei: str) -> dict:
    v = version()
    if v is None:
        return {}
    pfad = ABLAGE / v / datei
    return json.loads(pfad.read_text(encoding="utf-8"))["data"] if pfad.exists() else {}


@lru_cache(maxsize=1)
def items() -> dict[int, dict]:
    return {int(k): v for k, v in _lade("item.json").items()}


@lru_cache(maxsize=1)
def champions() -> dict[str, dict]:
    """Schluessel ist die interne ID ("MonkeyKing" fuer Wukong)."""
    return _lade("champion.json")


def item_preis(item_id: int, api_preis: int = 0) -> int:
    eintrag = items().get(item_id)
    if eintrag:
        return int(eintrag["gold"]["total"])
    return int(api_preis)
