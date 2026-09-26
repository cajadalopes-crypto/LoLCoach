# LoLCoach

Ein Coach fuer League of Legends, der waehrend Ranked-Partien mitschaut und
per Sprache sagt, was jetzt zu tun ist und WARUM - wie ein Challenger-Kollege,
dem man per Discord den Bildschirm teilt. Dazu ein Review nach dem Spiel, in dem
man mit ihm redet. Anforderungen: `ANFORDERUNGEN.md`. Bedienung fuer Carlos:
`ANLEITUNG.md`. Offene Aufgaben: `OFFEN.md`.

## Harte Grenzen (nicht verhandelbar)

- **Kein Speicherlesen, keine Injection, kein Eingriff in den Spielprozess.**
  Vanguard erkennt das; Strafen bis Hardware-Bann.
- **Nur, was der Spieler selbst sehen koennte:** Bildschirm (Aufnahme von
  aussen: Minimap, Mitspieler-Leiste, Chat) plus die offizielle lokale Live
  Client Data API. Keine Infos ausserhalb der eigenen Sicht.
- **Keine Eingaben, keine Automatisierung.** Der Coach beobachtet und redet.
  Er drueckt keine Taste und klickt nichts - auch nicht "nur zum Testen".
  Push-to-Talk liest nur den Tastenzustand (GetAsyncKeyState).

## Aufbau

| Modul | Aufgabe |
|---|---|
| `liveapi.py` | Live Client Data API (127.0.0.1:2999) |
| `zustand.py` | Rohdaten -> Spielzustand (reine Funktion eines Schnappschusses) |
| `aufzeichnung.py` | jede Partie nach `aufnahmen/` (+ `_bilder/` mit Protokollen, `_ansagen.json`, `_notizen.md`, `_spielakte.md`) |
| `bild.py`, `lage.py` | Spielfenster finden; Beobachter-Thread (dxcam, 15 Bilder/s): Minimap, Mitspieler-Leiste, Chat, Wellen; Lagebild (wer zuletzt wo, Timer, Leben, Wellen); Nachspielen aus Protokoll/Bildern |
| `minimap.py` | Champions erkennen + Verfolger (Umkreis, 6 ms/Bild), Flash-Spruenge, Orte in Worten |
| `hud.py` | Mitspieler-Leiste ueber der Minimap: Leben, Ult bereit |
| `welle.py` | Vasallen-Punkte -> Wellenstand je Lane |
| `texterkennung.py`, `zauber.py` | Windows-OCR fuer den Chat; Zauber-/Ult-Timer (Chat-Pings, Minimap-Spruenge) |
| `regeln.py` + `wissen/makro.toml` | Regelwerk: WANN der Coach etwas sagt (Saetze und Schwellen in der toml) |
| `sprechplan.py`, `stimme.py` | wer redet wann; Stimme Killian (neuronal, edge-tts), Pause/Wiederholen bei Fragen |
| `gehirn.py`, `stratege.py` | Spielakte + Briefing, Midgame-Plan, situative Anweisungen (Claude formuliert WAS) |
| `champions.py`, `wissen/lexikon/` | Wissensbasis: Steckbriefe aus Data Dragon; Lexikon (Grundlagen, Saison 2026, alle 173 Champions) |
| `sprache.py`, `antworten.py` | Push-to-Talk, faster-whisper (RTX 4070), Sofort-Antworten oder Claude |
| `itemnamen.py` | fast richtige Item-Namen in Claude-Saetzen korrigieren |
| `dashboard.py` + `web/dashboard.html` | Live-Dashboard :8790 |
| `verlauf.py`, `review.py`, `review_server.py` + `web/review.html` | Spielverstaendnis (Zeitleiste + Momente), Claude-Review mit Belegen, Review-Oberflaeche :8791 mit Gespraech (Text und Sprache) |
| `bericht.py` | Text-Bericht (Markdown) |
| `llm.py` | Claude ueber die Claude-Code-Kommandozeile (Abo), schlank (eigener Systemprompt, stdin) |

`python -m lolcoach` = live. Weitere Befehle: `abspielen`, `review`, `bericht`,
`frage`, `mikrotest`, `status`, `llm` (siehe `--help`).

Spielzustand ist eine REINE Funktion eines Schnappschusses: die API liefert
die Ereignisliste jedes Mal ganz. So laeuft jede Aufnahme Sekunde fuer Sekunde
durch denselben Code wie das Live-Spiel.

## Pruefen

- `python tests/alle.py` - alle Tests (echte Partien als Testfaelle, ~10 s).
- `python werkzeuge/generalprobe.py --ab 13.9 --minuten 2.5` - der komplette
  Live-Weg ohne Spiel: nachgebauter Spielclient + Fenster mit aufgezeichneten
  Minimap-Bildern; der Coach laeuft als Prozess dagegen (`aufnahmen_probe/`).
  Hat bisher jeden Verdrahtungsfehler vor Carlos gefunden.
- Oberflaeche ohne Browserfenster: `Brainstone/werkzeuge/browserprobe.py <url> name 3`.
- Neue Partie als Testfall: `python werkzeuge/testfall_aus_aufnahme.py aufnahmen/<x>.jsonl.gz tests/<name>.jsonl.gz`.

## Aufgaben: `OFFEN.md`

Alle offenen Wuensche stehen in `OFFEN.md` - nichts bleibt liegen. Oben steht
der verbindliche Grundsatz fuer Agenten (nur wenn wirklich effizient, kein
Kaltstart, keine vergeudeten Tokens). Neue Wuensche von Carlos sofort dort
eintragen, Erledigtes mit Commit nach unten.

## Arbeitsweise

Gruendlich vor schnell (Carlos: "kein Zeitdruck - clean und funktionsfaehig").
Wissen, das mit dem Patch veraltet (Timer, Builds, Matchups), gehoert in
`wissen/`, nie in den Code - und jeder Wert dort traegt seinen Stand. Was die
API oder das Bild wirklich liefern, wird an echten Aufnahmen geprueft, nicht aus
dem Gedaechtnis angenommen. Claude-Ausgaben im Spiel: kurz (hart gekuerzt),
nur aus der Lage, Item-Namen abgesichert; im Review nur mit Beleg.
