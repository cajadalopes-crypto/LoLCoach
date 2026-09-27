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
GRUBE = {"drache": "drache", "baron": "baron", "herold": "baron", "larven": "baron"}


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
    m.daten_frisch = True
    return m, modus


def pruefen(e: dict) -> dict:
    """Ein Takt des Kerns auf der Lage; Rueckgabe: Plan, Satz, Top-3 und die Verstoesse gegen soll/darf_nicht/
    satz_enthaelt."""
    m, modus = bauen(e)
    k = Kern(stellung="neu")
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


def alle(ordner: Path = ORDNER) -> list[dict]:
    aus = []
    for datei in sorted(ordner.glob("*.toml")):
        for e in tomllib.loads(datei.read_text(encoding="utf-8")).get("lage", []):
            r = pruefen(e)
            r["datei"] = datei.name
            aus.append(r)
    return aus
