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
    # Auftrag 023, 2: auch in KAMPF und ohne Abstand - Pflicht-Infos werden nie verschluckt
    a = k._flash_info(m(101), "KAMPF", [])
    assert a is not None and a.text == "Ziggs Flash weg.", a
    assert len(a.text.split()) <= 4
    timer[("s", "SummonerFlash")] = Timer("s", "Sona", "SummonerFlash", 410.0, "Chat", 110.0)
    timer[("c", "SummonerFlash")] = Timer("c", "Caitlyn", "SummonerFlash", 420.0, "Chat", 112.0)
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
    # Auftrag 027, 1.2 (091311 11:39 "aber du sagst nicht, was ich lieber machen soll"): mit der positiven Anweisung
    # (in der Wortgrenze von 14: die kurze Form)
    assert a is not None and a.text == "Du stehst tief: Viego und Twitch fehlen seit 30 Sekunden. Zieh dich zurück.", a
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
    assert pf.faellig(m(100.0), "LANE", cfg) == ("INFO_JUNGLER", "Teemo oberer Fluss, 6 Sekunden.")
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
    # Auftrag 023, 2: auch in KAMPF, kurz
    assert pf.faellig(m(140.0), "KAMPF", cfg) == ("INFO_JUNGLER", "Teemo sein Jungle unten.")
    pf.gesagt("INFO_JUNGLER", m(141.0))
    j.sichtbar = False
    ln.sichtbar = True                                               # 11:35: "Poppy unten gesehen" - drueckbar
    pf.takt(kern, m(695.0), "LANE")
    assert pf.faellig(m(695.0), "LANE", cfg) == ("INFO_LANE", "Poppy unten: Welle drücken.")
    pf2 = Pflicht()
    pf2.takt(NS(cfg=cfg, gefahr=False, vorn=lambda: {"verboten": True}), m(695.0), "LANE")
    assert pf2.offen["INFO_LANE"][1] == "Poppy unten: unterm Turm farmen."   # unter R1 nicht nach vorn
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


def objsymbole_018():
    """Auftrag 018, 1 (183125 17:21 "Ob der Herold noch steht, weiß ich nicht"): das Symbol der Grube lesen und ins
    Lagebild geben. Kuenstliche Karte: Fluss, oben ein lila Symbol, unten eine graue Uhr; dann unten ein Drachen-Symbol."""
    import numpy as np
    from types import SimpleNamespace as NS
    from lolcoach import objsymbole, welt
    karte = np.zeros((570, 570, 3), np.uint8)
    karte[...] = (25, 125, 165)                                   # Fluss (RGB)
    (ox, oy), (ux, uy) = [(int(fx * 570), int(fy * 570)) for fx, fy in objsymbole.GRUBEN.values()]
    karte[oy - 8:oy + 8, ox - 8:ox + 8] = (200, 80, 220)          # lila
    karte[uy - 6:uy + 6, ux - 12:ux + 12] = (225, 225, 225)       # Ziffern der Uhr
    assert objsymbole.lies(karte) == {"oben": "symbol", "unten": "timer"}
    karte[uy - 6:uy + 6, ux - 12:ux + 12] = (25, 125, 165)
    assert objsymbole.lies(karte)["unten"] == "leer"
    karte[uy - 8:uy + 8, ux - 8:ux + 8] = (190, 145, 110)         # Berg-Drache (tan)
    assert objsymbole.lies(karte)["unten"] == "symbol"
    # geglaettet: ein Wechsel gilt erst beim zweiten Bild, BGR wie live
    leser = objsymbole.Grubenleser()
    assert leser.lies_bgr(karte[..., ::-1]) is None and leser.lies_bgr(karte[..., ::-1]) == \
        {"oben": "symbol", "unten": "symbol"}
    herold = NS(schl="herold", lebt=True)
    assert welt._symbol(herold, {"oben": ("symbol", 1000.0)}, 1041.0) == " (Symbol auf der Karte zu sehen)"
    assert welt._symbol(herold, {"oben": ("timer", 1030.0)}, 1041.0) == ""     # im Kampf liest es oft Uhr
    assert welt._symbol(NS(schl="drache", lebt=False), {"unten": ("timer", 1000.0)}, 1041.0) == ""


def respawn_018():
    """Auftrag 018, 2 (183125 18:36): "Verkauf Dorans Klinge, kauf Sonnenköcher" wurde als "kein Platz" verworfen - der
    Verkauf ist kein Kauf, er macht einen Platz frei."""
    from lolcoach import stratege
    it = stratege._items()
    inv = [it[x][3] for x in ("Kontroll-Auge", "Überheblichkeit", "Stiefel", "Dorans Klinge", "Der Sammler",
                              "Letzter Atemzug")]
    g = stratege.pruefe("Verkauf Dorans Klinge, kauf Sonnenköcher, dann zur Top-Welle.", {"gold": 1649, "items": inv})
    assert not any("Platz" in x or "Gold" in x for x in g), g
    g = stratege.pruefe("Kauf Sonnenköcher, dann zur Top-Welle.", {"gold": 1649, "items": inv})
    assert any("kein Platz" in x for x in g), g


def tod_018():
    """Auftrag 018, 6 (183125 38:10-38:36): beim Tod bricht der laufende Satz ab; der Tod-Satz hat hoechstens 12
    Woerter und schickt keinen Toten zurueck; ein wartendes "geh zurueck" faellt weg."""
    from lolcoach import regeln, sprechplan, stimme
    t = regeln.tod_kurz("Fizz und Nautilus kamen zusammen. Bei zwei Gegnern: hinter den Turm oder zu deinem Team, "
                        "bevor sie in Reichweite sind.")
    assert t == "Fizz und Nautilus kamen zusammen.", t
    lang = regeln.tod_kurz("Du bist mit vollem Leben an deinem Turm geblieben, obwohl Garen, Fizz und Nautilus "
                           "dich zu dritt angelaufen haben.")
    assert len(lang.split()) <= 12, lang
    st = stimme.Nachgespielt()
    plan = sprechplan.Sprechplan(st)
    satz = regeln.Ansage("Stoß mit der Bot-Welle direkt in ihren Nexus-Turm, weil Nautilus noch 19 Sekunden "
                         "braucht und du mit Level-Vorteil sofort gewinnen kannst.", regeln.WICHTIG, "stratege:x",
                         zeit=2290.0)
    plan.neu([satz])
    st.takt(2290.0)
    assert plan.takt(2290.0) is satz and st.beschaeftigt
    zurueck = regeln.Ansage("Geh zurück, bevor sie auf dich engagen.", regeln.WICHTIG, "kern:ZURUECK", zeit=2291.0)
    plan.neu([zurueck])
    st.takt(2291.0)
    plan.takt(2291.0, ich_tot=True)
    assert st.abbrueche and st.abbrueche[-1][2] == "tot", st.abbrueche
    assert zurueck not in plan.warte


def turm_und_kampf_018():
    """Auftrag 018, 3 und 5: der sichere Turm mit Stufe; der Kampf daneben mit den Zahlen des Kerns und Kill-Check."""
    from types import SimpleNamespace as NS
    from lolcoach import welt
    from lolcoach.kern.sprache import an, unter
    assert unter("eurem äußeren Mid-Turm") == "unter euren äußeren Mid-Turm"
    assert an("deinem äußeren Top-Turm") == "unter deinem äußeren Top-Turm"
    udyr = NS(champion="Udyr", name="u", level=11, tot=False)
    kog = NS(champion="Kog'Maw", sichtbar=True, pos=(9000.0, 4000.0), leben=0.35, flash=250.0,
             s=NS(tot=False, level=11))
    b = NS(pos=(8000.0, 3000.0), gegner=[kog], mitspieler=[(udyr, (9100.0, 4100.0), 0.4, "am Drachen")], ich=None,
           partie=None)
    m = NS(b=b, mein_tempo=380.0, ult_mitspieler={"u": True}, leben=1.0)
    p = NS(gegner=lambda: [NS(champion="Tryndamere", tot=True)])
    text, weg = welt.kampf_lage(m, p)
    assert text.startswith("am Drachen: ihr Udyr 40 % L11 Ult bereit gegen Kog'Maw 35 % L11 Flash weg noch 250 s"), text
    assert "tot bei ihnen: Tryndamere" in text and "KILL-CHECK: dein Combo reicht für keinen dort" in text, text
    assert 3 < weg < 8, weg


