"""Lagebild: wer wurde zuletzt wo auf der Minimap gesehen.

Bilder kommen mit Wanduhrzeit (live vom Beobachter, im Nachspielen aus dem
Bilderordner einer Aufnahme). Der Aufrufer rechnet sie ueber den letzten
API-Schnappschuss in Spielzeit um - so laufen Live und Aufnahme gleich.
"""
from __future__ import annotations

import json
import threading
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np

from . import hud, minimap
from .zustand import Partie, Spieler

# Ults, die quer ueber die Karte versetzen (Minimap-Fernsprung ohne Teleport = Ult)
GLOBALE_ULTS = {"TwistedFate", "Shen", "Pantheon", "Galio", "Ryze", "Taliyah", "Nocturne", "Sion"}

SICHTBAR_TOLERANZ = 1.6   # Sekunden: so alt darf eine Sichtung sein und gilt noch als "jetzt sichtbar"


VERLAUF = 15.0            # Sekunden Positionsverlauf je Spieler
DECKUNG = 0.045           # Kartenanteil: so nah an der letzten Stelle liegt ein anderes Icon auf einem Verbuendeten
BRUNNEN = {"ORDER": (0.035, 0.965), "CHAOS": (0.965, 0.035)}   # Minimap-Anteile, Wiedereinstieg


