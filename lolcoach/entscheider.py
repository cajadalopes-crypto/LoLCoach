"""Der Entscheider: die beste naechste Handlung - auch wenn gerade nichts "passiert".

Die Regeln reagieren auf Ereignisse. Ein Challenger-Coach redet aber auch dazwischen: was ist
JETZT der Plan, in welcher Reihenfolge, und warum? Carlos' Reasoning-Datei (Reasoning/LoL
Reasoning.txt) gibt die Kette vor:

  Champion-Zustand -> Welle -> Lane-Prio -> Tempo -> Kartenzugang -> Information ->
  Gegner-Vorhersage -> moegliche Aktionen -> Gegenantwort -> Erwartungswert -> naechster Zustand

und die sechs Fragen, die jede Entscheidung beantworten muss: Wer ist staerker? Wer ist zuerst
da? Was sehen wir nicht? Welche Welle verlieren wir? Was bekommt der Gegner? Was gewinnen wir
nach dem Play?

Umsetzung: je Takt zaehlt der Entscheider die Handlungen auf, die gerade moeglich sind (Optionen),
prueft jede auf Sicherheit (wer kann dich erreichen, bevor du am Turm bist, und was siehst du
nicht), gibt ihr einen groben Wert (Gold-Aequivalent: Platten, Welle, Item-Timing, Objective,
Kill) und nimmt die beste. Gesprochen wird sie, wenn sie sich aendert und eine Weile haelt - als
Plan mit Reihenfolge ("erst ..., dann ...") und den Fakten, die ihn tragen. Mindestens zwei
Faktoren je Plan, sonst schweigt er (Carlos: "mehrere Faktoren, keine Standardphrasen").
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import komponist
from .bewertung import Bewertung
from .jungle import LANE_SEITE, Jungletracker, anders
from .kaufplan import _dat as kaufplan_dat
from .komponist import OBJ_NAME, sek

LANE_PHASE_BIS = 840
HALTEN = 3.0            # so lange muss eine neue beste Option halten, bevor sie gesagt wird
ABSTAND = 25.0          # mindestens so viele Sekunden zwischen zwei Plaenen
GLEICH_SPERRE = 75.0    # derselbe Plan kommt fruehestens nach so vielen Sekunden wieder
LAUF_ZUR_LANE = {"TOP": 27.0, "MIDDLE": 20.0, "BOTTOM": 27.0, "UTILITY": 27.0}   # Spawn -> Lane-Mitte [Schaetzung]


def wellen_spawns(bis: float) -> list[tuple[float, bool]]:
    """(Spawnzeit, Kanone?) aller Wellen bis `bis` - Saison 2026 (saison2026.md): 0:30 erste Welle,
    bis 14:00 alle 30 s mit Kanone jede 3. (erste = Welle 3 um 1:30), bis 25:00 alle 25 s mit
    Kanone jede 2., bis 30:00 jede Welle mit Kanone, danach alle 20 s."""
    aus, t, k = [], 30.0, 1
    while t <= bis:
        if t < 840:
            kanone = k % 3 == 0
            schritt = 30.0
        elif t < 1500:
            kanone = k % 2 == 0
            schritt = 25.0
        else:
            kanone = True
            schritt = 25.0 if t < 1800 else 20.0
        aus.append((t, kanone))
        t += schritt
        k += 1
    return aus


def naechste_kanone(zeit: float, rolle: str) -> float | None:
    """Spielzeit, zu der die naechste Kanonenwelle in deiner Lane ankommt."""
    lauf = LAUF_ZUR_LANE.get(rolle, 27.0)
    for t, kanone in wellen_spawns(zeit + 120):
        if kanone and t + lauf > zeit + 3:
            return t + lauf
    return None


def _namen_kurz(liste) -> str:
    n = [x.champion for x in liste]
    return n[0] if len(n) == 1 else ", ".join(n[:-1]) + " und " + n[-1]


def uhr(t: float) -> str:
    return f"{int(t // 60)} {int(t % 60):02d}"      # gesprochen "6 27"


@dataclass
class Option:
    name: str
    satz: str
    wert: float
    faktoren: int                 # wie viele unabhaengige Fakten den Satz tragen
    dringend: bool = False

    @property
    def thema(self) -> str:
        return {"zurueck": "gefahr", "druck": "druck", "freeze": "gefahr", "gruppe": "objective",
                "obj_plan": "objective", "seite": "seite", "seite_nicht": "seite", "gank": "druck",
                "invade": "druck", "hilfe": "hilfe", "hilfe_fern": "seite", "reset": "gefahr",
                "muster": "gefahr", "ueberzahl": "druck"}.get(
            self.name, "back" if self.name.startswith("back") else "")


@dataclass
class Entscheider:
    jungle: Jungletracker = field(default_factory=Jungletracker)
    _kandidat: tuple[str, float] | None = None
    _zuletzt: float = -1e9
    _gesagt: dict[str, float] = field(default_factory=dict)
    _einmal: set = field(default_factory=set)
    aktuell: Option | None = None          # die beste Option dieses Takts (fuer Fragen: "was soll ich tun?")

    # --- Optionen ------------------------------------------------------------------

    def optionen(self, b: Bewertung, platten: bool) -> list[Option]:
        rolle = b.ich.rolle
        if b.ich.tot or b.pos is None:
            return []
        if rolle == "JUNGLE":
            return self._jungle(b)
        aus: list[Option] = []
        lane_phase = b.zeit < LANE_PHASE_BIS
        g = b.lane
        j = b.jungler
        wahrsch = self.jungle.wahrscheinlich(b.zeit)
        meine = LANE_SEITE.get(rolle)
        j_bei_mir = wahrsch.get(meine, 0.5) if meine else 0.5
        gefahr = komponist.gefahr(b)
        verwundbar = komponist.verwundbar(b)
        wert_kraefte, _ = b.kraefte()
        vorsprung = b.vorsprung_satz()
        welle = b.welle
        schiebt_ihr = welle is not None and welle[0] >= welle[1] + 2
        schiebt_er = welle is not None and welle[1] >= welle[0] + 2
        j_offen = komponist.jungler_offen(b)

        # 1) Gefahr: jemand, den du nicht siehst, ist vor dir am Turm - und du kannst es dir nicht leisten.
        #    Der Lane-Gegner kurz im Busch ist kein Gank (Test 26.09.: "Shen kann schon da sein" alle 2 min);
        #    er zaehlt allein nur, wenn du wenig Leben hast und er staerker ist.
        if b.zum_turm is not None and b.zum_turm >= 5 and not b.unter_eigenem_turm:
            fremde = [x for x in gefahr if not (g and x.s.name == g.s.name)]
            # nur wer eben (<= 15 s) nah gesehen wurde: lange Fehlende sind Sache der Tief-Regel (regeln._tief_ohne_sicht)
            knapp = [x for x in fremde if x.ankunft is not None and x.ankunft < b.zum_turm - 1
                     and x.seit is not None and x.seit <= 15]
            lane_allein = (not fremde and g is not None and any(x.s.name == g.s.name for x in gefahr)
                           and b.leben is not None and b.leben < 0.45 and wert_kraefte <= -0.5)
            ausgesetzt = bool(verwundbar) or len(knapp) >= 2 or (b.tiefe or 0) >= 0.5
            if (knapp and ausgesetzt) or lane_allein:
                x = knapp[0] if knapp else g
                wer = _namen_kurz(knapp) if len(knapp) >= 2 else x.champion
                wann = komponist._wann(x)
                if len(knapp) >= 2:
                    # mehrere: ohne "seit X weg" - zwei Namen und ihre Zeiten waeren zu lang
                    wann = "können schon da sein" if (x.ankunft or 0) < 2 else f"können in {sek(x.ankunft)} da sein"
                grund = verwundbar[0] if verwundbar else komponist.todespreis(b)
                aus.append(Option("zurueck", f"{wer} {wann}, {sek(b.zum_turm)} bis zum Turm: jetzt zurück"
                                             + (f" - {grund}." if grund else "."),
                                  200, 2 + bool(verwundbar), dringend=True))

        # 2) Frueher Jungler-Plan: Startseite bekannt -> wo kommt der erste Gank?
        if lane_phase and meine and self.jungle.start and 95 <= b.zeit <= 200 and j and not j.s.tot:
            gank = anders(self.jungle.start)
            if gank == meine and (j.seit is None or j.seit >= 15):
                aus.append(Option("gank_erwartet",
                                  f"{j.champion} hat {self.jungle.start} angefangen, {self.jungle.start_grund}: "
                                  + (f"ab Minute 2 kommt {j.champion} zu dir" if b.zeit < 120
                                     else f"ab jetzt kann {j.champion} kommen")
                                  + ". Welle nicht über die Mitte, Ward in den Fluss.",
                                  150, 3))
            elif gank != meine:
                aus.append(Option("gank_weg",
                                  f"{j.champion} hat {self.jungle.start} auf deiner Seite angefangen: sein erster Gank "
                                  f"kommt {gank}. Bis etwa Minute 3 kannst du hart spielen.", 90, 2))

        # 2b) Zwei Tode kurz hintereinander (Reasoning #46, Spieler-Faktor): nach dem Wiedereinstieg einmal der
        #     Reset - sicher farmen bis zum naechsten Spike, kein Trade ohne Sicht. Und solange: kein Druck-Plan.
        serie = len(b.tode_kurz) >= 2
        if serie and b.zeit - b.tode_kurz[-1] <= 120 and ("reset", b.tode_kurz[-1]) not in self._einmal:
            k = b.kauf
            name = ("der " + k.item[4:]) if k is not None and k.item.startswith("Der ") else (k.item if k else "")
            spike = f"bis {name}" if name else "bis zum nächsten Level"
            wer = j.champion if j and not j.s.tot else "den Jungler"
            # kurz halten: 9 s Reset-Satz liess "Shen hat Flash benutzt" verfallen (test_zauber, 26.09.)
            aus.append(Option("reset", f"Zweimal gestorben: sicher farmen {spike}, kein Trade ohne Sicht auf {wer}.",
                              170, 3))

        # 2c) Muster: sein Jungler war schon zweimal an Toden auf deiner Lane beteiligt - er kommt wieder
        mlane = {"TOP": "Top", "MIDDLE": "Mid", "BOTTOM": "Bot", "UTILITY": "Bot"}.get(rolle)
        n_ganks = self.jungle.ganks.get(mlane, 0) if mlane else 0
        if lane_phase and j and not j.s.tot and n_ganks >= 2 and ("muster", n_ganks) not in self._einmal:
            andere = {l: n for l, n in self.jungle.ganks.items() if l != mlane}
            vergleich = f", woanders {sum(andere.values())}x" if andere else ", nirgends sonst"
            aus.append(Option("muster", f"{j.champion} war schon an {n_ganks} Toden auf deiner Lane beteiligt{vergleich}: "
                                        f"{j.champion} spielt auf dich. Welle bei dir halten, tief nur mit Sicht.", 120, 3))

        # 3) Druck: Lane-Gegner sichtbar, du staerker, Jungler tot oder sicher weit weg, Leben gut.
        #    (Camille-Partie 26.09., 4:42/4:50: "Gragas 19 s zu dir, zurueck" und 8 s spaeter "Spiel auf Rumble")
        j_weit = j is None or j.s.tot or (not j.unbekannt and j.ankunft is not None and j.ankunft >= 25
                                          and j_bei_mir < 0.5)
        if g and not g.s.tot and g.seit is not None and g.seit < 2 and not gefahr and not serie \
                and (b.leben or 1) >= 0.6 and wert_kraefte >= 1 and j_weit:
            grund = f"{j.champion} ist {'tot' if j.s.tot else j.ort}" if j and (j.s.tot or not j.unbekannt) else ""
            aus.append(Option("druck", f"Spiel auf {g.champion}: {vorsprung}" + (f", {grund}" if grund else "")
                              + (f" - {b.trade}." if b.trade else "."),
                              60 + 20 * wert_kraefte, 2 + bool(grund)))

        # 4) Recall-Planung mit Reihenfolge: Welle -> back -> Objective
        braucht_back = b.gold >= 1100 or (b.leben is not None and b.leben < 0.45)
        if braucht_back and not gefahr:
            ob = b.objective
            kauf = b.kauf.satz() if b.kauf is not None and b.kauf.kaufen else ""
            grund = (f"{b.gold // 100 * 100} Gold" + (f" {kauf}" if kauf else "") if b.gold >= 1100
                     else f"{int(b.leben * 100)} Prozent Leben")
            if schiebt_er and welle[2] is not None and welle[2] <= 0.45:
                satz = (f"{grund}, aber seine Welle mit {welle[1]} läuft auf deinen Turm: erst abfarmen, "
                        f"dann back - sonst frisst der Turm dein Gold.")
                aus.append(Option("back_warten", satz, 70, 3))
            elif schiebt_ihr:
                satz = f"{grund}: Welle in den Turm, dann back"
                if ob and 45 <= ob[1] <= 150:
                    satz += f" - dann bist du rechtzeitig zurück für {OBJ_NAME[ob[0]]} um {uhr(b.zeit + ob[1])}."
                else:
                    satz += "."
                aus.append(Option("back_plan", satz, 80 + b.gold / 50, 2 + bool(ob)))
            elif (k := naechste_kanone(b.zeit, b.ich.rolle)) and k - b.zeit <= 45:
                aus.append(Option("back_kanone", f"{grund}: Kanonenwelle kommt {uhr(k)} - die in den Turm schieben, "
                                                 f"dann back.", 75 + b.gold / 50, 3))

        # 4b) Knapp vor einem Bauteil: noch eine Welle mitnehmen, dann mit dem Bauteil zurueck
        k = b.kauf
        if (k is not None and not k.kaufen and k.naechstes and k.naechstes[1] <= 200 and b.gold >= 700
                and not gefahr and lane_phase and b.zeit >= 180):   # vor 3:00 ist kein Back-Fenster
            kanone = naechste_kanone(b.zeit, b.ich.rolle)
            welle_satz = (f"die Kanone {uhr(kanone)} mitnehmen" if kanone and kanone - b.zeit <= 40
                          else "noch eine Welle mitnehmen")
            aus.append(Option("back_knapp", f"Noch {k.naechstes[1]} Gold bis {kaufplan_dat(k.naechstes[0])}: "
                                            f"{welle_satz}, dann back.", 72, 2))

        # 5) Objective-Vorlauf 60-120 s: Reihenfolge planen (Welle, Reset, Weg). In der Lane-Phase nur fuer die
        #    Seite des Objectives; danach fuer alle - dann kaempfen alle fuenf darum.
        ob = b.objective
        if ob and 60 <= ob[1] <= 120 and meine is not None:
            name = OBJ_NAME[ob[0]]
            nah = (ob[0] == "drache" and meine == "unten") or (ob[0] != "drache" and meine == "oben")                 or rolle == "MIDDLE"
            if nah or not lane_phase:
                reset = b.gold >= 900 or (b.leben is not None and b.leben < 0.6)
                seite = ("Mid", "Bot") if ob[0] == "drache" else ("Mid", "Top")
                eigene_lane = {"TOP": "Top", "BOTTOM": "Bot", "UTILITY": "Bot", "MIDDLE": "Mid"}.get(rolle)
                prio = komponist._prio_satz(b, tuple(l for l in seite if l != eigene_lane))
                if lane_phase:
                    # die letzte Kanonenwelle vor dem Aufbruch zur Grube: die crashen - dann verliert er Platten/CS,
                    # waehrend du am Objective bist (grundlagen.md, Welle vor Objective)
                    spawn = b.zeit + ob[1]
                    kanonen = [t + LAUF_ZUR_LANE.get(rolle, 27.0) for t, k in wellen_spawns(spawn) if k]
                    weg = b.zum_objective or 20.0      # Lane -> Grube, plus ein paar Sekunden zum Crashen
                    kanone = max((k for k in kanonen if b.zeit + 10 <= k and k + 8 + weg <= spawn - 30), default=None)
                    if reset:
                        tun = "jetzt Welle rein und back, "
                    elif kanone is not None:
                        tun = f"crash die Kanonenwelle um {uhr(kanone)}, dann "
                    else:
                        tun = "Welle langsam aufbauen, "
                else:
                    tun = (f"Seitenwelle bis {uhr(b.zeit + ob[1] - 45)} rausschieben, " + ("dazwischen back, " if reset else ""))
                satz = (f"{name} in {sek(ob[1])}: {tun}spätestens {uhr(b.zeit + ob[1] - 30)} an der Grube sein"
                        + (f" - {prio}." if prio else "."))
                aus.append(Option("obj_plan", satz, 90, 2 + reset + bool(prio)))

        # 5a) Lokale Ueberzahl (Reasoning #19): du und Mitspieler bei dir gegen weniger sichtbare Gegner, und niemand
        #     Unbekanntes kann gleich dazukommen - das ist der Moment, nicht erst der naechste Plan.
        nah_gegner = [x for x in b.gegner if not x.s.tot and x.sichtbar and x.abstand is not None and x.abstand <= 1300]
        stark = any(x.level_vorsprung >= 2 or x.gold_vorsprung >= 2000 for x in nah_gegner)
        if (b.mitspieler_nah and nah_gegner and len(b.mitspieler_nah) + 1 > len(nah_gegner) and not gefahr
                and (b.leben is None or b.leben >= 0.5) and not serie and not stark):
            wir_n, die_n = len(b.mitspieler_nah) + 1, len(nah_gegner)
            ziel = min(nah_gegner, key=lambda x: x.abstand)
            dazu = f", {ziel.champion} ohne Flash" if ziel.flash and ziel.flash > 20 else ""
            aus.append(Option("ueberzahl", f"{wir_n} gegen {die_n} hier: {_namen_kurz(nah_gegner)}"
                                           f"{' allein' if die_n == 1 else ''}{dazu} - rein!", 150, 3, dringend=True))

        # 5b) Ein Mitspieler wird angegriffen: zwei Gegner sichtbar bei ihm (oder einer und er hat wenig Leben).
        #     Wer kann zuerst helfen? Du, wenn du rechtzeitig da bist - sonst die Gegenseite nutzen.
        if (b.leben is None or b.leben >= 0.5) and not gefahr:
            from .bewertung import abstand as _ab
            for s, wo, leben, ort in b.mitspieler:
                bei = [g for g in b.gegner if not g.s.tot and g.sichtbar and g.pos and _ab(g.pos, wo) <= 1400]
                bedraengt = len(bei) >= 2 or (len(bei) == 1 and leben is not None and leben < 0.4)
                if not bedraengt:
                    continue
                weg = _ab(b.pos, wo) * 1.15 / b.mein_tempo
                namen = _namen_kurz(bei)
                lz = f" ({int(leben * 100)} Prozent)" if leben is not None else ""
                if weg <= 10:
                    aus.append(Option("hilfe", f"{s.champion}{lz} kämpft {ort} gegen {namen} - du bist {sek(weg)} "
                                               f"weg: hin!", 160, 3, dringend=True))
                elif weg <= 25 and not lane_phase and (leben is None or leben >= 0.35):
                    # mit 6 Prozent ist er tot, bevor du nach 20 s ankommst (Camille-Partie 17:27)
                    aus.append(Option("hilfe", f"{s.champion}{lz} kämpft {ort} gegen {namen}, {sek(weg)} von dir: "
                                               f"hin, wenn der Kampf noch läuft.", 110, 3))
                elif g is not None and g.s.name not in {x.s.name for x in bei} and not g.s.tot:
                    continue    # dein Lane-Gegner ist nicht dabei - nichts gewonnen
                elif len(bei) >= 2:
                    aus.append(Option("hilfe_fern", f"{namen} sind bei {s.champion} {ort}, zu weit für dich "
                                                    f"({sek(weg)}): nutz es auf deiner Seite - Welle, Turm, Camps.",
                                      65, 3))
                break

        # 6) Freeze/Sicherheit: Jungler wahrscheinlich bei dir, Welle vor deinem Turm, du schiebst nicht
        if lane_phase and j and not j.s.tot and j_bei_mir >= 0.6 and (j.seit is None or j.seit >= 20) \
                and welle and welle[2] is not None and welle[2] <= 0.45 and not schiebt_ihr and b.zeit >= 115:
            aus.append(Option("freeze", f"Welle vor deinem Turm halten: {j.champion} ist wahrscheinlich auf deiner Seite "
                                        f"({int(j_bei_mir * 100)} Prozent), seit {sek(j.seit or b.zeit)} nicht gesehen.",
                              55, 3))

        # 7) Nach der Lane-Phase: Gruppe vor dem Objective, sonst Seitenwelle - mit dem, der antworten kann
        if not lane_phase and rolle in ("TOP", "MIDDLE", "BOTTOM"):
            if ob and 5 <= ob[1] <= 60:
                weg = f", {sek(b.zum_objective)} Weg" if b.zum_objective else ""
                # wer beim Spawn noch tot ist, kann nicht streiten
                fehlen = [s.champion for s in b.tote_gegner if s.respawn > ob[1] + 5]
                dazu = f", {', '.join(fehlen[:3])} beim Spawn noch tot" if fehlen else ""
                aus.append(Option("gruppe", f"{OBJ_NAME[ob[0]]} in {sek(ob[1])}{dazu}: Welle crashen und zum Team{weg}.",
                                  100 + 20 * len(fehlen), 2 + bool(fehlen)))
            elif not gefahr and not (ob and ob[1] <= 75):
                tp = b.zweiter is not None and b.zweiter[0] == "SummonerTeleport" and b.zweiter[1] <= 0
                tp_satz = ", Teleport bereit für den Kampf" if tp else ""
                sichtbar = [x for x in b.gegner if not x.s.tot and x.sichtbar]
                if g and (g.s.tot or (g.sichtbar and (g.ankunft or 0) >= 20)):
                    wo = "tot" if g.s.tot else g.ort
                    aus.append(Option("seite", f"Seite frei, {g.champion} {'ist ' if wo in ('tot', 'oben', 'unten') else ''}"
                                               f"{wo}: Welle drücken, Turm{tp_satz}.", 75, 2 + tp))
                elif g and g.seit is not None and g.seit < 3 and wert_kraefte >= 0.5 and (b.leben or 1) >= 0.6                         and len(sichtbar) >= 3:
                    aus.append(Option("seite", f"Split: nur {g.champion} kann antworten, {vorsprung} - das 1 gegen 1 "
                                               f"nimmst du{tp_satz}.", 80, 3 + tp))
                elif g and wert_kraefte <= -1 and len(sichtbar) < 3:
                    aus.append(Option("seite_nicht", f"Nicht allein splitten: {vorsprung}, und "
                                                     f"{5 - len(sichtbar) - len(b.tote_gegner)} Gegner siehst du nicht. "
                                                     f"Mit dem Team gehen.", 65, 3))
                elif len(sichtbar) >= 3:
                    aus.append(Option("seite", f"{len(sichtbar)} Gegner sichtbar weg von dir: Seitenwelle drücken, "
                                               f"Platten und Turm, bis sich einer zeigt{tp_satz}.", 70, 2 + tp))
        return aus

    # --- Jungle ---------------------------------------------------------------------------

    GANK_PUNKT = {"Top": (0.17, 0.17), "Mid": (0.5, 0.5), "Bot": (0.83, 0.83)}   # Minimap: Flusseingang je Lane
    ROLLEN_DER_LANE = {"Top": ("TOP",), "Mid": ("MIDDLE",), "Bot": ("BOTTOM", "UTILITY")}

    def _jungle(self, b: Bewertung) -> list[Option]:
        """Jungle: wohin gankst du (welche Lane ist verwundbar), und wann ist ein Invade frei.
        Je Lane zaehlt: gegnerischer Flash weg, seine Welle drueckt auf eure Seite (er steht vorn),
        Level/Items eurer Laner gegen seine, wo der gegnerische Jungler ist, dein Weg dorthin."""
        from .bewertung import abstand, einheiten
        p = b.partie
        if p is None or b.zeit < 150:
            return []
        aus: list[Option] = []
        gefahr = komponist.gefahr(b)
        if gefahr and b.leben is not None and b.leben < 0.4:
            return []    # erst sicher werden - die Regeln warnen schon
        feind_j = b.jungler
        j_seite = None
        if feind_j and not feind_j.s.tot and feind_j.seit is not None and feind_j.seit <= 20 and feind_j.ort:
            j_seite = "oben" if any(w in feind_j.ort for w in ("oben", "oberen")) else                 "unten" if any(w in feind_j.ort for w in ("unten", "unteren")) else "mitte"
        beste = None
        for lane, rollen in self.ROLLEN_DER_LANE.items():
            gegner = [g for g in b.gegner if g.s.rolle in rollen and not g.s.tot]
            freunde = [s for s in p.team(p.mein_team) if s.rolle in rollen and not s.tot]
            if not gegner or not freunde:
                continue
            wert, gruende = 0.0, []
            ohne = [g.champion for g in gegner if g.flash and g.flash > 30]
            if ohne:
                wert += 1.2
                gruende.append(f"{' und '.join(ohne)} ohne Flash")
            prio = b.prio.get(lane)
            if prio == "er":
                wert += 0.8
                gruende.append("die gegnerische Welle drückt, der Laner steht vorn")
            elif prio == "ihr":
                wert -= 1.0
            lv = sum(s.level for s in freunde) - sum(g.s.level for g in gegner)
            gd = sum(s.item_gold for s in freunde) - sum(g.s.item_gold for g in gegner)
            wert += 0.4 * lv + gd / 1500
            if lv >= 1 or gd >= 700:
                gruende.append(f"euer {'Laner' if len(freunde) == 1 else 'Duo'} ist vorn")
            seite = {"Top": "oben", "Bot": "unten", "Mid": "mitte"}[lane]
            if j_seite == seite:
                wert -= 1.5          # sein Jungler steht dort: Konter-Gank
            elif j_seite is not None and lane != "Mid":
                wert += 0.4
                gruende.append(f"{feind_j.champion} ist auf der anderen Seite")
            punkt = einheiten(*self.GANK_PUNKT[lane])
            weg = abstand(b.pos, punkt) * 1.15 / b.mein_tempo
            wert -= weg / 25
            if gruende and (beste is None or wert > beste[0]):
                beste = (wert, lane, gruende, weg)
        if beste is not None and beste[0] >= 1.0:
            wert, lane, gruende, weg = beste
            aus.append(Option("gank", f"Gank {lane}: {', '.join(gruende[:3])} - {sek(weg)} Weg.",
                              60 + 20 * wert, len(gruende) + 1))
        # Invade: sein Jungler eben auf der einen Seite gesehen -> seine Camps auf der anderen sind frei
        if j_seite in ("oben", "unten") and (b.leben or 1) >= 0.6 and not gefahr:
            frei = "unten" if j_seite == "oben" else "oben"
            lane = "Bot" if frei == "unten" else "Top"
            if b.prio.get(lane) != "er":        # ohne Prio dort laufen dir seine Laner in den Invade
                aus.append(Option("invade", f"{feind_j.champion} ist {j_seite} gesehen: seine Camps {frei} sind frei "
                                            f"- klauen, solange {feind_j.champion} drüben ist.", 55, 2))
        return aus

    # --- Sprechen ----------------------------------------------------------------------

    def pruefe(self, b: Bewertung | None, platten: bool):
        """Die Ansage dieses Takts (regeln.Ansage) oder None."""
        from .regeln import HINWEIS, WICHTIG, Ansage
        if b is None:
            self.aktuell = None
            return None
        opts = [o for o in self.optionen(b, platten) if o.faktoren >= 2]
        if not opts:
            self.aktuell, self._kandidat = None, None
            return None
        beste = max(opts, key=lambda o: o.wert)
        self.aktuell = beste
        if self._kandidat is None or self._kandidat[0] != beste.name:
            self._kandidat = (beste.name, b.zeit)
            if not beste.dringend:
                return None
        if not beste.dringend and b.zeit - self._kandidat[1] < HALTEN:
            return None
        einmal = beste.name in ("gank_erwartet", "gank_weg")
        if beste.name == "reset":
            self._einmal.add(("reset", b.tode_kurz[-1]))   # je Todesserie einmal
        if beste.name == "muster":
            mlane = {"TOP": "Top", "MIDDLE": "Mid", "BOTTOM": "Bot", "UTILITY": "Bot"}.get(b.ich.rolle)
            self._einmal.add(("muster", self.jungle.ganks.get(mlane, 0)))   # je neuer Anzahl einmal
        if einmal and beste.name in self._einmal:
            return None
        if b.zeit - self._zuletzt < ABSTAND and not beste.dringend:
            return None
        if b.zeit - self._gesagt.get(beste.name, -1e9) < GLEICH_SPERRE:
            return None
        self._zuletzt = b.zeit
        self._gesagt[beste.name] = b.zeit
        if einmal:
            self._einmal.add(beste.name)
        prio = WICHTIG if (beste.dringend or einmal or beste.wert >= 100) else HINWEIS
        return Ansage(beste.satz, prio, f"plan:{beste.name}", gueltig=8 if beste.dringend else 15, sperre=20,
                      thema=beste.thema)
