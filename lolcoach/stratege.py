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
    "hoechstens 25 Woerter insgesamt, zwei kurze Saetze, kein Absatz - er hoert zu, waehrend er spielt. "
    # Auftrag 016, 2 und 4 (Carlos' Notizen in 133448: Ketten statt Einzelbefehle; 9:29 "schwach" bei vollem Leben)
    "Sag immer die Kette, damit er sofort handeln kann: jeder Back-Rat nennt IM SELBEN SATZ, was er kauft (passend zu "
    "Gold und freien Plaetzen unter KAUF) und wohin danach, mit Grund - 'Back jetzt: Axiombogen, dann zu Yorick nach "
    "Mid, weil ...'. Angreifen (geh an, greif an, trade, all-in) nur, wenn KILL JETZT einen Gegner nennt; 'schwach' "
    "nur fuer einen Gegner unter 50 Prozent Leben. Bei NACH VORN VERBOTEN ist auch jede Welle, die du zum Gegner "
    "schiebst, nach vorn. Ein Kontroll-Auge hoechstens einmal je Back vorschlagen und nie als Grund fuer einen Back.")

VORWAERTS = _re.compile(
    r"\b(drück|drücke|drückt|push|pusht|pushen|erzwing\w*|nimm (den|ihren|das|die)(?! (welle|kanone|vasallen|cs)\b)|"
    r"rein(gehen)?\b|geh (rein|drauf)|"
    r"greif\w* an|angreifen|all[- ]?in\b|invad\w*|tauch\w*|dive\b|kampf (nehmen|annehmen)|nimm den kampf|"
    r"richtung (baron|drache|drachen|herold|inhib\w*|nexus)|zum (baron|drachen|herold|inhibitor|nexus)|"
    r"auf (ihren|den|die) ([\w-]+ ){0,2}[\w-]*(turm|inhib\w*|nexus)|turm (nehmen|holen|drücken)|splitt?\w*|"
    r"split.?push\w*)", _re.I)
VOR_AUFGESCHOBEN = _re.compile(r"(nicht|kein|nie\b|statt|erst wenn|sobald|wenn du wieder|nach dem (back|kauf|respawn)|"
                               r"später|zurück, |heil)\W*(\w+\W+){0,6}$", _re.I)
# "danach" / "dann" verschiebt nur nach einer Erholung ("Back jetzt, danach mit der Gruppe zum Drachen") - nicht nach
# "Nimm die Welle, dann auf den inneren Top-Turm" (Auftrag 015)
VOR_DANACH = _re.compile(r"(danach|dann)\W*(\w+\W+){0,6}$", _re.I)
ERHOLUNG = _re.compile(r"back|recall|heil|kauf|respawn|basis|lebst|zurück", _re.I)
VOR_VERNEINT_DANACH = _re.compile(r"^\W*(\w+\W+){0,4}(nicht|verboten|zu riskant|gestrichen|lass|vergiss)", _re.I)
INNERE = _re.compile(r"\bR[12]\b|\bEV\b|p_tod|todesrisiko\W+(\w+\W+){0,3}\d|\b\d[.,]\d\d\b|\bkerns?\b|kandidat|"
                     r"gesperrt|\bmodell\b|hysterese|\bwert [+-]?\d|"
                     # Auftrag 019: Haiku sagte "Der Entwurf passt nicht" (Nachspiel 101426, fuenfmal)
                     r"\bentwurf", _re.I)
ENTWARNUNG = _re.compile(r"kein(e|en)? (gank-?)?(risiko|gefahr|sorge)|keine angst|weit weg|in seiner (basis|base)|"
                         r"in der (basis|base)|ist eh (in|im|weg)|steht (eh |noch |gerade )?(in|im) (seiner|der) (basis|base)|"
                         r"\bsafe\b|\bsicher\b", _re.I)
TP_WORT = _re.compile(r"\b(tp|teleport\w*|port\w*)\b", _re.I)
TP_OK = _re.compile(r"in \d+ ?s\b|in \d+ sekunden|sobald|wenn dein tp|tp ist wieder|ohne tp|kein tp|tp (ist )?(noch )?nicht", _re.I)
FLASH_EIGEN = _re.compile(r"\b(dein(en)? flash|mit flash|flash (rein|rüber|drüber|hinterher))", _re.I)
ULT_EIGEN = _re.compile(r"\b(dein(e|er)? (ult|r)|mit (der |deiner )?ult|ult (rein|drauf))\b", _re.I)
OBJ_WORT = {"drache": r"drache|drachen", "baron": r"baron(?!-buff)", "herold": r"herold", "larven": r"larven",
            "aeltester": r"ältest\w*"}


def _alle_champions() -> list[str]:
    try:
        from . import ddragon
        return sorted({v.get("name", "") for v in ddragon.champions().values()} - {""}, key=len, reverse=True)
    except Exception:
        return []


def _seite(ort: str | None) -> str | None:
    """oben / unten / mitte / basis aus einem Ort ("in eurem oberen Jungle", "auf der Mid-Lane", "in eurer Basis")."""
    o = (ort or "").lower()
    if "basis" in o or "brunnen" in o:
        return "basis"
    if any(w in o for w in ("ober", "oben", "top")):
        return "oben"
    if any(w in o for w in ("unter", "unten", "bot")):
        return "unten"
    if any(w in o for w in ("mitte", "mid")):
        return "mitte"
    return None


def _besetzt(m) -> dict:
    if m is None:
        return {}
    try:
        from .kern.modi import lanes_besetzt
        return lanes_besetzt(m)
    except Exception:
        return {}


