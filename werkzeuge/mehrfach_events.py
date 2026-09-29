"""Auftrag 025, 3: Szenarien mit mehreren teilnehmbaren Events gleichzeitig - aus echten Aufnahmen, das Soll-Play legt
ein blinder Challenger-Kritiker fest (er sieht nur die Lage, nie den Coach).

    python werkzeuge/mehrfach_events.py finden        Momente aus buecher/protokolle/proben/pakete_025/*.json suchen,
                                                      je Moment die Lage in Worten (welt.text) holen, Kritiker-Auftrag
                                                      schreiben (proben/pakete_025/mehrfach_auftrag.txt)
    python werkzeuge/mehrfach_events.py toml          aus proben/pakete_025/mehrfach_kritik.json die Szenarien
                                                      tests/szenarien/<stamm>_auftrag025.toml schreiben
Ein Moment: der Spieler lebt, kaempft nicht, ist nicht in der Basis, und binnen 8 s gibt es >= 2 teilnehmbare Events
aus verschiedenen Gruppen (Mitspieler-Kampf <= 20 s Weg, Objective bald/da, Lane-Gegner weg, Kanone bald, Gold fuer
ein Item, erahnter Kampf, gefallener Turm). Hoechstens 3 je Partie, >= 90 s auseinander.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

WURZEL = Path(__file__).resolve().parent.parent
PROBE = WURZEL / "buecher" / "protokolle" / "proben" / "pakete_025"
SZEN = WURZEL / "tests" / "szenarien"
TEILNEHMBAR = {"KAMPF": "Kampf", "OBJ_BALD": "Objective", "OBJ_DA": "Objective", "LANE_WEG": "Lane",
               "KANONE_BALD": "Welle", "GOLD_SPIKE": "Kauf", "ERAHNT_KAMPF": "Kampf", "TURM_FAELLT": "Struktur"}
OPTIONEN = {
    "A": ("Welle farmen, freezen oder crashen (auf der eigenen Lane bleiben)",
          ["FARMEN", "WELLE_REIN_UND_BACK", "STAPELN", "WELLE_DRUECKEN", "UNTER_TURM_FARMEN", "WELLE_HALTEN",
           "WELLE_KLAEREN"]),
    "B": ("Back (zurueck in die Basis, einkaufen)", ["BACK_JETZT", "WELLE_REIN_UND_BACK", "KAUFEN"]),
    "C": ("Dem Mitspieler im Kampf helfen", ["HILFE", "ANNEHMEN", "MIT_GRUPPE", "ZUR_GRUPPE", "REIN"]),
    "D": ("Objective (Drache/Herold/Baron/Larven) vorbereiten, nehmen oder bestreiten",
          ["NEHMEN", "BESTREITEN", "ANLAUFEN", "TAUSCHEN", "ABGEBEN_TAUSCHEN"]),
    "E": ("Turm oder Platten druecken", ["PLATTEN", "DRUECKEN", "MIT_GRUPPE"]),
    "F": ("Zurueck unter den Turm / sicher warten", ["ZURUECK", "HALTEN_UNTER_TURM", "HALTEN", "RAUS", "WELLE_HALTEN"]),
    "G": ("Rotieren: zur Gruppe, zu einer anderen Lane oder per TP", ["ZUR_GRUPPE", "WOHIN", "SEITENWELLE", "TP_SPIEL",
                                                                    "WOHIN_TP_LANE"]),
}


def _uhr(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


def momente() -> list[dict]:
    aus = []
    for f in sorted(PROBE.glob("2026-*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        takte = {round(x["t"]): x for x in d["takte"]}
        ev = [e for e in d["events"] if e["typ"] in TEILNEHMBAR and not e.get("still")
              and not (e["typ"] == "KAMPF" and (e.get("weg") or 99) > 20)]
        je = []
        for e in ev:
            fenster = [x for x in ev if e["t"] <= x["t"] <= e["t"] + 8.0]
            gruppen = {TEILNEHMBAR[x["typ"]] for x in fenster}
            x = takte.get(round(e["t"] + 8.0)) or takte.get(round(e["t"] + 7.0))
            if len(gruppen) < 2 or x is None or x["tot"] or x["basis"] or x["modus"] in ("KAMPF", "TOT", "BASIS", None):
                continue
            if any(abs(e["t"] - m["t"]) < 90.0 for m in je):
                continue
            je.append({"stamm": d["stamm"], "t": round(e["t"] + 8.0, 1),
                       "events": [f"{x['typ']} {x.get('ort') or ''} {' '.join(x['wer'])}".strip() for x in fenster]})
            if len(je) >= 3:
                break
        aus += je
    return aus


def lagen(ms: list[dict]) -> None:
    """Die Lage in Worten (welt.text) zu jedem Moment - ein Nachspiel je Partie, parallel."""
    from concurrent.futures import ProcessPoolExecutor
    je: dict = {}
    for m in ms:
        je.setdefault(m["stamm"], []).append(m["t"])
    with ProcessPoolExecutor(len(je)) as ex:
        for stamm, texte in zip(je, ex.map(_lage_lauf, [(s, z) for s, z in je.items()])):
            for m in ms:
                if m["stamm"] == stamm:
                    m["lage"] = texte.get(m["t"])


def _lage_lauf(arg) -> dict:
    stamm, zeiten = arg
    import nachspielen as ns
    from lolcoach import welt
    offen = sorted(zeiten)
    aus = {}

    class Fertig(Exception):
        pass

    def bt(p, werk, kern, plan):
        while offen and p.zeit >= offen[0]:
            t = offen.pop(0)
            try:
                w = welt.bauen(kern, p, kern._lagebild)
                aus[t] = welt.text(w) if w is not None else None
            except Exception as e:
                aus[t] = f"(Lage nicht gebaut: {e})"
        if not offen:
            raise Fertig

    try:
        ns.durchspielen(ns.pfad_zu(stamm), beim_takt=bt)
    except Fertig:
        pass
    return aus


def finden() -> None:
    ms = momente()
    lagen(ms)
    ms = [m for m in ms if m.get("lage")]
    for i, m in enumerate(ms, 1):
        m["id"] = f"M{i:02d}"
    (PROBE / "mehrfach_momente.json").write_text(json.dumps(ms, ensure_ascii=False, indent=1), encoding="utf-8")
    teile = ["Du bist ein Challenger-Coach (League of Legends). Du siehst nur die LAGE eines Moments - nicht, was ein "
             "Coach gesagt hat. Entscheide je Moment das BESTE Play fuer den Spieler (Riven/Graves/..., siehe DU in der "
             "Lage) aus den Optionen A-G. Sind zwei gleichwertig, nenn beide. Harte Regeln: kein Trade/All-in ohne "
             "Kill-Check, nichts nach vorn unter 40 % Leben, ein Kampf nur mit Weg <= 8 s und nicht klar verloren.",
             "OPTIONEN:\n" + "\n".join(f"{k}: {v[0]}" for k, v in OPTIONEN.items()),
             "Schreib das Ergebnis als JSON-Datei nach " + str(PROBE / "mehrfach_kritik.json").replace("\\", "/") +
             ' im Format {"M01": {"beste": ["A"], "warum": "ein Satz"}, ...}. Antworte danach nur "fertig".']
    for m in ms:
        teile.append(f"=== {m['id']} ({_uhr(m['t'])}) - gleichzeitig: {'; '.join(m['events'])}\n{m['lage']}")
    (PROBE / "mehrfach_auftrag.txt").write_text("\n\n".join(teile), encoding="utf-8")
    print(f"{len(ms)} Momente -> {PROBE / 'mehrfach_auftrag.txt'}")


def toml() -> None:
    ms = {m["id"]: m for m in json.loads((PROBE / "mehrfach_momente.json").read_text(encoding="utf-8"))}
    kritik = json.loads((PROBE / "mehrfach_kritik.json").read_text(encoding="utf-8"))
    je: dict = {}
    for mid, k in kritik.items():
        m = ms.get(mid)
        if m is None or not k.get("beste"):
            continue
        soll = sorted({a for o in k["beste"] for a in OPTIONEN.get(o, ("", []))[1]})
        je.setdefault(m["stamm"], []).append((m, k, soll))
    for stamm, liste in je.items():
        ziel = SZEN / f"{stamm}_auftrag025.toml"
        z = [f"# Auftrag 025, 3: Momente mit mehreren teilnehmbaren Events (werkzeuge/mehrfach_events.py). Das Soll-Play",
             "# legte ein blinder Challenger-Kritiker fest (nur die Lage, nie der Coach).", "",
             f'aufnahme = "{stamm}"']
        # Spielmodus und Bots wie in den anderen Szenario-Dateien dieser Aufnahme (Practice Tool, Botpartie)
        for alt in sorted(SZEN.glob(f"{stamm}*.toml")):
            if alt.name == ziel.name:
                continue
            kopf = [x for x in alt.read_text(encoding="utf-8").splitlines() if x.startswith(("spielmodus", "bots"))]
            if kopf:
                z += kopf
                break
        z.append("")
        for m, k, soll in liste:
            z += ["[[szenario]]", f'id = "{m["id"].lower()}-mehrere-events-{_uhr(m["t"]).replace(":", "")}"',
                  f'zeit = "{_uhr(m["t"])}"', f"quelle = {json.dumps('; '.join(m['events']), ensure_ascii=False)}",
                  f"lage = {json.dumps('Kritiker: ' + ', '.join(k['beste']) + ' - ' + k.get('warum', ''), ensure_ascii=False)}",
                  f"soll = {json.dumps(soll)}",
                  'warum = "Buch 15, 0.3: das beste der gleichzeitigen Plays (blinder Kritiker)."', ""]
        ziel.write_text("\n".join(z), encoding="utf-8")
        print(ziel)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    {"finden": finden, "toml": toml}[sys.argv[1]]()
