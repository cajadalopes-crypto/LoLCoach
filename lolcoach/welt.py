"""Das Lagebild (Buch 14, Schritt A.1/A.2; Auftrag 019): EINE Quelle fuer Kern und Claude, je Takt aus den bestehenden
Modulen gebaut (Bewertung, Lagebild, Kartenlage, Zeitleiste, Kaufplan, Teamplan).

`bauen(kern, p)` gibt ein `Welt`-Objekt (Daten), `text(welt, seit)` den kompakten Text fuer Claude:
  - feste Reihenfolge (DU, PLAN, VORN, KAUF, SPIELER, KARTE, TIMER, STAERKE, SEIT DEM LETZTEN AUFRUF), damit der
    Zwischenspeicher der API den stabilen Anfang wiederfindet,
  - eindeutige Formen: "jetzt sichtbar ..." oder "zuletzt gesehen vor N s ..., jetzt unbekannt, vermutlich ...",
  - hoechstens ~1500 Tokens (gemessen: `tokens`).
Der Kern darf es lesen; umgebaut wird er erst in Schritt C.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

ROLLE_DE = {"TOP": "Top", "JUNGLE": "Jungle", "MIDDLE": "Mid", "BOTTOM": "ADC", "UTILITY": "Support"}
ROLLE_LANE = {"TOP": "oben", "MIDDLE": "in der Mitte", "BOTTOM": "unten", "UTILITY": "unten"}
STUFE_DE = {"aussen": "äußerer", "innen": "innerer", "Inhib": "Inhibitor-", "Nexus": "Nexus-"}
OBJ_DE = {"drache": "Drache", "baron": "Baron", "herold": "Herold", "larven": "Larven", "aeltester": "Ältester"}
SEIT_S = 30.0


def _uhr(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


GRUBE_VON = {"herold": "oben", "baron": "oben", "larven": "oben", "drache": "unten", "aeltester": "unten"}


KAMPF_BEI = 1200.0           # ein Gegner so nah an einem Mitspieler: dort wird gekaempft
KAMPF_RUND = 1500.0          # wer so nah an der Mitte steht, gehoert zum Kampf


def kampf_lage(m, p) -> tuple[str, float] | None:
    """Auftrag 018, 5 (183125 26:15, Anlass I6): der Kampf eines Mitspielers mit den Zahlen, die der Kern exakt hat -
    wer dort lebt, Leben und Level, Flash, Tote, dein Weg und Leben, der Kill-Check deines Combos auf die Gegner dort.
    (Text, dein Weg in s) oder None."""
    from .bewertung import WEGFAKTOR, abstand
    b = m.b if m is not None else None
    if b is None or b.pos is None or p is None:
        return None
    feinde = [g for g in b.gegner if g.sichtbar and not g.s.tot and g.pos is not None]
    freunde = [(s, wo, le, ort) for s, wo, le, ort in (b.mitspieler or []) if not s.tot and wo is not None]
    mitte = next(((wo, ort) for s, wo, le, ort in freunde if any(abstand(g.pos, wo) <= KAMPF_BEI for g in feinde)), None)
    if mitte is None:
        return None
    wo0, ort = mitte
    wir = [(s, le) for s, wo, le, _ in freunde if abstand(wo, wo0) <= KAMPF_RUND]
    die = [g for g in feinde if abstand(g.pos, wo0) <= KAMPF_RUND]
    weg = abstand(b.pos, wo0) * WEGFAKTOR / (m.mein_tempo or 340.0)
    pct = lambda x: "?" if x is None else f"{int(round(x * 100))} %"
    ihr = ", ".join(f"{s.champion} {pct(le)} L{s.level}"
                    + (" Ult bereit" if m.ult_mitspieler.get(s.name) else "") for s, le in wir)
    sie = ", ".join(f"{g.champion} {pct(g.leben)} L{g.s.level}"
                    + (f" Flash weg noch {int(g.flash)} s" if g.flash else "") for g in die)
    tote = [s.champion for s in p.gegner() if s.tot]
    from .stratege import kill_jetzt
    kill = [c for c in kill_jetzt(b) if c in {g.champion for g in die}]
    offen = [g.champion for g in die if g.leben is None]
    check = (f"dein Combo reicht für {', '.join(kill)}" if kill else "dein Combo reicht für keinen dort") \
        + (f" (Leben von {', '.join(offen)} unbekannt)" if offen else "")
    text = (f"{ort or 'in der Nähe'}: ihr {ihr} gegen {sie}"
            + (f"; tot bei ihnen: {', '.join(tote)}" if tote else "")
            + f"; dein Weg {int(round(weg))} s, dein Leben {pct(m.leben)}; KILL-CHECK: {check}")
    mit_dir = weg <= KAMPF_MIT_DIR_S
    global LETZTER_KAMPF
    ich = getattr(p, "ich", None)
    LETZTER_KAMPF = ([s.champion for s, _ in wir] + ([ich.champion] if mit_dir and ich else []), [g.champion for g in die])
    if (u := kampf_urteil(m, p, [s for s, _ in wir], {s.name: le for s, le in wir}, die, mit_dir)) is not None:
        ohne = len(b.unbekannte()) if hasattr(b, "unbekannte") else 0
        text += (f"; RECHNER {'mit dir' if mit_dir else 'ohne dich (zu weit)'}: {u.text()}"
                 + (f" (ohne {ohne} Gegner, die keiner sieht)" if ohne else ""))
    return text, weg


KAMPF_MIT_DIR_S = 12.0       # so nah (Laufzeit) zaehlst du im Rechner mit
LETZTER_KAMPF: tuple = ([], [])   # fuer Auswertungen: wer im letzten Kampf gezaehlt wurde


def kampf_urteil(m, p, freunde: list, leben: dict, die: list, mit_dir: bool = True):
    """Auftrag 020, 4: das Urteil des Kampfrechners fuer diesen Kampf (lolcoach/kampf_rechner.py) - mit dir, wenn
    du in KAMPF_MIT_DIR_S dort sein kannst."""
    try:
        from .combo import _eigene_werte
        from .kampf_rechner import Kaempfer, rechne
        b = m.b
        ich = p.ich
        wir = [Kaempfer(s.champion_id, "wir", s.level, tuple(s.items), leben.get(s.name),
                        m.ult_mitspieler.get(s.name), name=s.champion) for s in freunde]
        werte = getattr(b.partie, "werte", None) if getattr(b, "partie", None) is not None else None
        if mit_dir:
            wir.append(Kaempfer(ich.champion_id, "wir", ich.level, tuple(ich.items), m.leben, b.ult,
                                getattr(b.partie, "raenge", None) or None,
                                _eigene_werte(ich.champion_id, ich.level, werte) if werte else None,
                                name=ich.champion, ich=True))
        sie = [Kaempfer(g.s.champion_id, "sie", g.s.level, tuple(g.s.items), g.leben,
                        (False if g.ult else None) if getattr(g, "ult", None) is not None else None, name=g.champion)
               for g in die]
        return rechne(wir + sie)
    except Exception:
        return None


def _symbol(o, gruben: dict, zeit: float) -> str:
    """Auftrag 018, 1: was das Objective-Symbol der Minimap dazu sagt (eigene Sicht). 183125 17:21 sagte Claude "Ob
    der Herold noch steht, weiß ich nicht" - das lila Symbol war zu sehen."""
    g = gruben.get(GRUBE_VON.get(o.schl, ""))
    if g is None or not o.lebt:
        return ""
    # Nur die Bestaetigung. "Symbol fehlt, vermutlich genommen" war falsch: im Kampf an der Grube (183125 13:50-14:21)
    # lesen Effekte und Portraets als Uhr, und genommen meldet die API ohnehin sofort (DragonKill, HeraldKill ...).
    return " (Symbol auf der Karte zu sehen)" if g[0] == "symbol" else ""


