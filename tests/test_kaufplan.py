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
    """Was der Plan fuer sein ERSTES Ziel nennt (die Auffuellung fuer weitere Ziele steht in k.weitere)."""
    if not k:
        return []
    n = sum(len(s) for _, s in k.weitere)
    return list(k.kaufen[:len(k.kaufen) - n]) + ([k.naechstes[0]] if k.naechstes else [])


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
        # Auftrag 027, 2: das Langschwert im Stahlsiegel ist ein Schutzengel-Bauteil - es darf jetzt kommen
        assert not {"Caulfields Kriegshammer", "Stiefel"} & set(genannt(k)), (gold, k)
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
            if k is not None and k.verkaufen == "Kontroll-Auge":
                # Auftrag 024, 5.2 (231200 32:20): Auge stellen, dann ein FERTIGES Item - nie Bauteile dafuer
                assert k.kaufen == [k.item] and gold >= k.kosten, (lage, gold, k)
                continue
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
            for z, stuecke in k.weitere:             # Auftrag 027, 2: auch in der Auffuellung nur fuer ihr Ziel
                assert "Spitzhacke" not in stuecke or N["Spitzhacke"] in kaufplan._baum(N[z]), (n, gold, k)
            if n < 2:
                assert kaufplan.gruppe(ziel) == "Hydra" and "Spitzhacke" not in genannt(k), (n, gold, k)   # Tiamat da
            if N["Gottlose Hydra"] in lage:
                assert k.item != "Gefräßige Hydra", (n, gold, k)
    # 16:10: Caulfields und Zepter wollen beide DAS eine Langschwert - zusammen 1600, nicht 1250
    k = kaufplan.plan("Riven", inv("Dorans Klinge", "Axiombogen", "Langschwert", "Ionische Stiefel der Deutlichkeit",
                                   "Tiamat"), 1518)
    # Auftrag 027, 2: der Rest (818) kauft das zweite Langschwert fuers Zepter - das eigene verbraucht Caulfields
    assert k.kaufen == ["Caulfields Kriegshammer", "Langschwert"] and k.kosten == 1050, k
    # 16:16: Inventar voll, aber Caulfields verbraucht das Langschwert - kein "Verkauf Dorans" fuer 68 Gold
    k = kaufplan.plan("Riven", inv("Dorans Klinge", "Axiombogen", "Vampirisches Zepter", "Langschwert",
                                   "Ionische Stiefel der Deutlichkeit", "Tiamat"), 632)
    assert k.verkaufen is None and k.naechstes == ("Caulfields Kriegshammer", 68), k


def kaufbar_drei_regeln():
    """Soll 3: Platz frei oder eigene Bauteile verbraucht; nicht schon im Inventar; baut ins Ziel ein."""
    voll = inv("Tanz des Todes", "Axiombogen", "Eklipse", "Seryldas Bitterkeit", "Schutzengel", "Gefräßige Hydra")
    assert kaufplan.kaufbar("Langschwert", voll) == (False, "Inventar voll, und es verbraucht keine eigenen Bauteile")
    # Auftrag 028, 6.2 (loest 018, 4 ab): ein Elixier nur mit sechs fertigen Items - dann ja, vorher nie
    assert kaufplan.kaufbar("Elixier des Zorns", voll)[0]
    assert not kaufplan.kaufbar("Elixier des Zorns", voll[:5])[0]
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


def preis(i: int, rest: list) -> int:
    """Was der Kauf von `i` kostet, wenn eigene Bauteile in `rest` verschmelzen (sie werden aus `rest` genommen)."""
    c = IT[i]["gold"]["total"]
    for f in IT[i].get("from") or []:
        c -= IT[int(f)]["gold"]["total"] - kaufplan._baum_kosten(int(f), rest)[0]
    return c


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
        # Auftrag 027, 2: die Auffuellung - jedes Stueck kaufbar fuer SEIN Ziel, im Inventar nach dem Kauf davor
        danach = kaufplan._nach_kauf(tuple(i for i in lage if not k.verkaufen or IT[i]["name"] != k.verkaufen),
                                     genannt(k))
        for ziel, stuecke in k.weitere:
            for name in stuecke:
                ok, grund = kaufplan.kaufbar(name, danach, ziel)
                assert ok, (name, ziel, grund, [IT[i]["name"] for i in lage], gold, k)
            danach = kaufplan._nach_kauf(danach, stuecke)
        rest, summe = [i for i in lage if not k.verkaufen or IT[i]["name"] != k.verkaufen], 0
        for name in k.kaufen:           # der Reihe nach gekauft: jedes eigene Bauteil nur einmal
            summe += 300 if name == "Stiefel" else preis(N[name], rest)
            rest.append(N[name])         # 027: die Auffuellung baut auf dem Gekauften auf (Stiefel -> Ionische)
        assert summe == k.kosten <= gold, (summe, k, gold, [IT[i]["name"] for i in lage])


def auftrag_027_alles_gold():
    """091311: 19:52 mit 1792 Gold hiess es "Kauf Tiamat" (592 blieben), 20:09 standen 1800 Gold ungenutzt, 10:33
    blieben die einfachen Stiefel liegen; Traenke gehen vor Dorans."""
    k = kaufplan.plan("Riven", inv("Eklipse", "Ionische Stiefel der Deutlichkeit", "Axiombogen"), 1792)
    assert k.kaufen == ["Tiamat", "Langschwert"] and k.kosten == 1550, k
    k = kaufplan.plan("Riven", inv("Dorans Klinge", "Heiltrank", "Stiefel", "Axiombogen"), 729)
    assert k.kaufen == ["Ionische Stiefel der Deutlichkeit"], k
    k = kaufplan.plan("Riven", inv("Langschwert", "Ionische Stiefel der Deutlichkeit", "Axiombogen", "Spitzhacke",
                                   "Caulfields Kriegshammer"), 2228)
    assert k.kaufen[0] == "Eklipse" and k.weitere and 2228 - k.kosten < 300, k
    assert kaufplan._start_item(inv("Dorans Klinge", "Heiltrank")) == N["Heiltrank"]


def lexikon_bleibt_rueckfall():
    """Ohne eigenen Build: der statische Plan aus dem Lexikon wie bisher."""
    kern = [i for i in kaufplan.kern("Garen") if "Boots" not in IT[i].get("tags", [])]
    k = kaufplan.plan("Garen", (), 5000)
    assert kern and k is not None and k.item == IT[kern[0]]["name"], (k, kern)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for test in (build_aus_den_aufnahmen, befund_164326_kein_caulfields, volles_inventar_kauft_nichts,
                 befund_173159_keine_spitzhacke_ausser_im_ziel, kaufbar_drei_regeln, alles_genannte_ist_kaufbar,
                 auftrag_027_alles_gold, lexikon_bleibt_rueckfall):
        test()
        print(f"{test.__name__} OK")
