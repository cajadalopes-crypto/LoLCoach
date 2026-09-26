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
import zlib
from pathlib import Path
from typing import Iterator

import os

# LOLCOACH_AUFNAHMEN: anderer Ordner, z. B. fuer die Generalprobe (werkzeuge/generalprobe.py)
ORDNER = Path(os.environ.get("LOLCOACH_AUFNAHMEN") or Path(__file__).resolve().parent.parent / "aufnahmen")


def gz_text(pfad: Path) -> str:
    """Der lesbare Inhalt einer gzip-Datei, auch wenn sie abgebrochen ist (Coach-Fenster zu): alle
    Mitglieder, bis es nicht weitergeht; eine halbe letzte Zeile faellt weg."""
    roh, teile = Path(pfad).read_bytes(), []
    while roh:
        d = zlib.decompressobj(16 + zlib.MAX_WBITS)
        try:
            teile.append(d.decompress(roh))
        except zlib.error:
            break
        if not d.eof:           # abgebrochenes Mitglied: danach kann nichts Lesbares mehr kommen
            break
        roh = d.unused_data
    text = b"".join(teile).decode("utf-8", "replace")
    return text[:text.rfind("\n") + 1] if "\n" in text else ""


def gz_saeubern(pfad: Path) -> None:
    """Eine abgebrochene gzip-Datei sauber neu schreiben - sonst ist alles, was danach angehaengt wird,
    unlesbar (der Leser haengt am fehlenden Ende des alten Stroms fest)."""
    pfad = Path(pfad)
    if not pfad.exists():
        return
    text = gz_text(pfad)
    neu = pfad.with_name(pfad.name + ".neu")
    with gzip.open(neu, "wt", encoding="utf-8") as f:
        f.write(text)
    neu.replace(pfad)


def _spieler(daten: dict) -> list:
    return sorted((s.get("riotId") or s.get("summonerName") or "", s.get("championName") or "")
                  for s in daten.get("allPlayers") or [])


def fortsetzbar(daten: dict, ordner: Path = ORDNER, hoechstens: float = 900) -> Path | None:
    """Die juengste Aufnahme, wenn `daten` (jetzt laufende Partie) DIESELBE Partie ist - Coach neu gestartet
    oder Reconnect: dieselben Spieler und Champions, die Spielzeit laeuft weiter, kein Spielende, zuletzt
    vor hoechstens `hoechstens` Sekunden geschrieben. Sonst None (neue Partie, neue Aufnahme).
    (26.09.: ein Neustart teilte Partie 7 in zwei Aufnahmen - zwei Reviews, zwei "Partien" im Fortschritt.)"""
    kandidaten = sorted(Path(ordner).glob("*.jsonl.gz"), reverse=True)
    if not kandidaten or time.time() - kandidaten[0].stat().st_mtime > hoechstens:
        return None
    letzte = None
    for zeile in reversed(gz_text(kandidaten[0]).splitlines()):
        try:
            letzte = json.loads(zeile)["d"]
            break
        except (ValueError, KeyError):
            continue
    if not letzte or not _spieler(daten) or _spieler(letzte) != _spieler(daten):
        return None
    if any(e.get("EventName") == "GameEnd" for e in (letzte.get("events") or {}).get("Events", [])):
        return None
    if (daten.get("gameData") or {}).get("gameTime", 0) < (letzte.get("gameData") or {}).get("gameTime", 0) - 5:
        return None
    return kandidaten[0]


class Schreiber:
    def __init__(self, ordner: Path = ORDNER, fortsetzen: Path | None = None):
        ordner.mkdir(parents=True, exist_ok=True)
        if fortsetzen is not None:
            gz_saeubern(fortsetzen)
        self.pfad = fortsetzen or ordner / time.strftime("%Y-%m-%d_%H%M%S.jsonl.gz")
        self.fortgesetzt = fortsetzen is not None
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
        except (EOFError, OSError, zlib.error):   # abgebrochen (Fenster zu): lesen, was da ist
            return


def bilder(pfad: str | Path) -> list[tuple[float, Path]]:
    """Die Minimap-Bilder einer Aufnahme als (Wanduhr, Datei), zeitlich sortiert. Nur die mit reiner Zahl
    als Namen - chat_*.jpg und schirm_*.jpg liegen daneben (int("chat_...") liess das Aufraeumen seit
    Partie 4 still scheitern)."""
    ordner = Path(pfad).with_name(Path(pfad).name.removesuffix(".jsonl.gz") + "_bilder")
    if not ordner.exists():
        return []
    return sorted((int(b.stem) / 1000, b) for b in ordner.glob("*.jpg") if b.stem.isdigit())


def bildschirme(pfad: str | Path) -> list[tuple[float, Path]]:
    """Die gesicherten Spielbildschirme einer Aufnahme (schirm_<Wanduhr ms>.jpg), zeitlich sortiert."""
    ordner = Path(pfad).with_name(Path(pfad).name.removesuffix(".jsonl.gz") + "_bilder")
    if not ordner.exists():
        return []
    return sorted((int(b.stem[7:]) / 1000, b) for b in ordner.glob("schirm_*.jpg") if b.stem[7:].isdigit())


def neueste() -> Path | None:
    dateien = sorted(ORDNER.glob("*.jsonl.gz"))
    return dateien[-1] if dateien else None
