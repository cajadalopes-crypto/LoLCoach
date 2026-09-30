"""Welche Aktion des Gehirns ein Kommando meint (Auftrag 035).

Das Gehirn (werkzeuge/challenger/gehirn.py) kennt die Aktionen aus Phase 1 (AKTIONEN: Back, Objective, TP, Rotation,
Split, Gruppe, Jungle, Lane, Warten, Unterwegs) mit Ziel (Objective:Drache, Rotation:mid ...). Die 111 Entscheidungen
sagen Saetze. Diese Tafel verbindet beides - einmal, fuer zwei Zwecke:

- Reihenfolge (035, Teil 0): nach der Gefahr ordnet der Aktionswert des Gehirns (`hirn.wert(aktion, ziel)`); hat ein
  Kommando keine Aktion (Sicht, Warnung, Kauf, Ping ...) oder das Gehirn keinen Wert dafuer, gilt sein fester Wert.
- Challenger-Treue (035, Teil 2, werkzeuge/challenger/treue.py): ein Treffer ist, wenn die Aktion des Kommandos die
  Aktion des Spielers ist.

Richtung zaehlt: "Noch nicht back" ist Lane, "Kein TP" ist bleiben (Lane), "Gib den Drachen" ist nicht Objective.
"""
from __future__ import annotations

import re

from .kommando import Kommando

# Monster im Satz -> Ziel des Gehirns (phase1.MONSTER)
MONSTER = (("elder", "Elder"), ("ältest", "Elder"), ("aeltest", "Elder"), ("seele", "Drache"), ("drache", "Drache"),
           ("baron", "Baron"), ("herold", "Herold"), ("larven", "Larven"))
ZONE = (("mid", "mid"), ("mitte", "mid"), ("top", "oben"), ("oben", "oben"), ("bot", "unten"), ("unten", "unten"))
NEIN = re.compile(r"^\W*(nicht|kein\w*|noch nicht|gib\b|lass\b|abbrechen|zu spät|zu spaet|aufgeben)", re.I)

# Nummer -> Aktion (oder Funktion (Kommando, Text) -> Aktion). None: keine Aktion des Gehirns (Sicht, Warnung, Kauf,
# Ping, Spielstand) - dann zaehlt der feste Wert, und fuer die Treue ist das Kommando "ohne Aktion".
FEST = {
    # B1 Sicht: keine eigene Aktion (der Ward ist Teil dessen, was man ohnehin tut)
    **{f"S{i}": None for i in range(1, 15)},
    "S3": "Lane", "S4": "Jungle",
    # B2 Jungler und Warnungen: die Handlung im Satz
    "J1": None, "J2": "Lane", "J3": "Lane", "J4": "Lane", "J5": "Lane", "J6": "Lane", "J7": None, "J8": None,
    "J9": None, "J10": "Lane", "J11": "Warten", "J12": "Lane", "J13": "Unterwegs", "J14": "Lane",
    # B3 Wellen
    "W1": "Lane", "W2": "Lane", "W3": "Back", "W4": "Lane", "W5": "Lane", "W6": "Objective", "W7": "Lane",
    "W8": "Objective", "W9": "Lane", "W10": "Lane", "W11": "Split", "W12": "Lane", "W13": "Objective", "W14": None,
    # B4 Back und Kauf
    "B1": "Back", "B2": "Back", "B3": "Lane", "B4": "Back", "B5": "Back", "B6": None, "B7": None, "B8": None,
    "B9": None,
    # B5 TP
    "T1": "TP", "T2": "TP", "T3": "Lane", "T4": "TP", "T5": "TP", "T6": "TP", "T7": "TP", "T8": "Lane", "T9": None,
    # B6 Roams
    "R1": "Rotation", "R2": "Unterwegs", "R3": "Objective", "R4": "Objective", "R5": "Lane", "R6": "Rotation",
    "R7": None, "R8": "Lane", "R9": "Jungle", "R10": "Jungle",
    # B7 Objectives
    "O1": "Objective", "O2": "Objective", "O3": "Objective", "O4": "Objective", "O5": "Warten", "O6": "Objective",
    "O7": "Objective", "O8": "Objective", "O9": "Gruppe", "O10": "Split", "O11": "Lane", "O12": "Objective",
    # B8 Kaempfe als Makro
    "K1": "Gruppe", "K2": "Warten", "K3": "Gruppe", "K4": "Objective", "K5": "Warten", "K6": "Unterwegs",
    "K7": "Lane",
    # B9 Spaetphase
    "M1": "Rotation", "M2": "Split", "M3": "Gruppe", "M4": "Gruppe", "M5": "Split", "M6": "Split", "M7": "Split",
    "M8": "Gruppe", "M9": "Warten", "M10": None,
    # B10, B11: Spielstand und Pings - keine eigene Handlung
    "V1": None, "V2": None, "V3": "Lane", "V4": "Objective", "V5": "Lane",
    "P1": None, "P2": None, "P3": "Unterwegs", "P4": None,
    # B12 Warten
    "Z1": "Warten", "Z2": "Lane", "Z3": None,            # Z3: die haeufigste High-Elo-Aktion - aus dem Gehirn
    "G0": "Lane",                                       # Grund-Anweisung (einbau.takt.grund_kommando)
}
# Kommandos, deren Satz auch die Gegenrichtung sagen kann ("Drache bestreiten" / "Gib den Drachen")
GEGEN = {"O1": "Lane", "K1": "Lane", "K3": "Lane", "T1": "Lane", "B3": "Lane", "R1": "Lane", "O4": "Lane",
         "M2": "Gruppe", "K2": "Warten"}      # W13 "Lass die Welle und geh" heisst: zum Objective
