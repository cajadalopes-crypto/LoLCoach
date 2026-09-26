"""Stimmprobe: der Coach-Weg mit der echten neuronalen Stimme, stumm (Lautstaerke 0) - eine Aufnahme ab `ab` Minuten
fuer `minuten` Minuten in Echtzeit (davor im Schnellvorlauf). Misst je Ansage: Abgabe -> erster Ton, wie lange sie in
der Schlange der Stimme lag, wie lange die Synthese brauchte (und ob sie vorbereitet war), Ende/Abbruch/Widerruf;
meldet Fehler aus den Threads. Fuer Umbauten an stimme.py / sprechplan.py, ohne Fenster und ohne Spiel.

Gemessen 27.09. (Partie 212105 ab 8:00): erster Ton Median 0,29 s, Synthese-Stueck 0,25 s, keine Thread-Fehler.

    python werkzeuge/stimmprobe.py 2026-09-26_212105 8 2
"""
import contextlib
import io
import statistics
import sys
import threading
import time
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.stdout.reconfigure(encoding="utf-8")
from lolcoach import __main__ as m, aufzeichnung, lage, sprechplan, stimme  # noqa: E402

fehler = []
threading.excepthook = lambda a: fehler.append(f"{a.exc_type.__name__}: {a.exc_value}")
pfad = WURZEL / "aufnahmen" / f"{sys.argv[1] if len(sys.argv) > 1 else '2026-09-26_212105'}.jsonl.gz"
AB = 60.0 * float(sys.argv[2]) if len(sys.argv) > 2 else 480.0
BIS = AB + 60.0 * (float(sys.argv[3]) if len(sys.argv) > 3 else 2.0)


def quelle():
    vorher = None
    for w, d in aufzeichnung.lies_mit_zeit(pfad):
        t = (d.get("gameData") or {}).get("gameTime")
        if t is None:
            yield w, d
            continue
        if t > BIS:
            return
        if t >= AB and vorher is not None and vorher >= AB:
            time.sleep(max(0.0, min(2.0, t - vorher)))
        vorher = t
        yield w, d


st = stimme.Stimme(lautstaerke=0, neural="de-DE-KillianNeural")
messung = []
alt_melder = sprechplan.Sprechplan._melder


def melder(self, a, ab):
    innen = alt_melder(self, a, ab)
    eintrag = {"text": a.text, "ab": ab}
    messung.append(eintrag)

    def melde(art, jetzt):
        eintrag[art] = jetzt
        innen(art, jetzt)
    return melde


sprechplan.Sprechplan._melder = melder

# je Synthese: Start -> erstes Stueck, und Fehler
synth = []
alt_init = stimme._Strom.__init__


def init(self, text, *a, **k):
    eintrag = {"text": text, "start": time.monotonic()}
    synth.append(eintrag)
    alt_dazu = self._dazu

    def dazu(dek, daten, e=eintrag):
        e.setdefault("erst", time.monotonic())
        alt_dazu(dek, daten)
    self._dazu = dazu
    alt_init(self, text, *a, **k)
    self._eintrag = eintrag


stimme._Strom.__init__ = init
# je gesprochene Ansage: wann nahm die Stimme sie aus der Schlange (Beginn von spreche)
spricht = []
alt_spreche = stimme._Neural.spreche


def spreche(self, text, *a, **k):
    spricht.append((time.monotonic(), text))
    return alt_spreche(self, text, *a, **k)


stimme._Neural.spreche = spreche
with contextlib.redirect_stdout(io.StringIO()) as aus:
    plan = m._verfolge(quelle(), None, takt=0, sprecher=st, sicht=lage.sicht_fuer(pfad), alle=10**9, nur_coach=True)
time.sleep(6)
spaet = [e for e in messung if e["ab"] >= 0]
tone = [e["ton"] - e["ab"] for e in spaet if "ton" in e]
for e in spaet:
    art = next((k for k in ("ende", "abgebrochen", "widerrufen", "verworfen") if k in e), "?")
    ton = f"{e['ton'] - e['ab']:.2f}" if "ton" in e else "  - "
    start = next((t for t, x in spricht if t >= e["ab"] - 0.01 and x == stimme.sprechbar(e["text"])), None)
    s = next((x for x in synth if x["start"] >= e["ab"] - 5 and stimme.sprechbar(e["text"]).startswith(x["text"])), None)
    zer = (f"Schlange {start - e['ab']:.2f}" if start else "Schlange ?") + (
        f" Synthese {s['erst'] - s['start']:.2f} (vor Abgabe {e['ab'] - s['start']:.2f})" if s and "erst" in s else " Synthese ?")
    print(f"ton {ton}  {art:11} {zer:48} {e['text'][:70]}")
erst = [x["erst"] - x["start"] for x in synth if "erst" in x]
print(f"{len(synth)} Synthesen, {len(erst)} mit Audio: erstes Stueck Median {statistics.median(erst):.2f} s, "
      f"90 % {sorted(erst)[int(len(erst) * 0.9)]:.2f} s")
if tone:
    print(f"{len(tone)} mit Ton: Median {statistics.median(tone):.2f} s, max {max(tone):.2f} s")
print("Thread-Fehler:", fehler or "keine")
print("Ausgabe mit Fehlern:", [z for z in aus.getvalue().splitlines() if "!!" in z or "Fehler" in z][:10])
