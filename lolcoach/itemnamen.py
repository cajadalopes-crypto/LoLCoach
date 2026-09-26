"""Item-Namen in Claudes Saetzen absichern.

Gemessen 26.09.2026: trotz mitgegebener Ladenliste kamen "Schwarzer Fleischer"
(richtig: Schwarzes Beil) oder "Klingenkoralle" vor. Ein falscher Item-Name im
Ohr ist schlimmer als keiner - der Spieler sucht im Laden und findet nichts.

`absichern(text)` findet Wortgruppen, die einem echten Item-Namen mit gleicher
Wortzahl sehr nahe kommen, aber nicht genau stimmen ("Stereks Pegel",
"Tanz der Todes", "Gefraessige Hydra"), und setzt den richtigen Namen ein. Was
keinem Item aehnelt, bleibt unangetastet (frei erfundene Namen wie
"Klingenkoralle" erkennt das nicht - dagegen hilft nur die Ladenliste im Prompt).
"""
from __future__ import annotations

import difflib
import re
from functools import lru_cache

from . import ddragon

AB = 0.84     # Aehnlichkeit, ab der korrigiert wird (darunter: kein Item gemeint)


def _flach(s: str) -> str:
    return (s.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
            .replace("'", ""))


@lru_cache(maxsize=1)
def namen() -> tuple[str, ...]:
    return tuple(sorted({v["name"] for v in ddragon.items().values()
                         if v.get("gold", {}).get("purchasable") and len(v["name"]) >= 6}, key=len, reverse=True))


@lru_cache(maxsize=1)
def _nach_wortzahl() -> dict[int, dict[str, str]]:
    aus: dict[int, dict[str, str]] = {}
    for n in namen():
        aus.setdefault(len(n.split()), {})[_flach(n)] = n
    return aus


def absichern(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Gibt (korrigierter Text, [(falsch, richtig), ...])."""
    belegt: list[tuple[int, int]] = []
    for n in namen():  # exakte Namen zuerst: die bleiben, wie sie sind
        for m in re.finditer(re.escape(n), text):
            belegt.append((m.start(), m.end()))
    woerter = list(re.finditer(r"[\wäöüÄÖÜß'\-]+", text))
    korrekturen = []
    for laenge in (5, 4, 3, 2, 1):
        kandidaten = _nach_wortzahl().get(laenge, {})
        if not kandidaten:
            continue
        for i in range(len(woerter) - laenge + 1):
            a, b = woerter[i].start(), woerter[i + laenge - 1].end()
            if any(not (b <= x or a >= y) for x, y in belegt) or not text[a].isupper():
                continue
            gruppe = text[a:b]
            if len(gruppe) < 6:
                continue
            treffer = difflib.get_close_matches(_flach(gruppe), list(kandidaten), n=1, cutoff=AB)
            if treffer and kandidaten[treffer[0]] != gruppe:
                korrekturen.append((gruppe, kandidaten[treffer[0]], a, b))
                belegt.append((a, b))
    for falsch, richtig, a, b in sorted(korrekturen, key=lambda k: -k[2]):
        text = text[:a] + richtig + text[b:]
    return text, [(f, r) for f, r, _, _ in korrekturen]
