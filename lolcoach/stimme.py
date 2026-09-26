"""Sprachausgabe ueber die Windows-Stimme (SAPI, offline, sofort).

Vorerst "Microsoft Hedda" (Deutsch). Die Stimme lebt in einem eigenen
Thread: SAPI ist ein COM-Objekt und darf nur aus dem Thread benutzt werden,
der es angelegt hat - gesprochen wird aber aus mehreren (Regeln im Kern,
Antworten auf Fragen aus dem Sprach-Thread).

Der Thread spricht einen Satz nach dem anderen aus seiner eigenen Schlange
(nicht SAPIs), damit ein Satz einzeln angehalten werden kann:
  pausiere()  - der Spieler drueckt Push-to-Talk: aktueller Satz stoppt und
                wird gemerkt, die Schlange wartet.
  antworte(t) - die Antwort kommt vor allem anderen, danach der unterbrochene
                Satz noch einmal (war er nicht zu alt), dann geht es weiter.
  freigeben() - nichts verstanden: unterbrochener Satz und Schlange laufen weiter.
Gemessen in Partie 3 (26.09.2026): eine Antwort hat "Warwick ist in seinem
oberen Jungle" abgewuergt - der Spieler hat die Warnung nie gehoert.
"""
from __future__ import annotations

import queue
import re
import threading
import time

_ASYNC, _UNTERBRECHEN = 1, 2
ZWEITE_ANFRAGE_NACH = 0.35   # Sekunden ohne Audio, bis eine zweite Synthese-Anfrage mitlaeuft
# Live 26.09., 23:06-23:16 (Practice Tool): die Stimme blieb nach einem Antippen der Sprechtaste minutenlang
# angehalten; danach kam "Milio hat Flash benutzt" 154 s spaet - Carlos: "sowas von in der Vergangenheit".
PAUSE_HOECHSTENS = 15.0      # so lange darf die Stimme fuer eine Frage angehalten sein, dann geht sie von selbst weiter
VERALTET = 5.0               # so lange darf eine Ansage in der Schlange der Stimme warten - danach ist sie ueberholt
PRUEFEN_ALLE = 0.25          # Sekunden: so oft fragt die Stimme waehrend eines Satzes, ob er noch stimmt
NOCH_AKTUELL = 25.0   # so alt darf ein unterbrochener Satz sein, um wiederholt zu werden


class _Sapi:
    """Windows-Stimme: offline, sofort, klingt aber nach Roboter (Partie 3: 'viel zu roboterhaft')."""

    def __init__(self, sprache: str, lautstaerke: int):
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        self.v = win32com.client.Dispatch("SAPI.SpVoice")
        stimmen = self.v.GetVoices()
        for i in range(stimmen.Count):
            if sprache in stimmen.Item(i).GetDescription():
                self.v.Voice = stimmen.Item(i)
                break
        self.v.Rate = 1
        self.v.Volume = lautstaerke

    def spreche(self, text: str, stopp: threading.Event, beim_ton=None, gilt=None) -> bool:
        if beim_ton:
            beim_ton()
        self.v.Speak(text, _ASYNC)
        naechste = time.monotonic() + PRUEFEN_ALLE
        while not self.v.WaitUntilDone(40):
            pruefen = gilt is not None and time.monotonic() >= naechste
            if pruefen:
                naechste = time.monotonic() + PRUEFEN_ALLE
            if stopp.is_set() or (pruefen and not gilt()):
                self.v.Speak("", _ASYNC | _UNTERBRECHEN)
                return False
        return True


