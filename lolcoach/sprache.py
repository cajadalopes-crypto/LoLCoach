"""Mit dem Coach reden: Push-to-Talk, Spracherkennung, Antwort.

Nur solange die Taste gedrueckt ist, wird das Mikrofon gelesen - sonst
hoert der Coach nichts. Die Taste wird per GetAsyncKeyState abgefragt
(liest nur den Zustand, haengt sich nicht in die Tastatur ein, sendet nichts).

Erkennung: faster-whisper lokal, auf der Grafikkarte (RTX 4070: ~0,2 s je
Frage mit large-v3-turbo), sonst auf dem Prozessor mit `small` (~1 s).
Ein LoL-Vokabular als Vorgabe verhindert "Chang-Glue" statt "Jungler".
"""
from __future__ import annotations

import os
import pathlib
import threading
import time

import numpy as np

MODELLE = pathlib.Path(__file__).resolve().parent.parent / "daten" / "whisper"
RATE = 16000

TASTEN = {"maus4": 0x05, "maus5": 0x06, "mausmitte": 0x04, "alt": 0x12, "strg": 0x11, "shift": 0x10,
          "tab": 0x09, "capslock": 0x14, "pause": 0x13, "einfg": 0x2D, "pos1": 0x24, "ende": 0x23,
          "bildauf": 0x21, "bildab": 0x22, "num0": 0x60, "num1": 0x61, "num2": 0x62, "num3": 0x63}
TASTEN.update({f"f{i}": 0x6F + i for i in range(1, 25)})
TASTEN.update({c: ord(c.upper()) for c in "abcdefghijklmnopqrstuvwxyz0123456789"})

VOKABULAR = ("League of Legends. Jungler, Gank, Drache, Baron, Herold, Larven, Ältester, Flash, Teleport, "
             "Zünden, Recall, Top, Mid, Bot, Support, ADC, Turm, Platten, Welle, Items, Gold, CS")


def _cuda_bibliotheken() -> None:
    """cuBLAS/cuDNN aus den nvidia-Paketen fuer ctranslate2 auffindbar machen."""
    try:
        import nvidia
    except ImportError:
        return
    for p in nvidia.__path__:
        for b in pathlib.Path(p).glob("*/bin"):
            os.add_dll_directory(str(b))
            os.environ["PATH"] = str(b) + os.pathsep + os.environ["PATH"]


