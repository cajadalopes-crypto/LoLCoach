"""Carlos' Notizen (Sprechtaste: "Notiz ...") werden Szenario-Stubs (Buch 0, Kapitel 12.2).

Liest aufnahmen/*_notizen.md und legt je Notiz einen Stub in tests/szenarien/offen/<stamm>.toml an:
  - Zeit und Notiztext,
  - was der Coach +-20 s gesagt hat (die gespeicherten Live-Ansagen, also das, was Carlos gehoert hat),
  - die Lage aus der Bewertung (Nachspielen): Ort, Leben, Gold, Welle, Gegner mit Ort und Zeit, Objectives.
Beschriftet werden die Stubs spaeter (soll/darf_nicht/warum), dann wandern sie nach tests/szenarien/.
Vorhandene Stubs bleiben unangetastet; neue Notizen kommen dazu.

    python werkzeuge/szenario_aus_notizen.py [aufnahme ...]     (ohne Angabe: alle Aufnahmen mit Notizen)
"""
from __future__ import annotations

import json
import re
import sys
import time
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nachspielen as ns  # noqa: E402

OFFEN = Path(__file__).resolve().parent.parent / "tests" / "szenarien" / "offen"
ZEILE = re.compile(r"^- (\d+):(\d\d) \(([^)]*)\): (.+)$")
UM = 20.0


def notizen(stamm: str) -> list[tuple[float, str]]:
    datei = ns.AUFNAHMEN / f"{stamm}_notizen.md"
    aus = []
    for z in datei.read_text(encoding="utf-8").splitlines():
        if m := ZEILE.match(z.strip()):
            aus.append((int(m.group(1)) * 60 + int(m.group(2)), m.group(4).strip()))
    return aus


def gehoert(stamm: str, t: float) -> list[str]:
    datei = ns.AUFNAHMEN / f"{stamm}_ansagen.json"
    if not datei.exists():
        return []
    alle = json.loads(datei.read_text(encoding="utf-8"))
    alle = alle if isinstance(alle, list) else alle.get("ansagen", [])
    aus = []
    for a in alle:
        g = a.get("gesprochen") if a.get("gesprochen") is not None else a.get("zeit", 0)
        if abs(g - t) <= UM:
            aus.append(f"{ns.uhr(g)} [{a.get('schluessel', '?')}] {a.get('text', '')}")
    return aus


def literal(text: str) -> str:
    """TOML-Literal ueber mehrere Zeilen (keine Escapes noetig)."""
    return "'''\n" + text.replace("'''", "' ' '") + "'''"


def stubs(stamm: str) -> int:
    liste = notizen(stamm)
    if not liste:
        return 0
    OFFEN.mkdir(parents=True, exist_ok=True)
    ziel = OFFEN / f"{stamm}.toml"
    vorhanden = set()
    if ziel.exists():
        vorhanden = {s["id"] for s in tomllib.loads(ziel.read_text(encoding="utf-8")).get("szenario", [])}
    neu = [(t, n) for t, n in liste if f"{int(t // 60):02d}{int(t % 60):02d}-notiz" not in vorhanden]
    if not neu:
        return 0
    lauf = ns.durchspielen(ns.pfad_zu(stamm), halte_bei=[t for t, _ in neu])
    bots = any(getattr(s, "bot", False) for p, _, _ in lauf.halte.values() for s in p.gegner()) if lauf.halte else False
    teile = []
    if not ziel.exists():
        teile.append(f"# Stubs aus Carlos' Notizen ({time.strftime('%d.%m.%Y')}, werkzeuge/szenario_aus_notizen.py) - noch "
                     f"nicht beschriftet.\n# Beschriften (soll / darf_nicht / darf_nicht_sagen / warum), dann nach "
                     f"tests/szenarien/ verschieben.\n\naufnahme = \"{stamm}\"\nbots = {'true' if bots else 'false'}\n")
    for t, n in neu:
        lage = lauf.halte[t][2] if t in lauf.halte else "nicht nachspielbar (keine Daten zu dieser Zeit)"
        teile.append(
            f"\n[[szenario]]\nid = \"{int(t // 60):02d}{int(t % 60):02d}-notiz\"\nzeit = \"{ns.uhr(t)}\"\n"
            f"quelle = \"Notiz {ns.uhr(t)}\"\nnotiz = {literal(n)}\n"
            f"gesagt = {literal(chr(10).join(gehoert(stamm, t)) or '(nichts in +-20 s)')}\n"
            f"lage = {literal(lage)}\n# soll = []\n# darf_nicht_sagen = []\n# warum = ''''''\n")
    with open(ziel, "a", encoding="utf-8") as f:
        f.write("".join(teile))
    tomllib.loads(ziel.read_text(encoding="utf-8"))     # muss lesbar bleiben
    return len(neu)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    staemme = [a.removesuffix(".jsonl.gz") for a in sys.argv[1:]] or sorted(
        f.name.removesuffix("_notizen.md") for f in ns.AUFNAHMEN.glob("*_notizen.md"))
    for s in staemme:
        if not (ns.AUFNAHMEN / f"{s}.jsonl.gz").exists():
            print(f"{s}: keine Aufnahme")
            continue
        print(f"{s}: {stubs(s)} neue Stubs")


if __name__ == "__main__":
    main()
