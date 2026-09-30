"""Stufe 4, der Einbau (Auftrag 034) - ohne Aufnahmen, ohne Modelle, ohne Claude:

- MakroLage aus einem konstruierten Schnappschuss der Live-API plus konstruierten Leser-Werten (Minimap, HUD, 033);
- der Takt gibt aus einer Lage genau eine Anweisung; nie Schweigen;
- Gehirn-Attrappe: feste Werte rein, erwartetes Kommando raus (klar, geteilt, unklar);
- kein Planwechsel ohne Grund (Gefahr, Event, Frage, erledigt, abgelaufen);
- die Sicherheits-Sperre greift (Attrappe und der echte alte Kern: R1);
- Claude-Ausfall, Verspaetung und Abweichung fuehren zur Vorlage; ein treuer Satz wird gesprochen;
- fehlende Wahrnehmung: die betroffene Entscheidung schweigt, die anderen sprechen;
- der alte Kern in der Stellung "makro": die alten Regeln schweigen, gesprochen wird nur der Makro-Entscheider;
- Fragen: erst die Antwort, dann der Plan;
- Laufzeit je Entscheidung unter 50 ms.

    python tests/makro/test_einbau.py
"""
from __future__ import annotations

import os
import statistics
import sys
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(HIER.parents[1]))
os.environ["LOLCOACH_MAKRO_OHNE_GEHIRN"] = "1"      # nie die echten Modelle (in der Cloud fehlen sie ohnehin)

from bau import L, geg, hirn, ich, monster, welle  # noqa: E402
from lolcoach import bewertung, lage as lagemod, regeln, sprechplan, stimme as stimmen, zustand  # noqa: E402
from lolcoach.makro import wahrnehmung  # noqa: E402
from lolcoach.makro.einbau import MakroCoach  # noqa: E402
from lolcoach.makro.entscheidungen import Entscheidung  # noqa: E402
from lolcoach.makro.kommando import Kommando  # noqa: E402
from lolcoach.makro.live import LageBau, bereich  # noqa: E402
from lolcoach.makro.stimme import Stimme, abweichung  # noqa: E402
from lolcoach.makro.takt import Entscheider  # noqa: E402

UNZUVERLAESSIG = [e for e, (_, live) in wahrnehmung.EINGABEN.items() if not live]


# --- ein konstruierter Schnappschuss der Live-API ----------------------------------------------------------------------

def _sp(name, champ, team, rolle, level=9, tot=False, respawn=0.0, items=(), zauber=("Flash", "Teleport")):
    return {"championName": champ, "rawChampionName": f"game_character_displayname_{champ}", "riotIdGameName": name,
            "summonerName": name, "team": team, "position": rolle, "level": level, "isDead": tot,
            "respawnTimer": respawn, "items": [{"itemID": i, "price": 0, "consumable": False} for i in items],
            "scores": {"kills": 1, "deaths": 1, "assists": 1, "creepScore": 80, "wardScore": 5.0},
            "summonerSpells": {f"s{i}": {"rawDisplayName": f"GeneratedTip_SummonerSpell_Summoner{z}_DisplayName"}
                               for i, z in enumerate(zauber)}}


def schnappschuss(zeit=600.0, ereignisse=(), gold=1350.0, leben=0.8, lane_gegner_tot=False):
    wir = [_sp("Carlos", "Ambessa", "ORDER", "TOP", items=(3340, 1055)),
           _sp("Vi1", "Vi", "ORDER", "JUNGLE", zauber=("Flash", "Smite")),
           _sp("Sy", "Sylas", "ORDER", "MIDDLE"), _sp("Va", "Varus", "ORDER", "BOTTOM"),
           _sp("Ba", "Bard", "ORDER", "UTILITY")]
    die = [_sp("Aa", "Aatrox", "CHAOS", "TOP", tot=lane_gegner_tot, respawn=25.0 if lane_gegner_tot else 0.0),
           _sp("Le", "Lee Sin", "CHAOS", "JUNGLE", zauber=("Flash", "Smite")),
           _sp("Br", "Brand", "CHAOS", "MIDDLE"), _sp("Ez", "Ezreal", "CHAOS", "BOTTOM"),
           _sp("Leo", "Leona", "CHAOS", "UTILITY")]
    ev = [{"EventID": 0, "EventName": "GameStart", "EventTime": 0.0}] + [dict(e, EventID=i + 1) for i, e in enumerate(ereignisse)]
    return {"activePlayer": {"riotIdGameName": "Carlos", "summonerName": "Carlos", "currentGold": gold, "level": 9,
                             "championStats": {"currentHealth": 1000.0 * leben, "maxHealth": 1000.0, "moveSpeed": 345.0},
                             "abilities": {}},
            "allPlayers": wir + die, "events": {"Events": ev},
            "gameData": {"gameMode": "CLASSIC", "gameTime": zeit}}


