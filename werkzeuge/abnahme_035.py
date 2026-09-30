"""Auftrag 035: die Abnahme des Challenger-Gehirns in einem Zug - Teil 1 bis 3 OHNE Guthaben, bei Carlos (lokal, mit
daten/, aufnahmen/, Modellen und Windows). Die Abo-Runde (Teil 3.3) startet dieses Skript NIE - es sagt am Ende, ob
Teil 1 und 2 stehen und mit welchem Befehl sie laeuft.

    python werkzeuge/abnahme_035.py [--schnell] [--ohne-generalprobe] [--n 30000]

Schritte (je ein eigener Prozess, ohne LOLCOACH_API - Sparprotokoll):
  1. Laufzeit des echten Gehirns       werkzeuge/challenger/gehirn.py (messen)
  2. Generalprobe mit --kern makro     werkzeuge/generalprobe.py (Windows; der Coach als Prozess gegen die Aufnahme)
  3. Verdrahtung (Teil 1)              werkzeuge/makro_messen.py (alle Testpartien, Stub)
  4. Challenger-Treue (Teil 2)         werkzeuge/challenger/treue.py (beide Reihenfolgen, drei Vergleiche)
  5. Szenarien (Teil 3.1)              werkzeuge/szenarien.py --kern makro und --kern neu (die 14 bekannten Roten)
  6. Guthaben                          werkzeuge/guthaben.py
Ergebnis: buecher/challenger/abnahme_035.json und buecher/challenger/phase5_messung.md (Tor-Tabelle mit den Zahlen,
Treue gegen die drei Vergleiche, die Reihenfolge-Entscheidung, die Szenarien je Zeile) - die Grundlage fuer
phase5_bericht.md.

"Deutlich" (Tor Challenger-Treue) ist hier festgelegt als Messdefinition (kein Entscheidungswissen): der Coach hat
gegen jeden Vergleich mindestens 5 Prozentpunkte mehr Treffer UND einen um mehr als zwei gemeinsame Standardfehler
hoeheren Wert (doppelt robust). Gegen den alten Kern auf den Momenten, an die er sich anlegen laesst.
"""
from __future__ import annotations

import ast
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
WURZEL = HIER.parent
BUCH = WURZEL / "buecher" / "challenger"
AUS_JSON = BUCH / "abnahme_035.json"
AUS_MD = BUCH / "phase5_messung.md"
# die 14 bekannten Roten aus 028/033 (buecher/auftraege/033_bericht.md)
BEKANNT_ROT = ("s23-plan-hoechstens-14", "a4-lagebild-ungefragt", "wendepunkt-ansage", "0944-turm-ist-down",
               "0944-nach-turmfall-kein-farmen", "0944-erster-tower-was-jetzt", "wohin-kurz")
DEUTLICH_PP = 5.0


def _umgebung() -> dict:
    return {k: v for k, v in os.environ.items() if k not in ("LOLCOACH_API", "LOLCOACH_API_BUDGET")}


def _lauf(befehl: list[str], zeitlimit: float = 6 * 3600) -> tuple[int, str]:
    print(f"\n$ {' '.join(befehl)}", flush=True)
    t0 = time.time()
    p = subprocess.run([sys.executable, *befehl], cwd=WURZEL, env=_umgebung(), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=zeitlimit)
    aus = p.stdout + p.stderr
    print(aus[-3000:], flush=True)
    print(f"({time.time() - t0:.0f} s, Rueckgabe {p.returncode})", flush=True)
    return p.returncode, aus


def gehirn_laufzeit() -> dict | None:
    code, aus = _lauf(["werkzeuge/challenger/gehirn.py"])
    for z in reversed(aus.strip().splitlines()):
        if z.startswith("{") and "median_ms" in z:
            try:
                return ast.literal_eval(z)
            except (ValueError, SyntaxError):
                return None
    return None


def treue_urteil(t: dict) -> dict:
    """Schlaegt der Coach (die bessere Reihenfolge) alle drei Vergleiche deutlich?"""
    coach = f"Coach ({t['reihenfolge']})"
    pol = t["politiken"]
    c = pol[coach]
    urteile = {}
    for name in ("immer farmen", "haeufigste je Rolle und Minute"):
        v = pol[name]
        urteile[name] = _deutlich(c, v)
    alt = t.get("auf_den_alt_momenten", {}).get("politiken", {})
    alt_name = next((k for k in alt if k.startswith("alter Kern")), None)
    urteile["alter Kern"] = _deutlich(alt[coach], alt[alt_name]) if alt_name and coach in alt else None
    ok = all(u is not None and u["deutlich"] for u in urteile.values())
    return {"coach": coach, "urteile": urteile, "erreicht": ok}


