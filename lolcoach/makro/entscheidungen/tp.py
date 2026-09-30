"""B5. TP (T1-T9) - Rechner in lolcoach/makro/rechner.py (Entscheidung zu Phase 0, Punkt 2)."""
from __future__ import annotations

from ...bewertung import abstand
from .. import rechner, regeln
from ..kommando import Kommando, sek
from ..lage import MakroLage
from . import entscheidung
from ._hilfe import MONSTER_DAT, gegner_bei, monster_nah, name


def _tp_bereit(lage: MakroLage) -> bool:
    return lage.ich.tp_hat and lage.ich.tp_in == 0 and lage.ich.lebt


def _tp_nach(lage: MakroLage, ort) -> float:
    """Ankunft per TP an einem Ort: Ziel = naechster Mitspieler dort, sonst der Ort selbst (Turm/Vasall)."""
    nah = sorted((m for m in lage.mitspieler if m.lebt and m.pos), key=lambda m: abstand(m.pos, ort))
    ziel = nah[0].pos if nah and abstand(nah[0].pos, ort) < 3000 else ort
    return rechner.tp_ankunft(lage.ich.pos or lage.brunnen, ziel, ort, lage.zeit, lage.ich.tempo)


@entscheidung("T1", "TP zurueck in die Lane oder aufheben", "Re,D", ("eigene_zauber", "welle_eigen", "monster_timer"),
              ("Re:tp_abklingzeit", "Re:wellenkosten"))
def t1(lage: MakroLage):
    if not lage.ich.im_brunnen or not _tp_bereit(lage):
        return None
    w = lage.welle()
    if w.stand != "bei_uns" or w.groesse > -3 or monster_nah(lage, 180):
        return None
    gold, _ = rechner.wellenkosten(rechner.brunnen_lane(lage.lane or "top", lage.team), lage.zeit, "bei_uns")
    cd = rechner.tp_abklingzeit(lage.zeit, lage.ich.level)
    return Kommando("T1", "TP zurueck", f"mehrere Wellen laufen auf deinen Turm (etwa {gold:.0f} Gold) und kein Monster steht an",
                    f"TP ist in {sek(cd)} wieder da")


@entscheidung("T2", "TP zu Kampf oder Objective auf der anderen Seite", "Re,D",
              ("eigene_zauber", "kampf", "mitspieler_positionen", "welle_eigen"),
              ("Re:tp_ankunft", "Re:tp_urteil", "Re:ueberzahl", "D:wert"))
def t2(lage: MakroLage):
    k = lage.kampf
    if k is None or not _tp_bereit(lage) or k.in_s > 30 or lage.abstand_zu(k.pos) is None or lage.abstand_zu(k.pos) < 6000:
        return None
    ank = _tp_nach(lage, k.pos)
    lg = lage.lane_gegner
    u = rechner.tp_urteil(k.in_s, k.dauer_s, ank, lage.welle().stand, lg.tp_in == 0 if lg and lg.tp_in is not None else None,
                          lage.hirn.wert("TP"), None)
    if not u.tpen:
        return None
    zahl = f"{k.wir + 1} gegen {k.gegner}"
    vorher = f"Welle rein ({sek(rechner.crash_dauer())}), dann " if u.crash_zuerst else ""
    return Kommando("T2", f"{vorher}TP zum Kampf{' am ' + k.bei if k.bei else ''}", f"{zahl}, du bist in {sek(u.ankunft_s)} da, {u.grund}",
                    klasse="objective", wert=3.0)


@entscheidung("T3", "TP halten fuer das Objective", "Re,D", ("eigene_zauber", "monster_timer"), ("Re:tp_abklingzeit",))
def t3(lage: MakroLage):
    m = monster_nah(lage, 120)
    if m is None or m.spawn_in < 45 or not _tp_bereit(lage) or lage.plan.get("tp") != "lane":
        return None
    cd = rechner.tp_abklingzeit(lage.zeit, lage.ich.level)
    return Kommando("T3", "Nicht TP fuer die Lane", f"du brauchst ihn in {sek(m.spawn_in)} am {MONSTER_DAT[m.art]} (Abklingzeit {sek(cd)})",
                    klasse="objective", wert=2.0)


