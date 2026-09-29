"""Probe: Claude als Makro-Stratege neben dem Kern (Auftrag 013) - offline, nachgespielt, am Live-Coach aendert nichts.

Drei Schritte, jeder schreibt nach `buecher/protokolle/stratege_probe/`:

    python werkzeuge/stratege_probe.py sammeln            # Momente waehlen, Lage und Kern-Antwort festhalten
    python werkzeuge/stratege_probe.py fragen [--lauf 1]  # je Moment Claude mit dem Systemprompt STRATEGE (Strom)
    python werkzeuge/stratege_probe.py blind  [--lauf 1]  # Vorlage fuer die Blind-Kritik (A/B gemischt)
    python werkzeuge/stratege_probe.py kritik [--lauf 1]  # Urteile (urteile_<rolle>_<lauf>.jsonl) entblinden, zaehlen
    python werkzeuge/stratege_probe.py bericht [--lauf 1] # buecher/protokolle/STRATEGE_PROBE.md

Momente (hoechstens 70 Aufrufe):
  - 192113: die echten Fragen, die der Kern beantwortet (ohne Notizen, Nachfragen und Beschwerden), dazu die
    Wendepunkte (Turm, Objective) ab 10:00, hoechstens einer je 60 s,
  - 101426: die 10 Leerlauf-Fenster aus Auftrag 009 (Mitte des Fensters) und die Wendepunkte ab 14:00.
Am Wendepunkt und im Leerlauf fragt die Probe "Was jetzt, und warum?".

Der Kontext ist der, den `antworten.mit_claude` live baut (Kopfzeile, `kern.kontext()`, Spielakte ueber `gehirn`),
dazu die Kandidaten des Kerns mit EV, Risiko und Grund - als Fakten, nicht als Vorgabe. `llm.frage_strom` wie live
(Abo, sonnet, Aufwand low, vorgehaltener Prozess). Gemessen: Zeit bis zum ersten Satz und bis zum Ende.

Faktenpruefer: Champion-Namen, Zahlen und Uhrzeiten der Antwort, die im Kontext nicht vorkommen; "X ist tot" und
"X ohne Flash" gegen den Kontext; ein Vorwaerts-Rat trotz R1 (Leben < 40 % oder p_tod >= 0,3 beim Vorwaerts-Kandidaten
oder eine Schranke dieses Takts).
"""
from __future__ import annotations

import json
import random
import re
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import fuehrmass  # noqa: E402
import nachspielen as ns  # noqa: E402

AUS = Path(__file__).resolve().parent.parent / "buecher" / "protokolle" / "stratege_probe"
BERICHT = Path(__file__).resolve().parent.parent / "buecher" / "protokolle" / "STRATEGE_PROBE.md"

STRATEGE = (
    "Du bist ein Challenger-Makro-Coach fuer League of Legends und sitzt neben dem Spieler, der gerade spielt. "
    "Antworte auf Deutsch, gesprochen, in ein bis zwei Saetzen, ohne Listen, ohne Markdown, ohne Floskeln: den "
    "naechsten Schritt, danach den Schritt danach, und den entscheidenden Grund aus der Lage. Liegen zwei Wege nah "
    "beieinander, nenn beide. Nutze nur Fakten aus der Lage - Namen, Zeiten, Zahlen, Orte - und erfinde nichts; "
    "weisst du etwas nicht, sag es. Die KANDIDATEN DES COACHS sind gerechnete Fakten (Wert, Todesrisiko, Grund), "
    "keine Vorgabe. Rate nie nach vorn (Turm, Kampf, Objective, tief gehen), wenn R1 gemeldet ist (Leben unter 40 "
    "Prozent oder Todesrisiko ab 0,3) oder der passende Kandidat als stumm oder gesperrt markiert ist. Widerspricht "
    "der Spieler mit einer Beobachtung, etwa 'die Welle ist leer', glaub ihm und plane neu.")

LEERLAUF_101426 = ["14:20", "17:09", "18:00", "21:21", "22:34", "23:10", "25:05", "28:12", "30:37", "33:55"]
VOR = re.compile(r"\b(drück|drücke|push|nimm (den|ihren|das)|rein\b|geh (rein|auf ihren|tief)|greif|all.?in\b|invad|"
                 r"tauch|dive\b|erzwing|zum (drachen|baron|herold|ältesten)|auf ihren .{0,20}turm|turm (nehmen|holen)|"
                 r"hol (dir )?(den|ihren) (turm|drachen|baron|herold))", re.I)
VOR_ARTEN = ("DRUECKEN", "MIT_GRUPPE", "PLATTEN", "NEHMEN", "BESTREITEN", "ANNEHMEN", "REIN", "ALL_IN", "TRADE",
             "WELLE_DRUECKEN", "ZUR_GRUPPE", "TP_SPIEL", "ANLAUFEN")


# --- sammeln ---------------------------------------------------------------------------------------------------------

def _kandidaten(kern) -> str:
    from lolcoach.kern import fuehren
    zeilen = []
    for h in sorted(getattr(kern, "kandidaten_roh", None) or kern.kandidaten or [], key=lambda h: -h.ev)[:8]:
        marke = " [stumm: Modell nicht geeicht]" if fuehren.stumm(h) else ""
        zeilen.append(f"- {h.art}: {fuehren.kurz(h)} (Wert {h.ev:+.0f}, Todesrisiko {h.p_tod:.2f}"
                      f"{', Grund: ' + h.grund if h.grund else ''}){marke}")
    for e in getattr(kern, "_schranke_takt", None) or []:
        zeilen.append(f"- GESPERRT (R1): {e}")
    return "\n".join(zeilen) or "- keine"


def _r1(kern) -> str | None:
    m = kern.m
    if m is None:
        return None
    gruende = []
    if m.leben is not None and m.leben < 0.4:
        gruende.append(f"Leben {int(round(m.leben * 100))} %")
    vor = [h for h in (getattr(kern, "kandidaten_roh", None) or kern.kandidaten or []) if h.art in VOR_ARTEN]
    if vor and min(h.p_tod for h in vor) >= 0.3:
        gruende.append(f"Todesrisiko nach vorn mindestens {min(h.p_tod for h in vor):.2f}")
    gruende += [e for e in getattr(kern, "_schranke_takt", None) or []]
    return "; ".join(gruende) or None


