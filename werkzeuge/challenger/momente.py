"""Auftrag 029, Schritt 4: eine Partie, zehn Entscheidungsmomente - Faktenblatt fuer den Top-Laner.

    python werkzeuge/challenger/momente.py [MATCH_ID]     -> buecher/challenger/momente_roh.md

Ohne ID: die erste gueltige Partie mit Top-Laner (TP, Siegerteam, Challenger), 27-33 min, alle vier Monsterarten.
Die Lage enthaelt nur, was der Spieler wissen kann (kein Maphack):
  - eigenes Team: Positionen (Minimap), Leben/Level, tot/lebendig;
  - Scoreboard: Kills, Level, CS und Items ALLER Spieler, wer tot ist (mit Restzeit);
  - allen angesagte Ereignisse: Kills (mit Ort), Tuerme, Platten, Monster;
  - Gegner-Orte nur als "zuletzt gesehen" an einem angesagten Ereignis.
Markierung: [B] beobachtet (Minute oder Ereignis), [G] geschaetzt (abgeleitet/interpoliert), [U] unbekannt.
"""
from __future__ import annotations

import json
import sys
from collections import Counter

import ableitungen as abl
import grundlage as g
from grundlage import abstand, bereich, gegner, uhr

WO = {"basis_blau": "Basis Blau", "basis_rot": "Basis Rot", "top": "Toplane", "mid": "Midlane", "bot": "Botlane",
      "fluss_oben": "oberer Fluss", "fluss_unten": "unterer Fluss", "jungle_blau_oben": "blauer Jungle oben",
      "jungle_blau_unten": "blauer Jungle unten", "jungle_rot_oben": "roter Jungle oben",
      "jungle_rot_unten": "roter Jungle unten"}
MONSTER = {"HORDE": "Larven", "RIFTHERALD": "Herold", "BARON_NASHOR": "Baron", "AIR_DRAGON": "Wolkendrache",
           "CHEMTECH_DRAGON": "Chemtech-Drache", "EARTH_DRAGON": "Bergdrache", "FIRE_DRAGON": "Hoellendrache",
           "HEXTECH_DRAGON": "Hextech-Drache", "WATER_DRAGON": "Ozeandrache", "ELDER_DRAGON": "Elder"}
_ITEMS = None


def items():
    global _ITEMS
    if _ITEMS is None:
        d = sorted((g.WURZEL / "daten" / "ddragon").glob("*/item.json"))
        _ITEMS = json.loads(d[-1].read_text(encoding="utf-8"))["data"] if d else {}
    return _ITEMS


def item_name(i: int) -> str:
    return items().get(str(i), {}).get("name", str(i))


def inventar(p: g.Partie, pid: int, t: float) -> list[int]:
    """Items nach Kauf/Verkauf/Rueckgaengig/Verbrauch bis t (so zeigt sie das Scoreboard)."""
    inv: list[int] = []
    for e in p.events:
        if e["t"] > t or e.get("participantId") != pid:
            continue
        if e["typ"] == "ITEM_PURCHASED":
            inv.append(e["itemId"])
        elif e["typ"] in ("ITEM_SOLD", "ITEM_DESTROYED") and e.get("itemId") in inv:
            inv.remove(e["itemId"])
        elif e["typ"] == "ITEM_UNDO":
            if e.get("beforeId") in inv:
                inv.remove(e["beforeId"])
            if e.get("afterId"):
                inv.append(e["afterId"])
    return inv


def item_wert(inv) -> int:
    return sum(items().get(str(i), {}).get("gold", {}).get("total", 0) for i in inv)


def stand(p: g.Partie, t: float, team: int) -> dict:
    """Scoreboard und angesagte Ereignisse bis t, aus Sicht von `team`."""
    s = {"kills": Counter(), "tuerme": Counter(), "platten": Counter(), "monster": {g.BLAU: [], g.ROT: []}}
    for e in p.events:
        if e["t"] > t:
            break
        if e["typ"] == "CHAMPION_KILL":
            s["kills"][gegner(p.team(e["victimId"]))] += 1
        elif e["typ"] == "BUILDING_KILL" and e.get("buildingType") == "TOWER_BUILDING":
            s["tuerme"][gegner(e["teamId"])] += 1
        elif e["typ"] == "TURRET_PLATE_DESTROYED":
            s["platten"][gegner(e["teamId"])] += 1
        elif e["typ"] == "ELITE_MONSTER_KILL" and e.get("killerTeamId") in (g.BLAU, g.ROT):
            s["monster"][e["killerTeamId"]].append(MONSTER.get(e.get("monsterSubType") or e["monsterType"], "?"))
    return s


