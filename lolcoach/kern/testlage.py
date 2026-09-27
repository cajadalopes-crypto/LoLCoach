"""Konstruierte Lagen (Buch 1, 6.2): aus den Feldern von tests/szenarien/konstruiert/*.toml Merkmale samt minimaler
Bewertung bauen und den Kern einen Takt entscheiden lassen - ohne Aufnahme, erster Takt, kein Vorplan.

    lage = testlage.bauen(eintrag)          # (Merkmale, Modus)
    ergebnis = testlage.pruefen(eintrag)    # {"id", "plan", "satz", "verstoesse": [...]}

Format der Felder: Kopfkommentar von tests/szenarien/konstruiert/lane.toml und recall.toml. Blau (ORDER), Top."""
from __future__ import annotations

import tomllib
from pathlib import Path

from .. import bewertung, ddragon, kaufplan
from ..bewertung import BRUNNEN, Bewertung, GegnerLage, abstand, einheiten
from ..zustand import Spieler
from . import Kern, konfig
from .merkmale import KaufInfo, Merkmale, ObjectiveLage, WellenStand, lane_punkt

ORDNER = Path(__file__).resolve().parent.parent.parent / "tests" / "szenarien" / "konstruiert"
TEMPO = 345.0
GRUBE = {"drache": "drache", "baron": "baron", "herold": "baron", "larven": "baron", "aeltester": "drache"}


def sekunden(text: str) -> float:
    m, s = str(text).split(":")
    return int(m) * 60 + float(s)


def _spieler(name: str, champion: str, team: str, rolle: str, level: int, tot: bool = False, respawn: float = 0.0,
             items: tuple = (), zauber: tuple = ("SummonerFlash", "SummonerTeleport")) -> Spieler:
    ch = ddragon.champions()
    cid = next((k for k, v in ch.items() if v.get("name") == champion or k == champion), champion)
    gold = sum(ddragon.items().get(i, {}).get("gold", {}).get("total", 0) for i in items)
    return Spieler(name, champion, cid, team, rolle, level, 0, 0, 0, 0, 0.0, tot, respawn, tuple(items), gold,
                   zauber, frozenset({name}))


class _Bewertung(Bewertung):
    """Wie die echte, nur `kraefte()` fest aus der Lage (lane_gegner.kraefte), wenn angegeben."""
    fest: float | None = None

    def kraefte(self):
        if self.fest is not None:
            return self.fest, [f"du {'vorn' if self.fest > 0 else 'hinten'} ({self.fest:+.1f})"]
        return super().kraefte()


def _max_hp(champion_id: str, level: int) -> float:
    st = ddragon.champions().get(champion_id, {}).get("stats", {})
    return float(st.get("hp", 650)) + float(st.get("hpperlevel", 105)) * (level - 1)