def kampf_rechner_020():
    """Auftrag 020, 2: der Kampfrechner an konstruierten Lagen - Ueberzahl, Level/Items, Leben, Spiegel, Annahmen."""
    from lolcoach.kampf_rechner import Kaempfer as K, rechne
    s = 0.5
    u = rechne([K("Graves", "wir", 11, ich=True), K("Udyr", "wir", 11), K("KogMaw", "sie", 11)], s)
    assert u.urteil == "klar_vorn" and u.staerke > 0.5, u
    assert u.zahlen[0].startswith("ihr ") and "Burst gegen KogMaws" in u.zahlen[0] and "gegen dein" in u.zahlen[1], u
    u = rechne([K("Graves", "wir", 9, ich=True), K("Garen", "sie", 9)], s)
    assert u.urteil == "knapp", u                                       # gleiches Level, keine Items
    u = rechne([K("Graves", "wir", 13, items=(3031, 3036), ich=True), K("Garen", "sie", 9)], s)
    assert u.urteil == "klar_vorn", u
    u = rechne([K("Graves", "wir", 9, leben=0.2, ich=True), K("Garen", "sie", 9)], s)
    assert u.urteil == "klar_hinten" and u.tote[0][1] == "Graves", u
    u = rechne([K("Graves", "wir", 11, ich=True), K("Fizz", "sie", 11), K("Nautilus", "sie", 11)], s)
    assert u.urteil == "klar_hinten" and "Fizz'" in u.zahlen[0], u      # Genitiv
    assert any("Leben von Fizz unbekannt" in a for a in u.annahmen) and any("Ult von Nautilus" in a for a in u.annahmen)
    # Spiegel: dieselbe Lage von der anderen Seite ergibt die umgekehrte Staerke
    a = rechne([K("Riven", "wir", 8), K("Zed", "sie", 10)], s)
    b = rechne([K("Zed", "wir", 10), K("Riven", "sie", 8)], s)
    assert abs(a.staerke + b.staerke) < 1e-6, (a.staerke, b.staerke)
    assert rechne([K("Riven", "wir", 8)], s) is None                   # eine Seite fehlt


def gehirn_021():
    """Auftrag 021: Plan-Objekt (von Claude, nicht gesprochen), Wissensblock >= 4096 Tokens, Kampfansage nur fuer
    freigegebene Rechner-Urteile, neue Anlaesse (Objective-Timer, Fenster, Roam), Kern-Plan-Saetze nur als Ersatz."""
    from types import SimpleNamespace as NS
    from lolcoach import partie_wissen, stratege_live as sl, welt
    pl = sl.Plan("PLAN: Drache | Welle crashen | mit Udyr zum Drachen | Tryndamere tot | gilt bis 4:40 | "
                 "Abbruch wenn Tryndamere lebt", 250.0, "Drache in 30 Sekunden ...")
    assert (pl.ziel, pl.schritt, pl.danach, pl.bis, pl.abbruch) == \
        ("Drache", "Welle crashen", "mit Udyr zum Drachen", 280, "Tryndamere lebt"), vars(pl)
    assert pl.gilt(270) and not pl.gilt(281) and "als Naechstes Welle crashen" in pl.text(260)
    # die PLAN-Zeile wird gemerkt, nicht gesprochen
    ms = sl.MakroStratege.__new__(sl.MakroStratege)
    ms.frage_fn = sl.AufzeichnungsStub(["Drache in 30 Sekunden: Welle crashen, dann zum Drachen. "
                                        "PLAN: Drache | Welle crashen | zum Drachen | Trynd tot | gilt bis 4:40 | -"])
    ms.ausfall_s = 5.0
    ms._p = None
    gesagt = []
    v = ms._versuch("LAGE", {}, gesagt.append, "schnell")
    assert gesagt == ["Drache in 30 Sekunden: Welle crashen, dann zum Drachen."], gesagt
    assert v["plan"].startswith("PLAN: Drache"), v
    # Wissensblock
    t = partie_wissen._block("Graves", ("Graves", "Udyr", "Pantheon", "Urgot", "Zyra"),
                             ("Garen", "Tryndamere", "Fizz", "KogMaw", "Nautilus"))
    assert welt.tokens(t) >= 4096 and "GEGNER - Fizz" in t and "Carlos' eigener" not in t[:50], welt.tokens(t)
    # Kampfansage: klar hinten ja, klar vorn nur als Option (wissen/kampf_eichung.toml)
    assert "Nicht rein" in sl.kampf_regel("...; RECHNER mit dir: klar hinten: ihr 400 Burst ...")
    assert "zwei Optionen" in sl.kampf_regel("...; RECHNER mit dir: klar vorn: ihr 2400 Burst ...")
    assert sl.kampf_regel("ohne Rechner") == ""
    # "schwach" gilt dem eigenen Satzteil (183125 14:27, Runde 2: der Vorsatz nannte Garen, gemeint war Zyra)
    from lolcoach import stratege
    lage = {"gegner": [{"name": "Garen", "leben": 1.0, "sichtbar": True, "tot": False, "seit": 0}]}
    assert not stratege.sicherheit("Jetzt, wo Garen oben gesehen wurde: Zyra fast tot – back jetzt.", lage)
    assert stratege.sicherheit("Garen fast tot: back.", lage)
    # vor dem Sprechen noch einmal gegen die Lage JETZT (125902 9:15: "Crash die Welle" - inzwischen unter R1)
    alt = stratege.pruef_lage
    try:
        stratege.pruef_lage = lambda k, p: {"vorn": {"verboten": True, "leben": 30}}
        ms2 = sl.MakroStratege.__new__(sl.MakroStratege)
        ms2.kern, ms2._p = None, None
        a = NS(text="Crash die Welle jetzt, die Kanonenwelle gibt dir das längste Fenster.")
        assert ms2._noch_sicher(a)() is False
        stratege.pruef_lage = lambda k, p: {"vorn": {"verboten": False}}
        assert ms2._noch_sicher(a)() is True
    finally:
        stratege.pruef_lage = alt
    # neue Anlaesse
    ms = sl.MakroStratege(NS(m=None), NS(gesagt=[]), frage_fn=sl.AufzeichnungsStub(), aktiv=True)
    gegner = [NS(name="f", champion="Fizz", tot=False, respawn=0, kills=0, level=5, rolle="MIDDLE")]
    gl = [NS(s=gegner[0], sichtbar=True, seit=0.0)]
    m = NS(objectives=[NS(schl="drache", lebt=False, spawn_in=88.0)], lane_phase=True, b=NS(gegner=gl))
    p = NS(zeit=212.0, gegner=lambda: gegner)
    assert ms._neue_anlaesse(p, m) == "Objective: Drache in 88 Sekunden"
    assert ms._neue_anlaesse(p, m) is None                                 # einmal je Stufe
    gegner[0].level, gl[0].sichtbar, gl[0].seit = 6, False, 0.0
    p.zeit = 230.0
    m.objectives = []
    assert ms._neue_anlaesse(p, m) is None                                 # eben Level 6, aber noch gesehen
    gl[0].seit, p.zeit = 14.0, 244.0
    assert (ms._neue_anlaesse(p, m) or "").startswith("Roam: Fizz fehlt seit 14 Sekunden auf der Mid-Lane")
    gegner[0].tot, gegner[0].respawn = True, 20.0
    m.objectives = [NS(schl="baron", lebt=True, spawn_in=0.0)]
    p.zeit = 1300.0
    ms._obj_gesagt.add(("baron", "lebt"))
    assert ms._neue_anlaesse(p, m) == "Fenster: Fizz tot (der erste lebt in 20 Sekunden wieder)"


