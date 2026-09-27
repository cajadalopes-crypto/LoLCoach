"""Zauber-Timer: wer hat Flash (und Co.) gerade nicht.

Quellen, wie ein menschlicher Coach sie hat:
  - der Chat unten links: Mitspieler pingen "Urgot Blitz", wenn Urgot Flash benutzt hat,
  - die Minimap: ein Champion springt in einem Bild um Flash-Weite (Verfolger).
Die Live-API zeigt fremde Cooldowns nicht - also wird gerechnet: Verbrauch + Cooldown.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

# Grund-Cooldowns (Sekunden). Werden, wenn vorhanden, aus Data Dragon ueberschrieben.
GRUND = {"SummonerFlash": 300, "SummonerTeleport": 360, "SummonerDot": 180, "SummonerHeal": 240,
         "SummonerBarrier": 180, "SummonerExhaust": 240, "SummonerHaste": 240, "SummonerBoost": 240,
         "SummonerSmite": 90}
NAME_DE = {"SummonerFlash": "Flash", "SummonerTeleport": "Teleport", "SummonerDot": "Zünden",
           "SummonerHeal": "Heilen", "SummonerBarrier": "Barriere", "SummonerExhaust": "Erschöpfen",
           "SummonerHaste": "Geist", "SummonerBoost": "Reinigen", "SummonerSmite": "Zerschmettern",
           "R": "Ult"}
# Was im Chat steht (Client auf Deutsch, Spieler tippen auch Englisch)
WOERTER = {"blitz": "SummonerFlash", "flash": "SummonerFlash", "flashlos": "SummonerFlash",
           "zünden": "SummonerDot", "zuenden": "SummonerDot", "ignite": "SummonerDot",
           "teleport": "SummonerTeleport", "tp": "SummonerTeleport", "heilen": "SummonerHeal",
           "heal": "SummonerHeal", "barriere": "SummonerBarrier", "barrier": "SummonerBarrier",
           "erschöpfen": "SummonerExhaust", "erschoepfen": "SummonerExhaust", "exhaust": "SummonerExhaust",
           "geist": "SummonerHaste", "ghost": "SummonerHaste", "reinigen": "SummonerBoost",
           "cleanse": "SummonerBoost", "ult": "R", "ulti": "R", "ultimate": "R", "r": "R"}


def _woerter() -> dict[str, str]:
    """Umgangssprache (oben) plus die Namen, die der Client selbst in den Chat schreibt.
    Die eingebaute Nachricht beim Anklicken eines gegnerischen Zaubers lautet
    'Spieler (Champion): Zielchampion Zaubername' (z. B. "hotcode (Corki): Kog'Maw Heal",
    fuer die Ult "... Corki R") - im deutschen Client mit den deutschen Namen aus Data
    Dragon: Blitz, Entzuenden, Laeuterung, Teleportation, ... (geprueft 26.09.2026)."""
    global _WOERTER_CACHE
    if _WOERTER_CACHE is None:
        aus = dict(WOERTER)
        try:
            from . import ddragon
            daten = ddragon.roh("summoner.json") or {}
            for schl, v in (daten.get("data") or {}).items():
                if schl in GRUND:
                    for wort in re.findall(r"[a-zäöüß]+", v.get("name", "").lower()):
                        if len(wort) >= 4:
                            aus.setdefault(wort, schl)
        except Exception:
            pass
        _WOERTER_CACHE = aus
    return _WOERTER_CACHE


_WOERTER_CACHE: dict[str, str] | None = None


def cooldown(schluessel: str, spieler=None, zeit: float | None = None) -> float:
    """Aus Data Dragon (champions.zauber_cooldown), sonst die Grundwerte oben.
    Zauber-Tempo aus Stiefeln/Runen ist nicht eingerechnet: eher zu lang als zu kurz.
    Die Ult ("R") nach Rang: Level 6-10 Rang 1, 11-15 Rang 2, ab 16 Rang 3."""
    if schluessel == "R":
        try:
            from . import champions
            werte = champions.ult_cooldown(spieler.champion_id) if spieler else []
            if werte:
                rang = 0 if spieler.level < 11 else 1 if spieler.level < 16 else 2
                return float(werte[min(rang, len(werte) - 1)])
        except Exception:
            pass
        return 100.0
    if schluessel == "SummonerTeleport" and spieler is not None and zeit is not None:
        # Wiki Teleport (geprueft 26.09.2026): bis 10:00 300 s, danach 330-240 s je Level;
        # Top-Quest (spaetestens 13:35) mit eigenem TP: 30 s weniger.
        if zeit < 600:
            return 300.0
        cd = 330.0 - (min(18, max(1, spieler.level)) - 1) * 90.0 / 17
        if spieler.rolle == "TOP" and zeit >= 815:
            cd -= 30.0
        return cd
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


@lru_cache(maxsize=1)
def dash_champions() -> frozenset[str]:
    """Wer einen eigenen Dash, Sprung, Blink oder Teleport hat (wissen/dashes.toml, von Hand geprueft, dazu
    blinks.toml). Ein Sprung auf Minimap oder Bildschirm zaehlt bei ihnen nicht als Flash - lieber weniger Timer als
    falsche (Qualitaetsrunde 2, Entscheidung 3 Weg 1: 6 von 7 gemessenen Spruengen waren Dash-Champions)."""
    from . import wissen
    return frozenset(wissen.lade("dashes").get("ids", [])) | frozenset(blink_champions())


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
        if zauber == "R" and getattr(spieler, "level", 6) < 6:
            return None   # vor Level 6 gibt es keine Ult (Live 26.09., 1:47: "Heimerd / r" gelesen = Ult weg)
        schl = (spieler.name, zauber)
        alt = self.timer.get(schl)
        if alt and alt.zurueck > zeit and abs(alt.seit - zeit) < 60:
            if quelle == "Chat" and alt.quelle == "Minimap":
                alt.quelle = "Chat"  # Chat bestaetigt die Minimap
            return None
        if alt and alt.zurueck > zeit and quelle == "Minimap":
            # Flash ist laut Timer noch weg - ein neuer Sprung kann kein Flash sein (Camille-Partie 26.09.:
            # Rumble "flasht" 11:36, sein Flash war seit 7:16 weg). Lieber stumm als falsch.
            return None
        t = Timer(spieler.name, spieler.champion, zauber, zurueck or zeit + cooldown(zauber, spieler, zeit), quelle, zeit)
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
_STEMPEL = re.compile(r"^\s*\[?(\d{1,2})\s?[:.]\s?(\d{2})\b")


CHAT_FRISCH = 20.0   # Sekunden: so alt darf eine Chatzeile beim Lesen hoechstens sein


def chat_stempel(zeile: str) -> float | None:
    """Der Zeitstempel vorn in Sekunden, oder None (keiner oder unlesbar)."""
    m = _STEMPEL.match(zeile)
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def chat_zeit(zeile: str, gelesen: float) -> float | None:
    """Spielzeit, zu der die Zeile geschrieben wurde (Zeitstempel vorn, "04:48 Riven (Riven): ..."), wenn
    sie FRISCH ist (hoechstens CHAT_FRISCH vor dem Lesen) - sonst None, und die Zeile zaehlt nicht.
    Partie 6: der Chat blendet nach jedem Kill alte Zeilen wieder ein; der Leser las "02:13 ... Rumble hat
    Blitz benutzt" um 4:08 und 5:39 mit neuem Rauschen erneut - jedes Mal ein neuer Flash-Timer. Eine
    Zeile ohne lesbaren Stempel ist nicht zu datieren; der echte Ping wird ohnehin mehrmals gelesen."""
    if m := _STEMPEL.match(zeile):
        t = int(m.group(1)) * 60 + int(m.group(2))
        if 0 <= gelesen - t <= CHAT_FRISCH:
            return float(t)
    return None


def aus_chat(zeile: str, p) -> list[tuple[object, str, float | None]]:
    """Findet in einer Chatzeile (Champion, Zauber[, Rueckkehr]) fuer Gegner.

    "[Team] Schizoid Nevir (Riven): Urgot Blitz" -> Urgot, Flash.
    Der Absender steht vor dem Doppelpunkt; gesucht wird nur in der Nachricht.
    Eine Uhrzeit in der Nachricht wird als Rueckkehrzeit gelesen, wenn sie in
    der Zukunft liegt (manche Pings nennen sie)."""
    import difflib
    rest = re.sub(r"^\s*\[?\d{1,2}\s?[:.]\s?\d{2}\]?\s*", "", zeile)   # Zeitstempel vorn (Chat-Einstellung)
    nachricht = rest.split(":", 1)[1] if ":" in rest else rest
    # "Wukong — Blitz" (Strich) ist Carlos' Art, einen verbrauchten Zauber zu pingen - er zaehlt wie
    # "hat Blitz benutzt" (Partie 7: alle Pings so; kurz ignoriert, reagierte der Coach "extrem spaet").
    # Der Rumble-Fehler aus Partie 6 waren wieder eingeblendete ALTE Zeilen (chat_zeit), nicht das Format.
    woerter = re.findall(r"[a-zäöüß']+", nachricht.lower())
    woerterbuch = _woerter()
    zauber = [woerterbuch[w] for w in woerter if w in woerterbuch and (w != "r" or len(woerter) <= 3)]
    if not zauber:
        return []
    namen = {}
    for s in p.gegner():
        for n in {s.champion.lower(), s.champion_id.lower()}:
            namen[n.replace(" ", "").replace("'", "")] = s
    kandidaten = woerter + [a + b for a, b in zip(woerter, woerter[1:])]
    gegner = None
    # ein einzelnes "r" ist schnell falsch gelesen ("Heimerd / r" war "Heimerdinger - Blitz"): dann muss der
    # Name sicher sein
    nur_r = all(w == "r" for w in woerter if w in woerterbuch)
    for w in kandidaten:
        if treffer := difflib.get_close_matches(w.replace("'", ""), list(namen), n=1,
                                                cutoff=0.95 if nur_r else 0.8):
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
