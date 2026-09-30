"""Auftrag 035, Teil 0: Reihenfolge nach dem Aktionswert des Gehirns (Gefahr vorn, Ersatz fester Wert) und die Tafel
Kommando -> Aktion des Gehirns (makro/aktionen.py), die auch die Challenger-Treue (Teil 2) benutzt.

    python tests/makro/test_vorrang.py
"""
from __future__ import annotations

import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(HIER.parents[1]))

from faelle import FAELLE  # noqa: E402
from lolcoach.makro import aktionen, vorrang  # noqa: E402
from lolcoach.makro.entscheidungen import laden  # noqa: E402
from lolcoach.makro.kommando import Kommando  # noqa: E402
from lolcoach.makro.lage import Hirn  # noqa: E402

AKTIONEN = {"Back", "Objective", "TP", "Rotation", "Split", "Gruppe", "Jungle", "Lane", "Warten", "Unterwegs"}


def tafel_vollstaendig():
    """Jede der 111 Entscheidungen steht in der Tafel (mit Aktion oder bewusst ohne), jede feuernde Lage ergibt eine
    gueltige Aktion oder None."""
    reg = laden()
    fehlt = [i for i in reg if i not in aktionen.FEST]
    assert not fehlt, fehlt
    mit = 0
    for i, (feuert, _) in FAELLE.items():
        k = reg[i].pruefe(feuert())
        a = aktionen.aktion(k)
        if a is not None:
            mit += 1
            assert a[0] in AKTIONEN, (i, a)
    assert mit >= 70, mit


def hoerbar_positiv():
    """Jede der 111 Anweisungen ist fuer den Messer aus 027 (herzschlag.positiv) eine positive Anweisung - keine sagt
    nur, was man NICHT tun soll (sonst zaehlte sie als Luecke und "Negativ allein")."""
    from types import SimpleNamespace as NS
    from lolcoach.kern.herzschlag import negativ_allein, positiv
    reg = laden()
    schlecht = []
    for i, (feuert, _) in FAELLE.items():
        k = reg[i].pruefe(feuert())
        if not positiv(NS(schluessel=f"kern:MAKRO_{i}", text=k.text)) or negativ_allein(k.text):
            schlecht.append((i, k.text))
    assert not schlecht, schlecht


def plan_arten():
    """Jede Anweisung hat eine Plan-Art (fuer Szenarien und Nachspiele mit --kern makro, werkzeuge/nachspielen.py)."""
    from lolcoach.kern import handlung
    alte = set(handlung.VOR) | set(handlung.ZURUECK) | set(handlung.STUMM) | {
        "BACK_JETZT", "WELLE_REIN_UND_BACK", "KAUFEN", "STAPELN", "WELLE_HALTEN", "UNTER_TURM_FARMEN", "ZUR_GRUPPE",
        "TP_SPIEL", "SEITENWELLE", "WOHIN_TP_LANE", "WELLE_KLAEREN", "VORBEREITEN_OBJECTIVE", "WOHIN",
        "WELLE_DRUECKEN", "TAUSCHEN", "ABGEBEN_TAUSCHEN", "HALTEN_UNTER_TURM", "HILFE", "SICHT", "INFO"}
    reg = laden()
    for i, (feuert, _) in FAELLE.items():
        art = aktionen.plan_art(reg[i].pruefe(feuert()))
        assert art in alte, (i, art)
    assert aktionen.plan_art(Kommando("O1", "Gib den Drachen", "3 gegen 5")) == "ABGEBEN_TAUSCHEN"
    assert aktionen.plan_art(Kommando("W3", "Welle ist drin: jetzt Back", "x")) == "WELLE_REIN_UND_BACK"
    assert aktionen.plan_art(Kommando("G0", "Bleib an deiner Top-Welle", "x")) == "FARMEN"


def richtung():
    assert aktionen.aktion(Kommando("O1", "Drache bestreiten", "4 gegen 4")) == ("Objective", "Drache")
    assert aktionen.aktion(Kommando("O1", "Gib den Drachen", "3 gegen 5")) == ("Lane", "")
    assert aktionen.aktion(Kommando("B3", "Noch nicht back", "er ist tot")) == ("Lane", "")
    assert aktionen.aktion(Kommando("T8", "Kein TP", "zu spaet")) == ("Lane", "")
    assert aktionen.aktion(Kommando("R1", "Über den Fluss Mid", "Brand ohne Flash")) == ("Rotation", "mid")
    assert aktionen.aktion(Kommando("W13", "Lass die Welle und geh", "der Baron ist in 20 s")) == ("Objective", "Baron")
    assert aktionen.aktion(Kommando("Z3", "Nimm Camps", "unklar")) == ("Jungle", "")
    assert aktionen.aktion(Kommando("S1", "Trinket in den Fluss-Busch", "er kommt")) is None


def reihenfolge():
    hirn = Hirn(optionen=[("Lane", "", 0.6, 0.5, 0.05, "klar", []), ("Objective", "Drache", -0.5, 0.2, 0.1, "klar", []),
                          ("Back", "", 0.1, 0.2, 0.05, "klar", [])])
    obj = Kommando("W13", "Lass die Welle und geh", "der Drache ist in 20 s", klasse="objective", wert=2.0)
    lane = Kommando("W1", "Freeze an deinem Turm", "er ist allein vorn")
    ward = Kommando("S8", "Ward den Eingang", "Drache in 75 s", klasse="objective", wert=1.0)
    gefahr = Kommando("J14", "Raus hinter den Turm", "drei kommen", klasse="gefahr", wert=3.0)
    ks = [obj, lane, ward, gefahr]
    assert [k.id for k in vorrang.ordnen(ks, hirn, "fest")] == ["J14", "W13", "S8", "W1"]
    # wert: Gefahr vorn; Lane +0,6 vor Ward (fester Wert 1,0 als Ersatz? nein: 1,0 > 0,6) - der Ersatz zaehlt
    assert [k.id for k in vorrang.ordnen(ks, hirn, "wert")] == ["J14", "S8", "W1", "W13"]
    assert vorrang.effektiv(obj, hirn) == -0.5 and vorrang.effektiv(ward, hirn) == 1.0
    # ohne Gehirn: der feste Wert ueberall
    assert [k.id for k in vorrang.ordnen(ks, None, "wert")] == ["J14", "W13", "S8", "W1"]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for t in (tafel_vollstaendig, hoerbar_positiv, plan_arten, richtung, reihenfolge):
        t()
        print(f"{t.__name__} OK")
