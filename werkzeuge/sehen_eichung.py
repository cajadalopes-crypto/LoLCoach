"""Auftrag 033: Wahrnehmung eichen - Bildtafeln zum Beschriften und Messen der neuen Leser.

Nur fuers SEHEN (Buch 17, harte Regel): Carlos' Aufnahmen liefern hier Bilder und Zeiten, kein Entscheidungswissen.

    python werkzeuge/sehen_eichung.py tafel <art> [--n 20] [--seite 0]   Bildtafel nach buecher/challenger/sehen/
    python werkzeuge/sehen_eichung.py messen [<art> ...]                  Leser gegen die Beschriftung

Beschriftungen: buecher/challenger/sehen/<art>.json (von Hand, je Stichprobe "wahr").
"""
from __future__ import annotations

import gzip
import json
import random
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL))
AUFNAHMEN = WURZEL / "aufnahmen"
ABLAGE = WURZEL / "buecher" / "challenger" / "sehen"


# ---------------------------------------------------------------- Aufnahmen und Zeiten

def aufnahmen_mit_bildern() -> list[str]:
    """Stamm aller Aufnahmen mit Minimap-Bildern (Dateiname = Wandzeit in ms)."""
    out = []
    for d in sorted(AUFNAHMEN.glob("*_bilder")):
        if any(p.stem.isdigit() for p in d.glob("*.jpg")):
            out.append(d.name.removesuffix("_bilder"))
    return out


def minimaps(stamm: str) -> list[tuple[float, Path]]:
    d = AUFNAHMEN / f"{stamm}_bilder"
    return sorted((int(p.stem) / 1000, p) for p in d.glob("*.jpg") if p.stem.isdigit())


def schirme(stamm: str) -> list[tuple[float, Path]]:
    d = AUFNAHMEN / f"{stamm}_bilder"
    return sorted((int(p.stem.split("_")[1]) / 1000, p) for p in d.glob("schirm_*.jpg"))


@lru_cache(maxsize=32)
def api(stamm: str) -> list[tuple[float, dict]]:
    """(Wandzeit, Live-API-Schnappschuss) jede Sekunde."""
    for endung in (".jsonl.gz", ".jsonl.xz"):
        p = AUFNAHMEN / f"{stamm}{endung}"
        if p.exists():
            import lzma
            oeffne = gzip.open if endung.endswith("gz") else lzma.open
            out = []
            with oeffne(p, "rt", encoding="utf-8") as fh:
                for zeile in fh:
                    try:
                        r = json.loads(zeile)
                    except json.JSONDecodeError:
                        continue
                    if "d" in r and r["d"].get("gameData"):
                        out.append((r["w"], r["d"]))
            return out
    return []


def spielzeit(stamm: str, wand: float) -> float | None:
    a = api(stamm)
    if not a:
        return None
    ws = np.array([w for w, _ in a])
    i = int(np.clip(np.searchsorted(ws, wand), 1, len(ws) - 1))
    j = i if abs(ws[i] - wand) < abs(ws[i - 1] - wand) else i - 1
    return a[j][1]["gameData"]["gameTime"] + (wand - ws[j])


def schnappschuss(stamm: str, wand: float) -> dict | None:
    a = api(stamm)
    if not a:
        return None
    ws = np.array([w for w, _ in a])
    i = int(np.clip(np.searchsorted(ws, wand), 0, len(ws) - 1))
    return a[i][1]


