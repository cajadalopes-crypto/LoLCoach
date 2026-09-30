"""Auftrag 036: die Gefahr-Schwelle an den Pruefpartien bestimmen - ab welcher Todeswahrscheinlichkeit (Gefahr-Modell,
`Hirn.tod60`) eine Gefahr-Entscheidung (J4, J5, J9 ...) warnen darf.

    python werkzeuge/challenger/gefahr_schwelle.py [--n 30000] [--nur-zeigen]
        -> schreibt gefahr_schwelle in wissen/kern.toml [makro_gehirn] (ausser --nur-zeigen)
        -> buecher/challenger/gefahr_schwelle.json und eine Tabelle im Terminal

Laeuft bei Carlos (daten/challenger/phase1 und die Modelle), ohne Claude, ohne Guthaben. Einmal vor
`werkzeuge/abnahme_035.py`.

Grundlage wie werkzeuge/challenger/treue.py: die zurueckgelegten Pruefpartien (aufteilung.json), je Moment die
MakroLage aus dem Riot-Moment und der echte Entscheider. Je Moment ZWEI Laeufe:
  - Schwelle 0: jede Gefahr-Handregel, die feuert, warnt (mit Modellwert),
  - Schwelle unendlich: keine Handregel warnt (nur, was ohne Modell warnen darf: B4).
Alle Gefahr-Handregeln eines Moments teilen denselben Modellwert (tod60 ist eine Groesse der Lage). Deshalb ist
der Coach bei jeder Schwelle s in jedem Moment genau einer der beiden Laeufe: tod60 >= s -> Lauf 0, sonst Lauf
unendlich. So laesst sich jede Schwelle exakt durchrechnen, ohne den Entscheider erneut laufen zu lassen.

Gewaehlt wird (Auftrag 036, 1.1) die KLEINSTE Schwelle - also die mit den meisten Warnungen -, fuer die gilt:
  - Tod in 60 s nach einer Warnung mindestens doppelt so wahrscheinlich wie ohne Warnung (FAKTOR_MIN) und
  - Warnungen hoechstens 15 % aller Ansagen (ANTEIL_MAX; je Moment eine Ansage),
  - dazu mindestens N_MIN Warnungen (sonst ist die Rate Zufall).
Gewaehlt wird an der einen Haelfte der Pruefpartien (nach Partie geteilt), geprueft an der anderen - die Zahlen
beider Haelften stehen in der Ausgabe. Gibt es keine solche Schwelle, nimmt das Werkzeug die mit dem hoechsten
Faktor unter hoechstens 15 % Warnungen und sagt klar, dass das Ziel nicht erreicht ist.
"""
from __future__ import annotations

import json
import math
import re
import sys
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
WURZEL = HIER.parents[1]
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(WURZEL))

KERN_TOML = WURZEL / "wissen" / "kern.toml"
AUS = WURZEL / "buecher" / "challenger" / "gefahr_schwelle.json"
FAKTOR_MIN = 2.0
ANTEIL_MAX = 0.15
N_MIN = 50
RASTER = [round(0.005 * i, 3) for i in range(0, 191)]          # 0,000 ... 0,950


# --- die Rechnung (ohne Daten pruefbar: tests/makro/test_treue.py) -------------------------------------------------

def warnt(p, g0, gi, s: float):
    """Maske: warnt der Coach bei Schwelle s? p: tod60 je Moment (NaN = kein Modellwert), g0/gi: Form Gefahr bei
    Schwelle 0 / unendlich."""
    import numpy as np
    p = np.asarray(p, float)
    mit = np.nan_to_num(p, nan=-1.0) >= s
    return np.asarray(gi, bool) | (np.asarray(g0, bool) & mit)


def kurve(p, g0, gi, tod, maske=None, raster=RASTER) -> list[dict]:
    """Je Schwelle: Anteil Warnungen, Tod in 60 s mit und ohne Warnung, Faktor."""
    import numpy as np
    tod = np.asarray(tod, bool)
    m = np.ones(len(tod), bool) if maske is None else np.asarray(maske, bool)
    out = []
    for s in raster:
        w = warnt(p, g0, gi, s) & m
        ohne = ~w & m
        n_w, n = int(w.sum()), int(m.sum())
        r_w = float(tod[w].mean()) if n_w else float("nan")
        r_o = float(tod[ohne].mean()) if ohne.any() else float("nan")
        out.append({"schwelle": s, "warnungen": n_w, "anteil": n_w / n if n else float("nan"),
                    "tod_mit": r_w, "tod_ohne": r_o,
                    "faktor": r_w / r_o if n_w and r_o > 0 else float("nan")})
    return out


