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

KERN_MODI_3 = ("LANE", "BASIS", "TOT")
KERN_MODI_4 = KERN_MODI_3 + ("SEITE", "GRUPPE", "UNTERWEGS", "VERTEIDIGEN")     # Schritt 4 (Buch 5)
# Die Modi, in denen der Kern live spricht (seit Schritt 4). LOLCOACH_KERN_SCHRITT=3 oder Kern(modi=KERN_MODI_3) gibt
# den Stand von Schritt 3 - fuer Gegenproben beim Nachspielen.
KERN_MODI = KERN_MODI_4
SPIELSTART_S = 60.0      # davor schweigt der Kern in der Basis (nicht im Buch, Schritt 3: messungen.md)
STELLUNGEN = ("alt", "schatten", "neu")
# Kehrtwende-Richtung einer Ansage des alten Systems (nur Text, Kapitel 9.4 Punkt 5)
VOR_TEXT = re.compile(r"Geh rein|nimm den Kampf an|Halte deine Stellung|Bleib an deiner Welle|Trade|Spiel auf|"
                      r"Geh auf|Drück|Nehmt", re.I)


@lru_cache(maxsize=1)
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
        self.modi = modi or {"3": KERN_MODI_3, "4": KERN_MODI_4}.get(os.environ.get("LOLCOACH_KERN_SCHRITT", ""),
                                                                      KERN_MODI)
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
        self._angesagt: dict[tuple[str, str], float] = {}   # (Art, Ziel) -> zuletzt angesagt
        self._gefahr_gesagt: tuple[float, set] | None = None   # letzte GEFAHR: (Zeit, vor wem)
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
        ansagen = []
        self._letzte = None
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
        self._ereignisse_merken(m, p)
        self._bestaetigung_merken(m, modus)
        if not m.daten_frisch and modus != "TOT":
            self._modus_vorher = modus
            return []          # 4.3: ohne frische Daten keine neuen Plaene
        kand, self.gefahr = self._kandidaten(m, modus)
        self.kandidaten = kand
        ev = self.fuehrer.takt(m, kand, self.gefahr)
        aus = []
        # Spielbeginn: alle stehen im Brunnen, das Briefing redet - nichts, was er nicht selbst weiss
        start = modus == "BASIS" and m.zeit < SPIELSTART_S
        if ev is not None and ev.art in ("neu", "gefahr", "schritt") and not start:
            if (a := self._ansage_zum_plan(ev, m, modus, gesagt)) is not None:
                aus.append(a)
        if not aus and modus == "BASIS" and not start:
            if (a := self._basis_warten(m, gesagt)) is not None:
                aus.append(a)
        if not aus:
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
        self._modus_vorher = modus
        return aus

    # --- Kandidaten --------------------------------------------------------------------

    def _kandidaten(self, m: Merkmale, modus: str | None) -> tuple[list, bool]:
        from . import wert
        from .modi import back_gruende, zurueck, zurueck_saetze
        from .modi import basis, gruppe, lane, seite, tot, unterwegs, verteidigen
        from .plan import gefahr_schlaegt_an
        cfg = self.cfg
        if m.b is None or modus not in self.modi:
            return [], False
        je_modus = {"LANE": lane, "BASIS": basis, "TOT": tot, "SEITE": seite, "GRUPPE": gruppe,
                    "UNTERWEGS": unterwegs, "VERTEIDIGEN": verteidigen}
        kand = je_modus[modus].kandidaten(m, cfg)
        if modus not in ("BASIS", "TOT"):         # ZURUECK: in allen Modi ausser TOT und BASIS (Buch 0, 6.3)
            kand += zurueck(m, cfg, modus, back_gruende(m, cfg))
        tk = wert.todeskosten(m, cfg)
        for h in kand:
            wert.bewerte(h, m, cfg, tk)
        bleiben = next((h for h in kand if h.art in ("FARMEN", "HALTEN")), None)
        for h in kand:
            if h.art == "ZURUECK":
                zurueck_saetze(h, m, bleiben)
        # je Art die bessere Fassung (ZURUECK: nur raus / raus und back)
        beste: dict = {}
        for h in kand:
            if h.art not in beste or h.ev > beste[h.art].ev:
                beste[h.art] = h
        kand = list(beste.values())
        farmen = next((h for h in kand if h.art in ("FARMEN", "HALTEN")), None)    # "bleiben, wo du bist"
        gefahr = farmen is not None and gefahr_schlaegt_an(farmen, cfg["gefahr"])
        plan = self.fuehrer.plan
        als = plan.als() if plan is not None else None
        if gefahr:
            # Gefahr schlaegt Timing (Buch 3, 2.1): nur sichere Handlungen - und der schuetzende Freeze (Buch 1, 3.7)
            kand = [h for h in kand if h.art in SICHER or h.daten.get("schutz") or h.art == als]
        else:
            kand = [h for h in kand if not h.daten.get("nur_bei_gefahr") or h.art == als]
        kand = [h for h in kand if not (h.daten.get("klein") and h.p_tod >= cfg["gefahr"]["p_min"])]
        return kand, gefahr

    # --- Sprechen ----------------------------------------------------------------------

    def _ansage_zum_plan(self, ev, m: Merkmale, modus: str | None, gesagt: list):
        p = ev.plan
        if p is None:
            return None
        h = p.handlung
        if ev.art == "schritt":
            kategorie, text = "PLAN", ev.text
        else:
            if h.stumm:
                return None
            kategorie = "GEFAHR" if ev.art == "gefahr" and h.art in SICHER else "PLAN"
            text = h.satz or h.kurz()
        if not text:
            return None
        if ev.art == "neu" and self._laeuft_hin(h, m):
            # Buch 5, 2: "Laeufst du schon dorthin, schweigt der Coach" - der Plan gilt als gesagt, damit die
            # Erinnerung (Kapitel 6) greift, wenn du stehen bleibst
            p.gesagt = m.zeit
            p.start = {"sicher_weg": None, "pos": m.pos}
            return None
        if self._kehrtwende(h.art if ev.art != "schritt" else p.als(), m, gesagt):
            return None
        # derselbe Plan kam eben schon (er fiel kurz weg und kam wieder): nichts Neues - der Plan gilt still weiter
        # (102112, 6:47/6:59: zweimal "Stapel die Top-Welle bis zur Kanone")
        schl = (p.art, h.ziel.name if h.ziel else "")
        if kategorie == "PLAN" and ev.art != "schritt" and \
                m.zeit - self._angesagt.get(schl, -1e9) < self.cfg["sprechen"]["wiederholen_s"]:
            p.gesagt = self._angesagt[schl]
            return None
        # dieselbe Warnung vor denselben Gegnern eben erst gesagt: nichts Neues (235433, 6:12-7:04: fuenfmal "Raus zu
        # deinem Top-Tier-1-Turm" in 52 s) - kommt ein neuer Gegner dazu, darf sie wieder
        if kategorie == "GEFAHR" and ev.art != "schritt":
            von = set(h.daten.get("gefahr_von", []))
            alt = self._gefahr_gesagt
            if alt is not None and m.zeit - alt[0] < self.cfg["sprechen"]["gefahr_wiederholen_s"] and von <= alt[1]:
                p.gesagt = alt[0]
                return None
        if modus == "BASIS" and self._praefix is not None and m.zeit - self._praefix[0] <= 15:
            text = f"{self._praefix[1]} {text}"
            self._praefix = None
        a = self.sprecher.ansage(kategorie, p.art, text, m.zeit, self._pruefung(p), gesagt)
        if a is not None:
            p.gesagt = m.zeit
            self._angesagt[schl] = m.zeit
            if kategorie == "GEFAHR":
                self._gefahr_gesagt = (m.zeit, set(h.daten.get("gefahr_von", [])))
            p.start = {"sicher_weg": m.b.sicherer_ort()[1] if m.b is not None else None, "pos": m.pos}
            if h.art == "ZURUECK":
                self._rueckzug = (m.zeit, m.pos, [n for n, x in h.daten.get("wer", []) if x >= 0.05])
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

    def _pruefung(self, p):
        """Die Ansage stimmt, solange der Kern-Plan derselbe ist (ersetzt _noch_wahr, Kapitel 9.6)."""
        schritt = p.schritt

        def pruefe() -> bool:
            q = self.fuehrer.plan
            return q is p and q.schritt == schritt
        return pruefe

    def _gesprochen(self, a, kategorie: str, m: Merkmale) -> None:
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

    def _erinnerung(self, ev, m: Merkmale, gesagt: list):
        p = ev.plan
        h = p.handlung
        if p.als() == "ZURUECK" and h.daten.get("ort"):     # erinnert wird nur, wer noch nicht dort ist: "raus zu"
            text = f"Denk dran: raus zu {h.daten['ort']}: {h.grund}."
        else:
            text = f"Denk dran: {h.satz}" if h.satz else None
        if not text:
            return None
        a = self.sprecher.ansage("ERINNERUNG", p.art, text, m.zeit, self._pruefung(p), gesagt)
        if a is not None:
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
        z = basis.wohin(m, self.cfg, "BASIS")
        text = z.satz if z.satz.startswith(("Geh", "TP")) else "Geh jetzt: " + z.satz[0].lower() + z.satz[1:]
        a = self.sprecher.ansage("PLAN", z.art, text, m.zeit, None, gesagt)
        if a is not None:
            s["n"] += 1
            s["zuletzt"] = m.zeit
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
            t0, pos, wer = self._rueckzug
            if zeit - t0 > 10 or m.tot:
                self._rueckzug = None
            elif pos is not None and m.pos is not None and m.b is not None and abstand(pos, m.pos) >= 600:
                if any(g.champion in wer and g.sichtbar and g.pos is not None and abstand(g.pos, pos) <= 1500
                       for g in m.b.gegner):
                    text, self._rueckzug = "Gut raus - da war er.", None
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
        a = self.sprecher.ansage("BESTAETIGUNG", "bestaetigung", text, zeit, None, gesagt)
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
                         welle=m.welle.zustand if m.welle is not None else None)
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
                "info": [{"zeit": t, "text": x} for t, x in list(self.info)[-6:]][::-1]}

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
