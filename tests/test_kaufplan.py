"""Kaufplan folgt Carlos' echtem Build (Pruefung 27.09.c, R3): Befund-Lagen aus 164326 und 173159, volles Inventar,
kaufbar() mit seinen drei Regeln. Schnell (< 5 s), ohne Aufnahmen.

    python tests/test_kaufplan.py
"""
import random
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import ddragon, denker, kaufplan  # noqa: E402

IT = ddragon.items()
N = kaufplan._nach_name()
SCHMUCK = 3340     # Getarntes Auge


def inv(*namen) -> tuple[int, ...]:
    return tuple(N[n] for n in namen) + (SCHMUCK,)


def genannt(k) -> list[str]:
    return list(k.kaufen) + ([k.naechstes[0]] if k.naechstes else []) if k else []


def build_aus_den_aufnahmen():
    """wissen/build_carlos.toml: Axiombogen zuerst, beide Hydren EIN Schritt, Eklipse/Endloser Hunger EIN Schritt."""
    b = [[IT[i]["name"] for i in s] for s in kaufplan.carlos_build("Riven")]
    assert b[0] == ["Axiombogen"], b
    assert any({"Gefräßige Hydra", "Gottlose Hydra"} <= set(s) for s in b), b
    assert any({"Eklipse", "Endloser Hunger"} <= set(s) for s in b), b
    assert kaufplan.carlos_build("GibtEsNicht") == ()


def befund_164326_kein_caulfields():
    """164326 22-29 min: Axiombogen, Eklipse, Stiefel, Gefraessige Hydra (+ Riesenschwert) - der Coach sagte
    "Kauf Caulfields Kriegshammer"; Carlos baute Schutzengel. Und mit Riesenschwert bei vollem Inventar: Dorans weg,
    Stahlsiegel (so hat er es 29:15 gemacht)."""
    lage = inv("Dorans Klinge", "Axiombogen", "Eklipse", "Ionische Stiefel der Deutlichkeit", "Gefräßige Hydra")
    for gold in range(0, 4000, 50):
        k = kaufplan.plan("Riven", lage, gold)
        assert k is not None and k.item == "Schutzengel", (gold, k)
        assert not {"Caulfields Kriegshammer", "Langschwert", "Stiefel"} & set(genannt(k)), (gold, k)
    voll = inv("Dorans Klinge", "Axiombogen", "Eklipse", "Ionische Stiefel der Deutlichkeit", "Riesenschwert",
               "Gefräßige Hydra")
    k = kaufplan.plan("Riven", voll, 1580)
    assert k.item == "Schutzengel" and k.kaufen == ["Stahlsiegel"] and k.verkaufen == "Dorans Klinge", k


def volles_inventar_kauft_nichts():
    """164326 38:33: sechs fertige Items, der Coach sagte "Kauf Langschwert und Stiefel". Jetzt: kein Kauf (ausser
    Kontroll-Auge/Elixier) und kein Back-Grund - denker.kauf lohnt nicht, kauf_info gibt es nicht."""
    for lage in (inv("Tanz des Todes", "Axiombogen", "Eklipse", "Seryldas Bitterkeit", "Schutzengel", "Gefräßige Hydra"),
                 inv("Tanz des Todes", "Axiombogen", "Eklipse", "Ionische Stiefel der Deutlichkeit", "Schutzengel",
                     "Gefräßige Hydra"),
                 inv("Endloser Hunger", "Axiombogen", "Vampirisches Zepter", "Ionische Stiefel der Deutlichkeit",
                     "Gottlose Hydra", "Kontroll-Auge")):
        for gold in (0, 350, 1200, 3300, 6000):
            k = kaufplan.plan("Riven", lage, gold)
            erlaubt = {"Kontroll-Auge"} | {n for n in N if n.startswith("Elixier")}
            assert k is None or set(k.kaufen) <= erlaubt and (k.naechstes is None or k.naechstes[0] in erlaubt), (lage, gold, k)
            b = SimpleNamespace(kauf=k, gold=gold, ich=SimpleNamespace(champion_id="Riven", items=lage))
            assert denker.kauf(b, gold) == ("", False), (lage, gold)
            try:
                from lolcoach.kern.merkmale import kauf_info
            except Exception:       # Kern wird parallel bearbeitet - denker.kauf oben reicht dann
                continue
            ki = kauf_info(b)
            assert ki is None or not ki.lohnt, (lage, gold, ki)


