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
    wellen_front()


def wellen_front():
    """F1 (Qualitaetsrunde 1, Nachtrag Buch 1 1.4): Front statt Summe. 144655 3:13/5:17/5:38: gegnerische Vasallen an
    deinem Turm, deine naechste Welle laeuft erst dahinter los - die Summe ergab ZU_IHM."""
    from lolcoach.kern import konfig
    from lolcoach.kern.merkmale import WellenPuffer, lane_punkt

    def auf(team, *s_werte):
        return [(team, *lane_punkt("Top", s)) for s in s_werte]
    # Zusammenstoss (beide Farben in einer Gruppe) ist die Front, die blaue Gruppe dahinter laeuft nach
    z = welle.zustaende(auf("blau", 0.47, 0.48) + auf("rot", 0.50, 0.51, 0.52) + auf("blau", 0.28, 0.30, 0.31))["Top"]
    assert (z.blau, z.rot, z.alle_blau) == (2, 3, 5) and z.naechste_blau is not None and abs(z.naechste_blau - 0.31) < 0.01, z
    # drei gegnerische vor deinem Turm (Rueckfall 0,35), fuenf eigene hinter ihm: GECRASHT_BEI_DIR
    z = welle.zustaende(auf("rot", 0.37, 0.39, 0.41) + auf("blau", 0.15, 0.17, 0.19, 0.21, 0.23))["Top"]
    wp = WellenPuffer(konfig())
    for t in range(8):
        wp.lesen(100.0 + t, z, 100.0 + t, "ORDER")
        st = wp.stand(100.0 + t, "Top", "ORDER", None, {})
    assert st.zustand == "GECRASHT_BEI_DIR", st
    # zwei gegnerische reichen nicht (>= 3), solange dein Icon die Zone nicht verdeckt
    z = welle.zustaende(auf("rot", 0.37, 0.39) + auf("blau", 0.15, 0.17, 0.19, 0.21, 0.23))["Top"]
    wp = WellenPuffer(konfig())
    for t in range(8):
        wp.lesen(100.0 + t, z, 100.0 + t, "ORDER")
        st = wp.stand(100.0 + t, "Top", "ORDER", None, {})
    assert st.zustand != "GECRASHT_BEI_DIR", st


def rueckblick_passt_zum_leben():
    """G5 (Qualitaetsrunde 2, 133930 14:57): mit vollem Leben beim Einstieg ist "back" die falsche Lehre."""
    from lolcoach import komponist
    voll = komponist.todesrueckblick(None, ["Tristana", "Zoe"], None, False, 0.9)
    wenig = komponist.todesrueckblick(None, ["Tristana", "Zoe"], None, False, 0.3)
    assert "hinter den Turm oder zu deinem Team" in voll and "back" not in voll.lower(), voll
    assert "back" in wenig.lower(), wenig


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
        "Jungler oder Laner seit 30 bis 40 Sekunden weg, ab mehr als zweitausendfünfhundert Gold"   # Auftrag 002, S1
    # Auftrag 002, S1: Kill-Bilanzen ohne Schraegstrich ("du stehst sechs null")
    assert s("KDA 27/6/4") == "KDA siebenundzwanzig sechs vier"
    # Spielzeiten als Woerter (E8, gemessen: "7 57" las die Stimme "sieben, fuenf, sieben")
    assert s("Gank zwischen 2:45 und 3:30, Drache um 5:00") == \
        "Gank zwischen zwei fünfundvierzig und drei dreißig, Drache um fünf Minuten"
    assert s("Stapel die Top-Welle bis zur Kanone um 7 57: dann crashen.") == \
        "Stapel die Top-Welle bis zur Kanone um sieben siebenundfünfzig: dann crashen."
    assert s("Spawn um 8 00, 21 Uhr") == "Spawn um acht Minuten, 21 Uhr"
    for gleich in ("Mid-Lane", "Level 6", "Tri-Bush", "80 %", "5 sind weg"):
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
        # Viego uebernimmt einen Champion: die API meldet dessen Namen - dieselbe Partie (144655, 9:24)
        spieler = [dict(x) for x in schnappschuesse[30]["allPlayers"]]
        spieler[-1]["championName"] = "Viego" if spieler[-1].get("championName") != "Viego" else "Vex"
        assert aufzeichnung.fortsetzbar(dict(schnappschuesse[30], allPlayers=spieler), ordner) == s.pfad
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
    assert "zurück zu deinem nächsten Turm" in satz and "35 Prozent Leben" in satz and "3 Sekunden" in satz, satz
    # Sofort-Antwort aus dem Entscheider; Kauf-Fragen seit 27.09. aus dem Kaufplan (Claude widersprach sich live:
    # "zuerst Kontroll-Auge kaufen" und gleich darauf "kauf jetzt kein Kontroll-Auge"), das Warum bei Claude
    plan = entscheider.Option("druck", "Spiel auf Shen: du bist 2 Level vorn.", 100, 2)
    lb = S(entscheider=S(aktuell=plan))
    assert antworten.sofort("Was soll ich jetzt machen?", p, lb) == plan.satz
    kauf = antworten.sofort("Was soll ich kaufen?", p, lb)
    assert kauf is not None and "Ziel ist" in kauf, kauf
    assert antworten.sofort("Warum soll ich das kaufen?", p, lb) is None
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
    # Buch 0, 6.2: ohne Beleg kein Kill-Ruf - kein Leben im Bild, keine Combo-Rechnung, Ueberlegenheit 2,5 < 3,0
    assert u.art == "trade" and u.beleg is None, (u.art, u.wert, [(x.art, x.wert) for x in u.faktoren])
    # sein Leben eben (0,4 s) gelesen, aber die Combo-Rechnung sagt "reicht nicht": kein Kill (6.2, 11:33)
    b.lane = gl(g, flash=200.0, leben=0.45, leben_alter=0.4)
    b.gegner = [b.lane, b.jungler]
    assert denker.urteil(b).art == "trade", denker.urteil(b).art
    # klare Ueberlegenheit (3 Level vorn + der Level-6-Sprung): Kill - gesagt wird der tragende Beleg, keine Sammlung
    b.ich = replace(ich, level=8)
    b.lane = gl(g, flash=200.0, level_vorsprung=g.level - 8)
    b.gegner = [b.lane, b.jungler]
    u = denker.urteil(b)
    assert u.art == "kill" and u.beleg is not None and u.beleg.art == "ueberlegen", \
        (u.art, u.wert, [(x.art, x.wert) for x in u.faktoren])
    satz = denker.fenster_satz(b, u, anlass=f"Du bist jetzt Level 8, {g.champion} erst 5", ohne={"ult"})
    # Handlung zuerst, Gruende in einem Satz (Live 21:21: ~300 Zeichen je Ansage, der Coach redete 74 % der Zeit)
    # ... und der Anlass ist der erste Grund, nicht der Satzanfang (Nachlauf 194524: 3,5 s bis zum "geh rein")
    assert satz.startswith(f"Geh rein, das ist ein Kill: du bist jetzt Level 8, {g.champion} erst 5"), satz
    assert "klar überlegen" in satz and "kein Flash" not in satz and len(satz) <= 190, (len(satz), satz)
    assert satz.count("Level 8") == 1, satz                      # der Anlass sagt das Level, nicht zweimal
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
    b.ich = ich                 # zurueck auf Level 6 gegen 5 fuer die folgenden Faelle
    # am Turm: warten (kein Dive - Live 11:00/11:08), mit dem Jungler nah: kein All-in
    b.lane = gl(g, flash=200.0, pos=bewertung.TUERME[(zustand.gegenteam(p.mein_team), "Top", "aussen")])
    assert denker.urteil(b).art == "turm", denker.urteil(b).art
    b.leben_abs = 1200      # Turm in Zahlen (Wiki Turret): 5:30 aussen 248 pro Schuss, aufwaermend -> 3 Schuesse
    satz = denker.fenster_satz(b, denker.urteil(b))
    assert "Noch nicht rein" in satz and "Sein Turm trifft dich mit etwa 180, du hältst 3 Schüsse aus." in satz, satz
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
    # 1) ein langes Briefing bricht nur eine Gefahr ab (seit 27.09., Partie 144655: keine Satzfetzen) - eine
    #    Flash-Meldung wartet (sie steht ohnehin auf dem Dashboard, Kapitel 9.1)
    plan = sprechplan.Sprechplan(stimme.Stumm())
    # ~43 s Briefing, egal wie schnell die Stimme ist (Auftrag 002: [stimme] zeichen_pro_s)
    plan.neu([regeln.Ansage("B" * int(43 * sprechplan.ZEICHEN_PRO_SEKUNDE), regeln.WICHTIG, "briefing", zeit=26.0,
                            gueltig=90, sperre=600,
                            unterbrechbar=True)])
    assert plan.takt(26.0).schluessel == "briefing"
    plan.neu([regeln.Ansage("Gragas hat Flash benutzt.", regeln.WICHTIG, "zauber:x", zeit=67.0, gueltig=20)])
    assert plan.takt(67.0) is None, "keine Gefahr: bricht das Briefing nicht ab"
    plan.neu([regeln.Ansage("Gragas kommt auf dich zu.", regeln.WICHTIG, "gank", zeit=68.0, gueltig=20,
                            thema="gefahr")])
    a = plan.takt(68.0)
    assert a is not None and a.schluessel == "gank", "eine Gefahr wartet nicht ~50 s auf das Briefing"
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
        st.taste_los()
        meldungen = []
        st.sage("Milio hat Flash benutzt", melde=lambda art, t: meldungen.append(art))
        time.sleep(0.2)
        assert not gesprochen, "waehrend der Frage still"
        time.sleep(0.6)                        # keine Antwort gekommen: von selbst weiter ...
        st.sage("Jetzt wieder")
        time.sleep(0.2)
        # ... aber was waehrend der Frage kam, wird nicht nachgeholt (steht im Dashboard)
        assert gesprochen == ["Jetzt wieder"] and meldungen == ["verworfen"], (gesprochen, meldungen)
    finally:
        stimme._Sapi, stimme.PAUSE_HOECHSTENS, stimme.VERALTET = alt


