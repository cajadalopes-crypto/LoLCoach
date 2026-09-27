"""Modus UNTERWEGS (Buch 5, Kapitel 6): im Fluss, im Jungle oder Mid ohne Gruppe - das beste Ziel der Karte
(Kapitel 2): ein Turm, eine Seitenwelle, die Gruppe, ein Back. Gesagt nur, wenn der Plan neu ist und du nicht schon
dorthin laeufst, oder einmal, wenn du > 20 s nicht in seine Richtung gehst (kern/__init__)."""
from __future__ import annotations

from dataclasses import replace

from ..handlung import Handlung
from . import karte, lane as lane_modus
from .gruppe import _back_ohne_lane


def kandidaten(m, cfg: dict) -> list[Handlung]:
    aus = [karte.halten("UNTERWEGS")]
    aus += karte.turm_handlungen(m, cfg, "UNTERWEGS", "DRUECKEN", split=False)
    for lane, w in m.seitenwellen.items():
        if (h := karte.seitenwelle(m, cfg, "UNTERWEGS", lane, w)) is not None:
            aus.append(h)
    aus += karte.zur_gruppe(m, cfg, "UNTERWEGS")
    bald = m.teamkampf is not None or any(o.lebt or o.spawn_in <= 60 for o in m.objectives)
    if not bald:
        if m.lane_hier:
            w = m.wellen.get(m.lane_hier)
            aus += lane_modus.kandidaten(replace(m, welle=w), cfg, lane=m.lane_hier, modus="UNTERWEGS",
                                         arten={"BACK_JETZT", "WELLE_REIN_UND_BACK"})
        else:
            aus += _back_ohne_lane(m, cfg, "UNTERWEGS")
    return karte.umwandeln_zuerst(m, cfg, aus)
