"""Kleine Bausteine: Item-Namen, Wellen, Mitspieler-Leiste, Teleport-Timer, Kuerzen, Orte.

    python tests/test_bausteine.py
"""
import re
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import aufzeichnung, gehirn, hud, itemnamen, minimap, welle, zauber, zustand  # noqa: E402

HIER = Path(__file__).parent


def item_namen():
    text, k = itemnamen.absichern("Kauf dir jetzt Stereks Pegel und danach Tanz der Todes.")
    assert text == "Kauf dir jetzt Steraks Pegel und danach Tanz des Todes.", text
    text, k = itemnamen.absichern("Bau Schwarzes Beil, dann Gefraessige Hydra.")
    assert text == "Bau Schwarzes Beil, dann Gefräßige Hydra.", text      # "Bau" bleibt stehen
    for unberuehrt in ("Geh zum Drachen mit Lee Sin, Riven ist stark.", "Warwick ist in seinem oberen Jungle!"):
        assert itemnamen.absichern(unberuehrt) == (unberuehrt, []), unberuehrt


def wellen():
    # Lane-Geometrie: Ecke oben ist die Mitte der Top-Lane, Basen an den Enden
    assert welle._projektion(0.14, 0.16)[0] == "Top" and abs(welle._projektion(0.14, 0.16)[1] - 0.5) < 0.05
    assert welle._projektion(0.5, 0.5)[0] == "Mid"
    assert welle._projektion(0.93, 0.6)[0] == "Bot" and welle._projektion(0.93, 0.6)[1] > 0.7
    assert welle._projektion(0.35, 0.55) is None                     # Jungle
    # blaue Welle tief bei Rot, keine rote: "tief bei seinem Turm" fuer Blau, "tief bei deinem" fuer Rot
    punkte = [("blau", 0.93, y) for y in (0.30, 0.32, 0.34, 0.36)]
    z = welle.zustaende(punkte)["Bot"]
    assert z.blau == 4 and z.rot == 0 and z.schiebt == "blau"
    assert "tief bei seinem Turm" in z.worte("ORDER") and "tief bei deinem Turm" in z.worte("CHAOS"), z.worte("ORDER")
    assert welle.zustaende([])["Mid"].worte("ORDER") == "keine Welle zu sehen"


def mitspieler_leiste():
    """Echtes Bild (Partie 2, 26.09.2026): Lee Sin 93 %, Diana 95 % mit Ult bereit, Varus 32 %, Alistar 75 %."""
    bild = cv2.imread(str(HIER / "hud_ecke.jpg"))
    x0, y0, x1, y1 = hud.bereich(3840, 2160)
    ox, oy = 3840 - 907, 2160 - 907
    m = hud.lies(bild[y0 - oy:y1 - oy, x0 - ox:x1 - ox])
    leben = [x.leben for x in m]
    assert all(abs(a - b) <= 0.04 for a, b in zip(leben, [0.93, 0.95, 0.32, 0.75])), leben
    assert [x.ult_bereit for x in m] == [False, True, False, False], m
    assert all(type(x.ult_bereit) is bool for x in m)      # numpy-bool hat den Coach einmal abstuerzen lassen


def teleport_timer():
    p = zustand.partie(list(aufzeichnung.lies(HIER / "botspiel_riven_2.jsonl.gz"))[900])
    shen = p.gegenueber()                                   # Top, Level 8
    assert zauber.cooldown("SummonerTeleport", shen, 300) == 300
    assert 280 < zauber.cooldown("SummonerTeleport", shen, 700) < 300
    assert zauber.cooldown("SummonerTeleport", shen, 900) == zauber.cooldown("SummonerTeleport", shen, 700) - 30
    assert zauber.cooldown("SummonerFlash") == 300


def kuerzen_und_orte():
    assert gehirn.kuerzen("Eins. Zwei! Drei? Vier.", 2) == "Eins. Zwei!"
    assert minimap.woher("im oberen Fluss") == "aus dem oberen Fluss"
    assert minimap.woher("oben") == "von oben"
    assert minimap.woher("auf der Mid-Lane") == "über die Mid-Lane"
    assert minimap.ort(0.5, 0.5, "ORDER") == "in der Flussmitte"
    assert minimap.ort(0.33, 0.30, "ORDER") == "im oberen Fluss"


def profil_ueber_partien():
    import json
    import shutil
    import tempfile
    from lolcoach import profil
    with tempfile.TemporaryDirectory() as tmp:
        ordner = Path(tmp)
        for stamm in ("2026-09-26_100000", "2026-09-26_110000"):
            shutil.copy(HIER / "botspiel_riven_1.jsonl.gz", ordner / f"{stamm}.jsonl.gz")
        (ordner / "2026-09-26_100000_review.json").write_text(
            json.dumps({"naechste_partie": "Frueher kaufen.", "lektionen": [{"titel": "Gold gehortet", "wichtigkeit": 5}]}),
            encoding="utf-8")
        alle = profil.partien(ordner)
        assert [k.stamm for k in alle] == ["2026-09-26_110000", "2026-09-26_100000"]
        k = alle[0]
        assert k.champion == "Riven" and k.bots and not k.zaehlt and k.cs_min > 0, k
        # die laufende Partie (110000) sieht nur fruehere; ein Review einer alten Partie keine spaeteren
        assert profil.fokus(ordner, vor="2026-09-26_110000") == "Frueher kaufen."
        assert profil.partien(ordner, vor="2026-09-26_100000") == []
        assert "Gold gehortet" in profil.text(ordner) and "nur Bot-Partien" in profil.text(ordner)
        assert (ordner / profil.CACHE).exists()


def sprechbar():
    from lolcoach.stimme import sprechbar as s
    assert s("Jungler/Laner seit 30-40 s weg, ab 2500+ Gold") == \
        "Jungler oder Laner seit 30 bis 40 Sekunden weg, ab mehr als 2500 Gold"
    assert s("Gank zwischen 2:45 und 3:30, Drache um 5:00") == "Gank zwischen 2 45 und 3 30, Drache um Minute 5"
    for gleich in ("Mid-Lane", "Level 6", "Tri-Bush", "80 %", "KDA 27/6/4", "5 sind weg"):
        assert s(gleich) == gleich, s(gleich)