def sprechtaste_ist_stummtaste():
    """Carlos 27.09.: "meine Push-to-Talk-Taste muss seine Mute-Taste sein ... wenn ich fertig bin mit reden, ist
    das erste, was er machen muss, darauf zu antworten. Keine anderen Phrasen! Nach der Antwort kann er mit seinem
    Gelaber weitermachen" - und "40-mal hintereinander geh rein". Taste gehalten: kein Ton. Danach: nur die
    Antwort, auch zwischen ihren Teilen nichts; was der Plan waehrenddessen wollte, faellt weg. Ein abgebrochener
    Satz kommt nicht wieder (vorher: bei jedem Druck abgebrochen, danach wiederholt - die Schleife)."""
    import time
    from lolcoach import stimme
    begonnen, ganz = [], []

    class Langsam:
        def __init__(self, *a):
            pass

        def spreche(self, text, stopp, beim_ton=None, gilt=None):
            begonnen.append(text)
            ende = time.monotonic() + 0.3
            while time.monotonic() < ende:
                if stopp.is_set():
                    return False
                time.sleep(0.01)
            ganz.append(text)
            return True

    alt = stimme._Sapi
    stimme._Sapi = Langsam
    try:
        st = stimme.Stimme(lautstaerke=0)
        st.sage("Geh rein, das ist ein Kill.")
        time.sleep(0.1)
        st.pausiere()                                   # Taste unten: der laufende Satz bricht ab
        verworfen = []
        st.sage("Sett hat Flash benutzt.", dringend=True, melde=lambda art, t: verworfen.append(art))
        st.sage("Fiddlesticks ist oben.", melde=lambda art, t: verworfen.append(art))
        time.sleep(0.4)
        assert begonnen == ["Geh rein, das ist ein Kill."], f"sprach in die Frage hinein: {begonnen}"
        st.taste_los()
        st.antworte_teil("Ja, geh auf Sett,")
        time.sleep(0.5)                                 # Claude denkt noch - trotzdem keine Ansage dazwischen
        st.antworte_teil("er hat kein Flash.")
        st.antworte_ende()
        time.sleep(0.9)
        assert begonnen[1:] == ["Ja, geh auf Sett,", "er hat kein Flash."], begonnen
        assert verworfen == ["verworfen", "verworfen"], verworfen
        st.sage("Danach wieder normal.")
        time.sleep(0.5)
        assert begonnen[-1] == "Danach wieder normal.", begonnen
        begonnen.clear()
        st.sage("Geh rein, das ist ein Kill.")
        for _ in range(4):                              # er drueckt immer wieder
            time.sleep(0.1)
            st.pausiere()
            time.sleep(0.05)
            st.taste_los()
            st.freigeben()
        time.sleep(1.0)
        assert begonnen == ["Geh rein, das ist ein Kill."], begonnen
    finally:
        stimme._Sapi = alt


def satz_wird_zu_ende_gesagt_dann_korrigiert():
    """Carlos, Live 26.09. 23:20: "Wenn er mitten im Satz sieht, dass Ekko beim Drachen ist, muss er abbrechen und
    sagen: Ekko, ach nee, Ekko ist gerade beim Drachen." Abbrechen ergab Satzfetzen (Partie 144655: 11 von 18 Saetzen
    nach ein, zwei Woertern weg) - seit 27.09. bricht nur eine Gefahr einen Satz ab. Wird er beim Sprechen falsch,
    spricht die Stimme ihn zu Ende; dann fallen die Sperren, und die Korrektur beginnt mit 'Ach nee'. Was schon vor
    dem ersten Ton nicht mehr stimmt, wird gar nicht gesagt."""
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
        time.sleep(1.4)
        assert gesprochen and gesprochen[0][0] == "ganz" and a.ganz is True, (gesprochen, a.ganz)
        neu = regeln.Ansage("Ekko ist gerade beim Drachen.", regeln.SOFORT, "jungler_sicht", zeit=101.0,
                            sperre=30, thema="gefahr")
        plan.neu([neu])                          # die Sperre (30 s) ist gefallen: der Satz stimmte am Ende nicht
        plan.takt(101.0)
        assert neu.text == "Ach nee: Ekko ist gerade beim Drachen.", neu.text
        assert stimme.teilsaetze("Ach nee: Ekko ist oben, in 9 Sekunden bei dir.") == \
            ["Ach nee:", "Ekko ist oben,", "in 9 Sekunden bei dir."]
        # stimmt schon vor dem ersten Ton nicht mehr: kommt gar nicht
        weg = regeln.Ansage("Du hast 1300 Gold, geh back.", regeln.WICHTIG, "gold", zeit=102.0, pruefe=lambda: False)
        plan.neu([weg])
        assert plan.takt(110.0) is None and not plan.warte
    finally:
        stimme._Sapi = alt