def befund_173159_keine_spitzhacke_ausser_im_ziel():
    """173159 12-24 min: "Gold fuer Spitzhacke" zwoelf Minuten lang, Carlos hatte Zepter, Gottlose Hydra, dann
    Endlosen Hunger. Die Spitzhacke darf nur fallen, wenn sie ins Ziel-Item gehoert; keine zweite Hydra."""
    lagen = [inv("Dorans Klinge", "Axiombogen", "Kontroll-Auge", "Tiamat", "Ionische Stiefel der Deutlichkeit",
                 "Langschwert"),
             inv("Dorans Klinge", "Axiombogen", "Vampirisches Zepter", "Langschwert", "Ionische Stiefel der Deutlichkeit",
                 "Tiamat"),
             inv("Dorans Klinge", "Axiombogen", "Vampirisches Zepter", "Langschwert", "Ionische Stiefel der Deutlichkeit",
                 "Gottlose Hydra"),
             inv("Axiombogen", "Vampirisches Zepter", "Ionische Stiefel der Deutlichkeit", "Gottlose Hydra",
                 "Endloser Hunger")]
    for n, lage in enumerate(lagen):
        for gold in range(0, 3500, 50):
            k = kaufplan.plan("Riven", lage, gold)
            assert k is not None, (n, gold)
            ziel = N[k.item]
            if "Spitzhacke" in genannt(k):
                assert N["Spitzhacke"] in kaufplan._baum(ziel), (n, gold, k)
            if n < 2:
                assert kaufplan.gruppe(ziel) == "Hydra" and "Spitzhacke" not in genannt(k), (n, gold, k)   # Tiamat da
            if N["Gottlose Hydra"] in lage:
                assert k.item != "Gefräßige Hydra", (n, gold, k)
    # 16:10: Caulfields und Zepter wollen beide DAS eine Langschwert - zusammen 1600, nicht 1250
    k = kaufplan.plan("Riven", inv("Dorans Klinge", "Axiombogen", "Langschwert", "Ionische Stiefel der Deutlichkeit",
                                   "Tiamat"), 1518)
    assert k.kaufen == ["Caulfields Kriegshammer"] and k.kosten == 700, k
    # 16:16: Inventar voll, aber Caulfields verbraucht das Langschwert - kein "Verkauf Dorans" fuer 68 Gold
    k = kaufplan.plan("Riven", inv("Dorans Klinge", "Axiombogen", "Vampirisches Zepter", "Langschwert",
                                   "Ionische Stiefel der Deutlichkeit", "Tiamat"), 632)
    assert k.verkaufen is None and k.naechstes == ("Caulfields Kriegshammer", 68), k


