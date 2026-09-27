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
ZWEITE_ANFRAGE_NACH = 0.25   # Sekunden ohne Audio, bis eine zweite Synthese-Anfrage mitlaeuft
# (gemessen 27.09.: erstes Audio im Median 0,19 s, jede vierte Anfrage 0,6 s und mehr)
ENDE = object()              # _Strom.stueck: es kommt kein Stueck mehr
ERSTER_TON_HOECHSTENS = 2.0  # Sekunden ohne Audio fuer den ersten Teil, dann spricht die Windows-Stimme
# Live 26.09., 23:06-23:16 (Practice Tool): die Stimme blieb nach einem Antippen der Sprechtaste minutenlang
# angehalten; danach kam "Milio hat Flash benutzt" 154 s spaet - Carlos: "sowas von in der Vergangenheit".
PAUSE_HOECHSTENS = 15.0      # so lange darf die Stimme fuer eine Frage angehalten sein, dann geht sie von selbst weiter
VERALTET = 5.0               # so lange darf eine Ansage in der Schlange der Stimme warten - danach ist sie ueberholt
PRUEFEN_ALLE = 0.25          # Sekunden: so oft fragt die Stimme waehrend eines Satzes, ob er noch stimmt
STUMM_HOECHSTENS = 60.0   # Sekunden: laenger haelt keiner die Sprechtaste - danach gilt sie als losgelassen


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


class _Strom:
    """Eine laufende Synthese: die PCM-Stuecke kommen an, waehrend der Dienst noch rechnet - gespielt wird ab dem
    ersten. Gemessen 27.09. nachts: erstes MP3-Stueck im Median nach 0,19 s (0,11 davon Verbindungsaufbau), der
    ganze Teilsatz 0,1-0,3 s spaeter; bisher klang er erst, wenn er ganz da war. Kommt nach ZWEITE_ANFRAGE_NACH
    kein Audio, laeuft eine zweite Anfrage mit; die zuerst tonende gilt."""

    def __init__(self, text: str, stimme: str, tempo: str, faktor: float, sofort: bool = False):
        """`sofort`: beide Anfragen gleich (Gefahr, nicht vorgewaermt) - die schnellere gilt."""
        self.text, self.stimme, self.tempo, self.faktor = text, stimme, tempo, faktor
        self.zweite_nach = 0.0 if sofort else ZWEITE_ANFRAGE_NACH
        self.stuecke: list = []          # float32-Arrays, in Reihenfolge
        self.rate = 24000
        self.fertig = False
        self.fehler: BaseException | None = None
        self._neu = threading.Condition()
        threading.Thread(target=self._lauf, daemon=True).start()

    def _lauf(self) -> None:
        import asyncio
        try:
            asyncio.run(asyncio.wait_for(self._hole(), timeout=8))
        except BaseException as e:   # noqa: BLE001 - auch Abbrueche des Dienstes: der Sprecher faellt zurueck
            self.fehler = e
        finally:
            with self._neu:
                self.fertig = True
                self._neu.notify_all()

    def _dazu(self, dek, daten) -> None:
        import numpy as np
        neu = []
        for paket in dek.parse(daten):
            for f in dek.decode(paket):
                a = f.to_ndarray()
                a = a[0] if a.ndim == 2 else a
                a = a.astype(np.float32) / 32768.0 if a.dtype.kind == "i" else a.astype(np.float32)
                self.rate = f.sample_rate
                neu.append(a * self.faktor)
        if neu:
            with self._neu:
                self.stuecke.extend(neu)
                self._neu.notify_all()

    async def _hole(self) -> None:
        import asyncio
        import av
        import edge_tts
        gewinner: list[int | None] = [None]
        erstes = asyncio.Event()

        async def anfrage(nr: int) -> None:
            dek = av.CodecContext.create("mp3", "r")
            async for teil in edge_tts.Communicate(self.text, self.stimme, rate=self.tempo).stream():
                if teil["type"] != "audio":
                    continue
                if gewinner[0] is None:
                    gewinner[0] = nr
                    erstes.set()
                if gewinner[0] != nr:
                    return
                self._dazu(dek, teil["data"])
            if gewinner[0] is None:
                raise RuntimeError("edge-tts: kein Audio")

        def ruhig(t) -> None:
            # die verworfene Anfrage darf scheitern ("No audio received" unter Last) - ohne Konsolen-Warnung
            if not t.cancelled():
                t.exception()

        laeufe = {1: asyncio.create_task(anfrage(1))}
        laeufe[1].add_done_callback(ruhig)
        warte = asyncio.create_task(erstes.wait())
        await asyncio.wait({laeufe[1], warte}, timeout=self.zweite_nach, return_when=asyncio.FIRST_COMPLETED)
        warte.cancel()
        if gewinner[0] is None:
            laeufe[2] = asyncio.create_task(anfrage(2))
            laeufe[2].add_done_callback(ruhig)
        while True:
            offen = [t for t in laeufe.values() if not t.done()]
            w = laeufe.get(gewinner[0]) if gewinner[0] is not None else None
            if w is not None and w.done():
                for t in offen:
                    t.cancel()
                if w.exception() is not None:
                    raise w.exception()
                return
            if not offen:
                fehler = next((t.exception() for t in laeufe.values() if t.exception()), None)
                raise fehler or RuntimeError("edge-tts: kein Audio")
            await asyncio.wait(offen, return_when=asyncio.FIRST_COMPLETED)

    def stueck(self, i: int, bis: float):
        """Das i-te PCM-Stueck; wartet hoechstens bis `bis` (monotonic). ENDE: es kommt keins mehr; None: Zeit um."""
        with self._neu:
            while len(self.stuecke) <= i and not self.fertig:
                rest = bis - time.monotonic()
                if rest <= 0:
                    return None
                self._neu.wait(min(rest, 0.05))
            return self.stuecke[i] if i < len(self.stuecke) else ENDE

    def ganz(self, timeout: float = 8.0):
        """Das ganze Audio (fuer das Vorwaermen und Tests)."""
        import numpy as np
        with self._neu:
            self._neu.wait_for(lambda: self.fertig, timeout)
        if not self.stuecke:
            raise self.fehler or RuntimeError("edge-tts: kein Audio")
        return np.concatenate(self.stuecke), self.rate


