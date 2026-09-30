"""Challenger-Gehirn, Stufe 2 (Auftrag 031): die Modelle - trainiert auf Training, gemessen auf Pruefung.

    python werkzeuge/challenger/modelle.py            trainiert alles, schreibt daten/challenger/modelle/ + messung.json
    python werkzeuge/challenger/modelle.py V pi       nur diese

Modelle (LightGBM, CPU, niedrige Prozessprioritaet):
    V        Siegchance aus der Lage (nur Wissbares). Vergleich: Gold-Abstand allein (verdeckt!) und Item-Abstand.
    pi       Challenger-Policy: welche Aktion (mit Ziel) waehlt ein High-Elo-Spieler dieser Rolle hier?
             Gewicht Challenger 3, GM 2, Master 1. Vergleich: haeufigste Aktion je Rolle und Minute.
    Q        Aktionswert: Siegchance-Aenderung in 120 s, gegeben Lage + Aktion (Outcome-Modell der doppelt robusten
             Schaetzung). Vergleich Q0: dasselbe ohne Aktion ("jede Aktion gleich").
    gefahr30/60  Tod in 30/60 s, gegeben Lage + Aktion. Vergleich: Minute + Ort allein.
    jungler  Wo ist der Gegner-Jungler (11 Bereiche + tot)? Vergleich: Verteilung je Minute.

Die Siegchance-Aenderung (Ziel von Q) kommt aus V, kreuzgeschaetzt (V fuer Trainingspartien aus dem Modell der
jeweils anderen Haelfte), damit V seine eigenen Trainingspartien nicht auswendig "vorhersagt".
"""
from __future__ import annotations

import ctypes
import json
import sys
import time

import lightgbm as lgb
import numpy as np

import grundlage as g
import phase1 as f

MODELLE = g.ABLAGE / "modelle"
MESSUNG = MODELLE / "messung.json"
FADEN = 24
LIGA_GEWICHT = np.array([3.0, 2.0, 1.0, 1.0])
MIN_KEY = 1500               # Aktion+Ziel mit weniger Trainingsfaellen -> "sonst" der Aktion


def niedrige_prioritaet():
    try:
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    except Exception:
        pass


# ---------------------------------------------------------------- Daten

# Entscheidung zu Stufe 2 (Buch 17, 30.09.2026): keine Gegner-Items/-Level (Live-API zeigt sie nur "wie zuletzt
# gesehen"). Heraus faellt das ganze Gegner-Scoreboard aus Items, Level und CS - genau die Menge, deren Verzicht in 031
# gemessen wurde (Siegchance 0,163).
GEGNER_SCOREBOARD = ["itemwert_team_gegner", "level_team_gegner", "cs_team_gegner", "diff_itemwert_team",
                     "diff_level_team", "diff_itemwert_lane", "diff_level_lane", "diff_cs_lane"]
X_SPALTEN = [i for i, n in enumerate(f.NAMEN) if n not in GEGNER_SCOREBOARD]
BASIS_NAMEN = [f.NAMEN[i] for i in X_SPALTEN] + ["rolle", "seite", "anlass"]


def basis(D) -> np.ndarray:
    M = D["meta"]
    return np.hstack([D["X"][:, X_SPALTEN], M[:, [f.MI["rolle"], f.MI["team"], f.MI["anlass"]]].astype(np.float32)])


def aktion_schluessel(A) -> np.ndarray:
    """(a0, Ziel) als Text-Schluessel: Objective:<Monster>, Rotation:<Zone>, Unterwegs:<Wohin>, sonst die Aktion."""
    a0, ziel = A[:, f.AI["a0"]], A[:, f.AI["ziel"]]
    out = np.empty(len(a0), dtype=object)
    for k, name in enumerate(f.AKTIONEN):
        m = a0 == k
        if name == "Objective":
            out[m] = [f"Objective:{f.MONSTER[z]}" for z in ziel[m]]
        elif name == "Rotation":
            out[m] = [f"Rotation:{f.ZONEN[z]}" for z in ziel[m]]
        elif name == "Unterwegs":
            out[m] = [f"Unterwegs:{f.WOHIN[z]}" for z in ziel[m]]
        else:
            out[m] = name
    out[a0 < 0] = "–"
    return out


def schluessel_liste(keys, tr) -> list[str]:
    u, c = np.unique(keys[tr], return_counts=True)
    gut = [k for k, n in zip(u, c) if n >= MIN_KEY and k not in ("Tot", "–")]
    sonst = sorted({k.split(":")[0] + ":sonst" for k, n in zip(u, c) if n < MIN_KEY and ":" in k})
    return sorted(gut) + sonst


