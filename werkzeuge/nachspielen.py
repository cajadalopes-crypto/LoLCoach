"""Gemeinsame Grundlage der Messwerkzeuge (Buch 0, Kapitel 12): eine Aufnahme durch dasselbe Regelwerk und denselben
Sprechplan spielen wie live (stumm), dazu je Takt das Noetigste fuer Kehrtwenden, Luecken und die Gefahr-Eichung.

Benutzt von werkzeuge/szenarien.py, werkzeuge/kennzahlen.py und werkzeuge/szenario_aus_notizen.py."""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import aufzeichnung, bewertung, lage, minimap, regeln, sprechplan, stimme, zustand  # noqa: E402

AUFNAHMEN = aufzeichnung.ORDNER
LUECKE_AB = 5.0        # Sekunden ohne Schnappschuss (Wanduhr) = Datenluecke (Kapitel 12.3)

# Kehrtwende (Kapitel 9.4 Punkt 5) im alten System, nur am Text
ZURUECK = (regeln.RUECKZUG, regeln.BACK)
VOR = re.compile(r"Geh rein|nimm den Kampf an|Halte deine Stellung|Bleib an deiner Welle|Trade|Spiel auf|Geh auf|"
                 r"Drück|Nehmt", re.I)
OBJ_EVENTS = ("DragonKill", "BaronKill", "HeraldKill", "HordeKill", "TurretKilled", "InhibKilled")


