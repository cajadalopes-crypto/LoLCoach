"""Plan: halten statt hin und her (Buch 0, Kapitel 8).

Je Takt, in dieser Reihenfolge (8.2):
  1. Ungueltig? Die Art ist kein Kandidat mehr (Moduswechsel = Planpruefung) oder eine Abbruch-Pruefung schlaegt an.
     Ein erledigter Schritt ist kein ungueltiger Plan: WELLE_REIN_UND_BACK nach dem Crash gilt als BACK_JETZT weiter.
  2. Gefahr? p_tod(Plan) x Todeskosten >= schwelle_ge (und p_tod >= p_min), und eine sicherere Handlung hat mehr EV:
     sofort wechseln (GEFAHR).
  3. Erfuellt? Naechster Schritt; eine Ansage nur, wenn er eine neue Taetigkeit verlangt.
  4. Besser? Nur wenn EV(neu) - EV(Plan) >= max(hysterese_ge, hysterese_anteil x |EV(Plan)|), stabil_s lang, und
     seit dem letzten Wechsel halten_s vergangen sind.
  5. Nicht ausgefuehrt? Nach erinnern_nach_s einmal erinnern (BASIS: eigene Warteregel, kern/__init__)."""
from __future__ import annotations

from dataclasses import dataclass

from .handlung import SICHER, Handlung


HALTEN = ("crash_bis", "gold_start")      # Daten, die beim Nachrechnen des Plans bleiben (Stand beim Ansagen)


@dataclass
class Plan:
    handlung: Handlung
    seit: float
    gesagt: float | None = None       # wann angesagt
    schritt: int = 0                  # Index in handlung.schritte
    erinnert: bool = False
    schritt_seit: float = 0.0
    start: dict | None = None         # Lage beim Ansagen (fuer "nicht ausgefuehrt")

    @property
    def art(self) -> str:
        return self.handlung.art

    def als(self) -> str:
        """Die Kandidaten-Art, der der Plan im aktuellen Schritt entspricht (WELLE_REIN_UND_BACK nach dem Crash:
        BACK_JETZT)."""
        return self.handlung.daten.get("folge_art", {}).get(self.schritt, self.handlung.art)


@dataclass
class Ereignis:
    art: str                          # "neu" | "gefahr" | "schritt" | "erinnern" | "ende"
    plan: Plan | None
    vorher: str | None = None         # Art des vorigen Plans
    text: str = ""


def gefahr_schlaegt_an(h: Handlung, c: dict) -> bool:
    """Kapitel 7.5: p_tod x Todeskosten >= schwelle_ge und p_tod >= p_min."""
    return h.p_tod * h.verlust >= c["schwelle_ge"] and h.p_tod >= c["p_min"]


class PlanFuehrer:
    def __init__(self, cfg: dict):
        self.c = cfg["plan"]
        self.g = cfg["gefahr"]
        self.plan: Plan | None = None
        self._wechsel = -1e9
        self._besser: tuple[str, float] | None = None
        self.top: list[Handlung] = []

    def _neu(self, h: Handlung, zeit: float, art: str, vorher: Plan | None) -> Ereignis:
        self.plan = Plan(h, zeit, schritt_seit=zeit)
        self._wechsel = zeit
        self._besser = None
        return Ereignis(art, self.plan, vorher.art if vorher is not None else None)

    def takt(self, m, kandidaten: list[Handlung], gefahr: bool) -> Ereignis | None:
        zeit = m.zeit
        self.top = sorted(kandidaten, key=lambda h: -h.ev)[:3]
        if not kandidaten:
            if self.plan is not None:
                alt, self.plan = self.plan, None
                return Ereignis("ende", None, alt.art)
            return None
        beste = max(kandidaten, key=lambda h: h.ev)
        p = self.plan
        if p is None:
            return self._neu(beste, zeit, "gefahr" if gefahr and beste.art in SICHER else "neu", None)
        je_art = {h.art: h for h in kandidaten}
        # 3 vor 1: ein erledigter Schritt haelt den Plan (8.2 Punkt 1, erstes Beispiel)
        schritt = None
        if p.handlung.erfuellt is not None and p.handlung.erfuellt(m, p):
            p.schritt += 1
            p.schritt_seit = zeit
            satz = p.handlung.schritt_saetze.get(p.schritt)
            if satz:
                schritt = Ereignis("schritt", p, text=satz)
        # 1. ungueltig?
        frisch = je_art.get(p.als())
        grund = next((g for f in p.handlung.abbruch if (g := f(m, p))), None)
        if frisch is None or grund:
            return self._neu(beste, zeit, "gefahr" if gefahr and beste.art in SICHER else "neu", p)
        self._uebernehmen(p, frisch)
        # 2. Gefahr: der Plan selbst ist zu gefaehrlich, und eine sicherere Handlung ist mehr wert
        if gefahr_schlaegt_an(p.handlung, self.g) and p.art not in SICHER:
            sicher = [h for h in kandidaten if h.art in SICHER]
            if sicher:
                s = max(sicher, key=lambda h: h.ev)
                if s.ev > p.handlung.ev:
                    return self._neu(s, zeit, "gefahr", p)
        if schritt is not None:
            return schritt
        # 4. besser? (Hysterese in GE, stabil, halten)
        if beste.art != p.als():
            diff = beste.ev - p.handlung.ev
            if diff >= max(self.c["hysterese_ge"], self.c["hysterese_anteil"] * abs(p.handlung.ev)):
                if self._besser is None or self._besser[0] != beste.art:
                    self._besser = (beste.art, zeit)
                if zeit - self._besser[1] >= self.c["stabil_s"] and zeit - self._wechsel >= self.c["halten_s"]:
                    return self._neu(beste, zeit, "neu", p)
            else:
                self._besser = None
        else:
            self._besser = None
        return None

    def _uebernehmen(self, p: Plan, frisch: Handlung) -> None:
        """Die frische Rechnung dieses Takts (EV, p_tod, Satz) in den gehaltenen Plan - Schritt und Zeiten bleiben."""
        if frisch.art == p.handlung.art:
            daten = p.handlung.daten
            erfuellt, saetze = p.handlung.erfuellt, p.handlung.schritt_saetze
            p.handlung = frisch
            for k in HALTEN:
                if k in daten:
                    frisch.daten[k] = daten[k]
            frisch.erfuellt = frisch.erfuellt or erfuellt
            frisch.schritt_saetze = frisch.schritt_saetze or saetze
        else:        # der Plan steht in einem Folgeschritt (z. B. nach dem Crash = BACK_JETZT): Werte uebernehmen
            h = p.handlung
            h.ev, h.p_tod, h.verlust = frisch.ev, frisch.p_tod, frisch.verlust
            h.daten["wer"] = frisch.daten.get("wer", [])

    def erinnern(self, m, nicht_ausgefuehrt) -> Ereignis | None:
        """8.2 Punkt 5: einmal, `erinnern_nach_s` nach dem Ansagen, wenn nichts in Richtung des Plans geschah."""
        p = self.plan
        if p is None or p.erinnert or p.gesagt is None or m.zeit - p.gesagt < self.c["erinnern_nach_s"]:
            return None
        if not nicht_ausgefuehrt(m, p):
            return None
        p.erinnert = True
        return Ereignis("erinnern", p)
