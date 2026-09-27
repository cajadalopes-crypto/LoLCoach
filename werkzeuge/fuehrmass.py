"""Messen nach Buch 11, Kapitel 7 (Auftrag 003): Leerlauf, Wendepunkt-Verzug, Widersprueche, Stichwort-Antworten,
Antwortzeit - und die Fragen aus dem Sprechtasten-Log zum Einspielen (`protokoll.py --fragen`, Szenarien mit
`kern_frage`).

Das Messgeraet haengt nicht am Modell: was eine Handlung ist, was ein Wendepunkt ist, steht hier, nicht im Kern.
"""
from __future__ import annotations

import re
import statistics
from pathlib import Path

import nachspielen as ns

# Eine Antwort "mit Handlung" (Buch 11, 5, Regel 2): ein Verb oder Ziel, das Carlos tun kann - kein "Drache lebt."
HANDLUNG = re.compile(
    r"(?<![a-zäöüß])(geh|gehe|kauf|kaufe|verkauf|back|raus|rein|drück|drueck|nimm|nehmt|hol|farm|farmen|zieh|bleib|"
    r"warte|wart|lauf|schieb|push|split|tp|teleport|dreh|halte|halt|zurück|zurueck|zum|zur|zu deinem|zu den|"
    r"mit der gruppe|auf den|welle|platte|platten|dann|nicht)(?![a-zäöüß])", re.I)
PLAN_KATEGORIEN = ("PLAN", "WENDEPUNKT", "VORSCHAU", "FENSTER", "ERINNERUNG", "GEFAHR")
# Auftrag 004, Teil C 3: verbotene Floskeln (in Ansagen und Antworten)
FLOSKELN = ("bis sich etwas öffnet", "danach rechne ich neu", "ist gerade keine option.")
STILL = ("kern:INFO_FLASH", "kern:bestaetigung")
LOG_DRUCK = re.compile(r"^(\d+):(\d\d) gedrueckt ([0-9.]+) s")
LOG_TEXT = re.compile(r"erkannt nach ([0-9.]+) s, an die Stimme nach ([0-9.]+) s \(([^)]*)\): (.*)$")


def hat_handlung(text: str | None) -> bool:
    return bool(text) and bool(HANDLUNG.search(text))


def fragen_aus_log(stamm: str) -> list[dict]:
    """Die Fragen per Sprechtaste: [{zeit (Ende des Drueckens), text, live_s (bis zur Stimme), live_wie}]."""
    datei = ns.AUFNAHMEN / f"{stamm}_sprechtaste.log"
    if not datei.exists():
        return []
    aus, druck = [], None
    for z in datei.read_text(encoding="utf-8", errors="replace").splitlines():
        if (m := LOG_DRUCK.match(z.strip())):
            druck = int(m.group(1)) * 60 + int(m.group(2)) + float(m.group(3))
        elif druck is not None and (m := LOG_TEXT.search(z)):
            aus.append({"zeit": druck, "text": m.group(4).strip(), "live_s": float(m.group(2)),
                        "live_wie": m.group(3)})
            druck = None
    return aus


# --- Wendepunkte (Buch 11, 4 und 7) -------------------------------------------------------------------------------

def wendepunkte(lauf: ns.Lauf, ab: float = 0.0) -> list[tuple[float, str]]:
    """Turmfall (auch Inhibitor), Objective-Kill, Verlassen der Basis - [(Zeit, Art)]. Die Basis zaehlt als verlassen,
    wenn du >= 3 s in BASIS warst und danach >= 3 s lebend woanders bist (die Minimap flackert)."""
    aus = []
    t = lauf.takte
    for a, b in zip(t, t[1:]):
        if b.zeit < ab:
            continue
        if getattr(b, "strukturen", 0) > getattr(a, "strukturen", 0):
            aus.append((b.zeit, "Struktur"))
        if getattr(b, "obj_kills", 0) > getattr(a, "obj_kills", 0):
            aus.append((b.zeit, "Objective"))
    basis_seit, draussen_seit = None, None
    for x in t:
        if x.zeit < ab:
            continue
        if x.modus == "BASIS":
            basis_seit = basis_seit if basis_seit is not None else x.zeit
            draussen_seit = None
        elif x.modus not in ("TOT", None) and not getattr(x, "tot", False) and basis_seit is not None:
            draussen_seit = draussen_seit if draussen_seit is not None else x.zeit
            if x.zeit - draussen_seit >= 3.0:
                if draussen_seit - basis_seit >= 3.0:
                    aus.append((draussen_seit, "Basis verlassen"))
                basis_seit, draussen_seit = None, None
    return sorted(aus)


