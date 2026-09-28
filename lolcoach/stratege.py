"""Der Stratege: laesst das Gehirn im Spiel mitreden.

- Spielbeginn: Spielakte anlegen, danach das Briefing sprechen.
- Ende der Lane-Phase: "was ist ab jetzt dein Job".
- Situative Ansagen: Die Regeln entscheiden WANN (schnell, deterministisch), der
  Stratege laesst Claude formulieren WAS genau - fuer Carlos, aus der echten Lage.
  Carlos: "Er soll mir immer situativ sagen, wie ich das genau machen soll. Ich
  wuensche mir sehr viel Individualitaet beim Coach." Kommt Claude nicht rechtzeitig,
  wird der Standardsatz gesprochen - lieber allgemein als zu spaet.

Alles laeuft in Hintergrund-Threads; fertige Saetze gehen ueber `plan.einwerfen`
in den Sprechplan und werden dort wie jede Ansage getaktet.
"""
from __future__ import annotations

import threading
import time

from . import antworten, gehirn
from .regeln import WICHTIG, Ansage

VEREDELN_HOECHSTENS = 12.0   # Sekunden: laenger wartet der Standardsatz nicht
SPAET_EINGESTIEGEN = 180.0   # Spielzeit: danach kein Briefing mehr (Coach mitten in der Partie gestartet)
SYSTEM_JE_SCHLUESSEL = {"tod": gehirn.TOD_SYSTEM}


