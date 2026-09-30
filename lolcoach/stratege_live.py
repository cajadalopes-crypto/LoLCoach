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
ERSETZT = ("PLAN", "WENDEPUNKT", "VORSCHAU", "FENSTER", "MAKRO")    # Auftrag 021: Plan-Saetze fuehrt Claude
# ... und nur diese Anlaesse fragen nach einem verworfenen Vorschlag ein zweites Mal (Kosten, Runde 1: 218 Aufrufe)
KURZ_ANLASS = ("Lane:", "Fenster:", "Roam:", "Kampf in der Nähe")   # Auftrag 023, 4: ohne Wissensblock
ZUSAMMEN_S = 10.0          # Auftrag 023, 3: Anlaesse so kurz nacheinander fragen nur einmal
STOPP_S = 8.0              # Auftrag 023, 3: eine Warnung so kurz nach einem anderen Plan beginnt mit "Stopp –"
STOPP_KLEIN = ("zurück", "raus", "weg", "nicht", "bleib", "back")
NOCHMAL = ("Wendepunkt", "Respawn", "Ankunft in der Basis", "Kampf in der Nähe", "zwei Kills in 10 s")
NICHTS = _re.compile(r"^\W*nichts\W*$", _re.I)
PLAN_ZEILE = _re.compile(r"^\W*PLAN\s*:", _re.I)
# Auftrag 021, 1 (Buch 14 C.1): Claude fuehrt den Plan - Ziel, zwei Schritte, Grund, gueltig bis, Abbruch
PLAN_FORMAT = (" Nach dem gesprochenen Text schreibst du immer eine eigene letzte Zeile, die nicht gesprochen wird: "
               "'PLAN: Ziel | naechster Schritt | Schritt danach | Grund | gilt bis mm:ss | Abbruch wenn ...' - "
               "hoechstens 20 Woerter, Stichworte. "
               "Aenderst du den Plan nicht, wiederhol ihn dort. Bei NICHTS keine PLAN-Zeile.")


class Plan:
    """Der aktive Plan, von Claude gesetzt (Auftrag 021, 1): Ziel, naechste zwei Schritte, Grund, gueltig bis,
    Abbruch-Bedingung. Er beantwortet "Und dann?" und steht in jedem Prompt."""

    def __init__(self, zeile: str, zeit: float, satz: str):
        teile = [t.strip() for t in PLAN_ZEILE.sub("", zeile).split("|")]
        teile += [""] * (6 - len(teile))
        self.ziel, self.schritt, self.danach, self.grund, bis, self.abbruch = teile[:6]
        self.abbruch = self.abbruch.removeprefix("Abbruch wenn").strip(" :")
        m = _re.search(r"(\d{1,2}):(\d\d)", bis)
        self.bis = int(m.group(1)) * 60 + int(m.group(2)) if m else zeit + 90.0
        self.zeit, self.satz = zeit, satz

    def gilt(self, zeit: float) -> bool:
        return bool(self.ziel) and zeit <= self.bis

    def text(self, zeit: float) -> str:
        uhr = f"{int(self.bis // 60)}:{int(self.bis % 60):02d}"
        return (f"AKTIVER PLAN (seit {int(zeit - self.zeit)} s, gilt bis {uhr}): Ziel {self.ziel}; als Naechstes "
                f"{self.schritt}; danach {self.danach}; Grund: {self.grund}; Abbruch wenn {self.abbruch or '-'}. "
                "Aendere ihn nur, wenn sich die Lage geaendert hat oder er erledigt ist - dann zuerst, was sich "
                "geaendert hat.")


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


def claude_strom(prompt: str, bei_satz, system: str, timeout: float, bei_fertig=None, modell: str = "sonnet",
                 wissen: str | None = None, messung: dict | None = None) -> str:
    """Der echte Weg: Claude ueber die API (Auftrag 019) oder das Abo, gestreamt, mit vorgehaltenem Prozess.
    `wissen`: der Wissensblock der Partie (Auftrag 021), bei der API zwischengespeichert."""
    from . import llm
    return llm.frage_strom(prompt, bei_satz, system=system, modell=modell, timeout=timeout, aufwand="low",
                           nachladen=2, bei_fertig=bei_fertig, wissen=wissen, messung=messung)      # Auftrag 017: zwei vorgehalten


claude_strom.mit_fertig = True
claude_strom.mit_wissen = True


