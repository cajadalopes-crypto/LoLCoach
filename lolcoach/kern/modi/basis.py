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

ZUM = {"drache": "zum Drachen", "baron": "zum Baron", "herold": "zum Herold", "larven": "zu den Larven",
       "aeltester": "zum Ältesten"}
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
            vasallen_satz(ihre)
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
        ankunft = min((t + lauf for t, _ in wellen_spawns(m.zeit + 120, m.p.modus if m.p is not None else "CLASSIC")
                       if t + lauf > start + weg - 5), default=None)
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


def vasallen_satz(n: int) -> str:
    """"ein Vasall laeuft" / "9 Vasallen laufen" (140253 6:47: "1 Vasallen laufen auf deinen Turm")."""
    return "ein Vasall läuft auf deinen Turm" if n == 1 else f"{n} Vasallen laufen auf deinen Turm"


def _objective_option(m, cfg: dict, modus: str, o) -> Handlung | None:
    """Ein Objective als Ziel - nur, wenn es dich zieht (Buch 6, 4.1: objective_zieht statt [objective_wert]
    mindestens, das wegfaellt; Pruefung C2: "Baron lebt" ist kein Grund)."""
    from .. import objective as obj
    weg = _brunnen_weg(m, o.pos) if m.tot or o.weg is None else o.weg
    ankunft = (m.respawn if m.tot else 0.0) + weg
    u = obj.urteil_von(m, o, cfg)
    if not u.zieht:
        return None
    if o.lebt:
        grund = obj.grund(m, o, u, "NEHMEN")
    else:
        if o.spawn_in > 100 or ankunft > o.spawn_in:
            return None          # Pruefung c, R6: nie, wenn du zu spaet kommst (164326 7:48 "du kommst zu spaet")
        grund = f"Spawn um {uhr(m.zeit + o.spawn_in)}, {puenktlich(o.spawn_in - ankunft)}"
    h = Handlung("WOHIN", Ziel("objective", OBJ_NAME[o.schl], o.pos, weg), modus, weg, grund=grund,
                 satz=f"{ZUM[o.schl][0].upper()}{ZUM[o.schl][1:]}: {grund}.")
    h.daten["kurz"] = ZUM[o.schl]
    h.daten["objective"] = o.schl
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
    if (sw := _seitenwelle_option(m, cfg, modus, lane)) is not None:
        aus.append(sw)
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


def _seitenwelle_option(m, cfg: dict, modus: str, lane: str) -> Handlung | None:
    """Die Welle deiner Seite: Buch 5, 3 - der Toplaner haelt die Seite, wenn sonst nichts ansteht. Auftrag 012, 1
    (192113 20:38, 23:26: "Dann zur Top-Welle, sie laeuft sonst in deinen Turm" - sie stand leer an ihrem Nexus):
    braucht dich deine Welle nicht, die einer anderen Lane, die auf euren Turm laeuft, sonst deine Seite ohne Welle
    ("Geh nach Top: dort kommt ihre naechste Welle") - ein festes Ziel je Basis-Aufenthalt (C4, 102112 30:02)."""
    from .karte import welle_ohne_dich
    if welle_ohne_dich(m, lane, cfg) is not None:
        andere = [(l, w) for l, w in (m.seitenwellen or {}).items() if l != lane]
        if not andere:
            ziel = _lane_turm(m, lane)
            weg = _brunnen_weg(m, ziel)
            grund = "dort kommt ihre nächste Welle"
            h = Handlung("WOHIN", Ziel("lane", lane, ziel, weg), modus, weg, grund=grund, satz=f"Geh nach {lane}: {grund}.")
            h.daten["kurz"] = f"nach {lane}"
            h.daten["grund_kurz"] = grund
            return _mit_gefahr(h, m, ziel, weg, am_turm=True)
        lane = min(andere, key=lambda lw: _brunnen_weg(m, _lane_turm(m, lw[0])) or 0.0)[0]
    ziel = _lane_turm(m, lane)
    weg = _brunnen_weg(m, ziel)
    w = (m.wellen or {}).get(lane)
    # Buch 4, 4 (Auftrag 008): "dort nimmt sie sonst niemand" nur mit dem, wo dein Team ist
    from ..sprache import team_grund
    team = team_grund(m, lane)
    # Auftrag 012, 1 (192113 19:24 "sie laeuft sonst in deinen Turm" - sie lief zu ihnen): nur, wenn sie zu dir laeuft
    zu_dir = w is None or w.zustand in DRUECKT or w.zustand in ("MITTE", "UNBEKANNT", "GEHALTEN_BEI_DIR")
    grund = (vasallen_satz(w.ihre) if w is not None and w.zustand in DRUECKT and w.ihre
             else f"dort nimmt sie sonst niemand, {team}" if team
             else "sie läuft sonst in deinen Turm" if zu_dir else "dort kommt ihre nächste Welle")
    h = Handlung("WOHIN", Ziel("lane", f"die {lane}-Welle", ziel, weg), modus, weg, grund=grund,
                 satz=f"Geh zur {lane}-Welle: {grund}.")
    h.daten["kurz"] = f"zur {lane}-Welle"
    h.daten["grund_kurz"] = team or grund
    return _mit_gefahr(h, m, ziel, weg, am_turm=True)


