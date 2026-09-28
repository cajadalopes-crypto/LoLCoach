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
WEGFAKTOR = 1.15                      # Wege sind krumm (Waende): Luftlinie x 1,15 - fuer DEINE Wege (realistisch)
# Fuer die Ankunft eines GEGNERS gilt die Untergrenze ("fruehestens"): gemessen 27.09. an 1647 Strecken aus 5
# Partien (werkzeuge/gegner_tempo.py) liefen Gegner in 52 % der Faelle schneller als Luftlinie x 1,15 / Tempo,
# in 19 % um mehr als 15 % (gerade Lanes, Tempo-Buffs, Dashes). Luftlinie / (Tempo x 1,1) deckt 90 % ab.
GEGNER_TEMPO_RESERVE = 1.1
TURM_REICHWEITE = 775                 # Turmreichweite 750 + halbe Champion-Breite
FLASH_WEITE = 400
UNBEKANNT_AB = 45.0                   # so lange nicht gesehen: Ort unbekannt, rechne mit allem

# (Team, Lane, Stufe) -> Spiel-Einheiten
TIER = {"aussen": 1, "innen": 2, "Inhib": 3}   # Stufe eines Turms, wie Spieler sie nennen
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


def kraft(s: Spieler, leben: float | None) -> float:
    """Kampfkraft grob, fuer den Vergleich zweier Seiten: Level (je Stufe ~ +10 %: Grundwerte und
    Faehigkeitsraenge), Items (je 2500 Gold etwa eine Verdopplung), aktuelles Leben (unbekannt: 0,9).
    Live-Partie 26.09., Carlos: "ich bin Level 12, Vi Level 6, volles Leben - und er sagt 'renn weg,
    benutz Flash'". Ohne diese Zahl war jede Gefahr eine Laufzeit, nie ein Kampf."""
    lv = 1.10 ** (max(1, s.level) - 1)
    it = 1.0 + s.item_gold / 2500.0
    hp = 0.9 if leben is None else max(0.05, min(1.0, leben))
    return lv * it * hp


# Gold fuer einen Kill, gemessen am echten Goldsprung des Killers (72 Kills in 5 Partien, 27.09.,
# werkzeuge/kill_gold.py): nach der Todesserie des Opfers (Tode seit seinem letzten Kill oder Assist) ...
TODESSERIE_GOLD = (300, 255, 185, 155, 130)
# ... oder, hat er seit seinem letzten Tod getoetet, nach seiner Killserie (ab 4 geschaetzt, hoechstens +700)
KILLSERIE_GOLD = (300, 310, 350, 500, 600, 700, 800, 900, 1000)


def serien(p: Partie | None, s: Spieler) -> tuple[int, int] | None:
    """(Kills seit seinem letzten Tod, Tode seit seinem letzten Kill oder Assist) aus den Ereignissen der Partie."""
    if p is None:
        return None
    k_seit_tod = tode_serie = 0
    for e in p.ereignisse:
        if e.art != "ChampionKill":
            continue
        if e.opfer is not None and e.opfer.name == s.name:
            k_seit_tod = 0
            tode_serie += 1
        if e.taeter is not None and e.taeter.name == s.name:
            k_seit_tod += 1
            tode_serie = 0
        elif s.name in (e.daten.get("Assisters") or []):
            tode_serie = 0
    return k_seit_tod, tode_serie


def shutdown(s: Spieler, p: Partie | None = None) -> bool:
    """Liegt (sicher) ein Shutdown auf ihm? Mit den Ereignissen: 3 Kills seit seinem letzten Tod (dann ~500 statt
    300). Ohne: ab 3 Kills und 3 mehr als Tode."""
    if (sr := serien(p, s)) is not None:
        return sr[0] >= 3
    return s.kills >= 3 and s.kills - s.tode >= 3


def kopfgeld(s: Spieler, p: Partie | None = None) -> int:
    """Gold ueber die 300 hinaus, das ein Kill an `s` bringt. Mit den Ereignissen aus seiner Killserie seit dem letzten
    Tod (Kopfgeld setzt beim Tod zurueck - Live: Ekko 4/1 brachte 338, die alte Schaetzung aus allen Kills 580).
    Ohne Ereignisse die alte Schaetzung aus allen Kills/Assists/Toden."""
    if (sr := serien(p, s)) is not None:
        return KILLSERIE_GOLD[min(sr[0], len(KILLSERIE_GOLD) - 1)] - 300
    roh = (s.kills * 300 + s.assists * 150) / 3 - s.tode * 150
    return int(max(0, min(700, roh - 100)))


def gold_offen(s: Spieler, zeit: float) -> int:
    """Ungenutztes Gold eines Gegners, geschaetzt (Reasoning #4/#8: "Goldschaetzung", "gegnerisches Item-Timing"):
    500 Start + 20,4 je 10 s ab 1:05 + ~19,5 je Vasall + 300 je Kill + 150 je Assist - Items - ~150 Verbrauch.
    Die API liefert fremdes Gold nicht, den CS nur in Zehnerschritten: +-300 Gold."""
    verdient = 500 + max(0.0, zeit - 65) / 10 * 20.4 + s.cs * 19.5 + s.kills * 300 + s.assists * 150
    # je Rolle, gemessen an 158 Einkaeufen in 5 Partien (Schaetzung davor gegen den Kaufpreis, 27.09.): Jungler
    # verdienen je Monster mehr als 19,5 (-44 g/min), Supports ueber ihr Support-Item (-28 g/min), Laner lagen leicht
    # darueber (+5..10 g/min)
    verdient += GOLD_JE_ROLLE.get(s.rolle, -7.0) * max(0.0, zeit - 90) / 60
    return int(max(0, verdient - s.item_gold - 150))


