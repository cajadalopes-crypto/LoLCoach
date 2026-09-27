"""Der Entscheidungskern an konstruierten Lagen (Buch 1, 6.2; Buch 3, 7.2): tests/szenarien/konstruiert/*.toml.

Jede Lage: ein Takt des Kerns, Plan gegen soll / darf_nicht / satz_enthaelt - dazu die Satzform (Buch 0, 9.3):
PLAN hoechstens 18 Woerter, GEFAHR hoechstens 10.

    python tests/test_kern.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach.kern import konfig, testlage  # noqa: E402
from lolcoach.kern.handlung import SICHER  # noqa: E402


def konstruierte_lagen():
    c = konfig()["sprechen"]
    ergebnisse = [r for r in testlage.alle() if not r.get("uebersprungen")]   # Modi spaeterer Schritte: noch nicht
    rot = [r for r in ergebnisse if r["verstoesse"]]
    assert not rot, "\n".join(f"{r['datei']}: {r['id']} -> {r['plan']}: {r['verstoesse']}  Top: {r['top'][:4]}"
                              for r in rot)
    for r in ergebnisse:
        grenze = c["max_woerter_gefahr"] if r["gefahr"] and r["plan"] in SICHER else c["max_woerter"]
        assert len(r["satz"].split()) <= grenze, (r["id"], r["satz"])
    assert len(ergebnisse) >= 25, len(ergebnisse)


def neuer_plan_ist_der_beste():
    """Pruefung B: ein NEU gewaehlter Plan liegt nie mehr als hysterese_ge unter dem besten erlaubten Kandidaten -
    erlaubt ist unter Gefahr, was das Gate nicht ausloest (144655 6:44: STAPELN p_tod 0,51 hielt gegen FARMEN 0,02).
    Hält eine Regel einen schlechteren Plan, steht sie in `gehalten`."""
    import random
    from types import SimpleNamespace
    from lolcoach.kern.handlung import Handlung
    from lolcoach.kern.plan import PlanFuehrer, gefahr_schlaegt_an
    cfg = konfig()
    hg = cfg["plan"]["hysterese_ge"]
    zufall = random.Random(7)
    f = PlanFuehrer(cfg)
    arten = ["FARMEN", "STAPELN", "PLATTEN", "WELLE_REIN_UND_BACK", "BACK_JETZT", "ZURUECK"]
    for i in range(600):
        kand = []
        for art in arten:
            h = Handlung(art, None, "LANE", 10.0)
            h.ev = zufall.uniform(-600, 600)
            h.p_tod = zufall.choice([0.0, 0.02, 0.1, 0.5])
            h.verlust = 1500.0
            kand.append(h)
        m = SimpleNamespace(zeit=float(i), pos=None, b=None)
        ev = f.takt(m, kand, False)
        if ev is not None and ev.art in ("neu", "gefahr") and ev.plan is not None:
            erlaubt = kand
            if ev.art == "gefahr" or (ev.plan.handlung.art != max(kand, key=lambda h: h.ev).art
                                      and any(gefahr_schlaegt_an(h, cfg["gefahr"]) for h in kand)):
                erlaubt = [h for h in kand if h.art in SICHER or not gefahr_schlaegt_an(h, cfg["gefahr"])] or kand
            beste = max(h.ev for h in erlaubt)
            assert ev.plan.handlung.ev >= beste - hg, (i, ev.art, ev.plan.art, ev.plan.handlung.ev, beste)
        elif f.plan is not None and max(h.ev for h in kand) - f.plan.handlung.ev >= hg and f.gehalten is None:
            gefahr = gefahr_schlaegt_an(f.plan.handlung, cfg["gefahr"])
            assert gefahr or f.gehalten is not None, (i, f.plan.art)


def plan_haelt_bei_kurzer_luecke():
    """G3 (Qualitaetsrunde 2, 140253 3:56-4:05): faellt der Kandidat des Plans einen Takt heraus, bleibt der Plan; fehlt
    er laenger (luecke_s), kommt der beste andere - und kehrt der bessere zurueck, sperrt halten_s das nicht."""
    from types import SimpleNamespace
    from lolcoach.kern.handlung import Handlung
    from lolcoach.kern.plan import PlanFuehrer
    f = PlanFuehrer(konfig())

    def h(art, ev):
        x = Handlung(art, None, "LANE", 10.0)
        x.ev, x.p_tod, x.verlust = ev, 0.1, 1500.0
        return x

    def takt(t, *kand):
        return f.takt(SimpleNamespace(zeit=t, pos=None, b=None), list(kand), False)
    takt(100.0, h("WELLE_REIN_UND_BACK", 440), h("STAPELN", 200))
    assert f.plan.art == "WELLE_REIN_UND_BACK"
    takt(100.5, h("STAPELN", 200))                                   # ein Takt ohne ihn: der Plan haelt
    assert f.plan.art == "WELLE_REIN_UND_BACK", f.plan.art
    takt(101.0, h("WELLE_REIN_UND_BACK", 440), h("STAPELN", 200))
    takt(101.5, h("STAPELN", 200))
    takt(104.0, h("STAPELN", 200))                                   # laenger weg: STAPELN
    assert f.plan.art == "STAPELN", f.plan.art
    takt(104.5, h("WELLE_REIN_UND_BACK", 440), h("STAPELN", 200))    # zurueck, 240 besser
    takt(106.6, h("WELLE_REIN_UND_BACK", 440), h("STAPELN", 200))    # nach stabil_s, lange vor halten_s
    assert f.plan.art == "WELLE_REIN_UND_BACK", (f.plan.art, f.gehalten)


def fenster_gruende_sprechen_dafuer():
    """Pruefung C3: der Grund fuer ein Turm-Ziel spricht FUER die Handlung - jedes genannte Fenster (noch T Sekunden
    tot, fruehestens in T Sekunden) ist >= Weg + Dauer (`bis`). Vorher: "fruehestens in 0 Sekunden", "noch 3 Sekunden
    tot" (102112, 24:26 / 25:47 / 37:35)."""
    import random
    import re
    from types import SimpleNamespace
    from lolcoach.kern.modi.karte import TurmZiel, fenster_grund
    zufall = random.Random(3)
    for _ in range(500):
        ankunft = []
        for k in range(zufall.randint(0, 4)):
            tot = zufall.random() < 0.5
            s = SimpleNamespace(tot=tot, respawn=zufall.uniform(1, 50) if tot else 0.0)
            g = SimpleNamespace(s=s, champion=f"G{k}")
            ankunft.append((g, s.respawn + zufall.uniform(5, 30) if tot else zufall.uniform(0, 60)))
        ankunft.sort(key=lambda x: x[1])
        bis = zufall.uniform(5, 45)
        kommen = [g for g, t in ankunft if t <= bis][:1]
        z = TurmZiel("CHAOS", "Mid", "aussen", (0, 0), "den äußeren Mid-Turm", 10.0, ankunft, 0)
        m = SimpleNamespace(woanders=zufall.randint(0, 4))
        satz = fenster_grund(z, m, bis, kommen)
        for zahl in re.findall(r"(\d+) Sekunden", satz):
            assert int(zahl) >= int(bis), (satz, bis)
        if kommen:
            # Pruefung c, R2: kein "du schlaegst X" mehr - wer vorher kommt, wird nur benannt (der Satz ist stumm)
            assert "schlägst" not in satz and "vorher" in satz, satz


