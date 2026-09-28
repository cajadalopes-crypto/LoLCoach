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
    elif arg and arg[0] == "bericht":
        laeufe = [int(x) for x in arg[arg.index("--laeufe") + 1].split(",")] if "--laeufe" in arg else [nr]
        kritik = {}
        for n in laeufe:
            if (AUS / f"kritik_{n}.md").exists():
                kritik[n] = (AUS / f"kritik_{n}.md").read_text(encoding="utf-8")
        bericht(laeufe, kritik)
    else:
        print(__doc__)
