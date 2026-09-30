"""B10. Spielstand und Siegbedingung (V1-V5)."""
from __future__ import annotations

from ..kommando import Kommando
from ..lage import MakroLage
from . import entscheidung


@entscheidung("V1", "Siegbedingung ansagen und wechseln", "D", ("scoreboard", "uhr"), ("D:siegchance",))
def v1(lage: MakroLage):
    if lage.wir_skalieren is None or lage.zeit >= 1500:
        return None
    if lage.wir_skalieren:
        return Kommando("V1", "Nichts erzwingen vor Minute 25", "ihr skaliert besser")
    return Kommando("V1", "Jetzt spielen: Objectives und Kaempfe suchen", "sie skalieren besser, eure Zeit ist jetzt")


@entscheidung("V2", "Vorsprung umwandeln", "D", ("scoreboard", "ereignisse"), ("D:siegchance",))
def v2(lage: MakroLage):
    sc = lage.hirn.siegchance
    if sc is None or sc < 0.65:
        return None
    return Kommando("V2", "Objectives, keine Kaempfe ohne Grund", f"ihr steht bei {int(sc * 100)} % Siegchance")


@entscheidung("V3", "Rueckstand spielen", "D", ("scoreboard", "ereignisse"), ("D:siegchance",))
def v3(lage: MakroLage):
    sc = lage.hirn.siegchance
    if sc is None or sc > 0.35:
        return None
    return Kommando("V3", "Wellen halten, Sicht, auf ihren Fehler warten", f"ihr steht bei {int(sc * 100)} % Siegchance",
                    "keine 50:50-Kaempfe")


@entscheidung("V4", "Eigenes Spike-Fenster", "D", ("scoreboard", "eigene_items"), ("D:siegchance",))
def v4(lage: MakroLage):
    if not lage.spike_wir:
        return None
    return Kommando("V4", "In den naechsten 2 min ein Monster erzwingen", "euer Spike ist jetzt")


@entscheidung("V5", "Gegner-Spike abwarten", "D", ("scoreboard", "gegner_items"), ("D:siegchance",))
def v5(lage: MakroLage):
    if not lage.spike_gegner:
        return None
    return Kommando("V5", "Nicht kaempfen: Wellen und Sicht", "ihr Spike ist jetzt", klasse="gefahr", wert=2.0)
