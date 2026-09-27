"""Modi BASIS und TOT (Buch 0, 6.3; Buch 3, Kapitel 3 und 4): was kaufst du, und wohin danach.

KAUFEN nennt Items mit Namen aus dem Kaufplan (hoechstens drei Dinge, Kontroll-Auge dazu, wenn keins im Inventar
ist, ein Platz frei ist und 75 Gold uebrig bleiben; ist es der Fokus des Tages, zuerst), dazu in einem Satz das
Ziel (WOHIN). In der Lane-Phase ist das Ziel die Lane - mit der Wellen-Uhr - oder ein Objective auf deiner Seite;
TP zur Lane, wenn dort mehr auf dem Spiel steht, als das TP bis zum naechsten Objective wert ist. Danach das beste
Ziel der Karten-Rechnung (Buch 5), sonst die Seitenwelle oder dein Team. Jedes Ziel gegen die Gefahr dort zur
Ankunft (Qualitaetsrunde 1, E2), ein Ziel je Basis-Aufenthalt (C4). TOT: 8 s vor dem Respawn einmal Kauf und Ziel."""
from __future__ import annotations

from ... import ddragon, komponist
from ...entscheider import LAUF_ZUR_LANE, wellen_spawns
from .. import wert
from ..handlung import Handlung, Ziel
from . import KONTROLLAUGE, OBJ_NAME, _akk, lane_von, liste, objectives_meine_seite, puenktlich, uhr

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


def _brunnen_weg(m, ziel) -> float:
    """Dein Weg zu `ziel`: tot aus dem Brunnen, sonst von hier."""
    from ... import bewertung
    if ziel is None:
        return 25.0
    start = bewertung.BRUNNEN.get(m.p.mein_team if m.p is not None else "ORDER") if m.tot or m.pos is None else m.pos
    return bewertung.abstand(start, ziel) * bewertung.WEGFAKTOR / (m.mein_tempo or 345.0)


def _mit_gefahr(h: Handlung, m, ziel, weg: float, am_turm: bool = False) -> Handlung:
    """E2: die Gefahr wird am Ziel zur Ankunft gerechnet - tot nach dem Respawn aus dem Brunnen (wert.bewerte)."""
    h.daten["gefahr_am"] = (ziel, (m.respawn if m.tot else 0.0) + weg, am_turm)
    return h


def _lane_turm(m, lane: str):
    """Dein vorderster stehender Turm dieser Lane (Spiel-Einheiten)."""
    from ... import bewertung
    if m.p is None:
        return None
    mein = m.p.mein_team
    stehen = bewertung.stehende_tuerme(m.p)
    for stufe in ("aussen", "innen", "Inhib"):
        if (mein, lane, stufe) in stehen:
            return bewertung.TUERME[(mein, lane, stufe)]
    return None


def _lane_option(m, cfg: dict, modus: str, lane: str, druck: str = "") -> Handlung:
    """Zurueck auf deine Lane (Buch 3, 4.1) - mit der Folge statt der Wellen-Uhr zum Rechnen (E8)."""
    b = m.b
    ziel = _lane_turm(m, lane)
    weg = _weg_zur_lane(m, lane) if not m.tot else _brunnen_weg(m, ziel)
    if druck:
        grund = druck
        satz = f"Zurück nach {lane}: {grund}."
    else:
        lauf = LAUF_ZUR_LANE.get(b.ich.rolle, 27.0)
        start = m.zeit + (m.respawn if m.tot else 0.0)
        ankunft = min((t + lauf for t, _ in wellen_spawns(m.zeit + 120) if t + lauf > start + weg - 5), default=None)
        puffer = ankunft - (start + weg) if ankunft is not None else None
        if puffer is None:
            grund, satz = "deine Welle wartet", f"Zurück nach {lane}: deine Welle wartet."
        elif puffer >= 5:
            grund, satz = "du bist pünktlich zur Welle da", f"Zurück nach {lane}: du bist pünktlich zur Welle da."
        else:
            grund, satz = "lauf direkt, sonst verpasst du die Welle", f"Lauf direkt nach {lane}, sonst verpasst du die Welle."
    h = Handlung("WOHIN", Ziel("lane", lane, ziel, weg), modus, 20.0, grund=grund, satz=satz)
    h.daten["kurz"] = lane
    return _mit_gefahr(h, m, ziel, weg, am_turm=True)