class Lagebild:
    def __init__(self):
        from .zauber import Zaubertimer
        self.zuletzt: dict[tuple[str, str], tuple[float, float, float]] = {}  # (name, team) -> (zeit, x, y)
        self.verlauf: dict[tuple[str, str], deque] = {}
        self.letztes_bild: float | None = None
        self.zauber = Zaubertimer()
        self.chat: list[tuple[float, str]] = []   # (Spielzeit, Zeile) - alles, was im Chat stand
        self.mitspieler: dict[str, tuple[float, float, bool | None]] = {}  # Name -> (Zeit, Leben 0..1, Ult bereit)
        self.wellen: dict = {}            # Lane -> welle.LaneZustand
        self.wellen_zeit: float | None = None
        self.letzter_tod: tuple[float, str] | None = None   # (Spielzeit, Fakten der Todesanalyse)
        self.eigene: dict[str, tuple[bool, float]] = {}     # Taste -> (bereit, seit Spielzeit), aus dem HUD
        self._eigene_kandidat: dict[str, tuple[bool, float]] = {}   # Wechsel, einmal gelesen, noch unbestaetigt
        self.eigene_zeit: float | None = None
        self.platten: dict[tuple[str, str, str], int] = {}   # (Team, Lane, Stufe) -> verbleibende Platten (Minimap)
        self.gegner_leben: dict[str, tuple[float, float]] = {}   # Spielername -> (Zeit, Leben 0..1) aus dem Spielbild
        self.gegner_mana: dict[str, tuple[float, float]] = {}    # ... (Zeit, Mana 0..1) aus dem Balken darunter
        self._tp_kandidat: dict[str, tuple] = {}     # Spielername -> (Zeit, x, y, zuletzt gesehen) eines Fernsprungs
        self._tode: dict[str, float] = {}            # Spielername -> zuletzt tot (Spielzeit)
        self._recall: dict[str, float] = {}          # Gegner -> Spielzeit, zu der er nach 7 s Stillstand verschwand
        self.fernspruenge: list = []                 # gemeldete TP/globale Ults (zauber.Timer)

    def eigene_zauber(self, p: Partie, jetzt: float) -> dict[str, float] | None:
        """Beschwoererzauber des Spielers -> Sekunden bis bereit (0 = bereit), aus dem HUD (frisch, < 3 s).
        Die Restzeit rechnet ab dem Moment, in dem der Buchstabe von gelb auf weiss sprang."""
        if self.eigene_zeit is None or jetzt - self.eigene_zeit > 3 or not p.ich:
            return None
        from .zauber import cooldown
        aus = {}
        for taste, schl in zip(("D", "F"), p.ich.zauber):
            if (z := self.eigene.get(taste)) is None:
                continue
            bereit, seit = z
            aus[schl] = 0.0 if bereit else max(1.0, cooldown(schl, p.ich, seit) - (jetzt - seit))
        return aus

    def eigene_faehigkeiten(self, jetzt: float) -> dict[str, bool] | None:
        """Q W E R bereit? (aus dem HUD, frisch)"""
        if self.eigene_zeit is None or jetzt - self.eigene_zeit > 3:
            return None
        return {t: self.eigene[t][0] for t in "QWER" if t in self.eigene}

    def ereignisse(self, zeit_von_wand, liste, p: Partie) -> list:
        """Spruenge und Chatzeilen des Beobachters -> Zauber-Timer. Gibt die neuen Timer zurueck."""
        from . import zauber
        neu = []
        blinks = zauber.blink_champions()
        for e in liste:
            if e[0] == "sprung":
                s = e[1]
                sp = zuordnen(minimap.Sichtung(s.champion_id, s.team, s.x, s.y, 1.0), p)
                if (sp and sp.team != p.mein_team and "SummonerFlash" in sp.zauber
                        and sp.champion_id not in blinks and not sp.tot):
                    if t := self.zauber.benutzt(sp, "SummonerFlash", zeit_von_wand(s.zeit), "Minimap"):
                        neu.append(t)
            elif e[0] == "wellen":
                from . import welle
                self.wellen = welle.zustaende(e[2])
                self.wellen_zeit = zeit_von_wand(e[1])
            elif e[0] == "platten":
                self.platten.update(e[2])
            elif e[0] == "schirm_sprung":
                # Flash auf dem Spielbild (lebensbalken.Balkenspur): nur mit gelesenem Namen, und sind beide Namen
                # (Absprung, Landung) lesbar, muessen sie derselbe Spieler sein
                from .lebensbalken import zuordnen as balken_zuordnen
                team, anteil, x0, y0, x1, y1, weite, name_von, name_nach = e[2]
                sp_von = balken_zuordnen(name_von, p.gegner()) if name_von else None
                sp_nach = balken_zuordnen(name_nach, p.gegner()) if name_nach else None
                sp = sp_nach or sp_von
                from .champions import hat_blink_oder_dash
                # nur ohne eigenen Dash: Live 21:21, 9:18 sprangen Gragas und Tryndamere zugleich - ein Engage mit
                # beiden E, kein Flash. Bei Dash-Champions bleibt es beim Protokoll (zum Nachpruefen).
                if sp is not None and (sp_von is None or sp_nach is None or sp_von.name == sp_nach.name) \
                        and "SummonerFlash" in sp.zauber and sp.champion_id not in blinks and not sp.tot \
                        and not hat_blink_oder_dash(sp.champion_id):
                    if t := self.zauber.benutzt(sp, "SummonerFlash", zeit_von_wand(e[1]), "Bildschirm"):
                        neu.append(t)
            elif e[0] == "balken":
                # Lebensbalken ueber den Koepfen (Spielbild): nur mit gelesenem Namen zugeordnet
                from .lebensbalken import zuordnen as balken_zuordnen
                zeit = zeit_von_wand(e[1])
                for text, anteil, team, *mana in e[2]:
                    if team == "feind" and (sp := balken_zuordnen(text, p.gegner())):
                        self.gegner_leben[sp.name] = (zeit, float(anteil))
                        if mana and mana[0] is not None:
                            self.gegner_mana[sp.name] = (zeit, float(mana[0]))
            elif e[0] == "eigene":
                # eigene Faehigkeiten/Zauber aus dem HUD: Wechsel bereit -> weg ist der Moment der Nutzung
                # Ein Wechsel zaehlt erst, wenn ihn zwei Lesungen hintereinander zeigen (Partie 7, 13:10-13:12:
                # F weg / bereit / weg im Sekundentakt - ein Fehllesen haette die Restzeit neu gestartet)
                zeit = zeit_von_wand(e[1])
                for taste, bereit in e[2].items():
                    alt = self.eigene.get(taste)
                    if alt is None:
                        self.eigene[taste] = (bereit, zeit)
                    elif alt[0] != bereit:
                        kandidat = self._eigene_kandidat.get(taste)
                        if kandidat and kandidat[0] == bereit:
                            self.eigene[taste] = (bereit, kandidat[1])   # ab der ersten Lesung
                            self._eigene_kandidat.pop(taste, None)
                        else:
                            self._eigene_kandidat[taste] = (bereit, zeit)
                    else:
                        self._eigene_kandidat.pop(taste, None)
                self.eigene_zeit = zeit
            elif e[0] == "hud":
                # Reihenfolge der Leiste = Reihenfolge des Teams ohne dich (geprueft an Partie 2)
                andere = [s for s in p.team(p.mein_team) if s is not p.ich] if p.ich else []
                for sp, m in zip(andere, e[2]):
                    self.mitspieler[sp.name] = (zeit_von_wand(e[1]), m.leben, m.ult_bereit)
            elif e[0] == "chat":
                zeit = zeit_von_wand(e[1])
                self.chat.append((zeit, e[2]))
                if zauber.chat_stempel(e[2]) is not None:
                    self._chat_mit_stempel = True
                geschrieben = zauber.chat_zeit(e[2], zeit)
                if geschrieben is None and getattr(self, "_chat_mit_stempel", False):
                    continue   # alte Zeile, wieder eingeblendet und neu gelesen - zaehlt nicht noch einmal
                geschrieben = zeit if geschrieben is None else geschrieben   # Chat ohne Zeitstempel (Einstellung)
                for sp, schl, zurueck in zauber.aus_chat(e[2], p):
                    if t := self.zauber.benutzt(sp, schl, geschrieben, "Chat", zurueck):
                        neu.append(t)
        return neu

    def neu(self, zeit: float, sichtungen: list[minimap.Sichtung], p: Partie) -> None:
        self.letztes_bild = zeit if self.letztes_bild is None else max(self.letztes_bild, zeit)
        self.tod_merken(p)
        for s in sichtungen:
            sp = zuordnen(s, p)
            if sp:
                schl = (sp.name, sp.team)
                if sp.team != p.mein_team and schl in self.zuletzt:
                    self._fernsprung(sp, self.zuletzt[schl], zeit, s.x, s.y, p)
                self.zuletzt[schl] = (zeit, s.x, s.y)
                v = self.verlauf.setdefault(schl, deque())
                v.append((zeit, s.x, s.y))
                while v and v[0][0] < zeit - VERLAUF:
                    v.popleft()
        self._verbuendete_halten(zeit, sichtungen, p)
        self._recalls_merken(zeit, sichtungen, p)

    def _recalls_merken(self, zeit: float, sichtungen: list[minimap.Sichtung], p: Partie) -> None:
        """Ein Gegner stand 7 s still und ist jetzt weg: Recall (8 s kanalisieren), er steht im Brunnen. Streng
        (nicht 5,5 s wie beim Lane-Gegner): wer faelschlich im Brunnen vermutet wird, gilt als weiter weg, als
        er ist - die gefaehrliche Richtung."""
        gefunden = {sp.name for s in sichtungen if (sp := zuordnen(s, p)) is not None}
        for sp in p.gegner():
            g = self.zuletzt.get((sp.name, sp.team))
            if g is None or sp.tot:
                continue
            if sp.name in gefunden:
                self._recall.pop(sp.name, None)
            elif sp.name not in self._recall and 0.5 <= zeit - g[0] <= 3 and self.stand_still(sp, dauer=7.0):
                self._recall[sp.name] = g[0]

    def brunnen_seit(self, sp: Spieler, jetzt: float) -> tuple[float, float, float, str] | None:
        """Wo ein nicht sichtbarer Gegner sicher ist, obwohl die letzte Sichtung woanders war: nach einem Tod
        (Wiedereinstieg) oder einem Recall steht er in seinem Brunnen. (x, y, seit wann, 'Tod'/'Recall')."""
        g = self.zuletzt.get((sp.name, sp.team))
        if g is None or sp.tot:
            return None
        bx, by = BRUNNEN.get(sp.team, (0.5, 0.5))
        tod = self._tode.get(sp.name)
        if tod is not None and tod > g[0]:
            return bx, by, tod, "Tod"
        r = self._recall.get(sp.name)
        if r is not None and r >= g[0] - 0.01:
            return bx, by, r, "Recall"
        return None

    def _verbuendete_halten(self, zeit: float, sichtungen: list[minimap.Sichtung], p: Partie) -> None:
        """Verbuendete (und du) sind auf der Minimap IMMER zu sehen - fuer das eigene Team gibt es keinen Nebel.
        Fehlt einer, liegt sein Icon unter einem anderen oder ist am Kartenrand abgeschnitten (Brunnen). Live
        26.09.: Riven galt nur in 72 % der Takte als sichtbar, Braum in 57 %; um 2:00 lag Riven unter Heimerdinger,
        von 11:45 bis 14:08 stand sie im Brunnen, halb ueber den Kartenrand. Dann gilt er als gesehen:
          - unter einem Icon, das auf seiner letzten Stelle liegt: er laeuft mit ihm mit,
          - zuletzt im Brunnen: er steht noch dort,
          - seit der letzten Sichtung gestorben und wieder am Leben: er steht im Brunnen.
        Ohne einen dieser Gruende bleibt er unbekannt (kein Raten)."""
        if not p.ich or not p.mein_team:
            return
        gefunden = {sp.name for s in sichtungen if (sp := zuordnen(s, p)) is not None}
        for sp in p.team(p.mein_team):
            if sp.tot:
                self._tode[sp.name] = p.zeit
                continue
            schl = (sp.name, sp.team)
            alt = self.zuletzt.get(schl)
            if sp.name in gefunden or alt is None:
                continue
            t0, x0, y0 = alt
            if self._tode.get(sp.name, -1e9) >= t0 - 1:
                bx, by = BRUNNEN.get(sp.team, (x0, y0))
                self.zuletzt[schl] = (zeit, bx, by)     # nach dem Tod: Wiedereinstieg im Brunnen
                continue
            andere = [s for s in sichtungen if (sp2 := zuordnen(s, p)) is None or sp2.name != sp.name]
            naechst = min(andere, key=lambda s: (s.x - x0) ** 2 + (s.y - y0) ** 2) if andere else None
            deckung = (((naechst.x - x0) ** 2 + (naechst.y - y0) ** 2) ** 0.5, naechst) if naechst else None
            if deckung is not None and deckung[0] <= DECKUNG:
                self.zuletzt[schl] = (zeit, deckung[1].x, deckung[1].y)
            elif "Basis" in minimap.ort(x0, y0, p.mein_team) and sp.team == p.mein_team:
                self.zuletzt[schl] = (zeit, x0, y0)
            elif zeit - t0 <= 3 and self.stand_still(sp):
                bx, by = BRUNNEN.get(sp.team, (x0, y0))
                self.zuletzt[schl] = (zeit, bx, by)     # stand 5,5 s still und ist weg: Recall, jetzt im Brunnen

    def _fernsprung(self, sp: Spieler, alt: tuple[float, float, float], zeit: float, x: float, y: float,
                    p: Partie) -> None:
        """Teleport oder globale Ult von der Minimap: verschwunden und 3,5-15 s spaeter weit weg wieder da -
        schneller, als man laufen kann (> 1100 Einheiten/s, mindestens 3500 Einheiten). Nicht in der Basis
        (Recall), nicht nach einem Tod. Bestaetigt, wenn er am neuen Ort auch im naechsten Bild steht
        (ein falsch zugeordnetes Einzelbild ergaebe sonst einen TP-Timer)."""
        kand = self._tp_kandidat.get(sp.name)
        if kand is not None:
            t_neu, kx, ky, t0 = kand
            if zeit - t_neu <= 2.5 and abs(x - kx) + abs(y - ky) <= 0.05 and zeit > t_neu:
                del self._tp_kandidat[sp.name]
                self._fernsprung_melden(sp, t0, p)
                return
            if zeit - t_neu > 2.5:
                del self._tp_kandidat[sp.name]
        t0, x0, y0 = alt
        dt = zeit - t0
        if not (3.5 <= dt <= 15) or sp.tot or self._tot_zwischen(sp, t0, zeit):
            return
        d = ((x - x0) * 14820) ** 2 + ((y - y0) * 14881) ** 2
        d = d ** 0.5
        if d < 3500 or d / dt < 1100 or "Basis" in minimap.ort(x, y) or "Basis" in minimap.ort(x0, y0):
            return
        self._tp_kandidat[sp.name] = (zeit, x, y, t0)

    def _tot_zwischen(self, sp: Spieler, von: float, bis: float) -> bool:
        tod = self._tode.get(sp.name)
        return tod is not None and von - 1 <= tod <= bis

    def _fernsprung_melden(self, sp: Spieler, t0: float, p: Partie) -> None:
        from . import zauber
        if "SummonerTeleport" in sp.zauber and not self.zauber.fehlt(sp, "SummonerTeleport", t0 + 1):
            art = "SummonerTeleport"
        elif sp.champion_id in GLOBALE_ULTS and sp.level >= 6 and not self.zauber.fehlt(sp, "R", t0 + 1):
            art = "R"
        elif sp.rolle == "TOP" and t0 >= 815 and not self.zauber.fehlt(sp, "SummonerTeleport", t0 + 1):
            art = "SummonerTeleport"      # Top-Quest-TP (Saison 2026), auch ohne gewaehltes Teleport
        else:
            return
        if t := self.zauber.benutzt(sp, art, t0 + 1.0, "Minimap"):
            self.fernspruenge.append(t)

    def tod_merken(self, p: Partie) -> None:
        """Wer gerade tot ist - ein Wiedereinstieg in der Basis ist kein Teleport, und ein Verbuendeter steht
        danach im Brunnen."""
        for s in p.spieler:
            if s.tot:
                self._tode[s.name] = p.zeit

    def naehert_sich(self, sp: Spieler, ziel: tuple[float, float], jetzt: float, fenster: float = 2.5) -> float | None:
        """Um wie viel (Kartenanteil) ist `sp` in den letzten `fenster` Sekunden naeher an `ziel`
        gekommen? None, wenn er nicht durchgehend gesehen wurde."""
        v = self.verlauf.get((sp.name, sp.team))
        if not v or jetzt - v[-1][0] > 1.0:
            return None
        frueher = [(t, x, y) for t, x, y in v if t <= v[-1][0] - fenster + 0.5]
        if not frueher or v[-1][0] - frueher[-1][0] > fenster + 1.5:
            return None
        _, x0, y0 = frueher[-1]
        _, x1, y1 = v[-1]
        return (abs(x0 - ziel[0]) + abs(y0 - ziel[1])) - (abs(x1 - ziel[0]) + abs(y1 - ziel[1]))

    def stand_still(self, sp: Spieler, dauer: float = 5.5, toleranz: float = 0.015) -> bool:
        """Stand `sp` vor seiner letzten Sichtung mindestens `dauer` Sekunden auf
        der Stelle? So sieht ein Recall aus (8 s kanalisieren, dann weg)."""
        v = self.verlauf.get((sp.name, sp.team))
        if not v:
            return False
        ende, ex, ey = v[-1]
        punkte = [(t, x, y) for t, x, y in v if t >= ende - dauer - 1]
        return (ende - punkte[0][0] >= dauer
                and all(abs(x - ex) + abs(y - ey) <= toleranz for _, x, y in punkte))

    def gegner_mana_jetzt(self, sp: Spieler, jetzt: float) -> float | None:
        """Mana eines Gegners (0..1) aus dem Balken unter seinem Lebensbalken, wenn frisch (<= 2,5 s)."""
        g = self.gegner_mana.get(sp.name)
        return g[1] if g and jetzt - g[0] <= 2.5 else None

    def gegner_leben_jetzt(self, sp: Spieler, jetzt: float) -> float | None:
        """Leben eines Gegners (0..1) aus seinem Lebensbalken im Spielbild, wenn frisch (<= 2,5 s)."""
        g = self.gegner_leben.get(sp.name)
        return g[1] if g and jetzt - g[0] <= 2.5 else None

    def leben(self, sp: Spieler, jetzt: float) -> float | None:
        """Leben eines Mitspielers (0..1) aus der HUD-Leiste, wenn frisch (< 3 s)."""
        m = self.mitspieler.get(sp.name)
        return m[1] if m and jetzt - m[0] < 3 else None

    def ult_bereit(self, sp: Spieler, jetzt: float) -> bool | None:
        m = self.mitspieler.get(sp.name)
        return m[2] if m and jetzt - m[0] < 3 else None

    def welle(self, lane: str, jetzt: float):
        """Wellenstand einer Lane, wenn frisch (< 4 s)."""
        if self.wellen_zeit is None or jetzt - self.wellen_zeit > 4:
            return None
        return self.wellen.get(lane)

    def gesehen(self, sp: Spieler) -> tuple[float, float, float] | None:
        return self.zuletzt.get((sp.name, sp.team))

    def sichtbar(self, sp: Spieler) -> bool:
        g = self.gesehen(sp)
        return bool(g and self.letztes_bild is not None and g[0] >= self.letztes_bild - SICHTBAR_TOLERANZ)

    @property
    def aktiv(self) -> bool:
        return self.letztes_bild is not None


