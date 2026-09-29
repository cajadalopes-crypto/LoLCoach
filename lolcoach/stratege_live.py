"""Claude als Makro-Stratege im Live-Coach (Auftrag 015, Teil B aus 014).

Der Kern rechnet, warnt und liefert die Fakten; der Stratege (Claude ueber das Abo, `stratege.STRATEGE_SYSTEM`)
formuliert das Makro:
  B1  Fragen: jede echte Frage (JETZT, DANACH, WARUM, ENTWEDER, SOLL_ICH, RISIKO, AUGE, COACH, GEWISSHEIT, OFFEN)
      geht an den Strategen. Faktfragen (TIMER, WO, LAGE, KAUF), KLAEREN und Notizen bleiben beim Kern. Die Korrektur
      "die Welle ist leer" setzt der Kern vorher (Auftrag 012).
  B2  Wendepunkte (Kern-Satz WENDEPUNKT, Respawn, Ankunft in der Basis, zwei Kills in 10 s): der Stratege ersetzt den
      Plan-Satz des Kerns. Ist seine ganze Antwort nicht in `erster_satz_max_s` da, spricht der Kern.
  B3  Leerlauf nach der Lane-Phase: `leerlauf_s` ohne Plan-Satz und ohne Warnung - "Was jetzt?", NICHTS erlaubt.
  B4  Die Wellen-Saetze des Kerns (WELLE_DRUECKEN) nur noch, wenn der Stratege aus ist oder ausgefallen.
  B6  Jeder Aufruf mit allen Versuchen und verworfenen Saetzen samt Grund in `<aufnahme>_stratege.jsonl`.
Warnungen des Kerns gehen immer vor: der Sprechplan wirft in KAMPF und <= 10 s nach einer Gefahr nichts ein, und
Stratege-Saetze sind WICHTIG, nie SOFORT. Jeder Satz geht durch `stratege.pruefe`; verworfen wird einmal neu gefragt,
mit dem Grund, danach gilt der Kern.

Auftrag 016 (Carlos' Pflichtenheft aus 133448): Anlass "Kampf in der Naehe"; nach der Basis-Ankunft und bei jedem
Back die Kette im ersten Satz; ein Kontroll-Auge hoechstens einmal je Back, nach Carlos' Nein 5 min gar nicht.

Auftrag 017 (Inhalt statt Takt, Buch 13):
  - Die Antwort wird GANZ geprueft und als EIN Stueck gesprochen (vorher drei Ansagen ueber 8 s, 133448 1:32-1:40).
  - Latenz: kurzer Prompt (`kurzer_prompt`) mit dem Entwurf des Kerns (`mit_entwurf`) - ohne Entwurf denkt Claude
    4-7 s nach, mit ihm meist unter 1 s (stratege_probe_017/latenz_*.json); gesprochen wird beim Textende
    (message_stop), nicht erst beim Abschluss-Ereignis; ein Aufruf zur Zeit, Anlaesse waehrend eines Aufrufs verfallen.
  - Keine Fuellsaetze (wissen/fuellsaetze.toml); hat der Stratege nichts Neues, sagt er NICHTS und schweigt.
  - Lane-Phase: statt des 35-s-Takts Anlaesse mit Inhalt (Welle kippt, Kanone <= 20 s, Lane-Gegner weg/zurueck,
    Jungler gesehen, Flash weg, Spike kaufbar) - Frage "Freeze, Slow Push oder Crash, und warum?" mit
    wissen/wellen_regeln.md.
  - Ein aktiver Plan (`Schiedsrichter`): ein Plan-Satz (Kern oder Stratege) wird nur gesprochen, wenn er den Plan setzt
    oder aendert; innerhalb von 30 s nur nach einer echten Lageaenderung, dann beginnt er mit "Jetzt, wo ...".

Ausfall: kommt vom Abo `ausfall_s` lang nichts oder ein Fehler, macht der Coach still mit dem Kern weiter (einmal im
Protokoll), `pause_nach_ausfall_s` lang ohne Stratege. Schalter: [stratege] aktiv in wissen/kern.toml oder
`python -m lolcoach live --ohne-stratege`.
"""
from __future__ import annotations

import json
import re as _re
import threading
import time
from pathlib import Path

from . import stratege
from .regeln import WICHTIG, Ansage

STRATEGE_ABSICHTEN = frozenset(("JETZT", "DANACH", "WARUM", "ENTWEDER", "SOLL_ICH", "RISIKO", "AUGE", "COACH",
                                "GEWISSHEIT", "OFFEN"))
ANLASS_FENSTER_S = 5.0     # nach Respawn, Basis-Ankunft, Kills: so lange wartet der Stratege auf den Plan-Satz des Kerns
ANLASS_RUHE_S = 10.0       # ... kommt keiner, fragt er allein - nur, wenn so lange nichts Planendes gesagt wurde
PLAN_KATEGORIEN = ("PLAN", "WENDEPUNKT", "VORSCHAU", "FENSTER", "GEFAHR", "VORSICHT", "LAGEBILD", "TEAMPLAN")
NICHTS = _re.compile(r"^\W*nichts\W*$", _re.I)


def _cfg() -> dict:
    try:
        from . import wissen
        return dict(wissen.lade("kern").get("stratege", {}))
    except Exception:
        return {}


def kandidaten_text(kern) -> str:
    """Die Kandidaten des Kerns als Fakten (Wert, Todesrisiko, Grund; stumm markiert) - keine Vorgabe."""
    from .kern import fuehren
    zeilen = []
    for h in sorted(getattr(kern, "kandidaten_roh", None) or kern.kandidaten or [], key=lambda h: -h.ev)[:8]:
        marke = " [stumm: Modell nicht geeicht]" if fuehren.stumm(h) else ""
        zeilen.append(f"- {h.art}: {fuehren.kurz(h)} (Wert {h.ev:+.0f}, Todesrisiko {h.p_tod:.2f}"
                      f"{', Grund: ' + h.grund if h.grund else ''}){marke}")
    return "\n".join(zeilen) or "- keine"


