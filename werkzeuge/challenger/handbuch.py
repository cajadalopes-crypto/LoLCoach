"""Auftrag 031, Abschnitt 4: das Challenger-Handbuch aus den Daten.

    python werkzeuge/challenger/handbuch.py      -> buecher/challenger/handbuch.md (+ daten/challenger/modelle/handbuch.json)

Regeln: nur Aussagen mit n >= 200 und klarem Signal (|z| >= 3 bei Vergleichen, Unsicherheit ueber Partien), jede
mit Zahl, Fallzahl und Beispiel-Kommando. Was die Regel nicht besteht, steht NICHT drin (es wird unten gezaehlt).
Beschreibende Aussagen (was Gewinner tun) sind keine Ursache; kausal ist nur, was doppelt robust auf der Pruefung
geschaetzt ist (aus analyse.json) - das steht jeweils dabei.
"""
from __future__ import annotations

import json
from collections import defaultdict

import numpy as np

import grundlage as g
import modelle as mo
import phase1 as f
from analyse import partie_se

N_MIN = 200
Z_MIN = 3.0


class Buch:
    def __init__(self):
        self.abschnitte = defaultdict(list)
        self.verworfen = []

    def aussage(self, bereich, text, n, kommando, z=None, art="beschreibend"):
        if n < N_MIN or (z is not None and abs(z) < Z_MIN) or (isinstance(z, float) and np.isnan(z)):
            self.verworfen.append((bereich, text, n, z))
            return
        self.abschnitte[bereich].append({"text": text, "n": int(n), "kommando": kommando,
                                         "z": None if z is None else float(abs(z)), "art": art})


def tsd(n):
    return f"{int(n):,}".replace(",", ".")


def pct(x):
    return f"{100 * x:.0f} %"


def pp(x):
    return f"{100 * x:+.1f} Punkte"


def rate_vergleich(y, maske_a, maske_b, partie):
    ma, sa, na = partie_se(y[maske_a], partie[maske_a])
    mb, sb, nb = partie_se(y[maske_b], partie[maske_b])
    z = (ma - mb) / np.sqrt(sa ** 2 + sb ** 2) if sa and sb else np.nan
    return ma, mb, int(maske_a.sum()), int(maske_b.sum()), z


