"""Modus KAMPF und alles um den Kampf (Buch 7, Kapitel 4-8).

- `ANNEHMEN` (4): kommt ein sichtbarer Gegner oder eine Gruppe auf dich zu, EINE Frage - nimmst du den Kampf? Dann ist
  ANNEHMEN Kandidat und ZURUECK wegen dieser Gegner nicht; sonst ZURUECK wie bisher.
- KAMPF (5, 6): REIN, RAUS, DREHEN oder HALTEN (stumm) nach Tabelle 5.1 - nicht nach EV, nicht ueber den PlanFuehrer.
  Hoechstens fuenf Woerter, Kategorie GEFAHR, `gueltig` 1 s, ein Wechsel REIN <-> RAUS nur mit Kampf-Ereignis, >= 4 s
  Abstand, hoechstens drei Ansagen je Kampf, stumm, wenn du es schon tust.
- Entscheidungspunkte (3.3): ein Gegner und du (oder ein Mitspieler in 1500) naehern sich erstmals auf <= 1500 nach
  >= 10 s ohne solche Naehe - dort wird p_gewinn gerechnet. Die Probe dient der Eichung und dem Rueckblick (8).
- `rueckblick` (8): nach einem Tod aus der letzten Probe - wer da war, dein Leben, ob eine Ansage kam."""
from __future__ import annotations

from ...bewertung import abstand
from ...champions import _champ
from ..handlung import Handlung, Ziel
from .. import kampf as K

NAEHE = 1500.0            # Buch 7, 3.3: Entscheidungspunkt
NAEHE_PAUSE_S = 10.0
PROBE_ALT_S = 45.0        # so alt darf die Probe fuer den Rueckblick hoechstens sein


def _tags(cid: str) -> set:
    return set((_champ(cid) or {}).get("tags", []))


def angriffsreichweite(cid: str) -> float:
    return float((_champ(cid) or {}).get("stats", {}).get("attackrange", 150.0))


def _leben(g) -> float | None:
    return g.leben if g.leben is not None and (g.leben_alter is None or g.leben_alter <= 2.5) else None


def toetbar(g, c: dict) -> bool:
    le = _leben(g)
    grenze = c["toetbar_leben_tank"] if "Tank" in _tags(g.s.champion_id) else c["toetbar_leben"]
    return le is not None and le <= grenze


def sichtbare(m) -> list:
    b = m.b
    return [g for g in b.gegner if g.sichtbar and not g.s.tot and g.pos is not None and b.pos is not None]


# --- Ziel und Flucht (5.2, 5.3) ---------------------------------------------------------------------------------------

def reichweite_rein(m, cfg: dict) -> float:
    ch = K.champion_werte(cfg, m.b.ich.champion_id)
    return ch.get("reichweite_rein", 550) + (ch.get("flash_zusatz", 400) if m.b.flash == 0 else 0)


def ziel_wahl(m, cfg: dict):
    """(Gegner, fast_tot?) - toetbar, sonst ein Carry vor seiner Front, sonst der Naechste in Reichweite."""
    b, c = m.b, cfg["kampf"]
    alle = sichtbare(m)
    in_r = [g for g in alle if abstand(g.pos, b.pos) <= reichweite_rein(m, cfg)]
    if not in_r:
        return None, False
    fast = [g for g in in_r if toetbar(g, c)]
    if fast:
        return min(fast, key=lambda g: _leben(g)), True
    front = [g for g in alle if _tags(g.s.champion_id) & {"Tank", "Fighter"}]
    carrys = [g for g in in_r if _tags(g.s.champion_id) & {"Marksman", "Mage"}
              and all(abstand(g.pos, b.pos) < abstand(f.pos, b.pos) + c["hinter_front"]
                      for f in front if f is not g and abstand(f.pos, g.pos) > 150)]
    if carrys:
        return max(carrys, key=lambda g: K.kraft_gegner(g, m, c)), False
    return min(in_r, key=lambda g: abstand(g.pos, b.pos)), False