def waehlen(k: list[dict], anteil_max: float = ANTEIL_MAX, faktor_min: float = FAKTOR_MIN,
            n_min: int = N_MIN) -> tuple[dict | None, bool]:
    """(Zeile, erreicht): die kleinste Schwelle, die beide Bedingungen erfuellt; sonst die mit dem hoechsten Faktor
    unter anteil_max (erreicht=False); None, wenn es gar keine Zeile mit genug Warnungen gibt."""
    gut = [z for z in k if z["warnungen"] >= n_min and z["anteil"] <= anteil_max
           and not math.isnan(z["faktor"]) and z["faktor"] >= faktor_min]
    if gut:
        return min(gut, key=lambda z: z["schwelle"]), True
    rest = [z for z in k if z["warnungen"] >= n_min and z["anteil"] <= anteil_max and not math.isnan(z["faktor"])]
    if rest:
        return max(rest, key=lambda z: (z["faktor"], -z["schwelle"])), False
    return None, False


def politik(lauf0: list, lauf_inf: list, p, s: float) -> list:
    """Der Coach bei Schwelle s, je Moment: Lauf 0, wenn das Modell bestaetigt, sonst Lauf unendlich."""
    return [a if (not math.isnan(x) and x >= s) else b for a, b, x in zip(lauf0, lauf_inf, p)]


def toml_schreiben(text: str, wert: float, zeile_kommentar: str) -> str:
    """Setzt `gefahr_schwelle = wert` in [makro_gehirn] und ersetzt die Kommentarzeilen darunter."""
    zeilen = text.split("\n")
    i = next((j for j, z in enumerate(zeilen) if re.match(r"\s*gefahr_schwelle\s*=", z)), None)
    neu = [f"gefahr_schwelle = {wert:.3f}          # Auftrag 036: eine Gefahr-Entscheidung (J4, J5, J9 ...) warnt nur, "
           "wenn die",
           "                                 # Todeswahrscheinlichkeit in 60 s (Gefahr-Modell, Hirn.tod60) mindestens so "
           "hoch ist.",
           f"                                 # {zeile_kommentar}"]
    if i is None:
        k = next(j for j, z in enumerate(zeilen) if z.strip().startswith("[makro_gehirn]"))
        e = next((j for j in range(k + 1, len(zeilen)) if zeilen[j].strip().startswith("[")), len(zeilen))
        while e > k + 1 and not zeilen[e - 1].strip():
            e -= 1
        return "\n".join(zeilen[:e] + neu + zeilen[e:])
    e = i + 1
    while e < len(zeilen) and re.match(r"\s+#", zeilen[e]):
        e += 1
    return "\n".join(zeilen[:i] + neu + zeilen[e:])


# --- der Lauf ------------------------------------------------------------------------------------------------------

def _pc(x: float) -> str:
    return "   -  " if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:5.1f} %"