def _lage_satz(kern) -> str:
    """Die Lage in einem Satz fuer Carlos: Ort, Leben, Gold, Plan."""
    from lolcoach.kern.modus import bereich_worte
    from lolcoach.kern.fragen import satz
    m = kern.m
    if m is None or m.b is None:
        return "?"
    plan = kern.fuehrer.plan
    s = f"{bereich_worte(m.bereich)}, {int(round((m.leben or 0) * 100))} %, {int(m.b.gold or 0)} Gold"
    tote = [g.champion for g in m.b.gegner if g.s.tot]
    if tote:
        s += f", tot: {', '.join(tote)}"
    if plan is not None:
        s += f"; Plan {plan.art}" + (f" ({satz(plan.handlung)[:60]})" if plan.handlung.satz else "")
    return s


def sammeln() -> None:
    from lolcoach import gehirn
    from lolcoach.kern import fragen as F
    AUS.mkdir(parents=True, exist_ok=True)
    momente = []
    for stamm, ab_wp, leerlauf in (("2026-09-28_192113", 600.0, []), ("2026-09-28_101426", 840.0, LEERLAUF_101426)):
        pfad = ns.pfad_zu(stamm)
        # 1. Lauf: Wendepunkte
        lauf1 = ns.durchspielen(pfad)
        wp, letzt = [], -1e9
        for t, art in fuehrmass.wendepunkte(lauf1, ab_wp):
            if art in ("Struktur", "Objective") and t - letzt >= 60.0:
                wp.append((t, art))
                letzt = t
        wp = wp[:10]
        fragen = []
        if stamm.endswith("192113"):
            for i, f in enumerate(fuehrmass.fragen_aus_log(stamm)):
                a = F.absicht(f["text"])
                if a in ("NOTIZ", "OFFEN") and F._innere_frage(f["text"]) is None:
                    continue
                fragen.append((f["zeit"], f["text"], f"f{i}"))
        ziele = [(t, "wendepunkt", art) for t, art in wp] + [(ns.sekunden(u), "leerlauf", "Leerlauf") for u in leerlauf]
        ziele += [(t, "frage", (text, fid)) for t, text, fid in fragen]
        ziele.sort(key=lambda x: x[0])
        g = gehirn.Gehirn()
        akte = ns.AUFNAHMEN / f"{stamm}_spielakte.md"
        g.akte = akte.read_text(encoding="utf-8") if akte.exists() else None
        offen = list(ziele)
        erfasst = []

        def beim_takt(p, werk, kern, plan, offen=offen, erfasst=erfasst, g=g):
            while offen and p.zeit >= offen[0][0]:
                t, art, info = offen.pop(0)
                if kern.m is None or kern.m.b is None:
                    continue
                if art == "frage":
                    frage, fid = info
                    anlass = frage
                    ende = f"Frage des Spielers: {frage}"
                else:
                    frage, fid = None, None
                    was = "Leerlauf: seit ein paar Sekunden kein Plan-Satz" if art == "leerlauf" else f"Wendepunkt ({info})"
                    anlass = "Was jetzt, und warum?"
                    ende = f"ANLASS: {was} um {ns.uhr(p.zeit)}. Was jetzt, und warum?"
                lage = kern.kontext() or ""
                r1 = _r1(kern)
                inhalt = g.kontext(anlass, p, lage)
                if (kopf := kern.kopfzeile()):
                    inhalt = f"{kopf}\n\n{inhalt}"
                inhalt += f"\n\nKANDIDATEN DES COACHS (gerechnet, keine Vorgabe):\n{_kandidaten(kern)}"
                inhalt += f"\nR1: {r1}" if r1 else "\nR1: nichts gemeldet"
                erfasst.append({"stamm": stamm, "zeit": p.zeit, "uhr": ns.uhr(p.zeit), "art": art,
                                "anlass": info if art != "frage" else None, "frage": frage, "fid": fid,
                                "prompt": f"{inhalt}\n\n{ende}", "kontext": lage, "lage_satz": _lage_satz(kern),
                                "r1": r1, "leben": kern.m.leben,
                                "plan_p_tod": kern.fuehrer.plan.handlung.p_tod if kern.fuehrer.plan else None})
        lauf2 = ns.durchspielen(pfad, beim_takt=beim_takt, fragen=fragen or None)
        antworten = {r["id"]: r for r in lauf2.antworten}
        for e in erfasst:
            if e["art"] == "frage":
                r = antworten.get(e["fid"]) or {}
                e["kern"] = r.get("text")
                e["kern_absicht"] = r.get("absicht")
            else:
                gesagt = [a for a in lauf2.gesagt if a.schluessel.startswith("kern:") and a.schluessel != "kern:INFO_FLASH"
                          and e["zeit"] - 1.0 <= ns.gesprochen_um(a) <= e["zeit"] + 8.0]
                e["kern"] = gesagt[0].text if gesagt else None
                if e["kern"] is None:
                    vorher = [a for a in lauf2.gesagt if a.schluessel.startswith("kern:")
                              and ns.gesprochen_um(a) < e["zeit"]]
                    e["kern_vorher"] = (f"{ns.uhr(ns.gesprochen_um(vorher[-1]))} „{vorher[-1].text}“" if vorher else None)
        # nur, was der Kern beantwortet (sonst ging es live ohnehin an Claude)
        momente += [e for e in erfasst if e["art"] != "frage" or (e.get("kern") and e.get("kern_absicht") not in
                                                                   ("NOTIZ", None))]
    # hoechstens 70: die Fragen gleichmaessig ausduennen
    rest = [e for e in momente if e["art"] != "frage"]
    fr = [e for e in momente if e["art"] == "frage"]
    platz = 70 - len(rest)
    if len(fr) > platz:
        schritt = len(fr) / platz
        fr = [fr[int(i * schritt)] for i in range(platz)]
    momente = sorted(rest + fr, key=lambda e: (e["stamm"], e["zeit"]))
    for i, e in enumerate(momente):
        e["id"] = f"m{i:02d}"
    (AUS / "momente.json").write_text(json.dumps(momente, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(momente)} Momente: " + ", ".join(f"{a} {sum(1 for e in momente if e['art'] == a)}"
                                                 for a in ("frage", "wendepunkt", "leerlauf")))


# --- fragen ----------------------------------------------------------------------------------------------------------

