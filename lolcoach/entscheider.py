"""Der Entscheider: die beste naechste Handlung - auch wenn gerade nichts "passiert".

Die Regeln reagieren auf Ereignisse. Ein Challenger-Coach redet aber auch dazwischen: was ist
JETZT der Plan, in welcher Reihenfolge, und warum? Carlos' Reasoning-Datei (Reasoning/LoL
Reasoning.txt) gibt die Kette vor:

  Champion-Zustand -> Welle -> Lane-Prio -> Tempo -> Kartenzugang -> Information ->
  Gegner-Vorhersage -> moegliche Aktionen -> Gegenantwort -> Erwartungswert -> naechster Zustand

und die sechs Fragen, die jede Entscheidung beantworten muss: Wer ist staerker? Wer ist zuerst
da? Was sehen wir nicht? Welche Welle verlieren wir? Was bekommt der Gegner? Was gewinnen wir
nach dem Play?

Umsetzung: je Takt zaehlt der Entscheider die Handlungen auf, die gerade moeglich sind (Optionen),
prueft jede auf Sicherheit (wer kann dich erreichen, bevor du am Turm bist, und was siehst du
nicht), gibt ihr einen groben Wert (Gold-Aequivalent: Platten, Welle, Item-Timing, Objective,
Kill) und nimmt die beste. Gesprochen wird sie, wenn sie sich aendert und eine Weile haelt - als
Plan mit Reihenfolge ("erst ..., dann ...") und den Fakten, die ihn tragen. Mindestens zwei
Faktoren je Plan, sonst schweigt er (Carlos: "mehrere Faktoren, keine Standardphrasen").
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import komponist
from .bewertung import Bewertung
from .jungle import LANE_SEITE, Jungletracker, anders
from .komponist import OBJ_NAME, sek

LANE_PHASE_BIS = 840
HALTEN = 3.0            # so lange muss eine neue beste Option halten, bevor sie gesagt wird
ABSTAND = 25.0          # mindestens so viele Sekunden zwischen zwei Plaenen
GLEICH_SPERRE = 75.0    # derselbe Plan kommt fruehestens nach so vielen Sekunden wieder
LAUF_ZUR_LANE = {"TOP": 27.0, "MIDDLE": 20.0, "BOTTOM": 27.0, "UTILITY": 27.0}   # Spawn -> Lane-Mitte [Schaetzung]


def wellen_spawns(bis: float) -> list[tuple[float, bool]]:
    """(Spawnzeit, Kanone?) aller Wellen bis `bis` - Saison 2026 (saison2026.md): 0:30 erste Welle,
    bis 14:00 alle 30 s mit Kanone jede 3. (erste = Welle 3 um 1:30), bis 25:00 alle 25 s mit
    Kanone jede 2., bis 30:00 jede Welle mit Kanone, danach alle 20 s."""
    aus, t, k = [], 30.0, 1
    while t <= bis:
        if t < 840:
            kanone = k % 3 == 0
            schritt = 30.0
        elif t < 1500:
            kanone = k % 2 == 0
            schritt = 25.0
        else:
            kanone = True
            schritt = 25.0 if t < 1800 else 20.0
        aus.append((t, kanone))
        t += schritt
        k += 1
    return aus


def naechste_kanone(zeit: float, rolle: str) -> float | None:
    """Spielzeit, zu der die naechste Kanonenwelle in deiner Lane ankommt."""
    lauf = LAUF_ZUR_LANE.get(rolle, 27.0)
    for t, kanone in wellen_spawns(zeit + 120):
        if kanone and t + lauf > zeit + 3:
            return t + lauf
    return None


def _namen_kurz(liste) -> str:
    n = [x.champion for x in liste]
    return n[0] if len(n) == 1 else ", ".join(n[:-1]) + " und " + n[-1]


def uhr(t: float) -> str:
    return f"{int(t // 60)} {int(t % 60):02d}"      # gesprochen "6 27"


@dataclass
class Option:
    name: str
    satz: str
    wert: float
    faktoren: int                 # wie viele unabhaengige Fakten den Satz tragen
    dringend: bool = False

    @property
    def thema(self) -> str:
        return {"zurueck": "gefahr", "druck": "druck", "freeze": "gefahr", "gruppe": "objective",
                "obj_plan": "objective"}.get(self.name, "back" if self.name.startswith("back") else "")


@dataclass
class Entscheider:
    jungle: Jungletracker = field(default_factory=Jungletracker)
    _kandidat: tuple[str, float] | None = None
    _zuletzt: float = -1e9
    _gesagt: dict[str, float] = field(default_factory=dict)
    _einmal: set = field(default_factory=set)
    aktuell: Option | None = None          # die beste Option dieses Takts (fuer Fragen: "was soll ich tun?")

    # --- Optionen ------------------------------------------------------------------

    def optionen(self, b: Bewertung, platten: bool) -> list[Option]:
        rolle = b.ich.rolle
        if rolle == "JUNGLE" or b.ich.tot or b.pos is None:
            return []
        aus: list[Option] = []
        lane_phase = b.zeit < LANE_PHASE_BIS
        g = b.lane
        j = b.jungler
        wahrsch = self.jungle.wahrscheinlich(b.zeit)
        meine = LANE_SEITE.get(rolle)
        j_bei_mir = wahrsch.get(meine, 0.5) if meine else 0.5
        gefahr = komponist.gefahr(b)
        verwundbar = komponist.verwundbar(b)
        wert_kraefte, _ = b.kraefte()
        vorsprung = b.vorsprung_satz()
        welle = b.welle
        schiebt_ihr = welle is not None and welle[0] >= welle[1] + 2
        schiebt_er = welle is not None and welle[1] >= welle[0] + 2
        j_offen = komponist.jungler_offen(b)

        # 1) Gefahr: jemand, den du nicht siehst, ist vor dir am Turm - und du kannst es dir nicht leisten.
        #    Der Lane-Gegner kurz im Busch ist kein Gank (Test 26.09.: "Shen kann schon da sein" alle 2 min);
        #    er zaehlt allein nur, wenn du wenig Leben hast und er staerker ist.
        if b.zum_turm is not None and b.zum_turm >= 5 and not b.unter_eigenem_turm:
            fremde = [x for x in gefahr if not (g and x.s.name == g.s.name)]
            # nur wer eben (<= 15 s) nah gesehen wurde: lange Fehlende sind Sache der Tief-Regel (regeln._tief_ohne_sicht)
            knapp = [x for x in fremde if x.ankunft is not None and x.ankunft < b.zum_turm - 1
                     and x.seit is not None and x.seit <= 15]
            lane_allein = (not fremde and g is not None and any(x.s.name == g.s.name for x in gefahr)
                           and b.leben is not None and b.leben < 0.45 and wert_kraefte <= -0.5)
            ausgesetzt = bool(verwundbar) or len(knapp) >= 2 or (b.tiefe or 0) >= 0.5
            if (knapp and ausgesetzt) or lane_allein:
                x = knapp[0] if knapp else g
                wer = _namen_kurz(knapp) if len(knapp) >= 2 else x.champion
                wann = komponist._wann(x)
                if len(knapp) >= 2:
                    wann = wann.replace("kann", "können", 1)
                aus.append(Option("zurueck", f"{wer} {wann}, du brauchst {sek(b.zum_turm)} zum Turm. "
                                             f"Jetzt zurück" + (f", {verwundbar[0]}." if verwundbar else "."),
                                  200, 2 + bool(verwundbar), dringend=True))

        # 2) Frueher Jungler-Plan: Startseite bekannt -> wo kommt der erste Gank?
        if lane_phase and meine and self.jungle.start and 95 <= b.zeit <= 200 and j and not j.s.tot:
            gank = anders(self.jungle.start)
            if gank == meine and (j.seit is None or j.seit >= 15):
                aus.append(Option("gank_erwartet",
                                  f"{j.champion} hat {self.jungle.start} angefangen ({self.jungle.start_grund}): "
                                  + ("ab Minute 2 kommt er zu dir" if b.zeit < 120 else "er kann jetzt jederzeit kommen")
                                  + ". Welle nicht über die Mitte, Ward in den Fluss.",
                                  150, 3))
            elif gank != meine:
                aus.append(Option("gank_weg",
                                  f"{j.champion} hat {self.jungle.start} auf deiner Seite angefangen: sein erster Gank "
                                  f"kommt {gank}. Bis etwa Minute 3 kannst du hart spielen.", 90, 2))

        # 3) Druck: Lane-Gegner sichtbar, du staerker, Jungler tot oder sicher weit weg, Leben gut.
        #    (Camille-Partie 26.09., 4:42/4:50: "Gragas 19 s zu dir, zurueck" und 8 s spaeter "Spiel auf Rumble")
        j_weit = j is None or j.s.tot or (not j.unbekannt and j.ankunft is not None and j.ankunft >= 25
                                          and j_bei_mir < 0.5)
        if g and not g.s.tot and g.seit is not None and g.seit < 2 and not gefahr \
                and (b.leben or 1) >= 0.6 and wert_kraefte >= 1 and j_weit:
            grund = f"{j.champion} ist {'tot' if j.s.tot else j.ort}" if j and (j.s.tot or not j.unbekannt) else ""
            aus.append(Option("druck", f"Spiel auf {g.champion}: {vorsprung}" + (f", {grund}" if grund else "")
                              + (f" - {b.trade}." if b.trade else "."),
                              60 + 20 * wert_kraefte, 2 + bool(grund)))

        # 4) Recall-Planung mit Reihenfolge: Welle -> back -> Objective
        braucht_back = b.gold >= 1100 or (b.leben is not None and b.leben < 0.45)
        if braucht_back and not gefahr:
            ob = b.objective
            grund = (f"{b.gold // 100 * 100} Gold" if b.gold >= 1100 else f"{int(b.leben * 100)} Prozent Leben")
            if schiebt_er and welle[2] is not None and welle[2] <= 0.45:
                satz = (f"{grund}, aber seine Welle mit {welle[1]} läuft auf deinen Turm: erst abfarmen, "
                        f"dann back - sonst frisst der Turm dein Gold.")
                aus.append(Option("back_warten", satz, 70, 3))
            elif schiebt_ihr:
                satz = f"{grund}: Welle in den Turm, dann back"
                if ob and 45 <= ob[1] <= 150:
                    satz += f" - dann bist du rechtzeitig zurück für {OBJ_NAME[ob[0]]} um {uhr(b.zeit + ob[1])}."
                else:
                    satz += "."
                aus.append(Option("back_plan", satz, 80 + b.gold / 50, 2 + bool(ob)))
            elif (k := naechste_kanone(b.zeit, b.ich.rolle)) and k - b.zeit <= 45:
                aus.append(Option("back_kanone", f"{grund}: Kanonenwelle kommt {uhr(k)} - die in den Turm schieben, "
                                                 f"dann back.", 75 + b.gold / 50, 3))

        # 5) Objective-Vorlauf 60-120 s: Reihenfolge planen (Welle, Reset, Weg)
        ob = b.objective
        if ob and 60 <= ob[1] <= 120 and meine is not None:
            name = OBJ_NAME[ob[0]]
            nah = (ob[0] == "drache" and meine == "unten") or (ob[0] != "drache" and meine == "oben") \
                or rolle == "MIDDLE"
            if nah:
                reset = b.gold >= 900 or (b.leben is not None and b.leben < 0.6)
                seite = ("Mid", "Bot") if ob[0] == "drache" else ("Mid", "Top")
                prio = komponist._prio_satz(b, tuple(l for l in seite if l != {"TOP": "Top", "BOTTOM": "Bot",
                                                                                   "UTILITY": "Bot", "MIDDLE": "Mid"}.get(rolle)))
                satz = (f"{name} in {sek(ob[1])}: " + ("jetzt Welle rein und back, " if reset else "Welle langsam aufbauen, ")
                        + f"spätestens {uhr(b.zeit + ob[1] - 30)} an der Grube sein" + (f" - {prio}." if prio else "."))
                aus.append(Option("obj_plan", satz, 90, 2 + reset + bool(prio)))

        # 6) Freeze/Sicherheit: Jungler wahrscheinlich bei dir, Welle vor deinem Turm, du schiebst nicht
        if lane_phase and j and not j.s.tot and j_bei_mir >= 0.6 and (j.seit is None or j.seit >= 20) \
                and welle and welle[2] is not None and welle[2] <= 0.45 and not schiebt_ihr and b.zeit >= 115:
            aus.append(Option("freeze", f"Welle vor deinem Turm halten: {j.champion} ist wahrscheinlich auf deiner Seite "
                                        f"({int(j_bei_mir * 100)} Prozent), seit {sek(j.seit or b.zeit)} nicht gesehen.",
                              55, 3))

        # 7) Nach der Lane-Phase: Seitenwelle oder Gruppe
        if not lane_phase and rolle in ("TOP", "MIDDLE", "BOTTOM"):
            if ob and 5 <= ob[1] <= 60:
                weg = f", {sek(b.zum_objective)} Weg" if b.zum_objective else ""
                aus.append(Option("gruppe", f"{OBJ_NAME[ob[0]]} in {sek(ob[1])}: Welle crashen und zum Team{weg}.",
                                  100, 2))
            elif not gefahr:
                sichtbar = [x for x in b.gegner if not x.s.tot and x.sichtbar]
                if len(sichtbar) >= 3:
                    aus.append(Option("seite", f"{len(sichtbar)} Gegner sichtbar weg von dir: Seitenwelle drücken, "
                                               f"Platten und Turm, bis sich einer zeigt.", 70, 2))
        return aus

    # --- Sprechen ----------------------------------------------------------------------

    def pruefe(self, b: Bewertung | None, platten: bool):
        """Die Ansage dieses Takts (regeln.Ansage) oder None."""
        from .regeln import HINWEIS, WICHTIG, Ansage
        if b is None:
            self.aktuell = None
            return None
        opts = [o for o in self.optionen(b, platten) if o.faktoren >= 2]
        if not opts:
            self.aktuell, self._kandidat = None, None
            return None
        beste = max(opts, key=lambda o: o.wert)
        self.aktuell = beste
        if self._kandidat is None or self._kandidat[0] != beste.name:
            self._kandidat = (beste.name, b.zeit)
            if not beste.dringend:
                return None
        if not beste.dringend and b.zeit - self._kandidat[1] < HALTEN:
            return None
        einmal = beste.name in ("gank_erwartet", "gank_weg")
        if einmal and beste.name in self._einmal:
            return None
        if b.zeit - self._zuletzt < ABSTAND and not beste.dringend:
            return None
        if b.zeit - self._gesagt.get(beste.name, -1e9) < GLEICH_SPERRE:
            return None
        self._zuletzt = b.zeit
        self._gesagt[beste.name] = b.zeit
        if einmal:
            self._einmal.add(beste.name)
        prio = WICHTIG if (beste.dringend or einmal or beste.wert >= 100) else HINWEIS
        return Ansage(beste.satz, prio, f"plan:{beste.name}", gueltig=8 if beste.dringend else 15, sperre=20,
                      thema=beste.thema)
