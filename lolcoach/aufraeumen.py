"""Speicher (Auftrag 022): der Projektordner waechst nicht mehr unkontrolliert.

Regeln (Carlos: "nicht wie ein Geschwuer immer weiter wachsen"):
  1. Immer bleiben je Partie: .jsonl.gz, _ansagen.json, _kern.jsonl, _stratege.jsonl, _notizen.md, _sprechtaste.log,
     Bericht, Review - und im Bilderordner die kleinen Daten zum Nachspielen (sichtungen*, ereignisse*, wellen.json,
     gruben.json).
  2. Bilder (Minimap, Spielbildschirme, Chat) bleiben nur fuer Testpartien (`testpartien()`, gespeichert in
     wissen/testpartien.toml) und die letzten drei Partien.
  3. Flash-Clips: die 40 neuesten, der Rest geht.
  4. aufnahmen_probe/: nur das letzte Generalproben-Log bleibt (werkzeuge/generalprobe.py raeumt selbst auf).
Testpartien und die letzten drei Partien fasst es nie an. Ein Ordner mit einer Datei BEHALTEN bleibt ebenfalls.

    python werkzeuge/aufraeumen.py          # Trockenlauf: zeigt, was ginge
    python werkzeuge/aufraeumen.py --ja     # loescht
Nach jeder Partie ruft `python -m lolcoach` es mit ja=True auf.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from . import aufzeichnung

WURZEL = Path(__file__).resolve().parent.parent
AUFNAHMEN = WURZEL / "aufnahmen"
PROBE = WURZEL / "aufnahmen_probe"
LISTE = WURZEL / "wissen" / "testpartien.toml"
LETZTE = 3
FLASHCLIPS = 40
KLEIN = re.compile(r"^(sichtungen.*|ereignisse.*|wellen\.json|gruben\.json|BEHALTEN)$")
STAMM = re.compile(r"20\d\d-\d\d-\d\d_\d{6}")
KURZ_STAMM = re.compile(r"(?<![\d_-])(\d{6})(?!\d)")


def _staemme() -> list[str]:
    return sorted(p.name.removesuffix(".jsonl.gz") for p in aufzeichnung.alle(AUFNAHMEN))


def testpartien() -> dict[str, list[str]]:
    """Stamm -> Quellen: jede Aufnahme, die ein Szenario, ein Unit-Test, ein Nachspiel-Satz (Soll-Listen der Proben)
    oder das Freigabe-Tor aus 021 braucht - voll ("2026-09-29_183125") oder kurz ("183125") genannt."""
    alle = _staemme()
    kurz = {s.split("_")[1]: s for s in alle}
    quellen: dict[str, set[str]] = {}

    def dazu(text: str, wo: str) -> None:
        for s in STAMM.findall(text):
            if s in alle:
                quellen.setdefault(s, set()).add(wo)
        for k in KURZ_STAMM.findall(text):
            if k in kurz:
                quellen.setdefault(kurz[k], set()).add(wo)
    for p in list((WURZEL / "tests").glob("*.py")) + list((WURZEL / "tests" / "szenarien").rglob("*.toml")):
        dazu(p.read_text(encoding="utf-8", errors="replace"), str(p.relative_to(WURZEL)).replace("\\", "/"))
    for p in list((WURZEL / "buecher" / "protokolle" / "proben").glob("stratege_probe_0*/**/soll_*.json")) + \
            list((WURZEL / "buecher" / "protokolle").rglob("soll_*.json")):
        dazu(p.name, "Nachspiel-Satz (Soll-Liste)")
    return {s: sorted(q) for s, q in sorted(quellen.items())}


def schreibe_liste(tp: dict[str, list[str]]) -> None:
    z = ["# Testpartien (Auftrag 022): ihre Bilder bleiben. Automatisch ermittelt von lolcoach/aufraeumen.py -",
         "# nicht von Hand pflegen. Quelle je Partie: wer sie braucht.", ""]
    for s, q in tp.items():
        z += [f"[\"{s}\"]", "quellen = " + json.dumps(q, ensure_ascii=False), ""]
    LISTE.write_text("\n".join(z), encoding="utf-8")


def _letzte() -> set[str]:
    """Die letzten drei echten Partien (Aufnahme > 1 MB - Bruchstuecke von Neustarts zaehlen nicht)."""
    echte = [s for s in _staemme() if aufzeichnung.echt(AUFNAHMEN / f"{s}.jsonl.gz").stat().st_size > (1_000_000 if aufzeichnung.echt(AUFNAHMEN / f"{s}.jsonl.gz").name.endswith(".gz") else 30_000)]
    return set(echte[-LETZTE:])


def _groesse(p: Path) -> int:
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def plan() -> list[tuple[Path, int, str]]:
    """(Pfad, Bytes, Grund) fuer alles, was gehen darf."""
    tp = testpartien()
    schutz = set(tp) | _letzte()
    aus: list[tuple[Path, int, str]] = []
    for s in _staemme():
        ordner = AUFNAHMEN / f"{s}_bilder"
        if s in schutz or not ordner.exists() or (ordner / "BEHALTEN").exists():
            continue
        # ohne Sichtungsdatei sind die Minimap-Bilder die einzige Quelle fuers Nachspielen - dann bleiben sie
        sicht = (ordner / "sichtungen.jsonl.gz").exists() or (ordner / "sichtungen.json").exists()
        for f in ordner.iterdir():
            if f.is_file() and not KLEIN.match(f.name) and (sicht or not f.stem.isdigit()):
                aus.append((f, f.stat().st_size, f"Bilder von {s} (keine Testpartie)"))
    clips = sorted((d for o in AUFNAHMEN.glob("*_flashclips") for d in o.iterdir()),
                   key=lambda d: d.name, reverse=True)
    for d in clips[FLASHCLIPS:]:
        aus.append((d, _groesse(d), "Flash-Clip (nicht unter den 40 neuesten)"))
    if PROBE.exists():
        for f in PROBE.iterdir():
            if f.name != "generalprobe.log":
                aus.append((f, _groesse(f), "Generalprobe (nur das letzte Log bleibt)"))
    return aus


def probe_aufraeumen() -> float:
    """aufnahmen_probe/ bis auf das letzte Log leeren (werkzeuge/generalprobe.py am Ende). MB frei."""
    frei = 0
    if PROBE.exists():
        for f in PROBE.iterdir():
            if f.name != "generalprobe.log":
                frei += _groesse(f)
                shutil.rmtree(f, ignore_errors=True) if f.is_dir() else f.unlink(missing_ok=True)
    return frei / 1e6


def aufraeumen(ja: bool = False, ausgabe=print) -> float:
    """Trockenlauf (ja=False) oder loeschen. Schreibt wissen/testpartien.toml neu. Gibt die MB zurueck."""
    schreibe_liste(testpartien())
    p = plan()
    je: dict[str, int] = {}
    for _, n, grund in p:
        je[grund.split(" (")[0] if grund.startswith("Bilder") else grund] = je.get(
            grund.split(" (")[0] if grund.startswith("Bilder") else grund, 0) + n
    for grund, n in sorted(je.items(), key=lambda x: -x[1]):
        ausgabe(f"  {n / 1e6:8.1f} MB  {grund}")
    summe = sum(n for _, n, _ in p) / 1e6
    ausgabe(f"  {summe:8.1f} MB  {'geloescht' if ja else 'wuerden geloescht (Trockenlauf; --ja loescht)'}")
    # Auftrag 023, 6: fertige Aufnahmen ausser den letzten drei als .jsonl.xz (gzip 34 MB -> xz 0,5 MB; live bleibt gzip)
    letzte = _letzte_alle()
    xz = [q for q in AUFNAHMEN.glob("*.jsonl.gz") if q.name.removesuffix(".jsonl.gz") not in letzte]
    gz_mb = sum(q.stat().st_size for q in xz) / 1e6
    ausgabe(f"  {gz_mb:8.1f} MB  {len(xz)} Aufnahmen als xz ({'umgewandelt' if ja else 'wuerden umgewandelt'}, "
            "danach je ~1-2 %)")
    if ja:
        for f, _, _ in p:
            try:
                shutil.rmtree(f, ignore_errors=True) if f.is_dir() else f.unlink(missing_ok=True)
            except OSError:
                pass
        for o in AUFNAHMEN.glob("*_flashclips"):
            if o.is_dir() and not any(o.iterdir()):
                o.rmdir()
        for q in xz:
            try:
                summe += aufzeichnung.nach_xz(q) / 1e6
            except (OSError, ValueError):
                pass
    return summe


def _letzte_alle() -> set[str]:
    """Die letzten drei Aufnahmen ueberhaupt (auch Bruchstuecke): die juengste koennte noch geschrieben werden."""
    return {aufzeichnung.stamm(q) for q in aufzeichnung.alle(AUFNAHMEN)[-LETZTE:]}