def fragen(lauf_nr: int, system: str) -> None:
    from lolcoach import llm
    momente = json.loads((AUS / "momente.json").read_text(encoding="utf-8"))
    ziel = AUS / f"antworten_{lauf_nr}.jsonl"
    fertig = {json.loads(z)["id"] for z in ziel.read_text(encoding="utf-8").splitlines()} if ziel.exists() else set()
    llm.vorhalten("sonnet", system, "low")
    for e in momente:
        if e["id"] in fertig:
            continue
        saetze = []
        t0 = time.perf_counter()
        erster = [None]

        def bei_satz(s):
            if erster[0] is None:
                erster[0] = time.perf_counter() - t0
            saetze.append(s)
        fehler = None
        try:
            text = llm.frage_strom(e["prompt"], bei_satz, system=system, modell="sonnet", timeout=40, aufwand="low",
                                   nachladen=True).strip()
        except llm.LLMFehler as x:
            text, fehler = "", str(x)
        dauer = time.perf_counter() - t0
        r = {"id": e["id"], "text": text, "erster_s": erster[0], "ende_s": dauer, "fehler": fehler,
             "uhrzeit": time.strftime("%H:%M:%S")}
        with ziel.open("a", encoding="utf-8") as d:
            d.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{e['id']} {e['stamm'][-6:]} {e['uhr']} {dauer:.1f}s {'FEHLER ' + fehler if fehler else text[:90]}",
              flush=True)


# --- Faktenpruefer ---------------------------------------------------------------------------------------------------

def _champions() -> list[str]:
    from lolcoach import ddragon
    namen = [v.get("name", "") for v in ddragon.champions().values()]
    return sorted({n for n in namen if n}, key=len, reverse=True)


ZAHL = re.compile(r"(?<![\d:,.])(\d+)(?![\d:])")
UHR = re.compile(r"\b(\d{1,2}):(\d{2})\b")
TOT = re.compile(r"([A-ZÄÖÜ][\w'’. ]{2,20}?) (ist|sind) (gerade )?tot")
OHNE_FLASH = re.compile(r"([A-ZÄÖÜ][\w'’.]{2,20}) (hat kein|ohne) Flash")


def pruefe(e: dict, text: str, champions: list[str]) -> list[str]:
    flags = []
    p = e["prompt"]
    k = e["kontext"]
    for n in champions:
        if re.search(rf"(?<![\w]){re.escape(n)}(?![\w])", text) and n not in p:
            flags.append(f"Name nicht im Kontext: {n}")
    zahlen_p = set(ZAHL.findall(p)) | {str(int(round(float(x.replace(',', '.')) * 100))) for x in
                                       re.findall(r"\b0[.,]\d+\b", p)}
    for z in ZAHL.findall(re.sub(UHR, "", text)):
        if z not in zahlen_p:
            flags.append(f"Zahl nicht im Kontext: {z}")
    for m in UHR.finditer(text):
        if m.group(0) not in p:
            flags.append(f"Uhrzeit nicht im Kontext: {m.group(0)}")
    for m in TOT.finditer(text):
        name = next((n for n in champions if n in m.group(1)), None)
        if name and not re.search(rf"{re.escape(name)}: tot", k):
            flags.append(f"Widerspruch: {name} laut Kontext nicht tot")
    for m in OHNE_FLASH.finditer(text):
        name = next((n for n in champions if n in m.group(1)), None)
        if name and not re.search(rf"{re.escape(name)}: OHNE Flash", k):
            flags.append(f"Widerspruch: {name} ohne Flash steht nicht im Kontext")
    r1 = e.get("r1")
    if r1 and not e.get("leben"):            # tot: "Leben 0 %" ist kein R1 fuer den Rat nach dem Respawn
        r1 = "; ".join(x for x in r1.split("; ") if not x.startswith("Leben")) or None
    if r1:
        # verneint ("erzwingen wir nicht", "Turm druecken ist gestrichen") oder aufgeschoben ("erst ..., dann") zaehlt nicht
        for m in VOR.finditer(text):
            umfeld = text[max(0, m.start() - 40):m.end() + 40].lower()
            if re.search(r"nicht|kein|nie\b|gesperrt|gestrichen|erst wenn|sobald|statt|danach|dann|wenn du wieder", umfeld):
                continue
            flags.append(f"Vorwaerts trotz R1 ({r1[:60]}): „{text[m.start():m.start() + 40]}“")
            break
    return flags


# --- blind -----------------------------------------------------------------------------------------------------------

def blind(lauf_nr: int) -> None:
    momente = json.loads((AUS / "momente.json").read_text(encoding="utf-8"))
    antw = {r["id"]: r for r in map(json.loads, (AUS / f"antworten_{lauf_nr}.jsonl").read_text(
        encoding="utf-8").splitlines())}
    rnd = random.Random(13)
    schluessel, teile = {}, []
    for e in momente:
        s = (antw.get(e["id"]) or {}).get("text") or "(keine Antwort)"
        kern = e.get("kern") or "(still – der Coach sagt in diesem Moment nichts)"
        a_ist_kern = rnd.random() < 0.5
        schluessel[e["id"]] = "kern" if a_ist_kern else "stratege"
        a, b = (kern, s) if a_ist_kern else (s, kern)
        was = f"Frage des Spielers: „{e['frage']}“" if e["frage"] else (
            "Kein Frage – Leerlauf, der Coach schweigt seit ein paar Sekunden." if e["art"] == "leerlauf"
            else f"Keine Frage – Wendepunkt ({e['anlass']}).")
        teile.append(f"## {e['id']} · Partie {e['stamm'][-6:]} · {e['uhr']}\n\n{was}\n\nLAGE (was der Coach weiß):\n"
                     f"{e['kontext']}\n{('R1 (vorn gesperrt): ' + e['r1']) if e.get('r1') else ''}\n\n"
                     f"**A:** {a}\n\n**B:** {b}\n")
    (AUS / f"blind_{lauf_nr}.md").write_text("\n".join(teile), encoding="utf-8")
    (AUS / f"blind_{lauf_nr}_schluessel.json").write_text(json.dumps(schluessel, indent=1), encoding="utf-8")
    print(f"{len(teile)} Momente -> {AUS / f'blind_{lauf_nr}.md'}")


# --- bericht ---------------------------------------------------------------------------------------------------------

def _p90(xs: list[float]) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(0.9 * (len(xs) - 1))))] if xs else 0.0