def zuordnen(s: minimap.Sichtung, p: Partie) -> Spieler | None:
    kandidaten = [sp for sp in p.spieler if sp.champion_id == s.champion_id]
    if len(kandidaten) == 1:
        return kandidaten[0]
    return next((sp for sp in kandidaten if sp.team == s.team), None) if s.team else None


def champions(p: Partie) -> list[tuple[str, str]]:
    return [(s.champion_id, s.team) for s in p.spieler]


# --- live: der Beobachter ---------------------------------------------------------

def ereignis_als_json(e: tuple) -> dict:
    from dataclasses import asdict
    if e[0] == "sprung":
        return {"art": "sprung", "w": e[1].zeit, **asdict(e[1])}
    if e[0] == "hud":
        return {"art": "hud", "w": e[1], "m": [[m.leben, m.ult_bereit] for m in e[2]]}
    if e[0] == "wellen":
        return {"art": "wellen", "w": e[1], "p": [[t, round(x, 4), round(y, 4)] for t, x, y in e[2]]}
    if e[0] == "eigene":
        return {"art": "eigene", "w": e[1], "b": e[2]}
    if e[0] == "platten":
        return {"art": "platten", "w": e[1], "p": {"/".join(k): v for k, v in e[2].items()}}
    if e[0] == "balken":
        return {"art": "balken", "w": e[1], "b": [list(x) for x in e[2]]}      # (Text, Leben, Team[, Mana])
    return {"art": e[0], "w": e[1], "text": e[2]}


