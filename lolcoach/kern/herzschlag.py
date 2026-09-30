"""Auftrag 027, 1: der Herzschlag - solange du lebst und nicht kaempfst, hast du immer eine gesprochene, gueltige,
positive Anweisung: was jetzt, und was danach.

Carlos, 091311 (15:41): "Ich bleib so lange ab jetzt stehen, bis du mir konkrete Arbeitspakete gibst." Er stand, und es
kam nichts - 91 % "Paket-Abdeckung" zaehlten ein INTERNES Paket, nicht das, was er hoerte. Der Herzschlag schaut
deshalb auf das Gesprochene (`gesagt`) und spricht selbst, wenn dort keine gueltige positive Anweisung steht:

  - Tot: 12 s vor dem Respawn Kauf (im Laden geht das schon im Tod) und Ziel.
  - Basis: Ankunft oder Respawn im Brunnen mit Gold fuer einen Kauf - sofort die Kauf-Kette, danach das Ziel.
  - Stillstand: >= 5 s ohne Bewegung (nicht im Recall-Kanal) - die aktuelle Anweisung.
  - Auffrischung: 25 s ohne positive Anweisung - die aktuelle mit neuer Info, oder eine neue.
  - Spielende: Inhibitor offen und >= 3 Gegner lange tot - "Jetzt beenden: alle auf den Nexus."
Die Vorlage kommt aus dem aktiven Plan des Kerns (Welle, Turm, Back, Objective, Gruppe, Hilfe) - verlaesslich ohne
Claude. "Warum nicht" haengt nur noch als Nachsatz daran (`nachsatz`).
"""
from __future__ import annotations

import re
from types import SimpleNamespace as NS_

AUFFRISCHEN_S = 25.0
START_S = 30.0              # vor dem Spielbeginn (Brunnen, Einkauf) schweigt der Herzschlag
STILLSTAND_S = 5.0
STILL_SAGEN_S = 3.5         # der Satz entsteht vorher, damit er nach STILLSTAND_S gesprochen ist
TOT_VORLAUF_S = 12.0
MIN_ABSTAND_S = 8.0
NEGATIV_SCHL = ()      # "warum nicht" und Vorsicht tragen seit 027 die positive Anweisung selbst - der Text entscheidet
KEINE_ANWEISUNG = ("kern:INFO_", "kern:LAGEBILD", "kern:technik", "kern:TEAMPLAN", "tod", "briefing",
                   "kern:PAKET_COUNTDOWN", "kern:PAKET_MEILENSTEIN", "kern:PAKET_ERLEDIGT", "kern:BESTAETIGUNG",
                   "kern:ERINNERUNG")
HANDLUNG = re.compile(r"\b(geh|lauf|crash|farm|drück|druecke?|kauf|back|hilf|halte?n?|bleib|zurück|raus|nimm|push|"
                      r"warte|stell|verteidig|freez|schieb|folge|rotier|beenden?|tp|teleportier|jetzt|drache|baron|"
                      r"herold|welle|rein\b|dreh)\w*", re.I)
PAKET_ENDE = ("ERLEDIGT", "ABGEBROCHEN", "BUDGET_AB")
GRUBE = {"drache": "am Drachen", "baron": "am Baron", "herold": "am Herold", "larven": "an den Larven"}
NUR_NEIN = re.compile(r"\b(nicht hin|nicht rein|nicht zu|nicht vor|nicht dort|kein back|nicht back|stehst tief|"
                      r"fehlen|vorsicht)\b", re.I)


def positiv(a) -> bool:
    """Ist diese gesprochene Ansage eine positive Anweisung (was du tun sollst)?"""
    s = a.schluessel or ""
    if s in NEGATIV_SCHL or s.startswith(KEINE_ANWEISUNG):
        return False
    text = a.text or ""
    if s == "antwort":
        teil = text.split("–", 1)[-1]
        return bool(HANDLUNG.search(teil)) and not negativ_allein(teil)
    if s.startswith(("kern:", "stratege:")):
        return not negativ_allein(text)
    return False


