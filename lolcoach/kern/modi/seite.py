"""Modus SEITE (Buch 5, Kapitel 3): auf einer Seitenlane nach der Lane-Phase - bleiben und druecken oder gehen?

Split-Regel (3.1): druecken nur, wenn kein Objective dich ruft (ohne TP: nichts in <= 60 s; mit TP bleibst du bis
zum Kampf), du die Antwort schlaegst (kraft_gegen >= 1,2) und - hinter ihrem aeusseren Turm - fast alle Gegner
bekannt oder woanders sind. Dazu: Seitenwelle holen, Platten, Welle rein und rotieren, zur Gruppe / TP in einen
Kampf, Back mit der Welle DIESER Lane (Buch 3)."""
from __future__ import annotations

from dataclasses import replace

from ..handlung import Handlung
from . import karte, lane as lane_modus


def kandidaten(m, cfg: dict) -> list[Handlung]:
    lane = m.lane_hier or m.meine_lane or "Top"
    w = m.wellen.get(lane) if m.wellen else m.welle
    sicht = replace(m, welle=w)            # die Lane-Handlungen rechnen mit der Welle dieser Lane
    arten = {"FARMEN", "BACK_JETZT", "WELLE_REIN_UND_BACK"}
    if lane == m.meine_lane:
        arten.add("PLATTEN")               # Platten gibt es auch nach 14:00 (Buch 1, 3.6) - gegen deinen Lane-Gegner
    aus = lane_modus.kandidaten(sicht, cfg, lane=lane, modus="SEITE", arten=arten)
    umwandeln = karte.umwandeln(m, cfg) is not None
    if umwandeln:
        # nach einem gewonnenen Kampf gilt die Split-Regel nicht: jede Struktur im Fenster, vor dem Back (Kapitel 8;
        # 102112, 36:03: vier tot, du auf der Bot-Lane - der Coach sagte "Bot-Welle rein, dann back")
        aus += karte.turm_handlungen(m, cfg, "SEITE", "DRUECKEN", split=False)
    elif not karte.objective_ruft(m, cfg, lane):
        aus += karte.turm_handlungen(m, cfg, "SEITE", "DRUECKEN", split=True)
    z = w.zustand if w is not None else "UNBEKANNT"
    if w is not None and (z in ("ZU_DIR", "GROSS_ZU_DIR") or lane in m.seitenwellen):
        if (h := karte.seitenwelle(m, cfg, "SEITE", lane, w)) is not None:
            aus.append(h)
    if (h := karte.welle_und_raus(m, cfg, "SEITE", lane, w)) is not None:
        aus.append(h)
        if karte.objective_ruft(m, cfg, lane):
            # Split-Regel 1: ruft dich ein Objective und du hast kein TP, ist Seite halten kein Kandidat mehr
            aus = [x for x in aus if x.art not in ("FARMEN", "SEITENWELLE", "DRUECKEN", "PLATTEN")]
    aus += karte.zur_gruppe(m, cfg, "SEITE")
    return karte.umwandeln_zuerst(m, cfg, aus)