def aufraeumen_022():
    """Auftrag 022: das Aufraeumen fasst Testpartien und die letzten drei Partien nie an, und die kleinen Daten zum
    Nachspielen (Sichtungen, Ereignisse, gruben.json) bleiben immer."""
    from lolcoach import aufraeumen
    schutz = set(aufraeumen.testpartien()) | aufraeumen._letzte()
    assert "2026-09-29_183125" in schutz and "2026-09-27_213624" in schutz
    for pfad, _, _ in aufraeumen.plan():
        teil = next((t for t in pfad.parts if aufraeumen.STAMM.match(t)), "")
        assert aufraeumen.STAMM.match(teil) is None or teil[:17] not in schutz or "_flashclips" in teil, pfad
        assert not aufraeumen.KLEIN.match(pfad.name), pfad


def stimme_023():
    """Auftrag 023: Pflicht-Infos kurz und mit Vorrang (unterbrechen einen langen Plan-Satz), Anlaesse binnen 10 s
    zusammengefasst, Kern-Antworten setzen den einen Plan, Aufnahmen als xz gleich gelesen wie gz."""
    import gzip
    import json
    import tempfile
    from pathlib import Path
    from types import SimpleNamespace as NS
    from lolcoach import aufzeichnung, regeln, sprechplan, stimme, stratege_live as sl
    from lolcoach.kern.pflicht import ort_kurz
    assert ort_kurz("im oberen Fluss") == "oberer Fluss" and ort_kurz("in seinem unteren Jungle") == "sein Jungle unten"
    # Vorrang: ein langer Plan-Satz laeuft, die Info unterbricht ihn (sie wartet hoechstens INFO_WARTEN_S)
    st = stimme.Nachgespielt()
    plan = sprechplan.Sprechplan(st)
    lang = regeln.Ansage("Crash die Welle, dann back fuer Caulfields Kriegshammer und danach mit Udyr zum Drachen, "
                         "weil ihr Prio habt und Tryndamere noch tot ist.", regeln.WICHTIG, "stratege:x", zeit=100.0)
    plan.neu([lang])
    st.takt(100.0)
    plan.takt(100.0)
    info = regeln.Ansage("Teemo oberer Fluss.", regeln.WICHTIG, "kern:INFO_JUNGLER", zeit=100.5)
    plan.neu([info])
    st.takt(100.5)
    assert plan.takt(100.5) is info and st.abbrueche, st.abbrueche
    # zusammengefasst: ein zweiter Anlass 5 s spaeter fragt Claude nicht noch einmal
    fragen = []
    ms = sl.MakroStratege.__new__(sl.MakroStratege)
    ms._letzter_start, ms.schiedsrichter, ms.plan = 100.0, sl.Schiedsrichter(), NS(einwerfen=fragen.append)
    ms._starte(NS(zeit=105.0), "Lane: die Welle kippt", None)
    assert not fragen and ms.schiedsrichter.ereignisse[-1][1] == "die Welle kippt"
    # eine Kern-Antwort setzt den Plan
    ms.plan_obj = sl.Plan("PLAN: Drache | a | b | c | gilt bis 9:00 | -", 400.0, "Geh zum Drachen.")
    ms.antwort_gesprochen("Geh nach Top zur Welle.", 410.0)
    assert ms.schiedsrichter.aktiv[0] == "welle:top" and ms.plan_obj is None
    # Runde 2 (164809 21:16): eine Info mit Plan ("INFO_BASIS: ... Drache erzwingen") geht ueber den Schiedsrichter
    ms.schiedsrichter = sl.Schiedsrichter()
    ms.schiedsrichter.setze("Kauf jetzt, dann zur Mid-Welle zu Sion, nicht zum Drachen.", 1263.0)
    basis = regeln.Ansage("Los: 5200 Gold vorn und jetzt stärker: Drache und ihre Türme als Gruppe erzwingen.",
                          regeln.WICHTIG, "kern:INFO_BASIS", zeit=1276.0)
    flash = regeln.Ansage("Ahri Flash weg.", regeln.WICHTIG, "kern:INFO_FLASH", zeit=1276.0)
    assert ms._richte([basis, flash], NS(zeit=1276.0)) == [flash]
    # eine Warnung kurz nach einem anderen Plan sagt ausdruecklich, dass sie ihn ersetzt (120049 14:08/14:09)
    ms.schiedsrichter.setze("Lauf jetzt zur Top-Welle und crash sie.", 848.0)
    warn = regeln.Ansage("Zurück unter euren äußeren Mid-Turm: drei kommen.", regeln.WICHTIG, "kern:ZURUECK",
                         zeit=849.0, thema="gefahr")
    ms.plan_obj = None
    assert ms._richte([warn], NS(zeit=849.0))[0].text.startswith("Stopp – zurück unter")
    # ein nacktes Nein ist kein Plan-Satz (164809 23:09 "**Nein, nicht Top jetzt**")
    from lolcoach import stratege
    assert stratege.pruefe("Nein, nicht Top jetzt.", {"anlass": True})
    assert not stratege.pruefe("Nein, nicht Top jetzt.", {})            # als Antwort auf eine Frage erlaubt
    # xz liest dasselbe wie gz
    with tempfile.TemporaryDirectory() as d:
        pfad = Path(d) / "2026-01-01_120000.jsonl.gz"
        with gzip.open(pfad, "wt", encoding="utf-8") as f:
            for i in range(50):
                f.write(json.dumps({"w": 1000.0 + i, "d": {"gameData": {"gameTime": float(i)}}}) + "\n")
        vorher = list(aufzeichnung.lies_mit_zeit(pfad))
        assert aufzeichnung.nach_xz(pfad) > 0 and not pfad.exists() and aufzeichnung.gibt(pfad)
        assert list(aufzeichnung.lies_mit_zeit(pfad)) == vorher and aufzeichnung.alle(d) == [pfad]
    # Tempo: das Textende kommt, sobald die stille PLAN-Zeile beginnt - nicht erst nach ihr (API ohne Netz)
    from lolcoach import llm_api
    folge: list[str] = []

    class _Strom:
        text_stream = iter(["Geh zum Drachen. ", "Er kommt in 30 Sekunden.", "\nPLAN", ": Drache | Sicht | ",
                            "Drache | vorne | gilt bis 9:00 | Gegner da"])

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get_final_message(self):
            class _U:
                input_tokens = output_tokens = cache_read_input_tokens = cache_creation_input_tokens = 0
            m = type("M", (), {"model": "x", "usage": _U(), "stop_reason": "end_turn"})()
            return m

    class _Client:
        def with_options(self, **k):
            return self
        messages = type("Msg", (), {"stream": staticmethod(lambda **k: _Strom())})()
    alt_c, alt_k = llm_api._client, llm_api.KOSTEN.dazu
    llm_api._client, llm_api.KOSTEN.dazu = (lambda: _Client()), (lambda *a: 0.0)
    import os
    os.environ["LOLCOACH_API"] = "1"         # nur gegen den Attrappen-Client oben - nie die echte API (Buch 16)
    try:
        llm_api.frage_strom("?", lambda s: folge.append(s), bei_fertig=lambda: folge.append("FERTIG"))
    finally:
        os.environ.pop("LOLCOACH_API", None)
        llm_api._client, llm_api.KOSTEN.dazu = alt_c, alt_k
    assert folge.index("FERTIG") < next(i for i, s in enumerate(folge) if s.startswith("PLAN")), folge
    assert folge.count("FERTIG") == 1 and folge[0] == "Geh zum Drachen.", folge


