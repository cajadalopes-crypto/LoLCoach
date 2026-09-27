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

from . import (ansicht, aufzeichnung, bericht, komponist, lage, liveapi, llm, profil, regeln, sprechplan, stimme,
               wachhund, zustand)


def _verfolge(quelle, ich: str | None, takt: float, sprecher, schreiber=None, sicht=None,
              anzeigen=(), alle: int = 5, nur_coach: bool = False, gehirn: bool = False,
              gehirn_ablage=None, kern_ablage=None, kern_stellung: str = "neu",
              fokus: str | None = None) -> sprechplan.Sprechplan:
    """Gemeinsamer Kern fuer Live und Aufnahme.

    `quelle` liefert (Wanduhr, Rohdaten); `sicht` hat `zwischen(bis, champions)`
    und liefert die Minimap-Sichtungen bis zu dieser Wanduhrzeit. Je Takt:
    Lagebild fortschreiben, Regeln pruefen, Sprechplan takten, Ereignisse und
    alle `alle` Takte die Uebersicht zeigen."""
    gesehen: set[int] = set()
    rollen_gezeigt = False
    werk, plan = regeln.Regelwerk(), sprechplan.Sprechplan(sprecher)
    # Buch 0: der Entscheidungskern - ab Schritt 2 in jeder Stellung von --kern (Modus, Sperre, _kern.jsonl); ab
    # Schritt 3 spricht er mit --kern neu (Default) in LANE, BASIS und TOT selbst
    from .kern import Kern
    kern_ = Kern(kern_ablage, stellung=kern_stellung)
    kern_.fokus = fokus
    werk.kern = plan.kern = kern_
    kern_.transport = plan
    technik: list = []            # TECHNIK-Ansagen (Kapitel 9.1): Minimap nicht erkannt - durch den Sprechplan
    war_tot = [False]
    lagebild = lage.Lagebild() if sicht else None
    stratege_ = None
    if gehirn:
        from .stratege import Stratege
        stratege_ = Stratege(plan, werk=werk)
        stratege_.gehirn.ablage = gehirn_ablage
        stratege_.beobachter = getattr(sicht, "b", None)   # live: der Spielbildschirm fuer Claude
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
        bb = getattr(sicht, "b", None)
        if bb is not None and p.ich:
            bb.ich = (p.ich.champion_id, p.ich.team)      # live: der Beobachter ergaenzt das eigene Icon
        for wb, sichtungen in sicht.zwischen(w, lage.champions(p)):
            lagebild.neu(p.zeit - (w - wb), sichtungen, p)
        for t in lagebild.ereignisse(lambda wb: p.zeit - (w - wb), sicht.ereignisse(), p):
            print(f"{ansicht.uhr(t.seit)}  [{t.quelle}] {t.champion}: {t.zauber} weg bis {ansicht.uhr(t.zurueck)}")
        if bb is not None:
            minimap_gesund(p)

    minimap_stumm = [False]
    minimap_ab = [None]

    def minimap_gesund(p):
        """Live: Verbuendete sind auf der Minimap immer zu sehen. Sieht der Coach 30 s lang niemanden aus deinem Team,
        obwohl du lebst, liest er die Minimap nicht (Minimap-Groesse in den Einstellungen, verdeckt, Fenster) - dann
        rechnet alles ohne Karte und faellt auf feste Saetze zurueck. Das sagt er einmal, statt still weiterzumachen.
        Die 30 s zaehlen fruehestens ab seinem Start: vorher warnte er bei jedem Start mitten in der Partie sofort
        (noch kein Bild = "niemand gesehen") und sagte eine Sekunde spaeter "Die Minimap ist wieder da"."""
        if p.zeit < 90 or not p.ich or p.ich.tot:
            return
        if minimap_ab[0] is None:
            minimap_ab[0] = p.zeit
        zuletzt = max((g[0] for s in p.team(p.mein_team) if (g := lagebild.gesehen(s))), default=None)
        blind = p.zeit - max(zuletzt if zuletzt is not None else -1e9, minimap_ab[0]) > 30
        if blind and not minimap_stumm[0]:
            minimap_stumm[0] = True
            print("!! Minimap: seit 30 s niemand aus deinem Team erkannt - Minimap-Groesse/Fenster pruefen", flush=True)
            technik.append(regeln.Ansage("Ich erkenne auf der Minimap gerade niemanden aus deinem Team. Ist die Minimap "
                                         "verdeckt oder anders groß als sonst? Bis dahin rechne ich ohne Karte.",
                                         regeln.SOFORT, "kern:technik", zeit=p.zeit, gueltig=20, sperre=0))
        elif not blind and minimap_stumm[0]:
            minimap_stumm[0] = False
            print("Minimap wieder erkannt.", flush=True)
            technik.append(regeln.Ansage("Die Minimap ist wieder da.", regeln.SOFORT, "kern:technik", zeit=p.zeit,
                                         gueltig=20, sperre=0))

    def schritt_ereignisse(p):
        for e in p.ereignisse:
            if e.id in gesehen:
                continue
            gesehen.add(e.id)
            if satz := ansicht.ereignis(p, e):
                print(satz)

    def schritt_coach(p):
        ansagen = werk.pruefe(p, lagebild)
        ansagen += kern_.takt(p, lagebild)          # der Kern spricht in seinen Modi (kern.KERN_MODI)
        ansagen += technik
        technik.clear()
        tot = bool(p.ich and p.ich.tot)
        if tot and not war_tot[0] and getattr(sicht, "b", None) is not None:
            sicht.b.puffer_sichern()   # die Sekunden vor dem Tod als Bilder fuers Review
        war_tot[0] = tot
        if stratege_:
            for a in [a for a in ansagen if a.situativ]:
                stratege_.veredle(a)
            ansagen = [a for a in ansagen if not a.situativ]
        plan.neu(ansagen)
        if a := plan.takt(p.zeit, ich_tot=bool(p.ich and p.ich.tot)):
            print(f"{ansicht.uhr(p.zeit)}  >> {a.text}", flush=True)

    for n, (w, daten) in enumerate(quelle):
        if schreiber:
            sicher("Aufnahme", schreiber.schreibe, daten, w)
        p = sicher("Zustand", zustand.partie, daten, ich)
        if p is None:
            continue
        if not rollen_gezeigt and p.spieler:
            if p.ich and hasattr(sprecher, "vorwaermen"):
                sicher("Vorwaermen", lambda: sprecher.vorwaermen(komponist.anfaenge(p)))
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
        if schreiber and n % 20 == 0:
            # laufend sichern: wird das Fenster geschlossen, bleibt, was der Coach gesagt hat (Partie 4/5)
            sicher("Ansagen", _ansagen_speichern, schreiber.pfad, plan)
        if takt:
            # live weckt der Beobachter den Kern bei einem Sprung oder einem Gegner neben dir sofort (lage.Beobachter)
            wecker = getattr(getattr(sicht, "b", None), "wecker", None)
            if wecker is None:
                time.sleep(takt)
            elif wecker.wait(takt):
                wecker.clear()
    kern_.schliessen()
    return plan


