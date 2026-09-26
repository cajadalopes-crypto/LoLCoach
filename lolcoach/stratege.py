"""Der Stratege: laesst das Gehirn im Spiel mitreden.

- Spielbeginn: Spielakte anlegen, danach das Briefing sprechen.
- Ende der Lane-Phase: "was ist ab jetzt dein Job".
- Situative Ansagen: Die Regeln entscheiden WANN (schnell, deterministisch), der
  Stratege laesst Claude formulieren WAS genau - fuer Carlos, aus der echten Lage.
  Carlos: "Er soll mir immer situativ sagen, wie ich das genau machen soll. Ich
  wuensche mir sehr viel Individualitaet beim Coach." Kommt Claude nicht rechtzeitig,
  wird der Standardsatz gesprochen - lieber allgemein als zu spaet.

Alles laeuft in Hintergrund-Threads; fertige Saetze gehen ueber `plan.einwerfen`
in den Sprechplan und werden dort wie jede Ansage getaktet.
"""
from __future__ import annotations

import threading
import time

from . import antworten, gehirn
from .regeln import WICHTIG, Ansage

VEREDELN_HOECHSTENS = 12.0   # Sekunden: laenger wartet der Standardsatz nicht


class Stratege:
    def __init__(self, plan, modell: str = "sonnet", lane_phase_bis: float = 840):
        self.plan = plan
        self.gehirn = gehirn.Gehirn(modell)
        self.lane_phase_bis = lane_phase_bis
        self._briefing = self._midgame = False
        self.p = self.lagebild = None

    def aktualisiere(self, p, lagebild=None, ansagen=None) -> None:
        self.p, self.lagebild = p, lagebild
        if not p.ich:
            return
        if not self._briefing and p.spieler:
            self._briefing = True
            self.gehirn.akte_anlegen(p, fertig=lambda akte: self._briefing_sprechen())
        if not self._midgame and p.zeit >= self.lane_phase_bis and self.gehirn.akte:
            self._midgame = True
            self._im_hintergrund(lambda: self._sprich(gehirn.MIDGAME_SYSTEM, "Ende der Lane-Phase: sein Job ab jetzt",
                                                      "midgame"))

    def _briefing_sprechen(self) -> None:
        """Das Briefing kommt mit der Spielakte; nur wenn es fehlt, eigener Aufruf."""
        if self.gehirn.briefing and self.p is not None:
            self.plan.einwerfen(Ansage(self.gehirn.briefing, WICHTIG, "briefing", zeit=self.p.zeit,
                                       gueltig=90, sperre=600))
        else:
            self._sprich(gehirn.BRIEFING_SYSTEM, "Spielbeginn: Briefing fuer den Spieler", "briefing")

    def _im_hintergrund(self, f) -> None:
        threading.Thread(target=f, daemon=True).start()

    def _sprich(self, system: str, anlass: str, schluessel: str) -> None:
        p, lb = self.p, self.lagebild
        if p is None or not p.ich:
            return
        try:
            text = self.gehirn.frage(system, anlass, p, antworten.lage_text(p, lb), timeout=60)
        except Exception as e:
            print(f"  {schluessel} fehlgeschlagen: {e}", flush=True)
            return
        from .itemnamen import absichern
        text = absichern(gehirn.kuerzen(text, 6 if schluessel == "briefing" else 3))[0]
        self.plan.einwerfen(Ansage(text, WICHTIG, schluessel, zeit=self.p.zeit, gueltig=90, sperre=600))

    def veredle(self, a: Ansage) -> None:
        """Ersetzt den Standardsatz durch eine situative Anweisung. Gibt nach
        `VEREDELN_HOECHSTENS` Sekunden auf und laesst den Standardsatz sprechen."""
        p, lb = self.p, self.lagebild
        if p is None or not p.ich:
            self.plan.einwerfen(a)
            return
        erledigt = threading.Event()

        def lauf():
            try:
                text = self.gehirn.frage(gehirn.SITUATIV_SYSTEM, f"{a.text} (Standardsatz der Regel)", p,
                                         antworten.lage_text(p, lb), timeout=VEREDELN_HOECHSTENS + 5)
            except Exception:
                text = None
            if not erledigt.is_set():
                erledigt.set()
                if text:
                    from .itemnamen import absichern
                    a.text = absichern(gehirn.kuerzen(text, 2))[0]
                self.plan.einwerfen(a)

        def notbremse():
            time.sleep(VEREDELN_HOECHSTENS)
            if not erledigt.is_set():
                erledigt.set()
                self.plan.einwerfen(a)

        self._im_hintergrund(lauf)
        self._im_hintergrund(notbremse)
