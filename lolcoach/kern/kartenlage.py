"""Kartenlage (Buch 4, Kapitel 2; Auftrag 008): wo die Gegner sind und was daraus folgt.

Je Takt aus Minimap, API und Ereignissen: je Gegner die letzte Sichtung (Kartenseite, Alter), die vermutliche Seite,
MIA, Respawn, Flash und TP, Level und Item-Gold - und zusammengefasst: wie viele oben, in der Mitte, unten, unbekannt,
tot, dazu das Fenster je Seite (die Zeit, bis der erste Gegner dort sein kann; dieselbe Rechnung wie
karte.verteidiger, nur fuer die ganze Seite).

Carlos, 101426 26:45: "Ich weiss nie, wann wer wo ist, wann die Flashes sind ... ich habe gar keine Uebersicht." Daraus
das Lagebild (A4): auf Abruf ("Ueberblick?") und ab 14:00 ungefragt, immer mit einer Folgerung.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..bewertung import BRUNNEN, WEGFAKTOR, abstand, einheiten
from .sprache import kartenseite

SEITEN = ("oben", "Mitte", "unten")
_WORT = {"oben": "oben", "in der Mitte": "Mitte", "unten": "unten"}
# Kartenseite -> der Punkt, an dem ein Gegner "auf dieser Seite" ist: die Fluss-Kreuzung ihrer Lane (Minimap-Anteile)
PUNKT = {"oben": (0.12, 0.12), "Mitte": (0.5, 0.5), "unten": (0.88, 0.88)}
BASIS_RADIUS = 4500.0
ZAHL = {1: "einer", 2: "zwei", 3: "drei", 4: "vier", 5: "alle fünf"}
ZAHL_GROSS = {1: "Einer", 2: "Zwei", 3: "Drei", 4: "Vier", 5: "Alle fünf"}


@dataclass
class GegnerOrt:
    champion: str
    rolle: str
    seite: str | None = None          # letzte Sichtung: oben / Mitte / unten / Basis (None = nie gesehen)
    alter: float | None = None        # s seit der letzten Sichtung (0 = sichtbar)
    vermutlich: str | None = None     # Seite jetzt (Tote: Basis; Jungler: Prognose)
    mia: bool = False
    tot_bis: float | None = None      # Spielzeit des Respawns
    flash_bis: float | None = None    # Spielzeit, zu der Flash wieder da ist (nur wenn bekannt verbraucht)
    tp_bis: float | None = None
    level: int = 0
    item_gold: int = 0


@dataclass
class Kartenlage:
    zeit: float
    gegner: list[GegnerOrt] = field(default_factory=list)
    je_seite: dict[str, list[str]] = field(default_factory=dict)    # oben/Mitte/unten -> Namen (frisch gesehen)
    unbekannt: list[str] = field(default_factory=list)
    tot: list[str] = field(default_factory=list)
    fenster: dict[str, float] = field(default_factory=dict)         # Seite -> s bis der erste Gegner dort sein kann

    def zeile(self) -> str:
        """Fuers Dashboard und kern.kontext(): "oben 1 · Mitte 2 · unten 0 · unbekannt 1 · tot 1"."""
        teile = [f"{s} {len(self.je_seite.get(s, []))}" for s in SEITEN]
        return " · ".join(teile + [f"unbekannt {len(self.unbekannt)}", f"tot {len(self.tot)}"])

    def stand(self) -> dict:
        return {"je_seite": {s: self.je_seite.get(s, []) for s in SEITEN}, "unbekannt": self.unbekannt,
                "tot": self.tot, "fenster": {s: round(v) for s, v in self.fenster.items()},
                "flash": [(g.champion, round(g.flash_bis - self.zeit)) for g in self.gegner
                          if g.flash_bis is not None and g.flash_bis > self.zeit]}


def _seite(pos) -> str:
    return _WORT[kartenseite(pos)]


def bauen(m, lagebild, cfg: dict) -> Kartenlage | None:
    """Die Kartenlage dieses Takts. cfg = kern.toml [makro]."""
    b, p = m.b, m.p
    if b is None or p is None:
        return None
    k = Kartenlage(zeit=m.zeit, je_seite={s: [] for s in SEITEN})
    z = getattr(lagebild, "zauber", None)
    bekannt = cfg["bekannt_s"]
    for g in b.gegner:
        o = GegnerOrt(g.champion, g.s.rolle or "", level=g.s.level, item_gold=g.s.item_gold)
        if g.pos is not None and g.seit is not None:
            feind_brunnen = BRUNNEN.get(g.s.team)
            o.seite = "Basis" if feind_brunnen is not None and abstand(g.pos, feind_brunnen) <= BASIS_RADIUS \
                else _seite(g.pos)
            o.alter = 0.0 if g.sichtbar else g.seit
        if g.s.tot:
            o.tot_bis = m.zeit + float(g.s.respawn or 0.0)
            o.vermutlich = "Basis"
            k.tot.append(g.champion)
        else:
            if o.alter is not None and o.alter <= bekannt and o.seite in SEITEN:
                o.vermutlich = o.seite
                k.je_seite[o.seite].append(g.champion)
            elif o.alter is not None and o.alter <= bekannt and o.seite == "Basis":
                o.vermutlich = "Basis"
            else:
                k.unbekannt.append(g.champion)
                if g.s.rolle == "JUNGLE" and m.p_jungler is not None:
                    from .merkmale import meine_seite
                    meine = meine_seite(m)
                    if meine is not None:
                        o.vermutlich = {"oben": "oben", "unten": "unten"}[meine] if m.p_jungler >= 0.6 else \
                            ({"oben": "unten", "unten": "oben"}[meine] if m.p_jungler <= 0.4 else None)
            o.mia = m.lane_phase and g.s.rolle in ("TOP", "MIDDLE", "BOTTOM") and (o.alter is None or
                                                                                o.alter >= cfg["mia_s"])
        if z is not None:
            for zauber, feld in (("SummonerFlash", "flash_bis"), ("SummonerTeleport", "tp_bis")):
                t = z.timer.get((g.s.name, zauber))
                if t is not None and t.zurueck > m.zeit:
                    setattr(o, feld, t.zurueck)
        k.gegner.append(o)
    k.fenster = {s: fenster(m, s) for s in SEITEN}
    return k


def fenster(m, seite: str) -> float:
    """Sekunden, bis der erste Gegner auf `seite` sein kann: aus seiner letzten Sichtung (weitergelaufen, seit er
    ungesehen ist), Tote aus dem Brunnen nach dem Respawn; nie gesehen = sofort (0)."""
    ziel = einheiten(*PUNKT[seite])
    beste = 1e9
    for g in m.b.gegner:
        tempo = g.tempo or 350.0
        if g.s.tot:
            quelle = BRUNNEN.get(g.s.team)
            t = float(g.s.respawn or 0.0) + (abstand(quelle, ziel) * WEGFAKTOR / tempo if quelle else 0.0)
        elif g.pos is None or g.seit is None:
            t = 0.0
        else:
            t = max(0.0, abstand(g.pos, ziel) * WEGFAKTOR / tempo - (0.0 if g.sichtbar else g.seit))
        beste = min(beste, t)
    return beste if beste < 1e9 else 0.0


def _namen(namen: list[str]) -> str:
    return namen[0] if len(namen) == 1 else ", ".join(namen[:-1]) + " und " + namen[-1]


def folgerung(k: Kartenlage, m, plan_kurz: str | None = None) -> str:
    """Was aus der Lage folgt - Buch 4, 1.3: nur mit Wirkung auf dich. Der erste passende Satz:
    drei fehlen -> nicht tief; deine Seite leer und lange frei -> frei; zwei auf deiner Seite -> nicht allein vor; zwei
    tot -> dein Plan jetzt; eine grosse Gruppe woanders -> deine Seite; sonst, wie weit der Naechste ist."""
    mein = _seite(m.pos) if m.pos is not None else None
    n_mein = len(k.je_seite.get(mein, [])) if mein else 0
    dort = "in der Mitte" if mein == "Mitte" else mein
    if len(k.unbekannt) >= 3:
        return f"{ZAHL_GROSS.get(len(k.unbekannt), len(k.unbekannt))} fehlen: nicht tief gehen"
    if mein and n_mein == 0 and k.fenster.get(mein, 0) >= 20:
        wo = "Mitte" if mein == "Mitte" else mein
        return f"{wo[:1].upper()}{wo[1:]} ist {int(k.fenster[mein] // 5 * 5)} Sekunden frei"
    if n_mein >= 2:
        return f"{ZAHL_GROSS.get(n_mein, n_mein)} {dort}: nicht allein nach vorn"
    if len(k.tot) >= 2 and plan_kurz:
        return f"{ZAHL_GROSS.get(len(k.tot), len(k.tot))} tot: {plan_kurz} jetzt"
    gross = max(SEITEN, key=lambda s: len(k.je_seite.get(s, [])))
    if len(k.je_seite.get(gross, [])) >= 3 and gross != mein:
        andere = mein or next(s for s in SEITEN if s != gross)
        return f"{ZAHL_GROSS.get(len(k.je_seite[gross]))} {'in der Mitte' if gross == 'Mitte' else gross}: " \
               f"{'die Mitte' if andere == 'Mitte' else andere} ist frei"
    if m.b is not None:
        # nur wer frisch gesehen ist (101426: "der Naechste braucht 0 Sekunden zu dir" - ein Ungesehener)
        nah = [g for g in m.b.gegner if not g.s.tot and g.ankunft is not None and g.pos is not None
               and (g.sichtbar or (g.seit is not None and g.seit <= 5))]
        if nah:
            g = min(nah, key=lambda x: x.ankunft)
            return f"{g.champion} steht nah bei dir" if g.ankunft < 5 else \
                f"{g.champion} braucht {int(g.ankunft)} Sekunden zu dir"
    return "keiner von ihnen ist nah bei dir"


def satz(k: Kartenlage, m, kurz: bool = False, plan_kurz: str | None = None) -> str:
    """A4: wer wo ist (nach Kartenseite), bekannte Flashs und Tote, dann die Folgerung - "Viego und Twitch unten,
    Aurora Mitte ohne Flash bis 24:10, Sett fehlt. Oben ist frei." `kurz` (ungefragt): <= 16 Woerter, ohne Uhrzeiten."""
    from .zeitleiste import _uhr
    ohne = {g.champion: g.flash_bis for g in k.gegner if g.flash_bis is not None}
    teile = []
    for s in SEITEN:
        namen = k.je_seite.get(s, [])
        if not namen:
            continue
        wort = "Mitte" if s == "Mitte" else s
        if kurz:
            teile.append(f"{_namen(namen)} {wort}")
        else:
            mit = [f"{n} ohne Flash bis {_uhr(ohne[n])}" if n in ohne else n for n in namen]
            teile.append(f"{_namen(mit)} {wort}")
    basis = [g.champion for g in k.gegner if g.vermutlich == "Basis" and g.tot_bis is None and g.alter is not None
             and g.alter <= 20]
    if basis:
        teile.append(f"{_namen(basis)} in ihrer Basis")
    if k.tot:
        tote = {g.champion: g.tot_bis for g in k.gegner if g.tot_bis is not None}
        teile.append(f"{_namen(k.tot)} tot" if kurz else
                     _namen([f"{n} tot bis {_uhr(tote[n])}" for n in k.tot]))
    if k.unbekannt:
        teile.append(f"{_namen(k.unbekannt)} {'fehlt' if len(k.unbekannt) == 1 else 'fehlen'}")
    f = folgerung(k, m, plan_kurz)

    def bauen(t):
        erster = ", ".join(t) if t else "Keiner von ihnen ist zu sehen"
        return f"{erster[:1].upper()}{erster[1:]}. {f[:1].upper()}{f[1:]}."
    text = bauen(teile)
    if kurz:
        # zuerst fallen die Fehlenden, dann die Toten, dann Seiten, die die Folgerung nicht nennt (173159 17:50: "Olaf
        # unten, Cho'Gath tot: drei in der Mitte" - die Gruppe der Folgerung war weggekuerzt)
        rang = sorted(range(len(teile)), key=lambda i: (teile[i].endswith(("fehlt", "fehlen")), teile[i].endswith("tot"),
                                                        not any(w in f for w in teile[i].split()[-1:])), reverse=True)
        weg = set()
        for i in rang:
            if len(text.split()) <= 16 or len(weg) == len(teile) - 1:
                break
            weg.add(i)
            text = bauen([t for j, t in enumerate(teile) if j not in weg])
    return text