def lagebild(p, zeit):
    """Konstruierte Leser-Werte: Minimap (du Top vor deinem Turm, Mitspieler, Gegner), HUD (Leben/Ult der Mitspieler,
    Trinket 2 Ladungen), Wellen aller drei Lanes, ein Ward deines Teams im gegnerischen Jungle."""
    from lolcoach.sehen import Spurward
    from lolcoach.welle import LaneZustand
    lb = lagemod.Lagebild()
    lb.letztes_bild = zeit
    orte = {"Carlos": (0.12, 0.22), "Vi1": (0.28, 0.45), "Sy": (0.48, 0.52), "Va": (0.82, 0.9), "Ba": (0.8, 0.9),
            "Aa": (0.2, 0.08), "Le": (0.7, 0.35), "Br": (0.55, 0.45), "Ez": (0.9, 0.7), "Leo": (0.9, 0.7)}
    alter = {"Le": 40.0, "Br": 2.0}
    for s in p.spieler:
        x, y = orte[s.name]
        lb.zuletzt[(s.name, s.team)] = (zeit - alter.get(s.name, 0.0), x, y)
    for s in p.team("ORDER"):
        if s.name != "Carlos":
            lb.mitspieler[s.name] = (zeit, 0.3 if s.name == "Sy" else 0.9, True)
    lb.wellen = {l: LaneZustand(l, 4, 2, 0.5, "blau", s_blau=(0.45, 0.47, 0.5, 0.52), s_rot=(0.53, 0.55))
                 for l in ("Top", "Mid", "Bot")}
    lb.wellen_zeit = zeit
    lb.trinket = (2, zeit)
    lb.wardspur.wards = [Spurward(0.47, 0.23, "hell", 0.0, 0.0, bestaetigt=True)]
    lb.wards_zeit = zeit
    lb.platten = {(t, l, "aussen"): n for t in ("ORDER", "CHAOS") for l, n in (("Top", 3), ("Mid", 5), ("Bot", 4))}
    return lb


def lage_aus_schnappschuss():
    d = schnappschuss()
    p = zustand.partie(d)
    lb = lagebild(p, p.zeit)
    b = bewertung.bewerte(p, lb)
    assert b is not None and b.pos is not None, "die Bewertung kennt deine Position aus der Minimap"
    lage, merk = LageBau().bauen(p, b, lb, None)
    assert lage.team == "ORDER" and lage.ich.champion == "Ambessa" and lage.ich.rolle == "TOP"
    assert lage.gold == 1350 and abs(lage.ich.leben - 0.8) < 1e-6 and lage.ich.pos == b.pos
    assert lage.trinket == "gelb" and lage.trinket_ladungen == 2
    assert lage.lane_gegner.champion == "Aatrox" and lage.lane_gegner.gesehen_vor == 0.0
    assert lage.gegner_jungler.gesehen_vor == 40.0            # zuletzt gesehen vor 40 s (Minimap)
    sy = lage.rolle(lage.mitspieler, "MIDDLE")
    assert sy.leben == 0.3 and sy.pos is not None and sy.flash_in is None      # Blitz der Mitspieler: nicht lesbar
    assert set(lage.wellen) == {"top", "mid", "bot"} and lage.welle().groesse == 2
    assert lage.wards and "Flanke" in lage.wards[0].ort                       # Ward im gegnerischen Jungle
    for e in ("uhr", "scoreboard", "eigene_position", "mitspieler_positionen", "mitspieler_hud", "wellen_alle",
              "welle_eigen", "eigene_wards", "trinket_ladungen", "gegner_sichtungen"):
        assert e in lage.vorhanden, e
    for e in UNZUVERLAESSIG:
        assert e not in lage.vorhanden, f"{e} ist unzuverlaessig (033) und bleibt leer"
    assert all(g.tp_in is None and not g.backt for g in lage.gegner)         # TP-Stand, Recall: leer
    assert lage.ward_verloren is None and lage.gesehen_busch is None
    # Merkmale fuer das Gehirn: Namen wie im Training, unbekannt = None
    assert merk["minute"] == 10.0 and merk["rolle"] == 0 and merk["seite"] == 0.0 and merk["anlass"] == 0
    assert merk["bereich"] == bereich(*lage.ich.pos) and merk["in_eigener_lane"] == 1.0
    assert merk["geg1_gesehen_alter"] == 40.0 and merk["mit_lebend"] == 4 and merk["leben_anteil"] == 0.8
    assert merk["drache_da"] == 1.0 and merk["drache_bis"] == 0.0         # 10:00 - der Drache steht (Spawn 5:00)
    assert merk["baron_da"] == 0.0 and merk["baron_bis"] > 0 and merk["tote_gegner"] == 0
    assert "itemwert_team_gegner" not in merk and "diff_level_lane" not in merk   # Entscheidung zu Stufe 2
    assert merk["platten_wir"] == 3.0 and merk["platten_gegner"] == 3.0 and lage.gegner_platten["top"] == 3
    # ohne Minimap: keine Position, keine Wellen - diese Eingaben fehlen, nichts geraten
    lage2, merk2 = LageBau().bauen(p, None, None, None)
    assert lage2.ich.pos is None and "eigene_position" not in lage2.vorhanden and not lage2.wellen
    assert "x" not in merk2 and merk2.get("leben_anteil") is None and "mit_nah" not in merk2