# Auftrag 017, 0.2: nur was eine Makro-Frage braucht - ALTERNATIVEN, TEAMPLAN-Kurven, KARTENLAGE, STAND und die
# Kandidatenliste verlaengern den Prompt, ohne den Satz zu tragen
KURZ_WEG = ("ALTERNATIVEN:", "KARTENLAGE:", "STAND:", "KANDIDATEN DES COACHS", "- FARMEN:", "- ZURUECK:", "- BACK",
            "- WELLE", "- DRUECKEN", "- PLATTEN", "- SEITENWELLE", "- MIT_GRUPPE", "- ZUR_GRUPPE", "- NEHMEN",
            "- BESTREITEN", "- VORBEREITEN", "- HALTEN", "- KAUFEN", "- WOHIN", "- TP_", "- TRADE", "- ALL_IN",
            "- STAPELN", "- UNTER_TURM", "- WELLE_", "- ANNEHMEN", "- ABGEBEN", "- REIN", "- RAUS", "- DREHEN",
            "- VERTEIDIGEN", "- ANLAUFEN", "- GRUPPE", "- ERZWINGEN", "- KLAEREN")
SOFORT = "Antworte sofort mit dem Satz, ohne lange abzuwaegen."


def kurzer_prompt(prompt: str) -> str:
    zeilen = [z for z in prompt.splitlines() if not z.startswith(KURZ_WEG)]
    aus = []
    for z in zeilen:
        if z.startswith("TEAMPLAN:"):
            z = z.split(" (Kurven")[0]
        if z.startswith("ZEITLEISTE"):
            z = "; ".join(z.split("; ")[:3])
        aus.append(z)
    text = "\n".join(aus)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return f"{text}\n{SOFORT}"


def mit_entwurf(prompt: str, entwurf: str | None = None) -> str:
    """Auftrag 017, 0.2: ein konkreter Entwurf (der Plan-Satz des Kerns) - mit ihm antwortet Claude ohne langes
    Nachdenken (gemessen: erstes Token im Median 1,0 s statt 4,7 s, stratege_probe_017/latenz_entwurf.json)."""
    if entwurf is None:
        zeile = next((z for z in prompt.splitlines() if z.startswith("PLAN (entschieden):")), None)
        entwurf = zeile.split(":", 1)[1].strip() if zeile else None
    if not entwurf:
        return prompt
    return (f"{prompt}\nENTWURF DES COACHS: „{entwurf}“ - stimmt er, sag ihn als Kette (Schritt, danach, Grund); "
            f"passt er nicht zur Frage oder Lage, sag es besser. {SOFORT}")


def wellen_regeln() -> str:
    """wissen/wellen_regeln.md (Buch 13, Teil 3) ohne Kopf - fuer die Lane-Anlaesse."""
    try:
        text = (Path(__file__).resolve().parent.parent / "wissen" / "wellen_regeln.md").read_text(encoding="utf-8")
        return "\n".join(z for z in text.splitlines() if z.startswith("- ")).strip()
    except OSError:
        return ""


def claude_strom(prompt: str, bei_satz, system: str, timeout: float, bei_fertig=None) -> str:
    """Der echte Weg: Claude ueber das Abo, gestreamt, mit vorgehaltenem Prozess (wie `antworten.mit_claude`)."""
    from . import llm
    return llm.frage_strom(prompt, bei_satz, system=system, modell="sonnet", timeout=timeout, aufwand="low",
                           nachladen=2, bei_fertig=bei_fertig)      # Auftrag 017: zwei vorgehalten


claude_strom.mit_fertig = True


class AufzeichnungsStub:
    """Fuers Nachspielen (B5): kein Abo - jede Anfrage wird mitgeschrieben, die Antwort ist ein fester Satz (oder die
    naechste aus `antworten`). Ohne Vorgabe: NICHTS (Auftrag 017 - der Stratege schweigt ohne Substanz)."""

    def __init__(self, antworten: list[str] | None = None):
        self.anfragen: list[str] = []
        self.antworten = list(antworten or [])

    def __call__(self, prompt: str, bei_satz, system: str, timeout: float) -> str:
        self.anfragen.append(prompt)
        text = self.antworten.pop(0) if self.antworten else "NICHTS"
        for s in stratege._saetze(text):
            bei_satz(s)
        return text


# --- Auftrag 017, 1.5: ein aktiver Plan -----------------------------------------------------------------------------

AENDERUNG_S = 30.0          # innerhalb dieser Zeit aendert sich der Plan nur nach einer echten Lageaenderung
WIEDERHOLUNG_S = 60.0       # derselbe Plan wird fruehestens danach noch einmal gesagt
NUR_INFO = ("kern:INFO_", "kern:VORSICHT", "kern:technik", "kern:LAGEBILD", "tod", "briefing", "antwort")
ZIELE = (
    ("back", r"\bback\b|\brecall\b|zurück in die basis|\bheilen\b.*\bdann\b"),
    ("zurueck", r"\braus\b|zurück (unter|zu|zum|an|hinter) (deinen?|deinem|den|euren?|die) ?[\w-]*(turm|welle)|"
                r"zieh dich zurück|nicht (allein )?(nach )?vor"),
    ("drache", r"\bdrachen?\b"), ("herold", r"\bherold\b"), ("baron", r"\bbaron\b"), ("larven", r"\blarven\b"),
    ("turm", r"\b(ihren|auf den|den|am|zum) ([\w-]+ )?[\w-]*turm\b|\bplatten?\b|inhibitor"),
    ("gruppe", r"\bzu (deinem team|euch|[A-ZÄÖÜ]\w+ und [A-ZÄÖÜ]\w+)|\bgruppier|\bmit (dem |deinem )?team\b|zur gruppe"),
    ("welle:top", r"\btop(-welle| welle|-lane)?\b(?!-)"), ("welle:mid", r"\bmid(-welle| welle|-lane)?\b(?!-)"),
    ("welle:bot", r"\bbot(-welle| welle|-lane)?\b(?!-)"),
    ("welle", r"\bwelle\b|\bfarm|\bfreeze|\bslow push|\bcrash"),
)


EREIGNIS_SATZ = _re.compile(r"\b(ist|sind) (weg|down|gefallen|tot|drin)\W*$|^\W*(drache|herold|baron|larven) drin\W*$", _re.I)
EREIGNIS_KOPF = _re.compile(r"\b(tot|weg|gesehen|drin|down|gefallen|lebst|in \d+ sekunden)\b|^jetzt,? wo", _re.I)


