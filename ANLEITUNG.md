# LoL-Coach - Anleitung

## Spielen mit Coach

Im Ordner `LoLCoach` ein Terminal öffnen und starten - **bevor** die Partie lädt:

    python -m lolcoach

Dann einfach spielen. Sobald das Spiel geladen ist, sagt Killian "Coach verbunden".

- **Dashboard** (für den Platz neben dem Spielfenster): http://127.0.0.1:8790
- **Fragen stellen:** vordere Maus-Seitentaste (Maus 5) halten, sprechen, loslassen.
  Andere Taste: `python -m lolcoach live --ptt f9`
  - Sofort-Antworten: "Wo ist der Jungler?", "Wann kommt Drache?", "Wer ist tot?",
    "Hat Urgot Flash?", "Hat Urgot Ult?", "Wie stehen wir?", "Was hat Vi für Items?"
  - Abwägungen gehen an Claude (ein paar Sekunden): "Soll ich Herold machen oder pushen?",
    "Was soll ich kaufen?", "Was meinst du damit?"
  - **Notiz für die Entwicklung:** mit "Notiz" anfangen - der Coach sagt nur "Notiert"
    und schreibt es mit. Danach lese ich es.
- **Flash-Timer:** Pingt ein Mitspieler im Chat "Urgot Blitz" (oder "urgot ult"), läuft
  ein Timer. Der Coach sieht Flash auch selbst auf der Minimap.

## Nach der Partie: Review

Das Review entsteht automatisch (1-3 Minuten nach Spielende). Ansehen:

    python -m lolcoach review

- Zeitleiste mit deinen Toden, Kämpfen, Objectives; Klick springt hin
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
