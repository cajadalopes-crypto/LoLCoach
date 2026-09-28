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
    for r in ergebnisse:
        grenze = c["max_woerter_gefahr"] if r["gefahr"] and r["plan"] in SICHER else c["max_woerter"]
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
    """Auftrag 002, S3.1: ein bestaetigter Flash eines Gegners kurz ("Ziggs ohne Flash."), nicht in KAMPF, danach 3 s
    warten, hoechstens einer je 20 s, mehrere in einem Satz."""
    from types import SimpleNamespace as NS
    from lolcoach.kern import Kern
    from lolcoach.zauber import Timer
    k = Kern(stellung="neu")
    gegner = [NS(name="z", champion="Ziggs"), NS(name="s", champion="Sona"), NS(name="c", champion="Caitlyn")]
    p = NS(gegner=lambda: gegner)
    timer: dict = {}
    k._lagebild = NS(zauber=NS(timer=timer))

    # Auftrag 010, 2: ungefragt nur fuer nahe, eben gesehene Gegner - Caitlyn steht erst weit weg
    ort = {"z": 1200.0, "s": 2500.0, "c": 9000.0}

    def m(t):
        lagen = [NS(s=NS(name=n, tot=False), abstand=d, sichtbar=True, seit=0.0) for n, d in ort.items()]
        return NS(zeit=t, p=p, leben=1.0, b=NS(gegner=lagen))

    timer[("z", "SummonerFlash")] = Timer("z", "Ziggs", "SummonerFlash", 400.0, "Minimap", 100.0)
    assert k._flash_info(m(101), "KAMPF", []) is None                       # nicht in KAMPF
    k._kampf_zuletzt = 101.0
    assert k._flash_info(m(102), "LANE", []) is None                        # 3 s nach dem Kampf
    a = k._flash_info(m(104.5), "LANE", [])
    assert a is not None and a.text == "Ziggs ohne Flash.", a
    assert len(a.text.split()) <= 4
    timer[("s", "SummonerFlash")] = Timer("s", "Sona", "SummonerFlash", 410.0, "Chat", 110.0)
    timer[("c", "SummonerFlash")] = Timer("c", "Caitlyn", "SummonerFlash", 420.0, "Chat", 112.0)
    assert k._flash_info(m(115), "LANE", []) is None                        # hoechstens einer je 20 s
    a = k._flash_info(m(125), "LANE", [])
    assert a is not None and a.text == "Sona ohne Flash.", a                # Caitlyn ist weit weg: sie wartet
    ort["c"] = 3000.0
    a = k._flash_info(m(150), "LANE", [])
    assert a is not None and a.text == "Caitlyn ohne Flash.", a             # jetzt nah, Ziggs nicht noch einmal
    k2 = Kern(stellung="neu")
    k2._lagebild = NS(zauber=NS(timer={("c", "SummonerFlash"): Timer("c", "Caitlyn", "SummonerFlash", 420.0, "Chat",
                                                                     112.0)}))
    ort["c"] = 9000.0
    assert k2._flash_info(m(125), "LANE", []) is None                       # weit weg: nicht ungefragt


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


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for test in (konstruierte_lagen, neuer_plan_ist_der_beste, plan_haelt_bei_kurzer_luecke, fenster_gruende_sprechen_dafuer,
                 gold_reicht_fuer_das_genannte_item, info_flash_kurz_und_gebuendelt, zahlen_wie_spieler,
                 zwei_klar_unterlegene, keine_floskeln, konkrete_sprache, viego_bleibt_viego, kontrollauge_nur_mit_platz,
                 ihr_jungle_heisst_ihr_jungle, keine_verbotenen_gruende, warum_mit_vergleich,
                 vorsicht_statt_raus, drache_vor_inhibitor, recall_kanal, anteil_geglaettet,
                 warnung_nur_mit_neuer_lage, timer_zur_sprechzeit, absicht_aus_langem_satz):
        test()
        print(f"{test.__name__} OK")
