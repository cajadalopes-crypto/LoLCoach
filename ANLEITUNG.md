# LoL-Coach - Anleitung

## Spielen mit Coach

Doppelklick auf **`Coach starten.cmd`** im Ordner `LoLCoach` - oder im Terminal in
diesem Ordner (Windows PowerShell kennt kein `&&`, also nur diese eine Zeile):

    python -m lolcoach

Dann einfach spielen. Sobald das Spiel geladen ist, sagt Killian "Coach verbunden",
nach etwa 20 Sekunden kommt das Briefing - am Ende mit deinem Fokus aus dem Review
der letzten Partie. Stirbst du, sagt er dir, während du auf den Wiedereinstieg
wartest, warum und was du nächstes Mal tust.

- **Was der Coach rechnet:** Jede Ansage ist aus der Lage gerechnet, nicht vorgefertigt -
  wie schnell jeder Gegner frühestens bei dir sein kann (letzte Sichtung + Lauftempo), dein
  Leben und Flash (aus deinem HUD), wie tief du stehst, Level/Items gegen deinen Lane-Gegner,
  Welle und Prio aller Lanes, Platten (aus den Turm-Icons), was dein Gold kauft, was ein Tod
  gerade kostet, wer beim nächsten Objective zuerst da ist. Dazwischen sagt er den Plan
  ("1100 Gold reicht für Phage: Welle in den Turm, dann back - rechtzeitig für Larven um 8:00").
- **Dashboard** (für den Platz neben dem Spielfenster): http://127.0.0.1:8790 - oben der
  Kasten **Jetzt** mit genau diesen Zahlen und dem aktuellen Plan.
- **Fragen stellen:** vordere Maus-Seitentaste (Maus 5) halten, sprechen, loslassen.
  Andere Taste: `python -m lolcoach live --ptt f9`
  - Sofort-Antworten (ohne Wartezeit): "Was soll ich jetzt machen?", "Wo ist der Jungler?"
    (mit Ankunftszeit und wahrscheinlicher Seite), "Wie viele Platten?", "Wer hat Prio?",
    "Wann kommt Drache?", "Wer ist tot?", "Hat Urgot Flash?", "Hat Urgot Ult?",
    "Wie stehen wir?", "Was hat Vi für Items?"
  - Abwägungen gehen an Claude (ein paar Sekunden): "Soll ich Herold machen oder pushen?",
    "Was soll ich kaufen?", "Was meinst du damit?"
  - **Notiz für die Entwicklung:** mit "Notiz" anfangen - der Coach sagt nur "Notiert"
    und schreibt es mit. Danach lese ich es.
- **Makro-Stratege (seit 29.09.2026):** Deine Fragen, die Momente nach einem Turm, Objective,
  Respawn oder Kill-Doppel und längere Stille ab Minute 14 beantwortet Claude als Stratege.
  Der Coach rechnet weiter alles selbst, warnt immer zuerst und prüft jeden Satz des
  Strategen, bevor er ihn sagt. Timer, Flash, Stand, Kauf und "Was meinst du damit?"
  beantwortet weiter der Coach allein. Braucht Claude zu lange oder fällt aus, spricht der
  Coach still wie bisher weiter.
  - **Ausschalten**, falls live etwas klemmt: Coach beenden und neu starten mit
    `python -m lolcoach live --ohne-stratege` - oder dauerhaft in `wissen/kern.toml` unter
    `[stratege]` die Zeile `aktiv = true` auf `aktiv = false` setzen.
  - Was der Stratege gesagt und was die Prüfung verworfen hat, steht nach der Partie in
    `aufnahmen/<Partie>_stratege.jsonl`.
- **Was der Coach jetzt immer von sich aus sagt (seit 29.09.2026, Auftrag 016):**
  - jeden gegnerischen Flash, den er sieht, egal wie weit weg: „Poppy Flash weg.“
  - wo der gegnerische Jungler ist, sobald er nach 20 Sekunden ohne Sicht wieder auftaucht: „Teemo im oberen
    Fluss, bei dir in 6 Sekunden.“
  - wenn dein Lane-Gegner weit weg gesehen wird, mit Folge: „Poppy unten gesehen: drück deine Welle.“
  - bei jedem Back die Kette: was du kaufst und wohin danach.
  - in der Lane nach gut einer halben Minute Stille einen Wellen- oder Lane-Tipp vom Strategen, und wenn neben dir
    ein Mitspieler kämpft, ob du helfen sollst.
  - Sagst du „kein Kontroll-Auge“, schlägt er 5 Minuten lang keins vor.
- **Seit Auftrag 017 (29.09.2026):**
  - Claudes Antwort kommt am Stück, nicht mehr in Satzfetzen mit Pausen.
  - Es gibt keine Füllsätze mehr („Farm deine Welle weiter“); hat Claude nichts Neues, sagt er nichts.
  - In der Lane meldet sich Claude bei echten Anlässen (Welle kippt, Kanone kommt, Lane-Gegner weg oder zurück,
    Jungler gesehen, Flash weg, Spike kaufbar) mit Freeze, Slow Push oder Crash und dem Grund.
  - Es gilt immer ein Plan. Der Coach wechselt ihn nicht hin und her; ändert er ihn kurz danach, sagt er zuerst,
    was sich geändert hat („Jetzt, wo Poppy unten gesehen wurde: …“).
  - 60 Sekunden vor Drache, Herold oder Baron kommt die Vorbereitung, 40 Sekunden vorher „jetzt loslaufen“.
  - 12 Sekunden vor dem Respawn: Kauf und Ziel.