def auswertung(lauf_nr: int) -> dict:
    momente = json.loads((AUS / "momente.json").read_text(encoding="utf-8"))
    antw = {r["id"]: r for r in map(json.loads, (AUS / f"antworten_{lauf_nr}.jsonl").read_text(
        encoding="utf-8").splitlines())}
    champs = _champions()
    zeilen = []
    for e in momente:
        r = antw.get(e["id"]) or {}
        flags = pruefe(e, r.get("text") or "", champs) if r.get("text") else []
        zeilen.append((e, r, flags))
    ok = [r for _, r, _ in zeilen if r.get("text") and not r.get("fehler")]
    erste = [r["erster_s"] for r in ok if r.get("erster_s") is not None]
    enden = [r["ende_s"] for r in ok]
    return {"zeilen": zeilen, "erste": erste, "enden": enden,
            "fehler": [r for _, r, _ in zeilen if r.get("fehler")],
            "woerter": [len((r.get("text") or "").split()) for _, r, _ in zeilen if r.get("text")],
            "saetze": [len(re.findall(r"[.!?](\s|$)", r.get("text") or "")) for _, r, _ in zeilen if r.get("text")]}


def bericht(laeufe: list[int], kritik: dict | None = None) -> None:
    teile = ["# Stratege-Probe (Auftrag 013)", "",
             "Offline nachgespielt. Je Moment: was der Coach live sagt (Kern, heutiger Stand) und was Claude als "
             "Makro-Stratege sagt – mit derselben Lage, die Claude live bekäme, plus den gerechneten Kandidaten des "
             "Kerns. Latenz = bis zum ersten Satz / bis zum Ende. Fakten-Flag = Name, Zahl oder Uhrzeit, die nicht "
             "in der Lage steht, ein Widerspruch zur Lage oder ein Rat nach vorn trotz R1 (Leben unter 40 % oder "
             "Todesrisiko ab 0,3). „still“ = der Coach sagt in diesem Moment nichts.", "",
             "Lauf 1: Systemprompt STRATEGE (`stratege_probe/system_1.txt`). Lauf 2: derselbe plus eine Längenregel "
             "(höchstens 25 Wörter, `system_2.txt`) – Lauf 1 sprach im Median 52 Wörter, rund 20 s Stimme. Blind-Kritik: "
             "je Lauf ein Challenger- und ein Carlos-Kritiker (neue Agenten ohne Code), A/B gemischt; Urteile in "
             "`stratege_probe/urteile_*.jsonl`.", ""]
    for n in laeufe:
        a = auswertung(n)
        teile += [f"## Lauf {n}", "",
                  f"- Aufrufe: {len(a['zeilen'])}, davon mit Fehler/Abbruch: {len(a['fehler'])}"
                  + (" (" + "; ".join(sorted({(r['fehler'] or '')[:60] for r in a['fehler']})) + ")" if a['fehler'] else ""),
                  f"- Latenz erster Satz: Median {statistics.median(a['erste']):.1f} s, p90 {_p90(a['erste']):.1f} s; "
                  f"ganze Antwort: Median {statistics.median(a['enden']):.1f} s, p90 {_p90(a['enden']):.1f} s"
                  if a["erste"] else "- Latenz: -",
                  f"- Länge: Median {statistics.median(a['woerter']):.0f} Wörter, höchstens {max(a['woerter'])}; "
                  f"Sätze Median {statistics.median(a['saetze']):.0f}" if a["woerter"] else "",
                  f"- Antworten mit Fakten-Flag: {sum(1 for *_, f in a['zeilen'] if f)} von {len(a['zeilen'])}", ""]
        if kritik and n in kritik:
            teile += [kritik[n], ""]
        for stamm in ("2026-09-28_192113", "2026-09-28_101426"):
            teile += [f"### Partie {stamm}", "",
                      "| Zeit | Lage in einem Satz | Carlos' Frage | Coach live (Kern) | Stratege (Claude) | Latenz | Fakten-Flag |",
                      "|---|---|---|---|---|---|---|"]
            for e, r, flags in a["zeilen"]:
                if e["stamm"] != stamm:
                    continue
                frage = e["frage"] or ("– (Leerlauf)" if e["art"] == "leerlauf" else f"– (Wendepunkt: {e['anlass']})")
                kern = e.get("kern") or ("still" + (f"; zuletzt {e['kern_vorher']}" if e.get("kern_vorher") else ""))
                lat = (f"{r['erster_s']:.1f} / {r['ende_s']:.1f} s" if r.get("erster_s") is not None
                       else ("Fehler" if r.get("fehler") else "–"))
                zelle = [e["uhr"], e["lage_satz"], frage, kern, r.get("text") or f"({r.get('fehler') or 'fehlt'})", lat,
                         "; ".join(flags) or "–"]
                teile.append("| " + " | ".join(z.replace("|", "/").replace("\n", " ") for z in zelle) + " |")
            teile.append("")
    BERICHT.write_text("\n".join(teile), encoding="utf-8")
    print(BERICHT)


# --- kritik ----------------------------------------------------------------------------------------------------------

def kritik(lauf_nr: int) -> str:
    """Die Blind-Urteile (AUS/urteile_<rolle>_<lauf>.jsonl) entblinden und zaehlen -> AUS/kritik_<lauf>.md."""
    momente = {e["id"]: e for e in json.loads((AUS / "momente.json").read_text(encoding="utf-8"))}
    schl = json.loads((AUS / f"blind_{lauf_nr}_schluessel.json").read_text(encoding="utf-8"))
    zeilen = ["| Kritiker | Stratege besser | Kern besser | gleich | Stratege-Quote (ohne gleich) | falsch S / K | "
              "gefährlich S / K |", "|---|---|---|---|---|---|---|"]
    je_art = []
    for rolle in ("challenger", "carlos"):
        d = AUS / f"urteile_{rolle}_{lauf_nr}.jsonl"
        if not d.exists():
            continue
        urteile = [json.loads(z) for z in d.read_text(encoding="utf-8").splitlines() if z.strip()]
        z = {"s": 0, "k": 0, "g": 0, "sf": 0, "kf": 0, "sg": 0, "kg": 0}
        art = {}
        for u in urteile:
            a_ist = schl.get(u["id"])
            if a_ist is None:
                continue
            s_seite = "B" if a_ist == "kern" else "A"
            k_seite = "A" if s_seite == "B" else "B"
            w = "g" if u["besser"] == "gleich" else ("s" if u["besser"] == s_seite else "k")
            z[w] += 1
            z["sf"] += bool(u.get(f"{s_seite}_falsch"))
            z["kf"] += bool(u.get(f"{k_seite}_falsch"))
            z["sg"] += bool(u.get(f"{s_seite}_gefaehrlich"))
            z["kg"] += bool(u.get(f"{k_seite}_gefaehrlich"))
            x = art.setdefault(momente[u["id"]]["art"], {"s": 0, "k": 0, "g": 0})
            x[w] += 1
        n = z["s"] + z["k"]
        zeilen.append(f"| {rolle} ({len(urteile)}) | {z['s']} | {z['k']} | {z['g']} | "
                      f"{(100 * z['s'] / n if n else 0):.0f} % | {z['sf']} / {z['kf']} | {z['sg']} / {z['kg']} |")
        je_art.append(f"{rolle}: " + "; ".join(f"{a} Stratege {v['s']} / Kern {v['k']} / gleich {v['g']}"
                                                for a, v in sorted(art.items())))
    text = "**Blind-Kritik**\n\n" + "\n".join(zeilen) + "\n\nNach Anlass: " + " · ".join(je_art)
    (AUS / f"kritik_{lauf_nr}.md").write_text(text, encoding="utf-8")
    return text


