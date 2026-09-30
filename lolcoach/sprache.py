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
                # aufwaermen wie eine echte Frage (3 s, mit Vorgabe): mit 0,5 s Stille dauerte die erste echte
                # Frage der Partie noch 0,9 s statt 0,2 s (gemessen 27.09.)
                rausch = (np.random.default_rng(0).standard_normal(RATE * 3) * 0.01).astype(np.float32)
                list(self.modell.transcribe(rausch, language="de", beam_size=1, initial_prompt=VOKABULAR + ".",
                                            vad_filter=False, condition_on_previous_text=False)[0])
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

    def __init__(self, taste: str, bei_frage, beim_druecken=None, bei_abbruch=None, beim_loslassen=None):
        super().__init__(daemon=True)
        if taste.lower() not in TASTEN:
            raise ValueError(f"Unbekannte Taste '{taste}'. Moeglich: {', '.join(sorted(TASTEN))}")
        self.vk = TASTEN[taste.lower()]
        self.bei_frage, self.beim_druecken, self.bei_abbruch = bei_frage, beim_druecken, bei_abbruch
        self.beim_loslassen = beim_loslassen   # die Taste ist die Stummtaste: los = der Coach darf wieder
        self.geraet, self.geraet_rate = _mikrofon()
        # Auftrag 027, 0: welches Geraet mit welcher Host-API - beim WDM-KS-Fehler vom 30.09. fehlte genau das im Log
        try:
            import sounddevice as sd
            d = sd.query_devices(self.geraet if self.geraet is not None else sd.default.device[0])
            print(f"  (Mikrofon: {d['name']} - {sd.query_hostapis(d['hostapi'])['name']}, {self.geraet_rate} Hz)",
                  flush=True)
        except Exception:
            pass
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
            strom = self._oeffne(sd, stuecke)
            try:
                while win32api.GetAsyncKeyState(self.vk) & 0x8000 and not self._halt.is_set():
                    time.sleep(0.02)
            finally:
                if strom is not None:
                    try:
                        strom.stop()
                        strom.close()
                    except Exception:
                        pass
            if self.beim_loslassen:
                self.beim_loslassen()
            # Nur angetippt: keine Frage - aber der Coach wurde beim Druecken stumm geschaltet und muss wieder frei
            # sein. Live 26.09., 23:06: ein kurzes Antippen von Maus 5 hielt die Stimme minutenlang an, danach kamen
            # die alten Ansagen ("Milio hat Flash benutzt" 154 s spaet - Carlos: "sowas von in der Vergangenheit").
            if not stuecke:
                if self.bei_abbruch:
                    self.bei_abbruch()
                continue
            audio = _auf_16k(np.concatenate(stuecke), self.geraet_rate)
            if len(audio) < RATE * 0.3:
                if self.bei_abbruch:
                    self.bei_abbruch()
                continue
            threading.Thread(target=self.bei_frage, args=(audio,), daemon=True).start()

    def _oeffne(self, sd, stuecke):
        """Mikrofon oeffnen. Geht das gewaehlte Geraet nicht (Headset getrennt, Windows-Fehler), die uebrigen
        Eingaenge der Reihe nach probieren: Windows-Standard, dann alle ausser WDM-KS. Hotfix 30.09.2026 (Carlos:
        PortAudioError -9999 WDM-KS beim Druecken, der Sprech-Thread starb). Kein Mikrofon: None, die Frage entfaellt,
        der Coach laeuft weiter."""
        def rueckruf(d, *_):
            stuecke.append(d[:, 0].copy())
        kandidaten = [(self.geraet, self.geraet_rate)]
        try:
            kandidaten.append((None, int(sd.query_devices(kind="input")["default_samplerate"])))
        except Exception:
            pass
        try:
            for i, d in enumerate(sd.query_devices()):
                if d["max_input_channels"] > 0 and "WDM-KS" not in sd.query_hostapis(d["hostapi"])["name"]:
                    kandidaten.append((i, int(d["default_samplerate"])))
        except Exception:
            pass
        gesehen = set()
        for geraet, rate in kandidaten:
            if (geraet, rate) in gesehen:
                continue
            gesehen.add((geraet, rate))
            try:
                strom = sd.InputStream(device=geraet, samplerate=rate, channels=1, dtype="float32", callback=rueckruf)
                strom.start()
            except Exception as e:
                print(f"  (Mikrofon {geraet}: {type(e).__name__} - probiere das naechste)", flush=True)
                continue
            if (geraet, rate) != (self.geraet, self.geraet_rate):
                print(f"  (Mikrofon gewechselt auf Geraet {geraet}, {rate} Hz)", flush=True)
                self.geraet, self.geraet_rate = geraet, rate
            return strom
        print("  (Kein Mikrofon liess sich oeffnen - Headset angeschlossen?)", flush=True)
        return None

    def halt(self) -> None:
        self._halt.set()