def _objective_option(m, cfg: dict, modus: str, o) -> Handlung | None:
    """Ein Objective als Ziel - lebt es, nur wenn ihr es nehmen koennt: genug von euch rechtzeitig dort
    ([objective_wert] mindestens, Pruefung C2: "Baron lebt" ist kein Grund)."""
    weg = _brunnen_weg(m, o.pos) if m.tot or o.weg is None else o.weg
    ankunft = (m.respawn if m.tot else 0.0) + weg
    wir = 1 + (o.team_erreicht or 0)
    noetig = cfg["objective_wert"].get("mindestens", {}).get(o.schl, 2)
    if o.lebt:
        if wir < noetig:
            return None
        grund = "ihr seid dort " + {2: "zu zweit", 3: "zu dritt", 4: "zu viert"}.get(wir, "zu fünft")
    else:
        if o.spawn_in > 100 or ankunft > o.spawn_in + 10:
            return None
        grund = f"Spawn um {uhr(m.zeit + o.spawn_in)}, {puenktlich(o.spawn_in - ankunft)}"
    h = Handlung("WOHIN", Ziel("objective", OBJ_NAME[o.schl], o.pos, weg), modus, weg, grund=grund,
                 satz=f"{ZUM[o.schl][0].upper()}{ZUM[o.schl][1:]}: {grund}.")
    h.daten["kurz"] = ZUM[o.schl]
    return _mit_gefahr(h, m, o.pos, weg)


def _optionen(m, cfg: dict, modus: str) -> list[Handlung]:
    """Die Ziele in der Reihenfolge, in der sie gelten; `wohin` nimmt das erste, das nicht in den Tod fuehrt."""
    b, c = m.b, cfg["recall"]
    lane = lane_von(m)
    aus: list[Handlung] = []
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
            aus.append(h)
        for o in objectives_meine_seite(m):
            if (h := _objective_option(m, cfg, modus, o)) is not None:
                aus.append(h)
        aus.append(_lane_option(m, cfg, modus, lane, druck))
        return aus
    # nach der Lane-Phase nur die Karten-Rechnung (Buch 5, Kapitel 2; Pruefung C1) - kein altes Ziel, kein nacktes
    # Objective; findet sie nichts Positives: die Seitenwelle auf deiner Seite oder dein Team (Buch 5, GRUPPE)
    aus += _karten_ziele(m, cfg, modus)
    for o in sorted(m.objectives, key=lambda o: o.spawn_in):
        if (h := _objective_option(m, cfg, modus, o)) is not None:
            aus.append(h)
    gruppe = _team(m, modus)
    if gruppe is not None and len(gruppe[0]) >= 3:
        aus.append(gruppe[1])
    aus.append(_seitenwelle_option(m, cfg, modus, lane))
    if gruppe is not None and len(gruppe[0]) < 3:
        aus.append(gruppe[1])
    return aus


def _team(m, modus: str):
    """(Namen, WOHIN "zu deinem Team") der groessten Gruppe (>= 2 Mitspieler in 2000), sonst None."""
    from ... import bewertung, minimap
    freunde = [(s, wo) for s, wo in (m.mitspieler or []) if wo is not None]
    beste = None
    for _, wo in freunde:
        gruppe = [(s, w2) for s, w2 in freunde if bewertung.abstand(w2, wo) <= 2000]
        if len(gruppe) >= 2 and (beste is None or len(gruppe) > len(beste)):
            beste = gruppe
    if beste is None:
        return None
    x = sum(w[0] for _, w in beste) / len(beste)
    y = sum(w[1] for _, w in beste) / len(beste)
    namen = [s.champion for s, _ in beste]
    try:
        ort = minimap.ort(x / bewertung.BREITE, 1.0 - y / bewertung.HOEHE, m.p.mein_team)
    except Exception:
        ort = ""
    weg = _brunnen_weg(m, (x, y))
    grund = f"{liste(namen)} stehen {ort}".strip() if ort else f"{liste(namen)} sind zusammen"
    h = Handlung("WOHIN", Ziel("gruppe", "deinem Team", (x, y), weg), modus, weg, grund=grund,
                 satz=f"Geh zu deinem Team: {grund}.")
    h.daten["kurz"] = "zu deinem Team"
    return namen, _mit_gefahr(h, m, (x, y), weg)


def _seitenwelle_option(m, cfg: dict, modus: str, lane: str) -> Handlung:
    """Die Welle deiner Seite: Buch 5, 3 - der Toplaner haelt die Seite, wenn sonst nichts ansteht."""
    ziel = _lane_turm(m, lane)
    weg = _brunnen_weg(m, ziel)
    w = (m.wellen or {}).get(lane)
    grund = (f"{w.ihre} Vasallen laufen auf deinen Turm" if w is not None and w.zustand in DRUECKT and w.ihre
             else "dort nimmt sie sonst niemand")
    h = Handlung("WOHIN", Ziel("lane", f"die {lane}-Welle", ziel, weg), modus, weg, grund=grund,
                 satz=f"Geh zur {lane}-Welle: {grund}.")
    h.daten["kurz"] = f"zur {lane}-Welle"
    return _mit_gefahr(h, m, ziel, weg, am_turm=True)


