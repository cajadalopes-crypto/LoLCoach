"""Auftrag 035, Teil 1: die Verdrahtung des Makro-Entscheiders im Nachspiel (ohne Guthaben) - Tor-Masse aus 027/028
plus die Makro-Zahlen. Laeuft bei Carlos (Aufnahmen, Modelle); mit den Modellen in daten/challenger/modelle misst das
Protokoll auch die Laufzeit des echten Gehirns.

    python werkzeuge/makro_messen.py [stamm ...] [--reihenfolge fest|wert] [--kern makro|neu] [--ohne-stub]

Je Partie ein Nachspiel (werkzeuge/pakete_messen._lauf, parallel), Claude als Stimme ueber den Stub
(einbau.stimme_stub: der Weg, nicht der Text). Gemessen:
  - HOEREN (027/028, pakete_messen.hoeren): Anweisungs-Luecke p90/max, Stillstand, Basis, negativ allein, Hin und
    Her, Widerspruch, Fuellsaetze; Sicherheit (jeder gesprochene Satz, stratege.sicherheit)
  - MAKRO (makro_protokoll): Laufzeit je Entscheidung (mit Gehirn), Formen, Wechselgruende, Sperre, wie oft eine
    Entscheidung wegen fehlender Wahrnehmung schweigt, Vorlage statt Claude
Ergebnis: buecher/protokolle/proben/makro_035/<stamm>.json und ergebnis.json; am Ende die Tor-Zeilen von Teil 1.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(HIER.parent))

AUS = HIER.parent / "buecher" / "protokolle" / "proben" / "makro_035"
# Tor Stufe 5 (Auftrag 035), soweit Teil 1 es misst: (Name, Soll-Text, Pruefung)
def _quote_ok(paar, soll: float):
    """True/False, None ohne Faelle (nicht gemessen - etwa Basis ohne Kaufplan)."""
    return None if not paar[1] else paar[0] >= soll * paar[1]


TOR = [("Sicherheit", "0", lambda g: g["sicherheit"] == 0),
       ("Widerspruch je Partie", "<= 1", lambda g: max(g["widerspruch"], default=0) <= 1),
       ("Fuellsaetze", "<= 5 %", lambda g: g["fuell"][0] <= 0.05 * max(1, g["fuell"][1])),
       ("Luecke p90", "<= 20 s", lambda g: g["luecke_p90"] <= 20),
       ("Luecke laengste", "<= 35 s", lambda g: g["luecke_max"] <= 35),
       ("Stillstand", ">= 95 %", lambda g: _quote_ok(g["still"], 0.95)),
       ("Basis", ">= 95 %", lambda g: _quote_ok(g["basis"], 0.95)),
       ("Laufzeit je Takt (p95)", "< 50 ms", lambda g: g["ms_p95"] < 50)]


def _lauf(a: tuple) -> dict:
    stamm, kern, reihenfolge, stub = a
    if reihenfolge:
        os.environ["LOLCOACH_MAKRO_REIHENFOLGE"] = reihenfolge
    if stub:
        os.environ["LOLCOACH_MAKRO_STIMME"] = "stub"
    import pakete_messen as pm
    return pm._lauf(stamm, kern)


def makro_zahlen(d: dict) -> dict:
    """Aus dem Makro-Teil eines Laufs: Protokoll-Auswertung + Stumm-Anteil je Entscheidung."""
    import makro_protokoll as mp
    mk = d.get("makro") or {}
    e, a = mk.get("protokoll", []), mk.get("gesagt", [])
    r = mp.auswerten_daten(e, a, d["stamm"])
    n = max(1, len(e))
    stumm = Counter(i for x in e for i in x.get("stumm", []))
    r["stumm_anteil"] = {i: round(c / n, 3) for i, c in stumm.most_common()}
    r["takte_mit_stumm"] = round(sum(1 for x in e if x.get("stumm")) / n, 3)
    r["ms_liste"] = [x["ms"] for x in e if "ms" in x]
    r["hirn"] = mk.get("hirn")
    r["verworfen"] = mk.get("verworfen", 0)
    return r


def gesamt(ergebnisse: list[dict]) -> dict:
    h = [r["hoeren"] for r in ergebnisse]
    ms = sorted(m for r in ergebnisse for m in r["makro"]["ms_liste"])
    q = Counter()
    for r in ergebnisse:
        q.update(r["makro"]["quelle"])
    summe = lambda k: [sum(x[k][0] for x in h), sum(x[k][1] for x in h)]
    return {"sicherheit": sum(len(r["sicherheit"]) for r in ergebnisse),
            "widerspruch": [x["widerspruch"] for x in h], "fuell": summe("fuell"),
            "luecke_p90": max((x["luecke_p90"] for x in h), default=0.0),
            "luecke_max": max((x["luecke_max"] for x in h), default=0.0),
            "still": summe("still"), "basis": summe("basis"),
            "negativ_allein": sum(x["negativ"] for x in h), "hin_und_her": sum(x["hin_her"] for x in h),
            "ms_median": ms[len(ms) // 2] if ms else 0.0, "ms_p95": ms[int(0.95 * (len(ms) - 1))] if ms else 0.0,
            "ms_max": ms[-1] if ms else 0.0, "quelle": dict(q),
            "vorlage_anteil": round(sum(v for k, v in q.items() if k.startswith("vorlage")) / max(1, sum(q.values())), 3),
            "hirn_geladen": all(r["makro"]["hirn"] for r in ergebnisse) if ergebnisse else False}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    import pakete_messen as pm
    args = sys.argv[1:]
    wert = lambda name, vorgabe: args[args.index(name) + 1] if name in args else vorgabe
    kern, reihenfolge = wert("--kern", "makro"), wert("--reihenfolge", None)
    frei = {x for i, x in enumerate(args) if i > 0 and args[i - 1] in ("--kern", "--reihenfolge")}
    staemme = [a for a in args if not a.startswith("--") and a not in frei] or list(pm.TESTPARTIEN)
    AUS.mkdir(parents=True, exist_ok=True)
    from concurrent.futures import ProcessPoolExecutor
    t0 = time.monotonic()
    with ProcessPoolExecutor(min(len(staemme), os.cpu_count() or 2)) as ex:
        laeufe = list(ex.map(_lauf, [(s, kern, reihenfolge, "--ohne-stub" not in args) for s in staemme]))
    ergebnisse = []
    for d in laeufe:
        r = {"stamm": d["stamm"], "hoeren": pm.hoeren(d), "sicherheit": d["sicherheit"], "makro": makro_zahlen(d)}
        ergebnisse.append(r)
        h, m = r["hoeren"], r["makro"]
        print(f"{d['stamm']}: Luecke p90 {h['luecke_p90']} s / max {h['luecke_max']} s, Stillstand "
              f"{pm._quote(*h['still'])}, Basis {pm._quote(*h['basis'])}, negativ allein {h['negativ']}, hin und her "
              f"{h['hin_her']}, Widerspruch {h['widerspruch']}, Fuellsaetze {pm._quote(*h['fuell'])}, Sicherheit "
              f"{len(d['sicherheit'])}", flush=True)
        print(f"    Makro: {m['entscheidungen']} Entscheidungen, {m['ansagen']} Ansagen, Laufzeit Median "
              f"{m['ms']['median']:.2f} / p95 {m['ms']['p95']:.2f} / max {m['ms']['max']:.2f} ms (Gehirn "
              f"{'ja' if m['hirn'] else 'NEIN'}), Takte mit stummer Entscheidung {100 * m['takte_mit_stumm']:.0f} %, "
              f"Quelle {dict(m['quelle'])}, verworfen {m['verworfen']}", flush=True)
        for x in d["sicherheit"][:4]:
            print(f"    SICHERHEIT {x['t']} {x['schl']} {x['grund']}: {x['text']}", flush=True)
        (AUS / f"{Path(d['stamm']).name.removesuffix('.jsonl.gz')}.json").write_text(json.dumps({**r, "makro": {k: v for k, v in m.items() if k != "ms_liste"}},
                                                           ensure_ascii=False, default=str), encoding="utf-8")
    g = gesamt(ergebnisse)
    print(f"\nGESAMT ({len(staemme)} Partien, --kern {kern}, Reihenfolge {reihenfolge or 'wie kern.toml'}, "
          f"{time.monotonic() - t0:.0f} s): {json.dumps(g, ensure_ascii=False)}")
    print("\nTor Stufe 5, Teil 1 (Verdrahtung):")
    for name, soll, ok in TOR:
        e = ok(g)
        print(f"  {'--  ' if e is None else 'OK  ' if e else 'NEIN'} {name}: Soll {soll}"
              + (" (keine Faelle - nicht gemessen)" if e is None else ""))
    if not g["hirn_geladen"]:
        print("  !! Gehirn nicht geladen - die Laufzeit gilt ohne Modell (daten/challenger/modelle fehlt?)")
    (AUS / "ergebnis.json").write_text(json.dumps({"gesamt": g, "je_partie": [
        {**r, "makro": {k: v for k, v in r["makro"].items() if k != "ms_liste"}} for r in ergebnisse]},
        ensure_ascii=False, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