# --- Auftrag 014: Probe mit Schutzschicht (A1-A4) und Tor (A5) ----------------------------------------------------------
#
#     python werkzeuge/stratege_probe.py sammeln14        # die 70 aus 013 neu erfassen (Lage A1) + 30 neue (164326/173159)
#     python werkzeuge/stratege_probe.py fragen14         # Stratege mit Pruefung (A2), eine Wiederholung, sonst der Kern
#     python werkzeuge/stratege_probe.py blind14          # zwei Blind-Vorlagen (a, b) mit verschiedener A/B-Mischung
#     python werkzeuge/stratege_probe.py kritik14         # Urteile zaehlen, Tor pruefen
#     python werkzeuge/stratege_probe.py bericht14        # buecher/protokolle/STRATEGE_PROBE_014.md

AUS14 = AUS.parent / "buecher" / "protokolle" / "proben" / "stratege_probe_014"
BERICHT14 = BERICHT.parent / "STRATEGE_PROBE_014.md"
ALT = ("2026-09-28_192113", "2026-09-28_101426")
NEU = ("2026-09-27_164326", "2026-09-27_173159")


def _leerlauf_fenster(lauf, ab: float = 840.0, mindestens: float = 5.0) -> list[tuple[float, float]]:
    """Fenster ab 14:00 ohne gueltigen, gesagten Plan (lebend, nicht KAMPF/TOT) - wie fuehrmass.leerlauf, als Liste."""
    aus, start, letzt = [], None, None
    for t in lauf.takte:
        ok = (t.zeit >= ab and t.modus not in (None, "KAMPF", "TOT") and not getattr(t, "tot", False)
              and not getattr(t, "plan_gesagt", False))
        if ok and start is None:
            start = t.zeit
        if not ok and start is not None:
            if letzt - start >= mindestens:
                aus.append((start, letzt))
            start = None
        letzt = t.zeit
    return aus


def _wendepunkte(lauf, ab: float) -> list[tuple[float, str]]:
    wp, letzt = [], -1e9
    for t, art in fuehrmass.wendepunkte(lauf, ab):
        if art in ("Struktur", "Objective") and t - letzt >= 60.0:
            wp.append((t, art))
            letzt = t
    return wp


def _erfassen(stamm: str, ziele: list, fragen_: list) -> list[dict]:
    """Je Ziel (Zeit, Art, Info) die Lage im ersten Takt ab dieser Zeit - Prompt ohne Verlauf, Lage fuer die Pruefung,
    was der Kern sagt."""
    from lolcoach import gehirn, stratege
    pfad = ns.pfad_zu(stamm)
    g = gehirn.Gehirn()
    akte = ns.AUFNAHMEN / f"{stamm}_spielakte.md"
    g.akte = akte.read_text(encoding="utf-8") if akte.exists() else None
    offen = sorted(ziele, key=lambda x: x[0])
    erfasst = []

    def beim_takt(p, werk, kern, plan):
        while offen and p.zeit >= offen[0][0]:
            t, art, info = offen.pop(0)
            if kern.m is None or kern.m.b is None:
                continue
            if art == "frage":
                frage, fid = info
                anlass, ende = frage, f"Frage des Spielers: {frage}"
            else:
                frage, fid = None, None
                was = "Leerlauf: seit ein paar Sekunden kein Plan-Satz" if art == "leerlauf" else f"Wendepunkt ({info})"
                anlass, ende = "Was jetzt, und warum?", f"ANLASS: {was} um {ns.uhr(p.zeit)}. Was jetzt, und warum?"
            lage = kern.kontext() or ""
            inhalt = g.kontext(anlass, p, lage)
            if (kopf := kern.kopfzeile()):
                inhalt = f"{kopf}\n\n{inhalt}"
            inhalt += f"\n\nKANDIDATEN DES COACHS (gerechnet, keine Vorgabe):\n{_kandidaten(kern)}"
            erfasst.append({"stamm": stamm, "zeit": p.zeit, "uhr": ns.uhr(p.zeit), "art": art,
                            "anlass": info if art != "frage" else None, "frage": frage, "fid": fid,
                            "basis": inhalt, "ende": ende, "kontext": lage, "lage_satz": _lage_satz(kern),
                            "r1": _r1(kern), "leben": kern.m.leben, "pruef_lage": stratege.pruef_lage(kern, p)})
    lauf = ns.durchspielen(pfad, beim_takt=beim_takt, fragen=fragen_ or None)
    antworten = {r["id"]: r for r in lauf.antworten}
    for e in erfasst:
        if e["art"] == "frage":
            r = antworten.get(e["fid"]) or {}
            e["kern"], e["kern_absicht"] = r.get("text"), r.get("absicht")
        else:
            gesagt = [a for a in lauf.gesagt if a.schluessel.startswith("kern:") and a.schluessel != "kern:INFO_FLASH"
                      and e["zeit"] - 1.0 <= ns.gesprochen_um(a) <= e["zeit"] + 8.0]
            e["kern"] = gesagt[0].text if gesagt else None
    return erfasst


