"""Jede Testfunktion einzeln (Auftrag 034): in der Cloud fehlen daten/ (Data Dragon, Aufnahmen) und Windows - dort
bricht `tests/alle.py` beim ersten fehlenden Stueck ab und verdeckt, was danach noch laeuft. Dieses Werkzeug fuehrt
jede Funktion aus der `__main__`-Liste einer Testdatei in einem eigenen Prozess aus und sagt je Funktion OK oder
FEHLER (mit der letzten Zeile der Meldung). Mit `--basis DATEI` vergleicht es mit einem frueheren Lauf: neu rot ist
nur, was dort gruen war.

    python tests/einzeln.py                          # alle Dateien aus tests/alle.py
    python tests/einzeln.py test_kern                # nur eine
    python tests/einzeln.py --basis vorher.txt       # nur Abweichungen zum frueheren Lauf zaehlen
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER))
from alle import TESTS  # noqa: E402

def funktionen(datei: Path) -> list[str]:
    """Die Funktionen, die der `__main__`-Block aufruft (Tupel in einer for-Schleife oder einzelne Aufrufe)."""
    baum = ast.parse(datei.read_text(encoding="utf-8-sig"))
    defs = {k.name for k in baum.body if isinstance(k, ast.FunctionDef)}
    namen: list[str] = []
    for knoten in baum.body:
        if isinstance(knoten, ast.If) and "__main__" in ast.unparse(knoten.test):
            for k in ast.walk(knoten):
                if isinstance(k, ast.For) and isinstance(k.iter, ast.Tuple):
                    namen += [e.id for e in k.iter.elts if isinstance(e, ast.Name)]
                elif isinstance(k, ast.Call) and isinstance(k.func, ast.Name) and not k.args:
                    namen.append(k.func.id)
    return [n for n in dict.fromkeys(namen) if n in defs]


def lauf(datei: Path, fn: str) -> tuple[str, str]:
    code = (f"import sys; sys.path.insert(0, {str(datei.parent)!r}); sys.argv = [{str(datei)!r}]; "
            f"import runpy; g = runpy.run_path({str(datei)!r}, run_name='einzeln'); g[{fn!r}]()")
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=600)
    if p.returncode == 0:
        return "OK", ""
    aus = (p.stdout + p.stderr)[-1500:]
    return "FEHLER", aus


def basis_lesen(pfad: str) -> dict[str, str]:
    out = {}
    for z in Path(pfad).read_text(encoding="utf-8").splitlines():
        teile = z.split()
        if len(teile) == 2 and teile[0] in ("OK", "FEHLER"):
            out[teile[1]] = teile[0]
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    basis = None
    if "--basis" in args:
        i = args.index("--basis")
        basis = basis_lesen(args[i + 1])
        del args[i:i + 2]
    zahl = {"OK": 0, "FEHLER": 0}
    neu_rot, neu_gruen = [], []
    for name in args or TESTS:
        datei = HIER / f"{name}.py"
        for fn in funktionen(datei):
            st, aus = lauf(datei, fn)
            zahl[st] += 1
            print(f"{st:6} {name}.{fn}", flush=True)
            if st == "FEHLER" and aus.strip():
                print("   " + aus.strip().splitlines()[-1][:300])
            if basis is not None:
                vorher = basis.get(f"{name}.{fn}")
                if st == "FEHLER" and vorher != "FEHLER":
                    neu_rot.append(f"{name}.{fn}")
                elif st == "OK" and vorher == "FEHLER":
                    neu_gruen.append(f"{name}.{fn}")
    print(zahl)
    if basis is not None:
        print(f"neu rot: {neu_rot or 'keine'}")
        print(f"neu gruen: {neu_gruen or 'keine'}")
        sys.exit(1 if neu_rot else 0)