def plan_ziel_von(a) -> str | None:
    """Das Ziel eines positiven Plan-Satzes (Welle, Turm, Drache, Back ...) - None fuer alles andere; die Kauf-Kette
    ist die Fortsetzung des Backs und hat kein eigenes Ziel."""
    text = a.text or ""
    if a.schluessel in ("antwort", "kern:PAKET_KAUF") or text.startswith(("Kauf", "Verkauf", "Stell dein", "Du lebst")) \
            or not positiv(a):
        return None
    # Auftrag 028, 1: Gefahr und Kampf-Rufe unterbrechen den Plan, sie SIND keiner - danach gilt wieder der Plan
    # (091311 13:21: "Rein auf Malphite!" hielt 20 s lang jede Anweisung fern)
    if getattr(a, "thema", "") == "gefahr" or a.schluessel in KAMPF_RUFE:
        return None
    # auch "Überheblichkeit und Langschwert kaufen, dann Top" (Stratege, 183125 9:27) ist die Kauf-Kette, und ein
    # blosser Timer ("Drache in 92 Sekunden", 133448 16:21) ist keine Anweisung
    if re.search(r"\bkauf\w*\b.*\bdann\b", text, re.I) or re.fullmatch(r"[\w\s'-]+ in \d+ Sekunden\.?", text.strip()):
        return None
    from ..stratege_live import plan_ziel
    # ein Ereignis vorn ist kein Ziel: "Sie haben den Herold. Weiter die Top-Welle drücken." (101426 15:40)
    kopf = re.match(r"^(Sie haben|Ihr habt|Euer|Eure|Ihr|Ihre)\b[^.]*\.\s+(?=\S)", text)
    if kopf and not re.search(r"\b(drück|geh|nimm|farm|crash|back|hol)\w*", kopf.group(0), re.I):
        text = text[kopf.end():]
    z = plan_ziel(text)
    return None if z in (None, "zurueck") else z


KAMPF_RUFE = ("kern:REIN", "kern:RAUS", "kern:DREHEN", "kern:ZURUECK", "kern:JUNGLER_NAH", "kern:technik")
WECHSEL_S = 20.0           # Auftrag 028, 1: ein Planwechsel in 20 s nach dem letzten Plan-Satz braucht einen Grund
GRUND_SCHL = ("antwort", "kern:PAKET_ABGEBROCHEN", "kern:PAKET_BUDGET_AB", "kern:ZURUECK", "kern:RAUS",
              "kern:JUNGLER_NAH", "kern:VORSICHT")


def wechsel_grund(a) -> bool:
    """Auftrag 028, 1.1: darf dieser Satz den aktiven Plan wechseln? Gefahr (R1, neuer Gegner, Abbruch), ein echtes
    Event oder besseres Play MIT dem Grund vorn ("Plan geändert: ...", "Jetzt, wo ...", "Udyr weg: ...", ein
    Wendepunkt), oder Carlos fragt."""
    s = a.schluessel or ""
    t = (a.text or "").strip()
    if getattr(a, "thema", "") == "gefahr" or s in GRUND_SCHL or s.startswith("kern:INFO_"):
        return True
    if getattr(a, "_kategorie", None) in ("WENDEPUNKT", "GEFAHR") or getattr(a, "kategorie", None) in ("WENDEPUNKT",
                                                                                                         "GEFAHR"):
        return True
    if re.match(r"^\W*(plan geändert|jetzt, wo|stimmt\. neu|neu:)", t, re.I):
        return True
    if re.match(r"^(Sie haben|Ihr habt|Euer|Eure|Ihr|Ihre)\b[^.:]*\b(weg|genommen|down|gefallen|fällt|tot)\b", t):
        return True
    kopf = t.split(": ", 1)[0] if ": " in t else ""
    return bool(kopf) and bool(re.search(r"\b(tot|weg|gesehen|drin|down|gefallen|lebt wieder|gebackt)\b", kopf, re.I))


def ziele_vertraeglich(a: str, b: str) -> bool:
    """ "welle" und "welle:top" sind dasselbe Ziel; Back und Kauf auch."""
    return a == b or (a.startswith("welle") and b.startswith("welle") and "welle" in (a, b))


def negativ_allein(text: str) -> bool:
    """Sagt der Satz nur, was du NICHT tun sollst? (Auftrag 027, 1.2: "Warum nicht" steht nie allein.)"""
    if not NUR_NEIN.search(text or ""):
        return False
    # ein Satz, der mit "Nicht"/"Kein" beginnt, faellt ganz weg ("Nicht zu Yorick: Welle bringt mehr."), sonst nur der
    # verneinte Satzteil ("Welle zu deinem Turm ziehen, farmen, kein Trade bis zum Axiombogen." behaelt "farmen")
    rest = re.sub(r"(?:^|(?<=[.!?]))\s*(?:nicht|kein)\b[^.!?]*[.!?]?", " ", text, flags=re.I)
    rest = re.sub(r"[^.!?,;:]*\b(nicht|kein|fehlen|vorsicht|stehst tief)\b[^.!?,;:]*[.!?,;:]?", " ", rest, flags=re.I)
    return not HANDLUNG.search(rest)