def pruef_lage(kern, p) -> dict:
    """Was `pruefe` ueber die Lage wissen muss - nur Daten (JSON-faehig, fuer Protokoll und Nachspielen)."""
    from .bewertung import WEGFAKTOR, abstand
    m = kern.m
    b = m.b if m is not None else None
    j = b.jungler if b is not None else None
    gesehen = {s.champion: (wo, ort) for s, wo, _, ort in (b.mitspieler if b is not None else [])}
    mitspieler = []
    if p is not None and p.ich is not None:
        for s in p.team(p.mein_team):
            if s is p.ich or s.name == p.ich.name:
                continue
            wo, ort = gesehen.get(s.champion, (None, None))
            ankunft = (abstand(wo, b.pos) * WEGFAKTOR / (m.mein_tempo or 340.0)
                       if wo is not None and b is not None and b.pos is not None else None)
            mitspieler.append({"name": s.champion, "tot": bool(s.tot), "seite": _seite(ort),
                               "basis": _seite(ort) == "basis", "ankunft": ankunft})
    return {
        "champions": sorted({s.champion for s in p.spieler}) if p is not None else [],
        "gegner": [{"name": g.champion, "sichtbar": bool(g.sichtbar), "seit": g.seit, "tot": bool(g.s.tot),
                    "seite": _seite(g.ort)} for g in (b.gegner if b is not None else [])],
        "mitspieler": mitspieler,
        "jungler": j.champion if j is not None else None,
        "flash": b.flash if b is not None else None, "tp": m.tp_in if m is not None else None,
        "ult": b.ult if b is not None else None, "vorn": kern.vorn(),
        "gold": int(b.gold or 0) if b is not None else None,
        "items": list(p.ich.items) if p is not None and p.ich is not None else [],
        "ich_basis": bool(m is not None and m.bereich == "basis_eigen"),
        "objectives": [{"schl": o.schl, "lebt": bool(o.lebt), "spawn_in": o.spawn_in}
                       for o in (m.objectives or [] if m is not None else [])],
        # Auftrag 016, 4.2: der Combo-Check des Kerns und das Leben der sichtbaren Gegner (Balken im Bild)
        "kill": kill_jetzt(b) if b is not None else [],
        # Auftrag 017, 0.6: Wellen, an denen Mitspieler stehen (nach der Lane-Phase nicht dein Ziel)
        "besetzt": _besetzt(m), "lane_phase": bool(m is not None and m.lane_phase),
        "gegner_leben": {g.champion: round(g.leben, 2) for g in (b.gegner if b is not None else [])
                         if g.sichtbar and g.leben is not None},
        # Auftrag 024, 3: ist der Lane-Gegner wirklich weg? (kern/ereignisquellen.anwesenheit)
        "lane_gegner": _lane_gegner(b),
        # Auftrag 024, 5.5: reicht das Gold fuer ein Item (dann ist Back die Voreinstellung)?
        "kauf_bereit": bool(b is not None and getattr(b, "kauf", None) is not None and b.kauf.kaufen),
        # Auftrag 027, 3 (091311 20:17-21:19 "dein Team startet den Baron", es kaempfte am Drachen): wie viele
        # Mitspieler stehen laut Minimap an jeder Grube - und von wie vielen kennen wir den Ort
        "team_am": _team_am_mit_gedaechtnis(kern, b, m.zeit if m is not None else None),
    }


def _team_am_mit_gedaechtnis(kern, b, zeit) -> dict | None:
    """Im Tod liest der Coach die Minimap nicht (091311 21:00-21:19: keine Mitspieler) - dann gilt das letzte Bild
    mit Mitspielern, hoechstens 30 s alt."""
    ta = _team_am(b)
    if zeit is None:
        return ta
    if ta is not None and ta["bekannt"] >= 2:
        kern._team_am_letzt = (zeit, ta)
        return ta
    alt = getattr(kern, "_team_am_letzt", None)
    return alt[1] if alt is not None and 0 <= zeit - alt[0] <= 30.0 else ta


TEAM_NAH_GRUBE = 3000.0


def _team_am(b) -> dict | None:
    from .bewertung import GRUBEN, abstand, einheiten
    if b is None:
        return None
    orte = [wo for s, wo, *_ in b.mitspieler if wo is not None and not getattr(s, "tot", False)]
    am = {g: sum(1 for wo in orte if abstand(wo, einheiten(*GRUBEN[g])) <= TEAM_NAH_GRUBE)
          for g in ("drache", "baron")}
    return {"bekannt": len(orte), **am}


# "dein Team startet den Baron", "Jetzt, wo dein Team den Baron startet", "euer Team ist am Drachen"
TEAM_OBJ = _re.compile(r"\b(?:dein|euer)\s+team\b(?P<mitte>[^.;:!?]{0,30}?)\b(?P<obj>baron|drache\w*|herold|larven)\b"
                       r"(?P<nach>[^.;:!?,]{0,15})", _re.I)
TEAM_OBJ_TUT = _re.compile(r"start|mach|nimmt|nehm|hol|\bist\b|\bsteh|kämpf|beginn|\bam\b|\bbeim\b|schlag|\bhau", _re.I)


# Auftrag 024, 5.5 (231200 7:10 "Ja, Freeze am Turm statt Reset", 7:23 "Udyr steht oben im Fluss" auf "Wieso? Ich habe
# 1500 Gold"): "kein Back" nur mit Grund - reicht das Gold fuer ein Item, ist Back die Voreinstellung
KEIN_BACK = _re.compile(r"\b(kein(en)? (back|reset|recall)|nicht (back|resetten|recallen)|noch nicht back|"
                        r"statt (back|reset|recall|zu resetten)|back später|später back)\b", _re.I)