def bauen(e: dict) -> tuple[Merkmale, str]:
    cfg = konfig()
    zeit = sekunden(e["zeit"])
    modus = e.get("modus", "LANE")
    ich_d = e.get("ich", {})
    lane = "Top"
    inv = e.get("inventar", {})
    items = [2055] if inv.get("kontrollauge") else []
    items += [1036] * max(0, 6 - int(inv.get("frei", 3)) - len(items))      # Langschwerter belegen die Plaetze
    tot = modus == "TOT"
    ich = _spieler("Carlos", ich_d.get("champion", "Riven"), "ORDER", "TOP", int(ich_d.get("level", 6)), tot=tot,
                   respawn=float(e.get("respawn_in", 0.0)), items=tuple(items))
    leben = float(ich_d.get("leben", 1.0))
    welle_d = e.get("welle") or {}
    front = welle_d.get("front")
    if modus == "LANE":
        pos = einheiten(*lane_punkt(lane, front if front is not None else 0.45))
        bereich = "lane_eigen"
    else:
        pos = BRUNNEN["ORDER"]
        bereich = "basis_eigen"
    b = _Bewertung(zeit=zeit, ich=ich, gold=int(ich_d.get("gold", 0)), pos=None if tot else pos, ort="oben",
                   mein_tempo=TEMPO)
    b.leben = 0.0 if tot else leben
    b.leben_abs = int(_max_hp(ich.champion_id, ich.level) * b.leben)
    b.flash = float(ich_d.get("flash_in", 0))
    if "tp_in" in ich_d:
        b.zweiter = ("SummonerTeleport", float(ich_d["tp_in"]))
    turm = einheiten(*lane_punkt(lane, cfg["welle"]["turm_dein"]))
    if not tot:
        b.zum_turm = abstand(pos, turm) * bewertung.WEGFAKTOR / TEMPO if modus == "LANE" else 0.0
        b.turm_name = "deinem Top-Tier-1-Turm" if modus == "LANE" else "deiner Basis"
        b.unter_eigenem_turm = b.zum_turm <= 2.5
        b.tiefe = front if modus == "LANE" else None
    b.tod_kostet = bewertung.todeszeit(ich.level, zeit)
    b.fest = e.get("lane_gegner", {}).get("kraefte")
    # Gegner: dein Lane-Gegner und der Jungler
    lg = e.get("lane_gegner")
    im_brunnen = False
    if lg is not None:
        s = _spieler("Gegner-Top", lg.get("champion", "Sett"), "CHAOS", "TOP", int(lg.get("level", ich.level)),
                     tot="tot_noch" in lg, respawn=float(lg.get("tot_noch", 0.0)))
        im_brunnen = bool(lg.get("im_brunnen"))
        sichtbar = bool(lg.get("sichtbar", True)) and not s.tot and not im_brunnen
        ab = lg.get("abstand")
        tempo = bewertung.tempo(s)
        if im_brunnen:
            ab_b = abstand(pos, BRUNNEN["CHAOS"]) if pos else None
            gpos, seit, ankunft, ab = BRUNNEN["CHAOS"], 5.0, (ab_b / (tempo * 1.1) - 5.0) if ab_b else None, ab_b
        elif s.tot:
            gpos, seit, ankunft = None, None, None
        else:
            gpos = (pos[0] + ab, pos[1]) if pos and ab is not None else None
            seit = 0.0 if sichtbar else 10.0
            ankunft = max(0.0, ab / (tempo * 1.1) - seit) if ab is not None else None
        g = GegnerLage(s, sichtbar, seit, "oben", ab if not s.tot else None, ankunft, tempo, None, None,
                       s.level - ich.level, 0, kommt_naeher=bool(lg.get("kommt_naeher")), pos=gpos,
                       leben=lg.get("leben"), leben_alter=0.5 if lg.get("leben") is not None else None)
        b.gegner.append(g)
        b.lane = g
        if s.tot:
            b.tote_gegner.append(s)
    jd = e.get("jungler")
    if jd is not None:
        s = _spieler("Gegner-Jungle", jd.get("champion", "Fiddlesticks"), "CHAOS", "JUNGLE",
                     int(jd.get("level", max(1, ich.level - 1))))
        seit = jd.get("seit")
        sichtbar = seit == 0
        ab = jd.get("abstand")
        tempo = bewertung.tempo(s)
        ankunft = max(0.0, ab / (tempo * 1.1) - (seit or 0.0)) if ab is not None else None
        gpos = (pos[0] + ab, pos[1]) if pos and ab is not None else None
        g = GegnerLage(s, sichtbar, float(seit) if seit is not None else None, "oben", ab, ankunft, tempo, None,
                       None, s.level - ich.level, 0, pos=gpos)
        b.gegner.append(g)
        b.jungler = g
    # Merkmale
    m = Merkmale(zeit, tot, None if tot else pos, None if tot else bereich, lane, zeit < 840, None if tot else leben,
                 None, False, mein_tempo=TEMPO)
    m.b, m.p = b, None
    m.respawn = float(e.get("respawn_in", 0.0))
    m.lane_im_brunnen = im_brunnen
    if welle_d:
        z = welle_d.get("zustand", "UNBEKANNT")
        m.welle = WellenStand(lane, welle_d.get("unsere"), welle_d.get("ihre"), front, welle_d.get("trend"), z,
                              zeit - 10.0, z != "UNBEKANNT", cfg["welle"]["turm_dein"], cfg["welle"]["turm_ihr"])
    vw = (e.get("vorher") or {}).get("welle")
    if vw:
        m.welle_vorher = WellenStand(lane, vw.get("unsere"), vw.get("ihre"), vw.get("front"), vw.get("trend"),
                                     vw["zustand"], zeit - 20.0, True)
    m.kanone_in = e.get("kanone_in")
    m.p_jungler = (jd or {}).get("p_meine_seite")
    m.tp_in = float(ich_d["tp_in"]) if "tp_in" in ich_d else None
    k = e.get("kauf") or {}
    lohnt = bool(k.get("lohnt"))
    plan = kaufplan.plan(ich.champion_id, ich.items, b.gold) if lohnt else None
    kaufen = list(plan.kaufen) if plan is not None and plan.kaufen else ([] if not lohnt else ["Der Brutalisierer"])
    kosten = plan.kosten if plan is not None and plan.kaufen else (min(b.gold, 1337) if lohnt else 0)
    m.kauf = KaufInfo(kaufen, int(kosten), lohnt, bool(k.get("kern_fertig")))
    for schl, feld in (("objective", None), ("drache", "drache")):
        o = e.get(schl)
        if o is None:
            continue
        name = o.get("schl", feld)
        grube = einheiten(*bewertung.GRUBEN[GRUBE[name]])
        weg = o.get("weg")
        if weg is None and m.pos is not None:
            weg = abstand(m.pos, grube) * bewertung.WEGFAKTOR / TEMPO
        spawn = float(o.get("spawn_in", 0))
        m.objectives.append(ObjectiveLage(name, spawn <= 0, max(0.0, spawn), grube, weg, 0, 0, None, 0))
    if (jw := e.get("jungler_wir")) is not None:
        # Buch 6, Kapitel 6: euer Jungler, `abstand` Einheiten vor der Grube des (ersten) Objectives - dafuer braucht
        # die Lage eine Partie (sonst gibt es kein "euer Team")
        from ..zustand import Partie
        j = _spieler("Freund-Jungle", jw.get("champion", "Diana"), "ORDER", "JUNGLE", int(jw.get("level", ich.level)))
        ziel = m.objectives[0].pos if m.objectives else pos
        wo = (ziel[0] - float(jw.get("abstand", 2000)), ziel[1])
        b.mitspieler.append((j, wo, 1.0, ""))
        m.mitspieler = [(j, wo)]
        m.p = Partie(zeit, "CLASSIC", [ich, j, *(g.s for g in b.gegner)], ich, float(b.gold), [], False)
    m.daten_frisch = True
    return m, modus