def recalls_im_verlauf():
    """Recall-Beginn = Beginn des Stillstands vor dem Teleport, zurueck = am eigenen Aussenturm
    (vorher: 8-12 s 'weg', weil ein veraltetes Icon und der Lane-Anfang in der Basis zaehlten)."""
    from lolcoach import verlauf
    v = verlauf.baue(HIER / "botspiel_riven_2.jsonl.gz")
    r = [m for m in v.momente if m.art == "recall"]
    assert [verlauf.uhr(m.von) for m in r] == ["6:53", "10:01", "12:50"], [m.von for m in r]
    assert "Wieder in der Lane um 7:23 (30 s weg)" in r[0].fakten and "Gekauft: Caulfields Kriegshammer" in r[0].fakten
    # Kaempfe nach Zeit UND Ort: der Kampf unten ohne dich ist einer, und er sagt, wie weit weg du warst
    k = next(m for m in v.momente if m.art == "kampf" and verlauf.uhr(m.von) == "7:44")
    assert k.titel == "Kampf 2:0 (ohne dich)" and any("0.99 Kartenbreiten entfernt" in f for f in k.fakten), k


def akte_teile():
    roh = ("**AKTE:**\n- Trynd frueh stark\nBRIEFING:\nSpiel die Lane aggressiv.\n"
           "LANEPLAN:\n- **Spielweise:** Aggressiv traden\nLevel 1–3: Level 2 traden\nErster Back: 1300 Gold\n"
           "Unsinn: weg\nULTS:\nTryndamere: 5 s unsterblich\nFOKUS:\nHeute zurueck bei zwei Fehlenden.")
    t = gehirn.akte_teile(roh)
    assert t["AKTE"].startswith("- Trynd") and t["BRIEFING"] == "Spiel die Lane aggressiv."
    assert t["ULTS"].startswith("Tryndamere:") and t["FOKUS"].startswith("Heute")
    assert gehirn.laneplan_zeilen(t["LANEPLAN"]) == ["Spielweise: Aggressiv traden", "Level 1-3: Level 2 traden",
                                                     "Erster Back: 1300 Gold"]
    assert gehirn.akte_teile("nur Text ohne Marker")["AKTE"] == "nur Text ohne Marker"   # alte Antworten


def chat_zeitstempel():
    # Partie 4: "04:48 Riven (Riven): Tryndamere hat Blitz benutzt", gelesen um 4:51
    assert zauber.chat_zeit("04:48 Riven (Riven): Tryndamere hat Blitz benutzt", 291.0) == 288.0
    assert zauber.chat_zeit("02: 13 Camille (Camille): Rumble hat Blitz benutzt", 248.0) is None   # Partie 6: alt
    assert zauber.chat_zeit("Ille): Rumble- Blitz", 339.0) is None                                 # ohne Stempel


