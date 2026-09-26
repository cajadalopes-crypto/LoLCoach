"""Das Regelwerk: aus zwei aufeinanderfolgenden Zustaenden werden Ansagen.

Jede Regel schaut auf den Wechsel (vorher -> jetzt), damit sie genau einmal
ausloest - im Moment, in dem etwas passiert, nicht in jeder Sekunde danach.
Schwellen und Saetze stehen in `wissen/makro.toml` und `wissen/items.toml`.

Ob und wann eine Ansage gesprochen wird, entscheidet nicht die Regel,
sondern der Sprechplan (Vorrang, Pausen, keine Wiederholung).
"""
from __future__ import annotations

from dataclasses import dataclass

from . import ddragon, wissen
from .zustand import Partie, Spieler, gegenteam, struktur

SOFORT, WICHTIG, HINWEIS = 3, 2, 1


@dataclass
class Ansage:
    text: str
    prio: int
    schluessel: str        # gleiche Schluessel sperren sich gegenseitig (siehe `sperre`)
    zeit: float = 0.0      # Spielzeit der Entstehung
    gueltig: float = 12.0  # so lange darf sie warten, danach ist sie ueberholt
    sperre: float = 60.0   # so lange kommt derselbe Schluessel nicht wieder
    gesprochen: float | None = None  # Spielzeit, zu der der Sprechplan sie sagte


def _objective_name(schl: str, p: Partie) -> str:
    """Kurz, zum Satzanfang tauglich: "Drache jetzt", "Larven jetzt"."""
    if schl == "drache" and p.seele():
        return "Ältester Drache"
    return {"drache": "Drache", "larven": "Larven", "herold": "Herold", "baron": "Baron"}[schl]


def _lebende_objectives(p: Partie, bis: float = 0.0, puffer: float = 30.0) -> list[str]:
    """Objectives, die leben oder innerhalb von `bis` Sekunden spawnen - ohne
    die, die in weniger als `puffer` Sekunden ohnehin verschwinden."""
    obj = wissen.objektive()
    return [s for s in ("baron", "drache", "herold", "larven")
            if (n := p.naechster_spawn(s)) is not None and n <= p.zeit + bis
            and not ("weg" in obj[s] and obj[s]["weg"] - p.zeit < puffer)]


def _minuten(sek: float) -> str:
    s = int(round(sek))
    if s < 90:
        return f"{s} Sekunden"
    m, r = divmod(s, 60)
    return f"{m} Minuten" if r < 15 else (f"{m} Minuten 30" if r < 45 else f"{m + 1} Minuten")


def _legendaer(item_id: int, ab: int) -> bool:
    e = ddragon.items().get(item_id)
    return bool(e and not e.get("into") and e["gold"]["total"] >= ab and "Boots" not in e.get("tags", []))


