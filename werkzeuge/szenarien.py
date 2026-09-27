"""Szenarien pruefen: war der Rat in dieser Lage richtig? (Buch 0, Kapitel 12.1)

Spielt die Aufnahme jedes Szenario-Files nach (wie live, stumm) und prueft jedes Szenario:

  altes System (nur Text):  darf_nicht_sagen, muss_nennen_eins, muss_ziel, kehrtwenden_max, ansagen_max
                            im Fenster ([zeit-2, zeit+15] oder `fenster`, auch mehrere: [[von, bis], ...]);
                            seit der Qualitaetsrunde 1: ziele_max, satz_mit (+ satz_mit_anzahl), fassung_einmal,
                            woerter_max (+ woerter_schluessel), gold_reicht; seit der Qualitaetsrunde 2:
                            text_max = { "muster|muster" = n } (hoechstens n Saetze mit einem der Muster),
                            planwechsel_max (Wechsel der Plan-Art zwischen gesprochenen Kern-Saetzen)
  Datei:                    spielmodus = "CLASSIC" | "SWIFTPLAY" (Vorgabe CLASSIC) - muss zum gameMode der Aufnahme
                            passen, sonst rot (Qualitaetsrunde 2, G6: 133930 und 140253 sind Swiftplay)
  Kern (Modus, Plan-Art):   modus und [[modus_soll]] ab Schritt 2 (irgendein Takt in zeit +-2 s hat einen der
                            erlaubten Modi); soll (irgendein Takt in zeit +-2 s hat eine der Plan-Arten) und
                            darf_nicht (kein Takt im Fenster) ab Schritt 3; plan_p_tod_max (ein Takt in zeit +-2 s
                            mit einer soll-Art hat p_tod darunter)
  frage:                    wie per Sprechtaste, geprueft wird die Antwort - braucht Claude, nur mit --mit-claude
  typ = "review":           gegen das gespeicherte Review der Partie - nur mit --mit-claude

Ein Szenario ist rot, wenn ein gepruefter Teil verletzt ist; gruen, wenn mindestens ein Teil geprueft wurde und
alle halten; sonst uebersprungen. Am Ende die Quote.

    python werkzeuge/szenarien.py [tests/szenarien/<datei>.toml ...] [--nur alt|kern] [--mit-claude] [--lage]
                                  [--kern alt|schatten|neu] [--konstruiert]

--lage zeigt je Szenario die nachgespielte Lage neben der aus dem Szenario (Bestaetigung, Schritt 1).
--kern wie beim Coach (Default neu: der Kern spricht in LANE, BASIS, TOT und seit Schritt 4 in SEITE, GRUPPE,
UNTERWEGS, VERTEIDIGEN).
--konstruiert prueft die konstruierten Lagen (tests/szenarien/konstruiert/, Buch 1 6.2) statt der Aufnahmen.
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


def fenster_alle(sz: dict) -> list[tuple[float, float]]:
    """Alle Fenster eines Szenarios: `fenster = [von, bis]`, mehrere als [[von, bis], ...], sonst [zeit-2, zeit+15]."""
    f = sz.get("fenster")
    if f and isinstance(f[0], list):
        return [(ns.sekunden(a), ns.sekunden(b)) for a, b in f]
    if f:
        return [(ns.sekunden(f[0]), ns.sekunden(f[1]))]
    t = ns.sekunden(sz["zeit"])
    return [(t - 2, t + 15)]


def fenster(sz: dict) -> tuple[float, float]:
    """Die ganze Spanne (bei mehreren Fenstern vom ersten Anfang bis zum letzten Ende)."""
    alle = fenster_alle(sz)
    return alle[0][0], alle[-1][1]


def im_fenster(sz: dict, t: float) -> bool:
    return any(von <= t <= bis for von, bis in fenster_alle(sz))


ZIEL_NAME = re.compile(r"(?:äußeren |inneren )?(?:Top|Mid|Bot)-(?:Inhibitor-Turm|Inhibitor|Tier-\d-Turm|Turm|Welle)|"
                       r"Nexus-Turm|Nexus|Baron|Drache|Herold|Larven|Ältest\w*|nach (?:Top|Mid|Bot)|Seitenwelle|"
                       r"(?:zu )?deinem Team")
FASSUNG_VOR = re.compile(r"^(?:denk dran|ach nee|noch \d+ sekunden)\s*:\s*", re.I)
GOLD_FUER = re.compile(r"(\d+) Gold für (?:den |die |das )?([A-ZÄÖÜ][^,.:]*?)(?=[,.:]| und | dann |$)")


def ziele(text: str) -> set[str]:
    """Die Ziele, die ein Satz nennt (ziele_max): Strukturen, Lanes, Objectives - normalisiert."""
    aus = set()
    for z in ZIEL_NAME.findall(text):
        z = z.removeprefix("zu ").removeprefix("nach ").strip()
        aus.add(z.lower())
    return aus


def fassung(text: str) -> str:
    """Die Fassung eines Satzes (fassung_einmal): was vor dem ersten Doppelpunkt steht, ohne 'Denk dran:'."""
    t = text
    while (m := FASSUNG_VOR.match(t)):
        t = t[m.end():]
    return t.split(":", 1)[0].strip().lower()


def gold_verstoesse(a) -> list[str]:
    """gold_reicht: "N Gold fuer ITEM" - das Item kostet (abzueglich der Bauteile, die du hast) hoechstens N."""
    from lolcoach import kaufplan
    aus = []
    b = getattr(a, "_b", None)
    inventar = list(b.ich.items) if b is not None and b.ich is not None else []
    for gold, name in GOLD_FUER.findall(a.text):
        item = kaufplan._nach_name().get(name.strip())
        if item is None:
            aus.append(f"gold_reicht - Item '{name}' unbekannt")
            continue
        rest, _ = kaufplan._baum_kosten(item, list(inventar))
        if rest > int(gold):
            aus.append(f"gold_reicht - '{name}' kostet noch {rest}, genannt {gold} Gold: \"{a.text[:80]}\"")
    return aus


def neue_pruefungen(sz: dict, ansagen: list) -> list[str]:
    """Die Pruefschluessel der Qualitaetsrunde 1 (Buch 0, 12.1) auf die gesprochenen Ansagen im Fenster."""
    aus = []
    texte = [a.text for a in ansagen]
    if "ziele_max" in sz:
        genannt = set().union(*(ziele(t) for t in texte)) if texte else set()
        if len(genannt) > sz["ziele_max"]:
            aus.append(f"ziele_max {sz['ziele_max']} - {len(genannt)}: {sorted(genannt)}")
    if "satz_mit" in sz:
        treffer = [t for t in texte if all(any(w.lower() in t.lower() for w in gruppe) for gruppe in sz["satz_mit"])]
        soll = sz.get("satz_mit_anzahl")
        if (soll is None and not treffer) or (soll is not None and len(treffer) != soll):
            aus.append(f"satz_mit {sz['satz_mit']} - {len(treffer)} Saetze (soll {soll or '>= 1'})")
    if sz.get("fassung_einmal"):
        gesehen: dict[str, str] = {}
        for t in texte:
            f = fassung(t)
            if f in gesehen:
                aus.append(f"fassung_einmal - '{f}' zweimal: \"{gesehen[f][:50]}\" / \"{t[:50]}\"")
                break
            gesehen[f] = t
    if "woerter_max" in sz:
        for a in ansagen:
            if sz.get("woerter_schluessel") and not a.schluessel.startswith(sz["woerter_schluessel"]):
                continue
            n = len(a.text.split())
            if n > sz["woerter_max"]:
                aus.append(f"woerter_max {sz['woerter_max']} - {n} Woerter: \"{a.text[:80]}\"")
    if sz.get("gold_reicht"):
        for a in ansagen:
            aus += gold_verstoesse(a)
    for muster, n in (sz.get("text_max") or {}).items():
        treffer = [t for t in texte if re.search(muster, t, re.I)]
        if len(treffer) > n:
            aus.append(f"text_max '{muster}' {n} - {len(treffer)}: " + " / ".join(t[:45] for t in treffer))
    if "planwechsel_max" in sz:
        arten = [a.schluessel.split(":", 1)[1] for a in ansagen
                 if a.schluessel.startswith("kern:") and a.schluessel not in NICHT_PLAN]
        wechsel = [(x, y) for x, y in zip(arten, arten[1:]) if x != y]
        if len(wechsel) > sz["planwechsel_max"]:
            aus.append(f"planwechsel_max {sz['planwechsel_max']} - {len(wechsel)}: " + " -> ".join(
                [arten[0]] + [y for _, y in wechsel]))
    return aus


NICHT_PLAN = ("kern:bestaetigung", "kern:erinnerung")


def stehende_ansage(lauf: ns.Lauf, von: float) -> tuple[float, str] | None:
    """Die Kern-Ansage, die bei `von` noch gilt: vorher gesprochen (kern:<Art>), und der Plan hatte seitdem in jedem
    Takt diese Art. Der Kern sagt sein Ziel einmal und schweigt, solange du dorthin laeufst (Buch 5, Kapitel 2) - fuer
    muss_nennen_eins zaehlt sie wie gesagt (3632: "Mid-Inhibitor-Turm jetzt" um 36:13, der Plan haelt bis 36:47)."""
    vorher = [a for a in lauf.gesagt if a.schluessel.startswith("kern:") and ns.gesprochen_um(a) < von]
    if not vorher:
        return None
    a = vorher[-1]
    t, art = ns.gesprochen_um(a), a.schluessel.split(":", 1)[1]
    takte = [x for x in lauf.takte if t <= x.zeit <= von]
    if not takte or any(x.plan != art for x in takte):
        return None
    return t, a.text


def text_pruefen(sz: dict, texte: list[tuple[float, str]], champions, stehend: tuple | None = None) -> list[str]:
    """Die Textteile gegen gesprochene Saetze (oder eine Antwort). Rueckgabe: Verstoesse. `stehend`: die noch
    geltende Kern-Ansage von vor dem Fenster - zaehlt nur fuer muss_nennen_eins."""
    aus = []
    for verboten in sz.get("darf_nicht_sagen", []):
        for t, s in texte:
            if verboten.lower() in s.lower():
                aus.append(f"darf_nicht_sagen '{verboten}' - {ns.uhr(t)} \"{s[:110]}\"")
                break
    if sz.get("muss_nennen_eins") and not any(w.lower() in s.lower() for _, s in texte + ([stehend] if stehend else [])
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


def modi_um(lauf: ns.Lauf, t: float, um: float = 2.0) -> list[str]:
    """Die Modi des Kerns in den Takten zeit +-um (Reihenfolge wie gesehen, ohne Wiederholung)."""
    aus = []
    for x in lauf.takte:
        if t - um <= x.zeit <= t + um and x.modus not in aus:
            aus.append(x.modus)
    return aus


def plaene_um(lauf: ns.Lauf, von: float, bis: float) -> list[str]:
    """Die Plan-Arten des Kerns in den Takten [von, bis] (Reihenfolge wie gesehen, ohne Wiederholung)."""
    aus = []
    for x in lauf.takte:
        if von <= x.zeit <= bis and x.plan not in aus:
            aus.append(x.plan)
    return aus


def pruefe_datei(datei: Path, nur: str | None, mit_claude: bool, lage: bool, lauf: ns.Lauf | None = None,
                 kern: str = "neu") -> dict:
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
        lauf = ns.durchspielen(ns.pfad_zu(stamm), halte_bei=halte, rueckruf=bei_halt, kern_stellung=kern)
    soll_modus = cfg.get("spielmodus", "CLASSIC")
    print(f"== {stamm}{' (Bot-Partie)' if cfg.get('bots') else ''} [{lauf.spielmodus}]: {len(lauf.gesagt)} Ansagen "
          f"nachgespielt")
    ergebnis = {"gruen": 0, "rot": 0, "uebersprungen": 0, "rot_ids": [], "gruen_ids": [], "modus": None}
    if lauf.spielmodus and soll_modus != lauf.spielmodus:
        # G6: eine Zahl aus CLASSIC gilt in SWIFTPLAY nicht (Startgold, Level, Objectives) - die Datei muss es sagen
        print(f"  ROT   spielmodus\n          Datei sagt {soll_modus}, die Aufnahme ist {lauf.spielmodus}")
        ergebnis["rot"] += 1
        ergebnis["rot_ids"].append("spielmodus")
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
                ansagen = [a for a in lauf.gesagt if im_fenster(sz, ns.gesprochen_um(a))]
                texte = [(ns.gesprochen_um(a), a.text) for a in ansagen]
                teile = [k for k in ("darf_nicht_sagen", "muss_nennen_eins", "muss_ziel") if sz.get(k)]
                if teile:
                    geprueft += 1
                    stehend = stehende_ansage(lauf, von) if kern != "alt" else None
                    verstoesse += text_pruefen(sz, texte, lauf.champions, stehend)
                if "kehrtwenden_max" in sz:
                    geprueft += 1
                    kw = ns.kehrtwenden(lauf, von, bis)
                    if len(kw) > sz["kehrtwenden_max"]:
                        verstoesse.append(f"kehrtwenden_max {sz['kehrtwenden_max']} - {len(kw)}: " + "; ".join(
                            f"{ns.uhr(a)} \"{s1[:40]}\" -> {ns.uhr(b)} \"{s2[:40]}\"" for a, s1, b, s2 in kw))
                if "ansagen_max" in sz:
                    geprueft += 1
                    if len(texte) > sz["ansagen_max"]:
                        verstoesse.append(f"ansagen_max {sz['ansagen_max']} - {len(texte)}: "
                                          + " / ".join(f"{ns.uhr(t)} {s[:40]}" for t, s in texte))
                if any(k in sz for k in ("ziele_max", "satz_mit", "fassung_einmal", "woerter_max", "gold_reicht",
                                         "text_max", "planwechsel_max")):
                    geprueft += 1
                    verstoesse += neue_pruefungen(sz, ansagen)
        if "modus" in sz and "zeit" in sz and nur != "alt":
            geprueft += 1
            modi = modi_um(lauf, ns.sekunden(sz["zeit"]))
            if not set(modi) & set(sz["modus"]):
                verstoesse.append(f"modus {sz['modus']} - Kern: {modi or 'kein Modus'}")
        # Kern-Plan: nur wo der Kern schon entscheidet (Schritt 3: LANE, BASIS, TOT) - sonst "uebersprungen" mit dem
        # Modus, in dem es stand (dessen Schritt kommt noch)
        kern_modi = None
        if nur != "alt" and kern != "alt" and ("soll" in sz or "darf_nicht" in sz) and ("zeit" in sz or "fenster" in sz):
            von, bis = (ns.sekunden(sz["zeit"]) - 2, ns.sekunden(sz["zeit"]) + 2) if "zeit" in sz else fenster(sz)
            if not any(p for p in plaene_um(lauf, von, bis)):
                kern_modi = sorted({str(x.modus) for x in lauf.takte if von <= x.zeit <= bis})
                uebersprungen.append(f"Kern-Plan (der Kern entscheidet in {'/'.join(kern_modi)} noch nicht)")
        if nur != "alt" and kern != "alt" and "soll" in sz and "zeit" in sz and kern_modi is None:
            geprueft += 1
            t = ns.sekunden(sz["zeit"])
            plaene = plaene_um(lauf, t - 2, t + 2)
            if not set(plaene) & set(sz["soll"]):
                verstoesse.append(f"soll {sz['soll']} - Kern-Plan: {plaene or 'keiner'}")
            elif "plan_p_tod_max" in sz:
                pt = [x.plan_ptod for x in lauf.takte if t - 2 <= x.zeit <= t + 2 and x.plan in sz["soll"]
                      and x.plan_ptod is not None]
                if not pt or min(pt) >= sz["plan_p_tod_max"]:
                    verstoesse.append(f"plan_p_tod_max {sz['plan_p_tod_max']} - p_tod {min(pt) if pt else '?':.2f}"
                                      if pt else f"plan_p_tod_max {sz['plan_p_tod_max']} - kein p_tod")
        if nur != "alt" and kern != "alt" and "darf_nicht" in sz and ("zeit" in sz or "fenster" in sz) \
                and kern_modi is None:
            geprueft += 1
            von, bis = fenster(sz)
            falsch = [x for x in lauf.takte if von <= x.zeit <= bis and x.plan in sz["darf_nicht"]]
            if falsch:
                verstoesse.append(f"darf_nicht {sz['darf_nicht']} - {ns.uhr(falsch[0].zeit)} Plan {falsch[0].plan}")
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
    if cfg.get("modus_soll") and nur != "alt":
        treffer, alle, daneben = 0, 0, []
        for m in cfg["modus_soll"]:
            for z in m["zeiten"]:
                alle += 1
                modi = modi_um(lauf, ns.sekunden(z))
                if set(modi) & set(m["modus"]):
                    treffer += 1
                else:
                    daneben.append(f"{z}: soll {'/'.join(m['modus'])}, Kern {'/'.join(str(x) for x in modi) or '-'}")
        ergebnis["modus"] = (treffer, alle)
        print(f"  Modus-Sollwerte: {treffer} / {alle} getroffen ({100 * treffer / alle:.0f} %; Abnahme Schritt 2: "
              f">= 90 %)")
        for d in daneben:
            print(f"          daneben {d}")
    gepr = ergebnis["gruen"] + ergebnis["rot"]
    print(f"  Quote (--kern {kern}): {ergebnis['gruen']} gruen / {gepr} geprueft, {ergebnis['rot']} rot, "
          f"{ergebnis['uebersprungen']} uebersprungen")
    return ergebnis


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("dateien", nargs="*")
    ap.add_argument("--nur", choices=("alt", "kern"))
    ap.add_argument("--mit-claude", action="store_true", help="Fragen echt an Claude, Review pruefen")
    ap.add_argument("--lage", action="store_true", help="nachgespielte Lage je Szenario zeigen")
    ap.add_argument("--kern", choices=("alt", "schatten", "neu"), default="neu")
    ap.add_argument("--konstruiert", action="store_true", help="die konstruierten Lagen (Buch 1, 6.2)")
    args = ap.parse_args()
    if args.konstruiert:
        sys.exit(0 if konstruiert() else 1)
    dateien = [Path(d) for d in args.dateien] or sorted(SZENARIEN.glob("*.toml"))
    gesamt = {"gruen": 0, "rot": 0, "uebersprungen": 0}
    for d in dateien:
        e = pruefe_datei(d, args.nur, args.mit_claude, args.lage, kern=args.kern)
        for k in gesamt:
            gesamt[k] += e[k]
    gepr = gesamt["gruen"] + gesamt["rot"]
    print(f"\nGesamt: {gesamt['gruen']} gruen / {gepr} geprueft ({gesamt['rot']} rot, {gesamt['uebersprungen']} "
          f"uebersprungen)")


def konstruiert() -> bool:
    """Die konstruierten Lagen: je Lage ein Takt des Kerns, Plan gegen soll/darf_nicht/satz_enthaelt."""
    from lolcoach.kern import testlage
    alle_ = testlage.alle()
    ergebnisse = [r for r in alle_ if not r.get("uebersprungen")]
    for r in alle_:
        if r.get("uebersprungen"):
            print(f"  --    {r['datei']}: {r['id']}  [uebersprungen: {r['uebersprungen']}]")
            continue
        print(f"  {'ROT  ' if r['verstoesse'] else 'GRUEN'} {r['datei']}: {r['id']} -> {r['plan']}"
              + (f'  "{r["satz"]}"' if r["satz"] else ""))
        for v in r["verstoesse"]:
            print(f"          {v}  | Top: {r['top'][:4]}")
    gruen = sum(1 for r in ergebnisse if not r["verstoesse"])
    print(f"Konstruierte Lagen: {gruen} / {len(ergebnisse)} gruen, {len(alle_) - len(ergebnisse)} uebersprungen")
    return gruen == len(ergebnisse)


if __name__ == "__main__":
    main()
