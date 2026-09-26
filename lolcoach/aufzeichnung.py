"""Jede Partie wird Sekunde fuer Sekunde roh mitgeschrieben.

`aufnahmen/<Datum>_<Uhrzeit>.jsonl.gz`, eine Zeile je Abfrage:
{"w": Wanduhr, "d": Rohdaten der API}. Roh, weil sich erst an echten
Aufnahmen zeigt, was die API wirklich liefert - und weil jede Aufnahme
spaeter durch denselben Code laeuft wie das Live-Spiel.
"""
from __future__ import annotations

import gzip
import json
import time
from pathlib import Path
from typing import Iterator

import os

# LOLCOACH_AUFNAHMEN: anderer Ordner, z. B. fuer die Generalprobe (werkzeuge/generalprobe.py)
ORDNER = Path(os.environ.get("LOLCOACH_AUFNAHMEN") or Path(__file__).resolve().parent.parent / "aufnahmen")


class Schreiber:
    def __init__(self, ordner: Path = ORDNER):
        ordner.mkdir(parents=True, exist_ok=True)
        self.pfad = ordner / time.strftime("%Y-%m-%d_%H%M%S.jsonl.gz")
        self._f = gzip.open(self.pfad, "at", encoding="utf-8")
        self._offen = 0

    @property
    def bilderordner(self) -> Path:
        """Hier legt der Beobachter die Minimap-Bilder ab (Dateiname = Wanduhr in ms)."""
        return self.pfad.with_name(self.pfad.name.removesuffix(".jsonl.gz") + "_bilder")

    def schreibe(self, daten: dict, w: float | None = None) -> None:
        w = time.time() if w is None else w
        self._f.write(json.dumps({"w": round(w, 3), "d": daten}, ensure_ascii=False) + "\n")
        self._offen += 1
        if self._offen >= 15:  # alle ~15 s auf die Platte, falls etwas abstuerzt
            self._f.flush()
            self._offen = 0

    def schliesse(self) -> None:
        self._f.close()


def lies(pfad: str | Path) -> Iterator[dict]:
    """Rohdaten der Aufnahme, Zeile fuer Zeile. Eine abgebrochene letzte
    Zeile (Absturz mitten im Schreiben) wird still uebergangen."""
    for _, d in lies_mit_zeit(pfad):
        yield d


def lies_mit_zeit(pfad: str | Path) -> Iterator[tuple[float, dict]]:
    """(Wanduhr, Rohdaten) - die Wanduhr verknuepft mit den Minimap-Bildern."""
    with gzip.open(pfad, "rt", encoding="utf-8") as f:
        try:
            for zeile in f:
                try:
                    z = json.loads(zeile)
                    yield z["w"], z["d"]
                except (json.JSONDecodeError, KeyError):
                    continue
        except EOFError:
            return


def bilder(pfad: str | Path) -> list[tuple[float, Path]]:
    """Die Minimap-Bilder einer Aufnahme als (Wanduhr, Datei), zeitlich sortiert."""
    ordner = Path(pfad).with_name(Path(pfad).name.removesuffix(".jsonl.gz") + "_bilder")
    if not ordner.exists():
        return []
    return sorted((int(b.stem) / 1000, b) for b in ordner.glob("*.jpg"))


def neueste() -> Path | None:
    dateien = sorted(ORDNER.glob("*.jsonl.gz"))
    return dateien[-1] if dateien else None