GOLD_JE_ROLLE = {"JUNGLE": 45.0, "UTILITY": 28.0}


def carry(p: Partie, team: str) -> Spieler | None:
    """Der Carry eines Teams (Reasoning #25 "Wer ist Carry?"): wer am meisten Kills und Items hat - nur, wenn er
    deutlich vorn ist (mindestens 4 Kills oder 30 % ueber dem Item-Schnitt seines Teams)."""
    lebend = [s for s in p.team(team)]
    if not lebend:
        return None
    wert = {s.name: s.kills * 300 + s.assists * 100 + s.item_gold for s in lebend}
    s = max(lebend, key=lambda x: wert[x.name])
    schnitt = sum(x.item_gold for x in lebend) / len(lebend)
    return s if s.kills >= 4 or s.item_gold >= 1.3 * schnitt + 500 else None


def kill_gold(opfer: Spieler, erstes_blut: bool = False, p: Partie | None = None) -> int:
    """Gold fuer einen Kill an `opfer` + erstes Blut. Mit den Ereignissen (`p`) gemessen: Todesserie macht ihn billig
    (Heimerdinger 0/5 brachte ~130, nicht 300), Killserie teuer. Ohne: nach Level (Wiki) + Kopfgeld-Schaetzung."""
    from . import wissen
    g = wissen.lade("mechanik")["gold"]
    fb = g["first_blood_bonus"] if erstes_blut else 0
    if (sr := serien(p, opfer)) is not None:
        k, tode = sr
        gold = KILLSERIE_GOLD[min(k, len(KILLSERIE_GOLD) - 1)] if k else TODESSERIE_GOLD[min(tode, len(TODESSERIE_GOLD) - 1)]
        return gold + fb
    basis = g["kill_basis"][max(1, min(18, opfer.level)) - 1]
    return basis + fb + kopfgeld(opfer)


def _namen_liste(n: list[str]) -> str:
    return n[0] if len(n) == 1 else ", ".join(n[:-1]) + " und " + n[-1]


def todeszeit(level: int, zeit: float) -> float:
    """Sekunden tot, wenn man jetzt stirbt (Wiki Death, wissen/mechanik.toml [tod])."""
    import math
    from . import wissen
    cfg = wissen.lade("mechanik")["tod"]
    brw = cfg["brw"][max(1, min(18, level)) - 1]
    minute = zeit / 60
    tif = 0.0
    for stufe in cfg["tif"]:
        if minute >= stufe["ab"]:
            tif = stufe["basis"] + math.ceil(2 * (minute - stufe["ab"])) * stufe["je_halbe_minute"]
    return brw * (1 + min(tif, cfg["tif_max"]) / 100)


def stehende_tuerme(p: Partie) -> dict[tuple[str, str, str], tuple[float, float]]:
    weg = set()
    for e in p.kills_von("TurretKilled"):
        if st := struktur(e.daten.get("TurretKilled", "")):
            weg.add((st.team, st.lane, st.stufe))
    return {k: v for k, v in TUERME.items() if k not in weg}


# Auftrag 008, A2: jeder Turm mit Besitzer und Lage, ohne "Tier" (101426 27:00: "Zu welchem Bot Tier 2 - meinem oder
# dem des Gegners?") - ihre Tuerme im Akkusativ, wie die Ziele heissen ("Drueck ihren inneren Top-Turm")
TURM_DE = {"aussen": "ihren äußeren {lane}-Turm", "innen": "ihren inneren {lane}-Turm",
           "Inhib": "ihren {lane}-Inhibitor-Turm"}


def eigener_turm_name(k: tuple[str, str, str], meine_lane: str | None) -> str:
    """Dein Turm im Dativ ("zu ...", "an ..."): "deinem äußeren Mid-Turm" auf deiner Lane, sonst "eurem inneren Bot-Turm"
    (Auftrag 008, A2 - vorher "deinem Mid-Tier-1-Turm")."""
    from .kern.sprache import turm
    return turm("dein" if k[1] == meine_lane else "euer", k[1], k[2], "dat")
INHIB_ZURUECK = 300.0      # Sekunden, bis ein Inhibitor wieder steht


@dataclass
class Ziel:
    """Etwas auf der Karte, das DU jetzt tun kannst - von deiner Position aus gerechnet (Carlos 27.09., Minute
    25-38: "Drueckt jetzt die Tuerme" ohne Turm, "schieb die Welle in seinen Turm" in der eigenen Basis)."""
    art: str                     # "turm" (angreifen) / "verteidigen" (Supervasallen bei euch)
    lane: str
    name: str                    # "den äußeren Mid-Turm"
    pos: tuple[float, float]
    weg: float                   # deine Laufzeit (s)
    frei: float | None           # Sekunden, bis der erste bekannte Verteidiger dort sein kann (None: keiner)
    unbekannt: int               # lebende Gegner, deren Ort niemand kennt
    mitspieler: int              # Mitspieler, die jetzt schon in der Naehe (4000) stehen
    wert: float = 0.0

    def satz_weg(self) -> str:
        return f"{int(round(self.weg))} Sekunden von dir"


