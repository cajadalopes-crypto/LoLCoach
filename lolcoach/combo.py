"""Full-Combo-Schaden fuer Carlos' Champions: reicht er JETZT fuer den Kill?

Reasoning #1: "Exakte mathematische Einschaetzung: Reicht mein Full-Combo-Schaden jetzt fuer den Kill unter
Beruecksichtigung von Armor?" Gerechnet mit dem, was sicher bekannt ist:
  - dein Angriffsschaden, Durchdringung und Toedlichkeit (Live-API), deine Faehigkeitsraenge (Live-API) und ob die
    Faehigkeiten bereit sind (HUD),
  - seine Ruestung (Data Dragon: Grundwert nach Level + Item-Ruestung), sein Leben (Balken im Bild x Max-Leben).
Werte der Faehigkeiten aus dem offiziellen Wiki (wiki.leagueoflegends.com, abgerufen 26.09.2026): Riven V26.15,
Camille V26.19, Graves V26.17. Nur diese drei - Carlos' Champions; fuer alle anderen rechnet der Coach nicht
(lieber keine Zahl als eine falsche).

Vereinfachungen, alle zur vorsichtigen Seite: keine Krits, keine Items mit Aktiv-Schaden, keine Runen (Eroberer,
Elektrisieren), Camilles Q2 ganz als normaler Schaden (in Wahrheit teils wahrer Schaden), R-Schaden nur, wenn die
Ult bereit ist. Das Ergebnis ist deshalb eher zu niedrig als zu hoch.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from . import ddragon
from .rechnung import wachstum

WIKI = {
    "Riven": {
        "passiv": (0.30, 0.4676),                       # +% AD je Ladung, Level 1 .. 18
        "q": [45, 75, 105, 135, 165], "q_bonus": [0.60, 0.65, 0.70, 0.75, 0.80],    # je Cast, drei Casts
        "w": [65, 95, 125, 155, 185], "w_bonus": 1.00,
        "r_ad": 0.20,                                    # R aktiv: +20 % AD
        "r2_min": [100, 150, 200], "r2_min_bonus": 0.55, "r2_max": [300, 450, 600], "r2_max_bonus": 1.65,
    },
    "Camille": {
        "q1": [0.20, 0.25, 0.30, 0.35, 0.40], "q2": [0.40, 0.50, 0.60, 0.70, 0.80],    # +% AD auf den Treffer
        "w": [60, 85, 110, 135, 160], "w_bonus": 0.60,
        "e": [60, 90, 120, 150, 180], "e_bonus": 0.75,
    },
    "Graves": {
        "schuss": (1.4, 2.0),                            # ein Schuss aus der Naehe, alle vier Kugeln: x AD (Level 1 .. 18)
        "q1": [50, 75, 100, 125, 150], "q1_bonus": 0.55,
        "q2": [80, 125, 170, 215, 260], "q2_bonus": [0.45, 0.60, 0.75, 0.90, 1.05],
        "r": [275, 425, 575], "r_bonus": 1.50,
    },
}


def kann(champion_id: str) -> bool:
    from . import faehigkeiten
    return champion_id in WIKI or faehigkeiten.kann(champion_id)


def genau(champion_id: str) -> bool:
    """Von Hand geprueft (Treffer je Faehigkeit, Passiv, Ult-Verstaerkung). Alle anderen rechnen aus den Spieldaten
    eine Untergrenze (ein Treffer je Faehigkeit) - die gilt nur, wenn sie schon reicht."""
    return champion_id in WIKI


def mr(s) -> float:
    """Magieresistenz eines Gegners: Grundwert nach Level (Data Dragon) + Items."""
    st = (ddragon.champions().get(s.champion_id) or {}).get("stats", {})
    r = wachstum(float(st.get("spellblock", 30)), float(st.get("spellblockperlevel", 1.3)), s.level)
    it = ddragon.items()
    return r + sum(float(it.get(i, {}).get("stats", {}).get("FlatSpellBlockMod", 0.0)) for i in s.items)


def _eigene_werte(champion_id: str, level: int, werte: dict) -> dict:
    """Deine Werte aus der Live-API, aufgeteilt in Grundwert und Bonus (fuer die Formeln der Spieldaten)."""
    st = (ddragon.champions().get(champion_id) or {}).get("stats", {})
    aus = {}
    for name, api, basis, je in (("ad", "attackDamage", "attackdamage", "attackdamageperlevel"),
                                 ("ruestung", "armor", "armor", "armorperlevel"),
                                 ("mr", "magicResist", "spellblock", "spellblockperlevel"),
                                 ("leben_max", "maxHealth", "hp", "hpperlevel")):
        gesamt = float(werte.get(api) or 0.0)
        b = wachstum(float(st.get(basis, 0.0)), float(st.get(je, 0.0)), level)
        aus.update({name: gesamt, name + "_basis": b, name + "_bonus": max(0.0, gesamt - b)})
    ap = float(werte.get("abilityPower") or 0.0)
    aus.update(ap=ap, ap_basis=0.0, ap_bonus=ap, leben=float(werte.get("currentHealth") or 0.0),
               tempo_angriff=float(werte.get("attackSpeed") or 0.0), lauftempo=float(werte.get("moveSpeed") or 0.0))
    return aus


# Uebliche Punktvergabe: die erste Faehigkeit ist auf 9 voll, die zweite auf 13, die dritte auf 18 (R auf 6/11/16)
PUNKTE = ((1, 4, 5, 7, 9), (2, 8, 10, 12, 13), (3, 14, 15, 17, 18))
LEXIKON = Path(__file__).resolve().parent.parent / "wissen" / "lexikon" / "champions"


@lru_cache(maxsize=256)
def reihenfolge(champion_id: str) -> tuple[str, str, str]:
    """Skill-Reihenfolge aus dem Lexikon ('- Skill: Q > E > W'), sonst die haeufigste (Q > E > W, 71 von 135)."""
    try:
        text = (LEXIKON / f"{champion_id}.md").read_text(encoding="utf-8")
    except OSError:
        text = ""
    m = re.search(r"^- Skill:\s*([QWE])\s*>\s*([QWE])\s*>\s*([QWE])", text, re.M)
    return (m.group(1), m.group(2), m.group(3)) if m and len({m.group(1), m.group(2), m.group(3)}) == 3 else ("Q", "E", "W")


def raenge_geschaetzt(champion_id: str, level: int) -> dict[str, int]:
    """Raenge eines Gegners aus seinem Level - die Live-API nennt nur deine."""
    aus = {t: sum(1 for x in stufen if x <= level) for t, stufen in zip(reihenfolge(champion_id), PUNKTE)}
    aus["R"] = (level >= 6) + (level >= 11) + (level >= 16)
    return aus


def _gegner_werte(s, anteil: float | None) -> dict:
    """Werte eines Gegners: Grundwerte nach Level (Data Dragon) + Items. Ohne Runen und Stapel - eher zu wenig."""
    st = (ddragon.champions().get(s.champion_id) or {}).get("stats", {})
    it = ddragon.items()

    def items(schl: str) -> float:
        return sum(float(it.get(i, {}).get("stats", {}).get(schl, 0.0)) for i in s.items)

    aus = {}
    for name, basis, je, item in (("ad", "attackdamage", "attackdamageperlevel", "FlatPhysicalDamageMod"),
                                  ("ruestung", "armor", "armorperlevel", "FlatArmorMod"),
                                  ("mr", "spellblock", "spellblockperlevel", "FlatSpellBlockMod"),
                                  ("leben_max", "hp", "hpperlevel", "FlatHPPoolMod")):
        b, bonus = wachstum(float(st.get(basis, 0.0)), float(st.get(je, 0.0)), s.level), items(item)
        aus.update({name: b + bonus, name + "_basis": b, name + "_bonus": bonus})
    ap = items("FlatMagicDamageMod")
    aus.update(ap=ap, ap_basis=0.0, ap_bonus=ap, leben=aus["leben_max"] * (anteil if anteil is not None else 1.0),
               lauftempo=float(st.get("movespeed", 340)))
    return aus


def gegner_schaden(s, meine_werte: dict, ult_bereit: bool = True, anteil: float | None = None) -> float | None:
    """Untergrenze fuer den Combo eines Gegners auf dich: je Faehigkeit ein Treffer (Raenge aus seinem Level und
    der Skill-Reihenfolge), ein normaler Angriff, nach DEINER Ruestung/Magieresistenz (API). Ohne Runen,
    Durchdringung, Stapel. Beschwoererzauber zaehlen nicht. None ohne Spieldaten."""
    from . import faehigkeiten
    if not faehigkeiten.kann(s.champion_id) or not meine_werte:
        return None
    L = max(1, s.level)
    st = _gegner_werte(s, anteil)
    arm, mag = float(meine_werte.get("armor") or 0.0), float(meine_werte.get("magicResist") or 0.0)
    teiler = {"physisch": 100 / (100 + max(0.0, arm)), "magisch": 100 / (100 + max(0.0, mag)), "wahr": 1.0}
    summe = st["ad"] * teiler["physisch"]      # ein Angriff: Garens Q enthaelt schon einen
    for t, r in raenge_geschaetzt(s.champion_id, L).items():
        if r <= 0 or (t == "R" and not ult_bereit):
            continue
        summe += sum(max(0.0, x) * teiler.get(art, 0.0) for x, art in faehigkeiten.schaden(s.champion_id, t, r, L, st))
    return summe


def _allgemein(ich, werte: dict, raenge: dict[str, int], bereit: dict[str, bool] | None, ziel) -> float | None:
    """Untergrenze aus den Spieldaten (faehigkeiten.py): je bereite Faehigkeit ein Treffer ihrer Tooltip-
    Schadensteile nach Ruestung/Magieresistenz, dazu ein normaler Angriff."""
    from . import faehigkeiten
    L = max(1, ich.level)
    st = _eigene_werte(ich.champion_id, L, werte)
    arm = max(0.0, ruestung(ziel) * float(werte.get("armorPenetrationPercent") or 1.0)
              - float(werte.get("physicalLethality") or 0.0))
    mag = max(0.0, mr(ziel) * float(werte.get("magicPenetrationPercent") or 1.0)
              - float(werte.get("magicPenetrationFlat") or 0.0) - float(werte.get("magicLethality") or 0.0))
    teiler = {"physisch": 100 / (100 + arm), "magisch": 100 / (100 + mag), "wahr": 1.0}
    summe = st["ad"] * teiler["physisch"]      # ein Angriff: Garens Q enthaelt schon einen
    for t in "QWER":
        r = int(raenge.get(t) or 0)
        if r <= 0 or (bereit is not None and bereit.get(t) is False):
            continue
        summe += sum(max(0.0, x) * teiler.get(art, 0.0) for x, art in faehigkeiten.schaden(ich.champion_id, t, r, L, st))
    return summe


def _basis_ad(champion_id: str, level: int) -> float:
    st = (ddragon.champions().get(champion_id) or {}).get("stats", {})
    return wachstum(float(st.get("attackdamage", 60)), float(st.get("attackdamageperlevel", 3)), level)


def ruestung(s) -> float:
    """Ruestung eines Gegners: Grundwert nach Level (Data Dragon) + Ruestung aus Items."""
    st = (ddragon.champions().get(s.champion_id) or {}).get("stats", {})
    r = wachstum(float(st.get("armor", 30)), float(st.get("armorperlevel", 4)), s.level)
    it = ddragon.items()
    return r + sum(float(it.get(i, {}).get("stats", {}).get("FlatArmorMod", 0.0)) for i in s.items)


def schaden(ich, werte: dict, raenge: dict[str, int], bereit: dict[str, bool] | None, ziel, ziel_anteil: float) -> float | None:
    """Voller Combo-Schaden nach Ruestung (ohne Zuenden) auf `ziel` mit `ziel_anteil` Leben; None, wenn der
    Champion nicht gerechnet wird. `bereit`: Q/W/E/R aus dem HUD (None = unbekannt, dann zaehlt jeder Rang)."""
    daten = WIKI.get(ich.champion_id)
    if not werte:
        return None
    if daten is None:
        return _allgemein(ich, werte, raenge, bereit, ziel) if kann(ich.champion_id) else None
    L = max(1, ich.level)
    ad = float(werte.get("attackDamage") or 0.0)
    bonus = max(0.0, ad - _basis_ad(ich.champion_id, L))

    def rang(t: str) -> int:
        r = int(raenge.get(t) or 0)
        return r if r > 0 and (bereit is None or bereit.get(t) is not False) else 0

    phys = 0.0
    if ich.champion_id == "Riven":
        rr = rang("R")
        if rr:
            ad, bonus = ad * (1 + daten["r_ad"]), bonus + ad * daten["r_ad"]
        passiv = daten["passiv"][0] + (daten["passiv"][1] - daten["passiv"][0]) * (L - 1) / 17
        if q := rang("Q"):
            phys += 3 * (daten["q"][q - 1] + daten["q_bonus"][q - 1] * bonus)
        if w := rang("W"):
            phys += daten["w"][w - 1] + daten["w_bonus"] * bonus
        faehigkeiten = (3 if rang("Q") else 0) + (1 if rang("W") else 0) + (1 if rang("E") else 0)
        phys += (1 + min(faehigkeiten, 4)) * ad + min(faehigkeiten, 4) * passiv * ad    # AA zwischen den Faehigkeiten
        if rr:
            fehlend = 1 - ziel_anteil
            faktor = 1 + min(2.0, fehlend * 100 * 2.667 / 100)
            r2 = (daten["r2_min"][rr - 1] + daten["r2_min_bonus"] * bonus) * faktor
            phys += min(r2, daten["r2_max"][rr - 1] + daten["r2_max_bonus"] * bonus)
    elif ich.champion_id == "Camille":
        if q := rang("Q"):
            phys += ad * (1 + daten["q1"][q - 1]) + ad * (1 + daten["q2"][q - 1])
        if w := rang("W"):
            phys += daten["w"][w - 1] + daten["w_bonus"] * bonus
        if e := rang("E"):
            phys += daten["e"][e - 1] + daten["e_bonus"] * bonus
        phys += 2 * ad
    elif ich.champion_id == "Graves":
        schuss = daten["schuss"][0] + (daten["schuss"][1] - daten["schuss"][0]) * (L - 1) / 17
        phys += 2 * schuss * ad
        if q := rang("Q"):
            phys += daten["q1"][q - 1] + daten["q1_bonus"] * bonus + daten["q2"][q - 1] + daten["q2_bonus"][q - 1] * bonus
        if rr := rang("R"):
            phys += daten["r"][rr - 1] + daten["r_bonus"] * bonus
    # Ruestung: Prozent-Durchdringung (API: 1,0 = keine) und Toedlichkeit
    arm = ruestung(ziel) * float(werte.get("armorPenetrationPercent") or 1.0) - float(werte.get("physicalLethality") or 0.0)
    return phys * 100 / (100 + max(0.0, arm))
