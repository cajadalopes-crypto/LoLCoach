"""Auftrag 030, Schritt 3: die Entscheidungsmomente pruefen.

    python werkzeuge/challenger/phase1_pruefen.py      -> buecher/challenger/phase1_pruefung.md (+ Zahlen fuer den Bericht)

1. Zahlen je Rolle x Aktion x Phase (frueh < 14:00, mitte 14-25, spaet > 25), Zellen < 200 markiert; dazu je
   Rolle x Bereich, je Aufteilung und Liga.
2. 30 Momente gegen die ROHDATEN (daten/riot/*.json.gz, eigener schlichter Leser, nicht der Verdichter): Stand,
   Level, Items, Position zur Minute, Back im Fenster, Folge-Kills, Sieg.
3. Nullprobe je Aktions-Label: dieselbe Regel mit falschem Ort (gespiegelt / fremde Lane) oder falscher Zeit
   (+300 s). Quote = Anteil der echten Label-Momente, bei denen die Regel auch dann zutrifft.
4. Kein Maphack: test_kein_maphack.py (Zufallspositionen fuer ein Team, Lage muss gleich bleiben).
"""
from __future__ import annotations

import gzip
import json
import math
from collections import Counter, defaultdict

import numpy as np

import grundlage as g
import phase1 as f
import test_kein_maphack

PHASEN = [("frueh", 0, 14 * 60), ("mitte", 14 * 60, 25 * 60), ("spaet", 25 * 60, 10 ** 6)]
NULL_ART = {"Tot": "Zeit", "Back": "Zeit", "Objective": "Ort", "TP": "Zeit", "Rotation": "Zeit", "Split": "Ort",
            "Gruppe": "Ort", "Jungle": "Zeit", "Lane": "Lane", "Warten": "Zeit",
            "Unterwegs": "Zeit"}


