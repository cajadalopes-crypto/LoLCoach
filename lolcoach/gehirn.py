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
    # mechaniken.md (26.09.): Zahlen zu Schaden, XP, Gold, Tod, Vasallen, Tuermen, Camps, Monstern, CC
    "schaden": "Schaden", "kill": "Schaden", "killen": "Schaden", "töten": "Schaden", "rüstung": "Schaden",
    "magieresistenz": "Schaden", "durchdringung": "Schaden", "letalität": "Schaden", "heilung": "Schaden",
    "xp": "Erfahrung", "erfahrung": "Erfahrung", "respawn": "Tod", "respawnt": "Tod", "todeszeit": "Tod", "tot": "Tod",
    "kopfgeld": "Gold", "shutdown": "Gold", "bounty": "Gold", "platten": "Tuerme", "turm": "Tuerme",
    "türme": "Tuerme", "vasallen": "Vasallen", "kanone": "Vasallen", "minions": "Vasallen",
    "camp": "Dschungel", "camps": "Dschungel", "buff": "Dschungel", "scuttle": "Dschungel", "smite": "Dschungel",
    "jungle": "Dschungel", "tempo": "Bewegung", "laufen": "Bewegung", "stiefel": "Bewegung",
    "betäubung": "Kontrolle", "cc": "Kontrolle", "reinigen": "Kontrolle", "qss": "Kontrolle",
    "zähigkeit": "Kontrolle",
}
# Stichworte, die auch die Epischen Monster (mechaniken.md) brauchen
AUCH = {"Objective": "Epische", "Sicht": "Sicht", "Beschw": "Beschwoerer"}


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
    """Die Abschnitte aus grundlagen.md und mechaniken.md, die zu den Stichworten in `anlass` passen."""
    abschnitte = {**_abschnitte("grundlagen.md"), **_abschnitte("mechaniken.md")}
    if not abschnitte:
        return ""
    woerter = set(re.findall(r"[a-zäöüß]+", anlass.lower()))
    gesucht = {STICHWORTE[w] for w in woerter if w in STICHWORTE}
    gesucht |= {AUCH[g] for g in gesucht if g in AUCH}
    gewaehlt, laenge = [], 0
    for titel, text in abschnitte.items():
        if any(g.lower() in titel.lower() for g in gesucht) and laenge + len(text) <= hoechstens:
            gewaehlt.append(text)
            laenge += len(text)
    return "\n\n".join(gewaehlt)


def _champion_zeile(s) -> str:
    """'Riven (Top; Zünden + Flash)' - die Zauber gehoeren dazu: ohne sie riet das Briefing
    (26.09.) einmal zu Entzuenden, einmal zu Teleport, bei derselben Riven mit Zuenden."""
    from .zauber import NAME_DE
    zauber = " + ".join(NAME_DE.get(z, z.removeprefix("Summoner")) for z in s.zauber)
    return f"{s.champion} ({ROLLE_DE.get(s.rolle, '?')}{'; ' + zauber if zauber else ''})"


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
        # ganze Woerter: "Vi" steckt sonst in "Viego" und bekam dessen Zeile
        if zeile.startswith("- ") and any(re.search(rf"(?<![\w']){re.escape(n.lower())}(?![\w'])", zeile.lower()[:40])
                                          for n in {gegner.champion, gegner.champion_id}):
            return zeile[2:]
    return ""