def zuletzt_gesehen(p: g.Partie, pid: int, t: float):
    """Letztes angesagtes Ereignis mit Ort, an dem der Gegner beteiligt war (kein Maphack)."""
    best = None
    for e in p.events:
        if e["t"] > t:
            break
        pos = e.get("position")
        if not pos or e["typ"] not in ("CHAMPION_KILL", "BUILDING_KILL", "ELITE_MONSTER_KILL"):
            continue
        if pid in {e.get("killerId"), e.get("victimId"), *(e.get("assistingParticipantIds") or [])}:
            best = (e["t"], pos, e["typ"])
    return best


def lage(p: g.Partie, top: int, t: float) -> list[str]:
    team = p.team(top)
    i = abl._frame_vor(p, t)
    ft = abl._ftime(p, i)
    z = []
    st = stand(p, t, team)
    geg = gegner(team)
    z.append(f"- Stand [B]: Kills {st['kills'][team]}:{st['kills'][geg]}, Tuerme {st['tuerme'][team]}:{st['tuerme'][geg]}, "
             f"Platten {st['platten'][team]}:{st['platten'][geg]}; Monster wir: {', '.join(st['monster'][team]) or '–'}; "
             f"Gegner: {', '.join(st['monster'][geg]) or '–'}")
    f = p.frame(i)[top]
    selbst_tot = [(td, tr) for td, tr in p.tode(top) if td <= t < tr]
    z.append(f"- Du [B, Minute {uhr(ft)}]: "
             + (f"TOT noch {selbst_tot[0][1] - t:.0f} s [G Formel], " if selbst_tot else
                f"{WO.get(bereich(f[0], f[1]))} ({f[0]},{f[1]}), ")
             + f"Level {f[5]}, CS {f[6] + f[7]}, {f[3]} Gold in der Tasche, Leben {f[9]}/{f[10]}"
             + (", TP bereit? [U in den Daten, im Spiel sichtbar]" if p.hat_tp(top) else ""))
    lg = p.pid_von(geg, "TOP")
    if lg:
        fl = p.frame(i)[lg]
        inv_ich, inv_er = item_wert(inventar(p, top, t)), item_wert(inventar(p, lg, t))
        tot = [(td, tr) for td, tr in p.tode(lg) if td <= t < tr]
        zg = zuletzt_gesehen(p, lg, t)
        z.append(f"- Lane-Gegner {p.champ(lg)} [B Scoreboard]: Level {fl[5]}, CS {fl[6] + fl[7]}, Items {inv_er} Gold "
                 f"(du {inv_ich})" + (f", TOT noch {tot[0][1] - t:.0f} s" if tot else "")
                 + (f"; zuletzt gesehen {uhr(zg[0])} {WO.get(bereich(*zg[1]))} [B]" if zg else "; Ort [U]"))
    mit = []
    for pid, s in p.sp.items():
        if s["teamId"] != team or pid == top:
            continue
        fm = p.frame(i)[pid]
        tot = [(td, tr) for td, tr in p.tode(pid) if td <= t < tr]
        mit.append(f"{p.champ(pid)} ({g.ROLLE_DE[s['teamPosition']]}) "
                   + (f"TOT {tot[0][1] - t:.0f} s" if tot else f"{WO.get(bereich(fm[0], fm[1]))} L{fm[5]}"))
    z.append(f"- Mitspieler [B Minimap, Minute {uhr(ft)}]: " + "; ".join(mit))
    gg = []
    for pid, s in p.sp.items():
        if s["teamId"] != geg or pid == lg:
            continue
        tot = [(td, tr) for td, tr in p.tode(pid) if td <= t < tr]
        zg = zuletzt_gesehen(p, pid, t)
        gg.append(f"{p.champ(pid)} ({g.ROLLE_DE[s['teamPosition']]}) "
                  + (f"TOT {tot[0][1] - t:.0f} s" if tot else
                     (f"zuletzt {uhr(zg[0])} {WO.get(bereich(*zg[1]))}" if zg else "nie gesehen")))
    z.append("- Gegner [B tot/Scoreboard, Ort nur zuletzt gesehen, jetzt U]: " + "; ".join(gg))
    return z