class _Neural:
    """Microsofts neuronale Stimmen (wie "Vorlesen" in Edge), ueber edge-tts. Braucht Internet; faellt ein Satz
    aus, spricht ihn die Windows-Stimme. Gespielt wird ab dem ersten Stueck (_Strom), in einem durchgehenden
    Ausgabestrom je Ansage; Teilsaetze entstehen parallel, hoechstens VORAUS Stueck voraus."""

    VORAUS = 2

    def __init__(self, stimme: str, tempo: str, lautstaerke: int, ersatz: "_Sapi"):
        self.stimme, self.tempo, self.lautstaerke, self.ersatz = stimme, tempo, lautstaerke, ersatz
        self._stroeme: dict[str, _Strom] = {}
        self._fest: set[str] = set()
        self._schloss = threading.Lock()

    def strom(self, text: str, fest: bool = False, sofort: bool = False) -> _Strom:
        """Die Synthese von `text`: laufend, fertig (Zwischenspeicher) oder neu gestartet. `fest`: vorgewaermt,
        wird nie verdraengt."""
        with self._schloss:
            if fest:
                self._fest.add(text)
            s = self._stroeme.get(text)
            if s is None or (s.fertig and not s.stuecke):
                s = _Strom(text, self.stimme, self.tempo, self.lautstaerke / 100.0, sofort)
                self._stroeme[text] = s
                if len(self._stroeme) > 150 + len(self._fest):
                    for k in [k for k, v in self._stroeme.items() if v.fertig and k not in self._fest][:75]:
                        del self._stroeme[k]
            return s

    def vorwaermen(self, texte: list[str]) -> None:
        """Haeufige Satzanfaenge der Partie im Hintergrund synthetisieren, einer nach dem anderen (kein Gedraenge
        mit den gesprochenen Saetzen)."""
        def lauf():
            for t in texte:
                _still(lambda: self.strom(t, fest=True).ganz(8))
        threading.Thread(target=lauf, daemon=True).start()

    def vorbereiten(self, text: str, sofort: bool = False) -> None:
        """Der Sprechplan weiss, was als naechstes kommt: der Anfang wird schon synthetisiert."""
        for t in teilsaetze(text)[:self.VORAUS]:
            self.strom(t, sofort=sofort)

    def _synthese(self, text: str):
        return self.strom(text).ganz()

    _wasapi: bool | None = None     # None: noch nicht versucht

    def _ausgabe(self, rate: int):
        """Ausgabestrom ueber WASAPI (geteilt, Windows wandelt 24 auf 48 kHz): 60 ms Puffer statt der 182 ms von
        MME, das sounddevice sonst nimmt (gemessen 27.09., Carlos' Headset). Scheitert WASAPI einmal, dann MME."""
        import sounddevice as sd
        if self._wasapi is not False:
            try:
                apis = sd.query_hostapis()
                w = next(i for i, a in enumerate(apis) if "WASAPI" in a["name"])
                aus = sd.OutputStream(device=apis[w]["default_output_device"], samplerate=rate, channels=2,
                                      dtype="float32", latency=0.05,
                                      extra_settings=sd.WasapiSettings(auto_convert=True))
                _Neural._wasapi = True
                return aus
            except Exception as e:
                _Neural._wasapi = False
                print(f"  (Stimme: WASAPI geht nicht - {type(e).__name__}: {e}; nehme MME)", flush=True)
        return sd.OutputStream(samplerate=rate, channels=1, dtype="float32")

    def spreche(self, text: str, stopp: threading.Event, beim_ton=None, gilt=None, sofort: bool = False) -> bool:
        """`gilt()`: stimmt der Satz noch? Alle PRUEFEN_ALLE Sekunden gefragt - wenn nicht, bricht er ab.
        `sofort`: dringend (Gefahr, Antwort) - der erste Teil, wenn nicht im Speicher, mit zwei Anfragen zugleich.
        `beim_ton`: wird beim ersten Ton gerufen (Messung)."""
        import numpy as np
        teile = teilsaetze(text)
        stroeme: list[_Strom | None] = [None] * len(teile)

        def los(i: int) -> _Strom:
            if stroeme[i] is None:
                stroeme[i] = self.strom(teile[i], sofort=sofort and i == 0)
            return stroeme[i]

        for i in range(min(len(teile), self.VORAUS + 1)):
            los(i)
        aus = None
        naechste = time.monotonic() + PRUEFEN_ALLE

        def weiter() -> bool:
            nonlocal naechste
            if stopp.is_set():
                return False
            if gilt is not None and time.monotonic() >= naechste:
                naechste = time.monotonic() + PRUEFEN_ALLE
                return bool(gilt())
            return True

        try:
            for i in range(len(teile)):
                s = los(i)
                if i + self.VORAUS < len(teile):
                    los(i + self.VORAUS)
                n = 0
                while True:
                    # Haengt der Dienst beim ersten Teil, lieber gleich die Windows-Stimme als 8 s Stille (neuer Text
                    # braucht ~0,45 s, 9 von 10 unter 1,4 s - Aktualitaet vor Klang, Carlos 26.09.)
                    bis = time.monotonic() + (ERSTER_TON_HOECHSTENS if i == 0 and n == 0 else 4.0 if n == 0 else 3.0)
                    st = None
                    while st is None and time.monotonic() < bis:
                        st = s.stueck(n, min(bis, time.monotonic() + PRUEFEN_ALLE))
                        if not weiter():
                            if aus is not None:
                                aus.abort()
                            return False
                    if st is None or st is ENDE:
                        break
                    if aus is None:
                        aus = self._ausgabe(s.rate)
                        aus.start()
                        if beim_ton:
                            beim_ton()
                    aus.write(np.repeat(st.reshape(-1, 1), aus.channels, axis=1))   # WASAPI stereo: beide Ohren
                    n += 1
                if n == 0:
                    # kein Ton fuer diesen Teil: der Rest mit der Windows-Stimme
                    if aus is not None:
                        aus.stop()
                        aus.close()
                        aus = None
                    return self.ersatz.spreche(" ".join(teile[i:]), stopp, beim_ton if i == 0 else None, gilt)
            if aus is not None:
                # WASAPI wartet beim Stoppen nicht auf den Puffer: 0,1 s Stille hinterher, dann ist der Satz ganz raus
                aus.write(np.zeros((int(aus.samplerate * 0.1), aus.channels), dtype=np.float32))
                aus.stop()
            ende = time.monotonic() + 0.3
            while time.monotonic() < ende:
                if stopp.is_set():
                    return False
                time.sleep(0.02)
            return True
        finally:
            if aus is not None:
                try:
                    aus.close()
                except Exception:
                    pass