def _plansaetze(lauf: ns.Lauf) -> list:
    """Gesprochene Plan-Saetze: Kern-Saetze ausser INFO_FLASH und Bestaetigung, dazu Antworten."""
    return [a for a in lauf.gesagt if (a.schluessel.startswith("kern:") and a.schluessel not in STILL)
            or a.schluessel == "antwort"]


def _satzende(lauf: ns.Lauf, t: float) -> float:
    """Auftrag 004, Teil A 2: laeuft um `t` ein Satz, zaehlt der Verzug ab seinem Ende (gleiche Schaetzung wie die
    nachgespielte Stimme: Zeichen / sprechplan.ZEICHEN_PRO_SEKUNDE)."""
    from lolcoach import sprechplan, stimme
    ende = t
    for a in lauf.gesagt:
        g = a.gesprochen
        if g is None or g > t:
            continue
        e = g + len(stimme.sprechbar(a.text)) / sprechplan.ZEICHEN_PRO_SEKUNDE
        if e > t:
            ende = max(ende, e)
    return ende


def floskeln(lauf: ns.Lauf) -> list[tuple[float, str]]:
    """Ansagen und Antworten mit einer verbotenen Floskel (Auftrag 004, Teil C 3)."""
    aus = []
    for a in lauf.gesagt:
        if any(f in a.text.lower() for f in FLOSKELN):
            aus.append((ns.gesprochen_um(a), a.text[:90]))
    return aus


def _takt(lauf: ns.Lauf, t: float):
    vor = [x for x in lauf.takte if x.zeit <= t]
    return vor[-1] if vor else None


def wendepunkt_verzug(lauf: ns.Lauf, ab: float = 0.0) -> list[tuple[float, str, float | None, str]]:
    """Je Wendepunkt: (Zeit, Art, Verzug bis zum naechsten Plan-Satz oder None, Vermerk).

    Ausgenommen (Vermerk): du bist tot oder in KAMPF - dann zaehlt der Verzug ab dem Ende des Kampfs. Beim Verlassen
    der Basis gilt ein Plan-Satz aus der Basis, <= 60 s davor, als rechtzeitig (er nannte das Ziel fuer draussen).
    Ein Wendepunkt derselben Art <= 60 s nach einem mit Satz gilt als gedeckt (die drei Larven in 35 s)."""
    saetze = sorted(_plansaetze(lauf), key=ns.gesprochen_um)
    aus = []
    gedeckt: dict = {}           # Art -> Zeit des letzten Wendepunkts dieser Art mit Satz
    for t, art in wendepunkte(lauf, ab):
        if art != "Basis verlassen" and t - gedeckt.get(art, -1e9) <= 60.0:
            aus.append((t, art, 0.0, "Folge desselben Anlasses"))
            continue
        x = _takt(lauf, t)
        if x is not None and getattr(x, "tot", False):
            aus.append((t, art, None, "tot"))
            continue
        start = t
        if x is not None and x.modus == "KAMPF":
            nach = [y for y in lauf.takte if y.zeit >= t and y.modus != "KAMPF"]
            start = nach[0].zeit if nach else t
        start = _satzende(lauf, start)      # Auftrag 004: ab dem Ende des laufenden Satzes
        if art == "Basis verlassen":
            vorher = [a for a in saetze if t - 60.0 <= ns.gesprochen_um(a) <= t
                      and (_takt(lauf, ns.gesprochen_um(a)) or x).modus in ("BASIS", "TOT")]
            if vorher:
                aus.append((t, art, 0.0, "Satz in der Basis"))
                continue

        folgend = [ns.gesprochen_um(a) for a in saetze if ns.gesprochen_um(a) >= start - 0.5]
        verzug = (folgend[0] - start) if folgend and folgend[0] - start <= 60.0 else None
        if verzug is not None and verzug <= 3.0:
            gedeckt[art] = t
        aus.append((t, art, verzug, "nach dem Kampf" if start != t else ""))
    return aus


