"""Modus TOT (Buch 0, 6.3; Buch 3, 3): 8 s vor dem Respawn einmal Kauf und Ziel. Den Todesrueckblick (einmal je
Tod, ab 14 s Todeszeit) liefert die bestehende Todesanalyse (regeln._tod) - der Kern laesst sie in TOT sprechen."""
from __future__ import annotations

from .basis import kaufen, wohin


def kandidaten(m, cfg: dict, merker: dict | None = None, lage=None) -> list[Handlung]:
    """8 s vor dem Respawn einmal Kauf und Ziel (Buch 0, 6.3; Buch 3, 3). Davor: nichts (der Todesrueckblick kommt
    aus der bestehenden Todesanalyse)."""
    if not (0 < m.respawn <= 8.0):
        return []
    z = wohin(m, cfg, "TOT", merker, lage)       # dasselbe Ziel gilt danach in der Basis (C4)
    k = kaufen(m, cfg, "TOT", z)
    h = k or z
    h.satz = f"Noch {int(round(m.respawn))} Sekunden: " + h.satz[0].lower() + h.satz[1:]
    return [h]
