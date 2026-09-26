"""Zauber-Timer: wer hat Flash (und Co.) gerade nicht.

Quellen, wie ein menschlicher Coach sie hat:
  - der Chat unten links: Mitspieler pingen "Urgot Blitz", wenn Urgot Flash benutzt hat,
  - die Minimap: ein Champion springt in einem Bild um Flash-Weite (Verfolger).
Die Live-API zeigt fremde Cooldowns nicht - also wird gerechnet: Verbrauch + Cooldown.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Grund-Cooldowns (Sekunden). Werden, wenn vorhanden, aus Data Dragon ueberschrieben.
GRUND = {"SummonerFlash": 300, "SummonerTeleport": 360, "SummonerDot": 180, "SummonerHeal": 240,
         "SummonerBarrier": 180, "SummonerExhaust": 240, "SummonerHaste": 240, "SummonerBoost": 240,
         "SummonerSmite": 90}
NAME_DE = {"SummonerFlash": "Flash", "SummonerTeleport": "Teleport", "SummonerDot": "Zünden",
           "SummonerHeal": "Heilen", "SummonerBarrier": "Barriere", "SummonerExhaust": "Erschöpfen",
           "SummonerHaste": "Geist", "SummonerBoost": "Reinigen", "SummonerSmite": "Zerschmettern"}
# Was im Chat steht (Client auf Deutsch, Spieler tippen auch Englisch)
WOERTER = {"blitz": "SummonerFlash", "flash": "SummonerFlash", "flashlos": "SummonerFlash",
           "zünden": "SummonerDot", "zuenden": "SummonerDot", "ignite": "SummonerDot",
           "teleport": "SummonerTeleport", "tp": "SummonerTeleport", "heilen": "SummonerHeal",
           "heal": "SummonerHeal", "barriere": "SummonerBarrier", "barrier": "SummonerBarrier",
           "erschöpfen": "SummonerExhaust", "erschoepfen": "SummonerExhaust", "exhaust": "SummonerExhaust",
           "geist": "SummonerHaste", "ghost": "SummonerHaste", "reinigen": "SummonerBoost",
           "cleanse": "SummonerBoost"}


def cooldown(schluessel: str) -> float:
    """Aus Data Dragon (champions.zauber_cooldown), sonst die Grundwerte oben.
    Zauber-Tempo aus Stiefeln/Runen ist nicht eingerechnet: eher zu lang als zu kurz."""
    try:
        from . import champions
        if wert := champions.zauber_cooldown(schluessel):
            return float(wert)
    except Exception:
        pass
    return float(GRUND.get(schluessel, 300))


def blink_champions() -> set[str]:
    from . import wissen
    return set(wissen.lade("blinks").get("ids", []))


@dataclass
class Timer:
    name: str               # Spielername
    champion: str
    zauber: str             # "SummonerFlash"
    zurueck: float          # Spielzeit, ab der er wieder da ist
    quelle: str             # "Chat" oder "Minimap"
    seit: float             # Spielzeit des Verbrauchs
    gemeldet: bool = False


class Zaubertimer:
    def __init__(self):
        self.timer: dict[tuple[str, str], Timer] = {}

    def benutzt(self, spieler, zauber: str, zeit: float, quelle: str, zurueck: float | None = None) -> Timer | None:
        """Traegt einen Verbrauch ein. Gibt den Timer zurueck, wenn er neu ist
        (ein zweiter Ping fuer denselben Verbrauch aendert nichts)."""
        schl = (spieler.name, zauber)
        alt = self.timer.get(schl)
        if alt and alt.zurueck > zeit and abs(alt.seit - zeit) < 60:
            if quelle == "Chat" and alt.quelle == "Minimap":
                alt.quelle = "Chat"  # Chat bestaetigt die Minimap
            return None
        t = Timer(spieler.name, spieler.champion, zauber, zurueck or zeit + cooldown(zauber), quelle, zeit)
        self.timer[schl] = t
        return t

    def fehlt(self, spieler, zauber: str, zeit: float) -> float | None:
        """Sekunden, bis `zauber` wieder da ist; None, wenn nichts bekannt ist."""
        t = self.timer.get((spieler.name, zauber))
        return t.zurueck - zeit if t and t.zurueck > zeit else None

    def aktiv(self, zeit: float) -> list[Timer]:
        return [t for t in self.timer.values() if t.zurueck > zeit]


# --- Chat -----------------------------------------------------------------------

_ZEIT = re.compile(r"\b(\d{1,2})[:.](\d{2})\b")


def aus_chat(zeile: str, p) -> list[tuple[object, str, float | None]]:
    """Findet in einer Chatzeile (Champion, Zauber[, Rueckkehr]) fuer Gegner.

    "[Team] Schizoid Nevir (Riven): Urgot Blitz" -> Urgot, Flash.
    Der Absender steht vor dem Doppelpunkt; gesucht wird nur in der Nachricht.
    Eine Uhrzeit in der Nachricht wird als Rueckkehrzeit gelesen, wenn sie in
    der Zukunft liegt (manche Pings nennen sie)."""
    import difflib
    rest = re.sub(r"^\s*\[?\d{1,2}:\d{2}\]?\s*", "", zeile)   # Zeitstempel vorn (Chat-Einstellung)
    nachricht = rest.split(":", 1)[1] if ":" in rest else rest
    woerter = re.findall(r"[a-zäöüß']+", nachricht.lower())
    zauber = [WOERTER[w] for w in woerter if w in WOERTER]
    if not zauber:
        return []
    namen = {}
    for s in p.gegner():
        for n in {s.champion.lower(), s.champion_id.lower()}:
            namen[n.replace(" ", "").replace("'", "")] = s
    kandidaten = woerter + [a + b for a, b in zip(woerter, woerter[1:])]
    gegner = None
    for w in kandidaten:
        if treffer := difflib.get_close_matches(w.replace("'", ""), list(namen), n=1, cutoff=0.8):
            gegner = namen[treffer[0]]
            break
    if gegner is None:
        return []
    zurueck = None
    if m := _ZEIT.search(nachricht):
        t = int(m.group(1)) * 60 + int(m.group(2))
        if t > p.zeit:
            zurueck = float(t)
    return [(gegner, z, zurueck) for z in dict.fromkeys(zauber)]
