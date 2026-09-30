"""Der Sprechplan: wer redet wann.

Ein guter Coach redet wenig. Regeln liefern Ansagen, der Plan waehlt:
  - nie zwei Saetze uebereinander (geschaetzte Sprechdauer + Pause),
  - das Dringendste zuerst; was zu lange wartet, ist ueberholt und faellt weg,
  - derselbe Schluessel kommt erst nach seiner Sperrzeit wieder,
  - Hinweise (niedrigster Vorrang) nur nach einer laengeren Ruhe.
Alles in Spielzeit - so laeuft eine Aufnahme exakt wie das Live-Spiel.
"""
from __future__ import annotations

import re
import threading
import time

from .regeln import AN_LEBENDE, HINWEIS, RUECKZUG, SOFORT, WICHTIG, Ansage

def _zeichen_pro_s() -> float:
    try:
        from . import wissen
        return float(wissen.lade("kern").get("stimme", {}).get("zeichen_pro_s", 14.0))
    except Exception:
        return 14.0


# Killian +25 % gemessen 26.09. nachts: 14,3 Zeichen/s; seit Auftrag 002 aus [stimme] (Killian +50 %: 16,6); live fragt
# der Plan die Stimme
ZEICHEN_PRO_SEKUNDE = _zeichen_pro_s()
PAUSE = 1.5                  # zwischen zwei Saetzen (2,0 bis 26.09.; die Schaetzung ist jetzt ehrlicher)
RUHE_VOR_HINWEIS = 8.0       # Hinweise nur, wenn es so lange still war
RUHE_VOR_FLASH = 1.5         # Auftrag 007: "X ohne Flash" (3 Woerter, gilt 8 s) - mit 8 s Ruhe erklang sie nach jedem
                             # Satz kurz davor nie und galt trotzdem als gemeldet (213624 8:41 "Rumble ohne Flash")
THEMA_SPERRE = 30.0          # zwei Ansagen zum selben Thema (back, druck, gefahr, objective) nicht so kurz hintereinander
THEMA_SPERRE_JE = {"gefahr": 12.0,   # Gefahr aendert sich schnell: eine neue Warnung darf eher kommen
                   "druck": 8.0}     # ein Kampf-Fenster auch: aus "trade hart" wird mit seinem Flash ein Kill
# Nach einer Warnung kein "geh rein" (Camille-Partie 15:37/15:39: "rein" und "zurueck" in 2 s). Umgekehrt
# nicht: eine Gefahr darf immer kommen, auch direkt nach einem Druck-Satz.
WIDERSPRUCH = {"druck": ("gefahr", 15.0), "seite": ("gefahr", 15.0)}
# Live 26.09. 21:21: Flash-Meldungen warteten 9-17 s hinter langen Plaenen. Diese Ansagen sind lang und nicht eilig -
# eine wichtige, die es nicht ist (Flash, Gefahr, Jungler), darf sie abbrechen.
UNTERBRECHBAR = ("briefing", "midgame", "cs", "lane_tot", "aufbruch", "plan:back", "gold", "recallfenster",
                 "vorwarnung", "spike", "wiedereinstieg", "kontrollauge", "ward:")
# ... und bist du tot, ist jede Lane-Anweisung ueberholt (Live 21:21, 6:11: "Schieb die Welle in seinen Turm" -
# Carlos: "Warum sagst du mir das, obwohl ich selber tot war?")
NUR_LEBEND = ("lane_tot", "fenster", "plan:", "gold", "recallfenster", "anlauf", "jungler_sicht", "tief", "leben",
              "lane_fehlt", "lane_recall", "ohneflash", "ward:", "aufbruch", "kontrollauge", "level")


GESAGT_NACH = 4.0      # Sekunden: so lange laeuft eine Ansage mindestens, bevor eine gleich wichtige sie abbricht