LIVE_TAKT = 0.25   # Sekunden zwischen zwei Abfragen der Live-API im Spiel


def _fokus() -> str | None:
    """Fokus des Tages aus dem letzten Review (Buch 3, 3.3: ist es das Kontroll-Auge, steht es im Kauf-Satz zuerst)."""
    try:
        return profil.fokus()
    except Exception:
        return None

def _stimm_cfg() -> dict:
    """[stimme] aus wissen/kern.toml (Auftrag 002, S2): Name und Tempo - Carlos waehlt die Stimme aus den Proben."""
    try:
        from . import wissen
        return wissen.lade("kern").get("stimme", {})
    except Exception:
        return {}


# Partie 3: "viel zu roboterhaft"; Carlos hat Killian aus sechs Proben gewaehlt - seit Auftrag 002 in der toml
STIMME = _stimm_cfg().get("name", "de-DE-KillianNeural")
TEMPO = _stimm_cfg().get("tempo", "+25%")


def _stimme(name: str, warten: bool = False, tempo: str | None = None):
    return stimme.Stimme(warten=warten, neural=None if name == "windows" else name, tempo=tempo or TEMPO)


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
    spieler, uhr = None, None
    while True:
        try:
            daten = liveapi.alles(basis)
            vorbei = any(e.get("EventName") == "GameEnd" for e in (daten.get("events") or {}).get("Events", []))
            # Eine andere Partie ist keine Fortsetzung: Live 26.09., 23:05-23:06 (Practice Tool neu gestartet) lief
            # die API nur kurz nicht - der Coach behielt Briefing, Rolle ("du bist Jungler", Smite aus der ersten
            # Partie) und Aufnahme der alten. Andere Spieler oder eine zurueckgesprungene Spieluhr = Ende - ein anderer
            # Champion nicht: Viego heisst in der API wie der, den er uebernommen hat (aufzeichnung._spieler).
            jetzt_spieler = aufzeichnung._spieler(daten)
            jetzt_uhr = float((daten.get("gameData") or {}).get("gameTime") or 0.0)
            if jetzt_spieler:
                if spieler is not None and (jetzt_spieler != spieler or (uhr is not None and jetzt_uhr < uhr - 30)):
                    print("Neue Partie erkannt (andere Spieler oder Spieluhr von vorn) - die alte endet hier.",
                          flush=True)
                    return
                spieler, uhr = jetzt_spieler, jetzt_uhr
            yield time.time(), daten
            stumm_seit = None
        except liveapi.KeinSpiel:
            stumm_seit = stumm_seit or time.monotonic()
            if time.monotonic() - stumm_seit > (nach_spielende if vorbei else ohne_spielende):
                return
            time.sleep(1)