def eigene_inhibs_weg(p: Partie) -> list[tuple[str, float]]:
    """(Lane, seit Spielzeit) der eigenen Inhibitoren, die gerade fehlen - dort laufen Supervasallen."""
    aus = []
    for e in p.kills_von("InhibKilled"):
        st = struktur(e.daten.get("InhibKilled", ""))
        if st and st.team == p.mein_team and p.zeit - e.zeit < INHIB_ZURUECK:
            aus.append((st.lane, e.zeit))
    return aus


def verteidiger_ab(b: "Bewertung", ziel: tuple[float, float], weg: float) -> tuple[float | None, int, list]:
    """Bis wann niemand vom Gegner an `ziel` sein kann (Buch 0, 4.2 `fenster_gegner`): (fruehester bekannter
    Verteidiger in s, Zahl der Unbekannten, wer bis zu deiner Ankunft `weg` + 15 s dort sein kann). Tote: Respawn +
    Weg aus ihrem Brunnen. Wer laenger als 15 s nicht gesehen wurde, zaehlt als unbekannt - nicht als "schon dort".
    Genutzt von `ziele` und vom Kern (kern/merkmale.py)."""
    feind = gegenteam(b.partie.mein_team) if b.partie is not None else ROT
    zeiten, unbekannt, rechtzeitig = [], 0, []
    for g in b.gegner:
        if g.s.tot:
            t = g.s.respawn + abstand(BRUNNEN[feind], ziel) * 1.15 / 380.0
        elif g.pos is None or g.seit is None or g.seit > 15:
            unbekannt += 1
            continue
        else:
            t = max(0.0, abstand(g.pos, ziel) * 1.15 / (g.tempo or 350.0) - g.seit)
        zeiten.append(t)
        if t <= weg + 15:
            rechtzeitig.append(g)
    return (min(zeiten) if zeiten else None), unbekannt, rechtzeitig


