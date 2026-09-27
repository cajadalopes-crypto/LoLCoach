"""Kampf-Eichung (Buch 7, Kapitel 3.3): sagt kampf.p_gewinn Kaempfe vorher?

1. Proben an Entscheidungspunkten: ein Gegner und du (oder ein Mitspieler in 1500) naehern sich erstmals auf <= 1500
   nach >= 10 s ohne solche Naehe - p_gewinn DORT, vor dem Einstieg (der Kern legt sie beim Nachspielen an,
   kern.modi.kampf.Proben).
2. Ausgang in den naechsten 15 s: Kill-Gold eurer Kills minus Kill-Gold eurer Tode (bewertung.kill_gold). > 0 gewonnen,
   < 0 verloren; ohne Tod auf beiden Seiten "offen" (gezaehlt, nicht im Brier).
3. Nur echte Partien (bots = false). 4. Arten nach Beteiligten: 2 (Duell), 3-6, >= 7.
5. Faktoren (k, ult_faktor_weg, turm_faktor, mitspieler_anteil) nur mit >= eichung_min entschiedenen Proben; ein
   Faktor, der nicht messbar besser ist als 1, bleibt 1.
6. Brier je Art, Fallzahl, Anteil offen, Tabelle aller entschiedenen Proben.
7. Trennschaerfe je Merkmal (p, leben, level_diff, gold_diff, kopf_diff, turm): Mittel gewonnen / verloren, Fallzahl,
   AUC (P(zufaellige gewonnene Probe hat den hoeheren Wert als eine verlorene), Gleichstand halb; 0,5 = trennt nicht).
   level_diff/gold_diff: Mittel eurer Beteiligten minus Mittel der nahen Gegner, Gegner mit K.gegner_werte (G7).
   --json schreibt {"proben": [...], "trennschaerfe": [...]}; --aus liest das und die alte Liste.
8. --roh: Gegner mit den rohen API-Werten (Stand der letzten Sichtung) statt K.gegner_werte - im ganzen Nachspielen,
   also in p UND in level_diff/gold_diff. Ohne Schalter wie bisher.
9. --etikett (Verdacht aus S6: mit Vorsprung sind eure Tode teuer und eure Kills billig, das Gold-Etikett haengt dann am
   Vorsprung). Seite wie in 2: "eure" = Team des Opfers, alle Kills der Episode (15 s).
   gold (Standard): wie 2. koepfe: eure Kills minus eure Tode, > 0 gewonnen, < 0 verloren, Gleichstand offen.
   ueberlebt: du gestorben -> verloren; sonst mindestens ein Gegner tot -> gewonnen; sonst offen.
   Die Proben tragen dafuer kills_wir, tode_wir, ich_tot (--aus braucht eine --json-Datei mit diesen Feldern).

    python werkzeuge/kampf_eichung.py 2026-09-27_133930 2026-09-27_140253 ... [--json <datei>] [--aus <datei>] [--roh]
        [--etikett gold|koepfe|ueberlebt]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import nachspielen as ns  # noqa: E402

from lolcoach import aufzeichnung, bewertung, zustand  # noqa: E402
from lolcoach.kern import konfig  # noqa: E402

AUSGANG_S = 15.0


def art(probe: dict) -> str:
    n = len(probe["wir"]) + len(probe["gegner"])
    return "2" if n <= 2 else "3-6" if n <= 6 else ">=7"


def proben_einer_partie(stamm: str) -> list[dict]:
    pfad = ns.pfad_zu(stamm)
    lauf = ns.durchspielen(pfad)
    letzte = None
    for _, d in aufzeichnung.lies_mit_zeit(pfad):
        letzte = d
    p = zustand.partie(letzte)
    mein = p.mein_team
    kills = [e for e in p.kills_von("ChampionKill") if e.opfer is not None]
    ich = p.ich.name if p.ich else None
    aus = []
    for pr in lauf.kern.proben.liste:
        t0 = pr["zeit"]
        gold = 0.0
        tote = 0
        k_wir = k_die = 0      # eure Kills / eure Tode (Seite wie beim Gold: Team des Opfers)
        ich_tot = False
        for e in kills:
            if t0 <= e.zeit <= t0 + AUSGANG_S:
                g = bewertung.kill_gold(e.opfer, p=p)
                gold += g if e.opfer.team != mein else -g
                tote += 1
                if e.opfer.team != mein:
                    k_wir += 1
                else:
                    k_die += 1
                    ich_tot = ich_tot or e.opfer.name == ich
        ausgang = None if tote == 0 else (1 if gold > 0 else 0 if gold < 0 else None)
        aus.append(dict(pr, stamm=stamm, ausgang=ausgang, gold=gold, p_da_vorher=None, kills_wir=k_wir,
                        tode_wir=k_die, ich_tot=ich_tot))
    return aus


ETIKETTEN = ("gold", "koepfe", "ueberlebt")


def ausgang(pr: dict, etikett: str) -> int | None:
    """Ausgang einer Probe nach Etikett (Punkt 9); 'gold' ist der gespeicherte Standard."""
    if etikett == "gold":
        return pr["ausgang"]
    if "kills_wir" not in pr:
        raise SystemExit(f"--etikett {etikett}: die Proben tragen keine Kill-Zaehlung (--aus mit alter Datei?)")
    if etikett == "koepfe":
        d = pr["kills_wir"] - pr["tode_wir"]
        return 1 if d > 0 else 0 if d < 0 else None
    return 0 if pr["ich_tot"] else 1 if pr["kills_wir"] > 0 else None


def kt(pr: dict) -> str:
    if "kills_wir" not in pr:
        return ""
    return f", {pr['kills_wir']}:{pr['tode_wir']}{', du tot' if pr['ich_tot'] else ''}"


def p_neu(pr: dict, c: dict, k: float, ult: float, turm: float, anteil: float) -> float:
    """p_gewinn einer Probe mit anderen Faktoren, aus ihrer Aufschluesselung."""
    auf = pr.get("auf") or {}
    wir = sum(x[1] / (c["ult_faktor_weg"] if x[3] else 1.0) * (ult if x[3] else 1.0)
              * (anteil if i > 0 else 1.0) for i, x in enumerate(auf.get("wir", [])))
    die = sum(x[1] / (c["ult_faktor_weg"] if x[3] else 1.0) * (ult if x[3] else 1.0) * x[2] for x in auf.get("die", []))
    if die <= 0:
        return 1.0
    K = wir / die
    if auf.get("turm", 0) > 0:
        K *= turm
    elif auf.get("turm", 0) < 0:
        K /= turm
    return K ** k / (1 + K ** k)


def wirkt(pr: dict, name: str) -> bool:
    """Wirkt der Faktor in dieser Probe? k immer; ult nur mit einer weggebrannten Ult, turm nur am Turm, mitspieler nur
    mit einem Mitspieler im Kampf."""
    auf = pr.get("auf") or {}
    if name == "ult":
        return any(x[3] for x in auf.get("wir", []) + auf.get("die", []))
    if name == "turm":
        return auf.get("turm", 0) != 0
    if name == "mitspieler":
        return len(auf.get("wir", [])) > 1
    return True


def brier(werte: list[tuple[float, int]]) -> float | None:
    return sum((p - y) ** 2 for p, y in werte) / len(werte) if werte else None


MERKMALE = ("p", "leben", "level_diff", "gold_diff", "kopf_diff", "turm")


def merkmal(pr: dict, name: str) -> float | None:
    if name == "turm":
        return (pr.get("auf") or {}).get("turm", 0)
    return pr.get(name)


def auc(gew: list[float], verl: list[float]) -> float | None:
    """Wahrscheinlichkeit, dass eine zufaellige gewonnene Probe den hoeheren Wert hat als eine zufaellige verlorene;
    Gleichstand zaehlt halb. 0,5 = trennt nicht, unter 0,5 = trennt verkehrt herum."""
    if not gew or not verl:
        return None
    s = sum(1.0 if g > v else 0.5 if g == v else 0.0 for g in gew for v in verl)
    return s / (len(gew) * len(verl))


def trennschaerfe(entschieden: list[dict]) -> list[dict]:
    aus = []
    for name in MERKMALE:
        gew = [x for pr in entschieden if pr["ausgang"] == 1 and (x := merkmal(pr, name)) is not None]
        verl = [x for pr in entschieden if pr["ausgang"] == 0 and (x := merkmal(pr, name)) is not None]
        aus.append({"merkmal": name, "gewonnen": sum(gew) / len(gew) if gew else None,
                    "verloren": sum(verl) / len(verl) if verl else None, "auc": auc(gew, verl),
                    "n": len(gew) + len(verl), "n_gewonnen": len(gew), "n_verloren": len(verl)})
    return aus


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("aufnahmen", nargs="+")
    ap.add_argument("--json")
    ap.add_argument("--aus", help="Proben aus einer frueheren --json-Datei statt Nachspielen")
    ap.add_argument("--roh", action="store_true", help="Gegner mit rohen API-Werten statt kampf.gegner_werte (G7)")
    ap.add_argument("--etikett", choices=ETIKETTEN, default="gold", help="Ausgang: Kill-Gold (Standard), Koepfe, "
                    "ueberlebt (Docstring Punkt 9)")
    a = ap.parse_args()
    if a.roh:
        from lolcoach.kern import kampf as K
        K.gegner_werte = lambda g, m, c: (g.s.level, float(g.s.item_gold), False)
        print("Gegnerwerte: roh (API, Stand der letzten Sichtung)")
    cfg = konfig()
    c = cfg["kampf"]
    alle = []
    if a.aus:
        daten = json.loads(Path(a.aus).read_text(encoding="utf-8"))
        daten = daten["proben"] if isinstance(daten, dict) else daten
        alle = [pr for pr in daten if pr["stamm"] in a.aufnahmen]
    else:
        for stamm in a.aufnahmen:
            alle += proben_einer_partie(stamm)
    if a.etikett != "gold":
        print(f"Etikett: {a.etikett}")
        alle = [dict(pr, ausgang=ausgang(pr, a.etikett)) for pr in alle]
    entschieden =[pr for pr in alle if pr["ausgang"] is not None]
    print(f"Proben {len(alle)}, entschieden {len(entschieden)}, offen {len(alle) - len(entschieden)} "
          f"({100 * (len(alle) - len(entschieden)) / max(1, len(alle)):.0f} %)")
    for ar in ("2", "3-6", ">=7"):
        teil = [pr for pr in alle if art(pr) == ar]
        ent = [(pr["p"], pr["ausgang"]) for pr in teil if pr["ausgang"] is not None]
        if not teil:
            continue
        rate = sum(y for _, y in ent) / len(ent) if ent else None
        b = brier(ent)
        b0 = brier([(rate, y) for _, y in ent]) if ent else None
        print(f"  Art {ar:4}: {len(teil)} Proben, {len(ent)} entschieden, offen {len(teil) - len(ent)}; "
              + (f"Brier {b:.3f} (Grundrate {rate:.2f} -> {b0:.3f})" if ent else "kein entschiedener Kampf"))
    ent = [(pr["p"], pr["ausgang"]) for pr in entschieden]
    b_grund = None
    if ent:
        rate = sum(y for _, y in ent) / len(ent)
        b_grund = brier([(rate, y) for _, y in ent])
        print(f"  gesamt: Brier {brier(ent):.3f}, Grundrate {rate:.2f} -> {b_grund:.3f}")
        gew = [p_ for p_, y in ent if y == 1]
        verl = [p_ for p_, y in ent if y == 0]
        if gew and verl:
            print(f"  Trennschaerfe: mittleres p gewonnen {sum(gew) / len(gew):.2f} ({len(gew)}), "
                  f"verloren {sum(verl) / len(verl):.2f} ({len(verl)})")
    ts = trennschaerfe(entschieden)
    print("Trennschaerfe je Merkmal (nur entschiedene Proben; AUC 0,5 = trennt nicht):")
    print(f"  {'Merkmal':10} {'gewonnen':>9} {'verloren':>9} {'AUC':>5}  n (gew/verl)")
    for z in ts:
        fm = ".0f" if z["merkmal"] == "gold_diff" else ".2f"
        mg = "-" if z["gewonnen"] is None else format(z["gewonnen"], fm)
        mv = "-" if z["verloren"] is None else format(z["verloren"], fm)
        au = "-" if z["auc"] is None else f"{z['auc']:.2f}"
        print(f"  {z['merkmal']:10} {mg:>9} {mv:>9} {au:>5}  {z['n']} ({z['n_gewonnen']}/{z['n_verloren']})")
    # Faktoren: ein Parameter aendert sich nur mit >= eichung_min entschiedenen Proben, IN DENEN ER WIRKT (eine Probe
    # ohne weggebrannte Ult sagt nichts ueber ult_faktor_weg); die anderen bleiben auf dem Startwert
    namen = ("k", "ult", "turm", "mitspieler")
    start = (c["k"], c["ult_faktor_weg"], c["turm_faktor"], c["mitspieler_anteil"])
    gitter = ((1.0, 1.5, 2.0, 2.5, 3.0), (0.7, 0.8, 0.9, 1.0), (1.0, 1.25, 1.5, 1.75, 2.0), (0.6, 0.8, 1.0))
    n = [sum(1 for pr in entschieden if wirkt(pr, name)) for name in namen]
    frei = [n[i] >= c["eichung_min"] for i in range(4)]
    werte = [gitter[i] if frei[i] else (start[i],) for i in range(4)]
    beste = (brier([(p_neu(pr, c, *start), pr["ausgang"]) for pr in entschieden]) if entschieden else None, start)
    if entschieden and any(frei):
        for k in werte[0]:
            for ult in werte[1]:
                for turm in werte[2]:
                    for an in werte[3]:
                        b = brier([(p_neu(pr, c, k, ult, turm, an), pr["ausgang"]) for pr in entschieden])
                        if b < beste[0] - 1e-9:
                            beste = (b, (k, ult, turm, an))
        print(f"  beste Faktoren (k, ult, turm, mitspieler): {beste[1]}, Brier {beste[0]:.3f} (Start {start})")
    # Das Ziel der Eichung ist ein Modell, das vorhersagt (Soll: besser als die Grundrate). Erreicht es das mit KEINEN
    # Faktoren, ist die beste Wahl nur eine Abflachung Richtung 50 % - dann bleiben die Startwerte (messungen.md,
    # Schritt 5: am 27.09. wuerde k = 1 sonst 0904/0806/0701 kippen, ohne dass das Modell etwas trennt)
    if b_grund is not None and beste[0] is not None and beste[0] >= b_grund:
        print(f"  Kein Faktorsatz schlaegt die Grundrate ({beste[0]:.3f} >= {b_grund:.3f}): das Modell trennt nicht - "
              f"Startwerte bleiben")
        frei = [False] * 4
    for i, name in enumerate(namen):
        if not frei[i]:
            print(f"    {name}: Startwert {start[i]} - {n[i]} entschiedene Proben, in denen er wirkt "
                  f"(noetig {c['eichung_min']})")
            continue
        # "Liegt ein Faktor nicht messbar besser als 1, bleibt er 1" (messbar = mindestens 0,005 Brier)
        neutral = list(beste[1])
        neutral[i] = 1.0
        bn = brier([(p_neu(pr, c, *neutral), pr["ausgang"]) for pr in entschieden])
        gilt = beste[1][i] if bn - beste[0] >= 0.005 else 1.0
        print(f"    {name}: {n[i]} Proben; bester {beste[1][i]} -> Brier {beste[0]:.3f}; mit 1 -> {bn:.3f} -> gilt {gilt}")
    print("Entschiedene Proben:")
    for pr in sorted(entschieden, key=lambda x: (x["stamm"], x["zeit"])):
        print(f"  {pr['stamm'][-6:]} {ns.uhr(pr['zeit'])} p {pr['p']:.2f} -> {'gewonnen' if pr['ausgang'] else 'verloren'}"
              f" ({pr['gold']:+.0f} Gold{kt(pr)}) wir {pr['wir']} gegen {pr['gegner']}{' unter ihrem Turm' if pr['unter_turm'] else ''}")
    if a.json:
        Path(a.json).write_text(json.dumps({"proben": alle, "trennschaerfe": ts},
                                           ensure_ascii=False, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