class _Neural:
    """Microsofts neuronale Stimmen (wie "Vorlesen" in Edge), ueber edge-tts.
    Gemessen 26.09.2026: Conrad/Katja 0,35-0,45 s bis zum ersten Ton. Braucht
    Internet; faellt ein Satz aus, spricht ihn die Windows-Stimme."""

    def __init__(self, stimme: str, tempo: str, lautstaerke: int, ersatz: "_Sapi"):
        self.stimme, self.tempo, self.lautstaerke, self.ersatz = stimme, tempo, lautstaerke, ersatz
        self._cache: dict[str, tuple] = {}

    def _synthese(self, text: str):
        if text in self._cache:
            return self._cache[text]
        import asyncio
        import io
        import av
        import edge_tts
        import numpy as np

        async def hole_eins(erstes: asyncio.Event) -> bytes:
            daten = bytearray()
            async for teil in edge_tts.Communicate(text, self.stimme, rate=self.tempo).stream():
                if teil["type"] == "audio":
                    erstes.set()
                    daten += teil["data"]
            if not daten:
                raise RuntimeError("edge-tts: kein Audio")
            return bytes(daten)

        async def hole() -> bytes:
            """Gemessen 26.09. nachts, 15 Anfragen: erstes Audio im Median nach 0,17 s, aber jede zehnte erst nach
            1,4-1,8 s (Ausreisser beim Dienst) - live 'Stimme' 1,5 s im Median, bis 2,5 s. Kommt nach
            ZWEITE_ANFRAGE_NACH kein Audio, laeuft eine zweite Anfrage mit; die erste fertige gilt."""
            e1 = asyncio.Event()
            t1 = asyncio.create_task(hole_eins(e1))
            try:
                await asyncio.wait_for(e1.wait(), ZWEITE_ANFRAGE_NACH)
                return await t1
            except asyncio.TimeoutError:
                pass
            t2 = asyncio.create_task(hole_eins(asyncio.Event()))
            offen = {t1, t2}
            fehler = None
            while offen:
                fertig, offen = await asyncio.wait(offen, return_when=asyncio.FIRST_COMPLETED)
                for t in fertig:
                    if t.exception() is None:
                        for rest in offen:
                            rest.cancel()
                        return t.result()
                    fehler = t.exception()
            raise fehler or RuntimeError("edge-tts: kein Audio")

        mp3 = asyncio.run(asyncio.wait_for(hole(), timeout=6))
        with av.open(io.BytesIO(mp3)) as c:
            strom = c.streams.audio[0]
            rate = strom.rate
            teile = [f.to_ndarray() for f in c.decode(strom)]
        audio = np.concatenate(teile, axis=1)[0]
        if audio.dtype.kind == "i":
            audio = audio.astype(np.float32) / 32768.0
        audio = (audio.astype(np.float32) * (self.lautstaerke / 100.0))
        if len(self._cache) > 200:
            self._cache.clear()
        self._cache[text] = (audio, rate)
        return audio, rate

    def spreche(self, text: str, stopp: threading.Event, beim_ton=None, gilt=None) -> bool:
        """Satz fuer Satz: der erste klingt, sobald ER fertig ist, die weiteren entstehen parallel.
        `gilt()`: stimmt der Satz noch? Alle PRUEFEN_ALLE Sekunden gefragt - wenn nicht, bricht er ab.
        Gemessen 26.09.: ein 210-Zeichen-Satz brauchte 1,5 s bis zum ersten Ton (ganz synthetisiert),
        der erste Teilsatz davon 0,4-0,7 s. `beim_ton`: wird beim ersten Ton gerufen (Messung)."""
        import concurrent.futures as cf
        import sounddevice as sd
        teile = teilsaetze(text)
        with cf.ThreadPoolExecutor(max_workers=3) as pool:
            laeufe = [pool.submit(self._synthese, t) for t in teile]
            for i, lauf in enumerate(laeufe):
                try:
                    audio, rate = lauf.result(timeout=8)
                except Exception:
                    rest = " ".join(teile[i:])
                    return self.ersatz.spreche(rest, stopp, beim_ton if i == 0 else None, gilt)
                if stopp.is_set() or (gilt is not None and not gilt()):
                    return False
                if i == 0 and beim_ton:
                    beim_ton()
                sd.play(audio, rate)
                ende = time.monotonic() + len(audio) / rate + (0.3 if i == len(laeufe) - 1 else 0.02)
                naechste = time.monotonic() + PRUEFEN_ALLE
                while time.monotonic() < ende:
                    if stopp.is_set():
                        sd.stop()
                        return False
                    if gilt is not None and time.monotonic() >= naechste:
                        naechste = time.monotonic() + PRUEFEN_ALLE
                        if not gilt():
                            sd.stop()
                            return False
                    time.sleep(0.02)
        return True


