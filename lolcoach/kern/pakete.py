"""Buch 15, Teile 1, 3, 4 und 5 (Auftrag 025, 2 und 3): lebendige Arbeitspakete und der Chancen-Scanner.

Ein Paket ist der aktive Plan des Kerns (`PlanFuehrer.plan`) mit dem, was ihn LEBENDIG macht: Typ, Ziel, Wert,
Budget oder Frist aus den vier Uhren, und jeden Takt die Pruefung "erledigt?" und "abbrechen?". Hoechstens ein
aktives Paket, dazu ein "danach" (kern.danach_text). Das Plan-Objekt aus 021 (Claudes stille PLAN-Zeile) haengt als
`plan_text` am Paket.

Uebergaenge (Buch 15, 1): START und ERSETZT spricht der Plan-Satz (Claude formuliert, der Kern-Satz ist der Ersatz);
MEILENSTEIN, COUNTDOWN, BUDGET_AB, ABGEBROCHEN und ERLEDIGT spricht der Kern hier sofort (<= 8 Woerter, Kategorie
PAKET: keine Sprechsperre, Vorrang wie eine Pflicht-Info). Nach ERLEDIGT, ABGEBROCHEN und BUDGET_AB ist der Plan leer -
der naechste kommt im naechsten Takt mit Grund.

Chancen-Scanner (Buch 15, 5 = Event-Abwaegung 0.3): `hilfe_kandidat` macht aus einem Mitspieler-Kampf in Reichweite
einen Kandidaten HILFE mit Wert (Kampfrechner aus 020, nie bei "klar hinten"); gewechselt wird ueber die Hysterese des
PlanFuehrers. `warum_nicht` sagt einmal kurz, warum ein sichtbarer Kampf NICHT das beste Play ist.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from ..bewertung import abstand

TYP_VON_ART = {
    "PLATTEN": "TURM", "DRUECKEN": "TURM", "MIT_GRUPPE": "TURM",
    "WELLE_REIN_UND_BACK": "WELLE", "WELLE_DRUECKEN": "WELLE", "STAPELN": "WELLE", "WELLE_KLAEREN": "WELLE",
    "SEITENWELLE": "WELLE", "UNTER_TURM_FARMEN": "WELLE", "FARMEN": "WELLE", "WELLE_UND_RAUS": "WELLE",
    "BACK_JETZT": "BACK", "KAUFEN": "KAUF",
    "HILFE": "HILFE",
    "ZUR_GRUPPE": "ROTATION", "WOHIN": "ROTATION", "WOHIN_TP_LANE": "ROTATION", "TP_SPIEL": "ROTATION",
    "NEHMEN": "OBJECTIVE", "BESTREITEN": "OBJECTIVE", "TAUSCHEN": "OBJECTIVE", "ABGEBEN_TAUSCHEN": "OBJECTIVE",
    "ANLAUFEN": "OBJECTIVE",
    "HALTEN": "WARTEN", "HALTEN_UNTER_TURM": "WARTEN", "WELLE_HALTEN": "WARTEN",
    "ZURUECK": "WARTEN", "RAUS": "WARTEN",      # Rueckzug: unter dem Turm halten, bis die Gefahr weg ist
}
VORN = frozenset(("TURM", "WELLE", "OBJECTIVE", "HILFE", "WARTEN"))   # Pakete, die ein sicheres Fenster brauchen
# ... und deren Budget der Kern mit Countdown und "Raus jetzt" fuehrt. WELLE und WARTEN nicht: auf der Lane steht der
# Lane-Gegner immer in Reichweite (Messung 025: 60-76 "Raus jetzt" je Partie) - dort sprechen die Gefahr-Regeln
BUDGET_TYPEN = frozenset(("TURM", "OBJECTIVE", "HILFE"))
LANE_ORTE = ("oben", "unten", "auf der Mid-Lane")
# 026, 4: HALTEN wird NICHT angesagt - es flackert (alle paar Sekunden neu), und sein "danach" ist genau das, wogegen
# der Kern sich entschied (Szenario 3451: "Auf ihren Mid-Inhibitor-Turm" an der Drachengrube)
HALTEN_ANSAGEN = False
SPERRE_S = 15.0            # 026: so lange ist ein abgebrochenes Ziel kein Kandidat
START_NACH_S = 1.0         # 026, 4: so lange darf der Plan-Satz (Kern oder Claude) den Start sagen, dann der Paket-Kern
WARUM_NICHT_S = 30.0       # hoechstens ein "warum nicht" je so viele Sekunden (Buch 15, 0.3: "einmal kurz")
OBJ_WORT = {"drache": "Drache", "herold": "Herold", "baron": "Baron", "larven": "Larven"}
ENDE = ("ERLEDIGT", "ABGEBROCHEN", "BUDGET_AB", "ERSETZT")


@dataclass
class Paket:
    typ: str
    art: str
    ziel: str | None
    ziel_pos: tuple | None
    wert: float
    start: float
    grund: str = ""
    frist: float | None = None           # Spielzeit, bis zu der das Paket laeuft (Budget oder Frist)
    plan_text: str | None = None         # Claudes PLAN-Zeile (021), wenn sie zu diesem Paket gehoert
    partner: str | None = None           # HILFE: wer kaempft
    obj: str | None = None               # OBJECTIVE: welches
    gesagt: bool = False                 # wurde der Start gesprochen (Plan-Satz)?
    countdowns: int = 0
    budget_start: float | None = None    # sicheres Fenster beim ersten Takt des Pakets
    fortsetzung: bool = False            # setzt das vorige Paket fort (gleiches Ziel) - kein eigener Start-Satz
    ohne_satz: bool = False              # stummer Plan ohne ehrlichen Start-Satz (HALTEN ohne "danach")
    nah_start: frozenset = frozenset()   # Gegner, die beim Start schon <= 1000 standen (kein Abbruchgrund)
    verlauf: list = field(default_factory=list)    # (Spielzeit, Uebergang, Text)
    ende: str | None = None

    def rest(self, zeit: float) -> float | None:
        return None if self.frist is None else self.frist - zeit

    def eintrag(self, zeit: float, art: str, text: str = "") -> None:
        self.verlauf.append((round(zeit, 1), art, text))
        if art in ENDE:
            self.ende = art


class PaketFuehrer:
    def __init__(self, cfg: dict | None = None):
        from .uhren import cfg as uhren_cfg
        self.c = cfg or uhren_cfg()
        self.aktiv: Paket | None = None
        self.fertig: deque = deque(maxlen=400)       # abgeschlossene Pakete (fuer Messung und Bericht)
        self._plan_id: int | None = None
        self._erledigt_id: int | None = None
        self._vorback: set = set()
        self.gesperrt: dict = {}                      # (Art, Ziel) -> bis: abgebrochene Ziele (026)
        self._gold: float | None = None
        self._warum_nicht: set = set()

    # --- je Takt ---------------------------------------------------------------------------------------------------

    def takt(self, kern, m, uhren, events: list, modus: str | None) -> list[tuple[str, str]]:
        """(Uebergang, Satz) - was der Kern jetzt sagen muss (leerer Satz: nur protokolliert)."""
        aus: list[tuple[str, str]] = []
        plan = kern.fuehrer.plan
        if modus in ("TOT", "KAMPF") or m.tot:
            # Tod und Kampf haben eigene Regeln (Buch 15, 4 Punkt 7): das Paket endet still
            self._schliessen(m.zeit, "ABGEBROCHEN", "Kampf" if modus == "KAMPF" else "Tod")
            self._plan_id = None                      # danach bekommt auch derselbe Plan wieder ein Paket
            self._gold = self._gold_jetzt(m)
            return aus
        if plan is not None and (id(plan) != self._plan_id or (self.aktiv is None and id(plan) != self._erledigt_id)):
            self._plan_id = id(plan)
            if self.aktiv is not None:
                self._schliessen(m.zeit, "ERSETZT", plan.art)
            typ = TYP_VON_ART.get(plan.art)
            z0 = plan.handlung.ziel.name if plan.handlung.ziel is not None else None
            eben = next((f for f in reversed(self.fertig) if m.zeit - (f.verlauf[-1][0] if f.verlauf else f.start) < 10.0
                         and f.art == plan.art and f.ziel == z0 and f.ende in ("ERLEDIGT", "BUDGET_AB", "ABGEBROCHEN")), None)
            if eben is not None:
                typ = None                  # eben erledigt: derselbe Plan ist kein neues Paket (kein Flackern)
            if typ is not None:
                h = plan.handlung
                z = h.ziel
                self.aktiv = Paket(typ, plan.art, z.name if z is not None else None, z.pos if z is not None else None,
                                   h.ev, m.zeit, grund=h.grund, partner=h.daten.get("partner"),
                                   obj=h.daten.get("objective"))
                self.aktiv.eintrag(m.zeit, "START", h.satz or "")
                self.aktiv.nah_start = frozenset(g.champion for g in (m.b.gegner if m.b is not None else [])
                                                 if g.sichtbar and g.abstand is not None and g.abstand <= 1000)
                # Ausnahme (026, 4): setzt es nur das vorige fort - gleiches Ziel -, braucht es keinen neuen Start-Satz
                vor = self.fertig[-1] if self.fertig else None
                self.aktiv.fortsetzung = bool(vor is not None and vor.ziel == self.aktiv.ziel and self.aktiv.ziel
                                              and m.zeit - (vor.verlauf[-1][0] if vor.verlauf else vor.start) <= 2.0)
        p = self.aktiv
        if p is None:
            self._gold = self._gold_jetzt(m)
            return aus
        if plan is not None and plan.gesagt is not None:
            p.gesagt = True
        elif plan is not None and not p.gesagt and m.zeit - p.start >= START_NACH_S and not p.fortsetzung and not p.ohne_satz:
            # Auftrag 026, 4: jeder Paket-Start wird gesagt, spaetestens 2 s nach Beginn - auch FARMEN und HALTEN, die
            # der Kern sonst schweigend hielt (025: 94 % der Zeit ein Paket, angesagt nur 55 %)
            if (s := self._start_satz(kern, plan, m)):
                plan.gesagt = m.zeit
                p.gesagt = True
                p.eintrag(m.zeit, "START_GESAGT", s)
                aus.append(("START", s))
            else:
                p.ohne_satz = True                # nichts Ehrliches zu sagen (halten_satz leer): still
        self._frist(p, m, uhren)
        ueb = self._erledigt(p, m, events) or self._abbruch(p, m, uhren, events)
        if ueb is not None:
            art, text = ueb
            p.eintrag(m.zeit, art, text)
            self.fertig.append(p)
            self.aktiv = None
            if text:
                kern.fuehrer.plan = None              # der naechste Plan kommt sofort (Buch 15, 1)
                self._plan_id = None
                if art in ("ABGEBROCHEN", "BUDGET_AB"):
                    # 026: ein abgebrochenes Ziel ist SPERRE_S lang kein Kandidat - sonst waehlte der Kern es im
                    # naechsten Takt wieder und sagte es neu an (Szenarien 3451, a4: Plan-Saetze im Kreis)
                    self.gesperrt[(p.art, p.ziel)] = m.zeit + SPERRE_S
            elif plan is not None:
                self._erledigt_id = id(plan)          # still erledigt: dieser Plan bekommt kein neues Paket
            aus.append((art, text))
        else:
            if (mst := self._meilenstein(p, m, uhren)) is not None:
                p.eintrag(m.zeit, "MEILENSTEIN", mst)
                aus.append(("MEILENSTEIN", mst))
            elif (cd := self._countdown(p, m)) is not None:
                p.eintrag(m.zeit, "COUNTDOWN", cd)
                aus.append(("COUNTDOWN", cd))
        if (vb := self._vor_back(m, uhren)) is not None:
            aus.append(("VORBACK", vb))
        if (lw := self._lane_weg(kern, m, events)) is not None:
            aus.append(("CHANCE", lw))
        self._gold = self._gold_jetzt(m)
        return [(a, t) for a, t in aus if t]

    @staticmethod
    def _lane_weg(kern, m, events: list) -> str | None:
        """Auftrag 026, 6: der Lane-Gegner ist weg oder tot (Event) - die Chance auf der Lane: vor 14:00 Platten, danach
        die Welle. Nicht, wenn die Pflicht-Info (INFO_LANE) es eben gesagt hat - dann nur einmal."""
        if not getattr(m, "lane_phase", False) or m.tot or m.b is None or getattr(m.b, "lane", None) is None:
            return None
        name = m.b.lane.champion
        e = next((e for e in events if (e.typ == "LANE_WEG" or (e.typ == "TOD" and name in e.beteiligte))
                  and name in e.beteiligte), None)
        if e is None:
            return None
        pf = getattr(kern, "pflicht", None)
        if pf is not None and m.zeit - float(getattr(pf, "lane_gesagt", -1e9) or -1e9) < 20.0:
            return None
        zuletzt = getattr(kern, "_lane_chance", None)
        if zuletzt is not None and zuletzt[0] == name and m.zeit - zuletzt[1] < 60.0:
            return None                  # einmal je Abwesenheit ("Shen tot", 18 s spaeter "Shen weg")
        try:
            kern._lane_chance = (name, m.zeit)
        except AttributeError:
            pass
        wie = "tot" if e.typ == "TOD" else "weg"
        return f"{name} {wie}: Welle rein, dann Platten." if m.zeit < 840.0 else f"{name} {wie}: Welle drücken."

    def _vor_back(self, m, u) -> str | None:
        """Auftrag 026, 1: das Gold reicht fuer ein Item, die Back-Frist der Wellen-Uhr kommt in 8-12 s - einmal je
        Frist ansagen: "In 10 Sekunden Welle rein, dann Back: pünktlich zur Kanone um 9:30." """
        p = self.aktiv
        if u is None or getattr(u, "back_spaetestens", None) is None or getattr(u, "kanone_in", None) is None \
                or not getattr(m, "lane_phase", False) or m.tot \
                or (p is not None and p.typ in ("BACK", "KAUF")) or not (u.gold_bis and u.gold_bis[1] == 0):
            return None
        from ..sonderregeln import kauft_ohne_back
        ich = getattr(getattr(m, "b", None), "ich", None)
        if ich is not None and kauft_ohne_back(ich.champion_id):
            return None                  # Auftrag 028, 6.2: Ornn kauft ohne Back - kein Back fuer Gold
        n = u.back_spaetestens - m.zeit
        schl = round(u.back_spaetestens / 10.0)
        if not 8.0 <= n <= 12.0 or schl in self._vorback:
            return None
        self._vorback.add(schl)
        k = m.zeit + u.kanone_in
        return (f"In {int(round(n))} Sekunden Welle rein, dann Back: pünktlich zur Kanone um "
                f"{int(k // 60)}:{int(k % 60):02d}.")

    @staticmethod
    def _start_satz(kern, plan, m) -> str:
        """Der Start-Satz eines stummen Plans: FARMEN mit Grund und Vorschau, HALTEN nur mit dem, was danach kommt."""
        from . import fuehren
        h = plan.handlung
        if not h.stumm:
            return ""        # die anderen sagt der Kern selbst - mit seinen Sperren (Szenarien wohin-kurz, 3451)
        rufe = getattr(kern, "_back_rufe", None)
        if rufe and m.zeit - rufe[-1] <= 30.0 and getattr(kern, "_back_recall", -1e9) < rufe[-1]:
            return ""        # kein Farm-Satz gegen ein eben gesagtes Back (Szenario 2837, wie _ansage_zum_plan)
        try:
            if h.art == "FARMEN":
                if m.p is not None and getattr(m.p, "modus", None) == "SWIFTPLAY":
                    return fuehren.stumm_satz(h)        # Swiftplay hat eigene Zeiten (Szenario swiftplay-...)
                s = fuehren.farmen_satz(h, m, kern.zeitleiste, kern.danach_text, kern.cfg)
                # ein "dann back" darin unterliegt der Back-Sperre des Kerns (Szenario back-dauerton, 164326 25:01)
                # den Back ruft der Kern selbst; der Start-Satz nennt ihn nicht (sonst vier "back" in 10 min)
                if s and "back" in s.lower().split(" ") or (s and "back." in s.lower()):
                    s = ""
                return s or fuehren.stumm_satz(h)
            if h.art in ("HALTEN", "HALTEN_UNTER_TURM", "WELLE_HALTEN") and HALTEN_ANSAGEN:
                s = fuehren.halten_satz(m, kern.zeitleiste, kern.danach_text, kern.cfg)   # nie h.satz: der stumme Halte-Plan traegt dort Rechner-Text (Szenario s23)
                if s:
                    return s
                # Buch 15, 3: WARTEN nur mit Ende - aus den Uhren: bis die Gefahr sich zeigt, oder bis die Welle da ist
                u = getattr(kern, "uhren", None)
                if u is not None and u.wer and u.t_gefahr is not None and u.t_gefahr <= 15.0:
                    return f"Halten, bis {u.wer} sich zeigt."
                if u is not None and u.kanone_in is not None and 5.0 <= u.kanone_in <= 40.0 and m.lane_hier:
                    return f"Halten, bis die Kanone kommt: {int(u.kanone_in)} Sekunden."
                return ""
            return h.satz or ""
        except Exception:
            return ""

    def plan_zeile(self, text: str | None) -> None:
        """Auftrag 025, 2: das Plan-Objekt aus 021 geht im Paket auf."""
        if self.aktiv is not None and text:
            self.aktiv.plan_text = text

    def stand(self, zeit: float) -> dict | None:
        p = self.aktiv
        if p is None:
            return None
        return {"typ": p.typ, "art": p.art, "ziel": p.ziel, "rest": None if p.frist is None else round(p.frist - zeit, 1),
                "gesagt": p.gesagt, "seit": round(p.start, 1), "fortsetzung": p.fortsetzung}

    # --- Budget, Erledigt, Abbruch ---------------------------------------------------------------------------------

    def _frist(self, p: Paket, m, u) -> None:
        if u is None:
            return
        if p.typ in BUDGET_TYPEN and u.fenster is not None:
            p.frist = m.zeit + u.fenster                 # sicheres Fenster (Gefahr-Uhr)
            if p.budget_start is None:
                p.budget_start = u.fenster
        elif p.typ == "BACK":
            p.frist = u.back_spaetestens
        elif p.typ == "OBJECTIVE" and p.obj is not None:
            o = next((x for x in m.objectives or [] if x.schl == p.obj), None)
            if o is not None and not o.lebt:
                p.frist = m.zeit + o.spawn_in + 60.0

    def _erledigt(self, p: Paket, m, events: list) -> tuple[str, str] | None:
        for e in events:
            wir = dict(e.daten).get("wir")
            if p.typ == "TURM" and e.typ in ("TURM_FAELLT", "INHIB_FAELLT") and wir:
                # mit Besitzer (Szenario a2, sprache_konkret): "ihren Top-Turm" -> "Ihr Top-Turm fällt."
                name = (p.ziel or "").replace("ihren ", "Ihr ", 1).replace("den ", "Der ", 1)
                for alt, neu in (("Ihr inneren ", "Ihr innerer "), ("Ihr äußeren ", "Ihr äußerer ")):
                    name = name.replace(alt, neu, 1)       # Nominativ: "Ihr innerer Mid-Turm fällt."
                return "ERLEDIGT", f"{name if name.startswith(('Ihr ', 'Der ')) else 'Ihr Turm'} fällt."
            if p.typ == "OBJECTIVE" and e.typ == "OBJ_GENOMMEN" and wir and (p.obj is None or e.ort == p.obj):
                return "ERLEDIGT", f"{OBJ_WORT.get(e.ort, 'Objective')} genommen."
        if p.typ == "BACK" and m.bereich == "basis_eigen":
            return "ERLEDIGT", ""                       # angekommen: der Basis-Satz des Kerns sagt den Kauf
        if p.typ == "KAUF" and (m.bereich != "basis_eigen" or (self._gold is not None and m.b.gold is not None
                                                                and m.b.gold < self._gold - 250)):
            return "ERLEDIGT", ""                       # gekauft oder unterwegs
        if p.typ == "ROTATION" and p.ziel_pos is not None and m.pos is not None and abstand(m.pos, p.ziel_pos) <= 1200:
            return "ERLEDIGT", ""
        if p.typ == "HILFE" and m.zeit - p.start >= 4.0:
            from ..welt import kampf_lage
            if kampf_lage(m, m.p) is None:
                return "ERLEDIGT", "Kampf vorbei."
        return None

    def _abbruch(self, p: Paket, m, u, events: list) -> tuple[str, str] | None:
        """Buch 15, 4: die allgemeinen Gruende (Gefahr, Leben, Ziel weg, Partner weg, Ueberzahl, Frist) und je Typ."""
        for e in events:
            wir = dict(e.daten).get("wir")
            if p.typ == "OBJECTIVE" and e.typ == "OBJ_GENOMMEN" and not wir and (p.obj is None or e.ort == p.obj):
                return "ABGEBROCHEN", f"{OBJ_WORT.get(e.ort, 'Objective')} weg: nicht hin."
            if p.partner and e.typ == "TOD" and p.partner in e.beteiligte:
                return "ABGEBROCHEN", f"{p.partner} tot: nicht mehr hin."
        # das Budget eines Vorwaerts-Pakets ist abgelaufen - nur, wenn es beim Start eins hatte (sonst waere es gar nicht
        # gewaehlt worden; die Gefahr-Regeln des Kerns sprechen dann selbst) und das Paket >= 2 s lief
        if p.typ in BUDGET_TYPEN and u is not None and u.fenster is not None and u.fenster < 0 and u.wer \
                and p.budget_start is not None and p.budget_start >= 0 and m.zeit - p.start >= 2.0:
            return "BUDGET_AB", f"Raus jetzt: {u.wer} in {int(max(1, u.t_gefahr or 1))} Sekunden."
        # ... und ohne Budget: ein Gegner steht schon da (Messung 025, Abbruch-Reaktion 71 %: Turm-Pakete, die mit
        # negativem Fenster begannen, liefen weiter, als ein Gegner auf 1000 herankam)
        # Auftrag 026, 2: nicht nur der, den die Gefahr-Uhr nennt - jeder sichtbare Gegner, der neu auf 1000 herankommt
        # (101426 29:30, 192113 25:12, 231200 12:15/16:15: es kam ein anderer als "wer")
        if p.typ in ("TURM", "OBJECTIVE") and m.zeit - p.start >= 1.0 and m.b is not None:
            da = [g for g in m.b.gegner if g.sichtbar and not g.s.tot and g.abstand is not None and g.abstand <= 1000
                  and g.champion not in p.nah_start]           # nur wer NEU herankommt
            # ... und nur, wenn ihr dort nicht klar mehr seid (213624 16:31: drei von ihnen tot, einer kam - kein Raus)
            wir = 1 + sum(1 for s, wo, *_ in m.b.mitspieler or [] if wo is not None and not s.tot and m.pos is not None
                          and abstand(wo, m.pos) <= 1500)
            sie = sum(1 for g in m.b.gegner if g.sichtbar and not g.s.tot and g.abstand is not None and g.abstand <= 1500)
            if da and sie >= wir:
                return "BUDGET_AB", f"Raus jetzt: {da[0].champion} ist da."
        if p.typ in ("OBJECTIVE", "HILFE") and p.ziel_pos is not None and m.b is not None:
            # Ueberzahl aus der Gefahr-Uhr: sichtbare am Ziel UND Unsichtbare, die vor dir dort sein koennen
            dein_weg = abstand(m.pos, p.ziel_pos) / (m.mein_tempo or 340.0) if m.pos is not None else None
            sie = sum(1 for g in m.b.gegner if not g.s.tot and (
                (g.sichtbar and g.pos is not None and abstand(g.pos, p.ziel_pos) <= 2000)
                or (not g.sichtbar and dein_weg is not None and g.pos is not None and (g.seit or 99) <= 20
                    and abstand(g.pos, p.ziel_pos) / (g.tempo or 340.0) - (g.seit or 0) <= dein_weg)))
            wir = 1 + sum(1 for s, wo, *_ in m.b.mitspieler or [] if wo is not None and not s.tot
                          and abstand(wo, p.ziel_pos) <= 2500)
            if sie >= wir + 2:
                return "ABGEBROCHEN", f"Überzahl dort ({sie} gegen {wir}): nicht hin."
        if p.typ == "HILFE" and p.partner and p.ziel_pos is not None and m.b is not None:
            # Partner in anderem Kampf: er steht jetzt weit weg vom Ort, fuer den das Paket galt
            wo = next((w for s, w, *_ in m.b.mitspieler or [] if s.champion == p.partner), None)
            if wo is not None and abstand(wo, p.ziel_pos) > 2500:
                return "ABGEBROCHEN", f"{p.partner} ist weitergezogen: nicht hin."
        return None

    def _meilenstein(self, p: Paket, m, u) -> str | None:
        """TURM: eine Platte faellt (Goldsprung am Zielturm, ohne Kill) - mit dem Rest des Budgets."""
        if p.typ != "TURM" or p.ziel_pos is None or m.pos is None or self._gold is None or m.zeit >= 840.0:
            return None
        g = self._gold_jetzt(m)
        if g is None or not (120.0 <= g - self._gold <= 400.0) or abstand(m.pos, p.ziel_pos) > 1100:
            return None
        rest = p.rest(m.zeit)
        return "Platte." + (f" Noch {int(rest)} Sekunden." if rest is not None and rest >= 3 else "")

    def _countdown(self, p: Paket, m) -> str | None:
        rest = p.rest(m.zeit)
        bei = float(self.c.get("countdown_bei_s", 5.0))
        if rest is None or p.countdowns >= int(self.c.get("countdown_max", 2)) or p.typ not in BUDGET_TYPEN:
            return None
        if bei - 1.0 < rest <= bei and not any(v[1] == "COUNTDOWN" and m.zeit - v[0] < 3.0 for v in p.verlauf):
            p.countdowns += 1
            return f"Noch {int(round(rest))} Sekunden."
        return None

    def _schliessen(self, zeit: float, art: str, grund: str) -> None:
        if self.aktiv is not None:
            self.aktiv.eintrag(zeit, art, grund)
            self.fertig.append(self.aktiv)
            self.aktiv = None

    @staticmethod
    def _gold_jetzt(m) -> float | None:
        return float(m.b.gold) if m.b is not None and m.b.gold is not None else None


# --- Chancen-Scanner (Buch 15, 5) -------------------------------------------------------------------------------------

def hilfe_kandidat(kern, m, modus: str | None, tk: float | None):
    """Ein Mitspieler kaempft, du bist in <= hilfe_weg_s dort, der Rechner (mit dir) sagt nicht "klar hinten", dein
    Leben reicht: Kandidat HILFE mit Wert (Kills x Gewinnchance gegen Todeskosten). None sonst."""
    from ..welt import kampf_lage, kampf_urteil
    from .handlung import Handlung, Ziel
    from . import wert
    from .uhren import cfg as ucfg
    if modus not in ("LANE", "UNTERWEGS", "SEITE", "GRUPPE", "OBJECTIVE") or m.b is None or m.p is None \
            or (m.leben or 0.0) < 0.5 or m.tot:
        return None
    k = kampf_auffaellig(m)
    if k is None:
        return None
    weg, freunde_namen, feinde_namen, _ = k
    if weg > float(ucfg().get("hilfe_weg_s", 8.0)) or weg < 1.5:
        return None                                    # zu weit, oder du stehst schon drin (dann ist es KAMPF)
    b = m.b
    freunde = [s for s, wo, le, _ in b.mitspieler or [] if s.champion in freunde_namen and not s.tot]
    die = [g for g in b.gegner if g.champion in feinde_namen and not g.s.tot]
    if not freunde or not die:
        return None
    u = kampf_urteil(m, m.p, freunde, {s.name: le for s, wo, le, _ in b.mitspieler or []}, die, mit_dir=True)
    if u is None or u.urteil == "klar_hinten":
        return None
    pg = max(0.05, min(0.95, (u.staerke + 1.0) / 2.0))
    partner = freunde[0].champion
    wo = next((wo for s, wo, *_ in b.mitspieler if s.champion == partner), None)
    ort = next((o for s, wo_, le, o in b.mitspieler if s.champion == partner), None) or "in der Nähe"
    gegner = " und ".join(g.champion for g in die[:2])
    danach = getattr(kern, "danach_text", None)
    satz = (f"Planwechsel: {partner} kämpft mit {gegner} {ort}, du bist in {int(round(weg))} Sekunden da: hilf."
            + (f" Danach {danach.split(':')[0]}." if danach else ""))
    h = Handlung("HILFE", Ziel("gruppe", partner, wo, weg), modus, dauer=weg + 8.0, grund=u.text(), satz=satz,
                 daten={"partner": partner, "ev_bestreiten": (pg, 300.0 * len(die), tk or wert.todeskosten(m, kern.cfg)),
                        "kampf_mit": [g.champion for g in die]})
    wert.bewerte(h, m, kern.cfg, tk)
    return h


def kampf_auffaellig(m) -> tuple[float, list, list, str] | None:
    """(dein Weg in s, Mitspieler, Gegner, Ort) eines Mitspieler-Kampfs, der ein Event ist. Laning ist keiner: in der
    Lane-Phase auf einer Lane ohne ihren Jungler (Messung 025: ~100 "Yunara kämpft" je Partie waren Bot-Laning)."""
    from ..welt import LETZTER_KAMPF, kampf_lage
    if m is None or m.p is None or m.b is None:
        return None
    lage = kampf_lage(m, m.p)
    if lage is None:
        return None
    text, weg = lage
    freunde, feinde = LETZTER_KAMPF
    ort = text.split(": ", 1)[0]
    j = m.b.jungler.champion if m.b.jungler is not None else None
    if m.lane_phase and ort in LANE_ORTE and j not in feinde:
        return None
    return weg, list(freunde), list(feinde), ort


GRUPPEN_ZIELE = ("gruppe", "hilfe")
GRUPPEN_ARTEN = frozenset(("ZUR_GRUPPE", "MIT_GRUPPE", "HILFE", "ANNEHMEN", "REIN"))


def eine_stimme_blockt(kern, m, namen: list) -> bool:
    """Auftrag 026, 5: "X kämpft: nicht hin" widerspricht nie dem aktiven Plan - weder dem des Kerns (zur Gruppe, mit
    der Gruppe, hilf) noch dem, den Claude in den letzten 45 s gesagt hat (120049 24:08 "geh zu Lee Sin", 24:26 "Lee
    Sin kämpft: nicht hin"). Kippen darf der Plan nur ueber das Paket (Planwechsel mit "Jetzt, wo ...")."""
    pl = kern.fuehrer.plan
    if pl is not None and pl.art in GRUPPEN_ARTEN:
        return True
    ms = getattr(kern, "makro_stratege", None)
    sr = getattr(ms, "schiedsrichter", None)
    a = getattr(sr, "aktiv", None)
    if a is not None and m.zeit - a[1] <= 45.0:
        text = a[2] or ""
        if a[0] in GRUPPEN_ZIELE or any(n and n in text for n in namen) \
                or any(w in text.lower() for w in ("zum team", "zu deinem team", "hilf", "kämpf", "gruppe")):
            return True
    return False


def warum_nicht(kern, m, modus: str | None, fuehrer: PaketFuehrer) -> str | None:
    """Buch 15, 0.3: ein sichtbarer Kampf eines Mitspielers ist NICHT das Paket - einmal kurz der entscheidende Grund,
    hoechstens einer je WARUM_NICHT_S."""
    if modus not in ("LANE", "UNTERWEGS", "SEITE", "GRUPPE", "OBJECTIVE") or m.p is None or m.b is None:
        return None
    p = fuehrer.aktiv
    if p is not None and p.typ == "HILFE":
        return None
    k = kampf_auffaellig(m)
    if k is None:
        return None
    weg, freunde, feinde, _ = k
    if eine_stimme_blockt(kern, m, freunde + feinde):
        return None
    # eine echte Chance (HILFE waere moeglich) wird immer begruendet, ein ferner Kampf hoechstens je WARUM_NICHT_S
    chance = weg <= 8.0 and (m.leben or 0.0) >= 0.5 and hilfe_kandidat(kern, m, modus, None) is not None
    if chance:
        # erst, wenn der PlanFuehrer HILFE 2 s lang nicht genommen hat - sonst "nicht hin" und gleich "hilf"
        seit = getattr(fuehrer, "_chance_seit", None)
        if seit is None:
            fuehrer._chance_seit = m.zeit
        if seit is None or m.zeit - seit < 2.0:
            return None
    else:
        fuehrer._chance_seit = None
    if not chance and m.zeit - getattr(fuehrer, "_warum_zuletzt", -1e9) < WARUM_NICHT_S:
        return None
    schl = (tuple(sorted(freunde)), tuple(sorted(feinde)), int(m.zeit // 60))
    if schl in fuehrer._warum_nicht or weg > 20.0 or not freunde:
        return None
    from .uhren import cfg as ucfg
    fuehrer._warum_nicht.add(schl)
    fuehrer._warum_zuletzt = m.zeit
    # hoechstens 8 Woerter (Szenario 2631, max_woerter): Name, "kämpft: nicht hin", der eine Grund
    if weg > float(ucfg().get("hilfe_weg_s", 8.0)):
        grund = f"{int(round(weg))} Sekunden weg"
    elif (m.leben or 0.0) < 0.5:
        grund = f"dein Leben {int(round((m.leben or 0) * 100))} Prozent"
    elif hilfe_kandidat(kern, m, modus, None) is None:
        grund = "Rechner klar hinten"
    else:
        # 026, 7: der Plan beim Namen (025: "dein Plan bringt mehr" zaehlten die Kritiker als Fuellsatz)
        ziel = p.ziel if p is not None and p.ziel and len(p.ziel.split()) <= 3 else None
        grund = f"{ziel[:1].upper()}{ziel[1:]} bringt mehr" if ziel else "dein Plan bringt mehr"
    return f"{freunde[0]} kämpft: nicht hin, {grund}."
