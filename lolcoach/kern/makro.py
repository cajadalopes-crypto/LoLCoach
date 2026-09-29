"""Makro-Infos (Buch 4, Kapitel 5; Auftrag 008): wann welcher Satz - Beobachtung, Folgerung, Handlung (Kapitel 1).

| Anlass                  | gesagt, wenn                                                               |
|-------------------------|----------------------------------------------------------------------------|
| Teamplan                | teamplan.Sager (ab 14:00, bei Umschwung)                                   |
| Jungler-Sichtung, weit  | ihr Jungler frisch gesehen auf der anderen Seite, dein Plan nutzt das      |
|                         | Fenster (Platten, Turm, Seitenwelle, Trade) und es ist >= 15 s lang        |
| Jungler-Sichtung, nah   | frisch gesehen auf deiner Seite, du stehst vor der Mitte deiner Lane       |
|                         | (Lane-Phase) - als VORSICHT (zaehlt zu den Warnungen, A1)                  |
| Gruppierung             | >= 3 von ihnen sichtbar zusammen, Mid-Game, dein Plan ist eine Seitenlane  |
| Spike                   | ihr Staerkster schliesst ein Item ab oder erreicht Level 6/11/16, frisch   |
|                         | gesehen, und er ist auf deiner Seite oder dein Lane-Gegner                 |

Grenzen: hoechstens eine Makro-Info je makro_abstand_s (FENSTER und VORSCHAU zaehlen mit, GEFAHR und WENDEPUNKT
gehen vor); dieselbe Info (Art, Gegner, Seite) hoechstens einmal je info_wiederholen_s, ausser die Folgerung aendert
sich; ohne Wirkung auf deinen Plan nur aufs Dashboard.
MIA (Kapitel 5) geht im Vorsicht-Satz aus A1 auf (Abweichung: ein eigener MIA-Satz haette A1 unterlaufen).
"""
from __future__ import annotations

from .sprache import kartenseite, gross

NUTZT_FENSTER = {"PLATTEN", "DRUECKEN", "SEITENWELLE", "TRADE", "ALL_IN", "MIT_GRUPPE", "WELLE_DRUECKEN"}       # Buch 4, 5 (nicht Farmen)
VOR = {"DRUECKEN", "MIT_GRUPPE", "NEHMEN", "BESTREITEN", "PLATTEN", "ZUR_GRUPPE"}
SEITE_AKTION = {"SEITENWELLE", "PLATTEN", "DRUECKEN", "FARMEN", "WELLE_KLAEREN", "WELLE_DRUECKEN"}
ZAHL = {3: "Drei", 4: "Vier", 5: "Alle fünf"}
LEGENDAER = 2200          # Item-Gold ab dem ein Item als fertig zaehlt