def leerlauf(lauf: ns.Lauf, ab: float = 840.0) -> tuple[float, float]:
    """(Sekunden ohne gueltigen, gesagten Plan, Sekunden gezaehlt) - ab 14:00, lebend, nicht in KAMPF, mit Modus."""
    ohne, gesamt = 0.0, 0.0
    for a, b in zip(lauf.takte, lauf.takte[1:]):
        if a.zeit < ab or a.modus in (None, "KAMPF", "TOT") or getattr(a, "tot", False):
            continue
        dt = min(2.0, max(0.0, b.zeit - a.zeit))
        gesamt += dt
        if not getattr(a, "plan_gesagt", False):
            ohne += dt
    return ohne, gesamt


def _ziel(lauf: ns.Lauf, a) -> str:
    z = getattr(a, "_ziel", None)
    if z:
        return z
    if a.schluessel.startswith("kern:"):
        x = _takt(lauf, ns.gesprochen_um(a))
        return x.plan_ziel if x is not None else ""
    return ""


def widersprueche(lauf: ns.Lauf, fenster: float = 60.0) -> list[tuple[float, str, float, str]]:
    """Buch 11, 7: ein Plan-Satz (PLAN, WENDEPUNKT, VORSCHAU, FENSTER oder Antwort) mit anderem Ziel als der vorige,
    in <= 60 s, ohne neues Ereignis (9.4 Punkt 5, dazu die Wendepunkte aus Buch 11, 4 und der Weg in die Basis) und
    ohne "Neu:" am Anfang."""
    saetze = [a for a in _plansaetze(lauf) if a.schluessel == "antwort"
              or getattr(a, "_kategorie", "PLAN") in ("PLAN", "WENDEPUNKT", "VORSCHAU", "FENSTER")]
    saetze.sort(key=ns.gesprochen_um)
    # Wendepunkte (Buch 11, 4) und der Weg in die Basis sind neue Ereignisse - danach darf das Ziel ein anderes sein
    ereignisse = [t for t, _ in wendepunkte(lauf)]
    ereignisse += [b.zeit for a, b in zip(lauf.takte, lauf.takte[1:]) if b.modus in ("BASIS", "TOT")
                   and a.modus not in ("BASIS", "TOT")]
    aus = []
    for a1, a2 in zip(saetze, saetze[1:]):
        t1, t2 = ns.gesprochen_um(a1), ns.gesprochen_um(a2)
        if any(t1 < e <= t2 for e in ereignisse):
            continue
        z1, z2 = _ziel(lauf, a1), _ziel(lauf, a2)
        if not z1 or not z2 or z1 == z2 or t2 - t1 > fenster:
            continue
        text2 = a2.text.split("“ – ", 1)[-1]
        if text2.startswith("Neu:") or ns.neues_ereignis(lauf, t1, t2):
            continue
        aus.append((t1, f"{z1}: {a1.text[:50]}", t2, f"{z2}: {a2.text[:50]}"))
    return aus


