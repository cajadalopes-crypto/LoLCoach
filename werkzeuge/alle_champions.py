"""Alle Champions durch die Kampfrechnung: jeder als dein Lane-Gegner UND als dein eigener Champion - Steckbrief,
Ult-Abklingzeit, Lexikon-Tipps, Lane-Kurve, Faehigkeitsschaden (seiner auf dich, deiner auf ihn), Kampf-Urteil und
Fenster-Satz. Meldet jeden Champion, bei dem etwas fehlt, None liefert oder unplausibel ist.

    python werkzeuge/alle_champions.py
"""
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
from lolcoach import aufzeichnung, bewertung, champions, combo, ddragon, denker, wissen, zustand  # noqa: E402

HIER = Path(__file__).resolve().parent.parent / "tests"


def pruefen() -> dict[str, list[str]]:
    p = next(q for q in map(zustand.partie, aufzeichnung.lies(HIER / "botspiel_riven_1.jsonl.gz")) if q.zeit > 400)
    g0, j = p.gegenueber(), p.jungler(zustand.gegenteam(p.mein_team))
    kurve = wissen.lade("lane_kurve")["kurve"]
    alle = ddragon.champions()
    fehler: dict[str, list[str]] = {}

    def melde(cid, was):
        fehler.setdefault(cid, []).append(was)

    for cid, d in sorted(alle.items()):
        name = d.get("name", cid)
        if not champions.steckbrief(cid):
            melde(cid, "kein Steckbrief")
        # Ult-Abklingzeit: Formwechsel (Elise, Jayce, Nidalee), Udyr (6 Raenge), kurze Ults (Kassadin, Anivia, Teemo)
        # sind echte Werte aus Data Dragon - geprueft wird nur, dass es sie gibt und keine negativ ist
        r = champions.ult_cooldown(cid)
        if not r or any(x < 0 for x in r):
            melde(cid, f"Ult-Abklingzeit {r}")
        if not denker._tipps(cid):
            melde(cid, "keine Konter-Tipps im Lexikon")
        if cid not in kurve:
            melde(cid, "keine Lane-Kurve")
        # er als Lane-Gegner, Level 9, 2 Items
        g = replace(g0, champion_id=cid, champion=name, level=9, items=(3071, 3047), item_gold=3000)
        ich = replace(p.ich, level=9, items=(6692, 3047), item_gold=3000)
        werte = dict(p.werte)
        try:
            s_er = combo.gegner_schaden(g, werte)
            if s_er is None or not 50 <= s_er <= 6000:
                melde(cid, f"sein Schaden auf dich unplausibel: {s_er}")
        except Exception as e:
            melde(cid, f"sein Schaden: {type(e).__name__}: {e}")

        def gl(s, **kw):
            a = dict(s=s, sichtbar=True, seit=0.0, ort="oben", abstand=700.0, ankunft=2.0, tempo=345.0, flash=None,
                     ult=None, level_vorsprung=s.level - ich.level, gold_vorsprung=s.item_gold - ich.item_gold)
            a.update(kw)
            return bewertung.GegnerLage(**a)
        try:
            b = bewertung.Bewertung(zeit=900, ich=ich, leben=0.9, gold=800, pos=(1500, 12500), ult=True,
                                    zweiter=("SummonerDot", 0.0), partie=p)
            b.lane = gl(g, leben=0.5)
            b.jungler = gl(j, sichtbar=False, seit=20.0, ort="in seinem unteren Jungle", abstand=9000.0, ankunft=25.0)
            b.gegner = [b.lane, b.jungler]
            u = denker.urteil(b)
            if u is None:
                melde(cid, "kein Kampf-Urteil")
            else:
                satz = denker.fenster_satz(b, u)
                if not satz or "None" in satz or "{" in satz:
                    melde(cid, f"Fenster-Satz kaputt: {satz}")
        except Exception as e:
            melde(cid, f"Kampf-Urteil: {type(e).__name__}: {e}")
        # er als DEIN Champion (Carlos spielt auch andere): dein Combo auf einen Gegner
        try:
            ich2 = replace(ich, champion_id=cid, champion=name)
            b2 = bewertung.Bewertung(zeit=900, ich=ich2, leben=0.9, gold=800, pos=(1500, 12500), ult=True,
                                     zweiter=("SummonerDot", 0.0), partie=p)
            b2.lane = gl(g0, leben=0.5)
            b2.jungler = b.jungler
            b2.gegner = [b2.lane, b2.jungler]
            u2 = denker.urteil(b2)
            if u2 is None:
                melde(cid, "als eigener Champion kein Kampf-Urteil")
        except Exception as e:
            melde(cid, f"als eigener Champion: {type(e).__name__}: {e}")
    return fehler


if __name__ == "__main__":
    f = pruefen()
    n = len(ddragon.champions())
    for cid, was in f.items():
        print(f"{cid:14} {'; '.join(was)}")
    print(f"\n{n} Champions, {n - len(f)} ohne Befund")