def _gefuettert(quelle, hund):
    """Jeder Schnappschuss fuettert den Wachhund (wachhund.py) - bleiben sie aus, merkt er es nach Wanduhr."""
    for w, d in quelle:
        hund.fuettern(w, float((d.get("gameData") or {}).get("gameTime") or 0.0))
        yield w, d


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


_ANSAGEN_VORHER: dict = {}   # fortgesetzte Aufnahme -> Ansagen vor dem Neustart


def _ansagen_speichern(pfad, plan: sprechplan.Sprechplan) -> None:
    ziel = pfad.with_name(pfad.name.removesuffix(".jsonl.gz") + "_ansagen.json")
    alle = _ANSAGEN_VORHER.get(pfad, []) + [{k: v for k, v in asdict(a).items() if k != "pruefe"}
                                            for a in plan.gesagt]
    ziel.write_text(json.dumps(alle, ensure_ascii=False, indent=0), encoding="utf-8")


_SPERRE = None   # haelt den Sperr-Port, solange der Coach laeuft


def _nur_einmal(port: int = 8789) -> bool:
    """Genau ein Coach zur Zeit: zwei sprechen doppelt, schreiben in dieselbe Aufnahme und nur einer
    bekommt das Dashboard (26.09., 16:42 - ein alter Coach lief unbemerkt weiter)."""
    import socket
    global _SPERRE
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
        s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    try:
        s.bind(("127.0.0.1", port))
    except OSError:
        s.close()
        return False
    _SPERRE = s
    return True


_ABSTURZ = None   # offene Datei fuer faulthandler


