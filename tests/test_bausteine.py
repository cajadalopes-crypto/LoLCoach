"""Kleine Bausteine: Item-Namen, Wellen, Mitspieler-Leiste, Teleport-Timer, Kuerzen, Orte.

    python tests/test_bausteine.py
"""
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
    assert "Zurück zum Turm" in satz and "35 Prozent Leben" in satz and "3 Sekunden" in satz, satz
    # Sofort-Antwort aus dem Entscheider, Kauf-Frage bleibt bei Claude
    plan = entscheider.Option("druck", "Spiel auf Shen: du bist 2 Level vorn.", 100, 2)
    lb = S(entscheider=S(aktuell=plan))
    assert antworten.sofort("Was soll ich jetzt machen?", p, lb) == plan.satz
    assert antworten.sofort("Was soll ich kaufen?", p, lb) is None
    assert komponist.sek(105) == "1 Minute 45" and komponist.sek(1) == "1 Sekunde"
    # Todeszeit (Wiki Death): L9 @20:00 = 29,2 s, L18 @55:00 = 78,75 s
    assert round(bewertung.todeszeit(9, 1200), 1) == 29.2 and round(bewertung.todeszeit(18, 3300), 2) == 78.75
    b.tod_kostet, b.objective = 45.0, ("baron", 30.0)
    assert komponist.todespreis(b) == "ein Tod kostet jetzt 45 Sekunden, Baron in 30 Sekunden"
    # Kaufplan aus dem Lexikon-Build: Riven Kern Stiefel -> Axiombogen -> Endloser Hunger -> Tanz des Todes
    from lolcoach import kaufplan
    assert kaufplan.plan("Riven", (1055,), 1400).satz() == "reicht für den Brutalisierer"
    assert kaufplan.plan("Riven", (1055, 3158), 2800).satz() == "reicht für Axiombogen"
    assert kaufplan.plan("Riven", (1055, 3158), 1000).satz() == "noch 50 bis Caulfields Kriegshammer"


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


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for test in (item_namen, wellen, mitspieler_leiste, teleport_timer, kuerzen_und_orte, profil_ueber_partien,
                 zauber_im_briefing, recalls_im_verlauf, sprechbar, matchup_zeilen, chat_zeitstempel, akte_teile, chat_pings, eigene_tasten,
                 aufnahme_fortsetzen, bildschirm_momente, bewertung_und_plan, platten_lesen):
        test()
        print(f"{test.__name__} OK")