class Stratege:
    def __init__(self, plan, modell: str = "sonnet", lane_phase_bis: float = 840, werk=None):
        self.plan, self.werk = plan, werk
        self.gehirn = gehirn.Gehirn(modell)
        self.lane_phase_bis = lane_phase_bis
        self._briefing = self._midgame = False
        self.p = self.lagebild = None

    def aktualisiere(self, p, lagebild=None, ansagen=None) -> None:
        self.p, self.lagebild = p, lagebild
        if not p.ich:
            return
        if not self._briefing and p.spieler:
            self._briefing = True
            # Mitten in der Partie gestartet (Neustart, Reconnect): Akte ja - fuer Fragen und Vorwarnungen -,
            # aber kein Lane-Guide in Minute 19 (Partie 6, 16:42)
            spaet = p.zeit > SPAET_EINGESTIEGEN
            self.gehirn.akte_anlegen(p, fertig=lambda akte: self._briefing_sprechen(sprechen=not spaet))
        if not self._midgame and p.zeit >= self.lane_phase_bis and self.gehirn.akte:
            self._midgame = True
            self._im_hintergrund(lambda: self._sprich(gehirn.MIDGAME_SYSTEM, "Ende der Lane-Phase: sein Job ab jetzt",
                                                      "midgame"))

    def _briefing_sprechen(self, sprechen: bool = True) -> None:
        """Das Briefing kommt mit der Spielakte; nur wenn es fehlt, eigener Aufruf.
        `sprechen=False`: spaet eingestiegen - nur die Ult-Warnungen uebernehmen."""
        if self.werk is not None:
            self.werk.ult_warnungen = dict(self.gehirn.ult_warnungen)
            self.werk.trade_hinweis = self.gehirn.trade_hinweis
        if not sprechen:
            return
        if self.gehirn.briefing and self.p is not None:
            self.plan.einwerfen(Ansage(self.gehirn.briefing, WICHTIG, "briefing", zeit=self.p.zeit,
                                       gueltig=90, sperre=600, unterbrechbar=True))
        else:
            self._sprich(gehirn.BRIEFING_SYSTEM, "Spielbeginn: Briefing fuer den Spieler", "briefing")

    def _im_hintergrund(self, f) -> None:
        threading.Thread(target=f, daemon=True).start()

    def _sprich(self, system: str, anlass: str, schluessel: str) -> None:
        p, lb = self.p, self.lagebild
        if p is None or not p.ich:
            return
        try:
            text = self.gehirn.frage(system, anlass, p, antworten.lage_text(p, lb), timeout=60)
        except Exception as e:
            print(f"  {schluessel} fehlgeschlagen: {e}", flush=True)
            return
        from .itemnamen import absichern
        text = absichern(gehirn.kuerzen(text, 6 if schluessel == "briefing" else 3))[0]
        self.plan.einwerfen(Ansage(text, WICHTIG, schluessel, zeit=self.p.zeit, gueltig=90, sperre=600,
                                   unterbrechbar=True))

    def _bilder(self, a: Ansage) -> list[bytes] | None:
        """Der Spielbildschirm fuer Claude: beim Tod zwei Bilder davor (6 und 3 s - danach ist der
        Bildschirm grau), sonst der jetzige. None ohne Beobachter (Aufnahme, Tests)."""
        b = getattr(self, "beobachter", None)
        if b is None:
            return None
        bilder = [b.bildschirm(6), b.bildschirm(3)] if a.schluessel == "tod" else [b.bildschirm(0)]
        return [x for x in bilder if x] or None

    def veredle(self, a: Ansage) -> None:
        """Ersetzt den Standardsatz durch eine situative Anweisung. Gibt nach
        `a.frist` (sonst `VEREDELN_HOECHSTENS`) Sekunden auf und laesst den Standardsatz
        sprechen. Bringt die Ansage eigene Fakten mit (`a.kontext`, z. B. die Todesanalyse),
        stehen die statt der Lage im Auftrag."""
        p, lb = self.p, self.lagebild
        if p is None or not p.ich:
            self.plan.einwerfen(a)
            return
        erledigt = threading.Event()
        frist = a.frist or VEREDELN_HOECHSTENS
        system = SYSTEM_JE_SCHLUESSEL.get(a.schluessel, gehirn.SITUATIV_SYSTEM)
        bilder = self._bilder(a)

        def lauf():
            try:
                lage = ("FAKTEN:\n" + a.kontext) if a.kontext else antworten.lage_text(p, lb)
                text = self.gehirn.frage(system, f"{a.text} (Standardsatz der Regel)", p, lage, timeout=frist + 5,
                                         bilder=bilder)
            except Exception:
                text = None
            if not erledigt.is_set():
                erledigt.set()
                if text:
                    from .itemnamen import absichern
                    a.text = absichern(gehirn.kuerzen(text, 2))[0]
                self.plan.einwerfen(a)

        def notbremse():
            time.sleep(frist)
            if not erledigt.is_set():
                erledigt.set()
                self.plan.einwerfen(a)

        self._im_hintergrund(lauf)
        self._im_hintergrund(notbremse)


# --- Auftrag 014: Claude als Makro-Stratege - Systemprompt und harte Pruefung ------------------------------------------

import re as _re

# Auftrag 013, Lauf 2 plus Auftrag 014, A3/A4 (innere Begriffe, Sichtung, Hin und Her, Ton)
STRATEGE_SYSTEM = (
    "Du bist ein Challenger-Makro-Coach fuer League of Legends und sitzt neben dem Spieler, der gerade spielt. "
    "Antworte auf Deutsch, gesprochen, in ein bis zwei Saetzen, ohne Listen, ohne Markdown, ohne Floskeln: den "
    "naechsten Schritt, danach den Schritt danach, und den entscheidenden Grund aus der Lage. Liegen zwei Wege nah "
    "beieinander, nenn beide. Nutze nur Fakten aus der Lage - Namen, Zeiten, Zahlen, Orte - und erfinde nichts; "
    "weisst du etwas nicht, sag es kurz. Die KANDIDATEN DES COACHS sind gerechnete Fakten, keine Vorgabe. Steht "
    "NACH VORN VERBOTEN in der Lage, rate nichts nach vorn (Turm, Kampf, Objective, tief gehen), sondern nur, was "
    "dort erlaubt ist; was unter ZU RISKANT steht, schlaegst du nicht vor. 'Zuletzt gesehen vor N s ... jetzt "
    "unbekannt' heisst: der Gegner kann ueberall sein - gib fuer ihn nie Entwarnung. Porten nur, wenn DEINE ZAUBER "
    "TP bereit nennt. Sprich nie ueber Innereien: keine Worte wie R1, EV, Wert, Kern, Kandidat, Modell, gesperrt, "
    "und keine Todesrisiko-Zahlen. Innerhalb von 30 Sekunden drehst du deine letzte Empfehlung nicht um, ausser die "
    "Lage hat sich geaendert - dann sag zuerst, was sich geaendert hat ('Jetzt, wo Yi unten aufgetaucht ist: ...'). "
    "Eine Beobachtung des Spielers ist eine Tatsache - glaub ihm und plane neu. Nie von oben herab. Laenge: "
    "hoechstens 25 Woerter insgesamt, zwei kurze Saetze, kein Absatz - er hoert zu, waehrend er spielt.")

