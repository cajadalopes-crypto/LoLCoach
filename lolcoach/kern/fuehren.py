"""Fuehren (Buch 11): was danach kommt, Wendepunkte, neue Informationen (FENSTER), Vorschau und Optionen.

- `danach(kern, m)` (Kapitel 3): die beste Handlung, wenn die jetzige erledigt ist. Projektion auf die Kandidaten
  dieses Takts - ihr Weg ab dem Ziel der jetzigen Handlung, die Zeitleiste fortgeschrieben (was bis dahin spawnt,
  wer bis dahin lebt), dein Gold nach dem Gewinn. Wird nicht gespielt, nur gesagt und angezeigt.
- `Wendepunkte` (Kapitel 4): Struktur faellt, Objective faellt (egal wer), Kill in <= wendepunkt_kill_radius um dich
  oder dein Ziel, Basis verlassen. Danach kommt der naechste Plan sofort - mit dem, was passiert ist, vorn.
- `Fenster` (Kapitel 4): neue Informationen, die eine Option oeffnen - der Satz kommt nur, wenn der Plan wechselt.
- Saetze: WENDEPUNKT, VORSCHAU, FENSTER, Optionen (Kapitel 4, Form und Wortgrenzen aus [fuehren]).
"""
from __future__ import annotations

from ..bewertung import WEGFAKTOR, abstand
from .handlung import Handlung

# was "danach" nie ist: Bleiben, Rueckzug, Kampf-Rufe - und was vom ungeeichten Modell abhaengt (Entscheidung 2)
NIE_DANACH = frozenset(("FARMEN", "HALTEN", "STAPELN", "WELLE_HALTEN", "ZURUECK", "RAUS", "REIN", "DREHEN",
                        "ANNEHMEN", "HALTEN_UNTER_TURM", "BESTREITEN", "TP_SPIEL", "ABGEBEN_TAUSCHEN"))
BACK_ARTEN = frozenset(("BACK_JETZT", "WELLE_REIN_UND_BACK"))
OBJ_ZUM = {"drache": "zum Drachen", "baron": "zum Baron", "herold": "zum Herold", "larven": "zu den Larven",
           "aeltester": "zum Ältesten"}
OBJ_WORT = {"drache": "Drache", "baron": "Baron", "herold": "Herold", "larven": "Larven", "aeltester": "Ältester"}


def ziel_pos(h: Handlung):
    return h.daten.get("ziel_pos") or (h.ziel.pos if h.ziel is not None else None)


def stumm(h: Handlung) -> bool:
    """Eine Handlung, die der Coach nicht sagt (ungeeichtes Modell, Entscheidung 2 / Pruefung c, R2)."""
    from . import MODELL_STUMM
    return h.art in MODELL_STUMM or bool(h.daten.get("modell_stumm"))


def kurz(h: Handlung | None) -> str:
    """Die Handlung in wenigen Woertern, fuer "danach", Optionen und Antworten: "zum Drachen", "back", "Top-Welle",
    "auf den inneren Top-Turm", "zu deinem Team"."""
    if h is None:
        return ""
    if h.art in BACK_ARTEN:
        return "back"
    if h.art in ("WOHIN", "WOHIN_TP_LANE"):
        return h.daten.get("kurz") or (h.ziel.name if h.ziel else "")
    if h.art == "KAUFEN":
        w = h.daten.get("wohin")
        return f"kaufen, dann {w.daten.get('kurz')}" if w is not None and w.daten.get("kurz") else "kaufen"
    if (o := h.daten.get("objective")) and h.art not in ("DRUECKEN", "MIT_GRUPPE", "PLATTEN"):
        return OBJ_ZUM.get(o, o)
    if h.art == "ZUR_GRUPPE":
        return "zu deinem Team"
    if h.art in ("SEITENWELLE", "WELLE_KLAEREN") and h.daten.get("lane"):
        return f"{h.daten['lane']}-Welle"
    from .sprache import dativ
    if h.art == "PLATTEN" and h.ziel is not None:
        return f"Platten an {dativ(h.ziel.name)}"
    if h.art in ("DRUECKEN", "MIT_GRUPPE") and h.ziel is not None:
        return f"auf {h.ziel.name}" if h.ziel.name.startswith(("den ", "ihren ")) else h.ziel.name
    return h.ziel.name if h.ziel is not None else h.art.lower()