def _deutlich(c: dict, v: dict) -> dict:
    dt = 100 * (c["treffer"] - v["treffer"])
    dw = c["wert_dr"] - v["wert_dr"]
    se = math.hypot(c["wert_dr_se"], v["wert_dr_se"])
    return {"treffer_pp": round(dt, 1), "wert_pkt": round(dw, 2), "wert_se": round(se, 2),
            "deutlich": dt >= DEUTLICH_PP and dw > 2 * se}


def tor(m: dict) -> list[tuple[str, str, str, bool | None]]:
    """(Mass, Soll, Ist, erreicht) fuer die Tor-Tabelle aus 035."""
    v = m.get("verdrahtung", {}).get("gesamt", {})
    tu = m.get("treue_urteil")
    lz = m.get("gehirn_laufzeit") or {}
    ms_p95 = max(v.get("ms_p95", 0.0), lz.get("p95_ms", 0.0)) if v else None
    q = lambda paar: (f"{paar[0]}/{paar[1]} ({100 * paar[0] / paar[1]:.0f} %)" if paar and paar[1] else "keine Faelle")
    ok_q = lambda paar: None if not paar or not paar[1] else paar[0] >= 0.95 * paar[1]
    zeilen = [
        ("Challenger-Treue", "schlaegt alle drei Vergleiche deutlich", _treue_text(tu),
         None if tu is None else tu["erreicht"]),
        ("Tor 036: gegen haeufigste je Rolle und Minute", "hoeher bei Treffer UND Wert", _treue_text(tu, HAEUFIGSTE),
         None if tu is None or tu["urteile"].get(HAEUFIGSTE) is None else
         tu["urteile"][HAEUFIGSTE]["treffer_pp"] > 0 and tu["urteile"][HAEUFIGSTE]["wert_pkt"] > 0),
        ("Sicherheit", "0", str(v.get("sicherheit", "-")), None if not v else v["sicherheit"] == 0),
        ("Widerspruch (automatisch)", "<= 1 je Partie", str(max(v.get("widerspruch", [0]) or [0])) if v else "-",
         None if not v else max(v["widerspruch"] or [0]) <= 1),
        ("Fuellsaetze", "<= 5 %", q(v.get("fuell")) if v else "-",
         None if not v else v["fuell"][0] <= 0.05 * max(1, v["fuell"][1])),
        ("Anweisungs-Luecke p90 / laengste", "<= 20 s / <= 35 s",
         f"{v.get('luecke_p90', '-')} s / {v.get('luecke_max', '-')} s" if v else "-",
         None if not v else v["luecke_p90"] <= 20 and v["luecke_max"] <= 35),
        ("Stillstand", ">= 95 %", q(v.get("still")) if v else "-", ok_q(v.get("still")) if v else None),
        ("Basis", ">= 95 %", q(v.get("basis")) if v else "-", ok_q(v.get("basis")) if v else None),
        ("Laufzeit je Takt", "< 50 ms", "-" if ms_p95 is None else f"p95 {ms_p95:.1f} ms",
         None if ms_p95 is None else ms_p95 < 50),
        ("Guthaben", "0 $", m.get("guthaben", "-"), m.get("guthaben_null")),
    ]
    return zeilen


HAEUFIGSTE = "haeufigste je Rolle und Minute"


def _treue_text(tu: dict | None, nur: str | None = None) -> str:
    if tu is None:
        return "-"
    teile = []
    for name, u in tu["urteile"].items():
        if nur is not None and name != nur:
            continue
        teile.append(f"{name}: " + ("nicht anlegbar" if u is None else
                                    f"{u['treffer_pp']:+.1f} pp Treffer, {u['wert_pkt']:+.2f} Pkt Wert"))
    return "; ".join(teile)


