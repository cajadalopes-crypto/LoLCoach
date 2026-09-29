"""Lagebild: wer wurde zuletzt wo auf der Minimap gesehen.

Bilder kommen mit Wanduhrzeit (live vom Beobachter, im Nachspielen aus dem
Bilderordner einer Aufnahme). Der Aufrufer rechnet sie ueber den letzten
API-Schnappschuss in Spielzeit um - so laufen Live und Aufnahme gleich.
"""
from __future__ import annotations

import json
import os
import re
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
STILL_TOLERANZ = 0.02     # Minimap-Anteile (x + y): so weit wackelt ein stehendes Icon
BRUNNEN_ZONE = 0.07       # ... um den Brunnenpunkt: wer hier bleibt, steht (das Icon springt am Kartenrand)
AFK_AB = 90.0             # Spielzeit: bis dahin hat jeder gekauft und den Brunnen verlassen
AFK_STILL_BASIS = 60.0    # Sekunden regungslos in der eigenen Basis (Mitspieler, Minimap)
AFK_STILL_DRAUSSEN = 120.0   # ... anderswo (ein Support wartet auch mal lange im Busch)


def afk(sp: Spieler, p: Partie, lagebild=None) -> str | None:
    """Ist `sp` AFK? Die Belege in Worten, sonst None. Live 27.09., 1:48: "Ist mein Nasus AFK?" - der Nasus-Bot
    stand seit Spielbeginn im Brunnen, Stufe 1, 0 CS; Claude las "Nasus Jungle" und sagte "er cleart im
    Dschungel". Belege nur aus Zahlen:
      - ein Mitspieler (Mensch) ohne ein einziges Item nach 1:30 (jeder kauft zu Beginn) - bei Bots nicht: der
        Fiddlesticks-Bot derselben Partie hatte auch keins und lief normal. Bei Gegnern nie: die Live-API zeigt ihre
        Items nicht (133930 Zac, 144655 Kha'Zix: "kein einziges Item", beide gankten; 144655, 1:30: "spiel deine Lane
        nach vorn", 1:57 tot), und Stufe und Items eines Gegners stehen dort nur so, wie er zuletzt gesehen wurde
        (Kha'Zix 144655: bis 3:34 "Stufe 1, 0 Items", im ersten Moment auf der Karte Stufe 4) - Gegner also gar nicht,
      - ein Mitspieler (auf der Minimap immer zu sehen) steht regungslos: 60 s in der Basis, 120 s anderswo."""
    if p.zeit < AFK_AB or (p.ich is not None and sp.name == p.ich.name):
        return None
    gruende = []
    if sp.team != p.mein_team:
        return None
    if not sp.bot and not sp.items:
        gruende.append(f"nach {int(p.zeit // 60)}:{int(p.zeit % 60):02d} kein einziges Item, nicht einmal Startitems")
    still = (lagebild.still_seit(sp, p.zeit) if lagebild is not None and hasattr(lagebild, "still_seit")
             and sp.team == p.mein_team and not sp.tot else None)
    if still is not None:
        g = lagebild.zuletzt.get((sp.name, sp.team))
        wo = minimap.ort(g[1], g[2], p.mein_team) if g else ""
        basis = g is not None and abs(g[1] - BRUNNEN[sp.team][0]) + abs(g[2] - BRUNNEN[sp.team][1]) <= 0.2
        if still >= (AFK_STILL_BASIS if basis else AFK_STILL_DRAUSSEN) or (gruende and still >= 20):
            gruende.append(f"steht seit {int(still)} s regungslos {wo}".rstrip())
    if not gruende:
        return None
    if p.zeit >= 120 and sp.level <= 1 and sp.cs == 0:
        gruende.append("Stufe 1, 0 CS")
    return ", ".join(gruende)
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
        self.quest: tuple[str, float, float] | None = None   # Auftrag 006, W2: (Zustand, seit, zuletzt gelesen) von V
        self._quest_kandidat: tuple[str, float] | None = None
        self.platten: dict[tuple[str, str, str], int] = {}   # (Team, Lane, Stufe) -> verbleibende Platten (Minimap)
        # Auftrag 018, 1: Objective-Symbole der Minimap, Grube ("oben"/"unten") -> (symbol/timer/leer, seit Spielzeit)
        self.gruben: dict[str, tuple[str, float]] = {}
        self.gegner_leben: dict[str, tuple[float, float]] = {}   # Spielername -> (Zeit, Leben 0..1) aus dem Spielbild
        self.gegner_mana: dict[str, tuple[float, float]] = {}    # ... (Zeit, Mana 0..1) aus dem Balken darunter
        self._tp_kandidat: dict[str, tuple] = {}     # Spielername -> (Zeit, x, y, zuletzt gesehen) eines Fernsprungs
        self._tode: dict[str, float] = {}            # Spielername -> zuletzt tot (Spielzeit)
        self._recall: dict[str, float] = {}          # Gegner -> Spielzeit, zu der er nach 7 s Stillstand verschwand
        self.fernspruenge: list = []                 # gemeldete TP/globale Ults (zauber.Timer)
        self._still: dict[str, tuple[float, float, float]] = {}   # Mitspieler -> (seit, x, y) ohne Bewegung (AFK)

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

    def _quest_lesen(self, zustand: str, zeit: float) -> None:
        """Auftrag 006, W2: ein Wechsel am Quest-Platz zaehlt erst, wenn ihn zwei Lesungen hintereinander zeigen (wie
        bei den Tasten) - ein offener Shop oder ein Effekt darf das Quest-Ende nicht vortaeuschen."""
        if self.quest is not None and self.quest[0] == zustand:
            self._quest_kandidat = None
            self.quest = (zustand, self.quest[1], zeit)
            return
        k = self._quest_kandidat
        if k is not None and k[0] == zustand:
            self.quest, self._quest_kandidat = (zustand, k[1], zeit), None
        else:
            self._quest_kandidat = (zustand, zeit)

    def eigene_faehigkeiten(self, jetzt: float) -> dict[str, bool] | None:
        """Q W E R bereit? (aus dem HUD, frisch)"""
        if self.eigene_zeit is None or jetzt - self.eigene_zeit > 3:
            return None
        return {t: self.eigene[t][0] for t in "QWER" if t in self.eigene}

    def ereignisse(self, zeit_von_wand, liste, p: Partie) -> list:
        """Spruenge und Chatzeilen des Beobachters -> Zauber-Timer. Gibt die neuen Timer zurueck."""
        from . import zauber
        neu = []
        blinks = zauber.dash_champions()      # Dash, Sprung, Blink, Teleport (Qualitaetsrunde 2, Weg 1)
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
                self.wellen = welle.zustaende(e[2], p.mein_team)     # Farben relativ: blau = dein Team
                self.wellen_zeit = zeit_von_wand(e[1])
            elif e[0] == "platten":
                self.platten.update(e[2])
            elif e[0] == "gruben":
                for g, z in e[2].items():
                    if self.gruben.get(g, ("",))[0] != z:
                        self.gruben[g] = (z, zeit_von_wand(e[1]))
            elif e[0] == "schirm_sprung":
                # Flash auf dem Spielbild (lebensbalken.Balkenspur): nur mit gelesenem Namen, und sind beide Namen
                # (Absprung, Landung) lesbar, muessen sie derselbe Spieler sein
                from .lebensbalken import zuordnen as balken_zuordnen
                team, anteil, x0, y0, x1, y1, weite, name_von, name_nach, *mehr = e[2]
                sp_von = balken_zuordnen(name_von, p.gegner()) if name_von else None
                sp_nach = balken_zuordnen(name_nach, p.gegner()) if name_nach else None
                sp = sp_nach or sp_von
                # Die Minimap weiss, wer im Bild sein kann (Kamerarahmen): ohne lesbaren Namen nennt sie ihn, mit
                # Namen muss er drin sein. Live 26.09. 23:06: zwei 'Spruenge' ohne Namen - im Rahmen stand nur
                # Graves, kein Gegner (zwei verschiedene rote Balken, kein Flash).
                rahmen, groesse = (mehr + [None, None])[:2]
                if rahmen and groesse:
                    im_bild = self._im_rahmen(p, rahmen, zeit_von_wand(e[1]))
                    if sp is not None and sp.name not in {s.name for s in im_bild}:
                        sp = None
                    elif sp is None and im_bild:
                        lx = rahmen[0] + x1 / groesse[0] * (rahmen[2] - rahmen[0])
                        ly = rahmen[1] + y1 / groesse[1] * (rahmen[3] - rahmen[1])
                        abst = sorted((abs(g[1] - lx) + abs(g[2] - ly), s.name, s) for s in im_bild
                                      if (g := self.gesehen(s)) is not None)
                        if abst and abst[0][0] <= 0.08 and (len(abst) == 1 or abst[1][0] - abst[0][0] >= 0.05):
                            sp = abst[0][2]
                # nur ohne eigenen Dash: Live 21:21, 9:18 sprangen Gragas und Tryndamere zugleich - ein Engage mit
                # beiden E, kein Flash. Bei Dash-Champions bleibt es beim Protokoll (zum Nachpruefen).
                if sp is not None and (sp_von is None or sp_nach is None or sp_von.name == sp_nach.name) \
                        and "SummonerFlash" in sp.zauber and sp.champion_id not in blinks and not sp.tot \
                        and sp.champion_id not in blinks:
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
            elif e[0] == "quest":
                self._quest_lesen(e[2], zeit_von_wand(e[1]))
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
        self._stillstand_merken(p)

    def _stillstand_merken(self, p: Partie) -> None:
        """Seit wann steht jeder Mitspieler auf derselben Stelle (lebend, auf der Minimap immer zu sehen)?"""
        if not p.mein_team:
            return
        for sp in p.team(p.mein_team):
            g = self.zuletzt.get((sp.name, sp.team))
            if sp.tot or g is None:
                self._still.pop(sp.name, None)
                continue
            a = self._still.get(sp.name)
            # im Brunnen liegt das Icon halb ueber dem Kartenrand und springt um ein paar Pixel (Nasus 27.09.:
            # 0.040/0.956 -> 0.025/0.968 -> 0.018/0.988, ohne einen Schritt) - dort zaehlt nur "noch im Brunnen"
            bx, by = BRUNNEN.get(sp.team, (9.0, 9.0))
            beide_im_brunnen = a is not None and all(abs(x - bx) + abs(y - by) <= BRUNNEN_ZONE
                                                     for x, y in ((g[1], g[2]), (a[1], a[2])))
            if a is None or (abs(g[1] - a[1]) + abs(g[2] - a[2]) > STILL_TOLERANZ and not beide_im_brunnen):
                self._still[sp.name] = g

    def still_seit(self, sp: Spieler, jetzt: float) -> float | None:
        """Sekunden, die ein Mitspieler schon regungslos steht (None: bewegt sich / unbekannt)."""
        a, g = self._still.get(sp.name), self.zuletzt.get((sp.name, sp.team))
        if a is None or g is None or jetzt - g[0] > 3.0:
            return None
        return g[0] - a[0]

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

    def _im_rahmen(self, p: Partie, rahmen, zeit: float, rand: float = 0.03) -> list[Spieler]:
        """Lebende Gegner, die auf der Minimap gerade im Kamerarahmen stehen (frisch gesehen, <= 1,5 s)."""
        aus = []
        for s in p.gegner():
            g = self.gesehen(s)
            if s.tot or g is None or zeit - g[0] > 1.5:
                continue
            if rahmen[0] - rand <= g[1] <= rahmen[2] + rand and rahmen[1] - rand <= g[2] <= rahmen[3] + rand:
                aus.append(s)
        return aus

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
    if not s.team:
        return None
    # die Ringfarbe ist relativ (blau = dein Team): auf der roten Seite heisst ein blauer Ring CHAOS
    team = s.team if p.mein_team != "CHAOS" else ("CHAOS" if s.team == "ORDER" else "ORDER")
    return next((sp for sp in kandidaten if sp.team == team), None)


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