def aufnahme_fortsetzen():
    """Coach-Fenster mitten in der Partie getoetet (Datei nicht geschlossen), Coach neu gestartet: dieselbe
    Partie wird erkannt und weitergeschrieben - und hinterher ist ALLES lesbar."""
    import shutil
    import tempfile
    schnappschuesse = [d for d in aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")][:60]
    with tempfile.TemporaryDirectory() as tmp:
        ordner = Path(tmp)
        s = aufzeichnung.Schreiber(ordner)
        for d in schnappschuesse[:30]:
            s.schreibe(d)
        s._f.flush()
        abbruch = ordner / "abbruch.gz"               # Stand der Platte beim Toeten: ohne gzip-Ende
        shutil.copy(s.pfad, abbruch)
        s._f.close()
        abbruch.replace(s.pfad)
        assert aufzeichnung.fortsetzbar(schnappschuesse[30], ordner) == s.pfad
        andere = dict(schnappschuesse[30], allPlayers=schnappschuesse[30]["allPlayers"][:-1])
        assert aufzeichnung.fortsetzbar(andere, ordner) is None            # andere Spieler: neue Partie
        weiter = aufzeichnung.Schreiber(ordner, fortsetzen=s.pfad)
        for d in schnappschuesse[30:]:
            weiter.schreibe(d)
        weiter.schliesse()
        assert weiter.pfad == s.pfad and len(list(aufzeichnung.lies(s.pfad))) == 60


def bildschirm_momente():
    """Gesicherte Spielbildschirme finden ihren Moment: 3 s vor dem Tod 19:55 (Testpartie 2) -> im Review."""
    import shutil
    import tempfile
    from lolcoach import review, verlauf
    with tempfile.TemporaryDirectory() as tmp:
        ordner = Path(tmp)
        aufnahme = ordner / "2026-09-26_100000.jsonl.gz"
        shutil.copy(HIER / "botspiel_riven_2.jsonl.gz", aufnahme)
        shutil.copytree(HIER / "botspiel_riven_2_bilder", ordner / "2026-09-26_100000_bilder")
        v = verlauf.baue(aufnahme)
        tod = next(m.bis for m in v.momente if m.art == "tod" and m.bis > 1100)
        wand = v.wand0 + tod - 3
        (ordner / "2026-09-26_100000_bilder" / f"schirm_{int(wand * 1000)}.jpg").write_bytes(b"\xff\xd8bild")
        assert verlauf.bildschirm_bei(aufnahme, v, tod - 2.5) is not None
        assert verlauf.bildschirm_bei(aufnahme, v, tod - 30) is None          # nichts in der Naehe
        bilder = review.moment_bilder(aufnahme, v)
        assert len(bilder) == 1 and "vor deinem Tod" in bilder[0][0] and bilder[0][1] == b"\xff\xd8bild", bilder


def eigene_tasten():
    """Q W E R D F bereit? Echter HUD-Streifen aus Partie 6 (4K, ab Fenster 1075/1944): Q, W, D (Zuenden)
    bereit - E, R und F (Flash, 1:30) nicht. Gelber Tasten-Buchstabe = bereit."""
    import numpy as np
    streifen = cv2.imread(str(HIER / "hud_unten.png"))
    fenster = np.zeros((2160, 3840, 3), np.uint8)
    fenster[1944:1944 + streifen.shape[0], 1075:1075 + streifen.shape[1]] = streifen
    wahr = {"Q": True, "W": True, "E": False, "R": False, "D": True, "F": False}
    assert hud.eigene(fenster) == wahr, hud.eigene(fenster)
    assert hud.eigene(cv2.resize(fenster, (1920, 1080), interpolation=cv2.INTER_AREA)) == wahr   # skaliert mit


def chat_pings():
    """Partie 7: Carlos pingt verbrauchte Zauber als "Wukong — Blitz" - das zaehlt, genau wie "hat benutzt"."""
    p = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")) if q.spieler)
    g = p.gegenueber().champion                    # Shen
    assert [z for _, z, _ in zauber.aus_chat(f"02:38 Riven (Riven): {g} — Blitz", p)] == ["SummonerFlash"]
    assert [z for _, z, _ in zauber.aus_chat(f"02:13 Camille (Camille): {g} hat Blitz benutzt", p)] == ["SummonerFlash"]
    assert [z for _, z, _ in zauber.aus_chat(f"02:13 Lee Sin (Lee Sin): {g.lower()} flash", p)] == ["SummonerFlash"]


def matchup_zeilen():
    from types import SimpleNamespace as S
    vi = gehirn.matchup("Graves", S(champion="Vi", champion_id="Vi"))
    assert vi.startswith("Vi ("), vi[:40]                      # nicht die Viego-Zeile
    assert gehirn.matchup("Riven", S(champion="Urgot", champion_id="Urgot")).startswith("Urgot (")
    assert gehirn.matchup("Riven", S(champion="K'Sante", champion_id="KSante")).startswith("K'Sante (")


def zauber_im_briefing():
    p = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")) if q.spieler)
    quelle = gehirn.akte_quelle(p, fokus="Frueher kaufen.")
    namen = [zauber.NAME_DE[z] for z in p.ich.zauber]
    assert all(n in quelle.split("Mein Team")[0] for n in namen), quelle[:300]
    assert "FOKUS DES SPIELERS" in quelle and "Frueher kaufen." in quelle


def bewertung_und_plan():
    """Lagebewertung, Komponist, Entscheider: die Rechnungen, auf die sich die Ansagen stuetzen."""
    from types import SimpleNamespace as S
    from lolcoach import antworten, bewertung, entscheider, komponist
    p = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")) if q.zeit > 400)
    g, j = p.gegenueber(), p.jungler(zustand.gegenteam(p.mein_team))
    adc = next(s for s in p.gegner() if s.rolle == "BOTTOM")
    # Kanonenwellen 2026: 1:30, 3:00, 4:30, 6:00 ... + ~27 s Laufweg nach oben
    assert entscheider.naechste_kanone(300, "TOP") == 387, entscheider.naechste_kanone(300, "TOP")
    # Lauftempo aus Data Dragon + Stiefel
    assert 300 < bewertung.tempo(g) < 500
    b = bewertung.Bewertung(zeit=720, ich=p.ich, leben=0.35, pos=(1500, 11000), zum_turm=9, mein_tempo=345)

    def gl(s, **kw):
        a = dict(s=s, sichtbar=False, seit=5.0, ort="im oberen Fluss", abstand=2000.0, ankunft=3.0, tempo=350.0,
                 flash=None, ult=None, level_vorsprung=0, gold_vorsprung=0)
        a.update(kw)
        return bewertung.GegnerLage(**a)
    b.jungler = gl(j)
    b.lane = gl(g, sichtbar=True, seit=0.0, ort="oben", abstand=800.0, ankunft=2.0)
    fern = gl(adc, seit=40.0, ort="unten", abstand=11000.0, ankunft=0.0)     # Worst Case, aber unplausibel
    b.gegner = [b.jungler, b.lane, fern]
    assert [x.s.name for x in b.bedrohung(8)] == [b.lane.s.name, j.name], "ADC in Minute 12 bot ist keine Gefahr"
    satz = komponist.jungler_gesehen(b, b.jungler, "gefahr", platten=True)
    assert "zurück zu deinem Turm" in satz and "35 Prozent Leben" in satz and "3 Sekunden" in satz, satz
    # Sofort-Antwort aus dem Entscheider, Kauf-Frage bleibt bei Claude
    plan = entscheider.Option("druck", "Spiel auf Shen: du bist 2 Level vorn.", 100, 2)
    lb = S(entscheider=S(aktuell=plan))
    assert antworten.sofort("Was soll ich jetzt machen?", p, lb) == plan.satz
    assert antworten.sofort("Was soll ich kaufen?", p, lb) is None
    assert komponist.sek(105) == "1 Minute 45" and komponist.sek(1) == "1 Sekunde"
    # Todeszeit (Wiki Death): L9 @20:00 = 29,2 s, L18 @55:00 = 78,75 s
    assert round(bewertung.todeszeit(9, 1200), 1) == 29.2 and round(bewertung.todeszeit(18, 3300), 2) == 78.75
    b.tod_kostet, b.objective = 45.0, ("baron", 30.0)
    assert komponist.todespreis(b) == "ein Tod kostet dich 45 Sekunden, und Baron Nashor kommt in 30 Sekunden"
    # Kaufplan aus dem Lexikon-Build: Riven Kern Stiefel -> Axiombogen -> Endloser Hunger -> Tanz des Todes
    from lolcoach import kaufplan
    assert kaufplan.plan("Riven", (1055,), 1400).satz() == "reicht für den Brutalisierer"
    assert kaufplan.plan("Riven", (1055, 3158), 2800).satz() == "reicht für Axiombogen"
    assert kaufplan.plan("Riven", (1055, 3158), 1000).satz() == "noch 50 bis Caulfields Kriegshammer"


def denkkette():
    """Carlos' Beispiel (Live 26.09.): du Level 6, er 5, Ult und Zuenden bereit, er ohne Flash, Jungler weit weg
    -> zusammenhaengend "geh rein, das ist ein Kill" mit Gold und Kauf danach. Am Turm: warten. Jungler nah: kein
    All-in. Dazu die Stimme ("Vi" ist nicht "sechs") und die falsch gelesene Ult ("Heimerd / r" um 1:47)."""
    from dataclasses import replace
    from lolcoach import bewertung, denker, stimme
    p = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")) if q.zeit > 400)
    g, j = p.gegenueber(), p.jungler(zustand.gegenteam(p.mein_team))
    ich = replace(p.ich, level=6, items=(1055, 2003), item_gold=1100)
    g = replace(g, level=5, item_gold=900)

    def gl(s, **kw):
        a = dict(s=s, sichtbar=True, seit=0.0, ort="oben", abstand=700.0, ankunft=2.0, tempo=345.0, flash=None,
                 ult=None, level_vorsprung=s.level - ich.level, gold_vorsprung=s.item_gold - ich.item_gold)
        a.update(kw)
        return bewertung.GegnerLage(**a)
    b = bewertung.Bewertung(zeit=330, ich=ich, leben=0.95, gold=1150, pos=(1500, 12500), ult=True,
                            zweiter=("SummonerDot", 0.0), partie=p)
    b.lane = gl(g, flash=200.0)
    b.jungler = gl(j, sichtbar=False, seit=5.0, ort="in seinem unteren Jungle", abstand=9000.0, ankunft=25.0)
    b.gegner = [b.lane, b.jungler]
    u = denker.urteil(b)
    assert u.art == "kill", (u.art, u.wert, [(x.art, x.wert) for x in u.faktoren])
    satz = denker.fenster_satz(b, u, anlass=f"Du bist jetzt Level 6, {g.champion} erst 5", ohne={"ult"})
    # Handlung zuerst, Gruende in einem Satz (Live 21:21: ~300 Zeichen je Ansage, der Coach redete 74 % der Zeit)
    assert satz.startswith(f"Du bist jetzt Level 6, {g.champion} erst 5 - geh rein, das ist ein Kill: "), satz
    assert "kein Flash" in satz and len(satz) <= 190, (len(satz), satz)
    assert satz.count("Level 6") == 1, satz                      # der Anlass sagt das Level, nicht zweimal
    # dieselbe Lage als Frage per Sprechtaste: sofort aus dem Urteil, nicht ~3 s ueber Claude
    from types import SimpleNamespace
    from lolcoach import antworten
    alt, bewertung.bewerte = bewertung.bewerte, lambda *a, **k: b
    try:
        lb = SimpleNamespace(aktiv=True)
        assert antworten.sofort("Kann ich ihn killen?", p, lb).startswith("Geh rein, das ist ein Kill: ")
        assert antworten.sofort("Soll ich all in gehen?", p, lb).startswith("Geh rein")
        assert antworten.sofort("Warum kann ich ihn killen?", p, lb) is None          # Begruendung: Claude
        assert antworten.sofort("Wo soll ich reingehen? Auf welcher Lane?", p, lb) is None   # Ort: Claude
        andere = next(s for s in p.gegner() if s.name not in (g.name, j.name))
        assert antworten.sofort(f"Kann ich {andere.champion} killen?", p, lb) is None   # nicht der Lane-Gegner
    finally:
        bewertung.bewerte = alt
    # am Turm: warten (kein Dive - Live 11:00/11:08), mit dem Jungler nah: kein All-in
    b.lane = gl(g, flash=200.0, pos=bewertung.TUERME[(zustand.gegenteam(p.mein_team), "Top", "aussen")])
    assert denker.urteil(b).art == "turm", denker.urteil(b).art
    b.leben_abs = 1200      # Turm in Zahlen (Wiki Turret): 5:30 aussen 248 pro Schuss, aufwaermend -> 3 Schuesse
    satz = denker.fenster_satz(b, denker.urteil(b))
    assert "Noch nicht rein" in satz and "Sein Turm trifft mit etwa 240, du hältst 3 Schüsse aus." in satz, satz
    # Zuenden allein toetet: sein Leben (Balken x Max-Leben) unter 90 % des Zuendschadens (Level 6: 175)
    from lolcoach import rechnung
    assert rechnung.zuenden_schaden(6) == 175 and rechnung.zuenden_schaden(18) == 475
    b.lane = gl(g, flash=200.0, leben=0.1)
    # Riven: der volle Combo (combo.py) samt Zuenden rechnet - bei anderen Champions Zuenden allein
    faktoren = denker.urteil(b).faktoren
    assert any(x.art in ("combo_kill", "zuenden_kill") for x in faktoren), faktoren
    satz = denker.fenster_satz(b, denker.urteil(b))
    assert re.search(r"Shen hat nur (noch etwa )?1[01]0 Leben", satz), satz     # 110 mit der Leben-Rune (27.09.)
    assert "Prozent Leben" not in satz, satz
    b.jungler = gl(j, sichtbar=False, seit=3.0, ort="im oberen Fluss", abstand=1500.0, ankunft=4.0)
    b.gegner = [b.lane, b.jungler]
    u = denker.urteil(b)
    assert u.art == "halten" and "Kein All-in, solange" in denker.fenster_satz(b, u) and "aber" not in denker.fenster_satz(b, u), denker.fenster_satz(b, u)
    # Stimme: "Vi" als Name, erster Teilsatz frueh
    assert stimme.sprechbar("Vi ist oben, Kai'Sa unten.") == "Wai ist oben, Kaisa unten."
    assert stimme.teilsaetze("Du bist Level 6: geh rein. Danach back.") == ["Du bist Level 6:", "geh rein.", "Danach back."]
    # Ult erst ab Level 6; ein einzelnes "r" nur mit sicherem Namen
    p.zeit = 110
    assert not zauber.aus_chat("01:45 Riven (Riveh): Heimerd / r", p)
    t = zauber.Zaubertimer()
    assert t.benutzt(replace(g, level=2), "R", 107, "Chat") is None


def flash_auf_dem_bildschirm():
    """Balkenspur: ein Gegner-Balken springt in einem Bild ~300 px mit demselben Leben, dein Balken bleibt ruhig ->
    Flash (bestaetigt im Folgebild). Kein Flash: Kamera dreht (alle springen), Laufen, anderes Leben, Ruecksprung.
    Dazu das Lagebild: gelesener Name -> Flash-Timer mit Quelle 'Bildschirm'."""
    from lolcoach import lage
    from lolcoach.lebensbalken import Balken as B, Balkenspur

    def lauf(bilder):
        s, aus = Balkenspur(), []
        for i, balken in enumerate(bilder):
            aus += s.neu(1.0 + 0.08 * i, balken, 1600)
        return aus
    ich = B(800, 450, 0.9, "ich")
    er = lambda x, y, a=0.55: B(x, y, a, "feind")        # noqa: E731
    flash = lauf([[ich, er(900, 400)], [ich, er(1200, 420)], [ich, er(1205, 421)]])
    assert len(flash) == 1 and flash[0].von == (900, 400) and flash[0].nach == (1200, 420), flash
    kamera = [[ich, er(900, 400)], [B(1100, 450, 0.9, "ich"), er(1200, 400)], [B(1100, 450, 0.9, "ich"), er(1200, 400)]]
    assert not lauf(kamera)                                              # ohne ruhigen Bezug kein Sprung
    assert not lauf([[ich, er(900, 400)], [ich, er(925, 405)], [ich, er(950, 410)]])     # Laufen
    assert not lauf([[ich, er(900, 400)], [ich, er(1200, 420, 0.95)], [ich, er(1200, 420, 0.95)]])   # anderes Leben
    assert not lauf([[ich, er(900, 400)], [ich, er(1200, 420)], [ich, er(900, 400)]])    # zurueck: Fehlzuordnung
    p = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")) if q.zeit > 400)
    g = next(s for s in p.gegner() if s.champion_id == "Brand")      # ohne eigenen Dash
    adc = next(s for s in p.gegner() if s.champion_id == "Varus")
    shen = p.gegenueber()                                            # E ist ein Dash
    lb = lage.Lagebild()
    neu = lb.ereignisse(lambda w: 400.0, [("schirm_sprung", 0.0, ["feind", 0.5, 900, 400, 1200, 420, 0.19,
                                                                   g.champion, g.champion])], p)
    assert len(neu) == 1 and neu[0].quelle == "Bildschirm" and lb.zauber.fehlt(g, "SummonerFlash", 401) > 250, neu
    lb = lage.Lagebild()
    assert not lb.ereignisse(lambda w: 400.0, [("schirm_sprung", 0.0, ["feind", 0.5, 900, 400, 1200, 420, 0.19,
                                                                       g.champion, adc.champion])], p)   # zwei Namen
    # Live 21:21, 9:18: Gragas und Tryndamere "flashten" zugleich - ein Engage mit ihren E. Dash-Champions: stumm
    lb = lage.Lagebild()
    assert not lb.ereignisse(lambda w: 400.0, [("schirm_sprung", 0.0, ["feind", 0.5, 900, 400, 1200, 420, 0.19,
                                                                       shen.champion, shen.champion])], p)
    # Minimap: der Kamerarahmen sagt, wer im Bild sein kann (Live 26.09. 23:06: zwei Spruenge ohne Namen, im Rahmen
    # nur Graves - kein Flash). Rahmen oben links; Brand steht darin, Varus unten rechts.
    rahmen, groesse = [0.30, 0.20, 0.57, 0.35], [1600, 900]

    def mit_minimap(brand_pos, name=""):
        lb = lage.Lagebild()
        lb.neu(399.5, [minimap.Sichtung("Brand", g.team, *brand_pos, 0.95),
                       minimap.Sichtung("Varus", adc.team, 0.8, 0.8, 0.95)], p)
        return lb.ereignisse(lambda w: 400.0, [("schirm_sprung", 0.0, ["feind", 0.5, 900, 400, 1200, 420, 0.19,
                                                                       name, name, rahmen, groesse])], p)
    neu = mit_minimap((0.52, 0.30))                  # ohne Namen: Brand ist im Rahmen, nah am Landepunkt -> er
    assert len(neu) == 1 and neu[0].champion == "Brand", neu
    assert not mit_minimap((0.10, 0.90))             # ohne Namen, kein Gegner im Rahmen -> kein Flash
    assert not mit_minimap((0.10, 0.90), g.champion)  # Name gelesen, aber Brand ist gar nicht im Bild -> Veto
    # so, wie der Beobachter es live baut, muss es als JSON ins Protokoll (np.float64 aus dem Rahmen scheiterte)
    import json
    echt = minimap.kamerarahmen(cv2.imread(str(HIER / "minimap_brunnen.jpg")))
    e = ("schirm_sprung", 1.0, ["feind", 0.5, 900, 400, 1200, 420, 0.19, "", "", list(echt) if echt else None,
                                [1600, 900]])
    assert lage.ereignis_aus_json(json.loads(json.dumps(lage.ereignis_als_json(e))))[2] == e[2]


def brunnen_nach_recall_und_tod():
    """Gegner nach Recall (7 s still, dann weg) oder Tod steht im Brunnen - die Ankunft rechnet ab dort. Nur kurz
    gesehen und weg ist kein Recall (er kann im Busch stehen: lieber zu nah als zu weit)."""
    from lolcoach import lage
    p = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")) if q.zeit > 400)
    j = p.jungler(zustand.gegenteam(p.mein_team))
    def sicht(x, y):
        return minimap.Sichtung(j.champion_id, None, x, y, 1.0)
    lb = lage.Lagebild()
    for i in range(90):
        lb.neu(400 + i * 0.1, [sicht(0.3, 0.3)], p)
    for i in range(10):
        lb.neu(409 + i * 0.1, [], p)
    br = lb.brunnen_seit(j, 410)
    assert br is not None and br[3] == "Recall" and br[:2] == lage.BRUNNEN[j.team], br
    lb = lage.Lagebild()
    for i in range(20):
        lb.neu(400 + i * 0.1, [sicht(0.3, 0.3)], p)
    for i in range(10):
        lb.neu(402 + i * 0.1, [], p)
    assert lb.brunnen_seit(j, 403) is None
    lb._tode[j.name] = 405.0                    # gestorben nach der letzten Sichtung, wieder am Leben
    assert lb.brunnen_seit(j, 406)[3] == "Tod"


def live_partie_2121():
    """Aus der Live-Partie 26.09. 21:21 (Riven gegen Gragas): Briefing unterbrechbar, Siegquote statt Kurve,
    Jungler-Frage mit Schluss aus der Spielzeit."""
    from lolcoach import antworten, denker, lage, regeln, sprechplan, stimme
    # 1) ein langes Briefing haelt eine Flash-Meldung nicht mehr auf
    plan = sprechplan.Sprechplan(stimme.Stumm())
    plan.neu([regeln.Ansage("B" * 600, regeln.WICHTIG, "briefing", zeit=26.0, gueltig=90, sperre=600,
                            unterbrechbar=True)])
    assert plan.takt(26.0).schluessel == "briefing"
    plan.neu([regeln.Ansage("Gragas hat Flash benutzt.", regeln.WICHTIG, "zauber:x", zeit=67.0, gueltig=20)])
    a = plan.takt(67.0)
    assert a is not None and a.schluessel == "zauber:x", "die Flash-Meldung wartet nicht ~50 s auf das Briefing"
    plan.neu([regeln.Ansage("C" * 200, regeln.WICHTIG, "cs5", zeit=70.0, gueltig=40)])
    assert plan.takt(70.0) is None, "was nicht unterbrechbar ist, wird auch nicht unterbrochen"
    # 2) die Siegquote des konkreten Duells (Lexikon, lolalytics) statt der allgemeinen Kurve
    class Gragas:
        champion = champion_id = "Gragas"
    assert denker.siegquote("Riven", Gragas) == 45.9
    # 3) Jungler nie gesehen: was er JETZT tun kann (Clear-Zeiten)
    p = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")) if q.zeit > 400)
    j = p.jungler(zustand.gegenteam(p.mein_team))
    lb = lage.Lagebild()
    lb.neu(p.zeit, [], p)
    p.zeit = 205
    satz = antworten._wo(j, p, lb)
    assert "Full Clear ist etwa jetzt fertig" in satz and "Scuttle oder der erste Gank" in satz, satz


def combo_rechnung():
    """Reasoning #1 'Reicht mein Full-Combo-Schaden fuer den Kill?' - Riven (Wiki V26.15) aus der Live-Partie 21:21:
    Level 7, AD 119, Q3/W1/E1/R1 gegen Gragas Level 5 (Ruestung 53, 1235 Leben): voll ~1100 (reicht nicht), auf
    halbem Leben ~1220 gegen 618 (reicht). Windschnitt waechst mit seinem fehlenden Leben."""
    from lolcoach import combo, rechnung
    p = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER.parent / "aufnahmen" / "2026-09-26_212105.jsonl.gz"))
             if q.zeit > 330 and q.ich and q.ich.level >= 6) \
        if (HIER.parent / "aufnahmen" / "2026-09-26_212105.jsonl.gz").exists() else None
    if p is None:
        return      # Aufnahme nicht da (frischer Checkout): die Rechnung laeuft trotzdem im Kampf-Urteil
    g = p.gegenueber()
    voll = combo.schaden(p.ich, p.werte, p.raenge, None, g, 1.0)
    halb = combo.schaden(p.ich, p.werte, p.raenge, None, g, 0.5)
    assert 950 <= voll <= 1250 and halb > voll and halb > 0.5 * rechnung.max_leben(g), (voll, halb)
    ohne_r = combo.schaden(p.ich, p.werte, p.raenge, {"Q": True, "W": True, "E": True, "R": False}, g, 0.5)
    assert ohne_r < halb, "ohne bereite Ult keine Windschnitt-Rechnung"
    assert combo.kann("Heimerdinger") and not combo.genau("Heimerdinger")   # aus den Spieldaten: nur Untergrenze


