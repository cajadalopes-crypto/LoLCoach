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


GZ, XZ = ".jsonl.gz", ".jsonl.xz"


def echt(pfad: str | Path) -> Path:
    """Auftrag 023, 6: die Datei, die es wirklich gibt. Alte Aufnahmen liegen nach dem Aufraeumen als .jsonl.xz
    (gzip 34 MB, xz 0,5 MB); der Code nennt sie weiter <stamm>.jsonl.gz - dieser Name fuehrt hier zur xz-Datei."""
    p = Path(pfad)
    if p.name.endswith(GZ) and not p.exists():
        x = p.with_name(p.name.removesuffix(GZ) + XZ)
        if x.exists():
            return x
    return p


def gibt(pfad: str | Path) -> bool:
    return echt(pfad).exists()


def stamm(pfad: str | Path) -> str:
    return Path(pfad).name.removesuffix(GZ).removesuffix(XZ)


def alle(ordner: str | Path | None = None) -> list[Path]:
    """Alle Aufnahmen eines Ordners (gz und xz), sortiert, jeweils unter ihrem Namen <stamm>.jsonl.gz."""
    o = Path(ordner or ORDNER)
    staemme = {stamm(p) for p in o.glob("*" + GZ)} | {stamm(p) for p in o.glob("*" + XZ)}
    return [o / f"{s}{GZ}" for s in sorted(staemme)]


def gz_text(pfad: Path) -> str:
    """Der lesbare Inhalt einer gzip-Datei, auch wenn sie abgebrochen ist (Coach-Fenster zu): alle
    Mitglieder, bis es nicht weitergeht; eine halbe letzte Zeile faellt weg. Eine xz-Aufnahme (Auftrag 023)
    wird ganz gelesen."""
    p = echt(pfad)
    if p.name.endswith(XZ):
        import lzma
        text = lzma.decompress(p.read_bytes()).decode("utf-8", "replace")
        return text[:text.rfind("\n") + 1] if "\n" in text else ""
    roh, teile = p.read_bytes(), []
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


def gz_saeubern(pfad: Path) -> bool:
    """Eine abgebrochene gzip-Datei sauber neu schreiben - sonst ist alles, was danach angehaengt wird,
    unlesbar (der Leser haengt am fehlenden Ende des alten Stroms fest). False, wenn die Datei gesperrt bleibt:
    Live 26.09., 23:14 - beim Neustart hielt Windows sie fest (Virenscanner/OneDrive), der Coach brach mit
    PermissionError ab. Dann laeuft eine neue Aufnahme statt gar keiner."""
    pfad = Path(pfad)
    if not pfad.exists():
        return True
    text = gz_text(pfad)
    neu = pfad.with_name(pfad.name + ".neu")
    # newline="": der Text hat schon die Zeilenenden der Aufnahme - sonst macht Windows aus \r\n ein \r\r\n,
    # und jede zweite Zeile ist leer (Aufnahme 230520: 555 Leerzeilen nach dem Neustart)
    with gzip.open(neu, "wt", encoding="utf-8", newline="") as f:
        f.write(text)
    for _ in range(20):          # bis ~6 s: eine kurze Sperre (Scan, Sync) geht vorbei
        try:
            neu.replace(pfad)
            return True
        except PermissionError:
            time.sleep(0.3)
    neu.unlink(missing_ok=True)
    return False


def _spieler(daten: dict) -> list:
    """Wer spielt, auf welcher Seite - OHNE Champion: Viego meldet in der Live-API den Champion, den er gerade
    uebernommen hat (Partie 144655, 9:24: aus "Viego" wurde Kha'Zix, dann Vex - der Coach hielt jede Uebernahme fuer
    eine neue Partie, sagte "Partie vorbei", schrieb ein Review und fing viermal neu an). Ein neues Practice Tool
    faellt an der Spieluhr auf (sie laeuft von vorn)."""
    return sorted((s.get("riotId") or s.get("summonerName") or "", s.get("team") or "")
                  for s in daten.get("allPlayers") or [])


