"""Todesanalyse live: warum bist du gerade gestorben - gesagt, waehrend du auf den Respawn wartest.

Ein Freund auf Discord sagt nach deinem Tod nicht "Gank von Warwick", sondern: "Warwick war
40 Sekunden weg, deine Welle stand an seinem Turm - so weit vorne nur, wenn du weisst, wo er
ist." Das ist der Moment, in dem man lernt: die Szene ist frisch, und die Todeszeit ist
ohnehin Wartezeit.

Dafuer fuehrt der Rueckblick die letzten 45 Sekunden mit (je Takt: eigenes Leben, Gold, Ort,
Welle der eigenen Lane, wer von den Gegnern zu sehen war). Beim Tod werden daraus Fakten -
nur Gesehenes, wie in der Review-Zeitleiste -, und Claude sagt in zwei Saetzen den Grund und
was naechstes Mal zu tun ist (stratege.veredle mit gehirn.TOD_SYSTEM). Kommt Claude nicht
rechtzeitig, bleibt der Standardsatz der Regel.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from . import minimap
from .ansicht import uhr
from .zustand import Partie, gegenteam

RUECKBLICK = 45.0     # Sekunden
NAH = 0.18            # Kartenanteil (Manhattan): "in deiner Naehe"


@dataclass
class Blick:
    zeit: float
    leben: float | None           # 0..1
    gold: float | None
    ort: tuple[float, float] | None
    welle: str | None             # eigene Lane, in Worten aus deiner Sicht
    gegner: dict[str, tuple[bool, float, float, float] | None] = field(default_factory=dict)
    # Name -> (jetzt sichtbar, zuletzt gesehen um, x, y) oder None (nie gesehen)
    freunde_nah: list[str] = field(default_factory=list)


class Rueckblick:
    def __init__(self):
        self.blicke: deque[Blick] = deque()

    def merke(self, p: Partie, lb=None) -> None:
        if not p.ich:
            return
        m = p.werte.get("maxHealth")
        ort = welle = None
        gegner, nah = {}, []
        if lb is not None and lb.aktiv:
            if (g := lb.gesehen(p.ich)) and p.zeit - g[0] < 2:
                ort = (g[1], g[2])
            from .welle import LANE_DER_ROLLE
            if (lane := LANE_DER_ROLLE.get(p.ich.rolle)) and (z := lb.welle(lane, p.zeit)):
                welle = z.worte(p.mein_team)
            for s in p.gegner():
                if s.tot:
                    continue
                g = lb.gesehen(s)
                gegner[s.name] = (lb.sichtbar(s), g[0], g[1], g[2]) if g else None
            if ort:
                for s in p.team(p.mein_team):
                    if s is not p.ich and not s.tot and lb.sichtbar(s) and (g := lb.gesehen(s)) \
                            and abs(g[1] - ort[0]) + abs(g[2] - ort[1]) < NAH:
                        nah.append(s.champion)
        self.blicke.append(Blick(p.zeit, round(p.werte.get("currentHealth", 0) / m, 2) if m else None,
                                 p.gold, ort, welle, gegner, nah))
        while self.blicke and self.blicke[0].zeit < p.zeit - RUECKBLICK:
            self.blicke.popleft()

    def vor(self, zeit: float, sekunden: float) -> Blick | None:
        """Der letzte Blick, der mindestens `sekunden` vor `zeit` liegt."""
        kandidaten = [b for b in self.blicke if b.zeit <= zeit - sekunden]
        return kandidaten[-1] if kandidaten else None

    def auftauchen(self, name: str, zeit: float) -> tuple[float | None, float | None, str | None]:
        """Fuer einen Gegner: (Sekunden vor `zeit`, seit denen er durchgehend zu sehen war,
        wie lange er davor unsichtbar war, wo er zuletzt gesehen worden war) - soweit der
        Rueckblick reicht. (None, None, None), wenn er gar nicht zu sehen war."""
        blicke = [b for b in self.blicke if b.zeit <= zeit]
        if not blicke or not (letzter := blicke[-1].gegner.get(name)) or not letzter[0]:
            return None, None, None
        i = len(blicke) - 1
        while i > 0 and (g := blicke[i - 1].gegner.get(name)) and g[0]:
            i -= 1
        seit = zeit - blicke[i].zeit
        if i == 0:
            return seit, None, None           # die ganze Zeit sichtbar
        davor = blicke[i - 1].gegner.get(name)
        if not davor:
            return seit, None, "nie"
        return seit, blicke[i].zeit - davor[1], minimap.ort(davor[2], davor[3])


def _blick_satz(b: Blick, vorher: int, p: Partie) -> str:
    teile = [f"{vorher} s vorher:"]
    if b.leben is not None:
        teile.append(f"dein Leben {int(b.leben * 100)} %,")
    if b.gold is not None:
        teile.append(f"{int(b.gold)} Gold unausgegeben,")
    if b.ort:
        teile.append("du warst " + minimap.ort(*b.ort, p.mein_team) + ",")
    if b.welle:
        teile.append(f"deine Welle: {b.welle}")
    return " ".join(teile).rstrip(",")


def fakten(p: Partie, kill, rb: Rueckblick, lb=None) -> str:
    """Alles, was zum Tod gesichert ist - fuer Claude, in Zeilen."""
    zeit = kill.zeit if kill else p.zeit
    taeter = kill.taeter if kill else None
    helfer = [h for h in (p.spieler_namens(n) for n in (kill.daten.get("Assisters", []) if kill else [])) if h]
    beteiligt = [s for s in [taeter, *helfer] if s and s.team != p.mein_team]
    zeilen = [f"TOD um {uhr(zeit)}: getoetet von {taeter.champion if taeter else kill.daten.get('KillerName', '?') if kill else '?'}"
              + (f", beteiligt: {', '.join(h.champion for h in helfer)}" if helfer else " (allein)")
              + f". Wiedereinstieg in {int(p.ich.respawn)} s."]
    j = p.jungler(gegenteam(p.mein_team))
    if j and p.ich.rolle != "JUNGLE" and any(s is j for s in beteiligt):
        zeilen.append(f"Der gegnerische Jungler {j.champion} war beteiligt (Gank).")
    for n in (15, 5):
        if b := rb.vor(zeit, n):
            zeilen.append(_blick_satz(b, n, p))
    # Ohne eigene Position auf der Minimap ist "nicht zu sehen" nicht zu unterscheiden von
    # "nicht gelesen" (Partie 3, 21:17: alle fuenf Toeter angeblich unsichtbar - die Bilder fehlten).
    if not any(b.ort for b in rb.blicke if zeit - 12 <= b.zeit <= zeit):
        zeilen.append("Minimap fuer diesen Moment nicht gelesen - ueber Sicht und Positionen keine Aussage.")
        beteiligt_sicht = []
    else:
        beteiligt_sicht = beteiligt
    for s in beteiligt_sicht:
        seit, weg, wo = rb.auftauchen(s.name, zeit - 1)
        if seit is None:
            zeilen.append(f"{s.champion} war vor dem Tod nicht auf der Karte zu sehen.")
        elif weg is None and wo is None:
            zeilen.append(f"{s.champion} war die letzten {int(seit)} s durchgehend zu sehen.")
        elif wo == "nie":
            zeilen.append(f"{s.champion} tauchte {int(seit)} s vor dem Tod zum ersten Mal auf.")
        else:
            zeilen.append(f"{s.champion} tauchte {int(seit)} s vor dem Tod auf; davor {int(weg)} s nicht zu sehen "
                          f"(zuletzt {wo}).")
    if beteiligt_sicht and (b := rb.vor(zeit, 5)):
        fehlend = []
        for s in p.gegner():
            if s in beteiligt or s.name not in b.gegner:   # nicht drin: war da gerade tot
                continue
            g = b.gegner.get(s.name)
            if g is None:
                fehlend.append(f"{s.champion} (nie gesehen)")
            elif not g[0] and b.zeit - g[1] > 8:
                fehlend.append(f"{s.champion} (seit {int(b.zeit - g[1])} s, zuletzt {minimap.ort(g[2], g[3], p.mein_team)})")
        if fehlend:
            zeilen.append("5 s vorher nicht auf der Karte: " + ", ".join(fehlend))
        if b.ort:
            zeilen.append("Mitspieler in deiner Naehe: " + (", ".join(b.freunde_nah) or "keiner"))
    if taeter and taeter.team != p.mein_team:
        zeilen.append(f"Level: du {p.ich.level}, {taeter.champion} {taeter.level}; "
                      f"Itemgold: du {p.ich.item_gold}, {taeter.champion} {taeter.item_gold}.")
    if lb is not None and hasattr(lb, "zauber"):
        from .zauber import NAME_DE
        for s in beteiligt:
            weg = [f"{NAME_DE.get(z, z)} (noch {int(r)} s)" for z in ("SummonerFlash", "R")
                   if (r := lb.zauber.fehlt(s, z, zeit))]
            if weg:
                zeilen.append(f"Bekannt: {s.champion} hatte kein {', kein '.join(weg)}.")
    for schl, name in (("drache", "Drache"), ("baron", "Baron"), ("herold", "Herold"), ("larven", "Larven")):
        n = p.naechster_spawn(schl)
        if n is not None and 0 <= n - zeit <= p.ich.respawn + 45:
            zeilen.append(f"{name} spawnt in {int(n - zeit)} s - du bist noch {int(p.ich.respawn)} s tot.")
    return "\n".join(zeilen)