class Herzschlag:
    def __init__(self):
        self._letzt_positiv = -1e9      # Spielzeit der letzten gesprochenen positiven Anweisung
        self._letzt_herz = -1e9
        self._gilt_ab = -1e9            # was vor einem Paket-Ende gesagt wurde, gilt nicht mehr
        self._vorher: tuple | None = None
        self._raus_t = -1e9                 # wann du den Brunnen zuletzt verlassen hast
        self.kauf = self.still = False
        self._tot_gesagt = False
        self._basis_gesagt = -1e9
        self._war_basis = False
        self._ende_gesagt = -1e9
        self._still_seit: tuple | None = None
        self._still_gesagt = False

    def takt(self, kern, m, modus: str | None, gesagt: list, paket_ende: bool = False,
             nur_still: bool = False, diesmal: list = ()) -> str | None:
        """Der Satz, den der Kern jetzt sagen muss - None, wenn eine gueltige positive Anweisung laeuft. `self.kauf`
        sagt dem Kern danach, ob es der Kauf war (der hat Vorrang im Sprechplan). `paket_ende`: ein Paket ist eben
        erledigt oder abgebrochen - was davor galt, gilt nicht mehr, das naechste kommt gleich."""
        self.kauf = self.still = False
        # auch ein stilles Ende zaehlt (im Kampf, ohne Satz - 192113 12:00): das Paket-Protokoll entscheidet
        fertig = getattr(getattr(kern, "pakete", None), "fertig", None) or []
        ende_t = max((v[0] for pk in list(fertig)[-4:] for v in pk.verlauf if v[1] in PAKET_ENDE), default=-1e9)
        if paket_ende or ende_t > self._gilt_ab:
            self._letzt_positiv = -1e9
            self._gilt_ab = max(ende_t, m.zeit or 0.0) if paket_ende else ende_t
            self._letzt_herz = min(self._letzt_herz, self._gilt_ab - MIN_ABSTAND_S)
        for a in gesagt[-12:]:
            t = a.gesprochen if a.gesprochen is not None else a.zeit
            if t is not None and t > self._letzt_positiv and t >= self._gilt_ab and positiv(a):
                self._letzt_positiv = t
        z = m.zeit
        if m.b is None or z < START_S:
            return None                      # vor dem Spielbeginn nichts (140253 0:00, Szenario 0000)
        if m.tot:
            self._still_seit = None
            basis = False
            if not self._tot_gesagt and 0 < (m.respawn or 0.0) <= TOT_VORLAUF_S:
                self._tot_gesagt = True
                self.kauf = True
                self._basis_gesagt = z               # beim Respawn im Brunnen nicht noch einmal
                return self._sagen(z, kauf_satz(kern, m, respawn=m.respawn))
            return None
        self._tot_gesagt = False
        if modus == "KAMPF":
            self._still_seit = None
            return None
        # Spielende hat den hoechsten Wert
        # (nie unter R1 - 231200 24:44 "Jetzt beenden: alle auf den Nexus" mit wenig Leben, API-Nachspiel 027)
        leben = getattr(m, "leben", None)
        r1 = leben is not None and leben < (getattr(kern, "cfg", None) or {}).get("schranken", {}).get(
            "vor_leben_min", 0.4)
        if not nur_still and not r1 and z - self._ende_gesagt >= 30.0 and (s := ende_satz(m)) is not None:
            self._ende_gesagt = z
            return self._sagen(z, s)
        basis = m.bereich == "basis_eigen"
        if self._war_basis and not basis:
            self._raus_t = z
        # ein Ankommen ist es erst nach 10 s draussen (173159 14:23 und 14:38: der Rand des Brunnens flackerte)
        neu_basis = basis and not self._war_basis and z - self._raus_t >= 10.0
        self._war_basis = basis
        rufe = getattr(kern, "_back_rufe", None) or []
        # (16 s: der Kanal beginnt oft erst ein paar Sekunden nach dem Ruf - 144655 5:04 "Bleib dabei" im Recall)
        kanal = bool(rufe) and z - rufe[-1] <= 16.0 and m.pos is not None
        # im Recall-Kanal heisst: nach einem Back-JETZT still stehen (nicht "Welle rein, dann back", waehrend du
        # drueckst - 173159 12:05 kam der Kauf mitten im Crashen)
        stand = getattr(kern, "_stand", None)
        sofort = getattr(kern, "_back_sofort", None)
        # (nach "Welle rein, dann back" erst, wenn die Welle Zeit hatte - 6 s - und du dann stehst)
        kanal_kauf = kanal and stand is not None and z - stand[0] >= 1.5 and stand[0] >= rufe[-1] - 2.0 \
            and ((sofort is not None and sofort >= rufe[-1] - 1.0) or z - rufe[-1] >= 6.0)
        k = getattr(m.b, "kauf", None)
        # Basis: der Kauf kommt schon im Recall-Kanal (dann ist er beim Ankommen gesagt) oder sofort beim Ankommen
        # beim Ankommen noch einmal, wenn der Kanal-Kauf schon 12 s her ist (125902 3:58: 16 s Heimweg dazwischen;
        # 173159 12:05: nach 8 s kam derselbe Kauf zweimal)
        if not nur_still and (basis or kanal_kauf) and z - self._basis_gesagt >= (12.0 if neu_basis else 45.0) \
                and k is not None and k.kaufen \
                and (neu_basis or kanal_kauf or z - self._letzt_positiv >= 3.0):
            self._basis_gesagt = z
            self.kauf = True
            return self._sagen(z, kauf_satz(kern, m, gesagt=gesagt))
        # Stillstand: am selben Fleck, nicht im Recall-Kanal, nicht in der Basis - der Satz kommt schon nach
        # STILL_SAGEN_S, damit er nach 5 s zu hoeren ist (der Sprechplan braucht bis zu 2 s)
        # (auch im Brunnen: 091311 15:17-15:51 stand Carlos 34 s dort und wartete auf eine Anweisung)
        # der Einkauf ist wie der Kanal: im Brunnen die 10 s nach einer Kauf-Anweisung (dann kauft er gerade)
        einkauf = basis and any("kauf" in (a.text or "").lower() for a in gesagt[-6:]
                                if (a.gesprochen if a.gesprochen is not None else a.zeit or -1e9) >= z - 10.0)
        if m.pos is None or kanal or einkauf:
            self._still_seit = None
        else:
            from ..bewertung import abstand
            if self._still_seit is None or abstand(self._still_seit[1], m.pos) > 120.0:
                self._still_seit = (z, m.pos)
                self._still_gesagt = False
            elif not self._still_gesagt and z - self._still_seit[0] >= STILL_SAGEN_S \
                    and self._letzt_positiv >= self._still_seit[0]:
                self._still_gesagt = True        # waehrend des Stehens schon eine Anweisung gehoert - reicht
            elif not self._still_gesagt and z - self._still_seit[0] >= STILL_SAGEN_S:
                self._still_gesagt = True
                self.still = True            # Vorrang wie eine Pflicht-Info (125902 7:18: hinter "Warwick oben" zu spaet)
                if nur_still:                # in Gefahr: nur der Satz des sicheren Plans, sonst die letzte Warnung
                    from .handlung import SICHER
                    pl = getattr(getattr(kern, "fuehrer", None), "plan", None)
                    return self._sagen(z, vorlage(kern, m, nur_plan=True) if pl is not None and pl.art in SICHER
                                       else warn_satz(gesagt, z))
                if basis:
                    # im Brunnen: noch Gold - die Kauf-Kette; sonst wohin es geht (nicht der Kauf-Plan ein zweites Mal)
                    if k is not None and k.kaufen and z - self._basis_gesagt >= 45.0:
                        self._basis_gesagt = z
                        self.kauf, self.still = True, False
                        return self._sagen(z, kauf_satz(kern, m, gesagt=gesagt))
                    if (ziel := _ziel_kurz(kern, m)):
                        return self._sagen(z, geh_satz(ziel, "Raus jetzt,"))
                return self._sagen(z, auffrischen(kern, m, gesagt, still=True))
        # (sagt der Kern in diesem Takt selbst eine positive Anweisung, ist das die Auffrischung - 125902 27:21:
        # "Ihr Nexus-Turm jetzt" zweimal in einem Takt)
        # (nicht im Recall-Kanal: "Bleib dabei" 13 s nach "Back jetzt", 144655 5:04 und 102112 14:58)
        if not kanal and z - self._letzt_positiv >= AUFFRISCHEN_S \
                and z - self._letzt_herz >= MIN_ABSTAND_S and not any(positiv(a) for a in diesmal):
            if nur_still:
                # in Gefahr: die Handlung der letzten Warnung noch einmal (091311 24:18-25:01: 43 s nach "Raus
                # jetzt: Amumu ist da" nichts), sonst nichts - nie ein Vorwaerts-Satz
                return self._sagen(z, warn_satz(gesagt, z))
            return self._sagen(z, auffrischen(kern, m, gesagt))
        return None

    def verworfen(self) -> None:
        """Der Kern hat den Satz nicht gesagt (kein Hin und Her binnen 5 s) - der Herzschlag gilt als nicht geschlagen."""
        if self._vorher is not None:
            self._letzt_herz, self._letzt_positiv = self._vorher
            self._vorher = None
        if self.still:
            self._still_gesagt = False

    def _sagen(self, z: float, text: str | None) -> str | None:
        if not text:
            return None
        self._vorher = (self._letzt_herz, self._letzt_positiv)
        self._letzt_herz = z
        self._letzt_positiv = z
        return text


