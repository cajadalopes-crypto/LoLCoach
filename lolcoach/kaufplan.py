"""Kaufplan: was du dir mit deinem Gold JETZT kaufst - und wie viel bis zum naechsten Bauteil fehlt.

Reasoning (Abschnitt 1/8): "Gold bis Item, Gold bis Power Spike, naechster Component Spike -
wenn ich jetzt recall mache: was kaufe ich?". Statt "1300 Gold: back" sagt der Coach "reicht fuer
den Brutalisierer" oder "noch 150 bis Caulfields - Kanone mitnehmen, dann back".

Das naechste Item (Pruefung 27.09.c, R3 - 164326 sagte 13 Minuten "Caulfields", Carlos baute Hydra und Schutzengel):
1. das Item, dessen Bauteile du schon hast (Data Dragon from/into gegen dein Inventar - wer Tiamat hat, baut Hydra);
2. sonst der naechste Schritt aus DEINEM Build (wissen/build_carlos.toml, abgeleitet aus deinen Aufnahmen mit
   werkzeuge/build_aus_aufnahmen.py; ein Schritt nennt Gleichwertiges: "Gefraessige oder Gottlose Hydra");
3. erst als letzter Rueckfall der statische Plan aus dem Champion-Lexikon (Abschnitt "## Build 26.19", "Kern: A -> B").
Preise und Bauteile aus Data Dragon. Was schon im Inventar liegt, zaehlt als bezahlt (auch als Bauteil im Baum).

Jedes genannte Item muss kaufbar sein (kaufbar()): ein Platz frei - oder es verbraucht eigene Bauteile, oder ein
Start-Item (Dorans) wird dafuer verkauft; nicht schon im Inventar; baut ins Ziel-Item ein. Volles Inventar ohne das:
kein Kauf (164326 38:33 sagte bei sechs fertigen Items "Kauf Langschwert und Stiefel").
"""
from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

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
    if len(aus) < 2:
        # andere Schreibweisen (12 von 173 Champions, Pruefung 26.09.): "Richtung: ... (A oder B), dann C" oder
        # die Wege erst in den Zeilen darunter ("- Support: A -> B"): Item-Namen in Reihenfolge suchen
        roh = next((z for z in zeilen if z.startswith("Richtung")), "")
        kandidaten = [roh.split(":", 1)[-1]] + [z.split(":", 1)[-1] for z in zeilen
                                                if not z.startswith(("Richtung", "Situativ", "Stiefel", "Runen",
                                                                     "Beschwörer", "Skill"))]
        for zeile in kandidaten:
            gefunden = _items_in(zeile)
            if len(gefunden) >= 2:
                return tuple(gefunden[:3])      # der erste Weg - eine Zeile nennt manchmal zwei (Katarina)
    return tuple(aus)


def _items_in(zeile: str) -> list[int]:
    """Item-Namen in der Reihenfolge ihres Auftretens; bei "A oder B" / "A/B" nur A; ohne Stiefel."""
    it = ddragon.items()
    namen = _nach_name()
    treffer = []
    for n in sorted(namen, key=len, reverse=True):
        for m in re.finditer(r"(?<![\w])" + re.escape(n) + r"(?![\w])", zeile):
            if not any(a <= m.start() < e for a, e, _ in treffer):
                treffer.append((m.start(), m.end(), namen[n]))
    treffer.sort()
    aus, ende = [], -1
    for a, e, i in treffer:
        zwischen = zeile[ende:a] if ende >= 0 else ""
        if ende >= 0 and zwischen.strip() in ("oder", "/", ""):
            ende = e
            continue       # Alternative zum vorigen
        ende = e
        if "Boots" in it.get(i, {}).get("tags", []) or i in aus:
            continue
        aus.append(i)
    return aus


@dataclass
class Kauf:
    item: str                    # das naechste Kern-Item
    kaufen: list[str]            # was das Gold jetzt kauft (leer = nichts Sinnvolles)
    kosten: int
    naechstes: tuple[str, int] | None   # (Bauteil oder Item, fehlendes Gold), das als naechstes erreichbar wird
    verkaufen: str | None = None        # Inventar voll: dieses Item zuerst verkaufen (Start-Item)

    def satz(self) -> str:
        if self.kaufen:
            namen = [_akk(n) for n in self.kaufen]
            return "reicht für " + (namen[0] if len(namen) == 1 else ", ".join(namen[:-1]) + " und " + namen[-1])
        if self.naechstes:
            return f"noch {self.naechstes[1]} bis {_dat(self.naechstes[0])}"
        return ""