def kauf_018():
    """Auftrag 018, 4 (183125 34:26-36:47): Schwarzes Beil und Lord Dominiks Grüße teilen die einzigartige Gruppe
    LastWhisper (Spieldaten); Elixier ab Level 9, wenn sonst nichts passt - aber nur mit freiem Platz."""
    from lolcoach import kaufplan, stratege
    it = stratege._items()
    ids = lambda *n: tuple(it[x][3] for x in n)
    inv = ids("Beschichtete Stahlkappen", "Überheblichkeit", "Lord Dominiks Grüße", "Der Sammler",
              "Klinge der Unendlichkeit")
    assert kaufplan.konflikt(it["Schwarzes Beil"][3], inv) == it["Lord Dominiks Grüße"][3]
    assert kaufplan.konflikt(it["Lord Dominiks Grüße"][3], ids("Letzter Atemzug")) is None   # baut daraus
    assert not kaufplan.kaufbar("Schwarzes Beil", inv)[0]
    k = kaufplan.plan("Graves", inv, 4124, 18)
    assert k is not None and "Schwarzes Beil" not in k.kaufen and k.item != "Schwarzes Beil", k
    g = stratege.pruefe("Kauf Schwarzes Beil, dann nach Top.", {"gold": 4124, "items": list(inv)})
    assert any("einzigartig" in x for x in g), g
    # 26:02: "Klinge der Unendlichkeit" las sich als "Dorans Klinge der Unendlichkeit" (Kurzform "Klinge")
    ie = ids("Kontroll-Auge", "Überheblichkeit", "Stiefel", "Lord Dominiks Grüße", "Der Sammler", "Riesenschwert")
    g = stratege.pruefe("Kauf Klinge der Unendlichkeit, dann nach Top.", {"gold": 2412, "items": list(ie)})
    assert not g, g
    # 35:43, 1205 Gold: sechs Items - nichts, auch kein Elixier (es braucht einen Platz); mit freiem Platz und
    # fertigem Build (fuenf fertige Items) das Elixier - mitten im Spiel nie, dann ein Kontroll-Auge (Auftrag 028, 6.2)
    voll = inv + ids("Schildbogen der Unsterblichkeit")
    assert kaufplan.plan("Graves", voll, 1205, 18) is None
    alt = kaufplan._plan
    try:
        kaufplan._plan = lambda *a: None                   # Build fertig, ein Platz frei
        assert kaufplan.plan("Graves", inv, 1205, 18).kaufen == ["Elixier des Zorns"]
        assert kaufplan.plan("Graves", inv, 1205, 8).kaufen == ["Kontroll-Auge"]  # Elixier erst ab Level 9
        assert kaufplan.plan("Graves", inv[:3], 1205, 18).kaufen == ["Kontroll-Auge"]   # mitten im Spiel nie
        assert kaufplan.plan("Graves", inv, 50, 18) is None
        assert kaufplan.plan("Lux", inv, 1205, 18).kaufen == ["Elixier der Zauberei"]
    finally:
        kaufplan._plan = alt


def udyr_024():
    """Auftrag 024 (Udyr-Partie 231200): tot/lebendig aus der API, Lane-Gegner nur mit Beleg weg, keine kaputten
    "Jetzt, wo"-Saetze, kein Kaufrat beim Farmen, Notiz mit Frage, volles Inventar mit Gold, kein Back ohne Grund,
    Quest-TP im Wissensblock, Event-Quellen."""
    from types import SimpleNamespace as NS
    from lolcoach import kaufplan, stratege, stratege_live as sl
    from lolcoach.kern import ereignisquellen as eq, fuehren
    from lolcoach.kern.fragen import frage_in_notiz
    # 2: tot oder lebendig laut API - zur Pruef- und zur Sprechzeit
    lage = {"champions": ["Riven", "Xerath", "Gragas", "Udyr"], "gegner": [
        {"name": "Xerath", "tot": False}, {"name": "Gragas", "tot": True}, {"name": "Udyr", "tot": False}],
        "mitspieler": [], "lane_gegner": {"name": "Udyr", "anwesend": "vermutlich da"}}
    assert stratege.fakten("Jetzt, wo Xerath tot ist: Back jetzt.", lage)
    assert stratege.fakten("Gragas lebt, pass auf.", lage)
    assert not stratege.fakten("Gragas lebt in 5 Sekunden wieder.", lage)
    assert not stratege.fakten("Xerath fast tot, aber Udyr kommt.", lage)
    assert not stratege.fakten("Wenn Xerath tot ist, geh rein.", lage)
    # 3: "Udyr ist weg", obwohl er ungesehen auf seiner Lane steht
    assert stratege.fakten("Udyr ist weg, drück die Welle.", lage)
    lane = lambda seit, pos, ich, ort="oben": NS(lane=NS(s=NS(tot=False, rolle="TOP"), sichtbar=False, seit=seit,
                                                        pos=pos, ort=ort, champion="Udyr"), pos=ich)
    assert eq.anwesenheit(lane(25.0, (1300.0, 13500.0), (1300.0, 7300.0))) == "vermutlich da"   # 5:56: 6700 weg
    assert eq.anwesenheit(lane(25.0, (1300.0, 13500.0), (1300.0, 12700.0))) == "weg"            # du siehst hin
    assert eq.anwesenheit(lane(25.0, (1300.0, 13500.0), (1300.0, 13300.0))) == "vermutlich da"  # Icon verdeckt
    assert eq.anwesenheit(lane(5.0, (7000.0, 7000.0), (1300.0, 7300.0), "im oberen Fluss")) == "weg"
    q = eq.LaneQuelle()
    assert not q.takt(lane(5.0, (1300.0, 13500.0), (1300.0, 7300.0)), 100.0)
    assert not q.takt(lane(25.0, (1300.0, 13500.0), (1300.0, 12700.0)), 120.0)       # 025: erst nach 3 s "weg"
    assert [e.typ for e in q.takt(lane(28.0, (1300.0, 13500.0), (1300.0, 12700.0)), 123.0)] == ["LANE_WEG"]
    # Tod und Respawn als Events
    tq = eq.TodQuelle()
    sp = lambda tot: NS(zeit=1.0, spieler=[NS(name="x", champion="Xerath", tot=tot, respawn=10.0, team="CHAOS")])
    assert not tq.takt(sp(False)) and [e.typ for e in tq.takt(sp(True))] == ["TOD"]
    assert [e.typ for e in tq.takt(sp(False))] == ["RESPAWN"]
    # "Jetzt, wo Xerath tot ist" nur, solange er tot ist
    sr = sl.Schiedsrichter()
    sr.gilt = lambda was: "Xerath" not in was
    sr.setze("Geh zur Top-Welle.", 100.0)
    sr.ereignis(105.0, "Xerath tot ist")
    assert not sr.pruefe("Geh zum Drachen.", 110.0)[0]
    # "Stopp –" nur vor einem Rueckzug, nicht vor einem Kill-Ruf (Nachspiel 231200 13:30 "Stopp – Rein, Gragas fast tot!")
    from lolcoach import regeln
    ms = sl.MakroStratege.__new__(sl.MakroStratege)
    ms.schiedsrichter, ms.plan_obj = sl.Schiedsrichter(), None
    ms.schiedsrichter.setze("Geh zur Top-Welle und crash sie.", 800.0)
    rein = regeln.Ansage("Rein, Gragas fast tot!", regeln.WICHTIG, "kern:REIN", zeit=804.0, thema="gefahr")
    assert ms._richte([rein], NS(zeit=804.0))[0].text == "Rein, Gragas fast tot!"
    # 5.4: kein Ereignis aus einem Satzkopf ("Jetzt, wo Aus der Basis aufgetaucht ist")
    assert sl._als_ereignis("Aus der Basis: Farm Top, Langschwert in 64 Sekunden kaufbar.") is None
    assert sl._als_ereignis("Teemo im oberen Fluss.") == "Teemo im oberen Fluss aufgetaucht ist"
    assert sl._als_ereignis("Xerath TP weg.") == "Xerath TP weg ist"
    # 5.3: FARMEN ohne Kauf-Vorschau
    h = NS(ziel=NS(name="Top-Welle"))
    leiste = [NS(art="kauf", schl="Caulfields Kriegshammer", in_s=lambda j: 43, text="")]
    assert fuehren.farmen_mit_vorschau(h, leiste, 200.0, None, {"fuehren": {"vorschau_horizont_s": 90}}) == ""
    # 5.1: Notiz mit Frage
    assert frage_in_notiz("Notiz, okay, also ich bin jetzt gerade im Shop, was kaufe ich, was mache ich?")
    assert frage_in_notiz("Notiz: Xerath ist gar nicht tot, notier mal bitte, dass du Mist erzählst.") is None
    # 5.2: volles Inventar mit Kontroll-Auge und 4488 Gold -> Auge stellen, Tanz des Todes
    k = kaufplan.plan("Riven", (3026, 6696, 3158, 2055, 6692, 3074, 3340), 4488, 17)
    assert k is not None and k.kaufen == ["Tanz des Todes"] and k.verkaufen == "Kontroll-Auge", k
    # 5.5: "kein Back" nur mit Grund, wenn das Gold fuer ein Item reicht
    assert stratege.pruefe("Ja, Freeze am Turm statt Reset.", {"kauf_bereit": True})
    assert not stratege.pruefe("Ja, Freeze am Turm statt Reset.", {"kauf_bereit": False})
    # 4: Quest-TP im Wissensblock
    from lolcoach import partie_wissen
    assert "QUEST-TP" in partie_wissen._block("Riven", ("Riven",), ("Udyr",), True)
    assert "QUEST-TP" not in partie_wissen._block("Riven", ("Riven",), ("Udyr",), False)