def flucht(m, cfg: dict) -> tuple[bool, str]:
    """(moeglich?, Ort in einem Wort) - Buch 7, 5.3: vor dem schnellsten Verfolger am sicheren Ort, und keiner steht
    schon in seiner Angriffsreichweite + 150."""
    b = m.b
    ort, weg = b.sicherer_ort()
    wort = "Turm" if "Turm" in ort else "Basis" if "Basis" in ort else ort.split(",")[0].split(" und ")[0]
    if weg is None:
        return False, wort
    ch = K.champion_werte(cfg, b.ich.champion_id)
    bonus = (ch.get("flash_zusatz", 400) if b.flash == 0 else 0) + sum(
        d for taste, d in ch.get("flucht", {}).items() if b.bereit and b.bereit.get(taste))
    for g in sichtbare(m):
        d = abstand(g.pos, b.pos)
        if d > NAEHE:
            continue
        rw = angriffsreichweite(g.s.champion_id) + 150.0
        if d <= rw:
            return False, wort
        einholen = (d + bonus - rw) / max(1.0, (g.tempo or 350.0) - (b.mein_tempo or 345.0))
        if weg >= einholen:
            return False, wort
    return True, wort


def _dive_ok(m, cfg: dict, ziel, fast_tot: bool, p: float) -> bool:
    """Buch 7, 6: unter ihrem Turm REIN nur allein mit Beleg oder zu zweit mit Turm-Traeger."""
    b, c = m.b, cfg["kampf"]
    from .. import gefahr
    j = b.jungler
    pj = gefahr.p_da(j, 6.0, m, cfg["gefahr"]) if j is not None else 0.0
    nah_mit = [(s, le) for s, wo, le, *_ in b.mitspieler if not s.tot and wo is not None and abstand(wo, b.pos) <= NAEHE]
    if nah_mit:
        traeger = any(le is not None and b.leben is not None and le > b.leben for _, le in nah_mit)
        return traeger and p >= c["dive_team_p_min"]
    zweiter = any(g is not ziel and abstand(g.pos, b.pos) <= NAEHE for g in sichtbare(m))
    welle = m.lane_phase is False or (m.welle is not None and (m.welle.zustand == "GECRASHT_BEI_IHM"
                                                               or (m.welle.unsere or 0) >= 3))
    return (fast_tot and (b.leben or 0) >= c["dive_leben_min"] and not zweiter and pj < 0.2 and welle
            and p >= c["dive_allein_p_min"])


def raus_beleg(m, cfg: dict) -> bool:
    """Auftrag 002, S5.3: ein robuster Beleg fuer RAUS ohne das ungeeichte p_gewinn - in kampf_radius stehen >= 1
    Gegner mehr als ihr (du mitgezaehlt), ODER dein Leben liegt unter raus_leben_max und unter dem Balken des
    naechsten Gegners."""
    b, c = m.b, cfg["kampf"]
    if b is None or b.pos is None:
        return False
    r = c["kampf_radius"]
    gegner = [g for g in sichtbare(m) if abstand(g.pos, b.pos) <= r]
    wir = 1 + sum(1 for s, wo, *_ in b.mitspieler if wo is not None and not s.tot and abstand(wo, b.pos) <= r)
    if len(gegner) >= wir + 1:
        return True
    # Auftrag 003, Teil A 2: unter raus_leben_ohne_balken (15 %) mit einem Gegner in kampf_radius reicht das allein -
    # auch ohne seinen Balken (213624 19:00: 12 %, Sona 825 entfernt, Balken unbekannt)
    if b.leben is not None and b.leben < cfg["schranken"]["raus_leben_ohne_balken"] and gegner:
        return True
    if b.leben is not None and b.leben < cfg["schranken"]["raus_leben_max"] and gegner:
        naechster = min(gegner, key=lambda g: abstand(g.pos, b.pos))
        le = _leben(naechster)
        return le is not None and b.leben < le
    return False


