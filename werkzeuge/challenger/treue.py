"""Auftrag 035, Teil 2: Challenger-Treue - raet der Coach in einer echten High-Elo-Lage das, was der Spieler dort tat?

    python werkzeuge/challenger/treue.py [--n 30000] [--alt 3000] [--beispiele 10]
        -> buecher/challenger/treue.json und eine Tabelle im Terminal

Grundlage: die zurueckgelegten Pruefpartien aus 030 (aufteilung.json, Pruefung Spieler/Zeit), die kein Modell gesehen
hat - dieselbe Stichprobe wie analyse.Pruefdaten (lebende Momente, Aktion bekannt).

Je Moment:
  - die MakroLage AUS DEM RIOT-MOMENT (`lage_aus_moment`), nicht aus der Live-Wahrnehmung. Was die Riot-Daten nicht
    hergeben (Wellen, Wards, Trinket, HUD-Leben der Mitspieler, Zauber-Abklingzeiten, Kaufplan, Chat), bleibt leer -
    die Entscheidungen, die das brauchen, schweigen (`VORHANDEN`) und zaehlen NICHT als Fehler; sie werden getrennt
    ausgewiesen (`stumm_je_entscheidung`).
  - das Kommando des Coachs: der Entscheider aus lolcoach/makro/takt.py mit dem Gehirn (die vorberechneten Modellwerte
    des Moments - identisch mit gehirn.bewerte), ohne Planhalten (jeder Moment ist ein erster Takt), ohne die
    Sicherheits-Sperre (sie braucht die Live-Merkmale des alten Kerns);
  - die Aktion des Spielers (a0 = die Aktion der naechsten 60 s, phase1) und die Folge (Tod in 60 s, Siegchance 120 s).

Gemessen (je Politik: Coach mit Reihenfolge "wert" und "fest", "immer farmen", haeufigste Aktion je Rolle und Minute,
der alte Kern soweit anlegbar):
  - Treffer: Aktion des Kommandos == Aktion des Spielers (bei "geteilt" eine der zwei); streng (a0) und locker (die
    Aktion trifft irgendwann in den 60 s zu, flags). Ohne Aktion (Sicht, Warnung, Kauf, Ping) zaehlt als kein Treffer.
  - Treffer nur bei Siegern, nur bei Challenger-Spielern, beides.
  - Wert: was die empfohlenen Aktionen an Siegchance (120 s, Prozentpunkte) gegenueber dem Gespielten bringen -
    doppelt robust (AIPW, wie analyse.py: psi_a - Y, Standardfehler ueber Partien), dazu das reine Modell (Q).
  - Abdeckung: Anteil der Momente, in denen eine Entscheidung feuert (nicht nur die Grund-Anweisung G0), und mit Aktion.
  - Warnungs-Praezision: wenn der Coach warnt (Form Gefahr) - wie oft stirbt der Spieler in 60 s, gegen die Grundrate.
"""
from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

HIER = Path(__file__).resolve().parent
WURZEL = HIER.parents[1]
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(WURZEL))

AUS = WURZEL / "buecher" / "challenger" / "treue.json"
ROLLEN = ("TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY")
AKTIONEN = ["Tot", "Back", "Objective", "TP", "Rotation", "Split", "Gruppe", "Jungle", "Lane", "Warten", "Unterwegs"]
ZONEN = ["basis", "oben", "mid", "unten"]
MONSTER = ["–", "Drache", "Baron", "Herold", "Larven", "Elder"]
# Was die Riot-Daten je Moment hergeben (wahrnehmung.EINGABEN) - alles andere fehlt, seine Entscheidungen schweigen
VORHANDEN = frozenset(("uhr", "ereignisse", "scoreboard", "eigene_items", "gegner_items", "monster_timer",
                       "eigene_position", "mitspieler_positionen", "gegner_sichtungen", "kampf"))