def ereignis_aus_json(d: dict) -> tuple:
    from . import hud
    if d["art"] == "sprung":
        felder = {k: d[k] for k in ("champion_id", "team", "zeit", "weite", "x", "y")}
        return ("sprung", minimap.Sprung(**felder))
    if d["art"] == "hud":
        return ("hud", d["w"], [hud.Mitspieler(le, ul) for le, ul in d["m"]])
    if d["art"] == "wellen":
        return ("wellen", d["w"], [tuple(q) for q in d["p"]])
    if d["art"] == "eigene":
        return ("eigene", d["w"], d["b"])
    if d["art"] == "platten":
        return ("platten", d["w"], {tuple(k.split("/")): v for k, v in d["p"].items()})
    if d["art"] == "balken":
        return ("balken", d["w"], [tuple(x) for x in d["b"]])
    return (d["art"], d["w"], d["text"])


class _Kamera:
    """Bildschirmausschnitte: Desktop-Duplizierung (dxcam, 2-5 ms), sonst GDI (~110 ms)."""

    def __init__(self):
        self._dx = None
        try:
            import dxcam
            self._dx = dxcam.create(output_color="BGR")
        except Exception:
            self._dx = None
        self._letzt: dict[tuple, np.ndarray] = {}

    def hole(self, box: tuple[int, int, int, int]) -> np.ndarray | None:
        if self._dx is not None:
            try:
                bild = self._dx.grab(region=box)
                if bild is None:          # Bildschirm unveraendert seit dem letzten Mal
                    return self._letzt.get(box)
                self._letzt[box] = bild
                return bild
            except Exception:
                self._dx = None           # z. B. anderer Monitor: auf GDI ausweichen
        from PIL import ImageGrab
        return cv2.cvtColor(np.asarray(ImageGrab.grab(bbox=box, all_screens=True)), cv2.COLOR_RGB2BGR)


# Chat unten links, grosszuegig (Anteil des Spielfensters) - genau geeicht wird an einer Partie.
# Chat-Fenster (Anteile des Spielfensters), geeicht an Partie 4 und 5 (4K): mit Unterkante 0.90 lag die
# NEUESTE Zeile immer knapp darunter (~0.91) - ein Ping wurde erst lesbar, wenn die naechste Nachricht ihn
# hochschob (Partie 5: 5:03 gepingt, 6:01 gelesen). Unten 0.95 (Eingabezeile), oben 0.70 (darueber nur
# Spielwelt mit Namensschildern als Rauschen).
CHAT = (0.0, 0.70, 0.32, 0.95)
BILDSCHIRM_BREITE = 1600   # fuer Claude: Lebensbalken und Namen noch lesbar, ~150 KB je Bild
SCHIRM_ALLE = 5.0          # Sekunden: so oft ein Spielbild auf die Platte (Review), ~45 MB je 30-min-Partie
SPUR_ALLE = 0.08           # Sekunden: so oft sucht die Balkenspur Flash-Spruenge auf dem Spielbild (~12/s)
BILDER_BEHALTEN = 20 * 60     # Sekunden: aeltere Minimap-Bilder der laufenden Partie werden entfernt