def plan_ziel(text: str) -> str | None:
    """Das Ziel eines Plan-Satzes (vergleichbar ueber Kern und Stratege): back, zurueck, drache, turm, gruppe, welle:top
    ... - das erste im ersten Satz, das nicht verneint ist. None: kein Plan-Satz."""
    # das Ereignis vorweg ("Ihr innerer Top-Turm ist weg.", "Drei von ihnen tot: ...") ist nicht der Plan
    s = [x for x in stratege._saetze(text) if not EREIGNIS_SATZ.search(x)] or stratege._saetze(text) or [text]
    erster = s[0]
    if ": " in erster and EREIGNIS_KOPF.search(erster.split(": ", 1)[0]):
        erster = erster.split(": ", 1)[1]
    bestes = None                                        # das erste Ziel im Satz (nicht die erste Zeile der Liste)
    for rang, (ziel, muster) in enumerate(ZIELE):
        for m in _re.finditer(muster, erster, _re.I):
            if not _re.search(r"\b(nicht|kein\w*|statt|vergiss|nach dem|beim nächsten)\W+(\w+\W+){0,2}$",
                              erster[:m.start()], _re.I):
                if bestes is None or (m.start(), rang) < bestes[:2]:
                    bestes = (m.start(), rang, ziel)
                break
    return bestes[2] if bestes else None


class Schiedsrichter:
    """Auftrag 017, 1.5: Kern und Stratege schlagen nur vor. Gesprochen wird ein Plan-Satz, wenn er den aktiven Plan
    setzt oder aendert; eine Aenderung innerhalb von AENDERUNG_S nur nach einem Ereignis (Gefahr, Kill, Objective,
    Sichtung, Respawn, Basis, Welle kippt, Frage) - dann beginnt sie mit "Jetzt, wo <Ereignis>". Warnungen und Infos
    sprechen immer; eine Warnung setzt den Plan (zurueck), weil sie den alten unmoeglich macht."""

    def __init__(self):
        self.aktiv: tuple[str, float, str] | None = None      # (Ziel, Spielzeit, Text)
        self.ereignisse: list[tuple[float, str]] = []           # (Spielzeit, "Poppy weg ist")
        self.verworfen: list[dict] = []

    def ereignis(self, zeit: float, was: str) -> None:
        if self.ereignisse and self.ereignisse[-1][1] == was and zeit - self.ereignisse[-1][0] < 5.0:
            return
        self.ereignisse.append((zeit, was))
        del self.ereignisse[:-20]

    def setze(self, text: str, zeit: float) -> None:
        z = plan_ziel(text)
        if z is not None:
            self.aktiv = (z, zeit, text)

    def pruefe(self, text: str, zeit: float, warnung: bool = False) -> tuple[bool, str, str | None]:
        """(sprechen?, Text - bei einer Aenderung mit "Jetzt, wo ...", Grund des Verwerfens)."""
        z = plan_ziel(text)
        if z is None:
            return True, text, None
        a = self.aktiv
        if warnung or a is None:
            self.aktiv = (z, zeit, text)
            return True, text, None
        alter = zeit - a[1]
        if z == a[0]:
            if alter >= WIEDERHOLUNG_S:
                self.aktiv = (z, zeit, text)
                return True, text, None
            return self._weg(text, zeit, f"derselbe Plan ({z}) vor {int(alter)} s")
        if alter >= AENDERUNG_S:
            self.aktiv = (z, zeit, text)
            return True, text, None
        neu = [e for e in self.ereignisse if e[0] > a[1] - 0.5]
        if not neu:
            return self._weg(text, zeit, f"Planwechsel {a[0]} -> {z} nach {int(alter)} s ohne Lageänderung")
        if not _re.match(r"^\W*(jetzt|da |nachdem|weil|zwei|drei|vier|ihr|euer|eure|die|der|das|du lebst|"
                         r"[A-ZÄÖÜ][\w'’]+ (ist|sind|hat|war|oben|unten|tot|weg|gesehen|zurück))", text, _re.I):
            text = f"Jetzt, wo {neu[-1][1]}: {text[:1].lower()}{text[1:]}"
        self.aktiv = (z, zeit, text)
        return True, text, None

    def _weg(self, text: str, zeit: float, grund: str) -> tuple[bool, str, str]:
        self.verworfen.append({"zeit": zeit, "text": text, "grund": grund})
        del self.verworfen[:-200]
        return False, text, grund