def warn_satz(gesagt: list, jetzt: float) -> str | None:
    """Die Handlung der letzten Warnung (<= 60 s): "Raus jetzt: Amumu ist da." -> "Raus jetzt, Amumu ist da.";
    "Zurück unter euren Mid-Turm: drei kommen." bleibt. Ohne Warnung: None."""
    warn = ("kern:JUNGLER_NAH", "kern:VORSICHT", "kern:ZURUECK", "kern:RAUS", "kern:PAKET_BUDGET_AB",
            "kern:PAKET_ABGEBROCHEN")
    for a in reversed(list(gesagt)[-8:]):
        t = a.gesprochen if a.gesprochen is not None else a.zeit
        if t is None or jetzt - t > 60.0:
            break
        if (a.thema == "gefahr" or a.schluessel in warn) and positiv(a):
            return a.text
    return None


def eben_gesagt(text: str, gesagt: list, jetzt: float, fenster: float = 60.0) -> bool:
    """Wurde dieser Satz (sein Anfang, ohne Zahlen) in den letzten `fenster` Sekunden schon gesprochen - auch als
    Anfang eines "warum nicht"-Nachsatzes?"""
    kopf = _kern_des_satzes(text)
    return any(_kern_des_satzes(a.text or "") == kopf for a in gesagt[-10:]
               if (a.gesprochen if a.gesprochen is not None else a.zeit or -1e9) >= jetzt - fenster)


