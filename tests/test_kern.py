"""Der Entscheidungskern an konstruierten Lagen (Buch 1, 6.2; Buch 3, 7.2): tests/szenarien/konstruiert/*.toml.

Jede Lage: ein Takt des Kerns, Plan gegen soll / darf_nicht / satz_enthaelt - dazu die Satzform (Buch 0, 9.3):
PLAN hoechstens 14 Woerter, GEFAHR hoechstens 8 (Auftrag 002, S2.3; vorher 18 und 10).

    python tests/test_kern.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach.kern import konfig, testlage  # noqa: E402
from lolcoach.kern.handlung import SICHER  # noqa: E402


def konstruierte_lagen():
    c = konfig()["sprechen"]
    ergebnisse = [r for r in testlage.alle() if not r.get("uebersprungen")]   # Modi spaeterer Schritte: noch nicht
    rot = [r for r in ergebnisse if r["verstoesse"]]
    assert not rot, "\n".join(f"{r['datei']}: {r['id']} -> {r['plan']}: {r['verstoesse']}  Top: {r['top'][:4]}"
                              for r in rot)
    from lolcoach.stratege import back_ruf
    for r in ergebnisse:
        grenze = c["max_woerter_gefahr"] if r["gefahr"] and r["plan"] in SICHER else c["max_woerter"]
        if back_ruf(r["satz"]):
            grenze += 6              # Auftrag 016, 2: ein Back-Ruf traegt die Kette (Kauf und Ziel) - hoechstens 6 Woerter
        assert len(r["satz"].split()) <= grenze, (r["id"], r["satz"])
    assert len(ergebnisse) >= 25, len(ergebnisse)


def neuer_plan_ist_der_beste():
    """Pruefung B: ein NEU gewaehlter Plan liegt nie mehr als hysterese_ge unter dem besten erlaubten Kandidaten -
    erlaubt ist unter Gefahr, was das Gate nicht ausloest (144655 6:44: STAPELN p_tod 0,51 hielt gegen FARMEN 0,02).
    Hält eine Regel einen schlechteren Plan, steht sie in `gehalten`."""
    import random
    from types import SimpleNamespace
    from lolcoach.kern.handlung import Handlung
    from lolcoach.kern.plan import PlanFuehrer, gefahr_schlaegt_an
    cfg = konfig()
    hg = cfg["plan"]["hysterese_ge"]
    zufall = random.Random(7)
    f = PlanFuehrer(cfg)
    arten = ["FARMEN", "STAPELN", "PLATTEN", "WELLE_REIN_UND_BACK", "BACK_JETZT", "ZURUECK"]
    for i in range(600):
        kand = []
        for art in arten:
            h = Handlung(art, None, "LANE", 10.0)
            h.ev = zufall.uniform(-600, 600)
            h.p_tod = zufall.choice([0.0, 0.02, 0.1, 0.5])
            h.verlust = 1500.0
            kand.append(h)
        m = SimpleNamespace(zeit=float(i), pos=None, b=None)
        ev = f.takt(m, kand, False)
        if ev is not None and ev.art in ("neu", "gefahr") and ev.plan is not None:
            erlaubt = kand
            if ev.art == "gefahr" or (ev.plan.handlung.art != max(kand, key=lambda h: h.ev).art
                                      and any(gefahr_schlaegt_an(h, cfg["gefahr"]) for h in kand)):
                erlaubt = [h for h in kand if h.art in SICHER or not gefahr_schlaegt_an(h, cfg["gefahr"])] or kand
            beste = max(h.ev for h in erlaubt)
            assert ev.plan.handlung.ev >= beste - hg, (i, ev.art, ev.plan.art, ev.plan.handlung.ev, beste)
        elif f.plan is not None and max(h.ev for h in kand) - f.plan.handlung.ev >= hg and f.gehalten is None:
            gefahr = gefahr_schlaegt_an(f.plan.handlung, cfg["gefahr"])
            assert gefahr or f.gehalten is not None, (i, f.plan.art)


def plan_haelt_bei_kurzer_luecke():
    """G3 (Qualitaetsrunde 2, 140253 3:56-4:05): faellt der Kandidat des Plans einen Takt heraus, bleibt der Plan; fehlt
    er laenger (luecke_s), kommt der beste andere - und kehrt der bessere zurueck, sperrt halten_s das nicht."""
    from types import SimpleNamespace
    from lolcoach.kern.handlung import Handlung
    from lolcoach.kern.plan import PlanFuehrer
    f = PlanFuehrer(konfig())

    def h(art, ev):
        x = Handlung(art, None, "LANE", 10.0)
        x.ev, x.p_tod, x.verlust = ev, 0.1, 1500.0
        return x

    def takt(t, *kand):
        return f.takt(SimpleNamespace(zeit=t, pos=None, b=None), list(kand), False)
    takt(100.0, h("WELLE_REIN_UND_BACK", 440), h("STAPELN", 200))
    assert f.plan.art == "WELLE_REIN_UND_BACK"
    takt(100.5, h("STAPELN", 200))                                   # ein Takt ohne ihn: der Plan haelt
    assert f.plan.art == "WELLE_REIN_UND_BACK", f.plan.art
    takt(101.0, h("WELLE_REIN_UND_BACK", 440), h("STAPELN", 200))
    takt(101.5, h("STAPELN", 200))
    takt(104.0, h("STAPELN", 200))                                   # laenger weg: STAPELN
    assert f.plan.art == "STAPELN", f.plan.art
    takt(104.5, h("WELLE_REIN_UND_BACK", 440), h("STAPELN", 200))    # zurueck, 240 besser
    takt(106.6, h("WELLE_REIN_UND_BACK", 440), h("STAPELN", 200))    # nach stabil_s, lange vor halten_s
    assert f.plan.art == "WELLE_REIN_UND_BACK", (f.plan.art, f.gehalten)


def fenster_gruende_sprechen_dafuer():
    """Pruefung C3: der Grund fuer ein Turm-Ziel spricht FUER die Handlung - jedes genannte Fenster (noch T Sekunden
    tot, fruehestens in T Sekunden) ist >= Weg + Dauer (`bis`). Vorher: "fruehestens in 0 Sekunden", "noch 3 Sekunden
    tot" (102112, 24:26 / 25:47 / 37:35)."""
    import random
    import re
    from types import SimpleNamespace
    from lolcoach.kern.modi.karte import TurmZiel, fenster_grund
    zufall = random.Random(3)
    for _ in range(500):
        ankunft = []
        for k in range(zufall.randint(0, 4)):
            tot = zufall.random() < 0.5
            s = SimpleNamespace(tot=tot, respawn=zufall.uniform(1, 50) if tot else 0.0)
            g = SimpleNamespace(s=s, champion=f"G{k}")
            ankunft.append((g, s.respawn + zufall.uniform(5, 30) if tot else zufall.uniform(0, 60)))
        ankunft.sort(key=lambda x: x[1])
        bis = zufall.uniform(5, 45)
        kommen = [g for g, t in ankunft if t <= bis][:1]
        z = TurmZiel("CHAOS", "Mid", "aussen", (0, 0), "den äußeren Mid-Turm", 10.0, ankunft, 0)
        m = SimpleNamespace(woanders=zufall.randint(0, 4))
        satz = fenster_grund(z, m, bis, kommen)
        for zahl in re.findall(r"(\d+) Sekunden", satz):
            assert int(zahl) >= int(bis), (satz, bis)
        if kommen:
            # Pruefung c, R2: kein "du schlaegst X" mehr - wer vorher kommt, wird nur benannt (der Satz ist stumm)
            assert "schlägst" not in satz and "vorher" in satz, satz


