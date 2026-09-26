"""python -m lolcoach [live|abspielen|bericht|status|llm] ...

  live (Standard)       wartet auf eine Partie, coacht sie, schreibt sie mit (Daten + Minimap)
  abspielen [DATEI]     spielt eine Aufnahme durch denselben Code (Standard: die neueste)
  bericht [DATEI]       Post-Game-Bericht einer Aufnahme
  status                ein Schnappschuss, sofort
  llm "Frage"           prueft die Claude-Anbindung

  --ich CHAMPION        Perspektive setzen (Replay/Zuschauer haben keinen aktiven Spieler)
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from dataclasses import asdict

from . import ansicht, aufzeichnung, bericht, lage, liveapi, llm, regeln, sprechplan, stimme, zustand


def _verfolge(quelle, ich: str | None, takt: float, sprecher, schreiber=None, sicht=None,
              anzeigen=(), alle: int = 5, nur_coach: bool = False) -> sprechplan.Sprechplan:
    """Gemeinsamer Kern fuer Live und Aufnahme.

    `quelle` liefert (Wanduhr, Rohdaten); `sicht` hat `zwischen(bis, champions)`
    und liefert die Minimap-Sichtungen bis zu dieser Wanduhrzeit. Je Takt:
    Lagebild fortschreiben, Regeln pruefen, Sprechplan takten, Ereignisse und
    alle `alle` Takte die Uebersicht zeigen."""
    gesehen: set[int] = set()
    rollen_gezeigt = False
    werk, plan = regeln.Regelwerk(), sprechplan.Sprechplan(sprecher)
    lagebild = lage.Lagebild() if sicht else None
    for n, (w, daten) in enumerate(quelle):
        if schreiber:
            schreiber.schreibe(daten, w)
        p = zustand.partie(daten, ich)
        if not rollen_gezeigt and p.spieler:
            print(ansicht.rollen_tabelle(p))
            if p.zuschauer and not p.ich:
                print("(Zuschauer ohne --ich: Sicht Blau/Rot, der Coach schweigt)")
            rollen_gezeigt = True
        if sicht:
            for wb, sichtungen in sicht.zwischen(w, lage.champions(p)):
                lagebild.neu(p.zeit - (w - wb), sichtungen, p)
        if not nur_coach:
            for e in p.ereignisse:
                if e.id in gesehen:
                    continue
                gesehen.add(e.id)
                if satz := ansicht.ereignis(p, e):
                    print(satz)
        plan.neu(werk.pruefe(p, lagebild))
        if a := plan.takt(p.zeit):
            print(f"{ansicht.uhr(p.zeit)}  >> {a.text}", flush=True)
        for anzeige in anzeigen:
            anzeige.aktualisiere(p, lagebild, plan.gesagt)
        if n % alle == 0 and not nur_coach:
            print(ansicht.uebersicht(p))
        if takt:
            time.sleep(takt)
    return plan


def _dashboard():
    from . import dashboard
    try:
        d = dashboard.Dashboard()
    except OSError as e:
        print(f"Dashboard nicht gestartet ({e})")
        return None
    print(f"Dashboard: {d.url}")
    return d


def _live_quelle(basis: str, aus_nach: float = 10.0):
    """Liefert (Wanduhr, Schnappschuss), solange die Partie laeuft; endet, wenn
    die API `aus_nach` Sekunden lang nicht antwortet."""
    stumm_seit = None
    while True:
        try:
            daten = liveapi.alles(basis)
            yield time.time(), daten
            stumm_seit = None
        except liveapi.KeinSpiel:
            stumm_seit = stumm_seit or time.monotonic()
            if time.monotonic() - stumm_seit > aus_nach:
                return
            time.sleep(1)


class _LiveSicht:
    """Verbindet den Beobachter-Thread mit dem Kern: gibt ihm die Champions
    der Partie und holt ab, was er inzwischen gesehen hat."""

    def __init__(self, beobachter: lage.Beobachter):
        self.b = beobachter

    def zwischen(self, bis: float, champions):
        self.b.champions = champions
        return self.b.abholen()


def _ansagen_speichern(pfad, plan: sprechplan.Sprechplan) -> None:
    ziel = pfad.with_name(pfad.name.removesuffix(".jsonl.gz") + "_ansagen.json")
    ziel.write_text(json.dumps([asdict(a) for a in plan.gesagt], ensure_ascii=False, indent=0), encoding="utf-8")


def live(args) -> None:
    sprecher = stimme.Stumm() if args.stumm else stimme.Stimme()
    anzeigen = [] if args.ohne_dashboard else [d for d in [_dashboard()] if d]
    if not args.ohne_sprache:
        from . import sprache
        try:
            anzeigen.append(sprache.Gespraech(sprecher, args.ptt, args.modell_frage))
            print(f"Fragen an den Coach: Taste '{args.ptt}' gedrueckt halten und sprechen")
        except Exception as e:
            print(f"Sprachsteuerung aus ({type(e).__name__}: {e})")
    print("Warte auf eine Partie (Strg+C beendet) ...")
    while True:
        if not liveapi.laeuft(args.basis):
            time.sleep(2)
            continue
        schreiber = beobachter = None
        if not args.ohne_aufnahme:
            schreiber = aufzeichnung.Schreiber()
            print(f"Partie erkannt - Aufnahme: {schreiber.pfad}")
        if not args.ohne_bilder:
            ordner = schreiber.bilderordner if schreiber else None
            beobachter = lage.Beobachter(ordner)
            beobachter.start()
        sprecher.sage("Coach verbunden.")
        plan = None
        try:
            plan = _verfolge(_live_quelle(args.basis), args.ich, takt=1.0, sprecher=sprecher,
                             schreiber=schreiber, sicht=_LiveSicht(beobachter) if beobachter else None,
                             anzeigen=anzeigen)
        finally:
            if beobachter:
                beobachter.halt()
                print(f"Minimap: {beobachter.anzahl} Bilder ausgewertet"
                      + (f" - letzter Fehler: {beobachter.fehler}" if beobachter.fehler else ""))
            if schreiber:
                schreiber.schliesse()
                if plan:
                    _ansagen_speichern(schreiber.pfad, plan)
        if schreiber:
            # im Hintergrund: Claude braucht bis zu zwei Minuten, die naechste Partie nicht
            threading.Thread(target=_bericht_im_hintergrund, args=(schreiber.pfad, args.ich), daemon=False).start()
        print("Partie vorbei. Bericht wird geschrieben. Warte auf die naechste ...")


def _bericht_im_hintergrund(pfad, ich) -> None:
    try:
        ziel = bericht.schreibe(pfad, ich)
        print(f"Bericht: {ziel}", flush=True)
    except Exception as e:  # der Bericht darf den Coach nie beenden
        print(f"Bericht fehlgeschlagen: {type(e).__name__}: {e}", flush=True)


def bericht_befehl(args) -> None:
    pfad = args.datei or aufzeichnung.neueste()
    if not pfad:
        sys.exit("Keine Aufnahme gefunden.")
    ziel = bericht.schreibe(pfad, args.ich, mit_llm=not args.ohne_llm)
    print(ziel.read_text(encoding="utf-8"))
    print(f"\n-> {ziel}")


def abspielen(args) -> None:
    pfad = args.datei or aufzeichnung.neueste()
    if not pfad:
        sys.exit("Keine Aufnahme gefunden.")
    print(f"Aufnahme: {pfad}")
    sprecher = stimme.Stimme(warten=True) if args.laut else stimme.Stumm()
    bilder = [] if args.ohne_bilder else aufzeichnung.bilder(pfad)
    if bilder:
        print(f"Minimap: {len(bilder)} Bilder")
    plan = _verfolge(aufzeichnung.lies_mit_zeit(pfad), args.ich, takt=args.takt, sprecher=sprecher,
                     sicht=lage.SichtAusBildern(bilder) if bilder else None,
                     anzeigen=[d for d in [_dashboard() if args.dashboard else None] if d],
                     alle=args.alle, nur_coach=args.nur_coach)
    print(f"\n{len(plan.gesagt)} Ansagen.")


def frage_an_aufnahme(args) -> None:
    """Eine Frage wie per Mikrofon, aber als Text und gegen eine Aufnahme (mit Minimap)."""
    from . import antworten
    pfad = args.datei or aufzeichnung.neueste()
    bilder = aufzeichnung.bilder(pfad)
    sicht, lagebild, p = (lage.SichtAusBildern(bilder) if bilder else None), lage.Lagebild(), None
    for w, d in aufzeichnung.lies_mit_zeit(pfad):
        p = zustand.partie(d, args.ich)
        if sicht:
            for wb, s in sicht.zwischen(w, lage.champions(p)):
                lagebild.neu(p.zeit - (w - wb), s, p)
        if p.zeit >= args.minute * 60:
            break
    print(f"{ansicht.uhr(p.zeit)}  Du: {args.frage}")
    t = time.monotonic()
    antwort = antworten.sofort(args.frage, p, lagebild if sicht else None)
    quelle = "sofort"
    if antwort is None:
        antwort, quelle = antworten.mit_claude(args.frage, p, lagebild if sicht else None), "Claude"
    print(f"       Coach ({quelle}, {time.monotonic() - t:.2f} s): {antwort}")


def mikrotest(args) -> None:
    from . import sprache
    sprecher = stimme.Stimme()
    erkenner = sprache.Erkenner()

    def gehoert(audio):
        t = time.monotonic()
        text = erkenner.text(audio)
        print(f"  erkannt ({time.monotonic() - t:.2f} s, {erkenner.beschreibung}): {text}", flush=True)
        sprecher.sage(f"Verstanden: {text}" if text else "Nichts verstanden.", dringend=True)

    ptt = sprache.PushToTalk(args.ptt, gehoert, beim_druecken=sprecher.verstumme)
    print(f"Mikrofon: {ptt.geraet} bei {ptt.geraet_rate} Hz. Taste '{args.ptt}' halten, sprechen, loslassen. Strg+C beendet.")
    ptt.start()
    while True:
        time.sleep(1)


def status(args) -> None:
    try:
        p = zustand.partie(liveapi.alles(args.basis), args.ich)
    except liveapi.KeinSpiel as e:
        sys.exit(f"Keine Partie offen ({e})")
    print(ansicht.rollen_tabelle(p))
    print(ansicht.uebersicht(p))


def frage_llm(args) -> None:
    t = time.monotonic()
    try:
        print(llm.frage(args.frage, modell=args.modell))
    except llm.LLMFehler as e:
        sys.exit(f"LLM: {e}")
    print(f"({time.monotonic() - t:.1f} s)")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="lolcoach")
    ap.add_argument("--ich", help="Champion oder Name, aus dessen Sicht (Replay)")
    ap.add_argument("--basis", default=liveapi.BASIS, help=argparse.SUPPRESS)
    unter = ap.add_subparsers(dest="befehl")
    lv = unter.add_parser("live")
    lv.add_argument("--ohne-aufnahme", action="store_true")
    lv.add_argument("--ohne-bilder", action="store_true", help="keine Minimap (weder Erkennung noch Bilder)")
    lv.add_argument("--stumm", action="store_true")
    lv.add_argument("--ohne-dashboard", action="store_true")
    lv.add_argument("--ohne-sprache", action="store_true", help="keine Fragen per Mikrofon")
    lv.add_argument("--ptt", default="maus5", help="Push-to-Talk-Taste (maus4, maus5, f9, ...)")
    lv.add_argument("--modell-frage", default="haiku", help="Claude-Modell fuer freie Fragen")
    ab = unter.add_parser("abspielen")
    ab.add_argument("datei", nargs="?")
    ab.add_argument("--takt", type=float, default=0.0, help="Sekunden je Schnappschuss (0 = so schnell es geht)")
    ab.add_argument("--alle", type=int, default=60, help="Uebersicht alle N Schnappschuesse")
    ab.add_argument("--nur-coach", action="store_true", help="nur die Ansagen des Coaches")
    ab.add_argument("--laut", action="store_true", help="Ansagen vorlesen (wartet, bis jede gesprochen ist)")
    ab.add_argument("--ohne-bilder", action="store_true", help="Minimap-Bilder nicht auswerten")
    ab.add_argument("--dashboard", action="store_true", help="Dashboard mitlaufen lassen (sinnvoll mit --takt)")
    be = unter.add_parser("bericht")
    be.add_argument("datei", nargs="?")
    be.add_argument("--ohne-llm", action="store_true")
    fr = unter.add_parser("frage", help="eine Frage als Text an eine Aufnahme stellen")
    fr.add_argument("frage")
    fr.add_argument("datei", nargs="?")
    fr.add_argument("--minute", type=float, default=10.0)
    mt = unter.add_parser("mikrotest", help="Push-to-Talk und Spracherkennung ohne Partie pruefen")
    mt.add_argument("--ptt", default="maus5")
    unter.add_parser("status")
    lm = unter.add_parser("llm")
    lm.add_argument("frage")
    lm.add_argument("--modell", default="haiku")
    args = ap.parse_args()
    if args.befehl is None:
        args = ap.parse_args(sys.argv[1:] + ["live"])  # ohne Befehl: live mit allen Voreinstellungen
    {"live": live, "abspielen": abspielen, "bericht": bericht_befehl, "status": status,
     "llm": frage_llm, "frage": frage_an_aufnahme, "mikrotest": mikrotest}[args.befehl](args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