def _akk(name: str) -> str:
    """'Der Brutalisierer' -> 'den Brutalisierer' (reicht fuer ...)."""
    return "den " + name[4:] if name.startswith("Der ") else name


_WEIBLICH = ("hydra", "klinge", "axt", "hacke", "eklipse", "schneide", "sense", "lanze", "kette", "rüstung", "maske",
             "sichel", "peitsche", "glefe", "robe", "krone", "kappe", "tiamat")
_MAENNLICH = ("hammer", "bogen", "schild", "helm", "dolch", "mantel", "umhang", "gürtel", "handschuh", "stab", "panzer",
              "brutalisierer", "schlitzer", "reißer", "zahn", "splitter", "stein", "himmel", "anker", "streitkolben")
_SAECHLICH = ("schwert", "horn", "amulett", "buch", "messer", "juwel", "siegel", "herz", "visier", "medaillon")


def akk_artikel(name: str) -> str:
    """"Gefraessige Hydra" -> "die Gefraessige Hydra", "Axiombogen" -> "den Axiombogen", "Caulfields Kriegshammer"
    bleibt (Name im Genitiv), unbekannt ohne Artikel."""
    if name.startswith(("Der ", "Die ", "Das ")):
        return _akk(name) if name.startswith("Der ") else name[:1].lower() + name[1:]
    w = name.split()
    if len(w) > 1 and w[0].endswith("s") and w[0][:1].isupper():
        return name
    letztes = w[-1].lower()
    for endungen, art in ((_WEIBLICH, "die"), (_MAENNLICH, "den"), (_SAECHLICH, "das")):
        if letztes.endswith(endungen):
            return f"{art} {name}"
    return name


def mit_ziel(name: str, ziel: str | None) -> str:
    """Auftrag 009, 4: ein Bauteil wird mit seinem Ziel genannt - "Langschwert fuer die Gefraessige Hydra"."""
    ids = _nach_name()
    t, z = ids.get(name), ids.get(ziel) if ziel else None
    if t is None or z is None or t == z or t not in _baum(z):
        return name
    return f"{name} für {akk_artikel(ziel)}"


def _dat(name: str) -> str:
    """'Der Brutalisierer' -> 'zum Brutalisierer' ist zu viel Grammatik - 'bis Brutalisierer' klingt falsch,
    'bis zum Brutalisierer' richtig; ohne Artikel: 'bis Caulfields Kriegshammer'. Auftrag 009: auch 'bis zur Eklipse',
    'bis zum Axiombogen' (akk_artikel kennt das Geschlecht)."""
    if name.startswith("Der "):
        return "zum " + name[4:]
    a = akk_artikel(name)
    if a == name:
        return name
    w = name.split()
    if len(w) > 1 and w[0].endswith("e"):
        w[0] += "n"                                  # Dativ, schwach: "zur Gefraessigen Hydra"
    return {"die": "zur", "den": "zum", "das": "zum"}[a.split(" ", 1)[0]] + " " + " ".join(w)


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


def plan_rest(name: str | None, inventar, gold: float | None) -> int | None:
    """Auftrag 016, 5: so viel Gold fehlt noch, um `name` GANZ zu kaufen (die Bauteile im Inventar verschmelzen, kein
    neuer Platz) - None, wenn es schon reicht oder unbekannt ist."""
    i = _nach_name().get(name) if name else None
    if i is None or gold is None:
        return None
    rest, _ = _baum_kosten(i, [int(x) for x in inventar])
    fehlt = int(rest - gold)
    return fehlt if fehlt > 0 else None


@lru_cache(maxsize=256)
def folge(champion_id: str) -> tuple[int, ...]:
    """Die Items nach dem Kern (Lexikon, Zeile "Item 4-6"), ohne Stiefel und ohne die schon im Kern - sonst hatte ein
    fertiger Kern-Build nichts mehr zu kaufen (102112, 30:04: 3007 Gold in der Basis, der Coach wusste nichts)."""
    from .gehirn import abschnitt
    zeile = next((z.lstrip("- ") for z in abschnitt(champion_id, "Build", 4000).splitlines()
                  if z.lstrip("- ").startswith("Item 4")), "")
    k = kern(champion_id)
    return tuple(i for i in _items_in(zeile.split(":", 1)[-1]) if i not in k)