def faehigkeiten_aus_spieldaten():
    """Formeln aller Champions (CommunityDragon, wissen/faehigkeiten.json) gegen die von Hand geprueften Wiki-Werte:
    Riven Q/W/R, Graves R, Camille W stimmen auf den Punkt. Gegner-Raenge aus Level + Skill-Reihenfolge; sein Combo
    als Untergrenze gegen dein Leben; Nunus Q (1200 gegen Vasallen) und Maximalwerte sind draussen."""
    from lolcoach import combo, faehigkeiten as fa
    st = {"ad": 150.0, "ad_basis": 100.0, "ad_bonus": 50.0, "ap": 80.0, "ap_bonus": 80.0}
    w = combo.WIKI

    def gleich(champion, slot, rang, soll):
        (ist, _), = fa.schaden(champion, slot, rang, 9, st)
        assert abs(ist - soll) < 0.01, (champion, slot, ist, soll)     # Spieldaten sind float32
    gleich("Riven", "Q", 3, w["Riven"]["q"][2] + w["Riven"]["q_bonus"][2] * 50)
    gleich("Riven", "W", 2, w["Riven"]["w"][1] + 50.0)
    gleich("Riven", "R", 1, w["Riven"]["r2_min"][0] + w["Riven"]["r2_min_bonus"] * 50)
    gleich("Graves", "R", 1, w["Graves"]["r"][0] + w["Graves"]["r_bonus"] * 50)
    gleich("Camille", "W", 2, w["Camille"]["w"][1] + w["Camille"]["w_bonus"] * 50)
    assert fa.schaden("Annie", "Q", 5, 9, st)[0][1] == "magisch" and fa.schaden("Garen", "R", 1, 9, st)[0][1] == "wahr"
    assert all(n != "MonsterMinionDamage" for n, _ in fa.daten()["Nunu"]["Q"]["schaden"])
    assert sum(1 for c in fa.daten().values() if any(v["schaden"] for v in c.values())) >= 165
    assert combo.raenge_geschaetzt("Zed", 9) == {"Q": 5, "E": 2, "W": 1, "R": 1}
    assert sum(combo.raenge_geschaetzt("Garen", 18).values()) == 18
    # sein Combo auf dich: Zed Level 9 mit zwei Items gegen 60 Ruestung
    p = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")) if q.zeit > 400)
    from dataclasses import replace
    zed = replace(p.gegenueber(), champion_id="Zed", champion="Zed", level=9, items=(3142, 3071))
    mit = combo.gegner_schaden(zed, {"armor": 60, "magicResist": 40})
    ohne = combo.gegner_schaden(zed, {"armor": 60, "magicResist": 40}, ult_bereit=False)
    assert 350 <= ohne < mit <= 1600, (ohne, mit)


