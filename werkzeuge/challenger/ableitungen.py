"""Auftrag 029, Schritt 3: Ableitungen aus den Partien - und ihre Pruefung an je 50 Stichproben.

    python werkzeuge/challenger/ableitungen.py        schreibt buecher/challenger/ableitungen.md

Jede Ableitung ist eine Funktion `name(p: Partie) -> [dict]`. Jede hat eine Gegenprobe aus Daten, die sie SELBST
NICHT benutzt (z. B. Back aus Kaeufen, Gegenprobe aus der Position danach; TP aus Positionsspruengen, Gegenprobe aus
`summonerXCasts`). Stichprobe: 50 zufaellige Funde (fester Zufall 29), gezaehlt Treffer und Zweifel; die Zweifel
stehen einzeln im Buch, damit man sie liest.
"""
from __future__ import annotations

import json
import random
import statistics
from collections import Counter, defaultdict

import grundlage as g
from grundlage import BRUNNEN, WEGFAKTOR, RECALL, abstand, bereich, gegner, uhr

LADEN = 1300              # Laden-Reichweite um den Brunnen (grosszuegig)
TEMPO_REIHE = 1.35        # Laufen: Tempo aus der Minute x 1,35 (Geist, Zephyr, Buffs) ...
SPRUNG_ZUSCHLAG = 900     # ... plus Flash und Dash
ZEIT_SPIEL = 10.0         # s: Kauf-Zeitstempel und Minuten-Position liegen bis ~8 s auseinander (99 %, gemessen)
KAUF_LUECKE = 25.0        # Kaeufe, die so eng liegen, sind ein Ladenbesuch
KAMPF_ZEIT, KAMPF_RAUM = 15.0, 3000.0
OBJ_ZEIT, OBJ_RAUM = 30.0, 3000.0
GANK_BIS = 14 * 60
LANE_DES_TEILNEHMERS = {"top": {"TOP"}, "mid": {"MIDDLE"}, "bot": {"BOTTOM", "UTILITY"}}


# ---------------------------------------------------------------- Hilfen

def _frame_nah(p: g.Partie, t: float) -> int:
    return max(0, min(len(p.frames) - 1, round(t / 60)))