def gold_reicht_fuer_das_genannte_item():
    """Pruefung E5: "N Gold fuer X" - X kostet (abzueglich der Bauteile, die du hast) hoechstens N. Der Kern nennt,
    was der Kaufplan mit diesem Gold JETZT kauft (140253 3:49: "1050 Gold fuer Axiombogen" stimmte - der Brutalisierer
    lag schon im Inventar, Rest 713)."""
    import random
    from lolcoach import ddragon, kaufplan
    it = ddragon.items()
    zufall = random.Random(11)
    kern = list(kaufplan.kern("Riven")) + list(kaufplan.folge("Riven"))
    teile = sorted({int(f) for i in kern for f in (it.get(i, {}).get("from") or [])})
    for _ in range(300):
        inventar = tuple(zufall.sample(teile, zufall.randint(0, min(3, len(teile)))))
        gold = zufall.randint(300, 4000)
        k = kaufplan.plan("Riven", inventar, gold)
        if k is None:
            continue
        for name in k.kaufen:
            if name == "Stiefel":
                continue
            i = kaufplan._nach_name()[name]
            rest, _ = kaufplan._baum_kosten(i, list(inventar))
            assert rest <= gold, (name, rest, gold, inventar)


def info_flash_kurz_und_gebuendelt():
    """Auftrag 002, S3.1 und Auftrag 016, 1.1: jeder gesehene Flash eines Gegners kurz ("Ziggs Flash weg."), egal wie
    weit weg (die Einschraenkung auf nahe Gegner aus Auftrag 010 faellt weg), nicht in KAMPF, danach 3 s warten,
    hoechstens einer je 8 s, mehrere in einem Satz."""
    from types import SimpleNamespace as NS
    from lolcoach.kern import Kern
    from lolcoach.zauber import Timer
    k = Kern(stellung="neu")
    gegner = [NS(name="z", champion="Ziggs"), NS(name="s", champion="Sona"), NS(name="c", champion="Caitlyn")]
    p = NS(gegner=lambda: gegner)
    timer: dict = {}
    k._lagebild = NS(zauber=NS(timer=timer))
    ort = {"z": 1200.0, "s": 2500.0, "c": 9000.0}

    def m(t):
        lagen = [NS(s=NS(name=n, tot=False), abstand=d, sichtbar=True, seit=0.0) for n, d in ort.items()]
        return NS(zeit=t, p=p, leben=1.0, b=NS(gegner=lagen))

    timer[("z", "SummonerFlash")] = Timer("z", "Ziggs", "SummonerFlash", 400.0, "Minimap", 100.0)
    assert k._flash_info(m(101), "KAMPF", []) is None                       # nicht in KAMPF
    k._kampf_zuletzt = 101.0
    assert k._flash_info(m(102), "LANE", []) is None                        # 3 s nach dem Kampf
    a = k._flash_info(m(104.5), "LANE", [])
    assert a is not None and a.text == "Ziggs Flash weg.", a
    assert len(a.text.split()) <= 4
    timer[("s", "SummonerFlash")] = Timer("s", "Sona", "SummonerFlash", 410.0, "Chat", 110.0)
    timer[("c", "SummonerFlash")] = Timer("c", "Caitlyn", "SummonerFlash", 420.0, "Chat", 112.0)
    assert k._flash_info(m(110), "LANE", []) is None                        # hoechstens einer je 8 s
    a = k._flash_info(m(113), "LANE", [])
    assert a is not None and a.text == "Sona und Caitlyn Flash weg.", a     # Caitlyn weit weg: trotzdem (Auftrag 016)
    assert k._flash_info(m(125), "LANE", []) is None                        # keiner doppelt
    k2 = Kern(stellung="neu")
    k2._lagebild = NS(zauber=NS(timer={("c", "SummonerFlash"): Timer("c", "Caitlyn", "SummonerFlash", 420.0, "Chat",
                                                                     112.0)}))
    a = k2._flash_info(m(125), "LANE", [])
    assert a is not None and a.text == "Caitlyn Flash weg.", a              # 133448: Lux, Sona, Twitch weit weg


def zwei_klar_unterlegene():
    """Auftrag 003, Teil A 1: auch zwei Gegner sind keine Gefahr, wenn dein Leben >= 70 % ist, du vor JEDEM >= 2 Level
    und >= 1500 Item-Gold liegst und kein dritter Gegner mit p_da >= 0,2 kommt."""
    from types import SimpleNamespace as NS
    from lolcoach.kern import Kern
    k = Kern(stellung="neu")

    def gegner(name, level, gold):
        return NS(champion=name, s=NS(level=level, item_gold=gold, name=name), seit=0.0)

    def m(leben):
        return NS(leben=leben, zeit=900.0, p=NS(ich=NS(level=13, item_gold=7000), team=lambda t: [], mein_team="ORDER"),
                  b=NS(gegner=[gegner("Caitlyn", 8, 3850), gegner("Sona", 6, 3500), gegner("Xin Zhao", 12, 5200)]))

    zwei = {"Caitlyn", "Sona"}
    assert k._klar_unterlegen(m(0.75), zwei, {"Xin Zhao": 0.1}) is not None
    assert k._klar_unterlegen(m(0.66), zwei, {"Xin Zhao": 0.1}) is None          # unter 70 %
    assert k._klar_unterlegen(m(0.75), zwei, {"Xin Zhao": 0.25}) is None         # ein dritter kommt
    assert k._klar_unterlegen(m(0.75), {"Caitlyn", "Xin Zhao"}, {}) is None      # Xin nur 1 Level hinter dir
    assert k._klar_unterlegen(m(0.62), {"Sona"}, {}) is not None                 # einer: ab 60 % wie bisher


def keine_floskeln():
    """Auftrag 004, Teil C 3: keine Satzvorlage mit einer Floskel - "bis sich etwas oeffnet", "Danach rechne ich neu",
    "... ist gerade keine Option." (ohne Grund)."""
    from pathlib import Path
    wurzel = Path(__file__).resolve().parent.parent / "lolcoach"
    verboten = ("bis sich etwas öffnet", "danach rechne ich neu", "ist gerade keine option")
    for datei in [*wurzel.glob("kern/*.py"), *wurzel.glob("kern/modi/*.py"), wurzel / "antworten.py"]:
        if datei.name == "sprache.py":
            continue                         # dort steht die Liste der verbotenen Floskeln (Buch 4, 4)
        text = datei.read_text(encoding="utf-8").lower()
        for f in verboten:
            assert f not in text, (datei.name, f)


def zahlen_wie_spieler():
    """Auftrag 002, S1: was die Stimme bekommt - Gold als Zahlwort auf Hunderter, Kill-Bilanzen ohne Schraegstrich,
    Uhrzeiten mit der Null (Probe mit edge-tts und Whisper: werkzeuge/zahlenprobe.py)."""
    from lolcoach.stimme import sprechbar
    assert sprechbar("3000 Gold Vorsprung") == "dreitausend Gold Vorsprung"
    assert sprechbar("3.100 Gold") == "dreitausendeinhundert Gold"
    assert sprechbar("dann back. 3550 Gold für Hydra") == "dann back. dreitausendfünfhundert Gold für Hydra"
    assert sprechbar("mit 6/0 oben") == "mit sechs null oben"
    assert sprechbar("Kanone kommt 21 07: rein") == "Kanone kommt einundzwanzig null sieben: rein"
    assert sprechbar("Recall/Kauf") == "Recall oder Kauf"
    assert "/" not in sprechbar("Leben 1200/2000")


def konkrete_sprache():
    """Auftrag 008, A2: jeder Turm mit Besitzer und Lage, ohne "Tier", kein "Raus, zum Turm", kein Satz nur
    "Dann <Ort>." - die Regel selbst, jeder Turmname in jedem Fall und die Saetze der konstruierten Lagen."""
    from lolcoach import bewertung
    from lolcoach.kern.sprache import dativ, nominativ, turm, unter, vage_formen
    assert vage_formen("Raus zum Mid-Tier-1-Turm: Aurora und Viego kommen.")         # 101426, 36-mal
    assert vage_formen("Raus, zum Turm!")
    assert vage_formen("Dann Mid-Welle.") and vage_formen("Dann zu deinem Team.")
    assert vage_formen("Drück den inneren Top-Turm: 35 Sekunden, bis einer kommt.")
    assert vage_formen("Turm ist down: weiter auf den Nexus-Turm.")
    assert not vage_formen("Zurück unter deinen Mid-Turm: Aurora und Viego kommen.")
    assert not vage_formen("„Zu welchem Bot Tier 2?“ – Zu ihrem inneren Bot-Turm.")    # Carlos darf "Tier" sagen
    for lane in ("Top", "Mid", "Bot"):
        for stufe in bewertung.TIER:
            for poss in ("dein", "euer", "ihr"):
                for fall in ("nom", "akk", "dat"):
                    assert not vage_formen(turm(poss, lane, stufe, fall) + "."), (poss, lane, stufe, fall)
            ihr = bewertung.TURM_DE[stufe].format(lane=lane)
            assert not vage_formen(f"Drück {ihr}.") and not vage_formen(f"{nominativ(ihr)} jetzt.")
            assert not vage_formen(f"Mit der Gruppe zu {dativ(ihr)}.")
            assert not vage_formen(f"Zurück {unter(bewertung.eigener_turm_name(('ORDER', lane, stufe), 'Top'))}.")
    vage = [(r["id"], r["satz"], vage_formen(r["satz"])) for r in testlage.alle()
            if not r.get("uebersprungen") and r["satz"] and vage_formen(r["satz"])]
    assert not vage, vage


