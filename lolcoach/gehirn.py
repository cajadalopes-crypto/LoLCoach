"""Das Gehirn: das ganze Wissen des Coaches, in jeder Sekunde griffbereit.

Carlos: "Es ist dein Gehirn - ein absoluter Top-Challenger. Extrem wichtig ist,
dass du dieses Wissen jederzeit flexibel nutzen kannst."

Drei Quellen:
  - Steckbriefe aller Champions (champions.py, Data Dragon, je Patch),
  - das Lexikon (wissen/lexikon/: grundlagen.md, saison2026.md, champions/<Id>.md),
  - die Live-Lage (antworten.lage_text: Positionen, Timer, Leben, Gold, Items).

Zu Spielbeginn verdichtet Claude daraus einmal die SPIELAKTE: was in genau
dieser Partie zaehlt. Danach bekommt jede Anfrage an Claude (Frage, Briefing,
situative Anweisung) Spielakte + passende Lexikon-Abschnitte + Lage - so ist
jede Antwort schnell und trotzdem mit allem Wissen gespeist.
"""
from __future__ import annotations

import re
import threading
from functools import lru_cache
from pathlib import Path

from . import champions, llm
from .zustand import ROLLE_DE, Partie, gegenteam

LEXIKON = Path(__file__).resolve().parent.parent / "wissen" / "lexikon"

# Stichwort in Frage/Anlass -> Abschnitte der Grundlagen, deren Ueberschrift das Wort enthaelt
STICHWORTE = {
    "welle": "Welle", "wave": "Welle", "freeze": "Welle", "freezen": "Welle", "push": "Welle",
    "pushen": "Welle", "crash": "Welle", "vorbereiten": "Welle", "recall": "Recall", "zurück": "Recall",
    "back": "Recall", "kaufen": "Recall", "gold": "Recall", "trade": "Trading", "traden": "Trading",
    "lane": "Trading", "level": "Trading", "gank": "Trading", "drache": "Objective", "baron": "Objective",
    "herold": "Objective", "larven": "Objective", "objective": "Objective", "seele": "Objective",
    "ward": "Sicht", "wards": "Sicht", "sicht": "Sicht", "vision": "Sicht", "kampf": "Teamfight",
    "teamfight": "Teamfight", "fight": "Teamfight", "split": "Teamfight", "splitpush": "Teamfight",
    "teleport": "Rollen", "tp": "Rollen", "job": "Rollen", "aufgabe": "Rollen", "rolle": "Rollen",
    "flash": "Beschw", "zünden": "Beschw", "cooldown": "Beschw",
}


@lru_cache(maxsize=None)
def _abschnitte(datei: str) -> dict[str, str]:
    pfad = LEXIKON / datei
    if not pfad.exists():
        return {}
    teile = re.split(r"^## ", pfad.read_text(encoding="utf-8"), flags=re.M)
    return {t.split("\n", 1)[0].strip(): "## " + t.strip() for t in teile[1:]}


@lru_cache(maxsize=None)
def champion_eintrag(champion_id: str) -> str | None:
    pfad = LEXIKON / "champions" / f"{champion_id}.md"
    return pfad.read_text(encoding="utf-8") if pfad.exists() else None


def grundlagen(anlass: str, hoechstens: int = 5000) -> str:
    """Die Grundlagen-Abschnitte, die zu den Stichworten in `anlass` passen."""
    abschnitte = _abschnitte("grundlagen.md")
    if not abschnitte:
        return ""
    woerter = set(re.findall(r"[a-zäöüß]+", anlass.lower()))
    gesucht = {STICHWORTE[w] for w in woerter if w in STICHWORTE}
    gewaehlt, laenge = [], 0
    for titel, text in abschnitte.items():
        if any(g.lower() in titel.lower() for g in gesucht) and laenge + len(text) <= hoechstens:
            gewaehlt.append(text)
            laenge += len(text)
    return "\n\n".join(gewaehlt)


def _champion_zeile(s) -> str:
    return f"{s.champion} ({ROLLE_DE.get(s.rolle, '?')})"


def abschnitt(champion_id: str, titel: str, hoechstens: int = 2500) -> str:
    """Ein ##-Abschnitt aus dem Champion-Eintrag des Lexikons ('' wenn keiner)."""
    eintrag = champion_eintrag(champion_id)
    if not eintrag:
        return ""
    for teil in re.split(r"^## ", eintrag, flags=re.M)[1:]:
        kopf, _, rumpf = teil.partition("\n")
        if kopf.strip().lower().startswith(titel.lower()):
            return rumpf.strip()[:hoechstens]
    return ""


