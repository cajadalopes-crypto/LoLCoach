"""Der Entscheidungskern (buecher/00_entscheidungskern.md). Ein Objekt je Partie.

Schritt 2: Merkmale und Modus - Regelwerk.pruefe ruft `modus_bestimmen`, sobald die Bewertung des Takts steht; damit
sperrt es die alten Regeln (kern/sperre.py) und sammelt INFO-Zeilen fuers Dashboard.

Schritt 3: in LANE, BASIS und TOT entscheidet und spricht der Kern (`--kern neu`, Default): Kandidaten je Modus
(kern/modi/), Wert und Gefahr (wert.py, gefahr.py), ein gehaltener Plan (plan.py), hoechstens eine Ansage je Takt
mit eigenem Budget (sprechen.py), Bestaetigungen (Buch 3, 5). Die alten Regeln sind dort stumm. `schatten` rechnet
mit und schreibt "wuerde sagen" ins Protokoll, `alt` nur den Modus. Je Takt `<stamm>_kern.jsonl` (live).

Schritt 4 (Buch 5): dazu SEITE, GRUPPE, UNTERWEGS, VERTEIDIGEN - die Karten-Rechnung (modi/karte.py: Turm,
Seitenwelle, Gruppe/TP, Welle rein und rotieren, Umwandeln bis zum Nexus), Schweigen, wenn du schon hinlaeufst,
Erinnerung nach 20 s ohne Fortschritt, Bestaetigungen aus Kapitel 9."""
from __future__ import annotations

import json
import re
from collections import deque
from functools import lru_cache
from pathlib import Path

from .. import wissen
from .handlung import SICHER, richtung
from .merkmale import MerkmalBau, Merkmale
from .modus import Modus, bereich_worte

# Buch 5, Kapitel 2: Plaene mit einem Ort auf der Karte - laeufst du schon dorthin, schweigt der Coach; stehst du
# ohne_plan_s ausserhalb der Lane, ohne naeher zu kommen, erinnert er einmal (Kapitel 6)
ZIEL_ARTEN = ("DRUECKEN", "MIT_GRUPPE", "SEITENWELLE", "ZUR_GRUPPE")
# Pruefung E4: nach einer GEFAHR-Ansage 20 s nichts, was nach vorn geht, ausser die Gefahr ist sichtbar vorbei
VORWAERTS = frozenset(("TRADE", "ALL_IN", "PLATTEN", "DRUECKEN", "MIT_GRUPPE", "STAPELN", "WELLE_REIN_UND_BACK",
                       "VORBEREITEN_OBJECTIVE"))
NACH_GEFAHR_S = 20.0
GUT_RAUS_S = 10.0          # G4: so lange nach dem Rueckzug-Satz wird "Gut raus" beurteilt ...
GUT_RAUS_VERLUST = 0.20    # ... und dein Leben darf darin nicht um so viel fallen
WELLEN_ARTEN = frozenset(("FARMEN", "WELLE_REIN_UND_BACK", "STAPELN", "WELLE_HALTEN", "PLATTEN", "UNTER_TURM_FARMEN",
                          "VORBEREITEN_OBJECTIVE"))
RUECKZUG_EPISODE_S = 15.0
# Qualitaetsrunde 3, R1: Vorwaerts-Handlungen - unter vor_leben_min kein Kandidat, mit p_tod >= vor_p_tod_max nie gesagt
VOR_SCHRANKE = frozenset(("DRUECKEN", "MIT_GRUPPE", "NEHMEN", "BESTREITEN", "ZUR_GRUPPE", "TP_SPIEL", "PLATTEN",
                          "SEITENWELLE", "WELLE_KLAEREN", "VORBEREITEN_OBJECTIVE", "ANNEHMEN"))
# R2: haengen am ungeeichten p_gewinn - berechnet, protokolliert, stumm (bis die Kampf-Eichung besteht)
MODELL_STUMM = frozenset(("BESTREITEN", "TP_SPIEL"))
# Auftrag 004, Teil B: diese sprechen bei robuster Ueberlegenheit auch ohne Kampfmodell - und sind bei klarer
# Unterlegenheit aus (kern/ueberlegen.py)
UEBERLEGEN_ARTEN = frozenset(("DRUECKEN", "MIT_GRUPPE", "NEHMEN", "BESTREITEN", "ANNEHMEN", "REIN"))
BACK_RUF = re.compile(r"\bback\b", re.I)     # R4: ein Back-Ruf (Back jetzt, Jetzt back, ... dann back)
VORWAERTS_RUF = frozenset(("DRUECKEN", "MIT_GRUPPE", "NEHMEN", "BESTREITEN", "ZUR_GRUPPE", "TP_SPIEL", "ANNEHMEN",
                           "VORBEREITEN_OBJECTIVE", "PLATTEN", "SEITENWELLE", "WELLE_KLAEREN", "REIN", "DREHEN",
                           "TRADE", "ALL_IN"))       # R9: ein Ruf nach vorn vor einem Tod   # Pruefung D: so lange nach dem letzten ZURUECK-Plan gilt es als derselbe Rueckzug

KERN_MODI_3 = ("LANE", "BASIS", "TOT")
KERN_MODI_4 = KERN_MODI_3 + ("SEITE", "GRUPPE", "UNTERWEGS", "VERTEIDIGEN")     # Schritt 4 (Buch 5)
# Die Modi, in denen der Kern live spricht (seit Schritt 4). LOLCOACH_KERN_SCHRITT=3 oder Kern(modi=KERN_MODI_3) gibt
# den Stand von Schritt 3 - fuer Gegenproben beim Nachspielen.
KERN_MODI_5 = KERN_MODI_4 + ("KAMPF", "OBJECTIVE")     # Schritt 5 (Buch 7 und Buch 6): der Kern spricht ueberall
KERN_MODI = KERN_MODI_5
SPIELSTART_S = 60.0      # davor schweigt der Kern in der Basis (nicht im Buch, Schritt 3: messungen.md)
STELLUNGEN = ("alt", "schatten", "neu")
# Kehrtwende-Richtung einer Ansage des alten Systems (nur Text, Kapitel 9.4 Punkt 5)
VOR_TEXT = re.compile(r"Geh rein|nimm den Kampf an|Halte deine Stellung|Bleib an deiner Welle|Trade|Spiel auf|"
                      r"Geh auf|Drück|Nehmt", re.I)


@lru_cache(maxsize=1)
def _zeitleiste_stand(eintraege: list, jetzt: float) -> list[dict]:
    from .zeitleiste import fuer_stand
    return fuer_stand(eintraege, jetzt)


def konfig() -> dict:
    """wissen/kern.toml (einmal je Prozess gelesen)."""
    return wissen.lade("kern")


def ansage_richtung(a) -> str | None:
    """vor / zurueck / None einer gesprochenen Ansage: Kern nach Plan-Art, altes System nach Text."""
    if a.schluessel.startswith("kern:"):
        return richtung(a.schluessel.split(":", 1)[1])
    from ..regeln import BACK, RUECKZUG
    if RUECKZUG.search(a.text) or BACK.search(a.text):
        return "zurueck"
    return "vor" if VOR_TEXT.search(a.text) else None


