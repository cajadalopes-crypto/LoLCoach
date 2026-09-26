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
| `lolcoach/aufzeichnung.py` | schreibt jede Partie als `aufnahmen/*.jsonl.gz` mit (+ `_bilder/`, `_ansagen.json`) |
| `lolcoach/minimap.py` | Champions auf der Minimap erkennen (Riot-Portraets, ~60 ms/Bild); Orte in Worten |
| `lolcoach/lage.py` | Lagebild (wer zuletzt wo), Beobachter-Thread live, Sichtungen aus Bildern (Cache) |
| `lolcoach/regeln.py` | Regelwerk: aus Zustand + Lagebild werden Ansagen (Saetze in `wissen/makro.toml`) |
| `lolcoach/sprechplan.py` + `stimme.py` | wer redet wann; Windows-Stimme Hedda |
| `lolcoach/bericht.py` | Post-Game-Bericht, optional mit Claudes Analyse |
| `lolcoach/dashboard.py` + `web/` | Live-Dashboard fuer den zweiten Monitor, http://127.0.0.1:8790 |
| `lolcoach/llm.py` | Claude ueber die Kommandozeile (Abo), spaeter API |
| `python -m lolcoach` | live; `abspielen [--nur-coach --dashboard --takt 0.05 --laut]`, `bericht`, `status`, `llm` |

Tests: `python tests/test_grundlage.py` und `python tests/test_regeln.py` (zwei
echte Bot-Partien, die zweite mit Minimap-Sichtungen). Neue Partie als Testfall:
`python werkzeuge/testfall_aus_aufnahme.py aufnahmen/<x>.jsonl.gz tests/<name>.jsonl.gz`.

Oberflaeche pruefen ohne Browserfenster: Aufnahme mit `--dashboard --takt 0.05`
abspielen, dann `Brainstone/werkzeuge/browserprobe.py http://127.0.0.1:8790/ name 3`.

Spielzustand ist eine REINE Funktion eines Schnappschusses: die API liefert
die Ereignisliste jedes Mal ganz. Was "neu" ist, entscheidet der Aufrufer
ueber die EventID. So laesst sich jede Aufnahme Sekunde fuer Sekunde
nachspielen, und Live und Aufnahme laufen durch denselben Code.

## Entwickeln ohne Ranked

Replays (`Dokumente/League of Legends/Replays/*.rofl`, nur aktueller Patch)
bedienen dieselbe Live-API. Fuer Kamera/Zeitsteuerung braucht es in
`C:\Riot Games\League of Legends\Config\game.cfg` unter `[General]` die Zeile
`EnableReplayApi=1`. Im Replay fehlt `activePlayer` (Zuschauermodus).

## Aufgaben: `OFFEN.md`

Alle offenen Wuensche stehen in `OFFEN.md` - nichts bleibt liegen. Oben steht
der verbindliche Grundsatz fuer Agenten (nur wenn wirklich effizient, kein
Kaltstart, keine vergeudeten Tokens). Neue Wuensche von Carlos sofort dort
eintragen, Erledigtes mit Commit nach unten.

## Arbeitsweise

Schnell, sparsam, Tests nur wo sie Zeit sparen. Wissen, das mit dem Patch
veraltet (Timer, Builds, Matchups), gehoert in `wissen/`, nie in den Code -
und jeder Wert dort traegt seinen Stand. Was die API wirklich liefert, wird
an echten Aufnahmen geprueft, nicht aus dem Gedaechtnis angenommen.