def stimme_spielt_ab_dem_ersten_stueck():
    """Die Synthese liefert MP3-Stuecke; gespielt wird ab dem ersten (27.09.: erster Ton im Median 0,27 statt
    0,63 s). Haengt die erste Anfrage, gewinnt die zweite - und nur ihre Stuecke zaehlen, keine doppelten."""
    import asyncio
    import time
    import av  # noqa: F401 - kalt importiert dauert er unter Last ~1 s (live waermt "Los." vor)
    import edge_tts
    from lolcoach import stimme
    mp3 = (HIER / "satz.mp3").read_bytes()
    anfragen = []

    class Falsch:
        def __init__(self, text, stimme_, rate=None):
            anfragen.append(text)
            self.nr = len(anfragen)

        async def stream(self):
            if self.nr == 1:
                await asyncio.sleep(3.0)          # die erste haengt (wie jede vierte beim Dienst)
            for i in range(0, len(mp3), 1500):
                yield {"type": "audio", "data": mp3[i:i + 1500]}

    alt = edge_tts.Communicate
    edge_tts.Communicate = Falsch
    try:
        t0 = time.monotonic()
        s = stimme._Strom("Der Drache kommt in einer Minute.", "x", "+0%", 1.0)
        erstes = s.stueck(0, time.monotonic() + 5)
        assert erstes is not None and erstes is not stimme.ENDE
        assert time.monotonic() - t0 < 2.0, time.monotonic() - t0      # nicht erst nach den 3 s der ersten
        audio, rate = s.ganz()
        assert rate == 24000 and 1.5 < len(audio) / rate < 4.0, len(audio) / rate     # ~2,3 s, nicht doppelt
        assert len(anfragen) == 2 and s.fehler is None
    finally:
        edge_tts.Communicate = alt


def minimap_blind_wird_gesagt():
    """Liest der Coach live die Minimap nicht (Groesse, verdeckt, Fenster), rechnet er still ohne Karte - er muss es
    sagen. Verbuendete sind immer zu sehen: 30 s niemand aus dem Team = blind. (Ohne Fehlalarm an 3 echten Partien.)"""
    import contextlib
    import io
    from types import SimpleNamespace
    from lolcoach import __main__ as m, stimme

    class Blind:
        b = SimpleNamespace()

        def zwischen(self, bis, champions):
            return []

        def ereignisse(self):
            return []

    class Merker(stimme.Stumm):
        def __init__(self):
            self.gesagt = []

        def sage(self, text, dringend=False, melde=None, noch_wahr=None):
            self.gesagt.append(text)
    sp = Merker()
    with contextlib.redirect_stdout(io.StringIO()):
        m._verfolge(aufzeichnung.lies_mit_zeit(HIER / "botspiel_riven_1.jsonl.gz"), None, takt=0, sprecher=sp,
                    sicht=Blind(), alle=10**9, nur_coach=True)
    assert sum("Minimap" in t for t in sp.gesagt) == 1, sp.gesagt


def baron_aeltester_inhibitor():
    """Buff-Dauer und Inhibitor-Respawn: vorher kannte der Coach beides nicht. Inhibitor gegen die echte Partie
    125902 geprueft (gefallen 21:11, InhibRespawned 26:11,6)."""
    from types import SimpleNamespace as N
    from lolcoach import komponist, regeln, wissen
    obj = wissen.objektive()
    assert obj["baron"]["buff"] == 180 and obj["aeltester"]["buff"] == 150 and obj["inhibitor"]["respawn"] == 300
    b = N(ich=N(rolle="TOP", tot=False, respawn=0.0), mitspieler_nah=[], gold=500, kauf=None, partie=None,
          tiefe=0.4)    # auf seiner Lane: "lass sie laufen" gilt nur dort
    assert komponist.inhib_satz(b, "Top", False, 1571.0) == \
        "Sein Top-Inhibitor ist bis 26 11 weg - eure Supervasallen drücken Top: lass sie laufen und hol dir die Türme dahinter."
    assert komponist.inhib_satz(b, "Bot", True, 1740.0).startswith("Dein Bot-Inhibitor ist bis 29 00 weg")
    p = N(gegner=lambda: [], mein_team="ORDER")
    b.partie = p
    assert komponist.buff_satz(b, "baron", False, 1500.0).startswith(
        "Sie haben den Baron-Buff bis 25 00: kein Kampf allein")
    assert komponist.buff_satz(b, "aeltester", True, 1500.0).startswith("Ihr habt den Ältesten bis 25 00 - jetzt kämpfen")
    # der Rest der Kette: die Regel liest die Ereignisse (hier nur, dass es sie gibt)
    assert hasattr(regeln.Regelwerk, "_grosse_objectives")


def wecker_bei_sprung_und_gegner_nah():
    """Der Kern wartet sonst bis zu 0,25 s (Takt): ein Sprung oder ein Gegner, der neben dir neu auftaucht, weckt ihn
    sofort - ein Verbuendeter oder ein weit entfernter Gegner nicht, und hoechstens alle 0,1 s."""
    import threading
    from types import SimpleNamespace
    from lolcoach import lage, minimap
    S = minimap.Sichtung

    def neu():
        return SimpleNamespace(champions=[("Riven", "ORDER"), ("Ekko", "ORDER"), ("Vi", "CHAOS")],
                               ich=("Riven", "ORDER"), _ich_zuletzt=(10.0, 0.20, 0.20), wecker=threading.Event(),
                               _geweckt=0.0)
    w = lage.Beobachter._wecken
    b = neu()
    w(b, 10.5, [S("Vi", None, 0.25, 0.22, 0.95)], [], [])
    assert b.wecker.is_set()                                     # Gegner neu neben dir
    b = neu()
    w(b, 10.5, [S("Ekko", None, 0.22, 0.21, 0.95), S("Vi", None, 0.80, 0.80, 0.95)], [], [])
    assert not b.wecker.is_set()                                 # Verbuendeter nah, Gegner weit weg
    w(b, 10.6, [], [], ["sprung"])
    assert b.wecker.is_set()                                     # Flash-Sprung
    b.wecker.clear()
    w(b, 10.65, [], [], ["sprung"])
    assert not b.wecker.is_set()                                 # hoechstens alle 0,1 s


def satzanfaenge_vorgewaermt():
    """Die zu Spielbeginn vorgewaermten Anfaenge (komponist.anfaenge) muessen genau die sein, die stimme.teilsaetze
    von echten Saetzen abtrennt - sonst liegt nichts im Speicher. (27.09.: ein unbelegtes `j` liess die Liste
    abstuerzen, und `sicher()` haette es live verschluckt.)"""
    from lolcoach import komponist, stimme
    p = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")) if q.ich)
    anf = {stimme.sprechbar(t) for t in komponist.anfaenge(p)}
    j = p.jungler("CHAOS" if p.mein_team == "ORDER" else "ORDER")
    for satz in (f"{j.champion} ist im oberen Fluss, in 14 Sekunden bei dir. Geh zurück.",
                 "Geh rein, das ist ein Kill: dein Combo macht etwa 810, Heimerdinger hat nur 730 Leben.",
                 f"{j.champion} hat Flash benutzt, bis 6 45.",
                 "Nehmt jetzt den Drachen, ihr seid 5 gegen 3: Vi und Sion sind für 13 Sekunden tot."):
        assert stimme.teilsaetze(stimme.sprechbar(satz))[0] in anf, (stimme.teilsaetze(stimme.sprechbar(satz)), satz)


def eigene_position_aus_dem_kamerarahmen():
    """235433, 6:33: Riven liegt unter Poppy (davor unter Twisted Fate), 6,8 s ohne erkanntes Icon. Der
    Kamerarahmen sagt, wo sie ist: 3,6 s spaeter taucht sie bei (0,100, 0,168) wieder auf. Ein frei geschwenkter
    Rahmen (passt nicht zur letzten Sichtung) gibt nichts."""
    from types import SimpleNamespace
    from lolcoach import lage, minimap
    karte = cv2.imread(str(HIER / "minimap_riven_verdeckt.jpg"))
    rahmen = minimap.kamerarahmen(karte)
    pos = minimap.ich_aus_rahmen(rahmen, (97.0, 0.0772, 0.2228), 100.0)
    assert pos is not None and abs(pos[0] - 0.100) + abs(pos[1] - 0.168) < 0.03, pos
    assert minimap.ich_aus_rahmen(rahmen, (99.0, 0.60, 0.60), 100.0) is None          # Kamera woanders
    assert minimap.ich_aus_rahmen(rahmen, (90.0, 0.0772, 0.2228), 100.0) is None      # letzte Sichtung zu alt
    # der Beobachter ergaenzt nur das fehlende eigene Icon
    b = SimpleNamespace(ich=("Riven", "ORDER"), _ich_zuletzt=(97.0, 0.0772, 0.2228))
    ergaenzen = lage.Beobachter._ich_ergaenzen
    neu = ergaenzen(b, karte, 100.0, [minimap.Sichtung("Poppy", None, 0.142, 0.151, 0.95)])
    assert [s.champion_id for s in neu] == ["Poppy", "Riven"] and neu[1].guete == 0.0
    gesehen = [minimap.Sichtung("Riven", None, 0.2, 0.2, 0.97)]
    assert ergaenzen(b, karte, 101.0, gesehen) == gesehen and b._ich_zuletzt == (101.0, 0.2, 0.2)


