"""Makro-Rechner (Buch 17, Teil B "Re"; Auftrag 032, Abschnitt 1). Reine Funktionen, jede getestet (tests/makro/).

Vorhandenes wird benutzt, nicht nachgebaut: Karte/Wege aus lolcoach/bewertung.py (abstand, WEGFAKTOR, BRUNNEN,
TUERME, todeszeit), Wellen-Takt und Brunnen->Lane aus lolcoach/kern/uhren.py. Patch-Werte nur aus wissen/ (mechanik,
wellen, objektive, makro/patchwerte) - nie im Code.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..bewertung import BRUNNEN, WEGFAKTOR, abstand, todeszeit
from ..kern import uhren
from . import regeln

# ---------------------------------------------------------------- Wege


def tempo_standard() -> float:
    return float(uhren._toml("wege.toml").get("tempo_median", 365.0))


def ankunft(von, nach, tempo: float | None = None) -> float:
    """Laufzeit in s von A nach B: Luftlinie x WEGFAKTOR (Waende) / Lauftempo (gemessen 365, wissen/wege.toml)."""
    return abstand(von, nach) * WEGFAKTOR / (tempo or tempo_standard())


def ankunft_ab_brunnen(team: str, nach, tempo: float | None = None, respawn: float = 0.0) -> float:
    """Respawn (oder 0) + Weg vom eigenen Brunnen."""
    return max(0.0, respawn) + ankunft(BRUNNEN[team], nach, tempo)


def brunnen_lane(lane: str, team: str, tempo: float | None = None) -> float:
    """Brunnen -> eigener Aussenturm dieser Lane (kern/uhren.brunnen_lane)."""
    return uhren.brunnen_lane(lane, team, tempo) or 35.0


def todes_kosten(level: int, zeit: float) -> float:
    """So lange waerst du jetzt tot (bewertung.todeszeit, wissen/mechanik.toml)."""
    return todeszeit(level, zeit)


# ---------------------------------------------------------------- Wellen


def wellenwert(zeit: float) -> tuple[float, float]:
    """(Gold, XP) einer Welle um diese Zeit: 3 Nahkampf + 3 Fernkampf + Kanone anteilig (wissen/mechanik.toml,
    Kanonen-Takt aus wissen/wellen.toml)."""
    from .. import wissen
    m = wissen.lade("mechanik")
    gold, xp = m["gold"], m["xp"]
    kanone_jede = next(k for ab, k in reversed(uhren._toml("wellen.toml")["kanone_jede"]) if zeit >= ab)
    stufen = int(zeit // 90)
    kanonengold = min(gold["vasall_kanone"] + gold.get("vasall_kanone_pro_stufe", 0) * stufen, gold.get("vasall_kanone_max", 999))
    g = 3 * gold["vasall_nah"] + 3 * gold["vasall_fern"] + kanonengold / kanone_jede
    x = 3 * xp["vasall_nah"] + 3 * xp["vasall_fern"] + xp["vasall_kanone"] / kanone_jede
    return g, x


def wellentakt(zeit: float) -> float:
    takte = uhren._toml("wellen.toml")["takt"]
    return float(next(s for ab, s in reversed(takte) if zeit >= ab))


def wellenkosten(weg_s: float, zeit: float, stand: str | None) -> tuple[float, float]:
    """(Gold, XP), die du verlierst, wenn du `weg_s` Sekunden nicht in deiner Lane bist.

    Nach dem Stand: gecrasht -> die ersten ~25 s kostet es nichts (Rueckprall), mitte -> ~12 s, bei_uns -> sofort.
    Verloren ist, was dein Turm toetet (Anteil aus wissen/makro/patchwerte.toml [welle])."""
    w = regeln.patch("welle")
    puffer = {"gecrasht": w["rueckprall_nach_crash_s"], "bei_ihnen": w["rueckprall_nach_crash_s"] * 0.7,
              "mitte": w["mitte_bis_turm_s"], "bei_uns": w["bei_uns_bis_verlust_s"]}.get(stand or "mitte", w["mitte_bis_turm_s"])
    wellen = max(0.0, weg_s - puffer) / wellentakt(zeit)
    g, x = wellenwert(zeit)
    return wellen * g * w["anteil_verlust_am_turm"], wellen * x


def fenster_welle(stand: str | None) -> float | None:
    """s, bis die Welle nach diesem Stand wieder bei dir ist (Zeit fuer Ward, Roam, Back ohne Verlust)."""
    w = regeln.patch("welle")
    return {"gecrasht": w["rueckprall_nach_crash_s"], "bei_ihnen": w["rueckprall_nach_crash_s"] * 0.7,
            "mitte": w["mitte_bis_turm_s"], "bei_uns": 0.0}.get(stand or "", None)


def crash_dauer() -> float:
    return float(regeln.patch("welle")["crash_dauer_s"])


# ---------------------------------------------------------------- Ueberzahl


@dataclass
class Einheit:
    lebt: bool = True
    respawn: float = 0.0
    ankunft_s: float | None = 0.0     # s bis zum Ort (None = unbekannt wo)
    bekannt: bool = True


@dataclass
class Zahl:
    wir: int
    gegner_sicher: int
    gegner_moeglich: int

    @property
    def vorteil(self) -> int:
        """Vorsprung gegen das, was moeglich ist (vorsichtig)."""
        return self.wir - self.gegner_moeglich


def ueberzahl(T: float, wir: list[Einheit], gegner: list[Einheit], team_brunnen_weg: float = 40.0) -> Zahl:
    """Wer ist in T Sekunden am Ort? Tote zaehlen ab Respawn + Weg vom Brunnen; Unbekannte zaehlen als 'moeglich'."""
    def da(e: Einheit) -> bool:
        if e.ankunft_s is None:
            return False
        if not e.lebt:
            return e.respawn + team_brunnen_weg <= T
        return e.ankunft_s <= T
    w = sum(1 for e in wir if da(e))
    sicher = sum(1 for e in gegner if e.bekannt and da(e))
    moeglich = sicher + sum(1 for e in gegner if not e.bekannt and (e.lebt or e.respawn + team_brunnen_weg <= T))
    return Zahl(w, sicher, moeglich)


# ---------------------------------------------------------------- Zeitfenster


def fenster_gegner(respawn: float | None = None, backt: bool = False, weg_zur_lane: float = 30.0) -> float | None:
    """s, bis der Lane-Gegner wieder in der Lane sein kann: tot -> Respawn + Weg; im Recall -> Kanal + Einkauf + Weg."""
    r = regeln.patch("recall")
    if respawn and respawn > 0:
        return respawn + weg_zur_lane
    if backt:
        return r["kanal_s"] + r["einkauf_s"] + weg_zur_lane
    return None


def fenster_jungler(gesehen_pos, gesehen_vor: float | None, ziel, tempo: float | None = None) -> float | None:
    """s, bis der Gegner-Jungler fruehestens am Ziel sein kann (Untergrenze aus der letzten Sichtung)."""
    if gesehen_pos is None or gesehen_vor is None:
        return None
    return max(0.0, ankunft(gesehen_pos, ziel, tempo) - gesehen_vor)


# ---------------------------------------------------------------- TP


def tp_abklingzeit(zeit: float, level: int = 1, top_quest: bool = False) -> float:
    t = regeln.patch("tp")
    if zeit < t["unleashed_ab_s"]:
        return float(t["top_quest_abklingzeit_s"] if top_quest else t["abklingzeit_s"])
    a, b = t["top_quest_unleashed_s"] if top_quest else t["unleashed_abklingzeit_s"]
    return a + (b - a) * (max(1, min(18, level)) - 1) / 17


def tp_ankunft(ich_pos, tp_ziel_pos, ort, zeit: float, tempo: float | None = None) -> float:
    """s bis du per TP am Ort bist: Kanal + Anflug (nach Entfernung) + Weg vom TP-Ziel zum Ort."""
    t = regeln.patch("tp")
    anflug_max = t["anflug_max_unleashed_s"] if zeit >= t["unleashed_ab_s"] else t["anflug_max_s"]
    anteil = min(1.0, abstand(ich_pos, tp_ziel_pos) / t["volle_karte_einheiten"])
    return t["kanal_s"] + t["anflug_min_s"] + (anflug_max - t["anflug_min_s"]) * anteil + ankunft(tp_ziel_pos, ort, tempo)


@dataclass
class TPUrteil:
    tpen: bool
    grund: str
    ankunft_s: float
    crash_zuerst: bool = False


def tp_urteil(kampf_in: float, kampf_dauer: float, ankunft_s: float, welle_stand: str | None,
              gegner_tp_bereit: bool | None, wert_tp: float | None = None, wert_bleiben: float | None = None) -> TPUrteil:
    """TP zu Kampf/Objective oder nicht. Zu spaet (Ankunft nach Kampfende) -> nein. Welle bei dir -> erst crashen.
    Werte aus gehirn (Siegchance-Punkte) entscheiden, wenn beide da sind; sonst die Zeiten."""
    crash = welle_stand in ("bei_uns", "mitte")
    ank = ankunft_s + (crash_dauer() if crash else 0.0)
    if ank > kampf_in + kampf_dauer:
        return TPUrteil(False, "zu spaet: der Kampf ist vorbei, bevor du ankommst", ank, crash)
    if wert_tp is not None and wert_bleiben is not None and wert_tp <= wert_bleiben:
        return TPUrteil(False, "bleiben bringt mehr", ank, crash)
    grund = "rechtzeitig da"
    if gegner_tp_bereit is False:
        grund += ", ihr Top hat kein TP"
    return TPUrteil(True, grund, ank, crash)


# ---------------------------------------------------------------- Roam-Wert und Gold in Siegchance


def punkte_je_1000_gold(zeit: float) -> float:
    """Siegchance-Punkte je 1000 Gold Team-Vorsprung (eigene Messung, wissen/makro/patchwerte.toml)."""
    g = regeln.patch("gold_siegchance")
    m, p = g["minute"], g["punkte_je_1000"]
    x = zeit / 60
    if x <= m[0]:
        return p[0]
    for i in range(1, len(m)):
        if x <= m[i]:
            return p[i - 1] + (p[i] - p[i - 1]) * (x - m[i - 1]) / (m[i] - m[i - 1])
    return p[-1]


def roam_wert(weg_s: float, zeit: float, welle_stand: str | None, gewinn_punkte: float) -> float:
    """Netto in Siegchance-Punkten: Gewinn (Aktionswert/Kampf) minus verlorene Wellen (in Punkte umgerechnet)."""
    gold, _ = wellenkosten(weg_s, zeit, welle_stand)
    return gewinn_punkte - gold / 1000 * punkte_je_1000_gold(zeit)


# ---------------------------------------------------------------- Rueckwaertsplanung und Schluss


def rueckwaerts(spawn_in: float) -> tuple[str, str | None, float]:
    """Setup-Kette vor einem Monster (wissen/makro/regeln.toml O7: 90 Welle, 60 Back, 30 Sicht, 0 Grube).
    Rueckgabe: (Schritt jetzt, naechster Schritt, s bis dahin)."""
    schritte = sorted(regeln.regel("O7")["schritte"], key=lambda s: -s[0])     # 90, 60, 30, 0
    begonnen = [(s, n) for s, n in schritte if spawn_in <= s]
    if not begonnen:                                   # vor 90 s: noch frei, der erste Schritt kommt
        s0, n0 = schritte[0]
        return "frei", n0, spawn_in - s0
    s_j, jetzt = begonnen[-1]
    idx = [n for _, n in schritte].index(jetzt)
    if idx + 1 < len(schritte):
        naechst_s, naechst = schritte[idx + 1]
        return jetzt, naechst, max(0.0, spawn_in - naechst_s)
    return jetzt, None, 0.0


def schluss_moeglich(weg_s: float, ziel: str, respawns: list[float]) -> tuple[bool, float]:
    """Nach einem Ace: Reicht die Zeit bis Inhibitor/Nexus vor dem ersten Respawn? (Entscheidung zu Stufe 2, Punkt 3)
    Rueckgabe: (ja/nein, Reserve in s)."""
    r = regeln.regel("baron_nach_ace")
    zerstoeren = {"inhib": r["zerstoeren_inhib_s"], "nexus": r["zerstoeren_nexus_s"],
                  "turm": r["zerstoeren_turm_s"]}.get(ziel, r["zerstoeren_nexus_s"])
    erster = min(respawns) if respawns else 0.0
    reserve = erster - (weg_s + zerstoeren)
    return reserve >= 0, reserve