EILIG = ("lauf direkt", "sonst verpasst", "sonst kommst du zu spät")
ZAHL = {1: "einer", 2: "zwei", 3: "drei", 4: "vier", 5: "alle fünf"}


def _seite(pos) -> str:
    """oben / unten / in der Mitte - die Kartenhaelfte einer Position (Spiel-Einheiten, blaue Basis unten links)."""
    d = pos[1] - pos[0]
    return "oben" if d > 2000 else "unten" if d < -2000 else "in der Mitte"


def _zuletzt(m, name: str | None) -> str:
    """ "Kha'Zix war zuletzt oben" - der Gegner, der am meisten zur Gefahr beitraegt."""
    g = next((g for g in m.b.gegner if g.champion == name), None) if name else None
    if g is None or g.pos is None:
        return f"{name} ist nicht zu sehen" if name else "sie sind nicht zu sehen"
    return f"{name} war zuletzt {_seite(g.pos)}"


def _turm_option(m, modus: str, lane: str, stufe: str, satz: str, grund: str, kurz: str) -> Handlung | None:
    from ... import bewertung
    if m.p is None:
        return None
    k = (m.p.mein_team, lane, stufe)
    if k not in bewertung.stehende_tuerme(m.p):
        return None
    ziel = bewertung.TUERME[k]
    weg = _brunnen_weg(m, ziel)
    h = Handlung("WOHIN", Ziel("turm", f"{kurz}", ziel, weg), modus, weg, grund=grund, satz=satz)
    h.daten["kurz"] = kurz
    return _mit_gefahr(h, m, ziel, weg, am_turm=True)


