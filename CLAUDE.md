# LoLCoach

Ein Coach fuer League of Legends, der waehrend Ranked-Partien mitschaut und
per Sprache sagt, was jetzt zu tun ist und WARUM - wie ein Challenger-Kollege,
dem man per Discord den Bildschirm teilt. Dazu Post-Game-Analyse mit
Replay-Szenen. Anforderungen: `ANFORDERUNGEN.md`.

## Harte Grenzen (nicht verhandelbar)

- **Kein Speicherlesen, keine Injection, kein Eingriff in den Spielprozess.**
  Vanguard erkennt das; Strafen bis Hardware-Bann.
- **Nur, was der Spieler selbst sehen koennte:** Bildschirm (Aufnahme von
  aussen) plus die offizielle lokale Live Client Data API. Keine Infos
  ausserhalb der eigenen Sicht.
- **Keine Eingaben, keine Automatisierung.** Der Coach beobachtet und redet.
  Er drueckt keine Taste und klickt nichts - auch nicht "nur zum Testen".
  Ausnahme: die Replay-API steuert die Kamera eines REPLAYS (kein Live-Spiel).

## Aufbau

| Modul | Aufgabe |
|---|---|
| `lolcoach/liveapi.py` | Live Client Data API (127.0.0.1:2999) - holt Rohdaten |
| `lolcoach/zustand.py` | Rohdaten -> Spielzustand (reine Funktion, kein Gedaechtnis) |
| `lolcoach/wissen.py` + `wissen/*.toml` | gepflegte Wissensbasis (Timer, Makro, Matchups) |
| `lolcoach/aufzeichnung.py` | schreibt jede Partie als `aufnahmen/*.jsonl.gz` mit |
| `lolcoach/llm.py` | Claude ueber die Kommandozeile (Abo), spaeter API |
| `python -m lolcoach` | Live-Ansicht + Aufzeichnung; `abspielen`, `status`, `llm` |

Spielzustand ist eine REINE Funktion eines Schnappschusses: die API liefert
die Ereignisliste jedes Mal ganz. Was "neu" ist, entscheidet der Aufrufer
ueber die EventID. So laesst sich jede Aufnahme Sekunde fuer Sekunde
nachspielen, und Live und Aufnahme laufen durch denselben Code.

## Entwickeln ohne Ranked

Replays (`Dokumente/League of Legends/Replays/*.rofl`, nur aktueller Patch)
bedienen dieselbe Live-API. Fuer Kamera/Zeitsteuerung braucht es in
`C:\Riot Games\League of Legends\Config\game.cfg` unter `[General]` die Zeile
`EnableReplayApi=1`. Im Replay fehlt `activePlayer` (Zuschauermodus).

## Arbeitsweise

Schnell, sparsam, Tests nur wo sie Zeit sparen. Wissen, das mit dem Patch
veraltet (Timer, Builds, Matchups), gehoert in `wissen/`, nie in den Code -
und jeder Wert dort traegt seinen Stand. Was die API wirklich liefert, wird
an echten Aufnahmen geprueft, nicht aus dem Gedaechtnis angenommen.