GRUND = _re.compile(r"\b(weil|denn|sonst|da |bis|damit|solange)\b|:", _re.I)


def _lane_gegner(b) -> dict | None:
    if b is None or getattr(b, "lane", None) is None:
        return None
    from .kern.ereignisquellen import anwesenheit
    return {"name": b.lane.champion, "anwesend": anwesenheit(b)}


# Auftrag 024, 2 (231200 2:57 "Jetzt, wo Xerath tot ist", 7:56 "Gragas tot": beide lebten laut API)
TOT_WORT = r"(?:tot|gestorben|down)\b"
NICHT_TOT = ("fast", "beinahe", "halb", "gleich", "bald", "nicht", "kaum")      # "Zyra fast tot" heisst: wenig Leben
LEBT_WORT = r"(?:lebt(?! in\b)|ist wieder da|ist zurück)\b"
# Auftrag 024, 3 (231200 5:56 "Udyr ist weg": er stand ungesehen auf seiner Lane)
WEG_WORT = r"(?:ist |bleibt )?(?:weg|fehlt|verschwunden|nicht auf (?:seiner|der) Lane)\b"


def fakten(s: str, lage: dict) -> list[str]:
    """Auftrag 024, 2-3: nennt der Satz einen Lebenden tot, einen Toten lebend oder den Lane-Gegner weg, obwohl er da
    ist? Gemessen an der Lage zur Pruefzeit (vor dem Sprechen noch einmal: `stratege_live._noch_sicher`)."""
    gruende = []
    alle = [(g["name"], bool(g.get("tot"))) for g in (lage.get("gegner") or [])] + \
        [(g["name"], bool(g.get("tot"))) for g in (lage.get("mitspieler") or [])]
    for name, ist_tot in alle:
        for m in _re.finditer(rf"\b{_re.escape(name)}\b", s):
            if _re.search(r"\b(wenn|falls|sobald|bevor|bis)\b[^.,:;]*$", s[max(0, m.start() - 25):m.start()], _re.I):
                continue                                 # "wenn Udyr stirbt", "bis Xerath tot ist": Bedingung
            rest = s[m.end():m.end() + 30]
            t = _re.match(rf"\s+(?:(?:ist|sind|war)\s+)?(?:(\w+)\s+)?{TOT_WORT}", rest, _re.I)
            if t and not ist_tot and (t.group(1) or "").lower() not in NICHT_TOT:
                gruende.append(f"{name} lebt (API), der Satz nennt ihn tot")
                break
            if ist_tot and _re.match(rf"\s+{LEBT_WORT}", rest, _re.I):
                gruende.append(f"{name} ist tot (API), der Satz nennt ihn lebend")
                break
    lg = lage.get("lane_gegner") or {}
    if lg.get("anwesend") in ("da", "vermutlich da") and \
            _re.search(rf"\b{_re.escape(lg['name'])}\b\s+{WEG_WORT}", s, _re.I):
        gruende.append(f"{lg['name']} ist nicht weg ({lg['anwesend']})")
    # Auftrag 027, 3: "dein Team startet den Baron" nur, wenn die Minimap Mitspieler dort zeigt
    ta = lage.get("team_am") or {}
    if ta.get("bekannt", 0) >= 2:
        for m_ in TEAM_OBJ.finditer(s):
            if not TEAM_OBJ_TUT.search(m_.group("mitte") + " " + m_.group("nach")):
                continue
            if _re.search(r"\b(wenn|falls|sobald|bevor|bis|ob)\b", s[max(0, m_.start() - 25):m_.start()], _re.I):
                continue
            grube = "drache" if m_.group("obj").lower().startswith("drache") else "baron"
            if ta.get(grube, 0) == 0:
                gruende.append(f"kein Mitspieler an der Grube ({grube}, Minimap: {ta['bekannt']} gesehen, "
                               f"{ta.get('drache', 0)} am Drachen, {ta.get('baron', 0)} am Baron)")
                break
    return gruende


# --- Auftrag 015: Pruefungen aus den Sachfehlern der Probe 014 ---------------------------------------------------------

LAENGE_HOECHSTENS = 30
ORT_WORT = {"oben": r"oben|top", "unten": r"unten|bot", "mitte": r"in der mitte|mid", "basis": r"basis|base"}
# eine Namensliste: "Sett", "Master Yi", "Sett und Kai'Sa", "Cassio, Yi und Pantheon" (nur grosse Woerter)
NAMEN = r"(?P<namen>[A-ZÄÖÜ][\w'’.]*(?: [A-ZÄÖÜ][\w'’.]*)?(?:(?:, | und | oder )[A-ZÄÖÜ][\w'’.]*(?: [A-ZÄÖÜ][\w'’.]*)?)*)"
BEGLEITER = _re.compile(r"\bmit " + NAMEN)
TREFFEN = _re.compile(r"\bzu (deinem team|euch|\w+)|sammel|gruppier|treff|warte auf|zusammen mit|\bgegen\b", _re.I)
STEHT = _re.compile(NAMEN + r" (steht|stehen|ist|sind|läuft|laufen|wartet|warten|kommt|kommen) (gerade |jetzt |schon |"
                    r"noch |eh |direkt |bereits )?(?P<ort>oben|unten|mid\b|in der mitte|top\b|bot\b|in (eurer|der|ihrer|"
                    r"seiner) (basis|base)|bei dir|im|in|am|an)\b")
