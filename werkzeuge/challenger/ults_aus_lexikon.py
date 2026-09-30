"""Globale und lange Ults aus dem Lexikon -> wissen/makro/ults.toml (Auftrag 032, Regel J9).

    python werkzeuge/challenger/ults_aus_lexikon.py

Liest je Champion die Zeile '- R ...' in wissen/lexikon/champions/*.md. Global = der Text sagt global/ueber die (ganze)
Karte/egal wo/beliebigen Ort (aber nicht 'nicht global'); lang = groesste Zahl in der Zeile >= 2500 Einheiten.
"""
from __future__ import annotations

import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
LEX = WURZEL / "wissen" / "lexikon" / "champions"
ZIEL = WURZEL / "wissen" / "makro" / "ults.toml"
GLOBAL = ("global", "über die karte", "ueber die karte", "ganze karte", "egal wo", "beliebigen ort der karte")
LANG_AB = 2500


def lesen() -> list[tuple[str, str, int | None, str]]:
    out = []
    for p in sorted(LEX.glob("*.md")):
        zeilen = [z for z in p.read_text(encoding="utf-8").splitlines() if z.startswith("- R ")]
        if not zeilen:
            continue
        z = zeilen[0]
        klein = z.lower()
        glob = any(w in klein for w in GLOBAL) and "nicht global" not in klein
        zahlen = [int(x.replace(".", "")) for x in re.findall(r"\b(\d{1,2}\.?\d{3})\b", z)]
        weite = max(zahlen) if zahlen else None
        if glob:
            out.append((p.stem, "global", weite, z[4:z.find(":")] if ":" in z else ""))
        elif weite and weite >= LANG_AB:
            out.append((p.stem, "lang", weite, z[4:z.find(":")] if ":" in z else ""))
    return out


def schreiben() -> int:
    liste = lesen()
    z = ['# Globale und lange Ults (>= 2500 Einheiten) - erzeugt aus dem Lexikon von werkzeuge/challenger/ults_aus_lexikon.py',
         '# Regel J9 (wissen/makro/regeln.toml): ab Level 6 dieser Gegner nicht tief ohne Sicht.',
         'stand = "Lexikon 26.09.2026 (Patch 26.19), erzeugt 30.09.2026"', 'quelle = ["lexikon"]', '']
    for name, art, weite, ult in liste:
        z.append(f'[{name}]')
        z.append(f'art = "{art}"')
        if weite:
            z.append(f'weite = {weite}')
        z.append(f'ult = "{ult.strip()}"')
        z.append('')
    ZIEL.write_text("\n".join(z), encoding="utf-8")
    return len(liste)


if __name__ == "__main__":
    print(schreiben(), "Champions")