def keine_verbotenen_gruende():
    """Buch 4, 4 (Auftrag 008): kein Satzbaustein mit Floskel oder Tautologie, und "dort nimmt sie sonst niemand" nur mit
    dem, wo dein Team ist - in den Quelltexten und in den Saetzen der konstruierten Lagen."""
    from pathlib import Path
    from lolcoach.kern.sprache import FLOSKELN, TAUTOLOGIEN, verbotene_gruende
    assert verbotene_gruende("Geh zur Top-Welle: dort nimmt sie sonst niemand.")
    assert not verbotene_gruende("Geh zur Top-Welle: dort nimmt sie sonst niemand, dein Team ist unten.")
    assert verbotene_gruende("Drück den Turm, weil es sich lohnt.")
    wurzel = Path(__file__).resolve().parent.parent / "lolcoach"
    for datei in [*wurzel.glob("kern/*.py"), *wurzel.glob("kern/modi/*.py")]:
        if datei.name == "sprache.py":
            continue
        text = datei.read_text(encoding="utf-8").lower()
        for f in FLOSKELN + TAUTOLOGIEN:
            assert f not in text, (datei.name, f)
    schlecht = [(r["id"], r["satz"]) for r in testlage.alle()
                if not r.get("uebersprungen") and r["satz"] and verbotene_gruende(r["satz"])]
    assert not schlecht, schlecht


def warum_mit_vergleich():
    """Buch 4, 4 (Auftrag 008): WARUM in zwei Saetzen - die entscheidende Beobachtung, dann die Alternative mit ihrem
    konkreten Nachteil; entscheidend ist die Groesse, ohne deren Unterschied die Wahl kippt."""
    from types import SimpleNamespace as NS
    from lolcoach.kern import fuehren
    from lolcoach.kern.handlung import Handlung, Ziel
    cfg = konfig()
    rumble = NS(champion="Rumble", ankunft=15.0)
    m = NS(zeit=1200.0, b=NS(gegner=[rumble]))
    drache = Handlung("NEHMEN", Ziel("objective", "den Drachen"), "GRUPPE", 30.0, gewinn=900.0,
                      grund="drei von ihnen sind tot")
    turm = Handlung("DRUECKEN", Ziel("turm", "ihren inneren Top-Turm"), "SEITE", 30.0, gewinn=2000.0,
                    grund="30 Sekunden, bis einer kommt")
    for h, pt in ((drache, 0.05), (turm, 0.45)):
        h.p_tod, h.verlust = pt, 1500.0
        h.ev = sum(fuehren.ev_teile(h, m, cfg).values())
    turm.daten["wer"] = [("Rumble", 0.4)]
    assert fuehren.entscheidend(drache, turm, m, cfg) == "risiko"
    s = fuehren.warum_satz(drache, turm, m, cfg)
    assert s.count(".") == 2 and s.startswith("Zum Drachen: dort ist es sicherer") and "Rumble in 15 Sekunden" in s, s


def ihr_jungle_heisst_ihr_jungle():
    """Auftrag 008 (101426 26:59, Riven im roten Team): "in seinem unteren Jungle" war fuer das rote Team eigen."""
    from lolcoach.kern.merkmale import bereich_aus
    assert bereich_aus(0.69, 0.79, "CHAOS", "Mid") == "jungle_fremd_unten"
    assert bereich_aus(0.69, 0.79, "ORDER", "Mid") == "jungle_eigen_unten"
    assert bereich_aus(0.31, 0.21, "CHAOS", "Mid") == "jungle_eigen_oben"
    assert bereich_aus(0.31, 0.21, "ORDER", "Mid") == "jungle_fremd_oben"


def viego_bleibt_viego():
    """101426 5:25: in Urgots Gestalt nennt die API Viego "Urgot" - nur rawSkinName sagt noch Viego ("Raus ...: Aurora
    und Urgot kommen", Urgot war Carlos' Mitspieler)."""
    from lolcoach import zustand
    roh = {"championName": "Urgot", "rawChampionName": "game_character_displayname_Urgot",
           "rawSkinName": "game_character_skin_displayname_Viego_34", "riotIdGameName": "x", "team": "ORDER",
           "position": "JUNGLE", "scores": {}, "items": [], "summonerSpells": {}}
    s = zustand._spieler(roh)
    assert (s.champion, s.champion_id) == ("Viego", "Viego"), s
    roh.update(championName="Riven", rawChampionName="game_character_displayname_Riven",
               rawSkinName="game_character_skin_displayname_Riven_2")
    assert zustand._spieler(roh).champion == "Riven"


def kontrollauge_nur_mit_platz():
    """Auftrag 008, A3.3 (101426 28:39 "Kauf Tiamat und ein Kontroll-Auge"): fuenf Items, Tiamat fuellt den letzten
    Platz - kein Kontroll-Auge dazu; ohne Kern-Kauf passt es."""
    from types import SimpleNamespace as NS
    from lolcoach.kern.modi.basis import kontrollauge_dazu
    inv = (3156, 6696, 3173, 1033, 1053, 3340)
    assert not kontrollauge_dazu(NS(b=NS(ich=NS(items=inv), gold=1746), kauf=NS(kaufen=["Tiamat"], kosten=1200)))
    assert kontrollauge_dazu(NS(b=NS(ich=NS(items=inv), gold=400), kauf=NS(kaufen=[], kosten=0)))


def vorsicht_statt_raus():
    """Auftrag 008, A1: ungesehene Gefahr ist kein "Raus" - hoechstens ein Vorsicht-Satz je 90 s, nur jenseits des
    Flusses und wenn >= 2 Gegner seit >= 20 s fehlen."""
    from types import SimpleNamespace as NS
    from lolcoach.kern import Kern
    k = Kern(stellung="neu")

    def g(name, rolle, seit, sichtbar=False, ankunft=0.0):
        return NS(champion=name, s=NS(tot=False, rolle=rolle), sichtbar=sichtbar, seit=seit, ankunft=ankunft)

    def m(zeit, bereich="jungle_fremd_oben", seit_twitch=28.0, twitch_an=0.0):
        return NS(zeit=zeit, bereich=bereich, pos=None, p=None, leben=1.0,
                  b=NS(gegner=[g("Viego", "JUNGLE", 32.0), g("Twitch", "BOTTOM", seit_twitch, ankunft=twitch_an),
                               g("Aurora", "MIDDLE", 0.0, True)]))

    assert k._vorsicht(m(900.0, seit_twitch=12.0), "SEITE", []) is None     # nur einer fehlt >= 20 s
    assert k._vorsicht(m(900.0, twitch_an=25.0), "SEITE", []) is None       # Twitch kann noch nicht bei dir sein
    assert k._vorsicht(m(900.0, "jungle_eigen_oben"), "SEITE", []) is None   # nicht jenseits des Flusses
    assert k._vorsicht(m(900.0), "KAMPF", []) is None
    a = k._vorsicht(m(900.0), "SEITE", [])
    assert a is not None and a.text == "Du stehst tief: Viego und Twitch fehlen seit 30 Sekunden.", a
    assert k._vorsicht(m(960.0), "SEITE", []) is None                         # hoechstens einer je 90 s
    assert k._vorsicht(m(995.0), "SEITE", []) is None                         # dieselben Fehlenden: 180 s
    assert k._vorsicht(m(1085.0), "SEITE", []) is not None


