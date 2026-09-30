"""Die Makro-Lage live (Stufe 4, Auftrag 034): aus Live-API, Minimap, HUD, Chat und den Lesern aus 033.

    bau = LageBau()
    lage, merkmale = bau.bauen(p, b, lagebild, m)     # je Takt (makro/takt.py ruft hoechstens einmal je Sekunde)

- `lage`: `MakroLage` fuer die 111 Entscheidungen. `lage.vorhanden` sagt, welche Live-Eingaben (wahrnehmung.EINGABEN)
  in DIESEM Takt wirklich da sind - fehlt eine, schweigt jede Entscheidung, die sie liest (makro/takt.py).
- `merkmale`: dict Merkmal -> Wert fuer `gehirn.bewerte()` (Namen wie buecher/challenger/merkmale.md, Geometrie wie
  werkzeuge/challenger/phase1.py). Was live fehlt, steht als None (= NaN im Modell), nie geraten.

Fehlende Wahrnehmung bleibt leer: die sechs unzuverlaessigen Eingaben aus 033 (Ward weg, Blitz der Mitspieler,
TP-Stand der Gegner, Recall des Lane-Gegners, Kopfgeld, Busch ohne Sicht) werden nie gefuellt - `vorhanden` nennt sie
nie, die Felder bleiben auf "unbekannt" (None/False).

Quellen: `p` zustand.Partie (API), `b` bewertung.Bewertung (Minimap, HUD, Kaufplan - vom Regelwerk schon gerechnet),
`lagebild` lage.Lagebild (Sichtungen, Wellen aller Lanes, Wards, Trinket, Zauber-Timer, TP-Spruenge), `m`
kern.Merkmale des alten Kerns (Wellen-Zustand nach Buch 1 mit Crash-Erkennung, Kanonen-Uhr). Alles darf fehlen.
"""
from __future__ import annotations

import math

from . import wahrnehmung
from .lage import GRUBEN, Kampf, MakroLage, Monster, Spieler, Ward, Welle

# Team-Codes wie in der Live-API
ORDER, CHAOS = "ORDER", "CHAOS"
ROLLEN = ("TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY")
LANES = ("top", "mid", "bot")
TRINKETS = {3340: "gelb", 3364: "linse", 3363: "blau"}
KONTROLLAUGE = 2055
TP = ("SummonerTeleport", "SummonerTeleportUpgrade", "S12_SummonerTeleportUpgrade")
SPIKE_ITEM_GOLD = 2500         # ein fertiges Item (Legendaer) - daran erkennt der Coach einen Spike
SPIKE_S = 90.0                 # so lange gilt ein Spike als "jetzt" (V4, V5, J10)
MONSTER_EVENT = {"DragonKill": "drache", "BaronKill": "baron", "HeraldKill": "herold", "HordeKill": "larven"}
INHIB_ZURUECK = 300.0          # wie bewertung.INHIB_ZURUECK / phase1.INHIB_RESPAWN
BARON_BUFF, ELDER_BUFF = 180.0, 150.0
BRUNNEN_R = 1200.0             # so nah am eigenen Brunnen heisst "im Brunnen" (Kauf moeglich)
BASIS_R = 4200.0               # 036: ohne den alten Kern (m.bereich) gilt so nah am Brunnen als eigene Basis
KAMPF_R = 1200.0               # Champions beider Teams so eng beieinander: ein Kampf (Minimap; 034: 2000 - zu weit)
KAMPF_KILL_S = 10.0            # ... in einer Lane waehrend der Lane-Phase nur mit einem Kill so kurz davor
SICHTBAR_S = 3.0               # so frisch zaehlt eine Minimap-Sichtung als "jetzt"
FRISCH_MIT_S = 3.0             # Mitspieler-Position/HUD so frisch

# --- Geometrie wie werkzeuge/challenger/phase1.py (bereich_np, zone_np, NAHE_SICHTBAR) - gleiche Zahlen, reines Python
BRUNNEN_XY = {ORDER: (400.0, 400.0), CHAOS: (14340.0, 14390.0)}
DRACHE_XY, BARON_XY = (9866.0, 4414.0), (5007.0, 10471.0)
ZONE_VON_BEREICH = (0, 0, 1, 2, 3, 1, 3, 1, 3, 1, 3)
LANE_BEREICH = {"TOP": 2, "MIDDLE": 3, "BOTTOM": 4, "UTILITY": 4, "JUNGLE": -1}
NAHE_SICHTBAR, NAHE_SICHTBAR_LANE, LANE_PHASE_BIS = 1200.0, 1800.0, 14 * 60
ANLASS = {"takt": 0, "kill": 1, "tod": 2, "respawn": 3, "back": 4, "gebaeude": 5, "monster": 6, "spawn": 7}


