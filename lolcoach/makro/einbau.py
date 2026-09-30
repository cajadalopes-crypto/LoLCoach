"""Der Einbau (Stufe 4, Auftrag 034): der Coach entscheidet mit dem Challenger-Gehirn, nicht mehr mit den alten Regeln.

    coach = MakroCoach(kern)                   # von kern.Kern in der Stellung "makro" (--kern makro, Standard)
    ansagen = coach.takt(p, b, lagebild, m)    # je Takt des Coaches (live 4/s) - entschieden wird hoechstens 1/s

Je Takt:
1. `LageBau` fuellt die `MakroLage` aus API, Minimap, HUD, Chat und den Lesern aus 033 (makro/live.py).
2. `Entscheider`: Gehirn + 111 Entscheidungen + Vorrang -> genau eine Anweisung; Planwechsel nur mit Grund
   (makro/takt.py). Die Sicherheits-Sperre ist der alte Kern (`kern.makro_sperre`: R1, Kill-Check, Fakten,
   verbotene Begriffe).
3. Sprechen: eine neue Anweisung wird gesagt - Gefahr sofort als Vorlage, sonst formt Claude den Satz
   (makro/stimme.py) bis `frist_s`, sonst die Vorlage. Budget wie der alte Kern (kern/sprechen.Sprecher.platz:
   abstand_s, max_je_minute); Gefahr und ein Wechsel aus einem Ereignis sind frei. Steht der Plan und war es
   `erinnern_s` still, eine kurze Erinnerung - nie Schweigen.
4. Protokoll je Entscheidung (`<stamm>_makro.jsonl`): Anweisung, Form, Grund des Wechsels, gefeuert, stumm
   (fehlende Wahrnehmung), gesperrt, Laufzeit.

Schalter in wissen/kern.toml [makro_gehirn]. Ohne Modelle (daten/ fehlt) oder ohne lightgbm laeuft alles ohne Gehirn:
die Regeln und Rechner entscheiden allein (gemeldet einmal im Log).
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

from ..regeln import HINWEIS, SOFORT, WICHTIG, Ansage
from .live import LageBau, luecken
from .stimme import Stimme
from .takt import Entscheider

WURZEL = Path(__file__).resolve().parents[2]
GEHIRN_PY = WURZEL / "werkzeuge" / "challenger" / "gehirn.py"
STANDARD = {"takt_s": 1.0, "start_s": 45.0, "erinnern_s": 25.0, "halten_s": 20.0, "claude": True, "frist_s": 2.0,
            "modell": "schnell", "wendepunkt_abstand_s": 8.0, "reihenfolge": "wert", "wiederholen_s": 30.0,
            "still_s": 3.5, "still_radius": 120.0}
PRIO = {"GEFAHR": SOFORT, "WENDEPUNKT": WICHTIG, "PLAN": WICHTIG, "STILL": WICHTIG, "ERINNERUNG": HINWEIS}
# STILL (Stillstand, 027) ist budgetfrei wie PAKET_STILL; die Ansage laeuft ueber _sprechen/_ansage wie ein Plan
BACK_IDS = ("B1", "B2", "B4", "B5", "W3")      # Back-Rufe: danach steht Carlos im Recall-Kanal (nicht "still")
KAUF_IDS = ("B7", "B8")


def konfig() -> dict:
    try:
        from .. import wissen
        return {**STANDARD, **wissen.lade("kern").get("makro_gehirn", {})}
    except Exception:
        return dict(STANDARD)


def gehirn_laden():
    """Das Challenger-Gehirn (werkzeuge/challenger/gehirn.py, Modelle in daten/challenger/modelle). None, wenn es
    fehlt - dann entscheiden die Regeln und Rechner allein. LOLCOACH_MAKRO_OHNE_GEHIRN=1 schaltet es aus."""
    if os.environ.get("LOLCOACH_MAKRO_OHNE_GEHIRN") == "1":
        return None
    try:
        spec = importlib.util.spec_from_file_location("challenger_gehirn", GEHIRN_PY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.Gehirn()
    except Exception as e:
        print(f"Makro-Gehirn nicht geladen ({type(e).__name__}: {str(e)[:120]}) - Regeln und Rechner allein",
              flush=True)
        return None


class MakroCoach:
    def __init__(self, kern=None, hirn="laden", frage=None, ablage: Path | None = None, cfg: dict | None = None):
        self.kern = kern
        self.cfg = {**STANDARD, **(cfg or konfig())}
        self.hirn = gehirn_laden() if hirn == "laden" else hirn
        self.bau = LageBau()
        self.entscheider = Entscheider(hirn=self.hirn, sperre=getattr(kern, "makro_sperre", None),
                                       halten_s=float(self.cfg["halten_s"]),
                                       reihenfolge=os.environ.get("LOLCOACH_MAKRO_REIHENFOLGE") or
                                       str(self.cfg["reihenfolge"]))
        if frage is None and os.environ.get("LOLCOACH_MAKRO_STIMME") == "stub":
            frage = stimme_stub                # Nachspiel (035, Teil 1): der Weg ueber die Stimme ohne Claude
        self.stimme = Stimme(frage=frage if self.cfg.get("claude", True) else None, frist_s=float(self.cfg["frist_s"]),
                             modell=str(self.cfg["modell"]))
        from ..kern.sprechen import Sprecher
        try:
            self.budget = Sprecher(kern.cfg if kern is not None else _kern_cfg())
        except Exception:
            self.budget = None
        self.lage = None
        self.anweisung = None
        self.verworfen = 0                # Plan-Ansagen, die der Sprechplan verwarf und die erneut kamen
        self.protokoll: list[dict] = []
        self.gesagt: list[dict] = []      # je abgegebene Ansage {zeit, ansage, id, kategorie, quelle} (wie im Protokoll)
        self._entschieden = -1e9
        self._gesprochen = -1e9
        self._wendepunkt = -1e9
        self._frage = False
        self._offen: list[tuple] = []     # (Auftrag, Kategorie, Anweisung)
        self._wartet = None               # Anweisung, die auf Budget wartet
        self._gesagt_schl = None          # Schluessel der zuletzt gesprochenen Anweisung
        self._erinnert = 0                # so oft wurde derselbe Plan schon erinnert
        self._id_zuletzt: dict[str, float] = {}      # Nummer -> zuletzt gesagt (Wiederholsperre, 035)
        self._steht: tuple[float, tuple] | None = None   # (seit, Ort) - Carlos steht (027: Stillstand-Reaktion)
        self._still_gesagt = False
        self._letzte_ansage: Ansage | None = None     # die zuletzt abgegebene Plan-Ansage (kam sie an?)
        self._datei = None
        if ablage is not None:
            try:
                self._datei = open(ablage, "a", encoding="utf-8")
            except OSError:
                self._datei = None

    # --- je Takt -----------------------------------------------------------------------------------------------------

    def takt(self, p, b=None, lagebild=None, m=None, gesagt: list | None = None) -> list[Ansage]:
        if p is None or p.ich is None:
            return []
        gesagt = gesagt if gesagt is not None else self._transport_gesagt()
        zeit = float(p.zeit)
        self._verworfen(zeit)
        aus = self._fertige(zeit)
        if zeit - self._entschieden < float(self.cfg["takt_s"]) and not self._frage:
            return aus
        self._entschieden = zeit
        lage, merk = self.bau.bauen(p, b, lagebild, m)
        frage, self._frage = self._frage, False
        anw = self.entscheider.entscheide(lage, merk, self.bau.kontext(lage), self.bau.anlass, frage=frage)
        self.lage, self.anweisung = lage, anw
        self._protokollieren(anw, lage)
        if zeit < float(self.cfg["start_s"]):
            return aus                     # vor dem Spielbeginn (Brunnen, Einkauf) spricht der Entscheider nicht
        kurz = anw.grund not in ("event", "frage") \
            and zeit - self._id_zuletzt.get(anw.kommando.id, -1e9) < float(self.cfg["wiederholen_s"])
        # Wiederholsperre (Nachspiel 035: "Shen hat seinen Spike" fuenfmal in einer Minute): dieselbe Entscheidung hat
        # Carlos eben gehoert - kommt sie ohne Ereignis oder Frage wieder, nur kurz ("Weiter: ...")
        if self._im_kampf():
            # Buch 17: Mikro (Kampf) macht Carlos selbst; Buch 7: im Kampf nur kurze Rufe. Der Entscheider schweigt,
            # ausser einer Gefahr - und die nur als Handlung, hoechstens 5 Woerter. Der Plan kommt nach dem Kampf.
            if anw.form == "gefahr" and anw.schluessel != self._gesagt_schl and len(anw.kommando.tu.split()) <= 5:
                self._gesagt_schl = anw.schluessel
                from .kommando import sprechbar
                aus.append(self._ansage(anw, sprechbar(anw.kommando.tu[:1].upper() + anw.kommando.tu[1:] + "."),
                                        "GEFAHR", zeit, "vorlage:kampf"))
            return aus
        steht = self._stillstand(lage, zeit, gesagt)       # Carlos steht und hat seit dem keine Anweisung (027)
        wartet = self._wartet is not None and self._wartet.schluessel == anw.schluessel
        if anw.schluessel != self._gesagt_schl and not wartet:
            kategorie = ("GEFAHR" if anw.form == "gefahr" else
                         "WENDEPUNKT" if anw.grund in ("event", "frage") and
                         zeit - self._wendepunkt >= float(self.cfg["wendepunkt_abstand_s"]) else
                         "STILL" if steht else "PLAN")
            if kategorie == "PLAN" and not self._platz(zeit, gesagt):
                self._wartet = anw         # Budget voll: gesagt, sobald Platz ist - wenn der Plan dann noch gilt
                return aus
            self._wartet = None
            if kurz:
                self._gesagt_schl = anw.schluessel
                aus.append(self._ansage(anw, anw.kurz, "ERINNERUNG" if kategorie != "GEFAHR" else "GEFAHR", zeit,
                                        "vorlage:wiederholung"))
            else:
                aus += self._sprechen(anw, kategorie, zeit, p)
        elif wartet and (steht or self._platz(zeit, gesagt)):
            self._wartet = None            # steht er, wartet der Plan nicht mehr aufs Budget
            aus += self._sprechen(anw, "STILL" if steht else "PLAN", zeit, p)
        elif steht:
            from .kommando import sprechbar
            k = anw.kommando
            los = sprechbar(f"Los: {k.tu[:1].upper()}{k.tu[1:]}.")
            if any(x["ansage"] == los and zeit - x["zeit"] < 12.0 for x in self.gesagt[-4:]):
                los = anw.vorlage          # dasselbe "Los" eben gesagt - der Sprechplan verwuerfe es als Doppel
            aus.append(self._ansage(anw, los, "STILL", zeit, "vorlage:stillstand"))
        elif zeit - self._gesprochen >= self._erinnern_s() and not self._offen and self._platz(zeit, gesagt) \
                and self._still(zeit, gesagt):
            self._erinnert += 1
            aus.append(self._ansage(anw, anw.kurz, "ERINNERUNG", zeit, "vorlage:erinnerung"))
        if steht and aus:
            self._still_gesagt = True
        return aus

    def _erinnern_s(self) -> float:
        """Nie Schweigen: nach erinnern_s Stille die kurze Erinnerung. (034 verdoppelte den Abstand je Erinnerung -
        das Nachspiel 035 gab Luecken bis 78 s; das Tor verlangt <= 35 s.)"""
        return float(self.cfg["erinnern_s"])

    def _stillstand(self, lage, zeit: float, gesagt: list) -> bool:
        """Auftrag 027, Stillstand-Reaktion (Tor >= 95 %): steht Carlos still_s am selben Fleck und kam seit er steht
        keine Anweisung, bekommt er seine Anweisung sofort ("Los: ..."). Nicht im Tod, nicht in der Gefahr (die
        Warnung ist die Anweisung), nicht im Recall-Kanal nach einem Back-Ruf (16 s), nicht beim Einkauf (10 s nach
        der Kauf-Anweisung). Budgetfrei wie 027 (PAKET_STILL)."""
        from ..bewertung import abstand
        ich = lage.ich if lage is not None else None
        if ich is None or not ich.lebt or ich.pos is None:
            self._steht = None
            return False
        if self._steht is None or abstand(self._steht[1], ich.pos) > float(self.cfg["still_radius"]):
            self._steht, self._still_gesagt = (zeit, ich.pos), False
            return False
        seit = self._steht[0]
        if self._still_gesagt or zeit - seit < float(self.cfg["still_s"]) or self.anweisung is None or self._offen:
            return False
        back = max((self._id_zuletzt.get(i, -1e9) for i in BACK_IDS), default=-1e9)
        kauf = max((self._id_zuletzt.get(i, -1e9) for i in KAUF_IDS), default=-1e9)
        if zeit - back <= 16.0 or (ich.im_brunnen and zeit - kauf <= 10.0):
            return False
        # seit er steht, kam schon eine Anweisung (die Wiederholungen des Sprechplans zaehlen mit)
        return not any(a.gesprochen is not None and a.gesprochen >= seit - 1.5 for a in gesagt[-6:])

    def _verworfen(self, zeit: float) -> None:
        """Hat der Sprechplan die letzte Plan-Ansage verworfen (Sprech-Tor, Doppel, Back-Sperre aus 028, zu alt)? Dann
        gilt der Plan als nicht gesagt und wird erneut abgegeben - sonst hoerte Carlos den neuen Plan nie."""
        a = self._letzte_ansage
        if a is None or a.gesprochen is not None or zeit - a.zeit <= a.gueltig + 2.0:
            return
        self._letzte_ansage = None
        if self._id_zuletzt.get(a._makro["id"]) == a.zeit:
            self._id_zuletzt.pop(a._makro["id"], None)      # nie gehoert: keine Wiederholsperre
        aktiv = self.entscheider.aktiv
        if aktiv is not None and aktiv.schluessel == self._gesagt_schl:
            self._gesagt_schl = None
            self.verworfen += 1

    def _im_kampf(self) -> bool:
        """Carlos kaempft selbst (Modus KAMPF des alten Kerns, Buch 7)."""
        modus = getattr(getattr(self.kern, "modus", None), "aktuell", None)
        return modus == "KAMPF"

    def _transport_gesagt(self) -> list:
        t = getattr(self.kern, "transport", None)
        return list(getattr(t, "gesagt", []) or [])

    def _platz(self, zeit: float, gesagt: list) -> bool:
        return True if self.budget is None else self.budget.platz(zeit, gesagt)

    def _still(self, zeit: float, gesagt: list) -> bool:
        """Nie Schweigen heisst nicht Dauerreden: erinnert wird nur, wenn so lange NICHTS gesagt wurde."""
        letzte = next((a.gesprochen for a in reversed(gesagt) if a.gesprochen is not None), None)
        return letzte is None or zeit - letzte >= self._erinnern_s()

    def _sprechen(self, anw, kategorie: str, zeit: float, p) -> list[Ansage]:
        namen = {s.champion for s in p.spieler}
        auftrag = self.stimme.formen(anw, namen)
        self._gesagt_schl = anw.schluessel
        self._erinnert = 0
        if kategorie == "WENDEPUNKT":
            self._wendepunkt = zeit
        self._offen.append((auftrag, kategorie, anw))
        return self._fertige(zeit)

    def _fertige(self, zeit: float) -> list[Ansage]:
        """Formulierungen, die fertig sind (oder deren Frist um ist) - als Ansage, wenn ihr Plan noch gilt."""
        aus, offen = [], []
        for auftrag, kategorie, anw in self._offen:
            if not auftrag.fertig:
                offen.append((auftrag, kategorie, anw))
                continue
            aktiv = self.entscheider.aktiv
            if aktiv is None or aktiv.schluessel != anw.schluessel:
                continue                   # ueberholt, bevor der Satz fertig war
            text, quelle = auftrag.ergebnis()
            self.stimme.zaehlen(quelle)
            aus.append(self._ansage(anw, text, kategorie, zeit, quelle))
        self._offen = offen
        return aus

    def _ansage(self, anw, text: str, kategorie: str, zeit: float, quelle: str) -> Ansage:
        schl = anw.schluessel
        a = Ansage(text, PRIO[kategorie], f"kern:MAKRO_{anw.kommando.id}", zeit=zeit,
                   gueltig=5.0 if kategorie == "GEFAHR" else 8.0, sperre=0.0,
                   thema={"GEFAHR": "gefahr", "WENDEPUNKT": "wendepunkt"}.get(kategorie, ""),
                   pruefe=lambda: self.entscheider.aktiv is not None and self.entscheider.aktiv.schluessel == schl,
                   unterbrechbar=kategorie == "ERINNERUNG")
        # sprechplan._ein_plan (Regel 028): jeder Wechsel, den der Entscheider zulaesst, hat seinen Grund schon
        # (Gefahr, Event, Frage, erledigt, abgelaufen) - `_mit_grund` sagt das herzschlag.wechsel_grund. Die
        # Kategorie bleibt die echte (Kennzahlen zaehlen WENDEPUNKT gesondert, Auftrag 035).
        a._kategorie = kategorie
        # "abgelaufen" (der Plan stand 20 s) ist kein Grund im Sinne von 028 - kommt die Ansage binnen WECHSEL_S nach
        # dem letzten Plan-Satz (etwa einer Erinnerung), haelt der Sprechplan sie zurueck, und sie kommt erneut
        a._mit_grund = kategorie != "ERINNERUNG" and anw.grund in ("erster", "gefahr", "event", "frage", "erledigt")
        a._makro = {"id": anw.kommando.id, "form": anw.form, "quelle": quelle, "grund": anw.grund,
                    "kategorie": kategorie}
        if kategorie != "ERINNERUNG":
            self._letzte_ansage = a
        self._gesprochen = zeit
        if kategorie not in ("ERINNERUNG", "STILL") and quelle != "vorlage:wiederholung":
            self._id_zuletzt[anw.kommando.id] = zeit
        zeile = {"zeit": round(zeit, 1), "ansage": text, "id": anw.kommando.id, "kategorie": kategorie,
                 "quelle": quelle}
        self.gesagt.append(zeile)
        self._schreiben(zeile)
        return a

    # --- Fragen (Antwort zuerst, dann der Plan - Auftrag 028) ----------------------------------------------------------

    def frage_gestellt(self) -> None:
        """Carlos fragt: der naechste Takt entscheidet sofort und darf den Plan wechseln (Regel 028)."""
        self._frage = True

    def plan_satz(self) -> str | None:
        a = self.entscheider.aktiv
        return None if a is None else a.vorlage

    def beantworte(self, frage: str, p=None, lagebild=None) -> dict | None:
        """Fragen nach dem Plan beantwortet der Entscheider selbst (JETZT, SOLL_ICH, ENTWEDER, DANACH, WARUM, LAGE,
        RISIKO). Andere Absichten (Timer, Wo, Kauf, Notiz ...) liefern die Fakten des alten Wegs; `mit_plan` haengt
        dann den Plan an. None: der alte Weg (bzw. Claude) antwortet."""
        from ..kern.fragen import absicht
        self.frage_gestellt()
        a = absicht(frage)
        anw = self.entscheider.aktiv
        if anw is None:
            return None
        k = anw.kommando
        text = None
        if a in ("JETZT", "SOLL_ICH", "ENTWEDER"):
            text = anw.voll                # gefragt: der ganze Satz mit Grund und danach
        elif a == "DANACH":
            text = (f"Danach {k.danach}." if k.danach else "Danach entscheide ich neu, sobald sich etwas ändert.") \
                + f" Jetzt: {_gross(k.tu)}."
        elif a == "WARUM":
            alt = anw.zweite.tu if anw.zweite is not None else None
            text = f"Weil {k.weil}." + (f" Die andere Option wäre {alt}." if alt else "") + f" Also: {_gross(k.tu)}."
        elif a == "LAGE" and self.lage is not None:
            text = f"{self._stand_satz(p)} {anw.vorlage}"
        elif a == "RISIKO" and self.lage is not None:
            fehlen = [g.champion for g in self.lage.unbekannt(15)]
            wer = (f"Unbekannt sind {', '.join(fehlen[:-1]) + ' und ' + fehlen[-1] if len(fehlen) > 1 else fehlen[0]}."
                   if fehlen else "Alle Gegner sind gerade bekannt.")
            text = f"{wer} {anw.vorlage}"
        if text is None:
            return None
        return {"text": text.replace("..", "."), "absicht": a, "ziel": k.id, "quelle": "makro"}

    def mit_plan(self, antwort: str | None, absicht: str | None = None) -> str | None:
        """Erst die Antwort, dann der Plan (Auftrag 028) - nicht bei einer Notiz."""
        if not antwort or absicht in ("NOTIZ", "COACH") or (plan := self.plan_satz()) is None:
            return antwort
        if plan.split(":")[0].lower() in antwort.lower():
            return antwort
        return f"{antwort.rstrip()} Plan: {plan}"

    def _stand_satz(self, p) -> str:
        if p is None:
            return ""
        from ..zustand import gegenteam
        wir, die = p.mein_team, gegenteam(p.mein_team)
        sc = self.lage.hirn.siegchance if self.lage is not None else None
        s = f"Kills {p.kills(wir)} zu {p.kills(die)}, Drachen {len(p.drachen(wir))} zu {len(p.drachen(die))}."
        return s + (f" Ihr steht bei etwa {int(round(sc * 100))} Prozent." if sc is not None else "")

    def kontext_zeilen(self) -> list[str]:
        """Fuer Claude (kern.kontext): der entschiedene Plan und die Alternativen - Claude aendert ihn nicht."""
        a = self.entscheider.aktiv
        if a is None:
            return []
        k = a.kommando
        z = [f"PLAN (vom Coach entschieden, nicht aendern): {a.voll}"]
        if k.danach:
            z.append(f"DANACH: {k.danach}")
        if a.zweite is not None:
            z.append(f"ZWEITE OPTION: {a.zweite.text}")
        return z

    # --- Protokoll ---------------------------------------------------------------------------------------------------

    def _protokollieren(self, anw, lage) -> None:
        zeile = {"zeit": round(lage.zeit, 1), "id": anw.kommando.id, "form": anw.form, "text": anw.voll,
                 "neu": anw.neu, "grund": anw.grund, "klarheit": lage.hirn.klarheit,
                 "hirn": [o[:2] + (o[2],) for o in lage.hirn.optionen[:3]], "gefeuert": anw.gefeuert,
                 "gesperrt": anw.gesperrt, "fehlt": luecken(lage), "stumm": self._stumm_live(anw),
                 "ms": round(anw.ms, 2),
                 "ms_hirn": round(anw.ms_hirn, 2)}
        if anw.fehler:
            zeile["fehler"] = anw.fehler
        self.protokoll.append(zeile)
        if len(self.protokoll) > 4000:
            del self.protokoll[:1000]
        self._schreiben(zeile)

    def _stumm_live(self, anw) -> list[str]:
        """Entscheidungen, die in diesem Takt schweigen, weil eine Live-Eingabe fehlt - ohne die sechs, die immer
        schweigen (unzuverlaessig, 033). Auftrag 035, Teil 1: wie oft schweigt eine Entscheidung wegen Wahrnehmung?"""
        from . import wahrnehmung
        reg = self.entscheider._reg
        return [i for i in anw.stumm if i in reg and not wahrnehmung.fehlt(reg[i].eingaben)]

    def _schreiben(self, zeile: dict) -> None:
        """Eine Zeile nach <stamm>_makro.jsonl: je Entscheidung (id, form, ms ...) und je Ansage (ansage, quelle)."""
        if self._datei is not None:
            try:
                self._datei.write(json.dumps(zeile, ensure_ascii=False, default=str) + "\n")
                self._datei.flush()
            except (OSError, ValueError):
                pass

    def schliessen(self) -> None:
        if self._datei is not None:
            try:
                self._datei.close()
            except OSError:
                pass
            self._datei = None


def _gross(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def stimme_stub(prompt: str, **_) -> str:
    """Stub fuer Claude als Stimme (Nachspiel, Sparprotokoll): gibt die Vorlage aus den Fakten zurueck - prueft den
    Weg (Auftrag, Frist, Treue-Pruefung), nicht Claudes Formulierung (die misst die Abo-/API-Runde)."""
    for z in prompt.splitlines():
        if z.startswith("VORLAGE"):
            return z.split(":", 1)[1].strip()
    return ""


def _kern_cfg() -> dict:
    from ..kern import konfig as kk
    return kk()
