"""Objective-Eichung (Buch 6, Kapitel 10): Toetungszeiten und das Urteil gegen den Ausgang.

1. Toetungszeit: fuer jedes DragonKill, HordeKill (Larven), HeraldKill und BaronKill eures Teams - Beginn ist der
   erste Zeitpunkt nach dem Spawn, ab dem >= 1 von euch <= eichung_nah (700) an der Grube steht und bleibt; Dauer =
   Kill - Beginn. Beim Drachen mit der Rache bereinigt (x (1 - Rache)), sonst zaehlt sie doppelt. Gruppiert nach
   Objective, n (Median der Anwesenden) und Spalte, als Median mit Anzahl. Die Tabelle aendert sich nur mit >= 3
   Faellen.
2. Urteil gegen Ausgang: eine Probe je Versuch, an dessen Beginn (auch >= 2 von euch <= eichung_nah ohne Kill).
   Ausgang 1: euer Team nimmt es in 60 s ohne eigenen Tod. Brier gegen die Grundrate; Soll < 0,20 und besser als die
   Grundrate. puffer_s, steal_* und die Schwellen aendern sich nur mit >= 30 Versuchen.
3. Nur echte Partien: eine Aufnahme mit `bots = true` in tests/szenarien/<stamm>.toml wird uebersprungen.

    python werkzeuge/objective_eichung.py 2026-09-27_133930 2026-09-27_140253 ... [--json <datei>]
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import nachspielen as ns  # noqa: E402

from lolcoach.bewertung import abstand  # noqa: E402
from lolcoach.kern import konfig  # noqa: E402
from lolcoach.kern import objective as obj  # noqa: E402
from lolcoach.kern.modi.objective import spawn_zeit  # noqa: E402

EVENT = {"drache": "DragonKill", "aeltester": "DragonKill", "larven": "HordeKill", "herold": "HeraldKill",
         "baron": "BaronKill"}
AUSGANG_S = 60.0
SZENARIEN = Path(__file__).resolve().parent.parent / "tests" / "szenarien"


def bot_partie(stamm: str) -> bool:
    f = SZENARIEN / f"{stamm}.toml"
    if not f.exists():
        return False
    return bool(tomllib.loads(f.read_text(encoding="utf-8")).get("bots"))


def partie_messen(stamm: str, cfg: dict) -> tuple[list, list]:
    """(Toetungen, Versuche) einer Partie."""
    nah = cfg["objective"]["eichung_nah"]
    laeufe: dict = {}          # (schl, spawn) -> {"beginn", "n": [..], "probe", "max_n", "aktiv"}
    fertig = []                # abgeschlossene Laeufe (schl, spawn, beginn, ende, n-Liste, probe, max_n)
    letzte = {"p": None}

    def beim_takt(p, werk, kern, plan):
        letzte["p"] = p
        m = kern.m
        if m is None or m.b is None:
            return
        b = m.b
        leute = ([b.pos] if b.pos is not None and not m.tot else []) + [wo for s, wo, *_ in b.mitspieler
                                                                           if wo is not None and not s.tot]
        for o in m.objectives:
            if not o.lebt:
                continue
            key = (o.schl, spawn_zeit(m, o))
            n = sum(1 for wo in leute if abstand(wo, o.pos) <= nah)
            lauf = laeufe.get(key)
            if n >= 1:
                if lauf is None or not lauf["aktiv"]:
                    u = obj.urteil_von(m, o, cfg)
                    laeufe[key] = lauf = {"beginn": p.zeit, "n": [], "probe": (u.p_erfolg, u.n, u.grund),
                                          "max_n": 0, "aktiv": True}
                lauf["n"].append(n)
                lauf["max_n"] = max(lauf["max_n"], n)
                lauf["zuletzt"] = p.zeit
            elif lauf is not None and lauf["aktiv"] and p.zeit - lauf.get("zuletzt", p.zeit) > 3.0:
                lauf["aktiv"] = False
                fertig.append((key[0], key[1], lauf))

    ns.durchspielen(ns.pfad_zu(stamm), beim_takt=beim_takt)
    p = letzte["p"]
    if p is None:
        return [], []
    for key, lauf in laeufe.items():
        if lauf["aktiv"]:
            fertig.append((key[0], key[1], lauf))
    mein = p.mein_team
    tote_eigene = [e.zeit for e in p.kills_von("ChampionKill") if e.opfer is not None and e.opfer.team == mein]
    toetungen, versuche = [], []
    for schl, spawn, lauf in fertig:
        t0 = lauf["beginn"]
        kills = [e for e in p.kills_von(EVENT[schl]) if t0 <= e.zeit <= t0 + 180
                 and (schl != "aeltester" or e.daten.get("DragonType") == "Elder")
                 and (schl != "drache" or e.daten.get("DragonType") != "Elder")]
        unser = [e for e in kills if e.team == mein]
        if unser:
            ende = unser[-1].zeit if schl == "larven" else unser[0].zeit
            dauer = ende - t0
            if schl in ("drache", "aeltester"):
                vorher = len([e for e in p.kills_von("DragonKill") if e.team == mein and e.zeit < unser[0].zeit
                              and e.daten.get("DragonType") != "Elder"])
                dauer *= 1.0 - min(cfg["objective"]["rache_max"], cfg["objective"]["rache_je_drache"] * vorher)
            n_med = round(statistics.median(lauf["n"])) if lauf["n"] else 1
            spalte = obj._spalte(t0)
            toetungen.append({"stamm": stamm, "schl": schl, "beginn": t0, "dauer": round(dauer, 1), "n": n_med,
                              "spalte": spalte})
        # ein Versuch: ein Kill eures Teams folgte, oder >= 2 von euch standen dort
        if unser or lauf["max_n"] >= 2:
            tod = any(t0 <= t <= t0 + AUSGANG_S for t in tote_eigene)
            ausgang = 1 if (unser and unser[0].zeit - t0 <= AUSGANG_S and not tod) else 0
            pe, n, grund = lauf["probe"]
            versuche.append({"stamm": stamm, "schl": schl, "beginn": t0, "p": round(pe, 3), "n_urteil": n,
                             "max_n": lauf["max_n"], "ausgang": ausgang, "grund": grund})
    return toetungen, versuche


def brier(werte: list[tuple[float, int]]) -> float | None:
    return sum((p - y) ** 2 for p, y in werte) / len(werte) if werte else None


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("aufnahmen", nargs="+")
    ap.add_argument("--json")
    a = ap.parse_args()
    cfg = konfig()
    alle_t, alle_v = [], []
    for stamm in a.aufnahmen:
        if bot_partie(stamm):
            print(f"{stamm}: Bot-Partie - uebersprungen")
            continue
        t, v = partie_messen(stamm, cfg)
        alle_t += t
        alle_v += v
    print("1. Toetungszeiten (Median; Drache mit Rache bereinigt), je Objective / Spalte / n:")
    gruppen: dict = {}
    for x in alle_t:
        gruppen.setdefault((x["schl"], x["spalte"], x["n"]), []).append(x["dauer"])
    tab = cfg["objective"]["dauer"]
    for (schl, spalte, n), werte in sorted(gruppen.items()):
        liste = tab.get(schl, {}).get(spalte)
        n_min = tab["n_min"].get(schl, 1)
        soll = liste[min(max(0, n - n_min), len(liste) - 1)] if liste else None
        hinweis = "aendern" if len(werte) >= 3 else "Startwert (< 3 Faelle)"
        print(f"  {schl:9} {spalte:7} n={n}: Median {statistics.median(werte):.0f} s aus {len(werte)} "
              f"(Tabelle {soll if soll is not None else '-'}) -> {hinweis}")
    if not alle_t:
        print("  keine Toetung eures Teams mit Anwesenden an der Grube")
    print(f"2. Urteil gegen Ausgang: {len(alle_v)} Versuche")
    ent = [(x["p"], x["ausgang"]) for x in alle_v]
    if ent:
        rate = sum(y for _, y in ent) / len(ent)
        print(f"  Brier {brier(ent):.3f}, Grundrate {rate:.2f} -> {brier([(rate, y) for _, y in ent]):.3f} "
              f"(Soll < 0,20 und besser als die Grundrate)")
    print(f"  Parameter: {'aenderbar' if len(alle_v) >= 30 else f'Startwerte - nur {len(alle_v)} Versuche (noetig 30)'}")
    for x in sorted(alle_v, key=lambda x: (x["stamm"], x["beginn"])):
        print(f"  {x['stamm'][-6:]} {ns.uhr(x['beginn'])} {x['schl']:9} p {x['p']:.2f} (n {x['n_urteil']}, "
              f"dort bis {x['max_n']}) -> {'genommen' if x['ausgang'] else 'nicht/mit Tod'}  [{x['grund']}]")
    if a.json:
        Path(a.json).write_text(json.dumps({"toetungen": alle_t, "versuche": alle_v}, ensure_ascii=False, indent=1),
                                encoding="utf-8")


if __name__ == "__main__":
    main()