class MakroStratege:
    def __init__(self, kern, plan, gehirn=None, frage_fn=None, cfg: dict | None = None, ablage: Path | None = None,
                 synchron: bool = False, aktiv: bool | None = None):
        c = {**_cfg(), **(cfg or {})}
        self.kern, self.plan, self.gehirn = kern, plan, gehirn
        self.frage_fn = frage_fn or claude_strom
        import os
        if os.environ.get("LOLCOACH_STRATEGE_AUSFALL"):     # Generalprobe: Abo-Ausfall nachstellen (Auftrag 015, B5)
            def ausfall(*_, **__):
                time.sleep(float(os.environ["LOLCOACH_STRATEGE_AUSFALL"]))
                raise RuntimeError("Ausfall nachgestellt")
            self.frage_fn = ausfall
        self.aktiv = bool(c.get("aktiv", True)) if aktiv is None else aktiv
        self.erster_max = float(c.get("erster_satz_max_s", 5.0))
        self.leerlauf_erster_max = float(c.get("leerlauf_erster_satz_max_s", 8.0))
        self.ausfall_s = float(c.get("ausfall_s", 30.0))
        self.pause_ausfall = float(c.get("pause_nach_ausfall_s", 120.0))
        self.leerlauf_ab = float(c.get("leerlauf_ab_s", 840.0))
        self.leerlauf_s = float(c.get("leerlauf_s", 45.0))
        self.kampf_nah_s = float(c.get("kampf_nah_s", 6.0))
        self.kampf_abstand_s = float(c.get("kampf_abstand_s", 30.0))
        self.lane_abstand_s = float(c.get("lane_abstand_s", 20.0))
        self.synchron = synchron
        self.ablage = ablage
        self.verlauf: list[tuple[float, str]] = []      # (Spielzeit, gesprochener Stratege-Satz)
        self.protokoll: list[dict] = []
        self.ausfall_bis = -1e9
        self._laeuft = False
        self._schloss = threading.Lock()
        self._zeit = 0.0
        self._letzter_leerlauf = -1e9
        self._war_tot = None
        self._war_basis = None
        self._kills: list[float] = []
        self._kills_n = None
        self._strukturen_n = None
        self._offen: tuple[str, float] | None = None    # ein Anlass wartet auf den Plan-Satz des Kerns
        self._n = 0
        # Auftrag 016: Kampf in der Naehe (1.4), Kontroll-Auge hoechstens einmal je Back (5)
        self._mit_leben: dict[str, list] = {}
        self._kampf_zuletzt = -1e9
        self._kampf_text: str | None = None
        self._back_nr = 0
        self._auge_back = -1
        # Auftrag 017: Schiedsrichter, Lane-Anlaesse
        self.schiedsrichter = Schiedsrichter()
        self._lane_zuletzt = -1e9
        self._welle_kat: str | None = None
        self._welle_kand: tuple[str, float] | None = None
        self._kanone_gesagt: set = set()
        self._pflicht_stand: tuple = (None, None, None)
        self._lane_weg = False
        self._flash_eigen: float | None = None
        self._spike_gesagt: set = set()
        self._gefahr_vorher = False

    # --- Zustand -------------------------------------------------------------------------------------------------

    def bereit(self) -> bool:
        return self.aktiv and time.monotonic() >= self.ausfall_bis and self.kern is not None \
            and getattr(self.kern, "m", None) is not None

    def _ausfall(self, grund: str) -> None:
        if time.monotonic() >= self.ausfall_bis:
            print(f"  Stratege: Ausfall ({grund[:120]}) - {int(self.pause_ausfall)} s lang nur der Kern", flush=True)
        self.ausfall_bis = time.monotonic() + self.pause_ausfall

    def _schreibe(self, eintrag: dict) -> None:
        self.protokoll.append(eintrag)
        if self.ablage is None:
            return
        try:
            with open(self.ablage, "a", encoding="utf-8") as d:
                d.write(json.dumps(eintrag, ensure_ascii=False, default=str) + "\n")
        except OSError:
            pass

    # --- Anfrage ---------------------------------------------------------------------------------------------------

    def _prompt(self, p, anlass: str, ende: str, entwurf: str | None = None) -> str:
        kern = self.kern
        lage = kern.kontext() or ""
        if self.gehirn is not None:
            inhalt = self.gehirn.kontext(anlass, p, lage)
        else:
            inhalt = f"LAGE JETZT:\n{lage}"
        if (kopf := kern.kopfzeile()):
            inhalt = f"{kopf}\n\n{inhalt}"
        a = self.schiedsrichter.aktiv
        if a is not None and self._zeit - a[1] <= WIEDERHOLUNG_S:
            inhalt += f"\n\nAKTIVER PLAN (seit {int(self._zeit - a[1])} s): „{a[2]}“ - aendere ihn nur, wenn sich die " \
                      "Lage geaendert hat, und sag dann zuerst, was sich geaendert hat."
        eigene = [(t, s) for t, s in self.verlauf if self._zeit - t <= 60.0][-2:]
        if eigene:
            inhalt += "\n\nDEINE LETZTEN SAETZE (hoechstens 60 s alt): " + " | ".join(
                f"{int(t // 60)}:{int(t % 60):02d} „{s}“" for t, s in eigene)
        if (auge := self._auge_grund()):
            inhalt += f"\n\nKONTROLL-AUGE: nicht vorschlagen ({auge})."
        return mit_entwurf(kurzer_prompt(f"{inhalt}\n\n{ende}"), entwurf)

    def _auge_grund(self) -> str | None:
        """Auftrag 016, 5: hoechstens einmal je Back vorschlagen; sagt Carlos Nein, 5 min lang gar nicht."""
        if self._zeit < getattr(self.kern, "auge_nein_bis", -1e9):
            return "der Spieler will gerade keins"
        if self._auge_back == self._back_nr:
            return "schon vorgeschlagen seit dem letzten Back"
        return None

    def _lage(self, p, kette: bool = False) -> dict:
        lage = stratege.pruef_lage(self.kern, p)
        lage["auge"] = self._auge_grund()
        lage["kette_pflicht"] = kette
        return lage

    def _gesprochen(self, zeit: float, text: str) -> None:
        self.verlauf.append((zeit, text))
        if stratege.AUGE.search(text) and not stratege.AUGE_NEIN.search(text):
            self._auge_back = self._back_nr

    def _versuch(self, prompt: str, lage: dict, bei_satz=None) -> dict:
        """Ein Aufruf: jeder Satz wird geprueft, sobald er fertig ist; die GANZE gueltige Antwort (hoechstens
        stratege.LAENGE_HOECHSTENS Woerter) geht am Textende EINMAL an `bei_satz` (Auftrag 017, 0.1). Ist der erste
        Satz verworfen, gilt der ganze Versuch als verworfen; "NICHTS" heisst: der Stratege schweigt."""
        t0 = time.monotonic()
        v = {"text": "", "gruende": [], "erster_s": None, "ende_s": None, "fehler": None, "verworfen": [],
             "nichts": False, "messung": {}}
        gut: list[str] = []
        woerter = [0]
        erster_verworfen = [False]
        halb = [""]
        gemeldet = [False]

        def satz(s: str, ende: bool = False) -> None:
            s = " ".join(f"{halb[0]} {s}".split())
            halb[0] = ""
            if not s or erster_verworfen[0] or v["nichts"]:
                return
            if not gut and NICHTS.match(s):
                v["nichts"] = True
                return
            # llm.frage_strom schickt den ersten Teilsatz schon am Komma: geprueft wird der ganze Satz
            if not ende and s.endswith((",", ";", ":", "–", "-")):
                halb[0] = s
                return
            gruende = stratege.pruefe(s, lage)
            if not gut and lage.get("kette_pflicht") and not stratege.kette(s):
                gruende = gruende + ["Kette fehlt (Kauf und Ziel danach im ersten Satz)"]     # Auftrag 016, 2
            if gruende:
                v["verworfen"].append({"satz": s, "gruende": gruende})
                if not gut:
                    erster_verworfen[0] = True
                    v["gruende"] = gruende
                return
            n = len(s.split())
            if gut and woerter[0] + n > stratege.LAENGE_HOECHSTENS:
                return                                   # Auftrag 015, 6: ganze Saetze, hoechstens 30 Woerter
            gut.append(s)
            woerter[0] += n

        def fertig() -> None:
            if halb[0]:
                satz("", ende=True)
            if gemeldet[0]:
                return
            gemeldet[0] = True
            if gut:
                v["erster_s"] = time.monotonic() - t0
                if bei_satz is not None:
                    bei_satz(" ".join(gut))
        try:
            if getattr(self.frage_fn, "mit_fertig", False):
                self.frage_fn(prompt, satz, stratege.STRATEGE_SYSTEM, self.ausfall_s, bei_fertig=fertig)
            else:
                self.frage_fn(prompt, satz, stratege.STRATEGE_SYSTEM, self.ausfall_s)
        except Exception as e:                            # Abo-Fehler, Zeitueberschreitung: still weiter mit dem Kern
            v["fehler"] = f"{type(e).__name__}: {e}"
        if not v["fehler"]:
            fertig()
        v["ende_s"] = time.monotonic() - t0
        v["text"] = " ".join(gut)
        if not gut and not v["gruende"] and not v["fehler"] and not v["nichts"]:
            v["gruende"] = ["keine Antwort"]
        return v

    def _frage(self, p, anlass: str, ende: str, bei_satz=None, vorbereitet=None) -> tuple[str | None, list[dict]]:
        """Bis zu zwei Versuche (der zweite mit dem Grund des Verwerfens). (Text oder None, Versuche). `vorbereitet`:
        (Prompt, Pruef-Lage), im Takt gebaut - der Hintergrund-Faden liest den Kern dann nicht mehr."""
        prompt, lage = vorbereitet or (self._prompt(p, anlass, ende), self._lage(p))
        versuche = [self._versuch(prompt, lage, bei_satz)]
        a = versuche[0]
        if a["fehler"]:
            self._ausfall(a["fehler"])
            return None, versuche
        if a["nichts"]:
            return None, versuche
        if not a["text"] and a["gruende"]:
            weg = a["verworfen"][0]["satz"] if a["verworfen"] else ""
            b = self._versuch(prompt + f"\n\nDein Vorschlag „{weg}“ wurde verworfen: {'; '.join(a['gruende'])}. "
                              "Sag es neu, ohne das - oder NICHTS, wenn du nichts Neues hast.", lage, bei_satz)
            versuche.append(b)
            if b["fehler"]:
                self._ausfall(b["fehler"])
                return None, versuche
            if b["text"]:
                return b["text"], versuche
            return None, versuche
        return a["text"] or None, versuche

    # --- B1: Fragen --------------------------------------------------------------------------------------------------

    def antworte(self, frage: str, absicht: str | None, p, bei_satz=None, entwurf: str | None = None) -> str | None:
        """Blockierend (Sprechtasten-Faden): die GANZE Antwort des Strategen oder None (dann der Kern). "Und dann?"
        beantwortet der aktive Plan (sein naechster Schritt ist der Entwurf)."""
        if not self.bereit() or (absicht or "OFFEN") not in STRATEGE_ABSICHTEN or p is None:
            return None
        self._zeit = p.zeit
        kette = bool(stratege.BACK_WORT.search(frage) or _re.search(r"kauf|was (mach|tu)|und dann|danach|plan", frage,
                                                                     _re.I))
        ende = f"Frage des Spielers: {frage}" + (
            "\nSag die Kette: den naechsten Schritt und den danach (bei Back oder Kauf: was, dann wohin, warum)."
            if kette else "")
        a = self.schiedsrichter.aktiv
        if entwurf is None and a is not None and p.zeit - a[1] <= WIEDERHOLUNG_S:
            danach = getattr(self.kern, "danach_text", None)
            entwurf = a[2] + (f" Danach {danach}." if danach and _re.search(r"und dann|danach|was dann", frage, _re.I)
                              else "")
        text, versuche = self._frage(p, frage, ende, None, (self._prompt(p, frage, ende, entwurf), self._lage(p)))
        self._schreibe({"zeit": p.zeit, "art": "frage", "frage": frage, "absicht": absicht,
                        "quelle": "stratege" if text else "kern", "text": text, "versuche": versuche})
        if text:
            self._gesprochen(p.zeit, text)
            self.schiedsrichter.ereignis(p.zeit, "du gefragt hast")
            self.schiedsrichter.setze(text, p.zeit)
            if bei_satz is not None:
                bei_satz(text)
        return text

    # --- B2/B3/B4 und Auftrag 017: im Takt -------------------------------------------------------------------------

    def bearbeite(self, ansagen: list, p, lagebild=None) -> list:
        """Vor plan.neu: Wellen-Saetze weg (B4), ein Wendepunkt-Satz des Kerns geht an den Strategen (B2), Anlaesse
        ohne Kern-Satz, Lane-Anlaesse und der Leerlauf fragen ihn; zuletzt entscheidet der Schiedsrichter, welche
        Plan-Saetze der Sprechplan bekommt."""
        if p is None or not p.ich:
            return ansagen
        self._zeit = p.zeit
        anlass = self._anlass(p, ansagen)
        if not self.bereit():
            return self._richte(ansagen, p)
        ansagen = [a for a in ansagen if a.schluessel != "kern:WELLE_DRUECKEN"]
        m = self.kern.m
        modus = getattr(getattr(self.kern, "modus", None), "aktuell", None)
        if self._laeuft or modus in ("KAMPF", "TOT", None) or getattr(self.kern, "gefahr", False) \
                or (m is not None and m.tot):
            return self._richte(ansagen, p)             # Auftrag 017, 0.2: ein Aufruf zur Zeit - der Anlass verfaellt
        if anlass == "Kampf in der Nähe" or (anlass or "").startswith("Lane:"):
            self._starte(p, anlass, None)                   # sofort, ohne auf den Kern zu warten
            return self._richte(ansagen, p)
        if anlass:
            self._offen = (anlass, p.zeit)
        offen = self._offen if self._offen is not None and p.zeit - self._offen[1] <= ANLASS_FENSTER_S else None
        # der Plan-Satz des Kerns an einem Wendepunkt (oder kurz nach Respawn, Basis, Kills) geht an den Strategen
        wp = next((a for a in ansagen if a.schluessel.startswith("kern:") and (
            getattr(a, "_kategorie", None) == "WENDEPUNKT"
            or (offen is not None and getattr(a, "_kategorie", None) == "PLAN"))), None)
        if wp is not None:
            ansagen = [a for a in ansagen if a is not wp]
            self._offen = None
            self._starte(p, "Wendepunkt" if offen is None else offen[0], wp)
            return self._richte(ansagen, p)
        plan_satz = any(a.schluessel.startswith("kern:") and getattr(a, "_kategorie", None) in PLAN_KATEGORIEN
                        for a in ansagen)
        if self._offen is not None and offen is None:
            art = self._offen[0]
            self._offen = None
            if not plan_satz and p.zeit - self._zuletzt_plan() >= ANLASS_RUHE_S:
                self._starte(p, art, None)
        elif p.zeit >= self.leerlauf_ab and not (m is not None and m.lane_phase) and not plan_satz \
                and p.zeit - self._letzter_leerlauf >= self.leerlauf_s and p.zeit - self._zuletzt_plan() >= self.leerlauf_s:
            self._letzter_leerlauf = p.zeit
            self._starte(p, "Leerlauf", None)
        return self._richte(ansagen, p)

    def _richte(self, ansagen: list, p) -> list:
        """Auftrag 017, 1.5: nur Plan-Saetze, die den Plan setzen oder aendern; Warnungen und Infos immer."""
        aus = []
        for a in ansagen:
            if a.schluessel.startswith(NUR_INFO) or not a.schluessel.startswith("kern:"):
                aus.append(a)
                continue
            warnung = a.thema == "gefahr" or getattr(a, "_kategorie", None) in ("GEFAHR", "VORSICHT")
            if not warnung:
                a.text = ohne_fuellsatz(a.text)          # Auftrag 017, 0.3: "Weiter deine Top-Welle." faellt weg
                if not a.text:
                    continue
            ok, text, _ = self.schiedsrichter.pruefe(a.text, p.zeit, warnung=warnung)
            if ok:
                a.text = text
                aus.append(a)
        return aus

    def _anlass(self, p, ansagen: list | None = None) -> str | None:
        """Respawn, Ankunft in der Basis, zwei Kills in 10 s, Kampf in der Naehe, Lane-Anlaesse (Auftrag 017, 1.2);
        dazu die Ereignisse fuer den Schiedsrichter."""
        tot = bool(p.ich.tot)
        m = self.kern.m
        sr = self.schiedsrichter
        basis = m is not None and m.bereich == "basis_eigen"
        n = len(p.kills_von("ChampionKill"))
        anlass = None
        if self._kills_n is not None and n > self._kills_n:
            self._kills += [p.zeit] * (n - self._kills_n)
            sr.ereignis(p.zeit, "ein Kill gefallen ist")
        self._kills = [t for t in self._kills if p.zeit - t <= 10.0]
        if len(self._kills) >= 2:
            anlass, self._kills = "zwei Kills in 10 s", []
        struk = sum(len(p.kills_von(e)) for e in ("TurretKilled", "InhibKilled", "DragonKill", "HeraldKill",
                                                   "BaronKill", "HordeKill", "AtakhanKill"))
        if self._strukturen_n is not None and struk > self._strukturen_n:
            sr.ereignis(p.zeit, "ein Turm oder Objective gefallen ist")
        self._strukturen_n = struk
        if self._war_tot and not tot:
            anlass = "Respawn"
            sr.ereignis(p.zeit, "du wieder lebst")
        elif self._war_basis is False and basis and not tot and p.zeit >= 90.0:
            anlass = "Ankunft in der Basis"
            sr.ereignis(p.zeit, "du in der Basis bist")
        if tot and not self._war_tot:
            sr.ereignis(p.zeit, "du tot bist")
        if basis and self._war_basis is False:
            self._back_nr += 1                              # Auftrag 016, 5: ein neuer Back
        gefahr = bool(getattr(self.kern, "gefahr", False))
        if gefahr and not self._gefahr_vorher:
            sr.ereignis(p.zeit, "Gegner kommen")
        self._gefahr_vorher = gefahr
        for a in ansagen or []:
            if a.schluessel.startswith("kern:INFO_") or getattr(a, "_kategorie", None) == "WENDEPUNKT":
                sr.ereignis(p.zeit, _als_ereignis(a.text))
        if anlass is None and not tot and (k := self._kampf_nah(p)) is not None:
            anlass = k
        if anlass is None and not tot and m is not None:
            anlass = self._lane_anlass(p, m)
        self._war_tot, self._kills_n = tot, n
        if m is not None and m.bereich is not None:        # ohne Ort (Spielbeginn, Minimap weg) zaehlt nichts
            self._war_basis = basis
        return anlass

    def _lane_anlass(self, p, m) -> str | None:
        """Auftrag 017, 1.2 (Buch 13, Teil 3): Anlaesse mit Inhalt statt Zeittakt, nur in der Lane-Phase an deiner Lane -
        Welle kippt, Kanone <= 20 s, Lane-Gegner weg/zurueck, Jungler gesehen, Flash weg, Spike kaufbar. Rueckgabe
        "Lane: <Ereignis>" (hoechstens einer je lane_abstand_s)."""
        b = m.b
        if b is None or not m.lane_phase or p.zeit < 90.0:
            return None
        grund = None
        # Welle kippt: stabil >= 3 s in der anderen Richtung
        w = m.welle
        kat = None
        if w is not None:
            kat = "zu dir" if w.zustand in ("ZU_DIR", "GROSS_ZU_DIR", "GECRASHT_BEI_DIR") else \
                "zu ihm" if w.zustand in ("ZU_IHM", "GROSS_ZU_IHM", "GECRASHT_BEI_IHM") else None
        if kat is not None:
            if self._welle_kand is None or self._welle_kand[0] != kat:
                self._welle_kand = (kat, p.zeit)
            elif p.zeit - self._welle_kand[1] >= 3.0 and kat != self._welle_kat:
                if self._welle_kat is not None:
                    grund = f"die Welle kippt und jetzt {kat} läuft"
                self._welle_kat = kat
        # Kanone
        if grund is None and m.kanone_in is not None and 0 < m.kanone_in <= 20:
            schl = round((p.zeit + m.kanone_in) / 15)
            if schl not in self._kanone_gesagt:
                self._kanone_gesagt.add(schl)
                grund = f"die Kanonenwelle in {int(m.kanone_in)} Sekunden kommt"
        # Lane-Gegner, Jungler, Flash ueber die Informationspflicht des Kerns
        pf = getattr(self.kern, "pflicht", None)
        stand = (getattr(pf, "lane_gesagt", None), getattr(pf, "jungler_gesagt", None),
                 getattr(self.kern, "_flash_zuletzt", None))
        alt, self._pflicht_stand = self._pflicht_stand, stand
        g = b.lane
        if grund is None and alt[0] is not None and stand[0] != alt[0] and g is not None:
            grund, self._lane_weg = f"{g.champion} weg ist", True
        if grund is None and self._lane_weg and g is not None and not g.s.tot and g.sichtbar \
                and g.ankunft is not None and g.ankunft < 15:
            grund, self._lane_weg = f"{g.champion} zurück auf der Lane ist", False
        if grund is None and alt[1] is not None and stand[1] != alt[1] and b.jungler is not None:
            grund = f"{b.jungler.champion} gesehen wurde"
        if grund is None and alt[2] is not None and stand[2] != alt[2]:
            grund = "ein gegnerischer Flash weg ist"
        fl = b.flash
        if grund is None and fl is not None and fl > 0 and (self._flash_eigen is not None and self._flash_eigen <= 0):
            grund = "dein Flash weg ist"
        self._flash_eigen = fl
        k = m.kauf
        if grund is None and k is not None and k.kaufen and getattr(k, "kern_fertig", False) \
                and (k.item or k.kaufen[0]) not in self._spike_gesagt:
            self._spike_gesagt.add(k.item or k.kaufen[0])
            grund = f"du {k.item or k.kaufen[0]} kaufen kannst"
        if grund is None or m.bereich == "basis_eigen" or p.zeit - self._lane_zuletzt < self.lane_abstand_s:
            return None
        self.schiedsrichter.ereignis(p.zeit, grund)
        self._lane_zuletzt = p.zeit
        return f"Lane: {grund}"

    def _kampf_nah(self, p) -> str | None:
        """Auftrag 016, 1.4 (133448 6:23: "hilf Volibear, der ist neben dir, du bist volles Leben"): ein Mitspieler
        kaempft in <= kampf_nah_s Weg von dir - sein Leben faellt (>= 10 % in 3 s) und ein Gegner ist sichtbar bei ihm
        (<= 1200). Hoechstens einmal je kampf_abstand_s."""
        from .bewertung import WEGFAKTOR, abstand
        m = self.kern.m
        b = m.b if m is not None else None
        if b is None or b.pos is None or m.bereich == "basis_eigen":
            return None
        jetzt = p.zeit
        feinde = [g for g in b.gegner if g.sichtbar and not g.s.tot and g.pos is not None]
        for s, wo, leben, *_ in b.mitspieler or []:
            if s.tot or wo is None:
                continue
            verlauf = self._mit_leben.setdefault(s.champion, [])
            if leben is not None:
                verlauf.append((jetzt, leben))
            while verlauf and verlauf[0][0] < jetzt - 3.0:
                verlauf.pop(0)
            faellt = len(verlauf) >= 2 and verlauf[0][1] - verlauf[-1][1] >= 0.10
            weg = abstand(wo, b.pos) * WEGFAKTOR / (m.mein_tempo or 340.0)
            bei = [g for g in feinde if abstand(g.pos, wo) <= 1200]
            if faellt and bei and weg <= self.kampf_nah_s and jetzt - self._kampf_zuletzt >= self.kampf_abstand_s:
                self._kampf_zuletzt = jetzt
                self._kampf_text = (f"{s.champion} kämpft {int(round(weg))} s von dir gegen "
                                    + " und ".join(g.champion for g in bei[:3])
                                    + f", sein Leben {int(round((leben or 0) * 100))} %")
                self.schiedsrichter.ereignis(jetzt, f"{s.champion} neben dir kämpft")
                return "Kampf in der Nähe"
        return None

    def _zuletzt_plan(self) -> float:
        """Spielzeit des letzten gesprochenen Plan-Satzes, einer Warnung oder Antwort."""
        t = -1e9
        for a in reversed(getattr(self.plan, "gesagt", []) or []):
            if a.gesprochen is None:
                continue
            if (a.schluessel.startswith(("kern:", "stratege:", "antwort")) and not a.schluessel.startswith("kern:INFO_")) \
                    or a.thema == "gefahr":
                t = a.gesprochen
                break
        return t

    def _kern_ersatz(self, p):
        """Der Kern-Satz fuer Respawn und Basis, falls der Stratege zu spaet kommt oder verworfen wird: sein Plan mit
        Grund (bei einem Back mit Kette)."""
        try:
            from .kern.fragen import satz
            pl = self.kern.fuehrer.plan
            m = self.kern.m
            if m is None or pl is None or pl.handlung.stumm:
                return None
            text = satz(pl.handlung)
            if not text or stratege.fuellsatz(text):
                return None
            if stratege.back_ruf(text):
                text = self.kern._mit_kette(text, m)
        except Exception:
            return None
        a = Ansage(text, WICHTIG, f"kern:{pl.art}", zeit=p.zeit, gueltig=8.0, sperre=0.0)
        a._kategorie = "PLAN"
        return a

    def _welle_satz(self, m) -> str | None:
        """Der Wellenstand als Entwurf fuer einen Lane-Anlass ("Deine Top-Welle: 3 gegen 6, sie laeuft zu dir.")."""
        w = m.welle
        if w is None or w.unsere is None:
            return None
        zahl = f"{w.unsere} gegen {w.ihre}" if w.ihre is not None else f"{w.unsere} eigene Vasallen"
        folge = {"ZU_DIR": "sie läuft zu dir", "GROSS_ZU_DIR": "sie läuft groß zu dir",
                 "GECRASHT_BEI_DIR": "sie liegt an deinem Turm", "ZU_IHM": "sie läuft zu ihm",
                 "GROSS_ZU_IHM": "sie läuft groß zu ihm", "GECRASHT_BEI_IHM": "sie ist an seinem Turm",
                 "MITTE": "sie steht in der Mitte"}.get(w.zustand)
        return f"Deine {w.lane}-Welle: {zahl}, {folge}." if folge else None

    def _starte(self, p, art: str, kern_satz) -> None:
        """B2/B3 und Lane-Anlaesse: fragt den Strategen; seine ganze Antwort muss in der Frist da sein, sonst spricht
        der Kern-Satz (falls es einen gibt). Die Antwort geht als EINE Ansage in den Sprechplan - wenn der
        Schiedsrichter sie laesst."""
        self._laeuft = True
        self._n += 1
        nr = self._n
        zeit0 = p.zeit
        entschieden = threading.Event()
        uebernommen = [False]
        lane = art.startswith("Lane:")
        frist = self.leerlauf_erster_max if art == "Leerlauf" or lane else self.erster_max
        if kern_satz is None and art in ("Respawn", "Ankunft in der Basis"):
            kern_satz = self._kern_ersatz(p)            # Auftrag 016: die Kette kommt, auch wenn Claude ausfaellt
        uhr = f"{int(p.zeit // 60)}:{int(p.zeit % 60):02d}"
        kette = art == "Ankunft in der Basis" or (kern_satz is not None and stratege.back_ruf(kern_satz.text))
        nichts = " Hast du nichts Neues (keine neue Info, keine Entscheidung), antworte nur: NICHTS."
        entwurf = kern_satz.text if kern_satz is not None else None
        if lane:
            m = self.kern.m
            entwurf = self._welle_satz(m) if m is not None else None
            ende = (f"ANLASS (Lane, {uhr}): jetzt, wo {art.split(': ', 1)[1]}. Freeze, Slow Push oder Crash - und warum? "
                    "Ein Satz: Entscheidung mit Grund aus der Lage (EIGENE WELLE, LANE-GEGNER, Jungler, Kanone) und was "
                    f"danach kommt.{nichts}\nWELLEN-REGELN:\n{wellen_regeln()}")
        elif art == "Leerlauf":
            ende = f"ANLASS: seit einer Weile kein Plan-Satz ({uhr}). Was jetzt, was danach, warum?{nichts}"
        elif art == "Ankunft in der Basis":
            ende = (f"ANLASS: Ankunft in der Basis um {uhr}. Sag die ganze Kette in EINEM Satz: was du jetzt kaufst "
                    "(passend zu Gold und freien Plaetzen, siehe KAUF), dann wohin, und warum.")
        elif art == "Kampf in der Nähe":
            ende = (f"ANLASS: Kampf in der Naehe um {uhr}: {self._kampf_text}. Hin und helfen oder nicht? Mit Grund "
                    "(dein Leben, wer dort ist, wer fehlt) - und was danach kommt.")
        else:
            ende = (f"ANLASS: Wendepunkt ({art}) um {uhr}. Nenn den naechsten Schritt und den danach, mit Grund"
                    + (" - bei einem Back im selben Satz Kauf und Ziel." if kette else "."))
        t0 = time.monotonic()
        wiederholt = [False]

        def einwerfen(a) -> bool:
            warnung = getattr(a, "_kategorie", None) in ("GEFAHR", "VORSICHT")
            ok, text, _ = self.schiedsrichter.pruefe(a.text, max(self._zeit, zeit0), warnung=warnung)
            if ok:
                a.text = text
                self.plan.einwerfen(a)
            return ok

        def satz(s: str) -> None:
            with self._schloss:
                if uebernommen[0] or entschieden.is_set() or time.monotonic() - t0 > frist:
                    return                               # zu spaet: der Kern-Satz spricht
                uebernommen[0] = True
                entschieden.set()
            a = Ansage(s, WICHTIG, f"stratege:{art}:{nr}", zeit=max(self._zeit, zeit0), gueltig=12.0, sperre=0.0)
            a._kategorie = "STRATEGE"
            if not einwerfen(a):
                uebernommen[0] = False                   # derselbe Plan wie eben: nichts sagen
                wiederholt[0] = True

        def fallback() -> None:
            with self._schloss:
                if uebernommen[0] or entschieden.is_set():
                    return
                entschieden.set()
            if kern_satz is not None:
                kern_satz.zeit = max(kern_satz.zeit, self._zeit)
                einwerfen(kern_satz)

        try:
            vorbereitet = (self._prompt(p, "Was jetzt, und warum?", ende, entwurf), self._lage(p, kette))
        except Exception as e:                              # die Lage laesst sich nicht bauen: der Kern spricht
            print(f"  Stratege: Lage nicht gebaut ({type(e).__name__}: {e})", flush=True)
            self._laeuft = False
            if kern_satz is not None:
                einwerfen(kern_satz)
            return

        def lauf() -> None:
            try:
                try:
                    text, versuche = self._frage(p, "Was jetzt, und warum?", ende, satz, vorbereitet)
                except Exception as e:
                    text, versuche = None, [{"fehler": f"{type(e).__name__}: {e}"}]
                if not uebernommen[0]:
                    fallback()
                nichts_ = any(v.get("nichts") for v in versuche)
                quelle = "stratege" if uebernommen[0] else "wiederholt" if wiederholt[0] else (
                    "kern" if kern_satz is not None else "nichts" if nichts_ else "still")
                if uebernommen[0] and text:
                    self._gesprochen(zeit0, text)
                self._schreibe({"zeit": zeit0, "art": art, "quelle": quelle, "text": text if uebernommen[0] else
                                (kern_satz.text if kern_satz is not None else None),
                                "kern_satz": kern_satz.text if kern_satz is not None else None, "versuche": versuche})
            finally:
                self._laeuft = False

        if self.synchron:
            lauf()
            return
        threading.Timer(frist, fallback).start()
        threading.Thread(target=lauf, daemon=True).start()


