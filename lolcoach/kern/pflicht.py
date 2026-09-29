"""Informationspflicht (Auftrag 016, 1 - Carlos' Pflichtenheft aus 133448: "Der Coach schweigt"): ungefragt, kurz, immer.

| Info            | gesagt, wenn                                                                        | Beispiel                      |
|-----------------|-------------------------------------------------------------------------------------|-------------------------------|
| Jungler         | ihr Jungler taucht nach >= jungler_ohne_s ohne Sicht wieder auf (auch zum ersten   | "Teemo im oberen Fluss, bei   |
|                 | Mal ab 1:30); kann er in <= jungler_nah_s bei dir sein, mit "bei dir in N Sekunden" | dir in 6 Sekunden."           |
| Lane-Gegner weg | dein Lane-Gegner ist sichtbar weit weg (>= lane_weit_s von dir, andere Seite,      | "Poppy unten gesehen: drück   |
|                 | seine Basis), du stehst an deiner Lane - mit Folge; nach vorn nur ohne R1          | deine Welle."                 |
| Flash           | jeder gegnerische Flash, den der Coach sieht, egal wie weit (Kern._flash_info)      | "Poppy Flash weg."            |

Die Sperre aus Auftrag 009 (Lagebild nur mit Handlung) gilt hierfuer nicht; die Saetze zaehlen nicht zum Budget
(sprechen.FREI), warten aber nicht laenger als `gilt_s` - in KAMPF schweigen sie. Die Makro-Jungler-Sichtung
(makro.py) schweigt `jungler_ohne_s` lang nach einem Jungler-Satz von hier.
"""
from __future__ import annotations

from .sprache import kartenseite


class Pflicht:
    def __init__(self):
        self.jungler_zuletzt: float | None = None     # zuletzt sichtbar
        self.jungler_gesagt = -1e9
        self.lane_gesagt = -1e9
        self.lane_bereit = True                       # wieder scharf, sobald er nah war, tot war oder lange fehlte
        self.offen: dict[str, tuple[float, str]] = {}  # Art -> (seit, Text)

    def takt(self, kern, m, modus: str | None) -> None:
        """Erkennt die Anlaesse dieses Takts (jeder Takt, auch in KAMPF - dann wartet der Satz)."""
        b = m.b
        if b is None:
            return
        c = kern.cfg["pflicht"]
        j = b.jungler
        if j is not None and not j.s.tot and j.sichtbar:
            ohne = None if self.jungler_zuletzt is None else m.zeit - self.jungler_zuletzt
            if m.zeit >= c["ab_s"] and (ohne is None or ohne >= c["jungler_ohne_s"]) and j.ort:
                n = max(1, int(round(j.ankunft or 0)))
                nah = f", bei dir in {n} Sekunde{'n' if n != 1 else ''}" \
                    if j.ankunft is not None and j.ankunft <= c["jungler_nah_s"] and "Basis" not in j.ort else ""
                self.offen["INFO_JUNGLER"] = (m.zeit, f"{j.champion} {j.ort}{nah}.")
            self.jungler_zuletzt = m.zeit
        g = b.lane
        if g is None or g.s.tot:
            self.lane_bereit = True
            return
        # Kritik 016 (192113 24:32-24:48: fuenfmal "Teemo oben gesehen" in 16 s): wieder scharf erst, wenn er nah war
        # UND der letzte Satz >= 30 s her ist - oder nach lane_wieder_s
        seit = m.zeit - self.lane_gesagt
        if (g.sichtbar and g.ankunft is not None and g.ankunft < c["lane_nah_s"] and seit >= 30.0) \
                or seit >= c["lane_wieder_s"]:
            self.lane_bereit = True
        an_lane = str(getattr(m, "bereich", None) or "lane").startswith("lane")      # du stehst an einer Lane
        if not (g.sichtbar and g.pos is not None and m.pos is not None and self.lane_bereit and an_lane
                and modus in ("LANE", "SEITE") and m.zeit >= c["ab_s"]):
            return
        basis = "Basis" in (g.ort or "")
        meine, seine = kartenseite(m.pos), kartenseite(g.pos)
        andere = seine != meine and "Mitte" not in seine + meine
        if not (basis or andere or (g.ankunft is not None and g.ankunft >= c["lane_weit_s"])):
            return
        wo = "in seiner Basis" if basis else seine
        if kern.gefahr:
            return                      # Kritik 016 (192113 12:36: "in Ruhe farmen" bei 10 %, drei kamen): Gefahr geht vor
        v = kern.vorn()
        folge = "farm unter deinem Turm" if v["verboten"] else "drück deine Welle"
        self.offen["INFO_LANE"] = (m.zeit, f"{g.champion} {wo} gesehen: {folge}.")
        self.lane_bereit = False

    def faellig(self, m, modus: str | None, cfg: dict) -> tuple[str, str] | None:
        """(Art, Text) des naechsten offenen Satzes - nicht in KAMPF; zu alte fallen weg."""
        for art in list(self.offen):
            if m.zeit - self.offen[art][0] > cfg["pflicht"]["gilt_s"]:
                del self.offen[art]
        if modus == "KAMPF" or not self.offen:
            return None
        art = min(self.offen, key=lambda a: self.offen[a][0])
        return art, self.offen[art][1]

    def gesagt(self, art: str, m) -> None:
        self.offen.pop(art, None)
        if art == "INFO_JUNGLER":
            self.jungler_gesagt = m.zeit
        elif art == "INFO_LANE":
            self.lane_gesagt = m.zeit
