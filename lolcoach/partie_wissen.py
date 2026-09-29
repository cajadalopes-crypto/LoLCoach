"""Wissen je Partie fuer den Strategen (Buch 14, Schritt C.2; Auftrag 021, 2).

Ein Block, der sich waehrend der Partie nicht aendert - deshalb geht er als zwischengespeicherter System-Block an die
API (`llm_api._anfrage(wissen=...)`, cache_control). Haiku speichert erst ab 4096 Tokens zwischen: der Block wird
darum bewusst so voll, dass er darueber liegt (`MIN_TOKENS`), mit Inhalt, der traegt:
  - Makro-Regeln aus Buch 13 (Reden, Lane-Phase, Objectives, Midgame), wissen/wellen_regeln.md, Objective-Zeiten;
  - fuer die zehn Champions dieser Partie aus wissen/lexikon/champions: Kopf, Powerspikes, Lane-Plan, Makro/Teamfight,
    fuer Gegner dazu "Gegen diesen Champion";
  - Carlos' Build (wissen/build_carlos.toml) fuer seinen Champion.
"""
from __future__ import annotations

import re
import tomllib
from functools import lru_cache
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
LEXIKON = WURZEL / "wissen" / "lexikon" / "champions"
MIN_TOKENS = 4300
ABSCHNITTE_WIR = ("Kopf", "Powerspikes", "Makro/Teamfight")
ABSCHNITTE_SIE = ("Kopf", "Powerspikes", "Lane-Plan", "Gegen diesen Champion", "Makro/Teamfight")


def _abschnitte(champion_id: str, namen: tuple[str, ...], zeichen: int) -> str:
    try:
        text = (LEXIKON / f"{champion_id}.md").read_text(encoding="utf-8")
    except OSError:
        return ""
    teile = re.split(r"^## ", text, flags=re.M)
    aus = []
    for t in teile[1:]:
        kopf, _, rumpf = t.partition("\n")
        if kopf.strip() in namen:
            aus.append(f"{kopf.strip()}: " + " ".join(z.strip("- ").strip() for z in rumpf.splitlines() if z.strip()))
    return "\n".join(aus)[:zeichen]


def _buch13() -> str:
    try:
        text = (WURZEL / "buecher" / "13_challenger_coach.md").read_text(encoding="utf-8")
    except OSError:
        return ""
    a, b = text.find("## 1."), text.find("## 6.")
    teil = text[a:b if b > 0 else None]
    return "\n".join(z for z in teil.splitlines() if not z.startswith("| ") or "Anlass" not in z)


def _wellen() -> str:
    try:
        return (WURZEL / "wissen" / "wellen_regeln.md").read_text(encoding="utf-8")
    except OSError:
        return ""


def _build(champion_id: str) -> str:
    try:
        d = tomllib.loads((WURZEL / "wissen" / "build_carlos.toml").read_text(encoding="utf-8")).get(champion_id) or {}
    except (OSError, ValueError):
        return ""
    if not d.get("folge"):
        return ""
    return (f"Carlos' eigener {champion_id}-Build (aus {d.get('partien', '?')} Partien): "
            + " > ".join(" / ".join(s) for s in d["folge"]) + (f"; Stiefel: {d['stiefel']}" if d.get("stiefel") else ""))


OBJECTIVES = ("OBJECTIVE-ZEITEN (Saison 2026): Drache 5:00, danach 5:00 nach dem Kill; Aeltester 6:00 nach der Seele. "
              "Larven 8:00 (drei), weg um 14:45. Herold 15:00, weg um 19:45. Baron 20:00, danach 6:00. Inhibitor "
              "steht nach 5:00 wieder. Ein Objective nimmt nur, wer Prio hat: ihre Lanes gepusht, tot oder im Back; "
              "sonst tauschen (sie nehmen Drache, ihr den Turm). 60 s vorher Welle crashen und back, 40 s vorher "
              "loslaufen. Nach dem Herold rotieren (Drache oder Druck auf eine Lane), nach dem Baron back und mit dem "
              "Buff alle Lanes druecken. Tote Gegner sind das Fenster: zwei tot = Objective oder Turm jetzt, ihr "
              "Jungler tot = Objective auf seiner Seite ohne Konter.")