def bereich_wie_training():
    """live.bereich rechnet genau wie phase1.bereich_np (sonst sieht das Gehirn eine andere Karte)."""
    try:
        sys.path.insert(0, str(HIER.parents[1] / "werkzeuge" / "challenger"))
        import numpy as np
        import phase1
    except Exception as e:                      # ohne numpy/Daten-Werkzeuge: uebersprungen
        print(f"   (bereich_wie_training uebersprungen: {type(e).__name__})")
        return
    xs, ys = np.meshgrid(np.linspace(0, 14800, 60), np.linspace(0, 14800, 60))
    soll = phase1.bereich_np(xs.ravel(), ys.ravel())
    ist = [bereich(float(x), float(y)) for x, y in zip(xs.ravel(), ys.ravel())]
    assert list(soll) == ist


# --- der Entscheider ----------------------------------------------------------------------------------------------------

class HirnAttrappe:
    """Feste Werte rein, feste Optionen raus - wie gehirn.Gehirn.bewerte / lage_info."""

    def __init__(self, optionen, siegchance=0.5):
        self.optionen, self.siegchance = optionen, siegchance
        self.bekommen = None

    def bewerte(self, merkmale, kontext=None):
        self.bekommen = (merkmale, kontext)
        return self.optionen

    def lage_info(self, merkmale):
        return {"siegchance": self.siegchance, "jungler": {"Toplane": 0.7}, "jungler_unsicherheit": 0.4}


def eine_anweisung_je_takt():
    e = Entscheider()
    for lage in (L(), ich(L(), lebt=False, respawn=20, leben=0.0), monster(L(), "drache", 50),
                 geg(L(), "TOP", lebt=False, respawn=30)):
        a = e.entscheide(lage)
        assert a is not None and isinstance(a.kommando, Kommando) and a.kommando.text
        assert a.form in ("gefahr", "klar", "geteilt", "unklar", "grund")
        assert (a.zweite is not None) == (a.form == "geteilt")
    # nichts feuert: die Grund-Anweisung (nie Schweigen)
    e2 = Entscheider()
    e2._reg = {}
    a = e2.entscheide(L())
    assert a.kommando.id == "G0" and "Top-Welle" in a.kommando.text
    a = Entscheider()
    a._reg = {}
    assert "Respawn" in a.entscheide(ich(L(), lebt=False, respawn=12)).kommando.text


def gehirn_attrappe():
    # klar, Siegchance 80 %: V2 feuert, die Merkmale und der Kontext kommen an
    h = HirnAttrappe([("Lane", "", 0.6, 0.5, 0.05, "klar", [])], siegchance=0.8)
    e = Entscheider(hirn=h)
    lage = L()
    lage.hirn.optionen = []
    a = e.entscheide(lage, {"minute": 10.0}, {"welle_gecrasht": False})
    assert h.bekommen == ({"minute": 10.0}, {"welle_gecrasht": False})
    assert lage.hirn.siegchance == 0.8 and "V2" in a.gefeuert
    # unklar: was High-Elo hier am haeufigsten tut (Z3), nie Schweigen
    h = HirnAttrappe([("Lane", "", 0.1, 0.4, 0.05, "unklar", ["das tun High-Elo-Spieler hier am haeufigsten"]),
                      ("Back", "", 0.2, 0.1, 0.05, "unklar", [])])
    a = Entscheider(hirn=h).entscheide(L())
    assert a.form == "unklar" and a.kommando.id == "Z3" and "Welle" in a.kommando.tu, (a.form, a.kommando)
    # geteilt: zwei Optionen in einem Satz
    h = HirnAttrappe([("Lane", "", 0.3, 0.3, 0.05, "geteilt", []), ("Split", "", 0.2, 0.3, 0.05, "geteilt", [])],
                     siegchance=0.8)
    a = Entscheider(hirn=h).entscheide(monster(L(), "drache", 50))
    assert a.form == "geteilt" and a.zweite is not None and a.voll.startswith("Zwei Optionen."), a.voll
    assert " Oder: " in a.vorlage and len(a.vorlage.split()) <= 14, a.vorlage        # gesprochen: kurz (Auftrag 002)
    # das Gehirn faellt aus: die Regeln entscheiden allein, der Takt laeuft weiter
    class Kaputt(HirnAttrappe):
        def bewerte(self, *a, **k):
            raise RuntimeError("Modell kaputt")
    e = Entscheider(hirn=Kaputt([]))
    a = e.entscheide(L())
    assert a is not None and e.hirn_fehler and a.kommando.text