def auffrischen(kern, m, gesagt: list, fenster: float = 60.0, still: bool = False) -> str | None:
    """Die Auffrischung. Auftrag 028, 2: eine Anweisung kommt nur mit etwas NEUEM wieder - dem naechsten Schritt
    ("Farm Top, danach back: 1100 Gold fuer Eklipse"), einem Countdown <= 10 s bis zur Handlung ("Kanone in 6
    Sekunden, dann Back") oder einem neuen Grund aus der Lage ("... : Drache spawnt in 40 Sekunden"). Nackte
    Bestaetigungen ("Bleib dabei.", auch "Bleib dabei, Kanone in 18 Sekunden.") sind Fuellsaetze - lieber schweigen.
    `still`: Carlos steht - dann die Anweisung selbst, mit "Los:" (das Stehen ist das Neue)."""
    text = vorlage(kern, m)
    if not text:
        return None
    # Auftrag 028, 1: EIN Plan - widerspricht die Vorlage dem juengst gesprochenen Plan-Satz (< 20 s), gilt der
    # (sonst faellt der Herzschlag am Sprech-Tor weg und Carlos steht ohne Anweisung: 091311 13:21)
    z = plan_ziel_von(NS_(schluessel="kern:PAKET_HERZ", text=text))
    for a in reversed(list(gesagt)[-8:]):
        t = a.gesprochen if a.gesprochen is not None else None
        za = plan_ziel_von(a) if t is not None else None
        if za:
            if z and m.zeit - t < WECHSEL_S and not ziele_vertraeglich(za, z):
                text = a.text.split("“ – ", 1)[-1]
            break
    if not eben_gesagt(text, gesagt, m.zeit, fenster):
        return text
    kopf = text.split(": ")[0].split(", ")[0].rstrip(".")
    # 1. der naechste Schritt
    danach = (getattr(kern, "danach_text", None) or "").strip().rstrip(".")
    if danach and HANDLUNG.search(danach) and danach.lower() not in text.lower():
        s = f"{kopf}, danach {danach}."
        if not eben_gesagt(s, gesagt, m.zeit, fenster):
            return s
    # 2. ein Countdown <= 10 s bis zur Handlung
    if (c := countdown(kern, m)) is not None and not eben_gesagt(c, gesagt, m.zeit, 15.0):
        return c
    # 3. ein neuer Grund aus der Lage: ein Objective, das bald kommt
    swift = getattr(getattr(m, "p", None), "modus", None) == "SWIFTPLAY"      # dort gelten die Zeiten nicht
    e = min((e for e in getattr(kern, "zeitleiste", None) or [] if 5 <= e.in_s(m.zeit) <= 60
             and e.art == "objective" and not swift), key=lambda e: e.in_s(m.zeit), default=None)
    if e is not None:
        s = f"{kopf}: {e.text} in {e.in_s(m.zeit)} Sekunden."
        if not eben_gesagt(s, gesagt, m.zeit, fenster):
            return s
    return f"Los: {text}" if still else None


def countdown(kern, m) -> str | None:
    """Auftrag 028, 6.5: die Kanone nur, wenn sie die naechste Handlung ausloest - "Kanone in 6 Sekunden, dann Back"
    (Plan mit Back danach), hoechstens 10 s vorher."""
    u = getattr(kern, "uhren", None)
    pl = getattr(getattr(kern, "fuehrer", None), "plan", None)
    if u is None or u.kanone_in is None or not 2 <= u.kanone_in <= 10 or pl is None:
        return None
    schritte = [s.lower() for s in (getattr(pl.handlung, "schritte", None) or [])]
    if pl.art in ("WELLE_REIN_UND_BACK",) or "back" in schritte:
        return f"Kanone in {int(u.kanone_in)} Sekunden, dann Back."
    return None


def geh_satz(ziel: str, vorn: str = "Geh") -> str:
    """Aus der Kurzform von wohin ("Top", "zum Drachen", "TP auf deine Top-Welle") ein Satz."""
    if ziel in ("Top", "Mid", "Bot"):
        ziel = f"nach {ziel}"
    if ziel.startswith("TP "):
        return f"{ziel}." if vorn == "Geh" else f"{vorn} {ziel}."
    return f"{vorn} {ziel}."


