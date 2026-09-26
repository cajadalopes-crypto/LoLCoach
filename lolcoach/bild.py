"""Bildschirm: Aufnahme von aussen, wie ein Bildschirmteilen bei Discord.

Nur Bildschirmfotos des Spielfensters - kein Zugriff auf den Spielprozess.
Das Fenster wird ueber seinen Titel gefunden, damit es auf jedem Monitor
und in jeder Aufloesung stimmt.
"""
from __future__ import annotations

import ctypes

try:  # sonst liefert Windows bei 150 % Skalierung verkleinerte Koordinaten
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except (AttributeError, OSError):
    pass

import win32gui
from PIL import Image, ImageGrab

FENSTERTITEL = "League of Legends (TM) Client"

# Minimap sitzt unten rechts (FlipMiniMap=0). Bis sie vermessen ist, nehmen
# wir die Ecke grosszuegig: ein Quadrat mit diesem Anteil der Fensterhoehe.
ECKE_ANTEIL = 0.42


def spielfenster() -> tuple[int, int, int, int] | None:
    """(links, oben, rechts, unten) des Spielfensters in Bildschirmpixeln."""
    hwnd = win32gui.FindWindow(None, FENSTERTITEL)
    if not hwnd or win32gui.IsIconic(hwnd):
        return None
    l, o = win32gui.ClientToScreen(hwnd, (0, 0))
    _, _, b, h = win32gui.GetClientRect(hwnd)
    return (l, o, l + b, o + h) if b and h else None


def minimap_ecke() -> Image.Image | None:
    f = spielfenster()
    if not f:
        return None
    l, o, r, u = f
    seite = int((u - o) * ECKE_ANTEIL)
    return ImageGrab.grab(bbox=(r - seite, u - seite, r, u), all_screens=True)