def drache_vor_inhibitor():
    """Auftrag 009, 2.3 (Teil 0 aus 008): im Umwandel-Fenster geht ein Objective <= 10 s neben dir vor jeden Turm -
    danach der Turm, wenn das Fenster reicht; ist es weiter weg, entscheidet der EV (beide bleiben Kandidaten)."""
    from lolcoach.kern.handlung import Handlung, Ziel
    from lolcoach.kern.modi import karte
    from types import SimpleNamespace as NS
    cfg = konfig()

    def lage(weg):
        d = Handlung("NEHMEN", Ziel("objective", "den Drachen", (9800.0, 4400.0), weg), "GRUPPE", weg,
                     gefahr_t=weg + 14.0, satz="Zum Drachen: ihr seid vier.")
        d.daten["objective"] = "drache"
        t = Handlung("MIT_GRUPPE", Ziel("turm", "ihren Mid-Inhibitor", (11000.0, 11000.0), 25.0), "GRUPPE", 25.0,
                     gewinn=1000.0, gefahr_t=33.0)
        t.daten.update(turm=("CHAOS", "Mid", "Inhibitor"), umwandeln=True)
        return d, t

    alt = karte.umwandeln
    try:
        karte.umwandeln = lambda m, c: 60.0
        d, t = lage(6.0)
        assert karte.zuerst_filtern(karte.umwandeln_zuerst(NS(mein_tempo=345.0), cfg, [d, t])) == [d]
        assert karte.zuerst_filtern([t]) == [t]            # ist der Drache stumm, bleibt der Turm
        assert d.satz == ("Drache zuerst, der liegt neben euch; danach ihr Mid-Inhibitor, sie sind noch 60 Sekunden "
                          "tot."), d.satz
        d, t = lage(18.0)                       # weiter als 10 s: der EV entscheidet
        assert karte.zuerst_filtern(karte.umwandeln_zuerst(NS(mein_tempo=345.0), cfg, [d, t])) == [d, t]
        karte.umwandeln = lambda m, c: 25.0
        d, t = lage(6.0)                        # das Fenster reicht nicht fuer den Turm danach: nur der Drache
        assert karte.zuerst_filtern(karte.umwandeln_zuerst(NS(mein_tempo=345.0), cfg, [d, t])) == [d]
        assert d.satz == "Zum Drachen: ihr seid vier.", d.satz
    finally:
        karte.umwandeln = alt


def recall_kanal():
    """Auftrag 009, 2.3 (Teil 0 aus 008): im Recall-Kanal warnt der Kern nur, wenn der erste Gegner vor Kanal-Ende
    + 1 s da sein kann (102112 13:22: Kanal noch 0,5 s, Sett in 5,7 s - still; 213624 4:29: noch 3,5 s, Rumble in
    3,9 s - Warnung)."""
    from lolcoach.kern.modi import kanal_reicht
    assert kanal_reicht(0.5, 5.7)
    assert not kanal_reicht(3.5, 3.9)
    assert not kanal_reicht(3.0, 4.0)            # genau Kanal-Ende + 1 s: warnen
    assert kanal_reicht(3.0, None)


def anteil_geglaettet():
    """Auftrag 010, 4: Rivens Anteil am Drachen (102112 25:22) sprang in 0,5 s von 0,14 auf 1,0, als Tryndamere als
    "mit" zaehlte - geglaettet ueber 1,5 s ist er 0,57 statt 1,0; aeltere Werte fallen heraus."""
    from lolcoach.kern.objective import glaetten
    v: list = []
    assert abs(glaetten(v, 1522.30, 0.1387) - 0.1387) < 1e-9
    assert abs(glaetten(v, 1522.85, 0.9982) - 0.5685) < 1e-3
    assert abs(glaetten(v, 1524.20, 0.9982) - 0.9982) < 1e-9          # 1522,30 ist aelter als 1,5 s
    assert glaetten(v, 100.0, 0.2) == 0.2                               # Zeit rueckwaerts: neue Partie


def warnung_nur_mit_neuer_lage():
    """Auftrag 011, 1.2: dieselbe Warnung wird nur wiederholt, wenn p_tod um mehr als eine Stufe steigt (101426
    20:01 -> 20:10: 0,23 -> 0,43 ist eine Stufe - keine Wiederholung)."""
    from lolcoach.kern import gefahr_stufe
    cs = konfig()["schranken"]
    assert gefahr_stufe(0.23, cs) - gefahr_stufe(0.10, cs) == 1
    assert gefahr_stufe(0.43, cs) - gefahr_stufe(0.23, cs) == 1          # 20:10: keine Wiederholung
    assert gefahr_stufe(0.55, cs) - gefahr_stufe(0.23, cs) == 2          # deutlich hoeher: wieder warnen
    assert gefahr_stufe(0.0, cs) == 0 and gefahr_stufe(0.9, cs) == 4


def timer_zur_sprechzeit():
    """Auftrag 012, 3 (192113 4:37): "Drache in 30 Sekunden" gewaehlt bei 4:29,7, gesprochen erst 4:37,1, weil die Stimme
    noch sprach - die Zahl muss stimmen, wenn man sie hoert (Drache 5:00), nicht, als sie gerechnet wurde."""
    import re
    from lolcoach import sprechplan, stimme
    from lolcoach.kern import zeit_jetzt
    from lolcoach.regeln import WICHTIG, Ansage
    zps = sprechplan.ZEICHEN_PRO_SEKUNDE
    sprecher = stimme.Nachgespielt(zps)
    plan = sprechplan.Sprechplan(sprecher)
    uhr = [0.0]
    # ein langer Satz vorher (live: die Claude-Antwort auf die Win Condition, 4:21-4:36)
    lang = Ansage("Geh trotzdem jetzt zurück nach Top zur Welle. " * 4, WICHTIG, "kern:WOHIN", zeit=262.0, gueltig=30.0)
    drache = Ansage("Aus der Basis: Farm Top, Drache in 30 Sekunden.", WICHTIG, "kern:FARMEN", zeit=269.7, gueltig=12.0)
    drache.auffrischen = lambda t: zeit_jetzt(t, uhr[0] - drache.zeit, zps)
    t = 262.0
    while t < 285.0 and drache.gesprochen is None:
        uhr[0] = t
        if abs(t - 262.0) < 1e-6:
            plan.neu([lang])
        if abs(t - 269.7) < 0.05:
            plan.neu([drache])
        sprecher.takt(t)
        plan.takt(t)
        t = round(t + 0.1, 2)
    assert drache.gesprochen is not None and drache.gesprochen > 272.0, drache.gesprochen
    zahl = int(re.search(r"Drache in (\d+) Sekunden", drache.text).group(1))
    gehoert = drache.gesprochen + drache.text.index("Drache in") / zps
    assert abs((300.0 - gehoert) - zahl) <= 1.0, (drache.text, drache.gesprochen)
    # ohne Warten: nur die Sprechzeit bis zur Zahl; "seit" zaehlt hinauf
    assert zeit_jetzt("Drache in 30 Sekunden.", 0.0, zps) == "Drache in 30 Sekunden."
    assert zeit_jetzt("Master Yi fehlt seit 20 Sekunden.", 10.0, zps).startswith("Master Yi fehlt seit 31")


def absicht_aus_langem_satz():
    """Auftrag 012, 2: die Frage steckt in einem langen, wuetenden Satz - Fuellwoerter, Fluch und Beschwerde brechen
    die Erkennung nicht (192113)."""
    from lolcoach.kern.fragen import absicht
    faelle = {
        "Okay, ich bin jetzt in der Base. Wo gehe ich jetzt hin?": "JETZT",
        "Sag mir doch, was ich machen soll, du Fotze.": "JETZT",
        "Meine Welle ist top, Digga, mein Top ist reingepusht bis ins letzte Arschloch.": "JETZT",
        "Was mache ich denn, wenn dieser innere Top-Turm down ist? Als nächstes, als Macro-Play.": "DANACH",
        "Was mache ich, sobald ich zurück bin im Fountain?": "DANACH",
        "Muss ich keine Angst vor Ganks haben, wenn ich den zweiten Turm drücke.": "RISIKO",
        "Warum ist es sicher, jetzt gerade die Botwelle zu farmen?": "RISIKO",
        "Was soll ich mit dem Kontrollauge machen?": "AUGE",
        "Ich habe mich gefragt, ob du in der Lage wäre, auf der Jungle zu coachen.": "COACH",
        "Ich soll zu meinem eigenen inneren Mitturm gehen, da ist doch gar nichts los.": "WARUM",
        "Soll ich nichts anderes kaufen, nur Schutzengel?": "KAUF",
        "Weder keine Antwort und eine weitere Anforderung.": "NOTIZ",
        "Du sagst echt nie irgendwas anderes, außer dass ich meine Top Wave drücken soll.": "NOTIZ",
        # unveraendert
        "Warum bist du dir so sicher, dass der Drache bis dahin nicht schon tot ist?": "GEWISSHEIT",
        "Wie läuft es bei der Bot-Line?": "LAGE",
    }
    for frage, soll in faelle.items():
        assert absicht(frage) == soll, (frage, absicht(frage), soll)


