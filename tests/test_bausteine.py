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
    for gleich in ("Mid-Lane", "Level 6", "5:00", "Tri-Bush", "80 %", "KDA 27/6/4", "5 sind weg"):
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


def chat_zeitstempel():
    # Partie 4: "04:48 Riven (Riven): Tryndamere hat Blitz benutzt", gelesen um 4:51
    assert zauber.chat_zeit("04:48 Riven (Riven): Tryndamere hat Blitz benutzt", 291.0) == 288.0
    assert zauber.chat_zeit("04:48 Riven (Riven): Tryndamere hat Blitz benutzt", 400.0) == 400.0   # zu alt
    assert zauber.chat_zeit("Riven (Riven): Urgot Blitz", 291.0) == 291.0                          # ohne Stempel


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


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for test in (item_namen, wellen, mitspieler_leiste, teleport_timer, kuerzen_und_orte, profil_ueber_partien,
                 zauber_im_briefing, recalls_im_verlauf, sprechbar, matchup_zeilen, chat_zeitstempel):
        test()
        print(f"{test.__name__} OK")
