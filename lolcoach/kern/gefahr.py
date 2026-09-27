"""Gefahr: Wahrscheinlichkeit statt schlimmster Fall (Buch 0, Kapitel 7.5).

Je lebendem Gegner `p_da` - die Wahrscheinlichkeit, dass er im Fenster T bei dir ist - aus seiner fruehesten
Ankunft (`GegnerLage.ankunft`, vorhanden), ob er sichtbar ist, seit wann nicht, und der Seite, auf der er
wahrscheinlich ist (Jungler: `jungle.wahrscheinlich`, geeicht). Wer dich toetet, ist die Menge der Ankommenden:
`p_verliere` aus `kraft_gegen` (ein Verhaeltnis), gemindert durch Flash und deinen Turm.

    p_tod = 1 - Prod_g (1 - p_da(g, T) * p_kampf(g) * p_verliere({g} + sichtbare Nahe))

`p_kampf` ist nicht im Buch (Schritt 3, messungen.md): ein sichtbarer Gegner in 1500, der nicht auf dich zulaeuft,
ist da, kaempft aber nicht sicher - wer ungesehen ankommt oder auf dich zulaeuft, kommt zum Kaempfen."""
from __future__ import annotations

from ..bewertung import BRUNNEN, abstand
from ..zustand import gegenteam

NAH = 1500.0            # "sichtbare Nahe" und "abstand <= 1500" (7.5)
UNBEKANNT_AB = 45.0     # g unbekannt (> 45 s)


def rampe(x: float, cfg: dict) -> float:
    return max(0.0, min(1.0, x / cfg["anlauf_spielraum_s"]))


def ist_lane(g, m) -> bool:
    b = m.b
    return b is not None and b.lane is not None and g.s.name == b.lane.s.name


def p_seite(g, m, cfg: dict) -> float:
    """Wie wahrscheinlich ist er auf deiner Kartenseite (7.5)? Jungler: geeichte Prognose; Lane-Gegner: 1, wenn er
    fehlt (der Brunnen steckt schon in seiner Ankunft); Mid/Support ab 4:00 und alle nach der Lane-Phase: roam_basis."""
    rolle = g.s.rolle
    if ist_lane(g, m):
        # in der Lane-Phase ist er auf deiner Lane, fehlt er, kommt er zu dir; danach nur, wenn du auf deiner Lane
        # stehst - sonst wandert er wie alle (Schritt 4, messungen.md)
        if m.lane_phase or m.bereich == "lane_eigen":
            return 1.0
        return _gesehene_seite(g, m, cfg)
    if rolle == "JUNGLE":
        return m.p_jungler if m.p_jungler is not None else 0.5
    if m.lane_phase:
        return cfg["roam_basis"] if rolle in ("MIDDLE", "UTILITY") and m.zeit >= 240 else 0.0
    return _gesehene_seite(g, m, cfg)


def _gesehene_seite(g, m, cfg: dict) -> float:
    """Nach der Lane-Phase wie beim Jungler (jungle.wahrscheinlich): die Seite seiner letzten Sichtung, verblasst ueber
    90 s; nie gesehen oder ohne Ort roam_basis (Schritt 4, messungen.md - 102112, 35:35: Kai'Sa vor 7 s unten, Sona und
    Sett unten, du allein im unteren Fluss; mit roam_basis fuer alle war das "keine Gefahr")."""
    if g.pos is None or g.seit is None or g.seit > UNBEKANNT_AB:
        return cfg["roam_basis"]
    from ..bewertung import BREITE, HOEHE
    from ..jungle import seite
    from .merkmale import meine_seite
    dort = seite(g.pos[0] / BREITE, 1.0 - g.pos[1] / HOEHE)
    bleibt = max(0.35, 1.0 - g.seit / 90)
    meine = meine_seite(m)
    if meine is None:
        return bleibt
    return bleibt if dort == meine else 1.0 - bleibt


def _weg_vom_brunnen(g, m) -> float:
    """Sekunden, bis ein Toter aus seinem Brunnen bei dir ist."""
    if m.pos is None or m.p is None:
        return 30.0
    feind = gegenteam(m.p.mein_team)
    return abstand(BRUNNEN[feind], m.pos) * 1.15 / (g.tempo or 350.0)


def p_da(g, T: float, m, cfg: dict) -> float:
    """Kapitel 7.5: sichtbar -> 1, wenn er in T da sein kann und naeher kommt oder schon in 1500 steht; unsichtbar
    (<= 45 s) -> Seite x Rampe; unbekannt -> Seite x unbekannt_faktor; tot -> nur, wenn Respawn + Weg <= T."""
    if g.s.tot:
        rest = g.s.respawn + _weg_vom_brunnen(g, m)
        return p_seite(g, m, cfg) * rampe(T - rest, cfg) if rest <= T else 0.0
    t_min = g.ankunft if g.ankunft is not None else 0.0
    if g.sichtbar:
        if t_min <= T and (g.kommt_naeher or (g.abstand is not None and g.abstand <= NAH)):
            return 1.0
        return rampe(T - t_min, cfg)
    if g.seit is None or g.seit > UNBEKANNT_AB:
        return p_seite(g, m, cfg) * cfg["unbekannt_faktor"]
    return p_seite(g, m, cfg) * rampe(T - t_min, cfg)


