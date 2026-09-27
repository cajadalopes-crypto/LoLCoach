"""Modi BASIS und TOT (Buch 0, 6.3; Buch 3, Kapitel 3 und 4): was kaufst du, und wohin danach.

KAUFEN nennt Items mit Namen aus dem Kaufplan (hoechstens drei Dinge, Kontroll-Auge dazu, wenn keins im Inventar
ist, ein Platz frei ist und 75 Gold uebrig bleiben; ist es der Fokus des Tages, zuerst), dazu in einem Satz das
Ziel (WOHIN). In der Lane-Phase ist das Ziel die Lane - mit der Wellen-Uhr - oder ein Objective auf deiner Seite;
TP zur Lane, wenn dort mehr auf dem Spiel steht, als das TP bis zum naechsten Objective wert ist. Danach das beste
Ziel aus bewertung.ziele (bis Buch 5). TOT: 8 s vor dem Respawn einmal Kauf und Ziel."""
from __future__ import annotations

from ... import ddragon, komponist
from ...entscheider import LAUF_ZUR_LANE, wellen_spawns
from .. import wert
from ..handlung import Handlung, Ziel
from . import KONTROLLAUGE, OBJ_NAME, _akk, lane_von, liste, objectives_meine_seite, uhr

ZUM = {"drache": "zum Drachen", "baron": "zum Baron", "herold": "zum Herold", "larven": "zu den Larven"}
DRUECKT = ("ZU_DIR", "GROSS_ZU_DIR", "GECRASHT_BEI_DIR")


def _tp_abklingzeit(m, cfg: dict) -> float:
    c = cfg["recall"]
    if m.zeit < 600:
        return c["tp_abklingzeit_s"]
    return 330.0 - (max(1, m.b.ich.level) - 1) * 90.0 / 17.0      # Unleashed, saison2026.md


def _tp_verlust(m, cfg: dict) -> tuple[float, str]:
    """Was auf deiner Lane verloren geht, wenn du laeufst (Buch 3, 4.1), aus deiner Welle beim Recall."""
    w = m.welle_vorher
    if w is None:
        return 0.0, ""
    ww = wert.wellenwert(m.zeit, cfg)
    if w.zustand in DRUECKT:
        ihre = w.ihre if w.ihre is not None else 6
        return ww * ihre / 6.0 + (cfg["welle"]["gross_zuschlag"] if ihre > 6 else 0.0), \
            f"{ihre} Vasallen laufen auf deinen Turm"
    if w.zustand == "GECRASHT_BEI_IHM":
        return 0.5 * ww, ""
    return 0.0, ""