def pakete_025():
    """Auftrag 025 (Buch 15): Uhren, Events, lebendige Pakete - konstruierte Lagen, ohne Aufnahme."""
    from types import SimpleNamespace as NS
    from lolcoach.kern import events as ev, uhren
    from lolcoach.kern.ereignisquellen import Event
    from lolcoach.kern.handlung import Handlung, Ziel
    from lolcoach.kern.pakete import PaketFuehrer
    from lolcoach.kern.plan import Plan
    # Wellen-Uhr (wissen/wellen.toml): Welle alle 30 s ab 0:30, Kanone in Welle 3; ab 14:00 alle 25 s
    assert uhren.naechste_welle(85.0) == (90.0, True) and uhren.naechste_welle(95.0) == (120.0, False)
    assert uhren.naechste_welle(850.0)[0] == 865.0
    assert 25.0 < uhren.brunnen_lane("Top", "ORDER") < 40.0          # Brunnen -> Top-Aussenturm, Karte x Tempo
    # Paket: PLATTEN -> TURM mit Budget aus dem sicheren Fenster, Countdown bei 5 s, Turm faellt -> ERLEDIGT
    def lage(zeit, fenster, gold=500.0):
        return NS(zeit=zeit, tot=False, bereich="lane_eigen", pos=(4300.0, 13000.0), objectives=[], p=None,
                  lane_phase=False, lane_hier=None, mein_tempo=340.0, leben=1.0,
                  b=NS(gold=gold, gegner=[], mitspieler=[], lane=None))
    u = lambda f: NS(fenster=f, wer="Udyr", t_gefahr=f + 5.0, back_spaetestens=None)
    h = Handlung("PLATTEN", Ziel("turm", "ihren Top-Turm", (4318.0, 13875.0), 3.0), "LANE", 12.0, satz="Drück den Turm.")
    kern = NS(fuehrer=NS(plan=Plan(h, 100.0, gesagt=100.0)))
    pf = PaketFuehrer({"countdown_bei_s": 5.0, "countdown_max": 2})
    assert pf.takt(kern, lage(100.0, 12.0), u(12.0), [], "LANE") == []
    assert pf.aktiv.typ == "TURM" and pf.aktiv.frist == 112.0 and pf.aktiv.gesagt
    assert pf.takt(kern, lage(106.5, 5.0), u(5.0), [], "LANE") == [("COUNTDOWN", "Noch 5 Sekunden.")]
    fall = Event("TURM_FAELLT", "Turret_T2_L_03_A", (), 108.0, 1.0, (("wir", True),))
    assert pf.takt(kern, lage(108.0, 4.0), u(4.0), [fall], "LANE") == [("ERLEDIGT", "Ihr Top-Turm fällt.")]
    assert kern.fuehrer.plan is None and pf.aktiv is None and pf.fertig[-1].verlauf[0][1] == "START"
    # Budget abgelaufen: "Raus jetzt" (nur, wenn das Paket mit Budget begann und >= 2 s lief)
    kern.fuehrer.plan = Plan(h, 200.0)
    pf.takt(kern, lage(200.0, 8.0), u(8.0), [], "LANE")
    assert pf.takt(kern, lage(203.0, -1.0), u(-1.0), [], "LANE") == [("BUDGET_AB", "Raus jetzt: Udyr in 4 Sekunden.")]
    # OBJECTIVE: der Gegner nimmt den Drachen -> abgebrochen, der naechste Plan kommt sofort
    ho = Handlung("NEHMEN", Ziel("objective", "den Drachen", (9866.0, 4414.0), 20.0), "OBJECTIVE", 30.0,
                  daten={"objective": "drache"})
    kern.fuehrer.plan = Plan(ho, 300.0)
    pf.takt(kern, lage(300.0, None), NS(fenster=None, wer=None, t_gefahr=None, back_spaetestens=None), [], "OBJECTIVE")
    weg = Event("OBJ_GENOMMEN", "drache", ("drache",), 305.0, 1.0, (("wir", False),))
    assert pf.takt(kern, lage(305.0, None), NS(fenster=None, wer=None, t_gefahr=None, back_spaetestens=None), [weg],
                   "OBJECTIVE") == [("ABGEBROCHEN", "Drache weg: nicht hin.")]
    # Kampf und Tod beenden ein Paket still
    kern.fuehrer.plan = Plan(h, 400.0)
    pf.takt(kern, lage(400.0, 9.0), u(9.0), [], "LANE")
    assert pf.takt(kern, lage(401.0, 9.0), u(9.0), [], "KAMPF") == [] and pf.fertig[-1].ende == "ABGEBROCHEN"
    # Events: Objective bald (60 s vorher) und da
    er = ev.EventErkenner()
    o = lambda lebt, s: NS(schl="drache", lebt=lebt, spawn_in=s, weg=20.0)
    m = lambda zeit, obj: NS(zeit=zeit, objectives=[obj])
    assert not er._objective(m(230.0, o(False, 70.0)), None, None)
    assert [e.typ for e in er._objective(m(241.0, o(False, 59.0)), None, None)] == ["OBJ_BALD"]
    assert [e.typ for e in er._objective(m(300.0, o(True, 0.0)), None, None)] == ["OBJ_DA"]
    # Erahnung: ein Typ unter 60 % Eintritt bleibt still (wissen/events.toml)
    assert ev.still("ERAHNT_GANK") and not ev.still("ERAHNT_RUECKKEHR")