def tat(p: g.Partie, top: int, t: float) -> list[str]:
    """Was der Top-Laner in den naechsten 60 s tat."""
    z = []
    i = abl._frame_vor(p, t)
    wege = []
    for j in (i, i + 1, i + 2):
        if j < len(p.frames):
            f = p.frame(j)[top]
            wege.append(f"{uhr(abl._ftime(p, j))} {WO.get(bereich(f[0], f[1]))}")
    z.append("- Weg [B je Minute, dazwischen G]: " + " -> ".join(wege))
    ev = []
    for e in p.events:
        if not t <= e["t"] <= t + 60:
            continue
        beteiligt = top in {e.get("killerId"), e.get("victimId"), e.get("participantId"),
                            *(e.get("assistingParticipantIds") or [])}
        if not beteiligt:
            continue
        if e["typ"] == "ITEM_PURCHASED":
            ev.append(f"{uhr(e['t'])} kauft {item_name(e['itemId'])}")
        elif e["typ"] == "CHAMPION_KILL":
            if e["victimId"] == top:
                ev.append(f"{uhr(e['t'])} STIRBT gegen {p.champ(e['killerId']) if e['killerId'] else 'Turm/Monster'} "
                          f"({WO.get(bereich(*e['position']))})")
            else:
                ev.append(f"{uhr(e['t'])} {'Kill' if e['killerId'] == top else 'Assist'} an {p.champ(e['victimId'])} "
                          f"({WO.get(bereich(*e['position']))})")
        elif e["typ"] == "BUILDING_KILL":
            ev.append(f"{uhr(e['t'])} Turm/Gebaeude {e.get('laneType', '')} {e.get('towerType', '')}")
        elif e["typ"] == "TURRET_PLATE_DESTROYED":
            ev.append(f"{uhr(e['t'])} Platte {e.get('laneType', '')}")
        elif e["typ"] == "ELITE_MONSTER_KILL":
            ev.append(f"{uhr(e['t'])} beim {MONSTER.get(e.get('monsterSubType') or e['monsterType'])}")
        elif e["typ"] == "LEVEL_UP":
            ev.append(f"{uhr(e['t'])} Level {e['level']}")
    z.append("- Ereignisse [B]: " + ("; ".join(ev) or "keine"))
    tp = [x for x in abl.tps(p, "wahrscheinlich") if x["pid"] == top and t - 5 <= x["t"] <= t + 70]
    if tp:
        z.append("- TP [G, Positionssprung]: " + "; ".join(f"{uhr(x['t_von'])}->{uhr(x['t'])} {WO.get(x['von'])} -> "
                                                        f"{WO.get(x['nach'])} ({x['stufe']})" for x in tp))
    return z


def folge(p: g.Partie, top: int, t: float) -> list[str]:
    team = p.team(top)
    geg = gegner(team)
    z = []
    for dt in (30, 60, 120):
        k, obj, geb = Counter(), [], []
        for e in p.events:
            if not t < e["t"] <= t + dt:
                continue
            if e["typ"] == "CHAMPION_KILL":
                k[gegner(p.team(e["victimId"]))] += 1
            elif e["typ"] == "ELITE_MONSTER_KILL":
                obj.append(f"{MONSTER.get(e.get('monsterSubType') or e['monsterType'])} "
                           f"{'wir' if e.get('killerTeamId') == team else 'Gegner'}")
            elif e["typ"] == "BUILDING_KILL":
                geb.append(f"{'wir' if e['teamId'] == geg else 'Gegner'} {e.get('laneType', '')[:3]} "
                           f"{(e.get('towerType') or e.get('buildingType', ''))[:5]}")
        z.append(f"- +{dt} s [B]: Kills {k[team]}:{k[geg]}" + (f"; {', '.join(obj)}" if obj else "")
                 + (f"; Gebaeude: {', '.join(geb)}" if geb else ""))

    def gold(j):
        f = p.frame(min(j, len(p.frames) - 1))
        return sum(v[2] for pid, v in f.items() if p.team(pid) == team) - \
               sum(v[2] for pid, v in f.items() if p.team(pid) == geg)
    i = abl._frame_vor(p, t)
    z.append(f"- Gold-Abstand Team [B zur Minute, nur im Nachhinein bekannt]: {uhr(abl._ftime(p, i))} {gold(i):+d} -> "
             f"{uhr(abl._ftime(p, min(i + 2, len(p.frames) - 1)))} {gold(i + 2):+d}")
    z.append(f"- Partie [B]: {'gewonnen' if p.sieger == team else 'verloren'} ({uhr(p.dauer)})")
    return z


