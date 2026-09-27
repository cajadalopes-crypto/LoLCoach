"""Stille je Ansage: die 8 Stimmproben-Saetze (werkzeuge/stimmproben.py) auf dem echten Weg der Stimme
(_Neural.spreche: Teilsaetze, Strom, leerer Zwischenspeicher), die Ausgabe ohne Geraet - sie nimmt das Audio in
Echtzeit ab und hoert mit, es klingt nichts. Je Satz: Abgabe -> Ausgabe startet ("ton", das misst auch
stimmprobe.py) und -> erster hoerbarer Ton (Betrag > STILLE), Dauer gespielt, Stille am Anfang und am Ende.

    python werkzeuge/stille.py [tempo]      (Standard +25 %, wie in wissen/kern.toml)
"""
import statistics
import sys
import threading
import time
from pathlib import Path

import numpy as np

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.stdout.reconfigure(encoding="utf-8")
from lolcoach import stimme  # noqa: E402
from stimmproben import HEUTE, SAETZE, STILLE  # noqa: E402

TEMPO = sys.argv[1] if len(sys.argv) > 1 else "+25%"


class Ausgabe:
    """Wie sounddevice.OutputStream, ohne Geraet: spielt in Echtzeit ab (60 ms Puffer) und merkt sich, was wann klang."""
    channels = 2

    def __init__(self, rate: int):
        self.samplerate, self.stuecke, self.ende = rate, [], None

    def write(self, a) -> None:
        beginn = max(time.monotonic(), self.ende or 0.0)       # Unterlauf: das Stueck klingt spaeter
        self.stuecke.append((beginn, a[:, 0].copy()))
        self.ende = beginn + len(a) / self.samplerate
        time.sleep(max(0.0, self.ende - time.monotonic() - 0.06))

    def start(self) -> None:
        pass

    stop = close = abort = start


class Ersatz:
    def spreche(self, text, stopp, beim_ton=None, gilt=None) -> bool:
        ersetzt.append(text)
        return True


ersetzt: list = []
ausgaben: list = []
stimme._Neural._ausgabe = lambda self, rate: ausgaben.append(Ausgabe(rate)) or ausgaben[-1]
motor = stimme._Neural(HEUTE, TEMPO, 100, Ersatz())
motor._synthese("Los.")     # wie live: einmal vorwaermen (Module, Verbindung)
zeilen, tone, hoerbar, brutto, vorn, hinten, zeichen = [], [], [], [], [], [], 0
for satz in SAETZE:
    text = stimme.sprechbar(satz)
    ton = []
    ersetzt.clear()
    t0 = time.monotonic()
    ok = motor.spreche(text, threading.Event(), beim_ton=lambda: ton.append(time.monotonic()))
    if not ok or ersetzt or not ton:
        print(f"!! {satz}: {'Windows-Stimme' if ersetzt else 'kein Ton'}")
        continue
    gespielt = ausgaben[-1].stuecke[:-1]           # ohne die 0,1 s Nullen, die spreche fuer WASAPI anhaengt
    rate = ausgaben[-1].samplerate
    anfang, ende = gespielt[0][0], gespielt[-1][0] + len(gespielt[-1][1]) / rate
    laut = []
    for b, a in gespielt:
        i = np.flatnonzero(np.abs(a) > STILLE)
        if len(i):
            laut += [b + i[0] / rate, b + (i[-1] + 1) / rate]
    erst, letzt = min(laut), max(laut)
    tone.append(ton[0] - t0)
    hoerbar.append(erst - t0)
    brutto.append(ende - anfang)
    vorn.append(erst - anfang)
    hinten.append(ende - letzt)
    zeichen += len(text)
    zeilen.append(f"ton {tone[-1]:.2f}  hoerbar {hoerbar[-1]:.2f}  brutto {brutto[-1]:.2f}  still vorn {vorn[-1]:.2f}"
                  f" hinten {hinten[-1]:.2f}  {text}")
print(f"{HEUTE} {TEMPO}, Stille = Betrag < {STILLE}")
print("\n".join(zeilen))
if brutto:
    print(f"Median: ton {statistics.median(tone):.2f} s, hoerbar {statistics.median(hoerbar):.2f} s | Summe brutto "
          f"{sum(brutto):.1f} s, still vorn {sum(vorn):.2f} s, hinten {sum(hinten):.2f} s | "
          f"{zeichen} Zeichen, {zeichen / sum(brutto):.1f} Z/s brutto")