# Sprechbudget: Nachlauf 21:21 nach allen Umbauten - der Coach sprach 88 % der Spielzeit, alles Neue musste warten
# oder abbrechen ("geisteskrank zu spaet"). Hat er in der letzten Minute schon mehr als die Haelfte geredet, wartet
# das Beiwerk (Kauf, Objective-Vorlauf, Wards, Spikes, Aufbruch ...) und verfaellt, wenn es zu alt wird. Gefahr,
# Flash, Kampf-Fenster, Jungler kommen immer durch.
BUDGET_FENSTER = 60.0
BUDGET_ANTEIL = 0.5
BEIWERK = ("gold", "plan:back", "objstart", "objgegner", "vorwarnung", "cs", "aufbruch", "spike", "kontrollauge",
           "ward:", "wiedereinstieg", "recallfenster", "tipp", "wardplan", "item:", "jungler6", "lane_tot")


def kern(a: Ansage) -> bool:
    """Eine Ansage des Entscheidungskerns (Buch 0, 9.6) - oder des Makro-Strategen, der seinen Plan-Satz ersetzt
    (Auftrag 015)."""
    return a.schluessel.startswith(("kern:", "stratege:"))


_RAUS = re.compile(r"\bjetzt zurück|\braus zu\b", re.I)


INFO_WARTEN_S = 3.0          # Auftrag 023, 2: so lange darf ein Plan-Satz eine Pflicht-Info hoechstens aufhalten
PFLICHT_INFOS = ("kern:INFO_FLASH", "kern:INFO_JUNGLER", "kern:INFO_LANE", "kern:INFO_EINDRINGLING")


def pflicht_info(a: Ansage) -> bool:
    # Auftrag 025: Paket-Uebergaenge mit Vorrang; der Herzschlag (027) und der Start-Satz unterbrechen nichts
    return a.schluessel in PFLICHT_INFOS or (a.schluessel.startswith("kern:PAKET_")
                                             and a.schluessel not in ("kern:PAKET_HERZ", "kern:PAKET_START"))


def gefahr(a: Ansage) -> bool:
    """Nur eine Gefahr darf einen laufenden Satz abbrechen (Partie 144655: Saetze brachen nach ein, zwei Woertern ab -
    "Satzfetzen"): Thema Gefahr (Kern-GEFAHR, Unterzahl, Jungler), ein Gegner, der auf dich zulaeuft, oder ein Rat zum
    Rueckzug ("Vi seit 6 Sekunden weg ... Jetzt zurueck" - vor dem Tod 19:55, Testpartie 2). Der Todesrueckblick nicht,
    auch wenn er "geh zurueck" zitiert (140253, 8:34: "... 18 Sekunden davor hiess es: geh zurueck")."""
    if a.schluessel.startswith(("tod", "wiedereinstieg")):
        return False
    return (a.thema == "gefahr" or a.schluessel.startswith("anlauf") or bool(RUECKZUG.search(a.text))
            or bool(_RAUS.search(a.text)))


def unterbrechbar(a: Ansage) -> bool:
    """Lange Saetze (ueber ~14 s) duerfen immer von etwas Wichtigem abgebrochen werden - sonst wartet alles."""
    return a.unterbrechbar or a.schluessel.startswith(UNTERBRECHBAR) or len(a.text) > 180 or a.prio == HINWEIS


def _stimmt(a: Ansage) -> bool:
    """Stimmt die Ansage noch (regeln.Regelwerk._noch_wahr)? Eine kaputte Pruefung laesst sie gelten."""
    if a.pruefe is None:
        return True
    try:
        return bool(a.pruefe())
    except Exception:
        return True


# Frisch statt vollstaendig (Carlos, Live 26.09. 23:20: "die Top-Aktualitaet ist das Wichtigste ueberhaupt"): so
# lange darf eine Ansage hoechstens warten, egal was die Regel wollte - das Briefing ausgenommen.
WARTEN_HOECHSTENS = {SOFORT: 6.0, WICHTIG: 10.0, HINWEIS: 20.0}
ACH_NEE = 8.0     # Sekunden: so lange nach einem widerrufenen Satz beginnt der neue zum selben Thema mit "Ach nee"
DOPPEL_S = 10.0   # Auftrag 028, 1.3: so lange ist derselbe Satz aus keiner Quelle ein zweites Mal zu hoeren
HIN_UND_HER_S = 5.0   # Auftrag 027, 1.4: so lange nach einem Plan-Satz kein Satz mit anderem Ziel (Gefahr ausgenommen)
WARTEN = "<warten>"


