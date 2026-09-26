"""python -m lolcoach [live|abspielen|bericht|review|status|llm|frage|mikrotest] ...

  live (Standard)       wartet auf eine Partie, coacht sie, schreibt sie mit (Daten + Minimap)
  abspielen [DATEI]     spielt eine Aufnahme durch denselben Code (Standard: die neueste)
  bericht [DATEI]       Post-Game-Bericht einer Aufnahme (Text)
  review [DATEI]        Review-Oberflaeche: Zeitleiste, Minimap-Wiedergabe, Lektionen, Gespraech
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
              anzeigen=(), alle: int = 5, nur_coach: bool = False, gehirn: bool = False,
              gehirn_ablage=None) -> sprechplan.Sprechplan:
    """Gemeinsamer Kern fuer Live und Aufnahme.

    `quelle` liefert (Wanduhr, Rohdaten); `sicht` hat `zwischen(bis, champions)`
    und liefert die Minimap-Sichtungen bis zu dieser Wanduhrzeit. Je Takt:
    Lagebild fortschreiben, Regeln pruefen, Sprechplan takten, Ereignisse und
    alle `alle` Takte die Uebersicht zeigen."""
    gesehen: set[int] = set()
    rollen_gezeigt = False
    werk, plan = regeln.Regelwerk(), sprechplan.Sprechplan(sprecher)
    lagebild = lage.Lagebild() if sicht else None
    stratege_ = None
    if gehirn:
        from .stratege import Stratege
        stratege_ = Stratege(plan, werk=werk)
        stratege_.gehirn.ablage = gehirn_ablage
        anzeigen = [*anzeigen, stratege_]
        for a in anzeigen:
            if hasattr(a, "gehirn_setzen"):
                a.gehirn_setzen(stratege_.gehirn)
    gemeldet: set = set()

    def sicher(name: str, f, *a):
        """Ein Fehler in einem Baustein darf die Partie nie beenden (Generalprobe 26.09.:
        ein numpy-bool im Ereignisprotokoll hat den ganzen Coach abgeschossen)."""
        try:
            return f(*a)
        except Exception as e:
            schl = (name, type(e).__name__)
            if schl not in gemeldet:
                gemeldet.add(schl)
                import traceback
                print(f"!! {name}: {type(e).__name__}: {e}\n{traceback.format_exc(limit=3)}", flush=True)
            return None

    def schritt_sicht(p, w):
        for wb, sichtungen in sicht.zwischen(w, lage.champions(p)):
            lagebild.neu(p.zeit - (w - wb), sichtungen, p)
        for t in lagebild.ereignisse(lambda wb: p.zeit - (w - wb), sicht.ereignisse(), p):
            print(f"{ansicht.uhr(t.seit)}  [{t.quelle}] {t.champion}: {t.zauber} weg bis {ansicht.uhr(t.zurueck)}")

    def schritt_ereignisse(p):
        for e in p.ereignisse:
            if e.id in gesehen:
                continue
            gesehen.add(e.id)
            if satz := ansicht.ereignis(p, e):
                print(satz)

    def schritt_coach(p):
        ansagen = werk.pruefe(p, lagebild)
        if stratege_:
            for a in [a for a in ansagen if a.situativ]:
                stratege_.veredle(a)
            ansagen = [a for a in ansagen if not a.situativ]
        plan.neu(ansagen)
        if a := plan.takt(p.zeit):
            print(f"{ansicht.uhr(p.zeit)}  >> {a.text}", flush=True)

    for n, (w, daten) in enumerate(quelle):
        if schreiber:
            sicher("Aufnahme", schreiber.schreibe, daten, w)
        p = sicher("Zustand", zustand.partie, daten, ich)
        if p is None:
            continue
        if not rollen_gezeigt and p.spieler:
            print(ansicht.rollen_tabelle(p))
            if p.zuschauer and not p.ich:
                print("(Zuschauer ohne --ich: Sicht Blau/Rot, der Coach schweigt)")
            rollen_gezeigt = True
        if sicht:
            sicher("Minimap", schritt_sicht, p, w)
        if not nur_coach:
            sicher("Ereignisse", schritt_ereignisse, p)
        sicher("Regeln", schritt_coach, p)
        for anzeige in anzeigen:
            sicher(type(anzeige).__name__, anzeige.aktualisiere, p, lagebild, plan.gesagt)
        if n % alle == 0 and not nur_coach:
            sicher("Uebersicht", lambda: print(ansicht.uebersicht(p)))
        if takt:
            time.sleep(takt)
    return plan


STIMME = "de-DE-KillianNeural"  # Partie 3: "viel zu roboterhaft"; Carlos hat Killian aus sechs Proben gewaehlt


def _stimme(name: str, warten: bool = False):
    return stimme.Stimme(warten=warten, neural=None if name == "windows" else name)


def _dashboard():
    from . import dashboard
    try:
        d = dashboard.Dashboard()
    except OSError as e:
        print(f"Dashboard nicht gestartet ({e})")
        return None
    print(f"Dashboard: {d.url}")
    return d


def _live_quelle(basis: str, nach_spielende: float = 10.0, ohne_spielende: float = 120.0):
    """Liefert (Wanduhr, Schnappschuss), solange die Partie laeuft. Schweigt die API,
    endet die Partie nach `nach_spielende` Sekunden, wenn das Spiel wirklich vorbei war
    (GameEnd), sonst erst nach `ohne_spielende` - ein Reconnect oder Haenger darf die
    Partie nicht mittendrin beenden (Bericht, Review und neue Aufnahme waeren falsch)."""
    stumm_seit = None
    vorbei = False
    while True:
        try:
            daten = liveapi.alles(basis)
            vorbei = any(e.get("EventName") == "GameEnd" for e in (daten.get("events") or {}).get("Events", []))
            yield time.time(), daten
            stumm_seit = None
        except liveapi.KeinSpiel:
            stumm_seit = stumm_seit or time.monotonic()
            if time.monotonic() - stumm_seit > (nach_spielende if vorbei else ohne_spielende):
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

    def ereignisse(self):
        return self.b.ereignisse()


def _ansagen_speichern(pfad, plan: sprechplan.Sprechplan) -> None:
    ziel = pfad.with_name(pfad.name.removesuffix(".jsonl.gz") + "_ansagen.json")
    ziel.write_text(json.dumps([asdict(a) for a in plan.gesagt], ensure_ascii=False, indent=0), encoding="utf-8")


def live(args) -> None:
    sprecher = stimme.Stumm() if args.stumm else _stimme(args.stimme)
    anzeigen = [] if args.ohne_dashboard else [d for d in [_dashboard()] if d]
    try:
        from . import review_server
        review_server.starte()
        print(f"Review-Oberflaeche: http://127.0.0.1:{review_server.PORT}")
    except OSError as e:
        print(f"Review-Oberflaeche nicht gestartet ({e})")
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
            for a in anzeigen:
                if hasattr(a, "notizen"):  # Sprachnotizen landen neben der Aufnahme
                    a.notizen = schreiber.pfad.with_name(schreiber.pfad.name.removesuffix(".jsonl.gz") + "_notizen.md")
        if not args.ohne_bilder:
            ordner = schreiber.bilderordner if schreiber else None
            beobachter = lage.Beobachter(ordner)
            beobachter.start()
            for a in anzeigen:
                if hasattr(a, "beobachter_setzen"):   # Dashboard: Minimap mit 15/s
                    a.beobachter_setzen(beobachter)
        sprecher.sage("Coach verbunden.")
        plan = None
        try:
            plan = _verfolge(_live_quelle(args.basis), args.ich, takt=1.0, sprecher=sprecher,
                             schreiber=schreiber, sicht=_LiveSicht(beobachter) if beobachter else None,
                             anzeigen=anzeigen, gehirn=not args.ohne_gehirn,
                             gehirn_ablage=schreiber.pfad.with_name(
                                 schreiber.pfad.name.removesuffix(".jsonl.gz") + "_spielakte.md") if schreiber else None)
        finally:
            if beobachter:
                beobachter.halt()
                for a in anzeigen:
                    if hasattr(a, "beobachter_setzen"):
                        a.beobachter_setzen(None)
                print(f"Minimap: {beobachter.anzahl} Bilder ausgewertet"
                      + (f" - letzter Fehler: {beobachter.fehler}" if beobachter.fehler else ""))
            if schreiber:
                schreiber.schliesse()
                if plan:
                    _ansagen_speichern(schreiber.pfad, plan)
        if schreiber:
            # im Hintergrund: Claude braucht bis zu zwei Minuten, die naechste Partie nicht
            if plan and len(plan.gesagt) >= 3:   # nur nach einer echten Partie, nicht nach einem Test
                sprecher.sage("Partie vorbei. Ich schreibe jetzt das Review, das dauert ein, zwei Minuten.")
            threading.Thread(target=_bericht_im_hintergrund, args=(schreiber.pfad, args.ich, sprecher, args.basis),
                             daemon=False).start()
        print("Partie vorbei. Bericht wird geschrieben. Warte auf die naechste ...")


def _review_ansage(review: dict) -> str:
    """Nach dem Review gesprochen: der wichtigste Punkt und der Fokus fuer die naechste Partie."""
    from .gehirn import kuerzen
    teile = ["Review ist fertig."]
    lektionen = sorted(review.get("lektionen") or [], key=lambda l: -int(l.get("wichtigkeit") or 0))
    if lektionen and lektionen[0].get("titel"):
        teile.append(f"Wichtigster Punkt: {lektionen[0]['titel'].rstrip('.')}.")
    if fokus := (review.get("naechste_partie") or "").strip():
        teile.append(f"Fokus für die nächste Partie: {kuerzen(fokus, 1)}")
    teile.append("Alles Weitere auf der Review-Seite - frag mich dort.")
    return " ".join(teile)


def _bericht_im_hintergrund(pfad, ich, sprecher=None, basis: str = liveapi.BASIS) -> None:
    try:
        ziel = bericht.schreibe(pfad, ich, mit_llm=False)  # die Claude-Analyse steckt im Review
        print(f"Bericht: {ziel}", flush=True)
    except Exception as e:  # der Bericht darf den Coach nie beenden
        print(f"Bericht fehlgeschlagen: {type(e).__name__}: {e}", flush=True)
    try:
        from . import review
        print("Review wird geschrieben (1-3 Minuten) ...", flush=True)
        r = review.erstelle(pfad)
        stamm = pfad.name.removesuffix(".jsonl.gz")
        print(f"Review fertig: http://127.0.0.1:8791/?partie={stamm}", flush=True)
        if sprecher is not None and r.get("lektionen") and not liveapi.laeuft(basis):
            sprecher.sage(_review_ansage(r))   # nicht mitten in die naechste Partie hinein
    except Exception as e:
        print(f"Review fehlgeschlagen: {type(e).__name__}: {e}", flush=True)
    try:
        if (frei := lage.bilder_aufraeumen(behalte=3)) > 0:
            print(f"Alte Minimap-Bilder aufgeraeumt: {frei:.0f} MB frei (Sichtungen bleiben)", flush=True)
    except Exception as e:
        print(f"Aufraeumen fehlgeschlagen: {type(e).__name__}: {e}", flush=True)


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
    sprecher = _stimme(args.stimme, warten=True) if args.laut else stimme.Stumm()
    sicht = None if args.ohne_bilder else lage.sicht_fuer(pfad)
    if sicht:
        print(f"Minimap: {len(sicht.bilder)} Bilder")
    plan = _verfolge(aufzeichnung.lies_mit_zeit(pfad), args.ich, takt=args.takt, sprecher=sprecher,
                     sicht=sicht,
                     anzeigen=[d for d in [_dashboard() if args.dashboard else None] if d],
                     alle=args.alle, nur_coach=args.nur_coach)
    print(f"\n{len(plan.gesagt)} Ansagen.")


def frage_an_aufnahme(args) -> None:
    """Eine Frage wie per Mikrofon, aber als Text und gegen eine Aufnahme (mit Minimap)."""
    from . import antworten
    pfad = args.datei or aufzeichnung.neueste()
    sicht, lagebild, p = lage.sicht_fuer(pfad), lage.Lagebild(), None
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
    sprecher = _stimme(args.stimme)
    erkenner = sprache.Erkenner()

    def gehoert(audio):
        t = time.monotonic()
        text = erkenner.text(audio)
        print(f"  erkannt ({time.monotonic() - t:.2f} s, {erkenner.beschreibung}): {text}", flush=True)
        sprecher.antworte(f"Verstanden: {text}" if text else "Nichts verstanden.")

    ptt = sprache.PushToTalk(args.ptt, gehoert, beim_druecken=sprecher.pausiere)
    print(f"Mikrofon: {ptt.geraet} bei {ptt.geraet_rate} Hz. Taste '{args.ptt}' halten, sprechen, loslassen. Strg+C beendet.")
    ptt.start()
    while True:
        time.sleep(1)


def review_befehl(args) -> None:
    from . import review_server
    review_server.starte()
    url = f"http://127.0.0.1:{review_server.PORT}/"
    if args.datei:
        url += f"?partie={args.datei.removesuffix('.jsonl.gz').split('/')[-1].split(chr(92))[-1]}"
    print(f"Review: {url}  (Strg+C beendet)")
    if not args.ohne_sprache:
        try:
            review_server.Sprachfragen(args.ptt, _stimme(args.stimme))
            print(f"Fragen per Sprache: Taste '{args.ptt}' halten - bezieht sich auf die Partie und den Zeitpunkt im Browser")
        except Exception as e:
            print(f"Sprachfragen aus ({type(e).__name__}: {e})")
    if not args.ohne_browser:
        import webbrowser
        webbrowser.open(url)
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
    lv.add_argument("--stimme", default=STIMME, help="neuronale Stimme (de-DE-KatjaNeural, ...) oder windows")
    lv.add_argument("--ohne-dashboard", action="store_true")
    lv.add_argument("--ohne-sprache", action="store_true", help="keine Fragen per Mikrofon")
    lv.add_argument("--ohne-gehirn", action="store_true", help="kein Briefing, keine situativen Saetze (spart Claude-Aufrufe)")
    lv.add_argument("--ptt", default="maus5", help="Push-to-Talk-Taste (maus4, maus5, f9, ...)")
    lv.add_argument("--modell-frage", default="sonnet", help="Claude-Modell fuer freie Fragen")
    ab = unter.add_parser("abspielen")
    ab.add_argument("datei", nargs="?")
    ab.add_argument("--takt", type=float, default=0.0, help="Sekunden je Schnappschuss (0 = so schnell es geht)")
    ab.add_argument("--alle", type=int, default=60, help="Uebersicht alle N Schnappschuesse")
    ab.add_argument("--nur-coach", action="store_true", help="nur die Ansagen des Coaches")
    ab.add_argument("--laut", action="store_true", help="Ansagen vorlesen (wartet, bis jede gesprochen ist)")
    ab.add_argument("--stimme", default=STIMME, help="neuronale Stimme (de-DE-KatjaNeural, ...) oder windows")
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
    mt.add_argument("--stimme", default=STIMME, help="neuronale Stimme (de-DE-KatjaNeural, ...) oder windows")
    rv = unter.add_parser("review", help="Review-Oberflaeche nach dem Spiel (Browser)")
    rv.add_argument("datei", nargs="?", help="Aufnahme, die gleich geoeffnet wird")
    rv.add_argument("--ohne-browser", action="store_true")
    rv.add_argument("--ohne-sprache", action="store_true", help="keine Fragen per Headset")
    rv.add_argument("--ptt", default="maus5")
    rv.add_argument("--stimme", default=STIMME)
    unter.add_parser("status")
    lm = unter.add_parser("llm")
    lm.add_argument("frage")
    lm.add_argument("--modell", default="haiku")
    args = ap.parse_args()
    if args.befehl is None:
        args = ap.parse_args(sys.argv[1:] + ["live"])  # ohne Befehl: live mit allen Voreinstellungen
    {"live": live, "abspielen": abspielen, "bericht": bericht_befehl, "status": status,
     "llm": frage_llm, "frage": frage_an_aufnahme, "mikrotest": mikrotest, "review": review_befehl}[args.befehl](args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