# Plan-Art des alten Kerns -> Aktion (fuer den Vergleich mit dem alten Kern)
ALT_AKTION = {"BACK_JETZT": "Back", "WELLE_REIN_UND_BACK": "Back", "KAUFEN": None, "STAPELN": "Lane",
              "WELLE_HALTEN": "Lane", "UNTER_TURM_FARMEN": "Lane", "FARMEN": "Lane", "PLATTEN": "Lane",
              "WELLE_DRUECKEN": "Lane", "WELLE_KLAEREN": "Lane", "TRADE": "Lane", "ALL_IN": "Lane", "DRUECKEN": "Split",
              "SEITENWELLE": "Split", "ZUR_GRUPPE": "Gruppe", "MIT_GRUPPE": "Gruppe", "HILFE": "Unterwegs",
              "NEHMEN": "Objective", "BESTREITEN": "Objective", "ANLAUFEN": "Objective",
              "VORBEREITEN_OBJECTIVE": "Lane", "TAUSCHEN": "Split", "ABGEBEN_TAUSCHEN": "Split", "TP_SPIEL": "TP",
              "WOHIN_TP_LANE": "TP", "WOHIN": "Unterwegs", "ZURUECK": "Warten", "RAUS": "Warten",
              "HALTEN": "Warten", "HALTEN_UNTER_TURM": "Warten", "WELLE_UND_RAUS": "Lane", "REIN": "Lane",
              "ANNEHMEN": "Gruppe", "DREHEN": "Warten"}


# --- 1. Lage aus einem Riot-Moment -----------------------------------------------------------------------------------

def _wert(x, SP, name):
    i = SP.get(name)
    if i is None:
        return None
    v = float(x[i])
    return None if math.isnan(v) else v


def lage_aus_moment(x, meta, SP: dict, MI: dict):
    """MakroLage aus einer Zeile X (phase1.NAMEN) und meta (phase1.META). Nur Wissbares, wie im Training; fehlende
    Wahrnehmung leer (`lage.vorhanden = VORHANDEN`)."""
    from lolcoach.makro.lage import MakroLage, Monster, Spieler
    w = lambda n: _wert(x, SP, n)
    team = "ORDER" if int(meta[MI["team"]]) == 0 else "CHAOS"
    rolle = ROLLEN[int(meta[MI["rolle"]])]
    tot = bool(w("tot"))
    pos = (w("x"), w("y")) if w("x") is not None and w("y") is not None and not tot else None
    ich = Spieler(champion="Du", rolle=rolle, lebt=not tot, respawn=w("respawn_rest") or 0.0, pos=pos,
                  level=int(w("level") or 1), leben=w("leben_anteil") if w("leben_anteil") is not None else 1.0,
                  flash_in=None, ult_bereit=None, tp_hat=bool(w("hat_tp")), tp_in=None,
                  im_brunnen=bool(pos is not None and (w("abst_brunnen") or 1e9) <= 1200))
    lage = MakroLage(zeit=float(meta[MI["zeit"]]), team=team, ich=ich, gold=int(w("gold_tasche") or 0))
    lage.vorhanden = set(VORHANDEN)
    mit_rollen = [r for r in ROLLEN if r != rolle]
    for i, r in enumerate(mit_rollen, 1):
        mx, my = w(f"mit{i}_x"), w(f"mit{i}_y")
        lebt = mx is not None                                   # NaN = tot (phase1)
        lage.mitspieler.append(Spieler(champion=r.capitalize(), rolle=r, lebt=lebt, pos=(mx, my) if lebt else None,
                                       flash_in=None, ult_bereit=None, smite_bereit=None))
    for i, r in enumerate(ROLLEN):
        gtot = bool(w(f"geg{i}_tot"))
        alter = w(f"geg{i}_gesehen_alter")
        gx, gy = w(f"geg{i}_gesehen_x"), w(f"geg{i}_gesehen_y")
        g = Spieler(champion=f"Gegner-{r.capitalize()}", rolle=r, lebt=not gtot, respawn=w(f"geg{i}_respawn") or 0.0,
                    pos=(gx, gy) if gx is not None and gy is not None else None, gesehen_vor=alter,
                    flash_in=None, ult_bereit=None, tp_in=None, backt=False)
        if r == rolle and w("lg_nahe_sichtbar") == 1.0 and w("lg_x") is not None:
            g.pos, g.gesehen_vor = (w("lg_x"), w("lg_y")), 0.0          # nahe sichtbar: wie im Spiel auf dem Schirm
        if gtot:
            g.gesehen_vor = 0.0
        lage.gegner.append(g)
    for art in ("drache", "larven", "herold", "baron"):
        bis, da = w(f"{art}_bis"), w(f"{art}_da")
        if da == 1.0:
            spawn = 0.0
        elif bis is not None and bis >= 0:
            spawn = bis
        else:
            continue
        name = "elder" if art == "drache" and w("drache_ist_elder") == 1.0 else art
        lage.monster.append(Monster(name, spawn))
    return lage


