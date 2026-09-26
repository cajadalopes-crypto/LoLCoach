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


class _Sapi:
    """Windows-Stimme: offline, sofort, klingt aber nach Roboter (Partie 3: 'viel zu roboterhaft')."""

    def __init__(self, sprache: str, lautstaerke: int):
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        self.v = win32com.client.Dispatch("SAPI.SpVoice")
        stimmen = self.v.GetVoices()
        for i in range(stimmen.Count):
            if sprache in stimmen.Item(i).GetDescription():
                self.v.Voice = stimmen.Item(i)
                break
        self.v.Rate = 1
        self.v.Volume = lautstaerke

    def spreche(self, text: str, stopp: threading.Event) -> bool:
        self.v.Speak(text, _ASYNC)
        while not self.v.WaitUntilDone(40):
            if stopp.is_set():
                self.v.Speak("", _ASYNC | _UNTERBRECHEN)
                return False
        return True


class _Neural:
    """Microsofts neuronale Stimmen (wie "Vorlesen" in Edge), ueber edge-tts.
    Gemessen 26.09.2026: Conrad/Katja 0,35-0,45 s bis zum ersten Ton. Braucht
    Internet; faellt ein Satz aus, spricht ihn die Windows-Stimme."""

    def __init__(self, stimme: str, tempo: str, lautstaerke: int, ersatz: "_Sapi"):
        self.stimme, self.tempo, self.lautstaerke, self.ersatz = stimme, tempo, lautstaerke, ersatz
        self._cache: dict[str, tuple] = {}

    def _synthese(self, text: str):
        if text in self._cache:
            return self._cache[text]
        import asyncio
        import io
        import av
        import edge_tts
        import numpy as np

        async def hole() -> bytes:
            daten = bytearray()
            async for teil in edge_tts.Communicate(text, self.stimme, rate=self.tempo).stream():
                if teil["type"] == "audio":
                    daten += teil["data"]
            return bytes(daten)

        mp3 = asyncio.run(asyncio.wait_for(hole(), timeout=6))
        with av.open(io.BytesIO(mp3)) as c:
            strom = c.streams.audio[0]
            rate = strom.rate
            teile = [f.to_ndarray() for f in c.decode(strom)]
        audio = np.concatenate(teile, axis=1)[0]
        if audio.dtype.kind == "i":
            audio = audio.astype(np.float32) / 32768.0
        audio = (audio.astype(np.float32) * (self.lautstaerke / 100.0))
        if len(self._cache) > 200:
            self._cache.clear()
        self._cache[text] = (audio, rate)
        return audio, rate

    def spreche(self, text: str, stopp: threading.Event) -> bool:
        import sounddevice as sd
        try:
            audio, rate = self._synthese(text)
        except Exception:
            return self.ersatz.spreche(text, stopp)
        if stopp.is_set():
            return False
        sd.play(audio, rate)
        ende = time.monotonic() + len(audio) / rate + 0.3
        while time.monotonic() < ende:
            if stopp.is_set():
                sd.stop()
                return False
            time.sleep(0.02)
        return True


class Stimme:
    def __init__(self, sprache: str = "German", warten: bool = False, lautstaerke: int = 100,
                 neural: str | None = None, tempo: str = "+8%"):
        """`warten`: jeder Satz blockiert, bis er gesprochen ist - zum Anhoeren
        einer Aufnahme im Zeitraffer. `lautstaerke` 0 fuer Tests. `neural`: Name
        einer neuronalen Stimme (z. B. "de-DE-ConradNeural"), sonst die Windows-Stimme."""
        self.warten, self.lautstaerke, self.neural, self.tempo = warten, lautstaerke, neural, tempo
        self.protokoll: list[str] = []   # was angefangen wurde, in Reihenfolge
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
        motor = _Sapi(sprache, self.lautstaerke)
        if self.neural:
            motor = _Neural(self.neural, self.tempo, self.lautstaerke, ersatz=motor)
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
            self.protokoll.append(text)
            if not motor.spreche(text, self._stopp):
                self._unterbrochen = (text, time.monotonic())
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