class Zwischenspeicher:
    """Auftrag 019, 0.5: im Nachspiel je (Modell, System, Prompt) die Antwort merken - ein Wiederholungslauf mit
    unveraenderter Lage fragt nicht neu. Die Datei ist eine JSON-Zeilenliste."""
    mit_fertig = True
    mit_wissen = True

    def __init__(self, frage_fn, datei: Path):
        import hashlib
        self._h = hashlib.sha256
        self.frage_fn, self.datei = frage_fn, datei
        self.treffer = self.neu = 0
        self._d: dict[str, str] = {}
        self._schloss = threading.Lock()
        if datei.exists():
            for z in datei.read_text(encoding="utf-8").splitlines():
                try:
                    e = json.loads(z)
                    self._d[e["k"]] = e["t"]
                except (ValueError, KeyError):
                    pass

    def __call__(self, prompt, bei_satz, system, timeout, bei_fertig=None, modell="sonnet", wissen=None, messung=None):
        k = self._h(f"{modell}\n{system}\n{wissen or ''}\n{prompt}".encode("utf-8")).hexdigest()
        if k in self._d:
            self.treffer += 1
            text = self._d[k]
            if messung is not None:
                messung["zwischenspeicher"] = True
            for s in stratege._saetze(text):
                bei_satz(s)
            if bei_fertig is not None:
                bei_fertig()
            return text
        self.neu += 1
        extra = {"wissen": wissen, "messung": messung} if getattr(self.frage_fn, "mit_wissen", False) else {}
        text = self.frage_fn(prompt, bei_satz, system, timeout, bei_fertig=bei_fertig, modell=modell, **extra)
        with self._schloss:
            self._d[k] = text
            with open(self.datei, "a", encoding="utf-8") as f:
                f.write(json.dumps({"k": k, "t": text}, ensure_ascii=False) + "\n")
        return text


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
NUR_INFO = ("kern:INFO_", "kern:PAKET_", "kern:VORSICHT", "kern:technik", "kern:LAGEBILD", "tod", "briefing", "antwort")
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
        self.gilt = None          # Auftrag 024, 2: (Ereignistext) -> bool, "Xerath tot ist" nur, solange er tot ist

    def ereignis(self, zeit: float, was: str | None) -> None:
        if not was:
            return                # Auftrag 024, 5.4: kein Ereignis ("Aus der Basis aufgetaucht ist")
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
        neu = [e for e in self.ereignisse if e[0] > a[1] - 0.5 and (self.gilt is None or self.gilt(e[1]))]
        if not neu:
            return self._weg(text, zeit, f"Planwechsel {a[0]} -> {z} nach {int(alter)} s ohne Lageänderung")
        if not _re.match(r"^\W*(jetzt|da |nachdem|weil|zwei|drei|vier|ihr|euer|eure|die|der|das|du lebst|"
                         r"[A-ZÄÖÜ][\w'’]+ (ist|sind|hat|war|oben|unten|tot|weg|gesehen|zurück))", text, _re.I):
            text = f"Jetzt, wo {neu[-1][1]}: {text}"       # gross bleibt gross ("Herold", 183125 14:43)
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
        # Auftrag 019: Modell je Zweck ([llm] in wissen/kern.toml: schnell = Haiku, stark = Sonnet)
        try:
            from . import wissen
            lc = dict(wissen.lade("kern").get("llm", {}))
        except Exception:
            lc = {}
        self.modelle = {"lane": lc.get("modell_lane", "schnell"), "frage": lc.get("modell_frage", "schnell"),
                        "plan": lc.get("modell_plan", "stark")}
        if os.environ.get("LOLCOACH_MODELL"):          # Messung (Auftrag 019): ein Modell fuer alles
            self.modelle = {k: os.environ["LOLCOACH_MODELL"] for k in self.modelle}
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
        self.schiedsrichter.gilt = self._ereignis_gilt
        self._lane_zuletzt = -1e9
        self._welle_kat: str | None = None
        self._welle_kand: tuple[str, float] | None = None
        self._kanone_gesagt: set = set()
        self._pflicht_stand: tuple = (None, None, None)
        self._lane_weg = False
        self._flash_eigen: float | None = None
        self._spike_gesagt: set = set()
        self._gefahr_vorher = False
        # Auftrag 021: Plan-Objekt, Partie fuer den Wissensblock, neue Anlaesse
        self.plan_obj: Plan | None = None
        self._p = None
        self._obj_gesagt: set = set()
        self._tote_gegner: set = set()
        self._fenster_zuletzt = -1e9
        self._roam_gesagt: dict[str, float] = {}
        self._starke: dict[str, float] = {}
        self._letzter_start = -1e9

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

    def _prompt(self, p, anlass: str, ende: str, entwurf: str | None = None, kurz: bool = False) -> str:
        kern = self.kern
        from . import welt
        w = welt.bauen(kern, p)                          # Auftrag 019: das Lagebild statt kern.kontext()
        lage = welt.text(w, kurz=kurz) if w is not None else (kern.kontext() or "")
        if self.gehirn is not None:
            inhalt = self.gehirn.kontext(anlass, p, lage)
        else:
            inhalt = f"LAGE JETZT:\n{lage}"
        if (kopf := kern.kopfzeile()):
            inhalt = f"{kopf}\n\n{inhalt}"
        a = self.schiedsrichter.aktiv
        if self.plan_obj is not None and self.plan_obj.gilt(self._zeit):
            inhalt += "\n\n" + self.plan_obj.text(self._zeit)             # Auftrag 021, 1
        elif a is not None and self._zeit - a[1] <= WIEDERHOLUNG_S:
            inhalt += f"\n\nAKTIVER PLAN (seit {int(self._zeit - a[1])} s): „{a[2]}“ - aendere ihn nur, wenn sich die " \
                      "Lage geaendert hat, und sag dann zuerst, was sich geaendert hat."
        eigene = [(t, s) for t, s in self.verlauf if self._zeit - t <= 60.0][-2:]
        if eigene:
            inhalt += "\n\nDEINE LETZTEN SAETZE (hoechstens 60 s alt): " + " | ".join(
                f"{int(t // 60)}:{int(t % 60):02d} „{s}“" for t, s in eigene)
        if (auge := self._auge_grund()):
            inhalt += f"\n\nKONTROLL-AUGE: nicht vorschlagen ({auge})."
        return mit_entwurf(kurzer_prompt(f"{inhalt}\n\n{ende}"), entwurf)

    def _wissen(self) -> str | None:
        """Auftrag 021, 2: der Wissensblock dieser Partie (zwischengespeichert)."""
        try:
            from . import partie_wissen
            return partie_wissen.block(self._p)
        except Exception:
            return None

    def _ereignis_gilt(self, was: str) -> bool:
        """Auftrag 024, 2 (231200 2:57): "Jetzt, wo Xerath tot ist" nur, solange die API ihn tot meldet."""
        p = getattr(self, "_p", None)
        if p is None or not _re.search(r"\btot\b", was):
            return True
        genannt = [s for s in p.spieler if _re.search(rf"\b{_re.escape(s.champion)}\b", was)]
        return all(s.tot for s in genannt)

    def _noch_sicher(self, a):
        """Auftrag 021 (Nachspiel 125902 9:15: "Crash die Welle" - beim Fragen war nach vorn erlaubt, beim Sprechen
        stand das Leben unter R1): der Sprechplan prueft den Satz vor dem Sprechen noch einmal gegen die Lage JETZT."""
        def pruefe() -> bool:
            try:
                lage = stratege.pruef_lage(self.kern, self._p)
                # Auftrag 024, 2: tot oder lebendig zur SPRECHzeit (231200 2:57: gefragt 2:47, Xerath lebte 2:52)
                return not stratege.sicherheit(a.text, lage) and not stratege.fakten(a.text, lage)
            except Exception:
                return True
        return pruefe

    def _plan_merken(self, versuche: list[dict], zeit: float, text: str | None) -> None:
        zeile = next((v.get("plan") for v in reversed(versuche) if v.get("plan")), None)
        if text and zeile:
            self.plan_obj = Plan(zeile, zeit, text)
            pk = getattr(self.kern, "pakete", None)
            if pk is not None:
                pk.plan_zeile(zeile)                 # Auftrag 025, 2: das Plan-Objekt geht im Paket auf

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

    def _versuch(self, prompt: str, lage: dict, bei_satz=None, modell: str = "stark", kurz: bool = False) -> dict:
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
            if "plan" in v or PLAN_ZEILE.match(s or ""):  # Auftrag 021: die PLAN-Zeile wird gemerkt, nicht gesprochen
                erste = "plan" not in v
                v["plan"] = (v.get("plan", "") + " " + (s or "")).strip()
                if erste and gut:
                    fertig()                             # der gesprochene Teil ist da: nicht auf die PLAN-Zeile warten
                return
            if (i := (s or "").find("PLAN:")) > 0:
                v["plan"] = s[i:].strip()
                s = s[:i]
                satz(s, ende=True)
                if gut:
                    fertig()
                return
            s = " ".join(f"{halb[0]} {s}".replace("**", "").split())    # Auftrag 023: kein Markdown ("**Nein**")
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
            if not gut:
                v["erster_satz_s"] = time.monotonic() - t0     # Auftrag 023, 4: bis zum ersten gueltigen Satz
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
                extra = {"wissen": None if kurz else self._wissen(), "messung": v["messung"]} \
                    if getattr(self.frage_fn, "mit_wissen", False) else {}
                self.frage_fn(prompt, satz, stratege.STRATEGE_SYSTEM + PLAN_FORMAT, self.ausfall_s, bei_fertig=fertig,
                              modell=modell, **extra)
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

    def _frage(self, p, anlass: str, ende: str, bei_satz=None, vorbereitet=None,
               modell: str = "stark", nochmal: bool = True, kurz: bool = False) -> tuple[str | None, list[dict]]:
        """Bis zu zwei Versuche (der zweite mit dem Grund des Verwerfens). (Text oder None, Versuche). `vorbereitet`:
        (Prompt, Pruef-Lage), im Takt gebaut - der Hintergrund-Faden liest den Kern dann nicht mehr."""
        prompt, lage = vorbereitet or (self._prompt(p, anlass, ende), self._lage(p))
        versuche = [self._versuch(prompt, lage, bei_satz, modell, kurz)]
        a = versuche[0]
        from . import welt
        a["prompt_tokens"], a["modell"] = welt.tokens(prompt), modell      # Auftrag 019: Tokens je Aufruf
        if a["fehler"]:
            self._ausfall(a["fehler"])
            return None, versuche
        if a["nichts"]:
            return None, versuche
        if not a["text"] and a["gruende"] and not nochmal:
            return None, versuche                        # Auftrag 021: Kosten - nur wichtige Anlaesse fragen zweimal
        if not a["text"] and a["gruende"]:
            weg = a["verworfen"][0]["satz"] if a["verworfen"] else ""
            b = self._versuch(prompt + f"\n\nDein Vorschlag „{weg}“ wurde verworfen: {'; '.join(a['gruende'])}. "
                              "Sag es neu, ohne das - oder NICHTS, wenn du nichts Neues hast.", lage, bei_satz,
                              modell, kurz)
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
        self._p = p
        kette = bool(stratege.BACK_WORT.search(frage) or _re.search(r"kauf|was (mach|tu)|und dann|danach|plan", frage,
                                                                     _re.I))
        pl = self.plan_obj
        if entwurf is None and pl is not None and pl.gilt(p.zeit) and _re.search(r"und dann|danach|was dann|als nächstes",
                                                                                 frage, _re.I):
            entwurf = f"{pl.schritt[:1].upper()}{pl.schritt[1:]}, danach {pl.danach}: {pl.grund}."   # Auftrag 021, 1
        ende = f"Frage des Spielers: {frage}" + (
            "\nSag die Kette: den naechsten Schritt und den danach (bei Back oder Kauf: was, dann wohin, warum)."
            if kette else "") + (
            # Auftrag 023, 3: 30 von 52 Widerspruechen in 021 betrafen Antworten
            "\nDeine Antwort bestaetigt den AKTIVEN PLAN - oder aendert ihn ausdruecklich mit dem Grund zuerst "
            "('Jetzt, wo ...: ...'). Keine zweite Empfehlung daneben.")
        a = self.schiedsrichter.aktiv
        if entwurf is None and a is not None and p.zeit - a[1] <= WIEDERHOLUNG_S:
            danach = getattr(self.kern, "danach_text", None)
            entwurf = a[2] + (f" Danach {danach}." if danach and _re.search(r"und dann|danach|was dann", frage, _re.I)
                              else "")
        text, versuche = self._frage(p, frage, ende, None, (self._prompt(p, frage, ende, entwurf), self._lage(p)),
                                     self.modelle["frage"])
        self._schreibe({"zeit": p.zeit, "art": "frage", "frage": frage, "absicht": absicht,
                        "quelle": "stratege" if text else "kern", "text": text, "versuche": versuche})
        if text:
            self._gesprochen(p.zeit, text)
            self._plan_merken(versuche, p.zeit, text)
            self.schiedsrichter.ereignis(p.zeit, "du gefragt hast")
            self.schiedsrichter.setze(text, p.zeit)
            if bei_satz is not None:
                bei_satz(text)
        return text

    def antwort_gesprochen(self, text: str | None, zeit: float) -> None:
        """Auftrag 023, 3 (eine Stimme): auch eine Antwort des Kerns laeuft ueber den EINEN Plan - nennt sie ein Ziel,
        ist sie ab jetzt der Plan (die Frage ist das Ereignis); ein Claude-Plan mit anderem Ziel gilt nicht mehr."""
        if not text:
            return
        self.schiedsrichter.ereignis(zeit, "du gefragt hast")
        z = plan_ziel(text)
        if z is not None:
            self.schiedsrichter.setze(text, zeit)
            if self.plan_obj is not None and plan_ziel(self.plan_obj.satz) != z:
                self.plan_obj = None

    # --- B2/B3/B4 und Auftrag 017: im Takt -------------------------------------------------------------------------

    def bearbeite(self, ansagen: list, p, lagebild=None) -> list:
        """Vor plan.neu: Wellen-Saetze weg (B4), ein Wendepunkt-Satz des Kerns geht an den Strategen (B2), Anlaesse
        ohne Kern-Satz, Lane-Anlaesse und der Leerlauf fragen ihn; zuletzt entscheidet der Schiedsrichter, welche
        Plan-Saetze der Sprechplan bekommt."""
        if p is None or not p.ich:
            return ansagen
        self._zeit = p.zeit
        self._p = p
        anlass = self._anlass(p, ansagen)
        if not self.bereit():
            return self._richte(ansagen, p)
        ansagen = [a for a in ansagen if a.schluessel != "kern:WELLE_DRUECKEN"]
        m = self.kern.m
        modus = getattr(getattr(self.kern, "modus", None), "aktuell", None)
        ersetzt = lambda a: a.schluessel.startswith("kern:") and getattr(a, "_kategorie", None) in ERSETZT
        if self._laeuft and not (m is not None and m.tot):
            # Auftrag 021, 1: Claude fasst den Plan gerade neu - der Kern baut keinen eigenen Plan-Satz dazwischen
            return self._richte([a for a in ansagen if not ersetzt(a)], p)
        if self._laeuft or modus in ("KAMPF", "TOT", None) or getattr(self.kern, "gefahr", False) \
                or (m is not None and m.tot):
            return self._richte(ansagen, p)             # Auftrag 017, 0.2: ein Aufruf zur Zeit - der Anlass verfaellt
        if anlass == "Kampf in der Nähe" or (anlass or "").startswith(("Lane:", "Objective:", "Fenster:", "Roam:")):
            self._starte(p, anlass, None)                   # sofort, ohne auf den Kern zu warten
            return self._richte([a for a in ansagen if not ersetzt(a)], p)
        if anlass:
            self._offen = (anlass, p.zeit)
        offen = self._offen if self._offen is not None and p.zeit - self._offen[1] <= ANLASS_FENSTER_S else None
        # Auftrag 021, 1: JEDER Plan-Satz des Kerns geht als Entwurf an Claude (vorher nur der Wendepunkt); der Kern
        # spricht ihn nur als Ersatz, wenn Claude ausfaellt oder zu spaet kommt
        wp = next((a for a in ansagen if ersetzt(a)), None)
        if wp is not None:
            ansagen = [a for a in ansagen if not ersetzt(a)]
            self._offen = None
            art = offen[0] if offen is not None else "Wendepunkt" if getattr(wp, "_kategorie", None) == "WENDEPUNKT" \
                else "Plan"
            self._starte(p, art, wp)
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
        from .sprechplan import pflicht_info
        aus = []
        for a in ansagen:
            # Auftrag 023, 3 (164809 21:16): eine Info, die einen Plan sagt ("INFO_BASIS: ... Drache erzwingen"), ist
            # ein Plan-Satz - sie geht ueber den Schiedsrichter; die Pflicht-Infos nie
            info_mit_plan = a.schluessel.startswith("kern:INFO_") and not pflicht_info(a) \
                and plan_ziel(a.text) is not None
            if (a.schluessel.startswith(NUR_INFO) and not info_mit_plan) or not a.schluessel.startswith("kern:"):
                aus.append(a)
                continue
            warnung = a.thema == "gefahr" or getattr(a, "_kategorie", None) in ("GEFAHR", "VORSICHT")
            if not warnung:
                a.text = ohne_fuellsatz(a.text)          # Auftrag 017, 0.3: "Weiter deine Top-Welle." faellt weg
                if not a.text:
                    continue
            vorher = self.schiedsrichter.aktiv
            ok, text, _ = self.schiedsrichter.pruefe(a.text, p.zeit, warnung=warnung)
            erstes_wort = (text.split(" ", 1)[0] if text else "").lower().strip(",:!")
            rueckzug = plan_ziel(text) in ("zurueck", "back") or erstes_wort in STOPP_KLEIN
            # nur ein Rueckzug ersetzt den Plan - "Rein, Gragas fast tot!" (Kill-Ruf im Kampf) nicht (024, 231200 13:30)
            if ok and warnung and rueckzug and vorher is not None and p.zeit - vorher[1] <= STOPP_S \
                    and vorher[0] not in ("back", "zurueck") and plan_ziel(text) != vorher[0]:
                # Auftrag 023, 3 (120049 14:08/14:09): die Warnung kurz nach einem anderen Plan sagt, dass sie ihn
                # ersetzt - eine Stimme, die sich korrigiert, statt zwei, die sich widersprechen
                erstes = text.split(" ", 1)[0]
                text = "Stopp – " + (text[0].lower() + text[1:] if erstes.lower().strip(",:") in STOPP_KLEIN
                                     else text)
            if ok:
                a.text = text
                aus.append(a)
                if warnung and plan_ziel(text) is not None:
                    self.plan_obj = None             # Auftrag 023, 3: die Warnung ERSETZT den Plan, keine zweite Stimme
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
        try:
            neu = self._neue_anlaesse(p, m) if m is not None and not tot else None
        except (AttributeError, TypeError):          # verkuerzte Lagen (Tests, Spielbeginn)
            neu = None
        if anlass is None and neu is not None:
            anlass = neu
        if anlass is None and not tot and m is not None:
            anlass = self._lane_anlass(p, m)
        self._war_tot, self._kills_n = tot, n
        if m is not None and m.bereich is not None:        # ohne Ort (Spielbeginn, Minimap weg) zaehlt nichts
            self._war_basis = basis
        return anlass

    def _neue_anlaesse(self, p, m) -> str | None:
        """Auftrag 021, 3 (was in den Soll-Listen aus 019 fehlte): Objective-Timer mit Aufgabe (90 s und 30 s vorher,
        beim Spawn), das Fenster nach einem gegnerischen Tod, Roam-Gefahr eines starken Laners ohne Sicht."""
        from .welt import OBJ_DE
        sr = self.schiedsrichter
        aus = None
        for o in m.objectives or []:
            spawn = round(p.zeit + (o.spawn_in or 0.0)) if not o.lebt else None
            stufe = "90" if not o.lebt and 84 <= o.spawn_in <= 92 else "30" if not o.lebt and 25 <= o.spawn_in <= 33 \
                else None
            schl = (o.schl, round(spawn / 30) if spawn else None, stufe)
            if stufe and schl not in self._obj_gesagt:
                self._obj_gesagt.add(schl)
                aus = aus or f"Objective: {OBJ_DE.get(o.schl, o.schl)} in {int(round(o.spawn_in))} Sekunden"
            if o.lebt and (o.schl, "lebt") not in self._obj_gesagt and p.zeit > 120:
                self._obj_gesagt.add((o.schl, "lebt"))
                self._obj_gesagt.discard((o.schl, "weg"))
                aus = aus or f"Objective: {OBJ_DE.get(o.schl, o.schl)} ist jetzt da"
            if not o.lebt and (o.schl, "lebt") in self._obj_gesagt:
                self._obj_gesagt.discard((o.schl, "lebt"))
        # Fenster: ein Gegner stirbt, waehrend ein Objective lebt oder bald kommt, oder zwei sind tot
        tote = {s.name for s in p.gegner() if s.tot}
        neu_tot = [s for s in p.gegner() if s.tot and s.name not in self._tote_gegner]
        self._tote_gegner = tote
        if aus is None and neu_tot and p.zeit - self._fenster_zuletzt >= 20.0:
            nah = [o for o in m.objectives or [] if o.lebt or o.spawn_in <= 60]
            if nah or len(tote) >= 2:
                self._fenster_zuletzt = p.zeit
                wer = " und ".join(s.champion for s in p.gegner() if s.tot)
                rest = min(int(s.respawn or 0) for s in p.gegner() if s.tot)
                aus = f"Fenster: {wer} tot (der erste lebt in {rest} Sekunden wieder)"
                sr.ereignis(p.zeit, f"{neu_tot[0].champion} tot ist")
        # Roam-Gefahr: ein gegnerischer Laner (nicht der Jungler) mit Kill in den letzten 60 s oder frisch Level 6,
        # jetzt >= 12 s ohne Sicht - nur in der Lane-Phase
        b = m.b
        if b is not None:
            for g in b.gegner:
                s = g.s
                vorher = self._starke.get(s.name + ":k"), self._starke.get(s.name + ":l")
                if vorher[0] is not None and s.kills > vorher[0]:
                    self._starke[s.name] = p.zeit
                if vorher[1] is not None and s.level >= 6 > vorher[1]:
                    self._starke[s.name] = p.zeit
                self._starke[s.name + ":k"], self._starke[s.name + ":l"] = s.kills, s.level
                if aus is not None or not m.lane_phase or s.rolle in ("JUNGLE", "") or s.tot or g.sichtbar:
                    continue
                stark_seit = self._starke.get(s.name)
                if stark_seit is None or p.zeit - stark_seit > 60 or g.seit is None or g.seit < 12:
                    continue
                if p.zeit - self._roam_gesagt.get(s.name, -1e9) < 90:
                    continue
                self._roam_gesagt[s.name] = p.zeit
                lane = {"TOP": "Top", "MIDDLE": "Mid", "BOTTOM": "Bot", "UTILITY": "Bot"}.get(s.rolle, s.rolle)
                aus = (f"Roam: {s.champion} fehlt seit {int(g.seit)} Sekunden auf der {lane}-Lane, eben "
                       + ("Level 6" if s.level >= 6 and self._starke.get(s.name + ":l6") is None else "ein Kill"))
                self._starke[s.name + ":l6"] = 1.0 if s.level >= 6 else None
        return aus

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
                # Auftrag 018, 5: mit den Zahlen des Kerns und dem Kill-Check (welt.kampf_lage)
                from .welt import kampf_lage
                k = kampf_lage(m, p)
                self._kampf_text = (f"{s.champion} kämpft {int(round(weg))} s von dir, " + k[0]) if k else \
                    (f"{s.champion} kämpft {int(round(weg))} s von dir gegen "
                     + " und ".join(g.champion for g in bei[:3]) + f", sein Leben {int(round((leben or 0) * 100))} %")
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
        # Auftrag 023, 3: doppelte Anlaesse binnen ZUSAMMEN_S werden zusammengefasst - der zweite fragt nicht neu
        # (192113 10:24/10:26: "geh zum Drachen" und zwei Sekunden spaeter "Drache zu riskant"); sein Ereignis steht
        # beim naechsten Aufruf unter SEIT DEM LETZTEN AUFRUF
        if art not in ("Respawn", "Ankunft in der Basis") and p.zeit - self._letzter_start < ZUSAMMEN_S:
            self.schiedsrichter.ereignis(p.zeit, art.split(": ", 1)[-1])
            if kern_satz is not None:                  # der Satz des Kerns selbst geht wie immer ueber den Schiedsrichter
                ok, text, _ = self.schiedsrichter.pruefe(kern_satz.text, p.zeit)
                if ok:
                    kern_satz.text = text
                    self.plan.einwerfen(kern_satz)
            return
        self._letzter_start = p.zeit
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
            ende = (f"ANLASS: Kampf in der Naehe um {uhr}: {self._kampf_text}. Sag zuerst 'Hilf' oder 'Nicht "
                    "hin', dann den Grund aus diesen Zahlen (Leben, Level, Flash, Tote, dein Weg) - und was danach "
                    "kommt. Angreifen nur, wo der KILL-CHECK es traegt; sonst helfen heisst: dazustellen, Schaden "
                    f"vom Mitspieler nehmen.{kampf_regel(self._kampf_text)}")
        elif art.startswith("Objective:"):
            ende = (f"ANLASS ({uhr}): {art.split(': ', 1)[1]}. Sag den Timer MIT Aufgabe: wer lebt, wer tot ist, wer "
                    "hingeht, was du vorher mit deiner Welle machst - oder, wenn ihr keine Prio habt, was ihr "
                    "stattdessen tauscht. Ein Satz, dann der Schritt danach. Der Timer wird immer gesagt.")
        elif art.startswith("Fenster:"):
            ende = (f"ANLASS ({uhr}): {art.split(': ', 1)[1]}. Was macht ihr mit dem Fenster (Objective, Turm, "
                    "Inhibitor) und wer - mit Uhrzeit, bis wann es offen ist? Nach vorn nur, wenn es erlaubt ist; "
                    f"sonst, was du stattdessen tust.{nichts}")
        elif art.startswith("Roam:"):
            ende = (f"ANLASS ({uhr}): {art.split(': ', 1)[1]}. Warn kurz, wohin er vermutlich geht, und was du "
                    f"jetzt tust (Welle, Sicht, nicht zu weit vor).{nichts}")
        elif art == "Plan":
            ende = (f"ANLASS ({uhr}): der Coach will den Plan setzen (ENTWURF unten). Stimmt er, sag ihn als Kette "
                    "(Schritt, danach, Grund); ist es derselbe Plan wie der aktive, antworte NICHTS; ist er falsch, "
                    "sag den besseren.")
        else:
            ende = (f"ANLASS: Wendepunkt ({art}) um {uhr}. Nenn den naechsten Schritt und den danach, mit Grund"
                    + (" - bei einem Back im selben Satz Kauf und Ziel." if kette else "."))
        t0 = time.monotonic()
        wiederholt = [False]

        def einwerfen(a) -> bool:
            # Auftrag 021, Runde 1: Timer mit Aufgabe, Fenster und Roam-Warnung sind selbst das Ereignis - der
            # Schiedsrichter liess 12 von 17 Objective-Saetzen fallen ("derselbe Plan", "ohne Lageaenderung")
            warnung = getattr(a, "_kategorie", None) in ("GEFAHR", "VORSICHT") or \
                (a.schluessel.startswith("stratege:") and art.startswith("Objective:")
                 and plan_ziel(a.text) in (None, *(z for z in ("drache", "herold", "baron", "larven")
                                                    if z in art.lower().replace("ä", "ae"))))
            ok, text, _ = self.schiedsrichter.pruefe(a.text, max(self._zeit, zeit0), warnung=warnung)
            if ok:
                # Auftrag 027, 1.2: auch der Stratege sagt nie nur, was man NICHT tun soll ("Nicht hin, Sett hat 1410
                # Leben ...", API-Nachspiel 101426) - die positive Anweisung des Kerns kommt dazu, sonst entfaellt er
                from .kern.herzschlag import negativ_allein, vorlage
                if negativ_allein(text):
                    try:
                        v = vorlage(self.kern, self.kern.m) if getattr(self.kern, "m", None) is not None else None
                    except Exception:
                        v = None
                    if not v or negativ_allein(v):
                        return False
                    text = f"{text.rstrip()} {v}"
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
            a.pruefe = self._noch_sicher(a)
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
            kurz_ = art.startswith(KURZ_ANLASS)            # Auftrag 023, 4: kurzer Prompt, kein Wissensblock
            if kurz_:
                ende += " Ein Satz, hoechstens 18 Woerter."
            vorbereitet = (self._prompt(p, "Was jetzt, und warum?", ende, entwurf, kurz=kurz_),
                           {**self._lage(p, kette), "anlass": True})     # Auftrag 023, 3: kein nacktes Nein
        except Exception as e:                              # die Lage laesst sich nicht bauen: der Kern spricht
            print(f"  Stratege: Lage nicht gebaut ({type(e).__name__}: {e})", flush=True)
            self._laeuft = False
            if kern_satz is not None:
                einwerfen(kern_satz)
            return

        def lauf() -> None:
            try:
                try:
                    text, versuche = self._frage(p, "Was jetzt, und warum?", ende, satz, vorbereitet,
                                                 self.modelle["lane" if lane else "plan"],
                                                 nochmal=art in NOCHMAL, kurz=kurz_)
                except Exception as e:
                    text, versuche = None, [{"fehler": f"{type(e).__name__}: {e}"}]
                nichts_ = any(v.get("nichts") for v in versuche)
                if nichts_ and art == "Plan":
                    entschieden.set()                    # Auftrag 021: Claude haelt den Plan - der Kern-Satz schweigt
                # Auftrag 023, 3: hat Claude geantwortet, aber nichts Gueltiges (verworfen, NICHTS), spricht der Kern
                # seinen eigenen Plan nicht daneben - nur bei einem echten Ausfall, und bei Respawn/Basis (die Kette
                # ist Pflicht). 18 von 52 Widerspruechen in 021 waren Kern-Plan gegen Claude.
                fehler_ = any(v.get("fehler") for v in versuche)
                if not fehler_ and art not in ("Respawn", "Ankunft in der Basis"):
                    entschieden.set()
                if not uebernommen[0]:
                    fallback()
                quelle = "stratege" if uebernommen[0] else "wiederholt" if wiederholt[0] else (
                    "kern" if kern_satz is not None else "nichts" if nichts_ else "still")
                if uebernommen[0] and text:
                    self._gesprochen(zeit0, text)
                    self._plan_merken(versuche, zeit0, text)
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