# --- 2. Kommando -> Aktion, Treffer --------------------------------------------------------------------------------

def treffer(aktion: tuple[str, str] | None, key: str) -> bool:
    """Aktion (Aktion, Ziel) des Kommandos gegen den Schluessel der gespielten Aktion ("Objective:Drache", "Lane" ...).
    Das Ziel zaehlt bei Objective und Rotation, wenn beide eins nennen."""
    if aktion is None or not isinstance(key, str):
        return False
    akt, ziel = aktion
    k_akt, _, k_ziel = key.partition(":")
    if akt != k_akt:
        return False
    if akt in ("Objective", "Rotation") and ziel and k_ziel and k_ziel != "sonst":
        return ziel == k_ziel
    return True


def treffer_flags(aktion: tuple[str, str] | None, flags: int) -> bool:
    """Locker: die Aktion trifft irgendwann in den naechsten 60 s zu (phase1 flags, mehrere moeglich)."""
    if aktion is None or aktion[0] not in AKTIONEN:
        return False
    return bool(int(flags) >> AKTIONEN.index(aktion[0]) & 1)


def key_fuer(aktion: tuple[str, str] | None, q_zeile, keys_liste: list[str]) -> int | None:
    """Index des Modell-Schluessels fuer eine Aktion (fuer den Wert): genau "Akt:Ziel", sonst die beste Variante
    dieser Aktion nach Q (Objective ohne Monster, Rotation ohne Zone)."""
    if aktion is None:
        return None
    akt, ziel = aktion
    genau = f"{akt}:{ziel}" if ziel else akt
    if genau in keys_liste:
        return keys_liste.index(genau)
    kand = [i for i, k in enumerate(keys_liste) if k == akt or k.startswith(akt + ":")]
    if not kand:
        return None
    return max(kand, key=lambda i: float(q_zeile[i]))


# --- 3. Das Gehirn eines Moments (vorberechnet, identisch mit gehirn.bewerte) --------------------------------------

class MomentHirn:
    """Wie gehirn.Gehirn, aber mit den vorberechneten Modellwerten des Moments (q, pi, Gefahr, Siegchance, Jungler) -
    die Logik von bewerte() (Klarheit, Back nur mit Grund, Policy bei unklar) ist die echte (`gehirn_klasse`)."""

    def __init__(self, gehirn_klasse, schluessel, merkmale, schwellen):
        self._g = object.__new__(gehirn_klasse)
        self._g.schluessel, self._g.merkmale = list(schluessel), list(merkmale)
        self._g.idx = {n: i for i, n in enumerate(merkmale)}
        self._g.schwellen = schwellen
        self._jetzt = None
        g = self._g
        g.werte = lambda v: self._jetzt[:3]

    def setzen(self, q, p, gf, sieg=None, jungler=None):
        self._jetzt = (q, p, gf, sieg, jungler)

    def bewerte(self, v, kontext=None):
        return self._g.bewerte(v, mit_grund=False, kontext=kontext)

    def lage_info(self, v):
        _, _, _, sieg, jungler = self._jetzt
        return {"siegchance": sieg, "jungler": jungler or {}, "jungler_unsicherheit": None}


