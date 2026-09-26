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

from . import champions, gehirn, llm, verlauf
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
- Priorisiere nach Auswirkung auf die Partie (Tode mit Folgen, verlorene Objectives, gehortetes Gold).
  Hoechstens 5 Lektionen. Auch 1-2 echte Staerken, damit er weiss, was er beibehalten soll.
- Bot-Partie: sag knapp, was davon gegen echte Gegner gilt.
- Deutsch, direkt, wie im Voice-Chat nach dem Spiel - aber praezise.

Antworte NUR mit JSON in genau dieser Form:
{"zusammenfassung": "2-3 Saetze: warum die Partie so lief",
 "lektionen": [{"zeit": "21:03", "titel": "kurz", "was": "was passiert ist (Fakten)",
   "warum": "warum es ein Fehler war", "besser": "was konkret stattdessen", "beleg": ["Fakt aus der Zeitleiste", "..."],
   "wichtigkeit": 1-5}],
 "staerken": [{"zeit": "14:13", "titel": "kurz", "was": "was gut war und warum"}],
 "naechste_partie": "ein einziger Fokus fuer die naechste Partie"}"""

GESPRAECH_SYSTEM = """Du bist ein Challenger-Coach fuer League of Legends im Gespraech nach der Partie mit
deinem Schueler. Du kennst die Zeitleiste der Partie (aus Spieldaten und Minimap, nicht geraten), dein
Review und Auszuege aus deinem Wissen. Antworte auf Deutsch, direkt, 3-8 Saetze. Beziehe dich auf
Spielzeiten und Fakten. Was die Daten nicht zeigen, sagst du offen. Keine Allgemeinplaetze - wenn er
fragt, was er haette tun sollen, nenn die konkrete Handlung und warum. Wenn er widerspricht und recht hat,
gib es zu."""


def pfade(aufnahme: Path) -> dict[str, Path]:
    stamm = aufnahme.name.removesuffix(".jsonl.gz")
    return {"verlauf": aufnahme.with_name(stamm + "_verlauf.json"),
            "review": aufnahme.with_name(stamm + "_review.json"),
            "gespraech": aufnahme.with_name(stamm + "_gespraech.json")}


def _wissen(v: verlauf.Verlauf) -> str:
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
    return "\n\n".join(teile)


def _json_aus(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    start, ende = text.find("{"), text.rfind("}")
    return json.loads(text[start:ende + 1])


def erstelle(aufnahme: str | Path, neu: bool = False, modell: str = "sonnet") -> dict:
    """Zeitleiste bauen, Claude das Review schreiben lassen, beides speichern."""
    aufnahme = Path(aufnahme)
    p = pfade(aufnahme)
    if p["review"].exists() and not neu:
        return json.loads(p["review"].read_text(encoding="utf-8"))
    v = verlauf.baue(aufnahme)
    verlauf.speichern(v, p["verlauf"])
    inhalt = f"{_wissen(v)}\n\nZEITLEISTE DER PARTIE:\n{verlauf.als_text(v, hoechstens=60)}"
    antwort = llm.frage(inhalt, system=REVIEW_SYSTEM, modell=modell, timeout=240)
    try:
        review = _json_aus(antwort)
    except (ValueError, json.JSONDecodeError):
        review = {"zusammenfassung": antwort, "lektionen": [], "staerken": [], "naechste_partie": ""}
    review["_modell"] = modell
    p["review"].write_text(json.dumps(review, ensure_ascii=False, indent=1), encoding="utf-8")
    return review


_ZEIT = re.compile(r"\b(\d{1,2})[:.](\d{2})\b")


def _detail(v: verlauf.Verlauf, zeit: float, spanne: float = 45) -> str:
    """Sekunde fuer Sekunde (alle 5 s) um einen Zeitpunkt: Leben, Gold, Positionen."""
    namen = {s["name"]: s["champion"] for s in v.spieler}
    zeilen = [f"DETAIL {uhr(zeit - spanne)}-{uhr(zeit + 15)} (alle 5 s; Positionen nur Gesehenes):"]
    letzte = -1e9
    for s in v.sekunden:
        if zeit - spanne <= s.zeit <= zeit + 15 and s.zeit - letzte >= 5:
            letzte = s.zeit
            pos = "; ".join(f"{namen.get(n, n)} {'jetzt' if sicht else f'vor {int(alter)}s'} "
                            f"({x:.2f},{y:.2f})" for n, (x, y, alter, sicht) in s.positionen.items() if alter < 30)
            zeilen.append(f"{uhr(s.zeit)} Leben {int((s.leben or 0) * 100)} % Gold {int(s.gold or 0)} "
                          f"Kills {s.kills[0]}:{s.kills[1]} tot: {', '.join(namen.get(n, n) for n in s.tot) or '-'} | {pos}")
    zeilen.append("(Kartenkoordinaten 0..1, (0,0) oben links; blaue Basis unten links.)")
    return "\n".join(zeilen)


def frage(aufnahme: str | Path, text: str, zeit: float | None = None, modell: str = "sonnet") -> str:
    """Eine Frage im Gespraech nach der Partie. `zeit`: Moment, den der Spieler gerade ansieht."""
    aufnahme = Path(aufnahme)
    p = pfade(aufnahme)
    v = verlauf.baue(aufnahme)
    review = json.loads(p["review"].read_text(encoding="utf-8")) if p["review"].exists() else None
    verlauf_gespraech = json.loads(p["gespraech"].read_text(encoding="utf-8")) if p["gespraech"].exists() else []
    zeiten = [int(m.group(1)) * 60 + int(m.group(2)) for m in _ZEIT.finditer(text)]
    if zeit is not None:
        zeiten.append(zeit)
    teile = [_wissen(v), "ZEITLEISTE DER PARTIE:\n" + verlauf.als_text(v, hoechstens=45)]
    if review:
        teile.append("DEIN REVIEW:\n" + json.dumps(review, ensure_ascii=False))
    for z in zeiten[:2]:
        teile.append(_detail(v, z))
    if verlauf_gespraech:
        teile.append("BISHERIGES GESPRAECH:\n" + "\n".join(f"{e['wer']}: {e['text']}" for e in verlauf_gespraech[-8:]))
    antwort = llm.frage("\n\n".join(teile) + f"\n\nFRAGE DES SPIELERS: {text}", system=GESPRAECH_SYSTEM,
                        modell=modell, timeout=120).strip()
    verlauf_gespraech += [{"wer": "Spieler", "text": text, "zeit": zeit}, {"wer": "Coach", "text": antwort}]
    p["gespraech"].write_text(json.dumps(verlauf_gespraech, ensure_ascii=False, indent=1), encoding="utf-8")
    return antwort