def key_index(keys, liste) -> np.ndarray:
    pos = {k: i for i, k in enumerate(liste)}
    idx = np.array([pos.get(k, pos.get(k.split(":")[0] + ":sonst", -1)) if isinstance(k, str) else -1 for k in keys])
    return idx


def lade_alles():
    D = f.lade(("X", "meta", "aktion", "folge", "verdeckt"))
    M = D["meta"]
    D["tr"] = M[:, f.MI["aufteilung"]] == 0
    D["te"] = ~D["tr"]
    D["B"] = basis(D)
    D["keys"] = aktion_schluessel(D["aktion"])
    return D


def spiel_gewicht(M) -> np.ndarray:
    """Jede Partie zaehlt gleich (lange Partien haben mehr Momente)."""
    _, inv, cnt = np.unique(M[:, f.MI["partie"]], return_inverse=True, return_counts=True)
    w = 1.0 / cnt[inv]
    return w / w.mean()


def halbe(M) -> np.ndarray:
    return M[:, f.MI["partie"]].astype(np.int64) % 4 < 2        # unabhaengig von valid_maske (die nimmt nur gerade)


def valid_maske(M, tr) -> np.ndarray:
    """10 % der Trainingspartien als Abbruch-Kontrolle (early stopping)."""
    return tr & ((M[:, f.MI["partie"]].astype(np.int64) * 40503 % 2**16) % 10 == 0)


def trainiere(params, X, y, w, Xv, yv, wv, runden=600, cat=None):
    p = dict(params, num_threads=FADEN, verbose=-1, seed=31)
    ds = lgb.Dataset(X, y, weight=w, categorical_feature=cat or "auto", free_raw_data=True)
    dv = lgb.Dataset(Xv, yv, weight=wv, reference=ds, categorical_feature=cat or "auto")
    return lgb.train(p, ds, runden, valid_sets=[dv], callbacks=[lgb.early_stopping(30, verbose=False)])


# ---------------------------------------------------------------- Messgroessen

def logloss(p, y, w=None):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(np.average(-(y * np.log(p) + (1 - y) * np.log(1 - p)), weights=w))


def brier(p, y, w=None):
    return float(np.average((p - y) ** 2, weights=w))


def kalibrierung(p, y, stufen=10):
    rand = np.quantile(p, np.linspace(0, 1, stufen + 1))
    b = np.clip(np.searchsorted(rand, p, side="right") - 1, 0, stufen - 1)
    rows = [(float(p[b == i].mean()), float(y[b == i].mean()), int((b == i).sum())) for i in range(stufen) if (b == i).any()]
    ece = sum(n * abs(a - c) for a, c, n in rows) / max(1, sum(n for *_, n in rows))
    return rows, float(ece)


MIN_BEREICHE = [("0-10", 0, 10), ("10-20", 10, 20), ("20-30", 20, 30), ("30+", 30, 999)]


# ---------------------------------------------------------------- V

V_PARAMS = dict(objective="binary", learning_rate=0.05, num_leaves=127, min_data_in_leaf=400, feature_fraction=0.7,
                bagging_fraction=0.7, bagging_freq=1, lambda_l2=5.0)