def sammeln14() -> None:
    from lolcoach.kern import fragen as F
    AUS14.mkdir(parents=True, exist_ok=True)
    alt = json.loads((AUS / "momente.json").read_text(encoding="utf-8"))
    momente = []
    for stamm in ALT:
        vorher = [e for e in alt if e["stamm"] == stamm]
        fragen_ = []
        if stamm.endswith("192113"):
            for i, f in enumerate(fuehrmass.fragen_aus_log(stamm)):
                if F.absicht(f["text"]) in ("NOTIZ", "OFFEN") and F._innere_frage(f["text"]) is None:
                    continue
                fragen_.append((f["zeit"], f["text"], f"f{i}"))
        text_je_fid = {fid: text for _, text, fid in fragen_}
        # dieselben Momente wie 013: die Zeit des erfassten Takts, dieselben Fragen davor (derselbe Kern-Zustand)
        ziele = [(e["zeit"], e["art"], (text_je_fid[e["fid"]], e["fid"]) if e["art"] == "frage" else e["anlass"])
                 for e in vorher]
        neu = {(round(x["zeit"], 2), x["art"]): x for x in _erfassen(stamm, ziele, fragen_)}
        for e in vorher:
            x = neu.get((round(e["zeit"], 2), e["art"]))
            if x is not None:
                x["id"] = e["id"]
                momente.append(x)
    rnd = random.Random(14)
    zaehler = 0
    for stamm in NEU:
        lauf1 = ns.durchspielen(ns.pfad_zu(stamm))
        wp = _wendepunkte(lauf1, 600.0)
        ll = [((a + b) / 2, a, b) for a, b in _leerlauf_fenster(lauf1)]
        wp = sorted(rnd.sample(wp, min(8, len(wp))))
        ll = sorted(rnd.sample(ll, min(15 - len(wp), len(ll))))
        ziele = [(t, "wendepunkt", art) for t, art in wp] + [(t, "leerlauf", "Leerlauf") for t, *_ in ll]
        for x in sorted(_erfassen(stamm, ziele, []), key=lambda x: x["zeit"]):
            x["id"] = f"n{zaehler:02d}"
            zaehler += 1
            momente.append(x)
    (AUS14 / "momente.json").write_text(json.dumps(momente, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(momente)} Momente: alt {sum(1 for e in momente if e['stamm'] in ALT)}, "
          f"neu {sum(1 for e in momente if e['stamm'] in NEU)}")


def _frage_einmal(prompt: str, system: str) -> dict:
    from lolcoach import llm
    t0 = time.perf_counter()
    erster = [None]

    def bei_satz(s):
        if erster[0] is None:
            erster[0] = time.perf_counter() - t0
    try:
        text = llm.frage_strom(prompt, bei_satz, system=system, modell="sonnet", timeout=40, aufwand="low",
                               nachladen=True).strip()
        fehler = None
    except llm.LLMFehler as x:
        text, fehler = "", str(x)
    return {"text": " ".join(text.split()), "erster_s": erster[0], "ende_s": time.perf_counter() - t0,
            "fehler": fehler}


def fragen14() -> None:
    """A2-A4: Verlauf (eigene Saetze <= 60 s), Pruefung, bei Verwerfen einmal neu mit dem Grund, sonst der Kern-Satz."""
    from lolcoach import llm, stratege
    system = stratege.STRATEGE_SYSTEM
    (AUS14 / "system.txt").write_text(system, encoding="utf-8")
    momente = json.loads((AUS14 / "momente.json").read_text(encoding="utf-8"))
    ziel = AUS14 / "antworten.jsonl"
    fertig = {json.loads(z)["id"]: json.loads(z) for z in ziel.read_text(encoding="utf-8").splitlines()} \
        if ziel.exists() else {}
    llm.vorhalten("sonnet", system, "low")
    verlauf: dict[str, list] = {}
    for e in sorted(momente, key=lambda e: (e["stamm"], e["zeit"])):
        v = verlauf.setdefault(e["stamm"], [])
        if e["id"] in fertig:
            r = fertig[e["id"]]
            if r["quelle"] == "stratege":
                v.append((e["zeit"], r["text"]))
            continue
        eigene = [(t, s) for t, s in v if e["zeit"] - t <= 60.0][-2:]
        prompt = e["basis"]
        if eigene:
            prompt += "\n\nDEINE LETZTEN SAETZE (hoechstens 60 s alt): " + " | ".join(
                f"{ns.uhr(t)} „{s}“" for t, s in eigene)
        prompt += f"\n\n{e['ende']}"
        versuche = []
        a = _frage_einmal(prompt, system)
        a["text"] = stratege.kuerzen(a["text"])          # Auftrag 015, 6
        a["gruende"] = stratege.pruefe(a["text"], e["pruef_lage"]) if a["text"] else ["keine Antwort"]
        versuche.append(a)
        if a["gruende"]:
            b = _frage_einmal(prompt + f"\n\nDein Vorschlag „{a['text']}“ wurde verworfen: {'; '.join(a['gruende'])}. "
                              "Sag es neu, ohne das.", system)
            b["text"] = stratege.kuerzen(b["text"])
            b["gruende"] = stratege.pruefe(b["text"], e["pruef_lage"]) if b["text"] else ["keine Antwort"]
            versuche.append(b)
        ok = next((x for x in versuche if not x["gruende"]), None)
        if ok is not None:
            quelle, text = "stratege", ok["text"]
            v.append((e["zeit"], text))
        else:
            quelle, text = ("kern", e["kern"]) if e.get("kern") else ("still", None)
        r = {"id": e["id"], "quelle": quelle, "text": text, "versuche": versuche, "uhrzeit": time.strftime("%H:%M:%S")}
        with ziel.open("a", encoding="utf-8") as d:
            d.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{e['id']} {e['stamm'][-6:]} {e['uhr']} {quelle} {len(versuche)}x "
              f"{(text or '-')[:80]} {'VERWORFEN: ' + '; '.join(versuche[0]['gruende']) if versuche[0]['gruende'] else ''}",
              flush=True)


def _antworten14() -> dict:
    return {r["id"]: r for r in map(json.loads, (AUS14 / "antworten.jsonl").read_text(encoding="utf-8").splitlines())}