def momente(p: g.Partie, top: int, n: int = 10) -> list[tuple[str, float]]:
    """Die zehn Momente: (Name, Zeitpunkt der Lage). Reihenfolge = Vorrang; ein Moment, der weniger als 60 s neben
    einem schon gewaehlten liegt, faellt weg (sonst dreimal dieselbe Lage), dafuer rueckt ein Ersatz nach."""
    wunsch = []
    backs = [b for b in abl.backs(p) if b["pid"] == top and b["art"] == "Back" and b["kauf"]]
    if backs:
        wunsch.append(("Erster Back", backs[0]["t"] - 20))
    tp = [x for x in abl.tps(p, "sicher") + abl.tps(p, "wahrscheinlich") if x["pid"] == top]
    if tp:
        erster = min(tp, key=lambda x: x["t_von"])
        wunsch.append((f"TP ({erster['stufe']} erkannt)", erster["t_von"] - 25))
    ems = [e for e in p.events if e["typ"] == "ELITE_MONSTER_KILL"]
    for typ, name in (("DRAGON", "Erster Drache"), ("HORDE", "Erste Larven"), ("RIFTHERALD", "Herold"),
                      ("BARON_NASHOR", "Baron")):
        e = next((e for e in ems if e["monsterType"] == typ), None)
        if e:
            wunsch.append((name, e["t"] - 60))
    turm = next((e for e in p.events if e["typ"] == "BUILDING_KILL" and e.get("buildingType") == "TOWER_BUILDING"), None)
    if turm:
        wunsch.append(("Erster Turm", turm["t"] - 45))
    kampf = next((k for k in abl.kaempfe(p) if k["kills"] >= 3), None)
    if kampf:
        wunsch.append((f"Erster Kampf ({kampf['kills']} Kills)", kampf["t"] - 30))
    wunsch += [("Mitte 20:00", 20 * 60), ("Schluss", p.dauer - 100), ("Plattenende 14:00", 13 * 60 + 30)]
    # Ersatz
    lv6 = next((e["t"] for e in p.events if e["typ"] == "LEVEL_UP" and e.get("participantId") == top
                and e["level"] == 6), None)
    if lv6:
        wunsch.append(("Level 6", lv6 - 10))
    drachen = [e for e in ems if e["monsterType"] == "DRAGON"]
    if len(drachen) > 1:
        wunsch.append(("Zweiter Drache", drachen[1]["t"] - 60))
    if len(backs) > 1:
        wunsch.append(("Zweiter Back", backs[1]["t"] - 20))
    wunsch += [("Minute 25", 25 * 60), ("Minute 10", 10 * 60)]
    out = []
    for name, t in wunsch:
        if len(out) < n and 0 < t < p.dauer and all(abs(t - t2) >= 60 for _, t2 in out):
            out.append((name, t))
    return sorted(out, key=lambda x: x[1])


def waehle() -> str:
    liga = json.loads((g.ABLAGE / "liga.json").read_text(encoding="utf-8"))["spieler"]
    for mid in json.loads((g.ABLAGE / "gueltig.json").read_text(encoding="utf-8")):
        p = g.Partie(g.lade(mid))
        top = p.pid_von(p.sieger, "TOP")
        if not (27 * 60 <= p.dauer <= 33 * 60) or top is None or not p.hat_tp(top):
            continue
        if liga.get(p.sp[top]["puuid"]) != "Challenger":
            continue
        if {"DRAGON", "BARON_NASHOR", "HORDE", "RIFTHERALD"} <= {e.get("monsterType") for e in p.events}:
            return mid
    raise SystemExit("keine passende Partie")


def main():
    mid = sys.argv[1] if len(sys.argv) > 1 else waehle()
    p = g.Partie(g.lade(mid))
    top = p.pid_von(p.sieger, "TOP")
    lg = p.pid_von(gegner(p.sieger), "TOP")
    s = p.sp[top]
    z = [f"# Zehn Momente – Faktenblatt {mid}", "",
         f"{p.champ(top)} (Top, Team {'Blau' if p.team(top) == g.BLAU else 'Rot'}, Sieger, TP {p.tp_casts(top)}x) gegen "
         f"{p.champ(lg)}; {uhr(p.dauer)}; Endstand {s['kills']}/{s['deaths']}/{s['assists']}, Patch "
         f"{'.'.join(p.k['version'].split('.')[:2])}.", ""]
    for n, (name, t) in enumerate(momente(p, top), 1):
        z += [f"## {n}. {name} – Lage bei {uhr(t)}", "", "**Lage (nur Wissbares):**"] + lage(p, top, t)
        z += ["", "**Was der Top-Laner in den naechsten 60 s tat:**"] + tat(p, top, t)
        z += ["", "**Was daraus wurde:**"] + folge(p, top, t) + [""]
    (g.BUCH / "momente_roh.md").write_text("\n".join(z) + "\n", encoding="utf-8")
    print("\n".join(z))


if __name__ == "__main__":
    main()
