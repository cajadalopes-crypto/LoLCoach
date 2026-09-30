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
               "2026-09-26_125902", "2026-09-26_164809", "2026-09-26_120049", "2026-09-29_231200", "2026-09-30_091311",
               "2026-09-30_134020")
# Auftrag 028, 5 (Sparprotokoll): waehrend der Arbeit nur diese drei, alle erst am Ende
ARBEIT = ("2026-09-30_091311", "2026-09-30_134020", "2026-09-29_231200")
WICHTIG = ("OBJ_BALD", "OBJ_DA", "TURM_FAELLT", "FLASH_WEG", "TP_WEG", "LANE_WEG", "KAMPF")
AUS = Path(__file__).resolve().parent.parent / "buecher" / "protokolle" / "proben" / "pakete_028"   # 025-027: pakete_0NN


def _lauf(stamm: str) -> dict:
    """Ein Nachspiel; je Takt ein kleiner Datensatz."""
    import nachspielen as ns
    from lolcoach.bewertung import abstand
    from lolcoach.kern.pakete import hilfe_kandidat
    takte, events, pakete = [], [], []
    gesehen_ende: set = set()

    sicher: list = []
    gesehen_g = [0]

    def bt(p, werk, kern, plan):
        m = kern.m
        neu, gesehen_g[0] = plan.gesagt[gesehen_g[0]:], len(plan.gesagt)
        if m is None or m.b is None:
            return
        b = m.b
        if neu:
            # Auftrag 028, 3/5: Sicherheit wie im Abo-Nachspiel (nachspiel_abdeckung) - jeder Satz jeder Quelle
            from lolcoach import stratege
            from nachspiel_abdeckung import _kill_jetzt
            lage = {"vorn": {"verboten": bool((kern.vorn() or {}).get("verboten"))}, "kill": _kill_jetzt(b),
                    "gegner_leben": {g.champion: g.leben for g in b.gegner if g.sichtbar}}
            for a in neu:
                txt = a.text.split("“ – ", 1)[-1] if a.schluessel == "antwort" else a.text
                for grund in stratege.sicherheit(txt, lage):
                    sicher.append({"t": round(p.zeit, 1), "schl": a.schluessel, "text": txt[:90], "grund": grund})
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
                      "plan": pl.art if pl is not None else None, "lane_phase": bool(m.lane_phase),
                      "front": m.welle.front if m.welle is not None else None, "lane_hier": m.lane_hier,
                      "pos": list(b.pos) if b.pos is not None else None,
                      "kauf": bool(getattr(b, "kauf", None) is not None and b.kauf.kaufen),
                      # der Recall-Kanal: 16 s nach dem Back-Ruf (wie herzschlag - er beginnt oft erst nach der Welle)
                      "back_ruf": bool(getattr(kern, "_back_rufe", None)) and p.zeit - kern._back_rufe[-1] <= 16.0,
                      "wir_nah": 1 + sum(1 for s, wo, *_ in b.mitspieler or [] if wo is not None and not s.tot
                                         and b.pos is not None and abstand(wo, b.pos) <= 1500),
                      "sie_nah": sum(1 for g in b.gegner if g.sichtbar and not g.s.tot and g.abstand is not None
                                     and g.abstand <= 1500),
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
    gesagt = [{"t": round(ns.gesprochen_um(a), 1), "text": a.text, "schl": a.schluessel, "thema": a.thema,
               "kat": getattr(a, "_kategorie", None)} for a in lauf.gesagt]
    return {"stamm": stamm, "takte": takte, "events": events, "pakete": pakete, "gesagt": gesagt,
            "sicherheit": sicher, "dauer_s": round(time.monotonic() - t0)}


