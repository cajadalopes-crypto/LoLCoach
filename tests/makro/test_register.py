"""Register, Rechnung, Regeln und Vorrang (Auftrag 032).

- genau die 111 Nummern aus Buch 17, Teil B;
- jede Rechnung zeigt auf etwas, das es gibt (Rechner-Funktion, Regel mit Quelle und Datum, Feld des Gehirns);
- jede Entscheidung mit Grundlage R hat eine Regel mit Quelle;
- Vorrang: Gefahr vor Objective vor dem Rest, innerhalb nach Wert.
    python tests/makro/test_register.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lolcoach.makro import rechner, regeln, vorrang  # noqa: E402
from lolcoach.makro.entscheidungen import laden  # noqa: E402
from lolcoach.makro.kommando import Kommando  # noqa: E402

TEIL_B = {"S": 14, "J": 14, "W": 14, "B": 9, "T": 9, "R": 10, "O": 12, "K": 7, "M": 10, "V": 5, "P": 4, "Z": 3}
HIRN_FELDER = {"jungler", "gefahr", "wert", "siegchance", "ketten", "back", "ziel", "umwandlung", "rotation", "tausch",
               "klarheit", "policy"}


def rechnung_gueltig(eintrag: str) -> str | None:
    art, _, name = eintrag.partition(":")
    if art == "Re":
        return None if callable(getattr(rechner, name, None)) else f"Rechner {name} fehlt"
    if art == "R":
        try:
            r = regeln.regel(name)
        except KeyError:
            return f"Regel {name} fehlt"
        q = regeln.quellen()
        if not r.get("quelle") or any(x not in q for x in r["quelle"]):
            return f"Regel {name}: Quelle fehlt"
        if any(not q[x].get("datum") or not q[x].get("abgerufen") for x in r["quelle"]):
            return f"Regel {name}: Quelle ohne Datum"
        return None
    if art == "D":
        return None if name in HIRN_FELDER else f"Gehirn-Feld {name} unbekannt"
    return f"unbekannte Rechnung {eintrag}"


def test_111():
    reg = laden()
    assert len(reg) == 111, len(reg)
    for k, n in TEIL_B.items():
        ids = sorted(int(i[1:]) for i in reg if i[0] == k)
        assert ids == list(range(1, n + 1)), (k, ids)


def test_rechnung():
    for id_, e in laden().items():
        assert e.rechnung, id_
        for r in e.rechnung:
            f = rechnung_gueltig(r)
            assert f is None, (id_, f)


def test_r_hat_regel():
    for id_, e in laden().items():
        if "R" in e.grundlage.split(","):
            assert any(r.startswith("R:") for r in e.rechnung), id_


def test_regeln_quellen():
    for nr, r in regeln.alle_regeln().items():
        assert r.get("quelle"), nr
        assert rechnung_gueltig(f"R:{nr}") is None, nr


def test_vorrang():
    ks = [Kommando("W4", "a", "b", klasse="rest", wert=9), Kommando("O7", "a", "b", klasse="objective", wert=1),
          Kommando("J4", "a", "b", klasse="gefahr", wert=1), Kommando("O1", "a", "b", klasse="objective", wert=5),
          Kommando("B4", "a", "b", klasse="gefahr", wert=4)]
    assert [k.id for k in vorrang.ordnen(ks)] == ["B4", "J4", "O1", "O7", "W4"]
    assert vorrang.erstes([]) is None


def main() -> int:
    rot = 0
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            try:
                f()
                print(f"OK  {n}")
            except AssertionError as e:
                rot += 1
                print(f"ROT {n}: {e}")
    return 1 if rot else 0


if __name__ == "__main__":
    sys.exit(main())
