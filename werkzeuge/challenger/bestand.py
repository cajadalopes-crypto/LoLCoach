"""Auftrag 029, Schritte 1 und 2: Datenbestand pruefen, Liga je Spieler, Feldkatalog.

    python werkzeuge/challenger/bestand.py            verdichtet Neues, schreibt bestand.md + feldkatalog.md
    python werkzeuge/challenger/bestand.py --liga     holt vorher die drei Ligalisten (3 Riot-Abrufe)

Liga = Stand der Ligalisten beim Abruf (nicht zur Zeit der Partie). Wer in keiner der drei Listen steht, ist heute
unter Master (oder hat den Namen gewechselt - die PUUID bleibt, das zaehlt nicht).
Der Schluessel kommt aus geheim/riot_key.txt ueber werkzeuge/riot_download.py und wird nie ausgegeben.
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from collections import Counter, defaultdict

import grundlage as g

LIGA_DATEI = g.ABLAGE / "liga.json"
MIN_DAUER = 15 * 60


def liga_holen() -> dict:
    sys.path.insert(0, str(g.WURZEL / "werkzeuge"))
    import riot_download as rd  # nur benutzt, nicht geaendert
    rd.KEY = rd.schluessel()
    zuordnung, je = {}, {}
    for liga, pfad in (("Challenger", "challengerleagues"), ("Grandmaster", "grandmasterleagues"),
                       ("Master", "masterleagues")):
        d = rd.hole(f"{rd.PLATTFORM}/lol/league/v4/{pfad}/by-queue/RANKED_SOLO_5x5") or {}
        eintraege = d.get("entries", [])
        je[liga] = len(eintraege)
        for e in eintraege:
            if e.get("puuid"):
                zuordnung.setdefault(e["puuid"], liga)
    daten = {"stand": time.strftime("%Y-%m-%d %H:%M"), "abrufe": 3, "je_liste": je, "spieler": zuordnung}
    g.ABLAGE.mkdir(parents=True, exist_ok=True)
    LIGA_DATEI.write_text(json.dumps(daten), encoding="utf-8")
    return daten


def gueltig(k: dict) -> tuple[bool, str]:
    """Remakes, zu kurz, falsche Queue, Rollen unvollstaendig, Zeitleiste fehlt -> heraus (mit Grund)."""
    if k["queue"] != 420:
        return False, "Queue"
    if any(s["gameEndedInEarlySurrender"] for s in k["sp"]) or k["dauer"] < MIN_DAUER:
        return False, "Remake/unter 15 min"
    for team in (g.BLAU, g.ROT):
        if sorted(s["teamPosition"] for s in k["sp"] if s["teamId"] == team) != sorted(g.ROLLEN):
            return False, "Rollen unvollstaendig"
    if len(k["frames"]) < k["dauer"] // 60:
        return False, "Zeitleiste kurz"
    return True, ""


def pruefen() -> dict:
    liga = json.loads(LIGA_DATEI.read_text(encoding="utf-8")) if LIGA_DATEI.exists() else {"spieler": {}}
    zuordnung = liga["spieler"]
    raus = Counter()
    versionen, dauern, zeit = Counter(), [], []
    game_ids = Counter()
    doppelt_spieler = 0
    tabelle = defaultdict(Counter)          # liga -> rolle -> Spieler-Partien
    spieler_je_liga = defaultdict(set)
    sieger_ohne_frames = 0
    gueltige = []
    felder, nenner = Counter(), Counter()
    ende = Counter()
    n = 0
    for d in g.alle(mit_feldern=True):
        k = d["partie"]
        n += 1
        felder.update(d["felder"])
        nenner.update(d["nenner"])
        game_ids[k["id"]] += 1
        ende[k["ende"]] += 1
        ok, grund = gueltig(k)
        if not ok:
            raus[grund] += 1
            continue
        gueltige.append(k["id"])
        versionen[".".join(k["version"].split(".")[:2])] += 1
        dauern.append(k["dauer"] / 60)
        zeit.append(k["start"])
        pu = [s["puuid"] for s in k["sp"]]
        if len(set(pu)) != len(pu):
            doppelt_spieler += 1
        if not k["frames"]:
            sieger_ohne_frames += 1
        for s in k["sp"]:
            l = zuordnung.get(s["puuid"], "unter Master")
            tabelle[l][s["teamPosition"]] += 1
            spieler_je_liga[l].add(s["puuid"])
    g.ABLAGE.mkdir(parents=True, exist_ok=True)
    (g.ABLAGE / "gueltig.json").write_text(json.dumps(gueltige), encoding="utf-8")
    q = statistics.quantiles(dauern, n=4) if len(dauern) > 3 else [0, 0, 0]
    return {"n": n, "raus": raus, "gueltig": len(gueltige), "versionen": versionen, "dauer": (q, min(dauern), max(dauern)),
            "zeitraum": (min(zeit), max(zeit)), "doppelt_partie": sum(1 for v in game_ids.values() if v > 1),
            "doppelt_spieler": doppelt_spieler, "tabelle": tabelle, "spieler_je_liga": spieler_je_liga,
            "liga": liga, "felder": felder, "nenner": nenner, "ende": ende}


def _datum(ms):
    return time.strftime("%d.%m.%Y", time.localtime(ms / 1000))


def schreiben(r: dict) -> None:
    ligen = ["Challenger", "Grandmaster", "Master", "unter Master"]
    z = ["# Phase 0 – Datenbestand (Auftrag 029)", "",
         f"Stand {time.strftime('%d.%m.%Y %H:%M')}; Ligalisten vom {r['liga'].get('stand', '–')} "
         f"(Listen: {r['liga'].get('je_liste', {})}).", "",
         f"- Partien geladen: **{r['n']}**, gueltig: **{r['gueltig']}**; heraus: "
         + (", ".join(f"{k} {v}" for k, v in r["raus"].items()) or "keine"),
         f"- Spielende (`endOfGameResult`): {dict(r['ende'])}",
         f"- Patch (`gameVersion`): " + ", ".join(f"{k}: {v}" for k, v in r["versionen"].most_common()),
         f"- Queue: nur 420 (Solo/Duo) nach dem Filter",
         f"- Dauer (min): Quartile {r['dauer'][0][0]:.1f} / {r['dauer'][0][1]:.1f} / {r['dauer'][0][2]:.1f}, "
         f"min {r['dauer'][1]:.1f}, max {r['dauer'][2]:.1f}",
         f"- Zeitraum: {_datum(r['zeitraum'][0])} bis {_datum(r['zeitraum'][1])}",
         f"- Doppelte Partien: {r['doppelt_partie']}; Partien mit einem Spieler doppelt: {r['doppelt_spieler']}",
         "", "## Spieler-Partien je Liga und Rolle", "",
         "| Liga | " + " | ".join(g.ROLLE_DE[x] for x in g.ROLLEN) + " | Summe | Spieler |",
         "|---|" + "---:|" * (len(g.ROLLEN) + 2)]
    for l in ligen:
        zeile = r["tabelle"].get(l, Counter())
        z.append(f"| {l} | " + " | ".join(str(zeile[x]) for x in g.ROLLEN)
                 + f" | {sum(zeile.values())} | {len(r['spieler_je_liga'].get(l, ()))} |")
    (g.BUCH / "bestand.md").write_text("\n".join(z) + "\n", encoding="utf-8")

    # Feldkatalog
    f, nn = r["felder"], r["nenner"]
    namen = sorted({k for k, _ in f})
    gruppen = defaultdict(list)
    for name in namen:
        teile = name.split(".")
        if teile[0] == "ereignis":
            gruppe, nen = f"ereignis.{teile[1]}", nn.get(f"ereignis.{teile[1]}", 0)
        else:
            gruppe = ".".join(teile[:2]) if teile[1] in ("challenges", "missions", "championStats", "damageStats",
                                                           "objectives") else teile[0]
            nen = nn.get(teile[0], 0)
        if nen:
            gruppen[gruppe].append((name, f[(name, "da")] / nen, f[(name, "wert")] / nen))
    z = ["# Feldkatalog (Auftrag 029, Schritt 2)", "",
         f"Alle Felder, die in {r['n']} Partien wirklich vorkommen. **da** = Feld vorhanden, **Wert** = vorhanden und "
         "ungleich 0/leer/falsch (bei Zaehlern also: kam vor). Nenner: Spieler-Partien (`spieler`), Teams (`team`), "
         "Spieler-Minuten (`minute`, aus der Zeitleiste), Ereignisse der jeweiligen Art (`ereignis.*`).", ""]
    z.append("## Ereignisarten der Zeitleiste (Anzahl gesamt, je Partie)\n")
    z.append("| Art | Anzahl | je Partie |\n|---|---:|---:|")
    for k, v in sorted(((k, v) for k, v in nn.items() if k.startswith("ereignis.")), key=lambda kv: -kv[1]):
        z.append(f"| {k[9:]} | {v} | {v / max(1, r['n']):.1f} |")
    for gruppe in sorted(gruppen):
        z += ["", f"## {gruppe} ({len(gruppen[gruppe])} Felder)", "", "| Feld | da | Wert |", "|---|---:|---:|"]
        for name, da, wert in gruppen[gruppe]:
            z.append(f"| `{name[len(gruppe) + 1:] or name}` | {da:.0%} | {wert:.0%} |")
    z += ["", "## Was fehlt (fuer niemanden in den Daten)", "",
          "- **Wellen:** keine Vasallen-Positionen, kein Wellenstand; nur CS je Minute.",
          "- **Ward-Orte:** `WARD_PLACED`/`WARD_KILL` ohne Position (nur Typ, Zeit, Setzer/Zerstoerer).",
          "- **Nebel/Sicht:** wer wen wann sah, fehlt ganz.",
          "- **Abklingzeiten:** Ult, Flash, TP im Spiel fehlen; nur die Summe der Einsaetze (`summonerXCasts`, "
          "`spellXCasts`) je Partie.",
          "- **Wege zwischen den Minuten:** eine Position je Spieler und Minute; dazwischen nur Ereignis-Orte "
          "(Kills, Gebaeude, Platten, Monster).",
          "- **Leben im Kampf:** `health` nur zur vollen Minute; Schaden je Faehigkeit nur beim Tod.",
          "- **Recall selbst:** kein Ereignis; nur Kaeufe (Laden = Basis) und Positionen.",
          "- **Ganks ohne Kill, Absichten, Pings mit Zeit/Ort:** Pings nur als Summe je Partie."]
    (g.BUCH / "feldkatalog.md").write_text("\n".join(z) + "\n", encoding="utf-8")


if __name__ == "__main__":
    g.BUCH.mkdir(parents=True, exist_ok=True)
    print("neu verdichtet:", g.verdichten(leise=True))
    if "--liga" in sys.argv:
        d = liga_holen()
        print("Ligalisten:", d["je_liste"], "->", len(d["spieler"]), "PUUIDs")
    r = pruefen()
    schreiben(r)
    print(open(g.BUCH / "bestand.md", encoding="utf-8").read())