def p_kampf(g, m, cfg: dict, kampf_mit: str | None = None) -> float:
    """Kommt er zum Kaempfen? Ungesehen Ankommende und wer auf dich zulaeuft: ja. Ein Sichtbarer, der nur da
    steht: kampf_ohne_anlauf - ausser du suchst den Kampf mit ihm (`kampf_mit`, TRADE/ALL_IN). Dein Lane-Gegner,
    der auf dich zulaeuft, laeuft meist nur zu seiner Welle (echte Partie 140253, 0:38: "Raus zu deinem Turm" zu
    Spielbeginn) - er kommt sicher zum Kaempfen nur, wenn er staerker ist oder du unter der Haelfte bist."""
    if kampf_mit is not None and g.s.name == kampf_mit:
        return 1.0
    if not g.sichtbar or g.s.tot:
        return 1.0
    if g.kommt_naeher:
        b = m.b
        if ist_lane(g, m) and b is not None and (b.leben is None or b.leben >= 0.5) and b.kraefte()[0] > -1.0:
            return cfg["kampf_ohne_anlauf"]
        return 1.0
    return cfg["kampf_ohne_anlauf"]


def p_verliere(gruppe: list, m, cfg: dict, am_turm: bool = False, T: float | None = None) -> float:
    """Buch 7, 3.1: 1 - kampf.p_gewinn an deinem Ort, bedingt darauf, dass genau diese Menge kommt (Gewicht 1 - ihr
    p_da steckt schon in p_tod). Dein Turm steckt im Kampfurteil (turm_faktor), `am_turm` bleibt nur fuer die Aufrufer;
    Flash wirkt auf p_tod (flucht_flash)."""
    from .kampf import p_gewinn
    b = m.b
    # an deinem Turm oder <= 5 s davon: der Kampf findet unter ihm statt (vorher flucht_turm auf p - jetzt einmal in K)
    turm = 1 if am_turm or (b is not None and b.zum_turm is not None and b.zum_turm <= 5.0) else None
    p, _ = p_gewinn(m, b.pos if b is not None else None, T if T is not None else cfg["fenster_s"],
                    gewichte={g.s.name: 1.0 for g in gruppe}, turm=turm)
    return 1.0 - p


BASIS_RADIUS = 5000.0   # bis zu den Inhibitor-Tuermen (3900-4500 vom Brunnen): dort steht, wer respawnt


def p_da_am(g, T: float, m, cfg: dict, ort) -> float:
    """Buch 6, 3.1: p_da mit der Ankunft an `ort` statt bei dir (dieselbe Formel wie 7.5). ort None = bei dir.
    Ein Toter, dessen Brunnen <= BASIS_RADIUS von `ort` liegt, ist da, sobald Respawn + Weg <= T - ohne p_seite und
    ohne Anlauf-Rampe: er steht dort auf (102112 34:51: am Mid-Inhibitor-Turm zaehlten Sett, Kai'Sa und Fiddlesticks, die
    11-19 s spaeter daneben aufstanden, mit 0,09-0,15)."""
    b = m.b
    if ort is None or b is None or (b.pos is not None and abstand(b.pos, ort) < 1.0):
        return p_da(g, T, m, cfg)
    if g.s.tot:
        brunnen = BRUNNEN.get(g.s.team, ort)
        rest = g.s.respawn + abstand(brunnen, ort) * 1.15 / (g.tempo or 350.0)
        if abstand(brunnen, ort) <= BASIS_RADIUS:
            return 1.0 if rest <= T else 0.0      # Respawn und der kurze Weg sind bekannt - keine Anlauf-Rampe
        return p_seite(g, m, cfg) * rampe(T - rest, cfg) if rest <= T else 0.0
    if g.pos is None or g.seit is None:
        return p_seite(g, m, cfg) * cfg["unbekannt_faktor"]
    d = abstand(g.pos, ort)
    t_min = max(0.0, d * 1.15 / (g.tempo or 350.0) - (0.0 if g.sichtbar else g.seit))
    if g.sichtbar:
        return 1.0 if t_min <= T and d <= NAH else rampe(T - t_min, cfg)
    if g.seit > UNBEKANNT_AB:
        return p_seite(g, m, cfg) * cfg["unbekannt_faktor"]
    return p_seite(g, m, cfg) * rampe(T - t_min, cfg)