def danach(kern, m) -> Handlung | None:
    """Kapitel 3: die beste Handlung im projizierten Zustand nach der jetzigen - None bei GEFAHR, in KAMPF, ohne Plan
    oder wenn die jetzige kuerzer als danach_min_dauer_s dauert."""
    from . import wert
    c = kern.cfg["fuehren"]
    p = kern.fuehrer.plan
    if p is None or kern.gefahr or kern.modus.aktuell in ("KAMPF", None) or m is None or m.b is None:
        return None
    h = p.handlung
    if h.art in BACK_ARTEN or (h.art == "KAUFEN" and kern.modus.aktuell == "BASIS"):
        # nach dem Back: das Ziel fuer draussen (dieselbe Rechnung wie in der Basis, C4)
        from .modi import basis
        try:
            z = basis.wohin(m, kern.cfg, "BASIS", kern._wohin, kern._lage(m))
        except Exception:
            return None
        if h.art == "KAUFEN":
            w = h.daten.get("wohin")
            if w is not None and z is not None and z.daten.get("kurz") == w.daten.get("kurz"):
                return None          # das Ziel steht schon im Kauf-Satz
        return z if z is not None and z.satz else None
    T = max(h.dauer or 0.0, 0.0)
    if T < c["danach_min_dauer_s"]:
        return None
    start = ziel_pos(h) or m.pos
    tempo = m.mein_tempo or 345.0
    zw = wert.zeitwert(m.zeit, kern.cfg)
    beste, beste_ev = None, None
    for x in kern.kandidaten or []:
        if x is h or x.art == h.art or x.art in NIE_DANACH or stumm(x) or x.ziel is None:
            continue
        if h.ziel is not None and x.ziel.name == h.ziel.name:
            continue
        ev = x.ev
        pos = ziel_pos(x)
        if pos is not None and start is not None and x.ziel.weg is not None:
            weg_neu = abstand(start, pos) * WEGFAKTOR / tempo
            ev -= (weg_neu - x.ziel.weg) * zw          # von dort aus ist der Weg ein anderer
        # fortgeschrieben: ein Objective, das erst lange nach deiner Ankunft spawnt, ist noch keine Folge
        spawn = x.daten.get("spawn")
        if isinstance(spawn, (int, float)) and spawn - (m.zeit + T) > c["vorschau_horizont_s"]:
            continue
        if beste_ev is None or ev > beste_ev:
            beste, beste_ev = x, ev
    return beste


def text_danach(d: Handlung | None) -> str | None:
    if d is None:
        return None
    k = kurz(d)
    if d.art in ("WOHIN", "WOHIN_TP_LANE", "KAUFEN") or d.art in BACK_ARTEN:
        return k                     # Pruefung c, R6: das Ziel kurz - sein Grund stand schon im Kauf- oder Basis-Satz
    return f"{k}: {d.grund}" if d.grund else k


# --- Wendepunkte und neue Informationen -------------------------------------------------------------------------