def echtes_gehirn_schnittstelle():
    """Die echte Logik von werkzeuge/challenger/gehirn.py (Vektor aus dem Merkmals-dict, Klarheit, Back nur mit
    Grund) mit den Live-Merkmalen - nur die Modellwerte (werte, lage_info) sind fest, die Modelle fehlen hier."""
    try:
        import numpy as np
        sys.path.insert(0, str(HIER.parents[1] / "werkzeuge" / "challenger"))
        import gehirn as gh
        import modelle as mo
    except Exception as e:
        print(f"   (echtes_gehirn_schnittstelle uebersprungen: {type(e).__name__})")
        return

    class Fest(gh.Gehirn):
        def __init__(self, q, p_):
            self.schluessel = ["Back", "Lane", "Objective:Drache"]
            self.merkmale = list(mo.BASIS_NAMEN)
            self.idx = {n: i for i, n in enumerate(self.merkmale)}
            self.schwellen = {"delta": 0.005, "p_klar": 0.15, "p_geteilt": 0.08}
            self._q, self._p = np.array(q, float), np.array(p_, float)
            self.vektoren = []

        def werte(self, v):
            self.vektoren.append(v)
            return self._q, self._p, np.full(len(self._q), 0.05)

        def grund(self, v, a, b, n=3):
            return ["Leben hoch"]

        def lage_info(self, lage):
            return {"siegchance": 0.55, "jungler": {"Toplane": 0.2}, "jungler_unsicherheit": 0.9}

    p = zustand.partie(schnappschuss(gold=300.0))       # wenig Gold: kein Back-Grund aus dem Gold
    lb = lagebild(p, p.zeit)
    b = bewertung.bewerte(p, lb)
    bau = LageBau()
    lage, merk = bau.bauen(p, b, lb, None)
    h = Fest(q=[0.03, 0.01, 0.0], p_=[0.5, 0.3, 0.2])          # Back vorn, aber ohne Back-Grund
    a = Entscheider(hirn=h).entscheide(lage, merk, bau.kontext(lage))
    v = h.vektoren[0]
    assert v[h.idx["minute"]] == 10.0 and v[h.idx["rolle"]] == 0 and np.isnan(v[h.idx["lg_x"]])
    assert lage.hirn.optionen[0][0] == "Lane" and lage.hirn.klarheit == "klar", lage.hirn.optionen
    assert lage.hirn.siegchance == 0.55 and a.kommando is not None
    # die Welle ist gecrasht (Kontext aus der Lage): jetzt darf Back vorn stehen
    lage, merk = bau.bauen(p, b, lb, None)
    lage.wellen["top"].stand = "gecrasht"
    Entscheider(hirn=h).entscheide(lage, merk, bau.kontext(lage))
    assert lage.hirn.optionen[0][0] == "Back" and "Back-Grund: Welle gecrasht" in lage.hirn.optionen[0][6]
    assert lage.plan.get("back")                              # die anderen Entscheidungen wissen: Back ist der Plan


def _reg(*paare):
    """Ein eigenes Register: (Nummer, Klasse, Wert, feuert(lage) -> bool)."""
    return {i: Entscheidung(i, i, "R", ("uhr",), (), (lambda f, i=i, k=k, w=w: lambda l: Kommando(
        i, f"Tu {i}", f"Grund {i}", klasse=k, wert=w) if f(l) else None)(f)) for i, k, w, f in paare}


