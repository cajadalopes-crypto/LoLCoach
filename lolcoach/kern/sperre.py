"""Modus-Sperre fuer die alten Regeln (Buch 0, Kapitel 14; gilt ab Schritt 2): jede Regel spricht nur in den
Modi, in denen ihre Frage zaehlt. INFO-Themen (Flash, Items, Level, CS - Kapitel 9.1) gehen aufs Dashboard und
werden nur gesprochen, wenn sie den Lane-Gegner oder den Jungler in LANE/SEITE betreffen.

`entscheide(regel, ansage, modus, b, kern_spricht)` -> "sprechen" | "info" | "stumm". Ohne Modus (keine Minimap) spricht
seit der Qualitaetsrunde 1 keine alte Regel (Pruefung E6; vorher galt dann keine Sperre); ohne Kern ruft das Regelwerk
die Sperre gar nicht. Ab Schritt 3 (`--kern neu`): in den Modi, in denen der Kern spricht (LANE, BASIS, TOT), sind die alten Regeln
stumm - ausser dem Todesrueckblick (regeln._tod = TODESRUECKBLICK, einmal je Tod ab 14 s Todeszeit, Kapitel 6.3) und
_afk (bis Schritt 8); INFO-Themen gehen dort nur noch aufs Dashboard (Kapitel 9.1)."""
from __future__ import annotations

ALLE = frozenset(("TOT", "KAMPF", "OBJECTIVE", "VERTEIDIGEN", "BASIS", "LANE", "SEITE", "GRUPPE", "UNTERWEGS"))


def ausser(*modi: str) -> frozenset:
    return ALLE - set(modi)


LANE_SEITE = frozenset(("LANE", "SEITE"))

# Regel -> Modi, in denen sie spricht (Kapitel 14, Spalte "Sperre")
# Buch 6, 5 (aendert Kapitel 14, ab Schritt 5): _grosse_objectives, _vorwarnung, _zahlen, _objective_start und _ward
# sind in ALLEN Modi stumm - sonst sagen sie in SEITE, GRUPPE oder UNTERWEGS weiter "Nehmt Baron ..."; der Kern
# spricht das Objective (kern/objective.py). Dasselbe gilt fuer den Objective-Plan des Entscheiders (PLAN obj_plan).
SPERRE = {
    "_grosse_objectives": frozenset(),
    "_vorwarnung": frozenset(),
    "_zahlen": frozenset(),
    "_jungler_tot": LANE_SEITE,
    "_lane_tot": frozenset(("LANE",)),
    "_level": frozenset(("LANE",)),
    "_items": LANE_SEITE,                        # nur Lane-Gegner nah (unten)
    "_gold": frozenset(("LANE", "SEITE", "UNTERWEGS")),
    "_cs": frozenset(),                          # stumm: Dashboard, Review
    "_tod": frozenset(("TOT",)),
    "_jungler_gesehen": LANE_SEITE,
    "_lane_fehlt": frozenset(("LANE",)),
    "_leben": frozenset(("LANE", "SEITE", "UNTERWEGS")),
    "_zauber": LANE_SEITE,                       # nur Lane-Gegner/Jungler (unten)
    "_anlauf": frozenset(("LANE", "SEITE", "UNTERWEGS", "GRUPPE", "OBJECTIVE")),
    "_ward": frozenset(),                        # Buch 6, 5: bis Buch 4 kein Ward-Satz
    "_recall_fenster": LANE_SEITE,
    "_tief_ohne_sicht": LANE_SEITE,
    "_kontrollauge": frozenset(("BASIS", "TOT")),
    "_objective_start": frozenset(),
    "_fenster": LANE_SEITE,                      # Lane-Gegner <= 3500: die Regel verlangt schon <= 1800
    "_wiedereinstieg": frozenset(("TOT",)),
    "_afk": frozenset(),                         # Auftrag 008, A3.2: ganz aus (101426 23:24, "Kayn ist AFK" war falsch)
}

