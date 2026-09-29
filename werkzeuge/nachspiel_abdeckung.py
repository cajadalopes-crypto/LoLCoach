"""Auftrag 016, 6: Messen ohne Carlos - Nachspielen durch den Live-Weg, mit dem echten Strategen (Abo) und Carlos'
echten Fragen zur echten Zeit (aus `<stamm>_sprechtaste.log`). Zwei Schritte:

  laufen      spielt die Aufnahme nach und schreibt alles Gesprochene samt Lage und die Wahrheit der Partie
              (Flash-Timer der Gegner, Sichtbarkeit des Junglers, Basis, Tod) nach `<aus>/<stamm>.json`
  auswerten   Abdeckung (neues Hauptmass), Sicherheit und das lesbare Protokoll
              `buecher/protokolle/NACHSPIEL_<stamm>.md`

    python werkzeuge/nachspiel_abdeckung.py laufen 2026-09-29_133448 [--stub] [--aus <ordner>]
    python werkzeuge/nachspiel_abdeckung.py auswerten 2026-09-29_133448 [--aus <ordner>] [--vorher <ordner>]

`laufen` benutzt nur, was schon vor Auftrag 016 da war - so laeuft derselbe Schritt auf dem alten Stand (vorher).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(HIER.parent))
import nachspielen as ns  # noqa: E402

AUS = HIER.parent / "stratege_probe_016"
PROTOKOLLE = HIER.parent / "buecher" / "protokolle"
FLASH_FENSTER_S = 60.0       # ein gesehener Flash gilt als angesagt, wenn ihn ein Satz so lange danach nennt
JUNGLER_OHNE_S = 20.0        # Wiedersichtung: so lange ohne Sicht
JUNGLER_FENSTER_S = 8.0      # ... und so lange danach genannt
BACK_VOR_S, BACK_NACH_S = 45.0, 20.0     # die Kette zu einem Back: Satz so lange vor / nach der Ankunft in der Basis
LANE_AB_S, LANE_BIS_S = 90.0, 840.0      # Lane-Phase fuer die Stille
STILLE_SOLL_S = 45.0


# --- Schritt 1: laufen -----------------------------------------------------------------------------------------------

def _kill_jetzt(b) -> list[str]:
    """Die sichtbaren Gegner, die dein voller Combo jetzt toetet (wie denker._combo: 10 % Reserve)."""
    from lolcoach import combo, rechnung
    aus = []
    if b is None or b.partie is None or b.ich is None or not combo.kann(b.ich.champion_id):
        return aus
    for g in b.gegner:
        if g.s.tot or not g.sichtbar or g.leben is None:
            continue
        try:
            dmg = combo.schaden(b.ich, b.partie.werte, b.partie.raenge, b.bereit, g.s, g.leben)
        except Exception:
            dmg = None
        if dmg and dmg >= 1.1 * g.leben * rechnung.max_leben(g.s):
            aus.append(g.champion)
    return aus


def laufen(stamm: str, stub: bool = False, aus: Path = AUS) -> Path:
    import fuehrmass
    from lolcoach import stratege_live
    if not stub:
        stratege_live.AufzeichnungsStub = lambda *a, **k: stratege_live.claude_strom     # der echte Weg (Abo)
    fragen = [(f["zeit"], f["text"], i) for i, f in enumerate(fuehrmass.fragen_aus_log(stamm))]
    gesprochen, takte, flashes = [], [], {}
    gesehen = [0]
    info = {}
    letzte = [-1e9]

    def beim_takt(p, werk, kern, plan):
        m = kern.m
        b = m.b if m is not None else None
        if p.ich and not info:
            g = p.gegenueber()
            info.update(champion=p.ich.champion, gegner=g.champion if g else None, team=p.mein_team)
        neu = plan.gesagt[gesehen[0]:]
        gesehen[0] = len(plan.gesagt)
        if neu:
            try:
                vorn = kern.vorn()
            except Exception:
                vorn = {}
            kill = _kill_jetzt(b)
            gleben = {g.champion: g.leben for g in (b.gegner if b is not None else []) if g.sichtbar}
            for a in neu:
                gesprochen.append({"zeit": a.gesprochen if a.gesprochen is not None else p.zeit, "text": a.text,
                                   "schluessel": a.schluessel, "ganz": a.ganz,
                                   "leben": None if m is None or m.leben is None else round(m.leben, 2),
                                   "verboten": bool(vorn.get("verboten")), "kill": kill, "gegner_leben": gleben,
                                   "modus": kern.modus.aktuell, "gold": int(p.gold or 0) if p.gold is not None else None})
        lb = getattr(kern, "_lagebild", None)
        zb = getattr(lb, "zauber", None)
        if zb is not None and p.ich:
            feinde = {s.name for s in p.gegner()}
            for t in zb.timer.values():
                if t.zauber == "SummonerFlash" and t.name in feinde:
                    schl = f"{t.name}|{round(t.seit)}"
                    if schl not in flashes:
                        flashes[schl] = {"champion": t.champion, "seit": t.seit, "erkannt": p.zeit,
                                         "zurueck": t.zurueck, "quelle": getattr(t, "quelle", None)}
        if p.zeit - letzte[0] >= 0.5 and p.ich:
            letzte[0] = p.zeit
            j = b.jungler if b is not None else None
            ln = b.lane if b is not None else None
            takte.append({"zeit": round(p.zeit, 1), "tot": bool(p.ich.tot),
                          "bereich": m.bereich if m is not None else None,
                          "modus": kern.modus.aktuell, "leben": None if m is None or m.leben is None else round(m.leben, 2),
                          "jungler": None if j is None else {"name": j.champion, "sichtbar": bool(j.sichtbar),
                                                              "tot": bool(j.s.tot), "ort": j.ort,
                                                              "ankunft": j.ankunft},
                          "lane": None if ln is None else {"name": ln.champion, "sichtbar": bool(ln.sichtbar),
                                                           "tot": bool(ln.s.tot), "ort": ln.ort, "ankunft": ln.ankunft}})

    t0 = time.monotonic()
    lauf = ns.durchspielen(ns.pfad_zu(stamm), beim_takt=beim_takt, fragen=fragen, stratege="stub")
    ms = lauf.stratege
    aus.mkdir(parents=True, exist_ok=True)
    ziel = aus / f"{stamm}.json"
    ziel.write_text(json.dumps({
        "stamm": stamm, "stub": stub, "info": info, "dauer_s": round(time.monotonic() - t0),
        "minuten": round(lauf.sekunden_mit_daten / 60, 1), "gesprochen": gesprochen, "takte": takte,
        "flashes": list(flashes.values()), "antworten": lauf.antworten,
        "stratege": ms.protokoll if ms is not None else [],
        "notizen": [f for f in fuehrmass.fragen_aus_log(stamm) if f["text"].lower().lstrip(" ,.").startswith("notiz")
                    or "notiz" in f["text"].lower()[:40]],
    }, ensure_ascii=False, default=str, indent=0), encoding="utf-8")
    return ziel


# --- Schritt 2: auswerten --------------------------------------------------------------------------------------------

def _uhr(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


def _nennt(text: str, name: str) -> bool:
    from lolcoach import stratege
    return bool(stratege._namen_in(text, [name]))


def _nur_gesagt(g: dict) -> dict:
    """Bei einer Antwort zaehlt nur, was der Coach sagt - nicht Carlos' Frage davor („Frage“ – Antwort)."""
    if g["schluessel"] == "antwort" and "“ – " in g["text"]:
        return dict(g, text=g["text"].split("“ – ", 1)[1])
    return g