def akte_quelle(p: Partie, fokus: str | None = None) -> str:
    """Rohstoff fuer Spielakte + Briefing - schlank (gemessen 26.09.: 17 000 Zeichen, 35 s):
    fuer dich Kniffe/Spikes/Lane-Plan/Build und die EINE Matchup-Zeile gegen deinen Gegner,
    fuer Lane-Gegner und Jungler das Noetigste, fuer den Rest Kurzsteckbriefe.
    `fokus`: der Fokus aus dem Review der letzten Partie (profil.fokus)."""
    wir, die = p.mein_team, gegenteam(p.mein_team)
    g, j = p.gegenueber(), p.jungler(die)
    teile = [f"Ich: {_champion_zeile(p.ich)}. Mein Team: {', '.join(_champion_zeile(s) for s in p.team(wir))}. "
             f"Gegner: {', '.join(_champion_zeile(s) for s in p.team(die))}."]
    if p.ich.rolle == "TOP" and "SummonerTeleport" not in p.ich.zauber:
        teile[0] += (" Ich habe KEINEN Teleport; die Top-Rollenquest gibt mir spaetestens um 13:35 einen "
                     "(Abklingzeit dann 390 s) - vorher kein TP-Plan.")
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
    if fokus:
        teile.append(f"FOKUS DES SPIELERS (aus dem Review seiner letzten Partie): {fokus}")
    return "\n\n".join(teile)


AKTE_SYSTEM = (
    "Du bist ein Challenger-Coach fuer League of Legends und bereitest dich auf die Partie deines "
    "Schuelers vor (Ziel Diamond+). Schreib diese Teile, genau mit diesen Markern:\n"
    "AKTE:\n(fuer dich selbst, stichpunktartig, hoechstens 220 Woerter) Lane-Matchup (Trade-Fenster, welche "
    "gegnerische Faehigkeit abwarten, Spikes beider Seiten), gegnerischer Jungler (Gefahr, Gank-Zeiten), "
    "Win-Conditions beider Teams, gefaehrlichste Ults, Build-Richtung gegen dieses Team, Plan fuer "
    "Lane-Phase und danach.\n"
    "BRIEFING:\n(fuer den Spieler, ueber Headset gesprochen, der Lane-Guide fuer die ersten Minuten: genau 5 "
    "kurze Saetze, zusammen hoechstens 70 Woerter, kein Markdown, keine Doppelpunkt-Etiketten. 1. 'Spiel die Lane "
    "...' mit der SPIELWEISE - genau eine von: aggressiv traden, Level-2-All-in, sicher farmen und skalieren, Welle "
    "freezen, pushen und roamen, Proxy-Farmen - und warum genau in diesem Matchup. 2. Level 1 bis 3 in EINEM Satz "
    "(wann traden, welche gegnerische Faehigkeit abwarten). 3. die ersten Wellen. 4. der erste Back (ab wie viel "
    "Gold, welches Item). 5. die groesste Gefahr mit Zeit (z. B. Jungler-Gank ab 3:15).)\n"
    "LANEPLAN:\n(fuer den Bildschirm, zum Ablesen im Spiel: genau diese sechs Zeilen, je hoechstens 12 Woerter, "
    "ohne Markdown-Zeichen:\nSpielweise: ...\nLevel 1-3: ...\nWellen: ...\nErster Back: ...\nGefahr: ...\n"
    "Danach: ... (Plan nach der Lane-Phase))\n"
    "ULTS:\n(je gegnerischer Champion eine Zeile 'Name: Satz', hoechstens 15 Woerter, gesprochen: was seine Ult "
    "fuer den Spieler bedeutet und worauf er achten muss)\n"
    "FOKUS:\n(nur wenn das Material einen FOKUS DES SPIELERS nennt: EIN kurzer gesprochener Satz, hoechstens 20 "
    "Woerter, der diesen Fokus auf genau diese Partie anwendet - wann und wogegen er heute darauf achten muss; "
    "ohne Zeichen wie / oder +. Das BRIEFING selbst erwaehnt den Fokus nicht, dieser Satz wird danach gesprochen)\n"
    "Zahlen immer als Ziffern (1300 Gold, 3:15), nie ausgeschrieben - BRIEFING und LANEPLAN nennen dieselben "
    "Zahlen. Nur was das Material stuetzt; Item-Namen nur aus dem Material; Unsicheres als unsicher.")


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
    "kommentiere nie die Daten oder was fehlt ('nicht erwaehnt', 'laut Lage'), sprich nur zum Spieler. "
    "Sauberes gesprochenes Deutsch: LoL-Begriffe (All-in, Trade, Welle, Gank) als Nomen, keine "
    "eingedeutschten Verben wie 'all-inen'. Liegt ein Bild bei, ist es sein Bildschirm jetzt: nutze, was "
    "darauf zu sehen ist (Lebensbalken ueber den Koepfen, wer nah ist, Vasallen, sein Leben und Mana unten), "
    "aber sag nur, was wirklich zu sehen ist.")