def hoeren(d: dict, gesagt: list | None = None) -> dict:
    """Auftrag 027, 5: das Hauptmass - was Carlos HOERT (nicht das interne Paket).
      - Anweisungs-Luecke: Zeit (lebend, nicht KAMPF) ohne gueltige gesprochene positive Anweisung (gueltig bis ein
        Paket endet oder 30 s alt) - p90 und laengste Luecke.
      - Stillstand-Reaktion: >= 5 s am selben Fleck (nicht Kampf, nicht Recall-Kanal, nicht Basis) -> positive
        Anweisung in <= 2 s.
      - Basis-Reaktion: Brunnen (Ankunft oder Respawn) mit Gold fuer einen Kauf -> Kauf-Anweisung in <= 2 s.
      - Negativ allein: Saetze, die nur sagen, was man NICHT tun soll.
      - Hin und Her: zwei Plan-Saetze mit verschiedenem Ziel in < 5 s.
    `gesagt`: die gesprochenen Saetze eines anderen Laufs (API-Nachspiel), sonst die des Stub-Laufs."""
    from types import SimpleNamespace as NS
    from lolcoach.kern.herzschlag import START_S, negativ_allein, positiv
    from lolcoach.bewertung import abstand
    takte = d["takte"]
    g = gesagt if gesagt is not None else d["gesagt"]
    pos = sorted(s["t"] for s in g if positiv(NS(schluessel=s["schl"], text=s["text"])))
    enden = sorted(v[0] for pk in d["pakete"] for v in pk["verlauf"] if v[1] in ("ERLEDIGT", "ABGEBROCHEN", "BUDGET_AB"))
    luecken, cur, vor_t = [], 0.0, None
    import bisect
    for x in takte:
        # (die ersten 30 s zaehlen nicht: Einkauf und Briefing vor dem Spielbeginn, wie beim Stillstand)
        frei = not x["tot"] and x["modus"] not in ("KAMPF", "TOT") and x["t"] >= START_S
        dt = 0.0 if vor_t is None else min(1.0, x["t"] - vor_t)
        vor_t = x["t"]
        if not frei:
            if cur > 0:
                luecken.append(cur)
            cur = 0.0
            continue
        i = bisect.bisect_right(pos, x["t"]) - 1
        gueltig = False
        if i >= 0 and x["t"] - pos[i] <= 30.0:
            j = bisect.bisect_right(enden, pos[i])
            gueltig = not (j < len(enden) and enden[j] <= x["t"])
        if gueltig:
            if cur > 0:
                luecken.append(cur)
            cur = 0.0
        else:
            cur += dt
    if cur > 0:
        luecken.append(cur)
    lsort = sorted(luecken)
    p90 = lsort[int(0.9 * (len(lsort) - 1))] if lsort else 0.0
    # Stillstand
    still_n = still_ok = 0
    kauf_t = [s["t"] for s in g if "kauf" in s["text"].lower()]
    seit = None
    gemeldet = False
    for x in takte:
        # (die Basis zaehlt mit - Auftrag 027, 5: "ausserhalb von Kampf, Recall und Kanal"; 091311 15:41 stand er dort)
        # der Einkauf ist wie der Kanal: im Brunnen die 10 s nach einer Kauf-Anweisung (dann kauft er)
        einkauf = x["basis"] and any(x["t"] - 10.0 <= t <= x["t"] for t in kauf_t)
        if x["tot"] or x["modus"] in ("KAMPF", "TOT") or x.get("back_ruf") or x.get("pos") is None \
                or x["t"] < START_S or einkauf:
            seit, gemeldet = None, False
            continue
        if seit is None or abstand(tuple(seit[1]), tuple(x["pos"])) > 120.0:
            seit, gemeldet = (x["t"], x["pos"]), False
        elif not gemeldet and x["t"] - seit[0] >= 5.0:
            gemeldet = True
            still_n += 1
            # die Anweisung zaehlt, wenn sie waehrend des Stehens beginnt, bis 2 s nach den 5 s (ein Kauf-Satz beim
            # Ankommen im Brunnen ist die Anweisung fuers Stehen dort - 125902 27:24, 133448 13:11)
            # (1,5 s Spiel: die Takte hier liegen rund 1 s auseinander, der Kern sieht jeden - 091311 20:46 kam der
            # Satz im selben Moment, in dem Carlos stehen blieb)
            still_ok += any(seit[0] - 1.5 <= t <= x["t"] + 2.0 for t in pos)
    # Basis
    basis_n = basis_ok = 0
    war = False
    for x in takte:
        b = x["basis"] and not x["tot"]
        if b and not war and x.get("kauf") and x["t"] >= START_S:       # vor dem Spielbeginn: Startkauf, Briefing
            basis_n += 1
            basis_ok += any(x["t"] - 14.0 <= t <= x["t"] + 2.0 for t in kauf_t)   # im Tod 12 s vor dem Respawn gesagt, im Recall-Kanal davor
        war = b
    neg = [s for s in g if s["schl"] != "antwort" and negativ_allein(s["text"])]
    hin = 0
    # dieselbe Zielbestimmung wie die Regel im Kern (herzschlag.plan_ziel_von): Kauf-Kette und Rueckzug ohne eigenes
    # Ziel, ein Ereignis vorn ("Sie haben den Herold.") ist kein Ziel; eine Gefahr darf immer umwerfen
    from lolcoach.kern.herzschlag import plan_ziel_von, ziele_vertraeglich
    plan_s = [(s["t"], plan_ziel_von(NS(schluessel=s["schl"], text=s["text"]))) for s in g
              if s.get("thema") != "gefahr"]
    plan_s = [(t, z) for t, z in plan_s if z]
    for (t1, z1), (t2, z2) in zip(plan_s, plan_s[1:]):
        hin += t2 - t1 < 5.0 and not ziele_vertraeglich(z1, z2)
    # Auftrag 028, 1.5: Widerspruch - ein Planwechsel ohne Grund (Gefahr, Event vorn, Frage) binnen 20 s nach dem
    # letzten Plan-Satz; dieselbe Grund-Erkennung wie die Regel im Kern (herzschlag.wechsel_grund)
    from lolcoach.kern.herzschlag import WECHSEL_S, halte_ziel, wechsel_grund
    wid = []
    aktiv = None
    for s in g:
        a = NS(schluessel=s["schl"], text=s["text"], thema=s.get("thema") or "", kategorie=s.get("kat"))
        z = plan_ziel_von(a)
        if not z:
            continue
        if aktiv is not None and s["t"] - aktiv[0] < WECHSEL_S and not ziele_vertraeglich(aktiv[1], z) \
                and not wechsel_grund(a, halte_ziel(aktiv[2], aktiv[1])):
            wid.append((round(s["t"]), aktiv[2][:40], s["text"][:50]))
        aktiv = (s["t"], z, s["text"])
    # Auftrag 028, 2: Fuellsaetze - nackte Bestaetigungen und Entschuldigungen (ohne naechsten Schritt)
    fuell = [s for s in g if FUELL.match(s["text"].split("“ – ", 1)[-1] if s["schl"] == "antwort" else s["text"])]
    # Auftrag 028, 6.5: "Kanone" hoechstens 1 Nennung je 90 s Spielzeit
    dauer = max((x["t"] for x in takte), default=0.0) - START_S
    kanone = sum(1 for s in g if "kanone" in s["text"].lower() and s["schl"] != "antwort")
    return {"luecke_p90": round(p90, 1), "luecke_max": round(max(lsort) if lsort else 0.0, 1),
            "still": [still_ok, still_n], "basis": [basis_ok, basis_n], "negativ": len(neg), "hin_her": hin,
            "negativ_beispiele": [s["text"][:70] for s in neg[:3]],
            "widerspruch": len(wid), "widerspruch_beispiele": wid[:4], "fuell": [len(fuell), len(g)],
            "fuell_beispiele": [s["text"][:50] for s in fuell[:3]],
            "kanone": [kanone, round(max(dauer, 1.0) / 90.0, 1)]}


