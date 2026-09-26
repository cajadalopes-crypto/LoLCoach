"""Review nach dem Spiel: Lektionen aus der Zeitleiste - und das Gespraech darueber.

Grundsatz gegen "AI-Slop" (Carlos): jede Aussage steht auf einem Fakt der
Zeitleiste (verlauf.py) mit Spielzeit; zu jedem Fehler gehoert, was stattdessen
richtig gewesen waere und warum; was die Daten nicht zeigen (Wellenstand,
Cooldowns ohne Ping), wird als unbekannt benannt statt erfunden; wenige,
wichtige Punkte statt einer Liste von Allgemeinplaetzen.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import champions, gehirn, llm, minimap, profil, verlauf
from .ansicht import uhr

REVIEW_SYSTEM = """Du bist ein Challenger-Coach fuer League of Legends und machst mit deinem Schueler
(Ziel Diamond+) das Review einer Partie. Du bekommst die Zeitleiste der Partie - aus Spieldaten und
Minimap errechnet, nicht geraten - sowie deine Vorbereitung und Lexikon-Auszuege.

Regeln, ohne Ausnahme:
- Jede Aussage stuetzt sich auf Fakten der Zeitleiste. Nenne die Spielzeit und den Beleg. Keine Namen,
  Zahlen oder Umstaende, die dort nicht stehen (z. B. nicht 'allein', wenn nur 'Gegner holt' steht).
- Kein Allgemeinplatz ("mehr auf die Map schauen"). Sag, WAS er in DIESEM Moment gesehen haben konnte
  (z. B. "Warwick und Swain waren seit 35-44 s nicht auf der Karte") und was die richtige Handlung
  gewesen waere - so konkret, dass er es naechstes Mal tun kann.
- Was die Daten nicht zeigen (Wellenstand, Cooldowns ohne Ping, Leben der Gegner), nennst du als
  unbekannt, statt es zu erfinden. Lieber eine vorsichtige Aussage als eine falsche.
- Priorisiere nach Auswirkung auf die Partie (Tode mit Folgen, verlorene Objectives, gehortetes Gold,
  Farm-Loecher ohne Gegenwert - ein Farm-Loch mit Kills oder Objectives in der Zeit kann richtig gewesen sein,
  Recalls mit der Welle auf dem Weg zu ihm oder kurz vor einem Objective).
  Hoechstens 5 Lektionen. Auch 1-2 echte Staerken, damit er weiss, was er beibehalten soll.
- Bot-Partie: sag knapp, was davon gegen echte Gegner gilt.
- Kennst du BISHERIGE PARTIEN: hat der Spieler den Fokus der letzten Partie umgesetzt (Beleg aus DIESER
  Zeitleiste)? Kehrt ein Fehler wieder, sag es ("wie schon am 26.09.") - ein wiederkehrender Fehler wiegt
  schwerer als ein einmaliger, und der Fokus fuer die naechste Partie gilt dann ihm. Vergleiche Kennzahlen
  nur mit dem, was dort steht.
- Liegen BILDER bei (sein Spielbildschirm in Schluesselmomenten, Liste am Ende), nutze sie fuer das, was die
  Zeitleiste nicht hat: Leben ueber den Koepfen, wer wirklich im Kampf war, Position im Kampf, Vasallen, seine
  Faehigkeiten/Zauber unten (Zahl = Abklingzeit). Beleg dann als "Bild 19:40: ...". Nur, was zu sehen ist.
