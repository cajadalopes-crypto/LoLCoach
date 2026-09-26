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
import time

from . import ansicht, aufzeichnung, liveapi, llm, zustand


def _verfolge(quelle, ich: str | None, takt: float, schreiber=None, alle: int = 5) -> None:
    """Gemeinsamer Kern fuer Live und Aufnahme: neue Ereignisse als Satz,
    alle `alle` Takte die Uebersicht."""
    gesehen: set[int] = set()
    rollen_gezeigt = False
    for n, daten in enumerate(quelle):
        if schreiber:
            schreiber.schreibe(daten)
        p = zustand.partie(daten, ich)
        if not rollen_gezeigt and p.spieler:
            print(ansicht.rollen_tabelle(p))
            if p.zuschauer and not p.ich:
                print("(Zuschauer ohne --ich: Sicht Blau/Rot)")
            rollen_gezeigt = True
        for e in p.ereignisse:
            if e.id in gesehen:
                continue
            gesehen.add(e.id)
            if satz := ansicht.ereignis(p, e):
                print(satz)
        if n % alle == 0:
            print(ansicht.uebersicht(p))
        if takt:
            time.sleep(takt)


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
    print("Warte auf eine Partie (Strg+C beendet) ...")
    while True:
        if not liveapi.laeuft(args.basis):
            time.sleep(2)
            continue
        schreiber = None if args.ohne_aufnahme else aufzeichnung.Schreiber()
        if schreiber:
            print(f"Partie erkannt - Aufnahme: {schreiber.pfad}")
        try:
            _verfolge(_live_quelle(args.basis), args.ich, takt=1.0, schreiber=schreiber)
        finally:
            if schreiber:
                schreiber.schliesse()
        print("Partie vorbei. Warte auf die naechste ...")


def abspielen(args) -> None:
    pfad = args.datei or aufzeichnung.neueste()
    if not pfad:
        sys.exit("Keine Aufnahme gefunden.")
    print(f"Aufnahme: {pfad}")
    _verfolge(aufzeichnung.lies(pfad), args.ich, takt=args.takt, alle=args.alle)


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
    ab = unter.add_parser("abspielen")
    ab.add_argument("datei", nargs="?")
    ab.add_argument("--takt", type=float, default=0.0, help="Sekunden je Schnappschuss (0 = so schnell es geht)")
    ab.add_argument("--alle", type=int, default=60, help="Uebersicht alle N Schnappschuesse")
    unter.add_parser("status")
    lm = unter.add_parser("llm")
    lm.add_argument("frage")
    lm.add_argument("--modell", default="haiku")
    args = ap.parse_args()
    if args.befehl is None:
        args.befehl, args.ohne_aufnahme = "live", False
    {"live": live, "abspielen": abspielen, "status": status, "llm": frage_llm}[args.befehl](args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