def kampf_regel(kampf_text: str | None) -> str:
    """Auftrag 021, 4: Kampfansagen nur mit dem Kampfrechner und nur fuer freigegebene Urteile
    (wissen/kampf_eichung.toml: klar_hinten ja, klar_vorn an Carlos' Aufnahmen nicht belegt)."""
    import tomllib
    try:
        d = tomllib.loads((Path(__file__).resolve().parent.parent / "wissen" / "kampf_eichung.toml")
                          .read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    auf = d.get("aufnahmen", {})
    t = kampf_text or ""
    if not d.get("tor") or "RECHNER" not in t:
        return ""
    if "klar hinten" in t and auf.get("klar_hinten_sprechen", False):
        return " Der RECHNER sagt klar hinten: sag 'Nicht rein' mit seinen zwei Zahlen."
    if "klar vorn" in t and auf.get("klar_vorn_sprechen", False):
        return " Der RECHNER sagt klar vorn: 'Nehmt den Kampf' mit seinen zwei Zahlen - nur, wenn nach vorn erlaubt ist."
    return (" Der RECHNER ist nicht klar genug fuer einen Befehl: nenn zwei Optionen (helfen / nicht helfen) mit je "
            "einem Grund.")


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


def _als_ereignis(text: str) -> str | None:
    """Ein Info- oder Wendepunkt-Satz als Nebensatz fuer "Jetzt, wo ...": "Teemo im oberen Fluss." -> "Teemo im oberen
    Fluss aufgetaucht ist"; "Ihr aeusserer Mid-Turm ist weg." -> "ihr aeusserer Mid-Turm weg ist"."""
    s = stratege._saetze(text)[0] if stratege._saetze(text) else text
    s = s.split(":")[0].split(",")[0].rstrip(" .!")
    m = _re.match(r"^(.*?) (ist|sind) (.*)$", s)
    if m:
        return f"{m.group(1)[:1].lower()}{m.group(1)[1:]} {m.group(3)} {m.group(2)}"
    if s.endswith(("Flash weg", "TP weg")):
        return s + " ist"
    if s.endswith("gesehen"):
        return f"{s} wurde"
    # Auftrag 024, 5.4 (231200 8:14 "Jetzt, wo Aus der Basis aufgetaucht ist: Aus der Basis: Farm Top"): nur eine
    # Sichtung ("Teemo im oberen Fluss") taucht auf - ein Satzkopf mit Praeposition oder Befehl ist kein Ereignis
    if not s or s.split()[0].lower() in KEIN_EREIGNIS_KOPF:
        return None
    return f"{s} aufgetaucht ist"


KEIN_EREIGNIS_KOPF = frozenset(("aus", "in", "im", "nach", "vor", "bei", "zur", "zum", "zu", "auf", "mit", "jetzt",
                                "los", "back", "geh", "farm", "kauf", "crash", "bleib", "halte", "warte", "zurück",
                                "raus", "du", "dein", "deine", "noch", "danach", "dann", "erst"))
