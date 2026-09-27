"""Die Zeitleiste (Buch 11, Kapitel 2): was in den naechsten `zeitleiste_s` (180 s) passiert - nur Bekanntes.

Je Takt neu gebaut, sortiert. Quellen: Objective-Spawns (Buch 6, 2), Respawns der Gegner, bekannte Zauber-Timer der
Gegner (Flash, TP), euer Fenster (Tote plus Weg aus dem Brunnen, Buch 5, 8), Baron-Buff und Aeltester, Inhibitoren,
die naechste Kanonenwelle deiner Lane, dein Back-Bedarf (Gold zum naechsten Kauf) und dein TP.

Fuer Dashboard (`Kern.stand()["zeitleiste"]`), `Kern.kontext()` und die Saetze VORSCHAU/WENDEPUNKT (kern/fuehren.py).
"""
from __future__ import annotations

from dataclasses import dataclass

BUFF_S = {"baron": 180.0, "aeltester": 150.0}
INHIB_S = 300.0
ZAUBER_NAME = {"SummonerFlash": "Flash", "SummonerTeleport": "TP"}
OBJ_WORT = {"drache": "Drache", "baron": "Baron", "herold": "Herold", "larven": "Larven", "aeltester": "Ältester"}


@dataclass
class Eintrag:
    zeit: float              # Spielzeit, zu der es passiert
    art: str                 # objective, respawn, zauber, fenster, buff, inhib, welle, kauf, tp
    text: str                # "Herold spawnt", "Rumble lebt wieder", "Sona hat Flash wieder"
    schl: str | None = None  # Objective-Schluessel, Champion, Lane ...

    def in_s(self, jetzt: float) -> int:
        return max(0, int(round(self.zeit - jetzt)))


def _uhr(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


def bauen(m, cfg: dict, lagebild=None, einkommen: float | None = None) -> list[Eintrag]:
    """Die Zeitleiste zum Stand `m`. `einkommen`: dein Gold je Sekunde (fuer den Back-Bedarf), sonst ohne."""
    if m is None or m.b is None or m.p is None:
        return []
    c = cfg["fuehren"]
    jetzt, bis = m.zeit, m.zeit + c["zeitleiste_s"]
    p, b = m.p, m.b
    aus: list[Eintrag] = []
    # Objectives, die spawnen
    for o in m.objectives or []:
        if not o.lebt and 0 < o.spawn_in <= c["zeitleiste_s"]:
            aus.append(Eintrag(jetzt + o.spawn_in, "objective", f"{OBJ_WORT.get(o.schl, o.schl)} spawnt", o.schl))
    # Gegner stehen wieder auf
    for g in b.gegner:
        if g.s.tot and g.s.respawn is not None and 0 < g.s.respawn <= c["zeitleiste_s"]:
            aus.append(Eintrag(jetzt + g.s.respawn, "respawn", f"{g.champion} lebt wieder", g.champion))
    # euer Fenster: frueheste Rueckkehr eines Toten an deinen Ort (ab zwei Toten - Umwandeln, Buch 5, 8)
    tote = [g for g in b.gegner if g.s.tot]
    if len(tote) >= 2 and m.pos is not None:
        from .gefahr import _weg_vom_brunnen
        zurueck = min(g.s.respawn + _weg_vom_brunnen(g, m) for g in tote)
        if 0 < zurueck <= c["zeitleiste_s"]:
            aus.append(Eintrag(jetzt + zurueck, "fenster", f"euer Fenster endet ({len(tote)} tot)"))
    # bekannte Zauber der Gegner kommen zurueck (nur mit Beleg: Chat, Minimap, Bildschirm)
    z = getattr(lagebild, "zauber", None)
    if z is not None:
        feinde = {s.name for s in p.gegner()}
        for t in z.timer.values():
            if t.name in feinde and t.zauber in ZAUBER_NAME and jetzt < t.zurueck <= bis:
                aus.append(Eintrag(t.zurueck, "zauber", f"{t.champion} hat {ZAUBER_NAME[t.zauber]} wieder", t.champion))
    # Buffs und Inhibitoren aus den Ereignissen
    for e in p.ereignisse:
        if e.art == "BaronKill" or (e.art == "DragonKill" and e.daten.get("DragonType") == "Elder"):
            art = "baron" if e.art == "BaronKill" else "aeltester"
            ende = e.zeit + BUFF_S[art]
            if jetzt < ende <= bis:
                wer = "euer" if e.team == p.mein_team else "ihr"
                aus.append(Eintrag(ende, "buff", f"{wer} {'Baron-Buff' if art == 'baron' else 'Ältester-Buff'} endet", art))
        elif e.art == "InhibKilled":
            from ..bewertung import struktur
            st = struktur(e.daten.get("InhibKilled", ""))
            ende = e.zeit + INHIB_S
            if st is not None and jetzt < ende <= bis:
                wer = "euer" if st.team == p.mein_team else "ihr"
                aus.append(Eintrag(ende, "inhib", f"{wer} {st.lane}-Inhibitor steht wieder", st.lane))
    # deine Welle: die naechste Kanone deiner Lane (Wellen-Uhr, Buch 1)
    if m.kanone_in is not None and 0 < m.kanone_in <= c["zeitleiste_s"] and m.meine_lane:
        aus.append(Eintrag(jetzt + m.kanone_in, "welle", f"Kanone in deiner {m.meine_lane}-Welle", m.meine_lane))
    # dein Back-Bedarf: das naechste Item ist kaufbar
    k = getattr(b, "kauf", None)
    naechstes = getattr(k, "naechstes", None) if k is not None else None
    if naechstes and einkommen and einkommen > 0:
        item, fehlt = naechstes
        t = float(fehlt) / einkommen
        if 0 < t <= c["zeitleiste_s"]:
            aus.append(Eintrag(jetzt + t, "kauf", f"{item} kaufbar", item))
    # dein TP (auch das Quest-TP, Auftrag 002)
    if m.tp_in is not None and 0 < m.tp_in <= c["zeitleiste_s"]:
        aus.append(Eintrag(jetzt + m.tp_in, "tp", "dein TP ist wieder da"))
    aus.sort(key=lambda e: e.zeit)
    return aus


def fuer_stand(eintraege: list[Eintrag], jetzt: float, n: int = 8) -> list[dict]:
    return [{"zeit": round(e.zeit, 1), "uhr": _uhr(e.zeit), "in_s": e.in_s(jetzt), "text": e.text, "art": e.art}
            for e in eintraege[:n]]


def als_text(eintraege: list[Eintrag], jetzt: float, n: int = 6) -> str:
    """Eine Zeile fuer Kontext und Protokoll: "13:00 Herold spawnt (in 45 s); 13:12 Rumble lebt wieder (in 57 s)"."""
    return "; ".join(f"{_uhr(e.zeit)} {e.text} (in {e.in_s(jetzt)} s)" for e in eintraege[:n])