def _frame_vor(p: g.Partie, t: float) -> int:
    return max(0, min(len(p.frames) - 1, int(t // 60)))


def _ftime(p: g.Partie, i: int) -> float:
    return p.frames[i][0] / 1000.0


def _laufen(p: g.Partie, pid: int, t: float) -> float:
    return p.tempo(pid, _frame_nah(p, t)) * TEMPO_REIHE


def ladenbesuche(p: g.Partie, pid: int):
    """[(t_erster, t_letzter, [itemIds])] - Kaeufe nach 1:30, eng beieinander."""
    ks = [e for e in p.events if e["typ"] == "ITEM_PURCHASED" and e.get("participantId") == pid and e["t"] > 90]
    out = []
    for e in ks:
        if out and e["t"] - out[-1][1] <= KAUF_LUECKE:
            out[-1][1] = e["t"]
            out[-1][2].append(e["itemId"])
        else:
            out.append([e["t"], e["t"], [e["itemId"]]])
    return out


# Items, die sich ohne Laden kaufen (Upgrade/Verwandlung) - an den Zweifeln der ersten Runde gefunden, s. Buch
AUTO_ITEMS: set[int] = set()


# ---------------------------------------------------------------- 1. Back

def backs(p: g.Partie):
    """Ladenbesuch, der nicht direkt auf einen Tod folgt = Back (Recall). Dazu 'ohne Kauf': Minute in der eigenen
    Basis, lebend, kein Ladenbesuch +-45 s."""
    out = []
    for pid in p.sp:
        tode = p.tode(pid)
        besuche = [b for b in ladenbesuche(p, pid) if not (len(b[2]) == 1 and b[2][0] in AUTO_ITEMS)]
        for t0, t1, items in besuche:
            nach_tod = any(td <= t0 <= tr + 45 for td, tr in tode)
            out.append({"pid": pid, "t": t0, "t_ende": t1, "items": items, "art": "Tod" if nach_tod else "Back",
                        "kauf": True})
        for i in range(2, len(p.frames)):
            pos = p.pos(pid, i)
            t = _ftime(p, i)
            if pos is None or abstand(pos, BRUNNEN[p.team(pid)]) > 2500:
                continue
            if any(td <= t <= tr + 30 for td, tr in tode):
                continue
            if any(t0 - 45 <= t <= t1 + 45 for t0, t1, _ in besuche):
                continue
            out.append({"pid": pid, "t": t, "t_ende": t, "items": [], "art": "Back", "kauf": False})
    return out


def pruefe_back(p: g.Partie, b: dict):
    """Gegenprobe: die naechste Minute nach dem letzten Kauf muss vom Brunnen aus erreichbar sein (zu Fuss oder
    mit TP, falls TP gespielt). Ohne Kauf: die Minute davor oder danach passt zu einem Recall (nicht 'im Vorbeigehen')."""
    pid = b["pid"]
    if not b["kauf"]:
        i = _frame_nah(p, b["t"])
        vor, nach = p.pos(pid, i - 1), p.pos(pid, i + 1)
        # Ein echter Back ohne Kauf: in der Minute davor weit weg (Recall) ODER danach wieder weit weg
        ok = (vor and abstand(vor, BRUNNEN[p.team(pid)]) > 4000) or (nach and abstand(nach, BRUNNEN[p.team(pid)]) > 4000)
        return ok, "" if ok else "steht zwei Minuten in der Basis (AFK oder Warten)"
    i = next((j for j in range(len(p.frames)) if _ftime(p, j) >= b["t_ende"]), None)
    if i is None:
        return True, "Spielende"
    pos = p.pos(pid, i)
    dt = _ftime(p, i) - b["t_ende"]
    weit = abstand(pos, BRUNNEN[gegner(p.team(pid)) if b.get("fremd") else p.team(pid)]) - LADEN
    if weit <= _laufen(p, pid, b["t"]) * (dt + ZEIT_SPIEL) + SPRUNG_ZUSCHLAG:
        return True, ""
    if p.hat_tp(pid):
        return True, "TP danach"
    return False, f"{weit:.0f} Einheiten vom Laden, {dt:.0f} s nach dem Kauf"


# ---------------------------------------------------------------- 2. TP

GLOBALE_REISE = {"TwistedFate", "Shen", "Pantheon", "Galio", "Ryze", "TahmKench", "Nocturne", "Taliyah", "Bard",
                 "Kalista", "Quinn", "Hecarim", "Rammus", "Singed", "Evelynn", "Rakan", "Zilean", "Janna", "Ivern"}


def anker(p: g.Partie, pid: int):
    """Wo war der Spieler sicher, wann? (t, pos, toleranz, art). Minute exakt; Tod exakt (Opfer); Kill/Assist/
    Gebaeude/Monster nur, wenn die folgende Minute ihn dort zeigt (sonst Fernkampf/Globale); Kauf am Laden;
    Wiederbelebung im Brunnen."""
    team = p.team(pid)
    a = []
    for i, (ts, _) in enumerate(p.frames):
        pos = p.pos(pid, i)
        if pos:
            a.append((ts / 1000.0, pos, 0.0, "minute"))
    for td, tr in p.tode(pid):
        a.append((tr, BRUNNEN[team], 300.0, "wiederbelebt"))
    for t0, t1, items in ladenbesuche(p, pid):
        for t in {t0, t1}:
            a.append((t, BRUNNEN[team], LADEN, "kauf"))
    for e in p.events:
        pos = e.get("position")
        if not pos:
            continue
        typ, t = e["typ"], e["t"]
        if typ == "CHAMPION_KILL" and e.get("victimId") == pid:
            a.append((t, pos, 0.0, "tod"))
            continue
        dabei = e.get("killerId") == pid or pid in (e.get("assistingParticipantIds") or [])
        if not dabei or typ not in ("CHAMPION_KILL", "BUILDING_KILL", "ELITE_MONSTER_KILL", "TURRET_PLATE_DESTROYED"):
            continue
        nach = p.pos(pid, int(t // 60) + 1)
        if nach and abstand(nach, pos) <= 3000 and not p.tot_bei(pid, t + 1):
            a.append((t, pos, 1500.0, typ.lower()))
    # Tote stehen nicht im Laden, sondern am Todesort (Minute mit Leben 0, Kauf waehrend des Todes)
    a = [x for x in a if x[3] in ("tod", "wiederbelebt") or not p.tot_bei(pid, x[0])]
    a = [x for x in a if x[3] != "minute" or (p.frame(round(x[0] / 60)).get(pid) or (0,) * 11)[9] != 0]
    a.sort(key=lambda x: x[0])
    return a


# Zwei Stufen: "sicher" = zu Fuss selbst mit Geist, Flash und 10 s Zeitversatz unmoeglich; "wahrscheinlich" = mit
# normalem Tempo, krummem Weg (x 1,15) und 5 s Versatz nicht zu schaffen. Die Gegenprobe (Spieler OHNE TP) misst,
# wie oft jede Stufe falsch anschlaegt.
STUFEN = {"sicher": (TEMPO_REIHE, 1.0, SPRUNG_ZUSCHLAG, ZEIT_SPIEL),
          "wahrscheinlich": (1.0, WEGFAKTOR, 400.0, 5.0)}


def tps(p: g.Partie, stufe: str = "sicher"):
    faktor, weg, sprung, versatz = STUFEN[stufe]
    out = []
    for pid in p.sp:
        team = p.team(pid)
        tode = p.tode(pid)
        an = anker(p, pid)
        letzte = -999.0
        for a, b in zip(an, an[1:]):
            dt = b[0] - a[0]
            if dt <= 0.5 or a[3] == "tod":           # nach dem Tod geht es im Brunnen weiter (eigener Anker)
                continue
            if any(a[0] <= td < b[0] for td, _ in tode):
                continue
            tempo = p.tempo(pid, _frame_nah(p, a[0])) * faktor
            luft = abstand(a[1], b[1]) * weg - a[2] - b[2] - sprung
            if luft <= tempo * (dt + versatz):
                continue
            # Recall: der Kanal kann schon vor Anker a begonnen haben -> ab a nur noch der Weg vom Brunnen
            per_recall = max(0.0, abstand(BRUNNEN[team], b[1]) * weg - b[2] - sprung) / tempo
            if per_recall <= dt + versatz:
                continue
            if b[0] - letzte < 45:                  # derselbe Sprung, mehrfach gesehen
                continue
            letzte = b[0]
            von, nach = bereich(*a[1]), bereich(*b[1])
            art = "aus der Basis" if a[3] == "kauf" or von.startswith("basis") else                   ("zum Kampf" if b[3] in ("champion_kill", "tod") else "Ortswechsel")
            out.append({"pid": pid, "t": b[0], "t_von": a[0], "von": von, "nach": nach, "anker": (a[3], b[3]),
                        "luft": luft, "dt": dt, "art": art, "stufe": stufe})
    return out


def pruefe_tp(p: g.Partie, tp: dict, je_spieler: Counter):
    pid = tp["pid"]
    if not p.hat_tp(pid):
        c = p.champ(pid)
        return False, f"kein TP gespielt ({c}{', globale Reise' if c in GLOBALE_REISE else ''})"
    if je_spieler[(p.id, pid)] > p.tp_casts(pid):
        return False, f"mehr Spruenge ({je_spieler[(p.id, pid)]}) als TP-Einsaetze ({p.tp_casts(pid)})"
    return True, ""


# ---------------------------------------------------------------- 3. Kampf

def kaempfe(p: g.Partie):
    """Kills, die eng in Zeit (<= 15 s zum letzten) und Raum (<= 3000 zum Schwerpunkt) liegen. >= 2 Kills = Kampf."""
    ks = sorted((e for e in p.events if e["typ"] == "CHAMPION_KILL"), key=lambda e: e["t"])
    offen = []
    for e in ks:
        ziel = None
        for c in offen:
            sx = sum(k["position"][0] for k in c) / len(c)
            sy = sum(k["position"][1] for k in c) / len(c)
            if e["t"] - c[-1]["t"] <= KAMPF_ZEIT and abstand((sx, sy), e["position"]) <= KAMPF_RAUM:
                ziel = c
                break
        if ziel is None:
            offen.append([e])
        else:
            ziel.append(e)
    out = []
    for c in offen:
        beteiligt = set()
        tode = Counter()
        for k in c:
            beteiligt |= {k["killerId"], k["victimId"], *(k.get("assistingParticipantIds") or [])}
            tode[p.team(k["victimId"])] += 1
        beteiligt.discard(0)
        sx = sum(k["position"][0] for k in c) / len(c)
        sy = sum(k["position"][1] for k in c) / len(c)
        sieger = None
        if tode[g.BLAU] != tode[g.ROT]:
            sieger = g.BLAU if tode[g.BLAU] < tode[g.ROT] else g.ROT
        out.append({"t": c[0]["t"], "t_ende": c[-1]["t"], "kills": len(c), "ort": (sx, sy), "bereich": bereich(sx, sy),
                    "beteiligt": sorted(beteiligt), "tode": dict(tode), "sieger": sieger})
    return out


KAMPF_PRUEFBAR = 10.0    # s: nur Kaempfe, deren Beginn so nah an einer vollen Minute liegt, sind an Positionen pruefbar


def kampf_pruefbar(k: dict) -> bool:
    return abs(k["t"] - round(k["t"] / 60) * 60) <= KAMPF_PRUEFBAR


def pruefe_kampf(p: g.Partie, k: dict):
    """Gegenprobe aus den Minuten-Positionen (nur Kaempfe <= 10 s neben einer vollen Minute): >= 60 % der lebenden
    Beteiligten stehen in dieser Minute innerhalb 2000 + Tempo x Zeitabstand um den Kampfort."""
    i = _frame_nah(p, k["t"])
    dt = abs(_ftime(p, i) - k["t"])
    nah, da = 0, 0
    for pid in k["beteiligt"]:
        q = p.pos(pid, i)
        if not q or p.tot_bei(pid, _ftime(p, i)):
            continue
        da += 1
        nah += abstand(q, k["ort"]) <= 2000 + p.tempo(pid, i) * dt
    if not da:
        return True, "alle tot zur Minute"
    ok = nah >= 0.6 * da
    return ok, "" if ok else f"nur {nah}/{da} Beteiligte nah ({dt:.0f} s neben der Minute)"


# ---------------------------------------------------------------- 4. Umkaempftes Objective

def objectives(p: g.Partie):
    out = []
    for e in p.events:
        if e["typ"] != "ELITE_MONSTER_KILL":
            continue
        kills = [k for k in p.events if k["typ"] == "CHAMPION_KILL" and abs(k["t"] - e["t"]) <= OBJ_ZEIT
                 and abstand(k["position"], e["position"]) <= OBJ_RAUM]
        nehmer = e["killerTeamId"]
        tode = Counter(p.team(k["victimId"]) for k in kills)
        out.append({"t": e["t"], "typ": e.get("monsterSubType") or e["monsterType"], "team": nehmer,
                    "ort": e["position"], "umkaempft": bool(kills), "kills": len(kills),
                    "tode_nehmer": tode[nehmer], "tode_gegner": tode[gegner(nehmer)],
                    "helfer": len(e.get("assistingParticipantIds") or []) + 1})
    return out


def pruefe_objective(p: g.Partie, o: dict):
    """Gegenprobe aus den Positionen der Minute vor und nach dem Monster: Wie viele des Gegnerteams standen
    innerhalb 4000 um die Grube? Umkaempft -> mind. 2; frei -> hoechstens 2 (sonst Zweifel: Zweikampf ohne Kill?)."""
    geg = gegner(o["team"])
    beste = 0
    for i in (_frame_vor(p, o["t"]), _frame_vor(p, o["t"]) + 1):
        n = sum(1 for pid, s in p.sp.items() if s["teamId"] == geg and (q := p.pos(pid, i))
                and abstand(q, o["ort"]) <= 4000)
        beste = max(beste, n)
    if o["umkaempft"]:
        return beste >= 2, "" if beste >= 2 else f"Gegner nah: {beste} (Kills eher Nebenschauplatz)"
    return beste <= 2, "" if beste <= 2 else f"frei genommen, aber {beste} Gegner nah"


# ---------------------------------------------------------------- 5. Gank

def ganks(p: g.Partie):
    out = []
    for e in p.events:
        if e["typ"] != "CHAMPION_KILL" or e["t"] > GANK_BIS:
            continue
        ber = bereich(*e["position"])
        if ber not in ("top", "mid", "bot"):
            continue
        opfer = e["victimId"]
        if p.rolle(opfer) == "JUNGLE":
            continue
        team = gegner(p.team(opfer))
        jgl = p.pid_von(team, "JUNGLE")
        if jgl is None or jgl not in {e["killerId"], *(e.get("assistingParticipantIds") or [])}:
            continue
        out.append({"t": e["t"], "lane": ber, "opfer": opfer, "jungler": jgl, "team": team, "ort": e["position"],
                    "killer": e["killerId"], "helfer": e.get("assistingParticipantIds") or []})
    return out


def pruefe_gank(p: g.Partie, k: dict):
    """Gegenprobe: Opfer ist der Laner dieser Lane, und der Jungler kann aus seiner Minute davor dort sein."""
    if p.rolle(k["opfer"]) not in LANE_DES_TEILNEHMERS[k["lane"]]:
        return False, f"Opfer {g.ROLLE_DE.get(p.rolle(k['opfer']))} stirbt auf {k['lane']} (Roam-Opfer)"
    i = _frame_vor(p, k["t"])
    q = p.pos(k["jungler"], i)
    dt = k["t"] - _ftime(p, i)
    if q and abstand(q, k["ort"]) - SPRUNG_ZUSCHLAG > _laufen(p, k["jungler"], k["t"]) * dt:
        return False, "Jungler zu weit weg (Assist aus der Ferne)"
    return True, ""


# ---------------------------------------------------------------- 6. Rotation, Gruppe, Split

def zone(ber: str) -> str:
    if ber.startswith("basis"):
        return "basis"
    if ber == "mid":
        return "mid"
    if ber in ("top", "fluss_oben") or ber.endswith("_oben"):
        return "oben"
    return "unten"


def rotationen(p: g.Partie):
    """Seitenwechsel oben/mid/unten, der zwei Minuten haelt (a -> b -> b), lebend, ohne Basis und Tod dazwischen.
    Nur Laner und Support: der Jungler wechselt die Seite staendig (Pfad), das ist keine Rotation."""
    out = []
    for pid in p.sp:
        if p.rolle(pid) == "JUNGLE":
            continue
        for i in range(2, len(p.frames) - 2):
            a, b, c = p.pos(pid, i), p.pos(pid, i + 1), p.pos(pid, i + 2)
            if not a or not b or not c:
                continue
            za, zb, zc = zone(bereich(*a)), zone(bereich(*b)), zone(bereich(*c))
            if "basis" in (za, zb) or za == zb or zc != zb:
                continue
            t0, t1 = _ftime(p, i), _ftime(p, i + 2)
            if any(t0 - 5 <= td <= t1 for td, _ in p.tode(pid)):
                continue
            if any(t0 <= b0 <= t1 for b0, _, _ in ladenbesuche(p, pid)):
                continue
            out.append({"pid": pid, "t": _ftime(p, i + 1), "i": i + 1, "von": za, "nach": zb, "ber_von": bereich(*a),
                        "ber_nach": bereich(*b)})
    return out


def pruefe_rotation(p: g.Partie, r: dict):
    """Gegenprobe (ortsgenau): bis 120 s ist er IN DER NEUEN ZONE an einem Ereignis beteiligt (Kill, Tod, Gebaeude,
    Platte, Monster), oder dort steht ein Mitspieler (<= 2500) oder Gegner (<= 3000) bei ihm."""
    pid, team = r["pid"], p.team(r["pid"])
    for e in p.events:
        pos = e.get("position")
        if pos and r["t"] - 60 <= e["t"] <= r["t"] + 120 and zone(bereich(*pos)) == r["nach"] and \
                pid in {e.get("killerId"), e.get("victimId"), *(e.get("assistingParticipantIds") or [])}:
            return True, "Ereignis dort"
    for j in (r["i"], r["i"] + 1):
        q = p.pos(pid, j)
        if not q or zone(bereich(*q)) != r["nach"]:
            continue
        for x, s in p.sp.items():
            rr = p.pos(x, j)
            if x == pid or not rr or zone(bereich(*rr)) != r["nach"]:
                continue
            if abstand(q, rr) <= (2500 if s["teamId"] == team else 3000):
                return True, "bei Mitspieler" if s["teamId"] == team else "bei Gegner"
    return False, "allein unterwegs, nichts passiert"


def gruppen(p: g.Partie, ab_minute: int = 8):
    out = []
    for i in range(ab_minute, len(p.frames)):
        t = _ftime(p, i)
        for team in (g.BLAU, g.ROT):
            leute = [(pid, p.pos(pid, i)) for pid, s in p.sp.items() if s["teamId"] == team
                     and p.pos(pid, i) and not p.tot_bei(pid, t) and not bereich(*p.pos(pid, i)).startswith("basis")]
            beste = []
            for pid, q in leute:
                nah = [x for x, r in leute if abstand(q, r) <= 2500]
                if len(nah) > len(beste):
                    beste = nah
            if len(beste) >= 3:
                sx = sum(p.pos(x, i)[0] for x in beste) / len(beste)
                sy = sum(p.pos(x, i)[1] for x in beste) / len(beste)
                out.append({"t": t, "i": i, "team": team, "n": len(beste), "leute": beste, "ort": (sx, sy),
                            "bereich": bereich(sx, sy)})
    return out


def pruefe_gruppe(p: g.Partie, gr: dict):
    """Gegenprobe (ortsgenau): hat die Gruppe einen Anlass? +-60 s passiert innerhalb 3500 um ihren Schwerpunkt
    etwas (Kill, Gebaeude, Platte, Monster). Beisammenstehen allein belegt nichts (die Nullprobe bestand es zu 96 %)."""
    for e in p.events:
        pos = e.get("position")
        if pos and e["typ"] != "CHAMPION_SPECIAL_KILL" and abs(e["t"] - gr["t"]) <= 60 \
                and abstand(pos, gr["ort"]) <= 3500:
            return True, "Ereignis dort"
    return False, "ohne Anlass (nichts passiert dort +-60 s)"


def splits(p: g.Partie, ab_minute: int = 14):
    """Allein in einer Seitenlane (naechster Mitspieler >= 5000, mind. drei Mitspieler draussen), und zwar zwei
    Minuten hintereinander - eine Minute ist oft nur Welle abholen."""
    kandidaten = set()
    for i in range(ab_minute, len(p.frames)):
        t = _ftime(p, i)
        for pid, s in p.sp.items():
            q = p.pos(pid, i)
            if not q or p.tot_bei(pid, t):
                continue
            ber = bereich(*q)
            if ber not in ("top", "bot"):
                continue
            mit = [p.pos(x, i) for x, s2 in p.sp.items() if x != pid and s2["teamId"] == s["teamId"]
                   and p.pos(x, i) and not p.tot_bei(x, t)]
            if len(mit) < 3 or min(abstand(q, r) for r in mit) < 5000:
                continue
            if sum(1 for r in mit if not bereich(*r).startswith("basis")) < 3:
                continue
            kandidaten.add((i, pid, ber))
    out = []
    for i, pid, ber in sorted(kandidaten):
        if (i + 1, pid, ber) in kandidaten and (i - 1, pid, ber) not in kandidaten:
            out.append({"t": _ftime(p, i), "i": i, "pid": pid, "lane": ber, "ort": p.pos(pid, i)})
    return out


def pruefe_split(p: g.Partie, sp: dict):
    """Gegenprobe (lanegenau, bis 150 s): sein Team nimmt IN DIESER LANE Platte/Turm/Inhib, oder ein Gegner steht IN
    DIESER LANE bei ihm (<= 3000, er zieht Druck), oder er stirbt in dieser Lane (Split verloren - auch eine Folge)."""
    pid, team = sp["pid"], p.team(sp["pid"])
    lane_typ = {"top": "TOP_LANE", "bot": "BOT_LANE"}[sp["lane"]]
    for e in p.events:
        if not sp["t"] <= e["t"] <= sp["t"] + 150:
            continue
        if e["typ"] in ("BUILDING_KILL", "TURRET_PLATE_DESTROYED") and e.get("laneType") == lane_typ \
                and e.get("teamId") != team:
            return True, "Gebaeude/Platte"
        if e["typ"] == "CHAMPION_KILL" and e.get("victimId") == pid and bereich(*e["position"]) == sp["lane"]:
            return True, "stirbt dort"
    for j in (sp["i"], sp["i"] + 1):
        q = p.pos(pid, j)
        if not q or bereich(*q) != sp["lane"]:
            continue
        if any(s["teamId"] != team and (r := p.pos(x, j)) and bereich(*r) == sp["lane"] and abstand(q, r) <= 3000
               for x, s in p.sp.items()):
            return True, "zieht Gegner"
    return False, "nichts genommen, niemanden gezogen"


# ---------------------------------------------------------------- 7. Todeszeit

def todeszeiten(p: g.Partie):
    return [{"pid": pid, "t": td, "bis": tr} for pid in p.sp for td, tr in p.tode(pid)]


def pruefe_todeszeit(p: g.Partie, x: dict):
    """Gegenprobe: Leben 0 in den Minuten zwischen Tod und Wiederbelebung, Leben > 0 danach."""
    lo, hi = x["t"], None
    for i in range(len(p.frames)):
        t = _ftime(p, i)
        if t <= x["t"]:
            continue
        if p.frame(i)[x["pid"]][9] == 0:
            lo = t
        else:
            hi = t
            break
    if hi is None:
        return True, "Spielende"
    if x["bis"] < lo - 1:
        return False, f"Formel {x['bis'] - x['t']:.0f} s, aber zur Minute noch tot"
    if x["bis"] > hi + 1:
        return False, f"Formel {x['bis'] - x['t']:.0f} s, aber nach {hi - x['t']:.0f} s schon lebendig (Wiederbelebung/Zilean/GA?)"
    return True, ""


# ---------------------------------------------------------------- Pruefung

def _spiegel(ort):
    """Anderer Ort derselben Art: an der Hauptdiagonale gespiegelt (Top <-> Bot, oberer <-> unterer Fluss)."""
    x, y = ort
    return (y, x) if abs(x - y) > 3000 else (x + 5000 if x < 8000 else x - 5000, y)


NULL = {
    "Back": lambda p, x: {**x, "fremd": True},          # Laden des Gegners
    "Kampf": lambda p, x: {**x, "ort": _spiegel(x["ort"])},
    "Objective": lambda p, x: {**x, "t": x["t"] + 180},
    "Gank": lambda p, x: {**x, "lane": {"top": "bot", "bot": "top", "mid": "top"}[x["lane"]]},
    "Rotation": lambda p, x: {**x, "nach": x["von"]},
    "Gruppe": lambda p, x: {**x, "ort": _spiegel(x["ort"])},
    "Split": lambda p, x: {**x, "lane": "bot" if x["lane"] == "top" else "top"},
    "Todeszeit": lambda p, x: {**x, "bis": x["t"] + (x["bis"] - x["t"]) * 0.5},
}


def _zeile(p: g.Partie, art: str, x: dict) -> str:
    pid = x.get("pid") or x.get("opfer")
    wer = f"{p.champ(pid)} ({g.ROLLE_DE.get(p.rolle(pid), '?')})" if pid else ""
    t = uhr(x["t"])
    if art == "Back":
        return f"{t} {wer}: {x['art']}{'' if x['kauf'] else ' ohne Kauf'} {len(x['items'])} Kaeufe"
    if art == "TP":
        return f"{uhr(x['t_von'])}->{t} {wer}: {x['von']} -> {x['nach']} ({x['art']}; {x['luft']:.0f} zu weit in {x['dt']:.0f} s)"
    if art == "Kampf":
        return f"{t} {x['kills']} Kills {x['bereich']}, Tode {x['tode']}"
    if art == "Objective":
        return f"{t} {x['typ']} Team {x['team']}: {'umkaempft ' + str(x['kills']) + ' Kills' if x['umkaempft'] else 'frei'}"
    if art == "Gank":
        return f"{t} {x['lane']}: {p.champ(x['jungler'])} ganked {wer}"
    if art == "Rotation":
        return f"{t} {wer}: {x['ber_von']} -> {x['ber_nach']}"
    if art == "Gruppe":
        return f"{t} Team {x['team']}: {x['n']} beisammen {x['bereich']}"
    if art == "Split":
        return f"{t} {wer}: allein {x['lane']}"
    if art == "Todeszeit":
        return f"{t} {wer}: tot bis {uhr(x['bis'])}"
    return t


def pruefen(stichprobe: int = 50):
    gueltig = set(json.loads((g.ABLAGE / "gueltig.json").read_text(encoding="utf-8")))
    funde = defaultdict(list)          # art -> [(partie_id, fund)]
    summen = defaultdict(Counter)
    tp_je_spieler = Counter()
    tp_casts, tp_gefunden_bei_tp = 0, 0
    tp_ohne_tp, spieler_ohne_tp = 0, 0
    back_je_rolle = defaultdict(list)
    wahrsch = Counter()
    partien = {}
    for k in g.alle():
        if k["id"] not in gueltig:
            continue
        p = g.Partie(k)
        partien[p.id] = k
        for art, f in (("Back", backs), ("TP", tps), ("Kampf", kaempfe), ("Objective", objectives),
                       ("Gank", ganks), ("Rotation", rotationen), ("Gruppe", gruppen), ("Split", splits),
                       ("Todeszeit", todeszeiten)):
            xs = f(p)
            funde[art] += [(p.id, x) for x in xs]
            summen[art]["n"] += len(xs)
            if art == "TP":
                for x in xs:
                    tp_je_spieler[(p.id, x["pid"])] += 1
            if art == "Back":
                for pid in p.sp:
                    back_je_rolle[p.rolle(pid)].append(sum(1 for x in xs if x["pid"] == pid and x["art"] == "Back"))
        w = Counter(x["pid"] for x in tps(p, "wahrscheinlich"))
        for pid in p.sp:
            if p.hat_tp(pid):
                wahrsch["tp"] += w[pid]
                wahrsch["tp_takedowns"] += p.sp[pid]["ch"].get("teleportTakedowns") or 0
            else:
                wahrsch["ohne"] += w[pid]
            if p.hat_tp(pid):
                tp_casts += p.tp_casts(pid)
                tp_gefunden_bei_tp += tp_je_spieler[(p.id, pid)]
            else:
                spieler_ohne_tp += 1
                tp_ohne_tp += tp_je_spieler[(p.id, pid)]
    rnd = random.Random(29)
    pruef = {"Back": pruefe_back, "TP": lambda p, x: pruefe_tp(p, x, tp_je_spieler), "Kampf": pruefe_kampf,
             "Objective": pruefe_objective, "Gank": pruefe_gank, "Rotation": pruefe_rotation,
             "Gruppe": pruefe_gruppe, "Split": pruefe_split, "Todeszeit": pruefe_todeszeit}
    ergebnis = {}
    for art, liste in funde.items():
        if art == "Kampf":
            liste = [(m, x) for m, x in liste if x["kills"] >= 2 and kampf_pruefbar(x)]
        if art == "Back":
            liste = [(m, x) for m, x in liste if x["art"] == "Back"]
        probe = rnd.sample(liste, min(stichprobe, len(liste)))
        treffer, zweifel = 0, []
        for mid, x in probe:
            p = g.Partie(partien[mid])
            ok, warum = pruef[art](p, x)
            if ok:
                treffer += 1
            else:
                zweifel.append(f"{mid} {_zeile(p, art, x)} – {warum}")
        # Gegenprobe ueber ALLE Funde (billig genug)
        alle_ok = sum(1 for mid, x in liste if pruef[art](g.Partie(partien[mid]), x)[0])
        null_ok = None
        if art in NULL:
            null_ok = 0
            for mid, x in liste:
                pp = g.Partie(partien[mid])
                null_ok += bool(pruef[art](pp, NULL[art](pp, x))[0])
        ergebnis[art] = {"n": len(liste), "treffer": treffer, "probe": len(probe), "zweifel": zweifel,
                         "alle_ok": alle_ok, "null_ok": null_ok, "beispiele": [f"{m} {_zeile(g.Partie(partien[m]), art, x)}" for m, x in probe[:5]]}
    extra = {
        "tp_casts": tp_casts, "tp_gefunden": tp_gefunden_bei_tp, "tp_ohne_tp": tp_ohne_tp,
        "spieler_ohne_tp": spieler_ohne_tp, "wahrsch": wahrsch,
        "backs_je_rolle": {r: statistics.mean(v) for r, v in back_je_rolle.items() if r},
        "tp_arten": Counter(x["art"] for _, x in funde["TP"]),
        "kampf_2plus": sum(1 for _, x in funde["Kampf"] if x["kills"] >= 2),
        "einzelkills": sum(1 for _, x in funde["Kampf"] if x["kills"] == 1),
        "obj_umkaempft": Counter((x["typ"], x["umkaempft"]) for _, x in funde["Objective"]),
        "back_kauf": Counter((x["art"], x["kauf"]) for _, x in funde["Back"]),
        "partien": len(partien),
    }
    return ergebnis, extra


def schreiben(ergebnis: dict, extra: dict) -> None:
    n = extra["partien"]
    z = ["# Ableitungen und ihre Pruefung (Auftrag 029, Schritt 3)", "",
         f"{n} gueltige Partien. Je Ableitung 50 zufaellige Funde (Zufall 29), Gegenprobe aus Daten, die die "
         "Ableitung selbst nicht benutzt. **alle** = dieselbe Gegenprobe ueber alle Funde. Back: nur echte Backs "
         "(ohne Kauf nach Tod); Kampf: nur >= 2 Kills und <= 10 s neben einer vollen Minute (sonst an Positionen "
         "nicht pruefbar).", "",
         "**Nullprobe** = dieselbe Gegenprobe mit falschem Ort bzw. falscher Zeit (Kampf an der Diagonale gespiegelt, "
         "Objective 3 min spaeter, Gank/Split andere Lane, Rotation alte Zone, Gruppe gespiegelt, "
         "Back am gegnerischen Laden, Todeszeit halb so lang). Liegt sie nah an **alle**, trennt die Gegenprobe nicht.", "",
         "| Ableitung | Funde | je Partie | Stichprobe Treffer | Zweifel | alle Funde stimmig | Nullprobe |",
         "|---|---:|---:|---:|---:|---:|---:|"]
    for art, r in ergebnis.items():
        alle = f"{r['alle_ok'] / r['n']:.0%}" if r["alle_ok"] is not None and r["n"] else "–"
        null = f"{r['null_ok'] / r['n']:.0%}" if r.get("null_ok") is not None and r["n"] else "–"
        z.append(f"| {art} | {r['n']} | {r['n'] / n:.1f} | {r['treffer']}/{r['probe']} | {len(r['zweifel'])} | {alle} "
                 f"| {null} |")
    z += ["", "## Kennzahlen nebenbei", "",
          f"- **TP:** gefundene Spruenge bei TP-Spielern {extra['tp_gefunden']} von {extra['tp_casts']} TP-Einsaetzen "
          f"(`summonerXCasts`) = {extra['tp_gefunden'] / max(1, extra['tp_casts']):.0%} gefunden; bei Spielern OHNE TP "
          f"{extra['tp_ohne_tp']} Spruenge in {extra['spieler_ohne_tp']} Spieler-Partien (Fehlalarm-Quelle). "
          f"Arten: {dict(extra['tp_arten'])}. Stufe *wahrscheinlich* (normales Tempo, Weg x 1,15): "
          f"{extra['wahrsch']['tp']} bei TP-Spielern, {extra['wahrsch']['ohne']} bei Spielern ohne TP. "
          f"`teleportTakedowns` (Kills/Assists kurz nach TP) gesamt: {extra['wahrsch']['tp_takedowns']}",
          f"- **Back je Spieler und Partie:** " + ", ".join(f"{g.ROLLE_DE[r]} {v:.1f}" for r, v in
                                                         sorted(extra["backs_je_rolle"].items())),
          f"- **Ladenbesuche:** {dict(extra['back_kauf'])} (Tod = Kauf nach dem Tod, kein Back)",
          f"- **Kaempfe:** {extra['kampf_2plus']} mit >= 2 Kills, {extra['einzelkills']} Einzelkills",
          f"- **Objectives (Typ, umkaempft):** " + ", ".join(f"{a} {'umk.' if b else 'frei'} {v}"
                                                          for (a, b), v in sorted(extra["obj_umkaempft"].items()))]
    for art, r in ergebnis.items():
        z += ["", f"## {art}", "", "Beispiele:"] + [f"- {b}" for b in r["beispiele"]]
        if r["zweifel"]:
            z += ["", "Zweifel der Stichprobe:"] + [f"- {b}" for b in r["zweifel"]]
    (g.BUCH / "ableitungen.md").write_text("\n".join(z) + "\n", encoding="utf-8")


if __name__ == "__main__":
    e, x = pruefen()
    schreiben(e, x)
    print(open(g.BUCH / "ableitungen.md", encoding="utf-8").read()[:6000])
