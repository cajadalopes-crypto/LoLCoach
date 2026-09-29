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
        self.vorlauf_gesagt: set = set()              # (Objective, Spawn, Stufe)
        self.vorhersage_zuletzt = -1e9
        self.basis_seit: float | None = None          # lebend in der Basis seit
        self.basis_pos = None                         # (Zeit, Ort) beim letzten Stand
        self.basis_gesagt: list[float] = []

    def _basis_steht(self, kern, m, modus: str | None) -> None:
        """Auftrag 018, 2 (183125 18:46-19:48: nach dem Respawn eine Minute im Brunnen, keine Anweisung - "ich bleibe
        stehen, bis du mir sagst, was ich tun soll"): stehst du lebend basis_steht_s in der Basis, ohne dich zu
        bewegen, kommt der Plan noch einmal - hoechstens zweimal je Aufenthalt."""
        c = kern.cfg["pflicht"]
        if getattr(m, "tot", False) or modus != "BASIS" or getattr(m, "pos", None) is None:
            self.basis_seit, self.basis_pos, self.basis_gesagt = None, None, []
            return
        if self.basis_seit is None:
            self.basis_seit, self.basis_pos = m.zeit, (m.zeit, m.pos)
            return
        from ..bewertung import abstand
        if abstand(m.pos, self.basis_pos[1]) > c["basis_bewegt"]:
            self.basis_pos = (m.zeit, m.pos)                 # er geht los - die Uhr beginnt neu
            return
        steht = m.zeit - self.basis_pos[0]
        zuletzt = self.basis_gesagt[-1] if self.basis_gesagt else self.basis_pos[0]
        if steht < c["basis_steht_s"] or m.zeit - zuletzt < c["basis_steht_s"] or len(self.basis_gesagt) >= 2:
            return
        # derselbe Satz wie zuletzt in diesem Aufenthalt - kein neues Ziel (102112 3715: ein Ziel je Basis-Aufenthalt)
        gesagt = [e for e in getattr(kern, "_ansage_log", None) or []
                  if e["zeit"] >= self.basis_seit and not str(e["kategorie"]).startswith("INFO_")]
        pl = getattr(getattr(kern, "fuehrer", None), "plan", None)
        satz = gesagt[-1]["text"] if gesagt else (pl.handlung.satz if pl is not None and not pl.handlung.stumm else "")
        if not satz:
            return
        self.basis_gesagt.append(m.zeit)
        from .modi import kuerze
        from .sprache import gross
        satz = satz.removeprefix("Jetzt, wo du in der Basis bist: ").removeprefix("Jetzt, wo du wieder lebst: ")
        self.offen["INFO_BASIS"] = (m.zeit, kuerze(f"Los: {gross(satz)}", kern.cfg["sprechen"]["max_woerter"]))

    def _vorlauf(self, kern, m) -> None:
        """Auftrag 017, 1.3 (Buch 13, 4): 60 s vor dem Spawn die Vorbereitungskette, 40 s vorher loslaufen; ohne Prio
        (der Kern tauscht: ABGEBEN_TAUSCHEN) der Tausch-Satz. Nur fuer Objectives, die dich ziehen (Buch 6, 4.1)."""
        from . import objective as obj
        from .modi import OBJ_NAME
        c = kern.cfg["pflicht"]
        zum = {"drache": "zum Drachen", "baron": "zum Baron", "herold": "zum Herold", "larven": "zu den Larven",
               "aeltester": "zum Ältesten"}
        pl = getattr(getattr(kern, "fuehrer", None), "plan", None)
        for o in getattr(m, "objectives", None) or []:
            if o.lebt or o.spawn_in is None or o.schl not in zum:
                continue
            stufe = "vor" if c["vorlauf_s"] - 8 < o.spawn_in <= c["vorlauf_s"] + 2 else \
                "los" if c["loslaufen_s"] - 8 < o.spawn_in <= c["loslaufen_s"] + 2 else None
            schl = (o.schl, round(m.zeit + o.spawn_in), stufe)
            if stufe is None or schl in self.vorlauf_gesagt:
                continue
            try:
                if not obj.zieht(m, o, kern.cfg):
                    continue
            except Exception:
                continue
            self.vorlauf_gesagt.add(schl)
            name, n = OBJ_NAME.get(o.schl, o.schl), int(round(o.spawn_in / 5) * 5)
            if pl is not None and pl.art == "ABGEBEN_TAUSCHEN" and pl.handlung.satz:
                text = f"{name} in {n} Sekunden, ihr habt keine Prio: {pl.handlung.satz}"
            elif hasattr(kern, "_back_sperre") and kern._back_sperre(m, "back") is not None:
                # R4 (Back-Rufe je 10 min, ignoriert): die Vorbereitung ohne Back
                welle = "rein" if stufe == "los" else "crashen"
                text = f"{name} in {n} Sekunden: Welle {welle}, dann mit Team {zum[o.schl]}."
            elif m.leben is not None and m.leben < kern.cfg["schranken"]["vor_leben_min"]:
                text = f"{name} in {n} Sekunden: jetzt back, dann mit Team {zum[o.schl]}."     # R1: nicht crashen
            elif stufe == "vor":
                text = f"{name} in {n} Sekunden: Welle crashen, back, dann mit Team {zum[o.schl]}."
            else:
                text = f"{name} in {n} Sekunden: Welle rein und jetzt loslaufen, {zum[o.schl]}."
            self.offen["INFO_VORLAUF"] = (m.zeit, text)

    def _vorhersage(self, kern, m, j) -> None:
        """Auftrag 017, 1.1 (Buch 13, I2): ihr Jungler >= 45 s ungesehen, frueh im Spiel - "vermutlich" aus
        jungle.wahrscheinlich. Nur mit [pflicht] vorhersage = true: die Nachpruefung an allen Aufnahmen
        (werkzeuge/jungler_vorhersage.py) lag unter 65 %, dann bleibt sie stumm."""
        c = kern.cfg["pflicht"]
        jt = getattr(getattr(kern, "_lagebild", None), "jungle", None)
        if not c.get("vorhersage", False) or jt is None or j.sichtbar or j.seit is None \
                or j.seit < c["vorhersage_ohne_s"] or m.zeit > c["vorhersage_bis_s"] \
                or m.zeit - self.vorhersage_zuletzt < 60.0:
            return
        s, pw = max(jt.wahrscheinlich(m.zeit).items(), key=lambda x: x[1])
        if pw < 0.65:
            return
        self.vorhersage_zuletzt = m.zeit
        self.offen["INFO_JUNGLER"] = (m.zeit, f"{j.champion} vermutlich {s}.")

    def takt(self, kern, m, modus: str | None) -> None:
        """Erkennt die Anlaesse dieses Takts (jeder Takt, auch in KAMPF - dann wartet der Satz)."""
        b = m.b
        if b is None:
            return
        c = kern.cfg["pflicht"]
        self._vorlauf(kern, m)
        self._basis_steht(kern, m, modus)
        if b.jungler is not None and not b.jungler.s.tot:
            self._vorhersage(kern, m, b.jungler)
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