def matchup(champion_id: str, gegner) -> str:
    """Die Matchup-Zeile gegen genau diesen Gegner (Lexikon, Abschnitt Matchups)."""
    for zeile in abschnitt(champion_id, "Matchups", 20000).splitlines():
        if zeile.startswith("- ") and any(n.lower() in zeile.lower()[:40] for n in {gegner.champion, gegner.champion_id}):
            return zeile[2:]
    return ""


def akte_quelle(p: Partie) -> str:
    """Rohstoff fuer Spielakte + Briefing - schlank (gemessen 26.09.: 17 000 Zeichen, 35 s):
    fuer dich Kniffe/Spikes/Lane-Plan/Build und die EINE Matchup-Zeile gegen deinen Gegner,
    fuer Lane-Gegner und Jungler das Noetigste, fuer den Rest Kurzsteckbriefe."""
    wir, die = p.mein_team, gegenteam(p.mein_team)
    g, j = p.gegenueber(), p.jungler(die)
    teile = [f"Ich: {_champion_zeile(p.ich)}. Mein Team: {', '.join(_champion_zeile(s) for s in p.team(wir))}. "
             f"Gegner: {', '.join(_champion_zeile(s) for s in p.team(die))}."]
    ich = p.ich.champion_id
    if champion_eintrag(ich):
        teile.append(f"ICH ({p.ich.champion}) - Kniffe:\n{abschnitt(ich, 'Faehigkeiten', 1800)}\n"
                     f"Spikes:\n{abschnitt(ich, 'Powerspikes', 800)}\nLane-Plan:\n{abschnitt(ich, 'Lane-Plan', 1200)}\n"
                     f"Build:\n{abschnitt(ich, 'Build', 900)}")
        if g and (zeile := matchup(ich, g)):
            teile.append(f"MATCHUP gegen {g.champion}: {zeile}")
    else:
        teile.append(champions.steckbrief(ich))
    for s, was in ((g, ("Faehigkeiten", "Powerspikes", "Gegen diesen")), (j, ("Powerspikes", "Gegen diesen"))):
        if not s:
            continue
        if champion_eintrag(s.champion_id):
            teile.append(f"{s.champion.upper()}:\n" + "\n".join(abschnitt(s.champion_id, w, 900) for w in was))
        else:
            teile.append(champions.steckbrief(s.champion_id))
    rest = [s for s in p.spieler if s not in (p.ich, g, j)]
    teile.append("UEBRIGE:\n" + "\n".join(champions.steckbrief(s.champion_id, kurz=True) for s in rest))
    return "\n\n".join(teile)


AKTE_SYSTEM = (
    "Du bist ein Challenger-Coach fuer League of Legends und bereitest dich auf die Partie deines "
    "Schuelers vor (Ziel Diamond+). Schreib zwei Teile, genau mit diesen Markern:\n"
    "AKTE:\n(fuer dich selbst, stichpunktartig, hoechstens 220 Woerter) Lane-Matchup (Trade-Fenster, welche "
    "gegnerische Faehigkeit abwarten, Spikes beider Seiten), gegnerischer Jungler (Gefahr, Gank-Zeiten), "
    "Win-Conditions beider Teams, gefaehrlichste Ults, Build-Richtung gegen dieses Team, Plan fuer "
    "Lane-Phase und danach.\n"
    "BRIEFING:\n(fuer den Spieler, ueber Headset gesprochen, 4-6 kurze Saetze, kein Markdown) das Matchup und "
    "wann er traden kann, die groesste Gefahr, die Win-Condition, die Build-Richtung.\n"
    "ULTS:\n(je gegnerischer Champion eine Zeile 'Name: Satz', hoechstens 15 Woerter, gesprochen: was seine Ult "
    "fuer den Spieler bedeutet und worauf er achten muss)\n"
    "Nur was das Material stuetzt; Item-Namen nur aus dem Material; Unsicheres als unsicher.")


BRIEFING_SYSTEM = (
    "Du bist ein Challenger-Coach und sprichst deinen Schueler vor der Partie ueber Headset an. "
    "Deutsch, gesprochen, keine Aufzaehlungszeichen, kein Markdown, 5 bis 7 kurze Saetze: "
    "das Matchup und wann er traden kann, worauf er in der Lane achten muss, die Win-Condition, "
    "die Build-Richtung gegen dieses Team. Konkret und individuell, keine Allgemeinplaetze.")

