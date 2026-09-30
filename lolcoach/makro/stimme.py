"""Claude spricht nur noch (Stufe 4, Auftrag 034, Punkt 3).

Der Entscheider (makro/takt.py) legt fest, WAS gesagt wird. Claude bekommt Kommando, Grund und naechsten Schritt als
Fakten und formt daraus EINEN gesprochenen Satz. Er erfindet keine Aktion: weicht sein Satz vom Kommando ab
(`abweichung`), faellt er aus oder ist er zu langsam (`frist_s`), spricht die Vorlage. Der Coach schweigt nie deswegen.

    st = Stimme(frage=llm.frage, frist_s=2.0)
    auftrag = st.formen(anweisung, namen={"Aatrox", ...})     # sofort zurueck, Claude laeuft im Hintergrund
    ...
    text, quelle = auftrag.ergebnis()        # (Satz, "claude" | "vorlage:<grund>") - blockiert nie
"""
from __future__ import annotations

import re
import threading
import time

SYSTEM = (
    "Du bist die Stimme eines League-of-Legends-Coaches und sitzt neben dem Spieler, der gerade spielt. Du bekommst "
    "eine fertige Anweisung als Fakten: TU (die Handlung), WEIL (der Grund), DANACH (der naechste Schritt). Forme "
    "daraus EINEN kurzen gesprochenen deutschen Satz, hoechstens 14 Woerter, Handlung zuerst. Erfinde nichts: keine "
    "andere oder zusaetzliche Handlung, kein anderes Ziel, keine Namen, Zahlen oder Zeiten, die nicht in den Fakten "
    "stehen. Keine Verneinung weglassen. Kein Markdown, keine Anfuehrungszeichen, keine Einleitung.")

HOECHSTENS_WOERTER = 14      # wie [sprechen] max_woerter (Auftrag 002 / 035: Szenario s23-plan-hoechstens-14)
STOPP = {"der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem", "einer", "und", "oder", "dann",
         "jetzt", "mit", "zu", "zum", "zur", "in", "im", "an", "am", "auf", "bis", "fuer", "für", "von", "vor", "nach",
         "ist", "sind", "du", "dich", "dir", "dein", "deine", "deinen", "deinem", "deiner", "ihr", "ihre", "ihren",
         "ihrem", "sie", "er", "es", "noch", "nur", "schon", "danach", "weil", "sonst", "hier", "dort", "wieder"}
# Handlungen, die Claude nicht dazuerfinden darf (Richtung, Kampf, Back, TP, Objective)
HANDLUNGEN = {
    "vor": re.compile(r"\b(drück\w*|druck\w*|push\w*|rein\b|geh (rein|drauf)|greif\w*|angreif\w*|all[- ]?in|"
                      r"invad\w*|dive\w*|kämpf\w*|kaempf\w*|kampf|töte\w*|toete\w*|kill\w*|split\w*|erzwing\w*)", re.I),
    "zurueck": re.compile(r"\b(zurück\w*|zurueck\w*|raus\b|rückzug|rueckzug|weg da|flieh\w*)", re.I),
    "back": re.compile(r"\b(back|recall\w*|basis|heim)\b", re.I),
    "tp": re.compile(r"\b(tp|teleport\w*)\b", re.I),
    "ward": re.compile(r"\b(ward\w*|trinket|linse|kontroll-?auge)\b", re.I),
    "objective": re.compile(r"\b(drache\w*|baron|herold|larven|elder|nexus|inhib\w*)\b", re.I),
    "warten": re.compile(r"\b(warte\w*|halt\w*|bleib\w*)\b", re.I),
}
NICHT = re.compile(r"\b(nicht|kein\w*|nie)\b", re.I)
ZAHL = re.compile(r"\d+")


