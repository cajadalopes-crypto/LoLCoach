"""Kampfrechner (Buch 14, Schritt B; Auftrag 020): wer gewinnt den Kampf an diesem Ort?

Eingabe: Verbuendete und Gegner an einem Ort (`Kaempfer`): Level, Items oder genaue Werte, Leben (bekannt oder voll),
Ult (bekannt oder bereit), Faehigkeitsraenge (bekannt oder aus dem Level geschaetzt).

Rechnung, bewusst einfach und zur vorsichtigen Seite:
  - Burst je Champion gegen jeden Gegner: je Faehigkeit ein Treffer (Spieldaten, `faehigkeiten.py` - eher zu wenig),
    R nur mit Ult, dazu normale Angriffe im Burst-Fenster; nach Ruestung/Magieresistenz und Durchdringung.
  - Ablauf in Schritten von 0,25 s: jeder greift das Ziel an, das er am schnellsten toetet; im Burst-Fenster
    (BURST_S) mit Burst-Tempo, danach nur mit Angriffen; wer tot ist, faellt aus. Hoechstens DAUER_S.
  - Staerke = mittleres Restleben wir - mittleres Restleben sie (-1 .. 1).

Urteil: klar_vorn / knapp / klar_hinten ueber die Schwelle aus `wissen/kampf_eichung.toml` (an Riot-Partien geeicht,
`werkzeuge/kampf_eichung_riot.py`). Dazu die zwei entscheidenden Zahlen und die Annahmen.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from . import ddragon
from .rechnung import wachstum

BURST_S = 3.0
DAUER_S = 8.0
SCHRITT_S = 0.25
KRIT_BONUS = 0.75                 # ein Krit macht 175 %
EICHUNG = Path(__file__).resolve().parent.parent / "wissen" / "kampf_eichung.toml"
SCHWELLE_VORGABE = 0.35


@dataclass
class Kaempfer:
    champion_id: str
    team: str                         # "wir" | "sie"
    level: int
    items: tuple[int, ...] = ()
    leben: float | None = None        # 0..1; None = unbekannt (dann voll)
    ult: bool | None = None           # None = unbekannt (dann bereit)
    raenge: dict | None = None        # {"Q": 5, ...}; None = aus dem Level geschaetzt
    werte: dict | None = None         # genaue Werte (Riot-Zeitleiste, Live-API); None = aus Level + Items
    name: str = ""
    ich: bool = False

    @property
    def wer(self) -> str:
        return self.name or self.champion_id

    @property
    def wessen(self) -> str:
        """Genitiv: "Garens", "Fizz'", "Kog'Maws"."""
        return self.wer + ("'" if self.wer[-1:].lower() in "sßxz" else "s")


@dataclass
class Urteil:
    urteil: str                       # klar_vorn | knapp | klar_hinten
    staerke: float                    # -1 .. 1
    zahlen: list[str]                 # die zwei entscheidenden Zahlen, als Satzteile
    annahmen: list[str]
    tote: list[tuple[float, str]] = field(default_factory=list)   # (Sekunde, Champion) in der Reihenfolge
    burst: dict = field(default_factory=dict)                      # Name -> Burst auf das erste Ziel

    def text(self) -> str:
        wort = {"klar_vorn": "klar vorn", "knapp": "knapp", "klar_hinten": "klar hinten"}[self.urteil]
        return f"{wort}: " + "; ".join(self.zahlen)


def werte_aus_items(champion_id: str, level: int, items) -> dict:
    """Grundwerte nach Level (Data Dragon) + Item-Werte. Ohne Runen und Stapel."""
    st = (ddragon.champions().get(champion_id) or {}).get("stats", {})
    it = ddragon.items()

    def summe(schl: str) -> float:
        return sum(float(it.get(int(i), {}).get("stats", {}).get(schl, 0.0)) for i in items)

    aus = {}
    for name, basis, je, item in (("ad", "attackdamage", "attackdamageperlevel", "FlatPhysicalDamageMod"),
                                  ("ruestung", "armor", "armorperlevel", "FlatArmorMod"),
                                  ("mr", "spellblock", "spellblockperlevel", "FlatSpellBlockMod"),
                                  ("leben_max", "hp", "hpperlevel", "FlatHPPoolMod")):
        b = wachstum(float(st.get(basis, 0.0)), float(st.get(je, 0.0)), level)
        aus.update({name: b + summe(item), name + "_basis": b, name + "_bonus": summe(item)})
    ap = summe("FlatMagicDamageMod")
    tempo = float(st.get("attackspeed", 0.65)) * (1 + (float(st.get("attackspeedperlevel", 2.0)) / 100) * (level - 1)
                                                  * (0.7025 + 0.0175 * (level - 1)) + summe("PercentAttackSpeedMod"))
    aus.update(ap=ap, ap_basis=0.0, ap_bonus=ap, tempo_angriff=min(2.5, tempo), krit=min(1.0, summe("FlatCritChanceMod")),
               durchdringung=0.0, durchdringung_prozent=0.0, magie_durchdringung=0.0, magie_prozent=0.0)
    return aus


def werte_aus_riot(champion_id: str, level: int, cs: dict) -> dict:
    """Werte aus `championStats` eines Minuten-Frames der Match-V5-Zeitleiste."""
    st = (ddragon.champions().get(champion_id) or {}).get("stats", {})
    aus = {}
    for name, api, basis, je in (("ad", "attackDamage", "attackdamage", "attackdamageperlevel"),
                                 ("ruestung", "armor", "armor", "armorperlevel"),
                                 ("mr", "magicResist", "spellblock", "spellblockperlevel"),
                                 ("leben_max", "healthMax", "hp", "hpperlevel")):
        gesamt = float(cs.get(api) or 0.0)
        b = wachstum(float(st.get(basis, 0.0)), float(st.get(je, 0.0)), level)
        aus.update({name: gesamt, name + "_basis": b, name + "_bonus": max(0.0, gesamt - b)})
    ap = float(cs.get("abilityPower") or 0.0)
    aus.update(ap=ap, ap_basis=0.0, ap_bonus=ap, tempo_angriff=min(2.5, float(cs.get("attackSpeed") or 65) / 100),
               krit=0.0, durchdringung=float(cs.get("armorPen") or 0.0),
               durchdringung_prozent=float(cs.get("armorPenPercent") or 0.0) / 100,
               magie_durchdringung=float(cs.get("magicPen") or 0.0),
               magie_prozent=float(cs.get("magicPenPercent") or 0.0) / 100)
    return aus


def _werte(k: Kaempfer) -> dict:
    return k.werte if k.werte is not None else werte_aus_items(k.champion_id, k.level, k.items)


def _raenge(k: Kaempfer) -> dict:
    if k.raenge:
        return k.raenge
    from .combo import raenge_geschaetzt
    return raenge_geschaetzt(k.champion_id, max(1, k.level))


def _teiler(angreifer: dict, ziel: dict) -> dict[str, float]:
    arm = max(0.0, ziel["ruestung"] * (1 - angreifer.get("durchdringung_prozent", 0.0)) - angreifer.get("durchdringung", 0.0))
    mag = max(0.0, ziel["mr"] * (1 - angreifer.get("magie_prozent", 0.0)) - angreifer.get("magie_durchdringung", 0.0))
    return {"physisch": 100 / (100 + arm), "magisch": 100 / (100 + mag), "wahr": 1.0}


def burst(a: Kaempfer, ziel: Kaempfer) -> tuple[float, float]:
    """(Burst im Fenster, Angriffe je Sekunde danach) von `a` auf `ziel`, nach Resistenzen."""
    from . import faehigkeiten
    wa, wz = _werte(a), _werte(ziel)
    t = _teiler(wa, wz)
    angriff = wa["ad"] * (1 + wa.get("krit", 0.0) * KRIT_BONUS) * t["physisch"]
    tempo = max(0.3, wa.get("tempo_angriff", 0.65))
    summe = angriff * max(1.0, tempo * BURST_S)
    if faehigkeiten.kann(a.champion_id):
        for slot, r in _raenge(a).items():
            if r <= 0 or (slot == "R" and a.ult is False):
                continue
            summe += sum(max(0.0, x) * t.get(art, 0.0)
                         for x, art in faehigkeiten.schaden(a.champion_id, slot, int(r), max(1, a.level), wa))
    return summe, angriff * tempo


def _leben(k: Kaempfer) -> float:
    return _werte(k)["leben_max"] * (k.leben if k.leben is not None else 1.0)


@lru_cache(maxsize=1)
def schwelle() -> float:
    try:
        return float(tomllib.loads(EICHUNG.read_text(encoding="utf-8"))["schwelle"])
    except (OSError, ValueError, KeyError):
        return SCHWELLE_VORGABE


def rechne(kaempfer: list[Kaempfer], schwelle_: float | None = None) -> Urteil | None:
    """Das Urteil fuer diesen Kampf; None, wenn eine Seite fehlt."""
    wir = [k for k in kaempfer if k.team == "wir"]
    sie = [k for k in kaempfer if k.team == "sie"]
    if not wir or not sie:
        return None
    alle = wir + sie
    feinde = {id(k): (sie if k.team == "wir" else wir) for k in alle}
    b = {(id(a), id(z)): burst(a, z) for a in alle for z in feinde[id(a)]}
    voll = {id(k): _leben(k) for k in alle}
    rest = dict(voll)
    tote, t = [], 0.0
    while t < DAUER_S and any(rest[id(k)] > 0 for k in wir) and any(rest[id(k)] > 0 for k in sie):
        schaden = {}
        for a in alle:
            if rest[id(a)] <= 0:
                continue
            ziele = [z for z in feinde[id(a)] if rest[id(z)] > 0]
            tempo = lambda z: (b[(id(a), id(z))][0] / BURST_S if t < BURST_S else b[(id(a), id(z))][1])
            z = min(ziele, key=lambda z: rest[id(z)] / max(1e-6, tempo(z)))
            schaden[id(z)] = schaden.get(id(z), 0.0) + tempo(z) * SCHRITT_S
        t += SCHRITT_S
        for k in alle:
            if rest[id(k)] > 0 and schaden.get(id(k), 0.0) >= rest[id(k)]:
                tote.append((round(t, 2), k.wer))
            rest[id(k)] = max(0.0, rest[id(k)] - schaden.get(id(k), 0.0))
    staerke = sum(rest[id(k)] / voll[id(k)] for k in wir) / len(wir) - sum(rest[id(k)] / voll[id(k)] for k in sie) / len(sie)
    s = schwelle() if schwelle_ is None else schwelle_
    urteil = "klar_vorn" if staerke >= s else "klar_hinten" if staerke <= -s else "knapp"
    # die zwei entscheidenden Zahlen: euer Burst auf ihr schwaechstes Ziel, ihrer auf dich (sonst ihr erstes Ziel)
    def fokus(seite, gegen):
        z = min(gegen, key=lambda z: voll[id(z)] / max(1e-6, sum(b[(id(a), id(z))][0] for a in seite)))
        return z, sum(b[(id(a), id(z))][0] for a in seite)
    z_sie, ihr_burst = fokus(wir, sie)
    ich = next((k for k in wir if k.ich), None)
    z_wir = ich if ich is not None else fokus(sie, wir)[0]
    ihr_auf = sum(b[(id(a), id(z_wir))][0] for a in sie)
    zahlen = [f"ihr {int(round(ihr_burst, -1))} Burst gegen {z_sie.wessen} {int(round(voll[id(z_sie)], -1))} Leben",
              f"ihr Burst {int(round(ihr_auf, -1))} gegen {'dein' if z_wir.ich else z_wir.wessen} "
              f"{int(round(voll[id(z_wir)], -1))}"]
    annahmen = ["je Fähigkeit ein Treffer, ohne Runen, Beschwörerzauber, Schilde und Heilung"]
    for k in alle:
        if k.leben is None:
            annahmen.append(f"Leben von {k.wer} unbekannt: voll")
        if k.ult is None and k.level >= 6:
            annahmen.append(f"Ult von {k.wer} unbekannt: bereit")
        if not k.raenge:
            annahmen.append(f"Ränge von {k.wer} aus dem Level geschätzt")
    from . import faehigkeiten
    annahmen += [f"{k.wer}: keine Fähigkeitsdaten, nur Angriffe" for k in alle if not faehigkeiten.kann(k.champion_id)]
    return Urteil(urteil, round(staerke, 3), zahlen, annahmen, tote,
                  {a.wer: round(b[(id(a), id(z_sie))][0]) for a in wir} | {a.wer: round(b[(id(a), id(z_wir))][0]) for a in sie})
