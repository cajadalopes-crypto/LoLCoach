"""Wellen-Zustand aus den Vasallen-Punkten der Minimap.

Carlos: "Er soll mir immer situativ sagen, wie ich die Welle genau vorbereite." Dafuer
muss der Coach wissen, wo die Wellen stehen - die Live-API sagt es nicht, die Minimap
zeigt es: Vasallen sind kleine blaue und rote Punkte (~8 px bei 4K) entlang der Lanes.

Erkennung:
  - Farbe (Blau/Rot wie die Vasallen), kleine runde Flecken,
  - was ueber ~20 s an derselben Stelle leuchtet, ist ein Icon (Turm, Inhibitor) und
    wird ausgeblendet (gleitender Mittelwert je Pixel),
  - nichts in der Naehe eines Champion-Portraets (dessen Ring hat dieselben Farben),
  - jeder Punkt wird auf die naechste Lane projiziert: s = 0 an der blauen, 1 an der roten Basis.
Daraus je Lane: wo sich die Wellen treffen, wer wie viele hat, wer schiebt.

Front statt Summe (Nachtrag zu Buch 1, 1.4; Qualitaetsrunde 1, F1): die Punkte einer Lane werden entlang der Lane in
Gruppen geteilt (Luecke > `[welle] front_luecke`). Gezaehlt wird nur die Front - die Gruppe mit beiden Farben, sonst
die vorderste blaue und die ihr naechste rote Gruppe. Nachlaufende Wellen zaehlen nicht (144655, 3:13/5:17/5:38:
gegnerische Vasallen an deinem Turm, deine naechste Welle lief erst am inneren los - die Summe ergab ZU_IHM).
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

# Lanes als Linienzuege in Kartenanteilen, von der blauen zur roten Basis
LANES = {
    "Top": [(0.07, 0.80), (0.07, 0.25), (0.15, 0.15), (0.25, 0.07), (0.80, 0.07)],
    "Mid": [(0.25, 0.75), (0.75, 0.25)],
    "Bot": [(0.20, 0.93), (0.75, 0.93), (0.85, 0.85), (0.93, 0.75), (0.93, 0.20)],
}
LANE_ABSTAND = 0.045          # weiter weg von der Lane: kein Lane-Vasall (Jungle, Fluss)
TURM_AUSSEN = (0.35, 0.65)    # grob: s der aeusseren Tuerme (blau, rot)
STAND_MITTE = (0.45, 0.55)    # dazwischen steht die Front "in der Mitte der Lane" (wie worte())
WELLE_AB = 2                  # so viele gegnerische Vasallen auf deiner Haelfte machen "bei_uns"
STATISCH_AB = 0.8             # Anteil der Zeit, ab dem ein Pixel als Icon gilt
GEDAECHTNIS = 0.06            # Gewicht eines neuen Bildes im gleitenden Mittel (~1 Bild/s -> ~16 s)
REF = 570                     # Minimap-Kante bei 4K; Flaechen skalieren mit (Kante/REF)^2
ICON_RADIUS = 48 / 570 / 2    # Champion-Icon (minimap.PORTRAET) als Anteil der Minimap-Kante
SCHNITT_FLAECHE = 10          # F1: so gross muss ein von einer weissen Linie angeschnittener Vasall noch sein
RING_BIS = 1.1                # der farbige Ring reicht bis ~1,05 Icon-Radien (gemessen 27.09. an 314 freien Icons der
#                               Partie 140253, 764 px: Ring bei 30-33 px, Icon-Radius 32 px, ab 34 px nichts mehr)


@dataclass(frozen=True)
class LaneZustand:
    lane: str
    blau: int                 # Vasallen je Seite (gezaehlt)
    rot: int
    front: float | None       # s, wo sich die Wellen treffen / die vorderste Welle steht
    schiebt: str | None       # "blau", "rot" oder None (steht)
    vorn_blau: tuple = ()     # s der Front-Vasallen (F1); blau/rot oben zaehlen nur sie
    vorn_rot: tuple = ()
    naechste_blau: float | None = None   # die naechste nachlaufende Welle (ihre Spitze), zaehlt nicht fuer den Zustand
    naechste_rot: float | None = None
    alle_blau: int = 0        # alle Vasallen der Lane, Front und nachlaufend
    alle_rot: int = 0
    s_blau: tuple = ()        # s aller Vasallen der Lane (fuer stand())
    s_rot: tuple = ()

    def stand(self, mein_team: str) -> str | None:
        """Wo die Front steht, aus Sicht des Spielers (makro.lage.Welle.stand): "bei_uns" (eigene Haelfte),
        "mitte", "bei_ihnen"; None ohne Welle. Gilt fuer jede Lane (Auftrag 033, gemessen in phase3b_bericht.md)."""
        if self.front is None:
            return None
        s = self.front if mein_team == "ORDER" else 1 - self.front
        stand = "bei_uns" if s < STAND_MITTE[0] else "bei_ihnen" if s > STAND_MITTE[1] else "mitte"
        # Nur die eigene Welle zu sehen: sie laeuft nach vorn, die Gegnerwelle ist im Nebel - ihre Spitze auf der
        # eigenen Haelfte heisst NICHT "sie laeuft auf euren Turm" (Stichprobe wellen_proben.json, W0/W6)
        # "bei_uns" heisst: eine GEGNERWELLE ist auf eurer Haelfte - mindestens WELLE_AB gegnerische Vasallen dort.
        # Ein einzelner roter Punkt war in der Stichprobe oft keiner: Totenkopf-Marker einer Kill-Stelle, Pixel eines
        # Champion-Icons (4 von 24 "bei_uns" falsch, alle mit genau einem roten Punkt; wellen_labels.json)
        die_s = self.s_rot if mein_team == "ORDER" else tuple(1 - x for x in self.s_blau)
        if stand == "bei_uns" and sum(x < 0.5 for x in die_s) < WELLE_AB:
            stand = "mitte"
        return stand

    def worte(self, mein_team: str) -> str:
        """Aus Sicht des Spielers: 'eure 6 gegen seine 2, kurz vor seinem Turm'."""
        blau_ist_wir = mein_team == "ORDER"
        wir, die = (self.blau, self.rot) if blau_ist_wir else (self.rot, self.blau)
        if wir == 0 and die == 0:
            return "keine Welle zu sehen"
        s = self.front if blau_ist_wir else (1 - self.front if self.front is not None else None)
        if s is None:
            ort = "?"
        elif s >= 0.72:
            ort = "tief bei seinem Turm"
        elif s >= TURM_AUSSEN[1] - 0.06:
            ort = "an seinem Turm"
        elif s > 0.55:
            ort = "auf seiner Haelfte"
        elif s >= 0.45:
            ort = "in der Mitte der Lane"
        elif s > TURM_AUSSEN[0] + 0.06:
            ort = "auf deiner Haelfte"
        elif s > 0.28:
            ort = "an deinem Turm"
        else:
            ort = "tief bei deinem Turm"
        return f"eure {wir} gegen seine {die}, {ort}"


def _projektion(x: float, y: float) -> tuple[str, float, float] | None:
    """(Lane, s 0..1, Abstand) der naechsten Lane, oder None."""
    bestes = None
    for lane, punkte in LANES.items():
        laengen = [np.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(punkte, punkte[1:])]
        gesamt, bis = sum(laengen), 0.0
        for (a, b), l in zip(zip(punkte, punkte[1:]), laengen):
            dx, dy = b[0] - a[0], b[1] - a[1]
            t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / (l * l)))
            px, py = a[0] + t * dx, a[1] + t * dy
            d = np.hypot(x - px, y - py)
            if bestes is None or d < bestes[2]:
                bestes = (lane, (bis + t * l) / gesamt, d)
            bis += l
    return bestes if bestes and bestes[2] <= LANE_ABSTAND else None


# Pulks (Auftrag 033): ein Vasall ist ~8 px rund (Flaeche ~50 bei 570); ab 76 px Flaeche liegen mehrere uebereinander.
PULK_FLAECHE = (100, 900)       # Silhouette (bei 570): ein Vasall ~79, ab 100 ist es mehr als einer
PULK_FUELL = 0.3
PULK_KANTE = 70
KREIS_R = 3.8                   # heller Kern eines Vasallen, Radius px bei 570 (Flaeche ~45)
KREIS_MIN = 0.5                 # so viel eines Kerns muss unerklaert hell sein
SCHABLONE_R = 5.0               # ganzer Vasall samt dunklerem Rand, Radius bei 570 (Flaeche 79, an 490 freistehenden
#                                 gemessen, Rot und Blau gleich)
UEBERSTAND_AB = 8               # was so viel (px bei 570) ueber die Schablonen hinausragt, ist ein verdeckter Vasall
BUCKEL_MAX = 5.5                # ein Vasall ist innen hoechstens so dick (Radius ~4 px); dicker = Ping, Symbol
HALBMOND_KANTE = 9              # ein angeschnittener Vasall ist hoechstens so lang


LOCH_AB = 12                    # eingeschlossene Flaeche (bei 570): so viel hat kein Vasallen-Pulk


def _loch(teil: np.ndarray) -> int:
    """Pixel, die das Teil ganz umschliesst (Loch in der Mitte)."""
    rand = np.pad(teil, 1)
    flut = rand.copy()
    cv2.floodFill(flut, None, (0, 0), 1)
    return int((flut == 0).sum())


def _buckel(teil: np.ndarray, lin: float) -> list[tuple[float, float]]:
    """Mitten der Vasallen in einem Pulk. Ein Vasall ist immer derselbe Kreis: nacheinander wird der Kreis dorthin
    gelegt, wo er am meisten noch unerklaerte Flaeche deckt, bis der Rest keinen Teilkreis mehr ergibt - so zaehlt
    auch ein Vasall, von dem nur ein Halbmond hervorschaut (Carlos, 30.09., am Pulk neben Karma: fuenf statt drei)."""
    r = KREIS_R * lin
    k = int(np.ceil(r))
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    kreis = ((xx * xx + yy * yy) <= r * r).astype(np.float32)
    flaeche = float(kreis.sum())
    rest = np.pad(teil.astype(np.float32), k)
    aus = []
    for _ in range(12):
        deckung = cv2.filter2D(rest, -1, kreis, borderType=cv2.BORDER_CONSTANT)
        _, v, _, (x, y) = cv2.minMaxLoc(deckung)
        if v < KREIS_MIN * flaeche:
            break
        aus.append((float(x - k), float(y - k)))
        cv2.circle(rest, (x, y), int(round(r)), 0, -1)         # den Kreis als erklaert streichen
    return aus


KNOCHEN_AB = 130              # dunkle Pixel im Teamton rund um einen Punkt (bei 570): mehr = kein Vasall
KNOCHEN_JE_PIXEL = 2.0


def _mit_knochen(hsv: np.ndarray, s, team: str, f: float) -> bool:
    """Der Punkt ist Teil eines groesseren, dunkleren Symbols: Totenkopf einer Kill-Stelle (Schaedel hell, Knochen
    dunkel), Turm-Ziffer, Champion-Ring. Gezaehlt werden dunkle Pixel im Teamton im doppelten Kasten - an 240 roten
    Punkten der Wellen-Stichprobe (Auftrag 033): Schaedel/Tuerme/Ringe 136-1123, Vasallen und Vasallen-Pulks
    hoechstens 127 (buecher/challenger/phase3b_bericht.md)."""
    x0, y0, w, h = s[0] - s[2] // 2 - 2, s[1] - s[3] // 2 - 2, 2 * s[2] + 4, 2 * s[3] + 4
    win = hsv[max(0, y0):y0 + h, max(0, x0):x0 + w].reshape(-1, 3)
    ton = ((win[:, 0] <= 10) | (win[:, 0] >= 170)) if team == "rot" else ((win[:, 0] >= 95) & (win[:, 0] <= 112))
    dunkel = ton & (win[:, 1] >= 60) & (win[:, 2] >= 40) & (win[:, 2] < 130)
    # und im Verhaeltnis: ein Pulk hat viele dunkle Raender, aber je rotem Pixel nur ~1 (Schaedel/Ziffer 3-5)
    return float(dunkel.sum()) / f >= KNOCHEN_AB and dunkel.sum() >= KNOCHEN_JE_PIXEL * s[4]


class Wellenleser:
    def __init__(self):
        self._mittel: np.ndarray | None = None
        self.bilder = 0

    def punkte(self, karte: np.ndarray, champions: list[tuple[float, float]] = ()) -> list[tuple[str, float, float]]:
        """(team, x, y) je Vasall. Pflegt nebenbei die Icon-Maske (ein Aufruf je Sekunde reicht)."""
        seite = karte.shape[0]
        hsv = cv2.cvtColor(karte, cv2.COLOR_BGR2HSV)
        blau = cv2.inRange(hsv, (95, 120, 170), (112, 255, 255))
        rot = cv2.inRange(hsv, (0, 130, 150), (8, 255, 255)) | cv2.inRange(hsv, (172, 130, 150), (180, 255, 255))
        jetzt = ((blau | rot) > 0).astype(np.float32)
        if self._mittel is None or self._mittel.shape != jetzt.shape:
            self._mittel = jetzt.copy()
        else:
            self._mittel = (1 - GEDAECHTNIS) * self._mittel + GEDAECHTNIS * jetzt
        self.bilder += 1
        statisch = cv2.dilate((self._mittel > STATISCH_AB).astype(np.uint8), np.ones((5, 5), np.uint8))
        f = (seite / REF) ** 2
        # Champion-Icons samt Ring schwaerzen - nur die, nicht ihren Umkreis: der Ring hat die Vasallenfarben, ein
        # Vasall direkt daneben bleibt ganz (vorher: Raute 0,05 um die Icon-Mitte, am Schwerpunkt getestet - auf den
        # Diagonalen enger als der Ring, auf den Achsen weiter)
        icons = np.zeros(blau.shape, np.uint8)
        r = int(round(ICON_RADIUS * RING_BIS * seite)) + 1
        for a, b in champions:
            cv2.circle(icons, (int(round(a * seite)), int(round(b * seite))), r, 255, -1)
        # Weisse Linien (dein Laufweg, der Kamerarahmen) zerschneiden Vasallen in Stuecke unter der Mindestflaeche
        # (144655, 5:17: drei gegnerische am Turm, Stuecke 19/16/53 - die 1-px-Linie mit dunklem Schatten darunter).
        # Ein Stueck ab SCHNITT_FLAECHE, das eine weisse Linie beruehrt, zaehlt als Vasall.
        linie = cv2.dilate(cv2.inRange(hsv, (0, 0, 170), (180, 70, 255)), np.ones((5, 5), np.uint8)) > 0
        aus = []
        lin = seite / REF
        # Silhouette: der ganze Vasall, auch dunkler (hinten liegend) - fuer die Schablone im Pulk
        ton = {"rot": (hsv[..., 0] <= 10) | (hsv[..., 0] >= 170), "blau": (hsv[..., 0] >= 95) & (hsv[..., 0] <= 112)}
        silhouette = {t: (ton[t] & (hsv[..., 1] >= 90) & (hsv[..., 2] >= 60)).astype(np.uint8) for t in ton}
        # ganze, runde Vasallen je Farbe - ein angeschnittener Vasall liegt immer an einem ganzen der anderen Farbe
        # (Wellen im Kampf), ein Stueck Champion-Ring nicht
        rund = {}
        for team, maske in (("blau", blau), ("rot", rot)):
            m = maske.copy()
            m[(statisch > 0) | (icons > 0)] = 0
            n, marken, st, _ = cv2.connectedComponentsWithStats(m)
            ok = np.zeros(n, bool)
            for k, s in enumerate(st[1:], 1):
                ok[k] = (22 * f <= s[4] <= 75 * f and s[4] / max(1, s[2] * s[3]) >= 0.5
                         and max(s[2], s[3]) <= 13 * lin)
            # der dunkle Rand zwischen zwei Vasallen ist 1-2 px breit: um 3 px geweitet
            rund[team] = cv2.dilate(ok[marken].astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
        for team, maske in (("blau", blau), ("rot", rot)):
            maske = maske.copy()
            maske[(statisch > 0) | (icons > 0)] = 0
            andere = rund["rot" if team == "blau" else "blau"]
            # Pulks: Vasallen uebereinander (Carlos, 30.09.: "ein Vasall ist immer derselbe Kreis - aus der Anomalie
            # erkennt man, wie viele da liegen"). Erst die sichtbaren (helle Kreise), dann die Schablone eines ganzen
            # Vasallen um jeden legen: was von der Silhouette darueber hinausragt, ist ein weiterer, verdeckter Vasall.
            belegt = np.zeros(maske.shape, bool)
            sil = silhouette[team].copy()
            sil[(statisch > 0) | (icons > 0)] = 0
            n2, marken2, st2, _ = cv2.connectedComponentsWithStats(sil)
            for k, s in enumerate(st2[1:], 1):
                x0, y0, bw, bh = s[0], s[1], s[2], s[3]
                if not (PULK_FLAECHE[0] * f < s[4] <= PULK_FLAECHE[1] * f and s[4] / max(1, bw * bh) >= PULK_FUELL
                        and max(bw, bh) <= PULK_KANTE * lin):
                    continue
                if team == "rot" and _mit_knochen(hsv, s, team, f):
                    continue
                teil = (marken2[y0:y0 + bh, x0:x0 + bw] == k).astype(np.uint8)
                if _loch(teil) >= LOCH_AB * f:
                    continue      # hohl (Ping-Raute, Ward-Symbol)
                hell = teil & (maske[y0:y0 + bh, x0:x0 + bw] > 0)
                mitten = _buckel(hell, lin)
                if not mitten:
                    continue
                modell = np.zeros_like(teil)
                for px, py in mitten:
                    cv2.circle(modell, (int(round(px)), int(round(py))), int(round(SCHABLONE_R * lin)), 1, -1)
                n3, _, st3, cen3 = cv2.connectedComponentsWithStats(teil & (1 - modell))
                for s3, (qx, qy) in zip(st3[1:], cen3[1:]):
                    if s3[4] >= UEBERSTAND_AB * f:
                        mitten.append((float(qx), float(qy)))
                for px, py in mitten:
                    aus.append((team, float((x0 + px) / seite), float((y0 + py) / seite)))
                belegt[y0:y0 + bh, x0:x0 + bw] |= teil > 0
            n, marken, st, cen = cv2.connectedComponentsWithStats(maske)
            stuecke: list[tuple[float, float]] = []
            for k, (s, (cx, cy)) in enumerate(zip(st[1:], cen[1:]), 1):
                flaeche, fuell = s[4], s[4] / max(1, s[2] * s[3])
                x0, y0, bw, bh = s[0], s[1], s[2], s[3]
                if belegt[int(cy), int(cx)] or belegt[y0:y0 + bh, x0:x0 + bw][marken[y0:y0 + bh, x0:x0 + bw] == k].any():
                    continue      # schon im Pulk gezaehlt
                if not (SCHNITT_FLAECHE * f <= flaeche <= 75 * f and max(s[2], s[3]) <= 13 * seite / REF):
                    continue
                teil = marken[y0:y0 + bh, x0:x0 + bw] == k
                # halb unter einem Vasallen der anderen Farbe (Wellen im Kampf): ein angeschnittener Kreis
                # klein muss es sein: Bogenstuecke eines Champion-Rings liegen auch an der anderen Farbe, sind aber lang
                # - ein angeschnittener Vasall (Halbmond) ist hoechstens so gross wie ein ganzer
                verdeckt = (bool((andere[y0:y0 + bh, x0:x0 + bw] & teil).any()) and fuell >= PULK_FUELL
                            and max(bw, bh) <= HALBMOND_KANTE * lin)
                if fuell < 0.5 and not verdeckt:
                    continue
                if flaeche < 22 * f:
                    if not ((linie[y0:y0 + bh, x0:x0 + bw] & teil).any() or verdeckt):
                        continue
                    # zwei Haelften DESSELBEN Vasallen (je eine Seite der Linie) zaehlen einmal
                    nah = 7 * seite / REF
                    if any((cx - a) ** 2 + (cy - b) ** 2 <= nah * nah for a, b in stuecke):
                        continue
                    stuecke.append((cx, cy))
                if team == "rot" and _mit_knochen(hsv, s, team, f):   # nur Rot: Flussblau waere "dunkel"
                    continue
                aus.append((team, float(cx / seite), float(cy / seite)))
        return aus

    @property
    def bereit(self) -> bool:
        """Erst nach ~20 Bildern ist die Icon-Maske gelernt."""
        return self.bilder >= 20


FRONT_LUECKE = 0.06           # Rueckfall fuer [welle] front_luecke


def _gruppen(punkte: list[tuple[str, float]], luecke: float) -> list[list[tuple[str, float]]]:
    """(team, s) entlang der Lane in Gruppen: eine Luecke > `luecke` trennt."""
    aus: list[list[tuple[str, float]]] = []
    for p in sorted(punkte, key=lambda q: q[1]):
        if aus and p[1] - aus[-1][-1][1] <= luecke:
            aus[-1].append(p)
        else:
            aus.append([p])
    return aus


def _front(punkte: list[tuple[str, float]], luecke: float) -> tuple:
    """F1: (vorn_blau, vorn_rot, naechste_blau, naechste_rot) - s aufsteigend, blau schiebt zu s = 1."""
    gruppen = _gruppen(punkte, luecke)
    farben = [{t for t, _ in g} for g in gruppen]
    gemischt = [i for i, f in enumerate(farben) if len(f) == 2]
    if gemischt:
        i = max(gemischt, key=lambda k: len(gruppen[k]))
        vb = [s for t, s in gruppen[i] if t == "blau"]
        vr = [s for t, s in gruppen[i] if t == "rot"]
        hinter_b = [g for g, f in zip(gruppen[:i], farben[:i]) if f == {"blau"}]
        hinter_r = [g for g, f in zip(gruppen[i + 1:], farben[i + 1:]) if f == {"rot"}]
    else:
        blaue = [g for g, f in zip(gruppen, farben) if f == {"blau"}]
        rote = [g for g, f in zip(gruppen, farben) if f == {"rot"}]
        vb = [s for _, s in blaue[-1]] if blaue else []
        vr = [s for _, s in rote[0]] if rote else []
        hinter_b, hinter_r = blaue[:-1], rote[1:]
    nb = round(float(max(s for _, s in hinter_b[-1])), 3) if hinter_b else None
    nr = round(float(min(s for _, s in hinter_r[0])), 3) if hinter_r else None
    return (tuple(round(float(s), 3) for s in sorted(vb)), tuple(round(float(s), 3) for s in sorted(vr)), nb, nr)


def zustaende(punkte: list[tuple[str, float, float]], mein_team: str = "ORDER",
              luecke: float | None = None) -> dict[str, LaneZustand]:
    """Je Lane der Wellenstand. Die Minimap faerbt RELATIV: dein Team ist blau, der Gegner rot - egal auf welcher
    Seite. `blau`/`rot` im Ergebnis heissen aber Team ORDER / CHAOS (blaue Basis unten links, s = 0), wie ueberall
    im Coach; auf der roten Seite werden die Farben deshalb getauscht (echte Partie 140253, Riven Mid auf CHAOS: die
    eigenen Vasallen galten als seine, die Front lief falsch herum)."""
    if mein_team == "CHAOS":
        punkte = [("rot" if farbe == "blau" else "blau", x, y) for farbe, x, y in punkte]
    if luecke is None:
        try:
            from .kern import konfig
            luecke = float(konfig()["welle"].get("front_luecke", FRONT_LUECKE))
        except Exception:
            luecke = FRONT_LUECKE
    je_lane: dict[str, list[tuple[str, float]]] = {l: [] for l in LANES}
    for team, x, y in punkte:
        # Basen (unten links / oben rechts) zaehlen nicht: dort liegen Nexus-/Inhibitor-Icons
        # (gemessen an Partie 3, Bild 900: "Bot: eure 1 ... tief bei deinem Turm" aus der Basis)
        if (x < 0.24 and y > 0.76) or (x > 0.76 and y < 0.24):
            continue
        if pr := _projektion(x, y):
            je_lane[pr[0]].append((team, pr[1]))
    aus = {}
    for lane, t in je_lane.items():
        b, r, nb, nr = _front(t, luecke)
        if b and r:
            front = (b[-1] + r[0]) / 2 if b[-1] <= r[0] + 0.05 else (b[-1] + r[0]) / 2
            schiebt = "blau" if len(b) >= len(r) + 2 else "rot" if len(r) >= len(b) + 2 else None
        elif b:
            front, schiebt = b[-1], "blau"
        elif r:
            front, schiebt = r[0], "rot"
        else:
            front, schiebt = None, None
        aus[lane] = LaneZustand(lane, len(b), len(r), None if front is None else round(front, 3), schiebt,
                                b, r, nb, nr, sum(x[0] == "blau" for x in t), sum(x[0] == "rot" for x in t),
                                tuple(round(x[1], 3) for x in t if x[0] == "blau"),
                                tuple(round(x[1], 3) for x in t if x[0] == "rot"))
    return aus


LANE_DER_ROLLE = {"TOP": "Top", "MIDDLE": "Mid", "BOTTOM": "Bot", "UTILITY": "Bot"}
