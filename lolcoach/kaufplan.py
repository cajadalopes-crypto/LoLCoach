"""Kaufplan: was du dir mit deinem Gold JETZT kaufst - und wie viel bis zum naechsten Bauteil fehlt.

Reasoning (Abschnitt 1/8): "Gold bis Item, Gold bis Power Spike, naechster Component Spike -
wenn ich jetzt recall mache: was kaufe ich?". Statt "1300 Gold: back" sagt der Coach "reicht fuer
den Brutalisierer" oder "noch 150 bis Caulfields - Kanone mitnehmen, dann back".

Der Build kommt aus dem Champion-Lexikon (Abschnitt "## Build 26.19", Zeile "Kern: A -> B -> C"),
Preise und Bauteile aus Data Dragon. Was schon im Inventar liegt, zaehlt als bezahlt (auch als
Bauteil im Baum des naechsten Items).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from . import ddragon


@lru_cache(maxsize=1)
def _nach_name() -> dict[str, int]:
    aus = {}
    for i, v in ddragon.items().items():
        if i < 100000 and v.get("maps", {}).get("11") and v.get("gold", {}).get("purchasable"):
            aus.setdefault(v["name"], i)
    return aus


@lru_cache(maxsize=256)
def kern(champion_id: str) -> tuple[int, ...]:
    """Die Kern-Items (Reihenfolge) aus dem Lexikon, als Data-Dragon-IDs. Die Eintraege schreiben es
    verschieden: "Kern: A -> B -> C", "Richtung (ungeprueft): Rhaast - A, B oder C; Schatten - ...",
    "A oder B -> C/D". Genommen wird die erste Variante, je Schritt die erste Wahl."""
    import difflib
    from .gehirn import abschnitt
    text = abschnitt(champion_id, "Build", 4000)
    zeilen = [z.lstrip("- ") for z in text.splitlines()]
    zeile = next((z for z in zeilen if z.startswith("Kern")), None) or next(
        (z for z in zeilen if z.startswith("Richtung") and z.split(":", 1)[-1].strip()), "")
    zeile = re.sub(r"\([^)]*\)", "", zeile)   # "(op.gg meistgebaut, 64 % ...)" - das Komma darin trennt sonst
    zeile = zeile.split(":", 1)[-1].split(". Alternative")[0].split(". Stiefel")[0].split(";")[0]
    if " – " in zeile[:30]:
        zeile = zeile.split(" – ", 1)[1]          # "Rhaast – Eklipse, ..." -> "Eklipse, ..."
    namen = _nach_name()
    aus = []
    for schritt in re.split(r"→|->|,", zeile):
        wahl = re.split(r" oder |/", schritt)[0]
        n = re.sub(r"\(.*?\)", "", wahl).strip().rstrip(".")
        treffer = n if n in namen else next(iter(difflib.get_close_matches(n, list(namen), n=1, cutoff=0.85)), None)
        if treffer and namen[treffer] not in aus:
            aus.append(namen[treffer])
    return tuple(aus)


@dataclass
class Kauf:
    item: str                    # das naechste Kern-Item
    kaufen: list[str]            # was das Gold jetzt kauft (leer = nichts Sinnvolles)
    kosten: int
    naechstes: tuple[str, int] | None   # (Bauteil oder Item, fehlendes Gold), das als naechstes erreichbar wird

    def satz(self) -> str:
        if self.kaufen:
            return "reicht für " + " und ".join(_akk(n) for n in self.kaufen)
        if self.naechstes:
            return f"noch {self.naechstes[1]} bis {_dat(self.naechstes[0])}"
        return ""


def _akk(name: str) -> str:
    """'Der Brutalisierer' -> 'den Brutalisierer' (reicht fuer ...)."""
    return "den " + name[4:] if name.startswith("Der ") else name


def _dat(name: str) -> str:
    """'Der Brutalisierer' -> 'zum Brutalisierer' ist zu viel Grammatik - 'bis Brutalisierer' klingt falsch,
    'bis zum Brutalisierer' richtig; ohne Artikel: 'bis Caulfields Kriegshammer'."""
    return "zum " + name[4:] if name.startswith("Der ") else name


def _baum_kosten(item: int, inventar: list[int]) -> tuple[int, list[int]]:
    """(Restkosten, fehlende direkte Bauteile) - Inventar-Stuecke zaehlen als bezahlt (werden verbraucht)."""
    it = ddragon.items()
    e = it.get(item)
    if e is None:
        return 0, []
    if item in inventar:
        inventar.remove(item)
        return 0, []
    rest = e["gold"]["total"]
    fehlend = []
    for f in e.get("from") or []:
        f = int(f)
        teil_rest, _ = _baum_kosten(f, inventar)
        rest -= it[f]["gold"]["total"] - teil_rest
        if teil_rest > 0:
            fehlend.append(f)
    return rest, fehlend


def plan(champion_id: str, items: tuple[int, ...], gold: float) -> Kauf | None:
    it = ddragon.items()
    stiefel = [i for i in kern(champion_id) if "Boots" in it.get(i, {}).get("tags", [])]
    for ziel in [i for i in kern(champion_id) if i not in stiefel]:
        inventar = list(items)
        rest, fehlend = _baum_kosten(ziel, inventar)
        if rest <= 0:
            continue    # schon fertig
        name = it[ziel]["name"]
        hat_stiefel = any("Boots" in it.get(i, {}).get("tags", []) for i in items)
        if gold >= rest:
            extra = ["Stiefel"] if not hat_stiefel and gold - rest >= 300 else []
            return Kauf(name, [name] + extra, rest + 300 * len(extra), None)
        # Bauteile: das teuerste bezahlbare zuerst, dann auffuellen
        kaufen, kosten, frei = [], 0, gold
        kandidaten = []
        for f in fehlend:
            inv = list(items)
            k, _ = _baum_kosten(f, inv)
            kandidaten.append((k, f))
        for k, f in sorted(kandidaten, reverse=True):
            if 0 < k <= frei and k >= 300:
                kaufen.append(it[f]["name"])
                kosten += k
                frei -= k
        if not hat_stiefel and frei >= 300 and (kaufen or gold < 700):
            kaufen.append("Stiefel")
            kosten += 300
            frei -= 300
        billigstes = min(((k, f) for k, f in kandidaten if k > gold), default=None)
        naechstes = (it[billigstes[1]]["name"], int(billigstes[0] - gold)) if billigstes and not kaufen else None
        if not kaufen and naechstes is None:
            naechstes = (name, int(rest - gold))
        return Kauf(name, kaufen, kosten, naechstes)
    return None
