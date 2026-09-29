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


def laufen(stamm: str, stub: bool = False, aus: Path = AUS, weg: str | None = None, modell: str | None = None) -> Path:
    """Auftrag 019: `weg` ("api"/"abo") und `modell` ("schnell"/"stark", sonst je Zweck aus [llm]) ueber die Umgebung -
    so laufen mehrere Partien und Einstellungen parallel in eigenen Prozessen (`alle`)."""
    import os
    if weg:
        os.environ["LOLCOACH_LLM_WEG"] = weg
    if modell:
        os.environ["LOLCOACH_MODELL"] = modell
    aus.mkdir(parents=True, exist_ok=True)
    from lolcoach import llm_api
    llm_api.KOSTEN.datei = aus / f"{stamm}_kosten.json"
    import fuehrmass
    from lolcoach import stratege_live
    from lolcoach.zustand import gegenteam
    if not stub:
        # der echte Weg (API oder Abo), mit Zwischenspeicher je (Modell, System, Prompt) - Auftrag 019, 0.5
        zs = stratege_live.Zwischenspeicher(stratege_live.claude_strom, aus / "zwischenspeicher.jsonl")
        stratege_live.AufzeichnungsStub = lambda *a, **k: zs
    fragen = [(f["zeit"], f["text"], i) for i, f in enumerate(fuehrmass.fragen_aus_log(stamm))]
    gesprochen, takte, flashes = [], [], {}
    gesehen = [0]
    info = {}
    letzte = [-1e9]
    letzte_gross = [-1e9]
    letzte_p = [None]

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
                                   "kategorie": getattr(a, "_kategorie", None), "gefahr_satz": a.thema == "gefahr",
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
        letzte_p[0] = p
        if p.zeit - letzte[0] >= 0.5 and p.ich:
            letzte[0] = p.zeit
            j = b.jungler if b is not None else None
            ln = b.lane if b is not None else None
            t = {"zeit": round(p.zeit, 1), "tot": bool(p.ich.tot),
                 "bereich": m.bereich if m is not None else None,
                 "modus": kern.modus.aktuell, "leben": None if m is None or m.leben is None else round(m.leben, 2),
                 "gefahr": bool(kern.gefahr),
                 "jungler": None if j is None else {"name": j.champion, "sichtbar": bool(j.sichtbar),
                                                     "tot": bool(j.s.tot), "ort": j.ort, "ankunft": j.ankunft},
                 "lane": None if ln is None else {"name": ln.champion, "sichtbar": bool(ln.sichtbar),
                                                  "tot": bool(ln.s.tot), "ort": ln.ort, "ankunft": ln.ankunft,
                                                  "leben": ln.leben, "pos": ln.pos}}
            if p.zeit - letzte_gross[0] >= 5.0 and m is not None and b is not None:
                # Auftrag 017, 2.1: die Lage fuer den blinden Kritiker (ohne Coach-Saetze), alle 5 s
                letzte_gross[0] = p.zeit
                from lolcoach import ddragon
                it = ddragon.items()
                w = m.welle
                t["gross"] = {
                    "gold": int(p.gold or 0), "level": p.ich.level, "cs": getattr(p.ich, "cs", None),
                    "items": [it.get(i, {}).get("name", str(i)) for i in p.ich.items],
                    "flash_bereit": b.flash is not None and b.flash <= 0,
                    "welle": None if w is None else {"lane": w.lane, "unsere": w.unsere, "ihre": w.ihre,
                                                     "zustand": w.zustand},
                    "kanone_in": None if m.kanone_in is None else round(m.kanone_in),
                    "objectives": [{"schl": o.schl, "lebt": bool(o.lebt), "spawn_in": round(o.spawn_in or 0)}
                                   for o in m.objectives or []],
                    "gegner": [{"name": g.champion, "sichtbar": bool(g.sichtbar), "tot": bool(g.s.tot),
                                "ort": g.ort, "seit": None if g.seit is None else round(g.seit),
                                "leben": None if g.leben is None else round(g.leben, 2), "level": g.s.level}
                               for g in b.gegner],
                    "mitspieler": [{"name": s.champion, "tot": bool(s.tot), "ort": ort}
                                   for s, _, _, ort in (b.mitspieler or [])],
                    "stand": f"Kills {p.kills(p.mein_team)}:{p.kills(gegenteam(p.mein_team))}",
                }
            takte.append(t)

    t0 = time.monotonic()
    lauf = ns.durchspielen(ns.pfad_zu(stamm), beim_takt=beim_takt, fragen=fragen, stratege="stub")
    ms = lauf.stratege
    aus.mkdir(parents=True, exist_ok=True)
    ziel = aus / f"{stamm}.json"
    pl = letzte_p[0]
    ereignisse = [] if pl is None else [
        {"zeit": round(e.zeit, 1), "art": e.art, "wir": e.team == pl.mein_team,
         "taeter": e.taeter.champion if e.taeter is not None else None,
         "opfer": e.opfer.champion if e.opfer is not None else None}
        for e in pl.ereignisse if e.art in ("ChampionKill", "TurretKilled", "InhibKilled", "DragonKill", "HeraldKill",
                                            "BaronKill", "HordeKill", "AtakhanKill")]
    ziel.write_text(json.dumps({
        "ereignisse": ereignisse,
        "schiedsrichter": getattr(getattr(ms, "schiedsrichter", None), "verworfen", []),
        "stamm": stamm, "stub": stub, "info": info, "dauer_s": round(time.monotonic() - t0),
        "weg": os.environ.get("LOLCOACH_LLM_WEG"), "modell": os.environ.get("LOLCOACH_MODELL"),
        "kosten_dollar": llm_api.KOSTEN.summe(), "kosten": llm_api.KOSTEN.je_modell,
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
    aus = {"flash": fl, "jungler": jw, "backs": backs, "back_rufe": [
        {"zeit": g["zeit"], "text": g["text"], "kette": stratege.kette(g["text"])} for g in rufe],
        "stille_max": round(stille), "stille_lang": lang, "sicherheit": sich}
    aus.update(auftrag_017(d, ges))
    return aus


# --- Auftrag 017, Teil 2 -------------------------------------------------------------------------------------------

INFO_SCHL = ("kern:INFO_", "kern:VORSICHT", "kern:LAGEBILD", "kern:technik", "tod", "briefing")
WARN_SCHL = ("kern:ZURUECK", "kern:RAUS", "kern:WELLE_UND_RAUS", "kern:REIN", "kern:DREHEN", "kern:HALTEN_UNTER_TURM")


def _plan_saetze(ges: list) -> list:
    """Die gesprochenen Plan-Saetze (Kern, Stratege, Antworten) - ohne Infos und Warnungen."""
    from lolcoach.stratege_live import plan_ziel
    aus = []
    for g in ges:
        if g["schluessel"].startswith(INFO_SCHL) or g.get("gefahr_satz") or g["schluessel"] in WARN_SCHL:
            continue
        z = plan_ziel(g["text"])
        if z is not None:
            aus.append((g["zeit"], z, g))
    return aus


def _ereigniszeiten(d: dict, ges: list) -> list[float]:
    """Lageaenderungen: Kills, Tuerme, Objectives (API), dein Tod und Respawn, Basis, Gefahr, Infos und Wendepunkte,
    Carlos' Fragen."""
    t = [e["zeit"] for e in d.get("ereignisse", [])]
    vorher = None
    for x in d["takte"]:
        if vorher is not None:
            if x["tot"] != vorher["tot"] or (x.get("gefahr") and not vorher.get("gefahr")) \
                    or (x["bereich"] == "basis_eigen" and vorher["bereich"] not in (None, "basis_eigen")):
                t.append(x["zeit"])
        vorher = x
    t += [g["zeit"] for g in ges if g["schluessel"].startswith(("kern:INFO_", "antwort", "kern:VORSICHT"))
          or "ist weg" in g["text"] or " tot" in g["text"]]
    return sorted(t)


def auftrag_017(d: dict, ges: list) -> dict:
    """Widersprueche (Plan-Wechsel in < 30 s ohne Lageaenderung), Fuellsaetze (automatisch nach wissen/
    fuellsaetze.toml), I4 (Lane-Gegner weit weg gesehen, angesagt in <= 8 s), Latenz des Strategen (ganze Antwort)."""
    from lolcoach import stratege
    ps = _plan_saetze(ges)
    ev = _ereigniszeiten(d, ges)
    wid = []
    for (t1, z1, g1), (t2, z2, g2) in zip(ps, ps[1:]):
        if z1 != z2 and t2 - t1 < 30.0 and not any(t1 - 0.5 < e <= t2 for e in ev):
            wid.append({"zeit": t2, "von": z1, "nach": z2, "vorher": g1["text"], "text": g2["text"]})
    fuell = [g for g in ges if not g["schluessel"].startswith(INFO_SCHL)
             and any(stratege.fuellsatz(s) for s in stratege._saetze(g["text"]))]
    n_saetze = sum(1 for g in ges if not g["schluessel"].startswith(("tod", "briefing")))
    # I4: Lane-Gegner weit weg (>= 30 s Laufzeit oder in seiner Basis), du lebst an einer Lane
    i4, war = [], False
    for x in d["takte"]:
        ln = x.get("lane")
        weit = bool(ln and ln["sichtbar"] and not ln["tot"] and not x["tot"]
                    and str(x["bereich"] or "").startswith("lane") and x["zeit"] >= LANE_AB_S
                    and ((ln.get("ankunft") or 0) >= 30 or "Basis" in (ln.get("ort") or "")))
        if weit and not war:
            treffer = next((g for g in ges if x["zeit"] - 1.0 <= g["zeit"] <= x["zeit"] + JUNGLER_FENSTER_S
                            and _nennt(g["text"], ln["name"])), None)
            if not i4 or x["zeit"] - i4[-1]["zeit"] >= 30.0:
                i4.append({"zeit": x["zeit"], "name": ln["name"], "ort": ln["ort"],
                           "gesagt": treffer["text"] if treffer else None})
        war = weit
    # Latenz: bis zum ersten gueltigen ganzen Satz (bei Wiederholung: erster Versuch + zweiter)
    lat = []
    for e in d.get("stratege", []):
        vs = e.get("versuche") or []
        summe = 0.0
        for v in vs:
            if v.get("erster_s") is not None:
                lat.append(round(summe + v["erster_s"], 2))
                break
            summe += v.get("ende_s") or 0.0
    lat.sort()
    return {"widersprueche": wid, "fuellsaetze": [{"zeit": g["zeit"], "text": g["text"], "schluessel": g["schluessel"]}
                                                  for g in fuell],
            "saetze_n": n_saetze, "i4": i4,
            "latenz": {"n": len(lat), "median": lat[len(lat) // 2] if lat else None,
                       "p90": lat[min(len(lat) - 1, int(len(lat) * 0.9))] if lat else None}}


def lage_je_minute(d: dict) -> str:
    """Auftrag 017, 2.1: je Minute nur die Lage (ohne Coach-Saetze) - fuer den blinden Challenger-Kritiker."""
    info = d["info"]
    takte = d["takte"]
    gross = [x for x in takte if x.get("gross")]
    z = [f"# Lage je Minute – {d['stamm']}", "",
         f"Du spielst {info.get('champion')} ({'blau' if info.get('team') == 'ORDER' else 'rot'}), Lane-Gegner "
         f"{info.get('gegner')}. Je Minute: dein Zustand, Welle, Gegner, Mitspieler, Objectives, was passiert ist, und "
         "Carlos' Fragen (seine Worte). Was der Coach gesagt hat, steht hier NICHT.", ""]
    ende = int(takte[-1]["zeit"] // 60) if takte else 0
    fragen = [(a["zeit"], a["frage"]) for a in d.get("antworten", [])
              if not a["frage"].lower().lstrip(" ,.").startswith("notiz")]
    for mi in range(1, ende + 1):
        a, b = mi * 60, mi * 60 + 60
        g = min(gross, key=lambda x: abs(x["zeit"] - (a + 30)), default=None)
        z += [f"## Minute {mi} ({mi}:00–{mi}:59)", ""]
        if g is not None and a - 30 <= g["zeit"] <= b + 30:
            gr = g["gross"]
            tot = any(x["tot"] for x in takte if a <= x["zeit"] < b)
            z.append(f"- **Du** ({_uhr(g['zeit'])}): Level {gr['level']}, Leben "
                     f"{'?' if g['leben'] is None else int(round(g['leben'] * 100))} %, {gr['gold']} Gold, "
                     f"Flash {'bereit' if gr['flash_bereit'] else 'weg'}, Ort {g['bereich'] or '?'}, Modus {g['modus']}"
                     f"{', in dieser Minute tot' if tot else ''}. Items: {', '.join(gr['items']) or '–'}. {gr['stand']}.")
            w = gr.get("welle")
            if w:
                z.append(f"- **Welle {w['lane']}:** {w['unsere']} eigene gegen {w['ihre']} Vasallen, {w['zustand']}"
                         + (f"; Kanone in {gr['kanone_in']} s" if gr.get("kanone_in") is not None
                            and gr["kanone_in"] <= 60 else ""))
            geg = []
            for x in gr["gegner"]:
                if x["tot"]:
                    geg.append(f"{x['name']} tot")
                elif x["sichtbar"]:
                    geg.append(f"{x['name']} L{x['level']} sichtbar {x['ort']}"
                               + (f" ({int(round(x['leben'] * 100))} %)" if x.get("leben") is not None else ""))
                elif x["seit"] is not None:
                    geg.append(f"{x['name']} L{x['level']} vor {x['seit']} s {x['ort']}")
                else:
                    geg.append(f"{x['name']} nie gesehen")
            z.append("- **Gegner:** " + "; ".join(geg))
            z.append("- **Mitspieler:** " + "; ".join(f"{x['name']} {'tot' if x['tot'] else x['ort'] or '?'}"
                                                      for x in gr["mitspieler"]))
            obj = [f"{o['schl']} {'lebt' if o['lebt'] else 'in ' + str(o['spawn_in']) + ' s'}" for o in gr["objectives"]
                   if o["lebt"] or o["spawn_in"] <= 180]
            if obj:
                z.append("- **Objectives:** " + ", ".join(obj))
        ev = []
        for e in d.get("ereignisse", []):
            if a <= e["zeit"] < b:
                wer = "ihr" if e["wir"] else "sie"
                ev.append(f"{_uhr(e['zeit'])} {e['art']} ({wer}"
                          + (f": {e['taeter']} → {e['opfer']}" if e.get("opfer") else "") + ")")
        ev += [f"{_uhr(f['erkannt'])} {f['champion']} benutzt Flash" for f in d["flashes"] if a <= f["erkannt"] < b]
        vorher = None
        for x in takte:
            if a <= x["zeit"] < b and vorher is not None:
                j, jv = x.get("jungler"), vorher.get("jungler")
                if j and jv and j["sichtbar"] and not jv["sichtbar"]:
                    ev.append(f"{_uhr(x['zeit'])} Jungler {j['name']} gesehen {j['ort']}")
                if x["bereich"] == "basis_eigen" and vorher["bereich"] not in (None, "basis_eigen") and not x["tot"]:
                    ev.append(f"{_uhr(x['zeit'])} du bist in der Basis")
                if not x["tot"] and vorher["tot"]:
                    ev.append(f"{_uhr(x['zeit'])} du lebst wieder")
            vorher = x
        if ev:
            z.append("- **Ereignisse:** " + "; ".join(ev[:14]))
        fr = [f"{_uhr(t)} „{f[:160]}“" for t, f in fragen if a <= t < b]
        if fr:
            z.append("- **Carlos fragt:** " + " | ".join(fr))
        z.append("")
    return "\n".join(z)


def _quote(liste: list, schl: str = "gesagt") -> str:
    n = len(liste)
    k = sum(1 for x in liste if x.get(schl))
    return f"{k}/{n} ({100 * k / n:.0f} %)" if n else "– (keine)"


def kennzahlen(a: dict) -> dict:
    return {"flash": _quote(a["flash"]), "jungler": _quote(a["jungler"]), "i4": _quote(a["i4"]),
            "backs": _quote(a["backs"]), "back_rufe": _quote(a["back_rufe"], "kette"), "stille": f"{a['stille_max']} s",
            "sicherheit": len(a["sicherheit"]), "widersprueche": len(a["widersprueche"]),
            "fuellsaetze": f"{len(a['fuellsaetze'])}/{a['saetze_n']} "
                           f"({100 * len(a['fuellsaetze']) / max(1, a['saetze_n']):.1f} %)",
            "latenz": f"{a['latenz']['median']} / {a['latenz']['p90']} s (n = {a['latenz']['n']})"}


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
                             ("jungler", "I1 Jungler-Wiedersichtungen nach ≥ 20 s, angesagt", "≥ 90 %"),
                             ("i4", "I4 Lane-Gegner weit weg gesehen, angesagt", "≥ 90 %"),
                             ("backs", "Backs mit Kette (Kauf + Ziel)", "100 %"),
                             ("back_rufe", "Back-Rufe mit Kette", "100 %"),
                             ("stille", "längste Stille in der Lane-Phase (lebend)", "≤ 45 s"),
                             ("sicherheit", "Sicherheit: Vorwärts unter R1, Angriff ohne Kill-Check, innere Begriffe",
                              "0"),
                             ("widersprueche", "Widersprüche: Planwechsel < 30 s ohne Lageänderung", "0"),
                             ("fuellsaetze", "Füllsätze (automatisch, wissen/fuellsaetze.toml)", "≤ 5 %"),
                             ("latenz", "Stratege: bis zur ganzen gültigen Antwort, Median / p90", "≤ 3 / ≤ 5 s")):
        z.append(f"| {name} | {soll} | " + (f"{kv.get(schl, '–')} | " if kv else "") + f"{k[schl]} |")
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
    # Auftrag 017, 2.6: die Soll-Liste des blinden Kritikers, verglichen - "fehlt"-Minuten markiert
    soll_datei = aus / f"{stamm}_soll.json"
    soll = json.loads(soll_datei.read_text(encoding="utf-8")).get("minuten", {}) if soll_datei.exists() else {}
    if soll:
        n = [x for v in soll.values() for x in v]
        treffer = sum(1 for x in n if x.get("urteil") in ("gesagt", "teilweise"))
        z.insert(z.index("## Minute für Minute"),
                 f"**Soll-Liste (blinder Challenger-Kritiker):** {treffer}/{len(n)} gesagt oder teilweise "
                 f"({100 * treffer / max(1, len(n)):.0f} %), fehlt {len(n) - treffer}.\n")
    minute = -1
    ende = int(ges[-1]["zeit"] // 60) if ges else 0
    leer = [{"zeit": mi * 60.0, "leer": True} for mi in range(ende + 1)]
    for g in sorted(ges + leer, key=lambda x: (x["zeit"], not x.get("leer"))):
        mi = int(g["zeit"] // 60)
        if mi != minute:
            minute = mi
            s_ = soll.get(str(mi), [])
            fehlt_ = [x for x in s_ if x.get("urteil") == "fehlt"]
            z += ["", f"### Minute {mi}" + (" · **fehlt**" if fehlt_ else ""), ""]
            for x in s_:
                z.append(f"- *Soll:* {x.get('soll')} → **{x.get('urteil')}**" + (f" ({x['grund']})" if x.get("grund")
                                                                               else ""))
        if g.get("leer"):
            continue
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


def _lauf_einer(a: tuple) -> str:
    stamm, aus, weg, modell = a
    import contextlib
    import io
    puffer = io.StringIO()
    with contextlib.redirect_stdout(puffer):
        try:
            laufen(stamm, aus=Path(aus), weg=weg, modell=modell)
        except Exception as e:
            import traceback
            print(f"!! {stamm}: {type(e).__name__}: {e}")
            print(traceback.format_exc(limit=5))
    return f"== {stamm} ({weg}, {modell or 'je Zweck'}):\n" + puffer.getvalue()[-2000:]


def alle(staemme: list[str], aus: Path, weg: str, modell: str | None) -> None:
    """Auftrag 019, 0.2: alle Partien gleichzeitig, jede in ihrem eigenen Prozess."""
    from concurrent.futures import ProcessPoolExecutor
    t0 = time.monotonic()
    with ProcessPoolExecutor(len(staemme)) as ex:
        for text in ex.map(_lauf_einer, [(s, str(aus), weg, modell) for s in staemme]):
            print(text, flush=True)
    print(f"({len(staemme)} Partien parallel, {time.monotonic() - t0:.0f} s)", flush=True)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opt = {a.split("=", 1)[0]: (a.split("=", 1)[1] if "=" in a else True) for a in sys.argv[1:] if a.startswith("--")}
    aus = Path(opt["--aus"]) if "--aus" in opt else AUS
    was, staemme = args[0], args[1:]
    if was == "alle":
        alle(staemme, aus, opt.get("--weg", "api"), opt.get("--modell"))
        return
    for stamm in staemme:
        if was == "alle":
            break
        if was == "laufen":
            print(laufen(stamm, stub="--stub" in opt, aus=aus), flush=True)
        elif was == "lage":
            d = json.loads((aus / f"{stamm}.json").read_text(encoding="utf-8"))
            ziel = aus / f"LAGE_{stamm}.md"
            ziel.write_text(lage_je_minute(d), encoding="utf-8")
            print(ziel, flush=True)
        else:
            print(auswerten(stamm, aus, Path(opt["--vorher"]) if "--vorher" in opt else None), flush=True)


if __name__ == "__main__":
    main()