def stratege_pruefung():
    """Auftrag 014, A2: die gefaehrlichen Muster der Probe 013 werden verworfen, harmlose Saetze nicht."""
    from lolcoach.stratege import pruefe
    lage = {"champions": ["Riven", "Master Yi", "Teemo", "Sona", "Kai'Sa"], "jungler": "Master Yi",
            "gegner": [{"name": "Master Yi", "sichtbar": False, "seit": 288.0, "tot": False},
                       {"name": "Teemo", "sichtbar": True, "seit": 0.0, "tot": False}],
            "flash": 0.0, "tp": 56.0, "ult": True,
            "vorn": {"verboten": False, "leben": 90, "gesperrt": [], "ziele": [], "erlaubt": []}}
    assert pruefe("Yi ist seit 288 Sekunden in seiner Base, kein Gank-Risiko gerade.", lage)      # 013 9:42
    assert pruefe("Back, jetzt, 36 Prozent Leben ist R1.", lage)                                  # 013 19:06
    assert pruefe("Teleportier dich zurück nach Top.", lage)                                      # TP in 56 s
    assert pruefe("Aurora ist ohne Flash, geh rein.", lage)                                       # nicht in der Partie
    assert not pruefe("Farm die Welle fertig, danach zu Sona und Kai'Sa in den Fluss.", lage)
    assert not pruefe("Dein TP ist in 56 s wieder da, bis dahin bleib oben.", lage)
    baron = dict(lage, vorn={"verboten": False, "leben": 90, "gesperrt": ["auf den Baron"], "ziele": ["baron"],
                             "erlaubt": []})
    assert pruefe("Geh mit Sona und Kai'Sa Richtung Baron.", baron)                                # 013 20:24
    r1 = dict(lage, vorn={"verboten": True, "leben": 36, "gesperrt": [], "ziele": [], "erlaubt": ["back jetzt"]})
    assert pruefe("Push jetzt den inneren Bot-Turm, Level 14 gegen 8.", r1)
    # Auftrag 016: ein Back-Ruf nennt den Kauf (2); unter R1 ist auch "Welle rein" nach vorn (4.1, vorher erlaubt)
    assert not pruefe("Back jetzt und heilen, danach mit der Gruppe zum Drachen.", r1)
    assert pruefe("Mid-Welle rein, dann back.", r1)
    assert not pruefe("Nicht drücken, zurück unter deinen Turm.", r1)


def stratege_pruefung_015():
    """Auftrag 015, 1: die Sachfehler aus STRATEGE_PROBE_014 (Mitspieler, Gold, Sichtbarkeit, Objective, Laenge)."""
    from lolcoach.stratege import kuerzen, pruefe
    vorn = {"verboten": False, "leben": 90, "gesperrt": [], "ziele": [], "erlaubt": []}
    lage = {"champions": ["Riven", "Sett", "Kai'Sa", "Sona", "Brand", "Master Yi", "Pantheon", "Teemo", "Cassiopeia",
                          "Alistar"], "jungler": "Master Yi", "flash": 0.0, "tp": 0.0, "ult": True, "vorn": vorn,
            "gegner": [{"name": "Master Yi", "sichtbar": False, "seit": 60.0, "tot": False, "seite": "unten"},
                       {"name": "Pantheon", "sichtbar": True, "seit": 0.0, "tot": False, "seite": "mitte"}],
            "mitspieler": [{"name": "Sett", "tot": False, "seite": "basis", "basis": True, "ankunft": 45.0},
                           {"name": "Kai'Sa", "tot": False, "seite": "oben", "basis": False, "ankunft": 40.0},
                           {"name": "Sona", "tot": False, "seite": "unten", "basis": False, "ankunft": 5.0}],
            "gold": 1475, "items": [3077],
            "objectives": [{"schl": "drache", "lebt": False, "spawn_in": 290.0}]}
    # 1. Mitspieler (192113 16:50: "Push den inneren Bot-Turm mit Sett und Kai'Sa", Sett in der Basis)
    assert pruefe("Push den inneren Bot-Turm mit Sett und Kai'Sa, solange Cassiopeia weg ist.", lage)
    assert pruefe("Sett und Kai'Sa stehen unten bei dir, geh mit rein.", lage)
    assert not pruefe("Farm die Welle mit Sona zusammen fertig.", lage)
    assert not pruefe("Geh zu Sett in die Basis, dann mit Sett zum Mid-Turm.", lage)
    # 2. Gold (164326 18:17: "Kontroll-Auge zuerst kaufen, dann Gefraessige Hydra fertig", 1475 Gold)
    assert pruefe("Back jetzt, Kontroll-Auge zuerst kaufen, dann Gefräßige Hydra fertig.", lage)
    # Auftrag 016, 2: ein Back-Ruf nennt auch das Ziel danach
    assert not pruefe("Back jetzt und kauf Caulfields Kriegshammer für die Gefräßige Hydra, dann zurück zur Top-Welle.",
                      lage)
    # 3. Sichtbarkeit (192113 14:37: "Yi und Pantheon seh ich grad nicht", Pantheon war sichtbar)
    assert pruefe("Yi und Pantheon seh ich grad nicht, bleib hinter der Welle.", lage)
    assert pruefe("Master Yi steht unten bei Sona, geh nicht hin.", lage)
    assert not pruefe("Master Yi war vor 60 Sekunden unten, er kann überall sein.", lage)
    # 4. Objective (101426 33:43: "Drache erst, wenn ihr zusammensteht" - der Drache war genommen)
    assert pruefe("Drache erst, wenn ihr komplett zusammensteht, nicht vorher.", lage)
    assert not pruefe("Der Drache kommt erst in 290 Sekunden, bis dahin Welle farmen.", lage)
    # 5. "Nimm die Welle" ist kein Vorwaerts-Rat (164326 16:20)
    r1 = dict(lage, vorn={"verboten": True, "leben": 36, "gesperrt": [], "ziele": [], "erlaubt": []})
    assert not pruefe("Nimm die Welle mit und bleib am Turm.", r1)
    assert pruefe("Nimm die Welle, dann auf den inneren Top-Turm.", r1)
    # Fehlalarme aus dem Lauf mit 100 Momenten (Auftrag 015): nichts davon ist falsch
    fern = dict(lage, mitspieler=[{"name": "Sona", "tot": False, "seite": "unten", "basis": False, "ankunft": 26.0}],
                tp=37.0)
    assert not pruefe("Master Yi ist unklar und Pantheon steht direkt unten.", lage)
    assert not pruefe("Pantheon steht im oberen Jungle und Master Yi ist unsichtbar.", lage)
    assert not pruefe("Warte auf den Drachen um 22:20, geh nicht allein rein.", lage)
    assert not pruefe("Geh nicht Richtung Drache, solange Master Yi unbekannt ist.", lage)
    assert not pruefe("Geh danach mit TP in 37s nach oben.", fern)
    assert not pruefe("Unten steht es zwei gegen zwei mit Sona und Cassiopeia.", fern)
    assert not pruefe("Zurück zum Turm, dann back für den Kriegshammer, danach zur Top-Welle.", r1)   # 016: mit Ziel
    assert pruefe("Cassio, Yi und Pantheon sind unsichtbar, bleib hinten.", lage)          # 192113 24:38
    # 6. Laenge: ueber 30 Woerter auf ganze Saetze
    lang = ("Geh zurück zu deinem Turm, weil drei Gegner kommen und du allein bist. " * 3).strip()
    assert len(kuerzen(lang).split()) <= 30 and kuerzen(lang).endswith(".")