def abdeckung(d: dict) -> dict:
    """Die fuenf Groessen aus Auftrag 016, 6.3 (ohne die Notizen - die urteilt der Kritiker) und die Sicherheit."""
    from lolcoach import stratege
    ges = sorted((_nur_gesagt(g) for g in d["gesprochen"]), key=lambda x: x["zeit"])
    takte = d["takte"]
    # 1. Flash
    fl = []
    for f in d["flashes"]:
        start = f["erkannt"]
        treffer = next((g for g in ges if start - 1.0 <= g["zeit"] <= min(start + FLASH_FENSTER_S, f["zurueck"])
                        and "flash" in g["text"].lower() and _nennt(g["text"], f["champion"])), None)
        fl.append({"zeit": start, "champion": f["champion"], "gesagt": treffer["text"] if treffer else None,
                   "nach_s": round(treffer["zeit"] - start, 1) if treffer else None})
    # 2. Jungler-Wiedersichtungen nach >= 20 s
    jw, zuletzt, war = [], None, False
    for t in takte:
        j = t.get("jungler")
        if j is None:
            continue
        if j["sichtbar"] and not j["tot"]:
            if not war and t["zeit"] >= LANE_AB_S and (zuletzt is None or t["zeit"] - zuletzt >= JUNGLER_OHNE_S):
                treffer = next((g for g in ges if t["zeit"] - 1.0 <= g["zeit"] <= t["zeit"] + JUNGLER_FENSTER_S
                                and _nennt(g["text"], j["name"])), None)
                jw.append({"zeit": t["zeit"], "name": j["name"], "ort": j["ort"], "ohne_s": None if zuletzt is None
                           else round(t["zeit"] - zuletzt), "tot_ich": t["tot"],
                           "gesagt": treffer["text"] if treffer else None})
            zuletzt, war = t["zeit"], True
        else:
            war = False
    # 3. Backs mit Kette: Ankunft in der Basis lebend (nicht nach dem Respawn), ab 1:30
    backs, vorher_t = [], None
    for i, t in enumerate(takte):
        basis = t["bereich"] == "basis_eigen"
        # die Minimap flackert: eine Ankunft zaehlt, wenn du >= 4 s in der Basis bleibst
        bleibt = all(x["bereich"] in ("basis_eigen", None) for x in takte[i:i + 8])
        respawn = any(x["tot"] for x in takte[max(0, i - 20):i + 1])          # nach dem Tod ist es kein Back
        if vorher_t is not None and basis and bleibt and vorher_t["bereich"] not in (None, "basis_eigen") \
                and not respawn and t["zeit"] >= LANE_AB_S:
            kette = [g for g in ges if t["zeit"] - BACK_VOR_S <= g["zeit"] <= t["zeit"] + BACK_NACH_S
                     and stratege.kette(g["text"])]
            backs.append({"zeit": t["zeit"], "gesagt": kette[0]["text"] if kette else None,
                          "saetze": [g["text"] for g in ges if t["zeit"] - BACK_VOR_S <= g["zeit"] <= t["zeit"] + BACK_NACH_S
                                     and g["schluessel"] != "antwort"][-3:]})
        if t["bereich"] is not None:
            vorher_t = t
    rufe = [g for g in ges if g["schluessel"] != "antwort" and stratege.back_ruf(g["text"])]
    # 4. Laengste Stille in der Lane-Phase, solange du lebst
    stille, lang = 0.0, []
    zeiten = [g["zeit"] for g in ges]
    seg = None
    segmente = []
    for t in takte:
        lebt = not t["tot"] and LANE_AB_S <= t["zeit"] <= LANE_BIS_S
        if lebt and seg is None:
            seg = [t["zeit"], t["zeit"]]
        elif lebt:
            seg[1] = t["zeit"]
        elif seg is not None:
            segmente.append(seg)
            seg = None
    if seg is not None:
        segmente.append(seg)
    for a, b in segmente:
        punkte = [a] + [z for z in zeiten if a < z < b] + [b]
        for x, y in zip(punkte, punkte[1:]):
            if y - x > stille:
                stille = y - x
            if y - x > STILLE_SOLL_S:
                lang.append((round(x), round(y)))
    # Sicherheit
    sich = []
    for g in ges:
        for grund in stratege.sicherheit(g["text"], {"vorn": {"verboten": g["verboten"]}, "kill": g["kill"],
                                                     "gegner_leben": g["gegner_leben"]}):
            sich.append({"zeit": g["zeit"], "text": g["text"], "schluessel": g["schluessel"], "grund": grund})
    return {"flash": fl, "jungler": jw, "backs": backs, "back_rufe": [
        {"zeit": g["zeit"], "text": g["text"], "kette": stratege.kette(g["text"])} for g in rufe],
        "stille_max": round(stille), "stille_lang": lang, "sicherheit": sich}