# --- Buch 5: das erweiterte Format von mitte.toml (Karte nach der Lane-Phase) ---------------------------------------

MITTE_MODI = ("SEITE", "GRUPPE", "UNTERWEGS", "VERTEIDIGEN")
STANDARD_GEGNER = (("Sett", "TOP"), ("Fiddlesticks", "JUNGLE"), ("Galio", "MIDDLE"), ("Kai'Sa", "BOTTOM"),
                   ("Sona", "UTILITY"))
MITSPIELER_ROLLEN = ("JUNGLE", "MIDDLE", "BOTTOM", "UTILITY")
PUNKT = {"fluss_oben": (0.33, 0.35), "fluss_unten": (0.67, 0.65), "fluss_mitte": (0.5, 0.5),
         "jungle_eigen_oben": (0.22, 0.45), "jungle_eigen_unten": (0.55, 0.78),
         "jungle_fremd_oben": (0.45, 0.22), "jungle_fremd_unten": (0.78, 0.55)}
STUFE_NAME = {"aussen": "3", "innen": "2", "Inhib": "1"}
LANE_NR = {"Top": "2", "Mid": "1", "Bot": "0"}
S_JE_ZUSTAND = {"GECRASHT_BEI_IHM": None, "GECRASHT_BEI_DIR": None, "ZU_DIR": 0.42, "GROSS_ZU_DIR": 0.42,
                "ZU_IHM": 0.55, "GROSS_ZU_IHM": 0.55, "MITTE": 0.5, "LEER": 0.5}


def _ereignisse(e: dict, zeit: float) -> list:
    """TurretKilled/InhibKilled fuer alles, was laut `tuerme`/`inhibs_weg` nicht mehr steht (Carlos: blau/ORDER)."""
    from ..zustand import Ereignis
    aus, n = [], 0
    for seite, team, kurz in (("eure", "ORDER", "Order"), ("ihre", "CHAOS", "Chaos")):
        stehend = e.get("tuerme", {}).get(seite)
        if stehend is None:
            continue
        for (t, lane, stufe) in bewertung.TUERME:
            if t != team or f"{lane}:{stufe}" in stehend:
                continue
            n += 1
            aus.append(Ereignis(n, zeit - 60, "TurretKilled",
                                {"TurretKilled": f"Turret_T{kurz}_L{LANE_NR[lane]}_P{STUFE_NAME[stufe]}_x"}, None))
        for lane in e.get("inhibs_weg", {}).get(seite, []):
            n += 1
            aus.append(Ereignis(n, zeit - 30, "InhibKilled", {"InhibKilled": f"Inhib_T{kurz}_L{LANE_NR[lane]}_P1_x"},
                                None))
    return aus


