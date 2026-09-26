"""Das Regelwerk: aus zwei aufeinanderfolgenden Zustaenden werden Ansagen.

Jede Regel schaut auf den Wechsel (vorher -> jetzt), damit sie genau einmal
ausloest - im Moment, in dem etwas passiert, nicht in jeder Sekunde danach.
Schwellen und Saetze stehen in `wissen/makro.toml` und `wissen/items.toml`.

Ob und wann eine Ansage gesprochen wird, entscheidet nicht die Regel,
sondern der Sprechplan (Vorrang, Pausen, keine Wiederholung).
"""
from __future__ import annotations

from dataclasses import dataclass

from . import bewertung, ddragon, komponist, wissen
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
    situativ: bool = False  # hat Vorlauf: der Stratege darf sie aus der Lage neu formulieren
    kontext: str = ""       # Fakten fuer den Strategen statt der Lage (z. B. Todesanalyse)
    frist: float | None = None  # so lange darf der Stratege formulieren (sonst VEREDELN_HOECHSTENS)


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


def _namen(spieler) -> str:
    """'Zaahen und Anivia', 'Zaahen, Anivia und Swain'."""
    n = [s.champion for s in spieler]
    return n[0] if len(n) == 1 else ", ".join(n[:-1]) + " und " + n[-1]


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
        self.ult_warnungen: dict[str, str] = {}        # Champion -> ein Satz, was seine Ult bedeutet (Spielakte)
        from .todesanalyse import Rueckblick
        self.rueckblick = Rueckblick()                 # die letzten 45 s - fuer die Todesanalyse
        self._in_grube: dict[tuple[str, str], float] = {}   # (Jungler, Objective) -> seit wann in der Grube
        self._am_pit: dict[str, float] = {}                 # Objective -> seit wann zwei Mitspieler dort stehen
        self._obj_gesagt: dict[tuple[str, str], float] = {}  # (Objective, team/anlauf/gegner) -> zuletzt gesagt
        self._spikes: list[str] = []                   # eben fertig gewordene eigene Items (noch nicht gesagt)
        self._spike_bei = 0.0
        self.b: bewertung.Bewertung | None = None      # die Lagebewertung dieses Takts (bewertung.py)
        self._zauber_gesagt: dict[str, float] = {}      # Spielername -> zuletzt ein Verbrauch gemeldet

    def pruefe(self, p: Partie, lage=None) -> list[Ansage]:
        """`lage`: Lagebild aus der Minimap (lage.Lagebild) oder None ohne Bild."""
        v, self.vorher = self.vorher, p
        self.lage = lage
        if not p.ich or v is None or not v.ich or p.zeit < v.zeit:
            return []
        ansagen: list[Ansage] = []
        if not p.ich.tot:
            self.rueckblick.merke(p, lage)
        self.b = None
        if lage is not None and getattr(lage, "aktiv", False):
            try:
                self.b = bewertung.bewerte(p, lage)
            except Exception as e:   # die Bewertung darf keine Regel mitreissen - dann gelten die alten Saetze
                if not getattr(self, "_bewertung_fehler", False):
                    self._bewertung_fehler = True
                    print(f"!! Bewertung: {type(e).__name__}: {e}", flush=True)
        for regel in (self._vorwarnung, self._zahlen, self._jungler_tot, self._lane_tot,
                      self._level, self._items, self._gold, self._cs, self._tod,
                      self._jungler_gesehen, self._lane_fehlt, self._leben, self._zauber, self._anlauf,
                      self._ward, self._recall_fenster, self._tief_ohne_sicht, self._kontrollauge,
                      self._objective_start):
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

    def _gl(self, s: Spieler | None):
        """Die Bewertung dieses Gegners (bewertung.GegnerLage) oder None."""
        if self.b is None or s is None:
            return None
        return next((g for g in self.b.gegner if g.s.name == s.name), None)

    def _richtung(self, s: Spieler, p: Partie) -> str | None:
        """Wohin `s` zuletzt lief (aus dem Positionsverlauf der Minimap), in Worten."""
        v = getattr(self.lage, "verlauf", {}).get((s.name, s.team))
        if not v or len(v) < 2:
            return None
        t1, x1, y1 = v[-1]
        frueher = [(t, x, y) for t, x, y in v if t <= t1 - 2.0]
        if not frueher:
            return None
        _, x0, y0 = frueher[-1]
        dx, dy = x1 - x0, y1 - y0
        weg = (dx * dx + dy * dy) ** 0.5
        if weg < 0.015:
            return None
        from . import minimap
        k = 0.12 / weg
        ziel = minimap.ort(min(max(x1 + dx * k, 0.0), 1.0), min(max(y1 + dy * k, 0.0), 1.0), p.mein_team)
        return komponist.wohin(ziel)

    def _ich_in_basis(self, p: Partie) -> bool:
        if not self.lage or not self.lage.aktiv:
            return False
        from . import minimap
        g = self.lage.gesehen(p.ich)
        return bool(g and p.zeit - g[0] < 3 and "Basis" in minimap.ort(g[1], g[2], p.mein_team))

    def _ich_weg(self, p: Partie) -> bool:
        return p.ich.tot or self._ich_in_basis(p)

    def _platten_moeglich(self, p: Partie) -> bool:
        """Steht in deiner Lane noch ein gegnerischer Turm (aussen, innen, Inhib)?
        Seit 26.1 haben alle Platten bis zum Turmfall."""
        lane = {"TOP": "Top", "MIDDLE": "Mid", "BOTTOM": "Bot", "UTILITY": "Bot"}.get(p.ich.rolle)
        if not lane:
            return False
        gefallen = 0
        for e in p.kills_von("TurretKilled"):
            st = struktur(e.daten.get("TurretKilled", ""))
            if st and st.team != p.mein_team and st.lane == lane and st.stufe in ("aussen", "innen", "Inhib"):
                gefallen += 1
        return gefallen < 3

    def _lebend(self, p: Partie) -> tuple[int, int]:
        """(lebende eigene, lebende Gegner). Leben der Mitspieler kennt die API nicht."""
        return (sum(1 for s in p.team(p.mein_team) if not s.tot),
                sum(1 for s in p.gegner() if not s.tot))

    def _objective_machbar(self, p: Partie, schl: str, vorsprung: int) -> bool:
        wir, die = self._lebend(p)
        noetig = self.m["zahlen"]["lebend_baron" if schl == "baron" else "lebend_drache"]
        if wir - die < vorsprung or wir < noetig:
            return False
        fit = self._fit(p)
        return fit is None or fit >= noetig  # ohne HUD-Daten zaehlt nur, wer lebt

    def _fit(self, p: Partie) -> int | None:
        """Wie viele von euch leben UND haben genug Leben (HUD-Leiste + eigene Werte)?
        None, wenn die Leiste gerade nicht gelesen werden konnte."""
        if not self.lage or not hasattr(self.lage, "leben"):
            return None
        schwelle = self.m["zahlen"]["fit_ab"]
        werte = [self.lage.leben(s, p.zeit) for s in p.team(p.mein_team) if s is not p.ich and not s.tot]
        if any(w is None for w in werte):
            return None
        m = p.werte.get("maxHealth")
        ich_fit = not p.ich.tot and (not m or p.werte.get("currentHealth", 0) / m >= schwelle)
        return sum(1 for w in werte if w >= schwelle) + (1 if ich_fit else 0)

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
            if (text := self._satz(abschnitt, p)) and self.b is not None and not self._ich_weg(p):
                tp = "SummonerTeleport" in p.ich.zauber or (
                    p.ich.rolle == "TOP" and p.zeit >= self.m["rollenquest"]["top_teleport_spaetestens"])
                text = komponist.vorwarnung(self.b, schl, p.ich.rolle, abschnitt is self.m["vorwarnung"].get("drache_seele"),
                                            p.ich.rolle in self.m["seiten"][schl], tp)
            if text:
                yield Ansage(text, WICHTIG, f"vorwarnung:{schl}", gueltig=25, situativ=True)

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
            namen = [s.champion for s in sorted(tot, key=lambda s: s.respawn)]
            if objs:
                text = (komponist.zahlen(self.b, namen, fenster, objs[0], wir, die) if self.b is not None
                        else z["vorteil_objective"].format(anzahl=len(tot), sekunden=fenster,
                                                           objective=_objective_name(objs[0], p)))
                yield Ansage(text, SOFORT, f"jetzt:{objs[0]}", gueltig=6, sperre=20)
            elif wir > die:
                text = (komponist.zahlen(self.b, namen, fenster, None, wir, die) if self.b is not None
                        else z["vorteil_turm"].format(anzahl=len(tot), sekunden=fenster))
                yield Ansage(text, SOFORT, "zahlen", gueltig=6, sperre=20)
        eigene = [s for s in p.team(p.mein_team) if s.tot and s.respawn >= z["min_sekunden"]]
        vorher_eigene = [s for s in v.team(v.mein_team) if s.tot and s.respawn >= z["min_sekunden"]]
        if len(eigene) >= 2 and len(eigene) > len(vorher_eigene) and not p.ich.tot:
            fenster = int(min(s.respawn for s in eigene))
            text = (komponist.zahlen_nachteil(self.b, [s.champion for s in eigene], fenster) if self.b is not None
                    else self.m["zahlen"]["nachteil"].format(anzahl=5 - len(eigene), sekunden=fenster))
            yield Ansage(text, SOFORT, "zahlen_nachteil", gueltig=6, sperre=30)

    def _jungler_tot(self, p: Partie, v: Partie):
        j = p.jungler(gegenteam(p.mein_team))
        cfg = self.m["jungler_tot"]
        if not j or not self._tot_seit_eben(p, v, j) or j.respawn < cfg["min_sekunden"]:
            return
        if len(self._gegner_tot(p, self.m["zahlen"]["min_sekunden"])) >= 2:
            return  # die Zahlen-Regel sagt es besser
        objs = [o for o in self._objectives(p, bis=j.respawn - 10) if self._objective_machbar(p, o, 0)]
        mit_b = self.b is not None and p.ich.rolle != "JUNGLE" and not self._ich_weg(p)
        if objs and not self._ich_weg(p):
            nah = p.ich.rolle in self.m["seiten"][objs[0]]
            text = (komponist.jungler_tot(self.b, int(j.respawn), objs[0], nah, self._platten_moeglich(p)) if mit_b
                    else self.m["jungler_tot_objective"]["nah" if nah else "fern"].format(
                        champion=j.champion, sekunden=int(j.respawn), objective=_objective_name(objs[0], p)))
            yield Ansage(text, SOFORT if nah else WICHTIG, f"jetzt:{objs[0]}", gueltig=6, sperre=20)
        elif mit_b:
            yield Ansage(komponist.jungler_tot(self.b, int(j.respawn), None, False, self._platten_moeglich(p)),
                         WICHTIG, "jungler_tot", gueltig=8)
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
        if self.b is not None:
            text = komponist.lane_tot(self.b, g.champion, int(g.respawn), self._platten_moeglich(p))
        else:
            satz = cfg["mit_platten"] if self._platten_moeglich(p) else cfg["ohne_platten"]
            text = satz.format(champion=g.champion, sekunden=int(g.respawn))
        yield Ansage(text, WICHTIG, "lane_tot", gueltig=6)

    def _level(self, p: Partie, v: Partie):
        cfg = self.m["level"]
        g, g_alt = p.gegenueber(), v.gegenueber()
        ich, ich_alt = p.ich, v.ich
        if g and g_alt and p.ich.rolle != "JUNGLE":
            for stufe, frueh in ((2, True), (6, False)):
                if frueh and p.zeit > cfg["frueh_bis"]:
                    continue
                gl = self._gl(g)
                if g.level >= stufe > g_alt.level and ich.level < stufe:
                    text = (komponist.level(self.b, stufe, False, gl) if gl
                            else cfg[f"gegner_{stufe}"].format(champion=g.champion))
                    if stufe == 6 and (warnung := self.ult_warnungen.get(g.champion)):
                        text += " " + warnung
                    yield Ansage(text, WICHTIG, f"level{stufe}", gueltig=8)
                elif ich.level >= stufe > ich_alt.level and g.level < stufe:
                    text = (komponist.level(self.b, stufe, True, gl) if gl
                            else cfg[f"ich_{stufe}"].format(champion=g.champion))
                    yield Ansage(text, WICHTIG, f"level{stufe}", gueltig=8)
        j, j_alt = p.jungler(gegenteam(p.mein_team)), v.jungler(gegenteam(v.mein_team))
        if j and j_alt and j.level >= 6 > j_alt.level and p.ich.rolle != "JUNGLE":
            text = cfg["jungler_6"].format(champion=j.champion)
            if warnung := self.ult_warnungen.get(j.champion):
                text += " " + warnung
            yield Ansage(text, HINWEIS, "jungler6", gueltig=20)

    def _items(self, p: Partie, v: Partie):
        ab = self.m["items"]["legendaer_ab"]
        # eigener Powerspike: im Brunnen gekauft, gesagt wird es, bevor er wieder in der Lane ist.
        # Mehrere Kaeufe eines Besuchs (kommen in aufeinanderfolgenden Takten) werden ein Satz.
        for item in set(p.ich.items) - set(v.ich.items):
            if _legendaer(item, ab) and ("spike", item) not in self._gemeldet:
                self._gemeldet.add(("spike", item))
                self._spikes.append(ddragon.items().get(item, {}).get("name", str(item)))
                self._spike_bei = p.zeit
        if self._spikes and p.zeit - self._spike_bei >= 3:
            namen, self._spikes = " und ".join(self._spikes), []
            yield Ansage(self.m["items"]["ich_fertig"].format(item=namen), WICHTIG, f"spike:{namen}",
                         gueltig=40, sperre=10_000, situativ=True)
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
        if p.gold is None or v.gold is None or self._ich_weg(p) or self._inventar_voll(p) \
                or p.zeit - getattr(self, "_recallfenster_bei", -1e9) < 120:
            return  # im Brunnen kauft er gerade; mit sechs fertigen Items gibt es nichts zu kaufen
        # Solange das Gold liegen bleibt, jede Sekunde anbieten - der Sprechplan
        # laesst es nur alle `erneut_nach` Sekunden durch.
        if p.gold >= cfg["viel"]:
            text = (komponist.recall(self.b, "viel") if self.b is not None
                    else cfg["satz_viel"].format(gold=int(p.gold // 100 * 100)))
            yield Ansage(text, WICHTIG, "gold_viel", gueltig=5, sperre=cfg["erneut_nach_viel"])
        elif p.gold >= cfg["schwelle"]:
            text = (komponist.recall(self.b, "gold") if self.b is not None
                    else cfg["satz"].format(gold=int(p.gold // 100 * 100)))
            yield Ansage(text, HINWEIS, "gold", gueltig=5, sperre=cfg["erneut_nach"])

    def _kontrollauge(self, p: Partie, v: Partie):
        """Nach dem Einkauf ohne Kontroll-Auge im Inventar: eins mitnehmen (75 Gold). Wardscore
        in den ersten drei Partien 0,08-0,89 je Minute - Sicht ist die billigste Versicherung
        gegen genau die Ganks, an denen Partie 3 hing."""
        cfg = self.m["kontrollauge"]
        if p.ich.tot or p.gold is None or v.gold is None:
            return
        if v.gold - p.gold >= 250:
            self._kauf_bei = p.zeit
            return
        bei = getattr(self, "_kauf_bei", None)
        if bei is None or not (cfg["nach"] <= p.zeit - bei <= cfg["nach"] + 8) or p.zeit < cfg["ab"]:
            return
        self._kauf_bei = None
        it = ddragon.items()
        plaetze = [i for i in p.ich.items if i in it and "Trinket" not in it[i].get("tags", [])]
        if cfg["item"] in p.ich.items or p.gold < 75 or len(plaetze) >= 6:
            return
        yield Ansage(cfg["satz"], HINWEIS, "kontrollauge", gueltig=10, sperre=cfg["sperre"])

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
            prozent = max(1, int(anteil * 100))
            text = komponist.leben(self.b, prozent) if self.b is not None else cfg["satz"].format(prozent=prozent)
            yield Ansage(text, WICHTIG, "leben", gueltig=4, sperre=cfg["erneut_nach"])

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
        jl = self._gl(j) if rolle != "JUNGLE" else None
        platten = self._platten_moeglich(p)
        if nah or (meine_seite and not in_seinem_jungle and rolle != "JUNGLE"):
            text = (komponist.jungler_gesehen(self.b, jl, "gefahr", platten) if jl
                    else cfg["gefahr"].format(champion=j.champion, ort=ort))
            yield Ansage(text, SOFORT, "jungler_sicht", gueltig=3, sperre=15)
        elif meine_seite and rolle != "JUNGLE":
            text = (komponist.jungler_gesehen(self.b, jl, "seite", platten) if jl
                    else cfg["seine_seite"].format(champion=j.champion, ort=ort))
            yield Ansage(text, WICHTIG, "jungler_sicht", gueltig=4, sperre=30)
        elif p.zeit > cfg["lane_phase_bis"] and ("Mitte" in ort or "Mid-Lane" in ort):
            return  # spaet und mittig: keine Kartenseite, die frei waere
        elif jl and p.zeit <= cfg["lane_phase_bis"]:
            yield Ansage(komponist.jungler_gesehen(self.b, jl, "sicher", platten), WICHTIG, "jungler_sicht",
                         gueltig=5, sperre=40)
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
            satz = cfg["recall_mit_platten"] if self._platten_moeglich(p) else cfg["recall_ohne_platten"]
            yield Ansage(satz.format(champion=g.champion), WICHTIG, "lane_recall", gueltig=6, sperre=30)
            return
        if p.zeit - seit < cfg["fehlt_nach"]:
            return
        if abstand < 0.06 and p.zeit - ich[0] < 2:
            return  # stand direkt bei dir - vermutlich nur verdeckt
        self._gemeldet.add(("gemeldet", g.name, seit))
        gl = self._gl(g)
        text = (komponist.lane_fehlt(self.b, gl, int(p.zeit - seit), self._platten_moeglich(p), self._richtung(g, p))
                if gl else cfg["fehlt"].format(champion=g.champion, sekunden=int(p.zeit - seit)))
        yield Ansage(text, WICHTIG, "lane_fehlt", gueltig=6, sperre=45)

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
                self._zauber_gesagt[t.name] = p.zeit
                gl = self._gl(next((s for s in p.gegner() if s.name == t.name), None))
                if gl:
                    text = komponist.zauber_neu(self.b, gl, "Ult" if t.zauber == "R" else name,
                                                t.zurueck - p.zeit, t.quelle)
                else:
                    satz = cfg["neu_ult" if t.zauber == "R" else "neu_chat" if t.quelle == "Chat" else "neu_minimap"]
                    text = satz.format(champion=t.champion, zauber=name, dauer=_minuten(t.zurueck - p.zeit))
                yield Ansage(text, WICHTIG, f"zauber:{t.name}:{t.zauber}", gueltig=10, sperre=30)
        # vor einem Kampf: Gegner ohne Flash nah bei dir
        ich = self.lage.gesehen(p.ich) if self.lage.aktiv else None
        if ich and not self._ich_weg(p) and p.zeit - ich[0] < 2:
            for s in p.gegner():
                if p.zeit - self._zauber_gesagt.get(s.name, -1e9) < 60:
                    continue   # eben erst gemeldet - der Satz sagte schon, was es heisst
                rest = self.lage.zauber.fehlt(s, "SummonerFlash", p.zeit)
                g = self.lage.gesehen(s)
                nah = bool(g and self.lage.sichtbar(s) and abs(g[1] - ich[1]) + abs(g[2] - ich[2]) < cfg["nah"])
                if rest and rest > 15 and nah:
                    gl = self._gl(s)
                    text = (komponist.kein_flash_nah(self.b, gl, rest) if gl
                            else cfg["kampf"].format(champion=s.champion, dauer=_minuten(rest)))
                    yield Ansage(text, WICHTIG, f"ohneflash:{s.name}", gueltig=4, sperre=cfg["kampf_erneut"])
                ult = self.lage.zauber.fehlt(s, "R", p.zeit)
                if ult and ult > 10 and nah:
                    yield Ansage(cfg["kampf_ult"].format(champion=s.champion, dauer=_minuten(ult)), WICHTIG,
                                 f"ohneult:{s.name}", gueltig=4, sperre=cfg["kampf_erneut"])
        # Rueckkehr beim Lane-Gegner und Jungler
        for t in list(self.lage.zauber.timer.values()):
            if t.name in wichtig and t.zauber == "SummonerFlash" and v.zeit < t.zurueck <= p.zeit:
                yield Ansage(cfg["zurueck"].format(champion=t.champion), HINWEIS, f"flashzurueck:{t.name}",
                             gueltig=15, sperre=30)

    def _anlauf(self, p: Partie, v: Partie):
        """Gegner laufen sichtbar auf dich zu (Positionsverlauf der Minimap).
        Carlos: "Wenn ich im Late Game die Welle pushe, musst du mir sagen, dass der und der
        auf dem Weg ist." In der Lane-Phase zaehlt der Lane-Gegner nicht (der steht immer da)."""
        if not self.lage or not self.lage.aktiv or self._ich_weg(p):
            return
        from . import minimap
        cfg = self.m["anlauf"]
        ich = self.lage.gesehen(p.ich)
        if not ich or p.zeit - ich[0] > 1.5:
            return
        pos = (ich[1], ich[2])
        g = p.gegenueber()
        kommen = []
        for s in p.gegner():
            if s.tot or not self.lage.sichtbar(s):
                continue
            if g and s is g and p.zeit < cfg["ab"]:
                continue
            sg = self.lage.gesehen(s)
            abstand = abs(sg[1] - pos[0]) + abs(sg[2] - pos[1])
            naeher = self.lage.naehert_sich(s, pos, p.zeit)
            if naeher is not None and naeher >= cfg["naeher_um"] and cfg["nah_min"] <= abstand <= cfg["weit"]:
                kommen.append((s, minimap.woher(minimap.ort(sg[1], sg[2], p.mein_team))))
        mit_lage = [(gl, o) for s, o in kommen if (gl := self._gl(s))]
        if kommen and len(mit_lage) == len(kommen):
            text = komponist.anlauf(self.b, mit_lage)
            schl = "anlauf" if len(kommen) >= 2 else f"anlauf:{kommen[0][0].name}"
            yield Ansage(text, SOFORT, schl, gueltig=3, sperre=cfg["sperre"])
        elif len(kommen) >= 2:
            yield Ansage(cfg["mehrere"].format(anzahl=len(kommen), namen=", ".join(s.champion for s, _ in kommen)),
                         SOFORT, "anlauf", gueltig=3, sperre=cfg["sperre"])
        elif kommen:
            s, ort = kommen[0]
            yield Ansage(cfg["einer"].format(champion=s.champion, ort=ort), SOFORT, f"anlauf:{s.name}",
                         gueltig=3, sperre=cfg["sperre"])

    def _ward(self, p: Partie, v: Partie):
        """Ward-Vorschlag, wenn du an einer Stelle vorbeilaeufst, die JETZT zaehlt:
        vor einem Objective die Grube, in der Lane-Phase der Gank-Weg, wenn der gegnerische
        Jungler lange nicht zu sehen war. (Carlos: "du laeufst gerade vorbei, setz ein Ward -
        intelligent mit Position, Laufweg und Spielstand".)"""
        if not self.lage or not self.lage.aktiv or self._ich_weg(p):
            return
        cfg, w = self.m["ward"], wissen.lade("wards")
        ich = self.lage.gesehen(p.ich)
        if not ich or p.zeit - ich[0] > 1.5 or p.zeit < cfg["ab"]:
            return
        # Was zaehlt gerade?
        anlaesse = {}
        for schl, zweck in (("drache", "drache"), ("baron", "baron"), ("herold", "baron")):
            n = p.naechster_spawn(schl)
            if n is not None and 0 <= n - p.zeit <= cfg["objective_vorlauf"]:
                name = {"drache": "Drache", "baron": "Baron", "herold": "Herold"}[schl]
                anlaesse[zweck] = cfg["satz_objective"].format(objective=name, sekunden=int(n - p.zeit))
        j = p.jungler(gegenteam(p.mein_team))
        if j and not j.tot and p.zeit < self.m["sicht"]["lane_phase_bis"] and p.ich.rolle != "JUNGLE":
            g = self.lage.gesehen(j)
            weg = p.zeit - g[0] if g else p.zeit
            if weg >= cfg["jungler_weg_ab"]:
                zweck = {"TOP": "lane_top", "MIDDLE": "lane_mid", "BOTTOM": "lane_bot", "UTILITY": "lane_bot"}.get(p.ich.rolle)
                if zweck:
                    anlaesse[zweck] = cfg["satz_gank"].format(champion=j.champion, sekunden=int(weg))
        if not anlaesse:
            return
        blau = p.mein_team == "ORDER"
        for st in w["stelle"]:
            zweck = next((z for z in st["wofuer"] if z in anlaesse), None)
            if not zweck or abs(st["x"] - ich[1]) + abs(st["y"] - ich[2]) > w["radius"]:
                continue
            if st["seite"] == "fluss":
                ort = f"am {st['name']}"
            else:
                eigen = (st["seite"] == "blau") == blau
                ort = f"an {'deinem' if eigen else 'seinem'} {st['name']}"
            yield Ansage(cfg["satz"].format(ort=ort, grund=anlaesse[zweck]), HINWEIS,
                         f"ward:{st['name']}:{st['seite']}", gueltig=6, sperre=cfg["erneut_nach"])
            return

    GRUBEN = {"drache": (0.675, 0.71, "Drachengrube"), "baron": (0.325, 0.29, "Baron-Grube"),
              "herold": (0.325, 0.29, "Baron-Grube"), "larven": (0.325, 0.29, "Baron-Grube")}   # an map11 vermessen

    def _objective_start(self, p: Partie, v: Partie):
        """Dein Team (oder der Gegner) faengt ein Objective an - aus den Positionen an der Grube:
        zwei Mitspieler dort, der Jungler allein in der Grube, drei laufen darauf zu, oder Gegner
        sichtbar dort. Dazu, was du tun sollst (Rolle, Teleport, Abstand)."""
        if not self.lage or not self.lage.aktiv or p.ich.tot:
            return
        cfg = self.m["objective_start"]
        ich = self.lage.gesehen(p.ich)
        ich_pos = (ich[1], ich[2]) if ich and p.zeit - ich[0] < 3 else None

        def nah(s, gx, gy, r):
            g = self.lage.gesehen(s)
            return bool(g and p.zeit - g[0] < 2 and abs(g[1] - gx) + abs(g[2] - gy) <= r)

        def frei(schl: str, art: str) -> bool:
            """Wieder sagen erst nach `erneut_nach` s - einmal je Spawn reichte nicht: Partie 7, Ashe und
            Xerath 10:57 am Drachen, wieder weg; als Vi und Ashe 16:15 zurueckkamen, schwieg der Coach."""
            return p.zeit - self._obj_gesagt.get((schl, art), -1e9) >= cfg["erneut_nach"]

        for schl in _lebende_objectives(p):
            gx, gy, grube = self.GRUBEN[schl]
            ich_weit = abs(ich_pos[0] - gx) + abs(ich_pos[1] - gy) if ich_pos else 1.0
            name = _objective_name(schl, p)
            # die Gegner, wenn sie dort zu sehen sind - auch wenn du in der Naehe bist (Partie 7, 17:20: 0,14
            # von der Herold-Grube, Wukong und Ashe darin - und Stille); nur nicht, wenn du selbst drin stehst
            gegner = [s for s in p.gegner() if not s.tot and self.lage.sichtbar(s) and nah(s, gx, gy, cfg["radius"])]
            if len(gegner) >= 2 and ich_weit > cfg["eng"] and frei(schl, "gegner"):
                self._obj_gesagt[(schl, "gegner")] = p.zeit
                yield Ansage(cfg["gegner"].format(namen=_namen(gegner), grube=grube, objective=name), WICHTIG,
                             f"objgegner:{schl}", gueltig=15, sperre=20)
            if ich_weit <= cfg["ich_nah"]:
                continue   # dein Team faengt an, und du stehst selbst dort - das siehst du
            freunde = [s for s in p.team(p.mein_team) if s is not p.ich and not s.tot]
            dort = [s for s in freunde if nah(s, gx, gy, cfg["radius"])]
            j = p.jungler(p.mein_team)
            if j is not None and j is not p.ich and nah(j, gx, gy, cfg["eng"]):
                self._in_grube.setdefault((j.name, schl), p.zeit)
            elif j is not None:
                self._in_grube.pop((j.name, schl), None)
            if len(dort) >= 2:   # zwei an der Grube - aber nicht nur auf dem Weg durch den Fluss: 2 s bleiben
                self._am_pit.setdefault(schl, p.zeit)
            else:
                self._am_pit.pop(schl, None)
            text = None
            if (len(dort) >= 2 and p.zeit - self._am_pit.get(schl, p.zeit) >= cfg["bleiben"]
                    and frei(schl, "team")):
                self._obj_gesagt[(schl, "team")] = p.zeit
                text = cfg["team"].format(objective=name, grube=grube, namen=_namen(dort))
            elif (j is not None and p.zeit - self._in_grube.get((j.name, schl), p.zeit) >= cfg["jungler_ab"]
                  and frei(schl, "team")):
                self._obj_gesagt[(schl, "team")] = p.zeit
                text = cfg["jungler"].format(jungler=j.champion, objective=name)
            elif frei(schl, "anlauf") and frei(schl, "team"):
                laufen = [s for s in freunde if nah(s, gx, gy, cfg["anlauf_nah"])
                          and (self.lage.naehert_sich(s, (gx, gy), p.zeit) or 0) >= 0.03]
                if len(laufen) >= cfg["anlauf_ab"]:
                    self._obj_gesagt[(schl, "anlauf")] = p.zeit
                    text = cfg["anlauf"].format(grube=grube, objective=name)
            if text:
                dazu = cfg["dazu"]["nah"] if ich_weit <= cfg["hin_bis"] else self._satz(cfg["dazu"], p)
                if self.b is not None:
                    tp = "SummonerTeleport" in p.ich.zauber or (
                        p.ich.rolle == "TOP" and p.zeit >= self.m["rollenquest"]["top_teleport_spaetestens"])
                    dazu = komponist.obj_dazu(self.b, ich_weit <= cfg["hin_bis"], tp)
                yield Ansage(f"{text} {dazu}".strip(), WICHTIG, f"objstart:{schl}", gueltig=15, sperre=20)

    def _tief_ohne_sicht(self, p: Partie, v: Partie):
        """Tief auf seiner Seite, waehrend Gegner (oder in der Lane-Phase der Jungler) lange
        nicht zu sehen sind: zurueck, bis du sie siehst. Die Lektion, die das Review aus vier
        Toden von Partie 3 zog - live gesagt, bevor der fuenfte passiert."""
        if not self.lage or not self.lage.aktiv or self._ich_weg(p):
            return
        from . import minimap
        cfg = self.m["tief"]
        ich = self.lage.gesehen(p.ich)
        if p.zeit < cfg["ab"] or not ich or p.zeit - ich[0] > 1.5:
            return
        x, y = ich[1], ich[2]
        if "Basis" in minimap.ort(x, y):
            return
        # tief = auf der Lane an/hinter seinem Aussenturm, sonst weit in seinem Jungle.
        # (Erster Versuch "0.15 hinter dem Fluss": 18 Warnungen in Partie 3 - eine gewonnene
        # Top-Lane steht immer ein Stueck hinter der Ecke.)
        from .welle import _projektion
        blau = p.mein_team == "ORDER"
        pr = _projektion(x, y)
        tief = ((pr[1] if blau else 1 - pr[1]) >= cfg["lane_tief"] if pr
                else ((x - y) if blau else (y - x)) >= cfg["jungle_tief"])   # Fluss: x = y; blau unten links
        if not tief:
            self._tief_gewarnt = None    # zurueck auf deiner Seite: der naechste Vorstoss darf wieder warnen
            return
        # einmal je Vorstoss (17 Warnungen in Partie 3 hoert keiner mehr), bei langem Splitpush
        # alle `erneut_nach` Sekunden (sonst fehlte die Warnung vor dem Tod 21:18: seit 18:02 tief)
        if (bei := getattr(self, "_tief_gewarnt", None)) is not None and p.zeit - bei < cfg["erneut_nach"]:
            return
        nah = sum(1 for s in p.team(p.mein_team) if s is not p.ich and not s.tot and self.lage.sichtbar(s)
                  and (g := self.lage.gesehen(s)) and abs(g[1] - x) + abs(g[2] - y) < 0.18)
        if nah >= cfg["gruppe_ab"]:
            return
        fehlend = []
        for s in p.gegner():
            if s.tot:
                continue
            g = self.lage.gesehen(s)
            weg = p.zeit - g[0] if g else p.zeit
            # nur wer es seit seiner letzten Sichtung bis zu dir geschafft haben KANN (Swain vor
            # 25 s unten ist noch nicht oben) - so denkt ein Challenger, nicht nach der Stoppuhr
            erreichbar = not g or abs(g[1] - x) + abs(g[2] - y) <= weg * cfg["tempo"]
            if weg >= cfg["weg_ab"] and not self.lage.sichtbar(s) and erreichbar:
                fehlend.append((s, weg))
        j = p.jungler(gegenteam(p.mein_team))
        jungler_fehlt = next((w for s, w in fehlend if s is j and w >= cfg["jungler_ab"]), None)
        if len(fehlend) < cfg["mindestens"] and not (jungler_fehlt and p.zeit < self.m["sicht"]["lane_phase_bis"]):
            return
        if len(fehlend) < cfg["mindestens"]:
            fehlend = [(j, jungler_fehlt)]
        fehlend.sort(key=lambda sw: -sw[1])
        namen = [s.champion for s, _ in fehlend[:3]]
        kw = dict(namen=" und ".join([", ".join(namen[:-1]), namen[-1]] if len(namen) > 1 else namen),
                  sind="sind" if len(namen) > 1 else "ist", sie="sie" if len(namen) > 1 else "ihn",
                  sekunden=int(min(w for _, w in fehlend[:3])))
        if self.b is not None:
            text = komponist.tief(self.b, **kw)   # mit Leben, Flash (HUD) und Weg zum Turm
        else:
            text = cfg["satz"].format(**kw)
            if hasattr(self.lage, "eigene_zauber") and (ez := self.lage.eigene_zauber(p, p.zeit)) \
                    and ez.get("SummonerFlash", 0) > 0:
                text += " " + cfg["ohne_flash"]   # aus dem HUD: ohne Flash ist tief doppelt gefaehrlich
        self._tief_gewarnt = p.zeit
        # 10 s gueltig: solange er tief steht, stimmt der Satz (mit 4 s fiel er 20:53 hinter
        # einer anderen Ansage weg - 25 s vor dem Tod)
        yield Ansage(text, WICHTIG, "tief", gueltig=10, sperre=cfg["sperre"])

    def _recall_fenster(self, p: Partie, v: Partie):
        """Deine Welle laeuft in seinen Turm und du hast Gold oder wenig Leben: jetzt zurueck,
        dann verlierst du keine Vasallen (Carlos: "wie ich die Welle genau vorbereite")."""
        if not self.lage or not hasattr(self.lage, "welle") or self._ich_weg(p) or p.ich.rolle == "JUNGLE":
            return
        from .welle import LANE_DER_ROLLE, _projektion
        cfg = self.m["recall"]
        lane = LANE_DER_ROLLE.get(p.ich.rolle)
        z = self.lage.welle(lane, p.zeit) if lane else None
        if not z or z.front is None:
            return
        blau = p.mein_team == "ORDER"
        wir, die = (z.blau, z.rot) if blau else (z.rot, z.blau)
        s = z.front if blau else 1 - z.front
        ich = self.lage.gesehen(p.ich)
        in_lane = bool(ich and p.zeit - ich[0] < 2 and (pr := _projektion(ich[1], ich[2])) and pr[0] == lane)
        m = p.werte.get("maxHealth")
        leben = p.werte.get("currentHealth", 0) / m if m else 1.0
        grund = (p.gold or 0) >= cfg["gold_ab"] or leben < cfg["leben_unter"]
        if in_lane and grund and wir >= cfg["welle_ab"] and die <= 1 and s >= cfg["front_ab"]:
            self._recallfenster_bei = p.zeit  # die allgemeine Gold-Erinnerung schweigt dann
            text = (komponist.recall(self.b, "welle") if self.b is not None
                    else cfg["satz"].format(gold=int((p.gold or 0) // 100 * 100)))
            yield Ansage(text, WICHTIG, "recallfenster", gueltig=6, sperre=cfg["erneut_nach"])

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
        # Lange genug tot: der Stratege sagt statt des Standardsatzes den eigentlichen Grund
        # (todesanalyse.py) - Zeit dafuer ist die Todeszeit selbst.
        cfg_a = self.m["todesanalyse"]
        from .todesanalyse import fakten
        kontext = fakten(p, kill, self.rueckblick, self.lage)
        if self.lage is not None:
            self.lage.letzter_tod = (p.zeit, kontext)   # fuer Fragen danach ("warum bin ich gestorben?")
        if p.ich.respawn >= cfg_a["ab_sekunden"]:
            yield Ansage(text, WICHTIG, "tod", gueltig=p.ich.respawn, sperre=5, situativ=True, kontext=kontext,
                         frist=min(p.ich.respawn - cfg_a["puffer"], cfg_a["hoechstens"]))
        else:
            yield Ansage(text, WICHTIG, "tod", gueltig=15, sperre=5)
