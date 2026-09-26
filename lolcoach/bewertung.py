"""Die Lagebewertung: alles, was in dieser Sekunde zaehlt, zusammengerechnet.

Carlos 26.09.: "nicht nur eine Sache sehen, die eine Sache sagen, sondern wirklich Sachen
addieren, berechnen und eine korrekte Anweisung geben." Die Regeln entscheiden, WANN der Coach
spricht; hier steht, was in diesem Moment alles zusammenkommt:

  - du: Leben, Flash und zweiter Zauber (HUD), Ult (HUD), Gold, Ort, Lauftempo, wie weit bis zum
    eigenen Turm, ob du unter einem gegnerischen Turm stehst,
  - jeder Gegner: wo, seit wann nicht gesehen, wie schnell er fruehestens bei dir sein kann
    (Luftlinie x Wegfaktor / sein Lauftempo aus Data Dragon + Items), Flash und Ult (Timer aus
    Pings und Minimap), Level- und Item-Abstand zu dir,
  - deine Welle (Vasallen der Minimap), das naechste Objective, wer lebt.

Gesprochen wird hier nichts - der Komponist (komponist.py) baut daraus Saetze, und Claude
bekommt `text()` als berechnete Grundlage fuer jede Antwort.

Karte: Minimap-Anteile (0..1, y nach unten) <-> Spiel-Einheiten (Ursprung blaue Basis, y nach
oben). Turmpositionen aus den Kartendaten, am 26.09.2026 auf ein Minimap-Bild der Partie 7
gelegt: alle 18 Kreise sitzen auf den Turm-Icons.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import ddragon, minimap
from .zustand import BLAU, ROT, Partie, Spieler, gegenteam, struktur

BREITE, HOEHE = 14820.0, 14881.0      # Spiel-Einheiten der Karte (x, y)
WEGFAKTOR = 1.15                      # Wege sind krumm (Waende): Luftlinie x 1,15
TURM_REICHWEITE = 775                 # Turmreichweite 750 + halbe Champion-Breite
FLASH_WEITE = 400
UNBEKANNT_AB = 45.0                   # so lange nicht gesehen: Ort unbekannt, rechne mit allem

# (Team, Lane, Stufe) -> Spiel-Einheiten
TUERME = {
    (BLAU, "Top", "aussen"): (981, 10441), (BLAU, "Top", "innen"): (1512, 6699), (BLAU, "Top", "Inhib"): (1169, 4287),
    (BLAU, "Mid", "aussen"): (5846, 6396), (BLAU, "Mid", "innen"): (5048, 4812), (BLAU, "Mid", "Inhib"): (3651, 3696),
    (BLAU, "Bot", "aussen"): (10504, 1029), (BLAU, "Bot", "innen"): (6919, 1483), (BLAU, "Bot", "Inhib"): (4281, 1253),
    (ROT, "Top", "aussen"): (4318, 13875), (ROT, "Top", "innen"): (7943, 13411), (ROT, "Top", "Inhib"): (10481, 13650),
    (ROT, "Mid", "aussen"): (8955, 8510), (ROT, "Mid", "innen"): (9767, 10113), (ROT, "Mid", "Inhib"): (11134, 11207),
    (ROT, "Bot", "aussen"): (13866, 4505), (ROT, "Bot", "innen"): (13327, 8226), (ROT, "Bot", "Inhib"): (13624, 10572),
}
BRUNNEN = {BLAU: (400, 400), ROT: (14340, 14390)}
# Gruben (Minimap-Anteile wie regeln.GRUBEN)
GRUBEN = {"drache": (0.675, 0.71), "baron": (0.325, 0.29), "herold": (0.325, 0.29), "larven": (0.325, 0.29)}
LANE_DER_ROLLE = {"TOP": "Top", "MIDDLE": "Mid", "BOTTOM": "Bot", "UTILITY": "Bot"}


def einheiten(x: float, y: float) -> tuple[float, float]:
    """Minimap-Anteil -> Spiel-Einheiten."""
    return x * BREITE, (1.0 - y) * HOEHE


def abstand(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def tempo(s: Spieler) -> float:
    """Lauftempo ausser Kampf: Grundwert (Data Dragon) + Stiefel und flache Boni + Prozent-Boni der Items."""
    ch = ddragon.champions().get(s.champion_id) or {}
    basis = float(ch.get("stats", {}).get("movespeed", 340))
    it = ddragon.items()
    flach = prozent = 0.0
    for i in s.items:
        st = it.get(i, {}).get("stats", {})
        flach += st.get("FlatMovementSpeedMod", 0.0)
        prozent += st.get("PercentMovementSpeedMod", 0.0)
    return (basis + flach) * (1 + prozent)


def stehende_tuerme(p: Partie) -> dict[tuple[str, str, str], tuple[float, float]]:
    weg = set()
    for e in p.kills_von("TurretKilled"):
        if st := struktur(e.daten.get("TurretKilled", "")):
            weg.add((st.team, st.lane, st.stufe))
    return {k: v for k, v in TUERME.items() if k not in weg}


@dataclass
class GegnerLage:
    s: Spieler
    sichtbar: bool
    seit: float | None           # Sekunden seit der letzten Sichtung (0 = jetzt sichtbar), None = nie gesehen
    ort: str                     # wo zuletzt gesehen, in Worten ('' = nie)
    abstand: float | None        # Spiel-Einheiten zu dir (zuletzt gesehener Ort)
    ankunft: float | None        # fruehestens so viele Sekunden, bis er bei dir sein kann; None = unbekannt
    tempo: float
    flash: float | None          # Sekunden bis Flash zurueck; None = da oder unbekannt
    ult: float | None            # Sekunden bis Ult zurueck (nur wenn gepingt)
    level_vorsprung: int         # sein Level minus deins
    gold_vorsprung: int          # seine Items minus deine (Gold)
    kommt_naeher: bool = False   # sichtbar und laeuft auf dich zu

    @property
    def champion(self) -> str:
        return self.s.champion

    @property
    def unbekannt(self) -> bool:
        return self.seit is None or self.seit >= UNBEKANNT_AB


@dataclass
class Bewertung:
    zeit: float
    ich: Spieler
    leben: float | None = None                 # 0..1
    leben_abs: int | None = None
    gold: int = 0
    pos: tuple[float, float] | None = None      # Spiel-Einheiten
    ort: str = ""
    mein_tempo: float = 340.0
    flash: float | None = None                  # Sekunden bis bereit (0 = bereit); None = unbekannt / nicht genommen
    zweiter: tuple[str, float] | None = None    # (Zauber, Sekunden bis bereit)
    ult: bool | None = None
    zum_turm: float | None = None               # Sekunden bis zum naechsten eigenen Turm
    unter_gegnerturm: bool = False
    unter_eigenem_turm: bool = False
    tiefe: float | None = None                  # auf der eigenen Lane: 0 deine Basis .. 1 seine
    gegner: list[GegnerLage] = field(default_factory=list)
    lane: GegnerLage | None = None
    jungler: GegnerLage | None = None
    tote_gegner: list[Spieler] = field(default_factory=list)
    tote_eigene: list[Spieler] = field(default_factory=list)
    welle: tuple[int, int, float | None, str | None] | None = None   # (eure, seine, Front 0..1 aus deiner Sicht, wer schiebt)
    objective: tuple[str, float] | None = None  # (Schluessel, Sekunden bis Spawn; <= 0 lebt)
    zum_objective: float | None = None          # deine Laufzeit zur Grube (Sekunden)
    mitspieler_nah: list[Spieler] = field(default_factory=list)   # innerhalb ~1500 Einheiten
    trade: str = ""             # aus der Spielakte: worauf beim All-in gegen den Lane-Gegner achten
    platten_gegner: int | None = None   # Platten am vordersten stehenden Gegnerturm deiner Lane (Minimap)
    platten_eigen: int | None = None    # ... an deinem vordersten Turm

    # --- Ableitungen -------------------------------------------------------------

    def bedrohung(self, bis: float = 10.0) -> list[GegnerLage]:
        """Gegner, die in `bis` Sekunden bei dir sein koennen - zuerst die schnellsten.
        Nie gesehene zaehlen nicht (dafuer gibt es `unbekannte`)."""
        aus = [g for g in self.gegner if g.ankunft is not None and g.ankunft <= bis and not g.unbekannt
               and self.plausibel(g)]
        return sorted(aus, key=lambda g: g.ankunft)

    def plausibel(self, g: GegnerLage) -> bool:
        """Kommt dieser Gegner realistisch zu dir? Worst Case allein macht jeden, der 35 s nicht zu
        sehen war, zur Gefahr (Test 26.09.: 'Varus kann in 1 Sekunde da sein' - der ADC, Minute 12,
        bot). In der Lane-Phase wandern Jungler, Mid und Support; ein Laner nur, wenn er schon nah
        war oder sichtbar auf dich zulaeuft. Danach (ab 14:00) kann jeder kommen."""
        if self.zeit >= 840 or g.sichtbar or g.kommt_naeher:
            return True
        if g.s.rolle == "JUNGLE" or (self.lane and g.s.name == self.lane.s.name):
            return True
        # Mid und Support wandern - aber kaum vor Minute 4 (Camille-Partie 26.09., 2:29: "Anivia fehlt" oben)
        if g.s.rolle in ("MIDDLE", "UTILITY") and self.zeit >= 240:
            return True
        return g.abstand is not None and g.abstand <= 4000

    def unbekannte(self) -> list[GegnerLage]:
        return [g for g in self.gegner if g.unbekannt]

    def kraefte(self) -> tuple[float, list[str]]:
        """Du gegen deinen Lane-Gegner: Zahl (> 0 = du bist staerker) und die Gruende in Worten.
        Grobe Gewichte (Erfahrungswerte): ein Level ~ 600 Gold an Items, Leben zaehlt voll,
        Ult-Level 6 ist ein Sprung. Sein Leben kennt die API nicht - das steht im Bild."""
        g = self.lane
        if not g:
            return 0.0, []
        wert, gruende = 0.0, []
        lv = -g.level_vorsprung
        if lv:
            wert += lv
            gruende.append(f"{'du' if lv > 0 else g.champion} {abs(lv)} Level vorn")
        gd = -g.gold_vorsprung
        if abs(gd) >= 400:
            wert += gd / 600
            gruende.append(f"{'du' if gd > 0 else g.champion} {abs(gd) // 100 * 100} Gold an Items vorn")
        if self.ich.level >= 6 > g.s.level:
            wert += 1.5
        elif g.s.level >= 6 > self.ich.level:
            wert -= 1.5
        if self.leben is not None and self.leben < 0.6:
            wert -= (0.6 - self.leben) * 5
            gruende.append(f"du hast nur {int(self.leben * 100)} Prozent Leben")
        if self.ult is False and self.ich.level >= 6:
            wert -= 1
            gruende.append("deine Ult ist nicht bereit")
        if g.ult:
            wert += 1
            gruende.append(f"seine Ult ist weg")
        return wert, gruende

    def vorsprung_satz(self) -> str:
        """Gesprochen: 'du bist 2 Level und 500 Gold vorn', 'er ist 1 Level vorn', 'du 1 Level, er 800 Gold'."""
        g = self.lane
        if not g:
            return ""
        du, er = [], []
        lv, gd = -g.level_vorsprung, -g.gold_vorsprung
        (du if lv > 0 else er).append(f"{abs(lv)} Level") if lv else None
        (du if gd > 0 else er).append(f"{abs(gd) // 100 * 100} Gold") if abs(gd) >= 400 else None
        if du and er:
            return f"du {' und '.join(du)} vorn, er {' und '.join(er)}"
        if du:
            return f"du bist {' und '.join(du)} vorn"
        if er:
            return f"er ist {' und '.join(er)} vorn"
        return ""

    def fenster(self) -> list[tuple[float, str]]:
        """Zeitfenster, die gerade offen sind: (Sekunden, Beschreibung) - das kuerzeste zuerst."""
        aus = []
        if self.jungler and self.jungler.s.tot:
            aus.append((self.jungler.s.respawn, f"{self.jungler.champion} ist tot"))
        elif self.jungler and self.jungler.ankunft is not None and not self.jungler.unbekannt and self.jungler.ankunft >= 15:
            aus.append((self.jungler.ankunft, f"{self.jungler.champion} ist weit weg"))
        if self.lane and self.lane.s.tot:
            aus.append((self.lane.s.respawn, f"{self.lane.champion} ist tot"))
        if self.lane and self.lane.flash and self.lane.flash > 20:
            aus.append((self.lane.flash, f"{self.lane.champion} hat kein Flash"))
        return sorted(aus)

    # --- fuer Claude ------------------------------------------------------------

    def text(self) -> str:
        z = []
        ich = []
        if self.leben is not None:
            ich.append(f"Leben {int(self.leben * 100)} %")
        if self.flash is not None:
            ich.append("Flash bereit" if self.flash <= 0 else f"Flash weg noch {int(self.flash)} s")
        if self.ult is not None:
            ich.append("Ult bereit" if self.ult else "Ult nicht bereit")
        if self.zum_turm is not None:
            ich.append(f"{self.zum_turm:.0f} s bis zum eigenen Turm")
        if self.unter_gegnerturm:
            ich.append("STEHT UNTER GEGNERISCHEM TURM")
        if self.tiefe is not None:
            ich.append(f"Lane-Position {self.tiefe:.2f} (0 eigene Basis, 1 gegnerische)")
        if ich:
            z.append("Du: " + ", ".join(ich) + (f", {self.ort}" if self.ort else "") + ".")
        for g in sorted(self.gegner, key=lambda g: (g.ankunft is None, g.ankunft or 0)):
            if g.s.tot:
                z.append(f"- {g.champion}: tot, noch {int(g.s.respawn)} s")
                continue
            if g.seit is None:
                wo = "nie gesehen"
            elif g.seit < 1.5:
                wo = f"jetzt sichtbar {g.ort}" + (", kommt auf dich zu" if g.kommt_naeher else "")
            else:
                wo = f"vor {int(g.seit)} s {g.ort}"
            an = ("" if g.ankunft is None or g.unbekannt
                  else f", fruehestens in {g.ankunft:.0f} s bei dir" if g.ankunft > 0 else ", KANN SCHON BEI DIR SEIN")
            extra = []
            if g.flash:
                extra.append(f"ohne Flash noch {int(g.flash)} s")
            if g.ult:
                extra.append(f"ohne Ult noch {int(g.ult)} s")
            if g.level_vorsprung:
                extra.append(f"{abs(g.level_vorsprung)} Level {'ueber' if g.level_vorsprung > 0 else 'unter'} dir")
            z.append(f"- {g.champion} ({g.s.rolle or '?'}): {wo}{an}" + (f"; {', '.join(extra)}" if extra else ""))
        wert, gruende = self.kraefte()
        if self.lane and not self.lane.s.tot:
            urteil = "du staerker" if wert >= 1 else "er staerker" if wert <= -1 else "ausgeglichen"
            z.append(f"Kraefte gegen {self.lane.champion}: {urteil}" + (f" ({'; '.join(gruende)})" if gruende else "")
                     + " - sein Leben siehst du nur im Bild.")
        if self.platten_gegner is not None or self.platten_eigen is not None:
            z.append(f"Platten (Minimap): sein vorderster Turm deiner Lane {self.platten_gegner if self.platten_gegner is not None else '?'}"
                     f", deiner {self.platten_eigen if self.platten_eigen is not None else '?'}")
        if self.welle:
            wir, die, front, schiebt = self.welle
            z.append(f"Deine Welle: {wir} eigene gegen {die}, Front {front if front is None else round(front, 2)}"
                     + (f", {schiebt} schiebt" if schiebt else ""))
        if f := self.fenster():
            z.append("Offene Fenster: " + "; ".join(f"{t} ({int(s)} s)" for s, t in f))
        if self.objective:
            schl, s = self.objective
            z.append(f"Naechstes Objective: {schl} " + ("lebt" if s <= 0 else f"in {int(s)} s")
                     + (f", du brauchst ~{int(self.zum_objective)} s dorthin" if self.zum_objective else ""))
        if self.mitspieler_nah:
            z.append("Mitspieler bei dir: " + ", ".join(s.champion for s in self.mitspieler_nah))
        return "BEWERTUNG (berechnet, Worst Case fuer Laufzeiten):\n" + "\n".join(z)


def bewerte(p: Partie, lagebild=None, objective: tuple[str, float] | None = None) -> Bewertung | None:
    """Die Bewertung dieses Takts. `lagebild`: lage.Lagebild (ohne: nur API-Werte)."""
    if not p.ich:
        return None
    b = Bewertung(zeit=p.zeit, ich=p.ich, gold=int(p.gold or 0))
    m = p.werte.get("maxHealth")
    if m:
        b.leben_abs = int(p.werte.get("currentHealth", 0))
        b.leben = b.leben_abs / m
    b.mein_tempo = float(p.werte.get("moveSpeed") or tempo(p.ich))
    feind, mein = gegenteam(p.mein_team), p.mein_team
    tuerme = stehende_tuerme(p)
    lb = lagebild if lagebild is not None and getattr(lagebild, "aktiv", False) else None

    if lb is not None:
        if ez := lb.eigene_zauber(p, p.zeit):
            for schl, rest in ez.items():
                if schl == "SummonerFlash":
                    b.flash = rest
                elif b.zweiter is None:
                    b.zweiter = (schl, rest)
        if (ef := lb.eigene_faehigkeiten(p.zeit)) and p.ich.level >= 6:
            b.ult = ef.get("R")     # vor Level 6 ist R nie "bereit" - das ist kein Cooldown
        if (g := lb.gesehen(p.ich)) and p.zeit - g[0] < 3 and not p.ich.tot:
            b.pos = einheiten(g[1], g[2])
            b.ort = minimap.ort(g[1], g[2], mein)

    if b.pos:
        eigene = [v for (t, _, _), v in tuerme.items() if t == mein] + [BRUNNEN[mein]]
        b.zum_turm = min(abstand(b.pos, v) for v in eigene) * WEGFAKTOR / b.mein_tempo
        b.unter_gegnerturm = any(abstand(b.pos, v) <= TURM_REICHWEITE for (t, _, _), v in tuerme.items() if t == feind)
        b.unter_eigenem_turm = any(abstand(b.pos, v) <= TURM_REICHWEITE for (t, _, _), v in tuerme.items() if t == mein)
        if (lane := LANE_DER_ROLLE.get(p.ich.rolle)) and lb is not None:
            from .welle import _projektion
            g = lb.gesehen(p.ich)
            if pr := _projektion(g[1], g[2]):
                if pr[0] == lane and pr[2] < 0.06:
                    b.tiefe = pr[1] if mein == BLAU else 1 - pr[1]
        for s in p.team(mein):
            if s is p.ich or s.name == p.ich.name or s.tot or lb is None:
                continue
            if (g := lb.gesehen(s)) and p.zeit - g[0] < 3 and abstand(b.pos, einheiten(g[1], g[2])) <= 1500:
                b.mitspieler_nah.append(s)

    for s in p.gegner():
        gl = _gegner_lage(s, p, lb, b.pos)
        b.gegner.append(gl)
        if s.tot:
            b.tote_gegner.append(s)
        if s.rolle == p.ich.rolle and p.ich.rolle:
            b.lane = gl
        if s.rolle == "JUNGLE":
            b.jungler = gl
    b.tote_eigene = [s for s in p.team(mein) if s.tot]

    if lb is not None and (lane := LANE_DER_ROLLE.get(p.ich.rolle)) and (w := lb.welle(lane, p.zeit)):
        blau = mein == BLAU
        wir, die = (w.blau, w.rot) if blau else (w.rot, w.blau)
        front = w.front if blau or w.front is None else 1 - w.front
        schiebt = None if not w.schiebt else ("ihr" if (w.schiebt == "blau") == blau else "er")
        b.welle = (wir, die, front, schiebt)

    if lb is not None and (lane := LANE_DER_ROLLE.get(p.ich.rolle)) and getattr(lb, "platten", None):
        for team, feld in ((feind, "platten_gegner"), (mein, "platten_eigen")):
            vorn = next(((team, lane, s) for s in ("aussen", "innen", "Inhib") if (team, lane, s) in tuerme), None)
            if vorn is not None and vorn in lb.platten:
                setattr(b, feld, lb.platten[vorn])

    if objective is None:
        objective = naechstes_objective(p)
    b.objective = objective
    if objective and b.pos and objective[0] in GRUBEN:
        b.zum_objective = abstand(b.pos, einheiten(*GRUBEN[objective[0]])) * WEGFAKTOR / b.mein_tempo
    return b


OBEN = ("larven", "herold", "baron")


def naechstes_objective(p: Partie, bis: float = 150) -> tuple[str, float] | None:
    """Das Objective, das fuer DICH zaehlt: in der Lane-Phase zuerst eines auf deiner Kartenseite
    (Top: Larven/Herold/Baron, Bot: Drache), das bald kommt, dann eines dort, das lebt; sonst das
    naechste ueberhaupt. Ein lebender Drache verdeckte sonst die Larven fuer den Toplaner."""
    from . import regeln
    kandidaten = []
    for schl in regeln._lebende_objectives(p, bis=bis):
        n = p.naechster_spawn(schl)
        if n is not None:
            kandidaten.append((schl, n - p.zeit))
    if not kandidaten:
        return None
    rolle = p.ich.rolle if p.ich else ""
    if p.zeit < 840 and rolle in ("TOP", "BOTTOM", "UTILITY"):
        meine = [k for k in kandidaten if (k[0] in OBEN) == (rolle == "TOP")]
        kommt = [k for k in meine if k[1] > 0]
        if kommt:
            return min(kommt, key=lambda k: k[1])
        if meine:
            return min(meine, key=lambda k: k[1])
    kommt = [k for k in kandidaten if k[1] > 0]
    lebt = [k for k in kandidaten if k[1] <= 0]
    return min(kommt, key=lambda k: k[1]) if kommt and not lebt else min(kandidaten, key=lambda k: k[1])


def _gegner_lage(s: Spieler, p: Partie, lb, ich_pos) -> GegnerLage:
    ms = tempo(s)
    seit = ort = ab = ankunft = None
    sichtbar = naeher = False
    if lb is not None and not s.tot and (g := lb.gesehen(s)):
        seit = max(0.0, p.zeit - g[0])
        sichtbar = lb.sichtbar(s)
        if sichtbar:
            seit = 0.0
        ort = minimap.ort(g[1], g[2], p.mein_team)
        if ich_pos:
            ab = abstand(ich_pos, einheiten(g[1], g[2]))
            ankunft = max(0.0, ab * WEGFAKTOR / ms - seit)
            if sichtbar and (n := lb.naehert_sich(s, (ich_pos[0] / BREITE, 1 - ich_pos[1] / HOEHE), p.zeit)):
                naeher = n >= 0.03
    flash = ult = None
    if lb is not None and hasattr(lb, "zauber"):
        flash = lb.zauber.fehlt(s, "SummonerFlash", p.zeit)
        ult = lb.zauber.fehlt(s, "R", p.zeit)
    return GegnerLage(s=s, sichtbar=sichtbar, seit=seit, ort=ort or "", abstand=ab, ankunft=ankunft, tempo=ms,
                      flash=flash, ult=ult, level_vorsprung=s.level - p.ich.level,
                      gold_vorsprung=s.item_gold - p.ich.item_gold, kommt_naeher=naeher)