class Beobachter:
    """Merkt sich den Stand des vorigen Takts und meldet, was sich geaendert hat (Kapitel 4)."""

    def __init__(self):
        self.strukturen: set = set()
        self.objectives: set = set()
        self.tote: set = set()
        self.modus: str | None = None
        self.basis_seit: float | None = None
        self.jungler_sichtbar: float = -1e9
        self.lane_weg: bool = False
        self.tp_top: float | None = None
        self.flash_gesehen: set = set()
        self.flash_bis: dict = {}             # Auftrag 007: Spielername -> Flash zurueck (einmal je Verbrauch)
        self.erst = True

    def takt(self, m, modus: str | None, lagebild, cfg: dict, ziel=None) -> tuple[str | None, str | None]:
        """(Wendepunkt-Text, Fenster-Text) dieses Takts - oder None."""
        if m is None or m.p is None or m.b is None:
            return None, None
        c = cfg["fuehren"]
        p, b = m.p, m.b
        wp = fe = None
        # Strukturen und Objectives (Ereignisliste der API)
        strukturen, objectives = set(), set()
        for e in p.ereignisse:
            if e.art in ("TurretKilled", "InhibKilled"):
                strukturen.add((e.id, e.art, e.team, e.daten.get(e.art, "")))
            elif e.art in ("DragonKill", "BaronKill", "HeraldKill", "HordeKill"):
                objectives.add((e.id, e.art, e.team, e.daten.get("DragonType")))
        tote = {g.champion for g in b.gegner if g.s.tot}
        if not self.erst:
            neu_s = strukturen - self.strukturen
            neu_o = objectives - self.objectives
            if neu_s:
                _, art, team, _name = sorted(neu_s)[-1]
                # Auftrag 005: mit Lane - "Euer Turm ist weg" allein klang nach Grund fuer alles Folgende; Auftrag 008,
                # A2: mit Besitzer und Lage - "Ihr aeusserer Mid-Turm ist weg" (vorher "Turm ist down")
                from ..zustand import struktur
                from .sprache import turm as turm_wort
                st = struktur(_name)
                poss = "ihr" if team == p.mein_team else "euer"
                if st is None or st.lane == "?":
                    ding = "Inhibitor" if art == "InhibKilled" else "Turm"
                    wp = f"{'Ihr' if poss == 'ihr' else 'Euer'} {ding} ist weg"
                elif art == "InhibKilled":
                    wp = f"{'Ihr' if poss == 'ihr' else 'Euer'} {st.lane}-Inhibitor ist weg"
                else:
                    stufe = "Nexus-Turm" if st.stufe == "Nexus" else st.stufe
                    w = turm_wort(poss, st.lane, stufe, "nom")
                    wp = f"{w[:1].upper()}{w[1:]} ist weg"
            elif neu_o:
                _, art, team, typ = sorted(neu_o)[-1]
                name = {"DragonKill": "Ältester" if typ == "Elder" else "Drache", "BaronKill": "Baron",
                        "HeraldKill": "Herold", "HordeKill": "Larven"}[art]
                # Auftrag 008 (Kritik, 164326 33:02: "Baron weg. Farm Top" klang nach Entwarnung - sie hatten den Buff)
                akk = {"Drache": "den Drachen", "Ältester": "den Ältesten", "Baron": "den Baron", "Herold": "den Herold",
                       "Larven": "die Larven"}[name]
                wp = f"{name} drin" if team == p.mein_team else f"Sie haben {akk}"
            elif len(tote) >= 3 and len(self.tote) < 3:
                # Buch 4, 6 (Auftrag 008; 213624 16:22-16:41: vier von ihnen tot, gesagt wurde nichts davon): der dritte
                # Tote ist ein Wendepunkt - "Drei von ihnen tot: mit der Gruppe zu ihrem Mid-Inhibitor-Turm."
                wp = f"{({3: 'Drei', 4: 'Vier'}).get(len(tote), 'Alle fünf')} von ihnen tot"
            else:
                # Kill in der Naehe von dir oder deinem Ziel
                for champ in tote - self.tote:
                    g = next((x for x in b.gegner if x.champion == champ), None)
                    ort = g.pos if g is not None else None
                    nah = ort is not None and any(q is not None and abstand(ort, q) <= c["wendepunkt_kill_radius"]
                                                  for q in (m.pos, ziel))
                    if nah:
                        wp = f"{champ} ist tot"
                        break
            # Basis verlassen (Back beendet) - gegen Flackern: mindestens 3 s in der Basis
            if self.modus == "BASIS" and modus not in ("BASIS", "TOT", None) and not m.tot \
                    and self.basis_seit is not None and m.zeit - self.basis_seit >= 3.0 and wp is None:
                wp = "Aus der Basis"
            # FENSTER: neue Information, die eine Option oeffnen kann
            j = b.jungler
            if j is not None and j.sichtbar and m.zeit - self.jungler_sichtbar > 20.0 \
                    and j.abstand is not None and j.abstand > 6000 and j.ort:
                fe = f"{j.champion} {j.ort} gesehen"
            g = b.lane
            weg = bool(g is not None and (g.s.tot or getattr(m, "lane_im_brunnen", False)))
            if g is not None and weg and not self.lane_weg:
                sek = g.s.respawn if g.s.tot else None
                fe = f"{g.champion} ist {int(sek)} Sekunden weg" if sek else f"{g.champion} ist im Brunnen"
            self.lane_weg = weg
            tp = getattr(m, "tp_gegner_top", None)
            if tp is not None and tp > 30 and (self.tp_top is None or self.tp_top <= 0):
                from . import zeitleiste
                fe = f"Ihr Top hat kein TP bis {zeitleiste._uhr(m.zeit + tp)}"
            self.tp_top = tp
            z = getattr(lagebild, "zauber", None)
            if z is not None:
                for t in z.timer.values():
                    schl = (t.name, round(t.seit))
                    if t.zauber != "SummonerFlash" or schl in self.flash_gesehen or t.zurueck <= m.zeit:
                        continue
                    self.flash_gesehen.add(schl)
                    bis = self.flash_bis.get(t.name)
                    if bis is not None and t.seit < bis - 5.0:
                        continue          # Auftrag 007: derselbe Verbrauch, schon gemeldet (164326 3:13 und 4:18)
                    g = next((x for x in b.gegner if x.s.name == t.name), None)
                    if g is not None and g.abstand is not None and g.abstand <= 2000:
                        fe = f"{g.champion} ohne Flash"
                        self.flash_bis[t.name] = t.zurueck
        else:
            self.flash_gesehen = {(t.name, round(t.seit)) for t in getattr(getattr(lagebild, "zauber", None), "timer", {}).values()}
        if b.jungler is not None and b.jungler.sichtbar:
            self.jungler_sichtbar = m.zeit
        self.strukturen, self.objectives, self.tote = strukturen, objectives, tote
        if modus == "BASIS":
            self.basis_seit = self.basis_seit if self.modus == "BASIS" and self.basis_seit is not None else m.zeit
        else:
            self.basis_seit = None if modus not in ("BASIS",) else self.basis_seit
        self.modus = modus
        self.erst = False
        return wp, fe