def stimme_haengt_nicht():
    """Live 26.09. 23:06: nach einem Antippen der Sprechtaste blieb die Stimme angehalten, 'Milio hat Flash benutzt'
    kam 154 s spaet. Jetzt: angehalten ohne Antwort geht sie nach PAUSE_HOECHSTENS weiter, und was zu lange in
    ihrer Schlange lag, wird verworfen statt veraltet gesprochen."""
    import time
    from lolcoach import stimme
    gesprochen = []

    class Sofort:
        def __init__(self, *a):
            pass

        def spreche(self, text, stopp, beim_ton=None, gilt=None):
            if beim_ton:
                beim_ton()
            gesprochen.append(text)
            return True

    alt = stimme._Sapi, stimme.PAUSE_HOECHSTENS, stimme.VERALTET
    stimme._Sapi, stimme.PAUSE_HOECHSTENS, stimme.VERALTET = Sofort, 0.4, 5.0
    try:
        st = stimme.Stimme(lautstaerke=0)
        st.pausiere()                          # Sprechtaste gedrueckt - und nur angetippt, keine Antwort
        st.sage("Milio hat Flash benutzt")
        time.sleep(0.2)
        assert not gesprochen, "waehrend der Frage still"
        time.sleep(0.6)
        assert gesprochen == ["Milio hat Flash benutzt"], gesprochen   # von selbst weiter
        stimme.PAUSE_HOECHSTENS, stimme.VERALTET = 5.0, 0.2
        meldungen = []
        st.pausiere()
        st.sage("alt", melde=lambda art, t: meldungen.append(art))
        time.sleep(0.4)
        st.freigeben()
        time.sleep(0.3)
        assert "alt" not in gesprochen and meldungen == ["verworfen"], (gesprochen, meldungen)
    finally:
        stimme._Sapi, stimme.PAUSE_HOECHSTENS, stimme.VERALTET = alt