UNSICHTBAR = _re.compile(NAMEN + r" ((ist|sind|bleibt|bleiben) )?((gerade|grad|noch|jetzt|beide|alle|eh) )?"
                         r"(unsichtbar|nicht zu sehen|nicht sichtbar|verschwunden)|" + NAMEN.replace("namen", "namen2")
                         + r" (sehe?|seh) ich (\w+ )?nicht")
VIELLEICHT = _re.compile(r"zuletzt|\bwar\b|waren|vor \d+|vermutlich|wahrscheinlich|könnte|kann|vielleicht|unbekannt",
                         _re.I)
OBJ_ZIEL = _re.compile(r"\b(zum|zur|richtung|nimm|hol|mach|erzwing\w*|auf den|an den|bestreit\w*|start\w*|geht|geh)\b",
                       _re.I)
OBJ_ZEIT = _re.compile(r"in \d+|spawnt|kommt in|erst in|minute|sekunden|\d+:\d\d|um \d", _re.I)
OBJ_NEIN = _re.compile(r"nicht (richtung|zum|zur|auf|an|zu)|statt|kein(en)? (drachen|baron|herold)", _re.I)
OBJ_FAKT = _re.compile(r"genommen|geholt|ist weg|ist tot|haben den|habt den|vorbei|gefallen", _re.I)
KAUF_WORT = _re.compile(r"kauf|hol dir|zuerst|fertig|besorg", _re.I)
KAUF_SPAETER = _re.compile(r"beim nächsten back|später|nächstes mal", _re.I)
_ITEMS: dict | None = None


def kuerzen(text: str, woerter: int = LAENGE_HOECHSTENS) -> str:
    """Auftrag 015, 6: ueber `woerter` Woerter wird auf ganze Saetze gekuerzt (der erste bleibt immer)."""
    aus, n = [], 0
    for s in _saetze(text):
        w = len(s.split())
        if aus and n + w > woerter:
            break
        aus.append(s)
        n += w
    return " ".join(aus)


VERKAUF = _re.compile(r"\bverkauf\w*\s+([^,.;:]+?)(?=\s*(?:[,.;:]|\bund\b|\bdann\b|$))", _re.I)


def _items() -> dict:
    """Name -> (Preis gesamt, Grundpreis, Bauteile) der kaufbaren Items auf der Kluft."""
    global _ITEMS
    if _ITEMS is None:
        _ITEMS = {}
        try:
            from . import ddragon
            alle = ddragon.items()
            for i, v in alle.items():
                g = v.get("gold", {})
                if not g.get("purchasable") or not v.get("maps", {}).get("11") or v.get("requiredChampion"):
                    continue
                if v["name"] not in _ITEMS or int(i) < _ITEMS[v["name"]][3]:
                    _ITEMS[v["name"]] = (g.get("total", 0), g.get("base", 0), [int(x) for x in v.get("from", [])],
                                         int(i))
            _ITEMS["_id"] = {int(i): v for i, v in alle.items()}
        except Exception:
            _ITEMS = {}
    return _ITEMS


def _restpreis(item_id: int, besitz: list[int]) -> int:
    """Was ein Item noch kostet, wenn Bauteile schon im Inventar liegen (rekursiv)."""
    alle = _items().get("_id", {})
    if item_id in besitz:
        besitz.remove(item_id)
        return 0
    v = alle.get(item_id, {})
    g = v.get("gold", {})
    return g.get("base", 0) + sum(_restpreis(int(c), besitz) for c in v.get("from", []))


def _namen_in(text: str, namen: list[str]) -> list[str]:
    """Die Champions, die in `text` stehen - auch kurz ("Yi" fuer Master Yi, "Cassio" fuer Cassiopeia)."""
    woerter = _re.findall(r"[A-ZÄÖÜ][\w'’]*", text)
    aus = []
    for n in namen:
        teile = n.split()
        if any(w in teile or (len(w) >= 4 and n.lower().startswith(w.lower())) for w in woerter):
            aus.append(n)
    return aus