# --- Saetze ------------------------------------------------------------------------------------------------------

def _klein(satz: str) -> str:
    return satz[:1].lower() + satz[1:] if satz and not satz[:2].isupper() else satz


def _koerper(satz: str) -> str:
    """"Drück den inneren Top-Turm: 35 Sekunden, bis einer kommt." -> "drück den inneren Top-Turm, 35 Sekunden, bis
    einer kommt" (ohne Endpunkt, erster Doppelpunkt als Komma - der Anlass steht davor)."""
    s = satz.strip().rstrip(".")
    return s.replace(": ", ", ", 1)


def nachricht(was: str) -> bool:
    """Auftrag 005: ein Wendepunkt der anderen Seite (euer Turm weg, Drache weg) ist eine Nachricht, kein Grund - der
    Plan danach steht als eigener Satz (Kritiker R1: "Euer Turm ist weg: Drueck den inneren Top-Turm" las sich wie
    'weil')."""
    return was.startswith(("Euer ", "Zwei eurer", "Drei eurer", "Vier eurer", "Sie haben")) or was.endswith(" weg")


def verbinden(was: str, koerper: str) -> str:
    """"<Anlass>: <Plan>." - oder, bei einer Nachricht, "<Nachricht>. <Plan>."."""
    koerper = koerper.strip().rstrip(".")
    if nachricht(was):
        return f"{was}. {koerper[:1].upper()}{koerper[1:]}."
    return f"{was}: {koerper}."


def wendepunkt_satz(was: str, satz: str, danach_text: str | None, woerter: int) -> str:
    """Kapitel 4: "<Was passiert ist>: <Handlung> <Ziel>, <Grund>. Danach <danach>." - hoechstens `woerter`: zuerst
    faellt der Grund von danach, dann danach, dann der Grund der Handlung."""
    from .modi import kuerze
    koerper = _koerper(satz)
    kandidaten = []
    if danach_text and danach_text.split(":")[0].strip().lower().rstrip(".") != koerper.split(",")[0].strip().lower():
        # Auftrag 005: nie "Back. Danach back." - danach ist, was NACH dem Plan kommt
        kandidaten.append(f"{verbinden(was, koerper)} Danach {danach_text}.")
        kandidaten.append(f"{verbinden(was, koerper)} Danach {danach_text.split(':')[0]}.")
    kandidaten.append(verbinden(was, koerper))
    for k in kandidaten:
        if len(k.split()) <= woerter:
            return k
    return kuerze(f"{was}: {satz.strip()}", woerter)


