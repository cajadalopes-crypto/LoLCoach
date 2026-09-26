"""Sprachausgabe ueber die Windows-Stimme (SAPI, offline, sofort).

Vorerst "Microsoft Hedda" (Deutsch). Spricht asynchron - der Aufrufer
wartet nicht. Eine bessere Stimme kommt, wenn der Coach mehr zu sagen hat.
"""
from __future__ import annotations

import win32com.client

_ASYNC, _UNTERBRECHEN = 1, 2


class Stimme:
    def __init__(self, sprache: str = "German"):
        self._v = win32com.client.Dispatch("SAPI.SpVoice")
        stimmen = self._v.GetVoices()
        for i in range(stimmen.Count):
            if sprache in stimmen.Item(i).GetDescription():
                self._v.Voice = stimmen.Item(i)
                break
        self._v.Rate = 1

    def sage(self, text: str, dringend: bool = False) -> None:
        self._v.Speak(text, _ASYNC | (_UNTERBRECHEN if dringend else 0))


class Stumm:
    def sage(self, text: str, dringend: bool = False) -> None:
        pass
