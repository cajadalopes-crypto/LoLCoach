"""Stimmproben fuer die Stimmwahl: dieselben 8 Coach-Saetze je Stimme und Tempo als eine mp3.

Carlos (27.09.): der Coach rede zu langsam, Champion- und Item-Namen klaengen deutsch. Deshalb die heutige
Stimme (Killian, Text wie der Coach ihn heute spricht: stimme.sprechbar samt deutscher Lautschrift aus
AUSSPRACHE) gegen die mehrsprachigen deutschen Stimmen (Namen im Original: nur die _SPRECHBAR-Regeln).
Zwei Tempi: normal = +25 % (heute), schnell = +50 % (heute plus 20 %).

Jeder Satz wird einzeln synthetisiert wie eine Ansage im Coach; die mp3 haengt die acht Stuecke aneinander.
Dauer aus dem dekodierten Audio (PyAV); "netto" ohne die Stille am Anfang und Ende jedes Satzes.

    python werkzeuge/stimmproben.py
"""
import asyncio
import io
import sys
from pathlib import Path

import av
import edge_tts
import numpy as np

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.stdout.reconfigure(encoding="utf-8")
from lolcoach import stimme  # noqa: E402

ZIEL = WURZEL / "aufnahmen" / "stimmproben"
HEUTE = "de-DE-KillianNeural"
FEST = [HEUTE, "de-DE-FlorianMultilingualNeural", "de-DE-SeraphinaMultilingualNeural"]
TEMPI = {"normal": "+25%", "schnell": "+50%"}
STILLE = 0.01   # Betrag unter dem eine Probe als Stille zaehlt (fuer "netto")

SAETZE = [
    "Raus, zum Turm: Xin Zhao und Rumble kommen.",
    "Ziggs ohne Flash.",
    "Kauf Gefräßige Hydra, dann Top-Welle.",
    "Back jetzt: dreitausend Gold für Eklipse.",
    "Caitlyn und Sona ohne Flash, geh rein.",
    "Kai'Sa hat Schutzengel, Cho'Gath steht vorne.",
    "Wukong baut Tanz des Todes, du kaufst Axiombogen.",
    "Du stehst sechs null, ihr führt sieben zu drei.",
]


def nur_regeln(text: str) -> str:
    """sprechbar ohne AUSSPRACHE: Namen bleiben im Original."""
    for muster, ersatz in stimme._SPRECHBAR:
        text = muster.sub(ersatz, text)
    return text


def text_fuer(name: str, satz: str) -> str:
    return stimme.sprechbar(satz) if name == HEUTE else nur_regeln(satz)


def dekodiere(mp3: bytes) -> tuple[np.ndarray, int]:
    teile, rate = [], 24000
    with av.open(io.BytesIO(mp3)) as f:
        for rahmen in f.decode(audio=0):
            a = rahmen.to_ndarray()
            a = a[0] if a.ndim == 2 else a
            teile.append(a.astype(np.float32) / 32768.0 if a.dtype.kind == "i" else a.astype(np.float32))
            rate = rahmen.sample_rate
    return (np.concatenate(teile) if teile else np.zeros(0, np.float32)), rate


async def synthese(text: str, name: str, tempo: str, grenze: asyncio.Semaphore) -> bytes:
    async with grenze:
        for versuch in range(3):
            try:
                daten = bytearray()
                async for teil in edge_tts.Communicate(text, name, rate=tempo).stream():
                    if teil["type"] == "audio":
                        daten += teil["data"]
                if daten:
                    return bytes(daten)
                raise RuntimeError("kein Audio")
            except Exception:  # noqa: BLE001 - Dienst wackelt: zweimal nachfassen, dann melden
                if versuch == 2:
                    raise
                await asyncio.sleep(1.0)