def makro_stratege_wege():
    """Auftrag 015, Teil B: Verwerfen -> einmal neu -> Kern; Abo-Fehler -> still Ausfall; Wellen-Satz weg; der
    Wendepunkt-Satz des Kerns wird ersetzt oder, wenn der Stratege nichts Gueltiges hat, doch gesprochen."""
    from types import SimpleNamespace as NS
    from lolcoach import stratege
    from lolcoach.regeln import WICHTIG, Ansage
    from lolcoach.stratege_live import MakroStratege
    lage = {"champions": ["Riven"], "gegner": [], "mitspieler": [], "jungler": None, "flash": None, "tp": None,
            "ult": None, "gold": 0, "items": [], "objectives": [],
            "vorn": {"verboten": True, "leben": 30, "gesperrt": [], "ziele": [], "erlaubt": ["back jetzt"]}}
    alt = stratege.pruef_lage
    stratege.pruef_lage = lambda kern, p: lage
    try:
        kern = NS(m=NS(tot=False, bereich="lane:Top", b=None), modus=NS(aktuell="LANE"), gefahr=False,
                  kontext=lambda: "", kopfzeile=lambda: None, kandidaten=[], kandidaten_roh=[])
        gesagt = []
        plan = NS(einwerfen=gesagt.append, gesagt=[])
        p = NS(zeit=900.0, ich=NS(tot=False), kills_von=lambda k: [])

        def antwort(*texte):
            reste = list(texte)

            def f(prompt, bei_satz, system, timeout):
                t = reste.pop(0)
                for s in stratege._saetze(t):
                    bei_satz(s)
                return t
            return f
        ms = MakroStratege(kern, plan, frage_fn=antwort("Push den Turm jetzt.", "Push ihren Turm."), synchron=True,
                           aktiv=True)
        assert ms.antworte("Was jetzt?", "JETZT", p) is None                       # zweimal verworfen: der Kern
        assert len(ms.protokoll[-1]["versuche"]) == 2 and ms.protokoll[-1]["quelle"] == "kern"
        ms.frage_fn = antwort("Push den Turm jetzt.", "Back jetzt: heilen, dann zurück zur Top-Welle.")
        assert ms.antworte("Was jetzt?", "JETZT", p) == "Back jetzt: heilen, dann zurück zur Top-Welle."
        assert ms.antworte("Wann kommt der Drache?", "TIMER", p) is None             # Faktfrage: beim Kern

        def kaputt(*a):
            raise RuntimeError("Abo")
        ms.frage_fn = kaputt
        assert ms.antworte("Was jetzt?", "JETZT", p) is None and not ms.bereit()    # Ausfall, still
        ms.ausfall_bis = -1e9
        welle = Ansage("Drück die Top-Welle: 4 gegen 1 Vasallen.", WICHTIG, "kern:WELLE_DRUECKEN", zeit=900.0)
        wp = Ansage("Ihr äußerer Top-Turm ist weg. Farm Top.", WICHTIG, "kern:FARMEN", zeit=900.0)
        wp._kategorie = "WENDEPUNKT"
        ms.frage_fn = antwort("Back jetzt und heilen, danach mit deinem Team zum Mid-Turm.")
        p2 = NS(zeit=1000.0, ich=NS(tot=False), kills_von=lambda k: [])     # 017: > 60 s nach dem Plan der Antwort
        wp.zeit = welle.zeit = 1000.0
        rest = ms.bearbeite([welle, wp], p2)
        assert rest == [] and len(gesagt) == 1 and gesagt[0].schluessel.startswith("stratege:"), (rest, gesagt)
        gesagt.clear()
        ms.frage_fn = antwort("Push den Turm.", "Push den Turm.")
        wp2 = Ansage("Ihr innerer Top-Turm ist weg. Farm Top.", WICHTIG, "kern:FARMEN", zeit=1005.0)
        wp2._kategorie = "WENDEPUNKT"
        assert ms.bearbeite([wp2], NS(zeit=1005.0, ich=NS(tot=False), kills_von=lambda k: [])) == []
        # Fallback: der Kern-Satz - ein anderer Plan 5 s spaeter, erlaubt, weil der Turm fiel (Ereignis)
        assert gesagt == [wp2] and gesagt[0].text.endswith("Farm Top."), [a.text for a in gesagt]
    finally:
        stratege.pruef_lage = alt