def ziele(b: "Bewertung") -> list[Ziel]:
    """Tuerme, die ihr jetzt angreifen koennt, und eure Lanes mit Supervasallen - jedes mit deiner Laufzeit, wann
    der erste Verteidiger da sein kann (Tote: Respawn + Weg aus dem Brunnen) und wer von euch schon dort steht.
    Sortiert nach Wert: Ertrag, geteilt durch deinen Weg, nur was vor dem Verteidiger machbar ist."""
    p = b.partie
    if p is None or b.pos is None or not p.mein_team:
        return []
    mein, feind = p.mein_team, gegenteam(p.mein_team)
    tuerme = stehende_tuerme(p)
    aus: list[Ziel] = []

    def verteidiger(ziel: tuple[float, float], weg: float) -> tuple[float | None, int, list]:
        return verteidiger_ab(b, ziel, weg)

    def freunde(ziel: tuple[float, float]) -> int:
        return sum(1 for s, wo, *_ in b.mitspieler if wo is not None and abstand(wo, ziel) <= 4000)

    for lane in ("Top", "Mid", "Bot"):
        k = next(((feind, lane, st) for st in TIER if (feind, lane, st) in tuerme), None)
        if k is None:
            continue
        pos = tuerme[k]
        weg = abstand(b.pos, pos) * 1.15 / b.mein_tempo
        frei, unbekannt, dort = verteidiger(pos, weg)
        z = Ziel("turm", lane, TURM_DE[k[2]].format(lane=lane), pos, weg, frei, unbekannt, freunde(pos))
        # wer rechtzeitig dort sein kann, zaehlt nur, wenn er staerker ist als du (plus Mitspieler dort)
        haelt = not dort or b.kraft_gegen(dort, mit_verbuendeten=False) * (1 + 0.8 * z.mitspieler) >= 1.2
        z.wert = (1.0 + 0.3 * TIER[k[2]] + 0.35 * z.mitspieler) - weg / 60.0 - 0.25 * unbekannt \
            - (0.0 if haelt else 1.5)
        aus.append(z)
    for lane, seit in eigene_inhibs_weg(p):
        pos = TUERME.get((mein, lane, "Inhib")) or BRUNNEN[mein]
        weg = abstand(b.pos, pos) * 1.15 / b.mein_tempo
        frei, unbekannt, _ = verteidiger(pos, weg)
        z = Ziel("verteidigen", lane, f"die Supervasallen auf {lane}", pos, weg, frei, unbekannt, freunde(pos))
        z.wert = 1.6 - weg / 60.0 - 0.5 * z.mitspieler     # stehen schon zwei von euch dort, braucht es dich weniger
        aus.append(z)
    return sorted(aus, key=lambda z: -z.wert)


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
    pos: tuple[float, float] | None = None   # zuletzt gesehen (Spiel-Einheiten)
    shutdown: bool = False       # auf ihm liegt ein Shutdown (K/D)
    leben: float | None = None   # 0..1 aus seinem Lebensbalken im Spielbild (frisch), sonst unbekannt
    mana: float | None = None    # 0..1 aus dem Manabalken darunter (frisch), sonst unbekannt
    leben_alter: float | None = None   # Sekunden seit dem Lesen seines Balkens (Kill-Beleg, Buch 0 6.2: <= 1 s)

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
    turm_name: str = "deinem nächsten Turm"     # welcher: "deinem Top-Tier-1-Turm" (Dativ, fuer "zu ...", "an ...")
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
    mitspieler: list[tuple] = field(default_factory=list)   # (Spieler, Spiel-Einheiten, Leben 0..1|None, Ort) - frisch gesehen
    partie: "Partie | None" = None   # der Zustand dieses Takts (fuer Plaene, die alle Lanes brauchen)
    tode_kurz: list[float] = field(default_factory=list)   # Spielzeiten deiner Tode der letzten 4 Minuten
    shutdown_ich: bool = False  # auf dir liegt ein Shutdown
    trade: str = ""             # aus der Spielakte: worauf beim All-in gegen den Lane-Gegner achten
    platten_gegner: int | None = None   # Platten am vordersten stehenden Gegnerturm deiner Lane (Minimap)
    platten_eigen: int | None = None    # ... an deinem vordersten Turm
    prio: dict[str, str | None] = field(default_factory=dict)   # Lane -> "ihr" / "er" / None (Welle steht)
    kampf: "Kampflage | None" = None    # Kampf um das naechste Objective (wenn es in <= 90 s kommt oder lebt)
    tod_kostet: float = 0.0     # so lange waerst du tot, wenn du jetzt stirbst
    kauf: "object | None" = None   # kaufplan.Kauf: was dein Gold jetzt kauft / was bis zum naechsten Bauteil fehlt
    bereit: dict | None = None  # eigene Q/W/E/R bereit (HUD), None = unbekannt

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

    @property
    def in_basis(self) -> bool:
        return "eurer Basis" in (self.ort or "")

    def sicherer_ort(self) -> tuple[str, float | None]:
        """Buch 0, 7.5: der sichere Ort mit der kuerzesten Laufzeit - dein naechster stehender Turm oder die Basis
        (`turm_name`/`zum_turm` kennen beide schon) oder deine Gruppe (>= 2 Mitspieler beieinander).
        102112, 35:35: "zurueck zu deinem Top-Tier-3-Turm, 31 Sekunden", waehrend drei Mitspieler 8 s entfernt
        standen. (Ziel im Dativ fuer "zu ...", Laufzeit)."""
        beste: tuple[str, float | None] = (self.turm_name, self.zum_turm)
        if self.pos is None:
            return beste
        freunde = [(s, wo) for s, wo, *_ in self.mitspieler if wo is not None]
        for _, wo in freunde:
            gruppe = [x.champion for x, w2 in freunde if abstand(w2, wo) <= 1500]
            if len(gruppe) < 2:
                continue
            weg = abstand(self.pos, wo) * WEGFAKTOR / self.mein_tempo
            if beste[1] is None or weg < beste[1]:
                beste = (", ".join(gruppe[:-1]) + " und " + gruppe[-1], weg)
        return beste

    @property
    def auf_lane(self) -> bool:
        """Du stehst auf DEINER Lane - nur dann gibt es "deine Welle" und "seinen Turm" (Live 27.09.: "schieb die
        Welle in seinen Turm und geh back" in der eigenen Basis, Minute 25-38)."""
        return self.tiefe is not None and not self.in_basis

    @property
    def lane_nah(self) -> bool:
        """Dein Lane-Gegner ist bei dir (<= 3500) - nur dann ist er DAS Thema, nach der Lane-Phase erst recht
        (Live 27.09., 26:01/32:19: "geh auf Sett drauf", Sett auf der anderen Kartenseite)."""
        g = self.lane
        return g is not None and not g.s.tot and g.abstand is not None and g.abstand <= 3500

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
        if g.leben is not None:        # sein Balken im Bild: das entscheidet einen Kampf mehr als ein Level
            wert += ((self.leben if self.leben is not None else 1.0) - g.leben) * 4
            if g.leben <= 0.5:
                gruende.append(f"{g.champion} hat nur {int(g.leben * 100)} Prozent Leben")
        if self.ult is False and self.ich.level >= 6:
            wert -= 1
            gruende.append("deine Ult ist nicht bereit")
        if g.ult:
            wert += 1
            gruende.append(f"seine Ult ist weg")
        return wert, gruende

    def kraft_gegen(self, gegen: list["GegnerLage"], mit_verbuendeten: bool = True) -> float:
        """Kampfkraft deiner Seite geteilt durch die der Gegner (> 1: ihr gewinnt). Deine Seite: du (Leben aus
        der API) und Mitspieler in 1500 Einheiten (Leben aus der HUD-Leiste, zu 80 % - nicht jeder steigt
        voll ein). Gegner mit ihrem Leben aus dem Lebensbalken, sonst 0,9."""
        wir = kraft(self.ich, self.leben)
        if mit_verbuendeten and self.pos:
            for s, wo, leben, _ in self.mitspieler:
                if abstand(self.pos, wo) <= 1500:
                    wir += 0.8 * kraft(s, leben)
        die = sum(kraft(g.s, g.leben) for g in gegen)
        return wir / die if die > 0 else 99.0

    def ueberlegen_satz(self, gegen: list["GegnerLage"]) -> str:
        """Gesprochen, warum du staerker bist: 'Vi ist 6 Level und 3000 Gold unter dir, du hast volles Leben'."""
        if len(gegen) == 1:
            g = gegen[0]
            teile = []
            lv = self.ich.level - g.s.level
            gd = self.ich.item_gold - g.s.item_gold
            if lv > 0:
                teile.append(f"{lv} Level")
            if gd >= 500:
                teile.append(f"{gd // 100 * 100} Gold")
            satz = f"{g.champion} ist {' und '.join(teile)} unter dir" if teile else ""
            if g.leben is not None and g.leben <= 0.6:
                satz += (", " if satz else "") + f"{g.champion} hat {int(g.leben * 100)} Prozent Leben"
        else:
            satz = f"{_namen_liste([g.champion for g in gegen])} zusammen sind schwächer als du"
        if self.leben is not None and self.leben >= 0.85:
            satz += (", " if satz else "") + "du hast volles Leben"
        elif self.leben is not None:
            satz += (", " if satz else "") + f"du hast {int(self.leben * 100)} Prozent Leben"
        if any(abstand(self.pos, wo) <= 1500 for _, wo, _, _ in self.mitspieler) if self.pos else False:
            satz += ", dein Team ist bei dir"
        return satz

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

    def text(self, modus: str | None = None) -> str:
        """Die Bewertung fuer Claude. `modus` (Buch 0, Schritt 2): Lane-Gegner und Lane-Welle nur in LANE/SEITE
        oder wenn er <= 3500 entfernt ist; ohne Modus wie bisher nach deiner Position."""
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
        if self.tod_kostet:
            ich.append(f"ein Tod jetzt = {int(self.tod_kostet)} s grau")
        if self.shutdown_ich:
            ich.append(f"auf dir liegt ein Shutdown ({self.ich.kills}/{self.ich.tode})")
        if len(self.tode_kurz) >= 2:
            ich.append(f"{len(self.tode_kurz)} Tode in den letzten 4 Minuten - jetzt sicher spielen")
        if self.kauf is not None and self.kauf.satz():
            ich.append(f"Gold {self.gold}: {self.kauf.satz()} (Weg zu {self.kauf.item})")
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
            if g.flash and g.flash >= 1:
                extra.append(f"ohne Flash noch {int(g.flash)} s")
            if g.ult and g.ult >= 1:
                extra.append(f"ohne Ult noch {int(g.ult)} s")
            if g.level_vorsprung:
                extra.append(f"{abs(g.level_vorsprung)} Level {'ueber' if g.level_vorsprung > 0 else 'unter'} dir")
            if g.shutdown:
                extra.append(f"Shutdown auf ihm ({g.s.kills}/{g.s.tode})")
            if g.leben is not None:
                extra.append(f"Leben laut Bild {int(g.leben * 100)} %")
            z.append(f"- {g.champion} ({g.s.rolle or '?'}): {wo}{an}" + (f"; {', '.join(extra)}" if extra else ""))
        # Wo DU stehst - der Anker fuer alles (Live 27.09., Minute 25-38: "Sett, Sett, Top, Top, schieb die Welle",
        # waehrend er in der Basis oder auf Mid stand)
        lane_bezug = (modus in ("LANE", "SEITE") or self.lane_nah) if modus else (self.auf_lane or self.lane_nah)
        z.append(f"DEINE POSITION: {self.ort or '?'} - " + (
            "auf deiner Lane." if self.auf_lane else
            "in eurer Basis, NICHT auf deiner Lane: deine Welle und dein Lane-Gegner sind kein Thema, ausser er "
            "geht hin." if self.in_basis else
            "NICHT auf deiner Lane: deine Welle und dein Lane-Gegner sind nur Thema, wenn er in der Naehe ist."))
        wert, gruende = self.kraefte()
        if self.lane and not self.lane.s.tot and lane_bezug:
            urteil = "du staerker" if wert >= 1 else "er staerker" if wert <= -1 else "ausgeglichen"
            z.append(f"Kraefte gegen {self.lane.champion}: {urteil}" + (f" ({'; '.join(gruende)})" if gruende else "")
                     + " - sein Leben siehst du nur im Bild.")
        elif self.lane and not self.lane.s.tot:
            z.append(f"{self.lane.champion} (dein Lane-Gegner) ist NICHT bei dir"
                     + (f" ({int(self.lane.abstand)} Einheiten weg)" if self.lane.abstand is not None else "")
                     + " - kein Kampf-Thema, nicht 'geh auf ihn'.")
        ziele_ = ziele(self)
        if ziele_:
            z.append("ZIELE VON DEINER POSITION (berechnet, bestes zuerst; 'frei' = bis der erste Verteidiger dort "
                     "sein kann): " + "; ".join(
                         f"{x.name} ({x.art}): {int(x.weg)} s von dir, frei "
                         + (f"{int(x.frei)} s" if x.frei is not None else "?")
                         + (f", {x.unbekannt} Gegner unbekannt" if x.unbekannt else "")
                         + (f", {x.mitspieler} Mitspieler dort" if x.mitspieler else "")
                         + (" - lohnt" if x.wert > 0.2 else " - lohnt nicht") for x in ziele_[:4]))
        if lane_bezug and (self.platten_gegner is not None or self.platten_eigen is not None):
            z.append(f"Platten (Minimap): sein vorderster Turm deiner Lane {self.platten_gegner if self.platten_gegner is not None else '?'}"
                     f", deiner {self.platten_eigen if self.platten_eigen is not None else '?'}")
        if self.welle and lane_bezug:
            wir, die, front, schiebt = self.welle
            z.append(f"Deine Welle: {wir} eigene gegen {die}, Front {front if front is None else round(front, 2)}"
                     + (f", {schiebt} schiebt" if schiebt else ""))
        if self.prio:
            z.append("Lane-Prio (Minimap-Wellen): " + ", ".join(
                f"{l} {'ihr' if v == 'ihr' else 'Gegner' if v == 'er' else 'offen'}" for l, v in self.prio.items()))
        if f := self.fenster():
            z.append("Offene Fenster: " + "; ".join(f"{t} ({int(s)} s)" for s, t in f))
        if self.objective:
            schl, s = self.objective
            tp = self.zweiter is not None and self.zweiter[0] == "SummonerTeleport" and self.zweiter[1] <= 0
            zu_weit = (self.zum_objective is not None and self.zum_objective > 25 and not tp
                       and self.ich.rolle not in ("JUNGLE", "MIDDLE"))
            z.append(f"Naechstes Objective: {schl} " + ("lebt" if s <= 0 else f"in {int(s)} s")
                     + (f", du brauchst ~{int(self.zum_objective)} s dorthin" if self.zum_objective else "")
                     # Live 26.09., 3:41: Claude schickte Riven (Top, ohne TP, 37 s Weg) "zum Drachen"
                     + (" - FUER DICH ZU WEIT: nicht hingehen, Druck auf deiner Seite" if zu_weit else ""))
        if self.mitspieler_nah:
            z.append("Mitspieler bei dir: " + ", ".join(s.champion for s in self.mitspieler_nah))
        if self.kampf is not None:
            z.append("Kampf um das Objective (Minimap-Positionen, HUD-Leben): " + self.kampf.urteil()[1])
        return "BEWERTUNG (berechnet, Worst Case fuer Laufzeiten):\n" + "\n".join(z)