class Erkenner:
    """Laedt das Modell im Hintergrund, damit der Coach sofort startet."""

    def __init__(self):
        self.modell = None
        self.beschreibung = "laedt ..."
        self._fertig = threading.Event()
        threading.Thread(target=self._lade, daemon=True).start()

    def _lade(self) -> None:
        os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
        from faster_whisper import WhisperModel
        _cuda_bibliotheken()
        for name, geraet, typ in (("large-v3-turbo", "cuda", "float16"), ("small", "cpu", "int8")):
            try:
                self.modell = WhisperModel(name, device=geraet, compute_type=typ, download_root=str(MODELLE))
                self.modell.transcribe(np.zeros(RATE // 2, np.float32), language="de")  # aufwaermen
                self.beschreibung = f"{name} auf {geraet}"
                break
            except Exception as e:
                self.beschreibung = f"Fehler: {type(e).__name__}: {e}"
        self._fertig.set()

    def text(self, audio: np.ndarray, namen: list[str] = ()) -> str:
        self._fertig.wait(timeout=120)
        if self.modell is None:
            return ""
        vorgabe = VOKABULAR + (". " + ", ".join(namen) if namen else "") + "."
        teile, _ = self.modell.transcribe(audio, language="de", beam_size=1, initial_prompt=vorgabe,
                                          vad_filter=False, condition_on_previous_text=False)
        return " ".join(t.text.strip() for t in teile).strip()


def _mikrofon():
    """Das Headset (WASAPI, geteilt mit Discord), sonst der Windows-Standard."""
    import sounddevice as sd
    for i, d in enumerate(sd.query_devices()):
        api = sd.query_hostapis(d["hostapi"])["name"]
        if d["max_input_channels"] > 0 and "WASAPI" in api and "CORSAIR" in d["name"].upper():
            return i, int(d["default_samplerate"])
    d = sd.query_devices(kind="input")
    return None, int(d["default_samplerate"])


def _auf_16k(audio: np.ndarray, rate: int) -> np.ndarray:
    if rate == RATE:
        return audio
    n = int(len(audio) * RATE / rate)
    return np.interp(np.linspace(0, len(audio) - 1, n), np.arange(len(audio)), audio).astype(np.float32)


class PushToTalk(threading.Thread):
    """Haelt die Taste -> nimmt auf; laesst los -> ruft `bei_frage(audio)` im eigenen Thread.
    `beim_druecken()` wird sofort beim Druecken gerufen (z. B. Coach verstummt)."""

    def __init__(self, taste: str, bei_frage, beim_druecken=None):
        super().__init__(daemon=True)
        if taste.lower() not in TASTEN:
            raise ValueError(f"Unbekannte Taste '{taste}'. Moeglich: {', '.join(sorted(TASTEN))}")
        self.vk = TASTEN[taste.lower()]
        self.bei_frage, self.beim_druecken = bei_frage, beim_druecken
        self.geraet, self.geraet_rate = _mikrofon()
        self._halt = threading.Event()

    def run(self) -> None:
        import sounddevice as sd
        import win32api
        while not self._halt.is_set():
            if not win32api.GetAsyncKeyState(self.vk) & 0x8000:
                time.sleep(0.02)
                continue
            if self.beim_druecken:
                self.beim_druecken()
            stuecke: list[np.ndarray] = []
            with sd.InputStream(device=self.geraet, samplerate=self.geraet_rate, channels=1, dtype="float32",
                                callback=lambda d, *_: stuecke.append(d[:, 0].copy())):
                while win32api.GetAsyncKeyState(self.vk) & 0x8000 and not self._halt.is_set():
                    time.sleep(0.02)
            if not stuecke:
                continue
            audio = _auf_16k(np.concatenate(stuecke), self.geraet_rate)
            if len(audio) < RATE * 0.3:
                continue  # nur angetippt
            threading.Thread(target=self.bei_frage, args=(audio,), daemon=True).start()

    def halt(self) -> None:
        self._halt.set()


# Whisper erfindet bei Stille gern Saetze aus seinen Trainingsdaten (Untertitel).
ERFUNDEN = ("untertitel", "vielen dank fürs zuschauen", "danke fürs zuschauen", "copyright", "amara.org")


class Gespraech:
    """Push-to-Talk -> Text -> Antwort (sofort aus dem Zustand, sonst Claude) -> Stimme.

    Haengt wie das Dashboard am Kern (`aktualisiere`) und kennt so immer den
    neuesten Zustand."""

    def __init__(self, sprecher, taste: str, modell: str = "sonnet"):
        from . import antworten
        self.antworten, self.sprecher, self.modell = antworten, sprecher, modell
        self.erkenner = Erkenner()
        self.p = self.lagebild = self.gesagt = None
        self.notizen: pathlib.Path | None = None   # je Partie gesetzt (live)
        self.ptt = PushToTalk(taste, self._frage, beim_druecken=sprecher.pausiere)
        self.ptt.start()

    def aktualisiere(self, p, lagebild=None, ansagen=None) -> None:
        self.p, self.lagebild, self.gesagt = p, lagebild, ansagen

    def gehirn_setzen(self, gehirn) -> None:
        self.gehirn = gehirn

    def beobachter_setzen(self, beobachter) -> None:
        """Der Minimap-Leser der Partie haelt auch den Spielbildschirm - fuer Fragen mit Bild."""
        self.beobachter = beobachter

    def _frage(self, audio: np.ndarray) -> None:
        try:
            self._beantworte(audio)
        except Exception as e:  # nie haengen bleiben: sonst bleibt der Coach stumm
            print(f"  Sprachfrage fehlgeschlagen: {type(e).__name__}: {e}", flush=True)
            self.sprecher.freigeben()

    def _tastenlog(self, p, audio: np.ndarray, text: str = "") -> None:
        """Jeder Druck auf die Sprechtaste mit Spielzeit - Partie 6: 'hat Blitz benutzt'-Pings von Carlos'
        Konto, die er nicht geschickt hat; liegt die Taste (Maus 5) im Spiel auf Pingen?"""
        if self.notizen is None or p is None:
            return
        try:
            with open(self.notizen.with_name(self.notizen.name.replace("_notizen.md", "_sprechtaste.log")), "a",
                      encoding="utf-8") as f:
                f.write(f"{int(p.zeit // 60)}:{int(p.zeit % 60):02d} gedrueckt {len(audio) / RATE:.1f} s"
                        f"{' - ' + text if text else ''}\n")
        except OSError:
            pass

    def _beantworte(self, audio: np.ndarray) -> None:
        p = self.p
        self._tastenlog(p, audio)
        if p is None or not p.ich:
            self.sprecher.antworte("Ich sehe noch keine Partie.")
            return
        if float(np.sqrt(np.mean(audio ** 2))) < 0.003:
            self.sprecher.freigeben()
            return  # nichts gesagt
        text = self.erkenner.text(audio, [s.champion for s in p.spieler])
        woerter = text.lower().replace(",", " ").replace(".", " ").split()
        if not text or any(e in text.lower() for e in ERFUNDEN) or len(woerter) < 2:
            self.sprecher.freigeben()  # Rauschen, Raeuspern, "B."
            return
        print(f"  Du: {text}", flush=True)
        if woerter[0].strip(":") in NOTIZ_WORTE:
            self._notiere(text, p)
            antwort = "Notiert."
        else:
            antwort = self.antworten.sofort(text, p, self.lagebild)
            if antwort is None:
                letzte = [a for a in (self.gesagt or []) if a.schluessel != "antwort"][-3:]
                b = getattr(self, "beobachter", None)
                bild = b.bildschirm() if b is not None else None   # der Bildschirm, als er fragte
                antwort = self.antworten.mit_claude(text, self.p, self.lagebild, self.modell, letzte,
                                                    getattr(self, "gehirn", None), [bild] if bild else None)
                if antwort.strip().rstrip(".").lower() == "notiert":
                    self._notiere(text, p)  # Claude hat es als Rueckmeldung erkannt
        print(f"  Coach: {antwort}", flush=True)
        self.sprecher.antworte(antwort)
        if self.gesagt is not None:
            from .regeln import WICHTIG, Ansage
            self.gesagt.append(Ansage(f"„{text}“ – {antwort}", WICHTIG, "antwort", zeit=p.zeit, gesprochen=p.zeit))

    def _notiere(self, text: str, p) -> None:
        ziel = self.notizen or MODELLE.parent.parent / "aufnahmen" / "notizen.md"
        ziel.parent.mkdir(parents=True, exist_ok=True)
        with open(ziel, "a", encoding="utf-8") as f:
            f.write(f"- {int(p.zeit // 60)}:{int(p.zeit % 60):02d} ({p.ich.champion}): {text}\n")


NOTIZ_WORTE = {"notiz", "notizen", "notiere", "merk", "merke", "feedback"}