def _lane_s(lane: str, w: dict | None, turm_dein: float, turm_ihr: float) -> float:
    """Wo auf der Lane du stehst: an der Front der Welle dieser Lane (aus deiner Sicht), sonst in der Mitte."""
    if not w:
        return 0.5
    if w.get("front") is not None:
        return float(w["front"])
    z = w.get("zustand", "MITTE")
    if z == "GECRASHT_BEI_DIR":
        return turm_dein + 0.03
    if z == "GECRASHT_BEI_IHM":
        return turm_ihr - 0.03
    return S_JE_ZUSTAND.get(z) or 0.5


def _punkt(bereich: str | None, e: dict, turm: dict, modus: str) -> tuple[float, float]:
    """Spiel-Einheiten eines Bereich-Codes (blaue Seite)."""
    if not bereich:
        return einheiten(0.5, 0.5)
    if bereich.startswith("lane:"):
        lane = bereich.split(":", 1)[1]
        s = _lane_s(lane, e.get("wellen", {}).get(lane), *turm[lane])
        return einheiten(*lane_punkt(lane, s))
    if bereich.startswith("grube:"):
        return einheiten(*bewertung.GRUBEN[bereich.split(":", 1)[1]])
    if bereich == "basis_eigen":
        return BRUNNEN["ORDER"] if modus in ("BASIS", "TOT") else (1700.0, 1700.0)
    if bereich == "basis_fremd":
        return BRUNNEN["CHAOS"]
    return einheiten(*PUNKT.get(bereich, (0.5, 0.5)))


def _richtung(von: tuple, nach: tuple, weite: float) -> tuple[float, float]:
    d = abstand(von, nach)
    if d < 1:
        nach, d = BRUNNEN["CHAOS"], abstand(von, BRUNNEN["CHAOS"])
    return von[0] + (nach[0] - von[0]) * weite / d, von[1] + (nach[1] - von[1]) * weite / d


