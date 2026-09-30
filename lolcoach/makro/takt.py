"""Der Entscheider im Takt (Stufe 4, Auftrag 034): Challenger-Gehirn + 111 Entscheidungen + Vorrang -> genau eine
Anweisung je Moment.

    e = Entscheider(hirn=gehirn.Gehirn(), sperre=kern.makro_sperre)
    anw = e.entscheide(lage, merkmale, kontext, anlass="takt", frage=False)

Ablauf je Aufruf (hoechstens einmal je Sekunde, das haelt makro/einbau.py):
1. `hirn.bewerte(merkmale, kontext)` und `hirn.lage_info` -> `lage.hirn` (Optionen, Klarheit, Siegchance, Jungler-Karte).
   Ohne Gehirn (keine Modelle, Fehler) bleibt `lage.hirn` leer - die Regeln und Rechner entscheiden allein.
2. Alle 111 Entscheidungen, deren Live-Eingaben in diesem Takt da sind (`lage.vorhanden`, wahrnehmung.EINGABEN). Fehlt
   eine Eingabe, schweigt genau diese Entscheidung - die anderen sprechen.
3. Die Sicherheits-Sperre (der alte Kern: R1, Kill-Check, Fakten, verbotene Begriffe) streicht Kommandos, die nicht
   gesagt werden duerfen. `vorrang.ordnen`: seit 035 Gefahr vorn, dann der Aktionswert des Gehirns (Ersatz: der
   feste Wert); `reihenfolge="fest"` gibt die Reihenfolge aus 032 (Gefahr, Objective-Kette, Rest).
4. Die Klarheit entscheidet die Form: Gefahr immer als Kommando; klar -> ein Kommando; geteilt -> zwei Optionen;
   unklar -> die Objective-Kette, sonst was High-Elo hier am haeufigsten tut (Z3). Nie Schweigen: feuert nichts,
   gilt die Grund-Anweisung (G0).
5. Regel aus 028: ein Planwechsel nur mit Gefahr, Event oder Frage - oder wenn der Plan erledigt ist (seine
   Entscheidung feuert nicht mehr) oder laenger als `halten_s` steht. Sonst bleibt der Plan.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from . import vorrang, wahrnehmung
from .entscheidungen import laden
from .kommando import Kommando, sek, sprechbar
from .lage import Hirn, MakroLage

HALTEN_S = 20.0            # wie kern.herzschlag.WECHSEL_S (Auftrag 028, 1): so lange braucht ein Wechsel einen Grund
LANE_DE = {"top": "Top", "mid": "Mid", "bot": "Bot"}
# Was ein Kommando fuer die anderen Entscheidungen vorhat (lage.plan): Nummern -> Schluessel
PLAN_AUS_ID = {"B1": "back", "B2": "back", "B4": "back", "W3": "back", "W2": "back", "M2": "split", "M3": None,
               "T1": "tp", "T2": "tp", "T3": "tp", "T5": "tp", "T6": "tp", "R1": "roam", "R2": "roam", "R3": "roam",
               "R4": "roam", "R9": "roam"}
AKTION_PLAN = {"Back": "back", "Split": "split", "TP": "tp", "Rotation": "unterwegs", "Unterwegs": "unterwegs"}


@dataclass
class Anweisung:
    kommando: Kommando
    form: str                         # gefahr / klar / geteilt / unklar / grund
    zweite: Kommando | None = None    # bei "geteilt"
    zeit: float = 0.0
    neu: bool = True                  # neuer Plan in diesem Takt (sonst gehalten)
    grund: str = ""                   # warum gewechselt: erster / gefahr / event / frage / erledigt / abgelaufen
    seit: float = 0.0                 # seit wann dieser Plan gilt
    gefeuert: list[str] = field(default_factory=list)
    stumm: list[str] = field(default_factory=list)      # Entscheidungen ohne Wahrnehmung in diesem Takt
    gesperrt: list[tuple[str, str]] = field(default_factory=list)   # (Nummer, Grund) - von der Sicherheits-Sperre
    fehler: list[str] = field(default_factory=list)
    alternativen: list = field(default_factory=list)   # die zwei naechstbesten freien Kommandos (Protokoll)
    ms: float = 0.0                   # Laufzeit der Entscheidung (Gehirn + 111 + Vorrang + Sperre)
    ms_hirn: float = 0.0

    @property
    def schluessel(self) -> tuple:
        """Derselbe Plan: dieselbe Entscheidung mit derselben Handlung - Zahlen darin ("Warte 8 s") zaehlen nicht."""
        k = self.kommando
        return (k.id, re.sub(r"\d+", "#", k.tu), self.zweite.id if self.zweite is not None else None)

    @property
    def voll(self) -> str:
        """Der ganze Satz "Tu X: weil Y. Danach Z." (Protokoll, Dashboard, Frage "warum")."""
        k = self.kommando
        if self.form == "geteilt" and self.zweite is not None:
            z = self.zweite
            return sprechbar(f"Zwei Optionen. {k.text} Oder: {_gross(z.tu)} – {z.weil}.")
        return k.text

    @property
    def vorlage(self) -> str:
        """Der Satz, der gesprochen wird, wenn Claude nicht formt (oder abweicht) - hoechstens max_woerter (PLAN 14,
        GEFAHR 8; wissen/kern.toml [sprechen], Auftrag 002: "redest viel zu lange ... immer zu spaet"). Gekuerzt wird
        von hinten: erst "Danach ...", dann der Grund; die Handlung bleibt immer."""
        return kurz_genug(self, max_woerter(self.form == "gefahr"))

    @property
    def kurz(self) -> str:
        """Die Erinnerung: nur die Handlung (der Grund ist gesagt)."""
        return sprechbar(f"Weiter: {_gross(self.kommando.tu)}.")


def _gross(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def max_woerter(gefahr: bool) -> int:
    try:
        from .. import wissen
        c = wissen.lade("kern")["sprechen"]
        return int(c["max_woerter_gefahr"] if gefahr else c["max_woerter"])
    except Exception:
        return 8 if gefahr else 14


def _satz(*teile: str) -> str:
    from .kommando import jetzt_statt_null
    tu, *rest = [t.strip().rstrip(".") for t in teile if t and t.strip()]
    s = _gross(tu) + ((" – " if ":" in tu else ": ") + rest[0] if rest else "") + "."
    return sprechbar(jetzt_statt_null(s))


def kurz_genug(anw: "Anweisung", n: int) -> str:
    """Der laengste der Saetze voll / Handlung + Grund / Handlung, der hoechstens n Woerter hat (sonst die Handlung)."""
    k = anw.kommando
    if anw.form == "geteilt" and anw.zweite is not None:
        z = anw.zweite
        kandidaten = [anw.voll, sprechbar(f"{_satz(k.tu, k.weil)} Oder: {_satz(z.tu)}"),
                      sprechbar(f"{_satz(k.tu)} Oder: {_satz(z.tu)}")]
    else:
        kandidaten = [k.text, _satz(k.tu, k.weil), _satz(k.tu)]
    return next((s for s in kandidaten if len(s.split()) <= n), kandidaten[-1])


def grund_kommando(lage: MakroLage) -> Kommando:
    """G0 - nie Schweigen: feuert keine Entscheidung (oder sind alle gesperrt), gilt das, was High-Elo-Spieler
    in der Lane-Phase am haeufigsten tun (Aktion 'Lane' in phase1) - an der eigenen Welle bleiben."""
    ich = lage.ich
    lane = LANE_DE.get(lage.lane or "", None)
    if not ich.lebt:
        return Kommando("G0", f"Warte {sek(ich.respawn)} auf den Respawn", "danach zählt jede Sekunde",
                        f"direkt zurück {'an die ' + lane + '-Welle' if lane else 'zu deinen Camps'}", wert=-9)
    if lane is None:
        return Kommando("G0", "Nimm deine Camps", "ohne sicheren Plan bringt dir das das meiste Gold", wert=-9)
    if ich.im_brunnen:
        return Kommando("G0", f"Zurück an die {lane}-Welle", "dort liegt dein Gold", wert=-9)
    return Kommando("G0", f"Bleib an deiner {lane}-Welle", "gerade ist nichts wichtiger als Gold und Erfahrung", wert=-9)


def sicher_zurueck(lage: MakroLage) -> Kommando:
    """Letzter Rueckfall, wenn die Sperre alles streicht (auch G0): zurueck unter den eigenen Turm."""
    return Kommando("G0", "Zurück zu deinem Turm", "gerade ist jeder Schritt nach vorn zu riskant", klasse="gefahr",
                    wert=-9)


class Entscheider:
    def __init__(self, hirn=None, sperre=None, halten_s: float = HALTEN_S, reihenfolge: str = "wert"):
        self.hirn = hirn                  # werkzeuge/challenger/gehirn.Gehirn oder eine Attrappe (bewerte, lage_info)
        self.sperre = sperre              # (Text) -> [Gruende]; leer = darf gesagt werden
        self.halten_s = halten_s
        # Auftrag 035, Teil 0: "wert" = Gefahr vorn, dann der Aktionswert des Gehirns; "fest" = Stand 032/034
        self.reihenfolge = reihenfolge if reihenfolge in vorrang.REIHENFOLGEN else "wert"
        self.aktiv: Anweisung | None = None
        self.hirn_fehler: str | None = None
        self.zeiten: list[float] = []     # ms je Entscheidung (fuer den Bericht)
        self._reg = laden()

    # --- 1. Gehirn ---------------------------------------------------------------------------------------------------

    def _hirn(self, lage: MakroLage, merkmale: dict, kontext: dict) -> float:
        if self.hirn is None:
            return 0.0
        t = time.perf_counter()
        try:
            opts = self.hirn.bewerte(merkmale, kontext=kontext)
            info = self.hirn.lage_info(merkmale)
            lage.hirn = Hirn(optionen=list(opts), siegchance=info.get("siegchance"), jungler=info.get("jungler") or {},
                             jungler_unsicher=info.get("jungler_unsicherheit"))
        except Exception as e:                 # das Gehirn darf den Takt nie mitreissen
            if self.hirn_fehler is None:
                print(f"!! Makro-Gehirn: {type(e).__name__}: {e}", flush=True)
            self.hirn_fehler = f"{type(e).__name__}: {e}"
            lage.hirn = Hirn()
        return (time.perf_counter() - t) * 1000

    def _plan_setzen(self, lage: MakroLage) -> None:
        """lage.plan: was der gehaltene Plan und die beste Option des Gehirns vorhaben (fuer W2, W7, S3, M3 ...)."""
        a = self.aktiv
        if a is not None and (s := PLAN_AUS_ID.get(a.kommando.id)):
            lage.plan[s] = True
        beste = lage.hirn.beste()
        if beste is not None and lage.hirn.klarheit in ("klar", "geteilt"):
            akt, ziel, grund = beste[0], beste[1], beste[6] or []
            if akt == "Objective" and ziel:
                lage.plan.setdefault("objective", ziel.lower())
            elif akt == "Back" and any(str(g).startswith("Back-Grund") for g in grund):
                lage.plan["back"] = True
            elif akt in AKTION_PLAN and akt != "Back":
                lage.plan[AKTION_PLAN[akt]] = True

    # --- 2./3. Entscheidungen, Sperre, Vorrang ------------------------------------------------------------------------

    def _kommandos(self, lage: MakroLage, anw: Anweisung) -> list[Kommando]:
        vorh = lage.vorhanden
        aus = []
        for id_, e in self._reg.items():
            if wahrnehmung.fehlt(e.eingaben) or (vorh is not None and not set(e.eingaben) <= vorh):
                anw.stumm.append(id_)
                continue
            try:
                k = e.pruefe(lage)
            except Exception as ex:           # eine kaputte Entscheidung darf die anderen nicht mitreissen
                anw.fehler.append(f"{id_}: {type(ex).__name__}: {ex}")
                continue
            if k is not None:
                aus.append(k)
        anw.gefeuert = [k.id for k in aus]
        return aus

    def _gesperrt(self, k: Kommando) -> list[str]:
        if self.sperre is None:
            return []
        try:
            return list(self.sperre(k.text) or [])
        except Exception:
            return []

    # --- 4. Form -----------------------------------------------------------------------------------------------------

    def _form(self, lage: MakroLage, ks: list[Kommando]) -> tuple[Kommando, str, Kommando | None]:
        erst = ks[0]
        if erst.klasse == "gefahr":
            return erst, "gefahr", None
        klarheit = lage.hirn.klarheit
        if klarheit == "geteilt":
            zweite = next((k for k in ks[1:] if k.id != erst.id and k.tu != erst.tu and k.klasse != "gefahr"), None)
            return erst, ("geteilt" if zweite is not None else "klar"), zweite
        if klarheit == "unklar":
            obj = next((k for k in ks if k.klasse == "objective"), None)
            if obj is not None:
                return obj, "klar", None
            z3 = next((k for k in ks if k.id == "Z3"), None)
            return (z3 or erst), "unklar", None
        return erst, "klar", None

    # --- Hauptweg ----------------------------------------------------------------------------------------------------

    def entscheide(self, lage: MakroLage, merkmale: dict | None = None, kontext: dict | None = None,
                   anlass: str = "takt", frage: bool = False) -> Anweisung:
        t0 = time.perf_counter()
        ms_hirn = self._hirn(lage, merkmale if merkmale is not None else {}, kontext or {})
        self._plan_setzen(lage)
        anw = Anweisung(kommando=grund_kommando(lage), form="grund", zeit=lage.zeit)
        ks = self._kommandos(lage, anw)
        if lage.ich.im_brunnen and lage.ich.lebt:
            # im eigenen Brunnen bist du sicher: Warnungen fuer draussen (Lane, Spike, fehlende Gegner) halten dort
            # keinen Plan fest - dran sind Kauf und Rueckweg (Nachspiel 035: "Shen hat seinen Spike" hielt den Brunnen)
            from dataclasses import replace
            ks = [replace(k, klasse="rest", wert=k.wert - 20.0) if k.klasse == "gefahr" and k.id != "M9" else k
                  for k in ks]            # ... sie stehen hinten an (fester Wert - 20)
        frei = []
        for k in ks:
            if g := self._gesperrt(k):
                anw.gesperrt.append((k.id, "; ".join(g)))
            else:
                frei.append(k)
        frei = vorrang.ordnen(frei, lage.hirn, self.reihenfolge)
        if frei:
            anw.kommando, anw.form, anw.zweite = self._form(lage, frei)
            # im Brunnen kommt der Kauf zuerst (Auftrag 027, Basis-Reaktion >= 95 %) - ausser eine Gefahr
            kauf = next((k for k in frei if k.id in ("B7", "B8")), None)
            if kauf is not None and anw.form != "gefahr" and (lage.ich.im_brunnen or not lage.ich.lebt):
                anw.kommando, anw.form, anw.zweite = kauf, "klar", None
        elif self._gesperrt(anw.kommando):
            anw.kommando, anw.form = sicher_zurueck(lage), "gefahr"
        anw.alternativen = [k for k in frei if k is not anw.kommando][:2]
        self._halten(anw, ks, anlass, frage)
        a = self.aktiv
        a.ms_hirn = ms_hirn
        a.ms = (time.perf_counter() - t0) * 1000
        self.zeiten.append(a.ms)
        return a

    def _halten(self, anw: Anweisung, ks: list[Kommando], anlass: str, frage: bool) -> None:
        """Regel aus 028: der Plan bleibt, ausser Gefahr, Event, Frage, Plan erledigt oder abgelaufen."""
        alt = self.aktiv
        if alt is None:
            anw.grund, anw.seit = "erster", anw.zeit
            self.aktiv = anw
            return
        if anw.schluessel == alt.schluessel:
            anw.neu, anw.seit, anw.grund = False, alt.seit, "gleich"      # derselbe Plan - Zahlen frisch
            self.aktiv = anw
            return
        erledigt = alt.kommando.id not in {k.id for k in ks} or any(
            g[0] == alt.kommando.id for g in anw.gesperrt)
        # Eine Gefahr loest einen Plan immer ab - eine andere Gefahr aber nur, wenn die alte vorbei ist (oder ein
        # Ereignis/eine Frage): sonst wechselten sich Warnungen jede Sekunde ab (Nachspiel 035, botspiel_riven_2:
        # "Zurueck zum Turm" / "Shen hat seinen Spike" / "Nicht kaempfen" im Wechsel)
        neue_gefahr = anw.form == "gefahr" and (alt.form != "gefahr" or erledigt)
        grund = ("gefahr" if neue_gefahr else "frage" if frage else "event" if anlass != "takt"
                 else "erledigt" if erledigt else "abgelaufen" if anw.zeit - alt.seit >= self.halten_s else None)
        if grund is None:
            # gehalten: der alte Plan gilt weiter - mit den Zahlen dieses Takts, wenn seine Entscheidung noch feuert
            frisch = next((k for k in ks if k.id == alt.kommando.id
                           and re.sub(r"\d+", "#", k.tu) == re.sub(r"\d+", "#", alt.kommando.tu)), None)
            if frisch is not None:
                alt.kommando = frisch
            alt.neu, alt.zeit = False, anw.zeit
            alt.gefeuert, alt.stumm, alt.gesperrt, alt.fehler = anw.gefeuert, anw.stumm, anw.gesperrt, anw.fehler
            alt.grund = "gehalten"
            return
        anw.grund, anw.seit = grund, anw.zeit
        self.aktiv = anw

    def laufzeit(self) -> dict:
        z = sorted(self.zeiten)
        if not z:
            return {}
        return {"n": len(z), "median_ms": z[len(z) // 2], "p95_ms": z[min(len(z) - 1, int(len(z) * 0.95))],
                "max_ms": z[-1]}
