"""Modus GRUPPE (Buch 5, Kapitel 4): mit >= 2 Mitspielern unterwegs.

MIT_GRUPPE: eine Struktur in Reichweite, ihr seid mehr, als rechtzeitig verteidigen kann. SEITENWELLE: eine Welle
laeuft auf euren Turm auf DEINER Seite (Top), keiner von euch dort, und bei der Gruppe steht in 30 s nichts an -
gegen das "ARAM-Mid". BACK_JETZT nur, wenn kein Objective und kein Kampf ansteht. Nach einem gewonnenen Kampf
erst umwandeln, das Gold wartet (Kapitel 8)."""
from __future__ import annotations

from dataclasses import replace

from ..handlung import Handlung
from . import karte, lane as lane_modus, objectives_meine_seite


def kandidaten(m, cfg: dict) -> list[Handlung]:
    c = cfg["mitte"]
    aus = [karte.halten("GRUPPE")]
    aus += karte.turm_handlungen(m, cfg, "GRUPPE", "MIT_GRUPPE", split=False)
    steht_an = m.teamkampf is not None or any(o.lebt or o.spawn_in <= c["seitenwelle_frei_s"] for o in m.objectives)
    meine = m.meine_lane or "Top"
    if not steht_an and meine in m.seitenwellen:
        if (h := karte.seitenwelle(m, cfg, "GRUPPE", meine, m.seitenwellen[meine])) is not None:
            aus.append(h)
    aus += karte.zur_gruppe(m, cfg, "GRUPPE")
    # Back (Buch 3) - in der Gruppe nur, wenn nichts ansteht; die Welle der Lane, auf der du stehst
    bald = m.teamkampf is not None or any(o.lebt or o.spawn_in <= 60 for o in m.objectives)
    if not bald and m.lane_hier:
        w = m.wellen.get(m.lane_hier)
        aus += lane_modus.kandidaten(replace(m, welle=w), cfg, lane=m.lane_hier, modus="GRUPPE",
                                     arten={"BACK_JETZT", "WELLE_REIN_UND_BACK"})
    elif not bald:
        aus += _back_ohne_lane(m, cfg, "GRUPPE")
    return karte.umwandeln_zuerst(m, cfg, aus)


def _back_ohne_lane(m, cfg: dict, modus: str) -> list[Handlung]:
    """Nicht auf einer Lane: keine Welle geht verloren - BACK_JETZT mit jedem Back-Grund (Buch 3, 1)."""
    from . import back_gewinn, back_grund_text, back_gruende, nie_back
    from ..handlung import Ziel
    gruende = back_gruende(m, cfg)
    if not gruende or nie_back(m, cfg) is not None:
        return []
    cr = cfg["recall"]
    text = back_grund_text(gruende)
    return [Handlung("BACK_JETZT", Ziel("basis", "Basis"), modus, cr["kanal_s"] + cr["einkauf_s"],
                     gewinn=back_gewinn(m, cfg, gruende), gefahr_t=cr["kanal_s"], grund=text,
                     satz=f"Back jetzt: {text}.", schritte=["back", "kaufen", "zurück"])]


__all__ = ["kandidaten", "objectives_meine_seite"]
