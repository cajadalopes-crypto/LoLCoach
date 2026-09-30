"""Auftrag 031, Abschnitte 1 (Plausibilitaet), 2 (Klarheit) und 3 (Ketten) - alles auf der PRUEFUNG.

    python werkzeuge/challenger/analyse.py      -> daten/challenger/modelle/analyse.json + klarheit.json

Doppelt robust (AIPW): fuer Aktion a und Moment i ist
    psi_a = Q(x_i, a) + 1{A_i = a} * (Y_i - Q(x_i, a)) / e(a | x_i)
mit Y = Siegchance-Aenderung in 120 s, Q = Outcome-Modell, e = pi (Neigung, auf 0,02 geklemmt). Der Unterschied
psi_a - psi_b gemittelt ueber eine Lage-Gruppe schaetzt, was a statt b dort bringt - verglichen werden so nur aehnliche
Lagen (die Lage steckt in Q und e). Unsicherheit: Standardfehler ueber Partien (Momente einer Partie haengen zusammen).
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict

import lightgbm as lgb
import numpy as np

import grundlage as g
import modelle as mo
import phase1 as f

E_MIN = 0.02
N_STICHPROBE = 300_000


def partie_se(werte, partie):
    """Mittelwert und Standardfehler mit Partien als Einheit."""
    if len(werte) == 0:
        return np.nan, np.nan, 0
    u, inv = np.unique(partie, return_inverse=True)
    s = np.bincount(inv, werte)
    c = np.bincount(inv)
    m = s.sum() / c.sum()
    # Cluster-robuster SE eines Mittelwerts
    r = s - m * c
    se = np.sqrt((r ** 2).sum()) / c.sum()
    return float(m), float(se), int(len(u))


class Pruefdaten:
    def __init__(self):
        mo.niedrige_prioritaet()
        D = mo.lade_alles()
        self.keys_liste = json.loads((mo.MODELLE / "aktionen.json").read_text(encoding="utf-8"))["schluessel"]
        self.K = len(self.keys_liste)
        dv = np.load(mo.MODELLE / "delta_v.npy")
        k = mo.key_index(D["keys"], self.keys_liste)
        te = D["te"] & (k >= 0) & ~np.isnan(dv) & (D["X"][:, f.SP["tot"]] == 0)
        rng = np.random.default_rng(31)
        idx = np.sort(rng.choice(np.where(te)[0], min(N_STICHPROBE, te.sum()), replace=False))
        self.idx = idx
        self.X = D["X"][idx]
        self.M = D["meta"][idx]
        self.A = D["aktion"][idx]
        self.F = D["folge"][idx]
        self.B = D["B"][idx]
        self.k = k[idx]
        self.y = dv[idx]
        self.partie = self.M[:, f.MI["partie"]]
        lade = lambda n: lgb.Booster(model_file=str(mo.MODELLE / f"{n}.txt"))
        Q, G, pi = lade("Q"), lade("gefahr60"), lade("pi")
        n = len(idx)
        self.q = np.zeros((n, self.K), np.float32)
        self.gf = np.zeros((n, self.K), np.float32)
        for a in range(self.K):
            Z = mo.mit_aktion(self.B, np.full(n, a))
            self.q[:, a] = Q.predict(Z, num_threads=mo.FADEN)
            self.gf[:, a] = G.predict(Z, num_threads=mo.FADEN)
        self.p = pi.predict(self.B, num_threads=mo.FADEN).astype(np.float32)
        e = np.clip(self.p[np.arange(n), self.k], E_MIN, 1)
        rest = self.y - self.q[np.arange(n), self.k]
        self.korr = rest / e                        # AIPW-Korrektur, gilt nur fuer die beobachtete Aktion
        # ganze Daten fuer die Ketten
        self.D = D
        self.dv = dv

    def a(self, name: str) -> int:
        return self.keys_liste.index(name)

    def psi(self, a: int) -> np.ndarray:
        return self.q[:, a] + np.where(self.k == a, self.korr, 0.0)

    def vergleich(self, maske, a, b, was="Q"):
        """Modell: Mittel Q(a)-Q(b) (bzw. Gefahr) und Anteil Lagen mit a besser; DR: psi_a - psi_b mit SE."""
        ia = [self.a(x) for x in (a if isinstance(a, list) else [a])]
        ib = [self.a(x) for x in (b if isinstance(b, list) else [b])]
        M_ = self.q if was == "Q" else self.gf
        va = M_[maske][:, ia].max(1) if was == "Q" else M_[maske][:, ia].min(1)
        vb = M_[maske][:, ib].max(1) if was == "Q" else M_[maske][:, ib].min(1)
        d = va - vb
        out = {"n": int(maske.sum()), "modell_mittel": float(d.mean()) if len(d) else np.nan,
               "modell_anteil": float((d > 0).mean()) if len(d) else np.nan}
        if was == "Q" and len(ia) == 1 and len(ib) == 1 and maske.sum():
            ps = self.psi(ia[0])[maske] - self.psi(ib[0])[maske]
            m, se, np_ = partie_se(ps, self.partie[maske])
            out.update({"dr": m, "dr_se": se, "partien": np_,
                        "n_a": int((self.k[maske] == ia[0]).sum()), "n_b": int((self.k[maske] == ib[0]).sum())})
        if was == "G":
            out["gefahr_a"] = float(va.mean()) if len(va) else np.nan
            out["gefahr_b"] = float(vb.mean()) if len(vb) else np.nan
        return out

    # ---- Lage-Masken (nur Wissbares)
    def sp(self, n):
        return self.X[:, f.SP[n]]

    def gegner_nah(self, r=1500, alter=8):
        x, y = self.sp("x"), self.sp("y")
        nah = self.sp("lg_nahe_sichtbar") == 1
        for i in range(5):
            gx, gy, ga = self.sp(f"geg{i}_gesehen_x"), self.sp(f"geg{i}_gesehen_y"), self.sp(f"geg{i}_gesehen_alter")
            tot = self.sp(f"geg{i}_tot") == 1
            nah |= (~tot) & (ga <= alter) & (np.hypot(gx - x, gy - y) <= r)
        return nah

    def gegner_unbekannt(self, alter=20):
        c = np.zeros(len(self.X))
        for i in range(5):
            ga = self.sp(f"geg{i}_gesehen_alter")
            tot = self.sp(f"geg{i}_tot") == 1
            c += (~tot) & (np.isnan(ga) | (ga > alter))
        return c

    def mit_an(self, pos, r=3000):
        c = np.zeros(len(self.X))
        for i in range(1, 5):
            c += np.nan_to_num(np.hypot(self.sp(f"mit{i}_x") - pos[0], self.sp(f"mit{i}_y") - pos[1]), nan=1e9) <= r
        return c


def plausibel(P: Pruefdaten) -> list[dict]:
    m = P.sp("minute")
    rolle = P.M[:, f.MI["rolle"]]
    laner = rolle != 1
    ber = P.sp("bereich")
    erg = []

    def pruefe(name, maske, a, b, was, erwartet, art="vorgegeben", extra=None):
        r = P.vergleich(maske, a, b, was)
        if was == "Q":
            ok = r["modell_mittel"] > 0 and r["modell_anteil"] > 0.5
        else:   # Gefahr: a soll gefaehrlicher sein
            ok = r["modell_mittel"] > 0 and r["modell_anteil"] > 0.5
            if extra is not None:
                ok = ok and r["gefahr_a"] >= extra
        r.update({"name": name, "a": a, "b": b, "was": was, "erwartet": erwartet, "bestanden": bool(ok), "art": art})
        erg.append(r)

    # 1. Wenig Leben, Gegner nah: Back schlaegt Bleiben (Wert) und ist sicherer (Gefahr)
    s1 = (P.sp("leben_anteil") < 0.3) & P.gegner_nah() & laner & (P.sp("in_eigener_lane") == 1)
    pruefe("Wenig Leben (< 30 %), Gegner nah, in der Lane: Back schlaegt Bleiben", s1, "Back", "Lane", "Q", "Back > Lane")
    pruefe("... und Bleiben ist gefaehrlicher als Back", s1, "Lane", "Back", "G", "Gefahr Lane > Back")
    # 2. Nach einem Ace (5 Gegner tot) mit Baron oben: Baron schlaegt Farmen
    s2 = (P.sp("tote_gegner") >= 5) & (P.sp("baron_da") == 1)
    pruefe("Ace, Baron steht: Baron schlaegt Farmen (Lane/Jungle)", s2, "Objective:Baron", ["Lane", "Jungle"], "Q",
           "Baron > Farmen")
    # Untersuchung (nicht Teil der Pruefung): was tun High-Elo-Spieler nach einem Ace, und was empfiehlt das Gehirn?
    getan = Counter(P.keys_liste[k] for k in P.k[s2])
    kand = P.p[s2] >= 0.02
    best = np.where(kand, P.q[s2], -np.inf).argmax(1)
    erg[-1]["untersuchung"] = {"getan": getan.most_common(6),
                              "gehirn_empfiehlt": Counter(P.keys_liste[k] for k in best).most_common(6),
                              "baron_vs_basis": P.vergleich(s2, "Objective:Baron", "Unterwegs:gegn. Basis", "Q")}
    # 3. Allein Split ab 25:00, drei Gegner unbekannt: hohes Todesrisiko
    s3 = (m >= 25) & np.isin(ber, [2, 4]) & (P.sp("mit_nah") == 0) & (P.gegner_unbekannt() >= 3)
    basis = float(np.nanmean(P.F[(m >= 25), f.FI["tod_60"]]))
    pruefe("Split allein ab 25:00, >= 3 Gegner unbekannt: Split gefaehrlicher als Gruppe (und ueber 2x Grundrate)",
           s3, "Split", "Gruppe", "G", "Gefahr Split > Gruppe", extra=2 * basis)
    # 4. Objective in 60 s, Team dort: zum Objective schlaegt die Seitenwelle
    drache_bald = (P.sp("drache_da") == 1) | ((P.sp("drache_bis") > 0) & (P.sp("drache_bis") <= 60))
    s4 = drache_bald & (P.sp("drache_ist_elder") == 0) & (P.mit_an(g.DRACHE) >= 2) & (P.sp("abst_drache") > 3000) & laner
    pruefe("Drache in <= 60 s, >= 2 Mitspieler dort: Drache schlaegt Seitenwelle", s4, "Objective:Drache",
           ["Lane", "Split"], "Q", "Drache > Seitenwelle")
    return erg


def aus_den_daten(P: Pruefdaten, n_regeln=10) -> list[dict]:
    """Lage-Gruppen x Aktionspaare, doppelt robust geschaetzt; die zehn staerksten (|z| gross, n >= 200 Partien,
    je Gruppe nur eine) werden zu Pruefungen fuer das Modell."""
    m = P.sp("minute")
    rolle = P.M[:, f.MI["rolle"]]
    lane_geg_tot = np.zeros(len(m), bool)
    for r in range(5):
        lane_geg_tot |= (rolle == r) & (P.sp(f"geg{r}_tot") == 1)
    gruppen = {
        "Gegner-Inhibitor offen": P.sp("inhibs_offen_wir") >= 1,
        "eigener Inhibitor offen": P.sp("inhibs_offen_gegner") >= 1,
        "wir haben Baron-Buff": P.sp("baron_buff_wir") > 0,
        "Gegner hat Baron-Buff": P.sp("baron_buff_gegner") > 0,
        "mind. 1500 Gold in der Tasche": P.sp("gold_tasche") >= 1500,
        "Leben unter 35 %": P.sp("leben_anteil") < 0.35,
        "Seelenpunkt, Drache in <= 60 s": ((P.sp("drachen_wir") == 3) | (P.sp("drachen_gegner") == 3)) &
                                           ((P.sp("drache_da") == 1) | (P.sp("drache_bis") <= 60)),
        "Gegner-Jungler tot": P.sp("geg1_tot") == 1,
        "mind. 2 Gegner tot": P.sp("tote_gegner") >= 2,
        "mind. 2 von uns tot": P.sp("tote_wir") >= 2,
        "Lane-Phase, Lane-Gegner tot": (m < 14) & lane_geg_tot & (rolle != 1),
        "Herold steht": P.sp("herold_da") == 1,
        "Larven stehen": P.sp("larven_da") == 1,
        "ab 30:00": m >= 30,
        "Gegner-Jungler vor < 15 s gesehen": P.sp("geg1_gesehen_alter") < 15,
        "Baron steht, ab 25:00": (P.sp("baron_da") == 1) & (m >= 25),
        "Team 3000+ Items hinten": P.sp("diff_itemwert_team") <= -3000,
        "Team 3000+ Items vorn": P.sp("diff_itemwert_team") >= 3000,
    }
    paare = [("Back", "Lane"), ("Back", "Warten"), ("Back", "Gruppe"), ("Objective:Drache", "Lane"),
             ("Objective:Baron", "Lane"), ("Objective:Baron", "Back"), ("Gruppe", "Split"), ("Gruppe", "Lane"),
             ("Split", "Back"), ("Objective:Herold", "Lane"), ("Objective:Larven", "Lane"), ("Lane", "Warten"),
             ("Objective:Drache", "Back"), ("Gruppe", "Back")]
    paare = [(a, b) for a, b in paare if a in P.keys_liste and b in P.keys_liste]
    kand = []
    for gname, mask in gruppen.items():
        for a, b in paare:
            r = P.vergleich(mask, a, b, "Q")
            if r.get("partien", 0) < 200 or r["n_a"] < 100 or r["n_b"] < 100 or not r["dr_se"]:
                continue
            z = r["dr"] / r["dr_se"]
            kand.append((abs(z), gname, a, b, r, z))
    kand.sort(key=lambda t: -t[0])
    erg, gesehen = [], set()
    for az, gname, a, b, r, z in kand:
        if gname in gesehen or az < 3:
            continue
        gesehen.add(gname)
        besser, schlechter = (a, b) if z > 0 else (b, a)
        rr = P.vergleich(gruppen[gname], besser, schlechter, "Q")
        ok = rr["modell_mittel"] > 0 and rr["modell_anteil"] > 0.5
        rr.update({"name": f"{gname}: {besser} schlaegt {schlechter} (Daten, doppelt robust)", "a": besser,
                   "b": schlechter, "was": "Q", "erwartet": f"{besser} > {schlechter}", "bestanden": bool(ok),
                   "art": "aus den Daten", "z": float(abs(z))})
        erg.append(rr)
        if len(erg) >= n_regeln:
            break
    return erg


def klarheit(P: Pruefdaten) -> dict:
    """Schwelle delta = kleinster Wert-Abstand (beste - zweitbeste), ab dem die doppelt robuste Schaetzung auf der
    Pruefung den Vorsprung der besten Aktion bestaetigt (untere 95-%-Grenze > 0, auch fuer alle groesseren Abstaende)."""
    n = len(P.X)
    kand = P.p >= 0.02
    qm = np.where(kand, P.q, -np.inf)
    ordn = np.argsort(-qm, 1)
    b, z = ordn[:, 0], ordn[:, 1]
    gap = P.q[np.arange(n), b] - P.q[np.arange(n), z]
    gap = np.where(np.isfinite(qm[np.arange(n), z]), gap, 0)
    psi_d = np.zeros(n)
    for a in range(P.K):
        psi_d += np.where(b == a, P.psi(a), 0) - np.where(z == a, P.psi(a), 0)
    rand = np.quantile(gap, np.linspace(0, 1, 11))
    stufen = []
    for i in range(10):
        mk = (gap >= rand[i]) & (gap < rand[i + 1] if i < 9 else gap <= rand[i + 1])
        mm, se, np_ = partie_se(psi_d[mk], P.partie[mk])
        stufen.append({"von": float(rand[i]), "bis": float(rand[i + 1]), "modell": float(gap[mk].mean()), "dr": mm,
                       "dr_se": se, "n": int(mk.sum())})
    delta = None
    for i in range(10):
        if all(s["dr"] - 1.96 * s["dr_se"] > 0 for s in stufen[i:]):
            delta = stufen[i]["von"]
            break
    if delta is None:
        delta = float(rand[-2])
    schw = {"delta": float(delta), "p_klar": 0.15, "p_geteilt": 0.08}
    pb = P.p[np.arange(n), b]
    pz = P.p[np.arange(n), z]
    stufe = np.where((gap >= schw["delta"]) & (pb >= schw["p_klar"]), "klar",
                     np.where((pb >= schw["p_geteilt"]) & (pz >= schw["p_geteilt"]), "geteilt", "unklar"))
    anteil = {s: float((stufe == s).mean()) for s in ("klar", "geteilt", "unklar")}
    # Gegenprobe: in "klar" - was brachte es, wenn der Spieler die empfohlene Aktion tat, gegenueber der zweiten?
    kl = stufe == "klar"
    mm, se, np_ = partie_se(psi_d[kl], P.partie[kl])
    befolgt = float((P.k[kl] == b[kl]).mean())
    je_rolle = {}
    for r, rn in enumerate(f.ROLLEN):
        mr = P.M[:, f.MI["rolle"]] == r
        je_rolle[rn] = {s: float((stufe[mr] == s).mean()) for s in ("klar", "geteilt", "unklar")}
    # haeufigste Empfehlungen je Stufe
    top_klar = Counter(P.keys_liste[i] for i in b[kl]).most_common(8)
    top_geteilt = Counter(f"{P.keys_liste[i]} / {P.keys_liste[j]}" for i, j in zip(b[stufe == "geteilt"], z[stufe == "geteilt"])).most_common(8)
    (mo.MODELLE / "klarheit.json").write_text(json.dumps(schw), encoding="utf-8")
    return {"schwellen": schw, "stufen_gap": stufen, "anteil": anteil, "je_rolle": je_rolle,
            "klar_dr_vorsprung": mm, "klar_dr_se": se, "klar_befolgt": befolgt,
            "top_klar": top_klar, "top_geteilt": top_geteilt}


# ---------------------------------------------------------------- Ketten und Umwandlung

def basis_name(A):
    a0 = A[:, f.AI["a0"]]
    return np.array([f.AKTIONEN[x] if x >= 0 else "–" for x in a0])


def ketten(P: Pruefdaten) -> dict:
    D = P.D
    M, A, X = D["meta"], D["aktion"], D["X"]
    tr = D["te"] | D["tr"]           # beschreibend: alle Partien
    erg = {}
    # 1. 120 s vor einem genommenen vs. verlorenen Objective: was tun die Rollen?
    obj = np.concatenate([np.load(t)["obj"] for t in sorted(f.ZIEL.glob("teil_*.npz"))])
    partie = M[:, f.MI["partie"]]
    zeit = M[:, f.MI["zeit"]]
    team = M[:, f.MI["team"]]
    rolle = M[:, f.MI["rolle"]]
    grenzen = np.searchsorted(partie, np.arange(partie.max() + 2))
    a0 = A[:, f.AI["a0"]]
    wohin = A[:, f.AI["wohin"]]
    vorher = defaultdict(Counter)
    for art in (1, 2, 3, 4):                   # Drache, Baron, Herold, Larven
        oo = obj[obj[:, 2] == art]
        if art == 4:                            # Larven: nur die erste je Partie (drei Kills je Spawn)
            _, erst = np.unique(oo[:, 0], return_index=True)
            oo = oo[erst]
        grube = 5 if art == 1 else 6
        for p_nr, t_o, _, t_team, *_ in oo:
            if t_team < 0:
                continue
            lo, hi = grenzen[p_nr], grenzen[p_nr + 1]
            sel = np.arange(lo, hi)
            sel = sel[(zeit[sel] >= t_o - 120) & (zeit[sel] < t_o)]
            for i in sel:
                seite = "genommen" if team[i] == t_team else "verloren"
                c = vorher[(f.MONSTER[art], seite, f.ROLLEN[rolle[i]])]
                c["n"] += 1
                c["an der Grube"] += wohin[i] == grube
                c["Back"] += a0[i] == 1
                c["Lane"] += a0[i] == 8
                c["Tot"] += a0[i] == 0
                c["Gruppe"] += a0[i] == 6
    erg["vor_objective"] = {"|".join(k): dict(v) for k, v in vorher.items()}
    # 2. Nach einem gewonnenen Kampf (Kill-Moment, mind. 2 Gegner mehr tot): was tun sie, was bringt es?
    nach = (P.M[:, f.MI["anlass"]] == 1) & (P.sp("tote_gegner") - P.sp("tote_wir") >= 2)
    umw = {}
    for name in ("Objective:Drache", "Objective:Baron", "Objective:Herold", "Back", "Lane", "Gruppe", "Split", "Jungle",
                 "Unterwegs:Midlane", "Unterwegs:gegn. Jungle oben", "Unterwegs:gegn. Jungle unten"):
        if name not in P.keys_liste:
            continue
        a = P.a(name)
        mm, se, np_ = partie_se(P.psi(a)[nach], P.partie[nach])
        umw[name] = {"anteil_getan": float((P.k[nach] == a).mean()), "dr_wert": mm, "dr_se": se}
    erg["nach_gewonnenem_kampf"] = {"n": int(nach.sum()), "aktionen": umw,
                                    "folge_60": {"gebaeude_wir": float(np.nanmean(P.F[nach, f.FI["gebaeude_wir_60"]])),
                                                 "obj_wir": float(np.nanmean(P.F[nach, f.FI["obj_wir_60"]])),
                                                 "platten_wir": float(np.nanmean(P.F[nach, f.FI["platten_wir_60"]]))}}
    # 3. Ketten a0 -> a1 -> a2 (Grundaktionen) mit Wert (Siegchance-Aenderung 180 s, beschreibend) und Sieg
    vhat = np.load(mo.MODELLE / "vhat.npy")
    dv180 = mo.delta_v(D, vhat, sek=180)
    lebt = X[:, f.SP["tot"]] == 0
    kette = np.char.add(np.char.add(np.char.add(basis_name(A), " > "),
                                    np.char.add(np.array([f.AKTIONEN[x] if x >= 0 else "–" for x in A[:, f.AI["a1"]]]), " > ")),
                        np.array([f.AKTIONEN[x] if x >= 0 else "–" for x in A[:, f.AI["a2"]]]))
    je_rolle = {}
    for r, rn in enumerate(f.ROLLEN):
        mr = lebt & (rolle == r) & ~np.isnan(dv180)
        u, inv, cnt = np.unique(kette[mr], return_inverse=True, return_counts=True)
        s = np.bincount(inv, dv180[mr])
        sieg = np.bincount(inv, M[mr, f.MI["sieg"]])
        top = np.argsort(-cnt)[:12]
        je_rolle[rn] = [{"kette": str(u[i]), "n": int(cnt[i]), "dv180": float(s[i] / cnt[i]),
                         "sieg": float(sieg[i] / cnt[i])} for i in top if "–" not in u[i]]
    erg["ketten"] = je_rolle
    return erg


def main():
    P = Pruefdaten()
    out = {"stichprobe": int(len(P.idx)), "aktionen": P.keys_liste}
    out["plausibel"] = plausibel(P) + aus_den_daten(P)
    out["klarheit"] = klarheit(P)
    out["ketten"] = ketten(P)
    (mo.MODELLE / "analyse.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    for r in out["plausibel"]:
        print(("OK  " if r["bestanden"] else "DURCHGEFALLEN ") + r["name"], {k: r.get(k) for k in ("n", "modell_mittel", "modell_anteil", "dr", "dr_se")})
    print(out["klarheit"]["schwellen"], out["klarheit"]["anteil"])


if __name__ == "__main__":
    main()