@dataclass
class Spieler:
    name: str
    rolle: str
    team: str                # "wir" / "sie"
    level: int
    items: list[str]
    tot: bool
    respawn: float | None
    leben: int | None        # Prozent, nur wenn frisch sichtbar
    ort: str                 # die eindeutige Form
    flash: str               # "bereit" / "weg noch N s" / "unbekannt"
    ult: str
    bei_dir_s: int | None


@dataclass
class Welt:
    zeit: float
    du: str
    plan: str
    vorn: str
    kauf: str
    spieler: list[Spieler] = field(default_factory=list)
    karte: list[str] = field(default_factory=list)
    timer: list[str] = field(default_factory=list)
    staerke: list[str] = field(default_factory=list)
    ereignisse: list[tuple[float, str]] = field(default_factory=list)


class Chronik:
    """Die Ereignisse fuer "seit dem letzten Aufruf": Kills, Tuerme, Objectives, Sichtungen, Flashes, dein Tod."""

    def __init__(self):
        self.liste: deque = deque(maxlen=60)
        self._ereignis_ids: set = set()
        self._sichtbar: dict[str, float] = {}     # zuletzt sichtbar
        self._flash: set = set()

    def takt(self, p, b, lb) -> None:
        if p is None or b is None:
            return
        for e in p.ereignisse:
            if e.id in self._ereignis_ids:
                continue
            self._ereignis_ids.add(e.id)
            wir = "ihr" if e.team == p.mein_team else "sie"
            if e.art == "ChampionKill" and e.opfer is not None:
                wer = e.taeter.champion if e.taeter is not None else "?"
                self.liste.append((e.zeit, f"{wer} tötet {e.opfer.champion} ({wir})"))
            elif e.art in ("TurretKilled", "InhibKilled"):
                self.liste.append((e.zeit, f"{'Turm' if e.art == 'TurretKilled' else 'Inhibitor'} fällt ({wir})"))
            elif e.art in ("DragonKill", "HeraldKill", "BaronKill", "HordeKill", "AtakhanKill"):
                self.liste.append((e.zeit, f"{e.art.removesuffix('Kill')} genommen ({wir})"))
        for g in b.gegner:
            zuletzt = self._sichtbar.get(g.champion)
            if g.sichtbar and not g.s.tot:
                if zuletzt is None or p.zeit - zuletzt >= 10.0:      # Flackern der Minimap zaehlt nicht
                    self.liste.append((p.zeit, f"{g.champion} taucht auf ({g.ort or 'Ort unbekannt'})"))
                self._sichtbar[g.champion] = p.zeit
        z = getattr(lb, "zauber", None)
        if z is not None:
            feinde = {s.name for s in p.gegner()}
            for t in list(z.timer.values()):
                schl = (t.name, t.zauber, round(t.seit))
                if t.name in feinde and schl not in self._flash and t.zurueck > p.zeit:
                    self._flash.add(schl)
                    was = "Flash" if t.zauber == "SummonerFlash" else t.zauber.replace("Summoner", "")
                    self.liste.append((t.seit, f"{t.champion} benutzt {was}"))

    def seit(self, zeit: float, s: float = SEIT_S) -> list[tuple[float, str]]:
        return sorted(x for x in self.liste if zeit - s <= x[0] <= zeit + 0.5)


