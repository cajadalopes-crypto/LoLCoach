"""Auftrag 020, 3: den Kampfrechner an Riot-Partien (Match-V5) eichen.

Liest, was `werkzeuge/riot_download.py` nach `daten/riot/` geladen hat (laedt selbst nichts).
- Kaempfe: Haeufungen von CHAMPION_KILL (<= LUECKE_S zum vorigen Kill, <= ABSTAND vom ersten Kill des Kampfs).
- Beteiligte: Killer, Assists, Opfer und alle, die das Opfer traf oder die es trafen (victimDamageDealt/-Received).
- Stand: Werte aus `championStats` des Minuten-Frames davor (genau: AD, AP, Ruestung, MR, Leben, Tempo,
  Durchdringung), Level aus dem Frame, Raenge aus SKILL_LEVEL_UP bis zum Kampf. Leben zu Kampfbeginn und Ults kennt
  die Zeitleiste nicht: voll und bereit, fuer beide Seiten gleich.
- Sieger: die Seite mit weniger Toten; Gleichstand zaehlt nicht.
- Schwelle: die kleinste, bei der klar_vorn UND klar_hinten je >= 80 % treffen; Abdeckung = Anteil klar_*.

    python werkzeuge/kampf_eichung_riot.py [--neu] [--schreiben]
Ergebnis: stratege_probe_020/kaempfe.json.gz (je Kampf Staerke und Ausgang), mit --schreiben wissen/kampf_eichung.toml.
"""
from __future__ import annotations

import datetime
import gzip
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HIER = Path(__file__).resolve().parent
WURZEL = HIER.parent
sys.path.insert(0, str(WURZEL))
RIOT = WURZEL / "daten" / "riot"
AUS = WURZEL / "buecher" / "protokolle" / "proben" / "stratege_probe_020"
ZIEL = WURZEL / "wissen" / "kampf_eichung.toml"
LUECKE_S, ABSTAND = 15.0, 2000.0
TOR_TREFFER, TOR_ABDECKUNG = 0.80, 0.30
SLOT = {1: "Q", 2: "W", 3: "E", 4: "R"}


def _kaempfe(events: list[dict]) -> list[list[dict]]:
    kills = sorted((e for e in events if e["type"] == "CHAMPION_KILL"), key=lambda e: e["timestamp"])
    aus: list[list[dict]] = []
    for e in kills:
        if aus:
            k = aus[-1]
            p0, p = k[0]["position"], e["position"]
            if e["timestamp"] - k[-1]["timestamp"] <= LUECKE_S * 1000 and \
                    ((p["x"] - p0["x"]) ** 2 + (p["y"] - p0["y"]) ** 2) ** 0.5 <= ABSTAND:
                k.append(e)
                continue
        aus.append([e])
    return aus


