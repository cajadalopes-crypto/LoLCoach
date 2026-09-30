"""Baukasten fuer konstruierte Makro-Lagen (Auftrag 032). Grundlage: blau (ORDER), du bist Top (Ambessa gegen
Aatrox), 10:00, alle Gegner eben gesehen, Welle Top in der Mitte, das Gehirn sagt klar 'Lane'."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lolcoach.makro.lage import Hirn, Kampf, MakroLage, Monster, Spieler, Ward, Welle  # noqa: E402

__all__ = ["L", "ich", "geg", "mit", "welle", "monster", "hirn", "Kampf", "Ward", "Welle", "Spieler", "setze"]


def L(**kw) -> MakroLage:
    lage = MakroLage(
        zeit=600, team="ORDER", gold=300,
        ich=Spieler("Ambessa", "TOP", pos=(1500, 12500), level=9, leben=0.8, tp_hat=True, tp_in=None),
        mitspieler=[Spieler("Vi", "JUNGLE", pos=(3800, 7800), level=8), Spieler("Sylas", "MIDDLE", pos=(6800, 6800), level=9),
                    Spieler("Varus", "BOTTOM", pos=(12000, 1800), level=8), Spieler("Bard", "UTILITY", pos=(11800, 1600), level=7)],
        gegner=[Spieler("Aatrox", "TOP", pos=(3800, 13600), gesehen_vor=2, level=9),
                Spieler("LeeSin", "JUNGLE", pos=(11000, 9000), gesehen_vor=5, level=8),
                Spieler("Brand", "MIDDLE", pos=(8000, 8000), gesehen_vor=3, level=9),
                Spieler("Ezreal", "BOTTOM", pos=(13000, 3000), gesehen_vor=3, level=8),
                Spieler("Leona", "UTILITY", pos=(13000, 2800), gesehen_vor=3, level=7)],
        wellen={"top": Welle("mitte")},
        hirn=Hirn(optionen=[("Lane", "", 0.5, 0.5, 0.05, "klar", [])], siegchance=0.5),
    )
    return setze(lage, **kw)


def setze(obj, **kw):
    for k, v in kw.items():
        assert hasattr(obj, k), k
        setattr(obj, k, v)
    return obj


def ich(lage: MakroLage, **kw) -> MakroLage:
    setze(lage.ich, **kw)
    return lage


def geg(lage: MakroLage, rolle: str, **kw) -> MakroLage:
    setze(next(g for g in lage.gegner if g.rolle == rolle), **kw)
    return lage


def mit(lage: MakroLage, rolle: str, **kw) -> MakroLage:
    setze(next(g for g in lage.mitspieler if g.rolle == rolle), **kw)
    return lage


def welle(lage: MakroLage, lane: str = "top", **kw) -> MakroLage:
    lage.wellen[lane] = Welle(**kw)
    return lage


def monster(lage: MakroLage, art: str, spawn_in: float, **kw) -> MakroLage:
    lage.monster.append(Monster(art, spawn_in, **kw))
    return lage


def hirn(lage: MakroLage, optionen=None, **kw) -> MakroLage:
    if optionen is not None:
        lage.hirn.optionen = optionen
    setze(lage.hirn, **kw)
    return lage