REDEN = ("SO REDEST DU: ein Satz Beobachtung - Folge - Handlung, dann der Schritt danach. Immer genau ein Plan; "
         "aenderst du ihn, zuerst was sich geaendert hat. Keine Fuellsaetze: ohne neue Info oder Entscheidung sag "
         "NICHTS. Timer immer mit Aufgabe ('Drache in 30 Sekunden, Tryndamere tot: mit Udyr und Bot zum Drachen'). "
         "Fehlt ein starker Gegner auf seiner Lane (Kill eben, Level 6, Item-Spike), warne vor dem Roam mit Ort. "
         "Steht ein Gegner in deinem Jungle, nenn die Folge ('Buesche nicht blind betreten'). Ist der Flash oder das "
         "Leben des Lane-Gegners weg, nenn das Fenster als Option mit Uhrzeit - als Befehl nur, wenn KILL JETZT ihn "
         "nennt und nach vorn erlaubt ist. Jeder Back nennt das konkrete Item passend zu Gold und freien Plaetzen - "
         "genau das, was unter KAUF steht; nenn kein anderes Item als der Kaufplan. Widersprich dem AKTIVEN PLAN und "
         "deinen LETZTEN SAETZEN nie ohne neues Ereignis; sagt der Coach gerade 'zurueck' wegen einer Gefahr, schick "
         "den Spieler nicht nach vorn. Eine Seitenwelle (meist Top) ist kein Standardziel: nenn sie nur mit Grund "
         "(dort kommt eine grosse Welle, niemand sonst ist dort) und zieh Objectives mit dem Team vor.")


# Auftrag 024, 4 (Carlos 29:39: "die unbegrenzte Teleportation ... dass du die nie mit einkalkulierst"). Werte aus
# wissen/lexikon/saison2026.md (Rollenquests, Patch 26.19) und wissen/kern.toml [quest_tp] (gemessen 27.09.2026).
QUEST_TP = ("QUEST-TP (Saison 2026, Patch 26.19): Du spielst Top ohne Teleport. Die Top-Quest (1200 Punkte, "
            "spaetestens 13:35) gibt dir ein Quest-TP im Quest-Slot, Abklingzeit 390 s, beliebig oft. In der LAGE "
            "steht 'Quest-TP bereit' oder 'Quest-TP in N s'. Plane damit: Top-Welle crashen, dann per Quest-TP zum "
            "Drachen, zum Herold oder zur Gruppe; nach dem Back per Quest-TP zurueck auf die Lane statt zu laufen; "
            "ein Kampf an einem Objective ist fuer dich nur 'weit weg', wenn das Quest-TP nicht bereit ist.")


@lru_cache(maxsize=8)
def _block(mein: str, wir: tuple[str, ...], sie: tuple[str, ...], quest: bool = False) -> str:
    teile = [REDEN, OBJECTIVES, "WELLEN-REGELN:\n" + _wellen(), "MAKRO-REGELN (Buch 13):\n" + _buch13()]
    if quest:
        teile.insert(1, QUEST_TP)
    if (b := _build(mein)):
        teile.append(b)
    zeichen = 700
    while True:
        champs = [f"DEIN TEAM - {c}:\n{_abschnitte(c, ABSCHNITTE_WIR, zeichen)}" for c in wir] + \
                 [f"GEGNER - {c}:\n{_abschnitte(c, ABSCHNITTE_SIE, zeichen + 500)}" for c in sie]
        text = "\n\n".join(teile + ["CHAMPIONS DIESER PARTIE (Lexikon, Stand Patch 26.19):"] + champs)
        from .welt import tokens
        if tokens(text) >= MIN_TOKENS or zeichen >= 4000:
            return text
        zeichen += 400


def block(p) -> str | None:
    """Der Wissensblock fuer diese Partie (zwischengespeichert je Aufstellung) - None ohne Partie."""
    if p is None or p.ich is None:
        return None
    wir = tuple(s.champion_id for s in p.team(p.mein_team))
    sie = tuple(s.champion_id for s in p.gegner())
    quest = p.ich.rolle == "TOP" and not any("Teleport" in z for z in (p.ich.zauber or ()))
    return _block(p.ich.champion_id, wir, sie, quest)
