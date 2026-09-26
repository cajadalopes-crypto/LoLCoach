"""Macht aus einer Aufnahme einen schlanken Testfall fuer tests/.

Wirft weg, was kein Code liest (Beschreibungstexte, Runen, Faehigkeiten),
und behaelt jede Sekunde - Regeln reagieren auf Wechsel von Sekunde zu Sekunde.

    python werkzeuge/testfall_aus_aufnahme.py aufnahmen/<datei>.jsonl.gz tests/<name>.jsonl.gz
"""
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import aufzeichnung  # noqa: E402

ITEM_FELDER = ("itemID", "displayName", "price", "consumable", "count", "slot")
AKTIV_FELDER = ("riotId", "riotIdGameName", "summonerName", "currentGold", "level", "championStats", "error")


def schlank(d: dict) -> dict:
    d = dict(d)
    if "activePlayer" in d:
        d["activePlayer"] = {k: v for k, v in d["activePlayer"].items() if k in AKTIV_FELDER}
    spieler = []
    for s in d.get("allPlayers", []):
        s = {k: v for k, v in s.items() if k not in ("runes", "rawSkinName", "skinName")}
        s["items"] = [{k: i[k] for k in ITEM_FELDER if k in i} for i in s.get("items", [])]
        s["summonerSpells"] = {k: {"displayName": z.get("displayName"), "rawDisplayName": z.get("rawDisplayName")}
                               for k, z in (s.get("summonerSpells") or {}).items()}
        spieler.append(s)
    d["allPlayers"] = spieler
    return d


def main(quelle: str, ziel: str) -> None:
    with gzip.open(ziel, "wt", encoding="utf-8") as f:
        for w, d in aufzeichnung.lies_mit_zeit(quelle):
            f.write(json.dumps({"w": w, "d": schlank(d)}, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(ziel, Path(ziel).stat().st_size // 1024, "KB")
    # Minimap: nur die Sichtungen (sichtungen.json), nicht die Bilder
    cache = aufzeichnung.bilder(quelle)[0][1].parent / "sichtungen.json" if aufzeichnung.bilder(quelle) else None
    if cache and cache.exists():
        ordner = Path(ziel).with_name(Path(ziel).name.removesuffix(".jsonl.gz") + "_bilder")
        ordner.mkdir(exist_ok=True)
        (ordner / "sichtungen.json").write_bytes(cache.read_bytes())
        print(ordner / "sichtungen.json", cache.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main(*sys.argv[1:3])