def _ort(g, lb, zeit: float) -> str:
    if g.s.tot:
        return f"tot, noch {int(g.s.respawn or 0)} s"
    if g.sichtbar:
        return f"jetzt sichtbar {g.ort or '(Ort unbekannt)'}"
    if g.seit is None or g.pos is None:
        vermutlich = ROLLE_LANE.get(getattr(g.s, "rolle", ""), None)
        return "noch nie gesehen" + (f", vermutlich {vermutlich}" if vermutlich else "")
    if g.seit <= 10:
        return f"zuletzt gesehen vor {int(g.seit)} s {g.ort}, gerade nicht zu sehen"
    vermutlich = None
    jt = getattr(lb, "jungle", None)
    if getattr(g.s, "rolle", "") == "JUNGLE" and jt is not None:
        w = jt.wahrscheinlich(zeit)
        s, pw = max(w.items(), key=lambda x: x[1])
        vermutlich = f"{s} ({int(round(pw * 100))} %)"
    elif g.seit <= 60:
        vermutlich = "noch in der Nähe davon"
    else:
        vermutlich = ROLLE_LANE.get(getattr(g.s, "rolle", ""), None)
        vermutlich = f"auf seiner Lane {vermutlich}" if vermutlich else None
    return f"zuletzt gesehen vor {int(g.seit)} s {g.ort}, jetzt unbekannt" + (f", vermutlich {vermutlich}"
                                                                              if vermutlich else "")


def _zauber(p, lb, s, zeit: float, zauber: str) -> str:
    z = getattr(lb, "zauber", None)
    if zauber not in getattr(s, "zauber", ()):
        return "hat keins"
    t = z.timer.get((s.name, zauber)) if z is not None else None
    if t is None:
        return "unbekannt (gilt als bereit)"
    return f"weg noch {int(t.zurueck - zeit)} s" if t.zurueck > zeit else "bereit"


