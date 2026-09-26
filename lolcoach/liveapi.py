"""Live Client Data API - die offizielle, lokale Schnittstelle des Spielclients.

Laeuft nur, solange eine Partie oder ein Replay offen ist, auf
https://127.0.0.1:2999 mit selbstsigniertem Zertifikat. Riot gibt sie fuer
Drittprogramme frei; sie liest nichts aus dem Spielprozess.

Was sie liefert:
  - activePlayer: der eigene Champion ganz (Gold, Werte, Runen, Faehigkeiten).
    Im Replay/Zuschauermodus nur {"error": ...}.
  - allPlayers: fuer alle zehn Champion, Level, Items, KDA, CS, Wardscore,
    tot/Respawn, Rolle, NAMEN der Beschwoererzauber - das, was Tab zeigt.
  - events: alle Ereignisse seit Spielbeginn, jedes Mal die ganze Liste.
  - gameData: Spielzeit, Modus, Karte.

Was sie NICHT liefert: Positionen, Gold der anderen, Cooldowns der anderen
(Zauber wie Ultimates). Das kommt aus dem Bild oder wird erschlossen.
"""
from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request

BASIS = "https://127.0.0.1:2999"
_KONTEXT = ssl._create_unverified_context()  # lokal, selbstsigniert


class KeinSpiel(Exception):
    """Kein Spiel offen, Ladebildschirm, oder der Client antwortet nicht."""


def hole(pfad: str, basis: str = BASIS, timeout: float = 1.0):
    try:
        with urllib.request.urlopen(basis + pfad, timeout=timeout, context=_KONTEXT) as r:
            return json.load(r)
    except (urllib.error.URLError, OSError, ValueError) as e:
        # HTTPError (404 im Ladebildschirm) ist eine URLError
        raise KeinSpiel(str(e)) from e


def alles(basis: str = BASIS) -> dict:
    daten = hole("/liveclientdata/allgamedata", basis)
    if not isinstance(daten, dict) or "gameData" not in daten:
        raise KeinSpiel(f"unerwartete Antwort: {str(daten)[:200]}")
    return daten


def laeuft(basis: str = BASIS) -> bool:
    try:
        alles(basis)
        return True
    except KeinSpiel:
        return False