async def probe(name: str, tempo_name: str, grenze) -> dict:
    tempo = TEMPI[tempo_name]
    texte = [text_fuer(name, s) for s in SAETZE]
    datei = ZIEL / f"{name}_{tempo_name}.mp3"
    try:
        stuecke = await asyncio.gather(*(synthese(t, name, tempo, grenze) for t in texte))
    except Exception as e:  # noqa: BLE001
        return {"name": name, "tempo": tempo_name, "fehler": f"{type(e).__name__}: {e}"}
    brutto = netto = 0.0
    for mp3 in stuecke:
        a, rate = dekodiere(mp3)
        brutto += len(a) / rate
        laut = np.flatnonzero(np.abs(a) > STILLE)
        netto += (laut[-1] - laut[0] + 1) / rate if len(laut) else 0.0
    datei.write_bytes(b"".join(stuecke))
    zeichen = sum(len(t) for t in texte)
    return {"name": name, "tempo": tempo_name, "datei": datei.name, "brutto": brutto, "netto": netto,
            "zeichen": zeichen, "texte": texte}


async def haupt() -> None:
    ZIEL.mkdir(parents=True, exist_ok=True)
    angebot = await edge_tts.list_voices()
    mehrsprachig = sorted(v["ShortName"] for v in angebot
                          if v["Locale"].startswith("de-") and "Multilingual" in v["ShortName"])
    angeboten = {v["ShortName"] for v in angebot}
    namen = FEST + [n for n in mehrsprachig if n not in FEST]
    print("mehrsprachig deutsch im Angebot:", ", ".join(mehrsprachig) or "keine")
    for n in namen:
        if n not in angeboten:
            print(f"  {n}: nicht in list_voices() - versuche trotzdem")
    grenze = asyncio.Semaphore(8)
    ergebnisse = await asyncio.gather(*(probe(n, t, grenze) for n in namen for t in TEMPI))
    schreibe_liesmich(ergebnisse, mehrsprachig)
    for e in ergebnisse:
        if "fehler" in e:
            print(f"{e['name']} {e['tempo']}: FEHLER {e['fehler']}")
        else:
            print(f"{e['datei']}: {e['brutto']:.1f} s, {e['zeichen']} Zeichen, "
                  f"{e['zeichen'] / e['brutto']:.1f} Z/s (netto {e['zeichen'] / e['netto']:.1f} Z/s)")


def schreibe_liesmich(ergebnisse: list[dict], mehrsprachig: list[str]) -> None:
    z = (["# Stimmproben", "",
         "Erzeugt von `werkzeuge/stimmproben.py`. Jede mp3 enthaelt dieselben 8 Saetze, jeder einzeln synthetisiert",
         "(wie eine Ansage im Coach) und aneinandergehaengt.", "",
         f"- `{HEUTE}` (heute) bekommt den Text wie der Coach: `stimme.sprechbar` mit deutscher Lautschrift"
         " aus `AUSSPRACHE`.",
         "- Die mehrsprachigen Stimmen bekommen die Namen im Original (nur die `_SPRECHBAR`-Regeln).",
         f"- Tempi: `normal` = {TEMPI['normal']} (heute), `schnell` = {TEMPI['schnell']} (heute plus 20 %).",
         f"- Mehrsprachige deutsche Stimmen laut `edge_tts.list_voices()`: {', '.join(mehrsprachig) or 'keine'}.",
         "", "## Die 8 Saetze", "",
         "| # | Satz (Original, mehrsprachige Stimmen) | Killian bekommt |", "|---|---|---|"]
        + [f"| {i} | {s} | {stimme.sprechbar(s)} |" for i, s in enumerate(SAETZE, 1)]
        + ["", "## Dateien", "",
           "Zeichen/s = Zeichen des gesendeten Textes (alle 8 Saetze) / Sekunden. Brutto = ganze Audiodauer,",
           f"netto = ohne Stille (Betrag < {STILLE}) am Anfang und Ende jedes Satzes.", "",
           "| Datei | Dauer brutto | Dauer netto | Zeichen | Zeichen/s brutto | Zeichen/s netto |",
           "|---|---|---|---|---|---|"])
    for e in ergebnisse:
        if "fehler" in e:
            z.append(f"| {e['name']}_{e['tempo']}.mp3 | FEHLER: {e['fehler']} | | | | |")
        else:
            z.append(f"| `{e['datei']}` | {e['brutto']:.1f} s | {e['netto']:.1f} s | {e['zeichen']} | "
                     f"{e['zeichen'] / e['brutto']:.1f} | {e['zeichen'] / e['netto']:.1f} |")
    (ZIEL / "LIESMICH.md").write_text("\n".join(z) + "\n", encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(haupt())