def drucken_kurve(k: list[dict], titel: str) -> None:
    print(f"\n{titel}")
    print(f"{'Schwelle':>9} {'Warnungen':>10} {'Anteil':>8} {'Tod mit':>8} {'Tod ohne':>9} {'Faktor':>7}")
    for z in k:
        if round(z["schwelle"] * 100) % 5 == 0 or z.get("gewaehlt"):
            f = "   -  " if math.isnan(z["faktor"]) else f"{z['faktor']:6.2f}"
            print(f"{z['schwelle']:9.3f} {z['warnungen']:10d} {_pc(z['anteil']):>8} {_pc(z['tod_mit']):>8} "
                  f"{_pc(z['tod_ohne']):>9} {f:>7}{'   <- gewaehlt' if z.get('gewaehlt') else ''}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    n = int(args[args.index("--n") + 1]) if "--n" in args else 30000
    import numpy as np
    import phase1 as f
    import treue as tr
    from lolcoach.makro.einbau import konfig
    reihenfolge = str(konfig().get("reihenfolge", "wert"))
    P, hirn, setzen = tr.laden(n)
    lauf0, lauf_inf = [], []
    t0 = time.time()
    for i in range(len(P.k)):
        setzen(i)
        lauf0.append(tr.coach(tr.lage_aus_moment(P.X[i], P.M[i], f.SP, f.MI), P.B[i], hirn, reihenfolge, 0.0))
        lauf_inf.append(tr.coach(tr.lage_aus_moment(P.X[i], P.M[i], f.SP, f.MI), P.B[i], hirn, reihenfolge,
                                 float("inf")))
        if i % 5000 == 0:
            print(f"  Coach {i}/{len(P.k)} ({time.time() - t0:.0f} s)", flush=True)
    p = np.array([np.nan if a["tod60"] is None else a["tod60"] for a in lauf0])
    g0 = np.array([a["form"] == "gefahr" for a in lauf0])
    gi = np.array([a["form"] == "gefahr" for a in lauf_inf])
    tod = P.F[:, P.FI["tod_60"]] > 0
    # nach Partie geteilt: waehlen an der einen Haelfte, pruefen an der anderen
    _, inv = np.unique(P.partie, return_inverse=True)
    wahl = inv % 2 == 0
    k_wahl = kurve(p, g0, gi, tod, wahl)
    z, erreicht = waehlen(k_wahl)
    if z is None:
        sys.exit("!! Keine Schwelle mit genug Warnungen - nichts geschrieben.")
    s = z["schwelle"]
    for zz in k_wahl:
        zz["gewaehlt"] = zz["schwelle"] == s
    k_kontrolle = kurve(p, g0, gi, tod, ~wahl)
    k_alle = kurve(p, g0, gi, tod)
    kontrolle = next(x for x in k_kontrolle if x["schwelle"] == s)
    alle = next(x for x in k_alle if x["schwelle"] == s)
    # Treue bei dieser Schwelle gegen die Vergleiche (dieselbe Rechnung wie treue.py)
    politiken = {f"Coach (Schwelle {s:.3f})": politik(lauf0, lauf_inf, p, s),
                 "Coach, jede Handregel warnt (wie 035)": lauf0,
                 "Coach, keine Handregel warnt": lauf_inf,
                 "immer farmen": [{"aktionen": [("Lane", "")]} for _ in range(len(P.k))],
                 "haeufigste je Rolle und Minute": tr.haeufigste(P)}
    treue = tr.auswerten(P, politiken, 0)
    ergebnis = {"schwelle": s, "erreicht": erreicht, "reihenfolge": reihenfolge, "n": int(len(P.k)),
                "partien": int(inv.max() + 1), "ziel": {"faktor_min": FAKTOR_MIN, "anteil_max": ANTEIL_MAX, "n_min": N_MIN},
                "wahl": z, "kontrolle": kontrolle, "alle": alle,
                "handregel_feuert": float(g0.mean()), "ohne_modellwert": float(np.isnan(p).mean()),
                "tod60_verteilung": {q: float(np.nanquantile(p, q / 100)) for q in (10, 25, 50, 75, 90, 95, 99)},
                "kurve_wahl": k_wahl, "kurve_kontrolle": k_kontrolle, "treue": treue["politiken"]}
    AUS.write_text(json.dumps(ergebnis, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

    print(f"\nGefahr-Schwelle (Auftrag 036): {len(P.k)} Momente, Reihenfolge {reihenfolge}")
    print(f"Handregel-Gefahr feuert in {_pc(float(g0.mean()))} der Momente; tod60 Median "
          f"{ergebnis['tod60_verteilung'][50]:.3f}, p90 {ergebnis['tod60_verteilung'][90]:.3f}")
    drucken_kurve(k_wahl, "Wahl-Haelfte der Pruefpartien:")
    zeile = lambda x: (f"Warnungen {_pc(x['anteil'])} ({x['warnungen']}), Tod in 60 s mit Warnung {_pc(x['tod_mit'])}, "
                       f"ohne {_pc(x['tod_ohne'])}, Faktor {x['faktor']:.2f}")
    print(f"\nGewaehlt: {s:.3f}  -  {'ZIEL ERREICHT' if erreicht else 'ZIEL NICHT ERREICHT'} "
          f"(Faktor >= {FAKTOR_MIN}, Warnungen <= {ANTEIL_MAX:.0%})")
    print(f"  Wahl-Haelfte:      {zeile(z)}")
    print(f"  Kontroll-Haelfte:  {zeile(kontrolle)}")
    print(f"  alle Pruefpartien: {zeile(alle)}")
    print("\nTreue bei dieser Schwelle (alle Pruefpartien):")
    for name, r in treue["politiken"].items():
        print(f"  {name:42} Treffer {_pc(r['treffer'])}, Wert {r['wert_dr']:+.2f} ± {r['wert_dr_se']:.2f}"
              + (f", Warnungen {_pc(r['warnungen'])}" if "warnungen" in r else ""))
    if not erreicht:
        print("\n!! Keine Schwelle erfuellt beide Bedingungen - geschrieben wird die mit dem hoechsten Faktor unter "
              f"{ANTEIL_MAX:.0%} Warnungen. Das Gefahr-Modell trennt die Lagen der Handregeln nicht scharf genug.")
    if "--nur-zeigen" not in args:
        text = KERN_TOML.read_text(encoding="utf-8")
        kom = (f"bestimmt {time.strftime('%d.%m.%Y')} mit werkzeuge/challenger/gefahr_schwelle.py: Faktor "
               f"{alle['faktor']:.2f}, Warnungen {100 * alle['anteil']:.1f} %"
               + ("" if erreicht else " - ZIEL NICHT ERREICHT"))
        KERN_TOML.write_text(toml_schreiben(text, s, kom), encoding="utf-8")
        print(f"-> {KERN_TOML} (gefahr_schwelle = {s:.3f})")
    print(f"-> {AUS}")


if __name__ == "__main__":
    main()