def _still(f, *a) -> None:
    try:
        f(*a)
    except Exception:
        pass


def teilsaetze(text: str, erster_hoechstens: int = 90) -> list[str]:
    """In Saetze teilen (nach . ! ? und nach dem Doppelpunkt, an dem die Stimme ohnehin absetzt); ist der erste
    laenger als `erster_hoechstens`, auch am ersten Komma dahinter - damit der erste Ton frueh kommt."""
    teile = [t.strip() for t in re.split(r"(?<=[.!?:])\s+", text) if t.strip()]
    if teile and len(teile[0]) > erster_hoechstens:
        k = teile[0].find(", ", 30)
        if 0 < k < len(teile[0]) - 15:
            teile[0:1] = [teile[0][:k + 1], teile[0][k + 2:]]
    return teile or [text]


_SPRECHBAR = [
    (re.compile(r"\b(\d{1,2}):00\b"), r"Minute \1"),            # Spielzeit "5:00" -> "Minute 5"
    (re.compile(r"\b(\d{1,2}):(\d{2})\b"), r"\1 \2"),           # "2:45" -> "zwei fuenfundvierzig" (nicht "2 Uhr 45")
    (re.compile(r"(\d+)\s?[-–]\s?(\d+)"), r"\1 bis \2"),        # "30-40" -> "30 bis 40"
    (re.compile(r"(\d+)\s?s\b"), r"\1 Sekunden"),              # "30 s" -> "30 Sekunden"
    (re.compile(r"(\d+)\+"), r"mehr als \1"),                  # "2500+" -> "mehr als 2500"
    (re.compile(r"\s*→\s*"), ": "),                             # Lexikon-Pfeil: "E verbraucht -> er hat ..."
    (re.compile(r"(?<=[^\W\d])\s?/\s?(?=[^\W\d])"), " oder "),  # "Recall/Kauf" -> "Recall oder Kauf" (KDA 27/6/4 bleibt)
]


# Champion-Namen, die die deutsche Stimme falsch liest. Live 26.09.: "Vi" kam als "sechs" (roemische VI).
# V am Anfang spricht die Community wie W ("Warus", nicht "Farus"); Apostrophe liest die Stimme als Pause.
AUSSPRACHE = {
    "Vi": "Wai", "Viego": "Wiego", "Vex": "Wex", "Varus": "Warus", "Vayne": "Wäjn", "Veigar": "Weigar",
    "Vel'Koz": "Wel Kos", "Vladimir": "Wladimir", "Volibear": "Wolibär", "Kai'Sa": "Kaisa",
    "Kha'Zix": "Ka Sicks", "Cho'Gath": "Tscho Gath", "Kog'Maw": "Kog Mau", "Rek'Sai": "Reck Sai",
    "Bel'Veth": "Bell Weth", "K'Sante": "Ka Sante", "Nunu & Willump": "Nunu", "Nunu und Willump": "Nunu",
    "Dr. Mundo": "Doktor Mundo", "Jarvan IV.": "Jarvan", "Jarvan IV": "Jarvan", "LeBlanc": "Leblank",
    "Xin Zhao": "Schin Dschau", "Renata Glasc": "Renata", "Miss Fortune": "Miss Fortschun",
    "Twisted Fate": "Twisted Fäit", "CS": "C S",
    # Kuerzel aus dem Lexikon (Konter-Tipps): die Stimme las "AAs" und "CD" buchstabiert
    "AAs": "Auto-Angriffe", "AA": "Auto-Angriff", "CD": "Abklingzeit", "CDs": "Abklingzeiten",
}
_AUSSPRACHE = re.compile(r"(?<![\w'])(" + "|".join(re.escape(k) for k in sorted(AUSSPRACHE, key=len, reverse=True))
                         + r")(?![\w'])")