def optionen_satz(a: Handlung, b: Handlung, woerter: int) -> str | None:
    """Kapitel 4: zwei Wege, die Empfehlung zuerst - "Zwei Wege: zum Drachen, dein Team ist dort. Oder Top-Welle,
    dort nimmt sie sonst niemand." Hoechstens `woerter`, sonst ohne Gruende, sonst None."""
    ka, kb = kurz(a), kurz(b)
    if not ka or not kb or ka == kb:
        return None
    for s in (f"Zwei Wege: {ka}, {a.grund}. Oder {kb}, {b.grund}.", f"Zwei Wege: {ka}, {a.grund}. Oder {kb}.",
              f"Zwei Wege: {ka}. Oder {kb}."):
        if len(s.split()) <= woerter and "None" not in s:
            return s.replace(", .", ".")
    return None


def optionen(kern) -> tuple[Handlung, Handlung] | None:
    """Die zwei besten sagbaren Handlungen, wenn sie innerhalb von optionen_abstand liegen (15 % oder 150 GE)."""
    c = kern.cfg["fuehren"]
    top = [h for h in sorted(kern.kandidaten or [], key=lambda h: -h.ev)
           if h.art not in NIE_DANACH and not stumm(h) and h.ziel is not None and h.satz]
    if len(top) < 2:
        return None
    a, b = top[0], top[1]
    abstand_ge = max(c["optionen_abstand_ge"], c["optionen_abstand_anteil"] * abs(a.ev))
    if a.ev - b.ev <= abstand_ge and kurz(a) != kurz(b):
        return a, b
    return None


def vorschau_satz(kern, m, zeitleiste: list, danach_h: Handlung | None) -> str | None:
    """Kapitel 4, VORSCHAU: ein Ereignis der Zeitleiste in <= vorschau_horizont_s, das deinen Plan aendert -
    "Drache in 80 Sekunden: bis dahin Top-Welle, dann zum Drachen." / "Rumble lebt in 20 Sekunden wieder: den inneren
    Top-Turm noch schnell, dann raus." / "Euer Baron-Buff noch 60 Sekunden: jetzt auf den Mid-Inhibitor, danach back."."""
    c = kern.cfg["fuehren"]
    p = kern.fuehrer.plan
    if p is None or m is None:
        return None
    jetzt = kurz(p.handlung)
    for e in zeitleiste:
        n = e.in_s(m.zeit)
        if n > c["vorschau_horizont_s"] or n < 10:
            continue
        if e.art == "objective" and danach_h is not None and danach_h.daten.get("objective") == e.schl and jetzt:
            # Buch 4, 5 (Auftrag 008): der Vorlauf mit Warum - "bis dahin Bot-Welle, 6 Vasallen laufen in deinen Turm"
            grund = p.handlung.grund
            mit = f"{OBJ_WORT.get(e.schl, e.schl)} in {n} Sekunden: bis dahin {jetzt}, {grund}, dann {kurz(danach_h)}."
            if grund and len(mit.split()) <= c["max_woerter_wendepunkt"]:
                return mit
            return f"{OBJ_WORT.get(e.schl, e.schl)} in {n} Sekunden: bis dahin {jetzt}, dann {kurz(danach_h)}."
        if e.art == "respawn" and p.art in ("DRUECKEN", "MIT_GRUPPE", "PLATTEN") and jetzt:
            return f"{e.schl} lebt in {n} Sekunden wieder: {jetzt} noch schnell, dann zurück."
        if e.art == "buff" and e.text.startswith("euer") and jetzt:
            return f"Euer Buff noch {n} Sekunden: jetzt {jetzt}, danach back."
    return None


def ev_teile(h: Handlung, m, cfg: dict) -> dict[str, float]:
    """Die Groessen, die den EV tragen (wert.bewerte): Nutzen (Gewinn x Erfolg + Folgewert - Kosten), Risiko
    (- p_tod x Todeskosten), Zeit (- Dauer x Zeitwert)."""
    from .wert import zeitwert
    pe = h.p_erfolg if h.p_erfolg is not None else 1.0 - h.p_tod
    return {"nutzen": pe * h.gewinn + h.folgewert - h.kosten, "risiko": -h.p_tod * (h.verlust or 0.0),
            "zeit": -h.dauer * zeitwert(m.zeit, cfg)}