def ohne_fuellsatz(text: str) -> str:
    """Auftrag 017, 0.3: Fuellsaetze aus einem Kern-Satz streichen ("Euer aeusserer Mid-Turm ist weg. Weiter deine
    Top-Welle." -> "Euer aeusserer Mid-Turm ist weg."); nennt der naechste Satz eine Alternative ("Oder ..."), bleibt
    alles."""
    s = stratege._saetze(text)
    if not any(stratege.fuellsatz(x) for x in s):
        return text
    aus = []
    for i, x in enumerate(s):
        oder = i + 1 < len(s) and s[i + 1].lstrip().lower().startswith("oder")
        if stratege.fuellsatz(x) and not oder:
            continue
        aus.append(x)
    return " ".join(aus)


def _als_ereignis(text: str) -> str:
    """Ein Info- oder Wendepunkt-Satz als Nebensatz fuer "Jetzt, wo ...": "Teemo im oberen Fluss." -> "Teemo im oberen
    Fluss aufgetaucht ist"; "Ihr aeusserer Mid-Turm ist weg." -> "ihr aeusserer Mid-Turm weg ist"."""
    s = stratege._saetze(text)[0] if stratege._saetze(text) else text
    s = s.split(":")[0].split(",")[0].rstrip(" .!")
    m = _re.match(r"^(.*?) (ist|sind) (.*)$", s)
    if m:
        return f"{m.group(1)[:1].lower()}{m.group(1)[1:]} {m.group(3)} {m.group(2)}"
    if s.endswith("Flash weg"):
        return s.replace("Flash weg", "Flash weg ist")
    if s.endswith("gesehen"):
        return f"{s} wurde"
    return f"{s} aufgetaucht ist"