def zahlen(D) -> list[str]:
    M, A = D["meta"], D["aktion"]
    rolle, zeit, a0 = M[:, f.MI["rolle"]], M[:, f.MI["zeit"]], A[:, f.AI["a0"]]
    z = [f"Momente gesamt: **{len(M):,}** aus {len(np.unique(M[:, 0]))} Partien".replace(",", "."), ""]
    # Aufteilung und Liga
    au = Counter(M[:, f.MI["aufteilung"]].tolist())
    z.append("Aufteilung: " + ", ".join(f"{f.AUFTEILUNGEN[k]} {v:,}".replace(",", ".") for k, v in sorted(au.items())))
    li = Counter(M[:, f.MI["liga"]].tolist())
    z.append("Liga: " + ", ".join(f"{f.LIGEN[k]} {v:,}".replace(",", ".") for k, v in sorted(li.items())))
    an = Counter(M[:, f.MI["anlass"]].tolist())
    z.append("Anlass: " + ", ".join(f"{f.ANLAESSE[k]} {v:,}".replace(",", ".") for k, v in sorted(an.items())))
    z.append("")
    # Rolle x Aktion x Phase (Primaer-Aktion a0, nur Training - daraus lernt Stufe 2)
    tr = M[:, f.MI["aufteilung"]] == 0
    z += ["**Primaer-Aktion (a0) je Rolle und Phase, nur Training.** Fett = unter 200 Faelle.", "",
          "| Rolle | Phase | " + " | ".join(f.AKTIONEN) + " |", "|---|---|" + "---:|" * len(f.AKTIONEN)]
    duenn = []
    for r, rn in enumerate(f.ROLLEN):
        for pn, a, b in PHASEN:
            m = tr & (rolle == r) & (zeit >= a) & (zeit < b)
            c = Counter(a0[m].tolist())
            zellen = []
            for k, an_ in enumerate(f.AKTIONEN):
                v = c.get(k, 0)
                if (pn == "frueh" and an_ == "Split") or (rn == "JUNGLE" and an_ in ("Rotation", "Lane")):
                    zellen.append("·")                  # per Definition 0
                    continue
                if v < 200:
                    duenn.append(f"{g.ROLLE_DE[rn]}/{pn}/{an_} ({v})")
                zellen.append(f"**{v}**" if v < 200 else f"{v:,}".replace(",", "."))
            z.append(f"| {g.ROLLE_DE[rn]} | {pn} | " + " | ".join(zellen) + " |")
    z += ["", "· = per Definition 0 (Split erst ab 14:00; Jungler haben keine Lane und rotieren per Definition nicht).",
          f"Duenne Zellen (< 200): {len(duenn)}: " + "; ".join(duenn), ""]
    # Flags (alle zutreffenden Aktionen) - auch was a0 durch den Vorrang verdeckt
    fl = A[:, f.AI["flags"]].astype(np.int64)
    z.append("Aktion trifft zu (alle Flags, nicht nur a0), Anteil aller Momente: " + ", ".join(
        f"{an_} {((fl >> k) & 1).mean():.1%}" for k, an_ in enumerate(f.AKTIONEN)))
    tp = Counter(A[:, f.AI["tp"]].tolist())
    z.append(f"TP-Feld: sicher {tp.get(1, 0):,}, unbekannt {tp.get(-1, 0):,}, kein TP-Zauber {tp.get(0, 0):,}".replace(",", "."))
    zi = A[:, f.AI["ziel"]]
    ob = (fl >> 2) & 1 == 1
    z.append("Objective-Ziele: " + ", ".join(f"{f.MONSTER[k]} {v:,}".replace(",", ".")
                                             for k, v in sorted(Counter(zi[ob].tolist()).items()) if k))
    z.append("")
    # Rolle x Bereich
    X = D["X"]
    ber = X[:, f.SP["bereich"]].astype(int)
    z += ["**Momente je Rolle und Bereich** (wo steht der Spieler im Moment):", "",
          "| Rolle | " + " | ".join(f.BEREICHE) + " |", "|---|" + "---:|" * len(f.BEREICHE)]
    for r, rn in enumerate(f.ROLLEN):
        c = Counter(ber[rolle == r].tolist())
        z.append(f"| {g.ROLLE_DE[rn]} | " + " | ".join(f"{c.get(k, 0):,}".replace(",", ".") for k in range(len(f.BEREICHE))) + " |")
    z.append("")
    # Objective-Zustand
    O = np.load(sorted(f.ZIEL.glob("teil_*.npz"))[0])["obj"]
    Oall = np.concatenate([np.load(t)["obj"] for t in sorted(f.ZIEL.glob("teil_*.npz"))])
    zst = defaultdict(Counter)
    for row in Oall:
        zst[f.MONSTER[row[2]]][f.ZUSTAENDE[row[4]]] += 1
    z += ["**Objective-Zustand (Entscheidung 3):**", "", "| Monster | frei | bestritten | umkaempft |", "|---|---:|---:|---:|"]
    for k in ("Drache", "Elder", "Larven", "Herold", "Baron"):
        c = zst[k]
        n = sum(c.values()) or 1
        z.append(f"| {k} | {c['frei']} ({c['frei'] / n:.0%}) | {c['bestritten']} ({c['bestritten'] / n:.0%}) | "
                 f"{c['umkaempft']} ({c['umkaempft'] / n:.0%}) |")
    del O
    return z


# ---------------------------------------------------------------- Rohdaten-Abgleich

def roh(mid: str):
    with gzip.open(g.RIOT / "matches" / f"{mid}.json.gz", "rt", encoding="utf-8") as fh:
        m = json.load(fh)
    with gzip.open(g.RIOT / "timelines" / f"{mid}.json.gz", "rt", encoding="utf-8") as fh:
        t = json.load(fh)
    return m, t


