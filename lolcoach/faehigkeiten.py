"""Faehigkeitsschaden fuer jeden Champion aus den Spieldaten (CommunityDragon), nicht nur fuer Carlos' drei.

Reasoning #1 ("reicht mein Full-Combo-Schaden jetzt fuer den Kill?") hatte Zahlen nur fuer Riven, Camille und Graves
(`combo.WIKI`, von Hand aus dem Wiki). Die Formeln stehen aber fuer alle Champions in den Spieldaten: je Faehigkeit
Grundwerte je Rang (`DataValues`) und Rechnungen (`mSpellCalculations`: Grundwert + Anteil AD/AP/Leben ...). Welche
Rechnung Schaden ist und welcher Art (normal/magisch/wahr), steht im Tooltip (`<physicalDamage>{{ TotalDamage }}`).
`werkzeuge/faehigkeiten_holen.py` zieht das einmal in `wissen/faehigkeiten/cdragon.json` (Stand: `stand.toml`); hier wird nur gerechnet.

Was NICHT drinsteht und deshalb fehlt - alles zur vorsichtigen Seite (die Zahl ist eher zu niedrig):
  - wie oft eine Faehigkeit trifft (Rivens Q dreimal, Katarinas Dolche): gezaehlt wird ein Treffer,
  - Schaden nach Stapeln, fehlendem Leben des Ziels, Abstand: Teile, die das Ziel brauchen, zaehlen 0,
  - Runen und Item-Aktive.
Deshalb nutzt der Coach die Zahl nur in EINE Richtung: reicht schon diese Untergrenze, ist es sicher.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATEI = Path(__file__).resolve().parent.parent / "wissen" / "faehigkeiten" / "cdragon.json"

# mStat der Spieldaten -> Schluessel in `werte` (0 fehlt in den Daten = Faehigkeitsstaerke)
STAT = {0: "ap", 1: "ruestung", 2: "ad", 3: "tempo_angriff", 5: "mr", 6: "lauftempo", 11: "leben_max", 12: "leben"}
FORMEL = {0: "", 1: "_basis", 2: "_bonus"}     # mStatFormula: gesamt, Grundwert, Bonus (aus Items/Stufen)
ART = {"physicalDamage": "physisch", "magicDamage": "magisch", "trueDamage": "wahr"}


@lru_cache(maxsize=1)
def daten() -> dict:
    try:
        return json.loads(DATEI.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def kann(champion_id: str) -> bool:
    return champion_id in daten()


def _stat(werte: dict, teil: dict) -> float:
    name = STAT.get(int(teil.get("mStat", 0)))
    if name is None:
        return 0.0
    return float(werte.get(name + FORMEL.get(int(teil.get("mStatFormula", 0)), ""), 0.0) or 0.0)


def _teil(t, fa: dict, rang: int, level: int, werte: dict, tiefe: int = 0) -> float:
    """Ein Formelteil. Unbekannte Teile (Stapel, Ziel-Leben, Abstand ...) zaehlen 0 - die Untergrenze."""
    if tiefe > 8 or not isinstance(t, dict):
        return 0.0
    art = t.get("__type", "")
    dv = fa.get("werte", {})

    def wert(name):
        v = dv.get(name)
        return float(v[min(rang, len(v) - 1)]) if v else 0.0

    def unter(x):
        return _teil(x, fa, rang, level, werte, tiefe + 1)

    if art == "NamedDataValueCalculationPart":
        return wert(t.get("mDataValue"))
    if art == "StatByNamedDataValueCalculationPart":
        return _stat(werte, t) * wert(t.get("mDataValue"))
    if art == "StatByCoefficientCalculationPart":
        return _stat(werte, t) * float(t.get("mCoefficient", 0.0))
    if art == "StatBySubPartCalculationPart":
        return _stat(werte, t) * unter(t.get("mSubpart"))
    if art == "NumberCalculationPart":
        return float(t.get("mNumber", 0.0))
    if art == "ByCharLevelInterpolationCalculationPart":
        a, b = float(t.get("mStartValue", 0.0)), float(t.get("mEndValue", 0.0))
        return a + (b - a) * (max(1, min(18, level)) - 1) / 17
    if art == "ByCharLevelBreakpointsCalculationPart":
        v = float(t.get("mLevel1Value", 0.0))
        for bp in t.get("mBreakpoints", []):
            if level >= int(bp.get("mLevel", 99)):
                v += float(bp.get("{d5fd07ed}", bp.get("mBonusPerLevelAtAndAfter", 0.0))) * (level - int(bp["mLevel"]) + 1) \
                    if "mBonusPerLevelAtAndAfter" in bp else float(bp.get("mAdditionalBonusAtThisLevel", 0.0))
        return v
    if art == "EffectValueCalculationPart":
        eff = fa.get("effekte", [])
        i = int(t.get("mEffectIndex", 1)) - 1
        return float(eff[i][min(rang, len(eff[i]) - 1)]) if 0 <= i < len(eff) and eff[i] else 0.0
    if art == "SumOfSubPartsCalculationPart":
        return sum(unter(x) for x in t.get("mSubparts", []))
    if art == "ProductOfSubPartsCalculationPart":
        return unter(t.get("mPart1")) * unter(t.get("mPart2"))
    if art == "ClampSubPartsCalculationPart":
        s = sum(unter(x) for x in t.get("mSubparts", []))
        return max(float(t.get("mFloor", -1e9)), min(float(t.get("mCeiling", 1e9)), s))
    return 0.0


def rechnung(fa: dict, name: str, rang: int, level: int, werte: dict, tiefe: int = 0) -> float:
    """Eine benannte Rechnung einer Faehigkeit (Summe ihrer Teile, mal ihrem Faktor)."""
    r = fa.get("rechnungen", {}).get(name)
    if not isinstance(r, dict) or tiefe > 4:
        return 0.0
    if r.get("__type") == "GameCalculationModified":
        faktor = _teil(r.get("mMultiplier"), fa, rang, level, werte) if r.get("mMultiplier") else 1.0
        return faktor * rechnung(fa, r.get("mModifiedGameCalculation", ""), rang, level, werte, tiefe + 1)
    summe = sum(_teil(t, fa, rang, level, werte) for t in r.get("mFormulaParts", []))
    if r.get("mMultiplier"):
        summe *= _teil(r["mMultiplier"], fa, rang, level, werte)
    return summe


def schaden(champion_id: str, slot: str, rang: int, level: int, werte: dict) -> list[tuple[float, str]]:
    """[(Schaden vor Resistenzen, Art)] einer Faehigkeit auf Rang `rang` (1..5, R 1..3) - je Tooltip-Schadensteil."""
    fa = daten().get(champion_id, {}).get(slot)
    if not fa or rang <= 0:
        return []
    return [(rechnung(fa, name, rang, level, werte), art) for name, art in fa.get("schaden", [])]
