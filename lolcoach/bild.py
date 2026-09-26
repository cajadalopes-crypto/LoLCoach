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

FENSTERTITEL = "League of Legends (TM) Client"

def spielfenster() -> tuple[int, int, int, int] | None:
    """(links, oben, rechts, unten) des Spielfensters in Bildschirmpixeln."""
    hwnd = win32gui.FindWindow(None, FENSTERTITEL)
    if not hwnd or win32gui.IsIconic(hwnd):
        return None
    l, o = win32gui.ClientToScreen(hwnd, (0, 0))
    _, _, b, h = win32gui.GetClientRect(hwnd)
    return (l, o, l + b, o + h) if b and h else None
