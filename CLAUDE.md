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
| `bild.py`, `lage.py` | Spielfenster finden; Beobachter-Thread (dxcam, 60 Bilder/s): Minimap, HUD, Mitspieler-Leiste, Chat, Wellen, Platten, Spielbild; Lagebild (wer zuletzt wo, Timer, Leben, Wellen, Platten); Nachspielen aus Protokoll/Bildern |
| `minimap.py` | Champions erkennen (Kreis-Icons von CommunityDragon) + Verfolger (Umkreis, Halbmasken, Verdeckung, 6 ms/Bild), Flash-Spruenge mit Bestaetigung, Orte in Worten; Minimap-Groesse aus der game.cfg (`faktor()`, MinimapScale, nur gelesen) |
| `platten.py` | Platten-Ziffer in den Turm-Icons der Minimap (Vorlagen `wissen/platten_ziffern.png`) |
| `hud.py` | Mitspieler-Leiste ueber der Minimap: Leben, Ult bereit; eigene Q W E R D F bereit (gelbe Tastenbuchstaben) |
| `welle.py` | Vasallen-Punkte -> Wellenstand je Lane |
| `texterkennung.py`, `zauber.py` | Windows-OCR fuer den Chat; Zauber-/Ult-Timer (Chat-Pings, Minimap-Spruenge) |
| `regeln.py` + `wissen/makro.toml` | Regelwerk: WANN der Coach etwas sagt (Schwellen in der toml; die toml-Saetze nur noch ohne Minimap) |
| `bewertung.py` | Lagebewertung je Takt: alles verrechnet (Leben, Flash/TP/Ult aus dem HUD, Ankunftszeit jedes Gegners, Tiefe, Turmnaehe, Kraefte, Welle, Prio aller Lanes, Platten, naechstes Objective); `text()` fuer Claude |
| `komponist.py` | baut aus der Bewertung jede Ansage (Lage -> Handlung -> entscheidender Grund); Gefahr vor Chance |
| `entscheider.py`, `jungle.py` | der Plan zwischen den Ereignissen (Optionen, Sicherheit, Wert, Reihenfolge; nach Carlos' `Reasoning/LoL Reasoning.txt`); Jungler-Startseite und wahrscheinliche Kartenseite |
| `sprechplan.py`, `stimme.py` | wer redet wann (Vorrang, Themen-Sperre, kein "geh rein" direkt nach einer Warnung); Stimme Killian (neuronal, edge-tts) |
| `gehirn.py`, `stratege.py` | Spielakte + Briefing, Midgame-Plan, situative Anweisungen (Claude formuliert WAS) |
| `todesanalyse.py` | Rueckblick der letzten 45 s; beim Tod die Fakten fuer "warum und was naechstes Mal" |
| `profil.py` | Gedaechtnis ueber Partien: Kennzahlen je Aufnahme (Cache `aufnahmen/profil.json`), Fokus aus dem letzten Review -> Briefing, fruehere Partien -> Review |
| `champions.py`, `wissen/lexikon/` | Wissensbasis: Steckbriefe aus Data Dragon; Lexikon (Grundlagen, Mechaniken mit Zahlen, Saison 2026, alle 173 Champions in voller Tiefe); `wissen/mechanik.toml` maschinenlesbar |
| `sprache.py`, `antworten.py` | Push-to-Talk, faster-whisper (RTX 4070), Sofort-Antworten oder Claude |
| `itemnamen.py` | fast richtige Item-Namen in Claude-Saetzen korrigieren |
| `dashboard.py` + `web/dashboard.html` | Live-Dashboard :8790 |
| `verlauf.py`, `review.py`, `review_server.py` + `web/review.html` | Spielverstaendnis (Zeitleiste + Momente), Claude-Review mit Belegen, Review-Oberflaeche :8791 mit Gespraech (Text und Sprache) |
| `bericht.py` | Text-Bericht (Markdown) |
| `llm.py` | Claude ueber die Claude-Code-Kommandozeile (Abo), schlank (eigener Systemprompt, stdin) |

`python -m lolcoach` = live. Weitere Befehle: `abspielen`, `review`, `bericht`,
`frage`, `mikrotest`, `status`, `llm` (siehe `--help`). `live` und `abspielen` nehmen
`--kern alt|schatten|neu` (Entscheidungskern, Buch 0 Kapitel 3): der Kern (`lolcoach/kern/`) bestimmt in jeder
Stellung den Modus, sperrt die alten Regeln danach (Kapitel 14) und schreibt live `aufnahmen/<stamm>_kern.jsonl`.
Seit Schritt 3 ist `neu` Default: in LANE, BASIS und TOT entscheidet und spricht der Kern (Kandidaten je Modus in
`kern/modi/`, Wert und Gefahr in `wert.py`/`gefahr.py`, gehaltener Plan in `plan.py`, Budget in `sprechen.py`;
Welle nach Buch 1, Recall/Kauf nach Buch 3), die alten Regeln schweigen dort; `schatten` = das Regelwerk spricht,
der Kern schreibt "wuerde sagen"; `alt` = Stand Schritt 2. Schwellen und Startwerte: `wissen/kern.toml`.
Seit Schritt 4 (Buch 5) auch in SEITE, GRUPPE, UNTERWEGS, VERTEIDIGEN (`kern.KERN_MODI`): die Karten-Rechnung in
`kern/modi/karte.py` (Turm, Seitenwelle, Gruppe/TP, Welle rein und rotieren, Umwandeln bis zum Nexus). OBJECTIVE und
KAMPF spricht bis Schritt 5 noch das alte System. `LOLCOACH_KERN_SCHRITT=3` gibt fuer Gegenproben den Stand von
Schritt 3. Konstruierte Lagen: `tests/szenarien/konstruiert/*.toml` (`kern/testlage.py`, `tests/test_kern.py`).
Minimap-Farben sind relativ (dein Team blau) - im Coach heisst `blau` Team ORDER; `welle.zustaende` und der
Plattenleser drehen fuer die rote Seite um.

## Umbau nach den Buechern: `buecher/`

`buecher/00_entscheidungskern.md` sagt, wie der Coach entscheidet (Modus, Handlung, Wert,
Plan, Sprechen, Messen) und in welchen Schritten er umgebaut wird. Vor jeder Arbeit am
Entscheiden: das Buch ganz lesen, genau einen Schritt umsetzen (Kapitel 0), messen, in
`buecher/messungen.md` eintragen, committen, Carlos in drei, vier Saetzen sagen, was er
testen soll. Widerspricht die Wirklichkeit dem Buch, gilt die Wirklichkeit - unter
"Abweichungen vom Buch" eintragen, dann entscheiden.

**Arbeitsweise seit Buch 0: Beschwerde -> Szenario -> Modellaenderung.** Eine Beschwerde von
Carlos wird zuerst ein Szenario in `tests/szenarien/` (Lage aus der Aufnahme, Sollwert,
Begruendung). Erst dann aendert sich das Modell - so, dass das Szenario gruen wird und kein
anderes rot. Keine Einzelflicken mehr ("Live 27.09.: ..."-Sonderfaelle an einzelnen Regeln).
Seine Notizen per Sprechtaste ("Notiz ...") werden mit `werkzeuge/szenario_aus_notizen.py`
zu Stubs in `tests/szenarien/offen/` - der wichtigste Kanal, ueber den der Coach klueger wird.

Spielzustand ist eine REINE Funktion eines Schnappschusses: die API liefert
die Ereignisliste jedes Mal ganz. So laeuft jede Aufnahme Sekunde fuer Sekunde
durch denselben Code wie das Live-Spiel.

## Pruefen

- `python tests/alle.py` - alle Tests (echte Partien als Testfaelle, ~10 s).
- `python werkzeuge/szenarien.py` - war der Rat in dieser Lage richtig? Szenarien aus
  `tests/szenarien/*.toml` gegen das nachgespielte System (`--mit-claude`: auch Fragen und
  Review, `--lage`: nachgespielte Lage je Szenario, `--konstruiert`: die konstruierten Lagen aus
  `tests/szenarien/konstruiert/` ohne Aufnahme, `kern/testlage.py`). Buch 0, Kapitel 12.
- `python werkzeuge/kennzahlen.py [aufnahme ...]` - Ansagen je 30 min, Kehrtwenden, Verstoesse
  gegen Kapitel 9.4, Gefahr-Brier, Datenluecken, Szenario-Quote (ersetzt `sinnpruefung.py`).
- `python werkzeuge/generalprobe.py --ab 13.9 --minuten 2.5` - der komplette
  Live-Weg ohne Spiel: nachgebauter Spielclient + Fenster mit aufgezeichneten
  Minimap-Bildern; der Coach laeuft als Prozess dagegen (`aufnahmen_probe/`).
  Hat bisher jeden Verdrahtungsfehler vor Carlos gefunden.
- Oberflaeche ohne Browserfenster: `Brainstone/werkzeuge/browserprobe.py <url> name 3`.
- `python werkzeuge/wellen_eichung.py <aufnahme>` - Wellen-Eichung (Buch 1, 1.4) an den behaltenen Minimap-
  Ausschnitten: Bildtafel + `buecher/wellen_eichung/<stamm>.json` zum Beschriften, dann `--auswerten`. Die Ausschnitte
  der letzten drei Partien bleiben (`lage.bilder_aufraeumen`).
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