def bewerte(p: Partie, lagebild=None, objective: tuple[str, float] | None = None) -> Bewertung | None:
    """Die Bewertung dieses Takts. `lagebild`: lage.Lagebild (ohne: nur API-Werte)."""
    if not p.ich:
        return None
    b = Bewertung(zeit=p.zeit, ich=p.ich, gold=int(p.gold or 0), partie=p)
    b.shutdown_ich = shutdown(p.ich, p)
    b.tode_kurz = [e.zeit for e in p.ereignisse
                   if e.art == "ChampionKill" and e.opfer is p.ich and p.zeit - e.zeit <= 240]
    m = p.werte.get("maxHealth")
    if m:
        b.leben_abs = int(p.werte.get("currentHealth", 0))
        b.leben = b.leben_abs / m
    b.mein_tempo = float(p.werte.get("moveSpeed") or tempo(p.ich))
    try:
        b.tod_kostet = todeszeit(p.ich.level, p.zeit)
    except (KeyError, IndexError, TypeError):
        pass
    try:
        from . import kaufplan
        b.kauf = kaufplan.plan(p.ich.champion_id, p.ich.items, b.gold)
    except Exception:
        b.kauf = None
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
        if ef := lb.eigene_faehigkeiten(p.zeit):
            b.bereit = ef
        if ef and p.ich.level >= 6:
            b.ult = ef.get("R")     # vor Level 6 ist R nie "bereit" - das ist kein Cooldown
        if (g := lb.gesehen(p.ich)) and p.zeit - g[0] < 3 and not p.ich.tot:
            b.pos = einheiten(g[1], g[2])
            b.ort = minimap.ort(g[1], g[2], mein)

    if not b.pos and not p.ich.tot:
        # Ohne frische Position nie "geh zurueck zu deinem Turm" (Nachlauf 212105, 10:50 - Carlos: "Was ist denn mein
        # Tower?"): der Turm zur letzten Sichtung (bis 20 s alt), sonst der aeusserste stehende deiner Lane
        g = lb.gesehen(p.ich) if lb is not None else None
        if g is not None and p.zeit - g[0] < 20:
            wo = einheiten(g[1], g[2])
            k = min((k for k in tuerme if k[0] == mein), key=lambda k: abstand(wo, tuerme[k]), default=None)
        else:
            lane = LANE_DER_ROLLE.get(p.ich.rolle)
            k = next((k for st in TIER for k in tuerme if k[0] == mein and k[1] == lane and k[2] == st), None)
        if k is not None:
            b.turm_name = eigener_turm_name(k, LANE_DER_ROLLE.get(p.ich.rolle))
    if b.pos:
        eigene = [(k, v) for k, v in tuerme.items() if k[0] == mein] + [(None, BRUNNEN[mein])]
        naechster, wo = min(eigene, key=lambda kv: abstand(b.pos, kv[1]))
        b.zum_turm = abstand(b.pos, wo) * WEGFAKTOR / b.mein_tempo
        # Carlos, live 26.09.: "Was ist denn mein Tower? Er soll sagen Top, Mid, Bot - Tier 1, 2, 3."
        b.turm_name = eigener_turm_name(naechster, LANE_DER_ROLLE.get(p.ich.rolle)) if naechster else "deiner Basis"
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
            if (g := lb.gesehen(s)) and p.zeit - g[0] < 3:
                wo = einheiten(g[1], g[2])
                b.mitspieler.append((s, wo, lb.leben(s, p.zeit) if hasattr(lb, "leben") else None,
                                     minimap.ort(g[1], g[2], mein)))
                if abstand(b.pos, wo) <= 1500:
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

    if lb is not None and hasattr(lb, "welle"):
        for l in ("Top", "Mid", "Bot"):
            if (w := lb.welle(l, p.zeit)) is not None:
                b.prio[l] = prio_aus_welle(w, mein)

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
    if objective and objective[1] <= 90 and lb is not None:
        b.kampf = kampf_um(p, lb, objective[0])
    if objective and b.pos and objective[0] in GRUBEN:
        b.zum_objective = abstand(b.pos, einheiten(*GRUBEN[objective[0]])) * WEGFAKTOR / b.mein_tempo
    return b