def _kern_text(text: str) -> str:
    """Der Satz ohne Vorsatz ("Los:", "Plan geändert:", "Ach nee:"), Satzzeichen und Gross/klein - fuer Doppel."""
    t = re.sub(r"^\W*((los|plan geändert|ach nee|stimmt\. neu|neu)\s*:\s*)+", "", text.strip(), flags=re.I)
    return " ".join(re.findall(r"\w+", t.lower()))
# "Geh zurueck" eben gehoert - ein zweites aus anderem Grund sagt nichts Neues (Nachlauf 194524, 16:46-17:23: viermal
# "geh zurueck zu deinem Mid-Tier-1-Turm" in 37 s, aus Gold, Jungler und Unterzahl). Gezaehlt ab dem Moment, in dem
# die Worte "geh zurueck" im Satz fallen - kommt ein neues vorher, ist es das direktere und darf abbrechen.
# Eine Gefahr (SOFORT: "Vi ist direkt bei dir") kommt immer.
RUECKZUG_SPERRE = 12.0
# Buch 0, Schritt 2 (Kapitel 9.2): zwischen zwei Ansagen ausser SOFORT liegen mindestens `abstand_s` Sekunden
# (wissen/kern.toml [sprechen]) - das Briefing ausgenommen
GEFAHR_EBEN = 10.0     # so lange nach einer Gefahr-Ansage wirft der Stratege nichts ein (Kapitel 14)


def _abstand_s() -> float:
    try:
        from .kern import konfig
        return float(konfig()["sprechen"]["abstand_s"])
    except Exception:
        return 12.0


