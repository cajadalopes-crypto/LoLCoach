"""Wachhund nach Wanduhr: merkt, wenn keine Schnappschuesse mehr kommen, obwohl das Spiel noch offen ist.

Buch 0, Kapitel 4.3. Kommt von der API nichts mehr (oder haengt die Schleife), laeuft der Takt nicht - der Coach
wird nie gerufen, schweigt und merkt es nicht. Der Wachhund laeuft daneben in einem eigenen Faden:

  - nach GRENZE Sekunden ohne Schnappschuss, solange das Spielfenster da ist: einmal gesagt
    "Ich sehe das Spiel gerade nicht - ich melde mich, sobald die Daten wieder da sind.",
  - kommen wieder Daten: "Ich sehe das Spiel wieder.",
  - jede Luecke steht in `<stamm>_luecken.jsonl` neben der Aufnahme (Wanduhr und Spielzeit von/bis, Grund) -
    fuers Review: dort gibt es keine Aussage ueber Position oder Verhalten (Kapitel 11).

Ein Neustart des Coachs mitten in der Partie ist auch eine Luecke; sie traegt `neustart_eintragen` ein (Partie
102112: 15:55-24:24, Coach von Hand beendet und neu gestartet)."""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

GRENZE = 20.0          # Sekunden ohne Schnappschuss, bis der Coach es sagt
WEG = "Ich sehe das Spiel gerade nicht - ich melde mich, sobald die Daten wieder da sind."
WIEDER = "Ich sehe das Spiel wieder."


def luecken_datei(aufnahme: Path) -> Path:
    return aufnahme.with_name(aufnahme.name.removesuffix(".jsonl.gz") + "_luecken.jsonl")


def eintragen(datei: Path | None, eintrag: dict) -> None:
    if datei is None:
        return
    try:
        with open(datei, "a", encoding="utf-8") as f:
            f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
    except OSError:
        pass


def neustart_eintragen(aufnahme: Path, bis_spielzeit: float, von_spielzeit: float) -> None:
    """Die Aufnahme wird fortgesetzt: zwischen ihrer letzten Zeile und jetzt war der Coach aus."""
    if bis_spielzeit - von_spielzeit > 5:
        eintragen(luecken_datei(aufnahme), {"von_spielzeit": round(von_spielzeit, 1),
                                            "bis_spielzeit": round(bis_spielzeit, 1), "bis_wand": round(time.time(), 1),
                                            "grund": "Coach war aus (Neustart, Aufnahme fortgesetzt)"})


def spiel_offen() -> bool:
    """Das Spielfenster existiert (auch minimiert) - dann ist Stille ein Fehler, keine Pause."""
    try:
        import win32gui
        from .bild import FENSTERTITEL
        return bool(win32gui.FindWindow(None, FENSTERTITEL))
    except Exception:
        return False


class Wachhund(threading.Thread):
    def __init__(self, sprecher, datei: Path | None, grenze: float = GRENZE, spiel_da=spiel_offen,
                 uhr=time.time, takt: float = 1.0):
        super().__init__(daemon=True)
        self.sprecher, self.datei, self.grenze, self.spiel_da, self.uhr, self.takt = \
            sprecher, datei, grenze, spiel_da, uhr, takt
        self._zuletzt: tuple[float, float] | None = None     # (Wanduhr, Spielzeit) des letzten Schnappschusses
        self.luecke: tuple[float, float] | None = None       # offene Luecke: (Wanduhr, Spielzeit) ihres Beginns
        self._halt = threading.Event()
        self._schloss = threading.Lock()

    def fuettern(self, wand: float, spielzeit: float) -> None:
        with self._schloss:
            offen, self.luecke = self.luecke, None
            self._zuletzt = (wand, spielzeit)
        if offen is not None:
            eintragen(self.datei, {"von_wand": round(offen[0], 1), "von_spielzeit": round(offen[1], 1),
                                   "bis_wand": round(wand, 1), "bis_spielzeit": round(spielzeit, 1),
                                   "grund": "keine Schnappschuesse"})
            self._sagen(WIEDER)

    def _sagen(self, text: str) -> None:
        try:
            self.sprecher.sage(text, dringend=True)
        except Exception:
            pass

    def run(self) -> None:
        while not self._halt.wait(self.takt):
            with self._schloss:
                z, offen = self._zuletzt, self.luecke
            if z is None or offen is not None or self.uhr() - z[0] < self.grenze:
                continue
            if not self.spiel_da():
                continue            # Spiel zu: das ist das Ende der Partie, keine Luecke
            with self._schloss:
                self.luecke = z
            self._sagen(WEG)

    def halt(self) -> None:
        """Partie vorbei: eine offene Luecke wird ohne Ende eingetragen."""
        self._halt.set()
        with self._schloss:
            offen, self.luecke = self.luecke, None
        if offen is not None:
            eintragen(self.datei, {"von_wand": round(offen[0], 1), "von_spielzeit": round(offen[1], 1),
                                   "bis_wand": None, "bis_spielzeit": None,
                                   "grund": "keine Schnappschuesse bis zum Ende"})
