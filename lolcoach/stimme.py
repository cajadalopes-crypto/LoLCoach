"""Sprachausgabe ueber die Windows-Stimme (SAPI, offline, sofort).

Vorerst "Microsoft Hedda" (Deutsch). Die Stimme lebt in einem eigenen
Thread: SAPI ist ein COM-Objekt und darf nur aus dem Thread benutzt werden,
der es angelegt hat - gesprochen wird aber aus mehreren (Regeln im Kern,
Antworten auf Fragen aus dem Sprach-Thread).

Der Thread spricht einen Satz nach dem anderen aus seiner eigenen Schlange
(nicht SAPIs), damit ein Satz einzeln angehalten werden kann:
  pausiere()  - der Spieler drueckt Push-to-Talk: aktueller Satz stoppt und
                wird gemerkt, die Schlange wartet.
  antworte(t) - die Antwort kommt vor allem anderen, danach der unterbrochene
                Satz noch einmal (war er nicht zu alt), dann geht es weiter.
  freigeben() - nichts verstanden: unterbrochener Satz und Schlange laufen weiter.
Gemessen in Partie 3 (26.09.2026): eine Antwort hat "Warwick ist in seinem
oberen Jungle" abgewuergt - der Spieler hat die Warnung nie gehoert.
"""
from __future__ import annotations

import queue
import threading
import time

_ASYNC, _UNTERBRECHEN = 1, 2
NOCH_AKTUELL = 25.0   # so alt darf ein unterbrochener Satz sein, um wiederholt zu werden


class Stimme:
    def __init__(self, sprache: str = "German", warten: bool = False):
        """`warten`: jeder Satz blockiert, bis er gesprochen ist - zum Anhoeren
        einer Aufnahme im Zeitraffer."""
        self.warten = warten
        self._schlange: queue.Queue = queue.Queue()   # (text, fertig)
        self._vorrang: queue.Queue = queue.Queue()     # Antworten
        self._frei = threading.Event()
        self._frei.set()
        self._stopp = threading.Event()
        self._unterbrochen: tuple[str, float] | None = None
        self._bereit = threading.Event()
        threading.Thread(target=self._lauf, args=(sprache,), daemon=True).start()
        self._bereit.wait(timeout=5)

    def _lauf(self, sprache: str) -> None:
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        v = win32com.client.Dispatch("SAPI.SpVoice")
        stimmen = v.GetVoices()
        for i in range(stimmen.Count):
            if sprache in stimmen.Item(i).GetDescription():
                v.Voice = stimmen.Item(i)
                break
        v.Rate = 1
        self._bereit.set()
        while True:
            try:
                text, fertig = self._vorrang.get_nowait()
            except queue.Empty:
                if not self._frei.is_set():
                    time.sleep(0.03)
                    continue
                try:
                    text, fertig = self._schlange.get(timeout=0.05)
                except queue.Empty:
                    continue
            self._stopp.clear()
            v.Speak(text, _ASYNC)
            while not v.WaitUntilDone(40):
                if self._stopp.is_set():
                    v.Speak("", _ASYNC | _UNTERBRECHEN)
                    self._unterbrochen = (text, time.monotonic())
                    break
            if fertig is not None:
                fertig.set()

    def sage(self, text: str, dringend: bool = False) -> None:
        """`dringend`: vor alle wartenden Saetze, der laufende wird abgebrochen (nicht wiederholt)."""
        fertig = threading.Event() if self.warten else None
        if dringend:
            self._vorrang.put((text, fertig))
            if self._frei.is_set():
                self._stopp.set()
        else:
            self._schlange.put((text, fertig))
        if fertig:
            fertig.wait(timeout=60)

    def pausiere(self) -> None:
        self._frei.clear()
        self._unterbrochen = None
        self._stopp.set()

    def antworte(self, text: str) -> None:
        self._vorrang.put((text, None))
        self._wieder_und_frei()

    def freigeben(self) -> None:
        self._wieder_und_frei()

    def _wieder_und_frei(self) -> None:
        u, self._unterbrochen = self._unterbrochen, None
        if u and time.monotonic() - u[1] < NOCH_AKTUELL:
            self._vorrang.put((u[0], None))
        self._frei.set()

    # alter Name, wird noch von aussen benutzt
    def verstumme(self) -> None:
        self.pausiere()


class Stumm:
    def sage(self, text: str, dringend: bool = False) -> None:
        pass

    def pausiere(self) -> None:
        pass

    def antworte(self, text: str) -> None:
        pass

    def freigeben(self) -> None:
        pass

    def verstumme(self) -> None:
        pass