def pakete_026():
    """Auftrag 026: Gefahr-Uhr mit lange Ungesehenen und TP aus der Basis, Abbruch bei einem NEU herankommenden Gegner
    (nicht in Ueberzahl), Sperre fuer abgebrochene Ziele, eine Stimme, Back-Frist-Ansage, Chance "Lane-Gegner weg"."""
    from types import SimpleNamespace as NS
    from lolcoach.kern import uhren
    from lolcoach.kern.ereignisquellen import Event
    from lolcoach.kern.handlung import Handlung, Ziel
    from lolcoach.kern.pakete import PaketFuehrer, eine_stimme_blockt
    from lolcoach.kern.plan import Plan
    # Gefahr-Uhr: 60 s ungesehen zaehlt mit hoechstens 5 s (vorher gar nicht - 192113 20:59 Pantheon)
    g = lambda **k: NS(**{"s": NS(tot=False, zauber=(), name="u", respawn=0.0, team="CHAOS"), "ankunft": 30.0,
                          "seit": 60.0, "champion": "Pantheon", "ort": "oben", "sichtbar": False, **k})
    m = lambda *gg: NS(zeit=1250.0, leben=1.0, leben_trend=0.0, mein_tempo=340.0, tp_in=None, kanone_in=None,
                       meine_lane="Top", p=None, objectives=[],
                       b=NS(flash=None, gegner=list(gg), pos=(5000.0, 5000.0), sicherer_ort=lambda: ("Turm", 3.0),
                            kauf=None))
    u = uhren.rechnen(m(g()), {})
    assert u.t_gefahr == 5.0 and u.wer == "Pantheon", u
    tp = g(seit=10.0, ort="in seiner Basis", s=NS(tot=False, zauber=("SummonerTeleport",), name="t", respawn=0.0,
                                                  team="CHAOS"), champion="Xerath")
    assert uhren.rechnen(m(tp), {}).t_gefahr == 6.0                     # TP bereit aus der Basis
    # Abbruch: ein Gegner kommt NEU auf 1000 heran und ihr seid nicht mehr - "Raus jetzt", Ziel 15 s gesperrt
    h = Handlung("PLATTEN", Ziel("turm", "ihren Top-Turm", (4318.0, 13875.0), 3.0), "LANE", 12.0, satz="Drück den Turm.")
    kern = NS(fuehrer=NS(plan=Plan(h, 100.0, gesagt=100.0)), pflicht=NS(lane_gesagt=-1e9))
    feind = NS(sichtbar=True, s=NS(tot=False), abstand=900.0, champion="Udyr", pos=(4300.0, 13200.0))
    lage = lambda zeit, gegner, mit=(): NS(zeit=zeit, tot=False, bereich="lane_eigen", pos=(4300.0, 13000.0),
                                          objectives=[], p=None, lane_phase=False, lane_hier="Top", mein_tempo=340.0,
                                          leben=1.0, b=NS(gold=500.0, gegner=gegner, mitspieler=list(mit), lane=None))
    uo = NS(fenster=None, wer=None, t_gefahr=None, back_spaetestens=None, kanone_in=None, gold_bis=None)
    pf = PaketFuehrer({"countdown_bei_s": 5.0, "countdown_max": 2})
    pf.takt(kern, lage(100.0, []), uo, [], "LANE")
    assert pf.takt(kern, lage(102.0, [feind]), uo, [], "LANE") == [("BUDGET_AB", "Raus jetzt: Udyr ist da.")]
    assert pf.gesperrt[("PLATTEN", "ihren Top-Turm")] == 117.0 and kern.fuehrer.plan is None
    kern.fuehrer.plan = Plan(h, 200.0)
    pf.takt(kern, lage(200.0, []), uo, [], "LANE")
    zwei = [(NS(tot=False, champion="Ekko"), (4300.0, 13100.0), 1.0, "oben"),
            (NS(tot=False, champion="Lux"), (4200.0, 13100.0), 1.0, "oben")]
    assert pf.takt(kern, lage(202.0, [feind], zwei), uo, [], "LANE") == []      # ihr seid drei gegen einen
    # eine Stimme: waehrend "zur Gruppe" kein "X kämpft: nicht hin"
    k2 = NS(fuehrer=NS(plan=NS(art="ZUR_GRUPPE")))
    assert eine_stimme_blockt(k2, lage(300.0, []), ["Ekko"])
    # Back-Frist: 10 s vorher ansagen, einmal
    pf2 = PaketFuehrer({})
    ub = NS(back_spaetestens=410.0, kanone_in=50.0, gold_bis=("Eklipse", 0), fenster=None, wer=None, t_gefahr=None)
    ml = NS(zeit=400.0, lane_phase=True, tot=False)
    assert pf2._vor_back(ml, ub) == "In 10 Sekunden Welle rein, dann Back: pünktlich zur Kanone um 7:30."
    assert pf2._vor_back(ml, ub) is None
    # Chance: Lane-Gegner weg -> Platten (vor 14:00)
    mw = NS(zeit=500.0, lane_phase=True, tot=False, b=NS(lane=NS(champion="Udyr")))
    ev = Event("LANE_WEG", "im oberen Fluss", ("Udyr",), 500.0, 0.7)
    assert PaketFuehrer._lane_weg(kern, mw, [ev]) == "Udyr weg: Welle rein, dann Platten."


def herz_027():
    """Auftrag 027 (091311, "extrem passiv, gibt keine Kommandos"): der Herzschlag - Stillstand, Auffrischung, Kauf
    im Tod und im Brunnen; "warum nicht" nie allein; kein Hin und Her; die Kette im Tod wird nicht gekuerzt."""
    from types import SimpleNamespace as NS
    from lolcoach.kern.herzschlag import (Herzschlag, negativ_allein, nachsatz, plan_ziel_von, positiv, vorlage,
                                          ziele_vertraeglich)
    from lolcoach.kern.modi import kuerze, liste
    from lolcoach import stratege
    kern = NS(fuehrer=NS(plan=None), danach_text="Karthus", uhren=None, cfg={}, _back_rufe=[], _stand=None,
              pakete=NS(fertig=[]))
    def lage(z, pos=(1000.0, 1000.0), bereich="lane_eigen", tot=False, respawn=0.0, kaufen=()):
        return NS(zeit=z, b=NS(kauf=NS(kaufen=list(kaufen), verkaufen=None)), tot=tot, respawn=respawn, pos=pos,
                  bereich=bereich, meine_lane="Top", lane_hier="Top", p=None, tp_in=None)
    # vorlage: nie ein nackter Name ("Karthus. Nicht zu Karthus: ...", 026) - dann die Welle der Lane
    assert vorlage(kern, lage(10.0)) == "Geh zu deiner Top-Welle und farm sie."
    assert nachsatz(vorlage(kern, lage(10.0)), "Yorick kämpft: nicht hin, 10 Sekunden weg.") == \
        "Geh zu deiner Top-Welle und farm sie. Nicht zu Yorick: 10 Sekunden weg."
    # 091311 11:39 und 23:42: nur ein Nein ist keine Anweisung
    assert negativ_allein("Du stehst tief: Amumu und Braum fehlen seit 32 Sekunden.")
    assert negativ_allein("Cassiopeia kämpft: nicht hin, 14 Sekunden weg.")
    assert not negativ_allein("Du stehst tief. Zurück zu deinem äußeren Top-Turm.")
    assert positiv(NS(schluessel="kern:PAKET_WARUM_NICHT", text="Crash die Welle. Nicht zu Yorick: 10 s weg."))
    # Stillstand (15:41): nach 3,5 s am selben Fleck die Anweisung - mit Vorrang (STILL)
    h = Herzschlag()
    farm = [NS(gesprochen=99.0, zeit=99.0, schluessel="kern:FARMEN", text="Farm Top.")]
    assert h.takt(kern, lage(100.0), "LANE", farm) is None
    s = h.takt(kern, lage(103.6), "LANE", farm)
    assert s and h.still and not negativ_allein(s), s
    # Auffrischung: 25 s ohne positive Anweisung - eine neue
    assert h.takt(kern, lage(120.0, pos=(3000.0, 3000.0)), "LANE", farm) is None
    assert h.takt(kern, lage(129.0, pos=(5000.0, 3000.0)), "LANE", farm) is not None
    # im Tod 12 s vor dem Respawn: Kauf (im Laden geht das schon) - nicht nur "Du lebst in 11 Sekunden" (19:10)
    h = Herzschlag()
    s = h.takt(kern, lage(200.0, tot=True, respawn=11.0, kaufen=["Langschwert"]), "TOT", [])
    assert s and s.startswith("Du lebst in 11 Sekunden. Kauf Langschwert") and h.kauf, s
    # im Brunnen: sofort die Kauf-Kette (19:10: erst "Top", dann nichts vom Kauf)
    h = Herzschlag()
    s = h.takt(kern, lage(300.0, bereich="basis_eigen", kaufen=["Tiamat", "Langschwert"]), "BASIS", [])
    assert s == "Kauf Tiamat und Langschwert." and h.kauf, s
    assert liste(["Langschwert", "Langschwert"]) == "zweimal Langschwert"
    # die Kette im Tod wird gekuerzt, nicht weggeschnitten (091311 15:17: nur "Du lebst in 3 Sekunden.")
    lang = "Du lebst in 4 Sekunden: verkauf Dorans Klinge, dann kauf Langschwert für die Eklipse, dann warte an " \
           "deinem äußeren Top-Turm auf dein Team."
    assert kuerze(lang, 14) == lang
    # kein Hin und Her: Welle und Top-Welle sind dasselbe Ziel, Welle und Bot-Turm nicht (23:21)
    assert ziele_vertraeglich("welle", "welle:top") and not ziele_vertraeglich("welle:top", "turm")
    assert plan_ziel_von(NS(schluessel="kern:PAKET_KAUF", text="Kauf Tiamat, dann Top.")) is None
    # 091311 21:00: "dein Team startet den Baron" - die Minimap zeigt alle am Drachen
    am_drachen = {"team_am": {"bekannt": 4, "drache": 4, "baron": 0}}
    assert stratege.fakten("Jetzt, wo dein Team den Baron startet: back sofort.", am_drachen)
    assert not stratege.fakten("Dein Team ist am Drachen: geh hin.", am_drachen)
    assert not stratege.fakten("Wenn dein Team den Baron startet, geh mit.", am_drachen)
    # an der Baron-Grube, das Team laut Minimap am Drachen: kein "Bleib am Baron bei deinem Team" (091311 20:46)
    am_baron = lage(1246.0, bereich="grube:baron")
    k_team = NS(**{**vars(kern), "_team_am_letzt": (1240.0, {"bekannt": 4, "drache": 4, "baron": 0})})
    assert "Baron" not in (vorlage(k_team, am_baron) or ""), vorlage(k_team, am_baron)
    k_team._team_am_letzt = (1240.0, {"bekannt": 4, "drache": 0, "baron": 3})
    assert "Bleib am Baron" in vorlage(k_team, am_baron)
    # Spielende (1.5): Inhibitor offen, drei lange tot - aber nie unter R1 (231200 24:44 im API-Nachspiel)
    from lolcoach.kern import herzschlag
    alt = herzschlag.ende_satz
    herzschlag.ende_satz = lambda m: "Jetzt beenden: alle auf den Nexus, 3 von ihnen sind tot."
    try:
        for leben, soll in ((0.2, False), (0.9, True)):
            h = Herzschlag()
            m_ = lage(1500.0)
            m_.leben = leben
            s = h.takt(NS(**{**vars(kern), "cfg": {"schranken": {"vor_leben_min": 0.4}}}), m_, "SEITE", farm)
            assert (s is not None and s.startswith("Jetzt beenden")) == soll, (leben, s)
    finally:
        herzschlag.ende_satz = alt