def stimme_ueberlebt_audiofehler():
    """Wirft die Ausgabe (Headset kurz weg), darf der Sprech-Thread nicht sterben - sonst ist der Coach fuer den
    Rest der Partie stumm. Der naechste Satz kommt."""
    import time
    from lolcoach import stimme

    class Wirft:
        n = 0

        def __init__(self, *a):
            pass

        def spreche(self, text, stopp, beim_ton=None, gilt=None):
            Wirft.n += 1
            if Wirft.n == 1:
                raise OSError("Geraet weg")
            return True

    alt, alt_w = stimme._Sapi, stimme._Neural._wasapi
    stimme._Sapi = Wirft
    try:
        st = stimme.Stimme(lautstaerke=0)
        ende = []
        for t in ("eins", "zwei"):
            st.sage(t, melde=lambda a, _t: ende.append(a) if a != "ton" else None)
        bis = time.monotonic() + 3
        while len(ende) < 2 and time.monotonic() < bis:
            time.sleep(0.02)
        assert ende == ["abgebrochen", "ende"], ende
    finally:
        stimme._Sapi, stimme._Neural._wasapi = alt, alt_w


def konter_kauf_ohne_eigenes():
    """'Gegen Heimerdinger: Items: Magieresistenz, Merkurs Schuhe.' war vorgelesen - jetzt ein Rat, und was du
    schon hast (Merkurs Schuhe, genug Magieresistenz), faellt weg."""
    from types import SimpleNamespace as N
    from lolcoach import denker
    heimer = N(s=N(champion_id="Heimerdinger"), champion="Heimerdinger")
    assert denker.item_tipp(N(ich=N(items=[1055])), heimer, set()) == \
        "Gegen Heimerdinger kaufst du am besten Magieresistenz und Merkurs Schuhe."
    assert denker.item_tipp(N(ich=N(items=[3111])), heimer, set()) == \
        "Gegen Heimerdinger kaufst du am besten Magieresistenz."          # 20 MR aus den Schuhen reichen nicht
    assert denker.item_tipp(N(ich=N(items=[3111, 3155])), heimer, set()) == ""


def kein_zweites_geh_zurueck():
    """Nachlauf 194524: viermal "geh zurueck zu deinem Mid-Tier-1-Turm" in 37 s, und eine Gefahr brach die andere nach
    einer Sekunde ab. Ein eben gehoertes "geh zurueck" wird nicht wiederholt (ausser als Gefahr); eine Gefahr wartet,
    bis die laufende ihre Handlung gesagt hat; stirbt ein genannter Gegner, ist der Satz ueberholt."""
    from lolcoach import regeln, sprechplan, stimme
    A, W, S = regeln.Ansage, regeln.WICHTIG, regeln.SOFORT
    plan = sprechplan.Sprechplan(stimme.Stumm())
    assert plan.takt(100.0) is None
    plan.neu([A("Geh zurück zu deinem Top-Tier-1-Turm, Vi ist oben.", W, "jungler_sicht", zeit=100.0, thema="gefahr")])
    assert plan.takt(100.0) is not None
    plan.neu([A("Kassadin kann schon da sein. Geh jetzt zurück.", W, "plan:zurueck", zeit=106.0)])
    assert plan.takt(106.0) is None and not plan.warte            # eben gehoert: faellt weg
    plan.neu([A("Vi ist direkt bei dir. Geh zurück.", S, "jungler_sicht", zeit=107.0, sperre=0)])
    assert plan.takt(107.0) is not None                           # eine Gefahr kommt immer
    lang = A("Vi ist oben und kann in 7 Sekunden bei dir sein. Geh zurück zu deinem Mid-Tier-1-Turm, das sind 22 "
             "Sekunden.", S, "gefahr1", zeit=200.0)
    plan.neu([lang])
    assert plan.takt(200.0) is lang
    zweite = A("Braum und Warwick sind tot, ihr seid nur zu dritt.", S, "zahlen_nachteil", zeit=201.0)
    plan.neu([zweite])
    assert plan.takt(201.0) is None and zweite in plan.warte      # erst die Handlung der laufenden
    assert plan.takt(204.5) is zweite
    # stirbt der genannte Gegner, stimmt "Heimerdinger hat kein Flash - spiel aggressiv" nicht mehr
    from types import SimpleNamespace
    heimer = SimpleNamespace(name="h", champion="Heimerdinger", tot=False)
    vi_tot = SimpleNamespace(name="v", champion="Vi", tot=True)
    p = SimpleNamespace(gegner=lambda: [heimer, vi_tot])
    werk = regeln.Regelwerk()
    werk.vorher = p
    lebt = werk._alle_leben(A("Vi ist tot. Heimerdinger hat kein Flash - spiel aggressiv.", W, "jungler_tot"), p)
    assert lebt is not None and lebt()
    heimer.tot = True
    assert not lebt()
    vi = SimpleNamespace(gegner=lambda: [SimpleNamespace(name="v", champion="Vi", tot=False)])
    assert werk._alle_leben(A("Viel Gold, geh back.", W, "gold"), vi) is None           # ganzes Wort
    assert werk._alle_leben(A("Vi ist oben.", W, "jungler_sicht"), vi) is not None


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