@entscheidung("T4", "TP-Flanke in der Spaetphase", "Re,R", ("eigene_zauber", "kampf", "eigene_wards"), ("R:T4", "Re:tp_ankunft"))
def t4(lage: MakroLage):
    k = lage.kampf
    if lage.zeit < 1500 or k is None or not _tp_bereit(lage) or k.in_s > regeln.regel("T4")["kampf_start_toleranz_s"]:
        return None
    flanke = next((w for w in lage.wards if "Flanke" in w.ort or "hinter" in w.ort), None)
    if flanke is None:
        return None
    return Kommando("T4", f"Wenn sie anfangen: TP auf den Ward {flanke.ort}", "von hinten trifft deine Ankunft ihre Hinterleute",
                    klasse="objective", wert=3.0)


@entscheidung("T5", "TP zur Verteidigung", "Re", ("eigene_zauber", "gegner_sichtungen", "platten"), ("Re:tp_ankunft", "Re:ankunft"))
def t5(lage: MakroLage):
    v = lage.plan.get("verteidigen")        # (Lane, s bis der Turm faellt)
    if not v or not _tp_bereit(lage):
        return None
    lane, faellt_in = v
    turm = lage.eigener_turm(lane) or lage.eigener_turm(lane, "innen")
    if turm is None or lage.ich.pos is None:
        return None
    zu_fuss = rechner.ankunft(lage.ich.pos, turm, lage.ich.tempo)
    per_tp = rechner.tp_ankunft(lage.ich.pos, turm, turm, lage.zeit)
    if zu_fuss <= faellt_in or per_tp > faellt_in:
        return None
    return Kommando("T5", f"TP auf den {lane.capitalize()}-Turm", f"sonst faellt er in {sek(faellt_in)}", klasse="gefahr", wert=2.5)


@entscheidung("T6", "Konter-TP", "M,Re", ("tp_sprung", "eigene_zauber", "kampf"), ("Re:tp_ankunft", "Re:ueberzahl"))
def t6(lage: MakroLage):
    e = lage.ereignis("tp", "gegner", 5)
    k = lage.kampf
    if e is None or k is None or not _tp_bereit(lage):
        return None
    lg = lage.lane_gegner
    return Kommando("T6", "Du auch: TP dorthin", f"{name(lg, 'ihr Top')} TPt zum Kampf, sonst {k.wir} gegen {k.gegner + 1}",
                    klasse="objective", wert=3.0)


@entscheidung("T7", "TP-Ziel waehlen", "Re,M", ("gegner_sichtungen", "mitspieler_positionen"), ("Re:tp_ankunft",))
def t7(lage: MakroLage):
    ziele = lage.plan.get("tp_ziele")         # [(Name, Pos)]
    if not lage.plan.get("tp") or not ziele or len(ziele) < 2:
        return None
    sicher = [(n, p) for n, p in ziele if not gegner_bei(lage, p, 1500)]
    unsicher = [(n, p) for n, p in ziele if gegner_bei(lage, p, 1500)]
    if not sicher or not unsicher:
        return None
    g = gegner_bei(lage, unsicher[0][1], 1500)[0]
    return Kommando("T7", f"TP auf {sicher[0][0]}, nicht auf {unsicher[0][0]}", f"dort steht {name(g)}")


@entscheidung("T8", "Nicht TPen", "Re,D", ("eigene_zauber", "kampf"), ("Re:tp_urteil", "Re:tp_ankunft"))
def t8(lage: MakroLage):
    k = lage.kampf
    if k is None or not _tp_bereit(lage) or lage.abstand_zu(k.pos) is None or lage.abstand_zu(k.pos) < 6000:
        return None
    u = rechner.tp_urteil(k.in_s, k.dauer_s, _tp_nach(lage, k.pos), lage.welle().stand, None)
    if u.tpen and k.wir + 1 >= k.gegner:
        return None
    grund = u.grund if not u.tpen else f"auch mit dir {k.wir + 1} gegen {k.gegner}"
    return Kommando("T8", "Kein TP", grund, "TP fuer den naechsten Kampf halten")


@entscheidung("T9", "TP-Stand beider Tops", "M", ("eigene_zauber", "tp_stand_gegner"), ("Re:tp_abklingzeit",))
def t9(lage: MakroLage):
    lg = lage.lane_gegner
    if not _tp_bereit(lage) or lg is None or lg.tp_in is None or lg.tp_in < 60:
        return None
    return Kommando("T9", "Du hast TP, er nicht", f"noch {sek(lg.tp_in)}: jetzt ist dein Fenster fuer ein Play auf der anderen Seite")