def _dxcam_flicken() -> None:
    """dxcam 0.3.0 gibt seine COM-Objekte ein zweites Mal frei: `release()` ruft Release() von Hand, und das
    Python-Objekt haengt in einem Zyklus - der Garbage Collector ruft spaeter, in irgendeinem Faden, noch einmal
    Release() auf dem laengst zerstoerten Objekt auf (gemessen: nach release() + gc.collect() eine Referenz zu
    wenig). Jeder Wechsel der Ausschnittgroesse baut die Staging-Textur neu, und der Coach wechselte ~25-mal je
    Sekunde (Minimap, Spielbild, Leiste, Chat): 26./27.09.2026 viermal Zugriffsverletzung in _ctypes.pyd, Coach
    weg, ohne Traceback. Hier geben nur noch die comtypes-Zeiger selbst frei - genau einmal, wenn sie sterben."""
    from dxcam.core import dxgi_duplicator, stagesurf
    if getattr(stagesurf.StageSurface, "_geflickt", False):
        return

    def textur_los(self) -> None:
        if self.texture is not None:
            self.width = self.height = 0
            self.texture = None
            self.interface = None

    def duplikator_los(self) -> None:
        if self.duplicator is not None:
            self.release_frame()
            self.duplicator = None

    stagesurf.StageSurface.release = textur_los
    dxgi_duplicator.DXGIDuplicator.release = duplikator_los
    stagesurf.StageSurface._geflickt = True


