"""python -m lolcoach [live|abspielen|status|llm] ...

  live (Standard)       wartet auf eine Partie, zeigt sie an, schreibt sie mit
  abspielen [DATEI]     spielt eine Aufnahme durch denselben Code (Standard: die neueste)
  status                ein Schnappschuss, sofort
  llm "Frage"           prueft die Claude-Anbindung

  --ich CHAMPION        Perspektive setzen (Replay/Zuschauer haben keinen aktiven Spieler)
"""
from __future__ import annotations

import argparse
import sys
import threading
import time

from . import ansicht, aufzeichnung, bericht, liveapi, llm, regeln, sprechplan, stimme, zustand


def _verfolge(quelle, ich: str | None, takt: float, sprecher, schreiber=None, alle: int = 5,
              nur_coach: bool = False) -> sprechplan.Sprechplan:
    """Gemeinsamer Kern fuer Live und Aufnahme: Regeln pruefen, Sprechplan
    takten, neue Ereignisse als Satz, alle `alle` Takte die Uebersicht."""
    gesehen: set[int] = set()
    rollen_gezeigt = False
    werk, plan = regeln.Regelwerk(), sprechplan.Sprechplan(sprecher)
    for n, daten in enumerate(quelle):
        if schreiber:
            schreiber.schreibe(daten)
        p = zustand.partie(daten, ich)
        if not rollen_gezeigt and p.spieler:
            print(ansicht.rollen_tabelle(p))
            if p.zuschauer and not p.ich:
                print("(Zuschauer ohne --ich: Sicht Blau/Rot, der Coach schweigt)")
            rollen_gezeigt = True
        if not nur_coach:
            for e in p.ereignisse:
                if e.id in gesehen:
                    continue
                gesehen.add(e.id)
                if satz := ansicht.ereignis(p, e):
                    print(satz)
        plan.neu(werk.pruefe(p))
        if a := plan.takt(p.zeit):
            print(f"{ansicht.uhr(p.zeit)}  >> {a.text}", flush=True)
        if n % alle == 0 and not nur_coach:
            print(ansicht.uebersicht(p))
        if takt:
            time.sleep(takt)
    return plan


def _live_quelle(basis: str, aus_nach: float = 10.0):
    """Liefert Schnappschuesse, solange die Partie laeuft; endet, wenn die API
    `aus_nach` Sekunden lang nicht antwortet."""
    stumm_seit = None
    while True:
        try:
            yield liveapi.alles(basis)
            stumm_seit = None
        except liveapi.KeinSpiel:
            stumm_seit = stumm_seit or time.monotonic()
            if time.monotonic() - stumm_seit > aus_nach:
                return
            time.sleep(1)


def live(args) -> None:
    sprecher = stimme.Stumm() if args.stumm else stimme.Stimme()
    print("Warte auf eine Partie (Strg+C beendet) ...")
    while True:
        if not liveapi.laeuft(args.basis):
            time.sleep(2)
            continue
        schreiber = bilder = None
        if not args.ohne_aufnahme:
            schreiber = aufzeichnung.Schreiber()
            print(f"Partie erkannt - Aufnahme: {schreiber.pfad}")
            if not args.ohne_bilder:
                bilder = aufzeichnung.Bildschreiber(schreiber)
                bilder.start()
        sprecher.sage("Coach verbunden.")
        try:
            _verfolge(_live_quelle(args.basis), args.ich, takt=1.0, sprecher=sprecher, schreiber=schreiber)
        finally:
            if bilder:
                bilder.halt()
                print(f"{bilder.anzahl} Bilder in {bilder.ordner}"
                      + (f" - letzter Fehler: {bilder.fehler}" if bilder.fehler else ""))
            if schreiber:
                schreiber.schliesse()
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
    plan = _verfolge(aufzeichnung.lies(pfad), args.ich, takt=args.takt, sprecher=sprecher,
                     alle=args.alle, nur_coach=args.nur_coach)
    print(f"\n{len(plan.gesagt)} Ansagen.")


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
    lv.add_argument("--ohne-bilder", action="store_true")
    lv.add_argument("--stumm", action="store_true")
    ab = unter.add_parser("abspielen")
    ab.add_argument("datei", nargs="?")
    ab.add_argument("--takt", type=float, default=0.0, help="Sekunden je Schnappschuss (0 = so schnell es geht)")
    ab.add_argument("--alle", type=int, default=60, help="Uebersicht alle N Schnappschuesse")
    ab.add_argument("--nur-coach", action="store_true", help="nur die Ansagen des Coaches")
    ab.add_argument("--laut", action="store_true", help="Ansagen vorlesen (wartet, bis jede gesprochen ist)")
    be = unter.add_parser("bericht")
    be.add_argument("datei", nargs="?")
    be.add_argument("--ohne-llm", action="store_true")
    unter.add_parser("status")
    lm = unter.add_parser("llm")
    lm.add_argument("frage")
    lm.add_argument("--modell", default="haiku")
    args = ap.parse_args()
    if args.befehl is None:
        args.befehl, args.ohne_aufnahme, args.ohne_bilder, args.stumm = "live", False, False, False
    {"live": live, "abspielen": abspielen, "bericht": bericht_befehl, "status": status,
     "llm": frage_llm}[args.befehl](args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