VORWAERTS = _re.compile(
    r"\b(drück|drücke|drückt|push|pusht|pushen|erzwing\w*|nimm (den|ihren|das|die)|rein(gehen)?\b|geh (rein|drauf)|"
    r"greif\w* an|angreifen|all.?in\b|invad\w*|tauch\w*|dive\b|kampf (nehmen|annehmen)|nimm den kampf|"
    r"richtung (baron|drache|drachen|herold|turm|inhib\w*|nexus)|zum (baron|drachen|herold|turm|inhibitor|nexus)|"
    r"auf (ihren|den) \w*[- ]?(turm|inhib\w*|nexus)|turm (nehmen|holen|drücken)|splitt?\w*|split.?push\w*)", _re.I)
VOR_AUFGESCHOBEN = _re.compile(r"(nicht|kein|nie\b|statt|erst wenn|sobald|wenn du wieder|nach dem (back|kauf|respawn)|"
                               r"danach|dann|später|zurück, |heil)\W*(\w+\W+){0,6}$", _re.I)
VOR_VERNEINT_DANACH = _re.compile(r"^\W*(\w+\W+){0,4}(nicht|verboten|zu riskant|gestrichen|lass|vergiss)", _re.I)
INNERE = _re.compile(r"\bR[12]\b|\bEV\b|p_tod|todesrisiko\W+(\w+\W+){0,3}\d|\b\d[.,]\d\d\b|\bkerns?\b|kandidat|"
                     r"gesperrt|\bmodell\b|hysterese|\bwert [+-]?\d", _re.I)
ENTWARNUNG = _re.compile(r"kein(e|en)? (gank-?)?(risiko|gefahr|sorge)|keine angst|weit weg|in seiner (basis|base)|"
                         r"in der (basis|base)|ist eh (in|im|weg)|steht (eh |noch |gerade )?(in|im) (seiner|der) (basis|base)|"
                         r"\bsafe\b|\bsicher\b", _re.I)
TP_WORT = _re.compile(r"\b(tp|teleport\w*|port\w*)\b", _re.I)
TP_OK = _re.compile(r"in \d+ s|sobald|wenn dein tp|tp ist wieder|ohne tp|kein tp|tp (ist )?(noch )?nicht", _re.I)
FLASH_EIGEN = _re.compile(r"\b(dein(en)? flash|mit flash|flash (rein|rüber|drüber|hinterher))", _re.I)
ULT_EIGEN = _re.compile(r"\b(dein(e|er)? (ult|r)|mit (der |deiner )?ult|ult (rein|drauf))\b", _re.I)
OBJ_WORT = {"drache": r"drache|drachen", "baron": r"baron", "herold": r"herold", "larven": r"larven",
            "aeltester": r"ältest\w*"}


def _alle_champions() -> list[str]:
    try:
        from . import ddragon
        return sorted({v.get("name", "") for v in ddragon.champions().values()} - {""}, key=len, reverse=True)
    except Exception:
        return []