BRIEFING_WOERTER = 75   # ~25 s Sprechzeit; der Fokus-Satz kommt dazu (Partie 4: 120 Woerter = 45 s)

TOD_SYSTEM = (
    "Du bist ein Challenger-Coach und sprichst live ueber Headset. Dein Schueler ist gerade gestorben und "
    "wartet auf den Wiedereinstieg. Sag ihm in hoechstens zwei kurzen gesprochenen Saetzen (zusammen unter 35 "
    "Woertern; Deutsch, kein Markdown): den eigentlichen Grund - nur aus den FAKTEN, nichts dazuerfinden; steht "
    "dort, dass die Minimap nicht gelesen wurde, sag nichts ueber Sicht oder wer zu sehen war - und "
    "was er in genau so einer Lage naechstes Mal tut. Kein Trost, kein Vorwurf, keine Allgemeinplaetze. Zeigen "
    "die Fakten keinen Fehler (fairer Tausch, Objective dafuer bekommen), sag das in einem Satz. Hat der Tod mit "
    "seinem FOKUS HEUTE zu tun, sag es. Spawnt gleich ein Objective, das er verpasst, sag, was das Team jetzt "
    "tun sollte. Kommentiere nie die Daten, sprich nur zum Spieler. Liegen Bilder bei, sind es seine "
    "Bildschirme etwa 6 und 3 Sekunden vor dem Tod: lies daraus, was die Fakten nicht haben (Leben beider "
    "Seiten, wer im Kampf war, Vasallen, Turm) - nur, was wirklich zu sehen ist.")


_MARKER = re.compile(r"(?m)^[#*\s]*(AKTE|BRIEFING|LANEPLAN|ULTS|FOKUS)[*\s]*:[*]*")
LANEPLAN_FELDER = ("Spielweise", "Level 1-3", "Wellen", "Erster Back", "Gefahr", "Danach")


def akte_teile(roh: str) -> dict[str, str]:
    """Die Antwort auf AKTE_SYSTEM in ihre Teile - robust gegen Markdown um die Marker und gegen
    fehlende Teile (vorher: partition-Kette; fehlte ein Marker, verrutschte alles danach)."""
    stuecke = _MARKER.split(roh)
    teile = {stuecke[i]: stuecke[i + 1].strip() for i in range(1, len(stuecke) - 1, 2)}
    if "AKTE" not in teile and stuecke[0].strip():
        teile["AKTE"] = stuecke[0].strip()
    return teile


def laneplan_zeilen(text: str) -> list[str]:
    """Nur die sechs erwarteten Zeilen, in fester Reihenfolge, ohne Aufzaehlungszeichen."""
    gefunden = {}
    for zeile in text.splitlines():
        z = zeile.strip().lstrip("-*• ").replace("**", "").replace("–", "-").replace("—", "-")
        for feld in LANEPLAN_FELDER:
            if z.lower().startswith(feld.lower()) and ":" in z:
                gefunden.setdefault(feld, f"{feld}: {z.split(':', 1)[1].strip()}")
    return [gefunden[f] for f in LANEPLAN_FELDER if f in gefunden]