# nackt bestaetigen oder entschuldigen, ohne Schritt danach ("Bleib dabei, Kanone in 18 Sekunden." zaehlt mit)
FUELL = __import__("re").compile(r"^\W*(bleib dabei|weiter so|mach weiter|genau so|gut so|passt|okay|mein fehler|"
                                 r"tut mir leid|sorry|entschuldig\w*)\b(?![^.]*\b(dann|danach)\b)[^.]*\.?\s*$",
                                 __import__("re").I)


def _quote(ja: int, n: int) -> str:
    return f"{ja}/{n} ({100 * ja / n:.0f} %)" if n else "- (keine)"


def auswerten(d: dict) -> dict:
    takte, events, pakete, gesagt = d["takte"], d["events"], d["pakete"], d["gesagt"]
    # Paket-Abdeckung
    frei = [x for x in takte if not x["tot"] and x["modus"] not in ("KAMPF", "TOT") and not x["basis"]]
    mit = [x for x in frei if x["paket"] is not None]
    gesagt_p = [x for x in mit if x["paket"].get("gesagt") or x["paket"].get("fortsetzung")]   # 026, 4: Fortsetzung zaehlt
    # Abbruch-Reaktion. Wahrheit aus dem Bild, nicht aus der eigenen Uhr: waehrend eines Vorwaerts-Pakets kommt ein
    # sichtbarer Gegner neu auf <= 1000 an dich heran. Reagiert: das Paket endet oder eine Warnung kommt in [-3, +2] s.
    faelle, ok = 0, 0
    vorn = ("TURM", "OBJECTIVE")      # 026: bei HILFE ist ein naher Gegner der Kampf selbst, kein Abbruchgrund
    for i in range(1, len(takte)):
        x, v = takte[i], takte[i - 1]
        pk = v["paket"]
        if pk is None or pk["typ"] not in vorn or x["tot"] or x["modus"] == "KAMPF" and v["modus"] == "KAMPF":
            continue
        if not (x["nah"] is not None and x["nah"] <= 1000 and (v["nah"] is None or v["nah"] > 1000)):
            continue
        if x.get("sie_nah", 1) < x.get("wir_nah", 1):
            continue                      # 026: ihr seid dort mehr - der Gegner, der kommt, ist kein Abbruchgrund
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
    back_n = back_ok = back_erzw = 0
    for pk in pakete:
        if pk["typ"] != "BACK" or pk["ende"] != "ERLEDIGT":
            continue
        start = next((x for x in takte if x["t"] >= pk["start"]), None)
        if start is None or start["back_bis"] is None:
            continue
        if (start["leben"] or 1.0) < 0.4:
            back_erzw += 1                # Auftrag 026, 1: ein Back fuers Leben ist keine Timing-Entscheidung
            continue
        if not start.get("lane_phase") and not start.get("lane_hier"):
            back_erzw += 1                # ... und abseits jeder Lane (133448 15:56 an der Baron-Grube) verliert der
            continue                      # Back keine Welle, die du sonst gehabt haettest
        back_n += 1
        ankunft = pk["verlauf"][-1][0]
        # puenktlich: vor der Kanone zurueck (Frist + Kanal) - oder die Welle lag bei ihm, dann geht nichts verloren
        back_ok += ankunft <= start["back_bis"] + 8.0 + 1.0 or (start.get("front") or 0.0) >= 0.55
    # Chancen genutzt: Episoden mit HILFE-Kandidat
    ch_n = ch_ok = 0
    letzte = -1e9
    for x in takte:
        if x["hilfe"] and x["t"] - letzte > 20.0:
            ch_n += 1
            letzte = x["t"]
            ch_ok += any(x["t"] <= y["t"] <= x["t"] + 5.0 and (y["plan"] in ("HILFE", "ZUR_GRUPPE", "MIT_GRUPPE", "ANNEHMEN", "REIN"))
                         for y in takte) or any(x["t"] <= s["t"] <= x["t"] + 5.0 and s["schl"] == "kern:PAKET_WARUM_NICHT"
                                                for s in gesagt)
    # Event-Abdeckung
    ev_n = ev_ok = 0
    for e in events:
        if e["typ"] not in WICHTIG or (e["typ"] == "KAMPF" and (e.get("weg") or 99) > 20):
            continue
        if e["typ"] == "LANE_WEG":
            # 026: "Lane-Gegner weg" ist ein wichtiges Event der Lane-Phase - danach steht keiner mehr gegen dich
            x = next((y for y in takte if y["t"] >= e["t"]), None)
            if x is None or not x.get("lane_phase"):
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
            "back": _quote(back_ok, back_n) + f" (+{back_erzw} fuers Leben oder abseits der Lane)", "chancen": _quote(ch_ok, ch_n), "events": _quote(ev_ok, ev_n),
            "erahnt": {k: list(v) for k, v in erahnt.items()},
            "roh": {"frei": len(frei), "mit": len(mit), "gesagt": len(gesagt_p), "abbruch": [ok, faelle],
                    "budget": [budget_f, budget_n, budget_g], "back": [back_ok, back_n], "chancen": [ch_ok, ch_n],
                    "events": [ev_ok, ev_n]},
            "pakete_n": len(pakete), "sicherheit_liste": d.get("sicherheit") or []}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    staemme = args or list(ARBEIT if "--arbeit" in sys.argv else TESTPARTIEN)
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
        h = hoeren(d)
        r["hoeren"] = h
        for k in ("still", "basis"):
            summe.setdefault(k, [0, 0])
            summe[k] = [a + b for a, b in zip(summe[k], h[k])]
        summe["negativ"] = summe.get("negativ", 0) + h["negativ"]
        summe["hin_her"] = summe.get("hin_her", 0) + h["hin_her"]
        summe.setdefault("luecken", []).append((h["luecke_p90"], h["luecke_max"]))
        summe.setdefault("widerspruch", []).append(h["widerspruch"])
        summe["fuell"] = [a + b for a, b in zip(summe.get("fuell", [0, 0]), h["fuell"])]
        summe.setdefault("kanone", []).append(round(h["kanone"][0] / h["kanone"][1], 2))
        print(f"{r['stamm']}: HOEREN Luecke p90 {h['luecke_p90']} s / max {h['luecke_max']} s, Stillstand "
              f"{_quote(*h['still'])}, Basis {_quote(*h['basis'])}, negativ allein {h['negativ']}, hin und her "
              f"{h['hin_her']}, Widerspruch {h['widerspruch']}, Fuellsaetze {_quote(*h['fuell'])}, Kanone "
              f"{h['kanone'][0]} in {h['kanone'][1]} x 90 s, Sicherheit {len(r.get('sicherheit_liste') or [])}",
              flush=True)
        for x in (r.get("sicherheit_liste") or [])[:4]:
            print(f"    SICHERHEIT {x['t']} {x['schl']} {x['grund']}: {x['text']}", flush=True)
        print(f"{r['stamm']}: Abdeckung {r['abdeckung']} (angesagt {r['abdeckung_gesagt']}), Abbruch {r['abbruch']}, "
              f"Budget {r['budget']}, Back {r['back']}, Chancen {r['chancen']}, Events {r['events']}, "
              f"Pakete {r['pakete_n']}", flush=True)
    g = {"abdeckung": _quote(summe["mit"], summe["frei"]), "abdeckung_gesagt": _quote(summe["gesagt"], summe["frei"]),
         "abbruch": _quote(*summe["abbruch"]),
         "budget": f"{summe['budget'][0]}/{summe['budget'][1]} Fehler, {summe['budget'][2]} gefährlich",
         "back": _quote(*summe["back"]), "chancen": _quote(*summe["chancen"]), "events": _quote(*summe["events"]),
         "erahnt": {k: _quote(j, n) for k, (n, j) in erahnt.items()},
         "hoeren": {"luecke_p90_max": max(p for p, _ in summe["luecken"]), "luecke_max": max(x for _, x in summe["luecken"]),
                    "stillstand": _quote(*summe["still"]), "basis": _quote(*summe["basis"]),
                    "negativ_allein": summe["negativ"], "hin_und_her": summe["hin_her"],
                    "widerspruch_je_partie": summe["widerspruch"], "fuellsaetze": _quote(*summe["fuell"]),
                    "kanone_je_90s_max": max(summe["kanone"])}}
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