def satz_bricht_ab_wenn_er_nicht_mehr_stimmt():
    """Carlos, Live 26.09. 23:20: "Wenn er mitten im Satz sieht, dass Ekko beim Drachen ist, muss er abbrechen und
    sagen: Ekko, ach nee, Ekko ist gerade beim Drachen." Die Stimme fragt waehrend des Sprechens, ob der Satz noch
    stimmt; tut er es nicht, bricht sie ab, die Sperren fallen, der neue Satz zum Thema beginnt mit 'Ach nee'.
    Was schon vor dem ersten Ton nicht mehr stimmt, wird gar nicht gesagt."""
    import time
    from lolcoach import regeln, sprechplan, stimme
    gesprochen = []

    class Lang:
        def __init__(self, *a):
            pass

        def spreche(self, text, stopp, beim_ton=None, gilt=None):
            if beim_ton:
                beim_ton()
            ende = time.monotonic() + 2.0
            while time.monotonic() < ende:
                if stopp.is_set() or (gilt is not None and not gilt()):
                    gesprochen.append(("abgebrochen", text))
                    return False
                time.sleep(0.02)
            gesprochen.append(("ganz", text))
            return True

    alt = stimme._Sapi
    stimme._Sapi = Lang
    try:
        st = stimme.Stimme(lautstaerke=0)
        plan = sprechplan.Sprechplan(st)
        ekko_oben = [True]
        a = regeln.Ansage("Ekko ist oben und kann in 9 Sekunden bei dir sein.", regeln.SOFORT, "jungler_sicht",
                          zeit=100.0, sperre=30, thema="gefahr", pruefe=lambda: ekko_oben[0])
        plan.neu([a])
        plan.takt(100.0)
        time.sleep(0.3)
        ekko_oben[0] = False                     # mitten im Satz: Ekko taucht am Drachen auf
        time.sleep(0.5)
        assert gesprochen and gesprochen[0][0] == "abgebrochen" and a.ganz is False, (gesprochen, a.ganz)
        neu = regeln.Ansage("Ekko ist gerade beim Drachen.", regeln.SOFORT, "jungler_sicht", zeit=101.0,
                            sperre=30, thema="gefahr")
        plan.neu([neu])                          # die Sperre (30 s) ist mit dem Widerruf gefallen
        plan.takt(101.0)
        assert neu.text == "Ach nee - Ekko ist gerade beim Drachen.", neu.text
        # stimmt schon vor dem ersten Ton nicht mehr: kommt gar nicht
        weg = regeln.Ansage("Du hast 1300 Gold, geh back.", regeln.WICHTIG, "gold", zeit=102.0, pruefe=lambda: False)
        plan.neu([weg])
        assert plan.takt(110.0) is None and not plan.warte
    finally:
        stimme._Sapi = alt