class Beobachter(threading.Thread):
    """Schaut 1/`takt`-mal je Sekunde auf die Minimap (Verfolger, Flash-Spruenge)
    und einmal je Sekunde in den Chat (Windows-Texterkennung).

    Liefert ueber `abholen()` (Wanduhr, Sichtungen) und ueber `ereignisse()`
    Spruenge und neue Chatzeilen. Schreibt, wenn `ordner` gesetzt ist:
    alle Sichtungen je Bild (`sichtungen.jsonl.gz`), ein Minimap-Bild je Sekunde
    (nur die letzten 20 Minuten), Chat-Bilder, wenn neuer Text dazukommt."""

    def __init__(self, ordner: Path | None, takt: float = 1 / 60, bild_alle: float = 1.0):
        # 60 Bilder/s (Carlos, 26.09.: "ich habe immer noch max FPS"): Dashes verteilen sich auf mehr
        # Bilder, ein Flash bleibt ein Einzelbild-Sprung; bestaetigt wird nach Zeit (minimap.BESTAETIGT_NACH)
        super().__init__(daemon=True)
        self.ordner, self.takt, self.bild_alle = ordner, takt, bild_alle
        if ordner:
            ordner.mkdir(parents=True, exist_ok=True)
        self.champions: list[tuple[str, str]] = []
        self.anzahl = 0
        self.fehler: str | None = None
        self.messung: list[float] = []
        self._neu: list[tuple[float, list[minimap.Sichtung]]] = []
        self.aktuell: tuple[float, list[minimap.Sichtung]] = (0.0, [])   # letztes Bild, nicht abholend
        # Der Spielbildschirm, einmal je Sekunde, die letzten 12 s (JPEG, 1600 breit): damit Claude sieht,
        # was Carlos sieht - Leben ueber den Koepfen, wer im Kampf ist, die Welle (Carlos, 26.09.)
        self._bildschirme: deque[tuple[float, bytes]] = deque(maxlen=12)
        self._ereignisse: list[tuple] = []
        self._schloss = threading.Lock()
        self._halt = threading.Event()

    def run(self) -> None:
        import gzip
        import json
        from . import bild
        kamera = _Kamera()
        verfolger = None
        from .welle import Wellenleser
        wellenleser = Wellenleser()
        from .platten import Plattenleser
        plattenleser, platten_bei, platten_gemeldet = Plattenleser(), 0.0, {}
        letzte_sichtungen: list = []
        leser = None
        try:
            from .texterkennung import Leser
            leser = Leser()
        except Exception as e:
            self.fehler = f"Chat: {e}"
        self._spur_bild: tuple[float, np.ndarray] | None = None
        self._spur_signal = threading.Event()
        threading.Thread(target=self._spur_lauf, args=(leser,), daemon=True).start()
        letzte_spur = 0.0
        if self.ordner:   # fortgesetzte Partie: abgebrochene Protokolle erst saeubern, sonst ist das Angehaengte unlesbar
            from .aufzeichnung import gz_saeubern
            gz_saeubern(self.ordner / "sichtungen.jsonl.gz")
            gz_saeubern(self.ordner / "ereignisse.jsonl.gz")
        protokoll = gzip.open(self.ordner / "sichtungen.jsonl.gz", "at", encoding="utf-8") if self.ordner else None
        self._ereignis_datei = gzip.open(self.ordner / "ereignisse.jsonl.gz", "at", encoding="utf-8") if self.ordner else None
        gespeichert: list[Path] = []
        letztes_bild = letzter_chat = 0.0
        chat_zeilen: set[str] = set()
        try:
            while not self._halt.is_set():
                start = time.time()
                try:
                    f = bild.spielfenster()
                    if f and self.champions:
                        l, o, r, u = f
                        breite, hoehe = r - l, u - o
                        if verfolger is None or verfolger.champions != self.champions:
                            verfolger = minimap.Verfolger(list(self.champions), hoehe=hoehe)
                        kl, ko, kr, ku = minimap.kartenrechteck(breite, hoehe)
                        karte = kamera.hole((l + kl, o + ko, l + kr, o + ku))
                        ergebnis = verfolger.bild(karte, start) if karte is not None else None
                        if ergebnis is not None:
                            sichtungen, spruenge = ergebnis
                            letzte_sichtungen = sichtungen
                            self.aktuell = (start, sichtungen)   # fuer das Dashboard (15/s statt 1/s)
                            with self._schloss:
                                self._neu.append((start, sichtungen))
                                self._ereignisse += [("sprung", s) for s in spruenge]
                            if protokoll:
                                protokoll.write(json.dumps({"w": round(start, 3), "s": [
                                    # Guete dazu: 0 = unter einem Icon mitgefuehrt (erschlossen), nicht gesehen -
                                    # ohne sie hielt die Nachpruefung erschlossene Stellen fuer Fehlerkennungen
                                    [s.champion_id, s.team, round(s.x, 4), round(s.y, 4), round(s.guete, 2)]
                                    for s in sichtungen]}) + "\n")
                                if start - getattr(self, "_gesichert", 0.0) >= 2.0:
                                    # Fenster zu = nichts verloren (Partie 4/5: Coach geschlossen, Protokoll-Ende fehlte)
                                    self._gesichert = start
                                    protokoll.flush()
                            if self.ordner and start - letztes_bild >= self.bild_alle:
                                letztes_bild = start
                                ziel = self.ordner / f"{int(start * 1000)}.jpg"
                                cv2.imwrite(str(ziel), karte, [cv2.IMWRITE_JPEG_QUALITY, 85])
                                gespeichert.append(ziel)
                                while gespeichert and int(gespeichert[0].stem) / 1000 < start - BILDER_BEHALTEN:
                                    gespeichert.pop(0).unlink(missing_ok=True)
                            self.anzahl += 1
                        if start - letzte_spur >= SPUR_ALLE and not self._spur_signal.is_set():
                            letzte_spur = start
                            try:
                                spiel = kamera.hole((l, o, r, u))
                                if spiel is not None:
                                    self._spur_bild = (start, cv2.resize(
                                        spiel, (BILDSCHIRM_BREITE, round(BILDSCHIRM_BREITE * hoehe / breite)),
                                        interpolation=cv2.INTER_AREA))
                                    self._spur_signal.set()
                            except Exception as e:
                                self.fehler = f"Spur: {type(e).__name__}: {e}"
                        if start - letzter_chat >= 1.0:  # Chat, Mitspieler-Leiste, Bildschirm einmal je Sekunde
                            letzter_chat = start
                            try:   # eigener Schutz: ein Fehler hier darf Chat und Leiste nicht mitreissen
                                ganz = kamera.hole((l, o, r, u))
                                if ganz is not None:
                                    if (eig := hud.eigene(ganz)) is not None:   # Q W E R D F bereit?
                                        with self._schloss:
                                            self._ereignisse.append(("eigene", start, eig))
                                    klein = cv2.resize(ganz, (BILDSCHIRM_BREITE, round(BILDSCHIRM_BREITE * hoehe / breite)),
                                                       interpolation=cv2.INTER_AREA)
                                    self._balken_pruefen(start, klein, leser)
                                    ok, jpg = cv2.imencode(".jpg", klein, [cv2.IMWRITE_JPEG_QUALITY, 70])
                                    if ok:
                                        self._bildschirme.append((start, jpg.tobytes()))
                                        # alle SCHIRM_ALLE s eins auf die Platte: Material fuers Review
                                        if self.ordner and start - getattr(self, "_schirm_gesichert", 0.0) >= SCHIRM_ALLE:
                                            self._schirm_gesichert = start
                                            self._schirm_schreiben(start, jpg.tobytes())
                            except Exception as e:
                                self.fehler = f"Bildschirm: {type(e).__name__}: {e}"
                            hx0, hy0, hx1, hy1 = hud.bereich(breite, hoehe)
                            leiste = kamera.hole((l + hx0, o + hy0, l + hx1, o + hy1))
                            if leiste is not None:
                                with self._schloss:
                                    self._ereignisse.append(("hud", start, hud.lies(leiste, hoehe)))
                            if karte is not None and start - platten_bei >= 2.0:
                                platten_bei = start
                                stand = plattenleser.lies_karte(karte)
                                if stand != platten_gemeldet:
                                    platten_gemeldet = stand
                                    with self._schloss:
                                        self._ereignisse.append(("platten", start, stand))
                            if karte is not None:
                                punkte = wellenleser.punkte(karte, [(s.x, s.y) for s in letzte_sichtungen])
                                if wellenleser.bereit:
                                    with self._schloss:
                                        self._ereignisse.append(("wellen", start, punkte))
                        if leser and letzter_chat == start:
                            a, b, c, d = CHAT
                            box = (l + int(a * breite), o + int(b * hoehe), l + int(c * breite), o + int(d * hoehe))
                            chatbild = kamera.hole(box)
                            if chatbild is not None:
                                neue = [z for z in leser.zeilen(chatbild) if z not in chat_zeilen and len(z) > 3]
                                if neue:
                                    chat_zeilen.update(neue)
                                    with self._schloss:
                                        self._ereignisse += [("chat", start, z) for z in neue]
                                    if self.ordner:  # Material zum Eichen des Chat-Lesers
                                        cv2.imwrite(str(self.ordner / f"chat_{int(start * 1000)}.jpg"), chatbild,
                                                    [cv2.IMWRITE_JPEG_QUALITY, 80])
                except Exception as e:  # ein Bild weniger, nie die Partie verlieren
                    self.fehler = f"{type(e).__name__}: {e}"
                dauer = time.time() - start
                self.messung.append(dauer)
                del self.messung[:-300]
                self._halt.wait(max(0.0, self.takt - dauer))
        finally:
            if protokoll:
                protokoll.close()
            if self._ereignis_datei:
                self._ereignis_datei.close()

    def _spur_lauf(self, leser) -> None:
        """Arbeits-Thread der Balkenspur (lebensbalken.Balkenspur): ~12 Spielbilder/s, Balken finden (~13 ms),
        Spruenge pruefen; bei einem Sprung die Namen am Absprung (Bild davor) und am Landepunkt lesen. Die Spur
        selbst geht ins Protokoll - Material, um die Erkennung nach einer Partie nachzupruefen."""
        from collections import deque
        from . import lebensbalken
        spur = lebensbalken.Balkenspur()
        bilder: deque = deque(maxlen=4)
        while not self._halt.is_set():
            if not self._spur_signal.wait(0.5):
                continue
            t, klein = self._spur_bild
            self._spur_signal.clear()
            try:
                balken = lebensbalken.finde(klein)
                bilder.append((t, klein))
                spruenge = spur.neu(t, balken, klein.shape[1])
                with self._schloss:
                    self._ereignisse.append(("balkenspur", t, [[b.x, b.y, b.team, b.anteil] for b in balken]))
                for s in spruenge:
                    davor = next((k for zt, k in reversed(bilder) if zt < s.zeit), None)
                    landung = next((k for zt, k in bilder if zt >= s.zeit), klein)
                    name_von = name_nach = ""
                    if leser is not None:
                        b_von = lebensbalken.Balken(s.von[0], s.von[1], s.anteil, s.team)
                        b_nach = lebensbalken.Balken(s.nach[0], s.nach[1], s.anteil, s.team)
                        if davor is not None:
                            name_von = lebensbalken.namen_lesen(davor, [b_von], leser)[0][1]
                        name_nach = lebensbalken.namen_lesen(landung, [b_nach], leser)[0][1]
                    with self._schloss:
                        self._ereignisse.append(("schirm_sprung", s.zeit, [s.team, s.anteil, *s.von, *s.nach, s.weite,
                                                                          name_von, name_nach]))
            except Exception as e:
                self.fehler = f"Spur: {type(e).__name__}: {e}"

    def _balken_pruefen(self, start: float, klein, leser) -> None:
        """Gegnerische Lebensbalken im Spielbild finden (schnell, hier) und ihre Namen lesen (Texterkennung,
        ~50 ms je Balken - im eigenen Faden, damit die Minimap mit 60 Bildern/s nicht stockt)."""
        from . import lebensbalken
        try:
            feind = [b for b in lebensbalken.finde(klein) if b.team == "feind"][:3]
        except Exception as e:
            self.fehler = f"Balken: {e}"
            return
        if not feind or leser is None or getattr(self, "_balken_laeuft", False):
            return
        self._balken_laeuft = True

        def lauf():
            try:
                gelesen = lebensbalken.namen_lesen(klein, feind, leser)
                with self._schloss:
                    self._ereignisse.append(("balken", start, [(t, b.anteil, b.team, lebensbalken.mana(klein, b))
                                                               for b, t in gelesen]))
            except Exception as e:
                self.fehler = f"Balken-Namen: {e}"
            finally:
                self._balken_laeuft = False
        threading.Thread(target=lauf, daemon=True).start()

    def _schirm_schreiben(self, wand: float, jpg: bytes) -> None:
        ziel = self.ordner / f"schirm_{int(wand * 1000)}.jpg"
        if not ziel.exists():
            ziel.write_bytes(jpg)

    def puffer_sichern(self) -> None:
        """Alle Bildschirme der letzten 12 s auf die Platte - beim Tod: die Sekunden davor, jede einzeln
        (Carlos: 'Momente notieren, die du durch Screenshot siehst')."""
        if self.ordner:
            for wand, jpg in list(self._bildschirme):
                self._schirm_schreiben(wand, jpg)

    def bildschirm(self, vor: float = 0.0) -> bytes | None:
        """Der Spielbildschirm (JPEG) etwa `vor` Sekunden vor jetzt - None, wenn keiner da ist
        oder der naechste mehr als 2 s daneben liegt (z. B. Spiel minimiert)."""
        ziel = time.time() - vor
        bilder = list(self._bildschirme)
        if not bilder:
            return None
        w, jpg = min(bilder, key=lambda b: abs(b[0] - ziel))
        return jpg if abs(w - ziel) <= 2.0 else None

    def abholen(self) -> list[tuple[float, list[minimap.Sichtung]]]:
        with self._schloss:
            neu, self._neu = self._neu, []
        return neu

    def ereignisse(self) -> list[tuple]:
        with self._schloss:
            neu, self._ereignisse = self._ereignisse, []
        if getattr(self, "_ereignis_datei", None) and not self._ereignis_datei.closed:
            for e in neu:
                try:
                    self._ereignis_datei.write(json.dumps(ereignis_als_json(e), ensure_ascii=False, default=str) + "\n")
                except (TypeError, ValueError, OSError) as f:
                    self.fehler = f"Protokoll: {f}"
            try:
                self._ereignis_datei.flush()
            except OSError:
                pass
        return neu

    def halt(self) -> None:
        self._halt.set()
        self.join(timeout=3)