def pruef_lage(kern, p) -> dict:
    """Was `pruefe` ueber die Lage wissen muss - nur Daten (JSON-faehig, fuer Protokoll und Nachspielen)."""
    m = kern.m
    b = m.b if m is not None else None
    j = b.jungler if b is not None else None
    return {
        "champions": sorted({s.champion for s in p.spieler}) if p is not None else [],
        "gegner": [{"name": g.champion, "sichtbar": bool(g.sichtbar), "seit": g.seit, "tot": bool(g.s.tot)}
                   for g in (b.gegner if b is not None else [])],
        "jungler": j.champion if j is not None else None,
        "flash": b.flash if b is not None else None, "tp": m.tp_in if m is not None else None,
        "ult": b.ult if b is not None else None, "vorn": kern.vorn(),
    }


def _saetze(text: str) -> list[str]:
    return [s for s in _re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def _nach_vorn(satz: str) -> str | None:
    """Die erste Vorwaerts-Handlung im Satz, die weder verneint noch auf spaeter verschoben ist."""
    for m in VORWAERTS.finditer(satz):
        vor, nach = satz[:m.start()], satz[m.end():]
        welle_rein = m.group(0).lower().startswith("rein") and _re.search(r"welle\W*$", vor, _re.I)   # "Welle rein"
        if welle_rein or VOR_AUFGESCHOBEN.search(vor) or VOR_VERNEINT_DANACH.search(nach):
            continue
        return m.group(0)
    return None


def pruefe(satz: str, lage: dict) -> list[str]:
    """Auftrag 014, A2: die Gruende, aus denen ein Stratege-Satz nicht gesprochen werden darf - leer heisst: ok.
    1 nach vorn trotz R1 (oder zu einem zu riskanten Objective), 2 innere Begriffe, 3 Entwarnung fuer einen Gegner,
    der > 20 s nicht zu sehen war, 4 Fakten: Champion nicht in der Partie, TP/Flash/Ult nicht bereit."""
    gruende = []
    vorn = lage.get("vorn") or {}
    for s in _saetze(satz):
        if vorn.get("verboten") and (w := _nach_vorn(s)):
            gruende.append(f"nach vorn trotz R1 ({w})")
        for o in vorn.get("ziele") or []:
            muster = OBJ_WORT.get(o)
            if muster and _re.search(muster, s, _re.I) and (w := _nach_vorn(s)) is not None:
                gruende.append(f"zu riskantes Ziel ({o}: {w})")
        if (m := INNERE.search(s)):
            gruende.append(f"innerer Begriff ({m.group(0)})")
        if ENTWARNUNG.search(s):
            blind = [g["name"] for g in lage.get("gegner") or [] if not g["sichtbar"] and not g["tot"]
                     and (g["seit"] is None or g["seit"] > 20)]
            genannt = [n for n in blind if n.split()[0].lower() in s.lower()]
            if genannt:
                gruende.append(f"Entwarnung ohne Sicht ({', '.join(genannt)})")
            elif _re.search(r"kein(e|en)? (gank-?)?(risiko|gefahr)|keine angst", s, _re.I) and lage.get("jungler") in blind:
                gruende.append(f"Entwarnung ohne Sicht auf den Jungler ({lage['jungler']})")
        tp = lage.get("tp")
        if TP_WORT.search(s) and not TP_OK.search(s) and (tp is None or tp > 0):
            gruende.append("TP nicht bereit" if tp is not None else "kein TP bekannt")
        if FLASH_EIGEN.search(s) and lage.get("flash") is not None and lage["flash"] > 0:
            gruende.append("dein Flash ist nicht bereit")
        if ULT_EIGEN.search(s) and lage.get("ult") is False:
            gruende.append("deine Ult ist nicht bereit")
    im_spiel = set(lage.get("champions") or [])
    for n in _alle_champions():
        if n not in im_spiel and _re.search(rf"(?<!\w){_re.escape(n)}(?!\w)", satz):
            gruende.append(f"Champion nicht in der Partie ({n})")
    return list(dict.fromkeys(gruende))