def kein_planwechsel_ohne_grund():
    b_an = {"an": False}
    e = Entscheider(halten_s=20.0)
    e._reg = _reg(("A", "rest", 1.0, lambda l: True), ("B", "rest", 2.0, lambda l: b_an["an"]),
                  ("G", "gefahr", 0.0, lambda l: l.plan.get("gefahr_test", False)))
    a = e.entscheide(L(zeit=600))
    assert a.kommando.id == "A" and a.neu and a.grund == "erster"
    b_an["an"] = True                                 # B ist jetzt besser, aber es gibt keinen Grund
    a = e.entscheide(L(zeit=601))
    assert a.kommando.id == "A" and not a.neu and a.grund == "gehalten"
    a = e.entscheide(L(zeit=602), anlass="kill")      # Event: der Wechsel ist erlaubt
    assert a.kommando.id == "B" and a.neu and a.grund == "event"
    b_an["an"] = False
    a = e.entscheide(L(zeit=603))                     # B feuert nicht mehr: erledigt
    assert a.kommando.id == "A" and a.grund == "erledigt"
    b_an["an"] = True
    a = e.entscheide(L(zeit=604), frage=True)         # Carlos fragt
    assert a.kommando.id == "B" and a.grund == "frage"
    e2 = Entscheider(halten_s=20.0)
    e2._reg = e._reg
    b_an["an"] = False
    e2.entscheide(L(zeit=600))
    b_an["an"] = True
    assert e2.entscheide(L(zeit=610)).kommando.id == "A"      # 10 s: gehalten
    assert e2.entscheide(L(zeit=621)).grund == "abgelaufen"   # 21 s: der bessere Plan darf kommen
    g = L(zeit=622)
    g.plan["gefahr_test"] = True
    a = e2.entscheide(g)                                       # Gefahr wechselt immer
    assert a.kommando.id == "G" and a.form == "gefahr" and a.grund == "gefahr"


def sicherheits_sperre():
    # Attrappe: alles mit "Tu B" ist gesperrt - B wird nicht gesagt, A kommt
    e = Entscheider(sperre=lambda t: ["nach vorn trotz R1"] if "Tu B" in t else [])
    e._reg = _reg(("A", "rest", 1.0, lambda l: True), ("B", "rest", 5.0, lambda l: True))
    a = e.entscheide(L())
    assert a.kommando.id == "A" and a.gesperrt == [("B", "nach vorn trotz R1")]
    # alles gesperrt, auch G0: zurueck zum Turm
    e = Entscheider(sperre=lambda t: [] if "Turm" in t else ["gesperrt"])
    e._reg = _reg(("B", "rest", 5.0, lambda l: True))
    a = e.entscheide(L())
    assert a.kommando.id == "G0" and "Turm" in a.kommando.text and a.form == "gefahr"
    # der echte alte Kern als Sperre: R1 (Leben unter vor_leben_min) - nichts nach vorn
    from types import SimpleNamespace
    from lolcoach.kern import Kern
    k = Kern(stellung="neu")
    p = zustand.partie(schnappschuss(leben=0.1))
    k.m = SimpleNamespace(b=SimpleNamespace(gegner=[], partie=None, ich=None), leben=0.1, tot=False, zeit=600.0, p=p)
    assert k.makro_sperre("Drück die Welle in ihren Turm: er ist tot.")
    assert not k.makro_sperre("Zurück zu deinem Turm: zu wenig Leben.")
    assert k.makro_sperre("Aatrox ist tot: Welle drücken.")        # Fakten: Aatrox lebt laut API
    assert k.makro_sperre("Geh zur Welle, das lohnt sich.")        # verbotener Grund (Tautologie)
    # im Takt: das Kommando "Druck ..." faellt, der sichere Rest bleibt
    e = Entscheider(sperre=k.makro_sperre)
    a = e.entscheide(welle(ich(L(), leben=0.1), stand="bei_ihnen", groesse=3))
    assert not k.makro_sperre(a.vorlage), a.vorlage


def claude_nur_stimme():
    e = Entscheider()
    e._reg = _reg(("A", "rest", 1.0, lambda l: True))
    anw = e.entscheide(L())
    namen = {"Aatrox", "Ambessa", "Vi"}

    def warte(auftrag):
        t = time.monotonic()
        while not auftrag.fertig and time.monotonic() - t < 3:
            time.sleep(0.01)
        return auftrag.ergebnis()

    def kaputt(*a, **k):
        raise TimeoutError("Abo antwortet nicht")
    text, quelle = warte(Stimme(frage=kaputt, frist_s=1.0).formen(anw, namen))
    assert text == anw.vorlage and quelle.startswith("vorlage:ausfall"), quelle

    def langsam(*a, **k):
        time.sleep(1.0)
        return "Tu A jetzt."
    text, quelle = warte(Stimme(frage=langsam, frist_s=0.2).formen(anw, namen))
    assert text == anw.vorlage and quelle == "vorlage:zu langsam", quelle

    def erfindet(*a, **k):
        return "Tu A und geh dann rein auf Aatrox."
    text, quelle = warte(Stimme(frage=erfindet, frist_s=1.0).formen(anw, namen))
    assert text == anw.vorlage and "abweichung" in quelle, quelle

    def treu(*a, **k):
        return "Tu A, denn: Grund A."
    text, quelle = warte(Stimme(frage=treu, frist_s=1.0).formen(anw, namen))
    assert text == "Tu A, denn: Grund A." and quelle == "claude", (text, quelle)
    # Gefahr formt Claude nie - sie muss sofort heraus
    g = Entscheider()
    g._reg = _reg(("G", "gefahr", 1.0, lambda l: True))
    ga = g.entscheide(L())
    au = Stimme(frage=treu).formen(ga, namen)
    assert au.fertig and au.ergebnis() == (ga.vorlage, "vorlage:gefahr")
    # Treue-Pruefung einzeln
    v = "Warte 8 s auf Vi: dann 5 gegen 4. Danach Drache."
    assert not abweichung("Warte 8 Sekunden auf Vi, dann seid ihr 5 gegen 4, danach Drache.", v, namen)
    assert abweichung("Warte 10 s auf Vi, dann Drache.", v, namen)               # Zahl erfunden
    assert abweichung("Warte 8 s auf Vi, dann 5 gegen 4 und Drache - nicht warten.", v, namen)   # Verneinung
    assert abweichung("Warte 8 s auf Aatrox, dann 5 gegen 4. Danach Drache.", v, namen)          # Name erfunden
    assert abweichung("Warte 8 s auf Vi, dann 5 gegen 4 und back.", v, namen)                   # Handlung erfunden