def markdown(m: dict) -> str:
    z = tor(m)
    erreicht = all(e is True for *_, e in z)
    t = m.get("treue") or {}
    out = [f"# Abnahme 035 - Messung ({time.strftime('%d.%m.%Y %H:%M')})", "",
           f"**{'TOR ERREICHT' if erreicht else 'TOR NICHT ERREICHT'}** (Teil 1 bis 3 ohne die Abo-Runde)", "",
           "| Mass | Soll | Ist | |", "|---|---|---|---|"]
    out += [f"| {a} | {s} | {i} | {'✔' if e else '–' if e is None else '✘'} |" for a, s, i, e in z]
    if t:
        out += ["", "## Challenger-Treue", "", f"{t['n']} Momente aus {t['partien']} Pruefpartien. Reihenfolge: "
                f"**{t['reihenfolge']}** bleibt.", "",
                "| Politik | anlegbar | Treffer | locker | Sieger | Challenger | Sieger+Chall. | Wert (DR, Pkt) |",
                "|---|---:|---:|---:|---:|---:|---:|---:|"]
        pc = lambda x: "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.1f} %"
        for name, r in t["politiken"].items():
            out.append(f"| {name} | {pc(r['anlegbar'])} | {pc(r['treffer'])} | {pc(r['treffer_locker'])} | "
                       f"{pc(r['treffer_sieger'])} | {pc(r['treffer_challenger'])} | {pc(r['treffer_sieger_challenger'])} | "
                       f"{r['wert_dr']:+.2f} ± {r['wert_dr_se']:.2f} |")
        # Auftrag 036: die Warnungen - wie oft, und sagen sie etwas vorher?
        out += ["", f"Gefahr (Auftrag 036): gefahr_schwelle = {gefahr_schwelle()} (wissen/kern.toml)"
                + (f"; gewaehlt mit gefahr_schwelle.py: {m['gefahr_schwelle']}" if m.get("gefahr_schwelle") else
                   " - werkzeuge/challenger/gefahr_schwelle.py ist noch nicht gelaufen"), ""]
        for name, r in t["politiken"].items():
            if "warnungen" in r:
                out.append(f"- {name}: Warnungen {pc(r['warnungen'])}, Tod in 60 s nach Warnung "
                           f"{pc(r['warnung_tod60'])}, ohne Warnung {pc(r.get('ohne_warnung_tod60'))}, "
                           f"Formen {r['formen']}")
        out += ["", "Beispiele:", ""]
        for b in t.get("beispiele", []):
            out.append(f"- {b['minute']} min, {b['rolle']}, {b['liga']}, {'Sieg' if b['sieg'] else 'Niederlage'} - "
                       f"{b['lage']}. Coach: „{b['coach']}“ - der Spieler: {b['spieler']}"
                       f"{' (Treffer)' if b['treffer'] else ''}.")
    v = (m.get("verdrahtung") or {}).get("gesamt") or {}
    if v.get("still_fehl") or v.get("basis_fehl"):
        out += ["", "## Fehlfaelle Stillstand und Basis (Auftrag 036, je eine Zeile)", "",
                "| Partie | Art | Zeit | was fehlte | zuletzt gesagt |", "|---|---|---|---|---|"]
        for f_ in v.get("still_fehl", []):
            out.append(f"| {f_['stamm']} | Stillstand{' (Basis)' if f_['basis'] else ''} | {f_['ab']}-{f_['bis']} | "
                       f"keine positive Anweisung | {f_['zuletzt']} |")
        for f_ in v.get("basis_fehl", []):
            out.append(f"| {f_['stamm']} | Basis ({'Respawn' if f_['respawn'] else 'Ankunft'}) | {f_['zeit']} | "
                       f"kein Kauf-Satz (zuletzt {f_['kauf_zuletzt']}) | {f_['zuletzt']} |")
    s = m.get("szenarien")
    if s:
        out += ["", "## Szenarien (--kern makro)", "",
                f"{s['makro']['gruen']} gruen / {s['makro']['gruen'] + s['makro']['rot']} geprueft "
                f"(--kern neu: {s['neu']['gruen']} / {s['neu']['gruen'] + s['neu']['rot']})", "",
                "| Szenario | makro | neu | warum rot (makro) | Beurteilung (phase6_bericht.md) |", "|---|---|---|---|---|"]
        gr = s.get("gruende") or {}
        for sid, (mk, nu) in sorted(s["vergleich"].items()):
            warum = "; ".join(gr.get(sid, []))[:200].replace("|", "/")
            out.append(f"| {sid} | {mk} | {nu} | {warum} | |")
    return "\n".join(out) + "\n"


def gefahr_schwelle() -> str:
    try:
        import tomllib
        return str(tomllib.loads((WURZEL / "wissen" / "kern.toml").read_text(encoding="utf-8"))
                   ["makro_gehirn"].get("gefahr_schwelle", "-"))
    except Exception:
        return "-"


def gefahr_schwelle_kurz() -> str | None:
    """Die Zahlen aus werkzeuge/challenger/gefahr_schwelle.py (buecher/challenger/gefahr_schwelle.json)."""
    try:
        g = json.loads((BUCH / "gefahr_schwelle.json").read_text(encoding="utf-8"))
    except Exception:
        return None
    a = g["alle"]
    return (f"{g['schwelle']:.3f}, Warnungen {100 * a['anteil']:.1f} %, Tod mit/ohne Warnung "
            f"{100 * a['tod_mit']:.1f} / {100 * a['tod_ohne']:.1f} %, Faktor {a['faktor']:.2f}"
            + ("" if g["erreicht"] else " - ZIEL NICHT ERREICHT"))


