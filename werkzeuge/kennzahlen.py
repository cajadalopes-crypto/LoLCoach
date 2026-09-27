"""Kennzahlen je Aufnahme - altes System und Kern nebeneinander (Buch 0, Kapitel 12.3).

  - ungefragte Ansagen je 30 Minuten mit Daten (dazu, wie in Kapitel 1.2: Ankunftswarnungen "... bei dir" und
    Flash-Ansagen, Schluessel zauber/ohneflash/flashzurueck)
  - Kehrtwenden ohne neues Ereignis (Kapitel 9.4 Punkt 5)
  - Fassungswechsel (Qualitaetsrunde 1, Pruefung D): derselbe Plan des Kerns (ZURUECK und sein Back zaehlen als einer)
    kommt in <= 30 s mit anderem Satz wieder, ohne dass ein neuer Gegner genannt wird. Soll 0. Der erste "Jetzt back"
    nach "Raus zu ..." ist der Schritt des Plans, keine neue Fassung (D2).
  - Verstoesse gegen 9.4 je Nummer:
      1 kein aufloesbares Ziel ("die Welle", "die Tuerme", "seinen Turm" ohne Lane)
      2 Lane-/Wellenbefehl ausserhalb LANE/SEITE - bis der Kern den Modus liefert, genaehert: nicht auf deiner
        Lane und nicht (nach 14:00) auf einer Seitenlane; "an deiner Welle - geh hin" zaehlt als Weg
      3 Befehl auf einen Gegner, der > 3500 entfernt oder tot ist
      4 Team-Befehl, an dem du nicht teilnehmen kannst (dein Weg zum genannten Objective > sein Todesfenster)
      5 = Kehrtwenden; 6 (Widerspruch zum Plan) gibt es erst mit dem Kern
      7 "geh back" / "zurueck zu deiner Basis" in der Basis
  - Anteil GEFAHR / PLAN / ERINNERUNG / BESTAETIGUNG (Kern)
  - in der Lane-Phase: ungefragte Ansagen je 30 s (Abnahme Schritt 3: <= 1 im Mittel)
  - p_da-Brier (Kern, 7.5) gegen den schlimmsten Fall (p = 1, wenn frueheste Ankunft <= 10 s), auf denselben
    Proben. Wahrheit: der Gegner war in den naechsten 10 s sichtbar in 1500 um dich (wer ungesehen kam, zaehlt
    nicht - Grenze der Messung)
  - Kampf-Verstoesse (Buch 7, 11.3; Soll 0): in KAMPF eine alte Regel, ein Kern-Satz mit mehr als 5 Woertern,
    mehr als 3 Ansagen je Episode, ein Wechsel des Kampf-Rufs ohne Kampf-Ereignis (Kill/Tod oder neuer Gegner in 1500)
  - Objective-Ansagen ohne Chance (Buch 6, 14.4; Soll 0): eine Ansage von VORBEREITEN_OBJECTIVE, NEHMEN, STAPELN,
    WELLE_UND_RAUS, ZUR_GRUPPE oder WOHIN mit Objective, waehrend objective_zieht dafuer falsch war
  - Schranken-Verstoesse (Pruefung c, Soll 0): eine Vorwaerts-Ansage des Kerns mit Leben < vor_leben_min oder
    p_tod >= vor_p_tod_max im Takt des Sprechens, das Wort "schlaegst", ein Kauf-Satz mit einem Item, das nicht zum
    Inventar passt (kaufplan.kaufbar)
  - Datenluecken > 5 s (Wanduhr)
  - Szenario-Quote (tests/szenarien/<stamm>.toml, ohne Claude)

Geht in sinnpruefung.py auf (deren Pruefungen stecken in 1-4 und 7).

  - Auftrag 003 (Buch 11, 7): ungefragte Ansagen ohne INFO_FLASH und WENDEPUNKT (Ziel <= 50 je 30 min), Leerlauf,
    Wendepunkt-Verzug, Widersprueche, Stichwort-Antworten, Antwortzeit (werkzeuge/fuehrmass.py); mit --fragen werden
    die Fragen aus <stamm>_sprechtaste.log zur Zeit eingespielt

    python werkzeuge/kennzahlen.py [aufnahme ...] [--nur-kern] [--fragen]     (ohne Angabe: die 5 juengsten)

Altes System = --kern alt (Regelwerk mit der Modus-Sperre aus Schritt 2), Kern = --kern neu (Schritt 3).
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nachspielen as ns  # noqa: E402
from lolcoach import bewertung  # noqa: E402

LANE_WORT = re.compile(r"\b(Top|Mid|Bot)\b|\boben\b|\bunten\b", re.I)
OHNE_ZIEL = re.compile(r"\bdie Welle\b|\bdie Türme\b|\bseinen Turm\b", re.I)
WELLE = re.compile(r"(Schieb|Drück|Push|Farm|Crash|Halte)[^.]*\b(Welle|Kanonenwelle|Seitenwelle|seinen Turm)", re.I)
WEG = re.compile(r"an deiner Welle|\b(geh|lauf) (nach |zur )?(Top|Mid|Bot)\b", re.I)
BEFEHL_AUF = re.compile(r"^(Geh rein|Geh (sofort |jetzt )?auf (?P<a>[\w'.]+)|Greif (?P<b>[\w'.]+) an|Spiel auf "
                        r"(?P<c>[\w'.]+)|Trade (?P<d>[\w'.]+))", re.I)
BACK_BASIS = re.compile(r"\bgeh (dann |jetzt |sofort )?back\b|zurück zu deiner Basis", re.I)
TEAM = re.compile(r"Nehmt (jetzt )?(den |die )?(?P<obj>Baron|Drachen|Herold|Larven)", re.I)
FENSTER = re.compile(r"für (\d+) Sekunden tot|(\d+) Sekunden tot")
OBJ = {"baron": "baron", "drachen": "drache", "herold": "herold", "larven": "larven"}
FLASH_SCHL = ("zauber", "ohneflash", "flashzurueck")


def verstoesse(a, b) -> list[int]:
    """Nummern aus Kapitel 9.4, die dieser Satz verletzt (1, 2, 3, 4, 7)."""
    if b is None:
        return []
    t, aus = a.text, []
    if OHNE_ZIEL.search(t) and not LANE_WORT.search(t):
        aus.append(1)
    seite = b.zeit >= 840 and (b.ort or "") in ("oben", "unten")
    if WELLE.search(t) and b.ort and not (b.tiefe is not None or seite) and not WEG.search(t):
        aus.append(2)
    if m := BEFEHL_AUF.match(t):
        name = next((m.group(k) for k in "abcd" if m.group(k)), None)
        ziel = (next((g for g in b.gegner if g.champion.lower().startswith(name.lower())), None) if name else b.lane)
        if ziel is not None and (ziel.s.tot or ziel.abstand is None or ziel.abstand > 3500):
            aus.append(3)
    if (m := TEAM.search(t)) and b.pos is not None and (f := FENSTER.search(t)):
        obj = OBJ[m.group("obj").lower()]
        weg = bewertung.abstand(b.pos, bewertung.einheiten(*bewertung.GRUBEN[obj])) * 1.15 / b.mein_tempo
        if weg > int(f.group(1) or f.group(2)):
            aus.append(4)
    if BACK_BASIS.search(t) and "eurer Basis" in (b.ort or ""):
        aus.append(7)
    return aus


def brier_schlimmster_fall(lauf: ns.Lauf, fenster: float = 10.0, nah: float = 1500.0,
                           kern: bool = False) -> tuple[float, int, float]:
    """(Brier, Zahl der Proben, Grundrate) fuer p = 1 wenn frueheste Ankunft <= fenster - oder, mit `kern`, fuer das
    p_da des Gefahr-Modells (7.5) auf denselben Proben (lebende Gegner mit bekannter fruehester Ankunft)."""
    proben = lauf.proben
    fehler, n, treffer = 0.0, 0, 0
    for i, (t, ich, gegner) in enumerate(proben):
        spaeter = [pr for pr in proben[i + 1:i + 1 + int(fenster) + 2] if t < pr[0] <= t + fenster]
        for name, ankunft, sichtbar, seit, pos, tot, p_da in gegner:
            if tot or ankunft is None or (kern and p_da is None):
                continue
            p = p_da if kern else (1.0 if ankunft <= fenster else 0.0)
            da = any(s2 and pos2 is not None and bewertung.abstand(ich2, pos2) <= nah
                     for _, ich2, g2 in spaeter for n2, _, s2, _, pos2, _, _ in g2 if n2 == name)
            fehler += (p - float(da)) ** 2
            n += 1
            treffer += da
    return (fehler / n if n else math.nan), n, (treffer / n if n else math.nan)


FAMILIE = {"kern:BACK_JETZT": "kern:ZURUECK"}     # ZURUECK mit und ohne Back ist EIN Plan (Pruefung D1)


def fassungswechsel(lauf: ns.Lauf, fenster: float = 30.0) -> list[tuple[float, str, float, str]]:
    """Pruefung D4: aufeinanderfolgende Kern-Saetze desselben Plans in <= `fenster` s mit anderer Fassung (was vor dem
    ersten Doppelpunkt steht), ohne neuen Gegner im zweiten. [(t1, Satz 1, t2, Satz 2)]."""
    from szenarien import fassung
    kern = [a for a in lauf.gesagt if a.schluessel.startswith("kern:")]
    aus = []
    schritt_frei = True

    def ohne_anlass(a) -> str:
        # Auftrag 003: der Anlass eines WENDEPUNKT- oder FENSTER-Satzes ("Turm ist down: ...") ist das Ereignis, nicht
        # die Fassung - verglichen wird der Plan dahinter
        if getattr(a, "_kategorie", "") in ("WENDEPUNKT", "FENSTER") and ": " in a.text:
            return a.text.split(": ", 1)[1]
        return a.text
    for a1, a2 in zip(kern, kern[1:]):
        f1, f2 = FAMILIE.get(a1.schluessel, a1.schluessel), FAMILIE.get(a2.schluessel, a2.schluessel)
        t1, t2 = ns.gesprochen_um(a1), ns.gesprochen_um(a2)
        if f1 != f2 or t2 - t1 > fenster:
            schritt_frei = True
            continue
        if fassung(ohne_anlass(a1)) == fassung(ohne_anlass(a2)):
            continue
        if getattr(a2, "_kategorie", "") == "WENDEPUNKT":
            continue          # Buch 11, 4: ein Wendepunkt ist ein neues Ereignis (Struktur, Objective, Kill, Basis)
        if schritt_frei and a1.schluessel == "kern:ZURUECK" and a2.schluessel == "kern:BACK_JETZT":
            # der Back-Schritt des Rueckzugs, einmal (Pruefung D2 erlaubt ihn, wenn dich im Kanal keiner erreicht)
            schritt_frei = False
            continue
        neu = {c for c in lauf.champions if c and c in a2.text and c not in a1.text}
        if not neu:
            aus.append((t1, a1.text, t2, a2.text))
    return aus


def lane_phase_takt(lauf: ns.Lauf) -> tuple[int, float]:
    """(ungefragte Ansagen in der Lane-Phase, Sekunden Lane-Phase mit Daten) - Abnahme Schritt 3: <= 1 je 30 s."""
    ende = min([t.zeit for t in lauf.takte if t.modus in ("SEITE", "GRUPPE")] or [840.0])
    ende = min(ende, 840.0)
    sek = 0.0
    for a, b in zip(lauf.takte, lauf.takte[1:]):
        if b.zeit <= ende and b.wand - a.wand <= ns.LUECKE_AB:
            sek += max(0.0, b.zeit - a.zeit)
    n = sum(1 for a in lauf.gesagt if ns.gesprochen_um(a) <= ende and a.schluessel not in ("briefing", "kern:technik"))
    return n, sek


KAMPF_RUFE = ("kern:REIN", "kern:RAUS", "kern:DREHEN", "kern:HALTEN", "kern:ZIEL")
OBJ_ANSAGEN = ("VORBEREITEN_OBJECTIVE", "NEHMEN", "STAPELN", "WELLE_UND_RAUS", "ZUR_GRUPPE", "WOHIN")   # Buch 6, 14.4


def _takt_um(lauf: ns.Lauf, t: float):
    vorher = [x for x in lauf.takte if x.zeit <= t]
    return vorher[-1] if vorher else None


def kampf_verstoesse(lauf: ns.Lauf) -> list[tuple[float, str]]:
    """Buch 7, 11.3: was in KAMPF nicht sein darf - (Spielzeit, Grund)."""
    aus = []
    episoden = []            # [(von, bis)]
    for x in lauf.takte:
        if x.modus == "KAMPF":
            if episoden and x.zeit - episoden[-1][1] <= 1.5:
                episoden[-1][1] = x.zeit
            else:
                episoden.append([x.zeit, x.zeit])
    for von, bis in episoden:
        # im Kampf ist, was in einem KAMPF-Takt gesprochen wurde (wie im Protokoll) - nicht alles zwischen den
        # Episodengrenzen: der Modus wechselt im selben Takt zwischen KAMPF und LANE (144655 6:10 war LANE)
        drin = [a for a in lauf.gesagt if von <= ns.gesprochen_um(a) <= bis + 0.5
                and (x := _takt_um(lauf, ns.gesprochen_um(a))) is not None and x.modus == "KAMPF"]
        for a in drin:
            if getattr(a, "_regel", None) and a._regel != "_tod":      # der Rueckblick gehoert zu TOT (Buch 7, 8)
                aus.append((ns.gesprochen_um(a), f"alte Regel {a._regel}: {a.text[:50]}"))
            elif a.schluessel.startswith("kern:") and len(a.text.split()) > 5:
                aus.append((ns.gesprochen_um(a), f"{len(a.text.split())} Woerter: {a.text[:50]}"))
        kern = [a for a in drin if a.schluessel.startswith("kern:")]
        if len(kern) > 3:
            aus.append((von, f"{len(kern)} Ansagen in einer Episode"))
        rufe = [a for a in kern if a.schluessel.startswith(KAMPF_RUFE)]
        for a1, a2 in zip(rufe, rufe[1:]):
            if a1.schluessel == a2.schluessel:
                continue
            t1, t2 = ns.gesprochen_um(a1), ns.gesprochen_um(a2)
            x1, x2 = _takt_um(lauf, t1), _takt_um(lauf, t2)
            if x1 is None or x2 is None:
                continue
            if x2.kills == x1.kills and not (x2.nah_sichtbar - x1.nah_sichtbar):
                aus.append((t2, f"Wechsel ohne Ereignis: {a1.text} -> {a2.text}"))
    return aus


KAUF_ITEMS = re.compile(r"(?:^|[\s:])[Kk]auf ([^,.:]+?)(?:, dann|[.:]|$)")    # nicht "Verkauf"


def schranken_verstoesse(lauf: ns.Lauf) -> list[tuple[float, str]]:
    """Pruefung c, Ziel 3: in keinem Protokoll eine Vorwaerts-Handlung mit Leben < 40 % oder p_tod >= 0,3, kein
    "schlaegst", kein Kauf-Satz mit einem Item, das nicht zum Inventar passt."""
    from lolcoach.kern import konfig
    from lolcoach.kern import VOR_SCHRANKE
    cs = konfig()["schranken"]
    aus = []
    try:
        from lolcoach.kaufplan import kaufbar, _nach_name
    except ImportError:
        kaufbar = None
    for a in lauf.gesagt:
        t = ns.gesprochen_um(a)
        if "schlägst" in a.text:
            aus.append((t, f"schlaegst: {a.text[:60]}"))
        if a.schluessel.startswith("kern:") and a.schluessel.split(":", 1)[1] in VOR_SCHRANKE:
            x = _takt_um(lauf, t)
            if x is not None and x.leben is not None and x.leben < cs["vor_leben_min"]:
                aus.append((t, f"Leben {x.leben:.2f}: {a.text[:50]}"))
            elif x is not None and x.plan_ptod is not None and x.plan_ptod >= cs["vor_p_tod_max"]:
                aus.append((t, f"p_tod {x.plan_ptod:.2f}: {a.text[:50]}"))
        if kaufbar is not None and a.schluessel in ("kern:KAUFEN",):
            b = getattr(a, "_b", None)
            inventar = list(b.ich.items) if b is not None and b.ich is not None else []
            treffer = KAUF_ITEMS.search(a.text)
            if treffer:
                for name in re.split(r", | und ", treffer.group(1)):
                    name = re.sub(r"^(ein |eine |einen |den |die |das )", "", name.strip())
                    if name in ("Kontroll-Auge",) or name not in _nach_name():
                        continue
                    ok, grund = kaufbar(name, inventar)
                    if not ok:
                        aus.append((t, f"Kauf {name}: {grund}"))
    return aus


def objective_ohne_chance(lauf: ns.Lauf) -> list[tuple[float, str]]:
    """Buch 6, 14.4: Objective-Ansagen, waehrend objective_zieht falsch war."""
    aus = []
    for a in lauf.gesagt:
        if not a.schluessel.startswith("kern:"):
            continue
        art = a.schluessel.split(":", 1)[1]
        if art not in OBJ_ANSAGEN:
            continue
        t = ns.gesprochen_um(a)
        x = _takt_um(lauf, t)
        if x is None or not x.plan_obj or x.plan_obj not in x.obj_zieht:
            continue
        if not x.obj_zieht[x.plan_obj]:
            aus.append((t, a.text))
    return aus


def kennzahlen(pfad: Path, kern: str = "neu", fragen: bool = False) -> dict:
    import fuehrmass
    stamm = pfad.name.removesuffix(".jsonl.gz")
    liste = [(f["zeit"], f["text"], i) for i, f in enumerate(fuehrmass.fragen_aus_log(stamm))] if fragen else None
    lauf = ns.durchspielen(pfad, proben=True, kern_stellung=kern, fragen=liste)
    minuten = lauf.sekunden_mit_daten / 60
    gesagt = [a for a in lauf.gesagt if a.schluessel != "antwort"]      # Antworten sind nicht ungefragt
    v = {k: [] for k in (1, 2, 3, 4, 7)}
    for a in gesagt:
        for nr in verstoesse(a, getattr(a, "_b", None)):
            v[nr].append(a)
    kw = ns.kehrtwenden(lauf)
    brier, n, grund = brier_schlimmster_fall(lauf)
    brier_kern = brier_schlimmster_fall(lauf, kern=True)[0] if kern != "alt" else math.nan
    lp_n, lp_sek = lane_phase_takt(lauf)
    quote = None
    szen = Path(__file__).resolve().parent.parent / "tests" / "szenarien" / f"{pfad.name.removesuffix('.jsonl.gz')}.toml"
    if szen.exists():
        import io
        import contextlib
        import szenarien
        with contextlib.redirect_stdout(io.StringIO()):
            e = szenarien.pruefe_datei(szen, None, False, False, lauf=lauf, kern=kern)
        quote = (e["gruen"], e["gruen"] + e["rot"])
    return {"stamm": pfad.name.removesuffix(".jsonl.gz"), "minuten": minuten, "ansagen": len(gesagt),
            "je30": len(gesagt) / minuten * 30 if minuten else math.nan,
            "ankunft": sum("bei dir" in a.text for a in gesagt),
            "flash": sum(a.schluessel.split(":")[0] in FLASH_SCHL for a in gesagt),
            "kehrtwenden": kw, "fassungswechsel": fassungswechsel(lauf), "verstoesse": v, "brier": brier, "proben": n, "grundrate": grund,
            "luecken": lauf.luecken, "quote": quote, "brier_kern": brier_kern, "lane_phase": (lp_n, lp_sek),
            "kategorien": dict(lauf.kern.sprecher.kategorien) if lauf.kern is not None else {},
            "staerken": list(lauf.kern.staerken) if lauf.kern is not None else [], "kern": kern,
            "kampf": kampf_verstoesse(lauf), "ohne_chance": objective_ohne_chance(lauf),
            "schranken": schranken_verstoesse(lauf),
            # Auftrag 003, Teil A 4 / Buch 11, 4: INFO_FLASH und WENDEPUNKT zaehlen nicht zum Ziel <= 50 je 30 min
            "ohne_flash_wp": sum(1 for a in gesagt if getattr(a, "_kategorie", None) not in ("INFO_FLASH", "WENDEPUNKT")
                                 and a.schluessel != "kern:INFO_FLASH"),
            "fuehren": fuehrmass.kennzahlen(lauf, stamm)}


def ausgeben(k: dict) -> None:
    print(f"== {k['stamm']} (--kern {k['kern']}): {k['minuten']:.1f} Minuten mit Daten")
    print(f"   ungefragte Ansagen: {k['ansagen']} ({k['je30']:.0f} je 30 min; Ziel <= 45) - davon "
          f"Ankunft '... bei dir' {k['ankunft']}, Flash {k['flash']}")
    ow = k["ohne_flash_wp"]
    print(f"   ohne INFO_FLASH und WENDEPUNKT (Auftrag 003, Ziel <= 50): {ow} "
          f"({ow / k['minuten'] * 30 if k['minuten'] else math.nan:.0f} je 30 min)")
    n, sek = k["lane_phase"]
    print(f"   Lane-Phase: {n} Ansagen in {sek / 60:.1f} min = {n / (sek / 30) if sek else math.nan:.2f} je 30 s "
          f"(Abnahme Schritt 3: <= 1)")
    print(f"   Kehrtwenden ohne neues Ereignis: {len(k['kehrtwenden'])}")
    for t1, s1, t2, s2 in k["kehrtwenden"]:
        print(f"      {ns.uhr(t1)} \"{s1[:55]}\" -> {ns.uhr(t2)} \"{s2[:55]}\"")
    print(f"   Fassungswechsel (Pruefung D, Soll 0): {len(k['fassungswechsel'])}")
    for t1, s1, t2, s2 in k["fassungswechsel"]:
        print(f"      {ns.uhr(t1)} \"{s1[:55]}\" -> {ns.uhr(t2)} \"{s2[:55]}\"")
    print("   Verstoesse 9.4: " + ", ".join(f"{nr}: {len(x)}" for nr, x in k["verstoesse"].items())
          + f", 5: {len(k['kehrtwenden'])}")
    for nr, x in k["verstoesse"].items():
        for a in x[:3]:
            print(f"      {nr} {ns.uhr(ns.gesprochen_um(a))} {a.text[:110]}")
    kat = k["kategorien"]
    if kat and k["kern"] == "neu":
        print("   Kern: GEFAHR / PLAN / ERINNERUNG / BESTAETIGUNG / INFO_FLASH / WENDEPUNKT / VORSCHAU = "
              + " / ".join(str(kat.get(x, 0)) for x in ("GEFAHR", "PLAN", "ERINNERUNG", "BESTAETIGUNG", "INFO_FLASH",
                                                         "WENDEPUNKT", "VORSCHAU"))
              + (f"; Staerken: " + "; ".join(f"{ns.uhr(t)} {s}" for t, s in k["staerken"]) if k["staerken"] else ""))
    print(f"   Kampf-Verstoesse (Buch 7, Soll 0): {len(k['kampf'])}")
    for t, s in k["kampf"][:5]:
        print(f"      {ns.uhr(t)} {s}")
    print(f"   Schranken-Verstoesse (Pruefung c, Soll 0): {len(k['schranken'])}")
    for t, s in k["schranken"][:6]:
        print(f"      {ns.uhr(t)} {s[:100]}")
    print(f"   Objective-Ansagen ohne Chance (Buch 6, Soll 0): {len(k['ohne_chance'])}")
    for t, s in k["ohne_chance"][:5]:
        print(f"      {ns.uhr(t)} {s[:90]}")
    print(f"   p_da-Brier: schlimmster Fall {k['brier']:.3f} ({k['proben']} Proben, Grundrate {k['grundrate']:.3f})"
          + (f"   | Kern p_da {k['brier_kern']:.3f}" if not math.isnan(k["brier_kern"]) else ""))
    print("   Datenluecken > 5 s: " + (", ".join(f"{ns.uhr(a)}-{ns.uhr(b)} ({int(w)} s Wanduhr)"
                                          for a, b, w in k["luecken"]) or "keine"))
    import fuehrmass
    fuehrmass.ausgeben(k["fuehren"])
    print("   Szenario-Quote: " + (f"{k['quote'][0]} gruen / {k['quote'][1]} geprueft" if k["quote"]
                                     else "keine Szenarien"))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    nur_kern = "--nur-kern" in sys.argv
    pfade = [ns.pfad_zu(x) for x in args] or sorted(ns.AUFNAHMEN.glob("*.jsonl.gz"))[-5:]
    for p in pfade:
        for kern in (("neu",) if nur_kern else ("alt", "neu")):
            ausgeben(kennzahlen(p, kern, fragen="--fragen" in sys.argv))


if __name__ == "__main__":
    main()