# --- Nachspielen: Sichtungen aus dem Bilderordner ----------------------------------

def karte_aus_bild(pfad: Path, hoehe: int = minimap.REFERENZ_HOEHE) -> np.ndarray | None:
    """Neue Aufnahmen speichern genau die Minimap; die ersten (26.09.2026,
    12:00) die ganze Ecke - daraus wird die Minimap herausgeschnitten."""
    bild = cv2.imread(str(pfad))
    if bild is None:
        return None
    s = round(minimap.KARTE * hoehe)
    if abs(bild.shape[0] - s) <= 2:
        return bild
    ecke = bild.shape[0]
    x0 = ecke - round(minimap.RAND_RECHTS * hoehe) - s
    y0 = ecke - round(minimap.RAND_UNTEN * hoehe) - s
    return bild[y0:y0 + s, x0:x0 + s]


class SichtAusProtokoll:
    """Nachspielen aus dem Protokoll des Beobachters: jede Position (15/s) und
    jedes Ereignis (Spruenge, Chat, Mitspieler-Leiste) - genau was live ankam."""

    def __init__(self, ordner: Path):
        import gzip
        self.bilder = []  # fuer die Anzeige "Minimap: n Bilder"
        self._s = []
        with gzip.open(ordner / "sichtungen.jsonl.gz", "rt", encoding="utf-8") as f:
            try:
                for zeile in f:
                    try:
                        d = json.loads(zeile)
                    except json.JSONDecodeError:
                        continue
                    self._s.append((d["w"], [minimap.Sichtung(c, t, x, y, float(rest[0]) if rest else 1.0)
                                             for c, t, x, y, *rest in d["s"]]))
            except EOFError:
                pass
        self._e = []
        pfad = ordner / "ereignisse.jsonl.gz"
        if pfad.exists():
            with gzip.open(pfad, "rt", encoding="utf-8") as f:
                try:
                    for zeile in f:
                        try:
                            self._e.append(ereignis_aus_json(json.loads(zeile)))
                        except (json.JSONDecodeError, KeyError, TypeError):
                            continue
                except EOFError:
                    pass
        if not any(e[0] == "platten" for e in self._e):
            self._e += _platten_aus_bildern(ordner)
        self._e.sort(key=lambda e: e[1].zeit if e[0] == "sprung" else e[1])
        self.bilder = self._s
        self.i = self.j = 0
        self._bis = -1e18

    def zwischen(self, bis: float, champions_=None):
        aus = []
        while self.i < len(self._s) and self._s[self.i][0] <= bis:
            aus.append(self._s[self.i])
            self.i += 1
        self._bis = bis
        return aus

    def ereignisse(self) -> list:
        aus = []
        while self.j < len(self._e):
            e = self._e[self.j]
            w = e[1].zeit if e[0] == "sprung" else e[1]
            if w > self._bis:
                break
            aus.append(e)
            self.j += 1
        return aus