def modus_sperre_budget():
    """Buch 0, Schritt 2: ein Modus je Takt (Prioritaet, Hysterese 1,5 s, KAMPF sofort - und vorbei, sobald kein
    Gegner mehr in Reichweite ist), die alten Regeln sprechen nur in ihren Modi (Kapitel 14), Flash/Items/Level/CS
    gehen aufs Dashboard, zwischen zwei Ansagen ausser SOFORT liegen 12 s, und Claude bekommt die letzte Ansage nur,
    wenn die Frage darauf zeigt."""
    from types import SimpleNamespace as N
    from lolcoach import antworten, regeln, sprechplan, stimme
    from lolcoach.kern import konfig, sperre
    from lolcoach.kern.merkmale import Merkmale
    from lolcoach.kern.modus import Modus
    mo = Modus(konfig())

    def m(zeit, **kw):
        a = dict(zeit=zeit, tot=False, pos=(1000.0, 12000.0), bereich="lane_eigen", meine_lane="Top", lane_phase=True,
                 leben=0.9, leben_trend=0.0, im_kampf=False)
        a.update(kw)
        return Merkmale(**a)
    assert mo.neu(m(100)) == "LANE"
    assert mo.neu(m(101, bereich="basis_eigen")) == "LANE"          # Hysterese: erst nach 1,5 s
    assert mo.neu(m(102.6, bereich="basis_eigen")) == "BASIS"
    assert mo.neu(m(103, bereich="lane_eigen", im_kampf=True, gegner_im_radius=True)) == "KAMPF"   # sofort
    assert mo.neu(m(104, gegner_im_radius=True)) == "KAMPF"         # 3 s Nachlauf, solange er da ist
    assert mo.neu(m(104.5, gegner_im_radius=False)) == "KAMPF"      # Gegner weg: Kandidat LANE ...
    assert mo.neu(m(106.1, gegner_im_radius=False)) == "LANE"       # ... nach der Hysterese, nicht erst nach 3 s
    assert mo.neu(m(107, tot=True)) == "TOT"
    assert Modus(konfig()).neu(m(108, bereich=None)) is None         # Ort unbekannt: kein Modus, keine Sperre (4.3)
    # Sperre: Lane-Regel in der Basis stumm, Flash des Lane-Gegners in LANE gesprochen, sonst Dashboard
    b = N(lane=N(s=N(name="Sett")), jungler=N(s=N(name="Fiddle")), lane_nah=True)
    a = regeln.Ansage("Sett ist tot", regeln.WICHTIG, "lane_tot")
    assert sperre.entscheide("_lane_tot", a, "BASIS", b) == "stumm" and sperre.entscheide("_lane_tot", a, "LANE", b) == "sprechen"
    f = regeln.Ansage("Sett hat Flash benutzt", regeln.WICHTIG, "zauber:Sett:SummonerFlash")
    assert sperre.entscheide("_zauber", f, "LANE", b) == "sprechen"
    assert sperre.entscheide("_zauber", f, "UNTERWEGS", b) == "info"
    # Qualitaetsrunde 2, Entscheidung 3 Weg 3: spricht der Kern, sagt der Coach zu einem Flash nichts - der Timer (aus dem
    # Ping in der Anzeigetafel) steht nur auf dem Dashboard, auch der des Lane-Gegners
    assert all(sperre.entscheide("_zauber", f, m, b, kern_spricht=True) == "info" for m in ("LANE", "SEITE", "BASIS"))
    g = regeln.Ansage("Galio hat Flash benutzt", regeln.WICHTIG, "zauber:Galio:SummonerFlash")
    assert sperre.entscheide("_zauber", g, "LANE", b) == "info"      # nicht Lane-Gegner, nicht Jungler
    assert sperre.entscheide("_cs", regeln.Ansage("Minute 10", regeln.HINWEIS, "cs10"), "LANE", b) == "info"
    w = regeln.Ansage("Geh auf den Mid-Turm", regeln.WICHTIG, "plan:wohin")
    assert sperre.entscheide("_plan", w, "LANE", b) == "stumm" and sperre.entscheide("_plan", w, "BASIS", b) == "sprechen"
    assert sperre.entscheide("_lane_tot", a, None, b) == "stumm"      # ohne Modus: keine alte Regel (Pruefung E6)
    # Budget: 12 s zwischen zwei Ansagen ausser SOFORT; wer nur daran wartet, kommt danach noch, wenn er gilt
    plan = sprechplan.Sprechplan(stimme.Stumm())
    plan.neu([regeln.Ansage("Erste", regeln.WICHTIG, "a", zeit=100)])
    assert plan.takt(100) is not None
    plan.neu([regeln.Ansage("Zweite", regeln.WICHTIG, "b", zeit=103)])
    assert plan.takt(104) is None and plan.takt(111) is None      # Budget
    assert plan.takt(112.5).text == "Zweite"                         # sobald Platz ist - obwohl 9,5 s alt
    plan.neu([regeln.Ansage("Gefahr", regeln.SOFORT, "c", zeit=113)])
    assert plan.takt(113).text == "Gefahr"                           # SOFORT: kein Abstand
    # Claude: die letzte Ansage nur, wenn die Frage auf sie zeigt
    assert antworten.bezieht_sich_auf_ansage("Was meinst du damit?")
    assert antworten.bezieht_sich_auf_ansage("Warum hast du gesagt, dass ich back soll?")
    assert not antworten.bezieht_sich_auf_ansage("Was ist mein nächstes To-Do?")


def wachhund_meldet_datenluecke():
    """Buch 0, Kapitel 4.3: kommen keine Schnappschuesse, laeuft der Takt nicht - der Coach schwieg (Partie 102112,
    15:55-24:24). Der Wachhund nach Wanduhr sagt es einmal, meldet die Rueckkehr und traegt die Luecke ein; ist
    das Spiel zu, ist Stille das Ende der Partie und keine Luecke."""
    import json
    import tempfile
    import time
    from lolcoach import wachhund

    class Merker:
        def __init__(self):
            self.gesagt = []

        def sage(self, text, dringend=False, melde=None, noch_wahr=None):
            self.gesagt.append(text)
    with tempfile.TemporaryDirectory() as d:
        datei = Path(d) / "x_luecken.jsonl"
        sp = Merker()
        h = wachhund.Wachhund(sp, datei, grenze=0.2, spiel_da=lambda: True, takt=0.02)
        h.start()
        h.fuettern(time.time(), 955.0)
        time.sleep(0.5)                         # keine Daten mehr
        assert sp.gesagt == [wachhund.WEG], sp.gesagt
        h.fuettern(time.time(), 1464.0)         # wieder da
        time.sleep(0.1)
        h.halt()
        assert sp.gesagt == [wachhund.WEG, wachhund.WIEDER], sp.gesagt
        zeilen = [json.loads(z) for z in datei.read_text(encoding="utf-8").splitlines()]
        assert len(zeilen) == 1 and zeilen[0]["von_spielzeit"] == 955.0 and zeilen[0]["bis_spielzeit"] == 1464.0
        sp2 = Merker()
        h2 = wachhund.Wachhund(sp2, None, grenze=0.2, spiel_da=lambda: False, takt=0.02)
        h2.start()
        h2.fuettern(time.time(), 100.0)
        time.sleep(0.4)
        h2.halt()
        assert sp2.gesagt == [], "Spiel zu: keine Luecke"


def von_deiner_position_aus():
    """Live 27.09., Minute 25-38 (Basis, Mid): "Schieb die Welle in seinen Turm und geh back" in der eigenen Basis,
    "Drueckt jetzt die Tuerme" ohne Turm, "geh auf Sett", Sett auf der anderen Kartenseite, "Nehmt jetzt Baron"
    zehnmal. Jetzt ist deine Position der Anker: nicht auf der Lane keine Welle, Tuerme mit Namen und Weg, der
    Lane-Gegner nur, wenn er da ist, ein Team-Ruf hoechstens zweimal, solange keiner von euch hingeht."""
    from dataclasses import replace
    from lolcoach import bewertung, entscheider, komponist, regeln
    p = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")) if q.zeit > 1000)
    basis = bewertung.Bewertung(zeit=p.zeit, ich=p.ich, leben=1.0, gold=2400, partie=p, pos=(900.0, 900.0),
                                ort="in eurer Basis")
    basis.welle = (7, 1, 0.8, "ihr")                    # die Top-Welle schiebt - aber er steht in der Basis
    assert basis.in_basis and not basis.auf_lane and not basis.lane_nah
    saetze = [o.satz for o in entscheider.Entscheider().optionen(basis, False)]
    assert not any("Welle" in s or "seinen Turm" in s for s in saetze), saetze
    assert not any(o.name.startswith("back") for o in entscheider.Entscheider().optionen(basis, False))
    wohin = [s for s in saetze if s.startswith("Geh auf den ") or s.startswith("Geh ") and "Supervasallen" in s]
    assert wohin and "Sekunden von dir" in wohin[0], saetze
    zahl = komponist.zahlen(basis, ["Sett", "Galio"], 45, None, 5, 3)
    assert zahl.startswith("Drückt jetzt den ") and "Sekunden entfernt" in zahl, zahl
    # Team-Befehl nur, wenn du rechtzeitig dort bist (Buch 0, Schritt 2): 30 s Fenster, der Turm 37 s weg ->
    # kein "Drueckt jetzt", sondern dein eigenes Ziel
    zahl = komponist.zahlen(basis, ["Sett", "Galio"], 30, None, 5, 3)
    assert not zahl.startswith("Drückt") and "Geh auf den " in zahl and "Sekunden von dir" in zahl, zahl
    assert "DEINE POSITION: in eurer Basis" in basis.text() and "Deine Welle:" not in basis.text()
    # Team-Ruf: zweimal, dann nur noch, wenn einer von euch an der Grube steht
    rw = regeln.Regelwerk()
    rw.b = basis
    rufe = [rw._teamruf_frei("baron", replace(p, zeit=p.zeit + i * 30)) for i in range(4)]
    assert rufe == [True, True, False, False], rufe
    rw.b.pos = bewertung.einheiten(*bewertung.GRUBEN["baron"])
    assert rw._teamruf_frei("baron", replace(p, zeit=p.zeit + 150))