def szenarien(schnell: bool) -> dict:
    ergebnis = {}
    for kern in ("makro", "neu"):
        ziel = BUCH / f"szenarien_{kern}_035.json"
        _lauf(["werkzeuge/szenarien.py", "--kern", kern, "--json", str(ziel)])
        ergebnis[kern] = json.loads(ziel.read_text(encoding="utf-8")) if ziel.exists() else {"gruen": 0, "rot": 0}
    rot = lambda e: {i for d in (e.get("je_datei") or {}).values() for i in d["rot"]}
    gruen = lambda e: {i for d in (e.get("je_datei") or {}).values() for i in d["gruen"]}
    r_m, r_n, g_m, g_n = rot(ergebnis["makro"]), rot(ergebnis["neu"]), gruen(ergebnis["makro"]), gruen(ergebnis["neu"])
    wichtig = r_m | r_n | set(BEKANNT_ROT)
    stand = lambda sid, r, g: "rot" if sid in r else "gruen" if sid in g else "-"
    return {"makro": {k: ergebnis["makro"].get(k) for k in ("gruen", "rot", "uebersprungen")},
            "neu": {k: ergebnis["neu"].get(k) for k in ("gruen", "rot", "uebersprungen")},
            "vergleich": {sid: (stand(sid, r_m, g_m), stand(sid, r_n, g_n)) for sid in sorted(wichtig)},
            # 036: warum rot unter makro (szenarien.py --json schreibt die Verstoesse)
            "gruende": {sid: g for d in (ergebnis["makro"].get("je_datei") or {}).values()
                        for sid, g in (d.get("gruende") or {}).items()}}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    n = args[args.index("--n") + 1] if "--n" in args else "30000"
    start = time.strftime("%Y-%m-%dT%H:%M")
    m: dict = {"start": start}
    m["gefahr_schwelle"] = gefahr_schwelle_kurz()
    if m["gefahr_schwelle"] is None:
        print("!! buecher/challenger/gefahr_schwelle.json fehlt - zuerst python werkzeuge/challenger/gefahr_schwelle.py "
              "(Auftrag 036); gemessen wird mit dem Wert aus kern.toml", flush=True)
    m["gehirn_laufzeit"] = gehirn_laufzeit()
    if "--ohne-generalprobe" not in args:
        code, aus = _lauf(["werkzeuge/generalprobe.py", "--minuten", "2.5"])
        m["generalprobe"] = {"rueckgabe": code, "ende": aus.strip().splitlines()[-12:]}
    code, _ = _lauf(["werkzeuge/makro_messen.py"] + (["2026-09-30_091311", "2026-09-30_134020", "2026-09-29_231200"]
                                                    if "--schnell" in args else []))
    v = WURZEL / "buecher" / "protokolle" / "proben" / "makro_035" / "ergebnis.json"
    m["verdrahtung"] = json.loads(v.read_text(encoding="utf-8")) if v.exists() else {}
    _lauf(["werkzeuge/challenger/treue.py", "--n", n])
    t = BUCH / "treue.json"
    if t.exists():
        m["treue"] = json.loads(t.read_text(encoding="utf-8"))
        m["treue_urteil"] = treue_urteil(m["treue"])
    m["szenarien"] = szenarien("--schnell" in args)
    code, aus = _lauf(["werkzeuge/guthaben.py", "--seit", start])
    zeile = next((z for z in aus.splitlines() if z.startswith("Guthaben")), "Guthaben: ?")
    m["guthaben"] = zeile
    m["guthaben_null"] = "0,00 $" in zeile or "0.00 $" in zeile
    AUS_JSON.write_text(json.dumps(m, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    AUS_MD.write_text(markdown(m), encoding="utf-8")
    print(markdown(m))
    teil12 = all(e is True for a, *_, e in tor(m) if a != "Guthaben")
    print(("Teil 1 und 2 stehen - die Abo-Runde (Teil 3.3) darf laufen:\n" if teil12 else
           "Teil 1 und 2 stehen NICHT - die Abo-Runde (Teil 3.3) wartet. Sie liefe so:\n")
          + "  python werkzeuge/nachspiel_abdeckung.py laufen 2026-09-30_091311 2026-09-30_134020 2026-09-26_164809 "
            "--aus buecher/protokolle/proben/abo_035\n  (Claude formt dann die Saetze - Abo oder API nach [llm]; "
            "danach werkzeuge/kritik_mehrheit.py vorbereiten/auswerten)")
    print(f"-> {AUS_MD}\n-> {AUS_JSON}")


if __name__ == "__main__":
    main()