def _quote(liste: list, schl: str = "gesagt") -> str:
    n = len(liste)
    k = sum(1 for x in liste if x.get(schl))
    return f"{k}/{n} ({100 * k / n:.0f} %)" if n else "– (keine)"


def kennzahlen(a: dict) -> dict:
    return {"flash": _quote(a["flash"]), "jungler": _quote(a["jungler"]), "backs": _quote(a["backs"]),
            "back_rufe": _quote(a["back_rufe"], "kette"), "stille": f"{a['stille_max']} s",
            "sicherheit": len(a["sicherheit"])}


def auswerten(stamm: str, aus: Path = AUS, vorher: Path | None = None) -> tuple[Path, dict]:
    d = json.loads((aus / f"{stamm}.json").read_text(encoding="utf-8"))
    a = abdeckung(d)
    k = kennzahlen(a)
    kv = None
    if vorher is not None and (vorher / f"{stamm}.json").exists():
        kv = kennzahlen(abdeckung(json.loads((vorher / f"{stamm}.json").read_text(encoding="utf-8"))))
    info = d["info"]
    z = [f"# Nachspiel {stamm}", "",
         f"{info.get('champion', '?')} gegen {info.get('gegner', '?')} · {d['minuten']} min mit Daten · nachgespielt "
         f"durch den Live-Weg (Kern, Sprechplan, Makro-Stratege {'mit Stub' if d['stub'] else 'über das Abo'}), "
         f"Carlos' Fragen zur echten Zeit aus dem Sprechtasten-Log (`werkzeuge/nachspiel_abdeckung.py`).", "",
         "## Abdeckung", "",
         "| Größe | Soll | " + ("vorher | " if kv else "") + "jetzt |",
         "|---|---|" + ("---|" if kv else "") + "---|"]
    for schl, name, soll in (("flash", "gesehene gegnerische Flashes, angesagt", "100 %"),
                             ("jungler", "Jungler-Wiedersichtungen nach ≥ 20 s, angesagt", "≥ 90 %"),
                             ("backs", "Backs mit Kette (Kauf + Ziel)", "100 %"),
                             ("back_rufe", "Back-Rufe mit Kette", "100 %"),
                             ("stille", "längste Stille in der Lane-Phase (lebend)", "≤ 45 s"),
                             ("sicherheit", "Sicherheit: Vorwärts unter R1, Angriff ohne Kill-Check, innere Begriffe",
                              "0")):
        z.append(f"| {name} | {soll} | " + (f"{kv[schl]} | " if kv else "") + f"{k[schl]} |")
    z.append("")
    fehlt = [f"{_uhr(x['zeit'])} Flash {x['champion']}" for x in a["flash"] if not x["gesagt"]]
    fehlt += [f"{_uhr(x['zeit'])} Jungler {x['name']} ({x['ort']})" for x in a["jungler"] if not x["gesagt"]]
    fehlt += [f"{_uhr(x['zeit'])} Back ohne Kette" for x in a["backs"] if not x["gesagt"]]
    fehlt += [f"{_uhr(x)}–{_uhr(y)} still" for x, y in a["stille_lang"]]
    if fehlt:
        z += ["**Nicht abgedeckt:** " + " · ".join(fehlt), ""]
    if a["sicherheit"]:
        z += ["**Sicherheit verletzt:**", ""] + [f"- {_uhr(x['zeit'])} `{x['schluessel']}` „{x['text']}“ – {x['grund']}"
                                                  for x in a["sicherheit"]] + [""]
    # Minute fuer Minute
    z += ["## Minute für Minute", "",
          "Ungefragt: jeder Satz, den der Coach jetzt sagen würde (Kern `kern:`, Stratege `stratege:`). **Frage**: "
          "Carlos' echte Frage und die Antwort. *Notiz* steht als Maßstab dabei.", ""]
    ges = sorted(d["gesprochen"], key=lambda x: x["zeit"])
    notizen = {round(n["zeit"]): n["text"] for n in d.get("notizen", [])}
    minute = -1
    for g in ges:
        mi = int(g["zeit"] // 60)
        if mi != minute:
            minute = mi
            z += ["", f"### Minute {mi}", ""]
        lage = (f" · *{g['modus'] or '–'}, Leben {'?' if g['leben'] is None else int(round(g['leben'] * 100))} %, "
                f"{g['gold'] if g['gold'] is not None else '?'} Gold" + (", R1" if g["verboten"] else "")
                + (f", Kill: {', '.join(g['kill'])}" if g.get("kill") else "") + "*")
        if g["schluessel"] == "antwort":
            z.append(f"- {_uhr(g['zeit'])} **Frage** {g['text']}{lage}")
        else:
            wer = "Stratege" if g["schluessel"].startswith("stratege:") else "Kern" if g["schluessel"].startswith(
                "kern:") else g["schluessel"]
            z.append(f"- {_uhr(g['zeit'])} {wer}: „{g['text']}“" + ("" if g["ganz"] is not False else " *(abgebrochen)*")
                     + lage)
    if notizen:
        z += ["", "## Carlos' Notizen in dieser Partie", ""] + [f"- {_uhr(t)} {x}" for t, x in sorted(notizen.items())]
    verw = [(e["zeit"], v) for e in d["stratege"] for x in e.get("versuche", []) for v in x.get("verworfen", [])]
    n_auf = len(d["stratege"])
    n_kern = sum(1 for e in d["stratege"] if e.get("quelle") == "kern")
    z += ["", f"## Stratege: {n_auf} Aufrufe, {n_kern}× sprach der Kern-Ersatz, {len(verw)} Sätze verworfen", ""]
    z += [f"- {_uhr(t)} „{v['satz']}“ – {'; '.join(v['gruende'])}" for t, v in verw]
    PROTOKOLLE.mkdir(parents=True, exist_ok=True)
    ziel = PROTOKOLLE / f"NACHSPIEL_{stamm}.md"
    ziel.write_text("\n".join(z) + "\n", encoding="utf-8")
    (aus / f"{stamm}_abdeckung.json").write_text(json.dumps({"kennzahlen": k, "vorher": kv, "abdeckung": a},
                                                            ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return ziel, k


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opt = {a.split("=", 1)[0]: (a.split("=", 1)[1] if "=" in a else True) for a in sys.argv[1:] if a.startswith("--")}
    aus = Path(opt["--aus"]) if "--aus" in opt else AUS
    was, staemme = args[0], args[1:]
    for stamm in staemme:
        if was == "laufen":
            print(laufen(stamm, stub="--stub" in opt, aus=aus), flush=True)
        else:
            print(auswerten(stamm, aus, Path(opt["--vorher"]) if "--vorher" in opt else None), flush=True)


if __name__ == "__main__":
    main()