def fehlende_wahrnehmung():
    e = Entscheider()
    lage = welle(L(), stand="gecrasht", groesse=2)
    lage.vorhanden = {"uhr", "ereignisse", "scoreboard", "eigene_items", "gegner_items", "monster_timer",
                      "eigene_position", "gegner_sichtungen", "mitspieler_positionen"}     # keine Welle, kein HUD
    a = e.entscheide(lage)
    ohne_welle = [i for i, x in e._reg.items() if "welle_eigen" in x.eingaben]
    assert ohne_welle and all(i in a.stumm for i in ohne_welle)
    assert not set(a.gefeuert) & set(ohne_welle)
    assert a.kommando is not None and a.kommando.text                   # die anderen sprechen (oder G0)
    # die sechs unzuverlaessigen schweigen immer - auch wenn die Lage (im Test) ihre Felder fuellt
    lage = L(ward_verloren="Tri-Busch", gesehen_busch=True)
    a = Entscheider().entscheide(lage)
    for i, x in Entscheider()._reg.items():
        if wahrnehmung.fehlt(x.eingaben):
            assert i in a.stumm and i not in a.gefeuert, i
    assert {"S11", "S12", "B5", "T9", "O12", "P2"} <= set(a.stumm)


def laufzeit():
    """Die Entscheidung unter 50 ms je Takt (Gehirn-Attrappe; das echte Gehirn: 4,7 ms Median, phase3a_bericht)."""
    h = HirnAttrappe([("Lane", "", 0.6, 0.5, 0.05, "klar", [])], siegchance=0.6)
    e = Entscheider(hirn=h)
    lagen = [L(), monster(L(), "drache", 50), geg(L(), "TOP", lebt=False, respawn=30), welle(L(), stand="gecrasht"),
             hirn(L(), siegchance=0.8)]
    for _ in range(40):
        for lage in lagen:
            e.entscheide(lage, {"minute": 10.0})
    z = e.laufzeit()
    print(f"   Laufzeit Entscheider: Median {z['median_ms']:.2f} ms, p95 {z['p95_ms']:.2f} ms, max {z['max_ms']:.2f} ms "
          f"(n = {z['n']})")
    assert z["p95_ms"] < 50.0, z
    # dazu der Lagebau aus dem Schnappschuss (Partie, Bewertung, Lagebild)
    d = schnappschuss()
    p = zustand.partie(d)
    lb = lagebild(p, p.zeit)
    b = bewertung.bewerte(p, lb)
    bau = LageBau()
    t = []
    for _ in range(50):
        t0 = time.perf_counter()
        lage, merk = bau.bauen(p, b, lb, None)
        e.entscheide(lage, merk, bau.kontext(lage))
        t.append((time.perf_counter() - t0) * 1000)
    print(f"   Laufzeit Lagebau + Entscheider: Median {statistics.median(t):.2f} ms, max {max(t):.2f} ms")
    assert statistics.median(t) < 50.0


# --- der Einbau: Kern in der Stellung "makro", Sprechen, Fragen -------------------------------------------------------------

def _lauf(n=4, ereignisse=(), start=600.0, **kw):
    """Regelwerk + Kern(makro) + Sprechplan wie live, n Takte je 1 s. Rueckgabe (Kern, Plan, [Ansagen je Takt])."""
    from lolcoach.kern import Kern
    werk, plan = regeln.Regelwerk(), sprechplan.Sprechplan(stimmen.Stumm())
    k = Kern(stellung="makro")
    werk.kern = plan.kern = k
    k.transport = plan
    alle = []
    for i in range(n):
        p = zustand.partie(schnappschuss(zeit=start + i, ereignisse=ereignisse, **kw))
        lb = lagebild(p, p.zeit)
        alt = werk.pruefe(p, lb)
        assert alt == [], f"alte Regeln sprechen: {[a.text for a in alt]}"
        neu = k.takt(p, lb)
        alle.append(neu)
        plan.neu(neu)
        plan.takt(p.zeit)
    return k, plan, alle