- **Claude über die API (seit 29.09.2026, Auftrag 019):** Liegt ein Schlüssel in `geheim/claude_api_key.txt`,
  antwortet Claude über die API statt über das Abo: im Mittel nach 1,6 s statt nach 6–7 s. Im Fenster steht dann
  „Claude: ueber die API“.
  - **Kosten:** etwa 0,25 $ je 30 Minuten Spiel (Claude Haiku 4.5). Sie stehen nach der Partie in
    `aufnahmen/<Partie>_kosten.json`.
  - **Zurück aufs Abo:** in `wissen/kern.toml` unter `[llm]` `weg = "abo"`. Fällt die API aus, nimmt der Coach von
    selbst 2 Minuten lang das Abo.
- **Seit Auftrag 018 (29.09.2026, aus deiner Graves-Partie):**
  - Der Coach liest die Objective-Symbole auf der Minimap (lila oben, Drache unten). Claude sieht dann „Herold lebt
    (Symbol auf der Karte zu sehen)“ und sagt nicht mehr „weiß ich nicht“.
  - Stehst du nach dem Respawn oder einem Kauf 20 Sekunden still in der Basis, kommt der Plan noch einmal („Los: …“),
    höchstens zweimal.
  - Türme immer mit Stufe („unter eurem äußeren Mid-Turm“); gewartet wird am vordersten stehenden.
  - Kauf: keine Items mehr, die mit deinem Inventar kollidieren (einzigartige Gruppen aus den Spieldaten, z. B.
    Schwarzes Beil und Lord Dominiks Grüße). Ab Level 9 schlägt er ein Elixier vor, wenn sonst nichts passt – aber
    nur mit freiem Platz: laut Spieldaten liegt das Elixier bis zum Trinken im Inventar (deine Beobachtung 36:47).
    Bei vollem Inventar sagt er es dazu.
  - Kämpft ein Mitspieler in bis zu 15 s Weg, sagt Claude „Hilf“ oder „Nicht hin“ mit Grund und Kill-Check.
  - Beim Tod bricht der laufende Satz sofort ab; der Tod-Satz hat höchstens 12 Wörter und sagt keinem Toten „geh
    zurück“.
- **Seit Auftrag 021 (29.09.2026, noch nicht freigegeben):** Claude führt den Plan (Ziel, zwei Schritte, gilt bis)
  und sagt Timer mit Aufgabe („Drache in 30 Sekunden, Tryndamere tot: mit Udyr zum Drachen“), das Fenster nach
  gegnerischen Toden und Roam-Gefahr; der Kern meldet Gegner in deinem Jungle. Kämpfe sagt er nur als „Nicht rein“
  mit Zahlen oder als zwei Optionen. Das Freigabe-Tor ist noch nicht erreicht (021_bericht.md).
- **Flash-Timer:** Pingt ein Mitspieler im Chat "Urgot Blitz" (oder "urgot ult"), läuft
  ein Timer. Der Coach sieht Flash auch selbst auf der Minimap.

## Nach der Partie: Review

Das Review entsteht automatisch (1-3 Minuten nach Spielende). Ansehen:

    python -m lolcoach review

- **Fortschritt** (Startseite): alle Partien im Vergleich - CS/min, CS bei 10:00, Tode
  vor 14:00, gehortetes Gold, Wardscore; grün/rot gegen deinen Schnitt; dazu der Fokus
  aus jedem Review und ob du ihn umgesetzt hast. Bot-Partien zählen nicht im Schnitt.
- Zeitleiste mit deinen Toden, Kämpfen, Objectives, Farm-Löchern; Klick springt hin
- Minimap-Wiedergabe: wer wann wo war (abspielen, ±10 s)
- Lektionen mit Spielzeit, Beleg und was du stattdessen tun solltest
- **Mit dem Coach reden:** unten tippen - oder Maus 5 halten und fragen,
  z. B. "Warum war der Tod bei 21:17 mein Fehler?". Die Frage bezieht sich auch
  auf den Zeitpunkt, den du gerade ansiehst.

## Wenn etwas nicht geht

- Stimme stumm: `python -m lolcoach live --stumm`; alte Windows-Stimme: `--stimme windows`
- Mikrofon/Taste testen ohne Partie: `python -m lolcoach mikrotest`
- Claude antwortet nicht: `python -m lolcoach llm "test"` - sagt es "nicht angemeldet",
  im Terminal `claude` starten und `/login`.
- Weniger Claude-Aufrufe (kein Briefing, keine situativen Sätze, kein Makro-Stratege): `--ohne-gehirn`
- Nur den Makro-Strategen aus: `python -m lolcoach live --ohne-stratege`
