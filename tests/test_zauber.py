"""Zauber-Timer: Chat-Pings und Flash-Spruenge -> Timer -> Ansagen und Antworten.

Grundlage ist die dritte echte Partie (Riven gegen Urgot, Bots), in die zwei
Ereignisse eingespielt werden - wie sie der Beobachter live liefern wuerde.

    python tests/test_zauber.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import antworten, aufzeichnung, lage, minimap, regeln, sprechplan, stimme, zauber, zustand  # noqa: E402

PARTIE = Path(__file__).parent / "botspiel_riven_2.jsonl.gz"   # Riven gegen Shen, Vi, Brand, Varus, Rakan


def chat_formate():
    p = zustand.partie(list(aufzeichnung.lies(PARTIE))[600])
    faelle = {
        "[Team] Schizoid Nevir (Riven): Shen Blitz": ("Shen", "SummonerFlash"),
        "[12:34] Lee Sin (Lee Sin): vi flash": ("Vi", "SummonerFlash"),
        "Schizoid Nevir (Riven): brand zünden": ("Brand", "SummonerDot"),
        "[Team] Diana (Diana): Rakan Blitz 16:40": ("Rakan", "SummonerFlash"),
        "[Team] Riven: Schen Blitz": ("Shen", "SummonerFlash"),          # Texterkennung/Tippfehler
        "[Team] Shen (Shen): Ich komme": None,                           # kein Zauber
        "[Alle] Urgot: gg": None,
    }
    for zeile, erwartet in faelle.items():
        treffer = zauber.aus_chat(zeile, p)
        if erwartet is None:
            assert not treffer, (zeile, treffer)
        else:
            assert treffer and (treffer[0][0].champion, treffer[0][1]) == erwartet, (zeile, treffer)
    assert zauber.aus_chat("[Team] Diana (Diana): Rakan Blitz 16:40", p)[0][2] == 1000.0
    # Eingebaute Client-Nachricht (Klick auf den gegnerischen Zauber): "Spieler (Champion): Ziel Zaubername",
    # im deutschen Client mit den Namen aus Data Dragon
    for zeile, erwartet in {"Schizoid Nevir (Riven): Shen Entzünden": ("Shen", "SummonerDot"),
                            "Schizoid Nevir (Riven): Vi Teleportation": ("Vi", "SummonerTeleport"),
                            "Diana (Diana): Brand Läuterung": ("Brand", "SummonerBoost"),
                            "Diana (Diana): Varus R": ("Varus", "R")}.items():
        treffer = zauber.aus_chat(zeile, p)
        assert treffer and (treffer[0][0].champion, treffer[0][1]) == erwartet, (zeile, treffer)
    # Ult-Pings: "Shen Ult" / "shen r"; ein einzelnes r in einem langen Satz ist keine Ult
    assert [(s.champion, z) for s, z, _ in zauber.aus_chat("[Team] Riven: Shen Ult", p)] == [("Shen", "R")]
    assert [(s.champion, z) for s, z, _ in zauber.aus_chat("[Team] Riven: shen r", p)] == [("Shen", "R")]
    assert not zauber.aus_chat("[Team] Riven: shen geht jetzt r unten mit lee", p)
    shen = next(s for s in p.spieler if s.champion == "Shen")
    assert zauber.cooldown("R", shen) in (200.0, 180.0, 160.0), zauber.cooldown("R", shen)
    print("Chat-Formate OK")


def kette():
    werk, plan = regeln.Regelwerk(), sprechplan.Sprechplan(stimme.Stumm())
    lb = lage.Lagebild()
    sicht = lage.SichtAusBildern.aus_cache(PARTIE.with_name("botspiel_riven_2_bilder"))
    eingespielt = False
    antwort_vorher = antwort_nachher = None
    for w, d in aufzeichnung.lies_mit_zeit(PARTIE):
        p = zustand.partie(d)
        for wb, s in sicht.zwischen(w, lage.champions(p)):
            lb.neu(p.zeit - (w - wb), s, p)
        if 300 <= p.zeit and not eingespielt:
            eingespielt = True
            antwort_vorher = antworten.sofort("Hat Shen Flash?", p, lb)
            # Chat-Ping, ein Sprung von Brand (kein eigener Dash: Flash) und einer von Vi (Q-Dash: kein Timer,
            # Qualitaetsrunde 2 Weg 1); die Rakan-Zeile ohne Zauber zaehlt nicht
            vi = p.jungler("CHAOS")
            brand = next(s for s in p.gegner() if s.champion_id == "Brand")
            stempel = f"{int(p.zeit // 60):02d}:{int(p.zeit % 60):02d}"
            neu = lb.ereignisse(lambda wb: p.zeit - (w - wb), [
                ("chat", w, f"{stempel} Schizoid Nevir (Riven): Shen Blitz"),
                ("chat", w, f"{stempel} Schizoid Nevir (Riven): Shen Blitz"),     # doppelt: nur ein Timer
                ("chat", w, f"{stempel} Diana (Diana): Rakan komm"),
                ("chat", w, "01:10 Schizoid Nevir (Riven): Rakan hat Blitz benutzt"),   # alt, neu eingeblendet
                ("sprung", minimap.Sprung(vi.champion_id, None, w, 0.027, 0.6, 0.4)),
                ("sprung", minimap.Sprung(brand.champion_id, None, w, 0.027, 0.5, 0.5)),
            ], p)
            assert sorted(t.champion for t in neu) == ["Brand", "Shen"], neu
            assert lb.zauber.fehlt(vi, "SummonerFlash", p.zeit) is None
            antwort_nachher = antworten.sofort("Hat Shen Flash?", p, lb)
        plan.neu(werk.pruefe(p, lb))
        plan.takt(p.zeit)
        if p.zeit > 700:
            break
    texte = [(round(a.gesprochen), a.text) for a in plan.gesagt]
    assert any(300 <= t <= 315 and "Shen hat Flash benutzt" in x for t, x in texte), texte
    assert not any("Vi hat Flash benutzt" in x for t, x in texte), texte
    assert "vermutlich bereit" in antwort_vorher, antwort_vorher
    assert "Flash ist noch" in antwort_nachher and "Minuten" in antwort_nachher, antwort_nachher
    print("Kette OK:", antwort_nachher)
    for t, x in texte:
        if "Flash" in x:
            print(f"   {t // 60}:{t % 60:02d} {x}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    chat_formate()
    kette()