class _Groesse:
    """Nur die Kante, die dxcams StageSurface beim Bau abfragt (`output.surface_size`)."""

    def __init__(self, groesse: tuple[int, int]):
        self.surface_size = groesse


def _gdi(box: tuple[int, int, int, int]) -> np.ndarray:
    """Genau der Ausschnitt per BitBlt (Minimap bei 7680 x 2160: 8 ms). PIL kopierte erst den ganzen Bildschirm und
    schnitt dann aus - 125 ms fuer jeden noch so kleinen Ausschnitt (Auftrag 007, C1, gemessen 28.09.2026)."""
    import win32con
    import win32gui
    import win32ui
    l, o, r, u = box
    b, h = r - l, u - o
    hdc = win32gui.GetDC(0)
    quelle = win32ui.CreateDCFromHandle(hdc)
    ziel = quelle.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    try:
        bmp.CreateCompatibleBitmap(quelle, b, h)
        ziel.SelectObject(bmp)
        ziel.BitBlt((0, 0), (b, h), quelle, (l, o), win32con.SRCCOPY)
        return np.frombuffer(bmp.GetBitmapBits(True), dtype=np.uint8).reshape(h, b, 4)[..., :3].copy()
    finally:
        ziel.DeleteDC()
        quelle.DeleteDC()
        win32gui.ReleaseDC(0, hdc)
        win32gui.DeleteObject(bmp.GetHandle())


