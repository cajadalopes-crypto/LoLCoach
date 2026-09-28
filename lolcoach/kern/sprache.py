"""Konkrete Sprache (Auftrag 008, A2) - eine Regel fuer Szenarien, Tests und Kennzahlen, und die Turm-Namen dazu.

Carlos in 101426: "Zu welchem Bot Tier 2 - zu meinem oder zu dem des Gegners?", "Raus zum Turm ist schwammig",
"Was soll 'Mid-Welle' heissen, nichtssagend". Deshalb:

  - jeder Turm mit Besitzer und Lage, ohne "Tier": "dein aeusserer Mid-Turm", "euer innerer Bot-Turm",
    "ihr Inhibitor-Turm unten"; dein = deine Lane, euer = die anderen Lanes deines Teams, ihr = die Gegner
  - Rueckzug: "Zurueck unter deinen Mid-Turm"; im Kampf "Raus, zu deinem Turm!" / "Raus, zu Kayn!"
  - eine Welle nie allein: "Dann auf Mid, deine Welle ist gleich an deinem Turm." - nie "Dann Mid-Welle."
"""
from __future__ import annotations

import re

BESITZER = frozenset(("dein", "deine", "deinen", "deinem", "deines", "deiner", "euer", "eure", "euren", "eurem",
                      "eures", "eurer", "ihr", "ihre", "ihren", "ihrem", "ihres", "ihrer"))
_TURM = re.compile(r"[\wÄÖÜäöüß-]*(?:Turm|Türme|Tuerme)(?![\wÄÖÜäöüß-])")
_TIER = re.compile(r"\bTier\b|Tier-\d")
_DANN = re.compile(r"^Dann [\wÄÖÜäöüß'-]+(?: [\wÄÖÜäöüß'-]+){0,2}[.!]?$")
_WELLE_ALLEIN = re.compile(r"^(?:Dann |Geh |Zur |Auf )?(?:zur |auf die |die |deine )?(?:Top|Mid|Bot)-Welle[.!]?$")
_SATZ = re.compile(r"(?<=[.!?])\s+")
_FRAGE = re.compile(r"^„[^“]*“\s*[–-]\s*")


def saetze(text: str) -> list[str]:
    return [s.strip() for s in _SATZ.split(text or "") if s.strip()]


def vage_formen(text: str) -> list[str]:
    """Verstoesse gegen A2 in einem gesprochenen Text (leer = konkret). Eine Antwort "„Frage“ – Antwort" wird nur in
    ihrer Antwort geprueft - Carlos darf "Tier 2" sagen."""
    text = _FRAGE.sub("", text or "")
    aus = []
    if _TIER.search(text):
        aus.append("Tier")
    if "Raus, zum Turm" in text or "Raus zum Turm" in text:
        aus.append("Raus zum Turm")
    for s in saetze(text):
        if _DANN.match(s) and len(s.split()) <= 4:
            aus.append(f"nur Ort: {s}")
        elif _WELLE_ALLEIN.match(s):
            aus.append(f"Welle allein: {s}")
    for m in _TURM.finditer(text):
        davor = re.findall(r"[\wÄÖÜäöüß]+", text[max(0, m.start() - 40):m.start()])[-3:]
        if not any(w.lower() in BESITZER for w in davor):
            aus.append(f"Turm ohne Besitzer: {' '.join(davor + [m.group(0)])}")
    return aus


# Buch 4, 4 (Auftrag 008): verbotene Gruende - Floskeln, Tautologien, Gruende ohne Beobachtung
FLOSKELN = ("bis sich etwas öffnet", "danach rechne ich neu", "ist gerade keine option")
TAUTOLOGIEN = ("weil es sich lohnt", "lohnt sich", "das ist gut", "weil es besser ist", "ist einfach besser")


def verbotene_gruende(text: str) -> list[str]:
    """Verstoesse gegen Buch 4, 4 in einem gesprochenen Text: Floskel, Tautologie, "dort nimmt sie sonst niemand" ohne
    zu sagen, wo dein Team ist."""
    t = _FRAGE.sub("", text or "").lower()
    aus = [f"Floskel: {f}" for f in FLOSKELN if f in t]
    aus += [f"Tautologie: {f}" for f in TAUTOLOGIEN if f in t]
    for s in saetze(t):
        if "sonst niemand" in s and not any(w in s for w in ("team", "euch", "mitspieler")):
            aus.append(f"ohne Beobachtung: {s}")
    return aus


# --- Turm-Namen -------------------------------------------------------------------------------------------------

_ADJ = {"aussen": "äußer", "innen": "inner"}
_POSS = {"dein": ("dein", "deinen", "deinem"), "euer": ("euer", "euren", "eurem"), "ihr": ("ihr", "ihren", "ihrem")}
FALL = {"nom": 0, "akk": 1, "dat": 2}