def kern_stellung_makro():
    k, plan, alle = _lauf(4)
    assert k.makro_coach is not None and k.makro_coach.hirn is None
    gesagt = [a for takt in alle for a in takt]
    assert gesagt and all(a.schluessel.startswith("kern:MAKRO_") for a in gesagt), [a.schluessel for a in gesagt]
    assert len(alle[0]) == 1                                    # genau eine Anweisung
    assert sum(len(t) for t in alle[1:]) == 0                   # der Plan steht: kein neuer Satz
    assert plan.gesagt and plan.gesagt[0].text == gesagt[0].text
    assert k.makro_coach.protokoll and k.makro_coach.protokoll[0]["id"] == gesagt[0]._makro["id"]
    # der alte Kern rechnet mit (Sicherheits-Sperre), sagt aber nichts
    assert k.m is not None and k.spricht_in("LANE") and k.spricht_in(None)
    # nie Schweigen: nach erinnern_s Stille eine kurze Erinnerung
    k2, plan2, alle2 = _lauf(40)
    erinnert = [a for t in alle2 for a in t if a._kategorie == "ERINNERUNG"]
    assert erinnert and erinnert[0].text.startswith("Weiter:"), [a.text for t in alle2 for a in t]
    # ein Ereignis (Kill des Lane-Gegners) darf den Plan wechseln - hoerbar als WENDEPUNKT
    k3, plan3, alle3 = _lauf(3, lane_gegner_tot=True, ereignisse=[
        {"EventName": "ChampionKill", "EventTime": 598.0, "KillerName": "Carlos", "VictimName": "Aa", "Assisters": []}])
    assert any(a for t in alle3 for a in t)


def hoechstens_14_woerter():
    """Auftrag 002 / Szenario s23-plan-hoechstens-14: gesprochen hoechstens 14 Woerter (Gefahr 8) - gekuerzt wird von
    hinten, die Handlung bleibt."""
    from lolcoach.makro.takt import Anweisung
    lang = Kommando("W10", "Er ist 20 s tot: Welle crashen, zwei Platten", "du hast 35 s, bis er zurueck ist",
                    "dann Back und mit dem naechsten Bauteil zurueck an die Top-Welle")
    a = Anweisung(lang, "klar")
    assert len(a.voll.split()) > 14 and len(a.vorlage.split()) <= 14 and a.vorlage.startswith("Er ist 20 s tot")
    g = Anweisung(Kommando("J5", "Zurueck zum Turm", "Vi und Brand fehlen seit mindestens 15 s", "Bot anpingen",
                           klasse="gefahr"), "gefahr")
    assert g.vorlage == "Zurück zum Turm." and len(g.voll.split()) > 8


def verworfen_kommt_wieder():
    """Verwirft der Sprechplan die Plan-Ansage (Sprech-Tor, Back-Sperre aus 028, zu alt), gilt der Plan als nicht
    gesagt und kommt erneut - der neue Plan geht nie still verloren."""
    mc = MakroCoach(kern=None, hirn=None)
    mc.entscheider._reg = _reg(("A", "rest", 1.0, lambda l: True))
    p = zustand.partie(schnappschuss(zeit=600.0))
    erste = mc.takt(p, None, None, None, gesagt=[])
    assert len(erste) == 1 and erste[0].gesprochen is None and erste[0]._kategorie == "PLAN" and erste[0]._mit_grund
    for z in (601.0, 605.0):
        assert mc.takt(zustand.partie(schnappschuss(zeit=z)), None, None, None, gesagt=[]) == []
    neu = mc.takt(zustand.partie(schnappschuss(zeit=612.0)), None, None, None, gesagt=[])   # 8 s gueltig + 2 s
    assert len(neu) == 1 and neu[0].text == erste[0].text and mc.verworfen == 1


