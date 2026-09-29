"""Auftrag 017, 0.2: wo die Zeit des Strategen hingeht - Prozessstart, Promptlaenge, erstes Token, Satzende, Pruefung.

    python werkzeuge/latenz_probe.py sammeln 2026-09-29_133448      # Prompts wie live (Stub, Nachspielen)
    python werkzeuge/latenz_probe.py messen [--n=12] [--kurz]         # echte Aufrufe ueber das Abo, nacheinander

`sammeln` legt die Prompts der Stratege-Anlaesse und Fragen ab (stratege_probe_017/prompts.json). `messen` schickt sie
einzeln, mit vorgehaltenem Prozess und Pause dazwischen (wie live), und schreibt je Aufruf: warm/kalt, Promptlaenge,
Start, erstes Token, erster ganzer Satz, Ende, Eingabe-Token.
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(HIER.parent))
AUS = HIER.parent / "stratege_probe_017"
PAUSE = [4.0]


def sammeln(stamm: str) -> Path:
    import fuehrmass
    import nachspielen as ns
    from lolcoach import stratege_live
    stub = stratege_live.AufzeichnungsStub()
    stratege_live.AufzeichnungsStub = lambda *a, **k: stub
    fragen = [(f["zeit"], f["text"], i) for i, f in enumerate(fuehrmass.fragen_aus_log(stamm))]
    ns.durchspielen(ns.pfad_zu(stamm), fragen=fragen, stratege="stub")
    AUS.mkdir(exist_ok=True)
    ziel = AUS / "prompts.json"
    ziel.write_text(json.dumps(stub.anfragen, ensure_ascii=False, indent=0), encoding="utf-8")
    return ziel


def messen(n: int = 12, kurz: bool = False, entwurf: bool = False) -> dict:
    from lolcoach import llm, stratege
    prompts = json.loads((AUS / "prompts.json").read_text(encoding="utf-8"))
    schritt = max(1, len(prompts) // n)
    auswahl = prompts[::schritt][:n]
    if kurz:
        from lolcoach.stratege_live import kurzer_prompt
        auswahl = [kurzer_prompt(p) for p in auswahl]
    if entwurf:
        from lolcoach.stratege_live import mit_entwurf
        auswahl = [mit_entwurf(p) for p in auswahl]
    llm.vorhalten("sonnet", stratege.STRATEGE_SYSTEM, "low")
    time.sleep(3.0)
    zeilen = []
    for p in auswahl:
        m: dict = {}
        t0 = time.monotonic()
        erster = [None]

        def satz(s: str) -> None:
            if erster[0] is None and s.rstrip().endswith((".", "!", "?")):
                erster[0] = time.monotonic() - t0
        try:
            text = llm.frage_strom(p, satz, system=stratege.STRATEGE_SYSTEM, modell="sonnet", timeout=30,
                                   aufwand="low", nachladen=True, messung=m)
        except Exception as e:
            text = f"FEHLER {e}"
        m.update(erster_satz_s=erster[0], ganz_s=time.monotonic() - t0, woerter=len(text.split()))
        zeilen.append(m)
        print(json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in m.items()}), flush=True)
        time.sleep(PAUSE[0])                     # live liegen Sekunden zwischen zwei Anlaessen: der Vorrat ist warm

    def med(k):
        w = sorted(x[k] for x in zeilen if x.get(k) is not None)
        return (round(statistics.median(w), 2), round(w[int(len(w) * 0.9) - 1 if len(w) > 1 else 0], 2)) if w else None
    zusammen = {k: med(k) for k in ("start_s", "erstes_token_s", "erster_satz_s", "ende_s", "prompt_zeichen",
                                    "eingabe_token")}
    zusammen["warm"] = sum(1 for x in zeilen if x.get("warm"))
    zusammen["n"] = len(zeilen)
    AUS.mkdir(exist_ok=True)
    (AUS / f"latenz_{'entwurf' if entwurf else 'kurz' if kurz else 'voll'}.json").write_text(json.dumps({"zusammen": zusammen, "aufrufe": zeilen},
                                                                            indent=1), encoding="utf-8")
    print("MEDIAN/P90", json.dumps(zusammen), flush=True)
    return zusammen


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opt = {a.split("=")[0]: (a.split("=")[1] if "=" in a else True) for a in sys.argv[1:] if a.startswith("--")}
    if args[0] == "sammeln":
        print(sammeln(args[1]))
    else:
        PAUSE[0] = float(opt.get("--pause", 4.0))
        messen(int(opt.get("--n", 12)), "--kurz" in opt, "--entwurf" in opt)