def bauen(kern, p, lagebild=None) -> Welt | None:
    """Das Lagebild dieses Takts - None ohne Merkmale."""
    from . import ddragon
    from .bewertung import TUERME, stehende_tuerme
    m = getattr(kern, "m", None)
    if m is None or m.b is None or p is None or p.ich is None:
        return None
    b = m.b
    lb = lagebild if lagebild is not None else getattr(kern, "_lagebild", None)
    it = ddragon.items()
    iname = lambda ids: [it.get(i, {}).get("name", str(i)) for i in ids if "Trinket" not in it.get(i, {}).get("tags", [])]
    ich = p.ich
    zauber = []
    if b.flash is not None:
        zauber.append("Flash bereit" if b.flash <= 0 else f"Flash in {int(b.flash)} s")
    if m.tp_in is not None:
        zauber.append("TP bereit" if m.tp_in <= 0 else f"TP in {int(m.tp_in)} s")
    if b.ult is not None:
        zauber.append("Ult bereit" if b.ult else "Ult nicht bereit")
    from .kern.modus import bereich_worte
    du = (f"{ich.champion} L{ich.level} ({ROLLE_DE.get(ich.rolle, ich.rolle)}), "
          + ("TOT, Respawn in " + str(int(m.respawn)) + " s" if m.tot else
             f"Leben {int(round((m.leben or 0) * 100))} %") + f", Gold {int(b.gold or 0)}, {bereich_worte(m.bereich)}"
          + f", Modus {kern.modus.aktuell}. Items: {', '.join(iname(ich.items)) or '-'}. "
          + ("; ".join(zauber) + "." if zauber else ""))
    pl = kern.fuehrer.plan
    plan = "keiner"
    if pl is not None and not pl.handlung.stumm:
        from .kern.fragen import satz
        plan = satz(pl.handlung) + (f" Danach: {kern.danach_text}." if kern.danach_text else "")
    v = kern.vorn()
    from . import stratege
    kill = stratege.kill_jetzt(b)
    vorn = (f"VERBOTEN (Leben {v['leben']} %): nichts nach vorn, keine Welle zum Gegner" if v["verboten"] else
            "erlaubt" + (f"; zu riskant: {', '.join(v['gesperrt'])}" if v["gesperrt"] else "")) \
        + (f". KILL JETZT: {', '.join(kill)} (dein Combo reicht)" if kill else ". KILL JETZT: keiner")
    k = m.kauf
    from . import kaufplan
    frei = kaufplan.PLAETZE - kaufplan._belegt(list(ich.items))
    kauf = (f"{', '.join(k.kaufen)} für {k.kosten} Gold" + (f" (Ziel {k.item})" if k.item else "")
            + (f", dafür zuerst {k.verkaufen} verkaufen" if k.verkaufen else "")) if k is not None and k.kaufen else \
        (f"nichts; noch {k.naechstes[1]} Gold bis {k.naechstes[0]}" if k is not None and getattr(k, "naechstes", None)
         else "nichts Sinnvolles")
    kauf += f"; freie Plätze {frei}"
    w = Welt(zeit=m.zeit, du=du, plan=plan, vorn=vorn, kauf=kauf)
    # Spieler: erst ihr, dann sie, je nach Rolle
    ordnung = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
    gl = {g.s.name: g for g in b.gegner}
    mit = {s.name: (wo, le, ort) for s, wo, le, ort in (b.mitspieler or [])}
    for s in sorted(p.team(p.mein_team), key=lambda s: ordnung.index(s.rolle) if s.rolle in ordnung else 9):
        if s.name == ich.name:
            continue
        wo, le, ort = mit.get(s.name, (None, None, None))
        w.spieler.append(Spieler(s.champion, ROLLE_DE.get(s.rolle, s.rolle), "wir", s.level, iname(s.items), s.tot,
                                 s.respawn if s.tot else None, None if le is None else int(round(le * 100)),
                                 f"tot, noch {int(s.respawn or 0)} s" if s.tot else (f"jetzt {ort}" if ort else
                                                                                      "Ort unbekannt"),
                                 "?", "bereit" if m.ult_mitspieler.get(s.name) else
                                 "?" if s.name not in m.ult_mitspieler else "nicht bereit", None))
    for s in sorted(p.gegner(), key=lambda s: ordnung.index(s.rolle) if s.rolle in ordnung else 9):
        g = gl.get(s.name)
        if g is None:
            continue
        bei = int(g.ankunft) if g.ankunft is not None and not g.s.tot and (g.sichtbar or (g.seit or 99) <= 20) \
            and g.ankunft <= 30 else None
        w.spieler.append(Spieler(s.champion, ROLLE_DE.get(s.rolle, s.rolle), "sie", s.level, iname(s.items), s.tot,
                                 s.respawn if s.tot else None,
                                 None if g.leben is None or not g.sichtbar else int(round(g.leben * 100)),
                                 _ort(g, lb, m.zeit), _zauber(p, lb, s, m.zeit, "SummonerFlash"),
                                 "?" if getattr(g, "ult", None) is None else ("bereit" if not g.ult else
                                                                              f"weg noch {int(g.ult)} s"), bei))
    # Karte
    stehen = stehende_tuerme(p)
    for team, wer in ((p.mein_team, "eure"), (None, "ihre")):
        teile = []
        for lane in ("Top", "Mid", "Bot"):
            st = [STUFE_DE.get(k[2], k[2]) for k in TUERME if k[1] == lane and k in stehen
                  and ((k[0] == p.mein_team) == (team is not None))]
            teile.append(f"{lane}: {', '.join(st) if st else 'keiner'}")
        w.karte.append(f"Stehende Türme {wer}: " + "; ".join(teile))
    if (k := kampf_lage(m, p)) is not None and k[1] <= 30:
        w.karte.insert(0, f"KAMPF JETZT {k[0]}")
    for lane, st in sorted((m.wellen or {}).items()):
        if st is not None and st.unsere is not None:
            w.karte.append(f"Welle {lane}: {st.unsere} eure gegen {st.ihre if st.ihre is not None else '?'} ihre, "
                           f"{st.zustand}")
    # Timer
    gruben = getattr(lb, "gruben", None) or {}
    for o in sorted(m.objectives or [], key=lambda o: o.spawn_in):
        w.timer.append(f"{OBJ_DE.get(o.schl, o.schl)} " + ("lebt" if o.lebt else f"in {int(o.spawn_in)} s")
                       + _symbol(o, gruben, m.zeit))
    if m.kanone_in is not None and m.kanone_in <= 60:
        w.timer.append(f"Kanone in deiner Welle in {int(m.kanone_in)} s")
    tote = [f"{s.champion} {int(s.respawn or 0)} s" for s in p.spieler if s.tot]
    if tote:
        w.timer.append("Respawns: " + ", ".join(tote))
    # Staerke
    from .zustand import gegenteam
    wir, die = p.mein_team, gegenteam(p.mein_team)
    lv = sum(s.level for s in p.team(wir)) - sum(s.level for s in p.team(die))
    w.staerke.append(f"Kills {p.kills(wir)} zu {p.kills(die)}, Item-Gold {p.item_gold(wir) - p.item_gold(die):+d}, "
                     f"Level-Summe {lv:+d}")
    tp = getattr(kern.makro, "tp", None)
    if tp is not None:
        w.staerke.append(f"Teamplan {tp.plan}: {tp.satz}")
    chronik = getattr(kern, "chronik", None)
    if chronik is not None:
        w.ereignisse = chronik.seit(m.zeit)
    return w