def pflichtenheft_016():
    """Auftrag 016 (Carlos' Pflichtenheft aus 133448): Sicherheit (4), Ketten (2), Kaufen (5), Informationspflicht (1)."""
    from types import SimpleNamespace as NS
    from lolcoach import stratege
    from lolcoach.kern import konfig
    from lolcoach.kern.fragen import absicht
    from lolcoach.kern.pflicht import Pflicht
    from lolcoach.stratege import back_ruf, kette, pruefe
    from lolcoach.stratege_live import STRATEGE_ABSICHTEN
    champs = ["Riven", "Poppy", "Teemo", "Lux", "Sona", "Twitch", "Yorick", "Volibear", "Veigar", "Blitzcrank"]
    gegner = [{"name": n, "sichtbar": True, "seit": 0.0, "tot": False, "seite": "oben"} for n in ("Poppy", "Lux", "Sona")]
    r1 = {"champions": champs, "gegner": gegner, "mitspieler": [], "jungler": "Teemo", "flash": 0.0, "tp": None,
          "ult": True, "gold": 3083, "items": [1055, 6696, 1001], "objectives": [], "kill": [],
          "gegner_leben": {"Poppy": 1.0, "Lux": 1.0, "Sona": 1.0},
          "vorn": {"verboten": True, "leben": 5, "gesperrt": [], "ziele": [], "erlaubt": ["back jetzt"]}}
    voll = dict(r1, vorn={"verboten": False, "leben": 100, "gesperrt": [], "ziele": [], "erlaubt": []})
    # 4.1 (12:10, 5 % Leben, Lux und Sona voll daneben)
    satz = ('Die Frage ist nur eine Null, ich nehme sie als "was jetzt?": Schieb kurz die Top-Welle rein und geh back, '
            'du hast 3083 Gold für den Axiombogen.')
    assert any("R1" in g for g in pruefe(satz, r1)), pruefe(satz, r1)
    assert not pruefe("Farm die Top-Welle unter deinem Turm.", r1)                 # holen/farmen: erlaubt
    assert pruefe("Drück die Welle noch in ihren Turm.", r1)
    # 4.2 (9:29: "Poppy ist sichtbar und schwach ... geh sie jetzt an" bei vollem Leben, ohne Kill)
    satz = "Poppy ist sichtbar und schwach, 1180 Leben gegen deine 1550 Combo – geh sie jetzt an, bevor sie reagiert."
    gr = pruefe(satz, voll)
    assert any("Kill-Check" in g for g in gr) and any("schwach" in g for g in gr), gr
    kill = dict(voll, kill=["Poppy"], gegner_leben={"Poppy": 0.3, "Lux": 1.0, "Sona": 1.0})
    assert not pruefe("Poppy ist schwach, geh sie jetzt an.", kill)
    assert pruefe("Poppy ist schwach, geh sie jetzt an.", dict(kill, vorn=r1["vorn"]))    # Kill, aber R1
    assert not pruefe("Greif erst an, wenn ihr W weg ist, sonst farm die Welle.", voll)
    # 2. Ketten: jeder Back-Ruf nennt Kauf und Ziel im selben Satz
    assert pruefe("Geh jetzt back und kauf den Axiombogen, du hast 2486 Gold.", voll)
    assert not pruefe("Back jetzt: Axiombogen, dann zu Yorick nach Mid, weil Teemo unten ist.", voll)
    assert back_ruf("Ihr äußerer Mid-Turm ist weg. Back.") and not back_ruf("Nach dem Back zur Top-Welle.")
    assert kette("Kauf Axiombogen und Kontroll-Auge, dann zum unteren Fluss zu Volibear.")
    # 5. Kaufen: Plaetze, Kontroll-Auge
    inv = dict(voll, gold=924, items=[1055, 6696, 1001, 2055, 3133, 1037])
    assert any("Platz" in g for g in pruefe("Kauf das Langschwert für die Eklipse, dann Top.", inv))
    assert pruefe("Geh zurück nur für ein Kontroll-Auge.", voll)                   # 15:05
    assert pruefe("Kauf ein Kontroll-Auge, dann zum Mid-Turm.", dict(voll, auge="der Spieler will gerade keins"))
    assert not pruefe("Gut, ohne Auge: zurück zum äußeren Mid-Turm zu Yorick.", dict(voll, auge="nein"))
    assert stratege.AUGE_NEIN.search("Nein! Ich glaub's kein verficktes Kontrollauge, du ...!")
    assert not stratege.AUGE_NEIN.search("Ich hab das Auge nicht.")
    # 1.1: eine Flash-Frage beantwortet der Kern (Restzeit je Gegner, antworten.flash_satz)
    for f in ("Wer hat Flash?", "Wie sieht's mit den Flashes aus?", "Hat Poppy Flash?"):
        assert absicht(f) not in STRATEGE_ABSICHTEN, (f, absicht(f))
    # 1.2 und 1.3: Informationspflicht
    cfg = konfig()
    kern = NS(cfg=cfg, gefahr=False, vorn=lambda: {"verboten": False})
    pf = Pflicht()
    j = NS(champion="Teemo", s=NS(tot=False), sichtbar=False, ort="im oberen Fluss", ankunft=6.0)
    ln = NS(champion="Poppy", s=NS(tot=False), sichtbar=False, ort="unten", ankunft=45.0, pos=(12000.0, 1500.0))

    def m(t):
        return NS(zeit=t, pos=(1500.0, 12000.0), b=NS(jungler=j, lane=ln))
    j.sichtbar = True
    pf.takt(kern, m(100.0), "LANE")                                 # zum ersten Mal ab 1:30
    assert pf.faellig(m(100.0), "LANE", cfg) == ("INFO_JUNGLER", "Teemo im oberen Fluss, bei dir in 6 Sekunden.")
    pf.gesagt("INFO_JUNGLER", m(100.0))
    j.sichtbar = False
    pf.takt(kern, m(110.0), "LANE")
    j.sichtbar, j.ort, j.ankunft = True, "in seinem unteren Jungle", 30.0
    pf.takt(kern, m(115.0), "LANE")                                 # nur 15 s ohne Sicht: nichts
    assert pf.faellig(m(115.0), "LANE", cfg) is None
    j.sichtbar = False
    pf.takt(kern, m(116.0), "LANE")
    j.sichtbar = True
    pf.takt(kern, m(140.0), "LANE")                                 # 25 s ohne Sicht: sein Ort, ohne "bei dir"
    assert pf.faellig(m(140.0), "KAMPF", cfg) is None               # in KAMPF wartet er ...
    assert pf.faellig(m(141.0), "LANE", cfg) == ("INFO_JUNGLER", "Teemo in seinem unteren Jungle.")
    pf.gesagt("INFO_JUNGLER", m(141.0))
    j.sichtbar = False
    ln.sichtbar = True                                               # 11:35: "Poppy unten gesehen" - drueckbar
    pf.takt(kern, m(695.0), "LANE")
    assert pf.faellig(m(695.0), "LANE", cfg) == ("INFO_LANE", "Poppy unten gesehen: drück deine Welle.")
    pf2 = Pflicht()
    pf2.takt(NS(cfg=cfg, gefahr=False, vorn=lambda: {"verboten": True}), m(695.0), "LANE")
    assert pf2.offen["INFO_LANE"][1] == "Poppy unten gesehen: farm unter deinem Turm."   # unter R1 nicht nach vorn
    # Kritik 016: Angriffs-Rufe des Kerns ohne Kill-Check und "Back" in der Basis
    from lolcoach.stratege import sicherheit
    assert sicherheit("Rein auf Poppy!", {"vorn": {"verboten": False}, "kill": [], "gegner": [{"name": "Poppy"}]})
    assert not sicherheit("Rein auf Poppy!", {"vorn": {"verboten": False}, "kill": ["Poppy"], "gegner": [{"name": "Poppy"}]})
    assert pruefe("Back jetzt: Axiombogen, dann zu Yorick nach Mid.", dict(voll, ich_basis=True))
    assert any("Gold" in g for g in pruefe("Kauf Kriegshammer und Spitzhacke, dann Top.", dict(voll, gold=1060, items=[])))
    # 2. der Kern-Ersatz: ein Back-Ruf bekommt Kauf und Ziel
    from lolcoach.kern import Kern
    k = Kern(stellung="neu")
    mm = NS(b=NS(), kauf=NS(kaufen=["Axiombogen"]), zeit=700.0)
    txt = k._mit_kette("Top-Welle rein, dann back: 37 Prozent Leben.", mm)
    assert kette(txt) and txt.startswith("Top-Welle rein"), txt
    # 6.4: auch Makro-Infos des Kerns nicht nach vorn unter R1 (Nachspiel 192113 17:51, 101426 34:44)
    assert k._r1_vorn("1800 Gold vorn und jetzt stärker: Drache und ihre Türme als Gruppe erzwingen.",
                      NS(leben=0.3, tot=False))
    assert k._r1_vorn("Vier von ihnen tot, noch 12 Sekunden: auf ihren Nexus-Turm jetzt.", NS(leben=0.2, tot=False))
    assert not k._r1_vorn("Vier von ihnen tot, noch 12 Sekunden: auf ihren Nexus-Turm jetzt.", NS(leben=0.8, tot=False))


