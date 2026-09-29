"""Claude als Makro-Stratege im Live-Coach (Auftrag 015, Teil B aus 014).

Der Kern rechnet, warnt und liefert die Fakten; der Stratege (Claude ueber das Abo, `stratege.STRATEGE_SYSTEM`)
formuliert das Makro:
  B1  Fragen: jede echte Frage (JETZT, DANACH, WARUM, ENTWEDER, SOLL_ICH, RISIKO, AUGE, COACH, GEWISSHEIT, OFFEN)
      geht an den Strategen, Satz fuer Satz an die Stimme. Faktfragen (TIMER, WO, LAGE, KAUF), KLAEREN und Notizen
      bleiben beim Kern. Die Korrektur "die Welle ist leer" setzt der Kern vorher (Auftrag 012).
  B2  Wendepunkte (Kern-Satz WENDEPUNKT, Respawn, Ankunft in der Basis, zwei Kills in 10 s): der Stratege ersetzt den
      Plan-Satz des Kerns. Kommt sein erster gueltiger Satz nicht in `erster_satz_max_s`, spricht der Kern.
  B3  Leerlauf ab `leerlauf_ab_s`: `leerlauf_s` ohne Plan-Satz und ohne Warnung - "Was jetzt, und warum?",
      hoechstens einmal je `leerlauf_s`.
  B4  Die Wellen-Saetze des Kerns (WELLE_DRUECKEN) nur noch, wenn der Stratege aus ist oder ausgefallen.
  B6  Jeder Aufruf mit allen Versuchen und verworfenen Saetzen samt Grund in `<aufnahme>_stratege.jsonl`.
Warnungen des Kerns gehen immer vor: der Sprechplan wirft in KAMPF und <= 10 s nach einer Gefahr nichts ein, und
Stratege-Saetze sind WICHTIG, nie SOFORT. Jeder Satz geht durch `stratege.pruefe`; verworfen wird einmal neu gefragt,
mit dem Grund, danach gilt der Kern.

Auftrag 016 (Carlos' Pflichtenheft aus 133448): Leerlauf ab 1:30 nach 35 s, in der Lane-Phase als Wellen- und
Lane-Tipp ("Lane"); neuer Anlass "Kampf in der Naehe" (ein Mitspieler kaempft <= 6 s von dir, sofort gefragt); nach
der Basis-Ankunft und bei jedem Back die Kette im ersten Satz (Kauf und Ziel, sonst verworfen); ein Kontroll-Auge
hoechstens einmal je Back, nach Carlos' Nein 5 min gar nicht.

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


def claude_strom(prompt: str, bei_satz, system: str, timeout: float) -> str:
    """Der echte Weg: Claude ueber das Abo, gestreamt, mit vorgehaltenem Prozess (wie `antworten.mit_claude`)."""
    from . import llm
    return llm.frage_strom(prompt, bei_satz, system=system, modell="sonnet", timeout=timeout, aufwand="low",
                           nachladen=True)


class AufzeichnungsStub:
    """Fuers Nachspielen (B5): kein Abo - jede Anfrage wird mitgeschrieben, die Antwort ist ein fester, gueltiger Satz
    (oder die naechste aus `antworten`). So laufen die Stratege-Wege in Szenarien und Protokollen ohne Claude."""

    def __init__(self, antworten: list[str] | None = None):
        self.anfragen: list[str] = []
        self.antworten = list(antworten or [])

    def __call__(self, prompt: str, bei_satz, system: str, timeout: float) -> str:
        self.anfragen.append(prompt)
        text = self.antworten.pop(0) if self.antworten else "Bleib nah an deinem Team und warte auf den nächsten Plan."
        for s in stratege._saetze(text):
            bei_satz(s)
        return text


class MakroStratege:
    def __init__(self, kern, plan, gehirn=None, frage_fn=None, cfg: dict | None = None, ablage: Path | None = None,
                 synchron: bool = False, aktiv: bool | None = None):
        c = {**_cfg(), **(cfg or {})}
        self.kern, self.plan, self.gehirn = kern, plan, gehirn
        self.frage_fn = frage_fn or claude_strom
        import os
        if os.environ.get("LOLCOACH_STRATEGE_AUSFALL"):     # Generalprobe: Abo-Ausfall nachstellen (Auftrag 015, B5)
            def ausfall(*_):
                time.sleep(float(os.environ["LOLCOACH_STRATEGE_AUSFALL"]))
                raise RuntimeError("Ausfall nachgestellt")
            self.frage_fn = ausfall
        self.aktiv = bool(c.get("aktiv", True)) if aktiv is None else aktiv
        self.erster_max = float(c.get("erster_satz_max_s", 4.0))
        # Auftrag 016: im Leerlauf wartet kein Kern-Satz auf seinen Platz - der Stratege darf laenger brauchen
        self.leerlauf_erster_max = float(c.get("leerlauf_erster_satz_max_s", 8.0))
        self.ausfall_s = float(c.get("ausfall_s", 30.0))
        self.pause_ausfall = float(c.get("pause_nach_ausfall_s", 120.0))
        self.leerlauf_ab = float(c.get("leerlauf_ab_s", 90.0))
        self.leerlauf_s = float(c.get("leerlauf_s", 35.0))
        self.kampf_nah_s = float(c.get("kampf_nah_s", 6.0))
        self.kampf_abstand_s = float(c.get("kampf_abstand_s", 30.0))
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
        self._offen: tuple[str, float] | None = None    # ein Anlass wartet auf den Plan-Satz des Kerns
        self._n = 0
        # Auftrag 016: Kampf in der Naehe (1.4), Kontroll-Auge hoechstens einmal je Back (5)
        self._mit_leben: dict[str, list] = {}           # Mitspieler -> [(Zeit, Leben)] der letzten Sekunden
        self._kampf_zuletzt = -1e9
        self._kampf_text: str | None = None
        self._back_nr = 0
        self._auge_back = -1

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

    def _prompt(self, p, anlass: str, ende: str) -> str:
        kern = self.kern
        lage = kern.kontext() or ""
        if self.gehirn is not None:
            inhalt = self.gehirn.kontext(anlass, p, lage)
        else:
            inhalt = f"LAGE JETZT:\n{lage}"
        if (kopf := kern.kopfzeile()):
            inhalt = f"{kopf}\n\n{inhalt}"
        inhalt += f"\n\nKANDIDATEN DES COACHS (gerechnet, keine Vorgabe):\n{kandidaten_text(kern)}"
        eigene = [(t, s) for t, s in self.verlauf if self._zeit - t <= 60.0][-2:]
        if eigene:
            inhalt += "\n\nDEINE LETZTEN SAETZE (hoechstens 60 s alt): " + " | ".join(
                f"{int(t // 60)}:{int(t % 60):02d} „{s}“" for t, s in eigene)
        if (auge := self._auge_grund()):
            inhalt += f"\n\nKONTROLL-AUGE: nicht vorschlagen ({auge})."
        return f"{inhalt}\n\n{ende}"

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
        """Ein Aufruf: jeder Satz wird geprueft, sobald er fertig ist; gueltige gehen an `bei_satz` (hoechstens
        stratege.LAENGE_HOECHSTENS Woerter). Ist der erste verworfen, gilt der ganze Versuch als verworfen."""
        t0 = time.monotonic()
        v = {"text": "", "gruende": [], "erster_s": None, "ende_s": None, "fehler": None, "verworfen": []}
        gut: list[str] = []
        woerter = [0]
        erster_verworfen = [False]
        halb = [""]

        def satz(s: str, ende: bool = False) -> None:
            s = " ".join(f"{halb[0]} {s}".split())
            halb[0] = ""
            if not s or erster_verworfen[0]:
                return
            # llm.frage_strom schickt den ersten Teilsatz schon am Komma: eine Kette ("Back jetzt: Axiombogen, dann zu
            # Yorick") wird erst am Satzende geprueft (Nachspiel 133448, Auftrag 016: 14 Ketten am Komma verworfen)
            if not ende and s.endswith((",", ";", ":", "–", "-")) and (
                    stratege.back_ruf(s) or (not gut and lage.get("kette_pflicht"))):
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
            if v["erster_s"] is None:
                v["erster_s"] = time.monotonic() - t0
            if bei_satz is not None:
                bei_satz(s)
        try:
            self.frage_fn(prompt, satz, stratege.STRATEGE_SYSTEM, self.ausfall_s)
        except Exception as e:                            # Abo-Fehler, Zeitueberschreitung: still weiter mit dem Kern
            v["fehler"] = f"{type(e).__name__}: {e}"
        if halb[0] and not v["fehler"]:
            satz("", ende=True)                          # ein gehaltener Teilsatz ohne Fortsetzung
        v["ende_s"] = time.monotonic() - t0
        v["text"] = " ".join(gut)
        if not gut and not v["gruende"] and not v["fehler"]:
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
        if not a["text"] and a["gruende"]:
            weg = a["verworfen"][0]["satz"] if a["verworfen"] else ""
            b = self._versuch(prompt + f"\n\nDein Vorschlag „{weg}“ wurde verworfen: {'; '.join(a['gruende'])}. "
                              "Sag es neu, ohne das.", lage, bei_satz)
            versuche.append(b)
            if b["fehler"]:
                self._ausfall(b["fehler"])
                return None, versuche
            if b["text"]:
                return b["text"], versuche
            return None, versuche
        return a["text"] or None, versuche

    # --- B1: Fragen --------------------------------------------------------------------------------------------------

    def antworte(self, frage: str, absicht: str | None, p, bei_satz=None) -> str | None:
        """Blockierend (Sprechtasten-Faden): die Antwort des Strategen oder None (dann der Kern)."""
        if not self.bereit() or (absicht or "OFFEN") not in STRATEGE_ABSICHTEN or p is None:
            return None
        self._zeit = p.zeit
        kette = bool(stratege.BACK_WORT.search(frage) or _re.search(r"kauf|was (mach|tu)|und dann|danach|plan", frage,
                                                                     _re.I))
        ende = f"Frage des Spielers: {frage}" + (
            "\nSag die Kette: den naechsten Schritt und den danach (bei Back oder Kauf: was, dann wohin, warum)."
            if kette else "")
        text, versuche = self._frage(p, frage, ende, bei_satz, (self._prompt(p, frage, ende), self._lage(p)))
        self._schreibe({"zeit": p.zeit, "art": "frage", "frage": frage, "absicht": absicht,
                        "quelle": "stratege" if text else "kern", "text": text, "versuche": versuche})
        if text:
            self._gesprochen(p.zeit, text)
        return text

    # --- B2/B3/B4: im Takt ---------------------------------------------------------------------------------------------

    def bearbeite(self, ansagen: list, p, lagebild=None) -> list:
        """Vor plan.neu: Wellen-Saetze weg (B4), ein Wendepunkt-Satz des Kerns geht an den Strategen (B2), Anlaesse
        ohne Kern-Satz und der Leerlauf (B3) fragen ihn. Gibt die Ansagen zurueck, die der Sprechplan jetzt bekommt."""
        if p is None or not p.ich:
            return ansagen
        self._zeit = p.zeit
        anlass = self._anlass(p)
        if not self.bereit():
            return ansagen
        ansagen = [a for a in ansagen if a.schluessel != "kern:WELLE_DRUECKEN"]
        m = self.kern.m
        modus = getattr(getattr(self.kern, "modus", None), "aktuell", None)
        if self._laeuft or modus in ("KAMPF", "TOT", None) or getattr(self.kern, "gefahr", False) \
                or (m is not None and m.tot):
            return ansagen
        if anlass == "Kampf in der Nähe":
            self._starte(p, anlass, None)                   # Auftrag 016, 1.4: sofort, ohne auf den Kern zu warten
            return ansagen
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
            return ansagen
        plan_satz = any(a.schluessel.startswith("kern:") and getattr(a, "_kategorie", None) in PLAN_KATEGORIEN
                        for a in ansagen)
        if self._offen is not None and offen is None:
            # kein Kern-Satz im Fenster: der Stratege allein - nur, wenn seit ANLASS_RUHE_S nichts Planendes kam
            art = self._offen[0]
            self._offen = None
            if not plan_satz and p.zeit - self._zuletzt_plan() >= ANLASS_RUHE_S:
                self._starte(p, art, None)
        elif p.zeit >= self.leerlauf_ab and not plan_satz and p.zeit - self._letzter_leerlauf >= self.leerlauf_s \
                and p.zeit - self._zuletzt_plan() >= self.leerlauf_s:
            self._letzter_leerlauf = p.zeit
            self._starte(p, "Lane" if m is not None and m.lane_phase and modus == "LANE" else "Leerlauf", None)
        return ansagen

    def _anlass(self, p) -> str | None:
        """Respawn, Ankunft in der Basis, zwei Kills in 10 s (der Kern-Wendepunkt kommt als Satz)."""
        tot = bool(p.ich.tot)
        m = self.kern.m
        basis = m is not None and m.bereich == "basis_eigen"
        n = len(p.kills_von("ChampionKill"))
        anlass = None
        if self._kills_n is not None and n > self._kills_n:
            self._kills += [p.zeit] * (n - self._kills_n)
        self._kills = [t for t in self._kills if p.zeit - t <= 10.0]
        if len(self._kills) >= 2:
            anlass, self._kills = "zwei Kills in 10 s", []
        if self._war_tot and not tot:
            anlass = "Respawn"
        elif self._war_basis is False and basis and not tot and p.zeit >= 90.0:
            anlass = "Ankunft in der Basis"
        if basis and self._war_basis is False:
            self._back_nr += 1                              # Auftrag 016, 5: ein neuer Back
        if anlass is None and not tot and (k := self._kampf_nah(p)) is not None:
            anlass = k
        self._war_tot, self._kills_n = tot, n
        if m is not None and m.bereich is not None:        # ohne Ort (Spielbeginn, Minimap weg) zaehlt nichts
            self._war_basis = basis
        return anlass

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
        """Der Kern-Satz fuer einen Leerlauf, falls der Stratege zu spaet kommt oder verworfen wird: sein Plan mit
        Grund (bei einem Back mit Kette)."""
        try:
            from .kern.fragen import satz
            pl = self.kern.fuehrer.plan
            m = self.kern.m
            if m is None:
                return None
            text = satz(pl.handlung) if pl is not None and not pl.handlung.stumm else ""
            if not text:
                text = self._welle_satz(m)               # ohne Plan: der Wellenstand mit seiner Folge
            if not text:
                return None
            if stratege.back_ruf(text):
                text = self.kern._mit_kette(text, m)
        except Exception:
            return None
        a = Ansage(text, WICHTIG, f"kern:{pl.art if pl is not None else 'WELLE'}", zeit=p.zeit, gueltig=8.0, sperre=0.0)
        a._kategorie = "PLAN"
        return a

    def _welle_satz(self, m) -> str | None:
        """Auftrag 016, 3: ein Wellen-Satz aus dem Kern, wenn sonst nichts da ist ("Deine Top-Welle: 3 gegen 6, sie
        laeuft zu dir - farm sie am Turm.") - nach vorn nur ohne R1."""
        w = m.welle
        if w is None or w.unsere is None:
            return None
        vorn = not self.kern.vorn()["verboten"] and not getattr(self.kern, "gefahr", False)
        zahl = f"{w.unsere} gegen {w.ihre}" if w.ihre is not None else f"{w.unsere} eigene Vasallen"
        folge = {"ZU_DIR": "sie läuft zu dir, farm sie am Turm", "GROSS_ZU_DIR": "sie läuft zu dir, farm sie am Turm",
                 "GECRASHT_BEI_DIR": "sie liegt an deinem Turm, farm sie dort",
                 "ZU_IHM": "sie läuft zu ihm" + (", drück nach" if vorn else ", bleib hinter ihr"),
                 "GROSS_ZU_IHM": "sie läuft zu ihm" + (", drück sie in seinen Turm" if vorn else ", bleib hinter ihr"),
                 "GECRASHT_BEI_IHM": "sie ist an seinem Turm, jetzt ist Zeit für einen Back oder einen Ausflug",
                 "MITTE": "sie steht in der Mitte, farm sie dort"}.get(w.zustand)
        return f"Deine {w.lane}-Welle: {zahl}, {folge}." if folge else None

    def _starte(self, p, art: str, kern_satz) -> None:
        """B2/B3: fragt den Strategen; sein erster gueltiger Satz muss in erster_max da sein, sonst spricht der Kern-Satz
        (falls es einen gibt). Gueltige Saetze gehen einzeln per plan.einwerfen in den Sprechplan."""
        self._laeuft = True
        self._n += 1
        nr = self._n
        zeit0 = p.zeit
        entschieden = threading.Event()
        uebernommen = [False]
        frist = self.leerlauf_erster_max if art in ("Leerlauf", "Lane") else self.erster_max
        if kern_satz is None and art != "Kampf in der Nähe":
            kern_satz = self._kern_ersatz(p)            # Auftrag 016, 6.3: nie laenger still, auch wenn Claude ausfaellt
        uhr = f"{int(p.zeit // 60)}:{int(p.zeit % 60):02d}"
        kette = art == "Ankunft in der Basis" or (kern_satz is not None and stratege.back_ruf(kern_satz.text))
        # Auftrag 016, 2 und 3: je Anlass die Aufgabe - Ketten statt Einzelbefehle, in der Lane ein Wellen-Tipp
        if art == "Lane":
            ende = (f"ANLASS: Lane-Phase um {uhr}, seit einer Weile still. Gib einen Wellen- und Lane-Tipp mit Grund aus "
                    "der Lage (EIGENE WELLE, LANE-GEGNER, Jungler) - z. B. Welle rausdruecken, weil der Gegner fehlt; ein "
                    "1 gegen 1 suchen; Welle freezen; 'die Welle laeuft zu dir, weil ...' - und was danach kommt.")
        elif art == "Leerlauf":
            ende = f"ANLASS: seit einer Weile kein Plan-Satz ({uhr}). Was jetzt, und was danach, und warum?"
        elif art == "Ankunft in der Basis":
            ende = (f"ANLASS: Ankunft in der Basis um {uhr}. Sag die ganze Kette in EINEM Satz: was du jetzt kaufst "
                    "(passend zu Gold und freien Plaetzen, siehe KAUF), dann wohin, und warum.")
        elif art == "Kampf in der Nähe":
            ende = (f"ANLASS: Kampf in der Naehe um {uhr}: {self._kampf_text}. Hin und helfen oder nicht? Mit Grund "
                    "(dein Leben, wer dort ist, wer fehlt) - und was danach kommt.")
        else:
            ende = (f"ANLASS: Wendepunkt ({art}) um {uhr}. Nenn den naechsten Schritt und den danach, mit Grund"
                    + (" - bei einem Back im selben Satz Kauf und Ziel." if kette else "."))
        teile = [0]
        t0 = time.monotonic()

        def satz(s: str) -> None:
            with self._schloss:
                if not uebernommen[0]:
                    if entschieden.is_set() or time.monotonic() - t0 > frist:
                        return                               # zu spaet: der Kern-Satz spricht
                    uebernommen[0] = True
                    entschieden.set()
            teile[0] += 1
            # der Sprechplan nimmt bei gleichem Rang die neueste zuerst: spaetere Teile etwas "aelter", damit die
            # Reihenfolge haelt (Generalprobe 29.09., 24:09: Teil 3 kam vor Teil 2)
            a = Ansage(s, WICHTIG, f"stratege:{art}:{nr}:{teile[0]}", zeit=max(self._zeit, zeit0) - 0.01 * teile[0],
                       gueltig=12.0, sperre=0.0)
            a._kategorie = "STRATEGE"
            self.plan.einwerfen(a)

        def fallback() -> None:
            with self._schloss:
                if uebernommen[0] or entschieden.is_set():
                    return
                entschieden.set()
            if kern_satz is not None:
                kern_satz.zeit = max(kern_satz.zeit, self._zeit)
                self.plan.einwerfen(kern_satz)

        try:
            vorbereitet = (self._prompt(p, "Was jetzt, und warum?", ende), self._lage(p, kette))
        except Exception as e:                              # die Lage laesst sich nicht bauen: der Kern spricht
            print(f"  Stratege: Lage nicht gebaut ({type(e).__name__}: {e})", flush=True)
            self._laeuft = False
            if kern_satz is not None:
                self.plan.einwerfen(kern_satz)
            return

        def lauf() -> None:
            try:
                try:
                    text, versuche = self._frage(p, "Was jetzt, und warum?", ende, satz, vorbereitet)
                except Exception as e:
                    text, versuche = None, [{"fehler": f"{type(e).__name__}: {e}"}]
                if not uebernommen[0]:
                    fallback()
                quelle = "stratege" if uebernommen[0] else ("kern" if kern_satz is not None else "still")
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