PLAETZE = 6                                   # Item-Plaetze ohne Schmuckstueck
GRUPPEN = {3077: "Hydra", 3035: "Letztes Flüstern"}   # Spielregel: nur ein Item, das dieses Bauteil enthaelt
BUILD = Path(__file__).resolve().parent.parent / "wissen" / "build_carlos.toml"


@lru_cache(maxsize=1024)
def _baum(item: int) -> frozenset[int]:
    """Alle Bauteile im Rezept (rekursiv), ohne das Item selbst."""
    aus = set()
    for f in ddragon.items().get(item, {}).get("from") or []:
        aus |= {int(f)} | _baum(int(f))
    return frozenset(aus)


def gruppe(item: int) -> str | None:
    """Hydra fuer alles mit Tiamat im Rezept usw. - davon traegt man nur eins."""
    return next((g for teil, g in GRUPPEN.items() if teil in _baum(item)), None)


GRUPPEN_DATEI = Path(__file__).resolve().parent.parent / "wissen" / "item_gruppen.json"


@lru_cache(maxsize=1)
def _spielgruppen() -> dict[int, tuple[tuple[str, int], ...]]:
    """Item -> (Gruppe, hoechstens so viele) aus den Spieldaten (werkzeuge/item_gruppen.py)."""
    try:
        gruppen = json.loads(GRUPPEN_DATEI.read_text(encoding="utf-8"))["gruppen"]
    except (OSError, ValueError, KeyError):
        return {}
    aus: dict[int, list] = {}
    for g, v in gruppen.items():
        for i in v["items"]:
            aus.setdefault(int(i), []).append((g, int(v["max"])))
    return {i: tuple(x) for i, x in aus.items()}


def konflikt(item: int, inventar) -> int | None:
    """Auftrag 018, 4 (183125 35:04: "Kauf Schwarzes Beil" zu Lord Dominiks Grüße): das Inventar-Item, mit dem
    `item` eine einzigartige Gruppe teilt und das beim Kauf nicht verbraucht wird - sonst None. Stiefel regelt
    kaufbar() selbst."""
    sg = _spielgruppen()
    baum = _baum(item)
    for g, hoechstens in sg.get(item, ()):
        if g.startswith("Boots"):
            continue
        drin = [j for j in inventar if j != item and j not in baum and any(h == g for h, _ in sg.get(j, ()))]
        if len(drin) + 1 > hoechstens:
            return drin[0]
    return None


@lru_cache(maxsize=64)
def carlos_build(champion_id: str) -> tuple[tuple[int, ...], ...]:
    """Carlos' eigener Build: Schritte, je Schritt die gleichwertigen Items (haeufigstes zuerst). Leer ohne Eintrag."""
    try:
        eintrag = tomllib.loads(BUILD.read_text(encoding="utf-8")).get(champion_id) or {}
    except (OSError, ValueError):
        return ()
    namen = _nach_name()
    schritte = (tuple(namen[n] for n in s if n in namen) for s in eintrag.get("folge", []))
    return tuple(s for s in schritte if s)


def schritte(champion_id: str) -> list[tuple[int, ...]]:
    """Carlos' Build, dahinter der statische Plan (Lexikon Kern + Folge) - ohne Stiefel und ohne das, was sein Build
    schon nennt."""
    it = ddragon.items()
    eigen = list(carlos_build(champion_id))
    schon = {i for s in eigen for i in s}
    return eigen + [(i,) for i in (*kern(champion_id), *folge(champion_id))
                    if i not in schon and "Boots" not in it.get(i, {}).get("tags", [])]


def _tags(i: int) -> set:
    return set(ddragon.items().get(i, {}).get("tags", []))


def _belegt(items) -> int:
    return sum(1 for i in items if "Trinket" not in _tags(i))