def sprechbar(text: str) -> str:
    """Was Claude schreibt, ist nicht immer, was man sagt: die Stimme las 'Jungler/Laner' mit
    Schraegstrich und '30-40 s' als 'dreissig minus vierzig s' (Review-Ansage 26.09.)."""
    for muster, ersatz in _SPRECHBAR:
        text = muster.sub(ersatz, text)
    return _AUSSPRACHE.sub(lambda m: AUSSPRACHE[m.group(1)], text)


class Stimme:
    def __init__(self, sprache: str = "German", warten: bool = False, lautstaerke: int = 100,
                 neural: str | None = None, tempo: str = "+25%"):   # Carlos 26.09.: "viel peppiger" (vorher +15 %)
        """`warten`: jeder Satz blockiert, bis er gesprochen ist - zum Anhoeren
        einer Aufnahme im Zeitraffer. `lautstaerke` 0 fuer Tests. `neural`: Name
        einer neuronalen Stimme (z. B. "de-DE-ConradNeural"), sonst die Windows-Stimme."""
        self.warten, self.lautstaerke, self.neural, self.tempo = warten, lautstaerke, neural, tempo
        self.protokoll: list[str] = []   # was angefangen wurde, in Reihenfolge
        self._schlange: queue.Queue = queue.Queue()   # (text, fertig, melde, eingereiht)
        self._vorrang: queue.Queue = queue.Queue()     # Antworten
        self._frei = threading.Event()
        self._frei.set()
        self._stopp = threading.Event()
        self._unterbrochen: tuple[str, float] | None = None
        self._spricht = False
        self._pausiert_seit = 0.0
        self._gehalten = None      # aus der Schlange geholt, als die Stimme gerade angehalten wurde
        self._bereit = threading.Event()
        threading.Thread(target=self._lauf, args=(sprache,), daemon=True).start()
        self._bereit.wait(timeout=5)

    def _lauf(self, sprache: str) -> None:
        motor = _Sapi(sprache, self.lautstaerke)
        if self.neural:
            motor = _Neural(self.neural, self.tempo, self.lautstaerke, ersatz=motor)
            # einmal stumm vorwaermen (Module, Verbindung): kalt kam der erste Ton nach 1,9 s, warm nach 0,6-0,75 s
            threading.Thread(target=lambda: _still(motor._synthese, "Los."), daemon=True).start()
        self._bereit.set()
        while True:
            try:
                text, fertig, melde, noch_wahr = self._vorrang.get_nowait()
            except queue.Empty:
                if not self._frei.is_set():
                    if time.monotonic() - self._pausiert_seit > PAUSE_HOECHSTENS:
                        print("  (Stimme war zu lange angehalten - geht weiter)", flush=True)
                        self._wieder_und_frei()
                    time.sleep(0.03)
                    continue
                if self._gehalten is not None:
                    eintrag, self._gehalten = self._gehalten, None
                else:
                    try:
                        eintrag = self._schlange.get(timeout=0.05)
                    except queue.Empty:
                        continue
                if not self._frei.is_set():
                    # waehrend des Wartens angehalten (Sprechtaste): der Leerlauf sitzt fast immer in get() -
                    # ohne diese Pruefung sprach der naechste Satz in Carlos' Frage hinein
                    self._gehalten = eintrag
                    continue
                text, fertig, melde, rein, noch_wahr = eintrag
                if fertig is None and time.monotonic() - rein > VERALTET:
                    if melde:
                        _still(melde, "verworfen", time.monotonic())
                    continue
            widerrufen = [False]

            def gilt(nw=noch_wahr, w=widerrufen) -> bool:
                try:
                    ok = nw() if nw is not None else True
                except Exception:
                    ok = True
                if not ok:
                    w[0] = True
                return ok
            if noch_wahr is not None and not gilt():
                if melde:
                    _still(melde, "verworfen", time.monotonic())   # stimmt schon vor dem ersten Ton nicht mehr
                if fertig is not None:
                    fertig.set()
                continue
            self._stopp.clear()
            self.protokoll.append(text)
            self._spricht = True
            ganz = False
            try:
                ton = (lambda m=melde: _still(m, "ton", time.monotonic())) if melde else None
                ganz = motor.spreche(sprechbar(text), self._stopp, ton, gilt if noch_wahr is not None else None)
                if not ganz and not widerrufen[0]:
                    self._unterbrochen = (text, time.monotonic())
            finally:
                self._spricht = False
                if melde:
                    art = "ende" if ganz else ("widerrufen" if widerrufen[0] else "abgebrochen")
                    _still(melde, art, time.monotonic())
            if fertig is not None:
                fertig.set()

    @property
    def beschaeftigt(self) -> bool:
        """Spricht gerade oder hat noch etwas in der Schlange - der Sprechplan gibt dann nichts Neues ab
        (gemessen 26.09.: Killian spricht 11-12 Zeichen/s, der Plan schaetzte 14 - Saetze stauten sich
        in der Schlange und kamen veraltet an)."""
        return (self._spricht or self._gehalten is not None or not self._schlange.empty()
                or not self._vorrang.empty())

    def sage(self, text: str, dringend: bool = False, melde=None, noch_wahr=None) -> None:
        """`noch_wahr()`: stimmt der Satz noch (vor und waehrend des Sprechens gefragt)? `dringend`: vor alle wartenden Saetze, der laufende wird abgebrochen (nicht wiederholt).
        `melde(art, monotonic)`: "ton" beim ersten Ton, dann "ende" oder "abgebrochen" - die echte Verzoegerung."""
        fertig = threading.Event() if self.warten else None
        if dringend:
            self._vorrang.put((text, fertig, melde, noch_wahr))
            if self._frei.is_set():
                self._stopp.set()
        else:
            self._schlange.put((text, fertig, melde, time.monotonic(), noch_wahr))
        if fertig:
            fertig.wait(timeout=60)

    def pausiere(self) -> None:
        self._pausiert_seit = time.monotonic()
        self._frei.clear()
        self._unterbrochen = None
        self._stopp.set()

    def antworte(self, text: str) -> None:
        self._vorrang.put((text, None, None, None))
        self._wieder_und_frei()

    def antworte_teil(self, text: str) -> None:
        """Ein Satz einer gestreamten Antwort: sofort vor alles andere - der unterbrochene Satz kommt erst
        mit `antworte_ende` wieder (sonst stuende er zwischen zwei Saetzen der Antwort)."""
        self._vorrang.put((text, None, None, None))
        self._frei.set()

    def antworte_ende(self) -> None:
        self._wieder_und_frei()

    def freigeben(self) -> None:
        self._wieder_und_frei()

    def _wieder_und_frei(self) -> None:
        u, self._unterbrochen = self._unterbrochen, None
        if u and time.monotonic() - u[1] < NOCH_AKTUELL:
            self._vorrang.put((u[0], None, None, None))
        self._frei.set()

    # alter Name, wird noch von aussen benutzt
    def verstumme(self) -> None:
        self.pausiere()


class Stumm:
    def sage(self, text: str, dringend: bool = False, melde=None, noch_wahr=None) -> None:
        pass

    def antworte_teil(self, text: str) -> None:
        pass

    def antworte_ende(self) -> None:
        pass

    def pausiere(self) -> None:
        pass

    def antworte(self, text: str) -> None:
        pass

    def freigeben(self) -> None:
        pass

    def verstumme(self) -> None:
        pass