def uhr(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


def sekunden(text: str) -> float:
    """"5:17" -> 317.0"""
    m, s = text.split(":")
    return int(m) * 60 + float(s)


def pfad_zu(name: str) -> Path:
    p = Path(name)
    return p if p.exists() else AUFNAHMEN / f"{name.removesuffix('.jsonl.gz')}.jsonl.gz"


@dataclass
class Takt:
    zeit: float
    wand: float
    leben: float | None
    sichtbar: frozenset          # sichtbare Gegner (Champion)
    kills: int                   # ChampionKill bis hier
    objectives: int              # gefallene Objectives/Strukturen bis hier


@dataclass
class Lauf:
    pfad: Path
    gesagt: list = field(default_factory=list)          # regeln.Ansage, je mit ._b (Bewertung des Takts)
    takte: list[Takt] = field(default_factory=list)
    halte: dict = field(default_factory=dict)           # Sollzeit -> (Partie, Bewertung, Lage in Worten)
    proben: list = field(default_factory=list)          # je ~1 s: (zeit, pos, [(name, ankunft, sichtbar, seit, pos, tot)])
    luecken: list = field(default_factory=list)         # (von Spielzeit, bis Spielzeit, Sekunden Wanduhr)
    sekunden_mit_daten: float = 0.0
    champions: set = field(default_factory=set)


def durchspielen(pfad: Path, halte_bei=(), proben: bool = False, rueckruf=None) -> Lauf:
    """Die Aufnahme wie live, nur stumm. `halte_bei`: Spielzeiten, zu denen Partie und Bewertung festgehalten
    werden (der erste Takt ab dieser Zeit). `proben`: je Sekunde Gegner-Ankunft und Positionen (Gefahr-Eichung).
    `rueckruf(soll, p, b, lb, wand)`: an jeder Haltezeit, solange das Lagebild noch diesen Stand hat (Fragen)."""
    lauf = Lauf(pfad)
    sicht = lage.sicht_fuer(pfad)
    werk, plan = regeln.Regelwerk(), sprechplan.Sprechplan(stimme.Stumm())
    lb = lage.Lagebild() if sicht else None
    offen = sorted(halte_bei)
    vorher = None
    letzte_probe = -1e9
    for w, d in aufzeichnung.lies_mit_zeit(pfad):
        p = zustand.partie(d)
        if sicht and p.ich:
            for wb, s in sicht.zwischen(w, lage.champions(p)):
                lb.neu(p.zeit - (w - wb), s, p)
            lb.ereignisse(lambda wb: p.zeit - (w - wb), sicht.ereignisse(), p)
        neu = werk.pruefe(p, lb)
        for a in neu:
            a._b = werk.b
        plan.neu(neu)
        plan.takt(p.zeit)
        lauf.champions |= {s.champion for s in p.spieler}
        b = werk.b
        if vorher is not None:
            dw = w - vorher[0]
            if dw > LUECKE_AB:
                lauf.luecken.append((vorher[1], p.zeit, dw))
            else:
                lauf.sekunden_mit_daten += max(0.0, dw)
        vorher = (w, p.zeit)
        lauf.takte.append(Takt(p.zeit, w, b.leben if b else None,
                               frozenset(g.champion for g in b.gegner if g.sichtbar) if b else frozenset(),
                               len(p.kills_von("ChampionKill")),
                               sum(len(p.kills_von(e)) for e in OBJ_EVENTS)))
        while offen and p.zeit >= offen[0]:
            soll = offen.pop(0)
            lauf.halte[soll] = (p, b, lage_kurz(p, b, lb))
            if rueckruf is not None:
                rueckruf(soll, p, b, lb, w)
        if proben and b is not None and b.pos is not None and p.zeit - letzte_probe >= 1.0:
            letzte_probe = p.zeit
            lauf.proben.append((p.zeit, b.pos, [(g.champion, g.ankunft, g.sichtbar, g.seit, g.pos, g.s.tot)
                                                for g in b.gegner]))
    lauf.gesagt = plan.gesagt
    return lauf


def gesprochen_um(a) -> float:
    return a.gesprochen if a.gesprochen is not None else a.zeit


def richtung(text: str) -> str | None:
    if any(m.search(text) for m in ZURUECK):
        return "zurueck"
    if VOR.search(text):
        return "vor"
    return None


def neues_ereignis(lauf: Lauf, t1: float, t2: float) -> bool:
    """Kapitel 9.4 Punkt 5: neuer Gegner sichtbar, Kill oder Tod, dein Leben faellt um > 15 %, Objective gefallen."""
    im = [t for t in lauf.takte if t1 <= t.zeit <= t2]
    if len(im) < 2:
        return False
    a = im[0]
    gesehen = set(a.sichtbar)
    for t in im[1:]:
        if t.sichtbar - gesehen:
            return True
        if t.kills > a.kills or t.objectives > a.objectives:
            return True
        if a.leben is not None and t.leben is not None and a.leben - t.leben > 0.15:
            return True
    return False


def kehrtwenden(lauf: Lauf, von: float = 0.0, bis: float = 1e9) -> list[tuple]:
    """(Zeit 1, Satz 1, Zeit 2, Satz 2) - vor <-> zurueck in <= 30 s ohne neues Ereignis (altes System, Text)."""
    saetze = [(gesprochen_um(a), a.text, r) for a in lauf.gesagt if (r := richtung(a.text))]
    aus = []
    for (t1, s1, r1), (t2, s2, r2) in zip(saetze, saetze[1:]):
        if r1 != r2 and t2 - t1 <= 30 and von <= t2 <= bis and not neues_ereignis(lauf, t1, t2):
            aus.append((t1, s1, t2, s2))
    return aus


def lage_kurz(p, b, lb) -> str:
    """Die Lage eines Takts in wenigen Zeilen (fuer Menschen): Ort, Leben, Gold, Flash, Welle, Gegner mit Ort und
    Zeit, Tote, Mitspieler, Objectives."""
    if b is None:
        return f"{uhr(p.zeit)}: keine Bewertung (Minimap fehlt?)"
    z = [f"{p.ich.champion} L{p.ich.level}, {int(b.leben * 100) if b.leben is not None else '?'} % Leben, "
         f"{b.gold} Gold, {b.ort or 'Ort ?'}"
         + (", Flash weg (noch %d s)" % b.flash if b.flash else "") + (", auf deiner Lane" if b.tiefe is not None else "")]
    if b.welle:
        z.append(f"Welle {b.welle[0]}:{b.welle[1]}" + (f", {b.welle[3]} schiebt" if b.welle[3] else ""))
    geg = []
    for g in b.gegner:
        if g.s.tot:
            geg.append(f"{g.champion} tot (noch {int(g.s.respawn)} s)")
        elif g.seit is None:
            geg.append(f"{g.champion} nie gesehen")
        else:
            geg.append(f"{g.champion} {'sichtbar' if g.sichtbar else f'vor {int(g.seit)} s'} {g.ort}"
                       + (f" ({int(g.abstand)})" if g.abstand is not None else ""))
    z.append("Gegner: " + "; ".join(geg))
    if b.mitspieler:
        z.append("Mitspieler: " + "; ".join(f"{s.champion} {ort}" for s, _, _, ort in b.mitspieler))
    obj = []
    for schl in ("drache", "baron", "herold", "larven"):
        try:
            t = p.naechster_spawn(schl)
        except Exception:
            t = None
        if t is not None:
            weg = bewertung.abstand(b.pos, bewertung.einheiten(*bewertung.GRUBEN[schl])) * 1.15 / b.mein_tempo \
                if b.pos else None
            obj.append(f"{schl} {'lebt' if t <= p.zeit else f'in {int(t - p.zeit)} s'}"
                       + (f", {int(weg)} s von dir" if weg is not None else ""))
    if obj:
        z.append("Objectives: " + "; ".join(obj))
    return "\n".join(z)


def ort_von(lb, sp) -> str:
    g = lb.gesehen(sp) if lb is not None else None
    return minimap.ort(g[1], g[2]) if g else "?"
