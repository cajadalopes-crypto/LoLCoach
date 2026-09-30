"""Challenger-Gehirn - Schnittstelle fuer Stufe 4 (Auftrag 031).

    from gehirn import Gehirn
    hirn = Gehirn()
    for aktion, ziel, wert, p_highelo, gefahr, klarheit, grund in hirn.bewerte(lage):
        ...

`lage`: dict Merkmal -> Wert (Namen wie `Gehirn().merkmale`, s. buecher/challenger/merkmale.md + rolle, seite,
anlass) oder ein fertiger Vektor in dieser Reihenfolge. Fehlende Merkmale = NaN (LightGBM kommt damit zurecht,
die Aussage wird aber unsicherer - welche live fehlen: buecher/challenger/live_merkmale.md).

Rueckgabe: Liste, beste zuerst, nur Aktionen, die High-Elo-Spieler in so einer Lage ueberhaupt waehlen (pi >= 2 %):
    aktion      "Back", "Objective", "Rotation", "Lane", ... (phase1.AKTIONEN)
    ziel        "Drache", "oben", "Botlane", ... oder "" (Objective: Monster, Rotation: Zone, Unterwegs: Ort)
    wert        Siegchance-Aenderung in 120 s (Prozentpunkte), Modell Q
    p_highelo   wie oft High-Elo-Spieler (gewichtet Challenger 3, GM 2, Master 1) hier genau das tun, Modell pi
    gefahr      Todeswahrscheinlichkeit in 60 s bei dieser Aktion, Modell gefahr60
    klarheit    "klar" / "geteilt" / "unklar" (fuer die ganze Lage gleich; Schwellen aus klarheit.json)
    grund       Stichworte (nur bei der besten Aktion): die Kernmerkmale, die ihren Vorsprung vor der zweitbesten tragen
Dazu `hirn.lage_info(lage)`: Siegchance jetzt, Jungler-Karte (Bereich -> Wahrscheinlichkeit), fehlende Info.

Laufzeit: unter 20 ms je Aufruf auf der CPU (gemessen in `messen()`), ein Faden.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np

HIER = Path(__file__).resolve().parent
MODELLE = HIER.parents[1] / "daten" / "challenger" / "modelle"

AKTIONEN = ["Tot", "Back", "Objective", "TP", "Rotation", "Split", "Gruppe", "Jungle", "Lane", "Warten", "Unterwegs"]
BEREICHE = ["Basis Blau", "Basis Rot", "Toplane", "Midlane", "Botlane", "Fluss oben", "Fluss unten",
            "blauer Jungle oben", "blauer Jungle unten", "roter Jungle oben", "roter Jungle unten", "tot"]
P_MIN = 0.02
# lesbare Kernmerkmale fuer die Gruende
KERN = ["leben_anteil", "gold_tasche", "minute", "tote_gegner", "tote_wir", "mit_nah", "abst_brunnen", "drache_bis",
        "baron_da", "diff_itemwert_team", "diff_level_lane", "lg_nahe_sichtbar", "geg1_gesehen_alter", "inhibs_offen_wir",
        "baron_buff_wir", "seit_back"]

# kurze Stichworte fuer die Gruende (Merkmal -> Wort); Rest: der Merkmalsname
STICHWORT = {
    "leben_anteil": "Leben", "gold_tasche": "Gold in der Tasche", "itemwert": "Items", "level": "Level",
    "minute": "Spielzeit", "tot": "tot", "respawn_rest": "Respawn", "seit_back": "Zeit seit Back",
    "abst_brunnen": "Weg zur Basis", "abst_eigener_turm": "Abstand eigener Turm", "abst_gegner_turm": "Abstand Gegnerturm",
    "abst_drache": "Abstand Drache", "abst_baron": "Abstand Baron", "mit_nah": "Mitspieler nah",
    "mit_lebend": "Mitspieler am Leben", "mit_abstand": "Abstand zum Team", "tote_wir": "eigene Tote",
    "tote_gegner": "Gegner tot", "drache_da": "Drache steht", "drache_bis": "Drache spawnt", "baron_da": "Baron steht",
    "baron_bis": "Baron spawnt", "herold_da": "Herold steht", "larven_da": "Larven stehen", "larven_bis": "Larven spawnen",
    "herold_bis": "Herold spawnt", "drachen_wir": "unsere Drachen", "drachen_gegner": "Gegner-Drachen",
    "seele_wir": "unsere Seele", "seele_gegner": "Gegner-Seele", "baron_buff_wir": "unser Baron-Buff",
    "baron_buff_gegner": "Gegner-Baron-Buff", "inhibs_offen_wir": "Gegner-Inhib offen",
    "inhibs_offen_gegner": "unser Inhib offen", "diff_itemwert_team": "Item-Vorsprung Team",
    "diff_level_team": "Level-Vorsprung Team", "diff_itemwert_lane": "Item-Vorsprung Lane",
    "diff_level_lane": "Level-Vorsprung Lane", "diff_cs_lane": "CS-Vorsprung Lane", "lg_nahe_sichtbar": "Lane-Gegner sichtbar",
    "in_eigener_lane": "in deiner Lane", "bereich": "Ort", "zone": "Kartenseite", "geg1_gesehen_alter": "Jungler unbekannt seit",
    "geg1_tot": "Gegner-Jungler tot", "tuerme_wir": "unsere Tuerme", "tuerme_gegner": "Gegner-Tuerme",
    "platten_wir": "unsere Platten", "anlass": "Anlass", "rolle": "Rolle",
}


class Gehirn:
    def __init__(self, ordner: Path = MODELLE):
        meta = json.loads((ordner / "aktionen.json").read_text(encoding="utf-8"))
        self.schluessel: list[str] = meta["schluessel"]
        self.merkmale: list[str] = meta["merkmale"]
        self.idx = {n: i for i, n in enumerate(self.merkmale)}
        lade = lambda n: lgb.Booster(model_file=str(ordner / f"{n}.txt"))
        self.V, self.pi, self.Q = lade("V"), lade("pi"), lade("Q")
        self.G60, self.J = lade("gefahr60"), lade("jungler")
        k = ordner / "klarheit.json"
        self.schwellen = json.loads(k.read_text(encoding="utf-8")) if k.exists() else \
            {"delta": 0.01, "p_klar": 0.15, "p_geteilt": 0.08}
        self._K = np.arange(len(self.schluessel), dtype=np.float64)
        neutral = json.loads((ordner / "neutral.json").read_text(encoding="utf-8"))
        self.neutral = np.array([neutral.get(n, np.nan) for n in self.merkmale])
        self.kern = [self.idx[n] for n in KERN if n in self.idx]

    # ---- Eingabe
    def vektor(self, lage) -> np.ndarray:
        if isinstance(lage, dict):
            v = np.full(len(self.merkmale), np.nan)
            for n, w in lage.items():
                if n in self.idx and w is not None:
                    v[self.idx[n]] = float(w)
            return v
        return np.asarray(lage, dtype=np.float64).reshape(-1)

    def _mit_aktion(self, v: np.ndarray) -> np.ndarray:
        n = len(self.schluessel)
        return np.hstack([np.repeat(v[None, :], n, 0), self._K[:, None]])

    # ---- Kern
    def werte(self, v: np.ndarray):
        """Q, pi, Gefahr fuer alle Aktionen einer Lage (je ein Vektor ueber self.schluessel)."""
        Z = self._mit_aktion(v)
        q = self.Q.predict(Z, num_threads=1)
        g = self.G60.predict(Z, num_threads=1)
        p = self.pi.predict(v[None, :], num_threads=1)[0]
        return q, p, g

    def klarheit(self, q, p) -> tuple[str, int, int]:
        """(Stufe, beste, zweitbeste) - nur unter Aktionen mit pi >= P_MIN."""
        kand = np.where(p >= P_MIN)[0]
        if len(kand) == 0:
            kand = np.argsort(-p)[:3]
        ord_ = kand[np.argsort(-q[kand])]
        b = int(ord_[0])
        z = int(ord_[1]) if len(ord_) > 1 else b
        s = self.schwellen
        if q[b] - q[z] >= s["delta"] and p[b] >= s["p_klar"]:
            return "klar", b, z
        if p[b] >= s["p_geteilt"] and p[z] >= s["p_geteilt"]:
            return "geteilt", b, z
        return "unklar", b, z

    def grund(self, v, a: int, b: int, n: int = 3) -> list[str]:
        """Stichworte: welche Kernmerkmale tragen den Vorsprung von a vor b? Jedes Kernmerkmal wird einzeln auf seinen
        Median (Training) gesetzt; je mehr der Vorsprung Q(a) - Q(b) dabei schrumpft, desto mehr traegt es ihn.
        Ein Aufruf mit 2 x (16 + 1) Zeilen (~1 ms; die exakten LightGBM-Beitraege kosteten 40 ms)."""
        kern = [j for j in self.kern if not np.isnan(v[j])]
        V_ = np.repeat(v[None, :], len(kern) + 1, 0)
        for r, j in enumerate(kern, 1):
            V_[r, j] = self.neutral[j]
        Z = np.vstack([np.hstack([V_, np.full((len(V_), 1), float(a))]), np.hstack([V_, np.full((len(V_), 1), float(b))])])
        q = self.Q.predict(Z, num_threads=1)
        gap = q[: len(V_)] - q[len(V_):]
        beitrag = gap[0] - gap[1:]
        top = np.argsort(-beitrag)[:n]
        out = []
        for r in top:
            if beitrag[r] <= 0:
                continue
            j = kern[r]
            hoch = v[j] > self.neutral[j]
            out.append(f"{STICHWORT.get(self.merkmale[j], self.merkmale[j])} {'hoch' if hoch else 'niedrig'}")
        return out

    def bewerte(self, lage, mit_grund: bool = True):
        v = self.vektor(lage)
        q, p, g = self.werte(v)
        stufe, b, z = self.klarheit(q, p)
        kand = np.where(p >= P_MIN)[0]
        if len(kand) == 0:
            kand = np.argsort(-p)[:3]
        kand = kand[np.argsort(-q[kand])]
        out = []
        for i in kand:
            akt, _, ziel = self.schluessel[i].partition(":")
            gr = self.grund(v, int(i), z if i == b else b) if mit_grund and i == b else []
            out.append((akt, ziel, round(float(q[i]) * 100, 2), round(float(p[i]), 3), round(float(g[i]), 3), stufe, gr))
        return out

    def lage_info(self, lage) -> dict:
        v = self.vektor(lage)
        sieg = float(self.V.predict(v[None, :], num_threads=1)[0])
        pj = self.J.predict(v[None, :], num_threads=1)[0]
        ent = float(-(pj * np.log(np.clip(pj, 1e-9, 1))).sum() / np.log(len(pj)))
        fehlt = []
        alter = v[self.idx["geg1_gesehen_alter"]]
        if ent > 0.7:
            fehlt.append(f"Gegner-Jungler: Ort unklar (zuletzt {'nie' if np.isnan(alter) else f'vor {alter:.0f} s'} gesehen)")
        if v[self.idx["hat_tp"]] == 1:
            fehlt.append("TP-Abklingzeit (nicht im Modell)")
        return {"siegchance": sieg, "jungler": {BEREICHE[i]: round(float(x), 3) for i, x in enumerate(pj) if x >= 0.05},
                "jungler_unsicherheit": ent, "fehlt": fehlt}


def neutral_berechnen() -> None:
    """Median jedes Merkmals im Training -> neutral.json (fuer die Gruende)."""
    import phase1 as f
    import modelle as mo
    D = f.lade(("X", "meta"))
    B = mo.basis(D)
    tr = D["meta"][:, f.MI["aufteilung"]] == 0
    rng = np.random.default_rng(6)
    idx = rng.choice(np.where(tr)[0], 300000, replace=False)
    med = np.nanmedian(B[idx], 0)
    (MODELLE / "neutral.json").write_text(json.dumps({n: float(x) for n, x in zip(mo.BASIS_NAMEN, med)}), encoding="utf-8")


def messen(n: int = 200) -> dict:
    """Laufzeit je bewerte()-Aufruf an echten Pruef-Lagen (ein Faden)."""
    import phase1 as f
    import modelle as mo
    hirn = Gehirn()
    D = f.lade(("X", "meta"))
    B = mo.basis(D)
    te = np.where(D["meta"][:, f.MI["aufteilung"]] > 0)[0]
    rng = np.random.default_rng(4)
    zeiten = []
    for i in rng.choice(te, n, replace=False):
        t = time.perf_counter()
        hirn.bewerte(B[i])
        zeiten.append((time.perf_counter() - t) * 1000)
    z = np.array(zeiten[5:])
    return {"median_ms": float(np.median(z)), "p95_ms": float(np.percentile(z, 95)), "max_ms": float(z.max()), "n": len(z)}


if __name__ == "__main__":
    if not (MODELLE / "neutral.json").exists():
        neutral_berechnen()
    print(messen())