def _start_item(items) -> int | None:
    """Ein Start-Item (Dorans ...), das man fuer einen Platz verkauft: kein Rezept, baut in nichts, <= 500 Gold."""
    it = ddragon.items()
    kand = [i for i in items if i in it and not it[i].get("from") and not it[i].get("into")
            and it[i]["gold"]["total"] <= 500 and not {"Trinket", "Consumable", "Boots"} & _tags(i)]
    # Auftrag 017, 0.5 (192113 28:24: "Gerade nichts zu kaufen" bei 4130 Gold und sechs Plaetzen mit Nachfuellbarem
    # Trank): ein Trank, der einen Platz belegt und nicht verbraucht wird, geht zuerst
    trank = [i for i in items if i in it and "Consumable" in _tags(i) and not it[i].get("consumed")
             and i != 2055 and "Trinket" not in _tags(i)]
    return min(trank or kand, key=lambda i: it[i]["gold"]["total"], default=None)


def _verbraucht(item: int, inventar) -> int:
    """Wie viele Inventar-Stuecke das Item beim Kauf verbraucht (eigene Bauteile)."""
    inv = list(inventar)
    for f in ddragon.items().get(item, {}).get("from") or []:
        _baum_kosten(int(f), inv)
    return len(inventar) - len(inv)


def _noch_zu_kaufen(item: int, inventar: list) -> list[int]:
    """Das Item und die Bauteile darunter, die nicht im Inventar liegen (Inventar-Stuecke werden verbraucht)."""
    if item in inventar:
        inventar.remove(item)
        return []
    aus = [item]
    for f in ddragon.items().get(item, {}).get("from") or []:
        aus += _noch_zu_kaufen(int(f), inventar)
    return aus


def plaetze_nach(inventar, namen: list[str]) -> int:
    """Auftrag 008, A3.3: freie Plaetze, nachdem die genannten Items gekauft sind - jedes belegt einen Platz, ausser es
    verbraucht eigene Bauteile (die dann frei werden) oder ist ein Verbrauchsgut, das stapelt."""
    inv = [int(i) for i in inventar]
    frei = PLAETZE - _belegt(inv)
    for name in namen:
        i = _nach_name().get(name)
        if i is None:
            continue
        if "Consumable" in _tags(i) and i in inv:        # stapelt; sonst braucht auch ein Elixier einen Platz (018)
            continue
        vorher = len(inv)
        for f in ddragon.items().get(i, {}).get("from") or []:
            _baum_kosten(int(f), inv)          # verbrauchte eigene Bauteile fallen aus dem Inventar
        frei += (vorher - len(inv)) - 1
        inv.append(i)
    return frei


def kaufbar(name: str, inventar, ziel: str | None = None) -> tuple[bool, str]:
    """(kaufbar, Grund wenn nicht) fuer ein genanntes Item - Pruefung 27.09.c, R3, Soll 3:
    passt ins Inventar (Platz frei, oder es verbraucht eigene Bauteile, oder ein Start-Item wird dafuer verkauft),
    liegt nicht schon im Inventar (ausser das Ziel braucht noch eins), baut ins Ziel-Item ein oder ist es.
    Kontroll-Auge und Elixiere: mit freiem Platz oder (Auge) auf den Stapel. Stiefel: ohne Ziel-Pruefung.
    Bei True ist der Grund leer oder nennt den noetigen Verkauf ("nach Verkauf von Dorans Klinge")."""
    it = ddragon.items()
    inventar = [int(i) for i in inventar]
    i = _nach_name().get(name)
    if i is None:
        return False, f"{name} ist kein kaufbares Item"
    z = _nach_name().get(ziel) if ziel else None
    frei = PLAETZE - _belegt(inventar)
    if "Consumable" in _tags(i):
        if i in inventar or frei >= 1:                 # Auftrag 018, 4: auch Elixiere brauchen einen Platz
            return True, ""
        return False, "Inventar voll"
    stiefel = "Boots" in _tags(i)
    if stiefel and any("Boots" in _tags(j) and j not in _baum(i) for j in inventar):
        return False, "Stiefel liegen schon im Inventar"
    if i in inventar and not (z is not None and i in _noch_zu_kaufen(z, list(inventar))):
        return False, f"{name} liegt schon im Inventar"
    g = gruppe(i)
    if g is not None and any(j != i and gruppe(j) == g and not it.get(j, {}).get("into") for j in inventar):
        return False, f"schon eine {g} im Inventar"
    if (j := konflikt(i, inventar)) is not None:
        return False, f"{name} geht nicht zusammen mit {it[j]['name']} (einzigartig)"
    if z is not None and not stiefel and i != z:
        if i not in _baum(z):
            return False, f"{name} baut nicht in {ziel} ein"
        if i not in _noch_zu_kaufen(z, list(inventar)):
            return False, f"{ziel} braucht kein weiteres {name}"
    if frei + _verbraucht(i, inventar) >= 1:
        return True, ""
    start = _start_item(inventar)
    if start is not None:
        return True, f"nach Verkauf von {it[start]['name']}"
    return False, "Inventar voll, und es verbraucht keine eigenen Bauteile"