OBEN = ("larven", "herold", "baron")


def prio_aus_welle(w, mein: str) -> str | None:
    """Wer hat Prio in dieser Lane? Die Seite, deren Welle auf der gegnerischen Haelfte steht und
    nicht kleiner ist - deren Laner kann gehen, der andere muss unter seinem Turm farmen."""
    if w.front is None:
        return None
    blau = mein == BLAU
    wir, die = (w.blau, w.rot) if blau else (w.rot, w.blau)
    front = w.front if blau else 1 - w.front
    if front >= 0.52 and wir >= die:
        return "ihr"
    if front <= 0.48 and die >= wir:
        return "er"
    return None


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
    # zuerst, was in den naechsten 90 s kommt (Camille-Partie 14:21: ein seit 9 Minuten lebender Drache
    # verdeckte den Herold in 39 s), dann was lebt, dann das Naechste ueberhaupt
    bald = [k for k in kandidaten if 0 < k[1] <= 90]
    if bald:
        return min(bald, key=lambda k: k[1])
    lebt = [k for k in kandidaten if k[1] <= 0]
    if lebt:
        return max(lebt, key=lambda k: k[1])      # das zuletzt gespawnte
    return min(kandidaten, key=lambda k: k[1])


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
            ankunft = max(0.0, ab / (ms * GEGNER_TEMPO_RESERVE) - seit)     # fruehestens: die Untergrenze
            # nach Tod oder Recall steht er im Brunnen: ab dort rechnen, nicht ab der letzten Sichtung (die Ankunft
            # ab dem Sterbeort liess ihn "schon da sein", waehrend er noch einkaufte)
            if not sichtbar and hasattr(lb, "brunnen_seit") and (br := lb.brunnen_seit(s, p.zeit)):
                bx, by, t0, _ = br
                ab_brunnen = abstand(ich_pos, einheiten(bx, by))
                ankunft = max(ankunft, max(0.0, ab_brunnen / (ms * GEGNER_TEMPO_RESERVE) - (p.zeit - t0)))
                ort = minimap.ort(bx, by, p.mein_team)
            if sichtbar and (n := lb.naehert_sich(s, (ich_pos[0] / BREITE, 1 - ich_pos[1] / HOEHE), p.zeit)):
                naeher = n >= 0.03
    flash = ult = None
    if lb is not None and hasattr(lb, "zauber"):
        flash = lb.zauber.fehlt(s, "SummonerFlash", p.zeit)
        ult = lb.zauber.fehlt(s, "R", p.zeit)
    pos = einheiten(g[1], g[2]) if lb is not None and not s.tot and (g := lb.gesehen(s)) else None
    return GegnerLage(s=s, sichtbar=sichtbar, seit=seit, ort=ort or "", abstand=ab, ankunft=ankunft, tempo=ms,
                      flash=flash, ult=ult, level_vorsprung=s.level - p.ich.level,
                      gold_vorsprung=s.item_gold - p.ich.item_gold, kommt_naeher=naeher, pos=pos,
                      shutdown=shutdown(s, p),
                      leben=lb.gegner_leben_jetzt(s, p.zeit) if lb is not None and hasattr(lb, "gegner_leben_jetzt")
                      else None,
                      mana=lb.gegner_mana_jetzt(s, p.zeit) if lb is not None and hasattr(lb, "gegner_mana_jetzt")
                      else None,
                      leben_alter=(p.zeit - lb.gegner_leben[s.name][0]) if lb is not None
                      and s.name in getattr(lb, "gegner_leben", {}) else None)