class Kern:
    def __init__(self, ablage: Path | None = None, cfg: dict | None = None, stellung: str = "neu",
                 modi: tuple | None = None):
        from .plan import PlanFuehrer
        from .sprechen import Sprecher
        self.cfg = cfg or konfig()
        self.stellung = stellung if stellung in STELLUNGEN else "neu"
        import os
        self.modi = modi or {"3": KERN_MODI_3, "4": KERN_MODI_4, "5": KERN_MODI_5}.get(
            os.environ.get("LOLCOACH_KERN_SCHRITT", ""), KERN_MODI)
        self.bau = MerkmalBau(self.cfg)
        self.modus = Modus(self.cfg)
        self.m: Merkmale | None = None
        self.info: deque = deque(maxlen=12)       # (Spielzeit, Text) - INFO nur fuers Dashboard (Kapitel 9.1)
        self.fuehrer = PlanFuehrer(self.cfg)
        self.sprecher = Sprecher(self.cfg)
        self.transport = None                     # sprechplan.Sprechplan: was gesprochen wurde (Budget, Kehrtwenden)
        self.fokus: str | None = None             # Fokus des Tages (profil.fokus, live)
        self.staerken: list[tuple[float, str]] = []   # Bestaetigungen - fuer das Review (Buch 3, 5)
        self.gefahr = False                       # schlaegt das Gefahr-Modell gerade an (7.5)?
        self.kandidaten: list = []
        self.gesagt: list[tuple[float, str, str]] = []    # (Zeit, Kategorie, Text) des Kerns
        self._letzte: tuple[str, str] | None = None       # (Kategorie, Text) dieses Takts - fuers Protokoll
        self._fehler = False
        # neues Ereignis (9.4 Punkt 5) und Bestaetigungen
        self._sicht: deque = deque()              # (Zeit, sichtbare Gegner in 3000)
        self._ereignis_t = -1e9
        self._kills = self._objs = None
        self._leben_bei_ansage: float | None = None
        # Buch 7: Entscheidungspunkte (3.3), die laufende Kampf-Episode (5), ANNEHMEN je Gegner (4)
        from .modi.kampf import Proben
        self.proben = Proben()
        self._kampf = None
        self._annehmen_gesagt: dict[str, float] = {}
        # Entscheidung 2 (Carlos, 27.09.): Kampf-Rufe des ungeeichten Modells - berechnet, nicht gesprochen
        self.stumm_modell: list[dict] = []     # {"zeit", "art", "text", "modus"}
        self._stumm_takt: str | None = None
        self._schranke_takt: list | None = None     # R1: was die Vorwaerts-Schranke in diesem Takt strich
        self._back_rufe: list[float] = []            # R4: Spielzeiten gesprochener Back-Rufe
        self._back_stufe: bool = False               # R4: Ziel-Item beim letzten Back-Ruf komplett kaufbar?
        self._back_recall = -1e9                     # R4: zuletzt in die Basis gekommen
        self._sicher_weg: deque = deque()            # R5: (Zeit, Laufzeit zum sicheren Ort) der letzten Sekunden
        self._wohin_genannt: set = set()             # R6: schon einmal genannte Ziele (Kurzform danach)
        self._ruf_vor_tod: tuple | None = None       # R9: (Zeit des Todes, Ruf) fuer _kern.jsonl
        self._stumm_annehmen: tuple[float, set] = (-1e9, set())   # das stumme Urteil haelt wie ein Plan (Buch 7, 4)
        self._obj_gesagt: dict[tuple, str] = {}   # Buch 6, 9: (Objective, Spawn) -> Art des gesagten Urteils
        self._modus_vorher: str | None = None
        self._draussen: tuple[float, tuple] | None = None
        self._crash_zuletzt = self._leer_zuletzt = -1e9
        self._platte_geholt = -1e9
        self._platten_vorher: int | None = None
        self._utf_zuletzt = -1e9
        self._praefix: tuple[float, str] | None = None
        self._rueckzug: tuple[float, tuple, list] | None = None
        self._stapel_bestaetigt: str | None = None
        self._fokus_bestaetigt = False
        self._mitte_wache: dict = {}        # Buch 5, 9: Art -> (zuletzt, ...) - Plaene, deren Ausgang bestaetigt wird
        self._basis = {"seit": None, "kauf": None, "n": 0, "zuletzt": None, "gold": None}
        # Auftrag 002, S3: INFO_FLASH - offene und gemeldete Flash-Timer der Gegner ((Name, Zeit) -> Timer)
        self._lagebild = None
        self._ziel_zeit: dict = {}               # Auftrag 003, Teil A 5: Ziel (kurz) -> wann zuletzt gesagt
        # Buch 11 (Auftrag 003): Zeitleiste, danach, Wendepunkte, neue Informationen, Vorschau
        from .fuehren import Beobachter
        self.zeitleiste: list = []
        self.danach = None
        self.danach_text: str | None = None
        self._beobachter = Beobachter()
        self._wp: dict | None = None              # offener Wendepunkt {"zeit", "text"}
        self._wp_zuletzt = -1e9
        self._fe: dict | None = None              # neue Information (FENSTER) {"zeit", "text"}
        self._vorschau_zuletzt = -1e9
        self._gold_verlauf: deque = deque()        # (Zeit, Gold) - dein Einkommen fuer den Back-Bedarf
        self._flash_offen: dict = {}
        self._flash_gemeldet: set = set()
        self._flash_zuletzt = -1e9
        self._kampf_zuletzt = -1e9
        self._angesagt: dict[tuple[str, str], float] = {}   # (Art, Ziel) -> zuletzt angesagt
        self._gefahr_gesagt: tuple[float, set] | None = None   # letzte GEFAHR: (Zeit, vor wem)
        self._rueckzug_ep: dict | None = None   # Pruefung D: ein Rueckzug, ein Satz (+ einmal bei neuem Gegner)
        self._wohin: dict = {}                  # Pruefung C4: das Ziel eines Tod/Basis-Aufenthalts
        # G1 (Qualitaetsrunde 2): eine verlorene Lane ist eine Episode - {"t", "teil", "lang", "kurz", "rueckkehr"}
        self._schutz: dict | None = None
        self._schutz_ende: dict | None = None
        self._im_brunnen = -1e9                 # zuletzt in der eigenen Basis (Minimap)
        self._schutz_wieder = False             # G1: der Schutzplan verfiel ungesprochen - noch einmal anbieten
        self.gate_grund: str | None = None      # Pruefung A: warum das Gefahr-Gate nicht anschlug
        self._datei = None
        if ablage is not None:
            try:
                self._datei = open(ablage, "a", encoding="utf-8")
            except OSError:
                self._datei = None

    # --- vom Regelwerk gerufen ---------------------------------------------------------

    def modus_bestimmen(self, p, b, lagebild) -> str | None:
        """Merkmale dieses Takts (aus der Bewertung, die das Regelwerk schon gerechnet hat) und der Modus."""
        self.m = self.bau.neu(p, b, lagebild)
        if self.m is not None:
            self.m.fokus = self.fokus
        return self.modus.neu(self.m)

    def spricht_in(self, modus: str | None) -> bool:
        """Spricht der Kern in diesem Modus selbst (dann schweigen dort die alten Regeln)?"""
        return self.stellung == "neu" and modus in self.modi

    def info_dazu(self, zeit: float, text: str) -> None:
        self.info.append((zeit, text))

    # --- je Takt, nach dem Regelwerk ---------------------------------------------------

    def takt(self, p, lagebild=None) -> list:
        """Rueckgabe: Ansagen des Kerns (nur in Stellung `neu`)."""
        m = self.m
        self._lagebild = lagebild
        ansagen = []
        self._letzte = None
        self._stumm_takt = None
        if m is not None and self.stellung in ("schatten", "neu"):
            try:
                ansagen = self.schritt(m, self.modus.aktuell, p)
            except Exception as e:     # der Kern darf die Partie nie mitreissen
                if not self._fehler:
                    self._fehler = True
                    import traceback
                    print(f"!! Kern: {type(e).__name__}: {e}\n{traceback.format_exc(limit=4)}", flush=True)
        self._protokoll(p, m)
        return ansagen if self.stellung == "neu" else []

    def schritt(self, m: Merkmale, modus: str | None, p=None) -> list:
        """Ein Takt des Kerns auf fertigen Merkmalen (auch fuer Tests mit konstruierten Lagen)."""
        gesagt = self.transport.gesagt if self.transport is not None else []
        if modus not in ("TOT", "BASIS", None):
            self._wohin = {}           # draussen: der naechste Aufenthalt waehlt neu
        if modus == "BASIS" and self._modus_vorher not in ("TOT", "BASIS"):
            self._back_recall = m.zeit               # R4: recallt - der letzte Back-Ruf war nicht ignoriert
        if m.b is not None and m.pos is not None:
            self._sicher_weg.append((m.zeit, m.b.sicherer_ort()[1]))
            while self._sicher_weg and self._sicher_weg[0][0] < m.zeit - 2.5:
                self._sicher_weg.popleft()
        if modus in ("TOT", "BASIS") and self._modus_vorher not in ("TOT", "BASIS"):
            # Tod oder Back: danach ist ein Plan wieder neu - "derselbe Plan eben schon" (wiederholen_s) gilt fuer ein
            # Flackern, nicht ueber einen Tod hinweg (Qualitaetsrunde 1, 144655 6:11/6:42: der Plan fuer die verlorene
            # Lane kam nach dem Respawn nicht mehr)
            self._angesagt.clear()
            for sep in (self._schutz, self._schutz_ende):
                if sep is not None:
                    sep["rueckkehr"] = True           # G1: danach darf die kurze Fassung kommen (auch einer ruhenden)
        self._ereignisse_merken(m, p)
        self._korrekturen_anwenden(m)              # Auftrag 004, Teil C 2 (Buch 11, 5.6)
        self._fuehren_vorher(m, modus)             # Buch 11: Zeitleiste, Wendepunkte, neue Informationen
        self._schutz_episode(m)
        if m.b is not None and not m.tot:
            self.proben.takt(m, self.cfg)
        if modus == "KAMPF":
            self._kampf_zuletzt = m.zeit          # Auftrag 002, S3: INFO_FLASH erst 3 s nach dem Kampf
        if modus == "KAMPF" and "KAMPF" in self.modi:
            self._modus_vorher = modus
            return self._kampf_schritt(m)
        if self._kampf is not None:
            # nach dem Kampf wird der Plan sofort neu geprueft (Buch 7, 7)
            self._kampf = None
            self.fuehrer.plan = None
        if m.bereich == "basis_eigen":
            self._im_brunnen = m.zeit
        self._bestaetigung_merken(m, modus)
        if not m.daten_frisch and modus != "TOT":
            self._modus_vorher = modus
            return []          # 4.3: ohne frische Daten keine neuen Plaene
        if m.pos is None and modus not in ("TOT", "BASIS", None) and self.fuehrer.plan is not None:
            # 4.3 auch fuer den Ort: verliert die Minimap dich kurz, haelt der Plan (102112 36:06: ohne Ort kein Turm-
            # Ziel, DRUECKEN kippte fuer 8 s auf FARMEN)
            self._modus_vorher = modus
            return []
        kand, self.gefahr = self._kandidaten(m, modus)
        self.kandidaten = kand
        self.fuehrer.wendepunkt = self._wp is not None
        ev = self.fuehrer.takt(m, kand, self.gefahr)
        from . import fuehren
        self.danach = fuehren.danach(self, m)                     # Buch 11, 3
        self.danach_text = fuehren.text_danach(self.danach)
        # Buch 6, 5: der Modus kennt den Plan des vorigen Takts (OBJECTIVE bleibt, solange er ein Objective-Plan ist)
        from .modi.objective import OBJ_ARTEN
        pl = self.fuehrer.plan
        self.modus.objective_plan_merken(
            pl.handlung.daten.get("objective") if pl is not None and pl.art in OBJ_ARTEN else None, m.zeit)
        if self._schutz_wieder:
            self._schutz_wieder = False
            if ev is None and self.fuehrer.plan is not None and self.fuehrer.plan.handlung.daten.get("verloren"):
                from .plan import Ereignis
                ev = Ereignis("neu", self.fuehrer.plan)
        aus = []
        # Spielbeginn: alle stehen im Brunnen, das Briefing redet - nichts, was er nicht selbst weiss
        start = modus == "BASIS" and m.zeit < SPIELSTART_S
        if ev is not None and ev.art in ("neu", "gefahr", "schritt") and not start:
            if (a := self._ansage_zum_plan(ev, m, modus, gesagt)) is not None:
                aus.append(a)
        if not aus and modus == "BASIS" and not start:
            if (a := self._basis_warten(m, gesagt)) is not None:
                aus.append(a)
        plan = self.fuehrer.plan
        if plan is not None and plan.art in ("ZURUECK", "BACK_JETZT") and self._rueckzug_ep is not None:
            self._rueckzug_ep["zuletzt"] = m.zeit
        if not aus and not self.gefahr:       # "Denk dran" nie in GEFAHR (Pruefung D)
            er = self.fuehrer.erinnern(m, self._nicht_ausgefuehrt)
            if er is not None and (a := self._erinnerung(er, m, gesagt)) is not None:
                aus.append(a)
        if not aus:
            if (a := self._bestaetigung_allein(m, modus, gesagt)) is not None:
                aus.append(a)
        if not aus:
            if (a := self.sprecher.nachholen(m.zeit, gesagt)) is not None:
                self._gesprochen(a, "PLAN", m)
                aus.append(a)
        if not aus:
            if (a := self._flash_info(m, modus, gesagt)) is not None:
                aus.append(a)
        if not aus:
            if (a := self._vorschau(m, modus, gesagt)) is not None:
                aus.append(a)
        self._modus_vorher = modus
        return aus

    # --- Buch 11: Fuehren ------------------------------------------------------------------------------------------

    def _einkommen(self, m: Merkmale) -> float | None:
        """Dein Gold je Sekunde ueber die letzten 60 s (nur Zuwachs - ein Kauf ist kein Einkommen)."""
        if m.b is None or m.b.gold is None:
            return None
        v = self._gold_verlauf
        v.append((m.zeit, float(m.b.gold)))
        while v and v[0][0] < m.zeit - 60.0:
            v.popleft()
        if len(v) < 2 or v[-1][0] - v[0][0] < 10.0:
            return None
        zuwachs = sum(max(0.0, b - a) for (_, a), (_, b) in zip(v, list(v)[1:]))
        return zuwachs / (v[-1][0] - v[0][0])

    def _fuehren_vorher(self, m: Merkmale, modus: str | None) -> None:
        """Buch 11, 2 und 4: die Zeitleiste dieses Takts; ein Wendepunkt macht den Plan ungueltig (der naechste kommt
        sofort), eine neue Information (FENSTER) darf den naechsten Plan-Satz einleiten."""
        from . import zeitleiste
        self.zeitleiste = zeitleiste.bauen(m, self.cfg, self._lagebild, self._einkommen(m))
        plan = self.fuehrer.plan
        ziel = plan.handlung.daten.get("ziel_pos") or (plan.handlung.ziel.pos if plan and plan.handlung.ziel else None) \
            if plan is not None else None
        wp, fe = self._beobachter.takt(m, modus, self._lagebild, self.cfg, ziel=ziel)
        wp = self._strukturen_zusammen(wp, m)          # Auftrag 004, Teil A 2
        if wp is not None:
            self._wp = {"zeit": m.zeit, "text": wp, "erst": (self._wp or {}).get("erst", m.zeit)
                        if wp.startswith(("Zwei", "Drei", "Vier")) else m.zeit}
            self._ereignis_t = m.zeit                  # auch fuer Kehrtwenden ein neues Ereignis
            if modus != "KAMPF" and plan is not None and not (plan.art in SICHER and self.gefahr):
                self.fuehrer.plan = None               # erledigt oder ungueltig: der naechste Plan kommt sofort
        if fe is not None:
            self._fe = {"zeit": m.zeit, "text": fe}
        if modus == "KAMPF" and self._wp is not None:
            self._wp["zeit"] = m.zeit                  # der Wendepunkt wartet auf das Ende des Kampfs

    def _wp_leer(self, wp: str, h, m: Merkmale) -> bool:
        """Ein Wendepunkt-Satz, der nichts Neues sagt, entfaellt (Buch 11, 4 "Stille"): derselbe Anlass wie der zuletzt
        gesagte in ziel_wiederholen_s (die drei Larven in 35 s), oder beim Verlassen der Basis dasselbe Ziel, das in der
        Basis eben gesagt wurde, und kein danach."""
        from .fuehren import ziel_label
        n = self.cfg["fuehren"]["ziel_wiederholen_s"]
        letztes = getattr(self, "_letztes_ziel", None)
        gleich = letztes is not None and m.zeit - letztes[0] < n and letztes[1] == ziel_label(h)
        if getattr(self, "_wp_text", None) == wp and m.zeit - self._wp_zuletzt < n and gleich:
            return True
        if wp == "Aus der Basis":
            # das Ziel fuer draussen stand eben im Basis-Satz - draussen gilt es; ein anderes Ziel waere ein Widerspruch
            # ohne Ereignis (173159 14:40 "Geh zur Top-Welle" -> 14:47 "Aus der Basis: Farm die Bot-Welle")
            basis = getattr(self, "_basis_satz", -1e9)
            return h.art == "HALTEN" or m.zeit - basis < n or (gleich and not self.danach_text)
        return False

    def _strukturen_zusammen(self, wp: str | None, m: Merkmale) -> str | None:
        """Auftrag 004, Teil A 2: fallen mehrere Tuerme in 10 s, wird daraus EIN Satz - noch nicht gesagt: "Zwei Tuerme
        down: ..."; eben gesagt (<= 10 s): kein zweiter."""
        if wp is None or not wp.endswith(("ist down", "ist weg")):
            return wp
        offen = self._wp
        if offen is not None and offen["text"].endswith(("ist down", "ist weg", "down", "weg")) \
                and m.zeit - offen.get("erst", offen["zeit"]) <= 10.0 and not offen["text"].startswith(("Aus", "Drache",
                                                                                                         "Baron", "Herold",
                                                                                                         "Larven")):
            n = offen.get("n", 1) + 1
            offen["n"] = n
            zahl = {2: "Zwei", 3: "Drei", 4: "Vier"}.get(n, str(n))
            wir = not wp.startswith("Euer")
            return f"{zahl} Türme down" if wir else f"{zahl} eurer Türme weg"
        if offen is None and m.zeit - self._wp_zuletzt <= 10.0 and (getattr(self, "_wp_text", "") or "").endswith(
                ("ist down", "ist weg", "Türme down", "Türme weg")):
            return None
        return wp

    def _wendepunkt_offen(self, m: Merkmale) -> str | None:
        c = self.cfg["fuehren"]
        if self._wp is None or m.zeit - self._wp["zeit"] > c["wendepunkt_gilt_s"]:
            self._wp = None
            return None
        if m.zeit - self._wp_zuletzt < c["wendepunkt_abstand_s"]:
            return None
        return self._wp["text"]

    def _fenster_offen(self, m: Merkmale) -> str | None:
        if self._fe is None or m.zeit - self._fe["zeit"] > self.cfg["fuehren"]["fenster_gilt_s"]:
            self._fe = None
            return None
        return self._fe["text"]

    def _vorschau(self, m: Merkmale, modus: str | None, gesagt: list):
        """Buch 11, 4: ab vorschau_ab_s, vorschau_ruhe_s ohne Ansage, ein Ereignis der Zeitleiste in
        vorschau_horizont_s, das deinen Plan aendert - hoechstens einer je vorschau_abstand_s, mit Budget."""
        from . import fuehren
        c = self.cfg["fuehren"]
        p = self.fuehrer.plan
        if p is None or m.zeit < c["vorschau_ab_s"] or modus in ("KAMPF", "TOT", None) or self.gefahr \
                or m.zeit - self._vorschau_zuletzt < c["vorschau_abstand_s"]:
            return None
        letzte = max((a.gesprochen for a in gesagt if a.gesprochen is not None
                      and (a.schluessel.startswith("kern:") or a.schluessel == "antwort")), default=-1e9)
        if m.zeit - letzte < c["vorschau_ruhe_s"]:
            return None
        text = fuehren.vorschau_satz(self, m, self.zeitleiste, self.danach)
        if not text or len(text.split()) > c["max_woerter_wendepunkt"]:
            return None
        if BACK_RUF.search(text) and self._back_sperre(m, text) is not None:
            return None                                # Pruefung c, R4 gilt auch fuer "danach back"
        a = self.sprecher.ansage("VORSCHAU", p.art, text, m.zeit, self._pruefung(p), gesagt)
        if a is not None:
            self._vorschau_zuletzt = m.zeit
            p.gesagt = m.zeit
            if BACK_RUF.search(text):
                self._back_gesagt(m)
            self._gesprochen(a, "VORSCHAU", m)
        return a

    def _flash_info(self, m: Merkmale, modus: str | None, gesagt: list):
        """Auftrag 002, S3: ein bestaetigter Flash eines Gegners, kurz - "Ziggs ohne Flash." (213624 19:41: "du sagst
        nicht, wenn jemand geflasht hat ... dann kann ich als Riven besser entscheiden, auf wen ich draufflashe").
        Bestaetigt ist jeder Flash-Timer des Lagebilds: Chat-Ping, oder ein Sprung auf Minimap bzw. Bildschirm bei einem
        Champion ohne eigenen Dash (Entscheidung 3 der Pruefung b, `lage.ereignisse`). Nicht in KAMPF - dann 3 s nach
        dem Kampf, wenn der Flash noch weg ist; hoechstens einer je abstand_s, mehrere in einem Satz."""
        z = getattr(self._lagebild, "zauber", None)
        if z is None or m.p is None or modus == "KAMPF":
            return None
        c = self.cfg["info_flash"]
        feinde = {s.name for s in m.p.gegner()}
        for t in list(z.timer.values()):
            schl = (t.name, round(t.seit))
            if t.zauber == "SummonerFlash" and t.name in feinde and t.zurueck > m.zeit \
                    and schl not in self._flash_gemeldet:
                self._flash_offen[schl] = t
        self._flash_offen = {k: t for k, t in self._flash_offen.items() if t.zurueck > m.zeit + c["rest_min_s"]}
        if not self._flash_offen or m.zeit - self._kampf_zuletzt < c["nach_kampf_s"] \
                or m.zeit - self._flash_zuletzt < c["abstand_s"]:
            return None
        from .modi import liste
        namen = list(dict.fromkeys(t.champion for t in sorted(self._flash_offen.values(), key=lambda t: t.seit)))
        text = f"{liste(namen)} ohne Flash."
        a = self.sprecher.ansage("INFO_FLASH", "INFO_FLASH", text, m.zeit, None, gesagt)
        if a is not None:
            self._flash_gemeldet |= set(self._flash_offen)
            self._flash_offen = {}
            self._flash_zuletzt = m.zeit
            self._gesprochen(a, "INFO_FLASH", m)
        return a

    # --- Kandidaten --------------------------------------------------------------------

    def _kandidaten(self, m: Merkmale, modus: str | None) -> tuple[list, bool]:
        from . import wert
        from .modi import back_gruende, zurueck, zurueck_saetze
        from .modi import basis, gruppe, lane, seite, tot, unterwegs, verteidigen
        from .modi import objective as obj_modus
        from .plan import gefahr_schlaegt_an
        cfg = self.cfg
        if m.b is None or modus not in self.modi:
            return [], False
        je_modus = {"LANE": lane, "BASIS": basis, "TOT": tot, "SEITE": seite, "GRUPPE": gruppe,
                    "UNTERWEGS": unterwegs, "VERTEIDIGEN": verteidigen}
        plan_jetzt = self.fuehrer.plan
        if modus in ("BASIS", "TOT"):
            # ein Ziel je Tod/Basis-Aufenthalt (C4): was 8 s vor dem Respawn gesagt wurde, gilt in der Basis weiter
            kand = je_modus[modus].kandidaten(m, cfg, merker=self._wohin, lage=self._lage(m))
        elif modus == "LANE":
            kand = lane.kandidaten(m, cfg, schutz=self._schutz or False, plan=plan_jetzt)
        elif modus == "OBJECTIVE":
            kand = obj_modus.kandidaten(m, cfg, plan=plan_jetzt)       # Buch 6, 5
        else:
            kand = je_modus[modus].kandidaten(m, cfg)
            if modus in obj_modus.OBJ_MODI:
                # Buch 6, 5: Objective-Plaene gelten in UNTERWEGS, GRUPPE, SEITE und OBJECTIVE - dieselben Handlungen
                tuerme = [h for h in kand if h.art in ("DRUECKEN", "MIT_GRUPPE")]
                kand += obj_modus.handlungen(m, cfg, modus, plan=plan_jetzt, tuerme=tuerme)
                kand = [h for h in kand if not h.daten.get("ersetzt")]
                from .modi import karte
                kand = karte.umwandeln_zuerst(m, cfg, kand)      # Buch 6, 8: Objectives in der Reihenfolge
        annehmen = None
        if modus not in ("BASIS", "TOT"):         # ZURUECK: in allen Modi ausser TOT und BASIS (Buch 0, 6.3)
            kand += zurueck(m, cfg, modus, back_gruende(m, cfg))
            # Buch 7, 4: kommt einer auf dich zu - nimmst du den Kampf? Dann kein ZURUECK wegen dieser Gegner
            from .modi.kampf import annehmen as kampf_annehmen
            schon = self._stumm_annehmen[1] if m.zeit - self._stumm_annehmen[0] <= 10.0 else set()
            if (annehmen := kampf_annehmen(m, cfg, modus, plan=self.fuehrer.plan, schon=schon)) is not None:
                from .ueberlegen import lage as ueberlegen_lage
                u, grund = ueberlegen_lage(m, cfg, m.pos) if not cfg["kampf"].get("geeicht", False) else (None, "")
                if cfg["kampf"].get("geeicht", False):
                    kand.append(annehmen)
                elif u == "ueberlegen":
                    # Auftrag 004, Teil B: robust klar ueberlegen - der Kampf wird angesagt, mit diesem Grund
                    annehmen.grund = grund
                    annehmen.satz = f"Nimm den Kampf: {grund.split(', ')[0]}."
                    annehmen.daten["ueberlegen"] = grund
                    kand.append(annehmen)
                else:
                    # Entscheidung 2: berechnet und protokolliert, aber kein Kandidat - das ungeeichte Modell aendert
                    # nichts an dem, was sonst gesagt wird (auch kein ZURUECK faellt seinetwegen weg)
                    self._stumm(m, "ANNEHMEN", annehmen.satz, modus)
                    self._stumm_annehmen = (m.zeit, set(annehmen.daten.get("gruppe", [])))
                    annehmen = None
        tk = wert.todeskosten(m, cfg)
        for h in kand:
            wert.bewerte(h, m, cfg, tk)
        # Buch 6, 4.3: eine Objective-Handlung nur mit EV > 0 (nicht bloss besser als HALTEN)
        kand = [h for h in kand if h.daten.get("ev_min") is None or h.ev > h.daten["ev_min"]]
        # Buch 11, 5.6: Carlos' Korrektur ("Drache ist tot") gilt korrektur_gilt_s lang als Merkmal
        korr = getattr(self, "korrekturen", {})
        weg = {k.split(":", 1)[1] for k, t in korr.items() if k.startswith("tot:")
               and m.zeit - t <= self.cfg["fuehren"]["korrektur_gilt_s"]}
        if weg:
            kand = [h for h in kand if h.daten.get("objective") not in weg]
        self.kandidaten_roh = list(kand)          # Auftrag 004, Teil C: auch was stumm bleibt, mit seinem Grund
        kand = self._schranken(m, kand, modus)
        bleiben = next((h for h in kand if h.art in ("FARMEN", "HALTEN") or h.daten.get("verloren")), None)
        for h in kand:
            if h.art == "ZURUECK":
                zurueck_saetze(h, m, bleiben)
        # je Art die bessere Fassung (ZURUECK: nur raus / raus und back)
        beste: dict = {}
        for h in kand:
            if h.art not in beste or h.ev > beste[h.art].ev:
                beste[h.art] = h
        kand = list(beste.values())
        if annehmen is not None:
            gruppe = set(annehmen.daten.get("gruppe", []))
            kand = [h for h in kand if not (h.art == "ZURUECK" and {n for n, x in h.daten.get("wer", []) if x >= 0.05}
                                            <= gruppe)]
        # "bleiben, wo du bist" - bei verlorener Lane ist das der schuetzende Freeze (Pruefung A)
        farmen = next((h for h in kand if h.art in ("FARMEN", "HALTEN") or h.daten.get("verloren")), None)
        gefahr = farmen is not None and gefahr_schlaegt_an(farmen, cfg["gefahr"]) and annehmen is None
        self.gate_grund = None
        if gefahr:
            from .modi import am_sicheren_ort
            wer = {n for n, x in farmen.daten.get("wer", []) if x >= 0.05}
            if am_sicheren_ort(m):
                # Buch 0, 7.5 (Nachtrag Qualitaetsrunde 1): eine Gefahr, deren sicherer Ort dein aktueller Ort ist,
                # wird nicht gesagt - der Plan haelt
                gefahr, self.gate_grund = False, "am sicheren Ort"
            elif farmen.daten.get("verloren") and wer <= {farmen.daten.get("lane_gegner")}:
                # Pruefung A: kommt nur der Lane-Gegner, waehrend du nach dem Plan an deinem Turm farmst, ist das
                # keine Gefahr - genau das will der Plan
                gefahr, self.gate_grund = False, f"nur {farmen.daten.get('lane_gegner')} - der Plan fuer die Lane haelt"
            elif m.b.lane is not None and wer <= {m.b.lane.champion} and m.leben is not None \
                    and m.leben >= cfg["schranken"]["gefahr_lane_leben_min"] \
                    and m.b.kraefte()[0] >= cfg["schranken"]["gefahr_lane_kraft_min"]:
                # Pruefung c, R5: der Lane-Gegner allein ist keine Gefahr, solange du genug Leben hast und nicht
                # schwaecher bist (173159 7:45: "Raus ...: Cho'Gath kommt" bei 100 %) - bis Buch 2 die Matchups bringt
                gefahr, self.gate_grund = False, f"nur {m.b.lane.champion}, Leben und Kraft reichen"
            elif (einer := self._klar_unterlegen(m, wer)) is not None:
                # Auftrag 002, S5.2: genau ein Gegner, den du klar ueberragst, ist keine Gefahr (213624 15:15, 17:32,
                # 21:37 "Ziggs kommt" - Riven mit 20+ Kills); verallgemeinert R5 ueber den Lane-Gegner hinaus
                gefahr, self.gate_grund = False, f"nur {einer}, du liegst klar vorn"
        # der Plan fuer die verlorene Lane gilt gegen den Lane-Gegner allein - kommt noch wer, ist er keine Wahl
        # (140253 8:15: "Yasuo ist vorn: ... farm dort", waehrend Brand und Yasuo kamen)
        if farmen is not None and farmen.daten.get("verloren"):
            andere = {n for n, x in farmen.daten.get("wer", []) if x >= 0.05} - {farmen.daten.get("lane_gegner")}
            if andere:
                kand = [h for h in kand if h is not farmen]
        # Pruefung E4: nach einer GEFAHR-Ansage 20 s nichts nach vorn, ausser die Gefahr ist sichtbar vorbei (nicht in
        # KAMPF - dort entscheidet Tabelle 5.1, Buch 7 5.4)
        if self._gefahr_gesagt is not None and m.zeit - self._gefahr_gesagt[0] < NACH_GEFAHR_S and m.b is not None \
                and annehmen is None:
            von = self._gefahr_gesagt[1]
            vorbei = all(g.s.tot or (g.sichtbar and g.abstand is not None and g.abstand > 3000)
                         for g in m.b.gegner if g.champion in von) if von else False
            if not vorbei:
                kand = [h for h in kand if h.art not in VORWAERTS]
        plan = self.fuehrer.plan
        als = plan.als() if plan is not None else None
        if gefahr:
            # Gefahr schlaegt Timing (Buch 3, 2.1): nur sichere Handlungen - und der schuetzende Freeze (Buch 1, 3.7)
            kand = [h for h in kand if h.art in SICHER or h.daten.get("schutz") or h.art == als
                    or h.art == "ANNEHMEN"]
        else:
            # ein Plan "nur bei Gefahr" (ZURUECK, Back im Kampf) ist ohne Gefahr kein Kandidat mehr - die Luecke, die
            # jeder Plan ueberbrueckt (luecke_s, G3), haelt ihn noch kurz; danach gilt wieder der normale Plan ("Gefahr
            # schlaegt Timing", Buch 3, 2.1; 102112 25:22: der Rueckzug von 24:58 hielt vorher 24 s nach dem gewonnenen
            # Kampf, weil er als Plan Kandidat blieb, und schlug mit seinem Back-Wert den freien Drachen)
            kand = [h for h in kand if not h.daten.get("nur_bei_gefahr")]
        kand = [h for h in kand if not (h.daten.get("klein") and h.p_tod >= cfg["gefahr"]["p_min"])]
        return kand, gefahr

    # --- Sprechen ----------------------------------------------------------------------

    def _ansage_zum_plan(self, ev, m: Merkmale, modus: str | None, gesagt: list):
        p = ev.plan
        if p is None:
            return None
        h = p.handlung
        wp = self._wendepunkt_offen(m) if ev.art == "neu" else None       # Buch 11, 4
        if ev.art == "schritt":
            kategorie, text = "PLAN", ev.text
        else:
            if h.stumm and wp is None:
                return None
            kategorie = "GEFAHR" if (ev.art == "gefahr" and h.art in SICHER) or h.art == "ANNEHMEN" else "PLAN"
            text = h.satz or (h.kurz() if h.art != "WOHIN" else "")   # R6: ein WOHIN ohne Ziel sagt nichts
            if h.stumm:
                from .fuehren import stumm_satz
                # Buch 11, 4: nach einem Wendepunkt auch "Farm die Top-Welle" - oder, ist der Plan nur Halten, das,
                # was danach kommt; sonst schweigt er (kein "bleib, wo du bist")
                # Auftrag 004, Teil A 1: bleibt nur FARMEN, dann nur mit Vorschau ("Farm Top, Drache in 70 Sekunden,
                # dann zum Drachen."); nur Halten: das, was danach kommt; sonst still - nie ungefragt "unsicher"
                from .fuehren import farmen_mit_vorschau
                text = (farmen_mit_vorschau(h, self.zeitleiste, m.zeit, self.danach_text, self.cfg) if h.art == "FARMEN"
                        else (f"{self.danach_text[:1].upper()}{self.danach_text[1:]}." if self.danach_text else ""))
            if h.art == "ANNEHMEN":
                # Buch 7, 4: hoechstens einmal je Gegner und annehmen_wiederholen_s
                g = h.daten.get("kampf_mit")
                if m.zeit - self._annehmen_gesagt.get(g, -1e9) < self.cfg["kampf"]["annehmen_wiederholen_s"]:
                    p.gesagt = m.zeit
                    return None
        if not text:
            return None
        # Pruefung A / Buch 0 7.5: stehst du schon am sicheren Ort, wird der Rueckzug nicht gesagt - der Plan haelt
        if ev.art != "schritt" and h.daten.get("dort"):
            p.gesagt = m.zeit
            return None
        # Pruefung E3: in der Basis kein Wellenbefehl (der Modus hinkt, ein Plan von der Lane gilt noch)
        if m.bereich == "basis_eigen" and (p.als() in WELLEN_ARTEN or h.art in WELLEN_ARTEN):
            return None
        # Pruefung D: ZURUECK mit und ohne Back ist EIN Plan - im selben Rueckzug kein neuer Satz, ausser ein neuer
        # Gegner kommt dazu (einmal); "Jetzt back" einmal
        # (die Merker werden erst gesetzt, wenn der Satz wirklich gesprochen ist - `nach_dem_sprechen`)
        nach_dem_sprechen = None
        ep = self._rueckzug_aktiv(m)
        if p.art == "BACK_JETZT" and ev.art != "schritt" and ep is not None:
            # ein Back gleich nach dem Rueckzug ist dessen zweiter Schritt: einmal (Pruefung D)
            if ep["back"]:
                p.gesagt = ep["t"]
                return None
            nach_dem_sprechen = lambda: ep.update(back=True)          # noqa: E731
        if p.art == "ZURUECK":
            von = set(h.daten.get("gefahr_von", []))
            if ep is not None:
                if ev.art == "schritt":
                    if ep["back"]:
                        return None
                    nach_dem_sprechen = lambda: ep.update(back=True)      # noqa: E731
                elif von - ep["wer"] and not ep["wechsel"]:
                    nach_dem_sprechen = lambda: (ep.update(wechsel=True), ep["wer"].update(von))  # noqa: E731
                else:
                    p.gesagt = ep["t"]
                    return None
            elif ev.art != "schritt":
                nach_dem_sprechen = lambda: setattr(self, "_rueckzug_ep", {      # noqa: E731
                    "t": m.zeit, "zuletzt": m.zeit, "wer": set(von), "wechsel": False, "back": False})
        # G1 (Qualitaetsrunde 2): der Schutzplan einmal lang je Lane-Verlust; nach Tod oder Basis kurz, hoechstens alle
        # schutz_erinnern_s; sonst gilt er still (144655: vorher achtmal in neun Minuten, je 22 Woerter)
        if h.daten.get("verloren") and ev.art != "schritt" and self._schutz is not None:
            sep = self._schutz
            vorher = {k: sep[k] for k in ("lang", "kurz", "rueckkehr")}
            if not sep["lang"]:
                nach_dem_sprechen = lambda a=None: sep.update(lang=True, kurz=m.zeit, rueckkehr=False,  # noqa: E731
                                                              offen=(a, vorher))
            elif sep["rueckkehr"] and (sep["kurz"] is None
                                       or m.zeit - sep["kurz"] >= self.cfg["sprechen"]["schutz_erinnern_s"]):
                text = h.daten.get("kurz_satz") or text
                nach_dem_sprechen = lambda a=None: sep.update(kurz=m.zeit, rueckkehr=False,  # noqa: E731
                                                              offen=(a, vorher))
            else:
                p.gesagt = m.zeit
                sep["rueckkehr"] = False       # die Rueckkehr ist verbraucht, auch wenn der Plan still gilt
                return None
        # ein Back oder Rueckzug gleich nach dem Brunnen ist ein Flackern der Minimap beim Ankommen (144655 5:04: "Back
        # jetzt: 22 Prozent", eine Sekunde nachdem Riven im Brunnen stand - er verdraengte das Ziel fuer danach, G2)
        if p.art in ("BACK_JETZT", "ZURUECK") and ev.art != "schritt" and m.zeit - self._im_brunnen <= 3.0:
            p.gesagt = m.zeit
            return None
        # der Schutzplan einer verlorenen Lane (G1) gilt still weiter - ein Wendepunkt aendert ihn nicht (144655)
        wendepunkt = wp is not None and kategorie == "PLAN" and not h.daten.get("verloren")
        if wendepunkt and self._wp_leer(wp, h, m):
            wendepunkt, self._wp = False, None
            if h.stumm:
                p.gesagt = m.zeit               # der Plan in Carlos' Kopf gilt weiter (Buch 11, Prinzip 1)
                return None
        if ev.art == "neu" and not wendepunkt and self._laeuft_hin(h, m):
            # Buch 5, 2: "Laeufst du schon dorthin, schweigt der Coach" - der Plan gilt als gesagt, damit die
            # Erinnerung (Kapitel 6) greift, wenn du stehen bleibst
            p.gesagt = m.zeit
            p.start = {"sicher_weg": None, "pos": m.pos}
            return None
        if self._kehrtwende(h.art if ev.art != "schritt" else p.als(), m, gesagt):
            return None
        # derselbe Plan kam eben schon (er fiel kurz weg und kam wieder): nichts Neues - der Plan gilt still weiter
        # (102112, 6:47/6:59: zweimal "Stapel die Top-Welle bis zur Kanone")
        # KAUFEN zaehlt nach seinem Weiterweg, nicht nach der Einkaufsliste: nach einem Teilkauf ist es derselbe Plan
        # (Qualitaetsrunde 1, 133930 17:45 TOT "kauf Spitzhacke, Caulfields Kriegshammer ..., dann zur Top-Welle" ->
        # 17:57 BASIS "Kauf Caulfields Kriegshammer, dann zur Top-Welle" - Pruefung D4)
        weiter = h.daten.get("wohin") if p.art == "KAUFEN" else None
        ziel = weiter.ziel if weiter is not None and getattr(weiter, "ziel", None) is not None else h.ziel
        schl = (p.art, ziel.name if ziel else "")
        if kategorie == "PLAN" and ev.art != "schritt" and not wendepunkt and \
                m.zeit - self._angesagt.get(schl, -1e9) < self.cfg["sprechen"]["wiederholen_s"]:
            p.gesagt = self._angesagt[schl]
            return None
        # dieselbe Warnung vor denselben Gegnern eben erst gesagt: nichts Neues (235433, 6:12-7:04: fuenfmal "Raus zu
        # deinem Top-Tier-1-Turm" in 52 s) - kommt ein neuer Gegner dazu, darf sie wieder
        if kategorie == "GEFAHR" and ev.art != "schritt":
            cs = self.cfg["schranken"]
            von = set(h.daten.get("gefahr_von", []))
            alt = self._gefahr_gesagt
            # Pruefung c, R5: dieselbe Gegnermenge gefahr_gleiche_s (45 s) nicht erneut - ausser p_tod steigt deutlich
            # (164326 22:39/23:12: zweimal "Teemo und Naafiri kommen")
            if alt is not None and m.zeit - alt[0] < cs["gefahr_gleiche_s"] and von <= alt[1] \
                    and h.p_tod < alt[2] + cs["gefahr_anstieg"]:
                p.gesagt = alt[0]
                return None
            # Pruefung c, R5: kein Gefahr-Satz, waehrend du schon zum sicheren Ort laeufst
            if h.art in ("ZURUECK", "RAUS") and len(self._sicher_weg) >= 2 and self._sicher_weg[0][1] is not None \
                    and self._sicher_weg[-1][1] is not None and m.zeit - self._sicher_weg[0][0] >= 1.5 \
                    and (self._sicher_weg[0][1] - self._sicher_weg[-1][1]) * (m.mein_tempo or 340.0) \
                    >= cs["sicher_naeher"]:
                p.gesagt = m.zeit
                return None
        # Buch 6, 9: das Urteil zu einem Objective hoechstens einmal je Spawn - ein zweites Mal nur, wenn es kippt
        # (NEHMEN/BESTREITEN <-> ABGEBEN_TAUSCHEN); VORBEREITEN -> NEHMEN wird nicht angesagt (4.2)
        from .modi.objective import URTEIL_ARTEN
        okey = None
        if h.art in URTEIL_ARTEN and ev.art != "schritt" and h.daten.get("objective") and not wendepunkt:
            okey = (h.daten["objective"], h.daten.get("spawn"))
            alt = self._obj_gesagt.get(okey)
            if alt is not None and (alt == "ABGEBEN_TAUSCHEN") == (h.art == "ABGEBEN_TAUSCHEN"):
                p.gesagt = m.zeit
                return None
        if ev.art != "schritt" and not wendepunkt and self._ziel_eben(h, m.zeit):
            p.gesagt = m.zeit                    # Auftrag 003, Teil A 5: dasselbe Ziel eben erst gesagt
            return None
        if (grund := self._back_sperre(m, text)) is not None:
            p.gesagt = m.zeit                    # Pruefung c, R4: der Plan gilt still weiter
            self.gate_grund = grund
            return None
        text = self._kurzform(p, h, text)        # Pruefung c, R6
        if kategorie != "GEFAHR":
            from .modi import kuerze
            text = kuerze(text, self.cfg["sprechen"]["max_woerter"])      # Auftrag 002, S2.3
        if modus == "BASIS" and self._praefix is not None and m.zeit - self._praefix[0] <= 15:
            text = f"{self._praefix[1]} {text}"
            self._praefix = None
        # Buch 11, 4: WENDEPUNKT ("Turm ist down: ... Danach ...", Optionen) und FENSTER ("Rumble ist 40 Sekunden weg: ...")
        from . import fuehren
        cf = self.cfg["fuehren"]
        if wendepunkt:
            opt = fuehren.optionen(self)
            zwei = fuehren.optionen_satz(*opt, cf["max_woerter_optionen"] - len(wp.split())) if opt else None
            danach_text = self.danach_text
            if danach_text and BACK_RUF.search(danach_text) and self._back_sperre(m, danach_text) is not None:
                danach_text = None                    # Pruefung c, R4: auch "Danach back" zaehlt als Back-Ruf
            vor = next((e for e in reversed(getattr(self, "_ansage_log", None) or [])
                        if e["kategorie"] in ("PLAN", "WENDEPUNKT", "FENSTER")), None)
            if not zwei and vor is not None and m.zeit - vor["zeit"] <= cf["ziel_wiederholen_s"] \
                    and vor["art"] == h.art and vor.get("ziel") and vor["ziel"] == fuehren.ziel_label(h):
                text = f"{wp}: weiter {fuehren.kurz(h)}."     # derselbe Plan, eben gesagt - nur bestaetigen
            else:
                text = f"{wp}. {zwei}" if zwei else fuehren.wendepunkt_satz(wp, text, danach_text,
                                                                          cf["max_woerter_wendepunkt"])
            kategorie = "WENDEPUNKT"
        elif kategorie == "PLAN" and ev.art == "neu" and (fe := self._fenster_offen(m)) is not None \
                and not any(w in text for w in fe.split()[:2]):      # nennt der Satz ihn schon, keine zweite Zahl
            neu = f"{fe}: {fuehren._koerper(text)}."
            if len(neu.split()) <= cf["max_woerter_wendepunkt"]:
                text, kategorie = neu, "FENSTER"
        def merken(ansage=None, zeit=m.zeit):
            # was ein gesprochener Plan hinterlaesst - sofort oder beim Nachholen (Budget, 9.2)
            p.gesagt = zeit
            self._angesagt[schl] = zeit
            if okey is not None:
                self._obj_gesagt[okey] = h.art
            if BACK_RUF.search(text):
                self._back_gesagt(m)
            self._wohin_merken(h, zeit)
            if h.art == "WOHIN" and modus == "BASIS":
                self._basis["zuletzt"] = zeit      # Ziel 2 (173159 36:50/37:10): die Warteregel wartet ab hier
            if nach_dem_sprechen is not None:
                if h.daten.get("verloren"):
                    nach_dem_sprechen(ansage)
                else:
                    nach_dem_sprechen()
        # ein Wendepunkt bleibt wahr, auch wenn der Plan kurz wegfaellt - nur ein Kampf ueberholt ihn (Buch 11, 4;
        # 164326 5:49: der Satz wartete hinter einem langen und fiel weg, als der Plan eine Sekunde fehlte)
        pruefe = (lambda: self.modus.aktuell != "KAMPF") if kategorie == "WENDEPUNKT" else self._pruefung(p)
        a = self.sprecher.ansage(kategorie, p.art, text, m.zeit, pruefe, gesagt,
                                 danach=merken if kategorie in ("PLAN", "FENSTER") else None)
        if a is not None:
            # die Lage der Entscheidung, fuer protokoll.py (gesprochen wird vielleicht spaeter - Pruefung B)
            a._wahl = {"zeit": m.zeit, "plan": p.art, "ev": h.ev, "p_tod": h.p_tod, "gehalten": self.fuehrer.gehalten,
                       "top": [(x.art, x.ev, x.p_tod) for x in self.fuehrer.top], "gate": self.gate_grund}
            merken(a)
            if h.art == "ANNEHMEN":
                self._annehmen_gesagt[h.daten.get("kampf_mit")] = m.zeit
            if p.art in ("ZURUECK", "BACK_JETZT"):
                self.proben.ansage(m.zeit, "raus")
            elif p.art == "ANNEHMEN":
                self.proben.ansage(m.zeit, "rein")
            if kategorie == "GEFAHR":
                self._gefahr_gesagt = (m.zeit, set(h.daten.get("gefahr_von", [])), h.p_tod)
                self._wp = None                          # eine Gefahr ueberholt den Wendepunkt
            elif kategorie == "WENDEPUNKT":
                self._wp_text = self._wp["text"] if self._wp else None
                self._wp, self._wp_zuletzt = None, m.zeit
            elif kategorie == "FENSTER":
                self._fe = None
            p.start = {"sicher_weg": m.b.sicherer_ort()[1] if m.b is not None else None, "pos": m.pos}
            if h.art == "ZURUECK":
                self._rueckzug = (m.zeit, m.pos, [n for n, x in h.daten.get("wer", []) if x >= 0.05],
                                  m.b.leben if m.b is not None else None, set())
            self._gesprochen(a, kategorie, m)
        return a

    def _laeuft_hin(self, h, m: Merkmale) -> bool:
        """Du kommst dem Ort des Plans in den letzten 3 s deutlich naeher (>= 500 Einheiten). Nicht beim Umwandeln:
        dort sagt der Satz das Fenster und ruft das Team (Kapitel 8)."""
        if h.art not in ZIEL_ARTEN or h.daten.get("umwandeln") or h.ziel is None or h.ziel.pos is None \
                or m.pos is None:
            return False
        from ..bewertung import abstand
        v = [x for x in self.bau.verlauf if x[0] >= m.zeit - 3.0 and x[2] is not None]
        return bool(v) and abstand(v[0][2], h.ziel.pos) - abstand(m.pos, h.ziel.pos) >= 500

    def _lage(self, m: Merkmale) -> tuple:
        """Pruefung C4: die Lage kippt, wenn jemand stirbt, eine Struktur faellt oder ein Objective erscheint."""
        p = m.p
        if p is None:
            return ()
        return (len(p.kills_von("ChampionKill")), len(p.kills_von("TurretKilled")) + len(p.kills_von("InhibKilled")),
                frozenset(o.schl for o in m.objectives if o.lebt))

    def _pruefung(self, p):
        """Die Ansage stimmt, solange der Kern-Plan derselbe ist (ersetzt _noch_wahr, Kapitel 9.6)."""
        schritt = p.schritt

        def pruefe() -> bool:
            q = self.fuehrer.plan
            m = self.m
            if m is not None and m.bereich == "basis_eigen" and p.als() in WELLEN_ARTEN:
                return False       # Pruefung E3: in der Basis kein Wellenbefehl
            if self.modus.aktuell == "KAMPF":
                return False       # Buch 7, 11.3: in KAMPF kein Plan-Satz von vorher (nur die Kampf-Rufe, <= 5 Woerter)
            if p.art in VOR_SCHRANKE and m is not None and m.leben is not None \
                    and m.leben < self.cfg["schranken"]["vor_leben_min"]:
                return False       # Pruefung c, R1: das Leben fiel, bevor der Satz dran war
            obj = p.handlung.daten.get("objective")
            if obj and m is not None and m.obj_urteile and obj in m.obj_urteile and not m.obj_urteile[obj].zieht                     and p.art not in ("BESTREITEN", "ABGEBEN_TAUSCHEN"):
                return False       # Buch 6, 14.4: zieht das Objective beim Sprechen nicht mehr, faellt der Satz weg
            return q is p and q.schritt == schritt
        return pruefe

    def _korrekturen_anwenden(self, m: Merkmale) -> None:
        """Buch 11, 5.6 (Auftrag 004, Teil C 2): Carlos' Aussagen ueberschreiben das Merkmal korrektur_gilt_s lang -
        "der ist jetzt bei mir oben" setzt die Sichtung des Gegners auf deinen Ort, "ich bin beim Drachen" deinen Ort."""
        k = getattr(self, "korrekturen", None)
        if not k or m is None or m.b is None:
            return
        gilt = self.cfg["fuehren"]["korrektur_gilt_s"]
        bei = k.get("bei_mir")
        if bei is not None and m.zeit - bei[1] <= gilt and m.pos is not None:
            g = next((x for x in m.b.gegner if x.champion == bei[0] and not x.s.tot), None)
            if g is not None:
                g.pos, g.sichtbar, g.seit, g.abstand, g.ankunft = m.pos, True, 0.0, 0.0, 0.0
        ort = k.get("ort")
        if ort is not None and m.zeit - ort[1] <= gilt:
            from .merkmale import OBJ_GRUBE
            o = next((x for x in m.objectives or [] if x.schl == ort[0]), None)
            if o is not None:
                m.pos = o.pos
                m.bereich = f"grube:{OBJ_GRUBE.get(ort[0], ort[0])}"

    def _gesprochen(self, a, kategorie: str, m: Merkmale) -> None:
        a._kategorie = kategorie          # fuer Szenarien (kategorie_max) und Kennzahlen
        # Auftrag 004, Teil C 1: jede Ansage merkt sich 60 s lang ihren Grund und ihre Lage - "warum?" meint sie
        plan = self.fuehrer.plan
        grund = (plan.handlung.grund if plan is not None and kategorie != "INFO_FLASH" and plan.handlung.grund
                 else (a.text.split(": ", 1)[1].rstrip(".!") if ": " in a.text else ""))
        log = getattr(self, "_ansage_log", None)
        if log is None:
            self._ansage_log = log = deque()
        from . import fuehren as _f
        log.append({"zeit": m.zeit, "text": a.text, "art": a.schluessel.split(":", 1)[-1], "kategorie": kategorie,
                    "grund": grund, "leben": m.leben,
                    "ziel": _f.ziel_label(plan.handlung) if plan is not None and kategorie != "INFO_FLASH" else None})
        while log and log[0]["zeit"] < m.zeit - 60.0:
            log.popleft()
        if kategorie in ("PLAN", "WENDEPUNKT", "FENSTER", "VORSCHAU", "ERINNERUNG") and self.fuehrer.plan is not None:
            from .fuehren import ziel_label
            a._ziel = ziel_label(self.fuehrer.plan.handlung)      # Buch 11, 7: Widersprueche
            self._letztes_ziel = (m.zeit, a._ziel)                 # Buch 11, 5.3: die Antwort widerspricht nicht
            if self.modus.aktuell in ("BASIS", "TOT"):
                self._basis_satz = m.zeit                          # Buch 11, 4: das Ziel fuer draussen
        self.gesagt.append((m.zeit, kategorie, a.text))
        self._letzte = (kategorie, a.text)
        self._leben_bei_ansage = m.leben

    def _kehrtwende(self, art: str, m: Merkmale, gesagt: list) -> bool:
        """9.4 Punkt 5: vor <-> zurueck in <= 30 s ohne neues Ereignis - dann schweigt der Kern (der Plan gilt trotzdem
        und steht auf dem Dashboard)."""
        r = richtung(art)
        if r is None:
            return False
        for a in reversed(gesagt):
            if a.gesprochen is None or m.zeit - a.gesprochen > 30:
                break
            ra = ansage_richtung(a)
            if ra is None:
                continue
            return ra != r and self._ereignis_t < a.gesprochen
        return False

    def _kampf_schritt(self, m: Merkmale) -> list:
        """Buch 7, 5: in KAMPF die Tabelle 5.1 - REIN, RAUS, DREHEN, HALTEN; eigene Episode, kein PlanFuehrer."""
        from .modi.kampf import Kampf
        if m.b is None:
            return []
        if self._kampf is None:
            self._kampf = Kampf(m.zeit, m)
        r = self._kampf.takt(m, self.cfg)
        if r is None:
            return []
        art, satz, ziel = r
        if art in ("REIN", "DREHEN") and not self.cfg["kampf"].get("geeicht", False):
            from .ueberlegen import lage as ueberlegen_lage
            if ueberlegen_lage(m, self.cfg, m.pos)[0] != "ueberlegen":
                self._stumm(m, art, satz, "KAMPF")    # Entscheidung 2: Modell nicht geeicht (Auftrag 004: ausser klar
                return []                             # ueberlegen)
        if art == "RAUS" and not self.cfg["kampf"].get("geeicht", False):
            from .modi.kampf import raus_beleg
            if not raus_beleg(m, self.cfg):
                # Auftrag 002, S5.3: RAUS nur mit robustem Beleg, bis die Kampf-Eichung besteht (213624 1:11/1:17:
                # zweimal "Raus, zum Turm!" in einem Level-1/2-Kampf, den Riven gewann)
                self._stumm(m, art, satz, "KAMPF")
                return []
        a = self.sprecher.ansage("GEFAHR", art, satz, m.zeit, None, [])
        if a is None:
            return []
        a.gueltig = 1.0                   # was nach 1 s nicht gesprochen ist, faellt weg (5.4)
        self._kampf.gesagt(m, art, ziel)
        self.proben.ansage(m.zeit, "raus" if art == "RAUS" else "rein")
        self._gesprochen(a, "GEFAHR", m)
        return [a]

    def _klar_unterlegen(self, m: Merkmale, wer: set, p_da: dict | None = None) -> str | None:
        """Auftrag 002, S5.2: kommt genau ein Gegner, dein Leben ist >= gefahr_einzel_leben_min und du liegst >=
        gefahr_einzel_level Level UND >= gefahr_einzel_gold Item-Gold vor ihm, ist er keine Gefahr. Seine Werte nach
        Buch 7, 3.2 geschaetzt, wenn sie veraltet sind (kampf.gegner_werte).
        Auftrag 003, Teil A 1: dasselbe fuer zwei - dein Leben >= gefahr_zwei_leben_min (70 %), du liegst vor JEDEM so
        weit vorn, und kein dritter Gegner hat p_da >= gefahr_zwei_dritter_p_max im Fenster. Rueckgabe: die Namen."""
        from .kampf import gegner_werte
        cs = self.cfg["schranken"]
        if not wer or len(wer) > 2 or m.b is None or m.p is None or m.p.ich is None or m.leben is None:
            return None
        if m.leben < (cs["gefahr_einzel_leben_min"] if len(wer) == 1 else cs["gefahr_zwei_leben_min"]):
            return None
        gs = [g for g in m.b.gegner if g.champion in wer]
        if len(gs) != len(wer):
            return None
        ich = m.p.ich
        for g in gs:
            level, gold, _ = gegner_werte(g, m, self.cfg["kampf"])
            if ich.level - level < cs["gefahr_einzel_level"] or ich.item_gold - gold < cs["gefahr_einzel_gold"]:
                return None
        if len(gs) == 2:
            if p_da is None:
                from . import gefahr as gefahr_modell
                p_da = gefahr_modell.alle_p_da(m, self.cfg["gefahr"])
            if any(x >= cs["gefahr_zwei_dritter_p_max"] for n, x in p_da.items() if n not in wer):
                return None
        return " und ".join(g.champion for g in gs)

    def _back_sperre(self, m: Merkmale, text: str) -> str | None:
        """Pruefung c, R4: ein Back-Ruf nicht unter back_leben_min und nicht in KAMPF (dort gilt RAUS); hoechstens
        back_max_je_10min je 10 Minuten; nach einem Back-Ruf ohne Recall ein neuer erst nach back_ignoriert_s - ausser
        dein Leben faellt unter back_ausnahme_leben oder das Ziel-Item wird komplett kaufbar. Rueckgabe: der Grund."""
        if not BACK_RUF.search(text or ""):
            return None
        cs = self.cfg["schranken"]
        le = m.leben
        if le is not None and le < cs["back_leben_min"]:
            return "Back gesperrt: Leben unter 10 %"
        if self.modus.aktuell == "KAMPF":
            return "Back gesperrt: KAMPF"
        rufe = [t for t in self._back_rufe if m.zeit - t < 600]
        if len(rufe) >= cs["back_max_je_10min"]:
            return f"Back gesperrt: {len(rufe)} in 10 min"
        if rufe and m.zeit - rufe[-1] < cs["back_ignoriert_s"] and self._back_recall < rufe[-1]:
            stufe = bool(m.kauf is not None and m.kauf.kern_fertig)
            if not ((le is not None and le < cs["back_ausnahme_leben"]) or (stufe and not self._back_stufe)):
                return "Back gesperrt: der letzte wurde ignoriert"
        return None

    def _back_gesagt(self, m: Merkmale) -> None:
        self._back_rufe.append(m.zeit)
        self._back_stufe = bool(m.kauf is not None and m.kauf.kern_fertig)

    def _wohin_ziel(self, h) -> str | None:
        """R6: das Weiterweg-Ziel eines KAUFEN- oder WOHIN-Satzes ("zur Top-Welle", "Top", ...)."""
        if h.art == "KAUFEN":
            w = h.daten.get("wohin")
            return w.daten.get("kurz") if w is not None else None
        if h.art in ("WOHIN", "WOHIN_TP_LANE"):
            return h.daten.get("kurz")
        return None

    def _wohin_merken(self, h, zeit: float | None = None) -> None:
        if (z := self._wohin_ziel(h)) is not None:
            self._wohin_genannt.add(z)
            if zeit is not None:
                self._ziel_zeit[z] = zeit

    def _ziel_eben(self, h, zeit: float) -> bool:
        """Auftrag 003, Teil A 5 (Buch 11, 4 "Stille"): ein reines Ziel (WOHIN) wurde in ziel_wiederholen_s schon gesagt -
        auch vor einem neuen Basis-Besuch (213624 12:47 "Zum Drachen: ihr seid drei." -> 12:59 "Dann Drachen.")."""
        z = self._wohin_ziel(h)
        return h.art in ("WOHIN", "WOHIN_TP_LANE") and z is not None \
            and zeit - self._ziel_zeit.get(z, -1e9) < self.cfg["fuehren"]["ziel_wiederholen_s"]

    def _kurzform(self, p, h, text: str) -> str:
        """Pruefung c, R6: nach der ersten Nennung je Partie nur noch die Kurzform - "Dann Top-Welle." bzw. "Kauf X,
        dann Top-Welle." statt jedes Mal "dort nimmt sie sonst niemand"."""
        z = self._wohin_ziel(h)
        if z is None or z not in self._wohin_genannt:
            return text
        kurz = re.sub(r"^(zur|zum|zu den) ", "", z)
        # R10 (102112 38:01 "Dann Deinem Team."): "zu deinem Team", "auf ..." bleiben, wie sie sind
        if h.art != "KAUFEN" and not re.match(r"^(zu|auf|in|an) ", kurz):
            kurz = kurz[0].upper() + kurz[1:]
        if h.art == "KAUFEN" and ", dann " in text:
            return text.rsplit(", dann ", 1)[0] + f", dann {kurz}."     # das letzte ", dann" ist der Weiterweg
        if h.art in ("WOHIN", "WOHIN_TP_LANE"):
            praefix = re.match(r"^(Noch \d+ Sekunden: )", text)
            return (praefix.group(1) if praefix else "") + f"Dann {kurz}."
        return text

    def _schranken(self, m: Merkmale, kand: list, modus: str | None) -> list:
        """Qualitaetsrunde 3.
        R1: unter vor_leben_min ist keine Vorwaerts-Handlung Kandidat (Ausnahme: NEHMEN in der Grube ohne Kampf, das in
        <= 5 s faellt); eine Vorwaerts-Handlung mit p_tod >= vor_p_tod_max ist keiner.
        R2: was am ungeeichten Kampfmodell haengt (BESTREITEN, TP_SPIEL, daten["modell_stumm"]), wird berechnet und
        protokolliert, aber nicht Kandidat - bis [kampf].geeicht."""
        cs = self.cfg["schranken"]
        le = m.leben
        aus, weg = [], []
        for h in kand:
            if h.art in VOR_SCHRANKE:
                ausnahme = (h.art == "NEHMEN" and h.daten.get("in_grube") and h.daten.get("P_kampf", 1.0) < 0.1
                            and h.daten.get("faellt_in", 99.0) <= 5.0)
                if le is not None and le < cs["vor_leben_min"] and not ausnahme:
                    weg.append(f"{h.art}: Leben {le:.2f}")
                    continue
                if h.p_tod >= cs["vor_p_tod_max"]:
                    weg.append(f"{h.art}: p_tod {h.p_tod:.2f}")
                    continue
            if h.art in UEBERLEGEN_ARTEN or h.art in MODELL_STUMM or h.daten.get("modell_stumm"):
                u, grund = self._ueberlegen(m, h)
                if u == "unterlegen" and h.art in UEBERLEGEN_ARTEN:
                    weg.append(f"{h.art}: klar unterlegen, {grund}")      # Auftrag 004, Teil B: aus
                    continue
                if not self.cfg["kampf"].get("geeicht", False) and (h.art in MODELL_STUMM or h.daten.get("modell_stumm")):
                    if u == "ueberlegen" and h.art in UEBERLEGEN_ARTEN:
                        # Auftrag 004, Teil B: robust klar ueberlegen - spricht ohne Kampfmodell, mit diesem Grund
                        from .ueberlegen import mit_grund
                        mit_grund(h, grund)
                        h.daten["modell_stumm"] = False
                        h.daten["ueberlegen"] = grund
                    else:
                        self._stumm(m, h.art, h.satz or h.kurz(), modus, schluessel=h.ziel.name if h.ziel else None)
                        continue
            aus.append(h)
        self._schranke_takt = weg or None
        return aus

    def _ueberlegen(self, m: Merkmale, h) -> tuple[str | None, str]:
        """Auftrag 004, Teil B: die Lage am Ziel der Handlung - G ist, wer kommt, bevor sie erledigt ist."""
        from .ueberlegen import lage
        ort = h.daten.get("ziel_pos") or (h.ziel.pos if h.ziel is not None else None) or m.pos
        fenster = max(self.cfg["kampf"]["fenster_s"], min(h.dauer or 0.0, 45.0))
        u, grund = lage(m, self.cfg, ort, fenster)
        merk = getattr(self, "_ueberlegen_merk", None)
        if merk is None:
            self._ueberlegen_merk = merk = {}
        schl = (h.art, h.ziel.name if h.ziel is not None else None)
        if u == "ueberlegen":
            merk[schl] = (m.zeit, grund)
        elif u == "unterlegen":
            merk.pop(schl, None)
        elif schl in merk and m.zeit - merk[schl][0] <= self.cfg["ueberlegen"]["halten_s"]:
            return "ueberlegen", merk[schl][1]        # kein Flackern: das Urteil haelt halten_s
        return u, grund

    def _stumm(self, m: Merkmale, art: str, text: str, modus: str | None, schluessel: str | None = None) -> None:
        """Entscheidung 2: ein Kampf-Ruf des ungeeichten Modells - ins Protokoll, nicht in die Stimme. Derselbe Ruf
        (Art und Text, oder Art und `schluessel`, etwa das Ziel) steht hoechstens alle annehmen_wiederholen_s einmal
        darin."""
        alt = next((x for x in reversed(self.stumm_modell) if x["art"] == art
                    and (x.get("schluessel") == schluessel if schluessel else x["text"] == text)), None)
        if alt is not None and m.zeit - alt["zeit"] < self.cfg["kampf"]["annehmen_wiederholen_s"]:
            self._stumm_takt = self._stumm_takt or f"{art}: {text}"
            return
        self.stumm_modell.append({"zeit": m.zeit, "art": art, "text": text, "modus": modus, "schluessel": schluessel})
        self._stumm_takt = f"{art}: {text}"

    def rueckblick_text(self, zeit: float, taeter: str | None, beteiligt: list[str], turm: bool,
                        leben: float | None, sonst: str) -> str:
        """Buch 7, 8: der Todesrueckblick aus der Probe am letzten Entscheidungspunkt; erkennt sie keine Lage, gilt
        `sonst` (die Fassung der Qualitaetsrunde, komponist.todesrueckblick)."""
        from .modi.kampf import rueckblick
        if self.stellung != "neu" or "KAMPF" not in self.modi:
            return sonst
        # Pruefung c, R9: kam in den 20 s vor dem Tod ein Ruf des Coaches nach vorn, lehrt der Rueckblick nicht dagegen -
        # er beschreibt die Lage nuechtern, und der Ruf steht in _kern.jsonl als "Ruf vor Tod"
        gesagt = self.transport.gesagt if self.transport is not None else []
        ruf = next((a for a in reversed(gesagt) if a.schluessel.startswith("kern:") and a.gesprochen is not None
                    and zeit - 20.0 <= a.gesprochen <= zeit
                    and a.schluessel.split(":", 1)[1] in VORWAERTS_RUF), None)
        if ruf is not None:
            self._ruf_vor_tod = (zeit, ruf.text)
            wer = [n for n in beteiligt if n] or ([taeter] if taeter else [])
            plan = self.fuehrer.plan
            obj = plan.handlung.daten.get("objective") if plan is not None else None
            from .modi.objective import AM
            wo = AM.get(obj, "Dort") if obj else "Dort"
            wo = wo[0].upper() + wo[1:]
            zahl = {2: "zwei", 3: "drei", 4: "vier", 5: "fünf"}
            s1 = (f"{wo} kamen {zahl.get(len(wer), len(wer))} von ihnen zusammen." if len(wer) >= 2
                  else f"{wo} kam {wer[0]} dazu." if wer else f"{wo} kam es zum Kampf.")
            return s1 + " Schau es dir im Review an."
        probe = self.proben.letzte(zeit)
        if probe is not None:
            # was zuletzt GESPROCHEN wurde, zaehlt - uebergeben ist nicht gesagt, und nach "Raus" kann "Dreh um" und
            # "Rein!" gekommen sein (140253 10:16: "Raus kam, du bist geblieben", zuletzt gesprochen war "Rein!")
            gesagt = self.transport.gesagt if self.transport is not None else []
            richtung = None
            for a in gesagt:
                if a.gesprochen is None or not (probe["zeit"] <= a.gesprochen <= zeit):
                    continue
                if a.schluessel in ("kern:ZURUECK", "kern:RAUS", "kern:BACK_JETZT"):
                    richtung = "raus"
                elif a.schluessel in ("kern:REIN", "kern:ANNEHMEN", "kern:DREHEN"):
                    richtung = "rein"
            probe = dict(probe, ansage=richtung)
        j = self.m.b.jungler if self.m is not None and self.m.b is not None else None
        text = rueckblick(probe, taeter, beteiligt, turm, leben, jungler=j.champion if j is not None else None)
        if text is None or len(text.split()) > self.cfg["kampf"]["max_woerter_rueckblick"]:
            return sonst
        return text

    def _schutz_episode(self, m: Merkmale) -> None:
        """G1: die Episode der verlorenen Lane. Sie beginnt, wenn die Lane verloren ist (modi.lane_verloren), und endet,
        wenn die Kraft wieder >= 0 ist oder ihr Bauteil gekauft wurde. Das Bauteil ist das naechste aus dem Kaufplan
        zu Beginn - vorher fragte lane._bauteil je Takt mit dem Gold dieses Takts, das Item sprang (Caulfields ->
        Axiombogen -> Brutalisierer). Beginnt sie gegen denselben Gegner neu, ehe ihr Bauteil gekauft ist, setzt sie die
        alte fort (Bauteil, lange Fassung gesagt, Uhr der kurzen): die Kraft pendelt mit jedem Levelaufstieg zwischen
        -1 und 0 (144655: sechs Neubeginne in acht Minuten)."""
        from .modi import lane_kraft, lane_verloren
        from .modi.lane import _bauteil, bauteil_gekauft
        b = m.b
        if b is None or b.lane is None or b.ich is None:
            return
        kraft = lane_kraft(b)
        verloren, tode = lane_verloren(m)
        sep = self._schutz
        # uebergeben ist nicht gesprochen: verfiel der Satz ungesprochen (Sprechplan, Sperren), gilt er als nicht gesagt
        # (144655 6:45: die lange Fassung zum Brutalisierer wurde uebergeben und nie gesprochen)
        off = sep.get("offen") if sep is not None else None
        if off is not None and off[0] is not None:
            if off[0].gesprochen is not None:
                sep["offen"] = None
            elif m.zeit - off[0].zeit > off[0].gueltig + 2.0:
                sep.update(off[1])
                sep["offen"] = None
                self._schutz_wieder = True     # der Plan haelt still - also von hier aus noch einmal anbieten
                for k in [k for k in self._angesagt if k[0] == "WELLE_HALTEN"]:
                    del self._angesagt[k]
        if sep is not None and (kraft >= 0.0 or bauteil_gekauft(m, sep["teil"]) or b.lane.champion != sep["gegner"]):
            self._schutz_ende = dict(sep)
            self._schutz = sep = None
        if sep is None and verloren:
            alt = self._schutz_ende
            if alt is not None and alt["gegner"] == b.lane.champion and not bauteil_gekauft(m, alt["teil"]):
                self._schutz = dict(alt, rueckkehr=alt["rueckkehr"])        # dieselbe Episode, weiter
            else:
                self._schutz = {"t": m.zeit, "teil": _bauteil(m), "lang": False, "kurz": None, "rueckkehr": False,
                                "gegner": b.lane.champion}

    def _rueckzug_aktiv(self, m: Merkmale) -> dict | None:
        ep = self._rueckzug_ep
        return ep if ep is not None and m.zeit - ep["zuletzt"] <= RUECKZUG_EPISODE_S else None

    def _erinnerung(self, ev, m: Merkmale, gesagt: list):
        p = ev.plan
        h = p.handlung
        # nur an einen Plan, den es in diesem Takt gibt: haelt er ueber eine Luecke (G3), ist sein Schritt gerade nicht
        # erlaubt (140253 8:16: "Jetzt back", waehrend Yasuo dich im Kanal erreichte - nie_back, Pruefung D2)
        if not any(x.art == p.als() for x in (self.kandidaten or [])):
            return None
        ep = self._rueckzug_aktiv(m)
        im_rueckzug = ep is not None and p.als() in ("ZURUECK", "BACK_JETZT")
        if im_rueckzug:
            # im Rueckzug ist der Back sein zweiter Schritt, keine Erinnerung - einmal (Pruefung D, 144655 4:52/5:00)
            if ep["back"] or p.als() != "BACK_JETZT":
                return None
            gruende = h.daten.get("gruende") or ([h.grund] if h.grund else [])
            # R10 (164326 10:21 "Back jetzt: ..." -> 10:36 "Jetzt back: ..."): war der Back selbst der Plan, bleibt
            # seine Fassung; "Jetzt back" ist der zweite Schritt eines Rueckzugs
            text = ("Back jetzt" if p.art == "BACK_JETZT" else "Jetzt back") + (f": {gruende[0]}." if gruende else ".")
        elif p.als() == "ZURUECK" and h.daten.get("ort"):     # erinnert wird nur, wer noch nicht dort ist
            text = f"Denk dran: raus zu {h.daten['ort']}: {h.grund}."
        elif h.daten.get("verloren"):
            return None      # G1: der Schutzplan erinnert sich selbst (kurze Fassung nach Tod oder Basis)
        else:
            text = f"Denk dran: {h.satz}" if h.satz else None
            if text:
                from .modi import kuerze
                text = kuerze(text, self.cfg["sprechen"]["max_woerter"])      # Auftrag 002, S2.3
        if not text:
            return None
        if self._back_sperre(m, text) is not None:
            return None                          # Pruefung c, R4
        a = self.sprecher.ansage("ERINNERUNG", p.art, text, m.zeit, self._pruefung(p), gesagt)
        if a is not None:
            if im_rueckzug:
                ep["back"] = True
            if BACK_RUF.search(text):
                self._back_gesagt(m)
            self._gesprochen(a, "ERINNERUNG", m)
        return a

    def _nicht_ausgefuehrt(self, m: Merkmale, p) -> bool:
        """8.2 Punkt 5, nur wo es messbar ist: BACK (nicht in der Basis und du laeufst weiter herum) und ZURUECK (der
        Weg zum sicheren Ort ist nicht kuerzer geworden)."""
        art = p.als()
        if m.b is None or m.tot:
            return False
        if art == "BACK_JETZT":
            v = [x for x in self.bau.verlauf if x[0] >= m.zeit - 3.0 and x[2] is not None]
            from ..bewertung import abstand
            bewegt = len(v) >= 2 and m.pos is not None and abstand(v[0][2], m.pos) >= 200
            return m.bereich != "basis_eigen" and bewegt
        if art in ZIEL_ARTEN and p.start is not None and p.start.get("pos") is not None and m.pos is not None:
            # Kapitel 6: ausserhalb der Lane > ohne_plan_s, ohne dem Ziel naeher zu kommen
            z = p.handlung.ziel
            if z is None or z.pos is None or (m.bereich or "").startswith("lane") or p.gesagt is None \
                    or m.zeit - p.gesagt < self.cfg["mitte"]["ohne_plan_s"]:
                return False
            from ..bewertung import abstand
            return abstand(p.start["pos"], z.pos) - abstand(m.pos, z.pos) < 800 and abstand(m.pos, z.pos) > 1200
        if art == "ZURUECK" and p.start is not None and p.start.get("sicher_weg") is not None:
            # nur, wenn die Gefahr noch da ist und du nicht schon am sicheren Ort stehst (140253: "Denk dran: Bleib an
            # deinem Mid-Turm", waehrend Riven dort stand)
            jetzt = m.b.sicherer_ort()[1]
            return self.gefahr and jetzt is not None and jetzt > 4.0 and jetzt >= p.start["sicher_weg"] - 1.0
        return False

    def _basis_warten(self, m: Merkmale, gesagt: list):
        """Warteregel BASIS (6.3): > 20 s nach dem Kauf (oder dem Eintritt) noch in der Basis: das beste Ziel, danach
        alle 30 s, hoechstens dreimal - in der Basis ist Untaetigkeit selbst das Problem (102112, 31:00-32:00)."""
        from .modi import basis
        c = self.cfg["recall"]
        s = self._basis
        ref = s["kauf"] if s["kauf"] is not None else s["seit"]
        if ref is None or s["n"] >= c["basis_hoechstens"] or m.zeit - ref < c["basis_warten_s"]:
            return None
        if s["zuletzt"] is not None and m.zeit - s["zuletzt"] < c["basis_wieder_s"]:
            return None
        z = basis.wohin(m, self.cfg, "BASIS", self._wohin, self._lage(m))     # dasselbe Ziel wie beim Kauf (C4)
        if not z.satz:
            return None          # Pruefung c, R6: kein sicheres Ziel
        if self._ziel_eben(z, m.zeit):
            return None          # Auftrag 003, Teil A 5
        text = z.satz if z.satz.startswith(("Geh", "TP", "Lauf", "Zurück")) else \
            "Geh jetzt: " + z.satz[0].lower() + z.satz[1:]
        text = self._kurzform(None, z, text)       # Pruefung c, R6: "Dann Top-Welle."
        from .modi import kuerze
        text = kuerze(text, self.cfg["sprechen"]["max_woerter"])        # Auftrag 002, S2.3
        a = self.sprecher.ansage("PLAN", z.art, text, m.zeit, None, gesagt)
        if a is not None:
            s["n"] += 1
            s["zuletzt"] = m.zeit
            self._wohin_merken(z, m.zeit)
            self._gesprochen(a, "PLAN", m)
        return a

    # --- neues Ereignis und Bestaetigung -----------------------------------------------

    def _ereignisse_merken(self, m: Merkmale, p) -> None:
        """9.4 Punkt 5: ein Gegner wird in <= 3000 neu sichtbar (5 s davor nicht), Kill oder Tod, dein Leben faellt um
        > 15 % (seit der letzten Ansage), ein Objective faellt."""
        b = m.b
        if b is not None:
            nah = {g.champion for g in b.gegner if g.sichtbar and g.abstand is not None and g.abstand <= 3000}
            vorher = set().union(*(s for _, s in self._sicht)) if self._sicht else None
            if vorher is not None and nah - vorher:
                self._ereignis_t = m.zeit
            self._sicht.append((m.zeit, {g.champion for g in b.gegner if g.sichtbar}))
            while self._sicht and self._sicht[0][0] < m.zeit - 5.0:
                self._sicht.popleft()
        if p is not None:
            kills = len(p.kills_von("ChampionKill"))
            objs = sum(len(p.kills_von(e)) for e in ("DragonKill", "BaronKill", "HeraldKill", "HordeKill",
                                                     "TurretKilled", "InhibKilled"))
            if (self._kills is not None and kills > self._kills) or (self._objs is not None and objs > self._objs):
                self._ereignis_t = m.zeit
            self._kills, self._objs = kills, objs
        if m.leben is not None and self._leben_bei_ansage is not None and m.leben < self._leben_bei_ansage - 0.15:
            self._ereignis_t = m.zeit
            self._leben_bei_ansage = m.leben

    def _bestaetigung_merken(self, m: Merkmale, modus: str | None) -> None:
        """Buch 3, 5 / Buch 1, 4: Crash, leere Lane, Platten, Unter-Turm-Farmen merken; beim Eintritt in die Basis per
        Recall (ohne Tod, die letzte Position vor <= 12 s weit draussen) die passende Bestaetigung vor den Kauf-Satz."""
        from ..bewertung import BRUNNEN, abstand
        zeit = m.zeit
        w = m.welle
        if modus == "LANE" and w is not None:
            if w.zustand == "GECRASHT_BEI_IHM":
                self._crash_zuletzt = zeit
            elif w.zustand == "LEER":
                self._leer_zuletzt = zeit
        plan = self.fuehrer.plan
        self._mitte_merken(m)
        if plan is not None and plan.art == "UNTER_TURM_FARMEN":
            self._utf_zuletzt = zeit
        if m.b is not None and m.b.platten_gegner is not None:
            if plan is not None and plan.art == "PLATTEN" and self._platten_vorher is not None \
                    and m.b.platten_gegner < self._platten_vorher:
                self._platte_geholt = zeit
            self._platten_vorher = m.b.platten_gegner
        if not m.tot and m.bereich not in (None, "basis_eigen") and m.pos is not None:
            self._draussen = (zeit, m.pos)
        if modus == "BASIS" and self._modus_vorher not in ("BASIS", "TOT") and self._draussen is not None \
                and not m.tot:
            t0, pos = self._draussen
            brunnen = BRUNNEN.get(m.p.mein_team if m.p is not None else "ORDER")
            recall = zeit - t0 <= 12.0 and brunnen is not None and abstand(pos, brunnen) >= 4000
            if recall:
                start = zeit - self.cfg["recall"]["kanal_s"]
                text = None
                lohnt = m.kauf is not None and m.kauf.lohnt
                if (self._crash_zuletzt >= start - 10 or self._leer_zuletzt >= start - 10) and lohnt:
                    text = "Sauber: Welle drin, dann back."
                elif self._platte_geholt >= start - 30:
                    text = "Platte geholt und weg - genau so."
                elif self._utf_zuletzt >= start - 30 and m.welle_vorher is not None \
                        and m.welle_vorher.zustand == "LEER":
                    text = "Gut - nichts verloren."
                if text and self.sprecher.bestaetigung_frei(zeit, [], modus, self.gefahr):
                    self._praefix = (zeit, text)
                    self.sprecher.bestaetigt_zuletzt = zeit
                    self.staerken.append((zeit, text))
        # Basis-Uhr fuer die Warteregel
        s = self._basis
        if modus == "BASIS" and not m.tot:
            if s["seit"] is None:
                self._basis = s = {"seit": zeit, "kauf": None, "n": 0, "zuletzt": None, "gold": None}
            gold = m.b.gold if m.b is not None else None
            if gold is not None and s["gold"] is not None and s["gold"] - gold >= self.cfg["recall"]["kauf_sprung"]:
                s["kauf"], s["n"], s["zuletzt"] = zeit, 0, None
            s["gold"] = gold
        elif modus not in ("BASIS", None):
            s["seit"] = None

    def _bestaetigung_allein(self, m: Merkmale, modus: str | None, gesagt: list):
        """Bestaetigungen ohne Kauf-Satz: Rueckzug hat sich gelohnt, Stapel zur Kanone, Fokus Kontroll-Auge."""
        from ..bewertung import abstand
        from .modi import KONTROLLAUGE
        zeit = m.zeit
        if not self.sprecher.bestaetigung_frei(zeit, gesagt, modus, self.gefahr):
            return None
        text = None
        if self._rueckzug is not None:
            # G4 (Qualitaetsrunde 2): "Gut raus" erst 10 s nach dem Rueckzug-Satz - wenn dein Leben darin um < 20 Punkte
            # fiel, du am sicheren Ort bist und dort, wo du warst, einer von ihnen auftauchte. Vorher kam es nach
            # wenigen Sekunden (144655 4:39 - 13 s spaeter 19 %), auch im Kampf (133930 7:01), und immer als "er"
            # (140253 6:11: es kamen drei).
            from .modi import am_sicheren_ort
            t0, pos, wer, leben0, da = self._rueckzug
            if pos is not None and m.b is not None:
                da |= {g.champion for g in m.b.gegner if g.champion in wer and g.sichtbar and g.pos is not None
                       and abstand(g.pos, pos) <= 1500}
            tief = leben0 is not None and m.b is not None and m.b.leben is not None \
                and leben0 - m.b.leben >= GUT_RAUS_VERLUST
            if m.tot or tief or modus == "KAMPF" or zeit - t0 > GUT_RAUS_S + 5:
                self._rueckzug = None
            elif zeit - t0 >= GUT_RAUS_S and da and m.pos is not None and am_sicheren_ort(m) \
                    and abstand(pos, m.pos) >= 600:
                text = "Gut raus."        # Pruefung c, R8: ohne Pronomen (gewarnt vor mehreren, gesehen einer)
                self._rueckzug = None
        plan = self.fuehrer.plan
        if text is None and plan is not None and plan.art == "STAPELN" and m.welle is not None \
                and m.welle.zustand == "GECRASHT_BEI_IHM" and self._stapel_bestaetigt != plan.handlung.daten.get(
                    "objective"):
            o = next((o for o in m.objectives if o.schl == plan.handlung.daten.get("objective")), None)
            if o is not None and 15 <= o.spawn_in <= 30:
                text = "Genau so - er muss jetzt wählen."
                self._stapel_bestaetigt = o.schl
        if text is None:
            text = self._mitte_bestaetigung(m)
        if text is None and not self._fokus_bestaetigt and m.fokus and "kontroll" in m.fokus.lower() \
                and m.b is not None and KONTROLLAUGE in m.b.ich.items:
            text, self._fokus_bestaetigt = "Kontroll-Auge gekauft - genau der Fokus.", True
        if text is None:
            return None
        # G4: nie in KAMPF - auch nicht, wenn der Satz erst spaeter drankommt (133930 7:01)
        a = self.sprecher.ansage("BESTAETIGUNG", "bestaetigung", text, zeit,
                                 lambda: self.modus.aktuell != "KAMPF", gesagt)
        if a is not None:
            self.sprecher.bestaetigt_zuletzt = zeit
            self.staerken.append((zeit, text))
            self._gesprochen(a, "BESTAETIGUNG", m)
        return a

    def _mitte_merken(self, m: Merkmale) -> None:
        """Buch 5, 9: solange einer dieser Plaene laeuft, merken, woran sein Ausgang zu erkennen ist."""
        plan = self.fuehrer.plan
        if plan is None or m.b is None or m.p is None:
            return
        h, w = plan.handlung, self._mitte_wache
        if plan.art == "WELLE_UND_RAUS" and h.daten.get("spawn") is not None:
            w["WELLE_UND_RAUS"] = (m.zeit, h.daten["spawn"], h.daten.get("ziel_pos"))
        elif plan.art in ("DRUECKEN", "MIT_GRUPPE") and h.daten.get("umwandeln") and h.daten.get("turm"):
            w["UMGEWANDELT"] = (m.zeit, h.daten["turm"], h.daten.get("nexus_weg", 0))
        elif plan.art == "TP_SPIEL":
            w["TP_SPIEL"] = (m.zeit, w.get("TP_SPIEL", (0, len(m.tote_gegner)))[1])
        elif plan.art == "SEITENWELLE" and h.daten.get("lane"):
            from ..bewertung import stehende_tuerme
            lane = h.daten["lane"]
            eigene = sum(1 for k in stehende_tuerme(m.p) if k[0] == m.p.mein_team and k[1] == lane)
            w["SEITENWELLE"] = (m.zeit, lane, w.get("SEITENWELLE", (0, lane, eigene))[2])

    def _mitte_bestaetigung(self, m: Merkmale) -> str | None:
        """Buch 5, 9: pünktlich rotiert, umgewandelt, guter TP, Seitenwelle gerettet - je einmal, wenn es eintritt
        (hoechstens 60 s nach dem Plan; tot: keine)."""
        from ..bewertung import abstand, stehende_tuerme
        w, zeit = self._mitte_wache, m.zeit
        for k in [k for k, v in w.items() if zeit - v[0] > 60]:
            del w[k]
        if m.tot or m.p is None:
            w.clear()
            return None
        if (v := w.get("WELLE_UND_RAUS")) is not None:
            _, spawn, pos = v
            if zeit > spawn:
                del w["WELLE_UND_RAUS"]
            elif pos is not None and m.pos is not None and abstand(m.pos, pos) <= 2000:
                del w["WELLE_UND_RAUS"]
                return "Genau so - Welle drin und pünktlich da."
        from .modi.karte import steht
        if (v := w.get("UMGEWANDELT")) is not None and not steht(m, tuple(v[1]), v[2]):
            del w["UMGEWANDELT"]
            return "Sauber umgewandelt."
        if (v := w.get("TP_SPIEL")) is not None and m.tp_in is not None and m.tp_in > 0 \
                and len(m.tote_gegner) > v[1]:
            del w["TP_SPIEL"]
            return "Guter TP."
        if (v := w.get("SEITENWELLE")) is not None:
            _, lane, eigene = v
            wl = m.wellen.get(lane) if m.wellen else None
            jetzt = sum(1 for k in stehende_tuerme(m.p) if k[0] == m.p.mein_team and k[1] == lane)
            if jetzt < eigene:
                del w["SEITENWELLE"]
            elif m.lane_hier == lane and wl is not None and wl.zustand in ("LEER", "MITTE", "ZU_IHM", "GROSS_ZU_IHM"):
                del w["SEITENWELLE"]
                return "Welle gerettet - kein Turm verloren."
        return None

    # --- Protokoll, Dashboard, Claude ----------------------------------------------------

    def _protokoll(self, p, m: Merkmale | None) -> None:
        if self._datei is None or m is None:
            return
        plan = self.fuehrer.plan
        zeile = {"t": round(p.zeit, 2), "modus": self.modus.aktuell, "grund": self.modus.grund,
                 "bereich": m.bereich, "lane_phase": m.lane_phase, "kampf": m.im_kampf, "frisch": m.daten_frisch}
        if self.stellung != "alt":
            zeile.update(plan=plan.art if plan else None, schritt=plan.schritt if plan else None,
                         ziel=plan.handlung.ziel.name if plan and plan.handlung.ziel else None,
                         ev=round(plan.handlung.ev) if plan else None, gefahr=self.gefahr,
                         top=[(h.art, round(h.ev)) for h in self.fuehrer.top],
                         gehalten=self.fuehrer.gehalten, gate=self.gate_grund,
                         welle=m.welle.zustand if m.welle is not None else None)
            # Buch 6, 14: p_erfolg, anteil und objective_zieht je Objective - fuer die Kennzahl "ohne Chance"
            if m.obj_urteile:
                zeile["objectives"] = {s: [round(u.p_erfolg, 3), round(u.anteil, 3), u.zieht, u.grund]
                                       for s, u in m.obj_urteile.items()}
            if plan is not None and plan.handlung.daten.get("objective"):
                zeile["plan_objective"] = plan.handlung.daten["objective"]
            if self._stumm_takt:
                zeile["stumm"] = f"Modell nicht geeicht - {self._stumm_takt}"
            if self._schranke_takt:
                zeile["schranke"] = self._schranke_takt
            if self._ruf_vor_tod is not None and abs(self._ruf_vor_tod[0] - p.zeit) <= 1.0:
                zeile["ruf_vor_tod"] = self._ruf_vor_tod[1]
            if self._letzte is not None:
                zeile["wuerde_sagen" if self.stellung == "schatten" else "sagt"] = list(self._letzte)
        try:
            self._datei.write(json.dumps(zeile, ensure_ascii=False) + "\n")
        except (OSError, ValueError):
            pass

    def stand(self) -> dict:
        """Fuer Dashboard und Claude: Modus, Plan mit Grund, die Top-3 (9.5), die letzten INFO-Zeilen."""
        m = self.m
        plan = self.fuehrer.plan
        return {"modus": self.modus.aktuell, "seit": self.modus.seit, "grund": self.modus.grund,
                "bereich": bereich_worte(m.bereich if m else None),
                "plan": None if plan is None else {"art": plan.art, "ziel": plan.handlung.ziel.name
                                                   if plan.handlung.ziel else "", "grund": plan.handlung.grund,
                                                   "satz": plan.handlung.satz, "ev": round(plan.handlung.ev),
                                                   "schritte": plan.handlung.schritte, "schritt": plan.schritt},
                "top": [{"art": h.art, "ev": round(h.ev), "grund": h.grund} for h in self.fuehrer.top],
                "gefahr": self.gefahr,
                "info": [{"zeit": t, "text": x} for t, x in list(self.info)[-6:]][::-1],
                # Buch 11, 2 und 3
                "danach": self.danach_text,
                "zeitleiste": _zeitleiste_stand(self.zeitleiste, m.zeit if m else 0.0)}

    def kontext(self) -> str | None:
        """Buch 11, 6 (ersetzt Buch 0, 10.2): hoechstens 30 Zeilen fuer Claude - Modus, Ort, Leben, Gold; Plan mit Grund
        und danach; Top-3; Zeitleiste; Flash-Tabelle; Stand; Gegner und Mitspieler mit Ort und Zeit."""
        m = self.m
        if m is None or m.p is None or m.b is None:
            return None
        from . import fuehren, zeitleiste
        from .fragen import satz
        p, b = m.p, m.b
        z = [f"MODUS: {self.modus.aktuell} - du stehst {bereich_worte(m.bereich)}; Leben "
             f"{int(round((m.leben or 0) * 100))} %, Gold {int(b.gold or 0)}, Level {p.ich.level if p.ich else '?'}."]
        plan = self.fuehrer.plan
        if plan is not None:
            z.append(f"PLAN (entschieden): {satz(plan.handlung)}")
            if self.danach_text:
                z.append(f"DANACH: {self.danach_text}")
        top = [h for h in sorted(self.kandidaten or [], key=lambda h: -h.ev) if not fuehren.stumm(h)][:3]
        if top:
            z.append("ALTERNATIVEN: " + " | ".join(f"{fuehren.kurz(h)} ({h.grund or '-'}, EV {h.ev:+.0f})" for h in top))
        if self.zeitleiste:
            z.append("ZEITLEISTE (naechste 3 Minuten): " + zeitleiste.als_text(self.zeitleiste, m.zeit, 6))
        try:
            from ..antworten import flash_stand
            wort = {"weg": "OHNE Flash noch {r} s", "da": "Flash wieder da", "unbekannt": "unbekannt",
                    "ohne": "spielt kein Flash"}
            z.append("FLASH DER GEGNER: " + "; ".join(f"{c}: " + wort[a].format(r=int(r or 0))
                                                      for c, a, r in flash_stand(p, self._lagebild)))
        except Exception:
            pass
        from ..zustand import gegenteam
        wir, die = p.mein_team, gegenteam(p.mein_team)
        z.append(f"STAND: Kills {p.kills(wir)} zu {p.kills(die)}, Tuerme "
                 f"{sum(1 for e in p.kills_von('TurretKilled') if e.team == wir)} zu "
                 f"{sum(1 for e in p.kills_von('TurretKilled') if e.team == die)}, Drachen {len(p.drachen(wir))} zu "
                 f"{len(p.drachen(die))}, Item-Gold {p.item_gold(wir) - p.item_gold(die):+d}.")
        for g in b.gegner[:5]:
            if g.s.tot:
                z.append(f"- Gegner {g.champion}: tot, noch {int(g.s.respawn or 0)} s")
            else:
                wo = (g.ort or "Ort unbekannt") + (f", vor {int(g.seit)} s" if g.seit else ", sichtbar" if g.sichtbar else "")
                z.append(f"- Gegner {g.champion} L{g.s.level}: {wo}"
                         + (f", {int(g.abstand)} von dir" if g.abstand is not None else ""))
        for s, wo, le, *rest in (b.mitspieler or [])[:4]:
            z.append(f"- Mitspieler {s.champion}: {'tot' if s.tot else (rest[0] if rest and rest[0] else 'unterwegs')}")
        return "\n".join(z[:30])

    def kopfzeile(self) -> str | None:
        """Erste Zeile(n) jeder Claude-Frage (Kapitel 5.2, 10.2): Modus und - wenn der Kern entscheidet - sein Plan."""
        if self.modus.aktuell is None:
            return None
        zeile = f"MODUS: {self.modus.aktuell} - du stehst {bereich_worte(self.m.bereich if self.m else None)}"
        plan = self.fuehrer.plan
        if plan is not None and self.spricht_in(self.modus.aktuell) and not plan.handlung.stumm:
            zeile += f"\nPLAN DES COACHS: {plan.handlung.satz or plan.handlung.kurz()}"
        return zeile

    def schliessen(self) -> None:
        if self._datei is not None:
            try:
                self._datei.close()
            except OSError:
                pass
            self._datei = None