def mein_team(stamm: str) -> str | None:
    a = api(stamm)
    if not a:
        return None
    d = a[len(a) // 2][1]
    ich = d["activePlayer"].get("riotId") or d["activePlayer"].get("summonerName")
    for p in d["allPlayers"]:
        if ich and ich in (p.get("riotId"), p.get("summonerName")):
            return p["team"]
    return None


# ---------------------------------------------------------------- Bildtafeln

def tafel(bilder: list[tuple[str, Image.Image]], pfad: Path, spalten: int = 5, kante: int = 300) -> None:
    zeilen = (len(bilder) + spalten - 1) // spalten
    t = Image.new("RGB", (spalten * kante, zeilen * (kante + 22)), "white")
    d = ImageDraw.Draw(t)
    for k, (titel, im) in enumerate(bilder):
        x, y = (k % spalten) * kante, (k // spalten) * (kante + 22)
        t.paste(im.resize((kante, round(kante * im.size[1] / im.size[0]))), (x, y + 22))
        d.text((x + 4, y + 4), titel, fill="black")
    pfad.parent.mkdir(parents=True, exist_ok=True)
    t.save(pfad)


def uhr(t: float | None) -> str:
    if t is None:
        return "?"
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def stichprobe(n: int, quelle: str = "minimap", seed: int = 33, ab: float = 90, bis: float = 2400,
               stamm_filter=None) -> list[tuple[str, float, Path]]:
    """n zufaellige Bilder (Stamm, Wandzeit, Pfad) aus allen Aufnahmen, gleich verteilt ueber die Aufnahmen."""
    rnd = random.Random(seed)
    staemme = [s for s in aufnahmen_mit_bildern() if api(s) and (stamm_filter is None or stamm_filter(s))]
    out = []
    while len(out) < n and staemme:
        s = rnd.choice(staemme)
        liste = minimaps(s) if quelle == "minimap" else schirme(s)
        liste = [(w, p) for w, p in liste if (z := spielzeit(s, w)) is not None and ab <= z <= bis]
        if liste:
            w, p = rnd.choice(liste)
            out.append((s, w, p))
    return out


@lru_cache(maxsize=16)
def _sichtungen(stamm: str) -> list[tuple[float, list]]:
    p = AUFNAHMEN / f"{stamm}_bilder" / "sichtungen.jsonl.gz"
    out = []
    try:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            for zeile in fh:
                try:
                    r = json.loads(zeile)
                except json.JSONDecodeError:
                    continue
                out.append((r["w"], r["s"]))
    except (EOFError, OSError):      # abgebrochene Aufnahme: was bis dahin da ist, reicht
        pass
    return out


def champion_punkte(stamm: str, wand: float) -> list[tuple[float, float]]:
    """Icon-Mitten (Anteile) der naechstgelegenen Sichtung vor dem Bild."""
    s = _sichtungen(stamm)
    if not s:
        return []
    ws = np.array([w for w, _ in s])
    i = int(np.clip(np.searchsorted(ws, wand) - 1, 0, len(ws) - 1))
    return [(e[2], e[3]) for e in s[i][1]]


def lade_bgr(p: Path):
    import cv2
    return cv2.imread(str(p))


def markiert(p: Path, punkte: list[tuple[float, float]], farbe=(0, 255, 0), r: float = 0.03) -> Image.Image:
    im = Image.open(p).convert("RGB")
    d = ImageDraw.Draw(im)
    b = im.size[0]
    for x, y in punkte:
        d.ellipse(((x - r) * b, (y - r) * b, (x + r) * b, (y + r) * b), outline=farbe, width=3)
    return im


def label_datei(art: str) -> Path:
    return ABLAGE / f"{art}.json"


def labels(art: str) -> dict:
    p = label_datei(art)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


# ---------------------------------------------------------------- Wards

def ward_proben(n: int = 72, seed: int = 3303) -> list[dict]:
    """Zufaellige Minimaps ab 1:30 Spielzeit; je Bild die Funde des Lesers. Beschriftet wird auf der ganzen Karte:
    jeder Fund echt/falsch (Fehlalarme), jedes echte Ward gefunden/uebersehen (Treffer)."""
    from lolcoach import sehen
    return [{"stamm": s, "w": w, "pfad": str(p), "zeit": round(spielzeit(s, w)),
             "leser": [(o.x, o.y, o.art, o.guete) for o in sehen.wards(lade_bgr(p))]}
            for s, w, p in stichprobe(n, seed=seed)]


WARD_FARBE = {"hell": (0, 255, 0), "matt": (255, 220, 0), "kontrolle": (255, 0, 255), "blass": (0, 255, 255)}


def ward_tafeln(proben: list[dict], ordner: Path, je: int = 6) -> None:
    """Ganze Minimaps, Funde eingekreist (gruen eigen, gelb Team, magenta Kontrollauge), Nummer B<i>.<j> daneben."""
    for k in range(0, len(proben), je):
        bilder = []
        for i, e in enumerate(proben[k:k + je], k):
            im = Image.open(e["pfad"]).convert("RGB").resize((570, 570))
            d = ImageDraw.Draw(im)
            for j, (x, y, art, _) in enumerate(e["leser"]):
                d.ellipse(((x - 0.025) * 570, (y - 0.025) * 570, (x + 0.025) * 570, (y + 0.025) * 570),
                          outline=WARD_FARBE[art], width=2)
                d.text((x * 570 + 16, y * 570 - 6), str(j), fill=WARD_FARBE[art])
            bilder.append((f"B{i} {uhr(e['zeit'])} Funde {len(e['leser'])}", im))
        tafel(bilder, ordner / f"wards_{k // je}.png", spalten=3, kante=570)


# ---------------------------------------------------------------- Trinket

def eigenes_trinket(stamm: str, wand: float) -> int | None:
    """Item-ID des eigenen Trinkets laut Live-API (3340 gelb, 3364 Linse, 3363 blau)."""
    d = schnappschuss(stamm, wand)
    if not d:
        return None
    rid = d["activePlayer"].get("riotId")
    for p in d["allPlayers"]:
        if p.get("riotId") == rid:
            return next((it["itemID"] for it in p["items"] if it["itemID"] in (3340, 3363, 3364)), None)
    return None


def trinket_proben(n: int = 80, seed: int = 3310) -> list[dict]:
    """Zufaellige Schirmbilder mit gelbem Trinket (Live-API); je Bild die Lesung des Trinket-Lesers."""
    from lolcoach import sehen
    out = []
    for s, w, p in stichprobe(4 * n, quelle="schirm", seed=seed):
        if len(out) >= n:
            break
        if eigenes_trinket(s, w) != 3340:
            continue
        out.append({"stamm": s, "w": w, "pfad": str(p), "zeit": round(spielzeit(s, w)),
                    "leser": sehen.trinket(lade_bgr(p))})
    return out


def trinket_tafel(proben: list[dict], pfad: Path) -> None:
    from lolcoach import sehen
    bilder = []
    for i, e in enumerate(proben):
        im = Image.open(e["pfad"]).convert("RGB")
        x0, y0, x1, y1 = sehen.trinket_feld(im.size[0], im.size[1])
        bilder.append((f"T{i} {e['leser']}", im.crop((x0 - 6, y0 - 6, x1 + 6, y1 + 6))))
    tafel(bilder, pfad, spalten=10, kante=150)


# ---------------------------------------------------------------- Wellen aller Lanes

def _lane_punkt(lane: str, s: float) -> tuple[float, float]:
    from lolcoach.welle import LANES
    pk = LANES[lane]
    laengen = [float(np.hypot(b[0] - a[0], b[1] - a[1])) for a, b in zip(pk, pk[1:])]
    ziel, bis = s * sum(laengen), 0.0
    for (a, b), l in zip(zip(pk, pk[1:]), laengen):
        if bis + l >= ziel:
            t = (ziel - bis) / l
            return a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
        bis += l
    return pk[-1]


def welle_proben(n: int = 60, seed: int = 3320, vorlauf: int = 40) -> list[dict]:
    """Zufaellige Minimaps; der Wellenleser wird mit den `vorlauf` Bildern davor aufgewaermt (Icon-Maske)."""
    from lolcoach import welle
    out = []
    for s, w, p in stichprobe(n, seed=seed):
        team = mein_team(s) or "ORDER"
        ms = minimaps(s)
        k = next(i for i, (w2, _) in enumerate(ms) if w2 == w)
        leser = welle.Wellenleser()
        punkte = []
        for w2, p2 in ms[max(0, k - vorlauf):k + 1]:
            punkte = leser.punkte(lade_bgr(p2), champion_punkte(s, w2))
        z = welle.zustaende(punkte, team) if leser.bereit else {}
        out.append({"stamm": s, "w": w, "pfad": str(p), "zeit": round(spielzeit(s, w)), "team": team,
                    "punkte": [[f, round(x, 4), round(y, 4)] for f, x, y in punkte] if leser.bereit else None,
                    "lanes": {l: {"stand": zz.stand(team), "front": zz.front, "blau": zz.blau, "rot": zz.rot}
                              for l, zz in z.items()}})
    return out


def welle_tafeln(proben: list[dict], ordner: Path, je: int = 6) -> None:
    """Ganze Minimaps; je Lane ein Strich an der gelesenen Front und der Stand als Text."""
    kurz = {"bei_uns": "UNS", "mitte": "MIT", "bei_ihnen": "IHN", None: "-"}
    for k in range(0, len(proben), je):
        bilder = []
        for i, e in enumerate(proben[k:k + je], k):
            im = Image.open(e["pfad"]).convert("RGB").resize((570, 570))
            d = ImageDraw.Draw(im)
            zeile = []
            for lane, z in e["lanes"].items():
                zeile.append(f"{lane[0]}:{kurz[z['stand']]}")
                if z["front"] is not None:
                    x, y = _lane_punkt(lane, z["front"])
                    d.ellipse(((x - 0.02) * 570, (y - 0.02) * 570, (x + 0.02) * 570, (y + 0.02) * 570),
                              outline=(255, 255, 0), width=3)
                    d.text((x * 570 + 14, y * 570 + 6), lane[0], fill=(255, 255, 0))
            team = "blau" if e["team"] == "ORDER" else "ROT"
            bilder.append((f"W{i} {uhr(e['zeit'])} {team} " + " ".join(zeile), im))
        tafel(bilder, ordner / f"wellen_{k // je}.png", spalten=3, kante=570)


def welle_uns_tafeln(proben: list[dict], ordner: Path, je: int = 6) -> None:
    """Fuer die Frage "Gegnerwelle auf eurer Haelfte?": die gegnerische Haelfte abgedunkelt, jeder gelesene
    gegnerische Vasall gelb umrandet, im Titel die Lanes, die der Leser "bei_uns" nennt."""
    from lolcoach import welle
    for k in range(0, len(proben), je):
        bilder = []
        for i, e in enumerate(proben[k:k + je], k):
            im = Image.open(e["pfad"]).convert("RGB").resize((570, 570))
            maske = Image.new("L", (570, 570), 0)
            dm = ImageDraw.Draw(maske)
            # gegnerische Haelfte: oben rechts fuer ORDER, unten links fuer CHAOS (Diagonale)
            ecke = [(0, 0), (570, 0), (570, 570)] if e["team"] == "ORDER" else [(0, 0), (0, 570), (570, 570)]
            dm.polygon(ecke, fill=110)
            im.paste(Image.new("RGB", (570, 570), (0, 0, 0)), (0, 0), maske)
            d = ImageDraw.Draw(im)
            for f, x, y in e["punkte"] or []:
                if f == "rot":
                    d.rectangle((x * 570 - 6, y * 570 - 6, x * 570 + 6, y * 570 + 6), outline=(255, 255, 0))
            z = welle.zustaende([tuple(q) for q in e["punkte"] or []], e["team"])
            uns = [l for l, zz in z.items() if zz.stand(e["team"]) == "bei_uns"]
            bilder.append((f"W{i} {uhr(e['zeit'])} bei_uns: {' '.join(uns) or '-'}", im))
        tafel(bilder, ordner / f"uns_{k // je}.png", spalten=3, kante=570)


# Die eigene Haelfte der Seitenlanes als Streifen (Anteile x0, y0, x1, y1), mit Basis - fuer W11/W14/M6 zaehlen nur
# Top und Bot. Fuer CHAOS gespiegelt.
STREIFEN_ORDER = {"Top": (0.0, 0.25, 0.2, 1.0), "Bot": (0.0, 0.8, 0.75, 1.0)}


def welle_streifen(proben: list[dict], ordner: Path, je: int = 20) -> None:
    """Je Probe die eigene Haelfte von Top und Bot als Streifen; gelesene gegnerische Vasallen gelb umrandet, im
    Titel, ob der Leser dort "bei_uns" sagt."""
    from lolcoach import welle
    for k in range(0, len(proben), je):
        zeilen = []
        for i, e in enumerate(proben[k:k + je], k):
            im = Image.open(e["pfad"]).convert("RGB").resize((570, 570))
            if e["team"] == "CHAOS":
                im = im.rotate(180)
            d = ImageDraw.Draw(im)
            for f, x, y in e["punkte"] or []:
                if f == "rot":
                    if e["team"] == "CHAOS":
                        x, y = 1 - x, 1 - y
                    d.rectangle((x * 570 - 6, y * 570 - 6, x * 570 + 6, y * 570 + 6), outline=(255, 255, 0))
            z = welle.zustaende([tuple(q) for q in e["punkte"] or []], e["team"])
            teile = []
            for lane in ("Top", "Bot"):
                x0, y0, x1, y1 = STREIFEN_ORDER[lane]
                # CHAOS: gedreht, also ist Top (fuer ihn) jetzt unten - die eigene Seite liegt immer unten links
                l2 = lane if e["team"] == "ORDER" else ("Bot" if lane == "Top" else "Top")
                x0, y0, x1, y1 = STREIFEN_ORDER[l2]
                st = im.crop((int(x0 * 570), int(y0 * 570), int(x1 * 570), int(y1 * 570)))
                if l2 == "Top":
                    st = st.rotate(90, expand=True)
                teile.append((lane, z[lane].stand(e["team"]) if lane in z else None, st))
            zeilen.append((i, e, teile))
        H = 114 + 20
        t = Image.new("RGB", (2 * 440, len(zeilen) * H), "white")
        d = ImageDraw.Draw(t)
        for r, (i, e, teile) in enumerate(zeilen):
            for c, (lane, st, bild) in enumerate(teile):
                t.paste(bild.resize((428, 114)), (c * 440, r * H + 18))
                d.text((c * 440 + 2, r * H + 3), f"W{i} {uhr(e['zeit'])} {lane}: {st}", fill="black")
        t.save(ordner / f"streifen_{k // je}.png")


if __name__ == "__main__":
    print(aufnahmen_mit_bildern())