def bereich(x: float, y: float) -> int:
    """Kartenbereich 0-10 wie phase1.bereich_np (0/1 Basis blau/rot, 2 top, 3 mid, 4 bot, 5/6 Fluss, 7-10 Jungle)."""
    if math.hypot(x - BRUNNEN_XY[ORDER][0], y - BRUNNEN_XY[ORDER][1]) < 4200:
        return 0
    if math.hypot(x - BRUNNEN_XY[CHAOS][0], y - BRUNNEN_XY[CHAOS][1]) < 4200:
        return 1
    if x < 2300 or y > 12500:
        return 2
    if y < 2300 or x > 12500:
        return 4
    if abs(x - y) < 1500:
        return 3
    s = x + y
    if abs(s - 14800) < 1700:
        return 5 if y > x else 6
    if s < 14800:
        return 7 if y > x else 8
    return 9 if y > x else 10


def _abst(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _gegen(team: str) -> str:
    return CHAOS if team == ORDER else ORDER


def _lane_klein(lane: str | None) -> str | None:
    return None if lane is None else lane.lower()


class LageBau:
    """Baut je Takt die Makro-Lage. Haelt, was ueber Takte zaehlt: Zeit seit dem letzten Laden, Level und Items
    (fuer Spikes), eigener Anlass (Tod, Respawn, Back)."""

    def __init__(self):
        self.seit_laden = 0.0             # Spielzeit des letzten Ladenbesuchs (Start, Brunnen, Tod)
        self._tot_vorher = False
        self._im_brunnen_vorher = False
        self._level: dict[str, tuple[int, float]] = {}      # Spielername -> (Level, seit wann)
        self._items: dict[str, tuple[frozenset, float]] = {}   # Spielername -> (fertige Items, seit wann neu)
        self._spike: dict[str, float] = {}                   # Spielername -> Spielzeit des letzten Spikes
        self._ereignis_ids: set[int] = set()
        self._leben_bekannt = False
        self._platten: dict[str, float] = {}                # "wir"/"gegner" -> genommene Platten (Stand bis 14:00)
        self.anlass = "takt"

    # --- Hauptweg ---------------------------------------------------------------------------------------------------

    def bauen(self, p, b=None, lagebild=None, m=None) -> tuple[MakroLage, dict]:
        lb = lagebild if lagebild is not None and getattr(lagebild, "aktiv", False) else None
        team = p.mein_team or ORDER
        zeit = float(p.zeit)
        vorhanden = {"uhr", "ereignisse", "scoreboard", "eigene_items", "gegner_items", "monster_timer"}
        ich = self._ich(p, b, lb, zeit, vorhanden)
        # Auftrag 036 (Basis-Reaktion 83 %): 027 misst ab dem Betreten der eigenen Basis (m.bereich "basis_eigen"), der
        # Kauf kam erst am Brunnen (1200) - beim Heimlaufen Sekunden zu spaet
        if ich.lebt and ich.pos is not None:
            bereich = getattr(m, "bereich", None) if m is not None else None
            ich.in_basis = ich.im_brunnen or (bereich == "basis_eigen" if bereich is not None else
                                              _abst(ich.pos, BRUNNEN_XY[p.mein_team or ORDER]) <= BASIS_R)
        lage = MakroLage(zeit=zeit, team=team, ich=ich, gold=int(p.gold or 0))
        lage.vorhanden = vorhanden
        self._items_und_trinket(lage, p, lb, zeit, vorhanden)
        if b is not None and getattr(b, "kauf", None) is not None:
            k = b.kauf
            vorhanden.add("kaufplan")
            lage.spike_fehlt = 0 if k.kaufen else (k.naechstes[1] if k.naechstes else None)
            lage.plan["kauf"] = list(k.kaufen) or ([k.naechstes[0]] if k.naechstes else [])
        lage.mitspieler = self._mitspieler(p, b, lb, zeit, vorhanden)
        lage.gegner = self._gegner(p, lb, zeit, vorhanden)
        self._spikes(lage, p, zeit)
        self._wellen(lage, p, lb, m, zeit, vorhanden)
        lage.monster = self._monster(p, zeit)
        self._strukturen(lage, p, lb, zeit, vorhanden)
        lage.ereignisse = self._ereignisse(p, lb, zeit)
        self._wards(lage, lb, zeit, vorhanden)
        lage.kampf = self._kampf(lage, lb, kill_vor=min((e[2] for e in lage.ereignisse if e[0] in ("kill", "tod")),
                                                        default=None))
        if lb is not None:
            vorhanden |= {"gegner_sichtungen", "gegner_flash", "tp_sprung", "chat", "kampf"}
        self.anlass = self._anlass(p, ich, zeit)
        return lage, self.merkmale(lage, p)

    # --- ich --------------------------------------------------------------------------------------------------------

    def _ich(self, p, b, lb, zeit, vorhanden) -> Spieler:
        s = p.ich
        ich = Spieler(champion=s.champion, rolle=s.rolle, lebt=not s.tot, respawn=float(s.respawn or 0.0),
                      level=int(s.level), tp_hat=any(z in TP for z in s.zauber))
        ich.pos = b.pos if b is not None else None
        if ich.pos is not None:
            vorhanden.add("eigene_position")
        self._leben_bekannt = (b is not None and b.leben is not None) or s.tot
        if b is not None and b.leben is not None:
            ich.leben = float(b.leben)
        elif s.tot:
            ich.leben = 0.0
        if b is not None:
            ich.tempo = float(getattr(b, "mein_tempo", 365.0) or 365.0)
            ich.flash_in = b.flash if "SummonerFlash" in s.zauber else None
            ich.ult_bereit = b.ult
            if b.zweiter is not None and b.zweiter[0] in TP:
                ich.tp_in = float(b.zweiter[1])
            if b.flash is not None or b.zweiter is not None or b.bereit is not None:
                vorhanden.add("eigene_zauber")
        brunnen = BRUNNEN_XY[p.mein_team or ORDER]
        ich.im_brunnen = bool(not s.tot and ich.pos is not None and _abst(ich.pos, brunnen) <= BRUNNEN_R)
        # Zeit seit dem letzten Laden (Merkmal seit_back): Brunnen oder Tod (beides oeffnet den Laden)
        if s.tot or ich.im_brunnen or zeit < 5:
            self.seit_laden = zeit
        return ich

    def _items_und_trinket(self, lage: MakroLage, p, lb, zeit, vorhanden) -> None:
        items = set(p.ich.items)
        lage.trinket = next((TRINKETS[i] for i in items if i in TRINKETS), "gelb")
        lage.kontrollauge_inventar = KONTROLLAUGE in items
        # Wer ein Kontroll-Auge gesetzt hat, liest der Coach nicht verlaesslich (033: Wards deines Teams, nicht
        # deine) - bleibt False ("nicht bekannt gesetzt")
        if lb is not None and lage.trinket == "gelb" and (t := lb.trinket_ladungen(zeit)) is not None:
            lage.trinket_ladungen = int(t)
            vorhanden.add("trinket_ladungen")

    # --- Mitspieler und Gegner --------------------------------------------------------------------------------------

    def _mitspieler(self, p, b, lb, zeit, vorhanden) -> list[Spieler]:
        aus = []
        hud = pos = False
        for s in p.team(p.mein_team):
            if s is p.ich or s.name == p.ich.name:
                continue
            sp = Spieler(champion=s.champion, rolle=s.rolle, lebt=not s.tot, respawn=float(s.respawn or 0.0),
                         level=int(s.level), tp_hat=any(z in TP for z in s.zauber),
                         flash_in=None)                     # Blitz der Mitspieler: nicht lesbar (033)
            if lb is not None and not s.tot:
                if (g := lb.gesehen(s)) is not None and zeit - g[0] < FRISCH_MIT_S:
                    sp.pos = _einheiten(g[1], g[2])
                    pos = True
                if (le := lb.leben(s, zeit)) is not None:
                    sp.leben = float(le)
                    sp.ult_bereit = lb.ult_bereit(s, zeit)
                    hud = True
            if s.tot:
                sp.leben = 0.0
            if s.rolle == "JUNGLE" and "SummonerSmite" in s.zauber:
                sp.smite_bereit = None                      # Smite-Timer eines Mitspielers: unbekannt
            aus.append(sp)
        if pos:
            vorhanden.add("mitspieler_positionen")
        if hud:
            vorhanden.add("mitspieler_hud")
        return aus

    def _gegner(self, p, lb, zeit, vorhanden) -> list[Spieler]:
        aus = []
        for s in p.gegner():
            sp = Spieler(champion=s.champion, rolle=s.rolle, lebt=not s.tot, respawn=float(s.respawn or 0.0),
                         level=int(s.level), tp_hat=any(z in TP for z in s.zauber),
                         tp_in=None,              # TP-Stand der Gegner: unzuverlaessig (033) - leer
                         backt=False,             # Recall des Lane-Gegners: unzuverlaessig (033) - leer
                         gesehen_vor=None, ult_bereit=None, flash_in=None)
            if lb is not None:
                if (g := lb.gesehen(s)) is not None:
                    sp.pos = _einheiten(g[1], g[2])
                    sp.gesehen_vor = max(0.0, zeit - g[0])
                if "SummonerFlash" in s.zauber:
                    t = lb.zauber.timer.get((s.name, "SummonerFlash"))
                    sp.flash_in = None if t is None else max(0.0, t.zurueck - zeit)
                if (le := lb.gegner_leben_jetzt(s, zeit)) is not None:
                    sp.leben = float(le)
            if s.tot:
                sp.leben, sp.gesehen_vor = 0.0, 0.0
            aus.append(sp)
        return aus

    def _spikes(self, lage: MakroLage, p, zeit: float) -> None:
        """Level 6 oder ein fertiges Item (ab SPIKE_ITEM_GOLD, Data-Dragon-Preis) in den letzten SPIKE_S Sekunden.
        Gegner-Items und -Level zeigt die API nur 'wie zuletzt gesehen' (033) - ein Spike wird dann spaeter erkannt,
        nie erfunden."""
        from ..ddragon import item_preis
        for s in p.spieler:
            lvl_alt = self._level.get(s.name)
            if lvl_alt is not None and lvl_alt[0] < 6 <= s.level:
                self._spike[s.name] = zeit
            self._level[s.name] = (s.level, zeit)
            fertig = frozenset(i for i in s.items if _preis(item_preis, i) >= SPIKE_ITEM_GOLD)
            alt = self._items.get(s.name)
            if alt is not None and fertig - alt[0]:
                self._spike[s.name] = zeit
            self._items[s.name] = (fertig, zeit)
        neu = {n for n, t in self._spike.items() if zeit - t <= SPIKE_S}
        wir = {s.name for s in p.team(p.mein_team)}
        lage.spike_wir = bool(neu & wir)
        lage.spike_gegner = bool(neu - wir)
        namen = {s.champion: s.name for s in p.gegner()}
        for g in lage.gegner:
            g.spike_neu = namen.get(g.champion) in neu

    # --- Wellen, Monster, Strukturen ---------------------------------------------------------------------------------

    def _wellen(self, lage: MakroLage, p, lb, m, zeit, vorhanden) -> None:
        eigene = lage.lane
        alle = 0
        for lane in LANES:
            w = None
            if lb is not None:
                w = lb.welle(lane.capitalize(), zeit)
            if w is None:
                continue
            alle += 1
            wir, die = (w.blau, w.rot) if lage.team == ORDER else (w.rot, w.blau)
            welle = Welle(stand=w.stand(lage.team), groesse=int(wir) - int(die))
            lage.wellen[lane] = welle
        if alle == len(LANES):
            vorhanden.add("wellen_alle")
        # die eigene Lane: der Wellen-Zustand des alten Kerns (Buch 1, geeicht) kennt den Crash und die Kanonen-Uhr
        if eigene is not None:
            ws = getattr(m, "welle", None) if m is not None else None
            w = lage.wellen.get(eigene)
            if ws is not None and getattr(ws, "zustand", None) == "GECRASHT_BEI_IHM":
                w = w or Welle()
                w.stand = "gecrasht"
                lage.wellen[eigene] = w
            if w is not None and m is not None and getattr(m, "kanone_in", None) is not None:
                w.kanone_in = float(m.kanone_in)
            if eigene in lage.wellen and lage.wellen[eigene].stand is not None:
                vorhanden.add("welle_eigen")

    def _monster(self, p, zeit) -> list[Monster]:
        aus = []
        for art in ("drache", "larven", "herold", "baron"):
            try:
                t = p.naechster_spawn(art)
            except Exception:
                t = None
            if t is None:
                continue
            if art == "drache" and p.seele() is not None:
                name = "elder"
            else:
                name = art
            aus.append(Monster(name, max(0.0, t - zeit), seele=(art == "drache" and _seelen_drache(p))))
        return aus

    def _strukturen(self, lage: MakroLage, p, lb, zeit, vorhanden) -> None:
        from ..zustand import struktur
        weg = []
        for e in p.kills_von("TurretKilled"):
            st = struktur(e.daten.get("TurretKilled", ""))
            if st is not None:
                weg.append((e.zeit, (st.team, st.lane, st.stufe)))
        weg.sort(key=lambda x: -x[0])
        lage.tuerme_weg = [x[1] for x in weg]
        lage.turm_gefallen_vor = zeit - weg[0][0] if weg else None
        for e in p.kills_von("InhibKilled"):
            st = struktur(e.daten.get("InhibKilled", ""))
            if st is None or zeit - e.zeit >= INHIB_ZURUECK:
                continue
            (lage.inhib_offen_wir if st.team == lage.team else lage.inhib_offen_gegner).append(st.lane.lower())
        if lb is not None and getattr(lb, "platten", None):
            vorhanden.add("platten")
            for (team, lane, stufe), n in lb.platten.items():
                if team == lage.gegnerteam and stufe == "aussen":
                    lage.gegner_platten[lane.lower()] = int(n)
            self._platten_zaehlen(lage, lb.platten)

    def _platten_zaehlen(self, lage: MakroLage, platten: dict) -> None:
        """Merkmal platten_wir/_gegner (genommene Platten je Team) aus der Platten-Ziffer der Minimap: je Aussenturm
        5 minus die Ziffer, ein gefallener Aussenturm vor 14:00 zaehlt 5. Nur, wenn alle drei Tuerme einer Seite
        gelesen sind; nach 14:00 bleibt der letzte Stand (wie im Training: die Zahl waechst danach nicht mehr)."""
        if lage.zeit >= LANE_PHASE_BIS:
            return
        weg = set(lage.tuerme_weg)
        for seite, besitzer in (("wir", lage.gegnerteam), ("gegner", lage.team)):
            summe = 0
            for lane in ("Top", "Mid", "Bot"):
                k = (besitzer, lane, "aussen")
                if k in weg:
                    summe += 5
                elif k in platten:
                    summe += 5 - int(platten[k])
                else:
                    break
            else:
                self._platten[seite] = float(summe)

    def _ereignisse(self, p, lb, zeit) -> list[tuple[str, str, float]]:
        """(Art, wer, vor s), neueste zuerst: kill/tod (Champion oder 'ich'), ace/drache/baron/herold/larven/turm
        (wir/gegner), kampf (gewonnen/verloren: mehrere Tode in 15 s), tp (gegner: TP-Sprung auf der Minimap)."""
        aus = []
        wir = p.mein_team
        kills = []
        for e in p.ereignisse:
            vor = zeit - e.zeit
            if vor < 0 or vor > 300:
                continue
            seite = "wir" if e.team == wir else "gegner"
            if e.art == "ChampionKill" and e.opfer is not None:
                if e.opfer is p.ich or (p.ich and e.opfer.name == p.ich.name):
                    aus.append(("tod", "ich", vor))
                elif e.opfer.team == wir:
                    aus.append(("tod", e.opfer.champion, vor))
                else:
                    aus.append(("kill", e.opfer.champion, vor))
                kills.append((e.zeit, e.opfer.team == wir))
            elif e.art == "Ace":
                aus.append(("ace", seite, vor))
            elif e.art in MONSTER_EVENT:
                art = MONSTER_EVENT[e.art]
                if art == "drache" and e.daten.get("DragonType") == "Elder":
                    art = "elder"
                aus.append((art, seite, vor))
                aus.append(("objective", seite, vor))
            elif e.art in ("TurretKilled", "InhibKilled"):
                aus.append(("turm", seite, vor))
        # Kampf: mindestens drei Tode in 15 s - gewonnen, wenn mehr Gegner fielen
        if kills:
            t_letzt = max(t for t, _ in kills)
            im = [unser for t, unser in kills if t_letzt - t <= 15.0]
            if len(im) >= 3:
                ergebnis = "gewonnen" if im.count(False) > im.count(True) else \
                    "verloren" if im.count(True) > im.count(False) else "offen"
                aus.append(("kampf", ergebnis, zeit - t_letzt))
        if lb is not None:
            namen_gegner = {s.name for s in p.gegner()}
            for t in getattr(lb, "fernspruenge", []) or []:
                if getattr(t, "name", None) in namen_gegner and getattr(t, "zauber", "") in TP and 0 <= zeit - t.seit <= 300:
                    aus.append(("tp", "gegner", zeit - t.seit))
        aus.sort(key=lambda e: e[2])
        return aus

    def _wards(self, lage: MakroLage, lb, zeit, vorhanden) -> None:
        if lb is None:
            return
        stehen = lb.team_wards(zeit)
        if stehen is None:
            return
        vorhanden.add("eigene_wards")
        for w in stehen:
            pos = _einheiten(w.x, w.y)
            lage.wards.append(Ward(ort=_ward_ort(pos, w, lage.team), pos=pos,
                                   art="kontrolle" if w.art == "kontrolle" else "gelb"))

    def _kampf(self, lage: MakroLage, lb, kill_vor: float | None = None) -> Kampf | None:
        """Ein Kampf auf der Minimap: mindestens zwei sichtbare Gegner und ein Mitspieler (ohne dich) in KAMPF_R.
        In einer Lane waehrend der Lane-Phase (vor 14:00) ist das 2 gegen 2 kein Kampf, ausser ein Kill oder Tod liegt
        hoechstens KAMPF_KILL_S zurueck (Nachspiel 035: die Botlane galt dauernd als Kampf - "Nicht kaempfen: 1 gegen
        3" jede halbe Minute)."""
        if lb is None:
            return None
        sicht = [g for g in lage.gegner if g.lebt and g.pos is not None and g.gesehen_vor is not None
                 and g.gesehen_vor <= SICHTBAR_S]
        if len(sicht) < 2:
            return None
        bester = None
        for g in sicht:
            geg = [x for x in sicht if _abst(x.pos, g.pos) <= KAMPF_R]
            wir = [s for s in lage.mitspieler if s.lebt and s.pos is not None and _abst(s.pos, g.pos) <= KAMPF_R]
            if len(geg) >= 2 and wir and (bester is None or len(geg) + len(wir) > bester[0]):
                mitte = (sum(x.pos[0] for x in geg + wir) / (len(geg) + len(wir)),
                         sum(x.pos[1] for x in geg + wir) / (len(geg) + len(wir)))
                if lage.zeit < LANE_PHASE_BIS and bereich(*mitte) in (2, 3, 4) \
                        and (kill_vor is None or kill_vor > KAMPF_KILL_S):
                    continue
                bei = next((n.capitalize() for n, pos in GRUBEN.items() if n in ("drache", "baron")
                            and _abst(mitte, pos) <= 2500), wir[0].champion)
                bester = (len(geg) + len(wir), Kampf(pos=mitte, wir=len(wir), gegner=len(geg), bei=bei))
        return bester[1] if bester else None

    def _anlass(self, p, ich: Spieler, zeit: float) -> str:
        """Anlass wie phase1.ANLAESSE: Kill, eigener Tod, Respawn, Back, Gebaeude, Monster - sonst Takt."""
        anlass = "takt"
        if self._tot_vorher and ich.lebt:
            anlass = "respawn"
        elif ich.im_brunnen and not self._im_brunnen_vorher and ich.lebt:
            anlass = "back"
        self._tot_vorher, self._im_brunnen_vorher = not ich.lebt, ich.im_brunnen
        for e in p.ereignisse:
            if e.id in self._ereignis_ids:
                continue
            self._ereignis_ids.add(e.id)
            if zeit - e.zeit > 5:
                continue
            if e.art == "ChampionKill":
                anlass = "tod" if e.opfer is p.ich else "kill"
            elif e.art in ("TurretKilled", "InhibKilled") and anlass == "takt":
                anlass = "gebaeude"
            elif e.art in MONSTER_EVENT and anlass == "takt":
                anlass = "monster"
        return anlass

    # --- Merkmale fuer das Gehirn -----------------------------------------------------------------------------------

    def merkmale(self, lage: MakroLage, p) -> dict:
        """dict fuer gehirn.bewerte(): Namen wie phase1.NAMEN (ohne Gegner-Scoreboard, Entscheidung zu Stufe 2) plus
        rolle, seite, anlass. None = unbekannt (NaN)."""
        team, feind = lage.team, lage.gegnerteam
        m: dict = {"minute": lage.zeit / 60.0}
        ich = lage.ich
        if ich.pos is not None:
            x, y = ich.pos
            ber = bereich(x, y)
            m.update(x=x, y=y, bereich=ber, zone=ZONE_VON_BEREICH[ber],
                     in_eigener_lane=float(ber == LANE_BEREICH.get(ich.rolle, -1)),
                     abst_brunnen=_abst(ich.pos, BRUNNEN_XY[team]),
                     abst_drache=_abst(ich.pos, DRACHE_XY), abst_baron=_abst(ich.pos, BARON_XY),
                     abst_eigener_turm=_turm_abstand(ich.pos, team, lage.tuerme_weg),
                     abst_gegner_turm=_turm_abstand(ich.pos, feind, lage.tuerme_weg))
        m.update(tot=float(not ich.lebt), respawn_rest=0.0 if ich.lebt else ich.respawn, level=ich.level,
                 cs=p.ich.cs, gold_tasche=lage.gold, itemwert=p.ich.item_gold,
                 leben_anteil=0.0 if not ich.lebt else (ich.leben if self._leben_bekannt else None),
                 hat_tp=float(ich.tp_hat), seit_back=max(0.0, lage.zeit - self.seit_laden))
        # Team (Minimap), Reihenfolge nach Rolle wie im Training
        mit = sorted(lage.mitspieler, key=lambda s: ROLLEN.index(s.rolle) if s.rolle in ROLLEN else 9)
        m["mit_lebend"] = sum(s.lebt for s in mit)
        abst = [_abst(s.pos, ich.pos) for s in mit if s.lebt and s.pos is not None and ich.pos is not None]
        if "mitspieler_positionen" in lage.vorhanden and ich.pos is not None:
            m["mit_nah"] = sum(d <= 2500 for d in abst)
            m["mit_abstand"] = sum(abst) / len(abst) if abst else None
        for i, s in enumerate(mit[:4], 1):
            if s.lebt and s.pos is not None:
                m[f"mit{i}_x"], m[f"mit{i}_y"] = s.pos
        # Scoreboard und Ereignisse
        tuerme = {t: sum(1 for x in lage.tuerme_weg if x[0] != t and x[2] != "Nexus") for t in (team, feind)}
        m.update(kills_wir=p.kills(team), kills_gegner=p.kills(feind), tuerme_wir=tuerme[team],
                 tuerme_gegner=tuerme[feind], inhibs_offen_wir=len(lage.inhib_offen_gegner),
                 inhibs_offen_gegner=len(lage.inhib_offen_wir))
        for k, v in _objective_zaehler(p, team, lage.zeit).items():
            m[k] = v
        for seite in ("wir", "gegner"):
            if seite in self._platten:
                m[f"platten_{seite}"] = self._platten[seite]
        m.update(itemwert_team_wir=p.item_gold(team),
                 level_team_wir=sum(s.level for s in p.team(team)),
                 cs_team_wir=sum(s.cs for s in p.team(team)),
                 tote_wir=sum(s.tot for s in p.team(team)), tote_gegner=sum(s.tot for s in p.gegner()))
        # Lane-Gegner nahe sichtbar (die einzige Gegnerposition im Training ausser "zuletzt gesehen")
        lg = lage.lane_gegner
        if lg is not None and ich.pos is not None and "gegner_sichtungen" in lage.vorhanden:
            nah = False
            if lg.lebt and ich.lebt and lg.pos is not None and lg.gesehen_vor is not None and lg.gesehen_vor <= 1.0:
                lane_b = LANE_BEREICH.get(ich.rolle, -1)
                r = NAHE_SICHTBAR_LANE if (lage.zeit < LANE_PHASE_BIS and lane_b > 0 and bereich(*ich.pos) == lane_b
                                           and bereich(*lg.pos) == lane_b) else NAHE_SICHTBAR
                nah = _abst(lg.pos, ich.pos) <= r
            m["lg_nahe_sichtbar"] = float(nah)
            if nah:
                m["lg_x"], m["lg_y"] = lg.pos
        for i, r in enumerate(ROLLEN):
            g = lage.rolle(lage.gegner, r)
            if g is None:
                continue
            m[f"geg{i}_tot"] = float(not g.lebt)
            m[f"geg{i}_respawn"] = 0.0 if g.lebt else g.respawn
            if g.pos is not None and g.gesehen_vor is not None and g.lebt:
                m[f"geg{i}_gesehen_x"], m[f"geg{i}_gesehen_y"] = g.pos
                m[f"geg{i}_gesehen_alter"] = g.gesehen_vor
        for art in ("drache", "larven", "herold", "baron"):
            mon = next((x for x in lage.monster if (x.art == art or (art == "drache" and x.art == "elder"))), None)
            if mon is None:
                m[f"{art}_da"], m[f"{art}_bis"] = 0.0, -1.0
            else:
                m[f"{art}_da"] = float(mon.spawn_in <= 0)
                m[f"{art}_bis"] = max(0.0, mon.spawn_in)
        m["drache_ist_elder"] = float(any(x.art == "elder" for x in lage.monster))
        m["rolle"] = ROLLEN.index(ich.rolle) if ich.rolle in ROLLEN else None
        m["seite"] = 0.0 if team == ORDER else 1.0
        m["anlass"] = ANLASS.get(self.anlass, 0)
        return m

    def kontext(self, lage: MakroLage) -> dict:
        """Kontext fuer gehirn.bewerte (Back nur mit Grund): Welle gecrasht, Kaufplan. Der Recall des Lane-Gegners
        ist unzuverlaessig (033) und fehlt."""
        return {"welle_gecrasht": lage.welle().stand == "gecrasht", "spike_fehlt": lage.spike_fehlt,
                "lane_gegner_backt": False}


# --- Hilfen --------------------------------------------------------------------------------------------------------

def _einheiten(x: float, y: float) -> tuple[float, float]:
    from ..bewertung import einheiten
    return einheiten(x, y)


def _preis(item_preis, i: int) -> int:
    try:
        return int(item_preis(i) or 0)
    except Exception:
        return 0


def _seelen_drache(p) -> bool:
    """Der naechste Drache bringt einer Seite die Seele (drei Drachen, keine Seele)."""
    try:
        return p.seele() is None and any(len(p.drachen(t)) == 3 for t in (ORDER, CHAOS))
    except Exception:
        return False


def _turm_abstand(pos, team: str, weg: list) -> float:
    """Abstand zum naechsten stehenden Turm von `team` (ohne Nexus-Tuerme wie phase1: g.TUERME), sonst zum Brunnen."""
    from ..bewertung import TUERME
    gefallen = {x for x in weg if x[0] == team}
    d = [_abst(pos, xy) for k, xy in TUERME.items() if k[0] == team and k not in gefallen]
    return min(d) if d else _abst(pos, BRUNNEN_XY[team])


def _objective_zaehler(p, team: str, zeit: float) -> dict:
    """Drachen, Seele, Larven, Herold, Baron, Elder je Team, Baron-/Elder-Buff-Rest (wie phase1: Kill + 180/150 s)."""
    feind = _gegen(team)
    out = {}
    drachen = {t: [e for e in p.kills_von("DragonKill") if e.team == t] for t in (team, feind)}
    for t, seite in ((team, "wir"), (feind, "gegner")):
        elementar = [e for e in drachen[t] if e.daten.get("DragonType") != "Elder"]
        elder = [e for e in drachen[t] if e.daten.get("DragonType") == "Elder"]
        baron = [e for e in p.kills_von("BaronKill") if e.team == t]
        out[f"drachen_{seite}"] = len(elementar)
        out[f"seele_{seite}"] = float(len(elementar) >= 4)
        out[f"larven_{seite}"] = sum(1 for e in p.kills_von("HordeKill") if e.team == t)
        out[f"herold_{seite}"] = sum(1 for e in p.kills_von("HeraldKill") if e.team == t)
        out[f"baron_{seite}"] = len(baron)
        out[f"elder_{seite}"] = len(elder)
        out[f"baron_buff_{seite}"] = max(0.0, BARON_BUFF - (zeit - baron[-1].zeit)) if baron else 0.0
        out[f"elder_buff_{seite}"] = max(0.0, ELDER_BUFF - (zeit - elder[-1].zeit)) if elder else 0.0
    return out


def _ward_ort(pos, w, team: str) -> str:
    """Ort eines Wards in Worten, so dass die Entscheidungen ihn finden: an einer Grube (Drache / Baron, Herold,
    Larven), 'Flanke' im gegnerischen Jungle, sonst der Minimap-Ort."""
    if _abst(pos, DRACHE_XY) <= 2000:
        return "Drache"
    if _abst(pos, BARON_XY) <= 2000:
        return "Baron, Herold, Larven"
    ber = bereich(*pos)
    ihr_jungle = (9, 10) if team == ORDER else (7, 8)
    if ber in ihr_jungle:
        return "Flanke im gegnerischen Jungle"
    try:
        from ..minimap import ort
        return ort(w.x, w.y, team)
    except Exception:
        return "Karte"


def luecken(lage: MakroLage) -> list[str]:
    """Welche Live-Eingaben in diesem Takt fehlen (fuers Protokoll und den Bericht)."""
    vorh = getattr(lage, "vorhanden", None)
    if vorh is None:
        return []
    return sorted(e for e, (_, live) in wahrnehmung.EINGABEN.items() if live and e not in vorh)