def besitzer(team: str | None, lane: str | None, mein_team: str | None, meine_lane: str | None) -> str:
    """dein (dein Team, deine Lane), euer (dein Team, andere Lane), ihr (Gegner)."""
    if team is not None and mein_team is not None and team != mein_team:
        return "ihr"
    return "dein" if lane is not None and lane == meine_lane else "euer"


def turm(poss: str, lane: str | None, stufe: str, fall: str = "akk") -> str:
    """"deinen äußeren Mid-Turm", "ihrem Mid-Inhibitor-Turm", "ihr Nexus-Turm" - stufe aussen/innen/Inhib/Nexus-Turm."""
    p = _POSS[poss][FALL[fall]]
    if stufe in _ADJ:
        adj = _ADJ[stufe] + ("er" if fall == "nom" else "en")
        return f"{p} {adj} {lane}-Turm" if lane else f"{p} {adj} Turm"
    if stufe in ("Inhib", "Inhibitor", "Inhibitor-Turm"):
        return f"{p} {lane}-Inhibitor-Turm" if lane else f"{p} Inhibitor-Turm"
    return f"{p} Nexus-Turm"


# "ihren inneren Top-Turm" (Akkusativ, so heissen die Ziele) -> Dativ / Nominativ
_AKK_DAT = {"ihren": "ihrem", "deinen": "deinem", "euren": "eurem", "den": "dem"}
_AKK_NOM = {"ihren": "ihr", "deinen": "dein", "euren": "euer", "den": "der"}


def dativ(name: str) -> str:
    """"ihren inneren Top-Turm" -> "ihrem inneren Top-Turm" ("zu ...", "an ...")."""
    erstes, _, rest = name.partition(" ")
    return f"{_AKK_DAT[erstes]} {rest}" if erstes in _AKK_DAT and rest else name


def nominativ(name: str) -> str:
    """"ihren inneren Top-Turm" -> "ihr innerer Top-Turm", "ihren Nexus-Turm" -> "ihr Nexus-Turm"."""
    teile = name.split(" ")
    if teile[0] in _AKK_NOM:
        teile[0] = _AKK_NOM[teile[0]]
        if len(teile) > 2 and teile[1].endswith("eren"):
            teile[1] = teile[1][:-1] + "r"                   # äußeren -> äußerer, inneren -> innerer
    return " ".join(teile)


def gross(s: str) -> str:
    return s[:1].upper() + s[1:]


def unter(ort: str) -> str:
    """Der Rueckzug zu einem sicheren Ort (Dativ aus bewertung.sicherer_ort) als Ziel: "unter deinen Mid-Turm" (der
    aeussere ist immer dein vorderster - das Wort faellt weg), "in deine Basis", "zu Kayn und Yunara"."""
    erstes, _, rest = ort.partition(" ")
    if erstes in ("deinem", "eurem") and rest.endswith("Turm"):
        rest = rest.removeprefix("äußeren ")
        return f"unter {'deinen' if erstes == 'deinem' else 'euren'} {rest}"
    if ort == "deiner Basis":
        return "in deine Basis"
    return f"zu {ort}"


SEITE_DER_LANE = {"Top": "oben", "Mid": "in der Mitte", "Bot": "unten"}


def kartenseite(pos) -> str:
    """oben / unten / in der Mitte (Spiel-Einheiten, blaue Basis unten links) - wie basis._seite."""
    d = pos[1] - pos[0]
    return "oben" if d > 2000 else "unten" if d < -2000 else "in der Mitte"


def team_grund(m, lane: str) -> str | None:
    """Buch 4, 4 (verbotene Gruende): "dort nimmt sie sonst niemand" nur mit dem, wo dein Team ist - "dein Team ist
    unten" (>= 2 Mitspieler auf einer Seite) oder "keiner von euch ist oben". Steht einer von euch auf dieser Seite, ist
    der Satz falsch: None."""
    seite = SEITE_DER_LANE.get(lane)
    freunde = [wo for s, wo in (getattr(m, "mitspieler", None) or []) if wo is not None and not s.tot]
    if seite is None or not freunde:
        return None
    seiten = [kartenseite(wo) for wo in freunde]
    if seite in seiten:
        return None
    haupt = max(set(seiten), key=seiten.count)
    return f"dein Team ist {haupt}" if seiten.count(haupt) >= 2 else f"keiner von euch ist {seite}"


def an(ort: str) -> str:
    """Stehen am sicheren Ort: "unter deinem Mid-Turm", "in deiner Basis", "bei Kayn und Yunara"."""
    erstes, _, rest = ort.partition(" ")
    if erstes in ("deinem", "eurem") and rest.endswith("Turm"):
        return f"unter {erstes} {rest.removeprefix('äußeren ')}"
    if ort == "deiner Basis":
        return "in deiner Basis"
    return f"bei {ort}"