class Sprechplan:
    def __init__(self, sprecher):
        self.sprecher = sprecher
        self.warte: list[Ansage] = []
        self.frei_ab = -1e9           # Spielzeit, ab der wieder gesprochen werden darf
        self.zuletzt: dict[str, float] = {}
        self.gesagt: list[Ansage] = []
        self._einwurf: list[Ansage] = []
        self.thema_zuletzt: dict[str, float] = {}
        self._schloss = threading.Lock()
        self._laeuft: Ansage | None = None      # was gerade gesprochen wird (bis frei_ab)
        self._reden: list[tuple[float, float]] = []   # (Beginn, geschaetzte Dauer) - fuer das Sprechbudget
        self._ich_tot = False
        self._widerruf: tuple[float, str, str] | None = None   # (Spielzeit, Thema, Schluessel-Art) des widerrufenen
        self._rueckzug_gehoert = -1e9    # Spielzeit, zu der das letzte "geh zurueck" beim Spieler ankommt
        self.kern = None                 # kern.Kern: Modus fuer die Einwuerfe des Strategen (Kapitel 14)
        self.verworfen_sicher: list = []  # Auftrag 028, 3: (Zeit, Schluessel, Text, Grund) - am Sprech-Tor gefallen
        self.abstand_s = _abstand_s()

    def _melder(self, a: Ansage, ab: float):
        """Die Stimme meldet ersten Ton und Ende in Wanduhr; umgerechnet auf Spielzeit ab dem Moment der Abgabe.
        'widerrufen': mitten im Satz stimmte er nicht mehr - die Sperren fallen, damit das Neue gleich kommt."""
        def melde(art: str, jetzt: float) -> None:
            if art == "ton":
                a.ton = round(a.gesprochen + (jetzt - ab), 2)
                return
            a.ganz = art in ("ende", "ende_widerrufen")
            # Spielzeit des Endes: live die gemessene Dauer, beim Nachspielen (Wanduhr steht fast) mindestens die
            # geschaetzte - sonst galt "Ach nee" (8 s Wanduhr) dort fuer Minuten Spielzeit
            spiel = a.gesprochen + (jetzt - ab)
            if art in ("ende", "ende_widerrufen"):
                spiel = max(spiel, a.gesprochen + len(a.text) / ZEICHEN_PRO_SEKUNDE)
            if art == "verworfen" and a.ton is None:
                # nie erklungen (Frage an der Sprechtaste, veraltet): die Sperre faellt - stimmt es nach der
                # Antwort noch, darf das Regelwerk es frisch sagen
                self.zuletzt.pop(a.schluessel, None)
                if a.thema:
                    self.thema_zuletzt.pop(a.thema, None)
                return
            # ganz gesagt, stimmte am Ende aber nicht mehr ("Ekko ist oben" - er taucht am Drachen auf): die Sperre
            # faellt, die Korrektur beginnt mit "Ach nee". Nur bei einer Gefahr - ein Ward-Hinweis, an dem du vorbei
            # bist, wird nicht wiederholt (144655, 8:43/8:59). Nicht beim Kern: seine Pruefung heisst "derselbe Plan",
            # nicht "wahr" (144655, 4:49: "Ach nee: Bleib an deinem Top-Tier-1-Turm" nach einem erledigten Schritt)
            if art == "ende_widerrufen" and not kern(a) and a.thema == "gefahr":
                self.zuletzt.pop(a.schluessel, None)
                self.thema_zuletzt.pop(a.thema, None)
                self._widerruf = (spiel, a.thema, a.schluessel.split(":")[0])
            if art == "widerrufen":
                if RUECKZUG.search(a.text):
                    self._rueckzug_gehoert = -1e9
                self.zuletzt.pop(a.schluessel, None)
                if a.thema:
                    self.thema_zuletzt.pop(a.thema, None)
                self._widerruf = (spiel, a.thema, a.schluessel.split(":")[0])
        return melde

    def _ein_plan(self, a: Ansage, zeit: float) -> str | None:
        """Auftrag 028, 1: der Text, mit dem `a` gesprochen wird - None, wenn er den aktiven Plan ohne Grund wechselt
        (binnen WECHSEL_S nach dem letzten gesprochenen Plan-Satz, aus welcher Quelle auch immer). Ein Kern-Plan-Satz
        mit eigenem Grund ("Drück die Bot-Welle: Ezreal ist tot") wird hoerbar: "Plan geändert: ..."."""
        try:
            from .kern.herzschlag import WECHSEL_S, halte_ziel, plan_ursprung, plan_ziel_von, wechsel_grund, ziele_vertraeglich
        except Exception:
            return a.text
        z = plan_ziel_von(a)
        if not z:
            return a.text
        aktiv = next(((x.gesprochen, halte_ziel(x.text, plan_ziel_von(x)), plan_ziel_von(x)) for x in reversed(self.gesagt[-8:])
                      if x.gesprochen is not None and plan_ziel_von(x)), None)
        if aktiv is not None and zeit - aktiv[0] < HIN_UND_HER_S and not ziele_vertraeglich(aktiv[2], z) \
                and a.thema != "gefahr":
            # Auftrag 027, 1.4 / 028, 1: auch ein begruendeter Wechsel kommt nicht binnen 5 s nach dem letzten
            # Plan-Satz (Stub 028: sieben Mal "Farm Top" -> 4 s spaeter "Plan geändert: Platte ...") - er wartet
            return WARTEN
        if wechsel_grund(a, aktiv[1] if aktiv is not None and zeit - aktiv[0] < WECHSEL_S else None):
            return a.text
        if aktiv is None or zeit - aktiv[0] >= WECHSEL_S or ziele_vertraeglich(aktiv[2], z):
            return a.text
        if aktiv[1] != "back" and ": " in a.text and a.schluessel.startswith("kern:") \
                and not a.schluessel.startswith("kern:PAKET_") \
                and zeit - (plan_ursprung(sorted((x.gesprochen, plan_ziel_von(x)) for x in self.gesagt[-20:]
                                                 if x.gesprochen is not None and plan_ziel_von(x))) or aktiv[0]) >= 5.0:
            return f"Plan geändert: {a.text}"
        return None

    def _doppel(self, text: str, zeit: float) -> bool:
        """Auftrag 028, 1.3: kein Doppel binnen DOPPEL_S aus beliebiger Quelle - derselbe Satz, oder einer, der nur
        wiederholt, was eben gesagt wurde (231200 22:00-22:22: "Raus jetzt, nach Top." alle 4 s; "Los: X" 5 s nach X;
        die Kauf-Kette zweimal). Wer etwas anfuegt ("..., nicht zu Swain"), sagt Neues und darf."""
        k = _kern_text(text)
        if len(k) < 8:
            return False
        los = text.lstrip().lower().startswith("los:")     # er steht: das Stehen ist das Neue (Auftrag 027, 1)
        for x in reversed(self.gesagt[-10:]):
            if x.gesprochen is None or zeit - x.gesprochen > DOPPEL_S:
                continue
            if los and not x.text.lstrip().lower().startswith("los:"):
                continue
            kx = _kern_text(x.text.split("“ – ", 1)[-1] if x.schluessel == "antwort" else x.text)
            if kx == k or kx.startswith(k):
                return True
        return False

    def _vorbereiten(self, a: Ansage) -> None:
        """Sie kommt als naechste dran: die Stimme synthetisiert ihren Anfang schon (einmal je Ansage) - dann klingt
        sie ohne die 0,2-0,6 s des Dienstes."""
        if getattr(a, "_vorbereitet", False):
            return
        a._vorbereitet = True
        if f := getattr(self.sprecher, "vorbereiten", None):
            try:
                f(a.text)
            except Exception:
                pass

    def _gestorben(self, zeit: float) -> None:
        """Auftrag 018, 6 (183125 38:10-38:36: ein langer Satz lief weiter, als Carlos schon tot war): beim Tod bricht
        der laufende Satz sofort ab, was in der Stimme wartet, faellt weg - der Tod-Satz kommt gleich danach."""
        la = self._laeuft
        if la is not None and zeit < self.frei_ab and not la.schluessel.startswith("tod"):
            if hasattr(self.sprecher, "abbrechen"):
                self.sprecher.abbrechen()
            if self._reden:
                t0, _ = self._reden[-1]
                self._reden[-1] = (t0, max(0.0, zeit - t0))
            self.frei_ab = zeit
            self._laeuft = None

    def _noch_wahr(self, a: Ansage):
        return lambda: _stimmt(a) and not (self._ich_tot and a.schluessel.startswith(NUR_LEBEND))

    def geredet(self, zeit: float) -> float:
        """Sekunden Sprechzeit in den letzten BUDGET_FENSTER Sekunden (abgebrochene zaehlen bis zum Abbruch)."""
        ab = zeit - BUDGET_FENSTER
        self._reden = [(t, d) for t, d in self._reden if t + d > ab]
        return sum(min(t + d, zeit) - max(t, ab) for t, d in self._reden if t < zeit)

    def einwerfen(self, a: Ansage) -> None:
        """Aus einem anderen Thread (Stratege, Briefing): kommt beim naechsten Takt dran."""
        with self._schloss:
            self._einwurf.append(a)

    def neu(self, ansagen: list[Ansage]) -> None:
        with self._schloss:
            eingeworfen, self._einwurf = self._einwurf, []
        # Stratege (Kapitel 14): das Briefing einmal; Midgame-Plan und situative Saetze nur ausserhalb von KAMPF
        # und nicht direkt nach einer Gefahr
        modus = getattr(getattr(self.kern, "modus", None), "aktuell", None)
        jetzt = getattr(self, "_jetzt", None)
        if modus == "KAMPF" or (self.gesagt and self.gesagt[-1].thema == "gefahr" and self.gesagt[-1].gesprochen
                                is not None and jetzt is not None and jetzt - self.gesagt[-1].gesprochen < GEFAHR_EBEN):
            eingeworfen = [a for a in eingeworfen if a.schluessel == "briefing"]
        # Buch 0, 9.1 ab Schritt 3: der Midgame-Plan des Strategen laeuft als INFO durch den Kern (Dashboard)
        if getattr(self.kern, "stellung", "alt") in ("neu", "makro"):
            for a in [a for a in eingeworfen if a.schluessel == "midgame"]:
                self.kern.info_dazu(a.zeit, a.text)
            eingeworfen = [a for a in eingeworfen if a.schluessel != "midgame"]
        for a in [*eingeworfen, *ansagen]:
            if a.zeit - self.zuletzt.get(a.schluessel, -1e9) < a.sperre:
                continue
            if a.schluessel != "briefing":
                a.gueltig = min(a.gueltig, WARTEN_HOECHSTENS.get(a.prio, 10.0))
            self.warte = [w for w in self.warte if w.schluessel != a.schluessel]  # die neuere gilt
            self.warte.append(a)

    def takt(self, zeit: float, ich_tot: bool = False) -> Ansage | None:
        self._jetzt = zeit
        # Dasselbe Thema eben erst gesagt ("2000 Gold: ... back" 9:47 und 9:53, Camille-Partie 26.09.):
        # die zweite faellt weg - ausser sie ist SOFORT (Gefahr darf immer)
        # Kern-Ansagen (Buch 0, 9.6) laufen an Themen-, Widerspruchs- und Rueckzugssperre vorbei - der Kern haelt
        # seinen Plan selbst und prueft sein Budget selbst
        self.warte = [a for a in self.warte
                      if zeit - a.zeit <= a.gueltig + (self.abstand_s if getattr(a, "_budget", False) else 0.0)
                      and (kern(a) or (
                          not (a.thema and a.prio < SOFORT
                               and zeit - self.thema_zuletzt.get(a.thema, -1e9) < THEMA_SPERRE_JE.get(a.thema, THEMA_SPERRE))
                          and not (a.thema in WIDERSPRUCH
                                   and zeit - self.thema_zuletzt.get(WIDERSPRUCH[a.thema][0], -1e9) < WIDERSPRUCH[a.thema][1])
                          and not (a.prio < SOFORT and 0 <= zeit - self._rueckzug_gehoert < RUECKZUG_SPERRE
                                   and RUECKZUG.search(a.text))))]
        if ich_tot and not getattr(self, "_ich_tot", False):
            self._gestorben(zeit)
        self._ich_tot = ich_tot
        if ich_tot:
            # Auftrag 018, 6: nichts, was einen Lebenden wegschickt ("geh zurueck", "hinter den Turm")
            self.warte = [a for a in self.warte if not a.schluessel.startswith(NUR_LEBEND)
                          and not AN_LEBENDE.search(a.text)]
        self.warte = [a for a in self.warte if _stimmt(a)]     # was nicht mehr stimmt, faellt weg
        if not self.warte:
            return None
        kandidaten = self.warte
        if self.geredet(zeit) > BUDGET_ANTEIL * BUDGET_FENSTER:
            # "X ohne Flash" zaehlt beim Kern nicht zum Budget (kern/sprechen.FREI, Auftrag 002) - hier auch nicht: sonst
            # verfiel sie beim vollen Budget, galt aber als gemeldet (Auftrag 007: 213624 8:41 "Rumble ohne Flash")
            kandidaten = [a for a in self.warte if not ((a.prio == HINWEIS and a.schluessel != "kern:INFO_FLASH")
                                                        or a.schluessel.startswith(BEIWERK))]
            if not kandidaten:
                return None
        # bei gleichem Vorrang geht eine Gefahr vor (Pruefpartie 2, 19:39: "Du hast 5900 Gold ... recall" verdraengte
        # "Du stehst tief, Varus und Rakan seit 32 s weg" - 16 s vor dem Tod)
        # Auftrag 004, Teil A 2: ein Wendepunkt stellt sich vor alle wartenden PLAN-Saetze (er unterbricht nicht)
        # Auftrag 023, 2: Pflicht-Infos (Flash, Jungler, Lane-Gegner weg) gleich nach der Gefahr, vor jedem Plan-Satz
        # Auftrag 027, 1.3: wer still steht und wartet oder im Brunnen ankommt, hoert seine Anweisung vor der naechsten
        # Info (091311 27:06 hinter zwei "Büsche meiden"; 125902 15:39 der Kauf hinter "Warwick Mid")
        a = max(kandidaten, key=lambda a: (a.prio, a.thema == "gefahr",
                                           a.schluessel in ("kern:PAKET_STILL", "kern:PAKET_KAUF"), pflicht_info(a),
                                           a.thema == "wendepunkt", a.zeit))
        frei = self.frei_ab + ((RUHE_VOR_FLASH if a.schluessel == "kern:INFO_FLASH" else RUHE_VOR_HINWEIS)
                               if a.prio == HINWEIS else 0.0)
        # Live 26.09. 21:21: das Briefing (~50 s) hielt "Gragas hat Flash benutzt" 9 s und Vaynes Flash 16 s auf.
        # Laeuft etwas Unterbrechbares, darf eine wichtige Ansage es abbrechen.
        laeuft = self._laeuft
        # Jede Ansage beginnt mit der Handlung - nach GESAGT_NACH Sekunden ist das Entscheidende heraus. Dann darf
        # eine gleich wichtige Neuigkeit den Rest abbrechen (Live 21:21: Sonas Flash wartete 17 s hinter zwei Saetzen).
        # (eine Gefahr darf auch lang sein - "Du stehst tief, und Varus und Rakan ..." hat ueber 180 Zeichen, Testpartie 2,
        # 19:38, 16 s vor dem Tod)
        abbrechen = (laeuft is not None and zeit < self.frei_ab and gefahr(a) and a.prio >= WICHTIG
                     and (unterbrechbar(laeuft)
                          or (laeuft.gesprochen is not None and zeit - laeuft.gesprochen >= GESAGT_NACH
                              and a.prio >= laeuft.prio)))
        # Auftrag 023, 2: eine Pflicht-Info wartet hoechstens INFO_WARTEN_S - laeuft ein Plan-Satz laenger, bricht
        # sie ihn ab (nie eine Gefahr, nie eine andere Info)
        if not abbrechen and pflicht_info(a) and laeuft is not None and not gefahr(laeuft) \
                and not pflicht_info(laeuft) and self.frei_ab - zeit > INFO_WARTEN_S:
            abbrechen = True
        # Auftrag 027, 1.3: in der Basis kommt der Kauf sofort - er bricht eine Jungler-Info oder einen Satz ab, dessen
        # Handlung schon heraus ist (091311 12:34: "Amumu unterer Fluss" hielt den Kauf 4 s auf), nie eine Gefahr
        if not abbrechen and a.schluessel == "kern:PAKET_KAUF" and laeuft is not None and zeit < self.frei_ab \
                and not gefahr(laeuft) and laeuft.schluessel != a.schluessel \
                and (laeuft.schluessel.startswith(("kern:INFO_", "kern:PAKET_"))
                     or (laeuft.gesprochen is not None and zeit - laeuft.gesprochen >= GESAGT_NACH)):
            abbrechen = True
        if zeit < frei and a.prio < SOFORT and not abbrechen:
            self._vorbereiten(a)
            return None
        # Eine Gefahr bricht die andere nicht nach einer Sekunde ab (Nachlauf 194524, 17:22/17:23: "Vi ist oben und kann
        # in 7 Sekunden ..." - weg, bevor ihr "geh zurueck" kam, fuer "Braum und Warwick sind tot"): erst ihre Handlung
        if (a.prio == SOFORT and laeuft is not None and laeuft.prio == SOFORT and not unterbrechbar(laeuft)
                and zeit < self.frei_ab and getattr(self.sprecher, "beschaeftigt", True)
                and laeuft.gesprochen is not None and zeit - laeuft.gesprochen < GESAGT_NACH):
            self._vorbereiten(a)
            return None
        # was keine Gefahr ist, wartet, bis die Stimme frei ist - auch SOFORT (Zahlen, Buff, Technik)
        if (a.prio < SOFORT or not gefahr(a)) and getattr(self.sprecher, "beschaeftigt", False) and not abbrechen:
            self._vorbereiten(a)
            return None     # die Stimme spricht noch (live exakt statt geschaetzt)
        # Budget (Buch 0, 9.2): mindestens abstand_s seit der letzten Ansage - ausser SOFORT und dem Briefing
        letzte = next((x.gesprochen for x in reversed(self.gesagt) if x.gesprochen is not None), None)
        if (a.prio < SOFORT and a.schluessel != "briefing" and not kern(a) and not abbrechen and letzte is not None
                and zeit - letzte < self.abstand_s):
            # "wird gesagt, sobald wieder Platz ist und er dann noch gilt" (9.2): wer nur am Budget wartet, darf
            # abstand_s laenger warten - ob er noch stimmt, prueft weiter seine Pruefung (_stimmt)
            for w in self.warte:
                if w.prio < SOFORT:
                    w._budget = True
            self._vorbereiten(a)
            return None
        self.warte.remove(a)
        # Auftrag 028, 1: EIN Plan auch in der Reihenfolge des Sprechens - die Regel im Kern sieht, was er erzeugt;
        # hier zaehlt, was zuletzt GESPROCHEN wurde (231200 5:29: "Back jetzt", dann aus der Schlange "Geh zu deiner
        # Top-Welle"). Ein Wechsel binnen 20 s ohne Grund faellt weg; ein Kern-Satz mit eigenem Grund wird hoerbar.
        if (neu_text := self._ein_plan(a, zeit)) is None:
            return None
        if neu_text is WARTEN:
            self.warte.append(a)              # gleich noch einmal - die Wartefrist der Ansage laeuft weiter
            return None
        a.text = neu_text
        # Auftrag 028, 3: der Kill-Check fuer jede Quelle, gegen die Lage JETZT - nicht die beim Erzeugen
        if self.kern is not None and (gruende := self.kern.unsicher_jetzt(a.text)):
            self.verworfen_sicher.append((zeit, a.schluessel, a.text, "; ".join(gruende)))
            return None
        if self._doppel(a.text, zeit):
            return None
        if self.kern is not None and hasattr(self.kern, "teamnamen"):
            a.text = self.kern.teamnamen(a.text, a.schluessel, a.thema or "")     # Auftrag 028, 6.1: "ihre Sejuani"
        # "Ach nee - Ekko ist beim Drachen": der Satz davor wurde mitten drin widerrufen (Carlos' Wunsch 26.09.)
        w = self._widerruf
        # nur, wenn der neue Satz die neue Fassung des alten ist: dieselbe Art, oder beide eine Gefahr (Position) -
        # nicht "Ach nee: Vi hat kein Flash" nach einem abgebrochenen "nimm den Kampf an" (Stimmprobe 27.09.)
        if w is not None and zeit - w[0] <= ACH_NEE and (
                a.schluessel.split(":")[0] == w[2] or (a.thema == "gefahr" and w[1] == "gefahr")):
            # eigener Teil "Ach nee:" (vorgewaermt), dahinter der Satz wie sonst - sein Anfang liegt im Speicher.
            # Grossschreibung bleibt: meist beginnt der Satz mit einem Champion
            a.text = "Ach nee: " + a.text
            self._widerruf = None
        if (auffrischen := getattr(a, "auffrischen", None)) is not None:
            # Kritik 008 (173159 22:17 "Back jetzt: 29 Prozent Leben" bei 13 %): was sich bis zum Sprechen geaendert
            # hat, sagt der Satz so, wie es jetzt ist - der Kern gibt dafuer eine Funktion mit
            try:
                a.text = auffrischen(a.text)
            except Exception:
                pass
        a.gesprochen = zeit
        self.zuletzt[a.schluessel] = zeit
        if a.thema:
            self.thema_zuletzt[a.thema] = zeit
        self.frei_ab = zeit + len(a.text) / ZEICHEN_PRO_SEKUNDE + PAUSE
        if abbrechen and self._reden:          # der abgebrochene zaehlt nur bis jetzt
            t0, _ = self._reden[-1]
            self._reden[-1] = (t0, max(0.0, zeit - t0))
        if abbrechen and self._rueckzug_gehoert > zeit:     # sein "geh zurueck" kam nicht mehr an
            self._rueckzug_gehoert = -1e9
        if m := RUECKZUG.search(a.text):
            self._rueckzug_gehoert = zeit + m.start() / ZEICHEN_PRO_SEKUNDE
        self._reden.append((zeit, len(a.text) / ZEICHEN_PRO_SEKUNDE))
        self.sprecher.sage(a.text, dringend=(gefahr(a) and (a.prio == SOFORT or abbrechen)) or (abbrechen and pflicht_info(a)),
                           melde=self._melder(a, time.monotonic()),
                           noch_wahr=self._noch_wahr(a))
        self._laeuft = a
        self.gesagt.append(a)
        return a