class Regelwerk:
    def __init__(self):
        self.m = wissen.lade("makro")
        self.item_tipps = {i: v for v in wissen.lade("items").values()
                           if isinstance(v, dict) for i in v["ids"]}
        self.vorher: Partie | None = None
        self.lage = None
        self._gemeldet: set = set()  # einmalige Dinge (Vorwarnung je Spawn, CS je Minute)
        self._weg_seit: dict[str, float | None] = {}  # Spielername -> seit wann unsichtbar (lebendig)
        self._tot_bei: dict[str, float] = {}           # Spielername -> zuletzt tot gesehen (Spielzeit)

    def pruefe(self, p: Partie, lage=None) -> list[Ansage]:
        """`lage`: Lagebild aus der Minimap (lage.Lagebild) oder None ohne Bild."""
        v, self.vorher = self.vorher, p
        self.lage = lage
        if not p.ich or v is None or not v.ich or p.zeit < v.zeit:
            return []
        ansagen: list[Ansage] = []
        for regel in (self._vorwarnung, self._zahlen, self._jungler_tot, self._lane_tot,
                      self._level, self._items, self._gold, self._cs, self._tod,
                      self._jungler_gesehen, self._lane_fehlt, self._leben, self._zauber):
            for a in regel(p, v) or ():
                a.zeit = p.zeit
                ansagen.append(a)
        return ansagen

    # --- Hilfen ---------------------------------------------------------------

    def _satz(self, abschnitt: dict, p: Partie) -> str:
        """Satz fuer die eigene Rolle. Wer tot oder in der Basis ist, bekommt den
        allgemeinen Satz (keine Lane-Anweisung aus dem Brunnen - Partie 3, 24:58).
        Ein Toplaner ohne Teleport bekommt `TOP_ohne_tp` nur, bis die Top-Quest
        spaetestens Teleport gibt (Partie 3, 31:11: 'du sagst die ganze Zeit ohne Teleport')."""
        if self._ich_weg(p):
            return abschnitt.get("alle", "")
        rolle = p.ich.rolle
        if (rolle == "TOP" and "SummonerTeleport" not in p.ich.zauber and "TOP_ohne_tp" in abschnitt
                and p.zeit < self.m["rollenquest"]["top_teleport_spaetestens"]):
            return abschnitt["TOP_ohne_tp"]
        return abschnitt.get(rolle, abschnitt.get("alle", ""))

    def _ich_in_basis(self, p: Partie) -> bool:
        if not self.lage or not self.lage.aktiv:
            return False
        from . import minimap
        g = self.lage.gesehen(p.ich)
        return bool(g and p.zeit - g[0] < 3 and "Basis" in minimap.ort(g[1], g[2], p.mein_team))

    def _ich_weg(self, p: Partie) -> bool:
        return p.ich.tot or self._ich_in_basis(p)

    def _lebend(self, p: Partie) -> tuple[int, int]:
        """(lebende eigene, lebende Gegner). Leben der Mitspieler kennt die API nicht."""
        return (sum(1 for s in p.team(p.mein_team) if not s.tot),
                sum(1 for s in p.gegner() if not s.tot))

    def _objective_machbar(self, p: Partie, schl: str, vorsprung: int) -> bool:
        wir, die = self._lebend(p)
        noetig = self.m["zahlen"]["lebend_baron" if schl == "baron" else "lebend_drache"]
        return wir - die >= vorsprung and wir >= noetig

    # --- einzelne Regeln ------------------------------------------------------

    def _vorwarnung(self, p: Partie, v: Partie):
        vorlauf = self.m["vorwarnung"]["vorlauf"]
        for schl in ("drache", "larven", "herold", "baron"):
            n = p.naechster_spawn(schl)
            if n is None or not (0 < n - p.zeit <= vorlauf) or (schl, n) in self._gemeldet:
                continue
            self._gemeldet.add((schl, n))
            abschnitt = self.m["vorwarnung"][schl]
            if schl == "drache" and any(len(p.drachen(t)) == 3 for t in ("ORDER", "CHAOS")) and not p.seele():
                abschnitt = self.m["vorwarnung"]["drache_seele"]
            if text := self._satz(abschnitt, p):
                yield Ansage(text, WICHTIG, f"vorwarnung:{schl}", gueltig=25)

    def _objectives(self, p: Partie, bis: float = 0.0) -> list[str]:
        return _lebende_objectives(p, bis, self.m["seiten"]["nicht_mehr_vor_weg"])

    def _tot_seit_eben(self, p: Partie, v: Partie, s: Spieler) -> bool:
        alt = next((x for x in v.spieler if x.name == s.name and x.team == s.team), None)
        return s.tot and alt is not None and not alt.tot

    def _gegner_tot(self, p: Partie, min_s: float) -> list[Spieler]:
        return [s for s in p.gegner() if s.tot and s.respawn >= min_s]

    def _zahlen(self, p: Partie, v: Partie):
        z = self.m["zahlen"]
        tot, vorher = self._gegner_tot(p, z["min_sekunden"]), self._gegner_tot(v, z["min_sekunden"])
        if len(tot) >= 2 and len(tot) > len(vorher) and not p.ich.tot:
            fenster = int(min(s.respawn for s in tot))
            wir, die = self._lebend(p)
            objs = [o for o in self._objectives(p) if self._objective_machbar(p, o, z["vorsprung_mindestens"])]
            if objs:
                text = z["vorteil_objective"].format(anzahl=len(tot), sekunden=fenster,
                                                     objective=_objective_name(objs[0], p))
                yield Ansage(text, SOFORT, f"jetzt:{objs[0]}", gueltig=6, sperre=20)
            elif wir > die:
                yield Ansage(z["vorteil_turm"].format(anzahl=len(tot), sekunden=fenster), SOFORT,
                             "zahlen", gueltig=6, sperre=20)
        eigene = [s for s in p.team(p.mein_team) if s.tot and s.respawn >= z["min_sekunden"]]
        vorher_eigene = [s for s in v.team(v.mein_team) if s.tot and s.respawn >= z["min_sekunden"]]
        if len(eigene) >= 2 and len(eigene) > len(vorher_eigene) and not p.ich.tot:
            fenster = int(min(s.respawn for s in eigene))
            yield Ansage(self.m["zahlen"]["nachteil"].format(anzahl=5 - len(eigene), sekunden=fenster),
                         SOFORT, "zahlen_nachteil", gueltig=6, sperre=30)

    def _jungler_tot(self, p: Partie, v: Partie):
        j = p.jungler(gegenteam(p.mein_team))
        cfg = self.m["jungler_tot"]
        if not j or not self._tot_seit_eben(p, v, j) or j.respawn < cfg["min_sekunden"]:
            return
        if len(self._gegner_tot(p, self.m["zahlen"]["min_sekunden"])) >= 2:
            return  # die Zahlen-Regel sagt es besser
        objs = [o for o in self._objectives(p, bis=j.respawn - 10) if self._objective_machbar(p, o, 0)]
        if objs and not self._ich_weg(p):
            nah = p.ich.rolle in self.m["seiten"][objs[0]]
            text = self.m["jungler_tot_objective"]["nah" if nah else "fern"].format(
                champion=j.champion, sekunden=int(j.respawn), objective=_objective_name(objs[0], p))
            yield Ansage(text, SOFORT if nah else WICHTIG, f"jetzt:{objs[0]}", gueltig=6, sperre=20)
        elif text := self._satz(cfg, p):
            yield Ansage(text.format(champion=j.champion, sekunden=int(j.respawn)), WICHTIG,
                         "jungler_tot", gueltig=8)

    def _lane_tot(self, p: Partie, v: Partie):
        g = p.gegenueber()
        cfg = self.m["lane_tot"]
        if (not g or p.ich.rolle == "JUNGLE" or self._ich_weg(p) or not self._tot_seit_eben(p, v, g)
                or g.respawn < cfg["min_sekunden"]):
            return
        if len(self._gegner_tot(p, self.m["zahlen"]["min_sekunden"])) >= 2:
            return
        satz = cfg["mit_platten"] if p.zeit < cfg["platten_bis"] else cfg["ohne_platten"]
        yield Ansage(satz.format(champion=g.champion, sekunden=int(g.respawn)), WICHTIG, "lane_tot", gueltig=6)

    def _level(self, p: Partie, v: Partie):
        cfg = self.m["level"]
        g, g_alt = p.gegenueber(), v.gegenueber()
        ich, ich_alt = p.ich, v.ich
        if g and g_alt and p.ich.rolle != "JUNGLE":
            for stufe, frueh in ((2, True), (6, False)):
                if frueh and p.zeit > cfg["frueh_bis"]:
                    continue
                if g.level >= stufe > g_alt.level and ich.level < stufe:
                    yield Ansage(cfg[f"gegner_{stufe}"].format(champion=g.champion), WICHTIG, f"level{stufe}", gueltig=8)
                elif ich.level >= stufe > ich_alt.level and g.level < stufe:
                    yield Ansage(cfg[f"ich_{stufe}"].format(champion=g.champion), WICHTIG, f"level{stufe}", gueltig=8)
        j, j_alt = p.jungler(gegenteam(p.mein_team)), v.jungler(gegenteam(v.mein_team))
        if j and j_alt and j.level >= 6 > j_alt.level and p.ich.rolle != "JUNGLE":
            yield Ansage(cfg["jungler_6"].format(champion=j.champion), HINWEIS, "jungler6", gueltig=20)

    def _items(self, p: Partie, v: Partie):
        ab = self.m["items"]["legendaer_ab"]
        beobachtet = {s.name for s in (p.gegenueber(), p.jungler(gegenteam(p.mein_team))) if s}
        for s in p.gegner():
            alt = next((x for x in v.spieler if x.name == s.name and x.team == s.team), None)
            if not alt:
                continue
            for item in set(s.items) - set(alt.items):
                name = ddragon.items().get(item, {}).get("name", str(item))
                if tipp := self.item_tipps.get(item):
                    if tipp.get("nur_wenn_ich_heile") and p.heilung < self.m["items"]["heilung_ab"]:
                        continue
                    yield Ansage(tipp["satz"].format(champion=s.champion, item=name), HINWEIS,
                                 f"item:{s.name}:{item}", gueltig=30, sperre=10_000)
                elif s.name in beobachtet and _legendaer(item, ab):
                    yield Ansage(self.m["items"]["fertig"].format(champion=s.champion, item=name), HINWEIS,
                                 f"item:{s.name}:{item}", gueltig=30, sperre=10_000)

    def _gold(self, p: Partie, v: Partie):
        cfg = self.m["gold"]
        if p.gold is None or v.gold is None or self._ich_weg(p) or self._inventar_voll(p):
            return  # im Brunnen kauft er gerade; mit sechs fertigen Items gibt es nichts zu kaufen
        # Solange das Gold liegen bleibt, jede Sekunde anbieten - der Sprechplan
        # laesst es nur alle `erneut_nach` Sekunden durch.
        if p.gold >= cfg["viel"]:
            yield Ansage(cfg["satz_viel"].format(gold=int(p.gold // 100 * 100)), WICHTIG, "gold_viel",
                         gueltig=5, sperre=cfg["erneut_nach_viel"])
        elif p.gold >= cfg["schwelle"]:
            yield Ansage(cfg["satz"].format(gold=int(p.gold // 100 * 100)), HINWEIS, "gold",
                         gueltig=5, sperre=cfg["erneut_nach"])

    def _inventar_voll(self, p: Partie) -> bool:
        """Sechs Plaetze belegt, ohne Trinket und Verbrauchsgueter (Partie 3, 30:25)."""
        it = ddragon.items()
        belegt = [i for i in p.ich.items if i in it and not {"Trinket", "Consumable"} & set(it[i].get("tags", []))]
        return len(belegt) >= 6

    def _leben(self, p: Partie, v: Partie):
        cfg = self.m["leben"]
        m = p.werte.get("maxHealth")
        if not m or self._ich_weg(p):
            self._wenig_leben_seit = None
            return
        anteil = p.werte.get("currentHealth", 0.0) / m
        if anteil >= cfg["unter"]:
            self._wenig_leben_seit = None
            return
        self._wenig_leben_seit = getattr(self, "_wenig_leben_seit", None) or p.zeit
        if p.zeit - self._wenig_leben_seit >= cfg["dauer"]:
            yield Ansage(cfg["satz"].format(prozent=max(1, int(anteil * 100))), WICHTIG, "leben",
                         gueltig=4, sperre=cfg["erneut_nach"])

    def _cs(self, p: Partie, v: Partie):
        cfg = self.m["cs"]
        if p.ich.rolle in ("UTILITY", "JUNGLE"):
            return  # Support farmt nicht; Jungle-CS misst anders
        for minute in cfg["minuten"]:
            if v.zeit < minute * 60 <= p.zeit and ("cs", minute) not in self._gemeldet:
                self._gemeldet.add(("cs", minute))
                cspm = p.ich.cs / (p.zeit / 60)
                g = p.gegenueber()
                kw = dict(minute=minute, cs=p.ich.cs, cspm=f"{cspm:.1f}".replace(".", ","))
                text = (cfg["satz"].format(champion=g.champion, gegner_cs=g.cs, **kw) if g
                        else cfg["satz_ohne_gegner"].format(**kw))
                if cspm < cfg["ziel_pro_minute"]:
                    text += cfg["unter_ziel"]
                yield Ansage(text, HINWEIS, f"cs{minute}", gueltig=40)

    # --- Regeln aus der Minimap ------------------------------------------------

    def _unsichtbar_seit(self, p: Partie, s: Spieler) -> float | None:
        """Fuehrt Buch, seit wann `s` lebendig und unsichtbar ist. Tote zaehlen
        nicht (ihr Icon verschwindet, das ist kein Fehlen)."""
        if s.tot:
            self._tot_bei[s.name] = p.zeit
        if s.tot or self.lage.sichtbar(s):
            self._weg_seit[s.name] = None
        elif self._weg_seit.get(s.name) is None:
            self._weg_seit[s.name] = p.zeit
        return self._weg_seit[s.name]

    def _jungler_gesehen(self, p: Partie, v: Partie):
        if not self.lage or not self.lage.aktiv or p.ich.tot:
            return
        from . import minimap
        cfg = self.m["sicht"]
        j = p.jungler(gegenteam(p.mein_team))
        if not j:
            return
        weg_vorher = self._weg_seit.get(j.name)
        self._unsichtbar_seit(p, j)
        # neu aufgetaucht: jetzt sichtbar, vorher lange genug weg
        if not (self.lage.sichtbar(j) and weg_vorher is not None and p.zeit - weg_vorher >= cfg["neu_nach"]):
            return
        _, x, y = self.lage.gesehen(j)
        ort = minimap.ort(x, y, p.mein_team)
        if "Basis" in ort:
            return
        seite = minimap.seite_der_karte(x, y)
        rolle = p.ich.rolle
        meine_seite = ((rolle == "TOP" and seite == "oben") or (rolle in ("BOTTOM", "UTILITY") and seite == "unten")
                       or (rolle == "MIDDLE" and abs(x - 0.5) + abs(y - 0.5) < 0.35))
        ich = self.lage.gesehen(p.ich)
        nah = bool(ich and self.lage.sichtbar(p.ich) and abs(ich[1] - x) + abs(ich[2] - y) < cfg["nah_ab"])
        in_seinem_jungle = "seinem" in ort
        if nah or (meine_seite and not in_seinem_jungle and rolle != "JUNGLE"):
            yield Ansage(cfg["gefahr"].format(champion=j.champion, ort=ort), SOFORT, "jungler_sicht",
                         gueltig=3, sperre=15)
        elif meine_seite and rolle != "JUNGLE":
            yield Ansage(cfg["seine_seite"].format(champion=j.champion, ort=ort), WICHTIG, "jungler_sicht",
                         gueltig=4, sperre=30)
        elif p.zeit > cfg["lane_phase_bis"] and ("Mitte" in ort or "Mid-Lane" in ort):
            return  # spaet und mittig: keine Kartenseite, die frei waere
        elif text := cfg.get("sicher_spaet" if p.zeit > cfg["lane_phase_bis"] else f"sicher_{rolle}"):
            yield Ansage(text.format(champion=j.champion, ort=ort), WICHTIG, "jungler_sicht", gueltig=5, sperre=40)

    def _lane_fehlt(self, p: Partie, v: Partie):
        if not self.lage or not self.lage.aktiv:
            return
        from . import minimap
        cfg = self.m["sicht"]
        g = p.gegenueber()
        if not g or p.ich.rolle == "JUNGLE":
            return
        seit = self._unsichtbar_seit(p, g)
        if (seit is None or self._ich_weg(p) or not (cfg["fehlt_ab"] <= p.zeit <= cfg["fehlt_bis"])
                or ("gemeldet", g.name, seit) in self._gemeldet):
            return
        zuletzt = self.lage.gesehen(g)
        ich = self.lage.gesehen(p.ich)
        if not zuletzt or not ich or p.zeit - ich[0] > 2:
            return  # er war nie zu sehen, oder du selbst bist nicht auf der Karte zu finden
        if zuletzt[0] < self._tot_bei.get(g.name, -1):
            return  # seit dem Respawn noch nicht gesehen: er laeuft aus seiner Basis zurueck
        if "Basis" in minimap.ort(zuletzt[1], zuletzt[2], p.mein_team) \
                or "Basis" in minimap.ort(ich[1], ich[2], p.mein_team):
            return  # er kauft gerade, oder du bist selbst nicht in der Lane
        abstand = abs(ich[1] - zuletzt[1]) + abs(ich[2] - zuletzt[2])
        if abstand > cfg["fehlt_naehe"]:
            return  # nicht aus deiner Naehe verschwunden - betrifft dich nicht
        # Recall: stand vor dem Verschwinden still - sofort ansagen, das ist ein Fenster
        if p.zeit - seit < 3 and self.lage.stand_still(g):
            self._gemeldet.add(("gemeldet", g.name, seit))
            satz = cfg["recall_mit_platten"] if p.zeit < self.m["lane_tot"]["platten_bis"] else cfg["recall_ohne_platten"]
            yield Ansage(satz.format(champion=g.champion), WICHTIG, "lane_recall", gueltig=6, sperre=30)
            return
        if p.zeit - seit < cfg["fehlt_nach"]:
            return
        if abstand < 0.06 and p.zeit - ich[0] < 2:
            return  # stand direkt bei dir - vermutlich nur verdeckt
        self._gemeldet.add(("gemeldet", g.name, seit))
        yield Ansage(cfg["fehlt"].format(champion=g.champion, sekunden=int(p.zeit - seit)), WICHTIG,
                     "lane_fehlt", gueltig=6, sperre=45)

    def _zauber(self, p: Partie, v: Partie):
        """Flash & Co.: Verbrauch melden, vor Kaempfen erinnern, Rueckkehr melden.
        Quellen: Chat-Pings der Mitspieler, Flash-Spruenge auf der Minimap."""
        if not self.lage or not hasattr(self.lage, "zauber"):
            return
        from .zauber import NAME_DE
        cfg = self.m["zauber"]
        wichtig = {s.name for s in (p.gegenueber(), p.jungler(gegenteam(p.mein_team))) if s}
        for t in self.lage.zauber.aktiv(p.zeit):
            name = NAME_DE.get(t.zauber, t.zauber)
            if not t.gemeldet:
                t.gemeldet = True
                satz = cfg["neu_chat" if t.quelle == "Chat" else "neu_minimap"]
                yield Ansage(satz.format(champion=t.champion, zauber=name,
                                         dauer=_minuten(t.zurueck - p.zeit)), WICHTIG,
                             f"zauber:{t.name}:{t.zauber}", gueltig=10, sperre=30)
        # vor einem Kampf: Gegner ohne Flash nah bei dir
        ich = self.lage.gesehen(p.ich) if self.lage.aktiv else None
        if ich and not self._ich_weg(p) and p.zeit - ich[0] < 2:
            for s in p.gegner():
                rest = self.lage.zauber.fehlt(s, "SummonerFlash", p.zeit)
                g = self.lage.gesehen(s)
                if (rest and rest > 15 and g and self.lage.sichtbar(s)
                        and abs(g[1] - ich[1]) + abs(g[2] - ich[2]) < cfg["nah"]):
                    yield Ansage(cfg["kampf"].format(champion=s.champion, dauer=_minuten(rest)), WICHTIG,
                                 f"ohneflash:{s.name}", gueltig=4, sperre=cfg["kampf_erneut"])
        # Rueckkehr beim Lane-Gegner und Jungler
        for t in list(self.lage.zauber.timer.values()):
            if t.name in wichtig and t.zauber == "SummonerFlash" and v.zeit < t.zurueck <= p.zeit:
                yield Ansage(cfg["zurueck"].format(champion=t.champion), HINWEIS, f"flashzurueck:{t.name}",
                             gueltig=15, sperre=30)

    def _tod(self, p: Partie, v: Partie):
        if not (p.ich.tot and not v.ich.tot):
            return
        cfg = self.m["tod"]
        kill = next((e for e in reversed(p.ereignisse)
                     if e.art == "ChampionKill" and e.opfer is p.ich and e.zeit > v.zeit - 3), None)
        if kill is None:
            return
        beteiligt = [s for s in [kill.taeter, *(p.spieler_namens(n) for n in kill.daten.get("Assisters", []))] if s]
        j = p.jungler(gegenteam(p.mein_team))
        if kill.taeter is None and struktur(kill.daten.get("KillerName", "")):
            text = cfg["turm"]
        elif j and p.ich.rolle != "JUNGLE" and any(s is j for s in beteiligt):
            text = cfg["gank"].format(champion=j.champion)
        elif len(beteiligt) >= 2:
            text = cfg["ueberzahl"].format(anzahl=len(beteiligt))
        elif kill.taeter:
            t = kill.taeter
            gruende = []
            if t.level > p.ich.level:
                gruende.append(f"{t.level - p.ich.level} Level vorne")
            if t.item_gold - p.ich.item_gold >= 500:
                gruende.append(f"{(t.item_gold - p.ich.item_gold) // 100 * 100} Gold an Items vorne")
            text = (cfg["solo_nachteil"].format(champion=t.champion, grund=" und ".join(gruende)) if gruende
                    else cfg["solo"].format(champion=t.champion))
        else:
            return
        yield Ansage(text, WICHTIG, "tod", gueltig=15, sperre=5)
