"""Spielerprofil ueber alle Partien: was ein Coach von Partie zu Partie im Kopf behaelt.

Diamond+ erreicht man nicht in einer Partie, sondern indem man DIESELBEN Fehler
abstellt. Ein Coach, der jede Partie vergisst, entdeckt jedes Mal dieselben Fehler
neu und weiss nicht, ob der letzte Rat gewirkt hat. Deshalb:
  - je Partie harte Kennzahlen aus der Aufnahme (CS bei 10:00, Tode vor 14:00,
    gehortetes Gold, ...) - gerechnet, nicht geschaetzt, zwischengespeichert.
(Der Fokus aus dem Review und das Profil fuer Claude sind mit dem Review entfernt, Auftrag 028.)
Bot-Partien und Abbrueche (< 5 min) zaehlen fuer die Durchschnitte nicht mit.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from . import aufzeichnung, zustand
from .ansicht import uhr

CACHE = "profil.json"
KURZ = 300          # kuerzer: Abbruch/Test, kein echtes Spiel
FASSUNG = 2        # hochzaehlen, wenn sich die Kennzahlen aendern -> Cache wird neu gerechnet


@dataclass
class Kennzahlen:
    stamm: str
    champion: str
    rolle: str
    gegner: str | None
    ergebnis: str            # Win / Lose / abgebrochen
    dauer: float
    bots: bool               # Gegner sind Bots
    kda: str
    cs_min: float
    cs_10: int | None
    cs_10_gegner: int | None
    tode_vor_14: int
    horten: int              # wie oft >= 1500 Gold >= 60 s lebendig herumgetragen
    horten_max: int          # hoechster dabei getragener Betrag
    ward_min: float
    champion_id: str = ""    # fuer das Bild in der Oberflaeche

    @property
    def zaehlt(self) -> bool:
        return not self.bots and self.dauer >= KURZ

    def zeile(self) -> str:
        datum = f"{self.stamm[8:10]}.{self.stamm[5:7]}. {self.stamm[11:13]}:{self.stamm[13:15]}"
        ergebnis = {"Win": "Sieg", "Lose": "Niederlage"}.get(self.ergebnis, self.ergebnis)
        teile = [f"{datum} {self.champion} gegen {self.gegner or '?'}", ergebnis + (" (Bots)" if self.bots else ""),
                 uhr(self.dauer), f"KDA {self.kda}", f"CS/min {self.cs_min:.1f}"]
        if self.cs_10 is not None:
            teile.append(f"CS bei 10:00 {self.cs_10}" + (f" (Gegner {self.cs_10_gegner})" if self.cs_10_gegner is not None else ""))
        teile.append(f"Tode vor 14:00: {self.tode_vor_14}")
        if self.horten:
            teile.append(f"Gold gehortet: {self.horten}x, bis {self.horten_max}")
        teile.append(f"Wardscore/min {self.ward_min:.2f}")
        return ", ".join(teile)


def rechne(aufnahme: Path) -> Kennzahlen | None:
    """Kennzahlen einer Aufnahme (ca. 1 s fuer 35 Minuten)."""
    bei_10 = ende = None
    horten, horten_max, seit, hoch = 0, 0, None, 0.0
    for d in aufzeichnung.lies(aufnahme):
        p = zustand.partie(d)
        if not p.ich:
            continue
        ende = p
        if bei_10 is None and p.zeit >= 600:
            bei_10 = p
        if p.gold is not None and p.gold >= 1500 and not p.ich.tot:
            seit, hoch = seit or p.zeit, max(hoch, p.gold)
        else:
            if seit and p.zeit - seit >= 60:
                horten, horten_max = horten + 1, max(horten_max, int(hoch))
            seit, hoch = None, 0.0
    if not ende:
        return None
    ich, g = ende.ich, ende.gegenueber()
    g10 = bei_10.gegenueber() if bei_10 else None
    spielende = next((e for e in ende.ereignisse if e.art == "GameEnd"), None)
    tode = sum(1 for e in ende.ereignisse if e.art == "ChampionKill" and e.opfer is ich and e.zeit < 840)
    minuten = max(ende.zeit / 60, 1)
    return Kennzahlen(
        stamm=aufnahme.name.removesuffix(".jsonl.gz"), champion=ich.champion, rolle=ich.rolle,
        gegner=g.champion if g else None,
        ergebnis=spielende.daten.get("Result", "?") if spielende else "abgebrochen", dauer=ende.zeit,
        bots=any(s.bot for s in ende.gegner()), kda=f"{ich.kills}/{ich.tode}/{ich.assists}",
        cs_min=round(ich.cs / minuten, 2), cs_10=bei_10.ich.cs if bei_10 else None,
        cs_10_gegner=g10.cs if g10 else None, tode_vor_14=tode, horten=horten, horten_max=horten_max,
        ward_min=round(ich.ward_score / minuten, 2), champion_id=ich.champion_id)


def partien(ordner: Path | None = None, vor: str | None = None) -> list[Kennzahlen]:
    """Alle Partien im Aufnahme-Ordner, neueste zuerst. `vor`: nur die vor dieser Aufnahme
    (Stamm) - fuer die laufende Partie, deren Aufnahme noch waechst, und fuer das Review
    einer alten Partie, das keine spaeteren kennen darf."""
    ordner = Path(ordner or aufzeichnung.ORDNER)
    cache_datei = ordner / CACHE
    try:
        cache = json.loads(cache_datei.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    if cache.get("_fassung") != FASSUNG:
        cache = {"_fassung": FASSUNG}
    aus, geaendert = [], False
    for datei in sorted(aufzeichnung.alle(ordner), reverse=True):
        stamm = datei.name.removesuffix(".jsonl.gz")
        if vor and stamm >= vor:
            continue
        groesse = datei.stat().st_size
        eintrag = cache.get(stamm)
        if not eintrag or eintrag.get("_groesse") != groesse:
            try:
                k = rechne(datei)
            except (OSError, EOFError, ValueError):
                continue    # Aufnahme kaputt oder wird gerade geschrieben
            eintrag = {**asdict(k), "_groesse": groesse} if k else {"_groesse": groesse, "leer": True}
            cache[stamm], geaendert = eintrag, True
        if not eintrag.get("leer"):
            aus.append(Kennzahlen(**{f: v for f, v in eintrag.items() if not f.startswith("_")}))
    if geaendert:
        try:
            cache_datei.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass
    return aus