def blind14() -> None:
    momente = json.loads((AUS14 / "momente.json").read_text(encoding="utf-8"))
    antw = _antworten14()
    for durchgang, samen in (("a", 141), ("b", 142)):
        rnd = random.Random(samen)
        schluessel, teile = {}, []
        for e in rnd.sample(momente, len(momente)):
            r = antw.get(e["id"]) or {}
            s = r.get("text") or "(still – der Coach sagt in diesem Moment nichts)"
            kern = e.get("kern") or "(still – der Coach sagt in diesem Moment nichts)"
            a_ist_kern = rnd.random() < 0.5
            schluessel[e["id"]] = "kern" if a_ist_kern else "stratege"
            a, b = (kern, s) if a_ist_kern else (s, kern)
            was = f"Frage des Spielers: „{e['frage']}“" if e["frage"] else (
                "Keine Frage – Leerlauf, der Coach schweigt seit ein paar Sekunden." if e["art"] == "leerlauf"
                else f"Keine Frage – Wendepunkt ({e['anlass']}).")
            teile.append(f"## {e['id']} · {e['uhr']}\n\n{was}\n\nLAGE (was der Coach weiß):\n{e['kontext']}\n\n"
                         f"**A:** {a}\n\n**B:** {b}\n")
        (AUS14 / f"blind_{durchgang}.md").write_text("\n".join(teile), encoding="utf-8")
        (AUS14 / f"blind_{durchgang}_schluessel.json").write_text(json.dumps(schluessel, indent=1), encoding="utf-8")
    print(f"{len(momente)} Momente, zwei Vorlagen in {AUS14}")


def _zaehle14(rolle: str, durchgang: str, momente: dict) -> dict | None:
    d = AUS14 / f"urteile_{rolle}_{durchgang}.jsonl"
    if not d.exists():
        return None
    schl = json.loads((AUS14 / f"blind_{durchgang}_schluessel.json").read_text(encoding="utf-8"))
    z = {m: {"s": 0, "k": 0, "g": 0, "sf": 0, "kf": 0, "sg": 0, "kg": 0, "n": 0} for m in ("alt", "neu")}
    for zeile in d.read_text(encoding="utf-8").splitlines():
        if not zeile.strip():
            continue
        u = json.loads(zeile)
        if u.get("id") not in schl:
            continue
        menge = "neu" if momente[u["id"]]["stamm"] in NEU else "alt"
        s_seite = "B" if schl[u["id"]] == "kern" else "A"
        k_seite = "A" if s_seite == "B" else "B"
        x = z[menge]
        x["n"] += 1
        x["g" if u["besser"] == "gleich" else ("s" if u["besser"] == s_seite else "k")] += 1
        x["sf"] += bool(u.get(f"{s_seite}_falsch"))
        x["kf"] += bool(u.get(f"{k_seite}_falsch"))
        x["sg"] += bool(u.get(f"{s_seite}_gefaehrlich"))
        x["kg"] += bool(u.get(f"{k_seite}_gefaehrlich"))
    return z


def kritik14() -> tuple[str, bool]:
    from lolcoach import stratege
    momente = {e["id"]: e for e in json.loads((AUS14 / "momente.json").read_text(encoding="utf-8"))}
    antw = _antworten14()
    laeufe = {(r, d): _zaehle14(r, d, momente) for r in ("challenger", "carlos") for d in ("a", "b")}
    laeufe = {k: v for k, v in laeufe.items() if v is not None}
    zeilen = ["| Kritiker | Menge | Stratege besser | Kern besser | gleich | Quote Stratege | falsch S / K | "
              "gefährlich S / K |", "|---|---|---|---|---|---|---|---|"]
    mittel = {m: {k: 0.0 for k in ("s", "k", "g", "sf", "kf", "sg", "kg")} for m in ("alt", "neu")}
    for (rolle, dg), z in laeufe.items():
        for m in ("alt", "neu"):
            x = z[m]
            n = x["s"] + x["k"]
            zeilen.append(f"| {rolle} {dg} | {m} ({x['n']}) | {x['s']} | {x['k']} | {x['g']} | "
                          f"{100 * x['s'] / n if n else 0:.0f} % | {x['sf']} / {x['kf']} | {x['sg']} / {x['kg']} |")
            for k in mittel[m]:
                mittel[m][k] += x[k] / len(laeufe)
    for m in ("alt", "neu"):
        x = mittel[m]
        n = x["s"] + x["k"]
        zeilen.append(f"| **Mittel** | {m} | {x['s']:.1f} | {x['k']:.1f} | {x['g']:.1f} | "
                      f"**{100 * x['s'] / n if n else 0:.0f} %** | {x['sf']:.1f} / {x['kf']:.1f} | "
                      f"{x['sg']:.1f} / {x['kg']:.1f} |")
    # automatisch: die gesprochenen Stratege-Saetze noch einmal durch die Pruefung, dazu der Pruefer aus 013
    champs = _champions()
    vor_r1 = innere = zweit = 0
    for i, r in antw.items():
        if r["quelle"] != "stratege":
            continue
        gruende = stratege.pruefe(r["text"], momente[i]["pruef_lage"])
        vor_r1 += any(g.startswith(("nach vorn", "zu riskantes")) for g in gruende)
        zweit += any(f.startswith("Vorwaerts trotz R1") for f in pruefe(momente[i] | {"prompt": momente[i]["basis"]},
                                                                         r["text"], champs))
        innere += any(g.startswith("innerer Begriff") for g in gruende)
    tor = {
        "gefährlich S ≤ K (alt)": mittel["alt"]["sg"] <= mittel["alt"]["kg"],
        "gefährlich S ≤ K (neu)": mittel["neu"]["sg"] <= mittel["neu"]["kg"],
        "0 Vorwärts-Sätze trotz R1": vor_r1 == 0,
        "0 innere Begriffe": innere == 0,
        "falsch S ≤ K + 2 (alt)": mittel["alt"]["sf"] <= mittel["alt"]["kf"] + 2,
        "falsch S ≤ K + 2 (neu)": mittel["neu"]["sf"] <= mittel["neu"]["kf"] + 2,
        "Quote ≥ 65 % (neu)": (mittel["neu"]["s"] / (mittel["neu"]["s"] + mittel["neu"]["k"])
                               if mittel["neu"]["s"] + mittel["neu"]["k"] else 0) >= 0.65,
    }
    text = ("**Blind-Kritik (je Rolle zwei Durchgänge, neue Kritiker; Mittel über alle vier)**\n\n" + "\n".join(zeilen)
            + f"\n\n**Automatisch** (gesprochene Stratege-Sätze): Vorwärts trotz R1 {vor_r1}, innere Begriffe {innere}; "
            + f"zweite Meinung (grober Prüfer aus 013, von Hand nachzusehen): {zweit}."
            + "\n\n**Tor:** " + " · ".join(f"{k}: {'ja' if v else 'NEIN'}" for k, v in tor.items())
            + f"\n\n**Tor {'geschafft' if all(tor.values()) else 'nicht geschafft'}.**")
    (AUS14 / "kritik.md").write_text(text, encoding="utf-8")
    return text, all(tor.values())