FRAGE_WORTE = {"wo", "wann", "was", "wie", "warum", "wieso", "wer", "welche", "welcher", "welches", "soll", "sollte",
               "kann", "können", "ist", "hat", "hab", "habe", "gibt", "notiz", "merk", "merke"}
# Wortstaemme aus dem Spiel ("Ich bin Toplane", "Ich Powerfarme lieber" sind Aussagen, die zaehlen)
SPIEL_STAEMME = ("flash", "drach", "baron", "herold", "larven", "turm", "tower", "welle", "gold", "item", "back",
                 "recall", "jung", "lane", "line", "tot", "kill", "ult", "ward", "gank", "top", "mid", "bot", "farm",
                 "level", "teleport", "zünd", "leben", "mana", "push", "freez", "supp", "adc", "roam", "invad")


def _bruchstueck(text: str, woerter: list[str], champions: list[str]) -> bool:
    """Drei Woerter oder weniger, keine Frage, nichts aus dem Spiel: ein Bruchstueck, keine Frage an den Coach."""
    if len(woerter) > 3 or "?" in text:
        return False
    klein = {w.strip(".,!:;").lower() for w in woerter}
    if klein & FRAGE_WORTE or any(st in text.lower() for st in SPIEL_STAEMME):
        return False
    return not any(c.lower() in text.lower() for c in champions)


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
        self.ptt = PushToTalk(taste, self._frage, beim_druecken=self._gedrueckt, bei_abbruch=sprecher.freigeben,
                              beim_loslassen=getattr(sprecher, "taste_los", None))
        self.ptt.start()

    def _gedrueckt(self) -> None:
        """Taste gedrueckt: der Coach verstummt, und ein Claude-Prozess startet schon, waehrend er noch spricht
        (der Start kostet 0,6-0,9 s, die Frage dauert meist laenger - llm.vorhalten)."""
        self.sprecher.pausiere()
        if not getattr(self, "partie_vorbei", False):
            from . import llm
            threading.Thread(target=llm.vorhalten, args=(self.modell, self.antworten.SYSTEM, self.antworten.AUFWAND),
                             daemon=True).start()

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
        if getattr(self, "partie_vorbei", False):
            # ausserhalb einer Partie antwortet der Coach nicht (das Review ist entfernt, Auftrag 028)
            self.sprecher.freigeben()
            return
        p = self.p
        start = time.monotonic()
        self._tastenlog(p, audio)
        if p is None or not p.ich:
            self.sprecher.antworte("Ich sehe noch keine Partie.")
            return
        if float(np.sqrt(np.mean(audio ** 2))) < 0.003:
            self.sprecher.freigeben()
            return  # nichts gesagt
        text = self.erkenner.text(audio, [s.champion for s in p.spieler])
        erkannt = time.monotonic() - start
        woerter = text.lower().replace(",", " ").replace(".", " ").split()
        if not text or any(e in text.lower() for e in ERFUNDEN) or len(woerter) < 2:
            self.sprecher.freigeben()  # Rauschen, Raeuspern, "B."
            return
        print(f"  Du: {text}", flush=True)
        kern_ = getattr(self.lagebild, "kern", None)
        if kern_ is not None and hasattr(kern_, "hoere"):
            kern_.hoere(text, p.zeit)          # Auftrag 028, 6.3: sein Widerspruch sperrt alle Stimmen
        makro = None
        if _bruchstueck(text, woerter, [s.champion for s in p.spieler]):
            # Live 26.09. (Practice Tool): "Und man", "Da hoere ich", "Der Thomas Dau" - Nebengeraeusche oder
            # Gespraeche nebenbei; "Und man" bekam einen langen Rat ("Kauf jetzt Caulfields Kriegshammer ...")
            print("  (Bruchstueck ohne Frage - keine Antwort)", flush=True)
            self.sprecher.freigeben()
            return
        notiz = woerter[0].strip(":") in NOTIZ_WORTE
        if notiz:
            self._notiere(text, p)
            from .kern.fragen import frage_in_notiz
            if (innen := frage_in_notiz(text)) is not None:
                text = innen                   # Auftrag 024, 5.1: beantwortet UND notiert (231200 11:03)
                notiz = False
        if notiz:
            antwort = "Notiert."
        else:
            # Schritt 6 (Buch 11, 5): zuerst der Kern - dieselbe Wahrheit wie die Ansagen, ohne Claude
            r = self.antworten.frage_kern(text, p, self.lagebild) if hasattr(self.antworten, "frage_kern") else None
            antwort = (r or {}).get("text")
            if r and r.get("absicht") == "NOTIZ":
                self._notiere(text, p)
            # Auftrag 015, B1: echte Fragen an den Makro-Strategen (der Kern hat Korrekturen schon gesetzt); Faktfragen,
            # KLAEREN und Notizen bleiben beim Kern. Klappt es nicht, antwortet der Kern wie bisher.
            makro = getattr(getattr(self.lagebild, "kern", None), "makro_stratege", None)
            if makro is not None and r is not None and self._stratege_antwort(makro, text, r, p, erkannt, start):
                return
            if antwort is None and makro is not None and makro.aktiv and not makro.bereit():
                antwort = self.antworten.sofort(text, p, self.lagebild)   # Ausfall: kein zweiter Claude-Aufruf
                if antwort is None:
                    self.sprecher.freigeben()
                    return
            if antwort is None:
                antwort = self.antworten.sofort(text, p, self.lagebild)
            if antwort is None:
                letzte = [a for a in (self.gesagt or []) if a.schluessel != "antwort"][-3:]
                b = getattr(self, "beobachter", None)
                bild = b.bildschirm() if b is not None else None   # der Bildschirm, als er fragte
                gesprochen = []

                def satz_fertig(satz: str) -> None:
                    # Satz fuer Satz sprechen (2 s frueher als die ganze Antwort) - ausser der Coach will die Kamera
                    # oder erkennt eine Rueckmeldung ("Notiert"): das entscheidet der erste Satz
                    if not gesprochen and (satz.upper().startswith("KAMERA") or
                                           satz.strip().rstrip(".").lower() == "notiert"):
                        gesprochen.append(None)
                        return
                    if gesprochen and gesprochen[0] is None:
                        return
                    if self._sicher(satz) != satz:
                        return                 # Auftrag 028, 3: ein unsicherer Satz der Claude-Antwort faellt
                    if not gesprochen:
                        self._zeiten(p, erkannt, time.monotonic() - start, "Claude", text)
                    gesprochen.append(satz)
                    if hasattr(self.sprecher, "antworte_teil"):
                        self.sprecher.antworte_teil(satz)

                strom = hasattr(self.sprecher, "antworte_teil")
                antwort = self.antworten.mit_claude(text, self.p, self.lagebild, self.modell, letzte,
                                                    getattr(self, "gehirn", None), [bild] if bild else None,
                                                    bei_satz=satz_fertig if strom else None, vorhalten=True)
                if strom and gesprochen and gesprochen[0] is not None:
                    self.sprecher.antworte_ende()
                    print(f"  Coach: {antwort}", flush=True)
                    if self.gesagt is not None:
                        from .regeln import WICHTIG, Ansage
                        self.gesagt.append(Ansage(f"„{text}“ – {antwort}", WICHTIG, "antwort", zeit=p.zeit,
                                                  gesprochen=p.zeit))
                    return
                if antwort.upper().startswith("KAMERA:") and b is not None:
                    # Der Coach braucht einen Blick: "Schwenk kurz zum Drachen" - dann mit dem neuen Bild
                    # (Carlos: "er kann mir sagen, dass ich die Kamera verschieben soll - er ist ja mein Coach")
                    wohin = antwort.split(":", 1)[1].strip().rstrip(".")
                    print(f"  Coach: Schwenk kurz {wohin}", flush=True)
                    self.sprecher.antworte(f"Schwenk kurz die Kamera: {wohin}.")
                    time.sleep(self.antworten.KAMERA_WARTEN)
                    neu = b.bildschirm()
                    antwort = self.antworten.mit_claude(f"{text}\n({self.antworten.KAMERA_NACHFRAGE})", self.p,
                                                        self.lagebild, self.modell, letzte, getattr(self, "gehirn", None),
                                                        [neu] if neu else None)
                    if antwort.upper().startswith("KAMERA:"):
                        antwort = "Ich sehe es leider noch nicht - frag mich gleich noch mal."
                if antwort.strip().rstrip(".").lower() == "notiert":
                    self._notiere(text, p)  # Claude hat es als Rueckmeldung erkannt
        antwort = self._sicher(antwort)                # Auftrag 028, 3: auch die Antwort des Kerns
        if not antwort:
            self.sprecher.freigeben()
            return
        print(f"  Coach: {antwort}", flush=True)
        self._zeiten(p, erkannt, time.monotonic() - start, "ganz", text)
        if makro is not None and p is not None:
            makro.antwort_gesprochen(antwort, p.zeit)        # Auftrag 023, 3: eine Stimme - die Antwort ist der Plan
        self.sprecher.antworte(antwort)
        if self.gesagt is not None:
            from .regeln import WICHTIG, Ansage
            self.gesagt.append(Ansage(f"„{text}“ – {antwort}", WICHTIG, "antwort", zeit=p.zeit, gesprochen=p.zeit))

    def _stratege_antwort(self, makro, text: str, r: dict, p, erkannt: float, start: float) -> bool:
        """Auftrag 015, B1: die Antwort des Strategen. Seit Auftrag 017, 0.1 GANZ geprueft und am Stueck gesprochen
        (vorher Satz fuer Satz mit Pausen dazwischen). False: der Kern antwortet."""
        antwort = makro.antworte(text, r.get("absicht"), p, entwurf=r.get("text"))
        antwort = self._sicher(antwort)              # Auftrag 028, 3: Kill-Check beim Sprechen, nicht beim Fragen
        if not antwort:
            return False
        self._zeiten(p, erkannt, time.monotonic() - start, "Stratege", text)
        self.sprecher.antworte(antwort)
        print(f"  Coach (Stratege): {antwort}", flush=True)
        if self.gesagt is not None:
            from .regeln import WICHTIG, Ansage
            a = Ansage(f"„{text}“ – {antwort}", WICHTIG, "antwort", zeit=p.zeit, gesprochen=p.zeit)
            a._quelle = "stratege"
            self.gesagt.append(a)
        return True

    def _sicher(self, antwort: str | None) -> str | None:
        """Auftrag 028, 3 (231200 26:25 "Xerath töten sofort": beim Fragen geprueft, 3,5 s spaeter gesprochen - da
        hielt der Kill nicht mehr): jede Antwort geht beim Sprechen noch einmal durch den Kill-Check des Kerns."""
        kern = getattr(self.lagebild, "kern", None)
        if kern is None or not hasattr(kern, "sichere_antwort") or not antwort:
            return antwort
        try:
            return kern.sichere_antwort(antwort)
        except Exception:
            return antwort

    def _zeiten(self, p, erkannt: float, stimme: float, wie: str, text: str) -> None:
        """Wie lange er warten musste - je Frage ins Tastenprotokoll: Spracherkennung, bis die ersten Worte an die
        Stimme gingen (dazu ~0,45 s bis zum Ton). Carlos 27.09.: "antwortet extrem spaet"."""
        if self.notizen is None or p is None:
            return
        try:
            with open(self.notizen.with_name(self.notizen.name.replace("_notizen.md", "_sprechtaste.log")), "a",
                      encoding="utf-8") as f:
                f.write(f"    erkannt nach {erkannt:.2f} s, an die Stimme nach {stimme:.2f} s ({wie}): {text}\n")
        except OSError:
            pass

    def _notiere(self, text: str, p) -> None:
        ziel = self.notizen or MODELLE.parent.parent / "aufnahmen" / "notizen.md"
        ziel.parent.mkdir(parents=True, exist_ok=True)
        with open(ziel, "a", encoding="utf-8") as f:
            f.write(f"- {int(p.zeit // 60)}:{int(p.zeit % 60):02d} ({p.ich.champion}): {text}\n")


NOTIZ_WORTE = {"notiz", "notizen", "notiere", "merk", "merke", "feedback"}