def text(w: Welt) -> str:
    """Der Text fuer Claude, feste Reihenfolge."""
    z = [f"ZEIT {_uhr(w.zeit)}", f"DU: {w.du}", f"PLAN DES COACHS: {w.plan}", f"NACH VORN: {w.vorn}",
         f"KAUF: {w.kauf}", "SPIELER:"]
    for s in w.spieler:
        teile = [f"{'Mitspieler' if s.team == 'wir' else 'Gegner'} {s.name} ({s.rolle}) L{s.level}", s.ort]
        if s.leben is not None:
            teile.append(f"Leben {s.leben} %")
        if s.team == "sie":
            teile.append(f"Flash {s.flash}")
            if s.bei_dir_s is not None:
                teile.append(f"kann in {s.bei_dir_s} s bei dir sein")
        if s.ult not in ("?",):
            teile.append(f"Ult {s.ult}")
        if s.items:
            teile.append("Items: " + ", ".join(s.items[:6]))
        z.append("- " + "; ".join(teile))
    z.append("KARTE: " + " | ".join(w.karte))
    z.append("TIMER: " + ("; ".join(w.timer) if w.timer else "-"))
    z.append("STAERKE: " + " | ".join(w.staerke))
    z.append("SEIT DEM LETZTEN AUFRUF (30 s): " + ("; ".join(f"{_uhr(t)} {x}" for t, x in w.ereignisse)
                                                  if w.ereignisse else "nichts Neues"))
    return "\n".join(z)


def tokens(text_: str) -> int:
    """Grobe Tokenzahl (deutsch: ~3,3 Zeichen je Token) - ohne API-Aufruf."""
    return int(len(text_) / 3.3)
