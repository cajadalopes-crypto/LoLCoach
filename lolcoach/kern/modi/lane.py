"""Modus LANE (Buch 0, 6.3; Buch 1 Welle, Buch 3 Recall): Kandidaten fuer die naechsten 30 s auf deiner Lane.

Die Welle entscheidet den Zeitpunkt (Buch 3, Kapitel 2): gecrasht oder leer -> BACK_JETZT; zu ihm / Mitte ->
WELLE_REIN_UND_BACK; zu dir -> UNTER_TURM_FARMEN; unbekannt -> nur bei Leben oder Gefahr. Die Gefahr schlaegt das
Timing - das erledigt der Kern mit dem Gefahr-Gate (Kandidaten mit `nur_bei_gefahr` bzw. `schutz`)."""
from __future__ import annotations

from ... import denker
from ...kaufplan import _dat
from .. import gefahr, wert
from ..handlung import Handlung, Ziel
from . import (OBJ_NAME, abwesenheit, back_gewinn, back_grund_text, back_gruende, gegner_fenster, lane_verloren,
               lane_von, liste, nie_back, objective_wert, objectives_meine_seite, puenktlich, turm_ihr_name, uhr,
               welle_name)

ZUM = {"drache": "zum Drachen", "baron": "zum Baron", "herold": "zum Herold", "larven": "zu den Larven"}


def crash_dauer(m, cfg: dict, lane: str | None = None) -> float:
    """Buch 1, 3.2: grob, nur intern (nie gesagt): Weg der Front bis zu seinem Turm + 1 s je gegnerischem Vasall."""
    w, c = m.welle, cfg["welle"]
    laenge = c["lane_laenge_mid"] if (lane or lane_von(m)) == "Mid" else c["lane_laenge"]
    return max(0.0, w.turm_ihr - (w.front if w.front is not None else 0.5)) * laenge / c["vasallen_tempo"] \
        + (w.ihre or 0) * 1.0


def _kanone_vor(m, spawn_zeit: float) -> float | None:
    """Buch 1, 3.3: die Kanone, die 15-30 s vor dem Objective in der Lane ist (sonst die letzte davor)."""
    from ...entscheider import LAUF_ZUR_LANE, wellen_spawns
    lauf = LAUF_ZUR_LANE.get(m.b.ich.rolle, 27.0)
    kanonen = [t + lauf for t, k in wellen_spawns(spawn_zeit, m.p.modus if m.p is not None else "CLASSIC")
               if k and m.zeit < t + lauf < spawn_zeit]
    passend = [t for t in kanonen if 15 <= spawn_zeit - t <= 30]
    return (passend or kanonen or [None])[-1]


SCHUTZ_KURZ = "Weiter: am Turm farmen, kein Trade."     # G1: nach Tod oder Basis (<= 8 Woerter)


def kandidaten(m, cfg: dict, lane: str | None = None, modus: str = "LANE", arten=None,
               schutz=None) -> list[Handlung]:
    """`lane`/`modus`: auch fuer eine Seitenlane nach der Lane-Phase (Buch 5, 3.2) - dann ist `m.welle` die Welle
    DIESER Lane (der Aufrufer reicht eine Sicht mit ihr), und `arten` begrenzt auf das, was dort gilt."""
    aus = _kandidaten(m, cfg, lane or lane_von(m), modus, schutz)
    return aus if arten is None else [h for h in aus if h.art in arten]


def _bauteil(m) -> str | None:
    """Was die Lane wieder oeffnet: das naechste Bauteil aus dem Kaufplan (Pruefung A: "kein Trade bis zum
    Brutalisierer")."""
    from ... import kaufplan
    b = m.b
    try:
        k = kaufplan.plan(b.ich.champion_id, tuple(b.ich.items), float(b.gold or 0))
    except Exception:
        return None
    if k is None:
        return None
    if k.kaufen and k.kaufen[0] != "Stiefel":
        return k.kaufen[0]
    return k.naechstes[0] if k.naechstes else k.item