# _plan (Entscheider): je Plan-Art - Lane-Plaene nur LANE/SEITE, "wohin" nur ausserhalb LANE
PLAN = {
    "gank_erwartet": LANE_SEITE, "gank_weg": LANE_SEITE, "muster": LANE_SEITE, "druck": LANE_SEITE,
    "freeze": LANE_SEITE, "back_warten": LANE_SEITE, "back_kanone": LANE_SEITE, "back_knapp": LANE_SEITE,
    "seite": LANE_SEITE, "seite_nicht": LANE_SEITE, "reset": LANE_SEITE, "hilfe_fern": LANE_SEITE,
    "back_plan": frozenset(("LANE", "SEITE", "UNTERWEGS", "GRUPPE")),          # wie _gold: nie in der Basis
    "obj_plan": frozenset(),                     # wie _vorwarnung (Buch 6, 5)
    "gruppe": frozenset(("SEITE", "UNTERWEGS", "GRUPPE")),
    "wohin": ausser("LANE", "TOT", "KAMPF"),
    "zurueck": ausser("TOT", "BASIS"),           # ZURUECK: alle Modi ausser TOT und BASIS (Kapitel 6.3)
    "ueberzahl": ausser("TOT", "BASIS"), "hilfe": ausser("TOT", "BASIS"),
}

# INFO (Kapitel 9.1): diese Schluessel gehen aufs Dashboard, gesprochen nur unter der Bedingung in `entscheide`
INFO = ("zauber:", "ohneflash:", "flashzurueck:", "level", "cs", "item:", "spike:", "tipp", "jungler6")


def _name(schluessel: str) -> str:
    teile = schluessel.split(":")
    return teile[1] if len(teile) > 1 else ""


TODESRUECKBLICK_AB = 14.0     # Kapitel 6.3: einmal je Tod, ab so viel Todeszeit


def entscheide(regel: str, a, modus: str | None, b, kern_spricht: bool = False) -> str:
    if modus is None:
        # Pruefung E6 (Qualitaetsrunde 1): ohne Modus spricht keine alte Regel - vorher sprachen sie dann ungesperrt
        # (140253, 0:00 im Brunnen: "Schieb die naechste Welle in den Turm und geh dann back"). TECHNIK und das
        # Briefing laufen nicht durch das Regelwerk.
        return "stumm"
    if kern_spricht:
        if a.schluessel.startswith(INFO):
            return "info"
        if regel == "_tod":
            respawn = b.ich.respawn if b is not None and b.ich is not None else 0.0
            return "sprechen" if modus == "TOT" and respawn >= TODESRUECKBLICK_AB else "stumm"
        if regel == "_afk":
            return "stumm"                       # Auftrag 008, A3.2: ganz aus
        return "stumm"
    s = a.schluessel
    if regel == "_plan":
        art = s.split(":", 1)[1] if ":" in s else s
        return "sprechen" if modus in PLAN.get(art, ALLE) else "stumm"
    if s.startswith(INFO):
        lane = b.lane.s.name if b is not None and b.lane is not None else None
        jungler = b.jungler.s.name if b is not None and b.jungler is not None else None
        if s.startswith(("zauber:", "ohneflash:", "flashzurueck:")):
            spricht = modus in LANE_SEITE and _name(s) in (lane, jungler)
        elif s.startswith("jungler6"):
            spricht = modus in LANE_SEITE
        elif s.startswith("level"):
            spricht = modus == "LANE"
        elif s.startswith(("item:", "spike:", "tipp")):
            spricht = modus in LANE_SEITE and b is not None and b.lane_nah and (
                not s.startswith("item:") or _name(s) == lane)
        else:                                    # cs
            spricht = False
        return "sprechen" if spricht else "info"
    if s.startswith("aufbruch"):
        # der Kauf-Satz beim Verlassen der Basis gehoert zu BASIS/KAUFEN, nicht zu den Lane-Infos von _items
        return "sprechen" if modus in ("BASIS", "LANE", "SEITE", "UNTERWEGS", "GRUPPE") else "stumm"
    return "sprechen" if modus in SPERRE.get(regel, ALLE) else "stumm"