def kuerzen(text: str, saetze: int, woerter: int | None = None) -> str:
    """Hoechstens `saetze` Saetze - im Spiel zaehlt jede Sekunde Sprechzeit
    (Generalprobe 26.09.: ein "3-4 Saetze"-Plan kam mit acht Saetzen). `woerter`: dazu eine
    Obergrenze an ganzen Saetzen entlang (Partie 4: sechs Saetze waren 120 Woerter, 45 s)."""
    teile = re.split(r"(?<=[.!?])\s+", text.strip())[:saetze]
    if woerter:
        aus, n = [], 0
        for t in teile:
            n += len(t.split())
            if aus and n > woerter:
                break
            aus.append(t)
        teile = aus
    return " ".join(teile).strip()


class Gehirn:
    """Haelt die Spielakte und baut fuer jede Claude-Anfrage den Kontext."""

    def __init__(self, modell: str = "sonnet"):
        self.modell = modell
        self.akte: str | None = None
        self.briefing: str | None = None   # kommt mit der Akte (ein Aufruf statt zwei)
        self.ult_warnungen: dict[str, str] = {}  # Champion -> ein Satz zu seiner Ult (kommt mit der Akte)
        self.fokus_satz: str | None = None       # der Fokus aus dem letzten Review, auf diese Partie bezogen
        self.fokus: str | None = None            # derselbe Fokus im Wortlaut des Reviews (Dashboard)
        self.laneplan: list[str] = []            # "Spielweise: ...", "Level 1-3: ..." (Dashboard-Zettel)
        self._akte_laeuft = False
        self.ablage: Path | None = None    # je Partie: hier wird die Akte gespeichert

    # --- Spielakte ---------------------------------------------------------------

    def akte_anlegen(self, p: Partie, fertig=None) -> None:
        """Im Hintergrund (ein paar Sekunden). `fertig(akte)` wird danach gerufen."""
        if self._akte_laeuft or self.akte or not p.ich:
            return
        self._akte_laeuft = True

        def lauf():
            fokus = None
            if self.ablage:
                try:
                    from . import profil
                    fokus = profil.fokus(self.ablage.parent, vor=self.ablage.name.removesuffix("_spielakte.md"))
                except Exception as e:  # das Profil ist Zugabe - ohne es geht die Akte trotzdem
                    print(f"  Profil nicht lesbar: {e}", flush=True)
            self.fokus = fokus
            try:
                roh = llm.frage(akte_quelle(p, fokus), system=AKTE_SYSTEM, modell=self.modell,
                                timeout=90, aufwand="low").strip()
                teile = akte_teile(roh)
                akte, briefing = teile.get("AKTE", ""), teile.get("BRIEFING", "")
                ults, fokus_satz = teile.get("ULTS", ""), teile.get("FOKUS", "")
                self.laneplan = laneplan_zeilen(teile.get("LANEPLAN", ""))
                self.akte = akte.strip()
                if self.laneplan:
                    self.akte += "\nLANE-PLAN (so hast du es ihm gesagt):\n" + "\n".join(self.laneplan)
                if fokus:
                    self.akte += f"\nFOKUS HEUTE (aus dem Review der letzten Partie): {fokus}"
                self.ult_warnungen = {}
                for zeile in ults.splitlines():
                    name, _, satz = zeile.strip().lstrip("-* ").partition(":")
                    if name and satz.strip():
                        self.ult_warnungen[name.strip()] = kuerzen(satz.strip(), 1)
                from .itemnamen import absichern
                briefing = kuerzen(briefing, 6, woerter=BRIEFING_WOERTER)
                if fokus and (fokus_satz := kuerzen(fokus_satz.strip(), 1)):
                    briefing += " " + fokus_satz
                self.fokus_satz = fokus_satz if fokus else None
                self.briefing = absichern(briefing)[0] or None
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

    def frage(self, system: str, anlass: str, p: Partie, lage_text: str, timeout: float = 40,
              bilder: list[bytes] | None = None) -> str:
        return llm.frage(f"{self.kontext(anlass, p, lage_text)}\n\nANLASS: {anlass}", system=system, bilder=bilder,
                         modell=self.modell, timeout=timeout, aufwand="low").strip()