def sofort_back_und_objective():
    """'Soll ich backen?' und 'Sollen wir Drache machen?' kommen sofort aus dem Zustand (vorher ~3 s ueber Claude):
    wenig Leben -> ja; Gold fuer ein Bauteil und Gefahr -> erst zum Turm; zu wenig Gold -> noch nicht; der Drache
    aus der Kampflage an der Grube; erst in 2 Minuten -> das sagt die Antwort."""
    from types import SimpleNamespace
    from lolcoach import antworten, bewertung, kaufplan
    p = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")) if q.zeit > 400)
    lb = SimpleNamespace(aktiv=True)
    b = bewertung.Bewertung(zeit=p.zeit, ich=p.ich, leben=0.2, gold=1500, partie=p)
    b.kauf = kaufplan.Kauf("Schwarzes Beil", ["Caulfields Kriegshammer"], 1100, None)
    alt, bewertung.bewerte = bewertung.bewerte, lambda *a, **k: b
    alt_k = bewertung.kampf_um
    try:
        assert antworten.sofort("Soll ich backen?", p, lb).startswith("Ja, geh jetzt back: du hast nur 20 Prozent Leben")
        b.leben = 0.9
        b.welle = (5, 1, 0.7, "ihr")
        assert antworten.sofort("Soll ich recallen?", p, lb).startswith("Ja, jetzt: deine Welle läuft in seinen Turm")
        b.gold, b.kauf = 400, kaufplan.Kauf("Schwarzes Beil", [], 1100, ("Caulfields Kriegshammer", 700))
        assert antworten.sofort("Kann ich back?", p, lb).startswith("Noch nicht: du hast 400 Gold - dir fehlen 700")
        assert antworten.sofort("Warum soll ich backen?", p, lb) is None               # Begruendung: Claude
        bewertung.kampf_um = lambda *a: SimpleNamespace(urteil=lambda: ("nehmen", "Drache: ihr 4, sie 1 - nehmen."),
                                                        wir=[(p.ich, 12.0, 0.9, True)])
        p.naechster_spawn = lambda schl: p.zeit + 10
        assert antworten.sofort("Sollen wir Drache machen?", p, lb) == \
            "Drache: ihr 4, sie 1 - nehmen. Du brauchst 12 Sekunden dorthin."
        p.naechster_spawn = lambda schl: p.zeit + 130
        assert "erst in 2 Minuten" in antworten.sofort("Sollen wir Drache machen?", p, lb)
    finally:
        bewertung.bewerte, bewertung.kampf_um = alt, alt_k


def icon_in_der_brunnen_ecke():
    """Partie 19:45, 12:50: Riven steht im Brunnen, ihr Icon ist vom Kartenrand zu einem Drittel abgeschnitten - die
    ganze Vorlage fand sie 2,5 min lang nicht. Die Eckensuche vergleicht nur den sichtbaren Teil, nur im Brunnen
    ihres Teams, und findet dort niemand anderen."""
    img = cv2.imread(str(HIER / "minimap_brunnen.jpg"))
    assert not [s for s in minimap.finde(img, [("Riven", "ORDER")]) if s.champion_id == "Riven"]
    g, x, y = minimap.ecke(img, "Riven", 2160, "ORDER")
    assert g >= minimap.SCHWELLE_TEIL and x < 25 and y > 540, (g, x, y)
    assert minimap.ecke(img, "Riven", 2160, "CHAOS") is None
    for c in ("Heimerdinger", "Vi", "Caitlyn", "Ahri", "Garen"):
        assert minimap.ecke(img, c, 2160) is None, c
    v = minimap.Verfolger([("Riven", "ORDER"), ("Heimerdinger", "CHAOS")], hoehe=2160)
    sichtungen, _ = v.bild(img, 100.0)
    riven = [s for s in sichtungen if s.champion_id == "Riven"]
    assert riven and 0.0 <= riven[0].x < 0.05 and riven[0].y > 0.94, sichtungen


def platten_lesen():
    """Platten-Ziffern der Turm-Icons (Camille-Partie, ~10:40): oben 2, Mitte 4, unten 4 bei ihm, deine
    Mitte 4; Teemos Icon verdeckt deinen inneren Mid-Turm -> keine Zahl statt einer falschen."""
    from lolcoach import platten
    from lolcoach.bewertung import TUERME
    img = cv2.imread(str(HIER / "minimap_platten.jpg"))
    gelesen = {k: platten.lies(img, k[0], *v)[0] for k, v in TUERME.items()}
    erwartet = {("CHAOS", "Top", "aussen"): 2, ("CHAOS", "Mid", "aussen"): 4, ("CHAOS", "Bot", "aussen"): 4,
                ("ORDER", "Mid", "aussen"): 4, ("ORDER", "Top", "aussen"): 5, ("ORDER", "Mid", "innen"): None}
    for k, z in erwartet.items():
        assert gelesen[k] == z, (k, gelesen[k], z)
    # Platten wachsen nie nach; ein niedrigerer Wert gilt erst nach zwei Lesungen
    leser = platten.Plattenleser()
    leser.stand[("CHAOS", "Top", "aussen")] = 3
    leser.lies_karte(img)
    assert leser.stand[("CHAOS", "Top", "aussen")] == 3
    leser.lies_karte(img)
    assert leser.stand[("CHAOS", "Top", "aussen")] == 2


