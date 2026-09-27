"""Kennzahlen je Aufnahme - altes System und Kern nebeneinander (Buch 0, Kapitel 12.3).

  - ungefragte Ansagen je 30 Minuten mit Daten (dazu, wie in Kapitel 1.2: Ankunftswarnungen "... bei dir" und
    Flash-Ansagen, Schluessel zauber/ohneflash/flashzurueck)
  - Kehrtwenden ohne neues Ereignis (Kapitel 9.4 Punkt 5)
  - Verstoesse gegen 9.4 je Nummer:
      1 kein aufloesbares Ziel ("die Welle", "die Tuerme", "seinen Turm" ohne Lane)
      2 Lane-/Wellenbefehl ausserhalb LANE/SEITE - bis der Kern den Modus liefert, genaehert: nicht auf deiner
        Lane und nicht (nach 14:00) auf einer Seitenlane; "an deiner Welle - geh hin" zaehlt als Weg
      3 Befehl auf einen Gegner, der > 3500 entfernt oder tot ist
      4 Team-Befehl, an dem du nicht teilnehmen kannst (dein Weg zum genannten Objective > sein Todesfenster)
      5 = Kehrtwenden; 6 (Widerspruch zum Plan) gibt es erst mit dem Kern
      7 "geh back" / "zurueck zu deiner Basis" in der Basis
  - Anteil GEFAHR / PLAN / ERINNERUNG - erst mit dem Kern
  - p_da-Brier gegen den schlimmsten Fall (7.5): bis Schritt 3 nur der schlimmste Fall selbst (p = 1, wenn
    frueheste Ankunft <= 10 s) - die Latte, die das Gefahr-Modell unterbieten muss. Wahrheit: der Gegner war in
    den naechsten 10 s sichtbar in 1500 um dich (wer ungesehen kam, zaehlt nicht - Grenze der Messung)
  - Datenluecken > 5 s (Wanduhr)
  - Szenario-Quote (tests/szenarien/<stamm>.toml, ohne Claude)

Geht in sinnpruefung.py auf (deren Pruefungen stecken in 1-4 und 7).

    python werkzeuge/kennzahlen.py [aufnahme ...]      (ohne Angabe: die 5 juengsten)
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


def brier_schlimmster_fall(lauf: ns.Lauf, fenster: float = 10.0, nah: float = 1500.0) -> tuple[float, int, float]:
    """(Brier, Zahl der Proben, Grundrate) fuer p = 1 wenn frueheste Ankunft <= fenster."""
    proben = lauf.proben
    fehler, n, treffer = 0.0, 0, 0
    for i, (t, ich, gegner) in enumerate(proben):
        spaeter = [pr for pr in proben[i + 1:i + 1 + int(fenster) + 2] if t < pr[0] <= t + fenster]
        for name, ankunft, sichtbar, seit, pos, tot in gegner:
            if tot or ankunft is None:
                continue
            p = 1.0 if ankunft <= fenster else 0.0
            da = any(s2 and pos2 is not None and bewertung.abstand(ich2, pos2) <= nah
                     for _, ich2, g2 in spaeter for n2, _, s2, _, pos2, _ in g2 if n2 == name)
            fehler += (p - float(da)) ** 2
            n += 1
            treffer += da
    return (fehler / n if n else math.nan), n, (treffer / n if n else math.nan)


def kennzahlen(pfad: Path) -> dict:
    lauf = ns.durchspielen(pfad, proben=True)
    minuten = lauf.sekunden_mit_daten / 60
    gesagt = lauf.gesagt
    v = {k: [] for k in (1, 2, 3, 4, 7)}
    for a in gesagt:
        for nr in verstoesse(a, getattr(a, "_b", None)):
            v[nr].append(a)
    kw = ns.kehrtwenden(lauf)
    brier, n, grund = brier_schlimmster_fall(lauf)
    quote = None
    szen = Path(__file__).resolve().parent.parent / "tests" / "szenarien" / f"{pfad.name.removesuffix('.jsonl.gz')}.toml"
    if szen.exists():
        import io
        import contextlib
        import szenarien
        with contextlib.redirect_stdout(io.StringIO()):
            e = szenarien.pruefe_datei(szen, "alt", False, False, lauf=lauf)
        quote = (e["gruen"], e["gruen"] + e["rot"])
    return {"stamm": pfad.name.removesuffix(".jsonl.gz"), "minuten": minuten, "ansagen": len(gesagt),
            "je30": len(gesagt) / minuten * 30 if minuten else math.nan,
            "ankunft": sum("bei dir" in a.text for a in gesagt),
            "flash": sum(a.schluessel.split(":")[0] in FLASH_SCHL for a in gesagt),
            "kehrtwenden": kw, "verstoesse": v, "brier": brier, "proben": n, "grundrate": grund,
            "luecken": lauf.luecken, "quote": quote}


def ausgeben(k: dict) -> None:
    print(f"== {k['stamm']}: {k['minuten']:.1f} Minuten mit Daten")
    print(f"   ungefragte Ansagen: {k['ansagen']} ({k['je30']:.0f} je 30 min; Ziel <= 45) - davon "
          f"Ankunft '... bei dir' {k['ankunft']}, Flash {k['flash']}   | Kern: -")
    print(f"   Kehrtwenden ohne neues Ereignis: {len(k['kehrtwenden'])}   | Kern: -")
    for t1, s1, t2, s2 in k["kehrtwenden"]:
        print(f"      {ns.uhr(t1)} \"{s1[:55]}\" -> {ns.uhr(t2)} \"{s2[:55]}\"")
    print("   Verstoesse 9.4: " + ", ".join(f"{nr}: {len(x)}" for nr, x in k["verstoesse"].items())
          + f", 5: {len(k['kehrtwenden'])}, 6: -   | Kern: -")
    for nr, x in k["verstoesse"].items():
        for a in x[:3]:
            print(f"      {nr} {ns.uhr(ns.gesprochen_um(a))} {a.text[:110]}")
    print("   GEFAHR / PLAN / ERINNERUNG: - (Kern)")
    print(f"   p_da-Brier: schlimmster Fall {k['brier']:.3f} ({k['proben']} Proben, Grundrate {k['grundrate']:.3f})"
          f"   | Kern: -")
    print("   Datenluecken > 5 s: " + (", ".join(f"{ns.uhr(a)}-{ns.uhr(b)} ({int(w)} s Wanduhr)"
                                          for a, b, w in k["luecken"]) or "keine"))
    print("   Szenario-Quote (altes System): " + (f"{k['quote'][0]} gruen / {k['quote'][1]} geprueft"
                                                    if k["quote"] else "keine Szenarien"))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    pfade = [ns.pfad_zu(x) for x in args] or sorted(ns.AUFNAHMEN.glob("*.jsonl.gz"))[-5:]
    for p in pfade:
        ausgeben(kennzahlen(p))


if __name__ == "__main__":
    main()
