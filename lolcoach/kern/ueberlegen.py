"""Ueberlegenheits-Regel (Auftrag 004, Teil B) - bis die Kampf-Eichung besteht, robust statt p_gewinn.

Gegen die Gegnergruppe G, die in `fenster_s` am Ort sein kann (p_da_am >= p_da_min; veraltete Werte nach Buch 7,
3.2 geschaetzt), ist die Lage

  robust klar ueberlegen, wenn alles gilt:
    - eure Koepfe >= ihre (Mitspieler, die in fenster_s dort sind, zaehlen mit),
    - dein Leben >= leben_min (60 %),
    - und eins davon: du liegst vor JEDEM in G >= level_allein (3) Level; vor jedem >= level_mit_gold (2) Level UND
      >= gold (2000) Item-Gold; eure Koepfe >= ihre + koepfe_plus (2).
  robust klar unterlegen: spiegelbildlich (ihre Koepfe >= eure, und jeder in G liegt so weit vor dir, oder ihre
  Koepfe >= eure + 2).
  sonst: unklar (None).

Wirkung (kern/__init__): klar ueberlegen - DRUECKEN, MIT_GRUPPE, NEHMEN, BESTREITEN, ANNEHMEN und REIN sprechen auch
ohne Fenster, der Grund nennt die Ueberlegenheit; klar unterlegen - sie sind aus; unklar - wie bisher (nur mit
Fenster). Turm-Dives bleiben unter Buch 7, Kapitel 6.
"""
from __future__ import annotations

from ..bewertung import WEGFAKTOR, abstand

ARTEN = frozenset(("DRUECKEN", "MIT_GRUPPE", "NEHMEN", "BESTREITEN", "ANNEHMEN", "REIN"))
MITSPIELER_TEMPO = 380.0
ZAHL = {1: "eins", 2: "zwei", 3: "drei", 4: "vier", 5: "fünf"}


def lage(m, cfg: dict, ort, fenster_s: float | None = None) -> tuple[str | None, str]:
    """("ueberlegen" | "unterlegen" | None, Grund in Worten) - Grund z. B. "Level 17 gegen 12", "ihr seid vier gegen
    zwei". Ohne Gegner in G: (None, "") - dann entscheidet das Fenster wie bisher."""
    from . import gefahr
    from .kampf import gegner_werte
    c = cfg["ueberlegen"]
    b, p = m.b, m.p
    if b is None or p is None or p.ich is None or ort is None:
        return None, ""
    fenster = fenster_s if fenster_s is not None else cfg["kampf"]["fenster_s"]
    # auch Tote: wer in fenster_s neben dem Ziel aufsteht, ist da (p_da_am rechnet Respawn + Weg; 102112 34:49 - am
    # Mid-Inhibitor-Turm standen Sett, Kai'Sa und Fiddlesticks 11-19 s spaeter auf, "drei gegen eins" war falsch)
    G = [g for g in b.gegner if gefahr.p_da_am(g, fenster, m, cfg["gefahr"], ort) >= c["p_da_min"]]
    if not G:
        return None, ""
    wir = 1 + sum(1 for s, wo, *_ in (b.mitspieler or []) if wo is not None and not s.tot
                  and abstand(wo, ort) * WEGFAKTOR / MITSPIELER_TEMPO <= fenster)
    ihre = len(G)
    ich = p.ich
    werte = [gegner_werte(g, m, cfg["kampf"]) for g in G]
    vor_level = min(ich.level - lv for lv, _, _ in werte)
    vor_gold = min(ich.item_gold - gd for _, gd, _ in werte)
    hinter_level = min(lv - ich.level for lv, _, _ in werte)
    hinter_gold = min(gd - ich.item_gold for _, gd, _ in werte)
    leben = m.leben if m.leben is not None else 0.0
    koepfe = f"ihr seid {ZAHL.get(wir, wir)} gegen {ZAHL.get(ihre, ihre)}"
    hoechst = max(lv for lv, _, _ in werte)
    if wir >= ihre and leben >= c["leben_min"]:
        if vor_level >= c["level_allein"] or (vor_level >= c["level_mit_gold"] and vor_gold >= c["gold"]):
            return "ueberlegen", f"Level {ich.level} gegen {hoechst}" + (f", {koepfe}" if wir > ihre else "")
        if wir >= ihre + c["koepfe_plus"]:
            return "ueberlegen", koepfe
    if ihre >= wir:
        if hinter_level >= c["level_allein"] or (hinter_level >= c["level_mit_gold"] and hinter_gold >= c["gold"]):
            return "unterlegen", f"Level {ich.level} gegen {min(lv for lv, _, _ in werte)}"
        if ihre >= wir + c["koepfe_plus"]:
            return "unterlegen", f"sie sind {ZAHL.get(ihre, ihre)} gegen {ZAHL.get(wir, wir)}"
    return None, ""


def mit_grund(h, grund: str) -> None:
    """Der Satz nennt die Ueberlegenheit statt des Fenster-Grundes ("Drueck den inneren Top-Turm: Level 17 gegen 12.")."""
    if h.satz and "allein" in h.satz.split(": ", 1)[0] and ", ihr seid" in grund:
        grund = grund.split(", ihr seid")[0]      # "Drache allein: ..., ihr seid zwei" widerspricht sich (102112 26:41)
    h.grund = grund
    if h.satz:
        kopf = h.satz.split(": ", 1)[0].rstrip(".")
        h.satz = f"{kopf}: {grund}."
