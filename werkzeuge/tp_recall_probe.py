"""Auftrag 033: TP-Spruenge und Recalls der Gegner, wie das Lagebild sie aus der Minimap liest - nachgespielt.

Nur Sehen (Buch 17): Carlos' Aufnahmen liefern die Bilder und die Live-API als Wahrheit dafuer, ob ein Gegner wirklich
zurueck war (neue Items beim naechsten Sehen) - kein Entscheidungswissen.

    python werkzeuge/tp_recall_probe.py [stamm ...]     -> buecher/challenger/sehen/tp_recall.json

Je Partie:
  tp      jeder gemeldete Fernsprung (lage.Lagebild.fernspruenge): Spielzeit, Champion, Art (TP/Ult), Ort vorher/nachher
  recall  jeder erkannte Recall (Lagebild._recall: nach 7 s Stillstand verschwunden) und ob die Live-API danach neue
          Items zeigt oder der Gegner als Naechstes in seiner Basis auftaucht (= wirklich zurueck)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL))
sys.stdout.reconfigure(encoding="utf-8")
from lolcoach import aufzeichnung, lage, minimap, zustand  # noqa: E402

A = WURZEL / "aufnahmen"
ABLAGE = WURZEL / "buecher" / "challenger" / "sehen"


def _items(p, name: str) -> tuple:
    for s in p.spieler:
        if s.name == name:
            return tuple(sorted(getattr(s, "items", ()) or ()))
    return ()


def lauf(stamm: str) -> dict:
    pfad = next((A / f"{stamm}{e}" for e in (".jsonl.gz", ".jsonl.xz") if (A / f"{stamm}{e}").exists()), None)
    ordner = A / f"{stamm}_bilder"
    # lage.sicht_fuer kennt nur .jsonl.gz - bei .jsonl.xz fand es den Bilderordner nicht (alle Partien bis 29.09.)
    sicht = lage.SichtAusProtokoll(ordner) if (ordner / "sichtungen.jsonl.gz").exists() else lage.sicht_fuer(pfad)
    if sicht is None:
        return {"stamm": stamm, "tp": [], "recall": [], "fehlt": "keine Sichtungen"}
    lb = lage.Lagebild()
    tp, recalls = [], []
    gemeldet_tp = 0
    offen: dict[str, dict] = {}       # Gegner -> Recall, der auf das naechste Sehen wartet
    bekannt: set[tuple[str, float]] = set()
    p = None
    for w, d in aufzeichnung.lies_mit_zeit(pfad):
        p = zustand.partie(d, None)
        if p is None or not p.spieler:
            continue
        lb.tod_merken(p)
        for wb, s in sicht.zwischen(w, lage.champions(p)):
            lb.neu(p.zeit - (w - wb), s, p)
        for t in lb.fernspruenge[gemeldet_tp:]:
            vor = lb.verlauf.get(next((k for k in lb.verlauf if k[0] == t.name), None)) or []
            tp.append({"zeit": round(t.seit), "wer": t.name, "champion": t.champion, "art": t.zauber,
                       "wand": round(w - (p.zeit - t.seit), 2),
                       "wege": [(round(z, 1), round(x, 3), round(y, 3)) for z, x, y in list(vor)[-12:]]})
        gemeldet_tp = len(lb.fernspruenge)
        for name, t0 in list(lb._recall.items()):
            if (name, t0) in bekannt:
                continue
            bekannt.add((name, t0))
            offen[name] = {"wer": name, "zeit": round(t0), "items_vorher": _items(p, name)}
        # naechstes Sehen eines Gegners mit offenem Recall
        for name, r in list(offen.items()):
            g = next(((z, x, y) for (n, _t), (z, x, y) in lb.zuletzt.items() if n == name), None)
            if g and g[0] > r["zeit"] + 3:
                sp = next((x for x in p.spieler if x.name == name), None)
                r["naechst_zeit"] = round(g[0])
                r["naechst_ort"] = minimap.ort(g[1], g[2])
                r["items_nachher"] = _items(p, name)
                r["neue_items"] = r["items_nachher"] != r["items_vorher"]
                r["basis"] = "Basis" in r["naechst_ort"] or "Brunnen" in r["naechst_ort"]
                recalls.append(r)
                del offen[name]
    for r in recalls:
        r["items_vorher"], r["items_nachher"] = list(r["items_vorher"]), list(r["items_nachher"])
    return {"stamm": stamm, "tp": tp, "recall": recalls}


if __name__ == "__main__":
    staemme = sys.argv[1:]
    out = [lauf(s) for s in staemme]
    ABLAGE.mkdir(parents=True, exist_ok=True)
    (ABLAGE / "tp_recall.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for r in out:
        rc = r["recall"]
        print(r["stamm"], "TP", len(r["tp"]), "Recall", len(rc), "bestaetigt (Items/Basis)",
              sum(1 for x in rc if x.get("neue_items") or x.get("basis")))