class _Kamera:
    """Bildschirmausschnitte: Desktop-Duplizierung (dxcam, 2-5 ms), sonst GDI (nur der Ausschnitt).
    `LOLCOACH_KAMERA=gdi` erzwingt GDI - fuer die Generalprobe bei ausgeschaltetem Bildschirm: dann liefert die
    Duplizierung gar kein Bild (28.09.2026 gemessen: AcquireNextFrame nur Zeitueberschreitung), GDI schon."""

    def __init__(self):
        self._dx = None
        try:
            if os.environ.get("LOLCOACH_KAMERA", "").lower() != "gdi":
                import dxcam
                _dxcam_flicken()
                self._dx = dxcam.create(output_color="BGR")
        except Exception:
            self._dx = None
        self._letzt: dict[tuple, np.ndarray] = {}
        # je Ausschnittgroesse eine eigene Staging-Textur: dxcam baut sonst bei jedem Groessenwechsel neu
        # (ein 4K-Spielbild sind 33 MB, ~12-mal je Sekunde) - und jeder Neubau war ein Absturzlos (s. oben)
        self._flaechen: dict[tuple[int, int], object] = {}
        self._duplikator = None

    def hole(self, box: tuple[int, int, int, int]) -> np.ndarray | None:
        if self._dx is not None:
            try:
                dx = self._dx
                if dx._duplicator is not self._duplikator:   # neu aufgebaut (Alt-Tab, Aufloesung): Texturen weg
                    self._flaechen, self._duplikator = {}, dx._duplicator
                groesse = (box[2] - box[0], box[3] - box[1])
                if (f := self._flaechen.get(groesse)) is None:
                    # gleich in Ausschnittgroesse: StageSurface baut sonst erst den ganzen Bildschirm (7680 x 2160 =
                    # 66 MB je Ausschnittgroesse) und schrumpft erst mit dem naechsten NEUEN Bild - bei ruhigem
                    # Bildschirm nie (Auftrag 007, C3: der Kamera-Test fand (7680, 2160) statt (200, 100))
                    from dxcam.core.stagesurf import StageSurface
                    f = self._flaechen[groesse] = StageSurface(output=_Groesse(groesse), device=dx._device)
                dx._stagesurf = f      # passt schon; dxcam baut nur bei gedrehtem Bildschirm noch einmal um
                bild = dx.grab(region=box)
                if bild is None:          # Bildschirm unveraendert seit dem letzten Mal
                    return self._letzt.get(box)
                self._letzt[box] = bild
                return bild
            except Exception:
                self._dx = None           # z. B. anderer Monitor: auf GDI ausweichen
        return _gdi(box)


# Chat unten links, grosszuegig (Anteil des Spielfensters) - genau geeicht wird an einer Partie.
# Chat-Fenster (Anteile des Spielfensters), geeicht an Partie 4 und 5 (4K): mit Unterkante 0.90 lag die
# NEUESTE Zeile immer knapp darunter (~0.91) - ein Ping wurde erst lesbar, wenn die naechste Nachricht ihn
# hochschob (Partie 5: 5:03 gepingt, 6:01 gelesen). Unten 0.95 (Eingabezeile), oben 0.70 (darueber nur
# Spielwelt mit Namensschildern als Rauschen).
CHAT = (0.0, 0.70, 0.32, 0.95)
BILDSCHIRM_BREITE = 1600   # fuer Claude: Lebensbalken und Namen noch lesbar, ~150 KB je Bild
SCHIRM_ALLE = 5.0          # Sekunden: so oft ein Spielbild auf die Platte (Review), ~45 MB je 30-min-Partie
SPUR_ALLE = 0.08           # Sekunden: so oft sucht die Balkenspur Flash-Spruenge auf dem Spielbild (~12/s)
# Spielbild = die Mitte im Seitenverhaeltnis 16:9 (Auftrag 007, C2). Auf Carlos' 7680 x 2160 (randlos = ganzer
# Schirm) kopierte der Beobachter 12-mal je Sekunde 66 MB und stauchte sie auf 1600 x 450: Lebensbalken halb so hoch
# wie vermessen (lebensbalken rechnet mit der Bildbreite) - die Balkenspur waere blind gewesen. Die Mitte hat den
# Massstab von 4K, und Q W E R D F sitzen dort wie immer (hud.eigene rechnet von der Mitte aus).
SPIELBILD_SEITEN = 16 / 9

