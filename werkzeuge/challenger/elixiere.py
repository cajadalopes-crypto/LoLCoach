"""Auftrag 033 (Rest 3 aus 028): Wann kaufen High-Elo-Spieler Elixiere? Aus den Timelines (daten/riot/timelines).

Je Elixier-Kauf: Spielminute, fertige Items (kaufplan.fertige, Stiefel der zweiten Stufe zaehlen) und freie Plaetze
im Moment des Kaufs - das Inventar wird aus ITEM_PURCHASED / _SOLD / _DESTROYED / _UNDO nachgebaut. Dazu, wie viele
Spieler ueberhaupt Elixiere kaufen.

    python werkzeuge/challenger/elixiere.py [max_partien]   -> buecher/challenger/elixiere.json
"""
from __future__ import annotations

import gzip
import json
import sys
from collections import Counter
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL))
sys.stdout.reconfigure(encoding="utf-8")
from lolcoach import ddragon, kaufplan  # noqa: E402

TL = WURZEL / "daten" / "riot" / "timelines"


def elixier_ids() -> set[int]:
    return {i for i, d in ddragon.items().items() if "Elixier" in d.get("name", "") or "Elixir" in d.get("name", "")}


def partie(pfad: Path, elix: set[int]) -> tuple[list[dict], int]:
    d = json.load(gzip.open(pfad, "rt", encoding="utf-8"))
    inv: dict[int, list[int]] = {}
    kaeufe, kaeufer = [], set()
    level: dict[int, int] = {}
    for f in d["info"]["frames"]:
        for pid_s, pf in (f.get("participantFrames") or {}).items():
            level[int(pid_s)] = pf.get("level", 0)
        for e in f["events"]:
            t, pid = e["type"], e.get("participantId")
            if not pid:
                continue
            liste = inv.setdefault(pid, [])
            if t == "ITEM_PURCHASED":
                i = e["itemId"]
                if i in elix:
                    belegt = kaufplan._belegt(liste)
                    kaeufe.append({"min": round(e["timestamp"] / 60000, 1), "fertige": kaufplan.fertige(liste),
                                   "level": level.get(pid, 0),
                                   "frei": kaufplan.PLAETZE - belegt})
                    kaeufer.add(pid)
                    continue                  # getrunken, belegt keinen Platz
                # Bauteile verschmelzen: das neue Item verbraucht seine Teile aus dem Inventar
                for teil in ddragon.items().get(i, {}).get("from") or []:
                    kaufplan._baum_kosten(int(teil), liste)
                liste.append(i)
            elif t in ("ITEM_SOLD", "ITEM_DESTROYED"):
                if e["itemId"] in liste:
                    liste.remove(e["itemId"])
            elif t == "ITEM_UNDO":
                if e.get("beforeId") in liste:
                    liste.remove(e["beforeId"])
                if e.get("afterId"):
                    liste.append(e["afterId"])
    return kaeufe, len(kaeufer)


def main(n: int) -> dict:
    elix = elixier_ids()
    kaeufe, kaeufer, spieler = [], 0, 0
    for k, p in enumerate(sorted(TL.glob("*.json.gz"))[:n]):
        try:
            ka, kf = partie(p, elix)
        except (OSError, ValueError, KeyError):
            continue
        kaeufe += ka
        kaeufer += kf
        spieler += 10
    fertig = Counter(min(x["fertige"], 6) for x in kaeufe)
    frei = Counter(x["frei"] for x in kaeufe)
    minuten = sorted(x["min"] for x in kaeufe)
    q = lambda a: minuten[int(a * (len(minuten) - 1))] if minuten else None
    aus = {"partien": spieler // 10, "spieler": spieler, "kaeufer": kaeufer, "kaeufe": len(kaeufe),
           "anteil_kaeufer": round(kaeufer / max(1, spieler), 3),
           "minute_p10_p50_p90": [q(0.1), q(0.5), q(0.9)],
           "level_p10_p50_p90": [sorted(x["level"] for x in kaeufe)[int(a * (len(kaeufe) - 1))] for a in (0.1, 0.5, 0.9)]
           if kaeufe else None,
           "fertige_items": {str(k): v for k, v in sorted(fertig.items())},
           "freie_plaetze": {str(k): v for k, v in sorted(frei.items())},
           "anteil_ab_5_fertig": round(sum(v for k, v in fertig.items() if k >= 5) / max(1, len(kaeufe)), 3),
           "anteil_ab_5_fertig_und_frei": round(sum(1 for x in kaeufe if x["fertige"] >= 5 and x["frei"] >= 1)
                                                / max(1, len(kaeufe)), 3),
           "elixier_ids": sorted(elix)}
    (WURZEL / "buecher" / "challenger" / "elixiere.json").write_text(json.dumps(aus, indent=1), encoding="utf-8")
    return aus


if __name__ == "__main__":
    print(json.dumps(main(int(sys.argv[1]) if len(sys.argv) > 1 else 3000), indent=1))