def wohin(m, cfg: dict, modus: str) -> Handlung:
    """WOHIN / WOHIN_TP_LANE mit `daten['kurz']` (fuer den Kauf-Satz: "Top", "zu den Larven") und `grund`."""
    b, c = m.b, cfg["recall"]
    lane = lane_von(m)
    if m.lane_phase:
        verlust, druck = _tp_verlust(m, cfg)
        tp_cd = _tp_abklingzeit(m, cfg)
        braucht_tp = [o for o in m.objectives if o.spawn_in + c["tp_objective_nachlauf_s"] < tp_cd]
        if m.tp_in == 0 and verlust >= c["tp_lane_wert_min"] and not braucht_tp:
            naechstes = min(m.objectives, key=lambda o: o.spawn_in, default=None)
            spaeter = (f", {OBJ_NAME[naechstes.schl]} erst in {komponist.sek(naechstes.spawn_in)}"
                       if naechstes is not None else "")
            grund = (druck or "deine Welle wartet") + spaeter
            h = Handlung("WOHIN_TP_LANE", Ziel("lane", f"deine {lane}-Welle"), modus, 5.0, gewinn=verlust,
                         grund=grund, satz=f"TP auf deine {lane}-Welle: {grund}.")
            h.daten["kurz"] = f"TP auf deine {lane}-Welle"
            return h
        for o in objectives_meine_seite(m):
            if o.weg is not None and (o.lebt or o.spawn_in <= 100) and o.weg <= o.spawn_in + 10:
                grund = f"Spawn {uhr(m.zeit + o.spawn_in)}, du bist {uhr(m.zeit + o.weg)} dort"
                h = Handlung("WOHIN", Ziel("objective", OBJ_NAME[o.schl], o.pos, o.weg), modus, o.weg,
                             grund=grund, satz=f"{ZUM[o.schl][0].upper()}{ZUM[o.schl][1:]}: {grund}.")
                h.daten["kurz"] = ZUM[o.schl]
                return h
        if druck:
            grund = druck
        else:
            # die erste Welle, die du noch erreichst: dein Weg zu deinem Turm gegen die Wellen-Uhr (Buch 3, 4.1)
            lauf = LAUF_ZUR_LANE.get(b.ich.rolle, 27.0)
            weg = _weg_zur_lane(m, lane)
            ankunft = min((t + lauf for t, _ in wellen_spawns(m.zeit + 90) if t + lauf > m.zeit + weg - 5),
                          default=None)
            grund = (f"nächste Welle in {komponist.sek(ankunft - m.zeit)}, du brauchst {int(weg)}" if ankunft
                     else "deine Welle wartet")
        h = Handlung("WOHIN", Ziel("lane", lane), modus, 20.0, grund=grund, satz=f"Zurück nach {lane}: {grund}.")
        h.daten["kurz"] = lane
        return h
    # nach der Lane-Phase: das beste Ziel der Karten-Rechnung (Buch 5, Kapitel 2) - ein Turm oder eine Seitenwelle
    if (h := _karten_ziel(m, cfg, modus)) is not None:
        return h
    # sonst das Ziel der alten Bewertung; in den Kauf-Satz nur sein Grund (133930, 17:57: "Kauf ..., dann auf den
    # Bot-Inhibitor-Turm: Geh auf den Bot-Inhibitor-Turm, ...")
    z = komponist.bestes_ziel(b) if b.partie is not None and b.pos is not None else None
    if z is not None:
        satz = komponist.ziel_satz(b, z)
        grund = satz.removeprefix(f"Geh {z.lane} und ") if z.art == "verteidigen" else satz.split(": ", 1)[-1]
        h = Handlung("WOHIN", Ziel("turm", z.name, z.pos, z.weg), modus, z.weg, grund=grund.rstrip("."), satz=satz)
        h.daten["kurz"] = f"auf {z.name}" if z.art == "turm" else f"nach {z.lane}"
        return h
    for o in sorted(m.objectives, key=lambda o: o.spawn_in):
        if o.spawn_in <= 90:
            lebt = "leben" if o.schl == "larven" else "lebt"
            grund = f"{OBJ_NAME[o.schl]} {lebt if o.lebt else 'um ' + uhr(m.zeit + o.spawn_in)}"
            h = Handlung("WOHIN", Ziel("objective", OBJ_NAME[o.schl], o.pos, o.weg), modus, o.weg or 30.0,
                         grund=grund, satz=f"{ZUM[o.schl][0].upper()}{ZUM[o.schl][1:]}: {grund}.")
            h.daten["kurz"] = ZUM[o.schl]
            return h
    grund = f"deine {lane}-Welle wartet"
    h = Handlung("WOHIN", Ziel("lane", lane), modus, 30.0, grund=grund, satz=f"Geh nach {lane}: {grund}.")
    h.daten["kurz"] = f"nach {lane}"
    return h


def _karten_ziel(m, cfg: dict, modus: str) -> Handlung | None:
    """Buch 5, Kapitel 2 aus der Basis: der Turm (DRUECKEN, ohne Split-Regel - du bist nicht auf einer Seite) oder
    die Seitenwelle mit dem hoechsten EV, wenn er positiv ist; sonst None (dann das alte Ziel)."""
    from . import karte
    ziele = karte.turm_handlungen(m, cfg, modus, "DRUECKEN", split=False)
    for lane, w in (m.seitenwellen or {}).items():
        if (h := karte.seitenwelle(m, cfg, modus, lane, w)) is not None:
            ziele.append(h)
    for h in ziele:
        wert.bewerte(h, m, cfg)
    beste = max(ziele, key=lambda h: h.ev, default=None)
    if beste is None or beste.ev <= 0:
        return None
    if beste.art == "SEITENWELLE":
        lane = beste.daten["lane"]
        kurz, satz = f"zur {lane}-Welle", beste.satz
    else:
        kurz = f"auf {beste.ziel.name}"
        satz = f"Geh {kurz}: {beste.grund}."
    h = Handlung("WOHIN", beste.ziel, modus, beste.dauer, grund=beste.grund, satz=satz)
    h.daten["kurz"] = kurz
    return h