def entscheide(m, cfg: dict, weg_von: bool, hin_zu) -> tuple[str, str, str | None]:
    """(Art, Satz, Ziel-Name) nach Tabelle 5.1. `weg_von`: du bewegst dich von den Gegnern weg; `hin_zu(g)`: du
    naeherst dich g."""
    b, c = m.b, cfg["kampf"]
    p, _ = K.p_gewinn(m, b.pos, c["fenster_s"], cfg=cfg)
    ziel, fast_tot = ziel_wahl(m, cfg)
    kann, ort = flucht(m, cfg)
    # DREHEN: du laeufst weg, genau ein Verfolger nah, er fast tot, du nicht - und niemand sonst
    if weg_von:
        nahe = [g for g in sichtbare(m) if abstand(g.pos, b.pos) <= c["drehen_abstand"]]
        if len(nahe) == 1:
            g = nahe[0]
            le = _leben(g)
            frei = not any(x is not g and abstand(x.pos, b.pos) <= c["drehen_frei"] for x in sichtbare(m))
            from .. import gefahr
            pj = gefahr.p_da(b.jungler, 6.0, m, cfg["gefahr"]) if b.jungler is not None else 0.0
            p1, _ = K.p_gewinn(m, b.pos, c["fenster_s"], gewichte={g.s.name: 1.0}, cfg=cfg)
            if (le is not None and le <= c["drehen_gegner_leben"] and (b.leben or 0) >= c["drehen_eigen_leben"]
                    and p1 >= c["drehen_p_min"] and frei and pj < 0.2):
                return "DREHEN", f"Dreh um, {g.champion} fast tot!", g.champion
    if ziel is not None and p >= c["rein_p_min"]:
        if K._turm(m, ziel.pos) < 0 and not _dive_ok(m, cfg, ziel, fast_tot, p):
            return ("RAUS", "Lass ihn, Turm!", None) if hin_zu(ziel) else ("HALTEN", "", None)
        return "REIN", (f"Rein, {ziel.champion} fast tot!" if fast_tot else f"Rein auf {ziel.champion}!"), ziel.champion
    if p <= c["raus_p_max"]:
        if kann:
            return "RAUS", (f"Raus, zum {ort}!" if ort == "Turm" else "Raus, zur Basis!" if ort == "Basis"
                            else f"Raus zu {ort}!"), None
        if ziel is not None and K._turm(m, ziel.pos) >= 0:
            # kein Fluchtweg: wer ohnehin stirbt, soll etwas mitnehmen
            return "REIN", f"Rein auf {ziel.champion}!", ziel.champion
    return "HALTEN", "", None