def afk_erkannt():
    """Live 27.09., 1:48: "Ist mein Nasus AFK?" - "Nein, er cleart im Dschungel", waehrend der Nasus-Bot seit
    Spielbeginn im Brunnen stand. Jetzt gerechnet: regungslos im Brunnen (das Icon springt dort am Kartenrand),
    Menschen ohne ein Item nach 1:30; wer laeuft, ist nicht AFK. Sofort beantwortet und von selbst gesagt."""
    from dataclasses import replace
    from lolcoach import antworten, lage, regeln
    p0 = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")) if q.zeit > 30)
    steher, laeufer = [s for s in p0.team(p0.mein_team) if s.name != p0.ich.name][:2]
    lb = lage.Lagebild()
    bx, by = lage.BRUNNEN[p0.mein_team]
    for i in range(0, 100):
        p = replace(p0, zeit=20.0 + i)
        wackeln = (0.005, -0.009, 0.012, 0.0)[i % 4]    # wie Nasus: 0.040/0.956 -> 0.025/0.968 -> 0.018/0.988
        lb.neu(p.zeit, [minimap.Sichtung(steher.champion_id, p0.mein_team, bx + wackeln, by - wackeln, 1.0),
                        minimap.Sichtung(laeufer.champion_id, p0.mein_team, 0.2 + i * 0.004, 0.8 - i * 0.004, 1.0)], p)
    assert p.zeit >= lage.AFK_AB
    grund = lage.afk(steher, p, lb)
    assert grund and "regungslos in eurer Basis" in grund, grund
    assert lage.afk(laeufer, p, lb) is None
    antwort = antworten.sofort(f"Ist mein {steher.champion} AFK?", p, lb)
    assert antwort.startswith(f"Ja. {steher.champion} ist AFK: steht seit"), antwort
    assert antworten.sofort(f"Ist {laeufer.champion} afk?", p, lb).startswith(f"Nein, {laeufer.champion} spielt")
    assert "AFK (berechnet, gilt)" in antworten.lage_text(p, lb)
    # ein Mensch ohne ein einziges Item nach 1:30 - auch ohne Minimap; ein Bot ohne Items nicht (Fiddlesticks-Bot)
    mensch = replace(laeufer, bot=False, items=())
    assert "kein einziges Item" in lage.afk(mensch, p, None)
    assert lage.afk(replace(laeufer, bot=True, items=()), p, None) is None
    # Gegner nie: die API zeigt ihre Items nicht, und Stufe/Items stehen nur so, wie er zuletzt gesehen wurde
    # (144655: Kha'Zix bis 3:34 "Stufe 1, 0 Items" - im ersten Moment auf der Karte Stufe 4; 1:30 hiess es live
    # "Kha'Zix ist AFK ... spiel deine Lane nach vorn", 1:57 war Riven tot)
    feind = replace(p.gegner()[0], bot=False, items=(), level=1, cs=0)
    assert lage.afk(feind, p, None) is None
    assert lage.afk(feind, replace(p, zeit=214.0), None) is None
    # von selbst: einmal je Spieler
    rw = regeln.Regelwerk()
    rw.lage = lb
    gesagt = list(rw._afk(p, p)) + list(rw._afk(p, p))
    assert len(gesagt) == 1 and gesagt[0].text.startswith(f"{steher.champion} ist AFK"), [a.text for a in gesagt]


def antwort_ab_dem_ersten_teilsatz():
    """Carlos 27.09.: "antwortet extrem spaet". Die Antwort geht ab dem ersten Teilsatz an die Stimme, nicht erst
    am Satzende, und ein vorgehaltener Claude-Prozess wird benutzt statt neu gestartet (Start 0,6-0,9 s)."""
    import io
    import json as js
    from lolcoach import llm
    assert llm.erster_teil("Ja, geh jetzt auf Poppy drauf, aber nur") == ("Ja, geh jetzt auf Poppy drauf,", "aber nur")
    assert llm.erster_teil("Nein, zurück")[0] is None                 # zu kurz fuer einen eigenen Teil
    assert llm.erster_teil("Du hast noch 1,5 Sekunden bis zum Flash")[0] is None   # Dezimalkomma
    assert llm.erster_teil("Zieh dich jetzt zum Turm zurück – Vi")[0] == "Zieh dich jetzt zum Turm zurück"

    class Lauf:   # tut so, als waere es `claude -p` mit stream-json
        gestartet = 0

        def __init__(self, *_a, **_k):
            Lauf.gestartet += 1
            self.stdin, self.returncode = io.StringIO(), 0
            stuecke = ["Ja, geh jetzt auf Poppy", " drauf, aber nur Poppy.", " Deine Ult ist da."]
            self.stdout = [js.dumps({"type": "stream_event", "event": {"type": "content_block_delta", "delta": {
                "type": "text_delta", "text": s}}}) + "\n" for s in stuecke]
            self.stdout.append(js.dumps({"type": "result", "result": "".join(stuecke)}) + "\n")

        def poll(self):
            return None

        def wait(self, timeout=None):
            return 0

        def kill(self):
            pass

    alt = llm._starte, llm._programm
    llm._starte, llm._programm = Lauf, (lambda: "claude")
    try:
        llm.vorhalten("sonnet", "S", "low")
        assert Lauf.gestartet == 1
        teile: list = []
        antwort = llm.frage_strom("Frage", teile.append, system="S", modell="sonnet", aufwand="low")
        assert Lauf.gestartet == 1, "vorgehaltener Prozess nicht benutzt"
        assert teile == ["Ja, geh jetzt auf Poppy drauf,", "aber nur Poppy.", "Deine Ult ist da."], teile
        assert antwort.startswith("Ja, geh")
        llm.frage_strom("Frage", teile.append, system="S", modell="sonnet", aufwand="low")
        assert Lauf.gestartet == 2    # kein Vorrat mehr: neu gestartet
    finally:
        llm._starte, llm._programm = alt
        llm._VORRAT.clear()


_FESTHALTEN: list = []   # Zeiger, die erst beim Beenden sterben duerfen (dann gibt comtypes nichts mehr frei)


def kamera_gibt_nur_einmal_frei():
    """dxcam gab die Staging-Textur zweimal frei - von Hand und spaeter noch einmal durch den Garbage Collector -,
    und der Coach baute sie ~25-mal je Sekunde neu: 26./27.09.2026 viermal Zugriffsverletzung in _ctypes.pyd.
    Jetzt: eine Textur je Ausschnittgroesse, und nach release() + gc.collect() fehlt keine Referenz."""
    import ctypes
    import gc
    try:
        from comtypes import IUnknown
        from lolcoach import lage
    except ImportError:
        return
    k = lage._Kamera()
    if k._dx is None:
        return   # ohne Desktop-Duplizierung (kein Bildschirm) gibt es nichts zu pruefen
    for box in [(0, 0, 200, 100), (0, 0, 100, 200), (0, 0, 200, 100), (0, 0, 100, 200)]:
        k.hole(box)
    assert sorted(k._flaechen) == [(100, 200), (200, 100)], sorted(k._flaechen)
    s = k._flaechen[(200, 100)]
    assert (s.width, s.height) == (200, 100), (s.width, s.height)
    p = ctypes.cast(ctypes.cast(s.texture, ctypes.c_void_p).value, ctypes.POINTER(IUnknown))
    _FESTHALTEN.append(p)
    for _ in range(3):
        p.AddRef()      # Schutzreferenzen: nichts wird wirklich zerstoert, solange wir zaehlen
    s.release()
    gc.collect()
    n = p.AddRef() - 1
    p.Release()
    for _ in range(n):
        p.Release()
    assert n == 3, f"{3 - n} Freigabe(n) zu viel"