def eine(datei: str) -> list[dict]:
    from lolcoach.kampf_rechner import Kaempfer, rechne, werte_aus_riot
    name = Path(datei).name
    try:
        tl = json.load(gzip.open(RIOT / "timelines" / name, "rt", encoding="utf-8"))["info"]
        m = json.load(gzip.open(RIOT / "matches" / name, "rt", encoding="utf-8"))["info"]
    except (OSError, ValueError, KeyError):
        return []
    if m.get("gameDuration", 0) < 900:
        return []                                             # Remakes und Aufgaben
    teil = {p["participantId"]: p for p in m["participants"]}
    frames = tl["frames"]
    events = [e for f in frames for e in f["events"]]
    aus = []
    for kampf in _kaempfe(events):
        t0 = kampf[0]["timestamp"]
        f = frames[min(len(frames) - 1, max(0, int(t0 // 60000)))]
        dabei = set()
        for e in kampf:
            dabei |= {e.get("killerId"), e.get("victimId"), *e.get("assistingParticipantIds", [])}
            for d in e.get("victimDamageReceived", []) + e.get("victimDamageDealt", []):
                dabei.add(d.get("participantId"))
        dabei = {i for i in dabei if i in teil}
        raenge = {i: {"Q": 0, "W": 0, "E": 0, "R": 0} for i in dabei}
        for e in events:
            if e["type"] == "SKILL_LEVEL_UP" and e["timestamp"] < t0 and e.get("participantId") in raenge \
                    and e.get("levelUpType") == "NORMAL" and e.get("skillSlot") in SLOT:
                raenge[e["participantId"]][SLOT[e["skillSlot"]]] += 1
        kaempfer = []
        for i in sorted(dabei):
            pf = f["participantFrames"].get(str(i), {})
            lv = int(pf.get("level") or 1)
            cid = teil[i]["championName"]
            kaempfer.append(Kaempfer(cid, "wir" if teil[i]["teamId"] == 100 else "sie", lv,
                                     raenge=raenge[i], werte=werte_aus_riot(cid, lv, pf.get("championStats", {})),
                                     name=cid))
        tote = {"wir": 0, "sie": 0}
        for e in kampf:
            v = teil.get(e.get("victimId"))
            if v:
                tote["wir" if v["teamId"] == 100 else "sie"] += 1
        u = rechne(kaempfer, 1.0)
        if u is None:
            continue
        aus.append({"spiel": name, "t": round(t0 / 1000), "wir": sum(k.team == "wir" for k in kaempfer),
                    "sie": sum(k.team == "sie" for k in kaempfer), "kills": len(kampf), "staerke": u.staerke,
                    "sieger": "wir" if tote["wir"] < tote["sie"] else "sie" if tote["sie"] < tote["wir"] else None})
    return aus


def auswerten(kaempfe: list[dict], s: float) -> dict:
    mit = [k for k in kaempfe if k["sieger"]]
    vorn = [k for k in mit if k["staerke"] >= s and k["staerke"] > 0]
    hinten = [k for k in mit if k["staerke"] <= -s and k["staerke"] < 0]
    knapp = [k for k in mit if -s < k["staerke"] < s]
    q = lambda xs, w: round(sum(k["sieger"] == w for k in xs) / len(xs), 4) if xs else None
    return {"schwelle": s, "kaempfe": len(mit), "klar_vorn": len(vorn), "treffer_vorn": q(vorn, "wir"),
            "klar_hinten": len(hinten), "treffer_hinten": q(hinten, "sie"), "knapp": len(knapp),
            "knapp_wir_gewinnt": q(knapp, "wir"), "abdeckung": round((len(vorn) + len(hinten)) / max(1, len(mit)), 4)}


MENGEN = {
    "alle": lambda k: True,
    "je_seite_2": lambda k: k["wir"] >= 2 and k["sie"] >= 2,        # echte Teamkaempfe
    "gleich_viele": lambda k: k["wir"] == k["sie"],                 # Koepfe zaehlen hilft nicht
}


def _haelt(e: dict) -> bool:
    return bool(e["treffer_vorn"] and e["treffer_hinten"] and e["treffer_vorn"] >= TOR_TREFFER
                and e["treffer_hinten"] >= TOR_TREFFER and e["klar_vorn"] >= 30 and e["klar_hinten"] >= 30)


def eichen(kaempfe: list[dict]) -> tuple[float, dict]:
    """Die kleinste Schwelle, bei der beide klaren Urteile >= 80 % treffen - in JEDER Menge. Grund: die Beteiligten
    stammen aus den Kill-Ereignissen (wer starb, wer traf), deshalb gewinnt in `alle` fast immer die Seite mit mehr
    Koepfen (Basis "mehr Koepfe" 96 %); erst bei gleich vielen zeigt sich, ob der Rechner mehr kann."""
    for i in range(0, 101):
        s = i / 100
        je = {n: auswerten([k for k in kaempfe if f(k)], s) for n, f in MENGEN.items()}
        if all(_haelt(e) for e in je.values()):
            return s, je
    return 1.0, {n: auswerten([k for k in kaempfe if f(k)], 1.0) for n, f in MENGEN.items()}


def basis_koepfe(kaempfe: list[dict]) -> dict:
    """Vergleich: "die Seite mit mehr Beteiligten gewinnt" (nur Kaempfe mit ungleicher Zahl)."""
    ung = [k for k in kaempfe if k["sieger"] and k["wir"] != k["sie"]]
    return {"kaempfe": len(ung), "treffer": round(sum((k["wir"] > k["sie"]) == (k["sieger"] == "wir") for k in ung)
                                                  / max(1, len(ung)), 4)}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    AUS.mkdir(exist_ok=True)
    datei = AUS / "kaempfe.json.gz"
    if "--neu" in sys.argv or not datei.exists():
        namen = sorted(str(p) for p in (RIOT / "timelines").glob("*.json.gz") if (RIOT / "matches" / p.name).exists())
        with ProcessPoolExecutor() as ex:
            kaempfe = [k for teil in ex.map(eine, namen, chunksize=8) for k in teil]
        with gzip.open(datei, "wt", encoding="utf-8") as f:
            json.dump({"partien": len(namen), "kaempfe": kaempfe}, f)
    with gzip.open(datei, "rt", encoding="utf-8") as f:
        d = json.load(f)
    kaempfe = d["kaempfe"]
    s, je = eichen(kaempfe)
    tor = all(_haelt(e) for e in je.values()) and je["je_seite_2"]["abdeckung"] >= TOR_ABDECKUNG \
        and je["alle"]["abdeckung"] >= TOR_ABDECKUNG
    print(json.dumps({"partien": d["partien"], "schwelle": s, "tor": tor, **je, "basis_koepfe": basis_koepfe(kaempfe)},
                     ensure_ascii=False, indent=1))
    if "--schreiben" in sys.argv:
        stand = datetime.date.today().isoformat()
        z = ["# Kampfrechner (lolcoach/kampf_rechner.py) an Riot-Partien geeicht - werkzeuge/kampf_eichung_riot.py, Auftrag 020",
             f'stand = "{stand}"', 'quelle = "Match-V5 EUW Solo-Queue, Challenger bis Master (werkzeuge/riot_download.py)"',
             f"partien = {d['partien']}", f"schwelle = {s}            # |Staerke| ab hier klar_vorn / klar_hinten",
             f"tor = {'true' if tor else 'false'}                # >= 80 % je klares Urteil in jeder Menge, >= 30 % Abdeckung", ""]
        for n, e in je.items():
            z += [f"[{n}]"] + [f"{k} = {v}" for k, v in e.items() if k != "schwelle" and v is not None] + [""]
        alt = ZIEL.read_text(encoding="utf-8") if ZIEL.exists() else ""
        if "[aufnahmen]" in alt:                 # die Probe an Carlos' Aufnahmen bleibt stehen (von Hand gepflegt)
            z.append(alt[alt.index("[aufnahmen]"):].rstrip())
        ZIEL.write_text("\n".join(z) + "\n", encoding="utf-8")
        print("->", ZIEL)


if __name__ == "__main__":
    main()