def _absturz_mitschreiben() -> None:
    """Stirbt der Prozess im nativen Code (Zugriffsverletzung), gibt es keinen Traceback, und das Fenster ist zu:
    die vier Abstuerze vom 26./27.09.2026 liessen nur einen Eintrag in der Windows-Ereignisanzeige zurueck. Mit
    faulthandler steht der Python-Stapel aller Faeden in aufnahmen/absturz.log."""
    import faulthandler
    global _ABSTURZ
    try:
        aufzeichnung.ORDNER.mkdir(parents=True, exist_ok=True)
        _ABSTURZ = open(aufzeichnung.ORDNER / "absturz.log", "a", encoding="utf-8")
        _ABSTURZ.write(f"--- Coach gestartet {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        _ABSTURZ.flush()
        faulthandler.enable(_ABSTURZ, all_threads=True)
    except OSError:
        pass


def live(args) -> None:
    _absturz_mitschreiben()
    if not _nur_einmal():
        print("Der Coach laeuft schon in einem anderen Fenster (Dashboard http://127.0.0.1:8790).\n"
              "Dieses Fenster wird nicht gebraucht - es schliesst sich in 10 Sekunden.")
        time.sleep(10)
        return
    sprecher = stimme.Stumm() if args.stumm else _stimme(args.stimme, tempo=args.tempo)
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
    threading.Thread(target=_reviews_nachholen, daemon=True).start()
    for a in anzeigen:
        a.partie_vorbei = True   # noch keine Partie: die Sprechtaste redet uebers Review
    print("Warte auf eine Partie (Strg+C beendet) ...")
    while True:
        if not liveapi.laeuft(args.basis):
            time.sleep(2)
            continue
        schreiber = beobachter = None
        for a in anzeigen:
            a.partie_vorbei = False   # Sprechtaste wieder fuer die Partie
        if not args.ohne_aufnahme:
            try:
                fort = aufzeichnung.fortsetzbar(liveapi.alles(args.basis))
            except Exception:
                fort = None
            schreiber = aufzeichnung.Schreiber(fortsetzen=fort)
            if schreiber.fortgesetzt:       # gesperrte Datei: der Schreiber hat neu angefangen
                # dieselbe Partie wie die juengste Aufnahme (Neustart, Reconnect): weiterschreiben; das
                # Review des Bruchstuecks ist veraltet und entsteht nach dem Spiel neu
                stamm = fort.name.removesuffix(".jsonl.gz")
                for rest in ("_review.json", "_verlauf.json", "_bericht.md"):
                    fort.with_name(stamm + rest).unlink(missing_ok=True)
                datei = fort.with_name(stamm + "_ansagen.json")
                try:
                    _ANSAGEN_VORHER[fort] = json.loads(datei.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    _ANSAGEN_VORHER[fort] = []
                print(f"Partie erkannt - dieselbe wie eben, Aufnahme wird fortgesetzt: {schreiber.pfad}")
                try:   # der Coach war aus: eine Luecke in der Aufnahme (Buch 0, 4.3; Partie 102112, 15:55-24:24)
                    wachhund.neustart_eintragen(fort, float((liveapi.alles(args.basis).get("gameData") or {})
                                                            .get("gameTime") or 0.0), _spieldauer(fort))
                except Exception:
                    pass
            else:
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
        hund = wachhund.Wachhund(sprecher, wachhund.luecken_datei(schreiber.pfad) if schreiber else None)
        hund.start()
        try:
            # 4 Takte je Sekunde: Regeln + Bewertung kosten 0,4 ms (Camille-Partie gemessen) - mit 1 s Takt
            # kam "Vi kommt auf dich zu" bis zu einer Sekunde spaet (Carlos: "moeglichst Richtung Echtzeit")
            plan = _verfolge(_gefuettert(_live_quelle(args.basis), hund), args.ich, takt=LIVE_TAKT, sprecher=sprecher,
                             schreiber=schreiber, sicht=_LiveSicht(beobachter) if beobachter else None,
                             anzeigen=anzeigen, gehirn=not args.ohne_gehirn, alle=20,
                             gehirn_ablage=schreiber.pfad.with_name(
                                 schreiber.pfad.name.removesuffix(".jsonl.gz") + "_spielakte.md") if schreiber else None,
                             kern_ablage=schreiber.pfad.with_name(
                                 schreiber.pfad.name.removesuffix(".jsonl.gz") + "_kern.jsonl") if schreiber else None,
                             kern_stellung=args.kern, fokus=_fokus())
        finally:
            hund.halt()
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
            # nur nach einer echten Partie, nicht nach einem Test oder einem Wechsel nach Sekunden (Practice Tool)
            if plan and len(plan.gesagt) >= 3 and plan.gesagt[-1].zeit >= profil.KURZ:
                sprecher.sage("Partie vorbei. Ich schreibe jetzt das Review, das dauert ein, zwei Minuten.")
            threading.Thread(target=_bericht_im_hintergrund, args=(schreiber.pfad, args.ich, sprecher, args.basis),
                             daemon=False).start()
        for a in anzeigen:
            a.partie_vorbei = True    # Sprechtaste geht jetzt ans Review (Review-Seite, gewaehlte Partie)
        print("Partie vorbei. Bericht wird geschrieben. Warte auf die naechste ...")


def _reviews_nachholen(hoechstens: int = 3) -> None:
    """Partien ohne Review (Fenster waehrend des Reviews geschlossen - Partie 4 und 5) beim Start
    nachholen: die juengsten `hoechstens`, nur echte Partien ab 5 Minuten, still im Hintergrund."""
    try:
        from . import profil, review
        jetzt = time.time()
        offen = [k for k in profil.partien(aufzeichnung.ORDNER) if k.dauer >= profil.KURZ
                 and not review.pfade(aufzeichnung.ORDNER / f"{k.stamm}.jsonl.gz")["review"].exists()
                 # nicht, was vor Kurzem noch lief: die Partie kann gleich fortgesetzt werden (Neustart)
                 and jetzt - (aufzeichnung.ORDNER / f"{k.stamm}.jsonl.gz").stat().st_mtime > 900][:hoechstens]
        for k in reversed(offen):   # aelteste zuerst: jedes Review sieht die frueheren
            print(f"Review wird nachgeholt: {k.stamm} ({k.champion} gegen {k.gegner}) ...", flush=True)
            review.erstelle(aufzeichnung.ORDNER / f"{k.stamm}.jsonl.gz")
            print(f"Review fertig: http://127.0.0.1:8791/?partie={k.stamm}", flush=True)
    except Exception as e:  # darf den Coach nie stoeren
        print(f"Review nachholen fehlgeschlagen: {type(e).__name__}: {e}", flush=True)


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


def _spieldauer(pfad) -> float:
    """Spielzeit der letzten Zeile einer Aufnahme (Sekunden)."""
    for zeile in reversed(aufzeichnung.gz_text(pfad).splitlines()):
        try:
            return float((json.loads(zeile)["d"].get("gameData") or {}).get("gameTime") or 0.0)
        except (ValueError, KeyError, AttributeError):
            continue
    return 0.0


def _bericht_im_hintergrund(pfad, ich, sprecher=None, basis: str = liveapi.BASIS) -> None:
    try:
        ziel = bericht.schreibe(pfad, ich, mit_llm=False)  # die Claude-Analyse steckt im Review
        print(f"Bericht: {ziel}", flush=True)
    except Exception as e:  # der Bericht darf den Coach nie beenden
        print(f"Bericht fehlgeschlagen: {type(e).__name__}: {e}", flush=True)
    try:
        from . import review
        if _spieldauer(pfad) < profil.KURZ:
            print("Kurze Partie (Test, Wechsel, Remake) - kein Review.", flush=True)
            return
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
    sprecher = _stimme(args.stimme, warten=True, tempo=args.tempo) if args.laut else stimme.Stumm()
    sicht = None if args.ohne_bilder else lage.sicht_fuer(pfad)
    if sicht:
        print(f"Minimap: {len(sicht.bilder)} Bilder")
    plan = _verfolge(aufzeichnung.lies_mit_zeit(pfad), args.ich, takt=args.takt, sprecher=sprecher,
                     sicht=sicht,
                     anzeigen=[d for d in [_dashboard() if args.dashboard else None] if d],
                     alle=args.alle, nur_coach=args.nur_coach, kern_stellung=args.kern)
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

    ptt = sprache.PushToTalk(args.ptt, gehoert, beim_druecken=sprecher.pausiere, bei_abbruch=sprecher.freigeben,
                              beim_loslassen=getattr(sprecher, "taste_los", None))
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
    lv.add_argument("--tempo", default=TEMPO, help="Sprechtempo der Stimme, z. B. +50%% (Standard aus wissen/kern.toml)")
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
    ab.add_argument("--tempo", default=TEMPO, help="Sprechtempo der Stimme, z. B. +50%%")
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
    for sub in (lv, ab):   # Entscheidungskern (buecher/00_entscheidungskern.md, Kapitel 3)
        sub.add_argument("--kern", choices=("alt", "schatten", "neu"), default="neu",
                         help="neu (Default, Schritt 3) = der Kern spricht in LANE, BASIS, TOT, die alten Regeln "
                              "dort nicht; schatten = das Regelwerk spricht, der Kern rechnet mit und schreibt "
                              "'wuerde sagen' in <stamm>_kern.jsonl; alt = nur Modus und Sperre (Schritt 2)")
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