class Makro:
    def __init__(self):
        from .teamplan import Sager
        self.teamplan = Sager()
        self.tp = None
        self._gesagt: dict[tuple, tuple[float, str]] = {}
        self._j_sichtbar = -1e9           # zuletzt sah man ihren Jungler
        self._j_auftauchen = -1e9         # wann er nach >= 10 s ungesehen wieder auftauchte
        self._spikes: dict[str, tuple[int, int]] = {}

    # --- Budget und Doppelung ----------------------------------------------------------------------------------

    def _frei(self, kern, m, cfg) -> bool:
        return not any(k in ("MAKRO", "FENSTER", "VORSCHAU") and m.zeit - t < cfg["makro_abstand_s"]
                       for t, k, _ in kern.gesagt[-8:])

    def _neu(self, schl: tuple, folgerung: str, zeit: float, cfg) -> bool:
        alt = self._gesagt.get(schl)
        return alt is None or zeit - alt[0] >= cfg["info_wiederholen_s"] or alt[1] != folgerung

    # --- Regeln ------------------------------------------------------------------------------------------------

    def info(self, kern, m, modus) -> tuple[str, str, str, tuple, str] | None:
        """(Kategorie, Art, Text, Schluessel, Folgerung) der besten faelligen Makro-Info - oder None."""
        from . import fuehren
        from .teamplan import bestimmen
        cfg = kern.cfg["makro"]
        b, p = m.b, m.p
        if b is None or p is None or modus in ("KAMPF", "TOT", None) or kern.gefahr:
            return None
        self.tp = bestimmen(p, m.zeit, cfg.get("teamplan_kurve_min", 2))
        plan = kern.fuehrer.plan
        art = plan.art if plan is not None else None
        j = b.jungler
        frisch_j = False
        if j is not None and not j.s.tot:
            if j.sichtbar:
                if m.zeit - self._j_sichtbar >= 10.0:
                    self._j_auftauchen = m.zeit
                self._j_sichtbar = m.zeit
                frisch_j = m.zeit - self._j_auftauchen <= 4.0
        if not self._frei(kern, m, cfg):
            return None
        kandidaten = []
        # Teamplan (Kapitel 3)
        if self.tp is not None and self.teamplan.faellig(self.tp, p, m.zeit, cfg):
            kandidaten.append(("MAKRO", "TEAMPLAN", self.tp.satz, ("teamplan",), self.tp.plan))
        meine = kartenseite(m.pos) if m.pos is not None else None
        # Jungler-Sichtung (Kapitel 5)
        # Auftrag 016, 1.2: hat die Informationspflicht den Jungler eben gesagt, keine zweite Sichtung
        pflicht = getattr(kern, "pflicht", None)
        if pflicht is not None and m.zeit - pflicht.jungler_gesagt <= 20.0:
            frisch_j = False
        if frisch_j and j.pos is not None and meine is not None:
            seine = kartenseite(j.pos)
            wort = {"oben": "oben", "unten": "unten", "in der Mitte": "in der Mitte"}
            if seine != meine and "Mitte" not in seine and "Mitte" not in meine and art in NUTZT_FENSTER \
                    and j.ankunft is not None and j.ankunft >= cfg["jungler_fenster_min_s"] and plan is not None:
                n = int(j.ankunft // 5 * 5) if j.ankunft >= 15 else int(j.ankunft)
                f = f"{wort[meine]} {n} Sekunden frei, {fuehren.kurz(plan.handlung)} jetzt"
                kandidaten.append(("MAKRO", "JUNGLER_WEIT", f"{j.champion} {wort[seine]} gesehen: {f}.",
                                   ("jungler", j.champion, seine), f.split(",")[0]))
            elif seine == meine and m.lane_phase and m.bereich == "lane_eigen" and b.tiefe is not None \
                    and b.tiefe > 0.5 and j.ankunft is not None and j.ankunft <= 20:
                kandidaten.append(("VORSICHT", "JUNGLER_NAH", f"{j.champion} {wort[seine]} gesehen: zurück hinter die "
                                   f"Welle.", ("jungler", j.champion, seine), "zurück"))
            elif art not in NUTZT_FENSTER or plan is None:
                kern.info_dazu(m.zeit, f"{j.champion} {wort.get(seine, seine)} gesehen")    # ohne Wirkung: Dashboard
        # Tote: >= 3 von ihnen tot und dein Plan geht nach vorn (Buch 4, 6: 213624 16:35 "Drei von ihnen tot:
        # Mid-Inhibitor jetzt")
        tote = sorted((float(g.s.respawn or 0.0) for g in b.gegner if g.s.tot), reverse=True)
        if len(tote) >= 3 and art in VOR and plan is not None:
            n = len(tote)
            noch = int(tote[2])
            f = f"{fuehren.kurz(plan.handlung)} jetzt"
            kandidaten.append(("MAKRO", "TOTE", f"{ZAHL.get(n, str(n))} von ihnen tot" + (f", noch {noch} Sekunden"
                               if noch >= 5 else "") + f": {f}.", ("tote", n), f))
        # Gruppierung (Mid-Game)
        if not m.lane_phase and art in SEITE_AKTION and meine is not None:
            from ..bewertung import abstand
            sicht = [g for g in b.gegner if not g.s.tot and g.sichtbar and g.pos is not None]
            for g in sicht:
                gruppe = [x for x in sicht if abstand(x.pos, g.pos) <= 2500]
                if len(gruppe) < 3:
                    continue
                cx = sum(x.pos[0] for x in gruppe) / len(gruppe)
                cy = sum(x.pos[1] for x in gruppe) / len(gruppe)
                wo = kartenseite((cx, cy))
                zahl = ZAHL.get(len(gruppe), str(len(gruppe)))
                if wo == meine or "Mitte" in wo:
                    f = "Seitenwelle nur bis zum Fluss"
                else:
                    f = f"{meine} ist frei, {fuehren.kurz(plan.handlung)}" if plan is not None else f"{meine} ist frei"
                ort = "Mitte" if "Mitte" in wo else wo
                kandidaten.append(("MAKRO", "GRUPPE", f"{zahl} von ihnen {ort}: {f}.", ("gruppe", ort), f))
                break
        # Spike beim Gegner
        lebend = [g for g in b.gegner if not g.s.tot]
        if lebend:
            st = max(lebend, key=lambda g: g.s.kills * 300 + g.s.item_gold)
            from .. import ddragon
            it = ddragon.items()
            items = sum(1 for i in st.s.items if it.get(i, {}).get("gold", {}).get("total", 0) >= LEGENDAER)
            level = 6 if st.s.level >= 6 else 0         # Level 6 (Ult) - 11 und 16 trafen Supports (173159 22:00)
            alt = self._spikes.get(st.champion)
            self._spikes[st.champion] = (items, level)
            frisch = st.sichtbar or (st.seit is not None and st.seit <= 10)
            nah = (st.pos is not None and meine is not None and kartenseite(st.pos) == meine) or \
                (b.lane is not None and b.lane.champion == st.champion)
            vorn = p.ich is not None and (st.s.item_gold >= p.ich.item_gold or st.s.level > p.ich.level)
            if alt is not None and frisch and nah and vorn and (items > alt[0] or level > alt[1]):
                was = (f"hat {['kein', 'ein', 'zwei', 'drei', 'vier', 'fünf', 'sechs'][min(items, 6)]} "
                       f"Item{'s' if items != 1 else ''}") if items > alt[0] else f"ist Level {level}"
                # Auftrag 009, 4: kein Possessiv vor dem Namen ("Ihr Aurora ist Level 6", 101426 4:39)
                kandidaten.append(("MAKRO", "SPIKE", f"{st.champion} {was}: Kämpfe gegen {st.champion} nur mit "
                                   f"Team.", ("spike", st.champion, items, level), "nur mit Team"))
        for kat, art_, text, schl, folg in kandidaten:
            if self._neu(schl, folg, m.zeit, cfg):
                return kat, art_, text, schl, folg
        return None

    def gesagt(self, info: tuple, m) -> None:
        kat, art, text, schl, folg = info
        self._gesagt[schl] = (m.zeit, folg)
        if art == "TEAMPLAN" and self.tp is not None:
            self.teamplan.gesagt(self.tp, m.p, m.zeit)


def teamplan_bonus(h, tp) -> float:
    """Buch 4, 3: beim Gleichstand gewinnt die Handlung, die zum Teamplan passt - ein Punkt EV."""
    from .teamplan import PASST
    return 1.0 if tp is not None and h.art in PASST.get(tp.plan, ()) else 0.0


__all__ = ["Makro", "teamplan_bonus", "gross"]
