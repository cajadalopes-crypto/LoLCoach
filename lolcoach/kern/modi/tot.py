"""Modus TOT (Buch 0, 6.3; Buch 3, 3): 8 s vor dem Respawn einmal Kauf und Ziel. Den Todesrueckblick (einmal je
Tod, ab 14 s Todeszeit) liefert die bestehende Todesanalyse (regeln._tod) - der Kern laesst sie in TOT sprechen."""
from __future__ import annotations

from .basis import kaufen, wohin


def kandidaten(m, cfg: dict, merker: dict | None = None, lage=None) -> list[Handlung]:
    """Vor dem Respawn einmal Kauf und Ziel (Buch 0, 6.3; Buch 3, 3) - seit Auftrag 017, 1.4 (Buch 13, 5) 12 s vorher
    ("Du lebst in 12 s: Axiombogen kaufen, dann zu Yorick nach Mid"), immer als Kette. Davor: nichts (der
    Todesrueckblick kommt aus der bestehenden Todesanalyse)."""
    if not (0 < m.respawn <= cfg.get("recall", {}).get("respawn_kette_s", 12.0)):
        return []
    z = wohin(m, cfg, "TOT", merker, lage)       # dasselbe Ziel gilt danach in der Basis (C4)
    k = kaufen(m, cfg, "TOT", z)
    h = k or z
    if not h.satz:
        return []            # Pruefung c, R6: kein sicheres Ziel und nichts zu kaufen - kein Satz
    if k is None and z.daten.get("kurz"):
        h.satz = f"Nichts zu kaufen, dann {z.daten['kurz']}: {z.grund}." if z.grund else \
            f"Nichts zu kaufen, dann {z.daten['kurz']}."
    h.satz = f"Du lebst in {int(round(m.respawn))} Sekunden: " + h.satz[0].lower() + h.satz[1:]
    from . import kuerze
    h.satz = kuerze(h.satz, cfg["sprechen"]["max_woerter"] + 6)     # Auftrag 002, S2.3; 017: die Kette hat Platz
    return [h]