def p_tod(T: float, m, cfg: dict, am_turm: bool = False, kampf_mit: str | None = None) -> tuple[float, list]:
    """(p_tod im Fenster T, [(Champion, Anteil)] - wer dich toeten koennte, der Groesste zuerst)."""
    b = m.b
    if b is None:
        return 0.0, []
    # "Wer dich wirklich toetet, ist die Menge der Ankommenden" (7.5). Qualitaetsrunde 2, G2: gerechnet wird ueber die
    # Mengen - jede Teilmenge der moeglichen Ankommenden mit ihrer Wahrscheinlichkeit (unabhaengig), gekaempft gegen
    # sie und die sichtbar Nahen. Vorher kaempfte JEDER gegen alle wahrscheinlich Ankommenden, und jeder zaehlte dann
    # noch einmal fuer sich: vier Ungesehene "kamen" doppelt (133930 12:30: 0,79 statt 0,37). Sichtbar Anlaufende
    # (102112, 9:04: Sett, Galio, Fiddlesticks) haben p_da ~ 1 - ihre Menge zaehlt dann voll.
    nahe = [g for g in b.gegner if not g.s.tot and g.sichtbar and g.abstand is not None and g.abstand <= NAH]
    q, wer = [], []
    for g in b.gegner:
        pd = p_da(g, T, m, cfg)
        if pd <= 0.0:
            continue
        x = pd * p_kampf(g, m, cfg, kampf_mit)
        if x <= 0.0:
            continue
        q.append((g, x))
        # sein Anteil (fuer "wer kommt", 7.5): p_da * p_kampf * p_verliere({g} u sichtbare Nahe)
        a = x * p_verliere([g] + [n for n in nahe if n is not g], m, cfg, am_turm, T)
        if a > 0:
            wer.append((g.champion, a))
    p = _ueber_mengen(q, nahe, m, cfg, am_turm, T)
    # Flash bereit: du kommst oefter weg (Buch 7, 3.1: bleibt als Faktor auf p_tod)
    flucht = cfg["flucht_flash"] if b.flash == 0 else 1.0
    return p * flucht, sorted(((n, a * flucht) for n, a in wer), key=lambda w: -w[1])


MENGEN_MAX = 6          # so viele moegliche Ankommende werden einzeln gerechnet (2^6 = 64 Mengen), der Rest faellt weg


def _ueber_mengen(q: list, nahe: list, m, cfg: dict, am_turm: bool, T: float | None = None) -> float:
    """P(du verlierst) = Summe ueber die Mengen S der Ankommenden: P(S) * p_verliere(S u sichtbare Nahe)."""
    from itertools import combinations
    q = sorted(q, key=lambda gx: -gx[1])[:MENGEN_MAX]
    n = len(q)
    p = 0.0
    for r in range(1, n + 1):
        for S in combinations(range(n), r):
            ps = 1.0
            for i in range(n):
                ps *= q[i][1] if i in S else 1.0 - q[i][1]
            if ps < 1e-4:
                continue
            gruppe = [q[i][0] for i in S]
            gruppe += [g for g in nahe if all(g is not x for x in gruppe)]
            p += ps * p_verliere(gruppe, m, cfg, am_turm, T)
    return min(1.0, p)


def p_tod_am(m, ziel: tuple[float, float] | None, ankunft_s: float, cfg: dict,
             am_turm: bool = False) -> tuple[float, list]:
    """Pruefung E2 (Qualitaetsrunde 1): die Gefahr an `ziel`, wenn du in `ankunft_s` Sekunden dort bist - nach dem Tod
    Respawn + Weg aus dem Brunnen, aus der Basis der Weg - statt an dem Ort, an dem du gerade liegst (144655 1:59:
    "zurueck nach Top" mit p_tod 0,64, gerechnet am Todesort mit 0 % Leben; 140253 10:25: "zu den Larven" mit 0,97).
    Jeder Gegner laeuft von seiner letzten Sichtung aus weiter; du kommst mit vollem Leben, wenn du tot bist."""
    from dataclasses import replace
    b = m.b
    if b is None or ziel is None:
        return 0.0, []

    def weiter(g):
        if g.s.tot:
            return g
        if g.pos is None or g.seit is None:
            return replace(g, sichtbar=False, ankunft=None, abstand=None, kommt_naeher=False)
        d = abstand(g.pos, ziel)
        return replace(g, sichtbar=False, abstand=d, kommt_naeher=False,
                       ankunft=max(0.0, d * 1.15 / (g.tempo or 350.0) - g.seit))
    # aus dem Brunnen kommst du voll (G2: 144655 5:06 rechnete mit 0,43-0,68 Leben, waehrend Riven im Brunnen heilte)
    leben = 1.0 if m.tot or b.leben is None or m.bereich == "basis_eigen" else b.leben
    b2 = replace(b, gegner=[weiter(g) for g in b.gegner], pos=ziel, leben=leben, zum_turm=0.0 if am_turm else None)
    m2 = replace(m, pos=ziel, b=b2, leben=leben, bereich=None)
    return p_tod(ankunft_s + cfg["fenster_s"], m2, cfg, am_turm=am_turm)


def alle_p_da(m, cfg: dict, T: float | None = None) -> dict[str, float]:
    """Champion -> p_da im Standardfenster (Dashboard, Protokoll, Eichung mit kennzahlen.py)."""
    if m.b is None:
        return {}
    T = cfg["fenster_s"] if T is None else T
    return {g.champion: round(p_da(g, T, m, cfg), 3) for g in m.b.gegner}