def trainiere_V(D, messung):
    M, B, tr, te = D["meta"], D["B"], D["tr"], D["te"]
    y = M[:, f.MI["sieg"]].astype(np.float32)
    w = spiel_gewicht(M)
    va = valid_maske(M, tr)
    fit = tr & ~va
    t0 = time.time()
    V = trainiere(V_PARAMS, B[fit], y[fit], w[fit], B[va], y[va], w[va])
    V.save_model(str(MODELLE / "V.txt"))
    # kreuzgeschaetzt fuer die Trainingspartien
    vhat = np.zeros(len(y), np.float32)
    vhat[te] = V.predict(B[te], num_threads=FADEN)
    h = halbe(M)
    for seite in (True, False):
        fit2 = tr & ~va & (h == seite)
        va2 = va & (h == seite)
        m2 = trainiere(V_PARAMS, B[fit2], y[fit2], w[fit2], B[va2], y[va2], w[va2])
        ziel = tr & (h != seite)
        vhat[ziel] = m2.predict(B[ziel], num_threads=FADEN)
    np.save(MODELLE / "vhat.npy", vhat)
    # Vergleiche: Gold-Abstand allein (verdeckt, im Spiel NICHT sichtbar) und Item-Abstand (sichtbar), je Minuten-Stufe
    minute = D["X"][:, f.SP["minute"]]
    stufe = np.clip((minute // 5).astype(int), 0, 8)

    def logistisch(merkmal):
        from sklearn.linear_model import LogisticRegression
        Z = np.zeros((len(y), 18), np.float32)
        Z[np.arange(len(y)), stufe] = 1
        Z[np.arange(len(y)), 9 + stufe] = merkmal / 1000.0
        rng = np.random.default_rng(1)
        idx = rng.choice(np.where(fit)[0], min(600000, fit.sum()), replace=False)
        lr = LogisticRegression(max_iter=500).fit(Z[idx], y[idx], sample_weight=w[idx])
        return lr.predict_proba(Z[te])[:, 1]
    p_gold = logistisch(D["verdeckt"][:, 0])
    p_item = logistisch(D["X"][:, f.SP["diff_itemwert_team"]])
    pv = vhat[te]
    yt, wt, mt = y[te], w[te], minute[te]
    erg = {"runden": V.best_iteration, "sekunden": round(time.time() - t0), "n_train": int(fit.sum()), "n_pruef": int(te.sum())}
    for name, p in (("V", pv), ("Gold-Abstand allein", p_gold), ("Item-Abstand allein", p_item)):
        e = {"brier": brier(p, yt, wt), "logloss": logloss(p, yt, wt), "kal": kalibrierung(p, yt)[1], "je_minute": {}}
        for mn, a, b in MIN_BEREICHE:
            m = (mt >= a) & (mt < b)
            e["je_minute"][mn] = {"brier": brier(p[m], yt[m], wt[m]), "logloss": logloss(p[m], yt[m], wt[m]),
                                  "kal": kalibrierung(p[m], yt[m])[1], "n": int(m.sum())}
        erg[name] = e
    erg["kalibrierung_V"] = kalibrierung(pv, yt)[0]
    # je Pruefart
    au = M[te, f.MI["aufteilung"]]
    erg["V_je_pruefart"] = {f.AUFTEILUNGEN[k]: {"brier": brier(pv[au == k], yt[au == k]), "n": int((au == k).sum())}
                            for k in (1, 2, 3)}
    messung["V"] = erg
    return vhat


def trainiere_V_ohne(D, messung):
    """Risiko-Messung: die Live-API zeigt Gegner-Items/-Level nur 'wie zuletzt gesehen'. Was kostet V ohne sie?"""
    M, B, tr, te = D["meta"], D["B"], D["tr"], D["te"]
    raus = [BASIS_NAMEN.index(n) for n in GEGNER_SCOREBOARD if n in BASIS_NAMEN]   # seit 032 schon draussen
    B2 = B.copy()
    B2[:, raus] = np.nan
    y = M[:, f.MI["sieg"]].astype(np.float32)
    w = spiel_gewicht(M)
    va = valid_maske(M, tr)
    fit = tr & ~va
    V2 = trainiere(V_PARAMS, B2[fit], y[fit], w[fit], B2[va], y[va], w[va])
    V2.save_model(str(MODELLE / "V_ohne_gegnerwerte.txt"))
    p = V2.predict(B2[te], num_threads=FADEN)
    yt, wt = y[te], w[te]
    minute = D["X"][te, f.SP["minute"]]
    e = {"brier": brier(p, yt, wt), "logloss": logloss(p, yt, wt), "je_minute": {}}
    for mn, a, b in MIN_BEREICHE:
        m = (minute >= a) & (minute < b)
        e["je_minute"][mn] = {"brier": brier(p[m], yt[m], wt[m])}
    messung["V_ohne_gegnerwerte"] = e


# ---------------------------------------------------------------- Delta V (Ziel von Q)

def delta_v(D, vhat, sek=120) -> np.ndarray:
    """V desselben Spielers bei t+120 (zwischen seinen Momenten linear), minus V jetzt; Partie vorher zu Ende -> Sieg."""
    M = D["meta"]
    grp = M[:, f.MI["partie"]].astype(np.int64) * 16 + M[:, f.MI["pid"]]
    zeit = M[:, f.MI["zeit"]].astype(np.int64)
    key = grp * 100000 + zeit
    ordnung = np.argsort(key, kind="stable")
    ks, vs, gs, zs = key[ordnung], vhat[ordnung], grp[ordnung], zeit[ordnung]
    ziel = key + sek
    j = np.searchsorted(ks, ziel, side="left")
    j = np.clip(j, 1, len(ks) - 1)
    lo, hi = j - 1, j
    gleich_hi = gs[hi] == grp
    gleich_lo = gs[lo] == grp
    zt = zeit + sek
    w = np.where(gleich_hi & gleich_lo & (zs[hi] > zs[lo]), (zt - zs[lo]) / np.maximum(1, zs[hi] - zs[lo]), 1.0)
    v_hi = np.where(gleich_hi, vs[hi], np.nan)
    v_lo = np.where(gleich_lo, vs[lo], np.nan)
    v120 = np.where(gleich_hi & gleich_lo, v_lo + w * (v_hi - v_lo), np.where(gleich_lo, v_lo, v_hi))
    ende = zt >= M[:, f.MI["dauer"]] - 10
    v120 = np.where(ende, M[:, f.MI["sieg"]].astype(np.float32), v120)
    return (v120 - vhat).astype(np.float32)


# ---------------------------------------------------------------- pi

PI_PARAMS = dict(objective="multiclass", learning_rate=0.08, num_leaves=63, min_data_in_leaf=200,
                 feature_fraction=0.7, bagging_fraction=0.7, bagging_freq=1, lambda_l2=5.0)


def trainiere_pi(D, messung, keys_liste):
    M, B, tr, te = D["meta"], D["B"], D["tr"], D["te"]
    k = key_index(D["keys"], keys_liste)
    ok = k >= 0
    va = valid_maske(M, tr) & ok
    fit = tr & ~va & ok
    rng = np.random.default_rng(2)
    fit_i = rng.choice(np.where(fit)[0], min(900000, fit.sum()), replace=False)
    w = LIGA_GEWICHT[M[:, f.MI["liga"]]]
    t0 = time.time()
    pi = trainiere(dict(PI_PARAMS, num_class=len(keys_liste)), B[fit_i], k[fit_i], w[fit_i], B[va], k[va], w[va],
                   runden=400)
    pi.save_model(str(MODELLE / "pi.txt"))
    tm = te & ok
    P = pi.predict(B[tm], num_threads=FADEN)
    yt, wt = k[tm], w[tm]
    top = np.argsort(-P, 1)
    top1 = float(np.average(top[:, 0] == yt, weights=wt))
    top3 = float(np.average((top[:, :3] == yt[:, None]).any(1), weights=wt))
    # Vergleich: haeufigste Aktionen je Rolle und Minute (Training, gleiche Gewichte)
    rolle, minute = M[:, f.MI["rolle"]], np.minimum(M[:, f.MI["zeit"]] // 60, 45)
    zell = rolle * 64 + minute
    tab = np.zeros((5 * 64, len(keys_liste)))
    np.add.at(tab, (zell[fit], k[fit]), w[fit])
    rang = np.argsort(-tab, 1)
    b1 = float(np.average(rang[zell[tm], 0] == yt, weights=wt))
    b3 = float(np.average((rang[zell[tm], :3] == yt[:, None]).any(1), weights=wt))
    je_rolle = {}
    for r, rn in enumerate(f.ROLLEN):
        m = M[tm, f.MI["rolle"]] == r
        je_rolle[rn] = {"top1": float(np.average(top[m, 0] == yt[m], weights=wt[m])),
                        "top3": float(np.average((top[m, :3] == yt[m, None]).any(1), weights=wt[m])),
                        "basis_top1": float(np.average(rang[zell[tm][m], 0] == yt[m], weights=wt[m]))}
    messung["pi"] = {"klassen": len(keys_liste), "runden": pi.best_iteration, "sekunden": round(time.time() - t0),
                     "top1": top1, "top3": top3, "basis_top1": b1, "basis_top3": b3, "je_rolle": je_rolle,
                     "n_pruef": int(tm.sum())}
    # Neigung e(a|x) fuer alle Pruef-Momente (fuer die doppelt robuste Schaetzung)
    np.save(MODELLE / "pi_pruef.npy", P.astype(np.float32))
    np.save(MODELLE / "pi_pruef_idx.npy", np.where(tm)[0])


# ---------------------------------------------------------------- Q und Gefahr

Q_PARAMS = dict(objective="regression", learning_rate=0.05, num_leaves=127, min_data_in_leaf=400,
                feature_fraction=0.7, bagging_fraction=0.7, bagging_freq=1, lambda_l2=5.0)
G_PARAMS = dict(objective="binary", learning_rate=0.05, num_leaves=127, min_data_in_leaf=400,
                feature_fraction=0.7, bagging_fraction=0.7, bagging_freq=1, lambda_l2=5.0)


def mit_aktion(B, k):
    return np.hstack([B, k[:, None].astype(np.float32)])


def trainiere_Q(D, messung, keys_liste, dv):
    M, B, tr, te = D["meta"], D["B"], D["tr"], D["te"]
    k = key_index(D["keys"], keys_liste)
    ok = (k >= 0) & ~np.isnan(dv)
    va = valid_maske(M, tr) & ok
    fit = tr & ~va & ok
    cat = [B.shape[1]]
    w = spiel_gewicht(M)
    t0 = time.time()
    Q = trainiere(Q_PARAMS, mit_aktion(B[fit], k[fit]), dv[fit], w[fit], mit_aktion(B[va], k[va]), dv[va], w[va], cat=cat)
    Q.save_model(str(MODELLE / "Q.txt"))
    Q0 = trainiere(Q_PARAMS, B[fit], dv[fit], w[fit], B[va], dv[va], w[va])
    Q0.save_model(str(MODELLE / "Q0.txt"))
    tm = te & ok
    q = Q.predict(mit_aktion(B[tm], k[tm]), num_threads=FADEN)
    q0 = Q0.predict(B[tm], num_threads=FADEN)
    y, wt = dv[tm], w[tm]
    mse = lambda p: float(np.average((p - y) ** 2, weights=wt))
    var = float(np.average((y - np.average(y, weights=wt)) ** 2, weights=wt))
    messung["Q"] = {"runden": Q.best_iteration, "sekunden": round(time.time() - t0), "n_pruef": int(tm.sum()),
                    "mse_Q": mse(q), "mse_Q0_jede_Aktion_gleich": mse(q0), "mse_konstant": var,
                    "r2_Q": 1 - mse(q) / var, "r2_Q0": 1 - mse(q0) / var,
                    "delta_v_sd": float(np.sqrt(var))}


def trainiere_gefahr(D, messung, keys_liste):
    M, B, tr, te, F = D["meta"], D["B"], D["tr"], D["te"], D["folge"]
    k = key_index(D["keys"], keys_liste)
    lebt = D["X"][:, f.SP["tot"]] == 0
    erg = {}
    for dt in (30, 60):
        y = F[:, f.FI[f"tod_{dt}"]]
        ok = (k >= 0) & lebt & ~np.isnan(y)
        va = valid_maske(M, tr) & ok
        fit = tr & ~va & ok
        cat = [B.shape[1]]
        t0 = time.time()
        G = trainiere(G_PARAMS, mit_aktion(B[fit], k[fit]), y[fit], None, mit_aktion(B[va], k[va]), y[va], None, cat=cat)
        G.save_model(str(MODELLE / f"gefahr{dt}.txt"))
        tm = te & ok
        p = G.predict(mit_aktion(B[tm], k[tm]), num_threads=FADEN)
        yt = y[tm]
        # Vergleich: Minute + Ort allein (Rate je Minute und Bereich aus dem Training)
        minute = np.minimum(M[:, f.MI["zeit"]] // 60, 45)
        ber = np.clip(np.nan_to_num(D["X"][:, f.SP["bereich"]], nan=0), 0, 15).astype(int)
        zell = minute * 16 + ber
        s = np.bincount(zell[fit], y[fit], minlength=46 * 16)
        c = np.bincount(zell[fit], minlength=46 * 16)
        rate = (s + 1) / (c + 20)
        pb = rate[zell[tm]]
        erg[f"tod_{dt}"] = {"runden": G.best_iteration, "sekunden": round(time.time() - t0), "n_pruef": int(tm.sum()),
                            "rate": float(yt.mean()),
                            "Gefahr": {"logloss": logloss(p, yt), "brier": brier(p, yt), "kal": kalibrierung(p, yt)[1]},
                            "Minute+Ort": {"logloss": logloss(pb, yt), "brier": brier(pb, yt), "kal": kalibrierung(pb, yt)[1]},
                            "kalibrierung": kalibrierung(p, yt)[0]}
    messung["gefahr"] = erg


# ---------------------------------------------------------------- Jungler-Karte

J_PARAMS = dict(objective="multiclass", num_class=12, learning_rate=0.08, num_leaves=63, min_data_in_leaf=200,
                feature_fraction=0.7, bagging_fraction=0.7, bagging_freq=1, lambda_l2=5.0)


def trainiere_jungler(D, messung):
    M, B, tr, te = D["meta"], D["B"], D["tr"], D["te"]
    y = D["verdeckt"][:, 1].astype(int)
    ok = y >= 0
    va = valid_maske(M, tr) & ok
    fit = tr & ~va & ok
    rng = np.random.default_rng(3)
    fit_i = rng.choice(np.where(fit)[0], min(900000, fit.sum()), replace=False)
    t0 = time.time()
    J = trainiere(J_PARAMS, B[fit_i], y[fit_i], None, B[va], y[va], None, runden=400)
    J.save_model(str(MODELLE / "jungler.txt"))
    tm = te & ok
    P = J.predict(B[tm], num_threads=FADEN)
    yt = y[tm]
    ll = float(-np.mean(np.log(np.clip(P[np.arange(len(yt)), yt], 1e-9, 1))))
    minute = np.minimum(M[:, f.MI["zeit"]] // 60, 45)
    tab = np.ones((46, 12))
    np.add.at(tab, (minute[fit], y[fit]), 1)
    tab /= tab.sum(1, keepdims=True)
    pb = tab[minute[tm]]
    llb = float(-np.mean(np.log(pb[np.arange(len(yt)), yt])))
    # nur lebende Jungler (tot ist aus dem Scoreboard trivial)
    lebt = yt < 11
    ll_l = float(-np.mean(np.log(np.clip(P[lebt][np.arange(lebt.sum()), yt[lebt]], 1e-9, 1))))
    pbl = tab[minute[tm]][lebt]
    llb_l = float(-np.mean(np.log(pbl[np.arange(lebt.sum()), yt[lebt]])))
    top1 = float((P.argmax(1) == yt)[lebt].mean())
    top3 = float((np.argsort(-P, 1)[:, :3] == yt[:, None]).any(1)[lebt].mean())
    messung["jungler"] = {"runden": J.best_iteration, "sekunden": round(time.time() - t0), "n_pruef": int(tm.sum()),
                          "logloss": ll, "logloss_basis": llb, "logloss_lebend": ll_l, "logloss_lebend_basis": llb_l,
                          "top1_lebend": top1, "top3_lebend": top3,
                          "top1_lebend_basis": float((pbl.argmax(1) == yt[lebt]).mean())}


def main(welche):
    niedrige_prioritaet()
    MODELLE.mkdir(parents=True, exist_ok=True)
    messung = json.loads(MESSUNG.read_text(encoding="utf-8")) if MESSUNG.exists() else {}
    t0 = time.time()
    D = lade_alles()
    print(f"geladen {len(D['meta']):,} Momente in {time.time() - t0:.0f} s", flush=True)
    keys_liste = schluessel_liste(D["keys"], D["tr"])
    (MODELLE / "aktionen.json").write_text(json.dumps({"schluessel": keys_liste, "merkmale": BASIS_NAMEN},
                                                      ensure_ascii=False, indent=0), encoding="utf-8")
    messung["daten"] = {"momente": int(len(D["meta"])), "partien": int(len(np.unique(D["meta"][:, 0]))),
                        "training": int(D["tr"].sum()), "pruefung": int(D["te"].sum()), "aktionen": len(keys_liste)}
    if "V" in welche:
        trainiere_V(D, messung)
        print("V fertig", messung["V"]["V"]["brier"], flush=True)
    vhat = np.load(MODELLE / "vhat.npy")
    dv = delta_v(D, vhat)
    np.save(MODELLE / "delta_v.npy", dv)
    if "pi" in welche:
        trainiere_pi(D, messung, keys_liste)
        print("pi fertig", messung["pi"]["top1"], flush=True)
    if "Q" in welche:
        trainiere_Q(D, messung, keys_liste, dv)
        print("Q fertig", messung["Q"]["r2_Q"], flush=True)
    if "gefahr" in welche:
        trainiere_gefahr(D, messung, keys_liste)
        print("Gefahr fertig", flush=True)
    if "jungler" in welche:
        trainiere_jungler(D, messung)
        print("Jungler fertig", flush=True)
    if "V_ohne" in welche:
        trainiere_V_ohne(D, messung)
        print("V ohne Gegnerwerte fertig", messung["V_ohne_gegnerwerte"]["brier"], flush=True)
    MESSUNG.write_text(json.dumps(messung, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"fertig in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main(sys.argv[1:] or ["V", "pi", "Q", "gefahr", "jungler"])