def pruefe_015(s: str, lage: dict) -> list[str]:
    """Auftrag 015, 1: Mitspieler am falschen Ort, Gold, Sichtbarkeit falsch herum, Objective nicht da."""
    gruende = []
    mit = {x["name"]: x for x in lage.get("mitspieler") or []}
    gegner = {x["name"]: x for x in lage.get("gegner") or []}
    # 1. Mitspieler als Begleiter oder an einem Ort
    if not TREFFEN.search(s):
        for m in BEGLEITER.finditer(s):
            for n in _namen_in(m.group("namen"), list(mit)):
                x = mit[n]
                basis = x["basis"] and not lage.get("ich_basis")          # ihr steht beide in der Basis: ok
                if x["tot"] or basis or (x["ankunft"] is not None and x["ankunft"] > 15.0):
                    wo = "tot" if x["tot"] else "in der Basis" if x["basis"] else f"{int(x['ankunft'])} s weg"
                    gruende.append(f"Mitspieler nicht dabei ({n}: {wo})")
    for m in STEHT.finditer(s):
        ort = m.group("ort").lower()
        for n in _namen_in(m.group("namen"), list(mit)):
            x = mit[n]
            if x["tot"]:
                gruende.append(f"Mitspieler tot ({n})")
                continue
            if ort == "bei dir":
                if x["ankunft"] is not None and x["ankunft"] > 15.0:
                    gruende.append(f"Mitspieler nicht bei dir ({n}: {int(x['ankunft'])} s weg)")
                continue
            gesagt = next((k for k, r in ORT_WORT.items() if _re.fullmatch(r, ort) or _re.search(r, ort)), None)
            if gesagt and x["seite"] and gesagt != x["seite"]:
                gruende.append(f"Mitspieler woanders ({n}: {x['seite']}, nicht {gesagt})")
    # 3. Sichtbarkeit falsch herum
    for m in UNSICHTBAR.finditer(s):
        for n in _namen_in(m.group("namen") or m.group("namen2") or "", list(gegner)):
            if gegner[n]["sichtbar"]:
                gruende.append(f"Gegner ist sichtbar ({n})")
    for m in STEHT.finditer(s):
        for n in _namen_in(m.group("namen"), list(gegner)):
            x = gegner[n]
            if not x["sichtbar"] and not x["tot"] and (x["seit"] is None or x["seit"] > 10) \
                    and not VIELLEICHT.search(s[max(0, m.start() - 20):m.end() + 25]):
                gruende.append(f"Ort als aktuell für einen Unsichtbaren ({n})")
    # 4. Objective nicht da
    for o in lage.get("objectives") or []:
        muster = OBJ_WORT.get(o["schl"])
        if not muster or o["lebt"]:
            continue
        if _re.search(muster, s, _re.I) and (OBJ_ZIEL.search(s) or _re.search(r"\berst\b|\bwenn\b", s, _re.I)) \
                and not OBJ_ZEIT.search(s) and not OBJ_FAKT.search(s) and not OBJ_NEIN.search(s):
            gruende.append(f"Objective nicht da ({o['schl']})")
    # 2. Gold
    gold = lage.get("gold")
    if gold is not None and KAUF_WORT.search(s) and not KAUF_SPAETER.search(s):
        items = _items()
        # Auftrag 018, 2 (183125 18:36): "Verkauf Dorans Klinge, kauf Sonnenköcher" - der Verkauf ist kein Kauf, er
        # macht einen Platz frei und bringt Gold
        besitz_ids = [int(i) for i in lage.get("items") or []]
        for v in VERKAUF.finditer(s):
            n = next((n for n in sorted(items, key=len, reverse=True) if n != "_id" and n in v.group(1)), None)
            if n is not None and items[n][3] in besitz_ids:
                besitz_ids.remove(items[n][3])
                gold += int(items["_id"].get(items[n][3], {}).get("gold", {}).get("sell", 0))
        s = VERKAUF.sub(" ", s)
        rest = _re.sub(r"für ((die|den|das|deine|deinen|dein|eine|einen) )?[\wÄÖÜäöüß' -]+", " ", s)
        # auch kurz gesagt (Kritik 016, 192113 9:42: "Kriegshammer + Spitzhacke" bei 1060 Gold)
        kurz = {n.split()[-1]: n for n in items if n != "_id" and " " in n and len(n.split()[-1]) >= 6}
        for k, n in kurz.items():
            # Auftrag 018 (183125 26:02): "Klinge der Unendlichkeit" ist keine Kurzform von "Dorans Klinge" - nur
            # ersetzen, wenn kein voller Name mit diesem Wort dasteht
            if n not in rest and _re.search(rf"(?<!\w){_re.escape(k)}(?!\w)", rest) and not any(
                    v != "_id" and v in rest and _re.search(rf"(?<!\w){_re.escape(k)}(?!\w)", v) for v in items):
                rest = _re.sub(rf"(?<!\w){_re.escape(k)}(?!\w)", n, rest)
        namen = sorted((n for n in items if n != "_id" and _re.search(rf"(?<!\w){_re.escape(n)}(?!\w)", rest)),
                       key=len, reverse=True)
        genannt, preis, besitz = [], 0, list(besitz_ids)
        for n in namen:
            if any(n in g for g in genannt):
                continue
            genannt.append(n)
            preis += _restpreis(items[n][3], besitz)
        if genannt and preis > gold:
            gruende.append(f"Gold reicht nicht ({' + '.join(genannt)} = {preis}, du hast {gold})")
        try:                                               # Auftrag 018, 4: einzigartige Gruppen (Spieldaten)
            from .kaufplan import konflikt
            for n in genannt:
                if (j := konflikt(items[n][3], besitz_ids)) is not None:
                    alt = items["_id"].get(j, {}).get("name", str(j))
                    gruende.append(f"{n} geht nicht zusammen mit {alt} (einzigartig)")
        except Exception:
            pass
        if genannt:
            # Auftrag 016, 5 (133448 13:27: "kauf Auge, Hammer und Spitzhacke" - dann war fuer das Langschwert kein Platz)
            try:
                from . import kaufplan
                frei = kaufplan.plaetze_nach(besitz_ids, genannt)
            except Exception:
                frei = 0
            if frei < 0:
                gruende.append(f"kein Platz ({' + '.join(genannt)}: {-frei} Platz zu wenig)")
    return gruende


# --- Auftrag 016: Sicherheit, die in 133448 durchrutschte, und Ketten ----------------------------------------------------

# 4.1 (12:10, 5 % Leben, Lux und Sona voll daneben: "Schieb kurz die Top-Welle rein"): unter R1 ist jede Welle nach
# vorn, die man zum Gegner schiebt; erlaubt bleibt nur, sie auf der eigenen Seite zu holen oder zu farmen
WELLE_VOR = _re.compile(
    r"\b(schieb\w*|drück\w*|push\w*|crash\w*|stapel\w*|shove\w*)\b[^.;:]{0,30}?\bwellen?\b[^.;:]{0,15}|"
    r"\bwellen?\b[^.;:]{0,25}?\b(rein|reinschieben|reindrücken|rüber\w*|crashen|pushen|drücken|stapeln|schieben)\b|"
    r"\b(slow|fast) ?push\w*|such (dir )?(ein(en)? |das |den )?(1 ?(gegen|v|vs) ?1|duell)", _re.I)
