"""Flash-Pruefstand: synthetische Minimap mit 15 Bildern/s, bekannte Bewegungen.

Warum: die Flash-Erkennung (minimap.Verfolger) ist an echten 15-Bilder/s-Daten noch
nicht gemessen - Aufnahmen gibt es nur mit 1 Bild/s. Hier laufen echte Champion-Portraets
(Data Dragon, wie auf der Minimap: rund, farbiger Ring) ueber die echte Kartenzeichnung,
mit Bewegungen, deren Wahrheit bekannt ist:
  - laufen (350 Einheiten/s), stehen,
  - Flash (400 Einheiten sofort),
  - Dashes: Riven E (250 in 0,15 s), Riven Q x3 (je 225 in 0,25 s), Vi Q (725 in 0,5 s),
    Lee Sin Q2 (1100 in 0,8 s),
  - zwei Icons, die sich ueberdecken und wieder trennen,
  - verlorene Einzelbilder (Takt-Aussetzer).
Gemessen: gefundene Flashes (Treffer), Flash-Meldungen ohne Flash (Fehlalarme).

    python werkzeuge/flash_pruefstand.py
"""
import random
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import ddragon, minimap  # noqa: E402

SEITE = 570
TAKT = 1 / 15
E = SEITE / minimap.KARTE_EINHEITEN          # Pixel je Spiel-Einheit
PORTRAET = 48