class Kampf:
    """Eine Kampf-Episode: aktuelle Ansage, Ziel, Zeit und Zahl der Ansagen (5)."""

    def __init__(self, zeit: float, m):
        self.start = zeit
        self.n = 0
        self.art: str | None = None          # zuletzt GESAGT
        self.tabelle: str | None = None      # zuletzt ENTSCHIEDEN (Tabelle 5.1), auch ungesagt
        self.zuletzt = -1e9
        self.ziel_gesagt: str | None = None
        self.leben = m.b.leben if m.b is not None else None
        self.stand = self._stand(m)
        self.pos_vorher = m.pos
        self.abst_vorher: dict = {}

    @staticmethod
    def _stand(m) -> tuple:
        """Woran ein Kampf-Ereignis zu erkennen ist: Tote beider Seiten, wer in kampf_radius steht, Flash/Ult weg."""
        b = m.b
        tote = (len(b.tote_eigene), len(b.tote_gegner))
        radius = frozenset(g.s.name for g in sichtbare(m) if abstand(g.pos, b.pos) <= 1000)
        mit = frozenset(s.name for s, wo, *_ in b.mitspieler if wo is not None and b.pos is not None
                        and abstand(wo, b.pos) <= 1000)
        zauber = frozenset(g.s.name for g in b.gegner if (g.flash or 0) > 0 or (g.ult or 0) > 0)
        return tote, radius, mit, zauber

    def ereignis(self, m, c: dict) -> bool:
        """Buch 7, 5.4: Tod auf einer Seite, jemand neu in kampf_radius, Flash/Ult erkannt, dein Leben -15 %."""
        jetzt = self._stand(m)
        tote, radius, mit, zauber = self.stand
        neu = (jetzt[0] != tote or bool(jetzt[1] - radius) or bool(jetzt[2] - mit) or bool(jetzt[3] - zauber))
        le = m.b.leben
        if le is not None and self.leben is not None and self.leben - le >= c["ereignis_leben_faellt"]:
            neu = True
        return neu

    def takt(self, m, cfg: dict) -> tuple[str, str, str | None] | None:
        """(Art, Satz, Ziel) einer Ansage - oder None (stumm)."""
        b, c = m.b, cfg["kampf"]
        if b is None or b.pos is None:
            return None
        weg_von = False
        naeher: dict = {}
        for g in sichtbare(m):
            d = abstand(g.pos, b.pos)
            alt = self.abst_vorher.get(g.s.name)
            if alt is not None:
                naeher[g.s.name] = d < alt - 40
                weg_von = weg_von or d > alt + 40
            self.abst_vorher[g.s.name] = d
        art, satz, ziel = entscheide(m, cfg, weg_von, lambda g: naeher.get(g.s.name, False))
        self.tabelle = art                # die Entscheidung nach Tabelle 5.1 in diesem Takt (Protokoll, Szenarien)
        if art == "HALTEN" or not satz:
            return None
        if art == self.art and ziel == self.ziel_gesagt:
            return None
        if self.n >= c["max_je_episode"] or m.zeit - self.zuletzt < c["kampf_abstand_s"]:
            return None
        gegen = {"REIN": "RAUS", "RAUS": "REIN", "DREHEN": "RAUS"}
        if self.art is not None and gegen.get(art) == self.art and not self.ereignis(m, c):
            return None
        # stumm, wenn du es schon tust
        if art == "REIN" and ziel is not None and naeher.get(next((g.s.name for g in b.gegner if g.champion == ziel), ""),
                                                            False):
            return None
        if art == "RAUS" and weg_von and self.art is None:
            return None
        if ziel is not None and ziel == self.ziel_gesagt and art == "REIN":
            satz = "Rein!"
        if len(satz.split()) > c["max_woerter_kampf"]:
            satz = " ".join(satz.split()[:c["max_woerter_kampf"]])
        return art, satz, ziel

    def gesagt(self, m, art: str, ziel: str | None) -> None:
        self.n += 1
        self.art, self.zuletzt = art, m.zeit
        if ziel is not None:
            self.ziel_gesagt = ziel
        self.leben = m.b.leben if m.b is not None else self.leben
        self.stand = self._stand(m)


# --- ANNEHMEN (4) -------------------------------------------------------------------------------------------------