def verdrahtung_035():
    """Auftrag 035, Befunde aus dem Nachspiel botspiel_riven_2: keine Gefahr loest eine andere Gefahr ab, solange die
    alte gilt; dieselbe Entscheidung kommt binnen 30 s nur kurz wieder; wer steht, bekommt seine Anweisung ("Los:");
    im Brunnen halten Warnungen fuer draussen keinen Plan fest; das 2 gegen 2 in der Lane ist kein Kampf."""
    # Gefahr gegen Gefahr
    an = {"G2": False}
    e = Entscheider()
    e._reg = _reg(("G1", "gefahr", 3.0, lambda l: True), ("G2", "gefahr", 5.0, lambda l: an["G2"]))
    assert e.entscheide(L(zeit=600)).kommando.id == "G1"
    an["G2"] = True
    assert e.entscheide(L(zeit=601)).kommando.id == "G1"          # G1 gilt noch: kein Pingpong
    assert e.entscheide(L(zeit=602), anlass="kill").kommando.id == "G2"
    # Brunnen: die Warnung haelt keinen Plan
    e = Entscheider()
    e._reg = _reg(("G1", "gefahr", 3.0, lambda l: True), ("A", "rest", 1.0, lambda l: True))
    assert e.entscheide(ich(L(), im_brunnen=True)).kommando.id == "A"
    # Wiederholung kurz, Stillstand "Los:"
    mc = MakroCoach(kern=None, hirn=None)
    mc.entscheider._reg = _reg(("A", "rest", 1.0, lambda l: l.zeit < 605 or l.zeit >= 608),
                              ("B", "rest", 0.5, lambda l: 605 <= l.zeit < 609))
    def takt(z, x=0.12):
        d = schnappschuss(zeit=z)
        p = zustand.partie(d)
        lb = lagebild(p, z)
        s_ = lb.zuletzt[("Carlos", "ORDER")]
        lb.zuletzt[("Carlos", "ORDER")] = (z, x, s_[2])
        return mc.takt(p, bewertung.bewerte(p, lb), lb, None, gesagt=[])
    erste = takt(600.0)
    assert erste and erste[0].text.startswith("Tu A")
    texte = []
    for i, z in enumerate(range(601, 621)):
        texte += [a.text for a in takt(float(z), x=0.12 + (0.02 * i if z < 612 else 0.2))]
    assert any(t.startswith("Tu B") for t in texte), texte              # 605: A erledigt, B
    assert "Weiter: Tu A." in texte, texte                               # 609: B erledigt, A wieder - nur kurz
    assert any(t.startswith("Los:") or t.startswith("Tu") for t in texte[-2:]), texte   # er steht ab 612
    # Kampf: die Botlane 2 gegen 2 in der Lane-Phase ist keiner
    from lolcoach.makro.lage import Spieler as Sp
    lage = L(zeit=400)
    lage.gegner = [Sp("Ezreal", "BOTTOM", pos=(12500, 1800), gesehen_vor=0), Sp("Leona", "UTILITY", pos=(12600, 1900),
                                                                               gesehen_vor=0)]
    lage.mitspieler = [Sp("Varus", "BOTTOM", pos=(12000, 1700)), Sp("Bard", "UTILITY", pos=(12100, 1600))]
    lb = lagemod.Lagebild()
    bau = LageBau()
    assert bau._kampf(lage, lb) is None and bau._kampf(lage, lb, kill_vor=3.0) is not None
    lage.zeit = 1200
    assert bau._kampf(lage, lb) is not None


def fragen_antwort_dann_plan():
    k, plan, alle = _lauf(2)
    mc = k.makro_coach
    p = zustand.partie(schnappschuss(zeit=602))
    r = mc.beantworte("Was soll ich jetzt machen?", p)
    assert r["quelle"] == "makro" and r["text"] == mc.entscheider.aktiv.voll       # gefragt: der ganze Satz
    r = mc.beantworte("Warum soll ich das machen?", p)
    assert r["text"].startswith("Weil ") and "Also:" in r["text"]
    assert mc.beantworte("Und danach?", p)["text"].startswith("Danach")
    assert mc.beantworte("Ist es sicher?", p)["text"].endswith(mc.plan_satz())      # erst die Antwort, dann der Plan
    assert mc.beantworte("Wie steht es?", p)["text"].startswith("Kills ")
    assert mc._frage                                        # der naechste Takt darf den Plan wechseln
    assert mc.beantworte("Wann kommt der Herold?", p) is None                  # Fakten: der alte Weg
    assert mc.mit_plan("Herold in 2 Minuten.", "TIMER").startswith("Herold in 2 Minuten. Plan: ")
    assert mc.mit_plan("Notiert.", "NOTIZ") == "Notiert."
    assert "PLAN (vom Coach entschieden" in "\n".join(mc.kontext_zeilen())


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for test in (lage_aus_schnappschuss, bereich_wie_training, eine_anweisung_je_takt, gehirn_attrappe,
                 echtes_gehirn_schnittstelle,
                 kein_planwechsel_ohne_grund, sicherheits_sperre, claude_nur_stimme, fehlende_wahrnehmung, laufzeit,
                 kern_stellung_makro, verworfen_kommt_wieder, verdrahtung_035, hoechstens_14_woerter,
                 fragen_antwort_dann_plan):
        test()
        print(f"{test.__name__} OK")
