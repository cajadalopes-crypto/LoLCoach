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
    return champion_id in WIKI


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
    if daten is None or not werte:
        return None
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