def gold_reicht_fuer_das_genannte_item():
    """Pruefung E5: "N Gold fuer X" - X kostet (abzueglich der Bauteile, die du hast) hoechstens N. Der Kern nennt,
    was der Kaufplan mit diesem Gold JETZT kauft (140253 3:49: "1050 Gold fuer Axiombogen" stimmte - der Brutalisierer
    lag schon im Inventar, Rest 713)."""
    import random
    from lolcoach import ddragon, kaufplan
    it = ddragon.items()
    zufall = random.Random(11)
    kern = list(kaufplan.kern("Riven")) + list(kaufplan.folge("Riven"))
    teile = sorted({int(f) for i in kern for f in (it.get(i, {}).get("from") or [])})
    for _ in range(300):
        inventar = tuple(zufall.sample(teile, zufall.randint(0, min(3, len(teile)))))
        gold = zufall.randint(300, 4000)
        k = kaufplan.plan("Riven", inventar, gold)
        if k is None:
            continue
        for name in k.kaufen:
            if name == "Stiefel":
                continue
            i = kaufplan._nach_name()[name]
            rest, _ = kaufplan._baum_kosten(i, list(inventar))
            assert rest <= gold, (name, rest, gold, inventar)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for test in (konstruierte_lagen, neuer_plan_ist_der_beste, plan_haelt_bei_kurzer_luecke, fenster_gruende_sprechen_dafuer,
                 gold_reicht_fuer_das_genannte_item):
        test()
        print(f"{test.__name__} OK")