def inhalt_017():
    """Auftrag 017, Teil 0 und 1.5 (Nachspiel 133448): Fuellsaetze, Kauf, "schwach", Top-Welle, ganze Antwort, NICHTS,
    ein aktiver Plan."""
    from types import SimpleNamespace as NS
    from lolcoach import stratege
    from lolcoach.stratege import pruefe
    champs = ["Riven", "Poppy", "Teemo", "Lux", "Sona", "Twitch", "Yorick", "Volibear", "Veigar", "Blitzcrank"]
    lane = {"champions": champs, "gegner": [{"name": "Poppy", "sichtbar": True, "seit": 0.0, "tot": False,
                                             "seite": "oben"}], "mitspieler": [], "jungler": "Teemo", "flash": 0.0,
            "tp": None, "ult": True, "gold": 1300, "items": [1055, 1001], "objectives": [], "kill": [],
            "gegner_leben": {"Poppy": 0.24}, "ich_basis": False, "lane_phase": True, "besetzt": {},
            "vorn": {"verboten": False, "leben": 90, "gesperrt": [], "ziele": [], "erlaubt": []}}
    # 0.3 Fuellsaetze (133448 1:32, 1:40; 16:56 "Weiter deine Top-Welle")
    for s in ("Farm deine Welle weiter.", "Danach nimm die Kanone mit, weil sie extra Gold bringt.",
              "Weiter deine Top-Welle.", "Bleib nah an deinem Team und warte auf den nächsten Plan."):
        assert any("Füllsatz" in g for g in pruefe(s, lane)), s
    assert not pruefe("Farm die Welle am Turm, weil Teemo oben ist und sie zu dir läuft.", lane)
    # 0.5 Kauf: "Kauf jetzt" nur in der Basis oder im Back-Ruf (4:17 mitten auf der Lane)
    assert any("Basis" in g for g in pruefe("Kauf jetzt den Brutalisierer für den Axiombogen.", lane))
    assert not pruefe("Kauf jetzt den Brutalisierer für den Axiombogen, dann Top.", dict(lane, ich_basis=True, gold=1500))
    assert any("hast du schon" in g for g in pruefe("Vergiss den Axiombogen, spar für die Eklipse.",
                                                     dict(lane, items=[6696, 1001])))              # 13:12
    # 0.7 "schwach" nur mit Folge (1:35 "Poppy ist mit 24 Prozent schwach")
    assert any("Folge" in g for g in pruefe("Poppy ist mit 24 Prozent schwach.", lane))
    # 0.6 Top-Wellen-Reflex (192113 19:25, ADC und Support farmten sie)
    mid = dict(lane, lane_phase=False, besetzt={"Top": ["Twitch", "Sona"]})
    assert any("stehen schon" in g for g in pruefe("Geh zur Top-Welle: dort kommt ihre nächste Welle.", mid))
    # 0.5 Kaufplan: volles Inventar mit Trank - der Trank geht (192113 28:24 "nichts zu kaufen" bei 4130 Gold)
    from lolcoach import kaufplan
    n = kaufplan._nach_name()
    inv = tuple(n[x] for x in ("Axiombogen", "Nachfüllbarer Trank", "Eklipse", "Ionische Stiefel der Deutlichkeit",
                               "Schutzengel", "Gefräßige Hydra"))
    k = kaufplan.plan("Riven", inv, 4130)
    assert k is not None and k.kaufen and k.verkaufen == "Nachfüllbarer Trank", k
    # 0.1 die ganze Antwort am Stueck, auch wenn sie am Komma gestreamt kommt; NICHTS heisst schweigen
    from lolcoach.stratege_live import MakroStratege, Schiedsrichter, plan_ziel
    kern = NS(m=NS(tot=False, bereich="lane_eigen", b=None, lane_phase=True), modus=NS(aktuell="LANE"), gefahr=False,
              kontext=lambda: "", kopfzeile=lambda: None, kandidaten=[], kandidaten_roh=[])

    def strom(*teile):
        def f(prompt, bei_satz, system, timeout):
            for t in teile:
                bei_satz(t)
            return " ".join(teile)
        return f
    alt = stratege.pruef_lage
    stratege.pruef_lage = lambda k_, p_: lane
    try:
        ms = MakroStratege(kern, NS(einwerfen=lambda a: None, gesagt=[]),
                           frage_fn=strom("Farm die Welle am Turm,", "weil Teemo oben ist.",
                                          "Danach crash sie vor der Kanone."), synchron=True, aktiv=True)
        stuecke = []
        v = ms._versuch("x", lane, stuecke.append)
        assert stuecke == ["Farm die Welle am Turm, weil Teemo oben ist. Danach crash sie vor der Kanone."], stuecke
        ms.frage_fn = strom("NICHTS")
        p = NS(zeit=300.0, ich=NS(tot=False), kills_von=lambda k: [])
        assert ms.antworte("Was jetzt?", "JETZT", p) is None
        assert len(ms.protokoll[-1]["versuche"]) == 1 and ms.protokoll[-1]["versuche"][0]["nichts"]
    finally:
        stratege.pruef_lage = alt
    # 1.5 ein aktiver Plan: 133448 10:17 "Back jetzt" -> 10:35 "Schieb rein, dann back" -> 10:47 "Drück ihren inneren
    # Top-Turm" -> 10:52 "drück deine Welle" -> 10:59 "Back jetzt" - ohne Lageaenderung bleibt es beim ersten Plan
    assert plan_ziel("Back jetzt: Axiombogen, dann Top.") == "back"
    assert plan_ziel("Ihr äußerer Mid-Turm ist weg. Weiter deine Top-Welle.") == "welle:top"
    assert plan_ziel("Drei von ihnen tot: Drück ihren inneren Top-Turm, Level 13 gegen 8.") == "turm"
    sr = Schiedsrichter()
    assert sr.pruefe("Back jetzt: 1966 Gold für den Axiombogen. Danach Top.", 617.0)[0]
    assert not sr.pruefe("Drück ihren inneren Top-Turm, Level 12 gegen 8.", 635.0)[0]
    assert not sr.pruefe("Back jetzt: Axiombogen, dann Top.", 639.0)[0]                 # derselbe Plan, 22 s
    sr.ereignis(641.0, "Poppy unten gesehen wurde")
    ok, text, _ = sr.pruefe("Drück die Top-Welle in ihren Turm, dann back.", 642.0)
    assert ok and text.startswith("Jetzt, wo Poppy unten gesehen wurde:"), text
    assert sr.pruefe("Zurück unter deinen Turm: Lux und Sona kommen.", 649.0, warnung=True)[0]    # Warnung immer


def lagebild_019():
    """Auftrag 019 (Buch 14, A): eindeutige Ortsformen im Lagebild, Kostenzaehler, Zwischenspeicher im Nachspiel."""
    from types import SimpleNamespace as NS
    from lolcoach import welt
    g = NS(s=NS(tot=False, respawn=0, rolle="TOP"), sichtbar=True, ort="oben", seit=0.0, pos=(1, 1))
    assert welt._ort(g, None, 600.0) == "jetzt sichtbar oben"
    g = NS(s=NS(tot=False, respawn=0, rolle="JUNGLE"), sichtbar=False, ort="im oberen Fluss", seit=45.0, pos=(1, 1))
    jt = NS(wahrscheinlich=lambda z: {"oben": 0.3, "unten": 0.7})
    assert welt._ort(g, NS(jungle=jt), 600.0) == \
        "zuletzt gesehen vor 45 s im oberen Fluss, jetzt unbekannt, vermutlich unten (70 %)"
    g = NS(s=NS(tot=False, respawn=0, rolle="MIDDLE"), sichtbar=False, ort="auf der Mid-Lane", seit=120.0, pos=(1, 1))
    assert welt._ort(g, None, 600.0).endswith("jetzt unbekannt, vermutlich auf seiner Lane in der Mitte")
    g = NS(s=NS(tot=True, respawn=14.2, rolle="TOP"), sichtbar=False, ort="", seit=None, pos=None)
    assert welt._ort(g, None, 600.0) == "tot, noch 14 s"
    w = welt.Welt(zeit=605.0, du="Riven", plan="Farm Top.", vorn="erlaubt", kauf="nichts",
                  ereignisse=[(590.0, "Poppy taucht auf (unten)")])
    t = welt.text(w)
    assert t.startswith("ZEIT 10:05\nDU: Riven") and "SEIT DEM LETZTEN AUFRUF (30 s): 9:50 Poppy taucht auf" in t
    # Kostenzaehler (Preise je 1 Mio. Tokens)
    from lolcoach import llm_api
    k = llm_api.Kosten()
    d = k.dazu("claude-haiku-4-5", NS(input_tokens=1_000_000, output_tokens=100_000, cache_read_input_tokens=0,
                                      cache_creation_input_tokens=0))
    assert abs(d - 1.5) < 1e-9 and k.summe() == 1.5
    assert llm_api.modell_id("sonnet") == llm_api.modell_id("stark")
    # Zwischenspeicher: dieselbe Frage einmal ueber Claude, dann aus der Datei
    import tempfile
    from pathlib import Path
    from lolcoach.stratege_live import Zwischenspeicher
    aufrufe = []

    def fake(prompt, bei_satz, system, timeout, bei_fertig=None, modell="x"):
        aufrufe.append(prompt)
        bei_satz("Farm am Turm, weil Teemo oben ist.")
        return "Farm am Turm, weil Teemo oben ist."
    with tempfile.TemporaryDirectory() as tmp:
        zs = Zwischenspeicher(fake, Path(tmp) / "zs.jsonl")
        s1, s2 = [], []
        zs("LAGE", s1.append, "SYS", 5)
        zs2 = Zwischenspeicher(fake, Path(tmp) / "zs.jsonl")
        zs2("LAGE", s2.append, "SYS", 5)
        assert len(aufrufe) == 1 and s1 == s2 and zs2.treffer == 1
    from lolcoach.stratege import pruefe
    assert any("innerer" in g for g in pruefe("Der Entwurf passt nicht, farm die Welle am Turm.", {}))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for test in (konstruierte_lagen, neuer_plan_ist_der_beste, plan_haelt_bei_kurzer_luecke, fenster_gruende_sprechen_dafuer,
                 gold_reicht_fuer_das_genannte_item, info_flash_kurz_und_gebuendelt, zahlen_wie_spieler,
                 zwei_klar_unterlegene, keine_floskeln, konkrete_sprache, viego_bleibt_viego, kontrollauge_nur_mit_platz,
                 ihr_jungle_heisst_ihr_jungle, keine_verbotenen_gruende, warum_mit_vergleich,
                 vorsicht_statt_raus, drache_vor_inhibitor, recall_kanal, anteil_geglaettet,
                 warnung_nur_mit_neuer_lage, timer_zur_sprechzeit, absicht_aus_langem_satz,
                 stratege_pruefung, stratege_pruefung_015, makro_stratege_wege, pflichtenheft_016, inhalt_017, lagebild_019):
        test()
        print(f"{test.__name__} OK")
