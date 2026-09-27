"""Die Rechnung je Objective (Buch 6, Kapitel 3), von allen Modi benutzt.

Ein Objective ist ein Teamziel - gezaehlt wird, was DU daran aenderst:

    wir_an[k]   = k-kleinste Ankunft eurer Leute an der Grube (du eingeschlossen; Tote: Respawn + Weg aus dem Brunnen)
    n*          = argmin_{n >= n_min} (wir_an[n] + dauer(n)),  t0 = max(wir_an[n*], Spawn),  t1 = t0 + dauer
    dauer       = Tabelle [objective.dauer] (Spalte nach Spielzeit) * stufe_faktor / (1 - Rache der Drachen)
    P_kampf     = 1 - Prod (1 - p_da(g, t1 + puffer, Grube))
    p_gewinn    = kampf.p_gewinn(Grube, kampf_fenster_s)                         # EIN Kampfmodell (Buch 7)
    p_steal     = steal_mit_smite / steal_ohne_smite, wenn ihr Jungler rechtzeitig dort ist
    p_erfolg    = (1 - P_kampf * (1 - p_gewinn)) * (1 - p_steal)
    anteil      = p_erfolg - p_erfolg(ohne dich)

`zieht` (4.1): p_erfolg >= vorbereiten_p_min, anteil * wert + folgewert > 0 und - bis 14:00 - du wirst gebraucht
(Kapitel 6: Prio und euer Jungler geht hin). Sonst behandeln STAPELN, OBJECTIVE_VORLAUF, WOHIN, objective_ruft,
WELLE_UND_RAUS und ZUR_GRUPPE das Objective, als gaebe es keins."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..bewertung import BRUNNEN, WEGFAKTOR, abstand

MITSPIELER_TEMPO = 380.0
GROSS = ("baron", "aeltester")


@dataclass
class Urteil:
    schl: str
    n: int = 0                  # n*: so viele von euch nehmen es
    t0: float = 0.0             # Beginn (s ab jetzt)
    dauer: float = 0.0
    t1: float = 0.0             # Ende
    P_kampf: float = 0.0
    p_gewinn: float = 0.0
    p_steal: float = 0.0
    p_erfolg: float = 0.0
    p_erfolg_ohne: float = 0.0
    anteil: float = 0.0
    wert_uns: float = 0.0
    wert_ihnen: float = 0.0
    folgewert: float = 0.0
    gross: bool = False
    gebraucht: bool = True
    zieht: bool = False
    grund: str = ""             # warum (nicht) - fuers Protokoll
    die_zuerst: bool = False    # sie sind zuerst dort
    wer: list = field(default_factory=list)   # (Champion, Ankunft) eurer Leute
    die_an: list = field(default_factory=list)   # (Champion, Ankunft) ihrer Leute an der Grube, die Fruehesten zuerst
    mit: list = field(default_factory=list)      # Buch 6, 3.3 Nachtrag: wer mit dir kommt und es mit nimmt (Namen)
    auf: dict = field(default_factory=dict)      # Aufschluesselung des Kampfurteils (kampf.p_gewinn)


def _spalte(zeit: float) -> str:
    return "bis_14" if zeit < 840 else "bis_25" if zeit < 1500 else "danach"


def seele_ab(m) -> int:
    """Drachen bis zur Seele: 4, in Swiftplay 2 (mechanik.toml [swiftplay])."""
    if m.p is not None and getattr(m.p, "modus", None) == "SWIFTPLAY":
        from .. import wissen
        return int(wissen.lade("mechanik")["swiftplay"]["drache_max"])
    return 4


def drachen(m, team: str) -> int:
    return len(m.p.drachen(team)) if m.p is not None else 0


GEHT_HIN = 1000.0     # Kapitel 6: "hat sich ihr in 10 s um >= 1000 genaehert"


def geht_hin(m, o, name: str, wo) -> bool:
    """Ein Mitspieler geht zur Grube: er steht schon dort (grube_radius) oder kam ihr in 10 s um >= 1000 naeher
    (Kapitel 6 fuer euren Jungler, hier fuer alle)."""
    from . import konfig
    if abstand(wo, o.pos) <= konfig()["modus"]["grube_radius"]:
        return True
    return (getattr(m, "mitspieler_naeher", {}) or {}).get(o.schl, {}).get(name, 0.0) >= GEHT_HIN


MITKOMMEN_RADIUS = 1500.0   # Buch 6, 3.3 (Nachtrag): so nah bei dir "kommt mit, wenn du gehst"


def konfig_grube() -> float:
    from . import konfig
    return konfig()["modus"]["grube_radius"]


def mitkommende(m, o) -> set[str]:
    """Buch 6, 3.3 (Nachtrag, Carlos 27.09.): Mitspieler <= 1500 bei dir, die nicht selbst hingehen - sie kommen mit,
    wenn du gehst. Nur, wenn du lebst."""
    b = m.b
    if b is None or b.pos is None or m.tot:
        return set()
    # "bei dir" zuerst: wer neben dir laeuft, naehert sich der Grube mit dir - das beweist nicht, dass er ohne dich
    # ginge (102112 25:22: Tryndamere neben Riven auf dem Weg zum Drachen - "Drache mit Tryndamere")
    # ... aber nicht, wer zu einem ANDEREN Objective geht (102112 25:32: Tryndamere lief mit Riven zum Drachen und
    # zaehlte fuer den Baron als "kommt mit" - "Baron mit Tryndamere: ihr seid drei")
    anderswo = {s.name for s, wo, *_ in b.mitspieler if wo is not None
                for o2 in m.objectives if o2.schl != o.schl and geht_hin(m, o2, s.name, wo)}
    return {s.name for s, wo, *_ in b.mitspieler if not s.tot and wo is not None and s.name not in anderswo
            and abstand(wo, b.pos) <= MITKOMMEN_RADIUS and abstand(wo, o.pos) > konfig_grube()}


def wir_an(m, o, mit_mir: bool = True) -> list[tuple[str, float]]:
    """(Champion, Ankunft in s) eurer Leute an der Grube, die kuerzeste zuerst: du (tot: Respawn + Weg aus dem Brunnen)
    und die Mitspieler, die hingehen (geht_hin) - nicht jeder, der es in der Zeit KOENNTE (Abweichung, messungen.md
    Schritt 5: 102112 25:24 "Baron jetzt: ihr seid fuenf" mit zwei in der Basis; Buch 6, 8 selbst: "Baron faellt heraus,
    weil zwei eurer Leute in der Basis stehen"). Mit dir (`mit_mir`) zaehlen dazu die, die mit dir kommen
    (mitkommende, Buch 6 3.3 Nachtrag); ohne dich nur, wer nachweislich hingeht. Tote Mitspieler zaehlen nicht."""
    b, p = m.b, m.p
    mit = mitkommende(m, o) if mit_mir else set()
    aus = []
    mein = p.mein_team if p is not None else "ORDER"
    if mit_mir and b is not None:
        if m.tot:
            aus.append((b.ich.champion, m.respawn + abstand(BRUNNEN[mein], o.pos) * WEGFAKTOR / (m.mein_tempo or 345.0)))
        elif o.weg is not None:
            aus.append((b.ich.champion, o.weg))
    for s, wo, *_ in (b.mitspieler if b is not None else []):
        if s.tot or wo is None:
            continue
        if not (s.name in mit or (geht_hin(m, o, s.name, wo) and s.name not in mitkommende(m, o))):
            continue
        aus.append((s.champion, abstand(wo, o.pos) * WEGFAKTOR / MITSPIELER_TEMPO))
    return sorted(aus, key=lambda x: x[1])


def toetungszeit(m, o, cfg: dict, an: list[tuple[str, float]]) -> tuple[int, float, float] | None:
    """(n*, t0, dauer) - None: keine Spalte fuer diese Spielzeit oder zu wenige von euch."""
    c = cfg["objective"]
    d = c["dauer"]
    schl = o.schl
    tab = d.get(schl, {}).get(_spalte(m.zeit + max(0.0, o.spawn_in)))
    n_min = d["n_min"].get(schl, 1)
    if not tab or len(an) < n_min:
        return None
    faktor = 1.0
    if m.p is not None:
        wir = [s.level for s in m.p.team(m.p.mein_team)]
        if wir and sum(wir) / len(wir) >= c["stufe_ref"][_spalte(m.zeit)] + 3:
            faktor *= c["stufe_faktor"]
    if schl in ("drache", "aeltester") and m.p is not None:
        rache = min(c["rache_max"], c["rache_je_drache"] * drachen(m, m.p.mein_team))
        faktor /= (1.0 - rache)
    beste = None
    for n in range(n_min, len(an) + 1):
        dauer = tab[min(n - n_min, len(tab) - 1)] * faktor
        t0 = max(an[n - 1][1], o.spawn_in if not o.lebt else 0.0)
        if beste is None or t0 + dauer < beste[1] + beste[2]:
            beste = (n, t0, dauer)
    return beste


def werte(m, o, cfg: dict) -> tuple[float, float, float, bool]:
    """(wert_uns, wert_ihnen, folgewert, gross) - Kapitel 3.4."""
    w = cfg["objective_wert"]
    schl = o.schl
    if schl == "drache" and m.p is not None:
        seele = seele_ab(m)

        def wert_fuer(team):
            nr = drachen(m, team) + 1
            if nr >= seele:
                return w["drache_seele"]
            if nr == seele - 1 and seele >= 3:
                return w["drache_seelenpunkt"]
            return w["drache"]
        from ..zustand import gegenteam
        uns, ihnen = wert_fuer(m.p.mein_team), wert_fuer(gegenteam(m.p.mein_team))
        gross = max(drachen(m, m.p.mein_team), drachen(m, gegenteam(m.p.mein_team))) + 1 >= seele - 1 and seele >= 3
        return float(uns), float(ihnen), 0.0, gross
    uns = float(w.get(schl, 0))
    folge = 0.0
    if schl == "herold":
        from .wert import platte_gold
        folge = cfg["objective"]["herold_folge_anteil"] * 2 * platte_gold(m.zeit)   # grob: zwei Platten (Kapitel 7)
    return uns, uns, folge, schl in GROSS


def _p_erfolg(m, o, cfg: dict, mit_mir: bool) -> tuple[float, dict]:
    from . import gefahr, kampf
    from .modi import karte
    c = cfg["objective"]
    an = wir_an(m, o, mit_mir)
    tz = toetungszeit(m, o, cfg, an)
    if tz is None:
        return 0.0, {"an": an}
    n, t0, dauer = tz
    t1 = t0 + dauer
    T = t1 + c["puffer_s"]
    rest = 1.0
    gewichte = {}
    for g in m.b.gegner:
        if not g.s.tot or g.s.respawn < T:
            q = gefahr.p_da_am(g, T, m, cfg["gefahr"], o.pos)
            gewichte[g.s.name] = q
            rest *= 1.0 - q
    P_kampf = 1.0 - rest
    # EIN Kampfmodell (Buch 7, 3.2), gewichtet mit p_da an der Grube. Eure Leute zaehlen, wenn sie bis zum Ende dort
    # sein koennen - das Fenster ist daher T, nicht kampf_fenster_s allein (Abweichung, messungen.md Schritt 5)
    geher = {s.name for s, wo, *_ in m.b.mitspieler if not s.tot and wo is not None and geht_hin(m, o, s.name, wo)}
    geher -= mitkommende(m, o)                # wer bei dir steht, zaehlt nur mit dir (Nachtrag 3.3)
    if mit_mir:
        geher |= mitkommende(m, o)            # Buch 6, 3.3 Nachtrag: sie kaempfen mit, wenn du gehst
    p_g, auf = kampf.p_gewinn(m, o.pos, max(c["kampf_fenster_s"], T), gewichte=gewichte, cfg=cfg,
                              ohne_mich=not mit_mir or (m.tot and m.respawn > T), mitspieler_nur=geher)
    # Smite: der jeweilige Jungler lebt und kann bis zum Ende an der Grube sein
    j_die = m.b.jungler
    die_an, _ = karte.verteidiger(m, o.pos)
    smite_die = j_die is not None and any(g is j_die and t <= t1 for g, t in die_an)
    j_wir = next((s for s in (m.p.team(m.p.mein_team) if m.p else []) if s.rolle == "JUNGLE"), None)
    smite_wir = j_wir is not None and any(name == j_wir.champion and t <= t1 for name, t in an)
    p_steal = (c["steal_mit_smite"] if smite_wir else c["steal_ohne_smite"]) if smite_die else 0.0
    p = (1.0 - P_kampf * (1.0 - p_g)) * (1.0 - p_steal)
    zuerst = bool(die_an) and die_an[0][1] < (an[0][1] if an else 1e9)
    return p, {"n": n, "t0": t0, "dauer": dauer, "t1": t1, "P_kampf": P_kampf, "p_gewinn": p_g, "p_steal": p_steal,
               "an": an, "zuerst": zuerst, "die_an": [(g.champion, t) for g, t in die_an], "auf": auf}


def kampf_bei_ankunft(m, o, cfg: dict, weg: float) -> tuple[float, dict]:
    """Buch 6, 4.4: p_gewinn an der Grube, wenn DU ankommst - gekaempft wird dann, nicht am Ende eurer Toetungszeit;
    es zaehlt, wer bis weg + kampf_fenster_s dort ist (Abweichung, messungen.md Schritt 5)."""
    from . import gefahr, kampf
    T = weg + cfg["objective"]["kampf_fenster_s"]
    gewichte = {g.s.name: gefahr.p_da_am(g, T, m, cfg["gefahr"], o.pos) for g in m.b.gegner if not g.s.tot}
    return kampf.p_gewinn(m, o.pos, T, gewichte=gewichte, cfg=cfg)


def jungler_geht(m, o) -> bool:
    """Kapitel 6: euer Jungler lebt, ist bis Spawn + 5 s dort und steht <= 3000 von der Grube (oder hat sich ihr in 10 s um
    >= 1000 genaehert - Merkmale.jungler_wir_naeher)."""
    p, b = m.p, m.b
    if p is None or b is None:
        return False
    j = next((s for s in p.team(p.mein_team) if s.rolle == "JUNGLE" and s is not p.ich), None)
    if j is None or j.tot:
        return False
    wo = next((w for s, w, *_ in b.mitspieler if s.name == j.name), None)
    if wo is None:
        return False
    d = abstand(wo, o.pos)
    if d * WEGFAKTOR / MITSPIELER_TEMPO > max(0.0, o.spawn_in) + 5.0:
        return False
    return d <= 3000 or (getattr(m, "jungler_wir_naeher", {}) or {}).get(o.schl, 0.0) >= 1000


def gebraucht(m, o) -> tuple[bool, str]:
    """Kapitel 6 (bis 14:00): Prio (Welle GECRASHT_BEI_IHM oder Lane-Gegner tot bzw. im Brunnen) und euer Jungler geht
    hin; nie aus einer verlorenen Lane."""
    from .modi import lane_verloren
    from .modi import objectives_meine_seite
    if not m.lane_phase:
        return True, ""
    if lane_verloren(m)[0]:
        return False, "Lane verloren"
    if o.schl not in {x.schl for x in objectives_meine_seite(m)}:
        # Kapitel 6, Tabelle: die andere Kartenseite erreichst du in der Lane-Phase nicht zu Fuss - dort gilt TP_SPIEL
        return False, "andere Kartenseite (nur TP)"
    b = m.b
    prio = (m.welle is not None and m.welle.zustand == "GECRASHT_BEI_IHM") or (
        b is not None and b.lane is not None and (b.lane.s.tot or m.lane_im_brunnen))
    if not prio:
        return False, "keine Prio"
    if not jungler_geht(m, o):
        return False, "euer Jungler geht nicht hin"
    return True, "Prio und euer Jungler geht hin"


def urteil(m, o, cfg: dict) -> Urteil:
    u = Urteil(o.schl)
    if m.b is None:
        return u
    p, d = _p_erfolg(m, o, cfg, True)
    p0, _ = _p_erfolg(m, o, cfg, False)
    u.p_erfolg, u.p_erfolg_ohne = p, p0
    u.anteil = max(0.0, p - p0)
    u.n, u.t0, u.dauer, u.t1 = d.get("n", 0), d.get("t0", 0.0), d.get("dauer", 0.0), d.get("t1", 0.0)
    u.P_kampf, u.p_gewinn, u.p_steal = d.get("P_kampf", 0.0), d.get("p_gewinn", 0.0), d.get("p_steal", 0.0)
    u.die_zuerst = d.get("zuerst", False)
    u.wer = d.get("an", [])
    u.die_an = d.get("die_an", [])
    u.auf = d.get("auf", {})
    if m.b is not None and u.n:
        mit = {s.champion for s, *_ in m.b.mitspieler if s.name in mitkommende(m, o)}
        u.mit = [name for name, _ in u.wer[:u.n] if name in mit]
    u.wert_uns, u.wert_ihnen, u.folgewert, u.gross = werte(m, o, cfg)
    u.gebraucht, warum = gebraucht(m, o)
    c = cfg["objective"]
    if u.n == 0:
        u.grund = "zu wenige von euch rechtzeitig dort"
    elif p < c["vorbereiten_p_min"]:
        u.grund = f"p_erfolg {p:.2f} < {c['vorbereiten_p_min']}"
    elif u.anteil * u.wert_uns + u.folgewert <= 0:
        u.grund = "dein Anteil ist 0 - sie nehmen es ohne dich"
    elif not u.gebraucht:
        u.grund = warum
    else:
        u.zieht = True
        u.grund = warum or "ihr nehmt es, und du machst den Unterschied"
    return u


URTEIL_STABIL_S = 3.0     # ohne Ereignis kippt ein Urteil erst, wenn der neue Wert so lange besteht


def ereignis_stand(m, o) -> tuple:
    """Buch 6, 1.6: was ein Urteil kippen darf - Tod (ChampionKill), Spawn (lebt), Sichtung eines Unbekannten
    (unbekannt_anzahl), eine Struktur faellt."""
    p = m.p
    tode = len(p.kills_von("ChampionKill")) if p is not None else 0
    strukturen = sum(len(p.kills_von(e)) for e in ("TurretKilled", "InhibKilled")) if p is not None else 0
    return tode, strukturen, o.lebt, getattr(m, "unbekannt_anzahl", 0)


def urteile(m, cfg: dict) -> dict:
    """schl -> Urteil aller Objectives dieses Takts - einmal gerechnet, von allen Stellen gelesen (Merkmale.obj_urteile).
    Buch 6, 1.6: "Das Urteil haelt, bis ein Ereignis es kippt" - wechselt `zieht` ohne Ereignis, gilt das alte (102112
    30:10: Baron zog fuer einen Takt, und der Basis-Merker hielt "zum Baron" eine Minute lang)."""
    if getattr(m, "obj_urteile", None) is None:
        gd = getattr(m, "obj_gedaechtnis", None)
        aus = {}
        for o in m.objectives:
            u = urteil(m, o, cfg)
            if gd is not None:
                # kippt sofort mit einem Ereignis, sonst erst, wenn der neue Wert URTEIL_STABIL_S lang besteht (die
                # Ereignisliste ist unvollstaendig - Leben, Wege, ein Drachen-Kill; streng gehalten blieb in 102112
                # nach 35:16 ein falsches "zieht nicht" minutenlang stehen; Abweichung, messungen.md Schritt 5)
                stand = ereignis_stand(m, o)
                alt = gd.get(o.schl)
                if alt is None or alt["stand"] != stand or alt["zieht"] == u.zieht:
                    gd[o.schl] = {"stand": stand, "zieht": u.zieht, "neu": None}
                elif alt["neu"] is None or alt["neu"][0] != u.zieht:
                    alt["neu"] = (u.zieht, m.zeit)
                    u.zieht, u.grund = alt["zieht"], u.grund + " (gehalten: kein Ereignis)"
                elif m.zeit - alt["neu"][1] >= URTEIL_STABIL_S:
                    gd[o.schl] = {"stand": stand, "zieht": u.zieht, "neu": None}
                else:
                    u.zieht, u.grund = alt["zieht"], u.grund + " (gehalten: kein Ereignis)"
            aus[o.schl] = u
        m.obj_urteile = aus
    return m.obj_urteile


def urteil_von(m, o, cfg: dict) -> Urteil:
    u = urteile(m, cfg).get(o.schl)
    return u if u is not None else urteil(m, o, cfg)


def zieht(m, o, cfg: dict) -> bool:
    """Buch 6, 4.1: darf dieses Objective dich ziehen? Sonst behandeln STAPELN, OBJECTIVE_VORLAUF, WOHIN,
    objective_ruft, WELLE_UND_RAUS und ZUR_GRUPPE es, als gaebe es keins."""
    return urteil_von(m, o, cfg).zieht


def ziehende(m, cfg: dict, objectives=None) -> list:
    return [o for o in (m.objectives if objectives is None else objectives) if zieht(m, o, cfg)]


def sie_nehmen_es(m, o, cfg: dict) -> bool:
    """Kapitel 4.5: >= 2 Gegner sichtbar in grube_radius oder vor <= 10 s dort gesehen."""
    b = m.b
    if b is None:
        return False
    r = cfg["modus"]["grube_radius"]
    return sum(1 for g in b.gegner if not g.s.tot and g.pos is not None and abstand(g.pos, o.pos) <= r
               and (g.sichtbar or (g.seit is not None and g.seit <= 10.0))) >= 2


ZAHL = {2: "zwei", 3: "drei", 4: "vier", 5: "fünf"}


def grund(m, o, u: Urteil, art: str) -> str:
    """Der eine Grund (Kapitel 4.3, 9): aus P_kampf abgeleitet, hoechstens zwei Namen, keine Zahlen zum Selbstrechnen."""
    tote = [g.champion for g in (m.b.gegner if m.b is not None else []) if g.s.tot and g.s.respawn >= u.t1]
    if art == "VORBEREITEN_OBJECTIVE" and m.lane_phase:
        return f"dein Jungler ist {'unten' if o.schl in ('drache', 'aeltester') else 'oben'}"
    if u.n == 1 and u.die_an and art == "NEHMEN" and u.die_an[0][1] >= u.t1:
        # ein Fenster im Grund muss >= dein Weg + Dauer sein (Kapitel 9; 102112 26:35 hiess es sonst "der Erste von
        # ihnen braucht noch 0 Sekunden", waehrend Fiddlesticks daneben stand)
        return f"der Erste von ihnen braucht noch {int(u.die_an[0][1])} Sekunden"
    if u.P_kampf < 0.1:
        if len(tote) >= 3:
            return f"{ZAHL.get(len(tote), str(len(tote)))} von ihnen sind tot, keiner kommt rechtzeitig"
        if len(tote) >= 1:
            return f"{' und '.join(tote[:2])} {'ist' if len(tote) == 1 else 'sind'} tot, keiner kommt rechtzeitig"
        return "keiner von ihnen kommt rechtzeitig"
    wir = len(u.auf.get("wir", [])) if u.auf else max(1, u.n)
    if art == "NEHMEN":
        wir = max(1, u.n)                     # die, die es nehmen (n*), nicht jeder, der irgendwann kaeme
    if wir < 2:
        die = sorted(u.auf.get("die", []) if u.auf else [], key=lambda x: -x[1] * x[2])
        # Pruefung c, R2: kein "du schlaegst X" (das Modell ist nicht geeicht) - wer kommt, wird nur benannt
        return f"{die[0][0]} kommt dazu" if die else "du bist zuerst dort"
    satz = f"ihr seid {ZAHL.get(wir, str(wir))}"
    if u.auf and all(not x[3] for x in u.auf.get("wir", [])) and any(x[3] for x in u.auf.get("die", [])):
        satz += " mit Ults"
    return satz