def bauteil_gekauft(m, teil: str | None) -> bool:
    """Liegt `teil` (Name) im Inventar?"""
    if not teil or m.b is None or m.b.ich is None:
        return False
    from ... import ddragon
    return teil in {ddragon.items().get(i, {}).get("name") for i in m.b.ich.items}


def _lane_wieder_offen(m, plan) -> str | None:
    """Der Plan fuer die verlorene Lane gilt, bis die Kraft wieder >= 0 ist oder das Bauteil gekauft ist."""
    b = m.b
    if b is None or b.lane is None:
        return "kein Lane-Gegner"
    from . import lane_kraft
    if lane_kraft(b) >= 0.0:
        return "Kraft ausgeglichen"
    teil = plan.handlung.daten.get("bauteil")
    if teil:
        from ... import ddragon
        namen = {ddragon.items().get(i, {}).get("name") for i in b.ich.items}
        if teil in namen:
            return f"{teil} gekauft"
    return None


def _kandidaten(m, cfg: dict, lane: str, modus: str, schutz=None) -> list[Handlung]:
    b = m.b
    if m.bereich == "basis_eigen":
        return []          # der Modus hinkt 1,5 s: in der Basis kein Wellenbefehl (Pruefung E3, 102112 5:54)
    cw, cr, cg = cfg["welle"], cfg["recall"], cfg["gefahr"]
    w = m.welle
    z = w.zustand if w is not None else "UNBEKANNT"
    fr = wert.farm_rate(m.zeit, cfg)
    ww = wert.wellenwert(m.zeit, cfg)
    welle = welle_name(m, lane)
    aus = [Handlung("FARMEN", Ziel("lane", welle), modus, 10.0, gewinn=fr * 10.0)]
    gruende = back_gruende(m, cfg)
    nie = nie_back(m, cfg)
    back_g = back_gewinn(m, cfg, gruende) if gruende else 0.0
    grund_text = back_grund_text(gruende)
    kanal, einkauf = cr["kanal_s"], cr["einkauf_s"]
    obj_bald = [o for o in objectives_meine_seite(m, lane) if not o.lebt and o.spawn_in <= 60]

    # BACK_JETZT: gecrasht / leer; ohne Welle nur bei Leben; sonst nur, wenn die Gefahr anschlaegt (Buch 3, 2 / 2.1)
    if gruende and nie is None:
        leben = any(x.art == "LEBEN" for x in gruende)
        kritisch = b.leben is not None and b.leben < cr["leben_kritisch"]
        timing = z in ("GECRASHT_BEI_IHM", "LEER") or (z == "UNBEKANNT" and leben) or kritisch
        h = Handlung("BACK_JETZT", Ziel("basis", "Basis"), modus, kanal + einkauf, gewinn=back_g,
                     kosten=abwesenheit(m, cfg, z), gefahr_t=kanal, grund=grund_text,
                     satz=f"Back jetzt: {grund_text}.", schritte=["back", "kaufen", "zurück"])
        h.daten["nur_bei_gefahr"] = not timing
        aus.append(h)

    # WELLE_REIN_UND_BACK (Buch 1, 3.2): erst crashen, sonst verlierst du die Welle
    kritisch = b.leben is not None and b.leben < cr["leben_kritisch"]      # dann zaehlt die Welle nicht mehr
    if gruende and not kritisch and z in ("ZU_IHM", "GROSS_ZU_IHM", "MITTE") and w.unsere is not None \
            and w.unsere >= (w.ihre or 0):
        crash = crash_dauer(m, cfg, lane)
        if crash <= cw["crash_max_s"]:
            vw = wert.vasall_wert(m.zeit, cfg)
            warten, extra, satz = 0.0, 0.0, f"{lane}-Welle rein, dann back: {grund_text}."
            if m.kanone_in is not None and m.kanone_in <= cw["kanone_warten_s"]:
                p, _ = gefahr.p_tod(m.kanone_in + crash, m, cg)
                if p < cg["p_min"]:        # die Kanone lebt am Turm lange - sie verlaengert dein Fenster
                    warten = m.kanone_in
                    extra = wert.wellenwert(m.zeit, cfg, kanone=True) - ww
                    satz = f"Kanone kommt {uhr(m.zeit + m.kanone_in)}: die noch rein, dann back. {grund_text}."
            h = Handlung("WELLE_REIN_UND_BACK", Ziel("lane", welle), modus, warten + crash + kanal + einkauf,
                         gewinn=back_g + (w.ihre or 0) * vw + extra, kosten=abwesenheit(m, cfg, "GECRASHT_BEI_IHM"),
                         gefahr_t=warten + crash + kanal, grund=grund_text, satz=satz,
                         schritte=["Welle rein", "back", "kaufen", "zurück"])
            h.schritt_saetze[1] = f"Welle ist drin - jetzt back: {gruende[0].text}."
            h.daten.update(folge_art={1: "BACK_JETZT"}, crash_bis=warten + max(crash, 15.0), kanone=warten > 0)
            h.erfuellt = _welle_drin
            aus.append(h)

    # PLATTEN (Buch 1, 3.6): deine Welle am Turm, dein Gegner tot / im Brunnen / weit, und die Platte ist sicher
    g = b.lane
    if z == "GECRASHT_BEI_IHM" and (w.unsere or 0) >= 3 and b.platten_gegner != 0 and g is not None:
        fenster = gegner_fenster(g, m)
        weg = g.s.tot or getattr(m, "lane_im_brunnen", False) or (
            g.abstand is not None and g.abstand > 3000 and (fenster or 0) > cw["platten_dauer"])
        if weg and fenster is not None:
            n = max(1, min(b.platten_gegner or 5, int(fenster // cw["platten_dauer"])))
            dauer = n * cw["platten_dauer"]
            p, _ = gefahr.p_tod(dauer, m, cg)
            if p < cg["p_min"]:
                if g.s.tot:
                    grund = f"{g.champion} ist noch {int(g.s.respawn)} Sekunden tot"
                elif getattr(m, "lane_im_brunnen", False):
                    grund = f"{g.champion} ist gebackt"
                else:
                    grund = f"{g.champion} braucht {int(fenster)} Sekunden zu dir"
                ziel = turm_ihr_name(m, lane)
                am = "am " + ziel.split(" ", 1)[1] if ziel.startswith("den ") else ziel
                h = Handlung("PLATTEN", Ziel("turm", ziel), modus, dauer,
                             gewinn=n * wert.platte_gold(m.zeit) + fr * dauer, grund=grund,
                             satz=f"Platte {am}: {grund}.")
                h.daten["platten"] = n
                aus.append(h)

    # WELLE_HALTEN (Buch 1, 3.4): Freeze vor deinem Turm - angreifend, wenn du staerker bist; schuetzend, wenn der
    # Jungler wahrscheinlich auf deiner Seite ist oder du schwaecher bist. Nicht vor einem Objective.
    if z in ("GEHALTEN_BEI_DIR", "ZU_DIR") and w.front is not None and w.front <= w.turm_dein + 0.15 and not obj_bald:
        kr = b.kraefte()[0] if g is not None else 0.0
        j = b.jungler
        p_j = gefahr.p_da(j, 30.0, m, cg) if j is not None else 0.0
        angreifend = kr >= 1.0
        schuetzend = p_j >= 0.5 or kr <= -1.0
        if angreifend or schuetzend:
            gewinn = fr * 15.0 + (0.5 * ww if angreifend and not schuetzend else 0.0)
            if angreifend and not schuetzend and g is not None:
                satz = f"Lass die {lane}-Welle vor deinem Turm stehen: {g.champion} muss zum Farmen nach vorn."
                grund = f"{g.champion} muss nach vorn"
            else:
                grund = (f"{j.champion} ist wahrscheinlich auf deiner Seite" if p_j >= 0.5 and j is not None
                         else f"{g.champion} ist stärker" if g is not None else "du bist schwächer")
                satz = f"Lass die {lane}-Welle zu dir kommen: {grund}."
            h = Handlung("WELLE_HALTEN", Ziel("lane", welle), modus, 15.0, gewinn=gewinn, gefahr_t=10.0,
                         grund=grund, satz=satz)
            h.daten.update(am_turm=True, schutz=schuetzend)
            aus.append(h)

    # Pruefung A (Qualitaetsrunde 1): die Lane ist verloren (Kraft <= -1 oder zwei Tode gegen ihn) - dann ist der
    # schuetzende Freeze der Plan (Buch 1, 3.4), einmal gesagt, mit Grund und Bauteil. Er ersetzt FARMEN; Trade,
    # All-in und Stapeln (ein langsamer Push) gibt es bis dahin nicht.
    # G1 (Qualitaetsrunde 2): der Kern fuehrt den Lane-Verlust als Episode (`schutz`: ihr Bauteil steht fest, bis es
    # gekauft ist); False = keine Episode. Ohne Angabe (Tests, konstruierte Lagen) wie vorher aus der Lage.
    verloren, tode = lane_verloren(m) if modus == "LANE" else (False, 0)
    if schutz is not None:
        verloren = verloren and bool(schutz)
    if b.leben is not None and b.leben < cr["leben_kritisch"]:
        verloren = False        # dann ist nur noch back die Frage (Buch 3, 2) - der Plan fuer die Lane kommt danach
    if verloren and g is not None and not g.s.tot:
        teil = schutz["teil"] if schutz else _bauteil(m)
        grund = f"{g.champion} ist vorn"
        # <= 18 Woerter (G1); die kurze Fassung nach Tod oder Basis steht in daten["kurz_satz"]
        satz = (f"{g.champion} ist vorn: Welle zu deinem Turm ziehen, dort farmen, "
                + (f"kein Trade bis {_dat(teil)}." if teil else "kein Trade."))
        h = Handlung("WELLE_HALTEN", Ziel("lane", welle), modus, 10.0, gewinn=fr * 10.0 + 0.5 * ww, gefahr_t=10.0,
                     grund=grund, satz=satz)
        h.daten.update(am_turm=True, schutz=True, verloren=True, lane_gegner=g.champion, bauteil=teil, tode=tode,
                       kurz_satz=SCHUTZ_KURZ)
        h.abbruch.append(_lane_wieder_offen)
        aus = [x for x in aus if x.art not in ("FARMEN", "WELLE_HALTEN")] + [h]

    # STAPELN (Buch 1, 3.3): Objective auf deiner Seite in 45-100 s, Welle neutral, Jungler nicht wahrscheinlich hier
    j = b.jungler
    p_j30 = gefahr.p_da(j, 30.0, m, cg) if j is not None else 0.0
    if z in ("MITTE", "ZU_IHM", "LEER") and p_j30 < cw["stapeln_gefahr_max"] and not verloren:
        for o in objectives_meine_seite(m, lane):
            if o.lebt or not (45 <= o.spawn_in <= 100):
                continue
            t_k = _kanone_vor(m, m.zeit + o.spawn_in)
            if t_k is None:
                continue
            dauer = t_k - m.zeit
            h = Handlung("STAPELN", Ziel("lane", welle), modus, dauer,
                         gewinn=fr * dauer + 0.5 * ww + cr["vorlauf_bonus"] * objective_wert(o, cfg),
                         gefahr_t=min(dauer, 30.0), grund=f"{OBJ_NAME[o.schl]} um {uhr(m.zeit + o.spawn_in)}",
                         satz=f"Stapel die {lane}-Welle bis zur Kanone um {uhr(t_k)}: dann crashen und "
                              f"{ZUM[o.schl]}.",
                         schritte=[f"stapeln bis Kanone {uhr(t_k)}", "crashen", ZUM[o.schl]])
            h.daten["objective"] = o.schl
            aus.append(h)
            break

    # VORBEREITEN_OBJECTIVE (Buch 0, 6.3): Objective auf deiner Seite in <= 60 s - Welle, dann Grube
    for o in obj_bald:
        weg = o.weg if o.weg is not None else 20.0
        dauer = max(5.0, o.spawn_in - weg)
        h = Handlung("VORBEREITEN_OBJECTIVE", Ziel("objective", OBJ_NAME[o.schl], o.pos, weg), modus, dauer,
                     gewinn=fr * dauer + cr["vorlauf_bonus"] * objective_wert(o, cfg), gefahr_t=min(dauer, 30.0),
                     grund=f"Spawn um {uhr(m.zeit + o.spawn_in)}",
                     satz=f"{lane}-Welle rein, dann {ZUM[o.schl]}: Spawn um {uhr(m.zeit + o.spawn_in)}, "
                          f"{puenktlich(o.spawn_in - weg)}.",
                     schritte=["Welle rein", ZUM[o.schl]])
        h.daten["objective"] = o.schl
        aus.append(h)
        break

    # UNTER_TURM_FARMEN (Buch 1, 3.5): seine grosse Welle kommt zu dir - ein Back jetzt verschenkt sie
    if gruende and z in ("GECRASHT_BEI_DIR", "GROSS_ZU_DIR") and b.zum_turm is not None and b.zum_turm <= 20:
        verlust = abwesenheit(m, cfg, z)
        if verlust >= cw["stapel_verlust_min"]:
            ihre = w.ihre or 6
            dauer = max(10.0, ihre * 2.5)
            h = Handlung("UNTER_TURM_FARMEN", Ziel("turm", "deinem Turm"), modus, dauer,
                         gewinn=ww * ihre / 6.0, gefahr_t=min(dauer, 20.0), grund=f"{ihre} Vasallen",
                         satz=f"Farm unter deinem Turm, back erst, wenn die Welle weg ist: sonst verlierst du "
                              f"{ihre} Vasallen.", schritte=["unter dem Turm farmen", "back"])
            h.daten["am_turm"] = True
            aus.append(h)

    # TRADE / ALL_IN (Buch 0, 6.2/6.3): Lane-Gegner sichtbar <= 1000, das Urteil sagt Trade oder Kill
    if g is not None and g.sichtbar and not g.s.tot and g.abstand is not None and g.abstand <= 1000 and not verloren:
        try:
            u = denker.urteil(b)
        except Exception:
            u = None
        if u is not None and u.art in ("trade", "kill", "kill_schnell"):
            kg = denker.kill_gold(b)
            gute = [f for f in sorted(u.faktoren, key=lambda f: -f.wert) if f.wert > 0]
            grund = gute[0].satz if gute else "du bist stärker"
            h = Handlung("TRADE", Ziel("gegner", g.champion, g.pos, 0.0), modus, 5.0, gewinn=0.3 * kg + fr * 5.0,
                         grund=grund, satz=f"Trade {g.champion}: {grund}.")
            h.daten["kampf_mit"] = g.s.name
            aus.append(h)
            if u.art in ("kill", "kill_schnell") and u.beleg is not None:
                ev = denker.erwartung(b, u.wert)
                p_sieg = None
                if ev is not None:
                    import math
                    p_sieg = 1 / (1 + math.exp(-1.1 * (u.wert - 2.0)))
                h = Handlung("ALL_IN", Ziel("gegner", g.champion, g.pos, 0.0), modus, 8.0,
                             gewinn=kg + 0.5 * ww, p_erfolg=p_sieg, grund=u.beleg.satz,
                             satz=f"Geh rein auf {g.champion}: {u.beleg.satz}.")
                h.daten["kampf_mit"] = g.s.name
                h.daten["klein"] = True
                aus.append(h)
    return aus


def _welle_drin(m, plan) -> bool:
    """WELLE_REIN_UND_BACK, Schritt "Welle rein": gecrasht - oder die Zeit ist um (Buch 1, 3.2)."""
    if plan.schritt != 0:
        return False
    w = m.welle
    return (w is not None and w.zustand == "GECRASHT_BEI_IHM") or \
        m.zeit - plan.seit >= plan.handlung.daten.get("crash_bis", 15.0)


def liste_namen(namen: list[str]) -> str:
    return liste(namen)