def teleport_von_der_minimap():
    """Fernsprung: oben verschwunden, 6 s spaeter unten - Teleport. Laufen, ein falsches Einzelbild und der
    Wiedereinstieg nach einem Tod sind keiner."""
    from lolcoach import lage
    p = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")) if q.zeit > 700)
    shen = p.gegenueber()
    teleporter = next(s for s in p.gegner() if "SummonerTeleport" in s.zauber or s.rolle == "TOP")
    lb = lage.Lagebild()
    sicht = lambda x, y: [minimap.Sichtung(teleporter.champion_id, teleporter.team, x, y, 0.95)]
    lb.neu(700.0, sicht(0.08, 0.30), p)                 # oben in der Lane
    lb.neu(706.0, sicht(0.70, 0.90), p)                 # 6 s spaeter unten: Kandidat
    assert not lb.zauber.fehlt(teleporter, "SummonerTeleport", 707), "erst nach Bestaetigung"
    lb.neu(707.0, sicht(0.71, 0.90), p)                 # zweites Bild am selben Ort: bestaetigt
    # Teleport - oder, ohne Teleport, die globale Ult (Shen in dieser Partie hat kein TP)
    art = "SummonerTeleport" if "SummonerTeleport" in teleporter.zauber or teleporter.champion_id not in lage.GLOBALE_ULTS else "R"
    assert lb.zauber.fehlt(teleporter, art, 708), (art, "Fernsprung nicht erkannt")
    # Laufen: 40 s fuer dieselbe Strecke - kein Teleport
    lb2 = lage.Lagebild()
    lb2.neu(700.0, sicht(0.08, 0.30), p)
    lb2.neu(712.0, sicht(0.30, 0.55), p)
    lb2.neu(713.0, sicht(0.30, 0.55), p)
    assert not lb2.zauber.fehlt(teleporter, art, 714)
    # ein einzelnes falsches Bild weit weg, dann wieder oben - kein Teleport
    lb3 = lage.Lagebild()
    lb3.neu(700.0, sicht(0.08, 0.30), p)
    lb3.neu(706.0, sicht(0.70, 0.90), p)
    lb3.neu(707.0, sicht(0.08, 0.31), p)
    assert not lb3.zauber.fehlt(teleporter, art, 708)


def lebensbalken_lesen():
    """Lebensbalken im Spielbild (Camille-Partie): der eigene gruene Balken 64 % (HUD 617/955 = 65 %), sonst
    nichts; gruen -> Gegner-Rot umgefaerbt wird er 'feind'; ein gelesener Name wird dem Gegner zugeordnet."""
    import numpy as np
    from lolcoach import lage, lebensbalken
    img = cv2.imread(str(HIER / "schirm_balken.jpg"))
    b = lebensbalken.finde(img)
    assert len(b) == 1 and b[0].team == "ich" and abs(b[0].anteil - 0.65) <= 0.03, b
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, (45, 110, 110), (75, 255, 255))
    rot = img.copy()
    hell = hsv[..., 2][m > 0].astype(float) / 255
    rot[m > 0] = (np.array((45, 55, 205))[None, :] * hell[:, None] * 1.2).clip(0, 255).astype(np.uint8)
    b = lebensbalken.finde(rot)
    assert len(b) == 1 and b[0].team == "feind" and abs(b[0].anteil - 0.63) <= 0.04, b
    p = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")) if q.zeit > 400)
    g = p.gegenueber()
    lb = lage.Lagebild()
    lb.ereignisse(lambda w: 400.0, [("balken", 0.0, [(g.champion, 0.3, "feind")])], p)
    assert lb.gegner_leben_jetzt(g, 401.0) == 0.3 and lb.gegner_leben_jetzt(g, 404.0) is None
    # Manabalken darunter (Live 26.09., Heimerdinger: Leben 74 %, Mana sichtbar ~96 %)
    img = cv2.imread(str(HIER / "schirm_mana.png"))
    b = [x for x in lebensbalken.finde(img) if x.team == "feind"]
    assert len(b) == 1 and abs(b[0].anteil - 0.74) <= 0.03 and abs(lebensbalken.mana(img, b[0]) - 0.95) <= 0.04, b
    lb.ereignisse(lambda w: 410.0, [("balken", 0.0, [(g.champion, 0.5, "feind", 0.2)])], p)
    assert lb.gegner_mana_jetzt(g, 411.0) == 0.2
    assert lage.ereignis_aus_json(lage.ereignis_als_json(("balken", 1.0, [("Shen", 0.5, "feind", 0.2)])))[2] \
        == [("Shen", 0.5, "feind", 0.2)]


def verzoegerung_bis_zum_ohr():
    """Live misst der Plan, wann eine Ansage wirklich klingt (Carlos: 'geisteskrank zu spaet') und ob sie
    abgebrochen wurde - mit einer Ersatzstimme, die 0,1 s bis zum ersten Ton braucht."""
    import time
    from lolcoach import regeln, sprechplan, stimme

    class Langsam:
        def __init__(self, *a):
            pass

        def spreche(self, text, stopp, beim_ton=None, gilt=None):
            time.sleep(0.1)
            if beim_ton:
                beim_ton()
            return not stopp.wait(0.3 if "kurz" in text else 5)

    alt, stimme._Sapi = stimme._Sapi, Langsam
    try:
        st = stimme.Stimme(lautstaerke=0)
        plan = sprechplan.Sprechplan(st)
        lang = regeln.Ansage("lang " * 30, regeln.WICHTIG, "cs10", zeit=100.0, unterbrechbar=True)
        plan.neu([lang])
        plan.takt(100.0)
        time.sleep(0.3)
        eilig = regeln.Ansage("kurz: Vi kommt", regeln.SOFORT, "anlauf", zeit=101.0)
        plan.neu([eilig])
        plan.takt(101.0)
        ende = time.monotonic() + 3
        while eilig.ganz is None and time.monotonic() < ende:
            time.sleep(0.02)
    finally:
        stimme._Sapi = alt
    assert lang.ton is not None and 0.05 <= lang.ton - 100.0 <= 0.3, lang.ton
    assert lang.ganz is False, "abgebrochen"
    assert eilig.ton is not None and 0.05 <= eilig.ton - 101.0 <= 0.5 and eilig.ganz is True, (eilig.ton, eilig.ganz)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for test in (item_namen, wellen, mitspieler_leiste, teleport_timer, kuerzen_und_orte, profil_ueber_partien,
                 zauber_im_briefing, recalls_im_verlauf, sprechbar, matchup_zeilen, chat_zeitstempel, akte_teile, chat_pings, eigene_tasten,
                 aufnahme_fortsetzen, bildschirm_momente, bewertung_und_plan, denkkette, flash_auf_dem_bildschirm, brunnen_nach_recall_und_tod, live_partie_2121, combo_rechnung,
                 platten_lesen, teleport_von_der_minimap, lebensbalken_lesen, verzoegerung_bis_zum_ohr,
                 faehigkeiten_aus_spieldaten, icon_in_der_brunnen_ecke, stimme_haengt_nicht,
                 satz_bricht_ab_wenn_er_nicht_mehr_stimmt, sofort_back_und_objective):
        test()
        print(f"{test.__name__} OK")