def ein_plan_028():
    """Auftrag 028, 1 und 2: ein aktiver Plan fuer alle Quellen, Wechsel nur mit Grund, keine Fuellsaetze, keine
    Entschuldigungen, keine internen Etiketten nach "Jetzt, wo"."""
    from types import SimpleNamespace as NS
    from lolcoach import stratege
    from lolcoach.kern.herzschlag import auffrischen, countdown, wechsel_grund
    from lolcoach.regeln import WICHTIG, Ansage
    from lolcoach.sprechplan import Sprechplan
    from lolcoach.stratege_live import Schiedsrichter
    # 1.2: keine Entschuldigung - "Stimmt. Neu:"; ein reines "Tut mir leid." entfaellt
    assert stratege.ohne_entschuldigung("Mein Fehler. Kauf Tiamat, dann Top.") == "Stimmt. Neu: Kauf Tiamat, dann Top."
    assert stratege.ohne_entschuldigung("Tut mir leid.") == ""
    assert stratege.sicherheit("Jetzt, wo Plan: Farm deine Top-Welle.", {})           # 1.4: internes Etikett
    # 1.4: "Plan: ..." und "Wendepunkt: Aus der Basis: ..." sind kein Ereignis; eine Frage heisst "Neu:"
    sr = Schiedsrichter()
    sr.ereignis(100.0, "Plan: Farm deine Top-Welle")
    sr.ereignis(101.0, "Wendepunkt: Aus der Basis: Farm Top")
    sr.ereignis(102.0, "Plan: Welle gerettet - kein Turm verloren")                 # das Etikett faellt, der Rest ist eins
    assert sr.ereignisse == [(102.0, "Welle gerettet - kein Turm verloren")], sr.ereignisse
    sr.setze("Farm deine Top-Welle.", 100.0)
    sr.ereignis(105.0, "du gefragt hast")
    ok, text, _ = sr.pruefe("Geh zum Drachen: ihr seid vier.", 106.0)
    assert ok and text.startswith("Neu: Geh zum Drachen"), text
    # 1.1: ein Wechsel braucht einen Grund - Gefahr, Event vorn, Frage, "Plan geändert"
    assert wechsel_grund(NS(schluessel="kern:PAKET_CHANCE", text="Udyr weg: Welle rein, dann Platten.", thema=""))
    assert wechsel_grund(NS(schluessel="kern:DRUECKEN", text="Sie haben den Drachen genommen. Drück ihren Top-Turm.", thema=""))
    assert not wechsel_grund(NS(schluessel="kern:PAKET_HERZ", text="Geh zu deiner Top-Welle und farm sie.", thema=""))
    # das Sprech-Tor: 3 s nach "Back jetzt" kein "Geh zur Top-Welle" (231200 5:29); ein Kern-Satz mit eigenem
    # Grund nach 5 s wird hoerbar gewechselt
    sp = Sprechplan(NS())
    back = Ansage("Back jetzt: 14 Prozent Leben.", WICHTIG, "kern:PAKET_HERZ", zeit=100.0, gesprochen=100.0)
    sp.gesagt.append(back)
    herz = Ansage("Geh zu deiner Top-Welle und farm sie.", WICHTIG, "kern:PAKET_HERZ", zeit=103.0)
    assert sp._ein_plan(herz, 103.0) is None
    drueck = Ansage("Drück ihren inneren Mid-Turm: Level 14 gegen 10.", WICHTIG, "kern:DRUECKEN", zeit=107.0)
    assert sp._ein_plan(drueck, 107.0) is None               # "Back jetzt" gilt: nur Gefahr oder Frage (2302)
    sp.gesagt.append(Ansage("Farm deine Top-Welle.", WICHTIG, "kern:PAKET_HERZ", zeit=121.0, gesprochen=121.0))
    assert sp._ein_plan(drueck, 127.0) == "Plan geändert: Drück ihren inneren Mid-Turm: Level 14 gegen 10."
    assert sp._ein_plan(herz, 125.0) == herz.text                                  # nach 20 s ein neuer Plan
    # 1.3: kein Doppel binnen 10 s aus beliebiger Quelle (231200 22:00: "Raus jetzt, nach Top." alle 4 s)
    sp.gesagt.append(Ansage("Raus jetzt, nach Top.", WICHTIG, "kern:PAKET_STILL", zeit=130.0, gesprochen=130.0))
    assert sp._doppel("Raus jetzt, nach Top.", 134.0) and not sp._doppel("Raus jetzt, nach Top.", 141.0)
    assert not sp._doppel("Los: Raus jetzt, nach Top.", 135.0)          # er steht - das ist neu
    assert not sp._doppel("Raus jetzt, nach Top: Udyr kommt.", 135.0)   # ein Grund dazu ist neu
    sp.gesagt.append(Ansage("Los: Raus jetzt, nach Top.", WICHTIG, "kern:PAKET_STILL", zeit=135.0, gesprochen=135.0))
    assert sp._doppel("Los: Raus jetzt, nach Top.", 140.0)
    # 2: eine Anweisung kommt nur mit Neuem wieder - nie "Bleib dabei" (auch nicht mit Kanone)
    kern = NS(fuehrer=NS(plan=None), danach_text="", uhren=NS(kanone_in=18.0), cfg={}, _back_rufe=[], _stand=None,
              pakete=NS(fertig=[]))
    m = NS(zeit=200.0, b=NS(kauf=NS(kaufen=[], verkaufen=None)), tot=False, respawn=0.0, pos=(1000.0, 1000.0),
           bereich="lane_eigen", meine_lane="Top", lane_hier="Top", p=None, tp_in=None)
    eben = [Ansage("Geh zu deiner Top-Welle und farm sie.", WICHTIG, "kern:PAKET_HERZ", zeit=190.0, gesprochen=190.0)]
    assert auffrischen(kern, m, eben) is None                                          # nichts Neues: still
    assert auffrischen(kern, m, eben, still=True).startswith("Los:")                  # er steht: das ist neu
    kern.danach_text = "back für die Eklipse"
    assert auffrischen(kern, m, eben) == "Geh zu deiner Top-Welle und farm sie, danach back für die Eklipse."
    # 6.5: die Kanone nur als Countdown <= 10 s vor der Handlung (Back)
    assert countdown(kern, m) is None
    kern.uhren.kanone_in = 6.0
    kern.fuehrer.plan = NS(art="WELLE_REIN_UND_BACK", handlung=NS(schritte=["Welle rein", "back"]))
    assert countdown(kern, m) == "Kanone in 6 Sekunden, dann Back."
    # 3: der Kill-Check beim SPRECHEN, fuer jede Quelle (231200 26:25: beim Fragen hielt der Kill, beim Sprechen nicht)
    from lolcoach.kern import Kern
    k = NS(unsicher_jetzt=lambda t: ["Angriff ohne Kill-Check (töten)"] if "töte" in t else [])
    sp = Sprechplan(NS(beschaeftigt=False, sage=lambda *a, **kw: None))
    sp.kern = k
    sp.neu([Ansage("Rein: töte Xerath!", WICHTIG, "kern:PAKET_HERZ", zeit=300.0)])
    assert sp.takt(300.0) is None and sp.verworfen_sicher, sp.verworfen_sicher
    k.m = NS()
    k.teamnamen = lambda t, *a: t
    k.sichere_antwort = lambda t: Kern.sichere_antwort(k, t)
    import lolcoach.kern.herzschlag as hz
    alt, hz.vorlage = hz.vorlage, lambda kern, m: "Geh zu deiner Top-Welle und farm sie."
    try:
        assert k.sichere_antwort("Xerath töten sofort, dann Top crashen.") == \
            "Kein sicherer Kill mehr. Geh zu deiner Top-Welle und farm sie."
        assert k.sichere_antwort("Ja, TP. Dann töte Xerath.") == "Kein sicherer Kill mehr. Ja, TP."
        assert k.sichere_antwort("Ja, TP auf die Top-Welle.") == "Ja, TP auf die Top-Welle."
    finally:
        hz.vorlage = alt


