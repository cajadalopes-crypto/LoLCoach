"""Teamplan (Buch 4, Kapitel 3; Auftrag 008): wer will das Spiel wann entscheiden?

  - Kurve je Team: die Summe aus wissen/lane_kurve.toml [frueh, sechs, spaet] der fuenf Champions.
  - Stand: Item-Gold beider Teams, Tuerme, Drachen (Seelenpunkt), Baron, Level-Durchschnitt - als Punkte in Gold.
  - Plan, einer von vier: vorn und jetzt staerker -> ERZWINGEN; vorn, aber sie skalieren -> BEENDEN; hinten, aber
    ihr skaliert -> ZEIT; hinten und sie staerker -> CHANCEN.
  - Gesagt: einmal ab teamplan_ab_s (14:00), dann bei einem Umschwung (Gold-Vorsprung +-2000 seit dem letzten Satz,
    Inhibitor, Baron, Seele), hoechstens einmal je teamplan_abstand_s.
  - Beim Gleichstand zweier Handlungen gewinnt die, die zum Teamplan passt (PASST, ein Punkt EV).
"""
from __future__ import annotations

from dataclasses import dataclass

# welche Handlungen zu welchem Plan passen (Buch 4, 3: erzwingen = Gruppe, Zeit gewinnen = Seitenwellen)
PASST = {"ERZWINGEN": {"MIT_GRUPPE", "ZUR_GRUPPE", "NEHMEN", "BESTREITEN", "ANLAUFEN"},
         "BEENDEN": {"MIT_GRUPPE", "NEHMEN", "BESTREITEN", "DRUECKEN"},
         "ZEIT": {"SEITENWELLE", "FARMEN", "WELLE_KLAEREN", "WELLE_HALTEN", "HALTEN_UNTER_TURM", "ABGEBEN_TAUSCHEN"},
         "CHANCEN": {"SEITENWELLE", "DRUECKEN", "PLATTEN", "ABGEBEN_TAUSCHEN", "TAUSCHEN"}}
PHASE = ("früh", "Mitte", "spät")


@dataclass
class Teamplan:
    plan: str                        # ERZWINGEN / BEENDEN / ZEIT / CHANCEN
    punkte: int                      # Stand in Gold (> 0: ihr vorn)
    gold: int                        # Item-Gold-Vorsprung
    kurve_wir: tuple[int, int, int]
    kurve_die: tuple[int, int, int]
    phase: int                       # 0 frueh, 1 Mitte, 2 spaet
    satz: str


def _kurve(champions: list[str]) -> tuple[int, int, int]:
    from .. import wissen
    try:
        k = wissen.lade("lane_kurve").get("kurve", {})
    except Exception:
        k = {}
    werte = [k.get(c, [0, 0, 0]) for c in champions]
    return tuple(sum(w[i] for w in werte) for i in range(3))


def phase(zeit: float) -> int:
    return 0 if zeit < 840 else 1 if zeit < 1680 else 2


def stand(p, zeit: float) -> tuple[int, int]:
    """(Punkte, Item-Gold-Vorsprung): Gold + 600 je Turm + 400 je Drache (+1000 Seelenpunkt) + 1500 Baron-Buff +
    300 je Level im Durchschnitt."""
    from ..zustand import gegenteam
    wir, die = p.mein_team, gegenteam(p.mein_team)
    gold = p.item_gold(wir) - p.item_gold(die)
    tuerme = sum(1 if e.team == wir else -1 for e in p.kills_von("TurretKilled"))
    dw, dd = len(p.drachen(wir)), len(p.drachen(die))
    drachen = 400 * (dw - dd) + (1000 if dw >= 3 else 0) - (1000 if dd >= 3 else 0)
    baron = sum((1500 if e.team == wir else -1500) for e in p.kills_von("BaronKill") if 0 <= zeit - e.zeit <= 180)

    def schnitt(t):
        sp = p.team(t)
        return sum(s.level for s in sp) / len(sp) if sp else 0.0
    return int(gold + 600 * tuerme + drachen + baron + 300 * (schnitt(wir) - schnitt(die))), gold


def bestimmen(p, zeit: float, schwelle: int = 2) -> Teamplan | None:
    if p is None or not p.mein_team:
        return None
    from ..zustand import gegenteam
    wir, die = p.mein_team, gegenteam(p.mein_team)
    kw = _kurve([s.champion_id for s in p.team(wir)])
    kd = _kurve([s.champion_id for s in p.team(die)])
    ph = phase(zeit)
    punkte, gold = stand(p, zeit)
    g = abs(int(round(gold, -2)))
    if punkte >= 0:
        if kd[2] - kw[2] >= schwelle:      # ein Punkt ist Rauschen der groben Kurve (213624: -1 gegen 0)
            plan = "BEENDEN"
            # nach Minute 28 nicht mehr "vor Minute 30" (173159 36:23)
            wann = "vor Minute 30 Baron oder Inhibitor" if zeit < 1680 else "Baron oder Inhibitor, bevor es kippt"
            satz = (f"{g} Gold vorn, aber sie skalieren besser: {wann}."
                    if gold > 0 else f"Ihr liegt vorn, aber sie skalieren besser: {wann}.")
        else:
            plan = "ERZWINGEN"
            satz = (f"{g} Gold vorn und jetzt stärker: Drache und ihre Türme als Gruppe erzwingen."
                    if gold > 0 else "Ihr liegt vorn und seid stärker: Drache und ihre Türme als Gruppe erzwingen.")
    else:
        if kw[2] - kd[2] >= schwelle:
            plan = "ZEIT"
            satz = (f"{g} Gold hinten, aber ihr skaliert besser: nichts erzwingen, Wellen halten"
                    + (" bis Minute 30." if zeit < 1680 else "."))
        else:
            plan = "CHANCEN"
            satz = f"Sie sind {g} Gold vorn und stärker: kein 5 gegen 5, Picks und Seitenwellen."   # 14 Woerter
    return Teamplan(plan, punkte, gold, kw, kd, ph, satz)


class Sager:
    """Wann der Plan-Satz faellt (Buch 4, 3): ab teamplan_ab_s einmal, dann bei einem Umschwung, hoechstens einmal je
    teamplan_abstand_s."""

    def __init__(self):
        self.zuletzt: float | None = None
        self.gold_bei: int | None = None
        self.ereignisse: int = 0
        self.plan: str | None = None

    def faellig(self, tp: Teamplan, p, zeit: float, cfg: dict) -> bool:
        if tp is None or zeit < cfg["teamplan_ab_s"]:
            return False
        n = sum(len(p.kills_von(a)) for a in ("InhibKilled", "BaronKill")) + (1 if p.seele() else 0)
        if self.zuletzt is None:
            return True
        if zeit - self.zuletzt < cfg["teamplan_abstand_s"]:
            return False
        # Umschwung: Inhibitor, Baron oder Seele - oder der Gold-Vorsprung kippt um >= 2000 UND damit der Plan
        gold = abs(tp.gold - (self.gold_bei or 0)) >= cfg["teamplan_umschwung_gold"]
        return n > self.ereignisse or (gold and tp.plan != self.plan)

    def gesagt(self, tp: Teamplan, p, zeit: float) -> None:
        self.zuletzt, self.gold_bei, self.plan = zeit, tp.gold, tp.plan
        self.ereignisse = sum(len(p.kills_von(a)) for a in ("InhibKilled", "BaronKill")) + (1 if p.seele() else 0)