def kaufbar_drei_regeln():
    """Soll 3: Platz frei oder eigene Bauteile verbraucht; nicht schon im Inventar; baut ins Ziel ein."""
    voll = inv("Tanz des Todes", "Axiombogen", "Eklipse", "Seryldas Bitterkeit", "Schutzengel", "Gefräßige Hydra")
    assert kaufplan.kaufbar("Langschwert", voll) == (False, "Inventar voll, und es verbraucht keine eigenen Bauteile")
    # Auftrag 018, 4: das Elixier liegt bis zum Trinken im Inventar (Spieldaten "consumed" = beim Benutzen; 183125
    # 36:47 ging es mit sechs Items nicht zu kaufen)
    assert not kaufplan.kaufbar("Elixier des Zorns", voll)[0]
    mit_teil = inv("Endloser Hunger", "Axiombogen", "Vampirisches Zepter", "Riesenschwert",
                   "Ionische Stiefel der Deutlichkeit", "Gottlose Hydra")
    assert kaufplan.kaufbar("Schutzengel", mit_teil) == (True, "")                 # verbraucht das Riesenschwert
    assert not kaufplan.kaufbar("Stahlsiegel", mit_teil, "Schutzengel")[0]        # braucht einen Platz
    mit_dorans = inv("Dorans Klinge", "Axiombogen", "Eklipse", "Ionische Stiefel der Deutlichkeit", "Riesenschwert",
                     "Gefräßige Hydra")
    assert kaufplan.kaufbar("Stahlsiegel", mit_dorans, "Schutzengel") == (True, "nach Verkauf von Dorans Klinge")
    # schon im Inventar
    assert not kaufplan.kaufbar("Axiombogen", inv("Axiombogen"))[0]
    assert kaufplan.kaufbar("Langschwert", inv("Langschwert"), "Tiamat")[0]      # Tiamat braucht zwei
    assert not kaufplan.kaufbar("Langschwert", inv("Langschwert"))[0]
    assert not kaufplan.kaufbar("Gefräßige Hydra", inv("Gottlose Hydra"))[0]     # nur eine Hydra
    assert not kaufplan.kaufbar("Stiefel", inv("Ionische Stiefel der Deutlichkeit"))[0]
    # baut ins Ziel ein
    assert not kaufplan.kaufbar("Spitzhacke", (), "Gefräßige Hydra")[0]
    assert kaufplan.kaufbar("Spitzhacke", (), "Eklipse")[0]
    assert kaufplan.kaufbar("Eklipse", (), "Eklipse")[0]
    assert not kaufplan.kaufbar("Caulfields Kriegshammer", (), "Schutzengel")[0]
    assert not kaufplan.kaufbar("Spitzhacke", inv("Der Brutalisierer", "Caulfields Kriegshammer"), "Axiombogen")[0]
    assert not kaufplan.kaufbar("Quatsch", ())[0]


def alles_genannte_ist_kaufbar():
    """Jede Lage: was der Plan nennt (kaufen und naechstes), besteht kaufbar() gegen sein Ziel-Item."""
    zufall = random.Random(5)
    schritte = [i for s in kaufplan.schritte("Riven") for i in s]
    teile = sorted({t for i in schritte for t in kaufplan._baum(i)} - {N["Stiefel"]})
    fertig = schritte + [N["Ionische Stiefel der Deutlichkeit"], N["Dorans Klinge"]]
    for _ in range(400):
        lage = tuple(zufall.sample(fertig, zufall.randint(0, 5)) + zufall.sample(teile, zufall.randint(0, 3)))[:6]
        lage = tuple(i for n, i in enumerate(lage) if not (kaufplan.gruppe(i) and any(
            kaufplan.gruppe(j) == kaufplan.gruppe(i) for j in lage[:n]))) + (SCHMUCK,)
        gold = zufall.randint(0, 4000)
        k = kaufplan.plan("Riven", lage, gold)
        if k is None:
            continue
        for name in genannt(k):
            ok, grund = kaufplan.kaufbar(name, lage, k.item)
            assert ok, (name, grund, [IT[i]["name"] for i in lage], gold, k)
        rest, summe = [i for i in lage if not k.verkaufen or IT[i]["name"] != k.verkaufen], 0
        for name in k.kaufen:           # der Reihe nach gekauft: jedes eigene Bauteil nur einmal
            summe += 300 if name == "Stiefel" else kaufplan._baum_kosten(N[name], rest)[0]
        assert summe == k.kosten <= gold, (summe, k, gold, [IT[i]["name"] for i in lage])


def lexikon_bleibt_rueckfall():
    """Ohne eigenen Build: der statische Plan aus dem Lexikon wie bisher."""
    kern = [i for i in kaufplan.kern("Garen") if "Boots" not in IT[i].get("tags", [])]
    k = kaufplan.plan("Garen", (), 5000)
    assert kern and k is not None and k.item == IT[kern[0]]["name"], (k, kern)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for test in (build_aus_den_aufnahmen, befund_164326_kein_caulfields, volles_inventar_kauft_nichts,
                 befund_173159_keine_spitzhacke_ausser_im_ziel, kaufbar_drei_regeln, alles_genannte_ist_kaufbar,
                 lexikon_bleibt_rueckfall):
        test()
        print(f"{test.__name__} OK")