MIDGAME_SYSTEM = (
    "Du bist ein Challenger-Coach. Die Lane-Phase ist vorbei. Sag deinem Schueler ueber Headset in "
    "hoechstens 3 kurzen gesprochenen Saetzen (zusammen unter 45 Woertern; Deutsch, kein Markdown), was ab jetzt sein Job ist: "
    "Splitpush oder Gruppe, welche Seite, welche Objectives als naechstes, worauf er achten muss - "
    "abgeleitet aus Spielakte und aktueller Lage.")

SITUATIV_SYSTEM = (
    "Du bist ein Challenger-Coach und sprichst live ueber Headset. Aus dem Anlass und der Lage: sag "
    "dem Spieler in hoechstens zwei kurzen gesprochenen Saetzen (zusammen unter 30 Woertern; Deutsch, kein Markdown), was er "
    "GENAU JETZT tun soll und kurz warum - konkret fuer seine Position, sein Leben, sein Gold, die "
    "Welle und den Jungler. Keine Allgemeinplaetze. Stimmt der Anlass fuer ihn gerade nicht (zu weit "
    "weg, tot, falsche Seite), sag das Passende statt des Anlasses. Der Standardsatz zeigt nur den Anlass; "
    "kommentiere nie die Daten oder was fehlt ('nicht erwaehnt', 'laut Lage'), sprich nur zum Spieler.")


def kuerzen(text: str, saetze: int) -> str:
    """Hoechstens `saetze` Saetze - im Spiel zaehlt jede Sekunde Sprechzeit
    (Generalprobe 26.09.: ein "3-4 Saetze"-Plan kam mit acht Saetzen)."""
    teile = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(teile[:saetze]).strip()


class Gehirn:
    """Haelt die Spielakte und baut fuer jede Claude-Anfrage den Kontext."""

    def __init__(self, modell: str = "sonnet"):
        self.modell = modell
        self.akte: str | None = None
        self.briefing: str | None = None   # kommt mit der Akte (ein Aufruf statt zwei)
        self.ult_warnungen: dict[str, str] = {}  # Champion -> ein Satz zu seiner Ult (kommt mit der Akte)
        self._akte_laeuft = False
        self.ablage: Path | None = None    # je Partie: hier wird die Akte gespeichert

    # --- Spielakte ---------------------------------------------------------------

    def akte_anlegen(self, p: Partie, fertig=None) -> None:
        """Im Hintergrund (ein paar Sekunden). `fertig(akte)` wird danach gerufen."""
        if self._akte_laeuft or self.akte or not p.ich:
            return
        self._akte_laeuft = True

        def lauf():
            try:
                roh = llm.frage(akte_quelle(p), system=AKTE_SYSTEM, modell=self.modell,
                                timeout=90, aufwand="low").strip()
                akte, _, rest = roh.partition("BRIEFING:")
                briefing, _, ults = rest.partition("ULTS:")
                self.akte = akte.replace("AKTE:", "", 1).strip()
                self.ult_warnungen = {}
                for zeile in ults.splitlines():
                    name, _, satz = zeile.strip().lstrip("-* ").partition(":")
                    if name and satz.strip():
                        self.ult_warnungen[name.strip()] = kuerzen(satz.strip(), 1)
                from .itemnamen import absichern
                self.briefing = absichern(kuerzen(briefing, 6))[0] or None
            except llm.LLMFehler as e:
                print(f"  Spielakte fehlgeschlagen: {e}", flush=True)
                self.akte = None
            self._akte_laeuft = False
            if self.akte and self.ablage:
                self.ablage.write_text(self.akte, encoding="utf-8")
            if fertig:
                fertig(self.akte)

        threading.Thread(target=lauf, daemon=True).start()

    # --- Kontext fuer jede Anfrage -------------------------------------------------

    def kontext(self, anlass: str, p: Partie, lage_text: str) -> str:
        teile = []
        if self.akte:
            teile.append("SPIELAKTE (deine Vorbereitung):\n" + self.akte)
        else:
            teile.append("CHAMPIONS:\n" + "\n".join(champions.steckbrief(s.champion_id, kurz=True)
                                                    for s in p.spieler))
        if g := grundlagen(anlass):
            teile.append("LEXIKON (passende Grundlagen):\n" + g)
        teile.append("LAGE JETZT:\n" + lage_text)
        return "\n\n".join(teile)

    def frage(self, system: str, anlass: str, p: Partie, lage_text: str, timeout: float = 40) -> str:
        return llm.frage(f"{self.kontext(anlass, p, lage_text)}\n\nANLASS: {anlass}", system=system,
                         modell=self.modell, timeout=timeout, aufwand="low").strip()
