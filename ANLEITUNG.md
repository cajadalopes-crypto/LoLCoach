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
- Weniger Claude-Aufrufe (kein Briefing, keine situativen Sätze): `--ohne-gehirn`