def _still(f, *a) -> None:
    try:
        f(*a)
    except Exception:
        pass


def teilsaetze(text: str) -> list[str]:
    """In Saetze teilen (nach . ! ? und nach dem Doppelpunkt, an dem die Stimme ohnehin absetzt), den ersten dazu am
    ersten Komma: der Anfang ("Geh rein,", "Vi ist im oberen Fluss,") wiederholt sich und liegt dann schon im
    Zwischenspeicher (vorgewaermt oder eben gesagt) - der erste Ton kommt sofort, waehrend der Rest entsteht.
    Gemessen 27.09.: neuer Text braucht beim Dienst ~0,45 s bis zum ersten Audio, egal wie lang; ein Viertel der
    Satzanfaenge einer Partie war am Komma schon einmal gesagt worden (heute ohne Teilung: ein Zehntel)."""
    teile = [t.strip() for t in re.split(r"(?<=[.!?:])\s+", text) if t.strip()]
    # der erste richtige Satz - nach einem kurzen Vorsatz wie "Ach nee:" der zweite
    i = 1 if len(teile) > 1 and len(teile[0]) <= 12 else 0
    if teile:
        k = teile[i].find(", ")
        if k >= 8 and len(teile[i]) - k > 6:      # auch "Heimerdinger hat Flash benutzt," / "bis 6 45."
            teile[i:i + 1] = [teile[i][:k + 1], teile[i][k + 2:]]
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
        self._schlange: queue.Queue = queue.Queue()   # (text, fertig, melde, eingereiht, noch_wahr) - der Plan
        self._vorrang: queue.Queue = queue.Queue()     # (text, fertig, melde, noch_wahr) - dringend, vom Plan
        self._antworten: queue.Queue = queue.Queue()   # Text - die Antwort auf seine Frage, vor allem anderen
        # Die Sprechtaste gehoert der Frage (Carlos 27.09.: "sobald ich meine PTT-Taste druecke, muss er nur zuhoeren
        # und darauf antworten - nach der Antwort kann er mit seinem Gelaber weitermachen"):
        #   _stumm: Taste gehalten - kein Ton, nichts faengt an;
        #   _frei geloescht: vom Druck bis die Antwort ganz gesprochen ist - nur Antwortsaetze, keine Ansage.
        # Was der Plan in dieser Zeit sagen wollte (Flash, Gank ...), wird verworfen, nicht nachgeholt: es steht
        # im Dashboard, und stimmt es danach noch, kommt es frisch aus dem Regelwerk.
        self._frei = threading.Event()
        self._frei.set()
        self._stumm = threading.Event()
        self._stumm_seit = 0.0
        self._antwort_ende = False      # die Antwort ist komplett eingereiht (antworte / antworte_ende)
        self._stopp = threading.Event()
        self._spricht = False
        self._pausiert_seit = 0.0
        self._bereit = threading.Event()
        threading.Thread(target=self._lauf, args=(sprache,), daemon=True).start()
        self._bereit.wait(timeout=5)

    def _lauf(self, sprache: str) -> None:
        motor = _Sapi(sprache, self.lautstaerke)
        if self.neural:
            motor = _Neural(self.neural, self.tempo, self.lautstaerke, ersatz=motor)
            # einmal stumm vorwaermen (Module, Verbindung): kalt kam der erste Ton nach 1,9 s, warm nach 0,6-0,75 s
            threading.Thread(target=lambda: _still(motor._synthese, "Los."), daemon=True).start()
        self._motor = motor
        self._bereit.set()
        while True:
            if self._stumm.is_set():
                if time.monotonic() - self._stumm_seit <= STUMM_HOECHSTENS:
                    time.sleep(0.02)
                    continue
                self._stumm.clear()   # Loslassen verpasst: nie fuer immer stumm
            melde = noch_wahr = fertig = None
            try:
                text = self._antworten.get_nowait()
                dringend = True
            except queue.Empty:
                if not self._frei.is_set():
                    # die Frage laeuft: warten, bis die Antwort (ganz) da ist - Ansagen verwerfen
                    if self._antwort_ende or time.monotonic() - self._pausiert_seit > PAUSE_HOECHSTENS:
                        if not self._antwort_ende:
                            print("  (Stimme: keine Antwort gekommen - geht weiter)", flush=True)
                        self._frei.set()
                    self._verwerfen()
                    time.sleep(0.02)
                    continue
                try:
                    text, fertig, melde, noch_wahr = self._vorrang.get_nowait()
                    dringend = True
                except queue.Empty:
                    try:
                        text, fertig, melde, rein, noch_wahr = self._schlange.get(timeout=0.05)
                    except queue.Empty:
                        continue
                    dringend = False
                    if fertig is None and time.monotonic() - rein > VERALTET:
                        if melde:
                            _still(melde, "verworfen", time.monotonic())
                        continue
                if not self._frei.is_set() or self._stumm.is_set():
                    # genau jetzt gedrueckt: die Ansage gehoert nicht mehr in diese Zeit
                    if melde:
                        _still(melde, "verworfen", time.monotonic())
                    if fertig is not None:
                        fertig.set()
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
            if self._stumm.is_set():    # genau jetzt gedrueckt: der Satz bricht vor dem ersten Ton ab
                self._stopp.set()
            self.protokoll.append(text)
            self._spricht = True
            ganz = False
            try:
                ton = (lambda m=melde: _still(m, "ton", time.monotonic())) if melde else None
                ganz = motor.spreche(sprechbar(text), self._stopp, ton, gilt if noch_wahr is not None else None,
                                     **({"sofort": dringend} if isinstance(motor, _Neural) else {}))
            except Exception as e:
                # Ein Audiofehler (Headset kurz weg, WASAPI verweigert) darf den Sprech-Thread nie beenden - sonst
                # ist der Coach fuer den Rest der Partie stumm. Beim naechsten Satz ueber MME.
                print(f"  (Stimme: {type(e).__name__}: {e} - weiter ueber MME)", flush=True)
                _Neural._wasapi = False
            finally:
                self._spricht = False
                if melde:
                    art = "ende" if ganz else ("widerrufen" if widerrufen[0] else "abgebrochen")
                    _still(melde, art, time.monotonic())
            if fertig is not None:
                fertig.set()

    def _verwerfen(self) -> None:
        """Waehrend der Frage: was der Plan sagen wollte, faellt weg (gemeldet als 'verworfen')."""
        for q in (self._vorrang, self._schlange):
            while True:
                try:
                    e = q.get_nowait()
                except queue.Empty:
                    break
                fertig, melde = e[1], e[2]
                if melde:
                    _still(melde, "verworfen", time.monotonic())
                if fertig is not None:
                    fertig.set()

    @property
    def beschaeftigt(self) -> bool:
        """Spricht gerade oder hat noch etwas in der Schlange - der Sprechplan gibt dann nichts Neues ab
        (gemessen 26.09.: Killian spricht 11-12 Zeichen/s, der Plan schaetzte 14 - Saetze stauten sich
        in der Schlange und kamen veraltet an). Waehrend einer Frage immer: dann soll er nichts abgeben."""
        return (self._spricht or not self._frei.is_set() or not self._schlange.empty()
                or not self._vorrang.empty() or not self._antworten.empty())

    def sage(self, text: str, dringend: bool = False, melde=None, noch_wahr=None) -> None:
        """`noch_wahr()`: stimmt der Satz noch (vor und waehrend des Sprechens gefragt)? `dringend`: vor alle
        wartenden Saetze, der laufende wird abgebrochen - aber nie eine Frage oder ihre Antwort.
        `melde(art, monotonic)`: "ton" beim ersten Ton, dann "ende" oder "abgebrochen" - die echte Verzoegerung."""
        fertig = threading.Event() if self.warten else None
        if dringend:
            self._vorrang.put((text, fertig, melde, noch_wahr))
            if self._frei.is_set() and self._antworten.empty():
                self._stopp.set()
        else:
            self._schlange.put((text, fertig, melde, time.monotonic(), noch_wahr))
        if fertig:
            fertig.wait(timeout=60)

    def vorwaermen(self, texte: list[str]) -> None:
        """Satzanfaenge, die in dieser Partie oft kommen (komponist.anfaenge), schon zu Spielbeginn synthetisieren."""
        m = getattr(self, "_motor", None)
        if hasattr(m, "vorwaermen"):
            _still(m.vorwaermen, [sprechbar(t) for t in texte])

    def vorbereiten(self, text: str) -> None:
        """Der Satz kommt gleich dran: seinen Anfang schon synthetisieren (nur die neuronale Stimme)."""
        m = getattr(self, "_motor", None)
        if hasattr(m, "vorbereiten"):
            _still(m.vorbereiten, sprechbar(text))

    def pausiere(self) -> None:
        """Sprechtaste gedrueckt: sofort still; bis `taste_los` kein Ton, bis die Antwort fertig ist keine Ansage.
        Der abgebrochene Satz kommt NICHT wieder (Live 27.09., 15:40: ein Satz, der bei jedem Druck erneut
        abbrach und danach wiederholt wurde, ergab "geh rein, geh rein, geh rein ..." bis zum Ausschalten)."""
        self._pausiert_seit = self._stumm_seit = time.monotonic()
        self._antwort_ende = False
        self._stumm.set()
        self._frei.clear()
        self._stopp.set()

    def taste_los(self) -> None:
        """Sprechtaste losgelassen: jetzt darf die Antwort kommen - und nur sie."""
        self._pausiert_seit = time.monotonic()
        self._stumm.clear()

    def antworte(self, text: str) -> None:
        """Die ganze Antwort auf einmal: zuerst sie, dann geht es normal weiter."""
        self._antworten.put(text)
        self._antwort_ende = True

    def antworte_teil(self, text: str) -> None:
        """Ein Satz einer gestreamten Antwort. Die Synthese beginnt sofort - nicht erst, wenn der vorige Teil zu
        Ende gesprochen ist (sonst ~0,45 s Pause dazwischen)."""
        m = getattr(self, "_motor", None)
        if hasattr(m, "vorbereiten"):
            _still(m.vorbereiten, sprechbar(text), True)
        self._pausiert_seit = time.monotonic()   # die Antwort laeuft: nicht "keine Antwort gekommen"
        self._antworten.put(text)

    def antworte_ende(self) -> None:
        self._antwort_ende = True

    def freigeben(self) -> None:
        """Keine Antwort (nur angetippt, Rauschen): gleich normal weiter."""
        self._antwort_ende = True

    # alter Name, wird noch von aussen benutzt
    def verstumme(self) -> None:
        self.pausiere()


class Stumm:
    def sage(self, text: str, dringend: bool = False, melde=None, noch_wahr=None) -> None:
        pass

    def vorbereiten(self, text: str) -> None:
        pass

    def vorwaermen(self, texte: list[str]) -> None:
        pass

    def antworte_teil(self, text: str) -> None:
        pass

    def antworte_ende(self) -> None:
        pass

    def pausiere(self) -> None:
        pass

    def taste_los(self) -> None:
        pass

    def antworte(self, text: str) -> None:
        pass

    def freigeben(self) -> None:
        pass

    def verstumme(self) -> None:
        pass