# 4.2 (9:29: "Poppy ist sichtbar und schwach ... geh sie jetzt an" bei vollem Leben)
ANGRIFF = _re.compile(
    r"\bgeh\w* (?!zurück|zum|zur|nach|mit|in|auf|unter|an\b)(\w+ ){1,2}an\b(?! (den|die|das|dein\w*|ihr\w*|der|euren?)\b)|"
    r"\bgreif\w* (\w+ ){0,2}an\b|\bangreif\w*|\banzugreifen|\btrad(e|en|est|et)\b|\ball[- ]?in\b|hol dir den kill|"
    r"\bkill (ihn|sie)\b|\btöte\w*|\bfight\b|\bspiel (\w+ ){0,2}aggressiv|"
    # Kritik 016 (Nachspiel 133448 9:47 "Rein auf Poppy!", 192113 25:21 "Nimm den Kampf"): die Kampf-Rufe des Kerns
    r"\brein auf\b|\bnimm den kampf\b|\bkampf (an)?nehmen\b|\bdreh (dich )?um\b", _re.I)
BEDINGT = _re.compile(r"\b(nicht|kein\w*|nie|erst|wenn|sobald|falls|statt|ohne|vergiss|lass)\b", _re.I)
SCHWACH = _re.compile(r"\b(schwach|low|angeschlagen|fast tot|halb tot|wenig leben)\b", _re.I)
# 2: ein Back-Ruf nennt im selben Satz Kauf und Ziel
BACK_WORT = _re.compile(r"\b(back|recall|zurück in die basis|zurück in deine basis|heim)\b", _re.I)
BACK_NICHT = _re.compile(r"\b(nach dem|beim|vor dem|nächsten|letzten|ohne|kein\w*|nicht|zum|vom|erst nach)\W+(\w+\W+)?$",
                         _re.I)
KETTE_KAUF = _re.compile(r"\bkauf\w*|\bhol dir\b|\bnimm (\w+ ){0,3}mit\b|nichts zu kaufen|\bheil\w*", _re.I)
KETTE_ZIEL = _re.compile(r"\b(dann|danach|anschließend|und zurück)\b[^.]{0,70}?\b(zu|zur|zum|nach|in die|auf die|an die|"
                         r"an den|richtung|top|mid|bot|oben|unten|mitte|welle|lane|turm|drache\w*|herold|baron|larven|"
                         r"gruppe|fluss|jungle|team)\b", _re.I)
# 5: Kontroll-Auge
AUGE = _re.compile(r"kontroll-?auge|\bauge\b", _re.I)
AUGE_BACK = _re.compile(r"\b(back|recall|zurück)\b\W+(\w+\W+){0,6}?(nur )?(für|wegen|um) (das |ein |dein |ein paar )?"
                        r"(kontroll-?)?auge", _re.I)
# Auftrag 023, 3 (164809 23:09 "Nein, nicht Top jetzt"): ein nacktes Nein auf einen Anlass ist kein Plan - der Kern
# sprach 15 s spaeter "Danach zur Top-Welle", weil kein Ziel gesetzt war. Als Antwort auf eine Frage bleibt es erlaubt.
NUR_NEIN = _re.compile(r"^\W*nein\b\W+(\w+\W*){0,5}$", _re.I)
AUGE_NEIN = _re.compile(r"\b(nein|kein\w*|ohne|scheiß|verfickt\w*)\b[^.?!]{0,40}(kontroll-?)?auge|"
                        r"(kontroll-?)?auge[^.?!]{0,20}\b(nein|brauch ich nicht|will ich nicht)\b", _re.I)
_ITEM_RE: _re.Pattern | None = None
# --- Auftrag 017, Teil 0 -------------------------------------------------------------------------------------------
WELLE_ZIEL = _re.compile(r"\b(zur|nach|auf die|an die|zu deiner|farm (die|deine)|hol (die|deine)|zurück zur)\s+"
                         r"(?P<lane>top|mid|bot)(-welle|-lane| welle| lane)?\b", _re.I)
KAUF_JETZT = _re.compile(r"^\W*(kauf|kaufe|hol dir)\b|\bkauf (jetzt|sofort|gleich)\b|\bjetzt (den|die|das|ein|eine|einen) "
                         r"[\w-]+ kaufen\b", _re.I)
KAUF_SPAETER_017 = _re.compile(r"\b(beim|nach dem|im|vor dem) (nächsten )?(back|recall)|\bspäter\b|\bdanach\b|\bdann\b|"
                               r"\bin der basis\b|\bsobald\b", _re.I)
ABWAHL = _re.compile(r"\b(vergiss|lass|spar dir|kein(en)?|statt)\b", _re.I)
SCHWACH_FOLGE = _re.compile(r"\b(geh|greif|drück|zieh|nutz|trade|rein|farm|bleib|zwing|push|crash|halt|freeze|nimm|"
                            r"spiel|such|warte|back|zurück|lauf)\w*\b|:\s*\w", _re.I)
_FUELL: list | None = None


