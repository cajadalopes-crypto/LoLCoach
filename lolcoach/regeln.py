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
from .zustand import Partie, Spieler, gegenteam

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


def _satz(abschnitt: dict, p: Partie) -> str:
    """Satz fuer die eigene Rolle; ein Toplaner ohne Teleport bekommt die
    Variante `TOP_ohne_tp`, wenn es sie gibt."""
    rolle = p.ich.rolle
    if rolle == "TOP" and "SummonerTeleport" not in p.ich.zauber and "TOP_ohne_tp" in abschnitt:
        return abschnitt["TOP_ohne_tp"]
    return abschnitt.get(rolle, abschnitt.get("alle", ""))


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


def _legendaer(item_id: int, ab: int) -> bool:
    e = ddragon.items().get(item_id)
    return bool(e and not e.get("into") and e["gold"]["total"] >= ab and "Boots" not in e.get("tags", []))


class Regelwerk:
    def __init__(self):
        self.m = wissen.lade("makro")
        self.item_tipps = {i: v for v in wissen.lade("items").values()
                           if isinstance(v, dict) for i in v["ids"]}
        self.vorher: Partie | None = None
        self._gemeldet: set = set()  # einmalige Dinge (Vorwarnung je Spawn, CS je Minute)

    def pruefe(self, p: Partie) -> list[Ansage]:
        v, self.vorher = self.vorher, p
        if not p.ich or v is None or not v.ich or p.zeit < v.zeit:
            return []
        ansagen: list[Ansage] = []
        for regel in (self._vorwarnung, self._zahlen, self._jungler_tot, self._lane_tot,
                      self._level, self._items, self._gold, self._cs, self._tod):
            for a in regel(p, v) or ():
                a.zeit = p.zeit
                ansagen.append(a)
        return ansagen

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
            if text := _satz(abschnitt, p):
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
            objs = self._objectives(p)
            if objs:
                text = z["vorteil_objective"].format(anzahl=len(tot), sekunden=fenster,
                                                     objective=_objective_name(objs[0], p))
                yield Ansage(text, SOFORT, f"jetzt:{objs[0]}", gueltig=6, sperre=20)
            else:
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
        objs = self._objectives(p, bis=j.respawn - 10)
        if objs and not p.ich.tot:
            nah = p.ich.rolle in self.m["seiten"][objs[0]]
            text = self.m["jungler_tot_objective"]["nah" if nah else "fern"].format(
                champion=j.champion, sekunden=int(j.respawn), objective=_objective_name(objs[0], p))
            yield Ansage(text, SOFORT if nah else WICHTIG, f"jetzt:{objs[0]}", gueltig=6, sperre=20)
        elif text := _satz(cfg, p):
            yield Ansage(text.format(champion=j.champion, sekunden=int(j.respawn)), WICHTIG,
                         "jungler_tot", gueltig=8)

    def _lane_tot(self, p: Partie, v: Partie):
        g = p.gegenueber()
        cfg = self.m["lane_tot"]
        if (not g or p.ich.rolle == "JUNGLE" or p.ich.tot or not self._tot_seit_eben(p, v, g)
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
        if p.gold is None or v.gold is None or p.ich.tot:
            return
        # Solange das Gold liegen bleibt, jede Sekunde anbieten - der Sprechplan
        # laesst es nur alle `erneut_nach` Sekunden durch.
        if p.gold >= cfg["schwelle"]:
            viel = p.gold >= cfg["viel"]
            yield Ansage(cfg["satz_viel" if viel else "satz"].format(gold=int(p.gold // 100 * 100)),
                         WICHTIG if viel else HINWEIS, "gold", gueltig=5, sperre=cfg["erneut_nach"])

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
        if j and p.ich.rolle != "JUNGLE" and any(s is j for s in beteiligt):
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
