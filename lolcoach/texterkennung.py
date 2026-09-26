"""Text aus Bildschirmausschnitten lesen: die eingebaute Windows-Texterkennung (Deutsch).

Fuer den Chat unten links: dort pingen Mitspieler "Urgot Blitz", wenn Urgot
Flash benutzt hat. Nur lesen, was auf dem Bildschirm steht.
"""
from __future__ import annotations

import asyncio

import numpy as np


class Leser:
    def __init__(self, sprache: str = "de-DE"):
        from winrt.windows.globalization import Language
        from winrt.windows.media.ocr import OcrEngine
        self._motor = OcrEngine.try_create_from_language(Language(sprache))
        if self._motor is None:
            raise RuntimeError(f"Windows-Texterkennung fuer {sprache} nicht installiert")

    def zeilen(self, bild_bgr: np.ndarray, vergroessern: float = 1.0) -> list[str]:
        """Liest die Textzeilen eines BGR-Bildes, von oben nach unten."""
        import cv2
        from winrt.windows.graphics.imaging import BitmapPixelFormat, SoftwareBitmap
        from winrt.windows.storage.streams import DataWriter
        if vergroessern != 1.0:
            bild_bgr = cv2.resize(bild_bgr, None, fx=vergroessern, fy=vergroessern, interpolation=cv2.INTER_CUBIC)
        bgra = cv2.cvtColor(bild_bgr, cv2.COLOR_BGR2BGRA)
        h, w = bgra.shape[:2]
        schreiber = DataWriter()
        schreiber.write_bytes(bgra.tobytes())
        bitmap = SoftwareBitmap.create_copy_from_buffer(schreiber.detach_buffer(), BitmapPixelFormat.BGRA8, w, h)
        ergebnis = asyncio.run(self._lies(bitmap))
        return [z.text for z in ergebnis.lines]

    async def _lies(self, bitmap):
        return await self._motor.recognize_async(bitmap)