def fuellsaetze() -> list[_re.Pattern]:
    """Die Fuellsatz-Muster aus wissen/fuellsaetze.toml (erweiterbar) - ein Satz, der ganz auf eins passt, hat keine
    neue Info und keine Entscheidung (Auftrag 017, 0.3; Buch 13, Teil 3)."""
    global _FUELL
    if _FUELL is None:
        try:
            import tomllib
            from pathlib import Path
            d = tomllib.loads((Path(__file__).resolve().parent.parent / "wissen" / "fuellsaetze.toml")
                              .read_text(encoding="utf-8"))
            _FUELL = [_re.compile(x, _re.I) for x in d.get("muster", [])]
        except Exception:
            _FUELL = []
    return _FUELL


def fuellsatz(s: str) -> str | None:
    t = s.strip()
    for m in fuellsaetze():
        if m.search(t):
            return m.pattern
    return None


def pruefe_017(s: str, lage: dict) -> list[str]:
    """Auftrag 017, Teil 0: Fuellsaetze (3), "Kauf jetzt" nur in der Basis oder im Back-Ruf, nichts ueber schon
    Gekauftes (5), "schwach" nur mit Folge (7)."""
    gruende = []
    if fuellsatz(s):
        gruende.append("Füllsatz (keine neue Info, keine Entscheidung)")
    if KAUF_JETZT.search(s) and not lage.get("ich_basis") and not back_ruf(s) and not KAUF_SPAETER_017.search(s):
        gruende.append("Kauf jetzt nur in der Basis oder im Back-Ruf")
    besitz = [i for i in lage.get("items") or []]
    if besitz and (KAUF_WORT.search(s) or ABWAHL.search(s)):
        alle = _items().get("_id", {})
        fertig = {alle[i]["name"] for i in besitz if i in alle and not alle[i].get("into")
                  and alle[i].get("gold", {}).get("total", 0) >= 900}
        for n in fertig:
            kurz = n.split()[-1]
            if _re.search(rf"(?<!\w){_re.escape(n)}(?!\w)", s) or (len(kurz) >= 6 and _re.search(
                    rf"(?<!\w){_re.escape(kurz)}(?!\w)", s)):
                gruende.append(f"{n} hast du schon")
                break
    if SCHWACH.search(s) and not SCHWACH_FOLGE.search(s):
        gruende.append("„schwach“ ohne Folge")
    return gruende


def _item_re() -> _re.Pattern:
    global _ITEM_RE
    if _ITEM_RE is None:
        namen = {n for n in _items() if n != "_id" and len(n) >= 4}
        # auch kurz gesagt: "Kriegshammer" fuer Caulfields Kriegshammer, "Hydra" fuer die Gefraessige Hydra
        namen |= {n.split()[-1] for n in list(namen) if " " in n and len(n.split()[-1]) >= 5}
        namen = sorted(namen, key=len, reverse=True)
        _ITEM_RE = _re.compile("|".join(rf"(?<!\w){_re.escape(n)}(?!\w)" for n in namen) or r"(?!x)x")
    return _ITEM_RE


def back_ruf(s: str) -> bool:
    """Ruft der Satz jetzt zum Back ("Back jetzt", "geh back", "Recall") - nicht "nach dem Back", "beim naechsten"."""
    return any(not BACK_NICHT.search(s[:m.start()]) for m in BACK_WORT.finditer(s))


def kette(s: str) -> bool:
    """Auftrag 016, 2: der Satz nennt einen Kauf (Item oder "kauf") und ein Ziel danach ("dann zu Yorick nach Mid")."""
    return bool((KETTE_KAUF.search(s) or _item_re().search(s)) and KETTE_ZIEL.search(s))


def kill_jetzt(b) -> list[str]:
    """Der Combo-Check des Kerns fuer den Strategen: die sichtbaren Gegner, die dein voller Combo JETZT toetet (wie
    denker._combo, mit 10 % Reserve)."""
    from . import combo, rechnung
    aus = []
    if b is None or getattr(b, "partie", None) is None or b.ich is None or not combo.kann(b.ich.champion_id):
        return aus
    for g in b.gegner:
        if g.s.tot or not g.sichtbar or g.leben is None:
            continue
        try:
            dmg = combo.schaden(b.ich, b.partie.werte, b.partie.raenge, b.bereit, g.s, g.leben)
        except Exception:
            dmg = None
        if dmg and dmg >= 1.1 * g.leben * rechnung.max_leben(g.s):
            aus.append(g.champion)
    return aus


def sicherheit(s: str, lage: dict) -> list[str]:
    """Die harten Gruende (Auftrag 016, 6.4) fuer einen Satz - fuer Stratege UND Kern gemessen: nach vorn unter R1
    (auch eine Welle zum Gegner), Angriff ohne Kill-Check, "schwach" ohne Beleg, innere Begriffe."""
    gruende = []
    verboten = bool((lage.get("vorn") or {}).get("verboten"))
    if verboten and (w := _nach_vorn(s, r1=True)):
        gruende.append(f"nach vorn trotz R1 ({w})")
    kill = lage.get("kill") or []
    gleben = lage.get("gegner_leben") or {}
    feinde = list(gleben) + [g["name"] for g in lage.get("gegner") or [] if g["name"] not in gleben]
    for m in ANGRIFF.finditer(s):
        umfeld = s[max(0, m.start() - 25):m.end() + 30]
        if BEDINGT.search(umfeld):
            continue
        genannt = _namen_in(s, feinde)
        if verboten or not kill or (genannt and not set(genannt) & set(kill)):
            gruende.append(f"Angriff ohne Kill-Check ({m.group(0).strip()})")
        break
    for m in SCHWACH.finditer(s):
        if _re.search(r"\bnicht\s*$", s[:m.start()], _re.I):
            continue
        # nur der eigene Satzteil (Auftrag 021, 183125 14:27: "Jetzt, wo Garen oben gesehen wurde: Zyra fast tot"
        # meinte Zyra - der Vorsatz des Schiedsrichters hing Garen davor)
        fenster = s[max(0, m.start() - 40):m.start()].rsplit(":", 1)[-1]
        for n in _namen_in(fenster, feinde):
            le = gleben.get(n)
            if le is None or le >= 0.5:
                gruende.append(f"„schwach“ ohne Beleg ({n}: " + ("Leben unbekannt" if le is None else
                                                                   f"{int(round(le * 100))} %") + ")")
    if (m := INNERE.search(s)):
        gruende.append(f"innerer Begriff ({m.group(0)})")
    return gruende