def wohin(m, cfg: dict, modus: str, merker: dict | None = None, lage=None) -> Handlung:
    """WOHIN / WOHIN_TP_LANE mit `daten['kurz']` (fuer den Kauf-Satz: "Top", "zu den Larven") und `grund`.
    E2/G2: das erste Ziel mit p_tod bei Ankunft < wohin_p_tod_max (tot aus dem Brunnen, aus der Basis mit vollem
    Leben); eilig ("lauf direkt", "sonst verpasst du") nur unter wohin_direkt_max, sonst "bleib am Turm". Ist keins
    darunter: dein Team (>= 2), dann ein eigener Turm derselben Lane weiter hinten, sonst "Warte am Turm auf dein
    Team" auf der Seite mit den wenigsten Gegnern (Qualitaetsrunde 2: 144655 5:06, 140253 10:25, 133930 12:30 und 15:16
    schickten mit p_tod 0,67-0,79 zur Welle). C4: `merker` haelt ein Ziel je Basis-Aufenthalt, solange `lage` (Tote,
    Strukturen, lebende Objectives) gleich bleibt."""
    from .. import gefahr
    optionen = _optionen(m, cfg, modus)
    c = cfg["gefahr"]
    grenze, direkt = c["wohin_p_tod_max"], c["wohin_direkt_max"]

    def p_am(h):
        am = h.daten.get("gefahr_am")
        if not am or am[0] is None:
            return 0.0, []
        return gefahr.p_tod_am(m, am[0], am[1], c, am_turm=bool(am[2]))

    def text(h):
        return f"{h.satz} {h.grund}".lower()
    if merker is not None:
        schl = merker.get("ziel_schl")
        alt_obj = getattr(merker.get("wahl"), "daten", {}).get("objective") if merker.get("wahl") is not None else None
        if alt_obj is not None:
            # Buch 6, 4.1: ein Objective, das dich nicht mehr zieht, gilt, als gaebe es keins - auch als gemerktes Ziel
            from .. import objective as obj
            o = next((x for x in m.objectives if x.schl == alt_obj), None)
            if o is None or not obj.zieht(m, o, cfg):
                schl = None
        if schl is not None and merker.get("lage") == lage:
            alt = merker.get("wahl")
            gleich = [h for h in optionen if (h.art, h.ziel.name if h.ziel else "") == schl]
            if gleich and gleich[0].satz == getattr(alt, "satz", None):
                return gleich[0]
            if alt is not None:
                # dasselbe Ziel wie vorhin (C4) - als frische Kopie mit der Ankunft von jetzt (das Original wird von TOT
                # veraendert: "Noch 8 Sekunden: ..." kam sonst je Takt einmal mehr davor)
                from copy import copy
                neu = copy(alt)
                neu.daten = dict(alt.daten)
                am = neu.daten.get("gefahr_am")
                if am is not None and neu.ziel is not None and neu.ziel.weg is not None:
                    neu.daten["gefahr_am"] = (am[0], (m.respawn if m.tot else 0.0) + neu.ziel.weg, am[2])
                return neu
    wahl = None
    erstes = None
    for h in optionen:
        p, wer = p_am(h)
        erstes = erstes or (h, wer)
        if p >= grenze:
            continue
        if p >= direkt and any(w in text(h) for w in EILIG):
            if h.daten.get("kurz") in ("Top", "Mid", "Bot"):
                lane = h.daten["kurz"]
                zuletzt = _zuletzt(m, wer[0][0] if wer else None)
                h.satz, h.grund = (f"Zurück nach {lane}, bleib an deinem {lane}-Turm: {zuletzt}.",
                                   f"bleib an deinem {lane}-Turm, {zuletzt}")
            else:
                continue             # ein eiliges Objective, das nicht sicher ist: das naechste Ziel
        wahl = h
        break
    if wahl is None:
        wahl = _sicherer(m, cfg, modus, erstes, p_am, grenze)
    if merker is not None:
        merker["ziel_schl"] = (wahl.art, wahl.ziel.name if wahl.ziel else "")
        merker["lage"] = lage
        from copy import copy
        merker["wahl"] = copy(wahl)          # unveraendert ablegen - TOT schreibt "Noch 8 Sekunden: " in das Rueckgabeobjekt
        merker["wahl"].daten = dict(wahl.daten)
    return wahl


def _kein_ziel(modus: str) -> Handlung:
    """Pruefung c, R6: kein sicheres Ziel - ein WOHIN ohne Satz; der Kauf-Satz nennt dann kein Ziel."""
    h = Handlung("WOHIN", None, modus, 5.0, grund="", satz="")
    h.daten["kurz"] = None
    return h