def _kern_des_satzes(text: str) -> str:
    """Der Anfang eines Satzes ohne Zahlen - zwei Fassungen desselben Plans sind gleich."""
    return re.sub(r"\d+", "#", text.split(":")[0].split(",")[0]).strip().lower()[:40]


def _ziel_kurz(kern, m) -> str:
    # Auftrag 007: ein Ziel je Basis-Aufenthalt - hat der Kern es schon genannt, gilt es (102112 37:35 "zum Baron")
    bz = getattr(kern, "_basis_ziel", None)
    if bz is not None and len(bz) > 2 and bz[2] and m.bereich == "basis_eigen" \
            and bz[0] >= getattr(kern, "_basis_seit", 1e9):
        return bz[2]
    try:
        from .modi.basis import wohin
        from . import fuehren
        h = wohin(m, kern.cfg, "BASIS")
        return (h.daten.get("kurz") or fuehren.kurz(h)) if h is not None else ""
    except Exception:
        return ""


def kauf_satz(kern, m, respawn: float | None = None, gesagt: list = ()) -> str | None:
    """Kauf-Kette mit Ziel: "Kauf Tiamat und Langschwert, dann Top." - im Tod mit der Zeit bis zum Respawn. Ist das
    Ziel eben (<= 60 s) schon gesagt, bleibt es weg (213624 12:47 "Zum Drachen", dann "..., dann zum Drachen")."""
    k = getattr(m.b, "kauf", None)
    ziel = _ziel_kurz(kern, m)
    if ziel and any(ziel.lower() in (a.text or "").lower() for a in list(gesagt)[-8:]
                    if (a.gesprochen if a.gesprochen is not None else a.zeit or -1e9) >= m.zeit - 60.0):
        ziel = ""
    if k is None or not k.kaufen:
        if respawn is not None and ziel:
            return f"Du lebst in {int(respawn)} Sekunden: dann {ziel}."
        return None
    from .. import kaufplan
    from .modi import liste
    teile = [kaufplan._akk(x) for x in k.kaufen]
    # Auftrag 009, 4: das erste Bauteil mit seinem Ziel ("Kauf Langschwert für die Eklipse")
    eigen = len(k.kaufen) - sum(len(s) for _, s in getattr(k, "weitere", None) or [])
    ziel_item = getattr(k, "item", None)
    i = next((j for j, x in enumerate(k.kaufen[:min(2, eigen)]) if kaufplan.mit_ziel(x, ziel_item) != x), None)
    if i is not None:
        teile[i] = kaufplan.mit_ziel(k.kaufen[i], ziel_item)
    kopf = f"Du lebst in {int(respawn)} Sekunden. " if respawn is not None else ""
    vk = f"Verkauf {k.verkaufen}, dann kauf" if k.verkaufen else "Kauf"
    if k.verkaufen and k.verkaufen == "Kontroll-Auge":
        vk = "Stell dein Kontroll-Auge, dann kauf"
    # die Wortgrenze (14, Szenario s23): erst faellt das Ziel, dann die Stuecke hinten (vorn steht das Wichtigste)
    grenze = (getattr(kern, "cfg", None) or {}).get("sprechen", {}).get("max_woerter", 14)
    for n in range(len(teile), 0, -1):
        for mit_ziel in ((True, False) if ziel else (False,)):
            s = f"{kopf}{vk} {liste(teile[:n])}" + (f", dann {ziel}." if mit_ziel else ".")
            if len(s.split()) <= grenze:
                return s
    return f"{kopf}{vk} {teile[0]}."