def ornn_028():
    """Auftrag 028, 6 (Ornn-Partie 134020): Widerspruch sperrt alle Stimmen, doppelte Namen mit Team, Kauf mit Inhalt
    (Stiefel nach Gegnern, Spielakte-Build, kein Elixier mitten im Spiel, Ornn ohne Back)."""
    from lolcoach import kaufplan, stratege
    from lolcoach.kern.einspruch import Einsprueche
    from lolcoach.kern.sprache import teamnamen
    from lolcoach.sonderregeln import kauft_ohne_back
    # 6.3: "ich lass sie friezen" sperrt crash bis Tod/Back; "kein Elixier" fuer den Rest der Partie
    e = Einsprueche()
    e.hoere("Nee, ich lass den mal lieber pushen, damit ich reinfreezen kann.", 215.0)
    e.hoere("Ich kaufe kein Alexi mit Game.", 995.0)
    assert e.trifft("Crash die Welle, dann back.", 230.0) and not e.trifft("Nicht crashen: lass sie kommen.", 230.0)
    assert e.trifft("Kauf Elixier des Metalls, dann zum Baron.", 1340.0)
    e.lage(260.0, basis=True)
    assert [s.was for s in e.sperren] == ["kein Elixier"]
    lage = {"sperren": [{"was": s.was, "muster": s.muster} for s in e.sperren]}
    assert any("gesperrt" in g for g in stratege.pruefe("Kauf Elixier des Metalls, dann zum Baron.", lage))
    # 6.1: ein doppelter Name nie allein
    assert teamnamen("Sejuani Flussmitte.", {"Sejuani"}, "kern:INFO_JUNGLER") == "Ihre Sejuani Flussmitte."
    assert teamnamen("Geh zu deinem Team, nicht zu Sejuani.", {"Sejuani"}) == "Geh zu deinem Team, nicht zu eurer Sejuani."
    assert teamnamen("Sejuani kämpft mit Miss Fortune.", {"Sejuani"}, gegner={"Miss Fortune"}) == \
        "Eure Sejuani kämpft mit Miss Fortune."
    # 6.2: Ornn - Build bis Jak'Sho, Stahlkappen gegen Tryndamere und Miss Fortune nach dem ersten Item, kein Elixier
    it = stratege._items()
    ids = lambda *n: tuple(it[x][3] for x in n)
    g = ("Tryndamere", "MissFortune", "Sejuani", "Leona", "Brand")
    assert kaufplan.stiefel("Ornn", g)[0] == it["Beschichtete Stahlkappen"][3]
    assert it["Jak'Sho, der Proteaner"][3] in kaufplan.kern("Ornn")
    k = kaufplan.plan("Ornn", ids("Dorans Schild", "Bamis Glutstein", "Stoffrüstung", "Stiefel"), 1052, 7, g)
    assert k.kaufen == ["Kettenweste", "Rubinkristall"], k                        # 7:55: die ganze Kette
    k = kaufplan.plan("Ornn", ids("Dorans Schild", "Sonnenfeuer-Ägide", "Dornenpanzer", "Stiefel"), 1001, 11, g)
    assert k.kaufen == ["Beschichtete Stahlkappen"], k                            # nicht Elixier des Metalls
    assert kauft_ohne_back("Ornn") and not kauft_ohne_back("Riven")
    assert any("kauft ohne Back" in x for x in stratege.pruefe("Back jetzt: Dornenpanzer kaufen, dann Top.",
                                                                {"kauf_ohne_back": True}))
    assert any("hast du schon" in x for x in stratege.pruefe(
        "Back jetzt: Dorans Schild holen, dann Top zurück.", {"gold": 600, "items": list(ids("Dorans Schild"))}))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for test in (konstruierte_lagen, neuer_plan_ist_der_beste, plan_haelt_bei_kurzer_luecke, fenster_gruende_sprechen_dafuer,
                 gold_reicht_fuer_das_genannte_item, info_flash_kurz_und_gebuendelt, zahlen_wie_spieler,
                 zwei_klar_unterlegene, keine_floskeln, konkrete_sprache, viego_bleibt_viego, kontrollauge_nur_mit_platz,
                 ihr_jungle_heisst_ihr_jungle, keine_verbotenen_gruende, warum_mit_vergleich,
                 vorsicht_statt_raus, drache_vor_inhibitor, recall_kanal, anteil_geglaettet,
                 warnung_nur_mit_neuer_lage, timer_zur_sprechzeit, absicht_aus_langem_satz,
                 stratege_pruefung, stratege_pruefung_015, makro_stratege_wege, pflichtenheft_016, inhalt_017, lagebild_019,
                 objsymbole_018, respawn_018, kauf_018, tod_018, turm_und_kampf_018, kampf_rechner_020, gehirn_021,
                 aufraeumen_022, stimme_023, udyr_024, pakete_025, pakete_026, herz_027, ein_plan_028, ornn_028):
        test()
        print(f"{test.__name__} OK")