def entscheidend(h: Handlung, h2: Handlung, m, cfg: dict) -> str | None:
    """Buch 4, 4 (Auftrag 008): welche Groesse die Wahl von h gegen h2 entschieden hat - gemessen, wie das Buch es will:
    ohne ihren Unterschied gerechnet kippt die Wahl. Von den kippenden die mit dem groessten Beitrag; None, wenn keine
    allein kippt (dann tragen mehrere)."""
    a, b = ev_teile(h, m, cfg), ev_teile(h2, m, cfg)
    d = h.ev - h2.ev
    beitrag = {k: a[k] - b[k] for k in a}
    kippt = {k: v for k, v in beitrag.items() if v > 0 and d - v <= 0}
    return max(kippt, key=kippt.get) if kippt else None


def _ankunft(m, name: str) -> float | None:
    g = next((x for x in (m.b.gegner if m.b is not None else []) if x.champion == name), None)
    return g.ankunft if g is not None else None


def nachteil(alt: Handlung, h: Handlung, m, cfg: dict) -> str:
    """Der konkrete Nachteil der Alternative gegen den Plan (Buch 4, 4: "Der Turm oben haette Rumble in 15 Sekunden bei
    dir") - Risiko, Weg oder Nutzen, je nachdem, was die Wahl entschied."""
    k = entscheidend(h, alt, m, cfg)
    wer = [n for n, x in (alt.daten.get("wer") or []) if x >= 0.05]
    if (k == "risiko" or (k is None and alt.p_tod - h.p_tod >= 0.1)) and wer:
        t = _ankunft(m, wer[0])
        return (f"dort wäre {wer[0]} in {max(1, int(t))} Sekunden bei dir" if t is not None and t <= 60
                else f"zu riskant, {wer[0]} kann dort sein")
    if k == "zeit" or (k is None and alt.dauer - h.dauer >= 10):
        return f"{int(max(1, alt.dauer - h.dauer))} Sekunden weiter weg"
    return "bringt weniger"


_ZUM = {"den Drachen": "zum Drachen", "den Baron": "zum Baron", "den Herold": "zum Herold", "die Larven": "zu den Larven",
        "den Ältesten": "zum Ältesten"}


def _wohin_wort(h: Handlung) -> str:
    k = kurz(h) or h.art.lower()
    k = _ZUM.get(k, k)
    return k[:1].upper() + k[1:]


def warum_satz(h: Handlung, alt: Handlung | None, m, cfg: dict) -> str:
    """WARUM (Buch 4, 4 / Buch 11, 5), zwei Saetze: die entscheidende Beobachtung, dann die Alternative mit ihrem
    konkreten Nachteil - "Drache, weil drei von ihnen tot sind. Der Turm oben haette Rumble in 15 Sekunden bei dir."."""
    kh = _wohin_wort(h)
    k = entscheidend(h, alt, m, cfg) if alt is not None else None
    zusatz = {"risiko": "dort ist es sicherer", "zeit": "es liegt näher"}.get(k)
    if h.satz:
        # der Plan-Satz selbst (mit Verb - 213624 11:35: "Auf ihren inneren Top-Turm: ..." galt als Stichwort-Antwort)
        s1 = h.satz.strip().rstrip(".!") + (f", {zusatz}" if zusatz else "")
    elif zusatz:
        s1 = f"{kh}: {zusatz}" + (f", {h.grund}" if h.grund else "")
    else:
        s1 = f"{kh}: {h.grund}" if h.grund else kh
    if alt is None:
        return s1 + "."
    return f"{s1}. {_wohin_wort(alt)}: {nachteil(alt, h, m, cfg)}."


def stumm_satz(h: Handlung) -> str:
    """Ein sonst stummer Plan (FARMEN, HALTEN) als Satz - nur nach einem Wendepunkt (Buch 11, 1: nie Leerlauf)."""
    if h.art == "FARMEN" and h.ziel is not None:
        return f"Farm {h.ziel.name}."
    return ""


def ziel_label(h: Handlung | None) -> str:
    """Das Ziel eines Plans, vergleichbar ueber Ansage und Antwort (Buch 11, 7: Widersprueche): "drachen", "top",
    "inneren top-turm", "deinem team", "back"."""
    if h is None:
        return ""
    if h.art == "KAUFEN":
        w = h.daten.get("wohin")
        return ziel_label(w) if w is not None else "kaufen"
    k = kurz(h).lower()
    for vorn in ("kaufen, dann ", "zur ", "zum ", "zu den ", "zu ", "auf den ", "auf ", "platten am ", "deine ",
                 "deinen ", "dein ", "die "):
        k = k.removeprefix(vorn)
    return k.removesuffix("-welle")