def wohin(m, cfg: dict, modus: str, merker: dict | None = None, lage=None) -> Handlung:
    """WOHIN / WOHIN_TP_LANE mit `daten['kurz']` (fuer den Kauf-Satz: "Top", "zu den Larven") und `grund`.
    E2: das erste Ziel, das nicht in den Tod fuehrt (Gefahr am Ziel zur Ankunft, tot aus dem Brunnen). C4: `merker`
    haelt ein Ziel je Basis-Aufenthalt, solange `lage` (Tote, Strukturen, lebende Objectives) gleich bleibt."""
    from .. import gefahr
    optionen = _optionen(m, cfg, modus)
    c = cfg["gefahr"]

    def p_am(h):
        am = h.daten.get("gefahr_am")
        return gefahr.p_tod_am(m, am[0], am[1], c, am_turm=bool(am[2]))[0] if am and am[0] is not None else 0.0
    risiko = [(p_am(h), h) for h in optionen]
    sicher = [h for p, h in risiko if p < c["p_min"]]
    wahl = sicher[0] if sicher else min(risiko, key=lambda x: x[0])[1]
    if merker is not None:
        schl = merker.get("ziel_schl")
        if schl is not None and merker.get("lage") == lage:
            gleich = [h for h in optionen if (h.art, h.ziel.name if h.ziel else "") == schl]
            if gleich:
                return gleich[0]
        merker["ziel_schl"] = (wahl.art, wahl.ziel.name if wahl.ziel else "")
        merker["lage"] = lage
    return wahl


def _karten_ziele(m, cfg: dict, modus: str) -> list[Handlung]:
    """Buch 5, Kapitel 2 aus der Basis: die Tuerme (DRUECKEN, ohne Split-Regel - du bist nicht auf einer Seite) und
    Seitenwellen mit positivem EV, das beste zuerst."""
    from . import karte
    ziele = karte.turm_handlungen(m, cfg, modus, "DRUECKEN", split=False)
    for lane, w in (m.seitenwellen or {}).items():
        if (h := karte.seitenwelle(m, cfg, modus, lane, w)) is not None:
            ziele.append(h)
    for h in ziele:
        wert.bewerte(h, m, cfg)
    aus = []
    for beste in sorted((h for h in ziele if h.ev > 0), key=lambda h: -h.ev):
        if beste.art == "SEITENWELLE":
            lane = beste.daten["lane"]
            kurz, satz = f"zur {lane}-Welle", beste.satz
        else:
            kurz = f"auf {beste.ziel.name}"
            satz = f"Geh {kurz}: {beste.grund}."
        h = Handlung("WOHIN", beste.ziel, modus, beste.dauer, grund=beste.grund, satz=satz)
        h.daten["kurz"] = kurz
        aus.append(_mit_gefahr(h, m, beste.ziel.pos if beste.ziel else None, beste.dauer))
    return aus


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
    if ziel.daten.get("gefahr_am") is not None:
        h.daten["gefahr_am"] = ziel.daten["gefahr_am"]
    h.daten.update(wohin=ziel, items=list(k.kaufen), kontrollauge="ein Kontroll-Auge" in teile,
                   gold_start=m.b.gold, kauf_sprung=cfg["recall"]["kauf_sprung"], folge_art={1: ziel.art})
    h.erfuellt = _gekauft
    return h


def _gekauft(m, plan) -> bool:
    """KAUFEN, Schritt "kaufen": das Gold ist um einen Kauf gefallen - danach gilt der Plan als sein Ziel weiter."""
    d = plan.handlung.daten
    return plan.schritt == 0 and m.b is not None and m.b.gold <= d["gold_start"] - d["kauf_sprung"]


def kandidaten(m, cfg: dict, merker: dict | None = None, lage=None) -> list[Handlung]:
    z = wohin(m, cfg, "BASIS", merker, lage)
    aus = [z]
    if (k := kaufen(m, cfg, "BASIS", z)) is not None:
        aus.append(k)
    elif kontrollauge_dazu(m) and m.b.gold >= 75:
        mit = z.satz.rstrip(".") + ", nimm ein Kontroll-Auge mit."
        if len(mit.split()) <= cfg["sprechen"]["max_woerter"]:
            z.satz = mit
    return aus