def fortsetzbar(daten: dict, ordner: Path = ORDNER, hoechstens: float = 900) -> Path | None:
    """Die juengste Aufnahme, wenn `daten` (jetzt laufende Partie) DIESELBE Partie ist - Coach neu gestartet
    oder Reconnect: dieselben Spieler auf denselben Seiten, die Spielzeit laeuft weiter, kein Spielende, zuletzt
    vor hoechstens `hoechstens` Sekunden geschrieben. Sonst None (neue Partie, neue Aufnahme).
    (26.09.: ein Neustart teilte Partie 7 in zwei Aufnahmen - zwei Reviews, zwei "Partien" im Fortschritt.)"""
    kandidaten = sorted(Path(ordner).glob("*.jsonl.gz"), reverse=True)      # live: nur gzip, xz ist fertig
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
        if fortsetzen is not None and not gz_saeubern(fortsetzen):
            print(f"!! {fortsetzen.name} ist gesperrt - neue Aufnahme statt Fortsetzung", flush=True)
            fortsetzen = None
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
    """(Wanduhr, Rohdaten) - die Wanduhr verknuepft mit den Minimap-Bildern. gz oder xz (Auftrag 023)."""
    import lzma
    p = echt(pfad)
    oeffne = lzma.open if p.name.endswith(XZ) else gzip.open
    with oeffne(p, "rt", encoding="utf-8") as f:
        try:
            for zeile in f:
                try:
                    z = json.loads(zeile)
                    yield z["w"], z["d"]
                except (json.JSONDecodeError, KeyError):
                    continue
        except (EOFError, OSError, zlib.error, lzma.LZMAError):   # abgebrochen (Fenster zu): lesen, was da ist
            return


def nach_xz(pfad: str | Path) -> int:
    """Auftrag 023, 6: eine fertige gzip-Aufnahme verlustfrei in .jsonl.xz umwandeln (nach der Partie, nie live).
    Geprueft wird Byte fuer Byte gegen den gzip-Inhalt, erst dann faellt die gzip-Datei weg. Gibt die gesparten
    Bytes zurueck (0: nichts getan)."""
    import lzma
    p = Path(pfad)
    if not p.name.endswith(GZ) or not p.exists():
        return 0
    text = gz_text(p).encode("utf-8")
    ziel = p.with_name(p.name.removesuffix(GZ) + XZ)
    tmp = ziel.with_name(ziel.name + ".neu")
    tmp.write_bytes(lzma.compress(text, preset=6))
    if lzma.decompress(tmp.read_bytes()) != text:
        tmp.unlink(missing_ok=True)
        return 0
    vorher = p.stat().st_size
    tmp.replace(ziel)
    p.unlink()
    return vorher - ziel.stat().st_size


def bilderordner(pfad: str | Path) -> Path:
    """Der _bilder-Ordner einer Aufnahme - auch unter ihrem echten Namen .jsonl.xz (Auftrag 033: wer den xz-Pfad
    uebergab statt <stamm>.jsonl.gz, bekam keine Bilder und keine Sichtungen)."""
    return Path(pfad).with_name(stamm(pfad) + "_bilder")


def bilder(pfad: str | Path) -> list[tuple[float, Path]]:
    """Die Minimap-Bilder einer Aufnahme als (Wanduhr, Datei), zeitlich sortiert. Nur die mit reiner Zahl
    als Namen - chat_*.jpg und schirm_*.jpg liegen daneben (int("chat_...") liess das Aufraeumen seit
    Partie 4 still scheitern)."""
    ordner = bilderordner(pfad)
    if not ordner.exists():
        return []
    return sorted((int(b.stem) / 1000, b) for b in ordner.glob("*.jpg") if b.stem.isdigit())


def bildschirme(pfad: str | Path) -> list[tuple[float, Path]]:
    """Die gesicherten Spielbildschirme einer Aufnahme (schirm_<Wanduhr ms>.jpg), zeitlich sortiert."""
    ordner = bilderordner(pfad)
    if not ordner.exists():
        return []
    return sorted((int(b.stem[7:]) / 1000, b) for b in ordner.glob("schirm_*.jpg") if b.stem[7:].isdigit())


def neueste() -> Path | None:
    dateien = alle(ORDNER)
    return dateien[-1] if dateien else None