def minimap_groesse_aus_der_einstellung():
    """Partie 27.09., 13:03: MinimapScale 2,91 statt 1,5 - der Coach schnitt weiter die alte 570er-Karte aus und
    erkannte in 1629 von 1717 Bildern niemanden ("Ich erkenne auf der Minimap gerade niemanden ..."). Jetzt liest
    er die Groesse aus der game.cfg; Minimap, Icons und Mitspieler-Leiste wachsen mit. Bild: Ecke eines
    1600x900-Spielbilds derselben Partie."""
    import tempfile
    cfg = Path(tempfile.mkdtemp()) / "game.cfg"
    cfg.write_text("[General]\nMinimapScale=9\n[HUD]\nMinimapScaleSpectator=1.0000\nMinimapScale=2.9100\n",
                   encoding="utf-8")
    assert minimap.eingestellt(cfg) == 2.91 and minimap.eingestellt(cfg.with_name("fehlt.cfg")) is None
    k = minimap.groesse(2.91)
    assert minimap.groesse(1.5) == 1.0 and round(570 * k) == 764
    assert minimap.kartenrechteck(3840, 2160, k) == (3049, 1367, 3813, 2131)    # Raender 27/29 bleiben
    champions = [("Riven", "ORDER"), ("Pantheon", "ORDER"), ("Ryze", "ORDER"), ("Jinx", "ORDER"), ("Braum", "ORDER"),
                 ("Ornn", "CHAOS"), ("Sejuani", "CHAOS"), ("Olaf", "CHAOS"), ("Gnar", "CHAOS"), ("Braum", "CHAOS")]
    bild = cv2.imread(str(HIER / "minimap_gross.jpg"))
    ox, oy = 1600 - bild.shape[1], 900 - bild.shape[0]

    def karte(k_):
        kl, ko, kr, ku = minimap.kartenrechteck(1600, 900, k_)
        return bild[ko - oy:ku - oy, kl - ox:kr - ox]
    assert len(minimap.finde(karte(1.0), champions)) <= 1          # so war es: fast blind
    gefunden = [s.champion_id for s in minimap.finde(karte(k), champions)]
    assert {"Riven", "Pantheon", "Jinx", "Olaf"} <= set(gefunden) and gefunden.count("Braum") == 2, gefunden
    v = minimap.Verfolger(champions, hoehe=2160)                    # richtet sich nach der Karte, nicht dem Aufruf
    sichtungen, _ = v.bild(karte(k), 1.0)
    assert len(sichtungen) >= 6 and v.hoehe == minimap.massstab(318), (v.hoehe, sichtungen)
    hx0, hy0, hx1, hy1 = hud.bereich(1600, 900, k)
    m = hud.lies(bild[hy0 - oy:hy1 - oy, hx0 - ox:hx1 - ox], 900, k)
    assert all(abs(a - b) <= 0.06 for a, b in zip([x.leben for x in m], [0.73, 0.95, 0.63, 0.34])), m
    assert [x.ult_bereit for x in m] == [False, True, False, True], m
    assert hud.bereich(3840, 2160, 1.0) == hud.bereich(3840, 2160)   # ohne Faktor wie vermessen


def minimap_farben_relativ():
    """Die Minimap faerbt relativ: dein Team blau, der Gegner rot (echte Partie 140253, Riven Mid auf der roten Seite:
    die eigenen Vasallen galten als seine, die Platten-Ziffern wurden in der falschen Farbe gesucht). Im Coach heisst
    `blau` aber Team ORDER - auf der roten Seite werden die Farben getauscht."""
    from types import SimpleNamespace
    from lolcoach import lage, platten
    from lolcoach.bewertung import TUERME
    punkte = [("blau", 0.66, 0.34), ("blau", 0.64, 0.36), ("blau", 0.62, 0.38), ("rot", 0.55, 0.45)]   # Mid
    z = welle.zustaende(punkte, "CHAOS")["Mid"]
    assert (z.blau, z.rot) == (1, 3), z                  # drei eigene (CHAOS) Vasallen, ein gegnerischer
    assert z.worte("CHAOS").startswith("eure 3 gegen seine 1"), z.worte("CHAOS")
    assert (welle.zustaende(punkte)["Mid"].blau, welle.zustaende(punkte)["Mid"].rot) == (3, 1)   # blaue Seite
    farben = []
    alt = platten.lies
    try:
        platten.lies = lambda karte, team, gx, gy: (farben.append(team), (None, 0.0))[1]
        platten.Plattenleser().lies_karte(None, mein_team="CHAOS")
    finally:
        platten.lies = alt
    tuerme = list(TUERME)
    assert all(f != t[0] for f, t in zip(farben, tuerme)), "CHAOS-Tuerme sind fuer die rote Seite blau"
    sp = [SimpleNamespace(champion_id="Braum", team="ORDER", name="a"), SimpleNamespace(champion_id="Braum",
                                                                                         team="CHAOS", name="b")]
    p = SimpleNamespace(spieler=sp, mein_team="CHAOS")
    assert lage.zuordnen(minimap.Sichtung("Braum", "ORDER", 0.5, 0.5, 1.0), p).team == "CHAOS"   # blauer Ring


def wellenleser_ring_und_nachbar():
    """welle.py blendet an einem Champion-Icon nur Icon und Ring aus (gemessen an 140253: Ring bei 30-33 px, Icon-Radius
    32 px bei 764 px Kante). Ein Stueck Ring zaehlt nie als Vasall - vorher lagen 14 Punkte im Ring -, ein Vasall direkt
    neben dem Ring zaehlt (vorher fiel er in die Raute um die Icon-Mitte)."""
    import numpy as np
    seite = 764
    karte = np.full((seite, seite, 3), 40, np.uint8)
    mitte = (380, 380)
    blau = (255, 140, 40)                                      # BGR, im Farbbereich von welle.py
    cv2.ellipse(karte, mitte, (31, 31), 0, 38, 52, blau, 5)     # ein kompaktes Ringstueck auf der Diagonale
    cv2.circle(karte, (380 + 38, 380), 5, blau, -1)             # ein Vasall 38 px neben der Icon-Mitte (Achse)
    cv2.circle(karte, (380 - 29, 380 + 29), 5, blau, -1)        # ... und einer diagonal, 41 px
    leser = welle.Wellenleser()
    for _ in range(25):                                         # erst leere Karten: die Turm-Maske lernt, was steht
        leser.punkte(np.full((seite, seite, 3), 40, np.uint8))
    punkte = leser.punkte(karte, [(mitte[0] / seite, mitte[1] / seite)])
    abstaende = sorted(round(((x * seite - 380) ** 2 + (y * seite - 380) ** 2) ** 0.5) for _, x, y in punkte)
    assert len(punkte) == 2 and all(d >= 38 for d in abstaende), abstaende


