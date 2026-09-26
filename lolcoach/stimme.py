"""Sprachausgabe ueber die Windows-Stimme (SAPI, offline, sofort).

Vorerst "Microsoft Hedda" (Deutsch). Die Stimme lebt in einem eigenen
Thread: SAPI ist ein COM-Objekt und darf nur aus dem Thread benutzt werden,
der es angelegt hat - gesprochen wird aber aus mehreren (Regeln im Kern,
Antworten auf Fragen aus dem Sprach-Thread). `sage` legt nur in eine
Schlange und kehrt sofort zurueck.
"""
from __future__ import annotations

import queue
import threading

_ASYNC, _UNTERBRECHEN = 1, 2


class Stimme:
    def __init__(self, sprache: str = "German", warten: bool = False):
        """`warten`: jeder Satz blockiert, bis er gesprochen ist - zum Anhoeren
        einer Aufnahme im Zeitraffer."""
        self.warten = warten
        self._schlange: queue.Queue = queue.Queue()
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
            text, dringend, fertig = self._schlange.get()
            v.Speak(text, _ASYNC | (_UNTERBRECHEN if dringend else 0))
            if fertig is not None:
                v.WaitUntilDone(-1)
                fertig.set()

    def sage(self, text: str, dringend: bool = False) -> None:
        fertig = threading.Event() if self.warten else None
        self._schlange.put((text, dringend, fertig))
        if fertig:
            fertig.wait(timeout=60)

    def verstumme(self) -> None:
        """Bricht ab, was gerade gesprochen wird (z. B. weil der Spieler etwas fragt)."""
        self._schlange.put(("", True, None))


class Stumm:
    def sage(self, text: str, dringend: bool = False) -> None:
        pass

    def verstumme(self) -> None:
        pass