def _reihe(champion_id: str, items: tuple[int, ...]) -> list[int]:
    """Die offenen Ziel-Items, bestes zuerst: meiste eigene Bauteile (Gold), dann Carlos' Build, dann Lexikon."""
    it = ddragon.items()
    gruppen = {gruppe(i) for i in items if i in it and not it[i].get("into")} - {None}
    offen = []
    for n, schritt in enumerate(schritte(champion_id)):
        if any(i in items for i in schritt):
            continue
        for m, i in enumerate(schritt):
            if i in it and gruppe(i) not in gruppen and konflikt(i, items) is None:
                gedeckt = it[i]["gold"]["total"] - _baum_kosten(i, list(items))[0]
                offen.append((-gedeckt, n, m, i))
    return [i for *_, i in sorted(offen)]


def _versuch(ziel: int, items: tuple[int, ...], gold: float, frei: int, stiefel_fehlt: bool) -> Kauf | None:
    """Was das Gold fuer dieses Ziel kauft - nur was in die freien Plaetze passt, und jedes Stueck auch fuer sich
    im JETZIGEN Inventar (sonst sagt kaufbar() nein: Stiefel "passen" erst nach der Hydra, die zwei Bauteile
    verbraucht - der Spieler hoert beides in einem Satz). None: gar nichts davon passt."""
    it = ddragon.items()
    name = it[ziel]["name"]
    rest, fehlend = _baum_kosten(ziel, list(items))
    platz = frei + _verbraucht(ziel, items)          # Plaetze nach dem Kauf des ganzen Items
    if gold >= rest and platz >= 1:
        extra = ["Stiefel"] if stiefel_fehlt and gold - rest >= 300 and platz >= 2 and frei >= 1 else []
        return Kauf(name, [name] + extra, rest + 300 * len(extra), None)
    # Bauteile: das teuerste bezahlbare zuerst, dann auffuellen. Ein eigenes Bauteil zaehlt nur EINMAL (173159 16:10:
    # Caulfields und Zepter "verbrauchten" beide dasselbe Langschwert - 1518 Gold sollten fuer 1600 reichen)
    kandidaten = [(_baum_kosten(f, list(items))[0], f, _verbraucht(f, items)) for f in fehlend]
    kaufen, kosten, geld, plaetze, uebrig = [], 0, gold, frei, list(items)
    for _, f, v_jetzt in sorted(kandidaten, reverse=True):
        probe = list(uebrig)
        k, _ = _baum_kosten(f, probe)
        v = len(uebrig) - len(probe)
        if 0 < k <= geld and k >= 300 and plaetze + v >= 1 and frei + v_jetzt >= 1:
            kaufen.append(it[f]["name"])
            kosten += k
            geld -= k
            plaetze += v - 1
            uebrig = probe
    if stiefel_fehlt and geld >= 300 and plaetze >= 1 and frei >= 1 and (kaufen or gold < 700):
        kaufen.append("Stiefel")
        kosten += 300
    if kaufen:
        return Kauf(name, kaufen, kosten, None)
    erreichbar = [(k, f) for k, f, v in kandidaten if k > gold and frei + v >= 1]
    if erreichbar:
        k, f = min(erreichbar)
        return Kauf(name, [], 0, (it[f]["name"], int(k - gold)))
    if platz >= 1:
        return Kauf(name, [], 0, (name, int(rest - gold)))
    return None


def _erster(reihe: list[int], items: tuple[int, ...], gold: float, frei: int, stiefel_fehlt: bool) -> Kauf | None:
    for ziel in reihe:
        if (k := _versuch(ziel, items, gold, frei, stiefel_fehlt)) is not None:
            return k
    return None