def coach(lage, v, hirn, reihenfolge: str, gefahr_schwelle: float | None = None) -> dict:
    """Ein erster Takt des Entscheiders: Kommando, Form, Aktion(en), G0?, stumm (ohne Daten). `gefahr_schwelle`:
    None = wissen/kern.toml (Auftrag 036); werkzeuge/challenger/gefahr_schwelle.py setzt 0 und unendlich."""
    from lolcoach.makro import aktionen, wahrnehmung
    from lolcoach.makro.takt import Entscheider
    e = Entscheider(hirn=hirn, reihenfolge=reihenfolge, gefahr_schwelle=gefahr_schwelle)
    a = e.entscheide(lage, v, {"welle_gecrasht": False, "spike_fehlt": None, "lane_gegner_backt": False})
    akts = [aktionen.aktion(a.kommando)]
    if a.form == "geteilt" and a.zweite is not None:
        akts.append(aktionen.aktion(a.zweite))
    reg = e._reg
    return {"id": a.kommando.id, "form": a.form, "text": a.vorlage, "aktionen": akts, "g0": a.kommando.id == "G0",
            "stumm": [i for i in a.stumm if not wahrnehmung.fehlt(reg[i].eingaben)], "gefeuert": a.gefeuert,
            "tod60": a.tod60, "unbestaetigt": a.unbestaetigt}


# --- 4. Der alte Kern, soweit anlegbar -----------------------------------------------------------------------------

def alte_lage(x, meta, SP, MI) -> dict | None:
    """Eine Lage fuer kern/testlage (nur Top-Laner, lebend, ausserhalb der Basis): LANE bis 14:00 in der eigenen Lane,
    sonst SEITE/GRUPPE/UNTERWEGS. Welle unbekannt (nicht in den Daten). None: nicht anlegbar."""
    w = lambda n: _wert(x, SP, n)
    if ROLLEN[int(meta[MI["rolle"]])] != "TOP" or w("tot") or w("x") is None or (w("abst_brunnen") or 0) <= 4200:
        return None
    zeit = float(meta[MI["zeit"]])
    uhr = f"{int(zeit // 60)}:{int(zeit % 60):02d}"
    ich = {"level": int(w("level") or 1), "leben": w("leben_anteil") if w("leben_anteil") is not None else 1.0,
           "gold": int(w("gold_tasche") or 0)}
    lg_tot = w("geg0_respawn") if w("geg0_tot") else None
    if zeit < 840 and w("in_eigener_lane") == 1.0:
        e = {"id": "riot", "zeit": uhr, "modus": "LANE", "ich": ich, "welle": {"zustand": "UNBEKANNT"},
             "lane_gegner": ({"tot_noch": lg_tot} if lg_tot is not None else
                             {"abstand": math.hypot(w("lg_x") - w("x"), w("lg_y") - w("y")), "sichtbar": True}
                             if w("lg_nahe_sichtbar") == 1.0 and w("lg_x") is not None else {"sichtbar": False})}
        alter = w("geg1_gesehen_alter")
        if alter is not None:
            e["jungler"] = {"seit": alter}
        return e
    return None          # Mitte (SEITE/GRUPPE) braucht Wellen aller Lanes und Tuerme je Lane - nicht in den Daten


def alter_kern(e: dict) -> tuple[str, str] | None:
    from lolcoach.kern import testlage
    try:
        art = testlage.pruefen(e)["plan"]
    except Exception:
        return None
    a = ALT_AKTION.get(art or "")
    return None if a is None else (a, "")


# --- 5. Auswertung -------------------------------------------------------------------------------------------------

