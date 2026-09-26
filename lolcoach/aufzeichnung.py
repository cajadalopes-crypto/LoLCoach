"""Jede Partie wird Sekunde fuer Sekunde roh mitgeschrieben.

`aufnahmen/<Datum>_<Uhrzeit>.jsonl.gz`, eine Zeile je Abfrage:
{"w": Wanduhr, "d": Rohdaten der API}. Roh, weil sich erst an echten
Aufnahmen zeigt, was die API wirklich liefert - und weil jede Aufnahme
spaeter durch denselben Code laeuft wie das Live-Spiel.
"""
from __future__ import annotations

import gzip
import json
import threading
import time
from pathlib import Path
from typing import Iterator

ORDNER = Path(__file__).resolve().parent.parent / "aufnahmen"


class Schreiber:
    def __init__(self, ordner: Path = ORDNER):
        ordner.mkdir(parents=True, exist_ok=True)
        self.pfad = ordner / time.strftime("%Y-%m-%d_%H%M%S.jsonl.gz")
        self._f = gzip.open(self.pfad, "at", encoding="utf-8")
        self._offen = 0

    def schreibe(self, daten: dict) -> None:
        self._f.write(json.dumps({"w": round(time.time(), 2), "d": daten}, ensure_ascii=False) + "\n")
        self._offen += 1
        if self._offen >= 15:  # alle ~15 s auf die Platte, falls etwas abstuerzt
            self._f.flush()
            self._offen = 0

    def schliesse(self) -> None:
        self._f.close()


class Bildschreiber(threading.Thread):
    """Fotografiert neben der API-Aufnahme die Minimap-Ecke, einmal je
    `takt` Sekunden, nach `<aufnahme>_bilder/<Wanduhr in ms>.jpg`. Die Wanduhr
    ist dieselbe wie `w` in der API-Aufnahme - darueber passen Bild und Daten
    zusammen."""

    def __init__(self, schreiber: Schreiber, takt: float = 1.0):
        super().__init__(daemon=True)
        self.ordner = schreiber.pfad.with_name(schreiber.pfad.name.removesuffix(".jsonl.gz") + "_bilder")
        self.ordner.mkdir(exist_ok=True)
        self.takt = takt
        self.anzahl = 0
        self.fehler: str | None = None
        self._halt = threading.Event()

    def run(self) -> None:
        from . import bild
        while not self._halt.is_set():
            start = time.time()
            try:
                if (bildchen := bild.minimap_ecke()) is not None:
                    bildchen.save(self.ordner / f"{int(start * 1000)}.jpg", quality=85)
                    self.anzahl += 1
            except Exception as e:  # ein Bild weniger, nie die Partie verlieren
                self.fehler = f"{type(e).__name__}: {e}"
            self._halt.wait(max(0.0, self.takt - (time.time() - start)))

    def halt(self) -> None:
        self._halt.set()
        self.join(timeout=3)


def lies(pfad: str | Path) -> Iterator[dict]:
    """Rohdaten der Aufnahme, Zeile fuer Zeile. Eine abgebrochene letzte
    Zeile (Absturz mitten im Schreiben) wird still uebergangen."""
    with gzip.open(pfad, "rt", encoding="utf-8") as f:
        try:
            for zeile in f:
                try:
                    yield json.loads(zeile)["d"]
                except (json.JSONDecodeError, KeyError):
                    continue
        except EOFError:
            return


def neueste() -> Path | None:
    dateien = sorted(ORDNER.glob("*.jsonl.gz"))
    return dateien[-1] if dateien else None