def annehmen(m, cfg: dict, modus: str, plan=None, schon: set | None = None) -> Handlung | None:
    """Kommt ein sichtbarer Gegner (oder eine Gruppe) auf dich zu, <= annehmen_abstand: nimmst du den Kampf? Ist
    ANNEHMEN schon der Plan, zaehlt sein Gegner auch, wenn er stehen bleibt - das Urteil haelt, bis ein Ereignis es
    kippt (102112 26:29: Fiddlesticks 338 entfernt, blieb stehen - der Plan fiel auf FARMEN)."""
    from .. import gefahr
    from . import lane_verloren
    b, c = m.b, cfg["kampf"]
    if b is None or b.pos is None or m.tot:
        return None
    schon = set(schon or ()) | (set(plan.handlung.daten.get("gruppe", [])) if plan is not None
                                 and plan.art == "ANNEHMEN" else set())    # auch das stumme Urteil (Entscheidung 2)
    kommen = [g for g in sichtbare(m) if (g.kommt_naeher or g.champion in schon)
              and abstand(g.pos, b.pos) <= c["annehmen_abstand"]]
    if not kommen:
        return None
    lane = b.lane.s.name if b.lane is not None else None
    if modus == "LANE" and any(g.s.name == lane for g in kommen):
        return None                       # gegen den Lane-Gegner bleibt es TRADE/ALL_IN (Buch 2)
    if lane_verloren(m)[0]:
        return None
    mitte = (sum(g.pos[0] for g in kommen) / len(kommen), sum(g.pos[1] for g in kommen) / len(kommen))
    kampf_ort = ((mitte[0] + b.pos[0]) / 2, (mitte[1] + b.pos[1]) / 2)
    if K._turm(m, kampf_ort) < 0:
        return None                       # tauchen gibt es nur als REIN im Kampf
    j = b.jungler
    if j is not None and not j.s.tot and j.s.name not in {g.s.name for g in kommen}:
        anders = j.sichtbar is False and j.seit is not None and j.seit <= c["jungler_sicher_s"] and j.abstand is not None \
            and j.abstand > 6000
        if not anders and gefahr.p_da(j, 10.0, m, cfg["gefahr"]) >= c["jungler_p_max"]:
            return None
    if b.leben is None or b.leben < c["annehmen_leben_min"]:
        return None
    kern = K.champion_werte(cfg, b.ich.champion_id).get("kern", [])
    if kern and (not b.bereit or any(b.bereit.get(t) is False for t in kern)):
        return None
    p, auf = K.p_gewinn(m, b.pos, c["fenster_s"], cfg=cfg)
    if p < c["annehmen_p_min"]:
        return None
    g = min(kommen, key=lambda x: abstand(x.pos, b.pos))
    from ...bewertung import kill_gold
    wir = len(auf.get("wir", []))
    name = g.champion
    satz = (f"{name} allein: nimm den Kampf." if len(kommen) == 1 and wir <= 1
            else f"Zu {ZAHL.get(wir, str(wir))} gegen {name}: rein." if len(kommen) == 1
            else f"{name} und {next(x for x in kommen if x is not g).champion} kommen: nimm den Kampf.")
    h = Handlung("ANNEHMEN", Ziel("gegner", name, g.pos, abstand(g.pos, b.pos) / (b.mein_tempo or 345.0)), modus,
                 c["fenster_s"], gewinn=float(kill_gold(g.s, p=m.p)), p_erfolg=p, grund="nimm den Kampf", satz=satz)
    h.daten.update(kampf_mit=g.s.name, gruppe=[x.champion for x in kommen], p_gewinn=round(p, 2))
    return h


ZAHL = {2: "zweit", 3: "dritt", 4: "viert", 5: "fünft"}


# --- Entscheidungspunkte und Rueckblick (3.3, 8) -----------------------------------------------------------------

class Proben:
    """Buch 7, 3.3: je Entscheidungspunkt eine Probe (p_gewinn vor dem Einstieg) - fuer Eichung und Rueckblick."""

    def __init__(self):
        self.liste: list[dict] = []
        self._nah_zuletzt = -1e9
        self._p_da: dict = {}

    def takt(self, m, cfg: dict) -> dict | None:
        from .. import gefahr
        b = m.b
        if b is None or b.pos is None or m.tot:
            return None
        nahe = [g for g in sichtbare(m) if abstand(g.pos, b.pos) <= NAEHE]
        neu = None
        if nahe:
            if m.zeit - self._nah_zuletzt >= NAEHE_PAUSE_S:
                p, auf = K.p_gewinn(m, b.pos, cfg["kampf"]["fenster_s"], cfg=cfg)
                # Merkmale fuer die Trennschaerfe (kampf_eichung): Mittel eurer Beteiligten ("wir") minus Mittel der
                # nahen Gegner; Gegner mit der Schaetzung des Modells (K.gegner_werte, G7), wir mit den API-Werten
                werte = {b.ich.champion: (b.ich.level, float(b.ich.item_gold))}
                werte.update({s.champion: (s.level, float(s.item_gold)) for s, *_ in b.mitspieler})
                wir_w = [werte[n] for n, *_ in auf.get("wir", []) if n in werte]
                die_w = [K.gegner_werte(g, m, cfg["kampf"])[:2] for g in nahe]

                def diff(i: int) -> float | None:
                    if not wir_w or not die_w:
                        return None
                    return sum(x[i] for x in wir_w) / len(wir_w) - sum(x[i] for x in die_w) / len(die_w)
                neu = {"zeit": m.zeit, "p": p, "leben": b.leben, "gegner": [g.champion for g in nahe],
                       "wir": [n for n, *_ in auf.get("wir", [])], "p_da_vorher": dict(self._p_da),
                       "unter_turm": K._turm(m, b.pos) < 0, "ansage": None, "auf": auf,
                       "level_diff": diff(0), "gold_diff": diff(1), "kopf_diff": len(auf.get("wir", [])) - len(nahe)}
                self.liste.append(neu)
            self._nah_zuletzt = m.zeit
        self._p_da = {g.champion: gefahr.p_da(g, 10.0, m, cfg["gefahr"]) for g in b.gegner if not g.s.tot}
        return neu

    def ansage(self, zeit: float, richtung: str) -> None:
        """Nach der Probe kam eine Ansage: 'raus' (ZURUECK, RAUS) oder 'rein' (ANNEHMEN, REIN)."""
        if self.liste and zeit - self.liste[-1]["zeit"] <= PROBE_ALT_S and self.liste[-1]["ansage"] is None:
            self.liste[-1]["ansage"] = richtung

    def letzte(self, vor: float) -> dict | None:
        p = self.liste[-1] if self.liste else None
        return p if p is not None and 0 <= vor - p["zeit"] <= PROBE_ALT_S else None