def bauen_mitte(e: dict) -> tuple[Merkmale, str]:
    """Merkmale fuer SEITE/GRUPPE/UNTERWEGS/VERTEIDIGEN: echte Partie (gefallene Tuerme als Ereignisse), alle drei
    Wellen, Mitspieler, fuenf Gegner (fehlende: unbekannt), Teamkampf, Antwort-Kraft (Kopfkommentar mitte.toml)."""
    from ..zustand import Partie
    from .merkmale import Teamkampf, lane_hier, mitte_merkmale, turm_s
    cfg = konfig()
    zeit = sekunden(e["zeit"])
    modus = e.get("modus", "SEITE")
    ich_d = e.get("ich", {})
    level = int(ich_d.get("level", 15))
    ich = _spieler("Carlos", ich_d.get("champion", "Riven"), "ORDER", "TOP", level,
                   zauber=("SummonerFlash", "SummonerTeleport"))
    freunde = [_spieler(f"Freund{i}", f["champion"], "ORDER", MITSPIELER_ROLLEN[i % 4], level)
               for i, f in enumerate(e.get("mitspieler", []))]
    angaben = {g.get("rolle"): g for g in e.get("gegner", [])}
    k = e.get("teamkampf")
    if k is not None and not e.get("gegner"):
        # die Gegner des Kampfs stehen sichtbar dort (sonst waeren sie fuer die Gefahr "unbekannt")
        for champion, rolle in STANDARD_GEGNER[:int(k.get("gegner", 0))]:
            angaben[rolle] = {"champion": champion, "rolle": rolle, "bereich": k.get("ort"), "seit": 0}
    feinde = []
    for champion, rolle in STANDARD_GEGNER:
        g = angaben.get(rolle, {"champion": champion, "rolle": rolle})
        feinde.append(_spieler(f"Gegner-{rolle}", g.get("champion", champion), "CHAOS", rolle,
                               int(g.get("level", level - 1)), tot="tot_noch" in g, respawn=float(g.get("tot_noch", 0.0))))
    p = Partie(zeit, "CLASSIC", [ich, *freunde, *feinde], ich, float(ich_d.get("gold", 0)), _ereignisse(e, zeit), False)
    stehen = bewertung.stehende_tuerme(p)
    turm = {lane: (turm_s(lane, "ORDER", "ORDER", stehen, 0.35), turm_s(lane, "CHAOS", "ORDER", stehen, 0.65))
            for lane in ("Top", "Mid", "Bot")}
    bereich = ich_d.get("bereich", "lane:Top")
    pos = _punkt(bereich, e, turm, modus)
    if bereich == "lane:Top":
        bereich = "lane_eigen"                      # deine eigene Lane (Carlos: Top), wie live
    leben = float(ich_d.get("leben", 1.0))
    b = _Bewertung(zeit=zeit, ich=ich, gold=int(ich_d.get("gold", 0)), pos=pos, ort="", mein_tempo=TEMPO, partie=p)
    b.leben, b.leben_abs = leben, int(_max_hp(ich.champion_id, level) * leben)
    b.flash = float(ich_d.get("flash_in", 0))
    if "tp_in" in ich_d:
        b.zweiter = ("SummonerTeleport", float(ich_d["tp_in"]))
    b.tod_kostet = bewertung.todeszeit(level, zeit)
    eigene = [(k, v) for k, v in stehen.items() if k[0] == "ORDER"] + [(None, BRUNNEN["ORDER"])]
    naechster, wo = min(eigene, key=lambda kv: abstand(pos, kv[1]))
    b.zum_turm = abstand(pos, wo) * bewertung.WEGFAKTOR / TEMPO
    b.turm_name = (f"deinem {naechster[1]}-Tier-{bewertung.TIER[naechster[2]]}-Turm" if naechster else "deiner Basis")
    b.unter_eigenem_turm = b.zum_turm <= 2.5
    for s, f in zip(freunde, e.get("mitspieler", [])):
        wo_f = pos if f.get("bereich") == ich_d.get("bereich") else _punkt(f.get("bereich"), e, turm, modus)
        b.mitspieler.append((s, wo_f, f.get("leben"), f.get("bereich", "")))
        if abstand(pos, wo_f) <= 1500:
            b.mitspieler_nah.append(s)
    for s in feinde:
        g = angaben.get(s.rolle, {})
        seit = g.get("seit")
        sichtbar = seit == 0 and not s.tot
        tempo = bewertung.tempo(s)
        ab = g.get("abstand")
        if s.tot or seit is None:
            gpos, ab = None, None
        elif ab is not None and g.get("bereich") == ich_d.get("bereich"):
            gpos = _richtung(pos, _punkt(g.get("bereich"), e, turm, modus), ab)
            if abstand(gpos, pos) < 1:
                gpos = _richtung(pos, BRUNNEN["CHAOS"], ab)
        else:
            gpos = _punkt(g.get("bereich"), e, turm, modus)
            ab = ab if ab is not None else abstand(pos, gpos)
        ankunft = max(0.0, ab / (tempo * 1.1) - (seit or 0.0)) if ab is not None and seit is not None else None
        gl = GegnerLage(s, sichtbar, None if seit is None else float(seit), g.get("bereich", ""),
                        ab, ankunft, tempo, None, None, s.level - ich.level, 0, pos=gpos)
        b.gegner.append(gl)
        if s.tot:
            b.tote_gegner.append(s)
        if s.rolle == "TOP":
            b.lane = gl
        if s.rolle == "JUNGLE":
            b.jungler = gl
    b.tote_eigene = []
    m = Merkmale(zeit, False, pos, bereich, "Top", False, leben, None, False, mein_tempo=TEMPO,
                 mitspieler=[(s, wo) for s, wo, *_ in b.mitspieler])
    m.b, m.p = b, p
    for lane, w in e.get("wellen", {}).items():
        z = w.get("zustand", "MITTE")
        dein, ihr = turm[lane]
        m.wellen[lane] = WellenStand(lane, w.get("unsere"), w.get("ihre"), _lane_s(lane, w, dein, ihr), None, z,
                                     zeit - 10.0, True, dein, ihr)
    m.welle = m.wellen.get("Top")
    m.tp_in = float(ich_d["tp_in"]) if "tp_in" in ich_d else None
    top = angaben.get("TOP", {})
    m.tp_gegner_top = float(top["tp_in"]) if "tp_in" in top else None
    m.kauf = KaufInfo([], 0, False, False)
    if e.get("antwort_kraft") is not None:
        m.antwort_kraft = float(e["antwort_kraft"])
    for o in e.get("objectives", []):
        grube = einheiten(*bewertung.GRUBEN[GRUBE[o["schl"]]])
        spawn = float(o.get("spawn_in", 0))
        nah = sum(1 for _, wo_f, *_ in b.mitspieler if abstand(wo_f, grube) <= 1500)
        m.objectives.append(ObjectiveLage(o["schl"], bool(o.get("lebt")) or spawn <= 0, max(0.0, spawn), grube,
                                          o.get("weg"), nah, nah, None, 0))
    if (k := e.get("teamkampf")) is not None:
        kpos = _punkt(k.get("ort"), e, turm, modus)
        m.teamkampf = Teamkampf(k.get("ort"), kpos, int(k.get("eigene", 0)), int(k.get("gegner", 0)),
                                float(k.get("seit", 0)), int(k.get("tote_eigene", 0)), int(k.get("tote_gegner", 0)),
                                float(k.get("dein_weg", 0)) if k.get("dein_weg") is not None else m.weg(kpos))
    m.p_jungler = _p_jungler(m, b.jungler, e)
    m.lane_hier = lane_hier(m)
    mitte_merkmale(m, cfg["mitte"])
    m.daten_frisch = True
    return m, modus