def _woerter(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[\wÄÖÜäöüß'-]+", text)]


def abweichung(satz: str, vorlage: str, namen: set[str] = frozenset(), erlaubt: str | None = None) -> list[str]:
    """Warum `satz` nicht dasselbe sagt wie `vorlage` - leer heisst: treu. Geprueft wird hart, lieber die Vorlage
    als ein falscher Satz:
    - jede Zahl im Satz steht auch in der Vorlage;
    - kein Champion-Name, der nicht in der Vorlage steht;
    - keine Handlungsart (vor, zurueck, back, TP, Ward, Objective, warten), die die Vorlage nicht hat - und die
      Handlungsarten der Vorlage fehlen nicht;
    - Verneinung bleibt Verneinung;
    - die Inhaltswoerter der Handlung (TU) kommen vor (mindestens die Haelfte, gekuerzt auf 5 Buchstaben);
    - hoechstens HOECHSTENS_WOERTER Woerter.
    `erlaubt`: der ganze Satz (Grund, danach) - Zahlen, Namen und Handlungen daraus darf Claude nennen; die
    Handlungen der Vorlage muss er nennen."""
    g = []
    quelle = f"{vorlage} {erlaubt}" if erlaubt else vorlage
    if not satz or not satz.strip():
        return ["leer"]
    if len(satz.split()) > HOECHSTENS_WOERTER:
        g.append("zu lang")
    if extra := set(ZAHL.findall(satz)) - set(ZAHL.findall(quelle)):
        g.append(f"Zahl erfunden ({', '.join(sorted(extra))})")
    for n in namen:
        if re.search(rf"(?<!\w){re.escape(n)}(?!\w)", satz) and not re.search(rf"(?<!\w){re.escape(n)}(?!\w)", quelle):
            g.append(f"Name erfunden ({n})")
    for art, muster in HANDLUNGEN.items():
        im_satz, in_vorlage = bool(muster.search(satz)), bool(muster.search(vorlage))
        if im_satz and not muster.search(quelle):
            g.append(f"Handlung erfunden ({art})")
        elif in_vorlage and not im_satz and art != "warten":
            g.append(f"Handlung fehlt ({art})")
    if bool(NICHT.search(satz)) != bool(NICHT.search(vorlage)) and not (NICHT.search(satz) and erlaubt
                                                                     and NICHT.search(erlaubt)):
        g.append("Verneinung geaendert")
    return g


def tu_fehlt(satz: str, tu: str) -> bool:
    """Nennt der Satz die Handlung? Mindestens die Haelfte ihrer Inhaltswoerter (auf 5 Buchstaben gekuerzt)."""
    from .kommando import sprechbar
    kern = [w[:5] for w in _woerter(sprechbar(tu)) if w not in STOPP and len(w) >= 3]
    if not kern:
        return False
    im = {w[:5] for w in _woerter(satz)}
    return sum(w in im for w in kern) * 2 < len(kern)


def fakten(anw) -> str:
    """Die Fakten fuer Claude - nur, was der Entscheider festgelegt hat."""
    from .kommando import sprechbar
    k = anw.kommando
    z = [f"TU: {sprechbar(k.tu)}", f"WEIL: {sprechbar(k.weil)}"]
    if k.danach:
        z.append(f"DANACH: {sprechbar(k.danach)}")
    if anw.form == "geteilt" and anw.zweite is not None:
        z.append(f"ODER (gleich gut): {sprechbar(anw.zweite.tu)} - {sprechbar(anw.zweite.weil)}")
    z.append(f"VORLAGE (so waere es richtig): {anw.vorlage}")
    z.append(f"GANZ (nur zur Einordnung, nicht alles sagen): {anw.voll}")
    return "\n".join(z)


def strom_als_frage(strom):
    """Ein Strom-Weg (stratege_live.claude_strom / Zwischenspeicher: (prompt, bei_satz, system, timeout, modell=...))
    als `frage(prompt, system=, modell=, timeout=) -> str` fuer die Stimme (Nachspiel, Auftrag 035)."""
    def frage(prompt: str, system: str | None = None, modell: str = "schnell", timeout: float = 30.0, **_) -> str:
        teile: list[str] = []
        try:
            text = strom(prompt, teile.append, system, timeout, modell=modell)
        except TypeError:
            text = strom(prompt, teile.append, system, timeout)
        return text if isinstance(text, str) and text.strip() else " ".join(teile)
    return frage


class Auftrag:
    """Eine Formulierung im Hintergrund. `ergebnis()` blockiert nie."""

    def __init__(self, anw, vorlage: str, namen: set[str], frist_s: float, voll: str | None = None):
        self.anw = anw
        self.vorlage = vorlage
        self.voll = voll
        self.namen = set(namen)
        self.ende = time.monotonic() + frist_s
        self._fertig = threading.Event()
        self._text: str | None = None
        self._fehler: str | None = None
        self.direkt: str | None = None      # ohne Claude: "aus" (keine Stimme) oder "gefahr" (sofort)

    def _setzen(self, text: str | None, fehler: str | None = None) -> None:
        if not self._fertig.is_set():
            self._text, self._fehler = text, fehler
            self._fertig.set()

    @property
    def fertig(self) -> bool:
        """Claude hat geantwortet (oder ist ausgefallen) - oder die Frist ist um."""
        return self._fertig.is_set() or time.monotonic() >= self.ende

    def ergebnis(self) -> tuple[str, str]:
        if self.direkt is not None:
            return self.vorlage, f"vorlage:{self.direkt}"
        if not self._fertig.is_set():
            return self.vorlage, "vorlage:zu langsam"
        if self._fehler is not None:
            return self.vorlage, f"vorlage:ausfall ({self._fehler})"
        satz = (self._text or "").strip().strip('"„“').strip()
        satz = re.sub(r"\s+", " ", satz)
        g = abweichung(satz, self.vorlage, self.namen, self.voll)
        if tu_fehlt(satz, self.anw.kommando.tu):
            g.append("Handlung nicht genannt")
        if g:
            return self.vorlage, "vorlage:abweichung (" + "; ".join(g) + ")"
        return satz, "claude"


class Stimme:
    """Claude als Stimme. `frage(prompt, system=..., modell=..., timeout=...) -> str` (lolcoach.llm.frage oder ein
    Stub im Test). Ohne `frage` spricht immer die Vorlage. Gefahr formt Claude nie - sie muss sofort heraus."""

    def __init__(self, frage=None, frist_s: float = 2.0, modell: str = "schnell", synchron: bool = False):
        self.frage = frage
        self.frist_s = frist_s
        self.modell = modell
        # Nachspiel (035, Teil 3): auf Claude warten statt der Wanduhr-Frist - gemessen wird der Satz, nicht die Zeit
        self.synchron = synchron
        self.aufrufe = 0
        self.quellen: dict[str, int] = {}

    def formen(self, anw, namen: set[str] = frozenset()) -> Auftrag:
        a = Auftrag(anw, anw.vorlage, namen, self.frist_s, getattr(anw, "voll", None))
        if self.frage is None or anw.form == "gefahr":
            a.direkt = "aus" if self.frage is None else "gefahr"
            a._fertig.set()
            return a
        self.aufrufe += 1

        def lauf():
            try:
                text = self.frage(fakten(anw), system=SYSTEM, modell=self.modell, timeout=max(1.0, self.frist_s + 3))
                a._setzen(text)
            except Exception as e:           # Ausfall: die Vorlage spricht
                a._setzen(None, f"{type(e).__name__}")
        if self.synchron:
            lauf()
            a.ende = float("inf")
        else:
            threading.Thread(target=lauf, daemon=True, name="makro-stimme").start()
        return a

    def zaehlen(self, quelle: str) -> None:
        schl = quelle.split(" ", 1)[0]
        self.quellen[schl] = self.quellen.get(schl, 0) + 1