def main():
    mo.niedrige_prioritaet()
    D = f.lade(("X", "meta", "aktion", "folge", "verdeckt"))
    X, M, A, F, V = D["X"], D["meta"], D["aktion"], D["folge"], D["verdeckt"]
    sp = lambda n: X[:, f.SP[n]]
    partie = M[:, f.MI["partie"]]
    rolle = M[:, f.MI["rolle"]]
    minute = sp("minute")
    lebt = sp("tot") == 0
    sieg = M[:, f.MI["sieg"]].astype(float)
    tod60 = F[:, f.FI["tod_60"]]
    vhat = np.load(mo.MODELLE / "vhat.npy")
    an = json.loads((mo.MODELLE / "analyse.json").read_text(encoding="utf-8"))
    mess = json.loads((mo.MODELLE / "messung.json").read_text(encoding="utf-8"))
    B = Buch()

    # ---------------- A1 Gegner-Jungler
    alter = sp("geg1_gesehen_alter")
    gx, gy = sp("geg1_gesehen_x"), sp("geg1_gesehen_y")
    zone_gesehen = f.zone_np(f.bereich_np(gx, gy))
    wahr = V[:, 1].astype(int)
    zone_wahr = np.where(wahr >= 0, f.ZONE_VON_BEREICH[np.clip(wahr, 0, 10)], -1)
    lebt_j = (wahr >= 0) & (wahr < 11) & (sp("geg1_tot") == 0)
    for a, b in ((0, 15), (45, 60), (90, 120)):
        mk = lebt_j & (alter >= a) & (alter < b) & (zone_gesehen > 0)
        if mk.sum():
            treffer = (zone_wahr[mk] == zone_gesehen[mk]).mean()
            B.aussage("A1", f"Zuletzt vor {a}-{b} s gesehen: Der Gegner-Jungler ist noch auf derselben Kartenseite "
                            f"(oben/mid/unten) in {pct(treffer)} der Faelle.", mk.sum(),
                      "„Jungler vor 50 s unten gesehen – das ist alt, rechne oben mit ihm.“" if a >= 45 else
                      "„Jungler eben unten gesehen – oben hast du jetzt Luft.“")
    lm = mess.get("jungler", {})
    if lm:
        B.aussage("A1", f"Die Jungler-Karte trifft den Bereich des lebenden Gegner-Junglers mit ihren drei "
                        f"wahrscheinlichsten Bereichen in {pct(lm['top3_lebend'])} (Verteilung je Minute allein: Top-1 "
                        f"{pct(lm['top1_lebend_basis'])}, Modell Top-1 {pct(lm['top1_lebend'])}).", lm["n_pruef"],
                  "„Jungler wahrscheinlich im roten Jungle oben oder am Fluss – Ward dort, bevor du pushst.“",
                  art="Modell, Pruefung")
    laner_lane = lebt & (rolle != 1) & (sp("in_eigener_lane") == 1) & (minute < 14) & ~np.isnan(tod60)
    eigen_zone = sp("zone")
    weit_weg = laner_lane & (alter < 20) & (zone_gesehen > 0) & (zone_gesehen != eigen_zone) & (sp("geg1_tot") == 0)
    unbekannt = laner_lane & (np.isnan(alter) | (alter > 60)) & (sp("geg1_tot") == 0)
    ma, mb, na, nb, z = rate_vergleich(tod60, unbekannt, weit_weg, partie)
    B.aussage("A1", f"Lane-Phase: Ist der Gegner-Jungler seit ueber 60 s nicht gesehen, stirbt ein Laner in den "
                    f"naechsten 60 s in {pct(ma)} der Faelle; wurde er eben (< 20 s) auf der anderen Kartenseite "
                    f"gesehen, in {pct(mb)}."
                    + (" Eine Sichtung auf der anderen Seite macht die Lane also NICHT sicherer - gesehen wird er in "
                       "den Daten nur bei Kills, also dort, wo gekaempft wird (Carlos sieht ihn live oefter)."
                       if mb >= ma else ""), min(na, nb),
              "„Jungler seit einer Minute weg – nicht ueber die Mitte der Lane hinaus.“" if ma > mb else
              "„Jungler auf der anderen Seite gesehen heisst nicht sicher – Welle trotzdem nahe am Turm.“", z)

    # ---------------- A2 Gefahr
    unb = np.zeros(len(X))
    for i in range(5):
        ga = sp(f"geg{i}_gesehen_alter")
        unb += (sp(f"geg{i}_tot") == 0) & (np.isnan(ga) | (ga > 20))
    ber = sp("bereich")
    a0 = A[:, f.AI["a0"]]
    lage = lebt & (minute >= 25) & np.isin(ber, [2, 4]) & (sp("mit_nah") == 0) & (unb >= 3) & ~np.isnan(tod60)
    ma, mb, na, nb, z = rate_vergleich(tod60, lage & (a0 == 5), lage & (a0 != 5), partie)
    B.aussage("A2", f"Ab 25:00 allein in einer Seitenlane, drei oder mehr Gegner unbekannt: Wer dort 60 s allein "
                    f"weitersplittet, stirbt in {pct(ma)} der Faelle; wer die Seite verlaesst (zum Team, Back, Grube), "
                    f"in {pct(mb)}.", min(na, nb), "„Drei fehlen – raus aus der Seitenlane, zurueck zum Team.“", z)
    team = M[:, f.MI["team"]]
    gegn_jungle = np.where(team == 0, np.isin(ber, [9, 10]), np.isin(ber, [7, 8]))
    allein = lebt & gegn_jungle & (sp("mit_nah") == 0) & ~np.isnan(tod60)
    mit = lebt & gegn_jungle & (sp("mit_nah") >= 1) & ~np.isnan(tod60)
    ma, mb, na, nb, z = rate_vergleich(tod60, allein, mit, partie)
    B.aussage("A2", f"Allein im gegnerischen Jungle: Tod in 60 s in {pct(ma)}; mit mindestens einem Mitspieler: {pct(mb)}.",
              min(na, nb), "„Nicht allein in ihren Jungle – nimm den Support mit oder bleib auf unserer Seite.“", z)
    wenig = lebt & (sp("leben_anteil") < 0.3) & (sp("in_eigener_lane") == 1) & (minute < 14) & ~np.isnan(tod60) & (rolle != 1)
    ma, mb, na, nb, z = rate_vergleich(tod60, wenig & (a0 == 8), wenig & (a0 == 1), partie)
    B.aussage("A2", f"Lane-Phase mit unter 30 % Leben: Wer in der Lane bleibt, stirbt in 60 s in {pct(ma)} der Faelle; "
                    f"wer backt, in {pct(mb)}.", min(na, nb), "„30 % Leben – Welle unter den Turm, dann Back.“", z)

    # ---------------- A3 Lane
    lane_geg_tot = np.zeros(len(X), bool)
    for r in range(5):
        lane_geg_tot |= (rolle == r) & (sp(f"geg{r}_tot") == 1)
    pl = F[:, f.FI["platten_wir_60"]]
    phase = lebt & (rolle != 1) & (minute < 14) & (minute >= 5) & lane_geg_tot & ~np.isnan(pl)
    bleibt = phase & (A[:, f.AI["a0"]] == 8)
    back = phase & (A[:, f.AI["a0"]] == 1)
    ma, mb, na, nb, z = rate_vergleich(pl, bleibt, back, partie)
    B.aussage("A3", f"Lane-Gegner tot (5:00-14:00): Wer in der Lane bleibt, bekommt mit seinem Team in 60 s im Schnitt "
                    f"{ma:.2f} Platten; wer in der Zeit backt, {mb:.2f}.", min(na, nb),
              "„Er ist tot – Platte jetzt, backen danach.“", z)
    zehn = (M[:, f.MI["zeit"]] == 600) & (rolle != 1) & (rolle != 4)
    cs = sp("diff_cs_lane")
    for lo, hi, txt in ((20, 999, "20+ CS vorn"), (-999, -20, "20+ CS hinten")):
        mk = zehn & (cs >= lo) & (cs < hi)
        ma, se, np_ = partie_se(sieg[mk], partie[mk])
        B.aussage("A3", f"Bei 10:00 {txt} gegen den Lane-Gegner: Siegquote {pct(ma)} (Laner ohne Support).", mk.sum(),
                  "„20 CS vorn – dein Vorsprung ist echt, jetzt nicht verschenken.“" if lo > 0 else
                  "„20 CS hinten – umspielen statt duellieren: Welle unter deinem Turm halten.“",
                  (ma - 0.5) / se if se else None)

    # ---------------- A4 Back
    backm = (M[:, f.MI["anlass"]] == 4)
    gleich_vorher = np.r_[False, (partie[1:] == partie[:-1]) & (M[1:, f.MI["pid"]] == M[:-1, f.MI["pid"]])]
    item = sp("itemwert")
    gekauft = np.where(gleich_vorher, item - np.r_[item[0], item[:-1]], np.nan)
    gold_b = sp("gold_tasche") + np.clip(gekauft, 0, None)          # Gold beim Betreten des Ladens
    backm &= gleich_vorher
    for r, rn in enumerate(f.ROLLEN):
        mk = backm & (rolle == r) & (minute >= 5) & (minute < 20)
        if mk.sum() >= N_MIN:
            B.aussage("A4", f"{g.ROLLE_DE[rn]}: Median-Gold beim Betreten des Ladens (5:00-20:00, Tasche + gerade "
                            f"gekaufte Items) {np.median(gold_b[mk]):.0f} "
                            f"(Mitte der Haelfte: {np.percentile(gold_b[mk], 25):.0f}-{np.percentile(gold_b[mk], 75):.0f}).",
                      mk.sum(), f"„{np.median(gold_b[mk]) // 50 * 50:.0f} Gold – das ist dein Back-Moment.“")
    vo = an["ketten"]["vor_objective"]
    for mon in ("Drache", "Baron"):
        for rn in f.ROLLEN:
            ge, ve = vo.get(f"{mon}|genommen|{rn}"), vo.get(f"{mon}|verloren|{rn}")
            if not ge or not ve:
                continue
            p1, p2 = ge["an der Grube"] / ge["n"], ve["an der Grube"] / ve["n"]
            se = np.sqrt(p1 * (1 - p1) / ge["n"] + p2 * (1 - p2) / ve["n"])
            B.aussage("A6", f"{mon}, {g.ROLLE_DE[rn]}: In den 120 s vor dem Monster steht das Team, das es nimmt, in "
                            f"{pct(p1)} der Momente an der Grube; das Team, das es verliert, in {pct(p2)}.",
                      min(ge["n"], ve["n"]), f"„{mon} in einer Minute – jetzt hin, nicht erst beim Spawn.“",
                      (p1 - p2) / se if se else None)
            b1, b2 = ge["Tot"] / ge["n"], ve["Tot"] / ve["n"]
            se = np.sqrt(b1 * (1 - b1) / ge["n"] + b2 * (1 - b2) / ve["n"])
            B.aussage("A4", f"{mon}, {g.ROLLE_DE[rn]}: In den 120 s davor ist der Spieler des verlierenden Teams in "
                            f"{pct(b2)} der Momente tot, beim nehmenden in {pct(b1)}.", min(ge["n"], ve["n"]),
                      f"„{mon} kommt – jetzt nichts riskieren, erst Back, dann zur Grube.“", (b2 - b1) / se if se else None)

    # ---------------- A5 TP
    tp = A[:, f.AI["tp"]]
    B.aussage("A5", f"TP ist aus den Minuten-Positionen nur selten zeitlich erkennbar: {int((tp == 1).sum())} sichere "
                    f"TP-Momente gegen {int((tp == -1).sum())} Momente 'TP unbekannt'. Der TP-Wert kommt deshalb in "
                    f"Stufe 3 aus dem Rechner, nicht aus diesen Daten.", int((tp == 1).sum()),
              "„(kein TP-Kommando aus den Daten – Stufe 3)“")

    # ---------------- A6 Objectives: Wert in Siegchance-Punkten
    obj = np.concatenate([np.load(t)["obj"] for t in sorted(f.ZIEL.glob("teil_*.npz"))])
    zeit = M[:, f.MI["zeit"]]
    grenzen = np.searchsorted(partie, np.arange(partie.max() + 2))
    wert = defaultdict(list)
    wpart = defaultdict(list)
    for p_nr, t_o, art, t_team, zst, *_ in obj:
        if t_team < 0 or art == 4:
            continue
        lo, hi = grenzen[p_nr], grenzen[p_nr + 1]
        sel = np.arange(lo, hi)
        sel = sel[team[sel] == t_team]
        vor = sel[(zeit[sel] >= t_o - 40) & (zeit[sel] < t_o)]
        nach = sel[(zeit[sel] > t_o) & (zeit[sel] <= t_o + 40)]
        if len(vor) and len(nach):
            stufe = "vor 20:00" if t_o < 1200 else ("20-30" if t_o < 1800 else "ab 30:00")
            wert[(f.MONSTER[art], stufe)].append(vhat[nach].mean() - vhat[vor].mean())
            wpart[(f.MONSTER[art], stufe)].append(p_nr)
    for (mon, stufe), v in sorted(wert.items()):
        v = np.array(v)
        se = v.std() / np.sqrt(len(v))
        B.aussage("A11", f"{mon} ({stufe}): die Siegchance des nehmenden Teams steigt um {pp(v.mean())} "
                         f"(Siegchance-Modell, 40 s vorher gegen 40 s nachher).", len(v),
                  f"„{mon} ist {100 * v.mean():.0f} Punkte Siegchance wert – dafuer lohnt ein Kampf.“" if v.mean() >= 0.03 else
                  (f"„{mon} bringt nur {100 * v.mean():.1f} Punkte – nehmen, wenn es ohne grosses Risiko geht.“" if v.mean() >= 0.01
                   else f"„{mon} ist wenig wert ({100 * v.mean():.1f} Punkte) – dafuer nichts riskieren, der Turm danach zaehlt.“"),
                  v.mean() / se if se else None, art="Modell V")
    zust = defaultdict(lambda: np.zeros(3))
    for row in obj:
        zust[f.MONSTER[row[2]]][row[4]] += 1
    for mon, c in zust.items():
        if mon in ("Drache", "Baron"):
            B.aussage("A6", f"{mon}: frei genommen {pct(c[0] / c.sum())}, bestritten ohne Kill {pct(c[1] / c.sum())}, "
                            f"umkaempft (Kill +-30 s) {pct(c[2] / c.sum())}.", int(c.sum()),
                      f"„{mon}: rechne in jedem zweiten bis dritten Fall mit Kampf – vorher Leben und Ult pruefen.“")

    # ---------------- A7 Tausch
    tausch_g, tausch_n = [], []
    for p_nr, t_o, art, t_team, zst, *_ in obj:
        if art != 1 or t_team < 0 or zst != 0:
            continue
        lo, hi = grenzen[p_nr], grenzen[p_nr + 1]
        sel = np.arange(lo, hi)
        sel = sel[(team[sel] != t_team) & (zeit[sel] >= t_o - 60) & (zeit[sel] < t_o - 30)]
        if not len(sel):
            continue
        i = sel[0]
        gb = F[i, f.FI["gebaeude_wir_60"]] + F[i, f.FI["platten_wir_60"]] / 2
        dv = F[i, f.FI["teamgold_60"]]
        if np.isnan(gb):
            continue
        (tausch_g if gb >= 1 else tausch_n).append(dv)
    if tausch_g and tausch_n:
        a_, b_ = np.array(tausch_g), np.array(tausch_n)
        z = (a_.mean() - b_.mean()) / np.sqrt(a_.var() / len(a_) + b_.var() / len(b_))
        B.aussage("A7", f"Gegner nimmt einen Drachen frei: Holt das andere Team in dieser Minute mindestens einen Turm "
                        f"(oder zwei Platten), aendert sich sein Gold-Abstand um {a_.mean():+.0f}; ohne Tausch um {b_.mean():+.0f}.",
                  min(len(a_), len(b_)), "„Drache ist weg – dafuer jetzt Turm oben, nicht hinterherlaufen.“", z)

    # ---------------- A8 Kaempfe: Umwandeln (doppelt robust, Pruefung)
    nk = an["ketten"]["nach_gewonnenem_kampf"]
    akt = sorted(((k, v) for k, v in nk["aktionen"].items() if v["dr_se"]), key=lambda kv: -kv[1]["dr_wert"])
    if akt:
        beste, schlechteste = akt[0], akt[-1]
        z = (beste[1]["dr_wert"] - schlechteste[1]["dr_wert"]) / np.hypot(beste[1]["dr_se"], schlechteste[1]["dr_se"])
        B.aussage("A8", f"Nach einem gewonnenen Kampf (mind. 2 Gegner mehr tot): {beste[0]} bringt {pp(beste[1]['dr_wert'])} "
                        f"Siegchance in 120 s (getan in {pct(beste[1]['anteil_getan'])}); {schlechteste[0]} nur "
                        f"{pp(schlechteste[1]['dr_wert'])} (doppelt robust, Pruefung).", nk["n"],
                  f"„Kampf gewonnen – {beste[0].replace('Objective:', '')} jetzt, nicht zurueck in die Lane.“", z,
                  art="kausal geschaetzt (DR)")
        B.aussage("A8", f"Nach gewonnenen Kaempfen holt das Team in den 60 s danach im Schnitt {nk['folge_60']['gebaeude_wir']:.2f} "
                        f"Gebaeude, {nk['folge_60']['platten_wir']:.2f} Platten und {nk['folge_60']['obj_wir']:.2f} Monster.",
                  nk["n"], "„Zwei tot bei ihnen – Turm oder Monster, sofort.“")
    kills30 = F[:, f.FI["kills_wir_30"]] - F[:, f.FI["kills_gegner_30"]]
    km = (M[:, f.MI["anlass"]] == 1) & ~np.isnan(kills30)
    vorn = km & (sp("tote_gegner") - sp("tote_wir") >= 2)
    gleich = km & (sp("tote_gegner") == sp("tote_wir"))
    ma, mb, na, nb, z = rate_vergleich(kills30, vorn, gleich, partie)
    B.aussage("A8", f"Wer nach einem Kill zwei Gegner mehr tot hat, gewinnt die naechsten 30 s mit {ma:+.2f} Kills; bei "
                    f"Gleichstand {mb:+.2f}.", min(na, nb), "„Zwei mehr – jetzt ist der Moment, weiterzuspielen.“", z)

    # ---------------- A9, A12, A13: Partie-Kennzahlen (Gewinner gegen Verlierer derselben Rolle, gepaart)
    gueltig = json.loads((f.ZIEL / "partien.json").read_text(encoding="utf-8"))
    felder = {"A9": [("wardsPlaced", "Wards gesetzt"), ("detectorWardsPlaced", "Kontroll-Augen gesetzt"),
                     ("wardsKilled", "Wards zerstoert"), ("visionScore", "Sichtwert")],
              "A12": [("enemyMissingPings", "'Gegner fehlt'-Pings"), ("onMyWayPings", "'Auf dem Weg'-Pings"),
                      ("needVisionPings", "'Sicht noetig'-Pings"), ("dangerPings", "'Gefahr'-Pings")],
              "A13": [("visionWardsBoughtInGame", "gekaufte Kontroll-Augen")]}
    paare = defaultdict(list)
    rng = np.random.default_rng(5)
    for mid in rng.choice(gueltig, min(2500, len(gueltig)), replace=False):
        k = g.lade(mid)
        if k["dauer"] < 20 * 60:
            continue
        dauer = k["dauer"] / 60
        by = {(s["teamPosition"], bool(s["win"])): s for s in k["sp"]}
        for rn in f.ROLLEN:
            w, l = by.get((rn, True)), by.get((rn, False))
            if w and l:
                for ber_, liste in felder.items():
                    for fe, _ in liste:
                        paare[(ber_, fe, rn)].append(((w.get(fe) or 0) / dauer * 30, (l.get(fe) or 0) / dauer * 30))
    for ber_, liste in felder.items():
        for fe, name in liste:
            for rn in f.ROLLEN:
                v = np.array(paare[(ber_, fe, rn)])
                if not len(v):
                    continue
                d = v[:, 0] - v[:, 1]
                z = d.mean() / (d.std() / np.sqrt(len(d))) if d.std() else None
                B.aussage(ber_, f"{g.ROLLE_DE[rn]}: {name} je 30 min – Gewinner {v[:, 0].mean():.1f}, Verlierer "
                                f"{v[:, 1].mean():.1f} (gepaart je Partie; beschreibend, nicht Ursache).", len(d),
                          {"A9": "„Ward jetzt, bevor du weiter vorgehst.“", "A12": "„Ping Bot: Jungler fehlt.“",
                           "A13": "„Kontroll-Auge mitnehmen.“"}[ber_], z)

    # ---------------- A10 Seiten, Split, Gruppe; A11 Spielstand
    bestes = {}
    for p in an["plausibel"]:
        if p.get("art") == "aus den Daten" and p.get("partien", 0) >= N_MIN and p.get("dr_se"):
            k = (p["a"], p["b"])
            if k not in bestes or p["dr"] / p["dr_se"] > bestes[k]["dr"] / bestes[k]["dr_se"]:
                bestes[k] = p
    for p in bestes.values():
        if True:
            text = p["name"].replace(" (Daten, doppelt robust)", "")
            B.aussage("Q", f"{text}: {pp(p['dr'])} Siegchance in 120 s (doppelt robust, Pruefung, "
                             f"{p['partien']} Partien).", p["n"], f"„{p['a'].replace('Objective:', '')} statt "
                                                                 f"{p['b'].replace('Objective:', '')}.“",
                      p["dr"] / p["dr_se"], art="kausal geschaetzt (DR)")
    zwanzig = M[:, f.MI["zeit"]] == 1200                # Anlass dort meist "Spawn" (Baron 20:00)
    diff = sp("diff_itemwert_team")
    for lo, hi, txt in ((3000, 1e9, "3000+ Item-Gold vorn"), (-1e9, -3000, "3000+ Item-Gold hinten")):
        mk = zwanzig & (diff >= lo) & (diff < hi)
        ma, se, np_ = partie_se(sieg[mk], partie[mk])
        B.aussage("A11", f"Bei 20:00 {txt}: Siegquote {pct(ma)}.", mk.sum(),
                  "„Wir sind vorn – nichts erzwingen, Sicht und Objectives.“" if lo > 0 else
                  "„Wir liegen hinten – auf Picks und Gegner-Fehler spielen, keine 50:50-Kaempfe.“",
                  (ma - 0.5) / se if se else None)
    vm = mess.get("V", {})
    if vm:
        B.aussage("A11", f"Das Siegchance-Modell (nur Wissbares) liegt im Brier bei {vm['V']['brier']:.3f}; der echte "
                         f"Gold-Abstand allein (im Spiel unsichtbar) bei {vm['Gold-Abstand allein']['brier']:.3f}.",
                  vm["n_pruef"], "„Siegchance jetzt 62 % – ihr seid vorn, aber nicht sicher.“", art="Modell, Pruefung")

    # ---------------- schreiben
    titel = {"A1": "Gegner-Jungler lesen", "A2": "Gefahr ausserhalb des Bildes", "A3": "Lane-Druck und Lane-Gegner",
             "A4": "Zurueck in die Basis", "A5": "TP", "A6": "Objectives", "A7": "Cross-Map und Tausch",
             "A8": "Kaempfe als Makro-Entscheidung", "A9": "Sicht", "A10": "Seiten, Gruppe, Split",
             "A11": "Spielstand und Siegbedingung", "A12": "Team und Kommunikation", "A13": "Kaufen (Makro-Teil)",
             "Q": "Aus dem Aktionswert (doppelt robust, je Aktionspaar der staerkste Fund)"}
    z = ["# Challenger-Handbuch (aus den Daten, Auftrag 031)", "",
         f"Grundlage: {len(np.unique(partie))} High-Elo-Partien (EUW, Master bis Challenger, 16.17-16.19), "
         f"{tsd(len(M))} Entscheidungsmomente. Nur Aussagen mit n >= {N_MIN} und klarem Signal (|z| >= {Z_MIN:.0f}). "
         "**Beschreibend** = was in den Partien passiert (keine Ursache); **kausal geschaetzt** = doppelt robust auf "
         "zurueckgelegten Partien; **Modell** = Messung eines Modells auf der Pruefung.", ""]
    for k in titel:
        z.append(f"## {k}. {titel[k]}")
        z.append("")
        eintraege = B.abschnitte.get(k, [])
        if not eintraege:
            z.append("_Keine Aussage mit n >= 200 und klarem Signal._")
        for e in eintraege:
            zz = f", |z| {e['z']:.0f}" if e["z"] else ""
            z.append(f"- {e['text']} _(n = {tsd(e['n'])}{zz}; {e['art']})_  ")
            z.append(f"  Kommando: {e['kommando']}")
        z.append("")
    z += [f"_Verworfen (n < {N_MIN} oder kein klares Signal): {len(B.verworfen)} Aussagen._"]
    (g.BUCH / "handbuch.md").write_text("\n".join(z) + "\n", encoding="utf-8")
    (mo.MODELLE / "handbuch.json").write_text(json.dumps({"abschnitte": B.abschnitte, "verworfen": B.verworfen},
                                                         ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(f"{sum(len(v) for v in B.abschnitte.values())} Aussagen, {len(B.verworfen)} verworfen")


if __name__ == "__main__":
    main()
