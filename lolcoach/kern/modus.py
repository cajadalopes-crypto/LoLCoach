"""Modus: "Was ist gerade dein Job?" (Buch 0, Kapitel 5). EIN Modus je Takt, mit Hysterese.

Prioritaet (die erste passende Zeile gewinnt): TOT > KAMPF > OBJECTIVE > VERTEIDIGEN > BASIS > LANE > SEITE >
GRUPPE > UNTERWEGS. Ein neuer Modus gilt erst, wenn er `hysterese_s` lang ununterbrochen Kandidat war - TOT und
KAMPF sofort; KAMPF endet erst nach `kampf_ende_s` ohne Kampfmerkmale. Ohne frische Daten bleibt der Modus."""
from __future__ import annotations

from .merkmale import OBJ_GRUBE, Merkmale

MODI = ("TOT", "KAMPF", "OBJECTIVE", "VERTEIDIGEN", "BASIS", "LANE", "SEITE", "GRUPPE", "UNTERWEGS")

BEREICH_WORTE = {"lane_eigen": "auf deiner Lane", "basis_eigen": "in eurer Basis", "basis_fremd": "in ihrer Basis",
                 "fluss_oben": "im oberen Fluss", "fluss_unten": "im unteren Fluss", "fluss_mitte": "in der Flussmitte",
                 "jungle_eigen_oben": "in eurem oberen Jungle", "jungle_eigen_unten": "in eurem unteren Jungle",
                 "jungle_fremd_oben": "in ihrem oberen Jungle", "jungle_fremd_unten": "in ihrem unteren Jungle",
                 "grube:drache": "an der Drachengrube", "grube:baron": "an der Baron-Grube",
                 "lane:Top": "auf der Top-Lane", "lane:Mid": "auf der Mid-Lane", "lane:Bot": "auf der Bot-Lane"}


def bereich_worte(bereich: str | None) -> str:
    return BEREICH_WORTE.get(bereich or "", "Ort unbekannt")


class Modus:
    def __init__(self, cfg: dict):
        self.c = cfg["modus"]
        self.mindestens = cfg.get("objective_wert", {}).get("mindestens", {})
        self.aktuell: str | None = None
        self.seit: float = 0.0
        self.kandidat: str | None = None
        self.kandidat_seit: float = 0.0
        self._kampf_zuletzt = -1e9
        self.grund = ""                  # warum dieser Modus (fuer Dashboard und _kern.jsonl)

    def _roh(self, m: Merkmale) -> tuple[str, str]:
        """Die erste passende Zeile der Tabelle (Kapitel 5.1) und ihr Grund."""
        c = self.c
        if m.tot:
            return "TOT", "du bist tot"
        if m.im_kampf:
            return "KAMPF", "Gegner in Reichweite, Leben faellt"
        eigene_lane = m.lane_phase and m.bereich == "lane_eigen"
        if not eigene_lane:     # auf der eigenen Lane in der Lane-Phase bleibt es LANE (VORBEREITEN_OBJECTIVE)
            for o in m.objectives:
                if not (o.lebt or o.spawn_in <= c["objective_vorlauf_s"]):
                    continue
                # "du stehst an der Grube": in der Grube - oder <= objective_nah_s entfernt UND genug von euch
                # koennen dort sein, dass sich die Kernfrage (nehmen, bestreiten, abgeben, tauschen?) ueberhaupt
                # stellt (Schritt 2, messungen.md: sonst war mit einem lebenden Baron ab Minute 20 von der Mid-Lane
                # aus alles OBJECTIVE). Nicht aus der Basis heraus (der Heimweg-Schub macht die Laufzeit klein).
                in_grube = m.bereich == f"grube:{OBJ_GRUBE[o.schl]}"
                nah = (o.weg is not None and o.weg <= c["objective_nah_s"] and m.bereich != "basis_eigen"
                       and 1 + o.team_erreicht >= self.mindestens.get(o.schl, 2))
                if in_grube or nah or o.team_nah >= 1:
                    return "OBJECTIVE", f"{o.schl} {'lebt' if o.lebt else f'in {int(o.spawn_in)} s'}, " + (
                        "du stehst in der Grube" if in_grube else f"du {int(o.weg)} s entfernt, "
                        f"{o.team_erreicht} von euch koennen mit" if nah else f"{o.team_nah} von euch an der Grube")
        for name, _, weg in m.bedrohung:
            if weg is not None and weg <= c["verteidigen_weg_s"]:
                return "VERTEIDIGEN", f"Bedrohung an {name}, {int(weg)} s von dir"
        if m.bereich == "basis_eigen":
            return "BASIS", "in eurer Basis"
        if m.lane_phase and m.bereich == "lane_eigen":
            return "LANE", "Lane-Phase, auf deiner Lane"
        seitenlane = m.bereich in ("lane:Top", "lane:Bot") or (m.bereich == "lane_eigen" and m.meine_lane in ("Top", "Bot"))
        if not m.lane_phase and seitenlane:
            return "SEITE", f"nach der Lane-Phase {bereich_worte(m.bereich)}"
        if not m.lane_phase and m.team_nah(m.pos, c["gruppe_radius"]) >= c["gruppe_mindestens"]:
            return "GRUPPE", f"{m.team_nah(m.pos, c['gruppe_radius'])} Mitspieler bei dir"
        return "UNTERWEGS", bereich_worte(m.bereich)

    def neu(self, m: Merkmale | None) -> str | None:
        if m is None:
            return self.aktuell
        if not m.daten_frisch and not m.tot:
            return self.aktuell           # ohne frische Daten kein Wechsel (Kapitel 4.3)
        if m.bereich is None and not m.tot:
            # Ort unbekannt (Minimap liest dich nicht): kein Modus statt geraten (4.3) - dann gilt keine Sperre,
            # die alten Regeln sprechen wie ohne Kern (Generalprobe 27.09.: sonst "UNTERWEGS" und die Lane stumm)
            self.aktuell, self.kandidat, self.grund = None, None, "Ort unbekannt"
            return None
        roh, grund = self._roh(m)
        if roh == "KAMPF":
            self._kampf_zuletzt = m.zeit
        if roh in ("TOT", "KAMPF") or roh == self.aktuell or self.aktuell is None:
            if roh == self.aktuell:
                self.grund = grund
            return self._setze(roh, m.zeit, grund)
        # KAMPF endet kampf_ende_s nach den letzten Kampfmerkmalen - sofort, wenn kein lebender Gegner mehr in
        # Reichweite ist: dann ist der Kampf entschieden (Schritt 2, messungen.md; 102112 5:17 - Sett eben tot)
        if (self.aktuell == "KAMPF" and m.gegner_im_radius
                and m.zeit - self._kampf_zuletzt < self.c["kampf_ende_s"]):
            return self.aktuell
        if self.kandidat != roh:
            self.kandidat, self.kandidat_seit = roh, m.zeit
        if m.zeit - self.kandidat_seit >= self.c["hysterese_s"]:
            return self._setze(roh, m.zeit, grund)
        return self.aktuell

    def _setze(self, modus: str, zeit: float, grund: str) -> str:
        if modus != self.aktuell:
            self.aktuell, self.seit = modus, zeit
        self.kandidat, self.grund = None, grund
        return modus