def _saetze(text: str) -> list[str]:
    return [s for s in _re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def _nach_vorn(satz: str, r1: bool = False) -> str | None:
    """Die erste Vorwaerts-Handlung im Satz, die weder verneint noch auf spaeter verschoben ist. `r1`: unter R1 ist
    auch jede Welle nach vorn, die man zum Gegner schiebt (Auftrag 016, 4.1) - "Welle rein" gilt dann nicht mehr."""
    if r1:
        for m in WELLE_VOR.finditer(satz):
            vor = satz[:m.start()]
            if _re.search(r"\b(nicht|kein\w*|nie|vergiss|statt)\b", m.group(0), _re.I) \
                    or VOR_AUFGESCHOBEN.search(vor) or (VOR_DANACH.search(vor) and ERHOLUNG.search(vor)):
                continue
            return m.group(0)
    for m in VORWAERTS.finditer(satz):
        vor, nach = satz[:m.start()], satz[m.end():]
        welle_rein = not r1 and m.group(0).lower().startswith("rein") and _re.search(r"welle\W*$", vor, _re.I)
        spaeter = VOR_DANACH.search(vor) and ERHOLUNG.search(vor)
        if welle_rein or spaeter or VOR_AUFGESCHOBEN.search(vor) or VOR_VERNEINT_DANACH.search(nach):
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
        gruende += sicherheit(s, lage)
        for o in vorn.get("ziele") or []:
            muster = OBJ_WORT.get(o)
            if muster and _re.search(muster, s, _re.I) and (w := _nach_vorn(s)) is not None:
                gruende.append(f"zu riskantes Ziel ({o}: {w})")
        if back_ruf(s) and not kette(s):
            gruende.append("Back ohne Kette (Kauf und Ziel im selben Satz)")        # Auftrag 016, 2
        if back_ruf(s) and lage.get("ich_basis") and not _re.search(r"nächst|später|danach|dann back", s, _re.I):
            gruende.append("Back, obwohl du in der Basis bist")                     # Kritik 016 (133448 7:15)
        if not lage.get("lane_phase") and lage.get("besetzt"):
            for m_ in WELLE_ZIEL.finditer(s):
                lane = m_.group("lane").capitalize()
                if lane in lage["besetzt"] and not _re.search(r"\bnicht\b", s[:m_.start()][-20:], _re.I):
                    gruende.append(f"an der {lane}-Welle stehen schon {', '.join(lage['besetzt'][lane])}")
                    break
        gruende += pruefe_017(s, lage)
        gruende += fakten(s, lage)                                                  # Auftrag 024, 2-3
        if lage.get("kauf_bereit") and (m_ := KEIN_BACK.search(s)) and not GRUND.search(s[m_.end():]) \
                and not GRUND.search(s[:m_.start()]):
            gruende.append("kein Back ohne Grund - mit Gold für ein Item ist Back richtig")   # Auftrag 024, 5.5
        if lage.get("anlass") and NUR_NEIN.match(s):
            gruende.append("nur ein Nein - sag, was stattdessen")                    # Auftrag 023, 3
        if AUGE_BACK.search(s):
            gruende.append("Back nur für ein Kontroll-Auge")                         # Auftrag 016, 5
        elif lage.get("auge") and AUGE.search(s) and _re.search(r"kauf|hol|nimm|mit|plus|dazu|und", s, _re.I) \
                and not _re.search(r"ohne (\w+ )?auge|kein(e|en)? (\w+ )?auge", s, _re.I):
            gruende.append(f"Kontroll-Auge ({lage['auge']})")
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
        # "Dein Flash ist weg" ist eine Tatsache, kein Rat, ihn zu benutzen (Nachspiel 133448, Auftrag 017: 5 Fehlalarme)
        if FLASH_EIGEN.search(s) and lage.get("flash") is not None and lage["flash"] > 0 \
                and not _re.search(r"dein(en)? flash (ist )?(noch )?(weg|nicht|down|fehlt|in \d+|kommt|erst)|"
                                   r"ohne (deinen )?flash|flash (ist )?weg", s, _re.I):
            gruende.append("dein Flash ist nicht bereit")
        if ULT_EIGEN.search(s) and lage.get("ult") is False:
            gruende.append("deine Ult ist nicht bereit")
    for s in _saetze(satz):
        gruende += pruefe_015(s, lage)
    im_spiel = set(lage.get("champions") or [])
    for n in _alle_champions():
        if n not in im_spiel and _re.search(rf"(?<!\w){_re.escape(n)}(?!\w)", satz):
            gruende.append(f"Champion nicht in der Partie ({n})")
    return list(dict.fromkeys(gruende))