# Flash-Clips (Auftrag 007, A6, Stufe 1: nur sammeln): nach jedem Sprung (Balkenspur, Minimap) und jedem Chat-Ping
# "Blitz"/"Flash" 1,5 s Spielbild rund um den Anlass nach aufnahmen/<stamm>_flashclips/<Wanduhr ms>_<anlass>/.
# Die Erkennung baut erst jemand, wenn 20 echte Clips da sind.
CLIP_VOR = 1.0             # Sekunden Spielbild vor dem Anlass (der Sprung selbst liegt meist davor: Bestaetigung, Chat)
CLIP_NACH = 0.5            # ... und danach
CLIP_RING = 2.5            # Sekunden Spurbilder im Speicher (~30 Bilder, ~35 MB): ein Anlass darf 1,5 s spaet kommen
CLIP_BREITE = 800          # px: halbe Spurbreite, JPEG ~40 KB je Bild
CLIP_QUALITAET = 70
CLIP_WORTE = re.compile(r"blitz|flash", re.IGNORECASE)    # Chat-Ping (zauber.WOERTER)
# Sekunden: aeltere Minimap-Bilder der laufenden Partie werden entfernt. Bis 27.09. 20 min - dann war die Lane-Phase
# einer 35-min-Partie weg, bevor man die Welle daran eichen konnte (Buch 1, 1.4). Jetzt die ganze Partie; aufgeraeumt
# wird nach der Partie (bilder_aufraeumen: alles ausser den letzten drei Partien).
BILDER_BEHALTEN = 90 * 60


def spielbild(breite: int, hoehe: int) -> tuple[int, int]:
    """(links, Breite) des Spielbilds im Fenster: die Mitte in SPIELBILD_SEITEN, schmalere Fenster ganz."""
    b = min(breite, round(hoehe * SPIELBILD_SEITEN))
    return (breite - b) // 2, b


