"""Szenarien pruefen: war der Rat in dieser Lage richtig? (Buch 0, Kapitel 12.1)

Spielt die Aufnahme jedes Szenario-Files nach (wie live, stumm) und prueft jedes Szenario:

  altes System (nur Text):  darf_nicht_sagen, muss_nennen_eins, muss_ziel, kehrtwenden_max, ansagen_max
                            im Fenster ([zeit-2, zeit+15] oder `fenster`)
  Kern (Modus, Plan-Art):   modus, soll, darf_nicht, [[modus_soll]] - den Kern gibt es erst ab Schritt 2/3,
                            bis dahin "uebersprungen"
  frage:                    wie per Sprechtaste, geprueft wird die Antwort - braucht Claude, nur mit --mit-claude
  typ = "review":           gegen das gespeicherte Review der Partie - nur mit --mit-claude

Ein Szenario ist rot, wenn ein gepruefter Teil verletzt ist; gruen, wenn mindestens ein Teil geprueft wurde und
alle halten; sonst uebersprungen. Am Ende die Quote.

    python werkzeuge/szenarien.py [tests/szenarien/<datei>.toml ...] [--nur alt|kern] [--mit-claude] [--lage]

--lage zeigt je Szenario die nachgespielte Lage neben der aus dem Szenario (Bestaetigung, Schritt 1).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nachspielen as ns  # noqa: E402

SZENARIEN = Path(__file__).resolve().parent.parent / "tests" / "szenarien"
ZIEL = re.compile(r"\b(Top|Mid|Bot)\b|\boben\b|\bunten\b|Drache|Baron|Herold|Larven|Ältest|Inhibitor|Nexus|Basis|"
                  r"Grube|Brunnen", re.I)
UHR = re.compile(r"\b(\d{1,2}):(\d{2})\b")


def hat_ziel(text: str, champions) -> bool:
    """Ein aufloesbares Ziel: Lane, Objective, Struktur, Ort oder ein Champion der Partie (Kapitel 6.2)."""
    return bool(ZIEL.search(text)) or any(c and c in text for c in champions)


def fenster(sz: dict) -> tuple[float, float]:
    if "fenster" in sz:
        return ns.sekunden(sz["fenster"][0]), ns.sekunden(sz["fenster"][1])
    t = ns.sekunden(sz["zeit"])
    return t - 2, t + 15


def text_pruefen(sz: dict, texte: list[tuple[float, str]], champions) -> list[str]:
    """Die Textteile gegen gesprochene Saetze (oder eine Antwort). Rueckgabe: Verstoesse."""
    aus = []
    for verboten in sz.get("darf_nicht_sagen", []):
        for t, s in texte:
            if verboten.lower() in s.lower():
                aus.append(f"darf_nicht_sagen '{verboten}' - {ns.uhr(t)} \"{s[:110]}\"")
                break
    if sz.get("muss_nennen_eins") and not any(w.lower() in s.lower() for _, s in texte
                                                  for w in sz["muss_nennen_eins"]):
        aus.append(f"muss_nennen_eins {sz['muss_nennen_eins']} - nichts davon gesagt")
    if sz.get("muss_ziel") and not any(hat_ziel(s, champions) for _, s in texte):
        aus.append("muss_ziel - kein Satz mit aufloesbarem Ziel" + ("" if texte else " (gar nichts gesagt)"))
    if sz.get("muss_item"):
        from lolcoach import ddragon
        # nur kaufbare Items mit Namen (Data Dragon hat auch namenlose Eintraege - die passten auf jeden Satz)
        namen = {v["name"] for v in ddragon.items().values() if v.get("name", "").strip()
                 and v.get("gold", {}).get("purchasable") and v.get("maps", {}).get("11")}
        muster = re.compile(r"\b(" + "|".join(re.escape(n) for n in sorted(namen, key=len, reverse=True)) + r")\b")
        if not any(muster.search(s) for _, s in texte):
            aus.append("muss_item - kein Item aus der Ladenliste genannt")
    return aus


def review_pruefen(sz: dict, stamm: str) -> tuple[list[str], str | None]:
    """typ = "review" gegen das gespeicherte Review (und die Zeitleiste). Rueckgabe: (Verstoesse, uebersprungen?)."""
    datei = ns.AUFNAHMEN / f"{stamm}_review.json"
    if not datei.exists():
        return [], "kein gespeichertes Review"
    r = json.loads(datei.read_text(encoding="utf-8"))
    lek = r.get("lektionen") or []
    ganz = json.dumps(r, ensure_ascii=False)
    aus = []
    if "datenluecke" in sz:
        von, bis = (ns.sekunden(x) for x in sz["datenluecke"])
        zeiten = [int(m) * 60 + int(s) for m, s in UHR.findall(ganz)]
        if not (any(abs(z - von) <= 10 for z in zeiten) and any(abs(z - bis) <= 10 for z in zeiten)):
            aus.append(f"datenluecke {sz['datenluecke']} - im Review nicht genannt")
    if lek and sz.get("lektion_1_nicht"):
        kopf = f"{lek[0].get('titel', '')} {lek[0].get('was', '')}"
        if any(x.lower() in kopf.lower() for x in sz["lektion_1_nicht"]):
            aus.append(f"lektion_1_nicht - Lektion 1: \"{lek[0].get('titel', '')}\"")
    if sz.get("oben_eins"):
        oben = " ".join(json.dumps(x, ensure_ascii=False) for x in lek[:2])
        if not any(x in oben for x in sz["oben_eins"]):
            aus.append(f"oben_eins {sz['oben_eins']} - nicht in Lektion 1 oder 2")
    if sz.get("keine_position_in_luecke") and "datenluecke" in sz:
        von, bis = (ns.sekunden(x) for x in sz["datenluecke"])
        eintraege = list(lek) + list(r.get("staerken") or [])
        verlauf = ns.AUFNAHMEN / f"{stamm}_verlauf.json"
        if verlauf.exists():
            try:
                v = json.loads(verlauf.read_text(encoding="utf-8"))
                eintraege += [x for x in (v if isinstance(v, list) else v.get("zeitleiste", [])) if isinstance(x, dict)]
            except ValueError:
                pass
        for e in eintraege:
            z = UHR.search(str(e.get("zeit", "")))
            if z and von <= int(z.group(1)) * 60 + int(z.group(2)) <= bis and re.search(r"Du warst", json.dumps(
                    e, ensure_ascii=False)):
                aus.append(f"keine_position_in_luecke - {e.get('zeit')}: \"{str(e.get('titel') or e)[:80]}\"")
                break
    return aus, None


def antwort(frage: str, p, lb, wand: float, stamm: str) -> str:
    """Der alte Antwortweg wie live: erst sofort, sonst Claude mit Spielakte und dem Bildschirm des Moments."""
    from lolcoach import antworten, gehirn
    a = antworten.sofort(frage, p, lb)
    if a is not None:
        return a
    g = gehirn.Gehirn()
    akte = ns.AUFNAHMEN / f"{stamm}_spielakte.md"
    g.akte = akte.read_text(encoding="utf-8") if akte.exists() else None
    schirme = sorted((ns.AUFNAHMEN / f"{stamm}_bilder").glob("schirm_*.jpg"))
    bild = min(schirme, key=lambda f: abs(int(f.stem.split("_")[1]) / 1000 - wand)).read_bytes() if schirme else None
    return antworten.mit_claude(frage, p, lb, "sonnet", [], g, [bild] if bild else None)


def pruefe_datei(datei: Path, nur: str | None, mit_claude: bool, lage: bool, lauf: ns.Lauf | None = None) -> dict:
    """`lauf`: schon nachgespielt (kennzahlen.py) - dann ohne Fragen an Claude."""
    cfg = tomllib.loads(datei.read_text(encoding="utf-8"))
    stamm = cfg["aufnahme"]
    szen = cfg.get("szenario", [])
    halte = sorted({ns.sekunden(s["zeit"]) if "zeit" in s else fenster(s)[0]
                    for s in szen if "zeit" in s or "fenster" in s})
    antworten_: dict = {}

    def bei_halt(soll, p, b, lb, wand):
        for s in szen:
            if s.get("frage") and mit_claude and ns.sekunden(s["zeit"]) == soll and nur != "kern":
                antworten_[s["id"]] = antwort(s["frage"], p, lb, wand, stamm)

    if lauf is None:
        lauf = ns.durchspielen(ns.pfad_zu(stamm), halte_bei=halte, rueckruf=bei_halt)
    print(f"== {stamm}{' (Bot-Partie)' if cfg.get('bots') else ''}: {len(lauf.gesagt)} Ansagen nachgespielt")
    ergebnis = {"gruen": 0, "rot": 0, "uebersprungen": 0, "rot_ids": [], "gruen_ids": []}
    for sz in szen:
        verstoesse, geprueft, uebersprungen = [], 0, []
        if sz.get("typ") == "review":
            if mit_claude and nur != "kern":
                v, grund = review_pruefen(sz, stamm)
                if grund:
                    uebersprungen.append(f"review ({grund})")
                else:
                    geprueft += 1
                    verstoesse += v
            else:
                uebersprungen.append("review (--mit-claude)")
        elif nur != "kern":
            if sz.get("frage"):
                if sz["id"] in antworten_:
                    geprueft += 1
                    verstoesse += text_pruefen(sz, [(ns.sekunden(sz["zeit"]), antworten_[sz["id"]])], lauf.champions)
                else:
                    uebersprungen.append("frage (--mit-claude)")
            else:
                von, bis = fenster(sz)
                texte = [(ns.gesprochen_um(a), a.text) for a in lauf.gesagt if von <= ns.gesprochen_um(a) <= bis]
                teile = [k for k in ("darf_nicht_sagen", "muss_nennen_eins", "muss_ziel") if sz.get(k)]
                if teile:
                    geprueft += 1
                    verstoesse += text_pruefen(sz, texte, lauf.champions)
                if "kehrtwenden_max" in sz:
                    geprueft += 1
                    kw = ns.kehrtwenden(lauf, von, bis)
                    if len(kw) > sz["kehrtwenden_max"]:
                        verstoesse.append(f"kehrtwenden_max {sz['kehrtwenden_max']} - {len(kw)}: " + "; ".join(
                            f"{ns.uhr(a)} \"{s1[:40]}\" -> {ns.uhr(b)} \"{s2[:40]}\"" for a, s1, b, s2 in kw))
                if "ansagen_max" in sz:
                    geprueft += 1
                    if len(texte) > sz["ansagen_max"]:
                        verstoesse.append(f"ansagen_max {sz['ansagen_max']} - {len(texte)}")
        if any(k in sz for k in ("modus", "soll", "darf_nicht")):
            uebersprungen.append("Kern (modus/soll/darf_nicht, ab Schritt 2/3)")
        status = "rot" if verstoesse else ("gruen" if geprueft else "uebersprungen")
        ergebnis[status] += 1
        if status in ("rot", "gruen"):
            ergebnis[f"{status}_ids"].append(sz["id"])
        zeichen = {"rot": "ROT  ", "gruen": "GRUEN", "uebersprungen": "--   "}[status]
        print(f"  {zeichen} {sz['id']}" + (f"  [uebersprungen: {', '.join(uebersprungen)}]" if uebersprungen else ""))
        for v in verstoesse:
            print(f"          {v}")
        if sz["id"] in antworten_:
            print(f"          Antwort: {antworten_[sz['id']][:160]}")
        halt = ns.sekunden(sz["zeit"]) if "zeit" in sz else (fenster(sz)[0] if "fenster" in sz else None)
        if lage and halt in lauf.halte:
            print("          Szenario: " + " ".join(sz.get("lage", "").split())[:300])
            print(f"          Nachgespielt ({ns.uhr(halt)}): " + lauf.halte[halt][2].replace("\n", " | "))
    if cfg.get("modus_soll"):
        n = sum(len(m["zeiten"]) for m in cfg["modus_soll"])
        print(f"  --    Modus-Sollwerte ({n} Zeitpunkte): uebersprungen (Kern, ab Schritt 2)")
    gepr = ergebnis["gruen"] + ergebnis["rot"]
    print(f"  Quote altes System: {ergebnis['gruen']} gruen / {gepr} geprueft, {ergebnis['rot']} rot, "
          f"{ergebnis['uebersprungen']} uebersprungen")
    return ergebnis


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("dateien", nargs="*")
    ap.add_argument("--nur", choices=("alt", "kern"))
    ap.add_argument("--mit-claude", action="store_true", help="Fragen echt an Claude, Review pruefen")
    ap.add_argument("--lage", action="store_true", help="nachgespielte Lage je Szenario zeigen")
    args = ap.parse_args()
    dateien = [Path(d) for d in args.dateien] or sorted(SZENARIEN.glob("*.toml"))
    gesamt = {"gruen": 0, "rot": 0, "uebersprungen": 0}
    for d in dateien:
        e = pruefe_datei(d, args.nur, args.mit_claude, args.lage)
        for k in gesamt:
            gesamt[k] += e[k]
    gepr = gesamt["gruen"] + gesamt["rot"]
    print(f"\nGesamt: {gesamt['gruen']} gruen / {gepr} geprueft ({gesamt['rot']} rot, {gesamt['uebersprungen']} "
          f"uebersprungen)" + ("" if args.nur == "alt" else " - Kern: noch nicht gebaut (Schritt 2/3)"))


if __name__ == "__main__":
    main()
