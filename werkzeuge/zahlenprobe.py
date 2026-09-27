"""Zahlenprobe (Auftrag 002, S1 - dieselbe Probe wie E8): jede Satzvorlage mit Zahl durch die echte Stimme (edge-tts)
und mit Whisper zurueck. Zeigt je Vorlage: Text, was die Stimme bekommt (`stimme.sprechbar`), was Whisper hoert.

Die Vorlagen kommen aus den gespeicherten Live-Ansagen (`aufnahmen/*_ansagen.json`, auch Claude-Antworten): je
Zahl-Umfeld ("N Gold", "N Prozent", "N/N", Uhrzeit ...) das erste Beispiel. Dazu feste Faelle aus Carlos' Partie
213624 (11:12: "3000" kam als "drei null null null"; 7:00: "6/0").

    python werkzeuge/zahlenprobe.py [--stimme de-DE-KillianNeural] [--tempo +25%] [--nur 12]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.stdout.reconfigure(encoding="utf-8")
from lolcoach import stimme  # noqa: E402

FEST = [
    "Genau, das war dein Vorsprung von 3100 Gold in Items, ein klarer Free-Kill mit 3000 Gold Vorsprung.",
    "Dein Team steht gut, alle Lanes sind kill-los bis auf dich mit 6/0 oben.",
    "Ihr steht 7/3, Rumble ist 0/6/1.",
    "Back jetzt: 23 Prozent Leben, 850 Gold für Axiombogen.",
    "Kanone kommt 21 07: die noch rein, dann back. 3550 Gold für Gefräßige Hydra.",
    "Nexus-Turm jetzt: 5 von ihnen sind noch 16 Sekunden tot. Ruf dein Team.",
    "Drache in 1:30, Baron um 20:00.",
    "Noch 7 Sekunden: Dann Top-Welle.",
]

ZAHL = re.compile(r"(\S*\d[\d.:/ ]*\d?\S*)\s*(\S*)")


def vorlagen(nur: int) -> list[str]:
    """Je Zahl-Umfeld (die Zahl als N, dazu das Wort danach) das erste Beispiel aus den Live-Ansagen."""
    gesehen, aus = set(), []
    for datei in sorted((WURZEL / "aufnahmen").glob("*_ansagen.json"), reverse=True):
        try:
            eintraege = json.loads(datei.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for a in eintraege if isinstance(eintraege, list) else []:
            text = str(a.get("text", ""))
            if "»" in text or "“ –" in text:                      # Antwort: nur der Antwortteil
                text = text.split("“ – ", 1)[-1]
            for m in re.finditer(r"(\d+(?:[:/.]\d+)*)\s*([A-Za-zÄÖÜäöüß%-]*)", text):
                form = re.sub(r"\d+", "N", m.group(1))
                schluessel = (form, m.group(2).lower()[:10])
                if schluessel in gesehen:
                    continue
                gesehen.add(schluessel)
                # der Satz rund um die Zahl, hoechstens 120 Zeichen
                anf = max(0, text.rfind(".", 0, m.start()) + 1)
                ende = text.find(".", m.end())
                satz = text[anf:(ende + 1 if ende > 0 else len(text))].strip()[:120]
                if satz and satz not in aus:
                    aus.append(satz)
            if len(aus) >= nur:
                return aus
    return aus


async def _synth(text: str, name: str, tempo: str, pfad: Path) -> None:
    import edge_tts
    await edge_tts.Communicate(text, name, rate=tempo).save(str(pfad))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stimme", default="de-DE-KillianNeural")
    ap.add_argument("--tempo", default="+25%")
    ap.add_argument("--nur", type=int, default=24, help="so viele Vorlagen aus den Live-Ansagen")
    ap.add_argument("--ohne-fest", action="store_true")
    a = ap.parse_args()
    from faster_whisper import WhisperModel
    from lolcoach.sprache import _cuda_bibliotheken
    _cuda_bibliotheken()
    modell = None
    for name, geraet, typ in (("large-v3-turbo", "cuda", "float16"), ("small", "cpu", "int8")):
        try:
            modell = WhisperModel(name, device=geraet, compute_type=typ, download_root=str(WURZEL / "daten" / "whisper"))
            break
        except Exception:
            continue
    saetze = ([] if a.ohne_fest else FEST) + vorlagen(a.nur)
    with tempfile.TemporaryDirectory() as tmp:
        for i, text in enumerate(saetze):
            gesendet = stimme.sprechbar(text)
            pfad = Path(tmp) / f"{i}.mp3"
            asyncio.run(_synth(gesendet, a.stimme, a.tempo, pfad))
            teile, _ = modell.transcribe(str(pfad), language="de", beam_size=5)
            gehoert = " ".join(t.text.strip() for t in teile)
            print(f"[{i:2}] Text:      {text}")
            if gesendet != text:
                print(f"     Stimme:    {gesendet}")
            print(f"     Gehoert:   {gehoert}")


if __name__ == "__main__":
    main()