def _weg_zur_lane(m, lane: str) -> float:
    """Deine Laufzeit zu deinem vordersten stehenden Turm dieser Lane (Minimap-Geometrie), sonst ~25 s."""
    from ... import bewertung
    from ..merkmale import lane_punkt
    if m.pos is None:
        return 25.0
    w = m.welle_vorher or m.welle
    s = w.turm_dein if w is not None else 0.35
    blau = m.p is None or m.p.mein_team == "ORDER"
    ziel = bewertung.einheiten(*lane_punkt(lane, s if blau else 1.0 - s))
    return bewertung.abstand(m.pos, ziel) * bewertung.WEGFAKTOR / (m.mein_tempo or 345.0)


def kontrollauge_dazu(m) -> bool:
    """Buch 3, 3.3: keins im Inventar, ein Platz frei, nach dem Kern-Kauf >= 75 Gold uebrig."""
    b, k = m.b, m.kauf
    if KONTROLLAUGE in b.ich.items:
        return False
    it = ddragon.items()
    belegt = [i for i in b.ich.items if i in it and "Trinket" not in it[i].get("tags", [])]
    rest = b.gold - (k.kosten if k is not None and k.kaufen else 0)
    return len(belegt) < 6 and rest >= 75


def _fokus_kontrollauge(m) -> bool:
    f = getattr(m, "fokus", None) or ""
    return "kontroll" in f.lower()


def kaufen(m, cfg: dict, modus: str, ziel: Handlung) -> Handlung | None:
    """KAUFEN mit Namen und dem Ziel in einem Satz (9.3 BASIS)."""
    k = m.kauf
    if k is None or not k.kaufen:
        return None
    teile = [_akk(x) for x in k.kaufen[:2]]
    if kontrollauge_dazu(m):
        if _fokus_kontrollauge(m):
            teile = ["ein Kontroll-Auge"] + teile
        else:
            teile.append("ein Kontroll-Auge")
    teile = teile[:3]
    was = liste(teile)
    verkauf = f"Verkauf {k.verkaufen}, dann k" if k.verkaufen else "K"
    satz = f"{verkauf}auf {was}, dann {ziel.daten['kurz']}: {ziel.grund}."
    h = Handlung("KAUFEN", Ziel("basis", was), modus, 5.0, gewinn=k.kosten * cfg["kauf"]["kauf_faktor"] + 1000.0,
                 grund=ziel.grund, satz=satz, schritte=["kaufen", ziel.art])
    h.daten.update(wohin=ziel, items=list(k.kaufen), kontrollauge="ein Kontroll-Auge" in teile,
                   gold_start=m.b.gold, kauf_sprung=cfg["recall"]["kauf_sprung"], folge_art={1: ziel.art})
    h.erfuellt = _gekauft
    return h


def _gekauft(m, plan) -> bool:
    """KAUFEN, Schritt "kaufen": das Gold ist um einen Kauf gefallen - danach gilt der Plan als sein Ziel weiter."""
    d = plan.handlung.daten
    return plan.schritt == 0 and m.b is not None and m.b.gold <= d["gold_start"] - d["kauf_sprung"]


def kandidaten(m, cfg: dict) -> list[Handlung]:
    z = wohin(m, cfg, "BASIS")
    aus = [z]
    if (k := kaufen(m, cfg, "BASIS", z)) is not None:
        aus.append(k)
    elif kontrollauge_dazu(m) and m.b.gold >= 75:
        mit = z.satz.rstrip(".") + ", nimm ein Kontroll-Auge mit."
        if len(mit.split()) <= cfg["sprechen"]["max_woerter"]:
            z.satz = mit
    return aus