# Z3 nennt die Aktion im Text (takt.AKTION_DE)
Z3_TEXT = (("Back", "Back"), ("Bleib an der Welle", "Lane"), ("Geh zu deinem Team", "Gruppe"), ("Nimm Camps", "Jungle"),
           ("Druck die Seitenwelle", "Split"), ("Bleib, wo du bist", "Warten"), ("Halte den TP", "TP"),
           ("Wechsel die Seite", "Rotation"), ("Geh zum Objective", "Objective"), ("Geh", "Unterwegs"))


def _monster(text: str) -> str | None:
    t = text.lower()
    return next((z for w, z in MONSTER if w in t), None)


def _zone(text: str) -> str | None:
    t = text.lower()
    return next((z for w, z in ZONE if re.search(rf"\b{w}", t)), None)


def aktion(k: Kommando) -> tuple[str, str] | None:
    """(Aktion, Ziel) des Gehirns fuer ein Kommando - Ziel "" wo es keins gibt. None: keine Aktion."""
    if k.id == "Z3":
        a = next((a for w, a in Z3_TEXT if k.tu.startswith(w)), None)
        return None if a is None else (a, "")
    a = FEST.get(k.id)
    if a is None:
        return None
    if k.id in GEGEN and NEIN.search(k.tu):
        a = GEGEN[k.id]
    if a == "Objective":
        m = _monster(f"{k.tu} {k.weil}")
        return ("Objective", m) if m else ("Objective", "")
    if a == "Rotation":
        z = _zone(k.tu)
        return ("Rotation", z or "")
    return (a, "")


def wert(k: Kommando, hirn) -> float | None:
    """Aktionswert des Gehirns fuer dieses Kommando (Siegchance-Punkte in 120 s), None ohne Aktion oder Wert."""
    if hirn is None or not getattr(hirn, "optionen", None):
        return None
    a = aktion(k)
    if a is None:
        return None
    akt, ziel = a
    o = hirn.option(akt, ziel) if ziel else None
    if o is None:
        # ohne passendes Ziel: die beste Option dieser Aktion (Objective:Drache fuer "Objective", Rotation:mid ...)
        o = max((x for x in hirn.optionen if x[0] == akt), key=lambda x: x[2], default=None)
    return None if o is None else float(o[2])