def stichwort_antworten(lauf: ns.Lauf) -> list[tuple[float, str]]:
    """Antworten ohne Handlung - bei Absichten, die eine verlangen, oder aus hoechstens drei Woertern (Buch 11, 5.2)."""
    aus = []
    for r in lauf.antworten:
        text = r.get("text") or ""
        if not text or r.get("quelle") == "claude" or text.strip().rstrip(".").lower() == "notiert":
            continue
        verlangt = r.get("absicht") in ("JETZT", "DANACH", "WARUM", "ENTWEDER", "SOLL_ICH", "KAUF") \
            or r.get("absicht") is None
        if (verlangt and not hat_handlung(text)) or len(text.split()) <= 3:
            aus.append((r["zeit"], f"{r['frage'][:40]} -> {text[:60]}"))
    return aus


def antwortzeiten(lauf: ns.Lauf, stamm: str) -> dict:
    """Median der Rechenzeit ohne Claude (nachgespielt) und, aus dem Live-Log, bis zur Stimme mit Claude."""
    ohne = [r["dauer"] for r in lauf.antworten if r.get("quelle") != "claude" and r.get("text")]
    live = [f["live_s"] for f in fragen_aus_log(stamm) if f["live_wie"] == "Claude"]
    return {"ohne_claude": statistics.median(ohne) if ohne else None, "ohne_n": len(ohne),
            "claude_n": sum(1 for r in lauf.antworten if r.get("quelle") == "claude"),
            "mit_claude_live": statistics.median(live) if live else None}


def kennzahlen(lauf: ns.Lauf, stamm: str) -> dict:
    ohne, gesamt = leerlauf(lauf)
    verzug = wendepunkt_verzug(lauf)
    werte = [v for _, _, v, _ in verzug if v is not None]
    return {"leerlauf": (ohne, gesamt), "verzug": verzug, "floskeln": floskeln(lauf),
            "verzug_median": statistics.median(werte) if werte else None,
            "widersprueche": widersprueche(lauf), "stichwort": stichwort_antworten(lauf),
            "antwortzeit": antwortzeiten(lauf, stamm)}


def ausgeben(k: dict) -> None:
    ohne, gesamt = k["leerlauf"]
    print(f"   Leerlauf ab 14:00 (Buch 11, Soll <= 10 %): "
          f"{100 * ohne / gesamt if gesamt else 0:.0f} % ({ohne:.0f} von {gesamt:.0f} s)")
    verzug = k["verzug"]
    fehlt = [x for x in verzug if x[2] is None and x[3] != "tot"]
    med = k["verzug_median"]
    print(f"   Wendepunkt-Verzug (Soll Median <= 3 s): Median {med:.1f} s" if med is not None
          else "   Wendepunkt-Verzug (Soll Median <= 3 s): keine Wendepunkte mit Satz",
          f"- {len(verzug)} Wendepunkte, ohne Satz in 60 s: {len(fehlt)}")
    for t, art, v, vermerk in fehlt[:4]:
        print(f"      {ns.uhr(t)} {art}: kein Plan-Satz")
    print(f"   Floskeln (Auftrag 004, Soll 0): {len(k.get('floskeln', []))}")
    for t, s in k.get("floskeln", [])[:3]:
        print(f"      {ns.uhr(t)} {s}")
    print(f"   Widersprueche (Soll 0): {len(k['widersprueche'])}")
    for t1, s1, t2, s2 in k["widersprueche"][:4]:
        print(f"      {ns.uhr(t1)} {s1} -> {ns.uhr(t2)} {s2}")
    az = k["antwortzeit"]
    if az["ohne_n"] or az["claude_n"] or az["mit_claude_live"] is not None:
        print(f"   Stichwort-Antworten (Soll 0): {len(k['stichwort'])}")
        for t, s in k["stichwort"][:4]:
            print(f"      {ns.uhr(t)} {s}")
        oc = f"{az['ohne_claude'] * 1000:.0f} ms ({az['ohne_n']} Antworten)" if az["ohne_claude"] is not None else "-"
        mc = f"{az['mit_claude_live']:.1f} s live" if az["mit_claude_live"] is not None else "-"
        print(f"   Antwortzeit ohne Claude (Soll <= 1 s): {oc}; mit Claude (Live-Log, vorher): {mc}; "
              f"jetzt an Claude: {az['claude_n']}")