def vorlage(kern, m, nur_plan: bool = False) -> str | None:
    """Die aktuelle positive Anweisung aus dem Plan des Kerns. `nur_plan`: ohne Rueckfall (Welle, Ziel) - in Gefahr
    gilt nur, was der Plan selbst sagt."""
    if nur_plan:
        pl = kern.fuehrer.plan
        s = (pl.handlung.satz or "") if pl is not None else ""
        return s if s and HANDLUNG.search(s) and not negativ_allein(s) else None
    from . import fuehren
    pl = kern.fuehrer.plan
    text = ""
    # Swiftplay: die Objective-Zeiten der Vorschau sind die aus Classic (Szenario swiftplay-keine-classic-zeiten)
    swift = getattr(getattr(m, "p", None), "modus", None) == "SWIFTPLAY"
    if pl is not None:
        h = pl.handlung
        if h.art == "KAUFEN" and m.bereich != "basis_eigen" and not m.tot:
            pass                             # der Kauf-Satz nur im Brunnen (Szenario 0322: "Kauf ..." auf der Lane)
        elif h.art == "FARMEN":
            text = (not swift and fuehren.farmen_satz(h, m, kern.zeitleiste, kern.danach_text, kern.cfg)) \
                or fuehren.stumm_satz(h)
        elif h.art in ("HALTEN", "HALTEN_UNTER_TURM", "WELLE_HALTEN"):
            text = fuehren.halten_satz(m, kern.zeitleiste, kern.danach_text, kern.cfg) or h.satz or ""
        elif not h.stumm:
            text = h.satz or ""
    grube = (m.bereich or "").removeprefix("grube:") if (m.bereich or "").startswith("grube:") else None
    # ... aber nur, wenn das Team laut Minimap dort steht (091311 20:46 im Nachspiel: "Bleib am Baron bei deinem Team",
    # das Team war am Drachen - dieselbe Pruefung wie Teil 3)
    ta = (getattr(kern, "_team_am_letzt", None) or (None, {}))[1] or {}
    if grube in ("drache", "baron") and ta.get("bekannt", 0) >= 2 and ta.get(grube, 0) == 0:
        grube = None
    if (not text or not HANDLUNG.search(text)) and grube in GRUBE:
        # 091311 27:05: am Drachen stehend hiess es "Geh zu deiner Top-Welle" - wer an der Grube wartet, bleibt dort
        text = f"Bleib {GRUBE[grube]} bei deinem Team und halte die Sicht."
    if not text or negativ_allein(text) or not HANDLUNG.search(text):
        # keine Handlung darin (etwa nur Rechner-Zahlen "Karthus: klar vorn: ihr 1000 Burst ..."): die Vorlage.
        # Nicht, wenn zwei Gegner bei dir sind - dann spricht die Gefahr (140253 8:27: "Geh zu deiner Mid-Welle",
        # Brand und Yasuo kamen, 5 s spaeter "Raus")
        b = getattr(m, "b", None)
        nah = [g for g in (getattr(b, "gegner", None) or []) if getattr(g, "sichtbar", False) and not g.s.tot
               and getattr(g, "abstand", None) is not None and g.abstand <= 2000]
        if len(nah) >= 2:
            # dann gilt die letzte Warnung (091311 28:53: zwei Gegner nah, "Raus, zu eurem Mid-Turm!" 17 s vorher)
            return warn_satz(getattr(getattr(kern, "transport", None), "gesagt", None) or [], m.zeit)
        # ... und nicht gleich nach einer Warnung (140253 8:05 "Brand gesehen: zurück hinter die Welle", 8:27 "Geh zu
        # deiner Mid-Welle") - dann gilt die Warnung
        warn = ("kern:JUNGLER_NAH", "kern:VORSICHT", "kern:ZURUECK", "kern:RAUS")
        for a in reversed((getattr(getattr(kern, "transport", None), "gesagt", None) or [])[-6:]):   # juengste zuerst
            t = a.gesprochen if a.gesprochen is not None else a.zeit
            if t is not None and m.zeit - t <= 25.0 and (a.thema == "gefahr" or a.schluessel in warn):
                if not positiv(a):
                    return None
                # die Warnung sagte, was zu tun ist - ihre Handlung noch einmal ("Zurück hinter die Welle.");
                # steht die Handlung vor dem Doppelpunkt ("Zurück unter euren Turm: zwei kommen."), der ganze Satz
                s = (a.text or "").split(": ", 1)[-1].strip()
                s = s if HANDLUNG.search(s) else (a.text or "").strip()
                return s[:1].upper() + s[1:]
        lane = m.meine_lane or m.lane_hier
        danach = (kern.danach_text or "").split(":")[0]
        w = getattr(m, "welle", None)
        leer = w is not None and getattr(w, "zustand", None) in ("LEER", "GECRASHT_BEI_IHM", "GROSS_ZU_IHM")
        if danach and not negativ_allein(danach) and HANDLUNG.search(danach):
            text = f"{danach[:1].upper()}{danach[1:]}."
        elif lane and getattr(m, "lane_phase", True) is not False and not leer:
            text = f"Geh zu deiner {lane}-Welle und farm sie."
        elif (ziel := _ziel_satz(kern, m)):
            # nach der Lane-Phase oder mit leerer Welle: wohin der Kern dich schickt, mit seinem Grund (192113 20:46:
            # die leere Top-Welle tief bei ihnen war kein Ziel; A2: "Geh zur Mid-Welle." allein ist zu vage)
            text = ziel
        elif lane:
            text = f"Geh zu deiner {lane}-Welle und farm sie."
        else:
            return None
    from .modi import kuerze                  # die Wortgrenze wie jeder Plan-Satz (Auftrag 002, S2.3)
    kurz = kuerze(text, (getattr(kern, "cfg", None) or {}).get("sprechen", {}).get("max_woerter", 14))
    if HANDLUNG.search(kurz) and not negativ_allein(kurz):
        text = kurz            # (nicht, wenn die Handlung hinter dem Doppelpunkt stand: "Kanone kommt 36:02: die ...")
    else:
        # dann ganze Saetze von vorn, solange sie passen ("Kanone kommt 20 17: die noch rein, dann back.", s23)
        grenze = (getattr(kern, "cfg", None) or {}).get("sprechen", {}).get("max_woerter", 14)
        saetze, n = [], 0
        for s in re.split(r"(?<=[.!?])\s+", text):
            if saetze and n + len(s.split()) > grenze:
                break
            saetze.append(s)
            n += len(s.split())
        text = " ".join(saetze)
    # (Auftrag 028, 6.5: keine Kanone als Anhaengsel mehr - sie kommt nur als Countdown vor der Handlung, `countdown`)
    return text