def farmen_mit_vorschau(h: Handlung, zeitleiste: list, jetzt: float, danach_text: str | None, cfg: dict) -> str:
    """Auftrag 004, Teil A 1: FARMEN wird nur mit Vorschau gesagt - "Farm Top, Drache in 70 Sekunden, dann zum
    Drachen." Ohne ein Ereignis der Zeitleiste in <= vorschau_horizont_s: "" (still, wie vorher)."""
    if h.ziel is None:
        return ""
    lane = next((w for w in ("Top", "Mid", "Bot") if w in h.ziel.name), None)
    wo = lane or h.ziel.name
    for e in zeitleiste or []:
        n = e.in_s(jetzt)
        if n > cfg["fuehren"]["vorschau_horizont_s"] or n < 5:
            continue
        if e.art == "objective":
            was = f"{OBJ_WORT.get(e.schl, e.schl)} in {n} Sekunden"
        elif e.art == "respawn":
            was = f"{e.schl} lebt in {n} Sekunden wieder"
        elif e.art == "kauf":
            was = f"{e.schl} in {n} Sekunden kaufbar"
        elif e.art == "tp":
            was = f"dein TP in {n} Sekunden"
        elif e.art in ("buff", "inhib"):
            was = f"{e.text} in {n} Sekunden"
        else:
            continue
        return f"Farm {wo}, {was}" + (f", dann {danach_text.split(':')[0]}" if danach_text else "") + "."
    return ""


def farmen_satz(h: Handlung, m, zeitleiste: list, danach_text: str | None, cfg: dict) -> str:
    """Auftrag 007, A 1 (Entscheidung zu 004_frage 1): am Wendepunkt kommt FARMEN immer als Satz - mit Grund UND dem,
    was als Naechstes kommt: ein Ereignis der Zeitleiste, der Lane-Gegner weg, die Back-Bedingung, danach."""
    s = farmen_mit_vorschau(h, zeitleiste, m.zeit, danach_text, cfg)
    if s or h.ziel is None:
        return s
    lane = next((w for w in ("Top", "Mid", "Bot") if w in h.ziel.name), None)
    wo = lane or h.ziel.name
    b = m.b
    g = b.lane if b is not None else None
    if g is not None and g.s.tot and g.s.respawn >= 10:
        return f"Farm {wo}, {g.champion} ist {int(g.s.respawn)} Sekunden weg."
    k = getattr(b, "kauf", None) if b is not None else None
    n = getattr(k, "naechstes", None) if k is not None else None
    if n and b.gold is not None:
        from .modi import _akk
        item, fehlt = n
        ziel = int((b.gold + fehlt + 49) // 50 * 50)
        return f"Farm {wo}, bei {ziel} Gold back für {_akk(item)}."
    if k is not None and getattr(k, "kaufen", None):
        return f"Farm {wo}, {k.kaufen[0]} ist schon bezahlbar: nach der Welle back."
    if danach_text:
        return f"Farm {wo}, danach {danach_text.split(':')[0]}."
    # Buch 4, 4 (Auftrag 008): die Floskel nur mit dem, wo dein Team ist
    from .sprache import team_grund
    team = team_grund(m, lane) if lane else None
    return (f"Farm {wo}: dort nimmt die Welle sonst niemand, {team}." if team
            else f"Farm {wo}, sonst läuft die Welle in deinen Turm.")


def halten_satz(m, zeitleiste: list, danach_text: str | None, cfg: dict) -> str:
    """Auftrag 007, A 1: auch ein Halte-Plan bekommt am Wendepunkt einen Satz, wenn es etwas Ehrliches zu sagen gibt -
    was danach kommt, das naechste Ereignis der Zeitleiste, oder dein Team neben dir. Sonst still (kein "Warte, gerade
    ist nichts sicher", 164326 23:41)."""
    # Kritik Runde 3 (Auftrag 007, Teil D): "Warte hier: Baron spawnt in 32 Sekunden" bei 20 % Leben, "Bleib bei
    # deinem Team" 8 s vor "Back jetzt" - ein Halte-Plan hat keinen Grund zu warten; er sagt nur, was danach kommt
    if danach_text:
        return f"{danach_text[:1].upper()}{danach_text[1:]}."
    return ""