def bericht14() -> None:
    momente = json.loads((AUS14 / "momente.json").read_text(encoding="utf-8"))
    antw = _antworten14()
    versuche = [x for r in antw.values() for x in r["versuche"]]
    erste = [r["versuche"][0] for r in antw.values()]
    ok = [x for x in versuche if x["text"] and not x["fehler"]]
    quellen = {q: sum(1 for r in antw.values() if r["quelle"] == q) for q in ("stratege", "kern", "still")}
    verworfen = [(i, r["versuche"][0]["gruende"]) for i, r in antw.items() if r["versuche"][0]["gruende"]]
    arten = {}
    for _, gr in verworfen:
        for g in gr:
            k = g.split(" (")[0]
            arten[k] = arten.get(k, 0) + 1
    endlich = [r["versuche"][-1]["ende_s"] + (r["versuche"][0]["ende_s"] if len(r["versuche"]) > 1 else 0)
               for r in antw.values()]
    t = ["# Stratege-Probe mit Schutzschicht (Auftrag 014)", "",
         "Offline nachgespielt, Systemprompt `stratege.STRATEGE_SYSTEM` (A3/A4), Lage mit A1 (`kern.kontext()`: "
         "„zuletzt gesehen vor N s … jetzt unbekannt“, DEINE ZAUBER, NACH VORN VERBOTEN). Jeder Satz geht durch "
         "`stratege.pruefe` (A2); verworfen wird einmal neu gefragt, mit dem Grund, danach gilt der Kern-Satz. "
         "Menge **alt** = die 70 Momente aus 013 (192113, 101426), **neu** = 30 aus 164326 und 173159 (Wendepunkte "
         "und Leerlauf, nicht zum Bauen benutzt).", "",
         f"- Aufrufe: {len(versuche)} ({len(antw)} Momente, {len(versuche) - len(antw)} Wiederholungen), Fehler: "
         f"{sum(1 for x in versuche if x['fehler'])}",
         f"- Gesprochen: Stratege {quellen['stratege']}, Kern-Satz (Fallback) {quellen['kern']}, still {quellen['still']}",
         f"- Beim ersten Versuch verworfen: {len(verworfen)} von {len(antw)} – "
         + ", ".join(f"{k} {v}" for k, v in sorted(arten.items(), key=lambda kv: -kv[1])),
         f"- Latenz erster Satz (erster Versuch): Median {statistics.median([x['erster_s'] for x in erste if x['erster_s']]):.1f} s, "
         f"p90 {_p90([x['erster_s'] for x in erste if x['erster_s']]):.1f} s; ganze Antwort Median "
         f"{statistics.median([x['ende_s'] for x in ok]):.1f} s; mit Wiederholung bis zum gültigen Satz p90 "
         f"{_p90(endlich):.1f} s",
         f"- Länge: Median {statistics.median([len(x['text'].split()) for x in ok]):.0f} Wörter, höchstens "
         f"{max(len(x['text'].split()) for x in ok)}", ""]
    if (AUS14 / "kritik.md").exists():
        t += [(AUS14 / "kritik.md").read_text(encoding="utf-8"), ""]
    for stamm in ALT + NEU:
        t += [f"## Partie {stamm} ({'neu' if stamm in NEU else 'alt'})", "",
              "| Zeit | Lage in einem Satz | Carlos' Frage | Coach live (Kern) | Stratege | Quelle | Verworfen (1. Versuch) |",
              "|---|---|---|---|---|---|---|"]
        for e in sorted((e for e in momente if e["stamm"] == stamm), key=lambda e: e["zeit"]):
            r = antw.get(e["id"]) or {}
            v0 = r.get("versuche", [{}])[0]
            frage = e["frage"] or ("– (Leerlauf)" if e["art"] == "leerlauf" else f"– (Wendepunkt: {e['anlass']})")
            weg = (f"„{v0.get('text', '')}“ – {'; '.join(v0['gruende'])}" if v0.get("gruende") else "–")
            zelle = [e["uhr"], e["lage_satz"], frage, e.get("kern") or "still", r.get("text") or "still",
                     r.get("quelle", "?"), weg]
            t.append("| " + " | ".join(z.replace("|", "/").replace("\n", " ") for z in zelle) + " |")
        t.append("")
    BERICHT14.write_text("\n".join(t), encoding="utf-8")
    print(BERICHT14)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    arg = sys.argv[1:]
    nr = int(arg[arg.index("--lauf") + 1]) if "--lauf" in arg else 1
    if arg and arg[0] == "sammeln":
        sammeln()
    elif arg and arg[0] == "fragen":
        system = STRATEGE
        if (AUS / f"system_{nr}.txt").exists():
            system = (AUS / f"system_{nr}.txt").read_text(encoding="utf-8").strip()
        fragen(nr, system)
    elif arg and arg[0] == "blind":
        blind(nr)
    elif arg and arg[0] == "kritik":
        print(kritik(nr))
    elif arg and arg[0] in ("sammeln15", "fragen15", "bericht15"):
        # Auftrag 015: dieselben 100 Momente mit der erweiterten Pruefung, ohne neue Kritik
        AUS14 = AUS.parent / "buecher" / "protokolle" / "proben" / "stratege_probe_015"
        BERICHT14 = BERICHT.parent / "STRATEGE_PROBE_015.md"
        {"sammeln15": sammeln14, "fragen15": fragen14, "bericht15": bericht14}[arg[0]]()
    elif arg and arg[0] in ("sammeln14", "fragen14", "blind14", "bericht14"):
        {"sammeln14": sammeln14, "fragen14": fragen14, "blind14": blind14, "bericht14": bericht14}[arg[0]]()
    elif arg and arg[0] == "kritik14":
        print(kritik14()[0])
    elif arg and arg[0] == "bericht":
        laeufe = [int(x) for x in arg[arg.index("--laeufe") + 1].split(",")] if "--laeufe" in arg else [nr]
        kritik = {}
        for n in laeufe:
            if (AUS / f"kritik_{n}.md").exists():
                kritik[n] = (AUS / f"kritik_{n}.md").read_text(encoding="utf-8")
        bericht(laeufe, kritik)
    else:
        print(__doc__)