def _platten_aus_bildern(ordner: Path, jedes: int = 3) -> list[tuple]:
    """Platten-Ereignisse aus den gespeicherten Minimap-Bildern (Wanduhr = Dateiname in ms)."""
    from .platten import Plattenleser
    leser, gemeldet, aus = Plattenleser(), {}, []
    for pfad in sorted(ordner.glob("[0-9]*.jpg"))[::jedes]:
        karte = cv2.imread(str(pfad))
        if karte is None or karte.shape[0] != karte.shape[1] or karte.shape[0] > 700:
            continue   # alte Aufnahmen mit Rand um die Karte (Partie 1: 907 px) - dort stimmt die Lage nicht
        stand = leser.lies_karte(karte)
        if stand != gemeldet:
            gemeldet = stand
            aus.append(("platten", int(pfad.stem) / 1000, stand))
    return aus


def sicht_fuer(pfad):
    """Sichtungen einer Aufnahme: aus dem Protokoll (live mitgeschrieben, am
    dichtesten), aus den Bildern, oder - wenn die schon aufgeraeumt sind - aus der
    gespeicherten sichtungen.json."""
    from . import aufzeichnung
    ordner = Path(pfad).with_name(Path(pfad).name.removesuffix(".jsonl.gz") + "_bilder")
    if (ordner / "sichtungen.jsonl.gz").exists():
        return SichtAusProtokoll(ordner)
    if bilder := aufzeichnung.bilder(pfad):
        return SichtAusBildern(bilder)
    ordner = Path(pfad).with_name(Path(pfad).name.removesuffix(".jsonl.gz") + "_bilder")
    if (ordner / "sichtungen.json").exists():
        return SichtAusBildern.aus_cache(ordner)
    return None