class FlashClips:
    """Ringpuffer der Spurbilder (~12/s) und je Anlass ein Clip von CLIP_VOR bis CLIP_NACH um ihn. Geschrieben wird
    im Hintergrund, der Takt wartet nie; Anlaesse naeher als CLIP_NACH beieinander werden ein Clip."""

    def __init__(self, ordner: Path | None):
        self.ordner = ordner
        self._ring: deque[tuple[float, np.ndarray]] = deque()
        self._offen: list[list] = []          # [Zeit, [[Anlass, Text], ...]]
        self._fertig: deque[float] = deque(maxlen=8)
        self._schloss = threading.Lock()
        self.geschrieben = 0

    def anlass(self, art: str, zeit: float, text: str = "") -> None:
        if self.ordner is None:
            return
        with self._schloss:
            if any(abs(z - zeit) <= CLIP_NACH for z in self._fertig):
                return
            for o in self._offen:
                if abs(o[0] - zeit) <= CLIP_NACH:
                    o[1].append([art, text])
                    return
            self._offen.append([zeit, [[art, text]]])

    def bild(self, t: float, klein: np.ndarray) -> None:
        """Ein Spurbild (aus dem Faden der Balkenspur) - schliesst Clips ab, deren Nachlauf jetzt da ist."""
        if self.ordner is None:
            return
        h, b = klein.shape[:2]
        self._ring.append((t, cv2.resize(klein, (CLIP_BREITE, round(CLIP_BREITE * h / b)),
                                         interpolation=cv2.INTER_AREA)))
        while self._ring and self._ring[0][0] < t - CLIP_RING:
            self._ring.popleft()
        self._abschliessen(lambda o: t >= o[0] + CLIP_NACH)

    def alle_abschliessen(self) -> None:
        """Beim Beenden: offene Clips mit dem, was da ist."""
        self._abschliessen(lambda o: True)

    def _abschliessen(self, reif) -> None:
        with self._schloss:
            fertig = [o for o in self._offen if reif(o)]
            self._offen = [o for o in self._offen if not reif(o)]
            self._fertig.extend(o[0] for o in fertig)
        for zeit, anlaesse in fertig:
            bilder = [(bt, bb) for bt, bb in list(self._ring) if zeit - CLIP_VOR <= bt <= zeit + CLIP_NACH]
            if bilder:
                threading.Thread(target=self._schreiben, args=(zeit, anlaesse, bilder), daemon=True).start()

    def _schreiben(self, zeit: float, anlaesse: list, bilder: list) -> None:
        try:
            ziel = self.ordner / f"{int(zeit * 1000)}_{anlaesse[0][0]}"
            ziel.mkdir(parents=True, exist_ok=True)
            for bt, bb in bilder:
                cv2.imwrite(str(ziel / f"{int(bt * 1000)}.jpg"), bb, [cv2.IMWRITE_JPEG_QUALITY, CLIP_QUALITAET])
            (ziel / "anlass.json").write_text(json.dumps(
                {"w": round(zeit, 3), "anlass": anlaesse, "bilder": [round(bt - zeit, 3) for bt, _ in bilder]},
                ensure_ascii=False), encoding="utf-8")
            self.geschrieben += 1
        except OSError:
            pass


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
        # weckt den Kern sofort (statt nach bis zu 0,25 s Takt): ein Sprung (Flash) oder ein Gegner, der neben dir
        # neu auftaucht - die zwei Momente, in denen jede Zehntelsekunde zaehlt
        self.wecker = threading.Event()
        self._geweckt = 0.0

    def _wecken(self, zeit: float, sichtungen: list, vorher: list, spruenge: list) -> None:
        if zeit - self._geweckt < 0.1:
            return
        neu_nah = False
        ich, zuletzt = getattr(self, "ich", None), getattr(self, "_ich_zuletzt", None)
        if ich and zuletzt and zeit - zuletzt[0] < 2:
            feinde = {c for c, t in self.champions if t != ich[1]}
            vorher_ids = {s.champion_id for s in vorher}
            neu_nah = any(s.champion_id in feinde and s.champion_id not in vorher_ids and s.guete > 0
                          and abs(s.x - zuletzt[1]) + abs(s.y - zuletzt[2]) < 0.15 for s in sichtungen)
        if spruenge or neu_nah:
            self._geweckt = zeit
            self.wecker.set()

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
        from .objsymbole import Grubenleser
        grubenleser, gruben_bei = Grubenleser(), 0.0
        letzte_sichtungen: list = []
        leser = None
        try:
            from .texterkennung import Leser
            leser = Leser()
        except Exception as e:
            self.fehler = f"Chat: {e}"
        self._spur_bild: tuple[float, np.ndarray] | None = None
        self._spur_signal = threading.Event()
        self.clips = FlashClips(self.ordner.with_name(self.ordner.name.removesuffix("_bilder") + "_flashclips")
                                if self.ordner else None)
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
        blitz_pings: set[str] = set()     # Chat-Zeitstempel, zu denen schon ein Clip laeuft
        try:
            while not self._halt.is_set():
                start = time.time()
                try:
                    f = bild.spielfenster()
                    if f and self.champions:
                        l, o, r, u = f
                        breite, hoehe = r - l, u - o
                        ml, mb = spielbild(breite, hoehe)       # Spielbild: die 16:9-Mitte (32:9-Schirm)
                        mitte = (l + ml, o, l + ml + mb, u)
                        self._mitte_anteil = (ml / breite, (ml + mb) / breite)
                        k = minimap.faktor()     # Minimap-Groesse aus der game.cfg (nur gelesen, stat alle 2 s)
                        if verfolger is None or verfolger.champions != self.champions:
                            verfolger = minimap.Verfolger(list(self.champions), hoehe=round(hoehe * k))
                        verfolger.eigenes_team = (getattr(self, "ich", None) or (None, None))[1]
                        kl, ko, kr, ku = minimap.kartenrechteck(breite, hoehe, k)
                        karte = kamera.hole((l + kl, o + ko, l + kr, o + ku))
                        self._letzte_karte = karte          # fuer die Balkenspur: wer ist gerade im Bild?
                        ergebnis = verfolger.bild(karte, start) if karte is not None else None
                        if ergebnis is not None:
                            sichtungen, spruenge = ergebnis
                            sichtungen = self._ich_ergaenzen(karte, start, sichtungen)
                            self._wecken(start, sichtungen, letzte_sichtungen, spruenge)
                            letzte_sichtungen = sichtungen
                            self.aktuell = (start, sichtungen)   # fuer das Dashboard (15/s statt 1/s)
                            with self._schloss:
                                self._neu.append((start, sichtungen))
                                self._ereignisse += [("sprung", s) for s in spruenge]
                            for s in spruenge:
                                self.clips.anlass("minimap", s.zeit, s.champion_id)
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
                                spiel = kamera.hole(mitte)
                                if spiel is not None:
                                    self._spur_bild = (start, cv2.resize(
                                        spiel, (BILDSCHIRM_BREITE, round(BILDSCHIRM_BREITE * hoehe / mb)),
                                        interpolation=cv2.INTER_AREA))
                                    self._spur_signal.set()
                            except Exception as e:
                                self.fehler = f"Spur: {type(e).__name__}: {e}"
                        if start - letzter_chat >= 1.0:  # Chat, Mitspieler-Leiste, Bildschirm einmal je Sekunde
                            letzter_chat = start
                            try:   # eigener Schutz: ein Fehler hier darf Chat und Leiste nicht mitreissen
                                ganz = kamera.hole(mitte)
                                if ganz is not None:
                                    if (eig := hud.eigene(ganz)) is not None:   # Q W E R D F bereit?
                                        with self._schloss:
                                            self._ereignisse.append(("eigene", start, eig))
                                        if (q := hud.quest(ganz)) is not None:   # Auftrag 006, W2: nur lesen
                                            with self._schloss:
                                                self._ereignisse.append(("quest", start, q))
                                    klein = cv2.resize(ganz, (BILDSCHIRM_BREITE, round(BILDSCHIRM_BREITE * hoehe / mb)),
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
                            hx0, hy0, hx1, hy1 = hud.bereich(breite, hoehe, k)
                            leiste = kamera.hole((l + hx0, o + hy0, l + hx1, o + hy1))
                            if leiste is not None:
                                with self._schloss:
                                    self._ereignisse.append(("hud", start, hud.lies(leiste, hoehe, k)))
                            if karte is not None and start - platten_bei >= 2.0:
                                platten_bei = start
                                stand = plattenleser.lies_karte(
                                    karte, mein_team=(getattr(self, "ich", None) or (None, None))[1] or "ORDER")
                                if stand != platten_gemeldet:
                                    platten_gemeldet = stand
                                    with self._schloss:
                                        self._ereignisse.append(("platten", start, stand))
                            if karte is not None and start - gruben_bei >= 1.0:
                                gruben_bei = start
                                if (stand := grubenleser.lies_bgr(karte)) is not None:
                                    with self._schloss:
                                        self._ereignisse.append(("gruben", start, stand))
                            if karte is not None:
                                punkte = wellenleser.punkte(karte, [(s.x, s.y) for s in letzte_sichtungen])
                                if wellenleser.bereit:
                                    with self._schloss:
                                        self._ereignisse.append(("wellen", start, punkte))
                        if leser and letzter_chat == start:
                            a, b, c, d = CHAT   # Breite in 16:9-Einheiten: der Chat klebt am linken Rand (32:9)
                            box = (l + int(a * mb), o + int(b * hoehe), l + int(c * mb), o + int(d * hoehe))
                            chatbild = kamera.hole(box)
                            if chatbild is not None:
                                neue = [z for z in leser.zeilen(chatbild) if z not in chat_zeilen and len(z) > 3]
                                if neue:
                                    chat_zeilen.update(neue)
                                    with self._schloss:
                                        self._ereignisse += [("chat", start, z) for z in neue]
                                    for z in neue:
                                        # je Zeitstempel ("14:48") ein Clip: die Texterkennung las denselben Ping in
                                        # der Generalprobe 28.09. dreimal verschieden (drei Clips aus einem Ping)
                                        stempel = re.match(r"\s*(\d{1,2}:\d{2})", z)
                                        schl = stempel.group(1) if stempel else z
                                        if CLIP_WORTE.search(z) and schl not in blitz_pings:
                                            blitz_pings.add(schl)
                                            self.clips.anlass("chat", start, z)
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
            self.clips.alle_abschliessen()
            if protokoll:
                protokoll.close()
            if self._ereignis_datei:
                self._ereignis_datei.close()

    def _ich_ergaenzen(self, karte, zeit: float, sichtungen: list) -> list:
        """Das eigene Icon fehlt (im Kampf unter Gegner-Icons): die Position aus dem Kamerarahmen, wenn er zur
        letzten echten Sichtung passt (minimap.ich_aus_rahmen; an 172 Lueckenbildern: 87 % mit Position, Median
        211 Einheiten daneben - `werkzeuge/rahmen_luecken.py`). Guete 0 = erschlossen, nie ein Flash-Sprung."""
        ich = getattr(self, "ich", None)
        if not ich:
            return sichtungen
        eigen = next((s for s in sichtungen if s.champion_id == ich[0] and s.team in (None, ich[1])), None)
        if eigen is not None:
            if eigen.guete > 0:
                self._ich_zuletzt = (zeit, eigen.x, eigen.y)
            return sichtungen     # gesehen oder unter seiner Deckung mitgefuehrt
        try:
            pos = minimap.ich_aus_rahmen(minimap.kamerarahmen(karte), getattr(self, "_ich_zuletzt", None), zeit)
        except Exception:
            return sichtungen
        if pos is None:
            return sichtungen
        return sichtungen + [minimap.Sichtung(ich[0], None, pos[0], pos[1], 0.0)]

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
                for s in spruenge:
                    self.clips.anlass("spur", s.zeit, s.team)
                self.clips.bild(t, klein)
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
                    rahmen = minimap.kamerarahmen(getattr(self, "_letzte_karte", None))
                    if rahmen:   # das Spielbild ist nur die 16:9-Mitte: nur ihr Teil des Kamerarahmens (32:9)
                        a0, a1 = getattr(self, "_mitte_anteil", (0.0, 1.0))
                        rb = rahmen[2] - rahmen[0]
                        rahmen = (rahmen[0] + a0 * rb, rahmen[1], rahmen[0] + a1 * rb, rahmen[3])
                    with self._schloss:
                        self._ereignisse.append(("schirm_sprung", s.zeit, [s.team, s.anteil, *s.von, *s.nach, s.weite,
                                                                          name_von, name_nach,
                                                                          list(rahmen) if rahmen else None,
                                                                          [klein.shape[1], klein.shape[0]]]))
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
    """Neue Aufnahmen speichern genau die Minimap (quadratisch, je nach MinimapScale 570-780 px bei 4K); die
    ersten (26.09.2026, 12:00) die ganze Ecke (907 px) - daraus wird die Minimap herausgeschnitten."""
    bild = cv2.imread(str(pfad))
    if bild is None:
        return None
    s = round(minimap.KARTE * hoehe)
    if bild.shape[0] == bild.shape[1] and s - 2 <= bild.shape[0] <= minimap.groesse(3.0) * s + 2:
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
        if not any(e[0] == "gruben" for e in self._e):
            self._e += _gruben_aus_bildern(ordner)      # Auftrag 018, 1: Aufnahmen vor den Objective-Symbolen
        if not any(e[0] == "quest" for e in self._e):
            self._e += _quest_aus_bildern(ordner)       # Auftrag 006, W2: aeltere Aufnahmen
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


def _quest_aus_bildern(ordner: Path) -> list[tuple]:
    """Auftrag 006, W2: der Quest-Platz V aus den gesicherten Schirmbildern (schirm_<ms>.jpg, alle 5 s)."""
    from . import hud
    aus = []
    for b in sorted(ordner.glob("schirm_*.jpg")):
        if not b.stem[7:].isdigit():
            continue
        img = cv2.imread(str(b))
        if img is not None and (q := hud.quest(img)) is not None:
            aus.append(("quest", int(b.stem[7:]) / 1000, q))
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


def _gruben_aus_bildern(ordner: Path) -> list[tuple]:
    """Auftrag 018, 1: die Objective-Symbole aus den gespeicherten Minimap-Bildern (1 Hz, Wanduhr = Dateiname in
    ms). Einmal gerechnet, liegt das Ergebnis als gruben.json neben den Bildern (sonst kostet jedes Nachspiel ~6 s)."""
    from .objsymbole import Grubenleser
    zwischen = ordner / "gruben.json"
    if zwischen.exists():
        try:
            return [("gruben", w, s) for w, s in json.loads(zwischen.read_text(encoding="utf-8"))]
        except (OSError, ValueError, TypeError):
            pass
    leser, aus = Grubenleser(), []
    for pfad in sorted(ordner.glob("[0-9]*.jpg")):
        if not pfad.stem.isdigit() or (karte := cv2.imread(str(pfad))) is None:
            continue
        if (stand := leser.lies_bgr(karte)) is not None:
            aus.append(("gruben", int(pfad.stem) / 1000, stand))
    if aus:
        try:
            zwischen.write_text(json.dumps([[w, s] for _, w, s in aus]), encoding="utf-8")
        except OSError:
            pass
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


def _aufgenommen(pfad: Path) -> float:
    """Aufgenommene Spielzeit einer Aufnahme (letzter minus erster Schnappschuss, Sekunden) - nicht die Spieluhr:
    ein Coach, der mitten in der Partie startet, nimmt vielleicht nur eine Minute auf."""
    from . import aufzeichnung
    zeiten = []
    for zeile in aufzeichnung.gz_text(pfad).splitlines():
        try:
            zeiten.append(float((json.loads(zeile)["d"].get("gameData") or {}).get("gameTime") or 0.0))
        except (ValueError, KeyError, AttributeError):
            continue
    return max(zeiten) - min(zeiten) if zeiten else 0.0


def bilder_aufraeumen(behalte: int = 3) -> float:
    """Minimap-Bilder brauchen 120-180 MB je Partie. Nach der Auswertung reicht
    `sichtungen.json` (~1 MB) zum Nachspielen. Die Bilder der letzten `behalte`
    PARTIEN bleiben (fuer neue Erkennungsstaende und die Wellen-Eichung, Buch 1 1.4), aelteren bleibt nur die
    Sichtungsdatei. Gezaehlt werden echte Partien (ab profil.KURZ) - Bruchstuecke von Neustarts und Tests
    schoben sie vorher hinaus (27.09.: 130355 verlor seine Bilder an 132154 und 133930). Die juengste Aufnahme
    bleibt immer. Gibt die freigegebenen MB zurueck."""
    from . import aufzeichnung, zustand
    aufnahmen = sorted(aufzeichnung.ORDNER.glob("*.jsonl.gz"))
    try:
        from .profil import KURZ
        mit_bildern = [p for p in aufnahmen if aufzeichnung.bilder(p)]
        partien = [p for p in mit_bildern if _aufgenommen(p) >= KURZ]
        schuetzen = {p.name.removesuffix(".jsonl.gz") for p in partien[-behalte:]} if behalte else set()
    except Exception:          # im Zweifel wie frueher: die letzten `behalte` Aufnahmen
        schuetzen = {p.name.removesuffix(".jsonl.gz") for p in aufnahmen[-behalte:]} if behalte else set()
    if aufnahmen:
        schuetzen.add(aufnahmen[-1].name.removesuffix(".jsonl.gz"))
    frei = 0.0
    for pfad in aufnahmen:
        if pfad.name.removesuffix(".jsonl.gz") in schuetzen:
            continue
        # eine Datei BEHALTEN im Bilderordner schuetzt ihn (Wellen-Eichung, Flash-Messung - Qualitaetsrunde 1: 133930
        # verlor seine Bilder am 27.09. um 17:26, mitten in der Eichung)
        if (pfad.with_name(pfad.name.removesuffix(".jsonl.gz") + "_bilder") / "BEHALTEN").exists():
            continue
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