def bestaetigung_back_im_fenster():
    """Buch 3, 5 / 7.2: Crash an seinem Turm -> Recall -> Basis. Der Kern lobt einmal, vor dem Kauf-Satz ("Sauber:
    Welle drin, dann back."), und merkt es als Staerke fuers Review. Ohne Crash davor kein Lob."""
    from lolcoach.kern import Kern, testlage
    lane = {"zeit": "6:10", "ich": {"level": 6, "leben": 0.7, "gold": 1350},
            "welle": {"zustand": "GECRASHT_BEI_IHM", "unsere": 5, "ihre": 0, "front": 0.66},
            "kanone_in": 50, "lane_gegner": {"level": 6, "abstand": 2600},
            "jungler": {"p_meine_seite": 0.3, "seit": 30}, "kauf": {"lohnt": True}}
    basis = {"zeit": "6:24", "modus": "BASIS", "ich": {"level": 6, "leben": 1.0, "gold": 1350},
             "inventar": {"kontrollauge": False, "frei": 5}, "kanone_in": 30, "kauf": {"lohnt": True}}

    def lauf(welle: str) -> tuple[list, Kern]:
        k = Kern(stellung="neu")
        for zeit in ("6:10", "6:14"):                   # Crash, dann steht er im Kanal
            e = dict(lane, zeit=zeit, welle=dict(lane["welle"], zustand=welle))
            m, modus = testlage.bauen(e)
            k.schritt(m, modus)
        m, modus = testlage.bauen(basis)                 # 8 s spaeter im Brunnen: Recall, kein Tod
        return k.schritt(m, modus), k
    ansagen, k = lauf("GECRASHT_BEI_IHM")
    assert ansagen and ansagen[0].text.startswith("Sauber: Welle drin, dann back.") and "Kauf" in ansagen[0].text, \
        [a.text for a in ansagen]
    assert k.staerken and k.staerken[0][1].startswith("Sauber"), k.staerken
    ansagen, k = lauf("ZU_DIR")                          # die Welle war nicht drin: kein Lob
    assert ansagen and not ansagen[0].text.startswith("Sauber"), [a.text for a in ansagen]
    assert not k.staerken


def nur_gefahr_bricht_saetze_ab():
    """Partie 144655: live brachen 11 von 18 Saetzen nach ein, zwei Woertern ab - die Kern-Gefahr "Bleib an deinem
    Top-Tier-1-Turm" 0,3 s nach dem Start, weil ihr Plan-Schritt im naechsten Takt erledigt war, danach "Ach nee: ...".
    Jetzt bricht die eigene Pruefung keinen Satz ab, eine andere Ansage nur, wenn sie eine Gefahr ist - gemessen mit
    der Stimme des Nachspielens (spricht in Spielzeit wie live)."""
    from lolcoach import regeln, sprechplan, stimme
    st = stimme.Nachgespielt(sprechplan.ZEICHEN_PRO_SEKUNDE)
    plan = sprechplan.Sprechplan(st)

    def takte(*zeiten):
        for t in zeiten:
            st.takt(t)
            plan.takt(t)
    gilt = [True]
    a = regeln.Ansage("Bleib an deinem Top-Tier-1-Turm: Gangplank und Kha'Zix kommen.", regeln.SOFORT,
                      "kern:ZURUECK", zeit=205.9, sperre=0.0, thema="gefahr", pruefe=lambda: gilt[0])
    plan.neu([a])
    takte(205.9)
    assert st.beschaeftigt
    gilt[0] = False                              # naechster Takt: der Plan-Schritt ist erledigt
    plan.neu([regeln.Ansage("Setz ein Ward am Pixel-Bush oben.", regeln.WICHTIG, "ward:x", zeit=206.5, gueltig=20)])
    takte(206.2, 206.5, 207.0, 208.0, 209.0, 210.0, 211.0)
    assert not st.abbrueche and a.ganz is True, (st.abbrueche, a.ganz)
    e = regeln.Ansage("Raus zu deinem Top-Tier-1-Turm: Gangplank kommt.", regeln.SOFORT, "kern:ZURUECK", zeit=212.0,
                      sperre=0.0, thema="gefahr")
    plan.neu([e])
    takte(212.0)
    assert not e.text.startswith("Ach nee"), e.text          # der Kern-Satz davor war nicht falsch
    # eine Gefahr darf einen laufenden Satz abbrechen
    takte(230.0)
    c = regeln.Ansage("C" * 120, regeln.WICHTIG, "cs5", zeit=240.0, gueltig=40)
    plan.neu([c])
    takte(240.0)
    plan.neu([regeln.Ansage("Kha'Zix kommt auf dich zu.", regeln.SOFORT, "anlauf:x", zeit=241.0, gueltig=3)])
    takte(241.0)
    assert c.ganz is False and st.abbrueche and st.abbrueche[-1][2].startswith("verdraengt"), st.abbrueche


def zauber_timer_auf_dem_dashboard():
    """Carlos 27.09. (144655, 10:11): "Ich sehe keinen einzigen Flash-Timer auf dem Dashboard." Der Weg vom
    Lagebild zum Dashboard stimmt (nachgespielt mit dem Code der Partie: Gangplanks Flash 1:56-6:56 stand im
    Gegner-Kasten) - bekannt war in 9,5 Minuten nur dieser eine. Hier: ein Flash-Timer von der Minimap und eine Ult
    aus dem Chat kommen im Dashboard an (die Ult kam bis 27.09. nie an), abgelaufene nicht mehr."""
    from dataclasses import replace
    from lolcoach import dashboard, lage
    p = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")) if q.zeit > 400)
    g = p.gegner()[0]
    lb = lage.Lagebild()
    lb.zauber.benutzt(g, "SummonerFlash", p.zeit - 20, "Minimap")
    lb.zauber.benutzt(replace(g, level=max(6, g.level)), "R", p.zeit - 10, "Chat", zurueck=p.zeit + 50)
    z = dashboard.zustand_json(p, lb)
    weg = {x["name"]: x["rest"] for s in z["spieler"] if s["name"] == g.name for x in s["zauber_weg"]}
    assert "Flash" in weg and 250 <= weg["Flash"] <= 300 and weg.get("Ult") == 50, weg
    z = dashboard.zustand_json(replace(p, zeit=p.zeit + 400), lb)
    assert not any(s["zauber_weg"] for s in z["spieler"]), "abgelaufene Timer verschwinden"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for test in (item_namen, wellen, rueckblick_passt_zum_leben, mitspieler_leiste, teleport_timer, kuerzen_und_orte, profil_ueber_partien,
                 zauber_im_briefing, recalls_im_verlauf, sprechbar, matchup_zeilen, chat_zeitstempel, akte_teile, chat_pings, eigene_tasten,
                 aufnahme_fortsetzen, bildschirm_momente, bewertung_und_plan, denkkette, flash_auf_dem_bildschirm, brunnen_nach_recall_und_tod, live_partie_2121, combo_rechnung,
                 platten_lesen, teleport_von_der_minimap, lebensbalken_lesen, verzoegerung_bis_zum_ohr,
                 faehigkeiten_aus_spieldaten, icon_in_der_brunnen_ecke, stimme_haengt_nicht, sprechtaste_ist_stummtaste,
                 satz_wird_zu_ende_gesagt_dann_korrigiert, kein_zweites_geh_zurueck, stimme_spielt_ab_dem_ersten_stueck,
                 konter_kauf_ohne_eigenes, stimme_ueberlebt_audiofehler, eigene_position_aus_dem_kamerarahmen,
                 satzanfaenge_vorgewaermt, wecker_bei_sprung_und_gegner_nah, baron_aeltester_inhibitor,
                 minimap_blind_wird_gesagt, kamera_gibt_nur_einmal_frei, antwort_ab_dem_ersten_teilsatz, afk_erkannt,
                 von_deiner_position_aus, wachhund_meldet_datenluecke, modus_sperre_budget,
                 sofort_back_und_objective, minimap_groesse_aus_der_einstellung,
                 bestaetigung_back_im_fenster, minimap_farben_relativ, wellenleser_ring_und_nachbar,
                 nur_gefahr_bricht_saetze_ab, zauber_timer_auf_dem_dashboard):
        test()
        print(f"{test.__name__} OK")