def partie_se(werte, partie):
    import numpy as np
    werte, partie = np.asarray(werte, float), np.asarray(partie)
    if len(werte) == 0:
        return float("nan"), float("nan"), 0
    u, inv = np.unique(partie, return_inverse=True)
    s, c = np.bincount(inv, werte), np.bincount(inv)
    m = s.sum() / c.sum()
    return float(m), float(np.sqrt(((s - m * c) ** 2).sum()) / c.sum()), int(len(u))


def auswerten(P, politiken: dict, beispiele: int = 10) -> dict:
    """P: Pruefdaten (duck-typed wie analyse.Pruefdaten: M, A, F, k, y, q, psi(), keys_liste, partie, MI, AI, FI).
    politiken: Name -> Liste je Moment [{"aktionen": [...], "g0": bool, "form": str, ...} oder None (nicht anlegbar)]."""
    import numpy as np
    n = len(P.k)
    keys = [P.keys_liste[i] if i >= 0 else None for i in P.k]
    flags = P.A[:, P.AI["flags"]]
    sieg = P.M[:, P.MI["sieg"]] == 1
    chall = P.M[:, P.MI["liga"]] == 0
    tod60 = P.F[:, P.FI["tod_60"]] > 0
    psi = {a: P.psi(a) for a in range(len(P.keys_liste))}
    aus = {"n": int(n), "partien": int(len(np.unique(P.partie))), "politiken": {}}
    for name, liste in politiken.items():
        ok = np.array([u is not None for u in liste])
        t_streng = np.array([u is not None and any(treffer(a, keys[i]) for a in u["aktionen"]) for i, u in enumerate(liste)])
        t_locker = np.array([u is not None and any(treffer_flags(a, flags[i]) for a in u["aktionen"])
                             for i, u in enumerate(liste)])
        dr, modell, dr_i = [], [], []
        for i, u in enumerate(liste):
            if u is None or not u["aktionen"] or u["aktionen"][0] is None:
                continue
            j = key_fuer(u["aktionen"][0], P.q[i], P.keys_liste)
            if j is None or P.k[i] < 0:
                continue
            dr.append(psi[j][i] - P.y[i])
            modell.append(P.q[i, j] - P.q[i, P.k[i]])
            dr_i.append(i)
        m, se, np_ = partie_se(dr, P.partie[dr_i]) if dr else (float("nan"), float("nan"), 0)
        quote = lambda maske: float(t_streng[maske & ok].mean()) if (maske & ok).any() else float("nan")
        quote_l = lambda maske: float(t_locker[maske & ok].mean()) if (maske & ok).any() else float("nan")
        alle = np.ones(n, bool)
        r = {"anlegbar": float(ok.mean()), "n": int(ok.sum()),
             "treffer": quote(alle), "treffer_locker": quote_l(alle),
             "treffer_sieger": quote(sieg), "treffer_challenger": quote(chall), "treffer_sieger_challenger": quote(sieg & chall),
             "wert_dr": 100 * m, "wert_dr_se": 100 * se, "wert_partien": np_,
             "wert_modell": 100 * float(np.mean(modell)) if modell else float("nan"),
             "mit_aktion": float(np.mean([u is not None and u["aktionen"][0] is not None for u in liste]))}
        if liste and liste[0] is not None and "g0" in liste[0]:
            g0 = np.array([u is not None and u["g0"] for u in liste])
            r["abdeckung"] = float((~g0 & ok).mean())
            warn = np.array([u is not None and u["form"] == "gefahr" for u in liste])
            r["warnungen"] = float(warn.mean())
            r["warnung_tod60"] = float(tod60[warn].mean()) if warn.any() else float("nan")
            r["grundrate_tod60"] = float(tod60.mean())
            r["ohne_warnung_tod60"] = float(tod60[~warn].mean()) if (~warn).any() else float("nan")   # 036
            r["formen"] = dict(Counter(u["form"] for u in liste if u is not None))
            r["kommandos"] = dict(Counter(u["id"] for u in liste if u is not None).most_common(15))
            r["stumm_je_entscheidung"] = dict(Counter(s for u in liste if u is not None for s in u["stumm"])
                                              .most_common(40))
        aus["politiken"][name] = r
    # Beispiele: zufaellige Momente mit Kommando, gespielter Aktion und Folge (Coach, Reihenfolge wie gewaehlt)
    haupt = next(iter(politiken))
    rng = np.random.default_rng(35)
    kand = [i for i, u in enumerate(politiken[haupt]) if u is not None and not u["g0"]]
    aus["beispiele"] = []
    for i in (rng.choice(kand, min(beispiele, len(kand)), replace=False) if kand else []):
        u = politiken[haupt][int(i)]
        aus["beispiele"].append({
            "minute": round(float(P.M[i, P.MI["zeit"]]) / 60, 1), "rolle": ROLLEN[int(P.M[i, P.MI["rolle"]])],
            "liga": ["Challenger", "Grandmaster", "Master", "unter Master"][int(P.M[i, P.MI["liga"]])],
            "sieg": bool(sieg[i]), "lage": lage_kurz(P, int(i)), "coach": u["text"], "form": u["form"],
            "spieler": keys[int(i)], "treffer": bool(any(treffer(a, keys[int(i)]) for a in u["aktionen"])),
            "tod_60": bool(tod60[i])})
    return aus