def icon(champion_id: str, ring: tuple[int, int, int]) -> tuple[np.ndarray, np.ndarray]:
    bild = minimap._champion_bild(champion_id)
    klein = cv2.resize(bild, (PORTRAET, PORTRAET), interpolation=cv2.INTER_AREA)
    maske = np.zeros((PORTRAET, PORTRAET), np.uint8)
    cv2.circle(maske, (PORTRAET // 2, PORTRAET // 2), PORTRAET // 2 - 1, 255, -1)
    cv2.circle(klein, (PORTRAET // 2, PORTRAET // 2), PORTRAET // 2 - 2, ring, 3)
    return klein, maske


def zeichne(grund: np.ndarray, icons, positionen) -> np.ndarray:
    bild = grund.copy()
    for (ic, ma), (x, y) in zip(icons, positionen):
        if x is None:
            continue
        x0, y0 = int(round(x - PORTRAET / 2)), int(round(y - PORTRAET / 2))
        if x0 < 0 or y0 < 0 or x0 + PORTRAET > SEITE or y0 + PORTRAET > SEITE:
            continue
        bereich = bild[y0:y0 + PORTRAET, x0:x0 + PORTRAET]
        bereich[ma > 0] = ic[ma > 0]
    return bild


class Bahn:
    """Position je Zeitpunkt aus Abschnitten: ('lauf', dauer, richtung), ('steh', dauer),
    ('flash', richtung), ('dash', einheiten, dauer, richtung)."""

    def __init__(self, start, schritte):
        self.punkte = [(0.0, start)]
        t, (x, y) = 0.0, start
        self.flashes = []
        self.weg_ab = None
        for s in schritte:
            if s[0] == "lauf":
                _, dauer, (dx, dy) = s
                n = int(dauer / 0.01)
                for _ in range(n):
                    t += 0.01
                    x += dx * 350 * E * 0.01
                    y += dy * 350 * E * 0.01
                    self.punkte.append((t, (x, y)))
            elif s[0] == "steh":
                t += s[1]
                self.punkte.append((t, (x, y)))
            elif s[0] == "flash":
                dx, dy = s[1]
                t += 0.001
                x += dx * 400 * E
                y += dy * 400 * E
                self.punkte.append((t, (x, y)))
                self.flashes.append(t)
            elif s[0] == "weg":
                # in den Nebel: ab jetzt nicht mehr auf der Karte (bleibt es bis zum Ende)
                t += 0.001
                self.punkte.append((t, (None, None)))
                self.weg_ab = t
                t += s[1]
                self.punkte.append((t, (None, None)))
                continue
            elif s[0] == "zuck":
                # Fehlzuordnung wie Partie 4, 4:16 (Galio): sofort Flash-weit weg, in zwei Bildern zurueck
                dx, dy = s[1]
                for dt, anteil in ((0.001, 1.0), (0.07, -0.15), (0.07, -0.35)):   # gemessen: 5 px, dann halb zurueck
                    t += dt
                    x += dx * 380 * E * anteil
                    y += dy * 380 * E * anteil
                    self.punkte.append((t, (x, y)))
            elif s[0] == "dash":
                _, einheiten, dauer, (dx, dy) = s
                n = max(1, int(dauer / 0.01))
                for _ in range(n):
                    t += dauer / n
                    x += dx * einheiten * E / n
                    y += dy * einheiten * E / n
                    self.punkte.append((t, (x, y)))
        self.ende = t

    def bei(self, t):
        for i in range(len(self.punkte) - 1, -1, -1):
            if self.punkte[i][0] <= t:
                return self.punkte[i][1]
        return self.punkte[0][1]


def szenen():
    r, l, o, u = (1, 0), (-1, 0), (0, -1), (0, 1)
    ro = (0.707, -0.707)
    return {
        "laufen + Flash": [Bahn((150, 300), [("lauf", 2, r), ("flash", r), ("lauf", 2, r)])],
        "stehen + Flash": [Bahn((150, 300), [("steh", 2), ("flash", o), ("steh", 2)])],
        "Riven E": [Bahn((150, 300), [("lauf", 1.5, r), ("dash", 250, 0.15, r), ("lauf", 1.5, r)])],
        "Riven Q x3": [Bahn((150, 300), [("lauf", 1, r), ("dash", 225, 0.25, r), ("steh", 0.3),
                                        ("dash", 225, 0.25, r), ("steh", 0.3), ("dash", 225, 0.25, r),
                                        ("lauf", 1, r)])],
        "Vi Q": [Bahn((150, 300), [("lauf", 1, r), ("dash", 725, 0.5, r), ("lauf", 1, r)])],
        "Lee Sin Q2": [Bahn((120, 300), [("lauf", 1, r), ("dash", 1100, 0.8, r), ("lauf", 1, r)])],
        "E + Flash (Riven)": [Bahn((150, 300), [("lauf", 1, r), ("dash", 250, 0.15, r), ("flash", ro),
                                               ("lauf", 1.5, r)])],
        "Verdeckung": [Bahn((150, 300), [("lauf", 4, r)]), Bahn((330, 300), [("steh", 1), ("lauf", 3, l)])],
        "Fehlzuordnung zurueck": [Bahn((150, 300), [("lauf", 1.5, u), ("zuck", r), ("lauf", 1.5, u)])],
        # Carlos, Partie 5: "wenn sich die Icons ueberdecken, erkennt das Tool nicht, wer alles da ist"
        # - Urgot laeuft unter Vi (die spaeter gezeichnet wird, also oben liegt), bleibt 2 s, laeuft weiter
        "Stapel": [Bahn((90, 300), [("lauf", 5, r), ("steh", 2), ("lauf", 5, r)]),
                   Bahn((90 + 5 * 350 * E, 300), [("steh", 12)])],
        "halb verdeckt": [Bahn((90, 300), [("lauf", 5, r), ("steh", 2), ("lauf", 5, r)]),
                          Bahn((90 + 5 * 350 * E + 24, 300), [("steh", 12)])],
        # Partie 7: Wukong ging 19 px neben Riven in den Nebel und hing danach als Geist an ihr
        # (der im Nebel verschwindet, liegt oben - gezeichnet wird in dieser Reihenfolge)
        "Nebel neben Icon": [Bahn((150 + 19, 300), [("lauf", 8, r)]),
                             Bahn((150, 300), [("lauf", 2, r), ("weg", 6)])],
        "Gruppe mit Flash": [Bahn((200, 250), [("lauf", 1.5, u), ("flash", u), ("lauf", 1.5, u)]),
                             Bahn((230, 260), [("lauf", 3, u)]), Bahn((180, 280), [("lauf", 3, r)])],
    }


def pruefe(ausfall: float = 0.0, rausch: float = 0.0, samen: int = 1, takt: float = TAKT) -> dict:
    random.seed(samen)
    ver = ddragon.version()
    grund = cv2.resize(cv2.imread(str(ddragon.ABLAGE / str(ver) / "map11.png")), (SEITE, SEITE))
    namen = ["Urgot", "Vi", "Brand"]
    ergebnis = {}
    for name, bahnen in szenen().items():
        icons = [icon(namen[i], (60, 60, 230)) for i in range(len(bahnen))]
        champions = [(namen[i], "CHAOS") for i in range(len(bahnen))]
        verfolger = minimap.Verfolger(champions, hoehe=2160)
        ende = max(b.ende for b in bahnen)
        t, gefunden = 0.0, []
        bilder = gesehen = 0          # Sichtbarkeit: Bilder, in denen JEDER Champion am richtigen Ort gemeldet ist
        geister = 0                   # Bilder, in denen ein Champion im Nebel noch gemeldet wird (>0,5 s danach)
        while t <= ende + 0.5:
            t += takt
            if random.random() < ausfall:
                continue  # Takt-Aussetzer: dieses Bild fehlt
            bild = zeichne(grund, icons, [b.bei(t) for b in bahnen])
            # Vasallen laufen immer irgendwo: im echten Spiel ist kaum ein Minimap-Bild pixelgleich
            for k in range(6):
                mx = int(40 + (t * 12 + k * 9) % 480)
                cv2.circle(bild, (mx, 540), 4, (230, 150, 60), -1)
            if rausch:
                bild = np.clip(bild.astype(np.int16) + np.random.normal(0, rausch, bild.shape), 0, 255).astype(np.uint8)
            aus = verfolger.bild(bild, t)
            if aus:
                gefunden += aus[1]
                for i, b in enumerate(bahnen):
                    wx, wy = b.bei(t)
                    if wx is None:
                        if b.weg_ab is not None and t - b.weg_ab > 0.5:
                            geister += any(s.champion_id == namen[i] for s in aus[0])
                        continue
                    bilder += 1
                    gesehen += any(s.champion_id == namen[i] and abs(s.x * SEITE - wx) + abs(s.y * SEITE - wy) <= 14
                                   for s in aus[0])
        wahr = sum(len(b.flashes) for b in bahnen)
        # ein gefundener Sprung zaehlt als Treffer, wenn er hoechstens 0,3 s nach einem echten Flash liegt
        echte = [f for b in bahnen for f in b.flashes]
        treffer = sum(1 for f in echte if any(0 <= s.zeit - f <= 0.3 for s in gefunden))
        fehl = sum(1 for s in gefunden if not any(0 <= s.zeit - f <= 0.3 for f in echte))
        ergebnis[name] = (wahr, treffer, fehl, gesehen / max(1, bilder), geister)
    return ergebnis


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for titel, kw in (("sauber", {}), ("10 % Bildaussetzer", {"ausfall": 0.1}), ("Rauschen", {"rausch": 6.0}),
                      ("60 Bilder/s", {"takt": 1 / 60}), ("60 Bilder/s + Aussetzer", {"takt": 1 / 60, "ausfall": 0.1})):
        erg = pruefe(**kw)
        w = sum(e[0] for e in erg.values())
        tr = sum(e[1] for e in erg.values())
        fa = sum(e[2] for e in erg.values())
        print(f"== {titel}: {tr}/{w} Flashes gefunden, {fa} Fehlalarme")
        for name, (wahr, treffer, fehl, sicht, geister) in erg.items():
            if treffer != wahr or fehl:
                print(f"   {name}: {treffer}/{wahr} gefunden, {fehl} Fehlalarme")
            if name in ("Stapel", "halb verdeckt", "Verdeckung"):
                print(f"   {name}: alle am richtigen Ort in {sicht * 100:.0f} % der Bilder")
            if name == "Nebel neben Icon":
                print(f"   {name}: {geister} Geister-Bilder (im Nebel noch gemeldet)")