- Kennst du WAS DER COACH LIVE GESAGT HAT (gerechnete Warnungen und Plaene mit Spielzeit): vergleiche mit dem,
  was danach passiert ist. Ist er einer Warnung oder einem Plan nicht gefolgt und hat es gekostet (Tod, Objective,
  verpasstes Fenster), ist das ein starker Beleg ("12:32 sagte ich: Swain und Alistar koennen da sein, zurueck -
  12:40 gestorben"). Lag der Coach falsch oder zu spaet, sag das ehrlich in einem Satz - daran wird der Coach besser.
- Deutsch, direkt, wie im Voice-Chat nach dem Spiel - aber praezise. Sprich den Spieler mit "du" an,
  auch in der Zusammenfassung (nicht "Riven hat ...", sondern "du hast ...").

Antworte NUR mit JSON in genau dieser Form:
{"zusammenfassung": "2-3 Saetze: warum die Partie so lief",
 "lektionen": [{"zeit": "21:03", "titel": "kurz", "was": "was passiert ist (Fakten)",
   "warum": "warum es ein Fehler war", "besser": "was konkret stattdessen", "beleg": ["Fakt aus der Zeitleiste", "..."],
   "wichtigkeit": 1-5}],
 "staerken": [{"zeit": "14:13", "titel": "kurz", "was": "was gut war und warum"}],
 "fokus_umgesetzt": "1-2 Saetze: ob und wo der Fokus der letzten Partie umgesetzt wurde, mit Beleg - leer, wenn es keinen gab",
 "naechste_partie": "ein einziger Fokus fuer die naechste Partie, ein Satz, als Handlung formuliert"}"""

GESPRAECH_SYSTEM = """Du bist ein Challenger-Coach fuer League of Legends im Gespraech nach der Partie mit
deinem Schueler. Du kennst die Zeitleiste der Partie (aus Spieldaten und Minimap, nicht geraten), dein
Review und Auszuege aus deinem Wissen. Antworte auf Deutsch, direkt, 3-8 Saetze. Beziehe dich auf
Spielzeiten und Fakten; Orte mit Worten ("im oberen Fluss"), nie als Zahlen. Was die Daten nicht
zeigen, sagst du offen. Tode, Kills und Objectives NUR aus der Liste EREIGNISSE bzw. der Zeitleiste -
nie aus Positionen erschliessen (in der Basis sein heisst nicht gestorben sein). Ob der Spieler lebte,
steht in jeder DETAIL-Zeile ("du lebst" / "du bist TOT"). Keine Allgemeinplaetze - wenn er
fragt, was er haette tun sollen, nenn die konkrete Handlung und warum. Wenn er widerspricht und recht hat,
gib es zu. Liegt ein BILD bei, ist es sein Spielbildschirm in dem Moment, nach dem er fragt: lies daraus
Leben, wer da war, Vasallen, seine Faehigkeiten und Zauber - nur, was zu sehen ist."""


def pfade(aufnahme: Path) -> dict[str, Path]:
    stamm = aufnahme.name.removesuffix(".jsonl.gz")
    return {"verlauf": aufnahme.with_name(stamm + "_verlauf.json"),
            "review": aufnahme.with_name(stamm + "_review.json"),
            "gespraech": aufnahme.with_name(stamm + "_gespraech.json")}


def _wissen(v: verlauf.Verlauf, ordner: Path | None = None) -> str:
    teile = []
    if v.spielakte:
        teile.append("DEINE VORBEREITUNG (Spielakte):\n" + v.spielakte)
    else:
        teile.append("CHAMPIONS:\n" + "\n".join(champions.steckbrief(s["id"], kurz=True) for s in v.spieler))
    for s in v.spieler:
        if s["ich"] or (not s["freund"] and s["rolle"] == next((x["rolle"] for x in v.spieler if x["ich"]), None)):
            if eintrag := gehirn.champion_eintrag(s["id"]):
                teile.append(f"LEXIKON {s['champion']}:\n{eintrag[:4000]}")
    if g := gehirn.grundlagen("welle recall objective teamfight split", hoechstens=5000):
        teile.append("LEXIKON GRUNDLAGEN:\n" + g)
    if ordner and (bisher := profil.text(ordner, vor=v.datei.removesuffix(".jsonl.gz"))):
        teile.append(bisher)
    return "\n\n".join(teile)


def _json_aus(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    start, ende = text.find("{"), text.rfind("}")
    return json.loads(text[start:ende + 1])


def _gesagt_text(v, hoechstens: int = 70) -> str:
    """Die gesprochenen Ansagen (Warnungen, Plaene) mit Spielzeit - ohne Statistik-Saetze (CS)."""
    zeilen = []
    for a in v.ansagen:
        t = a.get("gesprochen") or a.get("zeit")
        if t is None or str(a.get("schluessel", "")).startswith("cs"):
            continue
        zeilen.append(f"{int(t // 60)}:{int(t % 60):02d} {a.get('text', '')}")
    if len(zeilen) > hoechstens:        # gleichmaessig ausduennen, die Reihenfolge bleibt
        schritt = len(zeilen) / hoechstens
        zeilen = [zeilen[int(i * schritt)] for i in range(hoechstens)]
    return "\n".join(zeilen)


def erstelle(aufnahme: str | Path, neu: bool = False, modell: str = "sonnet") -> dict:
    """Zeitleiste bauen, Claude das Review schreiben lassen, beides speichern."""
    aufnahme = Path(aufnahme)
    p = pfade(aufnahme)
    if p["review"].exists() and not neu:
        return json.loads(p["review"].read_text(encoding="utf-8"))
    v = verlauf.baue(aufnahme)
    verlauf.speichern(v, p["verlauf"])
    inhalt = f"{_wissen(v, aufnahme.parent)}\n\nZEITLEISTE DER PARTIE:\n{verlauf.als_text(v, hoechstens=60)}"
    if gesagt := _gesagt_text(v):
        inhalt += "\n\nWAS DER COACH LIVE GESAGT HAT:\n" + gesagt
    bilder = moment_bilder(aufnahme, v)
    if bilder:
        inhalt += "\n\nBILDER (sein Spielbildschirm, in dieser Reihenfolge):\n" + "\n".join(
            f"{i}. {text}" for i, (text, _) in enumerate(bilder, 1))
    antwort = llm.frage(inhalt, system=REVIEW_SYSTEM, modell=modell, timeout=300,
                        bilder=[b for _, b in bilder] or None)
    try:
        review = _json_aus(antwort)
    except (ValueError, json.JSONDecodeError):
        review = {"zusammenfassung": antwort, "lektionen": [], "staerken": [], "naechste_partie": ""}
    from .itemnamen import absichern
    for teil in (review.get("lektionen") or []) + (review.get("staerken") or []):
        for k in ("was", "warum", "besser", "titel"):
            if isinstance(teil.get(k), str):
                teil[k] = absichern(teil[k])[0]
    for k in ("zusammenfassung", "fokus_umgesetzt", "naechste_partie"):
        if isinstance(review.get(k), str):
            review[k] = absichern(review[k])[0]
    review["_modell"] = modell
    p["review"].write_text(json.dumps(review, ensure_ascii=False, indent=1), encoding="utf-8")
    return review


def moment_bilder(aufnahme: Path, v: verlauf.Verlauf, hoechstens: int = 6) -> list[tuple[str, bytes]]:
    """Die Spielbildschirme der wichtigsten Momente: 3 s vor jedem Tod, die Mitte schwerer Kaempfe,
    verlorene Objectives - die schwersten zuerst ausgewaehlt, dann nach Zeit."""
    kandidaten = []
    for m in v.momente:
        if m.art == "tod":
            kandidaten.append((m.gewicht + 2, m.bis - 3, f"{uhr(m.bis - 3)} - 3 s vor deinem Tod ({m.titel})"))
        elif m.art == "kampf" and m.gewicht >= 3:
            mitte = (m.von + m.bis) / 2
            kandidaten.append((m.gewicht, mitte, f"{uhr(mitte)} - mitten im {m.titel}"))
        elif m.art == "objective" and "Gegner" in m.titel:
            kandidaten.append((m.gewicht, m.von, f"{uhr(m.von)} - {m.titel}"))
    aus, zeiten = [], []
    for _, zeit, text in sorted(kandidaten, key=lambda k: -k[0]):
        if len(aus) >= hoechstens or any(abs(zeit - z) < 8 for z in zeiten):
            continue
        if (pfad := verlauf.bildschirm_bei(aufnahme, v, zeit)) is not None:
            aus.append((zeit, text, pfad.read_bytes()))
            zeiten.append(zeit)
    return [(text, b) for _, text, b in sorted(aus)]


_ZEIT = re.compile(r"\b(\d{1,2})[:.](\d{2})\b")


def _detail(v: verlauf.Verlauf, zeit: float, spanne: float = 45) -> str:
    """Sekunde fuer Sekunde (alle 5 s) um einen Zeitpunkt: Leben, Gold, Positionen."""
    namen = {s["name"]: s["champion"] for s in v.spieler}
    zeilen = [f"EREIGNISSE {uhr(zeit - spanne)}-{uhr(zeit + 15)} (aus der Spiel-API, sicher):"]
    zeilen += [f"  {uhr(z)} {satz}" for z, satz in v.ereignisse if zeit - spanne <= z <= zeit + 15] or ["  keine"]
    zeilen.append(f"DETAIL {uhr(zeit - spanne)}-{uhr(zeit + 15)} (alle 5 s; 'du' = der Spieler; Positionen nur Gesehenes):")
    letzte = -1e9
    for s in v.sekunden:
        if zeit - spanne <= s.zeit <= zeit + 15 and s.zeit - letzte >= 5:
            letzte = s.zeit
            ich_tot = v.ich in s.tot
            ich_pos = s.positionen.get(v.ich)
            ich_ort = minimap.ort(ich_pos[0], ich_pos[1], v.team) if ich_pos and ich_pos[2] < 5 else "Ort unbekannt"
            du = (f"du bist TOT" if ich_tot else
                  f"du lebst, {int((s.leben or 0) * 100)} % Leben, {int(s.gold or 0)} Gold, {ich_ort}")
            andere = "; ".join(f"{namen.get(n, n)} {'jetzt' if sicht else f'vor {int(alter)} s'} "
                               f"{minimap.ort(x, y, v.team)}" for n, (x, y, alter, sicht) in s.positionen.items()
                               if alter < 30 and n != v.ich)
            tote = ", ".join(namen.get(n, n) for n in s.tot if n != v.ich) or "-"
            zeilen.append(f"{uhr(s.zeit)} {du} | Kills {s.kills[0]}:{s.kills[1]} | andere tot: {tote} | gesehen: {andere}")
    return "\n".join(zeilen)


_verlaeufe: dict[str, verlauf.Verlauf] = {}


def frage(aufnahme: str | Path, text: str, zeit: float | None = None, modell: str = "sonnet",
          gesprochen: bool = False) -> str:
    """Eine Frage im Gespraech nach der Partie. `zeit`: Moment, den der Spieler gerade ansieht.
    `gesprochen`: die Antwort wird vorgelesen - kurz halten (eine Antwort las sich in 40 s vor)."""
    aufnahme = Path(aufnahme)
    p = pfade(aufnahme)
    if aufnahme.name not in _verlaeufe:
        _verlaeufe[aufnahme.name] = verlauf.baue(aufnahme)
    v = _verlaeufe[aufnahme.name]
    review = json.loads(p["review"].read_text(encoding="utf-8")) if p["review"].exists() else None
    verlauf_gespraech = json.loads(p["gespraech"].read_text(encoding="utf-8")) if p["gespraech"].exists() else []
    zeiten = [int(m.group(1)) * 60 + int(m.group(2)) for m in _ZEIT.finditer(text)]
    if zeit is not None:
        zeiten.append(zeit)
    teile = [_wissen(v, aufnahme.parent), "ZEITLEISTE DER PARTIE:\n" + verlauf.als_text(v, hoechstens=45)]
    if review:
        teile.append("DEIN REVIEW:\n" + json.dumps(review, ensure_ascii=False))
    bilder = []
    for z in zeiten[:2]:
        teile.append(_detail(v, z))
        if (pfad := verlauf.bildschirm_bei(aufnahme, v, z)) is not None:   # sein Bildschirm in dem Moment
            bilder.append(pfad.read_bytes())
            teile.append(f"BILD {len(bilder)}: sein Spielbildschirm um {uhr(z)}")
    if verlauf_gespraech:
        teile.append("BISHERIGES GESPRAECH:\n" + "\n".join(f"{e['wer']}: {e['text']}" for e in verlauf_gespraech[-8:]))
    hinweis = ("\n(Die Antwort wird vorgelesen: hoechstens 4 kurze Saetze, keine Aufzaehlungen - das "
               "Wichtigste zuerst; Details kann er nachfragen.)") if gesprochen else ""
    antwort = llm.frage("\n\n".join(teile) + f"\n\nFRAGE DES SPIELERS: {text}{hinweis}", system=GESPRAECH_SYSTEM,
                        modell=modell, timeout=120, aufwand="medium", bilder=bilder or None).strip()
    from .itemnamen import absichern
    antwort = absichern(antwort)[0]
    verlauf_gespraech += [{"wer": "Spieler", "text": text, "zeit": zeit}, {"wer": "Coach", "text": antwort}]
    p["gespraech"].write_text(json.dumps(verlauf_gespraech, ensure_ascii=False, indent=1), encoding="utf-8")
    return antwort