# --- Kampf um ein Objective --------------------------------------------------------

KAMPF_FENSTER = 15.0     # wer in so vielen Sekunden an der Grube sein kann, kaempft mit


@dataclass
class Kampflage:
    schl: str
    wir: list[tuple[Spieler, float | None, float | None, bool | None]]   # (Spieler, Sekunden zur Grube, Leben, Ult bereit)
    die: list[tuple[Spieler, float | None, float | None]]              # (Gegner, fruehestens an der Grube, seit wann nicht gesehen)
    ohne_flash: list[str]
    ohne_ult: list[str]
    gold: int                  # Item-Gold ihr minus die (alle)
    carry: str = ""            # ihr Carry (Reasoning #25): den zuerst

    def zahlen(self) -> tuple[int, int, int]:
        """(ihr in KAMPF_FENSTER, die sicher in KAMPF_FENSTER, die unbekannt)."""
        wir = sum(1 for _, t, le, _ in self.wir if t is not None and t <= KAMPF_FENSTER and (le is None or le >= 0.35))
        # Gegner: dort, wenn frisch gesehen (<= 10 s) und rechtzeitig; weg, wenn er es selbst im Worst Case nicht
        # schafft; alles dazwischen ist unbekannt (Partie 7: "2 gegen 4" zaehlte jeden Worst Case als Gegner)
        die = sum(1 for _, t, seit in self.die if t is not None and t <= KAMPF_FENSTER and seit is not None and seit <= 10)
        offen = sum(1 for _, t, seit in self.die if t is None or (t <= KAMPF_FENSTER and (seit is None or seit > 10)))
        return wir, die, offen

    def urteil(self) -> tuple[str, str]:
        """('nehmen' | 'abgeben' | 'offen', gesprochener Satz mit den Gruenden)."""
        from .komponist import OBJ_NAME
        wir, die, offen = self.zahlen()
        ults = sum(1 for *_, u in self.wir if u)
        schwach = [s.champion for s, t, le, _ in self.wir if t is not None and t <= KAMPF_FENSTER and le is not None and le < 0.35]
        gruende = [f"ihr {wir} in 15 Sekunden dort" + (f" mit {ults} Ults" if ults else ""),
                   f"sie {die}" + (f", {offen} unbekannt" if offen else "")]
        if self.ohne_flash:
            gruende.append(f"{', '.join(self.ohne_flash[:2])} ohne Flash")
        if schwach:
            gruende.append(f"{', '.join(schwach[:2])} fast tot")
        if abs(self.gold) >= 1500:
            gruende.append(f"{'ihr' if self.gold > 0 else 'sie'} {abs(self.gold) // 100 * 100} Gold vorn")
        name = OBJ_NAME.get(self.schl, self.schl)
        if self.carry:
            gruende.append(f"ihr Carry ist {self.carry}")
        vorteil = wir - (die + offen * 0.5) + (0.5 if self.gold >= 1500 else -0.5 if self.gold <= -1500 else 0) \
            + 0.3 * len(self.ohne_flash) + 0.4 * len(self.ohne_ult)
        if vorteil >= 1:
            return "nehmen", f"{name}: {', '.join(gruende)} - nehmen."
        if vorteil <= -1:
            return "abgeben", f"{name} nicht erzwingen: {', '.join(gruende)} - abgeben, auf der anderen Seite tauschen."
        return "offen", f"{name} ist ein Münzwurf: {', '.join(gruende)} - nur mit Sicht und allen Ults."