def _sicherer(m, cfg: dict, modus: str, erstes, p_am, grenze: float) -> Handlung:
    """G2: kein Ziel unter der Grenze - dein Team (>= 2), dann dein Turm auf der Seite des Ziels weiter hinten (mit
    Schutz-Zusatz), sonst am inneren Turm der Seite mit den wenigsten Gegnern auf dein Team warten."""
    # Auftrag 007, A 3 (Entscheidung zu 005_frage 1): in der Lane-Phase ist das Respawn-Ziel der aeussere Turm - ausser
    # >= 2 Gegner standen in den letzten 10 s sichtbar <= 2000 davon; dann der innere, mit ehrlichem Grund (144655
    # 1:59, 164326 12:59: "bleib am Inhibitor-Turm: Gangplank war zuletzt oben" kostete die ganze Welle)
    if m.lane_phase and m.b is not None:
        from ...bewertung import abstand
        h00 = erstes[0] if erstes is not None else None
        k00 = h00.daten.get("kurz") if h00 is not None else None
        l00 = k00 if k00 in ("Top", "Mid", "Bot") else lane_von(m)
        aussen = _turm_option(m, modus, l00, "aussen", f"Zurück nach {l00}: an deinen äußeren {l00}-Turm, dort kommt "
                              f"deine Welle.", "dort kommt deine Welle", f"zu deinem äußeren {l00}-Turm")
        if aussen is not None:
            dort = [g.champion for g in m.b.gegner if not g.s.tot and g.pos is not None
                    and (g.sichtbar or (g.seit is not None and g.seit <= 10.0))
                    and abstand(g.pos, aussen.ziel.pos) <= 2000]
            if len(dort) < 2:
                return aussen
            wer = " und ".join(dort[:2])
            innen = _turm_option(m, modus, l00, "innen", f"Bleib an deinem inneren {l00}-Turm: {wer} stehen an deinem "
                                 f"äußeren.", f"{wer} stehen an deinem äußeren", f"zu deinem inneren {l00}-Turm")
            if innen is not None:
                return innen
    gruppe = _team(m, modus)
    if gruppe is not None and len(gruppe[0]) >= 2:
        # Pruefung c, R6: sind >= 2 Mitspieler zusammen, ist das Ziel dein Team - ist es dort zu gefaehrlich, gibt es
        # kein Ziel (dann bleibt es beim Kauf-Satz), und nicht "warte am Turm" (173159 36:06: "vier von ihnen sind
        # unten", dein Team vermutlich genau dort)
        return gruppe[1] if p_am(gruppe[1])[0] < grenze else _kein_ziel(modus)
    h0, wer = erstes if erstes is not None else (None, [])
    zuletzt = _zuletzt(m, wer[0][0] if wer else None)
    kurz = h0.daten.get("kurz") if h0 is not None else None
    lane = kurz if kurz in ("Top", "Mid", "Bot") else lane_von(m)
    ziel0 = h0.ziel.pos if h0 is not None and h0.ziel is not None else None
    for stufe, turm, kurz in (("aussen", f"äußeren {lane}-Turm", f"zu deinem äußeren {lane}-Turm"),
                              ("innen", f"inneren {lane}-Turm", f"zu deinem inneren {lane}-Turm"),
                              ("Inhib", f"{lane}-Inhibitor-Turm", f"zu deinem {lane}-Inhibitor-Turm")):
        h = _turm_option(m, modus, lane, stufe, f"Zurück nach {lane}, bleib an deinem {turm}: {zuletzt}.",
                         f"bleib an deinem {turm}, {zuletzt}", kurz)
        if h is None or (ziel0 is not None and h.ziel.pos == ziel0):
            continue
        if p_am(h)[0] < grenze:
            return h
    # die Seite mit den wenigsten Gegnern (zuletzt gesehen), dort der innere Turm
    je = {"Top": 0, "Mid": 0, "Bot": 0}
    wo = {"oben": "Top", "in der Mitte": "Mid", "unten": "Bot"}
    for g in m.b.gegner:
        if not g.s.tot and g.pos is not None:
            je[wo[_seite(g.pos)]] += 1
    seite = min(("Top", "Mid", "Bot"), key=lambda l: (je[l], l != lane_von(m)))
    meiste = max(je, key=je.get)
    n = je[meiste]
    wort = {"Top": "oben", "Mid": "in der Mitte", "Bot": "unten"}[meiste]
    grund = (f"{ZAHL.get(n, str(n))} von ihnen {'ist' if n == 1 else 'sind'} {wort}" if n
             else "keiner von ihnen ist zu sehen")                    # Pruefung c, R6: Einzahl und Mehrzahl
    for stufe in ("innen", "Inhib", "aussen"):
        # Pruefung c, R6: "Top-Inhibitor-Turm", nie "Inhibitor-Top-Turm"
        name = {"innen": f"inneren {seite}-Turm", "Inhib": f"{seite}-Inhibitor-Turm", "aussen": f"äußeren {seite}-Turm"}[stufe]
        dein = "deinem" if seite == lane_von(m) else "eurem"
        h = _turm_option(m, modus, seite, stufe, f"Warte an {dein} {name} auf dein Team: {grund}.",
                         f"warte dort auf dein Team, {grund}", f"zu {dein} {name}")
        if h is not None and p_am(h)[0] < grenze:
            return h
    return _kein_ziel(modus)      # Pruefung c, R6: ein Rueckfall-Ziel mit p_tod >= 0,3 wird nicht gesagt


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
    """Buch 3, 3.3: keins im Inventar, ein Platz frei NACH dem Kern-Kauf, danach >= 75 Gold uebrig. Auftrag 008, A3.3
    (101426 28:39 "Kauf Tiamat und ein Kontroll-Auge" bei fuenf Items: der eine freie Platz war fuer Tiamat - R3 pruefte
    jedes Item allein gegen das Inventar vor dem Kauf)."""
    from ... import kaufplan
    b, k = m.b, m.kauf
    if KONTROLLAUGE in b.ich.items or getattr(m, "auge_aus", False):     # Auftrag 016, 5: Carlos sagte Nein
        return False
    rest = b.gold - (k.kosten if k is not None and k.kaufen else 0)
    return kaufplan.plaetze_nach(b.ich.items, k.kaufen if k is not None and k.kaufen else []) >= 1 and rest >= 75