ELIXIER_AB_LEVEL = 9
ELIXIER = {"Zorn": 2140, "Zauberei": 2139, "Metall": 2138}


def elixier(champion_id: str) -> int:
    """Das passende Elixier: magischer Schaden Zauberei, Tanks Metall, sonst Zorn (Angriffsschaden)."""
    c = ddragon.champions().get(champion_id) or {}
    info, tags = c.get("info") or {}, c.get("tags") or []
    if info.get("magic", 0) > info.get("attack", 0):
        return ELIXIER["Zauberei"]
    if tags[:1] == ["Tank"]:
        return ELIXIER["Metall"]
    return ELIXIER["Zorn"]


def plan(champion_id: str, items: tuple[int, ...], gold: float, level: int | None = None) -> Kauf | None:
    """Was dein Gold jetzt kauft (Reihenfolge der Ziele: _reihe). None: nichts zu kaufen - auch bei vollem Inventar,
    wenn kein Ziel eigene Bauteile verbraucht und kein Start-Item zu verkaufen ist (kein "Gold fuer ..." mehr).
    Auftrag 018, 4 (183125 35:43, 1205 Gold: "Gerade nichts zu kaufen"): mit `level` ab 9 dann ein Elixier. Es
    braucht einen freien Platz, bis man es trinkt: die Spieldaten fuehren es als "consumed" (verbraucht beim BENUTZEN,
    wie das Kontroll-Auge), und 183125 36:47 konnte Carlos es mit sechs Items nicht kaufen."""
    k = _plan(champion_id, items, gold)
    frei = PLAETZE - _belegt(tuple(int(i) for i in items))
    if k is None and level is not None and level >= ELIXIER_AB_LEVEL and frei >= 1:
        e = ddragon.items().get(elixier(champion_id))
        if e is not None and gold >= e["gold"]["total"]:
            return Kauf(e["name"], [e["name"]], e["gold"]["total"], None)
    return k


def _plan(champion_id: str, items: tuple[int, ...], gold: float) -> Kauf | None:
    it = ddragon.items()
    items = tuple(int(i) for i in items)
    frei = PLAETZE - _belegt(items)
    stiefel_fehlt = not any("Boots" in _tags(i) for i in items)
    reihe = _reihe(champion_id, items)
    ohne = _erster(reihe, items, gold, frei, stiefel_fehlt)
    start = _start_item(items) if frei <= 0 else None
    if start is not None and (ohne is None or not ohne.kaufen):
        # Inventar voll: fuer den PLATZ das Start-Item verkaufen - 164326 29:15 hat Carlos genau das getan (Dorans
        # weg, Stahlsiegel fuer den Schutzengel). Sein Verkaufswert zaehlt nicht: "Verkauf Dorans" nur, wo der Platz
        # fehlt, nicht wo 68 Gold fehlen (173159 16:16 - Caulfields verbraucht das Langschwert, passt also so)
        rest = list(items)
        rest.remove(start)
        mit = _erster(reihe, tuple(rest), gold, frei + 1, stiefel_fehlt)
        if mit is not None and mit.kaufen:
            mit.verkaufen = it[start]["name"]
            return mit
        if ohne is None:
            return mit
    if frei <= 0 and (ohne is None or not ohne.kaufen):
        # Auftrag 024, 5.2 (231200 32:20, 4488 Gold, fuenf fertige Items und ein Kontroll-Auge: "Nichts zu kaufen: alle
        # sechs Plaetze voll"): das Kontroll-Auge im Inventar wird gestellt, dann ist der Platz frei. Ein fertiges
        # Item verkauft der Coach nicht (test_kaufplan.volles_inventar_kauft_nichts, Szenario 3715)
        if KONTROLLAUGE in items:
            rest = list(items)
            rest.remove(KONTROLLAUGE)
            mit = _erster(reihe, tuple(rest), gold, frei + 1, stiefel_fehlt)
            if mit is not None and mit.kaufen == [mit.item]:      # nur fuer ein fertiges Item, nie fuer Bauteile
                mit.verkaufen = it[KONTROLLAUGE]["name"]
                return mit
    return ohne


KONTROLLAUGE = 2055