def _namen(n: list[str]) -> str:
    return n[0] if len(n) == 1 else ", ".join(n[:-1]) + " und " + n[-1]


def rueckblick(probe: dict | None, taeter: str | None, beteiligt: list[str], turm: bool, leben: float | None,
               jungler: str | None = None, gewarnt: frozenset = frozenset(),
               wiederbelebt: frozenset = frozenset()) -> str | None:
    """Buch 7, 8: zwei Saetze aus der Probe am letzten Entscheidungspunkt - was entschied, was naechstes Mal. None: die
    Probe erkennt keine der Lagen, dann gilt der Rueckblick der Qualitaetsrunde (komponist.todesrueckblick)."""
    if probe is None:
        return None
    wer = [n for n in beteiligt if n] or ([taeter] if taeter else [])
    if turm or (probe["unter_turm"] and len(wer) <= 1):
        return ("Allein unter seinem Turm – der Turm hat entschieden. Tauch nur, wenn er fast tot ist und du mehr als "
                "die Hälfte Leben hast.")
    if taeter and taeter in wiederbelebt:
        # Auftrag 005 (173159 35:13): kein Nebel - er stand eben neben dir wieder auf
        return f"{taeter} ist gerade neben dir wiederbelebt. Tief bei ihnen zählt jeder Respawn-Timer."
    if taeter and probe["p_da_vorher"].get(taeter, 1.0) < 0.3 and taeter not in probe["gegner"] \
            and taeter not in gewarnt:        # Auftrag 005 (144655 9:23): wer angesagt war, kam nicht ungesehen
        # Pruefung c, R9: keine Pronomen; "Jungler" nur, wenn der Taeter ihr Jungler ist (173159 35:24: Kai'Sa, ADC)
        sicht = "ihren Jungler" if jungler is not None and taeter == jungler else taeter
        return f"{taeter} kam aus dem Nebel, niemand hatte {taeter} gesehen. Ohne Sicht auf {sicht} nicht so tief stehen."
    if not wer:
        return None
    if probe["ansage"] == "raus":
        verb = "hat" if len(wer) == 1 else "haben"
        s2 = "Bei zwei Gegnern sofort raus." if len(wer) >= 2 else "Kommt der Rückzug, geh sofort."
        return f"Raus kam, du bist geblieben – {_namen(wer[:2])} {verb} dich erreicht. {s2}"
    le = probe["leben"] if probe["leben"] is not None else leben
    if probe["p"] < 0.35 and len(wer) >= 2:
        prozent = f"{int(round((le or 0) * 10)) * 10} Prozent"
        s2 = ("Gegen zwei nur mit deinem Team oder unter deinem Turm." if le is not None and le >= 0.6
              else "Gegen zwei erst mit vollem Leben oder mit deinem Jungler.")
        return f"Du bist mit {prozent} gegen {_namen(wer[:2])} geblieben. {s2}"
    if len(wer) == 1:
        return f"Duell gegen {wer[0]} verloren. Schau es dir im Review an."
    return None