def _fokus_kontrollauge(m) -> bool:
    f = getattr(m, "fokus", None) or ""
    return "kontroll" in f.lower()


def kaufen(m, cfg: dict, modus: str, ziel: Handlung) -> Handlung | None:
    """KAUFEN mit Namen und dem Ziel in einem Satz (9.3 BASIS)."""
    k = m.kauf
    if k is None or not k.kaufen:
        return None
    from ...kaufplan import mit_ziel
    teile = [_akk(x) for x in k.kaufen[:2]]
    # Auftrag 009, 4: das (erste) Bauteil mit seinem Ziel - "Kauf Langschwert fuer die Gefraessige Hydra"
    ziel_item = getattr(k, "item", None)
    i = next((j for j, x in enumerate(k.kaufen[:2]) if mit_ziel(x, ziel_item) != x), None)
    if i is not None:
        teile[i] = mit_ziel(k.kaufen[i], ziel_item)
    if kontrollauge_dazu(m):
        if _fokus_kontrollauge(m):
            teile = ["ein Kontroll-Auge"] + teile
        else:
            teile.append("ein Kontroll-Auge")
    teile = teile[:3]
    was = liste(teile)
    verkauf = f"Verkauf {k.verkaufen}, dann k" if k.verkaufen else "K"
    # Pruefung c, R6: kein sicheres Ziel - Auftrag 016, 2 (die Kette immer): dann der sichere Platz, dein Turm
    satz = (f"{verkauf}auf {was}, dann {ziel.daten['kurz']}: {ziel.grund}." if ziel.daten.get("kurz")
            else f"{verkauf}auf {was}, dann warte an deinem Turm auf dein Team.")
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
    elif kontrollauge_dazu(m) and m.b.gold >= 75 and z.satz:
        mit = z.satz.rstrip(".") + ", nimm ein Kontroll-Auge mit."
        if len(mit.split()) <= cfg["sprechen"]["max_woerter"]:
            z.satz = mit
    return aus