def roh_werte(m, t, pid: int, s: int) -> dict:
    """Schlichter, unabhaengiger Leser der Rohdaten."""
    teams = {p["participantId"]: p["teamId"] for p in m["info"]["participants"]}
    team = teams[pid]
    ev = [e for fr in t["info"]["frames"] for e in fr["events"]]
    bis = lambda e: e["timestamp"] <= s * 1000
    k_wir = sum(1 for e in ev if e["type"] == "CHAMPION_KILL" and bis(e) and teams[e["victimId"]] != team)
    k_geg = sum(1 for e in ev if e["type"] == "CHAMPION_KILL" and bis(e) and teams[e["victimId"]] == team)
    t_wir = sum(1 for e in ev if e["type"] == "BUILDING_KILL" and e.get("buildingType") == "TOWER_BUILDING"
                and bis(e) and e["teamId"] != team)
    lvl = max([1] + [e["level"] for e in ev if e["type"] == "LEVEL_UP" and e["participantId"] == pid and bis(e)])
    preis = f.preise()
    inv = []
    for e in ev:
        if e.get("participantId") != pid or not bis(e):
            continue
        if e["type"] == "ITEM_PURCHASED":
            inv.append(e["itemId"])
        elif e["type"] in ("ITEM_SOLD", "ITEM_DESTROYED") and e["itemId"] in inv:
            inv.remove(e["itemId"])
        elif e["type"] == "ITEM_UNDO":
            if e["beforeId"] in inv:
                inv.remove(e["beforeId"])
            if e["afterId"]:
                inv.append(e["afterId"])
    kills60 = sum(1 for e in ev if e["type"] == "CHAMPION_KILL" and s * 1000 < e["timestamp"] <= (s + 60) * 1000
                  and teams[e["victimId"]] != team)
    # Kauf nach dem Tod zaehlt nicht als Back: bis Respawn + 45 s (Level beim Tod aus den Roh-Ereignissen)
    tode = []
    for e in ev:
        if e["type"] == "CHAMPION_KILL" and e["victimId"] == pid:
            lv = max([1] + [x["level"] for x in ev if x["type"] == "LEVEL_UP" and x["participantId"] == pid
                            and x["timestamp"] <= e["timestamp"]])
            tode.append((e["timestamp"], e["timestamp"] + 1000 * (g.respawn(lv, e["timestamp"] / 60000) + 45)))
    # nur der ERSTE Kauf eines Ladenbesuchs (kein Kauf in den 25 s davor) - ein Besuch beginnt einmal
    kaeufe = [e["timestamp"] for e in ev if e["type"] == "ITEM_PURCHASED" and e["participantId"] == pid]
    starts = [k for i, k in enumerate(kaeufe) if i == 0 or k - kaeufe[i - 1] > 25000]
    kauf60 = any(s < math.ceil(k / 1000) <= s + 60 and k > 90000 and not any(a <= k <= b for a, b in tode)
                 for k in starts)
    pos, hp0, gold60 = None, None, None
    fr_ = t["info"]["frames"]
    if s % 60 == 0 and s // 60 < len(fr_):
        pf = fr_[s // 60]["participantFrames"][str(pid)]
        pos = (pf["position"]["x"], pf["position"]["y"])
        hp0 = pf["championStats"]["health"] == 0
        if s // 60 + 1 < len(fr_) and abs(fr_[s // 60 + 1]["timestamp"] - (s + 60) * 1000) < 2000:
            gold60 = fr_[s // 60 + 1]["participantFrames"][str(pid)]["totalGold"] - pf["totalGold"]
    sieg = next(p["win"] for p in m["info"]["participants"] if p["participantId"] == pid)
    return {"kills_wir": k_wir, "kills_gegner": k_geg, "tuerme_wir": t_wir, "level": lvl,
            "itemwert": sum(preis.get(i, 0) for i in inv), "kills_wir_60": kills60, "kauf_60": kauf60, "pos": pos,
            "sieg": int(sieg), "tot_minute": hp0, "gold_60": gold60}


def abgleich(D, partien: list[str], n: int = 30) -> tuple[list[str], dict]:
    rnd = np.random.default_rng(3030)
    M, X, A, F = D["meta"], D["X"], D["aktion"], D["folge"]
    # Haelfte volle Minuten (Position pruefbar), Haelfte Ereignis-Momente
    minute = np.where(M[:, f.MI["anlass"]] == 0)[0]
    sonst = np.where(M[:, f.MI["anlass"]] != 0)[0]
    idx = list(rnd.choice(minute, n // 2, replace=False)) + list(rnd.choice(sonst, n - n // 2, replace=False))
    stimmt = Counter()
    zeilen, abw = [], []
    for i in idx:
        mid = partien[M[i, 0]]
        pid, s = int(M[i, 1]), int(M[i, f.MI["zeit"]])
        m, t = roh(mid)
        r = roh_werte(m, t, pid, s)
        back_bit = bool((A[i, f.AI["flags"]] >> 1) & 1)
        vergleiche = {
            "kills_wir": X[i, f.SP["kills_wir"]] == r["kills_wir"],
            "kills_gegner": X[i, f.SP["kills_gegner"]] == r["kills_gegner"],
            "tuerme_wir": X[i, f.SP["tuerme_wir"]] == r["tuerme_wir"],
            "level": X[i, f.SP["level"]] == r["level"],
            "itemwert": X[i, f.SP["itemwert"]] == r["itemwert"],
            "back_60": back_bit == r["kauf_60"],
            "kills_wir_60": np.isnan(F[i, f.FI["kills_wir_60"]]) or F[i, f.FI["kills_wir_60"]] == r["kills_wir_60"],
            "sieg": M[i, f.MI["sieg"]] == r["sieg"],
        }
        if r["pos"] is not None:
            vergleiche["pos_minute"] = abs(X[i, f.SP["x"]] - r["pos"][0]) < 1 and abs(X[i, f.SP["y"]] - r["pos"][1]) < 1
            r["pos_minute"] = r["pos"]
            vergleiche["tot_minute"] = bool(X[i, f.SP["tot"]]) == r["tot_minute"]
            r["tot_minute"] = r["tot_minute"]
        if r["gold_60"] is not None:
            vergleiche["gold_60"] = abs(F[i, f.FI["gold_60"]] - r["gold_60"]) < 1
        for k, v in vergleiche.items():
            stimmt[(k, bool(v))] += 1
            if not v:
                abw.append(f"{mid} pid {pid} {g.uhr(s)}: {k} Moment={_wert(k, X, F, A, M, i)} roh={r.get(k, r['kauf_60'])}")
        a0 = int(A[i, f.AI["a0"]])
        zeilen.append(f"| {mid} | {g.ROLLE_DE[f.ROLLEN[M[i, f.MI['rolle']]]]} | {g.uhr(s)} | "
                      f"{f.ANLAESSE[M[i, f.MI['anlass']]]} | {f.BEREICHE[int(X[i, f.SP['bereich']])]} | "
                      f"{int(X[i, f.SP['kills_wir']])}:{int(X[i, f.SP['kills_gegner']])} | L{int(X[i, f.SP['level']])} | "
                      f"{f.AKTIONEN[a0] if a0 >= 0 else '–'} | {_folge(F, i)} | "
                      f"{'ok' if all(vergleiche.values()) else 'ABWEICHUNG'} |")
    return zeilen, {"stimmt": stimmt, "abw": abw}


def _wert(k, X, F, A, M, i):
    if k == "back_60":
        return bool((A[i, f.AI["flags"]] >> 1) & 1)
    if k == "kills_wir_60":
        return F[i, f.FI["kills_wir_60"]]
    if k == "sieg":
        return M[i, f.MI["sieg"]]
    if k.startswith("tot_minute"):
        return bool(X[i, f.SP["tot"]])
    if k == "gold_60":
        return F[i, f.FI["gold_60"]]
    if k == "pos_minute":
        return (round(float(X[i, f.SP["x"]])), round(float(X[i, f.SP["y"]])))
    return X[i, f.SP[k]]


def _folge(F, i):
    v = F[i, f.FI["kills_wir_60"]]
    if np.isnan(v):
        return "Ende"
    return (f"60 s: Kills {int(v)}:{int(F[i, f.FI['kills_gegner_60']])}, Gold {int(F[i, f.FI['gold_60']])}"
            + (", Tod" if F[i, f.FI["tod_60"]] else ""))


# ---------------------------------------------------------------- Nullprobe

def nullprobe(partien: list[str], n_partien: int = 300) -> dict:
    rnd = np.random.default_rng(300)
    echt = Counter()
    treffer = Counter()
    for nr in rnd.choice(len(partien), n_partien, replace=False):
        p = g.Partie(g.lade(partien[nr]))
        R = f.Raster(p)
        for x in __import__("ableitungen").tps(p, "sicher"):
            R.tp_sicher.setdefault(x["pid"], []).append(int(math.ceil(x["t"])))
        for pid in range(1, 11):
            sek = np.array([s for s, _ in f.zeitpunkte(R, pid)], np.int64)
            sek = sek[sek + 300 + 70 <= p.dauer]
            if not len(sek):
                continue
            fl, *_ = f.aktion_flags(R, pid, sek)
            varianten = {"Zeit": f.aktion_flags(R, pid, sek + 300)[0],
                         "Ort": f.aktion_flags(R, pid, sek, spiegel=True)[0],
                         "Lane": f.aktion_flags(R, pid, sek, fremde_lane=True)[0]}
            for k, an in enumerate(f.AKTIONEN):
                m = (fl >> k) & 1 == 1
                nv = varianten[NULL_ART[an]]
                name = an if an != "Jungle" else ("Jungle (Jungler)" if p.rolle(pid) == "JUNGLE" else "Jungle (Laner)")
                echt[name] += int(m.sum())
                treffer[name] += int((((nv >> k) & 1) == 1)[m].sum())
    return {an: (echt[an], treffer[an] / max(1, echt[an])) for an in echt}


def main():
    partien = json.loads((f.ZIEL / "partien.json").read_text(encoding="utf-8"))
    D = f.lade()
    z = ["# Pruefung der Entscheidungsmomente (Auftrag 030, Schritt 3)", ""]
    z += ["## 1. Zahlen", ""] + zahlen(D)
    zeilen, ab = abgleich(D, partien)
    st = ab["stimmt"]
    felder = sorted({k for k, _ in st})
    _, ab300 = abgleich(D, partien, 300)
    st3 = ab300["stimmt"]
    z += ["", "## 2. 30 Momente gegen die Rohdaten", "",
          "Eigener schlichter Leser der Riot-JSON (nicht der Verdichter). Feld stimmt / geprueft:", "",
          " · ".join(f"{k} {st[(k, True)]}/{st[(k, True)] + st[(k, False)]}" for k in felder), "",
          "Dasselbe an 300 Momenten: " + " · ".join(f"{k} {st3[(k, True)]}/{st3[(k, True)] + st3[(k, False)]}"
                                                     for k in sorted({k for k, _ in st3})), "",
          "Hinweis: `tot_minute` ist zur vollen Minute per Bau gleich (die Todeszeit wird an den Minuten mit Leben 0/>0 "
          "gekappt); dazwischen gilt die Formel.", "",
          "| Partie | Rolle | Zeit | Anlass | Bereich | Kills | Level | Aktion 60 s | Folge | Rohdaten |",
          "|---|---|---|---|---|---|---|---|---|---|"] + zeilen
    if ab["abw"]:
        z += ["", "Abweichungen:"] + [f"- {a}" for a in ab["abw"]]
    nu = nullprobe(partien)
    z += ["", "## 3. Nullprobe je Aktions-Label (300 Partien)", "",
          "Quote = Anteil der Momente mit diesem Label, bei denen dieselbe Regel auch mit falschem Ort oder falscher "
          "Zeit zutrifft. Klar unter 100 % = das Label haengt an Ort/Zeit des Moments.", "",
          "| Aktion | Momente | Nullprobe | Quote |", "|---|---:|---|---:|"]
    for an, (n, q) in nu.items():
        z.append(f"| {an} | {n:,} | {NULL_ART[an.split(' ')[0]]} | {q:.0%} |".replace(",", "."))
    mh = test_kein_maphack.main(30)
    sab = test_kein_maphack.sabotage(5)
    z += ["", "## 4. Kein Maphack", "",
          f"`test_kein_maphack.py`, 30 Partien, {mh['momente']:,} Lagen: Spalten verletzt {mh['verletzt']}, "
          f"Lane-Gegner-Ort weiter als 1200 {mh['lg_zu_weit']}, Zufallspositionen kamen in {mh['lg_geaendert']:,} "
          f"Lagen bei lg_* an (der Test sieht also etwas). **{'BESTANDEN' if mh['bestanden'] else 'DURCHGEFALLEN'}**. "
          f"Sabotage-Gegenprobe (Jungler-Position in eine Spalte geschrieben): {sab['verletzt']:,} von "
          f"{sab['momente']:,} Lagen verletzt, Test {'faellt durch (richtig)' if not sab['bestanden'] else 'BESTEHT - blind!'}."
          .replace(",", ".")]
    (g.BUCH / "phase1_pruefung.md").write_text("\n".join(z) + "\n", encoding="utf-8")
    print("\n".join(z))


if __name__ == "__main__":
    main()