# --- Plan-Art (Auftrag 035, Teil 0): die Messwerkzeuge (Szenarien, Nachspiele, Kennzahlen) pruefen Plan-Arten des
# alten Kerns (kern/handlung.py: BACK_JETZT, WELLE_REIN_UND_BACK, FARMEN ...). Mit --kern makro bekommt jedes Kommando
# die Art, der es entspricht - so bleiben die Szenarien pruefbar, und `--kern neu` bleibt vergleichbar.
# "SICHT" (Wards) und "INFO" (Warnung, Spielstand, Ping) gab es im alten Kern nicht als Plan.
ART = {
    **{f"S{i}": "SICHT" for i in range(1, 15)}, "S3": "WELLE_DRUECKEN", "S11": "HALTEN",
    "J1": "INFO", "J2": "WELLE_HALTEN", "J3": "PLATTEN", "J4": "ZURUECK", "J5": "ZURUECK", "J6": "PLATTEN",
    "J7": "INFO", "J8": "INFO", "J9": "INFO", "J10": "ZURUECK", "J11": "HALTEN", "J12": "HALTEN", "J13": "ZUR_GRUPPE",
    "J14": "RAUS",
    "W1": "WELLE_HALTEN", "W2": "STAPELN", "W3": "WELLE_REIN_UND_BACK", "W4": "WELLE_DRUECKEN", "W5": "WELLE_HALTEN",
    "W6": "VORBEREITEN_OBJECTIVE", "W7": "WELLE_DRUECKEN", "W8": "ANLAUFEN", "W9": "UNTER_TURM_FARMEN",
    "W10": "PLATTEN", "W11": "SEITENWELLE", "W12": "STAPELN", "W13": "ANLAUFEN", "W14": "INFO",
    "B1": "BACK_JETZT", "B2": "BACK_JETZT", "B3": "PLATTEN", "B4": "BACK_JETZT", "B5": "BACK_JETZT", "B6": "WOHIN",
    "B7": "KAUFEN", "B8": "KAUFEN", "B9": "KAUFEN",
    "T1": "WOHIN_TP_LANE", "T2": "TP_SPIEL", "T3": "FARMEN", "T4": "TP_SPIEL", "T5": "TP_SPIEL", "T6": "TP_SPIEL",
    "T7": "TP_SPIEL", "T8": "FARMEN", "T9": "INFO",
    "R1": "HILFE", "R2": "ZUR_GRUPPE", "R3": "ANLAUFEN", "R4": "ANLAUFEN", "R5": "FARMEN", "R6": "WOHIN",
    "R7": "WOHIN", "R8": "FARMEN", "R9": "WOHIN", "R10": "WOHIN",
    "O1": "BESTREITEN", "O2": "NEHMEN", "O3": "NEHMEN", "O4": "NEHMEN", "O5": "RAUS", "O6": "NEHMEN",
    "O7": "VORBEREITEN_OBJECTIVE", "O8": "NEHMEN", "O9": "MIT_GRUPPE", "O10": "TAUSCHEN", "O11": "ZURUECK",
    "O12": "NEHMEN",
    "K1": "ANNEHMEN", "K2": "HALTEN", "K3": "HILFE", "K4": "NEHMEN", "K5": "HALTEN_UNTER_TURM", "K6": "HILFE",
    "K7": "HALTEN",
    "M1": "WOHIN", "M2": "SEITENWELLE", "M3": "ZUR_GRUPPE", "M4": "MIT_GRUPPE", "M5": "SEITENWELLE",
    "M6": "SEITENWELLE", "M7": "SEITENWELLE", "M8": "DRUECKEN", "M9": "HALTEN_UNTER_TURM", "M10": "INFO",
    "V1": "INFO", "V2": "INFO", "V3": "WELLE_HALTEN", "V4": "NEHMEN", "V5": "HALTEN",
    "P1": "INFO", "P2": "INFO", "P3": "HILFE", "P4": "INFO",
    "Z1": "HALTEN", "Z2": "PLATTEN", "G0": "FARMEN",
}
# Gegenrichtung ("Gib den Drachen", "Nicht kaempfen", "Kein TP" ...)
ART_GEGEN = {"O1": "ABGEBEN_TAUSCHEN", "K1": "ZURUECK", "K3": "FARMEN", "T1": "FARMEN", "R1": "FARMEN", "O4": "FARMEN",
             "K2": "HALTEN"}
ART_DER_AKTION = {"Back": "BACK_JETZT", "Lane": "FARMEN", "Gruppe": "ZUR_GRUPPE", "Jungle": "WOHIN",
                  "Split": "SEITENWELLE", "Warten": "HALTEN", "TP": "TP_SPIEL", "Rotation": "WOHIN",
                  "Objective": "ANLAUFEN", "Unterwegs": "WOHIN"}


def plan_art(k: Kommando) -> str:
    """Die Plan-Art des alten Kerns, der ein Kommando entspricht (fuer Szenarien und Nachspiele)."""
    if k.id == "Z3":
        a = aktion(k)
        return ART_DER_AKTION.get(a[0], "HALTEN") if a else "HALTEN"
    if k.id == "G0":
        t = k.tu.lower()
        return "ZURUECK" if "turm" in t else "KAUFEN" if "respawn" in t else "FARMEN"
    if k.id in ART_GEGEN and NEIN.search(k.tu):
        return ART_GEGEN[k.id]
    if k.id == "W1" and re.search(r"\b(push|drück|druck)", k.tu, re.I):
        return "WELLE_DRUECKEN"
    return ART.get(k.id, "INFO")
