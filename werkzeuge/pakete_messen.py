"""Auftrag 025, 4 (Buch 15, Teil 7): die automatischen Masse der lebendigen Arbeitspakete - ohne Claude, ohne Kritiker.

    python werkzeuge/pakete_messen.py [stamm ...]          (ohne Angabe: die acht Testpartien)
    python werkzeuge/pakete_messen.py --eichen [stamm ...]  schreibt die Eintrittsquoten der Erahnung nach
                                                            wissen/events.toml (Buch 15, 0.2: unter 60 % still)

Je Partie ein Nachspiel des Kerns (werkzeuge/nachspielen.py), parallel. Gemessen (Soll aus Buch 15, 7):
  - Paket-Abdeckung: Anteil der Takte, in denen du lebst, nicht kaempfst und nicht in der Basis bist, mit aktivem Paket
    (und davon angesagt)                                                                     Soll >= 90 %
  - Abbruch-Reaktion: Ungueltig-Ereignisse (Objective weg, Partner tot, sicheres Fenster < 0 bei einem Vorwaerts-Paket)
    - in <= 2 s beendet oder gewarnt?                                                       Soll >= 95 %
  - Budget-Treue: jedes Vorwaerts-Paket mit sicherem Fenster F >= 3 s - kam vor Ablauf ein sichtbarer Gegner auf
    <= 800 an dich heran (Fehler)? Starbst du darin (gefaehrlich)?                           Fehler <= 5 %, gefaehrlich 0
  - Back-Puenktlichkeit: Back-Paket erledigt (Basis) spaetestens Back-Frist + Kanal + 1 s?   Soll >= 80 %
  - Chancen genutzt: Mitspieler-Kampf in <= 8 s, Rechner nicht "klar hinten", Leben >= 50 % - HILFE oder "warum
    nicht" binnen 5 s?                                                                       Soll >= 70 %
  - Event-Abdeckung: wichtige Events (Objective bald/da, Turm faellt, Flash, Lane-Gegner weg, Mitspieler-Kampf nah) -
    binnen 15 s ein Satz, der sie aufgreift (Name/Objective/Turm im Satz, oder ein Paket-Uebergang)?  Soll >= 85 %
  - Erahnung: je Typ die Eintrittsquote (siehe unten)                                         Soll >= 60 %
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TESTPARTIEN = ("2026-09-28_101426", "2026-09-28_192113", "2026-09-29_133448", "2026-09-29_183125",
               "2026-09-26_125902", "2026-09-26_164809", "2026-09-26_120049", "2026-09-29_231200")
WICHTIG = ("OBJ_BALD", "OBJ_DA", "TURM_FAELLT", "FLASH_WEG", "TP_WEG", "LANE_WEG", "KAMPF")
AUS = Path(__file__).resolve().parent.parent / "buecher" / "protokolle" / "proben" / "pakete_025"


def _lauf(stamm: str) -> dict:
    """Ein Nachspiel; je Takt ein kleiner Datensatz."""
    import nachspielen as ns
    from lolcoach.bewertung import abstand
    from lolcoach.kern.pakete import hilfe_kandidat
    takte, events, pakete = [], [], []
    gesehen_ende: set = set()

    def bt(p, werk, kern, plan):
        m = kern.m
        if m is None or m.b is None:
            return
        b = m.b
        modus = kern.modus.aktuell
        hilfe = None
        if not m.tot and modus not in ("KAMPF", "TOT", "BASIS"):
            try:
                h = hilfe_kandidat(kern, m, modus, None)
                hilfe = None if h is None else h.daten.get("partner")
            except Exception:
                hilfe = None
        u = kern.uhren
        nah = min((abstand(g.pos, b.pos) for g in b.gegner if g.sichtbar and not g.s.tot and g.pos is not None
                   and b.pos is not None), default=None)
        pl = kern.fuehrer.plan
        takte.append({"t": round(p.zeit, 2), "modus": modus, "tot": bool(m.tot), "leben": m.leben,
                      "plan": pl.art if pl is not None else None,
                      "basis": m.bereich == "basis_eigen", "paket": kern.pakete.stand(p.zeit),
                      "fenster": None if u is None else u.fenster, "wer": None if u is None else u.wer,
                      "back_bis": None if u is None else u.back_spaetestens, "nah": nah, "hilfe": hilfe,
                      "lane_ort": b.lane.ort if b.lane is not None else None,
                      "lane_sicht": bool(b.lane.sichtbar) if b.lane is not None else None,
                      "jungler_nah": (abstand(b.jungler.pos, b.pos) if b.jungler is not None and b.jungler.sichtbar
                                      and b.jungler.pos is not None and b.pos is not None else None)})
        for e in kern.events_takt:
            d = {k: v for k, v in e.daten if isinstance(v, (int, float, str, bool)) or v is None}
            if "pos" in dict(e.daten) and dict(e.daten)["pos"] is not None:
                d["pos"] = list(dict(e.daten)["pos"])
            events.append({"typ": e.typ, "ort": e.ort, "wer": list(e.beteiligte), "t": round(e.zeit, 1), **d})
        for pk in list(kern.pakete.fertig):
            if id(pk) not in gesehen_ende:
                gesehen_ende.add(id(pk))
                pakete.append({"typ": pk.typ, "art": pk.art, "ziel": pk.ziel, "start": pk.start, "gesagt": pk.gesagt,
                               "ende": pk.ende, "verlauf": pk.verlauf, "partner": pk.partner, "obj": pk.obj})

    t0 = time.monotonic()
    lauf = ns.durchspielen(ns.pfad_zu(stamm), beim_takt=bt)
    gesagt = [{"t": round(ns.gesprochen_um(a), 1), "text": a.text, "schl": a.schluessel} for a in lauf.gesagt]
    return {"stamm": stamm, "takte": takte, "events": events, "pakete": pakete, "gesagt": gesagt,
            "dauer_s": round(time.monotonic() - t0)}


def _quote(ja: int, n: int) -> str:
    return f"{ja}/{n} ({100 * ja / n:.0f} %)" if n else "- (keine)"


def auswerten(d: dict) -> dict:
    takte, events, pakete, gesagt = d["takte"], d["events"], d["pakete"], d["gesagt"]
    # Paket-Abdeckung
    frei = [x for x in takte if not x["tot"] and x["modus"] not in ("KAMPF", "TOT") and not x["basis"]]
    mit = [x for x in frei if x["paket"] is not None]
    gesagt_p = [x for x in mit if x["paket"].get("gesagt")]
    # Abbruch-Reaktion. Wahrheit aus dem Bild, nicht aus der eigenen Uhr: waehrend eines Vorwaerts-Pakets kommt ein
    # sichtbarer Gegner neu auf <= 1000 an dich heran. Reagiert: das Paket endet oder eine Warnung kommt in [-3, +2] s.
    faelle, ok = 0, 0
    vorn = ("TURM", "OBJECTIVE", "HILFE")
    for i in range(1, len(takte)):
        x, v = takte[i], takte[i - 1]
        pk = v["paket"]
        if pk is None or pk["typ"] not in vorn or x["tot"] or x["modus"] == "KAMPF" and v["modus"] == "KAMPF":
            continue
        if not (x["nah"] is not None and x["nah"] <= 1000 and (v["nah"] is None or v["nah"] > 1000)):
            continue
        faelle += 1
        t = x["t"]
        ende = any(t - 3.0 <= y["t"] <= t + 2.0 and (y["paket"] is None or y["paket"]["art"] != pk["art"])
                   for y in takte[max(0, i - 12):i + 8])
        warn = any(t - 3.0 <= s["t"] <= t + 2.0 and (s["schl"].startswith("kern:PAKET_")
                                                     or s["schl"] in ("kern:ZURUECK", "kern:RAUS")) for s in gesagt)
        ok += ende or warn
    for e in events:                                # Objective weg / Partner tot waehrend eines passenden Pakets
        for pk in pakete:
            if not (pk["start"] <= e["t"] <= (pk["verlauf"][-1][0] if pk["verlauf"] else pk["start"])):
                continue
            if (e["typ"] == "OBJ_GENOMMEN" and not e.get("wir") and pk["typ"] == "OBJECTIVE") or \
                    (e["typ"] == "TOD" and pk.get("partner") and pk["partner"] in e["wer"]):
                faelle += 1
                ende = pk["verlauf"][-1][0] if pk["verlauf"] else None
                ok += ende is not None and ende - e["t"] <= 2.0
    # Budget-Treue: Vorwaerts-Pakete mit Fenster >= 3 s beim Start
    budget_n = budget_f = budget_g = 0
    for pk in pakete:
        if pk["typ"] not in ("TURM", "WELLE", "OBJECTIVE", "HILFE", "WARTEN") or pk["art"] in (
                "FARMEN", "UNTER_TURM_FARMEN", "HALTEN", "HALTEN_UNTER_TURM", "WELLE_HALTEN"):
            continue
        start = next((x for x in takte if x["t"] >= pk["start"]), None)
        if start is None or start["fenster"] is None or start["fenster"] < 3.0:
            continue
        budget_n += 1
        bis = pk["start"] + start["fenster"]
        drin = [x for x in takte if pk["start"] < x["t"] <= bis]
        if any(x["nah"] is not None and x["nah"] <= 800 for x in drin):
            budget_f += 1
            if any(x["tot"] for x in takte if pk["start"] < x["t"] <= bis + 5.0):
                budget_g += 1
    # Back-Puenktlichkeit
    back_n = back_ok = 0
    for pk in pakete:
        if pk["typ"] != "BACK" or pk["ende"] != "ERLEDIGT":
            continue
        start = next((x for x in takte if x["t"] >= pk["start"]), None)
        if start is None or start["back_bis"] is None:
            continue
        back_n += 1
        ankunft = pk["verlauf"][-1][0]
        back_ok += ankunft <= start["back_bis"] + 8.0 + 1.0
    # Chancen genutzt: Episoden mit HILFE-Kandidat
    ch_n = ch_ok = 0
    letzte = -1e9
    for x in takte:
        if x["hilfe"] and x["t"] - letzte > 20.0:
            ch_n += 1
            letzte = x["t"]
            ch_ok += any(x["t"] <= y["t"] <= x["t"] + 5.0 and y["paket"] is not None and y["paket"]["typ"] == "HILFE"
                         for y in takte) or any(x["t"] <= s["t"] <= x["t"] + 5.0 and s["schl"] == "kern:PAKET_WARUM_NICHT"
                                                for s in gesagt)
    # Event-Abdeckung
    ev_n = ev_ok = 0
    for e in events:
        if e["typ"] not in WICHTIG or (e["typ"] == "KAMPF" and (e.get("weg") or 99) > 20):
            continue
        ev_n += 1
        worte = [w for w in e["wer"] if w] + ([e["ort"]] if e["typ"].startswith("OBJ") and e["ort"] else [])
        worte = [{"drache": "Drache", "herold": "Herold", "baron": "Baron", "larven": "Larven"}.get(w, w) for w in worte]
        if e["typ"] == "TURM_FAELLT":
            worte = ["Turm"]
        ev_ok += any(e["t"] - 1.0 <= s["t"] <= e["t"] + 15.0 and (s["schl"].startswith("kern:PAKET_") or any(
            w.lower() in s["text"].lower() for w in worte)) for s in gesagt)
    # Erahnung: Eintritt je Typ
    erahnt: dict = {}
    for e in events:
        if not e["typ"].startswith("ERAHNT_"):
            continue
        eta = float(e.get("eta") or 15.0)
        t, bis = e["t"], e["t"] + eta + 20.0
        if e["typ"] == "ERAHNT_KAMPF":
            ja = any(t <= f["t"] <= bis and (f["typ"] == "KAMPF" or (f["typ"] == "OBJ_GENOMMEN" and f["ort"] == e["ort"]))
                     for f in events)
        elif e["typ"] == "ERAHNT_GANK":
            ja = any(t <= x["t"] <= bis and x["jungler_nah"] is not None and x["jungler_nah"] <= 2500 for x in takte)
        elif e["typ"] == "ERAHNT_LANE_BACK":
            ja = any(t <= x["t"] <= t + 30.0 and x["lane_ort"] and "Basis" in x["lane_ort"] for x in takte) \
                or any(t <= f["t"] <= t + 30.0 and f["typ"] == "LANE_WEG" for f in events)
        elif e["typ"] == "ERAHNT_RUECKKEHR":
            ja = any(t + eta - 10.0 <= x["t"] <= bis and x["lane_sicht"] for x in takte)
        else:
            continue
        n, j = erahnt.get(e["typ"], (0, 0))
        erahnt[e["typ"]] = (n + 1, j + ja)
    return {"stamm": d["stamm"], "abdeckung": _quote(len(mit), len(frei)), "abdeckung_gesagt": _quote(len(gesagt_p), len(frei)),
            "abbruch": _quote(ok, faelle), "budget": f"{budget_f}/{budget_n} Fehler, {budget_g} gefährlich",
            "back": _quote(back_ok, back_n), "chancen": _quote(ch_ok, ch_n), "events": _quote(ev_ok, ev_n),
            "erahnt": {k: list(v) for k, v in erahnt.items()},
            "roh": {"frei": len(frei), "mit": len(mit), "gesagt": len(gesagt_p), "abbruch": [ok, faelle],
                    "budget": [budget_f, budget_n, budget_g], "back": [back_ok, back_n], "chancen": [ch_ok, ch_n],
                    "events": [ev_ok, ev_n]},
            "pakete_n": len(pakete)}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    staemme = args or list(TESTPARTIEN)
    AUS.mkdir(parents=True, exist_ok=True)
    from concurrent.futures import ProcessPoolExecutor
    t0 = time.monotonic()
    with ProcessPoolExecutor(len(staemme)) as ex:
        laeufe = list(ex.map(_lauf, staemme))
    ergebnisse = []
    summe = {"frei": 0, "mit": 0, "gesagt": 0, "abbruch": [0, 0], "budget": [0, 0, 0], "back": [0, 0],
             "chancen": [0, 0], "events": [0, 0]}
    erahnt: dict = {}
    for d in laeufe:
        (AUS / f"{d['stamm']}.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        r = auswerten(d)
        ergebnisse.append(r)
        for k in ("frei", "mit", "gesagt"):
            summe[k] += r["roh"][k]
        for k in ("abbruch", "budget", "back", "chancen", "events"):
            summe[k] = [a + b for a, b in zip(summe[k], r["roh"][k])]
        for typ, (n, j) in r["erahnt"].items():
            a, b = erahnt.get(typ, (0, 0))
            erahnt[typ] = (a + n, b + j)
        print(f"{r['stamm']}: Abdeckung {r['abdeckung']} (angesagt {r['abdeckung_gesagt']}), Abbruch {r['abbruch']}, "
              f"Budget {r['budget']}, Back {r['back']}, Chancen {r['chancen']}, Events {r['events']}, "
              f"Pakete {r['pakete_n']}", flush=True)
    g = {"abdeckung": _quote(summe["mit"], summe["frei"]), "abdeckung_gesagt": _quote(summe["gesagt"], summe["frei"]),
         "abbruch": _quote(*summe["abbruch"]),
         "budget": f"{summe['budget'][0]}/{summe['budget'][1]} Fehler, {summe['budget'][2]} gefährlich",
         "back": _quote(*summe["back"]), "chancen": _quote(*summe["chancen"]), "events": _quote(*summe["events"]),
         "erahnt": {k: _quote(j, n) for k, (n, j) in erahnt.items()}}
    print("GESAMT:", json.dumps(g, ensure_ascii=False), f"({time.monotonic() - t0:.0f} s)")
    (AUS / "ergebnis.json").write_text(json.dumps({"gesamt": g, "je_partie": ergebnisse}, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    if "--eichen" in sys.argv:
        from lolcoach.kern import events as ev
        zeilen = ["# Buch 15, 0.2 (Auftrag 025): Eintrittsquoten der Erahnung, gemessen von werkzeuge/pakete_messen.py",
                  f'stand = "{time.strftime("%d.%m.%Y")} an {len(staemme)} Aufnahmen: {", ".join(staemme)}"',
                  "still_unter = 0.6          # darunter bleibt ein Typ still (nie gesagt, nie abgewogen)", "",
                  "[erahnung]"]
        for typ, (n, j) in sorted(erahnt.items()):
            zeilen.append(f"{typ} = {{ quote = {j / n:.2f}, n = {n} }}" if n else f"# {typ}: n = 0")
        ev.WISSEN.write_text("\n".join(zeilen) + "\n", encoding="utf-8")
        print("geeicht ->", ev.WISSEN)


if __name__ == "__main__":
    main()
