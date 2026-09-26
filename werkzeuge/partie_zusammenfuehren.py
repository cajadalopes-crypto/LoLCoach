"""Eine Partie, die ueber mehrere Aufnahmen verteilt ist (Coach neu gestartet, bevor es die Fortsetzung
gab), zu EINER Aufnahme zusammenfuehren - damit Review und Fortschritt sie als eine Partie sehen.

    python werkzeuge/partie_zusammenfuehren.py <ziel-stamm> <teil-stamm> [...]

Ziel ist die erste Aufnahme der Partie. Die Teile werden angehaengt (Schnappschuesse, Minimap-Bilder,
Sichtungen, Ereignisse, Ansagen, Notizen, Sprechtasten-Log); ihre Dateien wandern nach
aufnahmen/_zusammengefuehrt/ (nichts wird geloescht). Veraltetes Review/Verlauf/Bericht des Ziels
wandert mit - der naechste Coach-Start (oder `python -m lolcoach review`) schreibt es neu.
"""
from __future__ import annotations

import gzip
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import aufzeichnung  # noqa: E402

A = aufzeichnung.ORDNER
ABLAGE = A / "_zusammengefuehrt"


def _gz_schreiben(pfad: Path, zeilen: list[str]) -> None:
    neu = pfad.with_name(pfad.name + ".neu")
    with gzip.open(neu, "wt", encoding="utf-8") as f:
        f.write("".join(z if z.endswith("\n") else z + "\n" for z in zeilen))
    neu.replace(pfad)


def _zeilen(pfad: Path) -> list[str]:
    return aufzeichnung.gz_text(pfad).splitlines() if pfad.exists() else []


def _w(zeile: str) -> float:
    try:
        return float(json.loads(zeile)["w"])
    except (ValueError, KeyError, TypeError):
        return 0.0


def fuehre_zusammen(ziel: str, teile: list[str]) -> None:
    ABLAGE.mkdir(exist_ok=True)
    zb = A / f"{ziel}_bilder"
    zb.mkdir(exist_ok=True)
    aufnahme = _zeilen(A / f"{ziel}.jsonl.gz")
    sichtungen, ereignisse = _zeilen(zb / "sichtungen.jsonl.gz"), _zeilen(zb / "ereignisse.jsonl.gz")
    ansagen_datei = A / f"{ziel}_ansagen.json"
    ansagen = json.loads(ansagen_datei.read_text(encoding="utf-8")) if ansagen_datei.exists() else []
    for teil in teile:
        aufnahme += _zeilen(A / f"{teil}.jsonl.gz")
        tb = A / f"{teil}_bilder"
        sichtungen += _zeilen(tb / "sichtungen.jsonl.gz")
        ereignisse += _zeilen(tb / "ereignisse.jsonl.gz")
        if (d := A / f"{teil}_ansagen.json").exists():
            ansagen += json.loads(d.read_text(encoding="utf-8"))
        for endung in ("_notizen.md", "_sprechtaste.log"):
            if (d := A / f"{teil}{endung}").exists():
                with open(A / f"{ziel}{endung}", "a", encoding="utf-8") as f:
                    f.write(d.read_text(encoding="utf-8"))
        if tb.exists():
            for b in tb.glob("*.jpg"):
                shutil.move(str(b), zb / b.name)
    _gz_schreiben(A / f"{ziel}.jsonl.gz", sorted(aufnahme, key=_w))
    _gz_schreiben(zb / "sichtungen.jsonl.gz", sorted(sichtungen, key=_w))
    _gz_schreiben(zb / "ereignisse.jsonl.gz", sorted(ereignisse, key=_w))
    ansagen_datei.write_text(json.dumps(ansagen, ensure_ascii=False, indent=0), encoding="utf-8")
    # Teile und das veraltete Review des Ziels in die Ablage
    for teil in teile:
        for d in A.glob(f"{teil}*"):
            shutil.move(str(d), ABLAGE / d.name)
    for endung in ("_review.json", "_verlauf.json", "_bericht.md", "_gespraech.json"):
        if (d := A / f"{ziel}{endung}").exists():
            shutil.move(str(d), ABLAGE / d.name)
    n = len(list(aufzeichnung.lies(A / f"{ziel}.jsonl.gz")))
    print(f"{ziel}: {n} Schnappschuesse, {len(sichtungen)} Minimap-Zeilen, {len(ansagen)} Ansagen - "
          f"Teile {', '.join(teile)} in {ABLAGE.name}/")


if __name__ == "__main__":
    fuehre_zusammen(sys.argv[1], sys.argv[2:])
