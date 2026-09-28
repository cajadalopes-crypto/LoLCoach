"""Modus VERTEIDIGEN (Buch 5, Kapitel 7): eine tatsaechliche Bedrohung an einer eigenen Struktur, du bist nah.

WELLE_KLAEREN: gegnerische Welle (auch Supervasallen) an eurem Turm/Inhibitor, du <= 15 s entfernt, hoechstens ein
Gegner dort. HALTEN_UNTER_TURM: >= 2 Gegner belagern, ihr seid dort weniger - hinter dem Turm bleiben, nur klaeren
(zaehlt als Schutz: gilt auch, wenn das Gefahr-Modell anschlaegt). TAUSCHEN: die Verteidigung ist aussichtslos
(kraft_gegen < 0,6), und ein gleichwertiges Ziel ist in <= 20 s erreichbar."""
from __future__ import annotations

from ... import bewertung
from ...bewertung import TUERME, abstand
from ..handlung import Handlung, Ziel
from . import karte

STUFE_WORT = {"aussen": "am äußeren Turm", "innen": "am inneren Turm", "Inhib": "am Inhibitor-Turm"}


def _eigene_tuerme(m) -> list[tuple[str, str, tuple[float, float]]]:
    """(Lane, Stufe, Position) deiner stehenden Tuerme."""
    mein = m.p.mein_team if m.p is not None else "ORDER"
    return [(k[1], k[2], v) for k, v in bewertung.stehende_tuerme(m.p).items() if k[0] == mein] if m.p is not None else []


def _zahl(n: int) -> str:
    return {1: "allein", 2: "zu zweit", 3: "zu dritt", 4: "zu viert", 5: "zu fünft"}.get(n, f"zu {n}")


def kandidaten(m, cfg: dict) -> list[Handlung]:
    cm, cmo = cfg["mitte"], cfg["modus"]
    b = m.b
    aus = [karte.halten("VERTEIDIGEN")]
    sichtbar = [g for g in b.gegner if g.sichtbar and not g.s.tot and g.pos is not None]
    tuerme = _eigene_tuerme(m)
    for lane, w in m.wellen.items():
        if w is None or w.zustand not in ("GECRASHT_BEI_DIR", "GROSS_ZU_DIR", "ZU_DIR") or not (w.ihre or 0):
            continue
        # der vorderste stehende eigene Turm dieser Lane
        vorn = next((t for st in ("aussen", "innen", "Inhib") for t in tuerme if t[0] == lane and t[1] == st), None)
        if vorn is None:
            continue
        weg = m.weg(vorn[2])
        if weg is None or (weg > cmo["verteidigen_weg_s"] and getattr(m, "belagerung", None) is None):
            continue
        dort = [g for g in sichtbar if abstand(g.pos, vorn[2]) <= cmo["verteidigen_radius"]]
        wir = 1 + m.team_nah(vorn[2], cmo["verteidigen_radius"])
        wo = STUFE_WORT[vorn[1]]
        turmwert = karte.turm_gewinn(karte.TurmZiel("", lane, vorn[1], vorn[2], "", weg, [], 0), m, cfg)
        supervasallen = lane in [l for l, _ in bewertung.eigene_inhibs_weg(m.p)]
        if len(dort) <= 1 and not supervasallen and (w.ihre or 0) < cfg["schranken"]["welle_min"]:
            continue        # Pruefung c, R7: kleine Wellen sind keine Ansage (173159 33:56 "1 Vasallen")
        if len(dort) <= 1:
            grund = "keiner von ihnen dort" if not dort else f"nur {dort[0].champion} dort"
            was = "Supervasallen" if supervasallen else f"{w.ihre} Vasallen"
            h = Handlung("WELLE_KLAEREN", Ziel("lane", f"die {lane}-Welle", vorn[2], weg), "VERTEIDIGEN", weg + 10,
                         gewinn=turmwert, gefahr_t=weg + 10, grund=grund,
                         satz=f"Klär die {lane}-Welle {wo}: {was}, {grund}.")
            h.daten["ziel_pos"] = vorn[2]
            aus.append(h)
        elif len(dort) >= 2 and wir < len(dort):
            h = Handlung("HALTEN_UNTER_TURM", Ziel("turm", f"deinem {lane}-Turm", vorn[2], weg), "VERTEIDIGEN", 10.0,
                         gewinn=0.5 * turmwert, grund=f"{_zahl(wir)} gegen {len(dort)}",
                         satz=f"Bleib hinter dem Turm, nicht rein: {_zahl(wir)} gegen {len(dort)}. Klär nur, "
                              f"was kommt.")
            h.daten.update(am_turm=True, schutz=True)
            aus.append(h)
            if b.kraft_gegen(dort) < 0.6:
                aus += _tauschen(m, cfg, lane)
    bel = getattr(m, "belagerung", None)
    if bel is not None and not any(h.art != "HALTEN" for h in aus):
        # Auftrag 007, A 4 (Buch 5, 7, Nachtrag): die Belagerung holt dich auch aus der Ferne - der Weg zaehlt als Kosten
        name, pos, grund = bel
        weg = m.weg(pos) or 0.0
        h = Handlung("ZUR_GRUPPE", Ziel("turm", name, pos, weg), "VERTEIDIGEN", weg + 10.0,
                     gewinn=cmo["belagerung_gewinn"], grund=grund, satz=f"Zurück, verteidige {name}: {grund}.")
        h.daten["ziel_pos"] = pos
        aus.append(h)
    return aus


def _tauschen(m, cfg: dict, lane: str) -> list[Handlung]:
    """TAUSCHEN: die Seite ist verloren - ein Turm woanders in <= 20 s, an dem keiner von ihnen ist."""
    aus = []
    for z in karte.turm_ziele(m):
        if z.lane == lane or z.weg > 20 or karte.rechtzeitig(z, z.weg + karte.turm_dauer(z, cfg["mitte"])):
            continue
        name = z.name[4:] if z.name.startswith("den ") else z.name
        h = Handlung("TAUSCHEN", Ziel("turm", z.name, z.pos, z.weg), "VERTEIDIGEN",
                     z.weg + karte.turm_dauer(z, cfg["mitte"]), gewinn=karte.turm_gewinn(z, m, cfg),
                     grund="dort ist keiner",
                     satz=f"Die {lane}-Seite ist verloren - drück den {name}, dort ist keiner.")
        h.daten["ziel_pos"] = z.pos
        aus.append(h)
    return aus


__all__ = ["kandidaten", "TUERME"]
