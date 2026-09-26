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


# championFull: Faehigkeiten samt Cooldowns (champions.py); runesReforged: Runen.
DATEIEN = ("item.json", "champion.json", "summoner.json", "championFull.json", "runesReforged.json")


def _nachladen(v: str) -> None:
    """Holt, was fuer Version v noch fehlt (auch Dateien, die spaeter dazukamen)."""
    ordner = ABLAGE / v
    ordner.mkdir(parents=True, exist_ok=True)
    for datei in DATEIEN:
        if not (ordner / datei).exists():
            daten = _json_holen(f"{CDN}/cdn/{v}/data/{SPRACHE}/{datei}")
            (ordner / datei).write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")


@lru_cache(maxsize=1)
def version() -> str | None:
    """Neueste Version; laedt sie nach, wenn noch nicht auf der Platte."""
    try:
        neu = _json_holen(f"{CDN}/api/versions.json")[0]
        _nachladen(neu)
        return neu
    except OSError:
        lokal = _lokale_versionen()
        return lokal[-1] if lokal else None


def roh(datei: str):
    """Ganze Datei der aktuellen Version (runesReforged.json ist eine Liste, kein "data")."""
    v = version()
    if v is None:
        return None
    pfad = ABLAGE / v / datei
    if not pfad.exists():  # Stand ohne diese Datei (offline) -> juengste Version, die sie hat
        pfad = next((ABLAGE / w / datei for w in reversed(_lokale_versionen())
                     if (ABLAGE / w / datei).exists()), pfad)
    return json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else None


def _lade(datei: str) -> dict:
    daten = roh(datei)
    return daten["data"] if daten else {}


@lru_cache(maxsize=1)
def items() -> dict[int, dict]:
    return {int(k): v for k, v in _lade("item.json").items()}


@lru_cache(maxsize=1)
def champions() -> dict[str, dict]:
    """Schluessel ist die interne ID ("MonkeyKing" fuer Wukong). Grundwerte aus den Spieldaten gehen vor
    (wissen/grundwerte.json, werkzeuge/faehigkeiten_holen.py): Data Dragon 16.19.1 fuehrt fuer alle Champions
    attackdamageperlevel = 0 - dein Grund-AD war so auf Level 13 ~33 zu niedrig, der Bonus-AD (Combo) zu hoch."""
    daten = _lade("champion.json")
    try:
        echt = json.loads((Path(__file__).resolve().parent.parent / "wissen" / "grundwerte.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        echt = {}
    for cid, werte in echt.items():
        if cid in daten:
            daten[cid].setdefault("stats", {}).update(werte)
    return daten


def item_preis(item_id: int, api_preis: int = 0) -> int:
    eintrag = items().get(item_id)
    if eintrag:
        return int(eintrag["gold"]["total"])
    return int(api_preis)
