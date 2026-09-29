"""Ergibt die Ansage von Carlos' Position aus Sinn? - die Pruefung, die gefehlt hat.

Aufgegangen in werkzeuge/kennzahlen.py (Buch 0, Kapitel 12.3: Verstoesse gegen 9.4 je Nummer); bleibt fuer den
Vergleich mit frueheren Messungen, bis Schritt 8 aufraeumt.

Live 27.09. (Partie 102112, Minute 25-38): "Geh sofort auf Sett drauf" mit Sett auf der anderen Kartenseite,
"Schieb die Welle in seinen Turm und geh back" in der eigenen Basis, "Drueckt jetzt die Tuerme" ohne einen
Turm, "Nehmt jetzt Baron" zehnmal, waehrend die Bot-Mitspieler nie hingingen. ansagen_pruefen.py fand nichts
davon: es prueft Widersprueche, Hin und Her, Sprache - nie, ob der Rat zur Lage passt.

Je Ansage, gegen die Bewertung des Takts, in dem sie entstand:
  - ZIEL_WEIT: ein Befehl auf einen Gegner ("geh rein", "geh auf X") und der ist weiter als 3500 weg / tot,
  - NICHT_AUF_LANE: Welle schieben / "seinen Turm", aber du bist nicht auf deiner Lane,
  - BACK_IN_BASIS: "geh back", aber du stehst schon in der Basis,
  - OHNE_ZIEL: "die Tuerme" ohne zu sagen welche,
  - SCHLEIFE: derselbe Befehl zum dritten Mal in 5 Minuten.

    python werkzeuge/sinnpruefung.py [aufnahme ...] [--ab MINUTE]
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import aufzeichnung, lage, regeln, sprechplan, stimme, zustand  # noqa: E402

AUFNAHMEN = Path(__file__).resolve().parent.parent / "aufnahmen"
BEFEHL_AUF = re.compile(r"^(Geh rein|Geh (sofort |jetzt )?auf (?P<a>[\w'.]+)|Greif (?P<b>[\w'.]+) an|Spiel auf "
                        r"(?P<c>[\w'.]+)|Trade (?P<d>[\w'.]+))", re.I)
WELLE = re.compile(r"(Schieb|Drück|Push|Farm)[^.]*\b(Welle|Kanonenwelle|Seitenwelle|seinen Turm)", re.I)
BACK = re.compile(r"\bgeh (dann |jetzt )?back\b", re.I)
OHNE_ZIEL = re.compile(r"\bdie Türme\b(?![^.]*\b(Top|Mid|Bot|oben|unten|Mitte)\b)", re.I)
WEIT = 3500.0


def durchspielen(pfad: Path):
    sicht = lage.sicht_fuer(pfad)
    werk, plan = regeln.Regelwerk(), sprechplan.Sprechplan(stimme.Stumm())
    lb = lage.Lagebild() if sicht else None
    for w, d in aufzeichnung.lies_mit_zeit(pfad):
        p = zustand.partie(d)
        if sicht and p.ich:
            for wb, s in sicht.zwischen(w, lage.champions(p)):
                lb.neu(p.zeit - (w - wb), s, p)
            lb.ereignisse(lambda wb: p.zeit - (w - wb), sicht.ereignisse(), p)
        neu = werk.pruefe(p, lb)
        for a in neu:
            a._b = werk.b
        plan.neu(neu)
        plan.takt(p.zeit)
    return plan.gesagt


def fehler(a, b, verlauf) -> list[str]:
    aus = []
    if b is None:
        return aus
    t = a.text
    m = BEFEHL_AUF.match(t)
    if m:
        name = next((m.group(k) for k in "abcd" if m.group(k)), None)
        ziel = (next((g for g in b.gegner if g.champion.lower().startswith(name.lower())), None) if name
                else b.lane)
        if ziel is not None and (ziel.s.tot or ziel.abstand is None or ziel.abstand > WEIT):
            wo = "tot" if ziel.s.tot else ("unbekannt" if ziel.abstand is None else f"{int(ziel.abstand)} weg")
            aus.append(f"ZIEL_WEIT ({ziel.champion} {wo})")
    auf_lane = b.tiefe is not None
    # "in 27 Sekunden bist du an deiner Welle - geh hin" ist ein Weg dorthin, kein Unsinn; ohne bekannten Ort
    # (tot, Minimap verloren) laesst sich nichts sagen
    if (WELLE.search(t) and not auf_lane and b.ort and "an deiner Welle" not in t
            and not re.search(r"\b(geh|lauf) (nach |zur )?(Top|Mid|Bot)", t, re.I)):
        aus.append(f"NICHT_AUF_LANE (du: {b.ort or '?'})")
    if BACK.search(t) and "Basis" in (b.ort or ""):
        aus.append("BACK_IN_BASIS")
    if OHNE_ZIEL.search(t):
        aus.append("OHNE_ZIEL")
    # Schleife: derselbe BEFEHL (Team-Ruf, Plan) - Warnungen und Meldungen zu verschiedenen Ereignissen nicht
    art = a.schluessel
    if art.startswith(("jetzt:", "plan:", "inhib")):     # "zahlen": jeder neue Tod ist eine neue Lage
        frueher = [z for z in verlauf[art] if a.zeit - z <= 300]
        if len(frueher) >= 2:
            aus.append(f"SCHLEIFE ({len(frueher) + 1}x {art} in 5 min)")
        verlauf[art].append(a.zeit)
    return aus


def main() -> None:
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    ab = float(sys.argv[sys.argv.index("--ab") + 1]) * 60 if "--ab" in sys.argv else 0.0
    if "--ab" in sys.argv:
        args.remove(sys.argv[sys.argv.index("--ab") + 1])
    pfade = [Path(x) if Path(x).exists() else AUFNAHMEN / f"{x}.jsonl.gz" for x in args] or \
        aufzeichnung.alle(AUFNAHMEN)[-5:]
    gesamt = defaultdict(int)
    for pfad in pfade:
        gesagt = durchspielen(pfad)
        verlauf: dict = defaultdict(list)
        n = 0
        print(f"== {pfad.name}: {len(gesagt)} Ansagen")
        for a in gesagt:
            f = fehler(a, getattr(a, "_b", None), verlauf)
            if f and a.zeit >= ab:
                n += 1
                for x in f:
                    gesamt[x.split(" ")[0]] += 1
                print(f"  {int(a.zeit // 60)}:{int(a.zeit % 60):02d} {', '.join(f)} | {a.text[:150]}")
        print(f"  -> {n} unsinnige von {len(gesagt)}")
    print("Summe:", dict(gesamt))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