def _p_jungler(m: Merkmale, j, e: dict) -> float | None:
    """Wie `jungle.wahrscheinlich` im Spiel: die Seite seiner letzten Sichtung, verblasst ueber 90 s - ohne Sichtung
    (oder `jungler.p_meine_seite` in der Lage) None, dann rechnet p_seite mit 0,5."""
    if (jd := e.get("jungler")) and "p_meine_seite" in jd:
        return jd["p_meine_seite"]
    if j is None or j.pos is None or j.seit is None:
        return None
    from ..bewertung import BREITE, HOEHE
    from ..jungle import anders, seite
    from .merkmale import meine_seite
    dort = seite(j.pos[0] / BREITE, 1.0 - j.pos[1] / HOEHE)
    bleibt = max(0.35, 1.0 - j.seit / 90)
    w = {dort: bleibt, anders(dort): 1.0 - bleibt}
    s = meine_seite(m)
    return max(w.values()) if s is None else w[s]


def pruefen(e: dict, modi: tuple | None = None) -> dict:
    """Ein Takt des Kerns auf der Lage; Rueckgabe: Plan, Satz, Top-3 und die Verstoesse gegen soll/darf_nicht/
    satz_enthaelt."""
    m, modus = bauen_mitte(e) if e.get("modus") in MITTE_MODI else bauen(e)
    k = Kern(stellung="neu", modi=modi)
    k.m = m
    ansagen = k.schritt(m, modus)
    plan = k.fuehrer.plan
    art = plan.art if plan is not None else None
    satz = ansagen[0].text if ansagen else (plan.handlung.satz if plan is not None else "")
    verstoesse = []
    if e.get("soll") and art not in e["soll"]:
        verstoesse.append(f"soll {e['soll']} - Plan {art}")
    if art is not None and art in e.get("darf_nicht", []):
        verstoesse.append(f"darf_nicht {e['darf_nicht']} - Plan {art}")
    for text in e.get("satz_enthaelt", []):
        if text.lower() not in (satz or "").lower():
            verstoesse.append(f"satz_enthaelt '{text}' - \"{satz}\"")
    return {"id": e["id"], "plan": art, "satz": satz, "gefahr": k.gefahr,
            "top": [(h.art, round(h.ev), round(h.p_tod, 2)) for h in sorted(k.kandidaten, key=lambda h: -h.ev)],
            "verstoesse": verstoesse}


def alle(ordner: Path = ORDNER, modi: tuple | None = None) -> list[dict]:
    """Alle Lagen; die in Modi, in denen der Kern noch nicht entscheidet (Schritt 3: nur LANE, BASIS, TOT), kommen mit
    `uebersprungen` zurueck - sie sind die Abnahme eines spaeteren Schritts (z. B. mitte.toml, Buch 5, Schritt 4)."""
    from . import KERN_MODI
    modi = modi or KERN_MODI
    aus = []
    for datei in sorted(ordner.glob("*.toml")):
        for e in tomllib.loads(datei.read_text(encoding="utf-8")).get("lage", []):
            modus = e.get("modus", "LANE")
            if modus not in modi:
                aus.append({"id": e["id"], "datei": datei.name, "plan": None, "satz": "", "gefahr": False, "top": [],
                            "verstoesse": [], "uebersprungen": f"der Kern entscheidet in {modus} noch nicht"})
                continue
            r = pruefen(e, modi)
            r["datei"] = datei.name
            aus.append(r)
    return aus