def _ziel_satz(kern, m) -> str:
    """Der WOHIN-Satz des Kerns als Anweisung: "Dann zur Mid-Welle: sie laeuft sonst in deinen Turm." -> "Geh zur
    Mid-Welle: sie laeuft sonst in deinen Turm." (ohne Grund die Kurzform)."""
    try:
        from .modi.basis import wohin
        h = wohin(m, kern.cfg, "BASIS")
    except Exception:
        h = None
    s = (getattr(h, "satz", None) or "") if h is not None else ""
    s = re.sub(r"^(Dann|Zurück)\s+", "", s)
    if "sonst niemand" in s:
        # die lange Floskel einmal je Partie (R6, Szenario wohin-kurz) - der Herzschlag sagt, was du dort tust
        kurz = (h.daten.get("kurz") or "") if h is not None else ""
        if kurz.endswith("-Welle"):
            return f"Geh {kurz} und farm sie."
        s = s.split(":")[0]
    if s and HANDLUNG.search(s) and ":" in s:
        s = s[:1].upper() + s[1:]
        return s if s.split()[0].lower() not in ("zur", "zum", "zu", "nach") else f"Geh {s[:1].lower()}{s[1:]}"
    ziel = _ziel_kurz(kern, m)
    return geh_satz(ziel) if ziel else ""


def aktiver_plan_satz(gesagt: list, jetzt: float, fenster: float = 60.0) -> str | None:
    """Auftrag 028, 1: der juengst GESPROCHENE Plan-Satz (jede Quelle, <= `fenster` s) - der eine aktive Plan."""
    for a in reversed(list(gesagt)[-10:]):
        t = a.gesprochen if a.gesprochen is not None else None
        if t is None:
            continue
        if jetzt - t > fenster:
            break
        if plan_ziel_von(a):
            return (a.text or "").split("“ – ", 1)[-1]
    return None


def nachsatz(positiv_text: str | None, warum: str, gesagt: list = (), jetzt: float | None = None,
             grenze: int = 14) -> str | None:
    """ "Warum nicht" nur als Nachsatz zu einer positiven Anweisung: "Crash die Welle. Nicht zu Yorick: 10 s weg."
    Die Wortgrenze gilt fuer den ganzen Satz (Szenario s23): erst faellt der Grund, dann ist die Anweisung eben
    gesagt "Bleib dabei"."""
    if not positiv_text:
        return None
    wer, _, grund = warum.partition(" kämpft: nicht hin, ")
    if not grund:
        return None
    pos = positiv_text.rstrip(".")
    if jetzt is not None and eben_gesagt(pos, gesagt, jetzt):
        # dieselbe Anweisung eben erst: nur ihr Kopf, das Neue ist die abgewogene Chance (Auftrag 028, 2 - kein
        # "Bleib dabei." mehr, 091311 34:32)
        kopf = pos.split(": ")[0].split(", ")[0]
        return f"{kopf}, nicht zu {wer}: {grund.rstrip('.')}." if len(f"{kopf} {wer} {grund}".split()) + 2 <= grenze \
            else f"{kopf}, nicht zu {wer}."
    for s in (f"{pos}. Nicht zu {wer}: {grund.rstrip('.')}.", f"{pos}. Nicht zu {wer}."):
        if len(s.split()) <= grenze:
            return s
    return f"{pos}. Nicht zu {wer}."


def ende_satz(m) -> str | None:
    """Auftrag 027, 1.5: ein Inhibitor (oder Nexus-Turm) von ihnen offen und >= 3 Gegner tot mit >= 15 s Respawn."""
    p = m.p
    if p is None or m.b is None:
        return None
    tot_lang = [g for g in m.b.gegner if g.s.tot and (g.s.respawn or 0) >= 15.0]
    if len(tot_lang) < 3:
        return None
    offen = any(e.team == p.mein_team and m.zeit - e.zeit <= 290.0 for e in p.kills_von("InhibKilled"))
    if not offen:
        return None
    tp = " Per TP, wenn bereit." if m.tp_in is not None and m.tp_in <= 0 else ""
    return f"Jetzt beenden: alle auf den Nexus, {len(tot_lang)} von ihnen sind tot.{tp}"