def kampf_um(p: Partie, lb, schl: str) -> Kampflage | None:
    """Wer kann in wie vielen Sekunden an der Grube von `schl` sein - beide Seiten - und in welchem Zustand."""
    if lb is None or not getattr(lb, "aktiv", False) or schl not in GRUBEN or not p.ich:
        return None
    grube = einheiten(*GRUBEN[schl])
    wir = []
    for s in p.team(p.mein_team):
        if s.tot:
            continue
        g = lb.gesehen(s)
        t = abstand(einheiten(g[1], g[2]), grube) * WEGFAKTOR / tempo(s) if g and p.zeit - g[0] < 5 else None
        if s.name == p.ich.name:
            m = p.werte.get("maxHealth")
            leben = p.werte.get("currentHealth", 0) / m if m else None
            ult = None
        else:
            leben, ult = lb.leben(s, p.zeit), lb.ult_bereit(s, p.zeit)
        wir.append((s, t, leben, ult))
    die, ohne_flash, ohne_ult = [], [], []
    for s in p.gegner():
        if s.tot:
            continue
        g = lb.gesehen(s)
        if g and p.zeit - g[0] < UNBEKANNT_AB:
            seit = 0.0 if lb.sichtbar(s) else p.zeit - g[0]
            t = max(0.0, abstand(einheiten(g[1], g[2]), grube) / (tempo(s) * GEGNER_TEMPO_RESERVE) - seit)
        else:
            seit = t = None
        die.append((s, t, seit))
        if hasattr(lb, "zauber"):
            if (r := lb.zauber.fehlt(s, "SummonerFlash", p.zeit)) and r > 20:
                ohne_flash.append(s.champion)
            if (r := lb.zauber.fehlt(s, "R", p.zeit)) and r > 20:
                ohne_ult.append(s.champion)
    gold = p.item_gold(p.mein_team) - p.item_gold(gegenteam(p.mein_team))
    c = carry(p, gegenteam(p.mein_team))
    return Kampflage(schl, wir, die, ohne_flash, ohne_ult, gold,
                     carry=f"{c.champion} mit {c.kills} Kills" if c is not None and not c.tot else "")