def bilder_aufraeumen(behalte: int = 3) -> float:
    """Minimap-Bilder brauchen 120-180 MB je Partie. Nach der Auswertung reicht
    `sichtungen.json` (~1 MB) zum Nachspielen. Die Bilder der letzten `behalte`
    Partien bleiben (fuer neue Erkennungsstaende), aelteren bleibt nur die
    Sichtungsdatei. Gibt die freigegebenen MB zurueck."""
    from . import aufzeichnung, zustand
    aufnahmen = sorted(aufzeichnung.ORDNER.glob("*.jsonl.gz"))
    frei = 0.0
    for pfad in aufnahmen[:-behalte] if behalte else aufnahmen:
        bilder = aufzeichnung.bilder(pfad)
        if not bilder:
            continue
        protokoll = pfad.with_name(pfad.name.removesuffix(".jsonl.gz") + "_bilder") / "sichtungen.jsonl.gz"
        if protokoll.exists():
            # neue Partien: das Minimap-Protokoll (15-60/s) hat alles - die Bilder werden nicht mehr gebraucht.
            # Spielbildschirme (schirm_*) und Chat-Bilder bleiben fuers Review.
            for _, b in bilder:
                frei += b.stat().st_size
                b.unlink()
            continue
        champions_ = next((champions(p) for p in map(zustand.partie, aufzeichnung.lies(pfad)) if p.spieler), None)
        if not champions_:
            continue
        sicht = SichtAusBildern(bilder)
        sicht._berechne(champions_)  # stellt sicher, dass sichtungen.json vollstaendig ist
        if len(sicht._ergebnis or {}) < len(bilder):
            continue
        for _, b in bilder:
            frei += b.stat().st_size
            b.unlink()
    return frei / 1e6


class SichtAusBildern:
    """Liefert fuer ein Wanduhr-Intervall die Sichtungen aus den gespeicherten Bildern.

    Die Erkennung laeuft beim ersten Mal parallel ueber alle Bilder und wird
    als `sichtungen.json` im Bilderordner abgelegt - danach dauert ein
    Nachspielen Sekunden. Der Cache haengt an Champions und Erkennungsstand
    (`minimap.STAND`); aendert sich eins, wird neu gerechnet."""

    def __init__(self, bilder: list[tuple[float, Path]]):
        self.bilder = bilder
        self.i = 0
        self._ergebnis: dict[str, list[minimap.Sichtung]] | None = None

    @classmethod
    def aus_cache(cls, ordner: Path) -> "SichtAusBildern":
        """Nur aus `sichtungen.json`, ohne Bilder (Testfaelle)."""
        import json
        namen = json.loads((ordner / "sichtungen.json").read_text(encoding="utf-8"))["bilder"]
        return cls(sorted((int(n.removesuffix(".jpg")) / 1000, ordner / n) for n in namen))

    def _berechne(self, champions_: list[tuple[str, str]]) -> None:
        import json
        from concurrent.futures import ThreadPoolExecutor
        from dataclasses import asdict
        cache = self.bilder[0][1].parent / "sichtungen.json" if self.bilder else None
        kennung = {"stand": minimap.STAND, "champions": sorted(map(list, champions_))}
        self._ergebnis = {}
        if cache and cache.exists():
            gespeichert = json.loads(cache.read_text(encoding="utf-8"))
            alt = {k: [minimap.Sichtung(**s) for s in v] for k, v in gespeichert["bilder"].items()}
            if gespeichert.get("kennung") == kennung:
                self._ergebnis = alt
            else:
                # Neuer Erkennungsstand: neu rechnen - aber nur, wo das Bild noch da ist. Sonst gilt das Alte
                # (vorher: leer gerechnet und die Datei damit ueberschrieben - Testpartie 2 verlor so alles)
                self._ergebnis = {k: v for k, v in alt.items() if not (self.bilder[0][1].parent / k).exists()}
        fehlend = [p for _, p in self.bilder if p.name not in self._ergebnis and p.exists()]
        if not fehlend:
            return

        def eins(pfad: Path):
            karte = karte_aus_bild(pfad)
            return pfad.name, ([] if karte is None else minimap.finde(karte, champions_))

        with ThreadPoolExecutor() as pool:
            self._ergebnis.update(pool.map(eins, fehlend))
        if cache:
            cache.write_text(json.dumps({"kennung": kennung, "bilder": {
                k: [asdict(s) for s in v] for k, v in self._ergebnis.items()}}), encoding="utf-8")

    def ereignisse(self) -> list:
        aus, self._offen = getattr(self, "_offen", []), []
        return aus

    def _wellen_berechnen(self) -> None:
        """Wellen je Bild (der Reihe nach - die Icon-Maske lernt ueber die Zeit); im Cache
        neben den Sichtungen. Ohne Bilder (nur sichtungen.json) gibt es keine Wellen."""
        import json
        from .welle import Wellenleser
        cache = self.bilder[0][1].parent / "wellen.json" if self.bilder else None
        if cache and cache.exists():
            self._wellen = json.loads(cache.read_text(encoding="utf-8"))
            return
        self._wellen = {}
        if not self.bilder or not self.bilder[0][1].exists():
            return
        leser = Wellenleser()
        for _, pfad in self.bilder:
            karte = karte_aus_bild(pfad)
            if karte is None:
                continue
            champs = [(s.x, s.y) for s in (self._ergebnis or {}).get(pfad.name, [])]
            punkte = leser.punkte(karte, champs)
            if leser.bereit:
                self._wellen[pfad.name] = [[t, round(x, 4), round(y, 4)] for t, x, y in punkte]
        cache.write_text(json.dumps(self._wellen), encoding="utf-8")

    def zwischen(self, bis: float, champions_: list[tuple[str, str]]) -> list[tuple[float, list[minimap.Sichtung]]]:
        if self._ergebnis is None and champions_:
            self._berechne(champions_)
            self._wellen_berechnen()
        aus = []
        while self.i < len(self.bilder) and self.bilder[self.i][0] <= bis:
            w, pfad = self.bilder[self.i]
            self.i += 1
            if self._ergebnis is not None:
                aus.append((w, self._ergebnis.get(pfad.name, [])))
            if (punkte := getattr(self, "_wellen", {}).get(pfad.name)) is not None:
                self._offen = getattr(self, "_offen", []) + [("wellen", w, [tuple(q) for q in punkte])]
        return aus
