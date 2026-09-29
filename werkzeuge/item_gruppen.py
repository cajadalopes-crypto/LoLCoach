"""Auftrag 018, 4: einzigartige Item-Gruppen aus den Spieldaten nach `wissen/item_gruppen.json`.

Data Dragon kennt sie nicht; die Spieldaten schon: jedes Item hat `mItemGroups`, jede Gruppe `mMaxGroupOwnable`
(CommunityDragon, `items.cdtb.bin.json`). 183125 35:04: "Kauf Schwarzes Beil" zu Lord Dominiks Grüße - beide stehen in
`Items/ItemGroups/LastWhisper` (hoechstens 1). Gespeichert werden nur Gruppen mit Grenze und mindestens zwei
verschiedenen Items; Namen deutsch aus Data Dragon.

    python werkzeuge/item_gruppen.py
"""
from __future__ import annotations

import datetime
import json
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))
QUELLE = "https://raw.communitydragon.org/latest/game/items.cdtb.bin.json"
ZIEL = HIER.parent / "wissen" / "item_gruppen.json"


def main() -> None:
    from lolcoach import ddragon
    anfrage = urllib.request.Request(QUELLE, headers={"User-Agent": "LoLCoach"})    # ohne: 403
    with urllib.request.urlopen(anfrage, timeout=60) as r:
        d = json.loads(r.read().decode("utf-8"))
    grenzen = {k: v["mMaxGroupOwnable"] for k, v in d.items()
               if isinstance(v, dict) and v.get("__type") == "ItemGroup" and v.get("mMaxGroupOwnable")}
    namen = {int(i): v["name"] for i, v in ddragon.items().items() if v.get("maps", {}).get("11")}
    mitglieder = defaultdict(set)
    for v in d.values():
        if isinstance(v, dict) and isinstance(v.get("itemID"), int) and v["itemID"] in namen:
            for g in v.get("mItemGroups") or []:
                if g in grenzen:
                    mitglieder[g].add(v["itemID"])
    gruppen = {g.removeprefix("Items/ItemGroups/"): {"max": grenzen[g], "items": sorted(ids),
                                                     "namen": [namen[i] for i in sorted(ids)]}
               for g, ids in sorted(mitglieder.items()) if len(ids) >= 2}
    ZIEL.write_text(json.dumps({"quelle": QUELLE, "stand": datetime.date.today().isoformat(),
                                "ddragon": ddragon.version(),
                                "gruppen": gruppen}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(gruppen), "Gruppen ->", ZIEL)


if __name__ == "__main__":
    main()