def lage_kurz(P, i: int) -> str:
    """Die Lage eines Moments in Worten (fuer die Beispiele)."""
    x, SP = P.X[i], P.SP
    w = lambda n: _wert(x, SP, n)
    teile = [f"Level {int(w('level') or 0)}", f"{int(100 * (w('leben_anteil') or 0))} % Leben",
             f"{int(w('gold_tasche') or 0)} Gold"]
    if w("in_eigener_lane") == 1.0:
        teile.append("in der eigenen Lane")
    tg, tw = int(w("tote_gegner") or 0), int(w("tote_wir") or 0)
    if tg or tw:
        teile.append(f"tot: {tg} Gegner, {tw} eigene")
    for art in ("drache", "baron", "herold", "larven"):
        if w(f"{art}_da") == 1.0:
            teile.append(f"{art} steht")
        elif (b := w(f"{art}_bis")) is not None and 0 <= b <= 90:
            teile.append(f"{art} in {int(b)} s")
    return ", ".join(teile)


def haeufigste(P) -> list:
    """Vergleich: die haeufigste Aktion je Rolle und Minute im TRAINING (Gewichte wie trainiere_pi)."""
    import numpy as np
    import modelle as mo
    import phase1 as f
    D = P.D
    k = mo.key_index(D["keys"], P.keys_liste)
    fit = D["tr"] & (k >= 0)
    M = D["meta"]
    zell = M[:, f.MI["rolle"]] * 64 + np.minimum(M[:, f.MI["zeit"]] // 60, 45)
    tab = np.zeros((5 * 64, len(P.keys_liste)))
    np.add.at(tab, (zell[fit], k[fit]), mo.LIGA_GEWICHT[M[fit, f.MI["liga"]]])
    beste = tab.argmax(1)
    z = P.M[:, f.MI["rolle"]] * 64 + np.minimum(P.M[:, f.MI["zeit"]] // 60, 45)
    out = []
    for i in range(len(P.k)):
        akt, _, ziel = P.keys_liste[beste[z[i]]].partition(":")
        out.append({"aktionen": [(akt, "" if ziel == "sonst" else ziel)]})
    return out


def laden(n: int = 30000):
    """Pruefdaten (analyse.Pruefdaten, n Momente) und das Gehirn der Momente - gemeinsam mit
    werkzeuge/challenger/gefahr_schwelle.py (Auftrag 036). Rueckgabe: (P, hirn, setzen(i)) - setzen(i) legt die
    Modellwerte von Moment i ins Gehirn."""
    import numpy as np
    import analyse
    import gehirn as gh
    import modelle as mo
    import phase1 as f
    analyse.N_STICHPROBE = n
    t0 = time.time()
    P = analyse.Pruefdaten()
    P.SP, P.MI, P.AI, P.FI = f.SP, f.MI, f.AI, f.FI
    print(f"Pruefdaten: {len(P.k)} Momente aus {len(np.unique(P.partie))} Partien ({time.time() - t0:.0f} s)", flush=True)
    import lightgbm as lgb
    V = lgb.Booster(model_file=str(mo.MODELLE / "V.txt"))
    sieg_v = V.predict(P.B, num_threads=mo.FADEN)
    J = lgb.Booster(model_file=str(mo.MODELLE / "jungler.txt"))
    pj = J.predict(P.B, num_threads=mo.FADEN)            # Jungler-Karte je Moment (wie gehirn.lage_info)
    meta = json.loads((mo.MODELLE / "aktionen.json").read_text(encoding="utf-8"))
    k_json = mo.MODELLE / "klarheit.json"
    schwellen = json.loads(k_json.read_text(encoding="utf-8")) if k_json.exists() else \
        {"delta": 0.01, "p_klar": 0.15, "p_geteilt": 0.08}
    hirn = MomentHirn(gh.Gehirn, meta["schluessel"], meta["merkmale"], schwellen)
    assert list(meta["schluessel"]) == list(P.keys_liste)

    def setzen(i: int) -> None:
        hirn.setzen(P.q[i], P.p[i], P.gf[i], float(sieg_v[i]),
                    {gh.BEREICHE[j]: float(x) for j, x in enumerate(pj[i]) if x >= 0.05})
    return P, hirn, setzen


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    wert = lambda name, vorgabe: int(args[args.index(name) + 1]) if name in args else vorgabe
    n, n_alt, n_bsp = wert("--n", 30000), wert("--alt", 3000), wert("--beispiele", 10)
    import numpy as np
    import phase1 as f
    P, hirn, setzen = laden(n)
    politiken = {"Coach (wert)": [], "Coach (fest)": []}
    t0 = time.time()
    for i in range(len(P.k)):
        lage_w = lage_aus_moment(P.X[i], P.M[i], f.SP, f.MI)
        lage_f = lage_aus_moment(P.X[i], P.M[i], f.SP, f.MI)
        setzen(i)
        politiken["Coach (wert)"].append(coach(lage_w, P.B[i], hirn, "wert"))
        politiken["Coach (fest)"].append(coach(lage_f, P.B[i], hirn, "fest"))
        if i % 5000 == 0:
            print(f"  Coach {i}/{len(P.k)} ({time.time() - t0:.0f} s)", flush=True)
    politiken["immer farmen"] = [{"aktionen": [("Lane", "")]} for _ in range(len(P.k))]
    politiken["haeufigste je Rolle und Minute"] = haeufigste(P)
    # der alte Kern: nur Top-Laner in der Lane-Phase (anlegbar), hoechstens n_alt Momente
    alt: list = [None] * len(P.k)
    rng = np.random.default_rng(34)
    kand = [i for i in range(len(P.k)) if alte_lage(P.X[i], P.M[i], f.SP, f.MI) is not None]
    for i in (rng.choice(kand, min(n_alt, len(kand)), replace=False) if kand else []):
        a = alter_kern(alte_lage(P.X[i], P.M[i], f.SP, f.MI))
        alt[int(i)] = {"aktionen": [a]}
    politiken["alter Kern (--kern neu, Top/Lane)"] = alt
    ergebnis = auswerten(P, politiken, n_bsp)
    # die Vergleiche auf denselben Momenten wie der alte Kern (fair)
    nur = [i for i, u in enumerate(alt) if u is not None]
    if nur:
        teil = _teilmenge(P, nur)
        ergebnis["auf_den_alt_momenten"] = auswerten(teil, {k: [v[i] for i in nur] for k, v in politiken.items()}, 0)
    ergebnis["reihenfolge"] = ("wert" if _besser(ergebnis, "Coach (wert)", "Coach (fest)") else "fest")
    AUS.write_text(json.dumps(ergebnis, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    drucken(ergebnis)
    print(f"-> {AUS}")


def _teilmenge(P, idx):
    from types import SimpleNamespace
    q = SimpleNamespace(M=P.M[idx], A=P.A[idx], F=P.F[idx], k=P.k[idx], y=P.y[idx], q=P.q[idx], X=P.X[idx],
                        keys_liste=P.keys_liste, partie=P.partie[idx], MI=P.MI, AI=P.AI, FI=P.FI, SP=P.SP)
    q.psi = lambda a: P.psi(a)[idx]
    return q


def _besser(e: dict, a: str, b: str) -> bool:
    """Die bessere Reihenfolge: hoeherer Wert (doppelt robust); bei Gleichstand im Standardfehler die hoehere Treffer-
    quote."""
    pa, pb = e["politiken"][a], e["politiken"][b]
    if abs(pa["wert_dr"] - pb["wert_dr"]) > max(pa["wert_dr_se"], pb["wert_dr_se"]):
        return pa["wert_dr"] > pb["wert_dr"]
    return pa["treffer"] >= pb["treffer"]


def drucken(e: dict) -> None:
    pc = lambda x: "  -  " if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:4.1f} %"
    pp = lambda x, s: "   -   " if math.isnan(x) else f"{x:+.2f} ± {s:.2f}"
    print(f"\nChallenger-Treue: {e['n']} Momente aus {e['partien']} Pruefpartien")
    print(f"{'Politik':38} {'anlegbar':>8} {'Treffer':>8} {'locker':>8} {'Sieger':>8} {'Chall.':>8} {'S+C':>8} "
          f"{'Wert (DR, Pkt)':>16} {'Modell':>7}")
    for name, r in e["politiken"].items():
        print(f"{name:38} {pc(r['anlegbar']):>8} {pc(r['treffer']):>8} {pc(r['treffer_locker']):>8} "
              f"{pc(r['treffer_sieger']):>8} {pc(r['treffer_challenger']):>8} {pc(r['treffer_sieger_challenger']):>8} "
              f"{pp(r['wert_dr'], r['wert_dr_se']):>16} {r['wert_modell']:+7.2f}")
    for name in ("Coach (wert)", "Coach (fest)"):
        r = e["politiken"][name]
        print(f"{name}: Abdeckung {pc(r['abdeckung'])}, mit Aktion {pc(r['mit_aktion'])}, Warnungen {pc(r['warnungen'])}"
              f" (Tod in 60 s nach Warnung {pc(r['warnung_tod60'])}, ohne Warnung {pc(r.get('ohne_warnung_tod60'))}, "
              f"Grundrate {pc(r['grundrate_tod60'])}), "
              f"Formen {r['formen']}")
    print(f"Reihenfolge: {e['reihenfolge']} bleibt")
    if "auf_den_alt_momenten" in e:
        print("\nAuf den Momenten, an die sich der alte Kern anlegen laesst:")
        for name, r in e["auf_den_alt_momenten"]["politiken"].items():
            print(f"  {name:38} Treffer {pc(r['treffer'])}, Wert {pp(r['wert_dr'], r['wert_dr_se'])}")
    for b in e.get("beispiele", []):
        print(f"  {b['minute']:5.1f} min {b['rolle']:7} {b['liga']:11} {'Sieg ' if b['sieg'] else 'Niederl.'} | "
              f"{b['lage']} | Coach: {b['coach']} | Spieler: {b['spieler']} {'TREFFER' if b['treffer'] else ''}")


if __name__ == "__main__":
    main()
