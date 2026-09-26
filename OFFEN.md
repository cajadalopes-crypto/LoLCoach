# OFFEN - alle Aufgaben, nichts bleibt liegen

> **GRUNDSATZ AGENTEN (Carlos, 26.09.2026, verbindlich):**
> Agenten nur, wenn sie WIRKLICH effizient sind. Kein Kaltstart-Mist, keine
> vergeudeten Tokens, kein verschwendetes Nutzungsguthaben. Ein Agent lohnt sich
> nur fuer abgeschlossene Arbeit mit klarer Grenze (eigene Dateien, eigenes Thema),
> die er ohne langes Einlesen schafft - hier gut moeglich: frisches Projekt, flache
> Struktur, CLAUDE.md + OFFEN.md reichen als Einstieg. Alles, was Kontext aus
> dem laufenden Gespraech braucht oder Dateien anderer beruehrt: selbst machen.
> Ein laufender Agent wird fortgesetzt (SendMessage), nicht neu gestartet.

Lebendes Dokument (Carlos: "flexibel, im Flow"): jeder Wunsch aus Carlos'
Rueckmeldungen (Chat, Sprachnotizen im Spiel, `aufnahmen/*_notizen.md`) landet
sofort hier. Kein Zeitdruck - sauber und funktionsfaehig vor schnell.
Abgearbeitet wird von oben nach unten, allein oder mit Agenten nach obigem
Grundsatz. Erledigtes wandert mit Commit nach unten.

## In Arbeit

- **Champion-Lexikon fuer alle Champions** (Agent, fortgesetzt statt neu gestartet):
  kompakte Eintraege fuer die restlichen ~144, blockweise Jungle/Mid/ADC/Support.

## Als Naechstes

- **Generalprobe ohne Spiel**: nachgebauter Spielclient (Live-API aus einer
  Aufnahme) + nachgebautes Spielfenster (Minimap-/HUD-Bilder an der echten
  Stelle) -> der komplette Live-Weg laeuft einmal durch: Beobachter mit dxcam,
  Verfolger, Mitspieler-Leiste, Regeln, Stratege, Dashboard, Ansagen,
  Aufnahme, Review danach. Findet Verdrahtungsfehler, bevor Carlos spielt.
- **Spielakte schneller**: 35 s gemessen (Quelle 17 000 Zeichen). Kuerzere Quelle
  und knappere Akte, damit das Briefing vor der ersten Welle (0:30) kommt.
- **Gehirn in die Regeln**: Spikes/Ults aus der Wissensbasis ("Urgot hat Level 6 -
  seine Ult richtet unter 25 % hin"), Ult-Timer aus Chat-Pings ("Urgot R")
  mit Cooldowns aus Data Dragon; weitere Anlaesse situativ (Recall-Fenster,
  Lane-Gegner tot, Jungler gesehen), sobald eine Partie zeigt, wie lange Claude
  live braucht.
- **Anlauf-Warnungen Mid-/Lategame**: "Vex kommt von unten auf dich zu" beim
  Splitpushen (Richtung aus dem Verfolger).
- **Ward-Vorschlaege**: "du laeufst gerade am Tri-Bush vorbei, setz ein Ward",
  passend zu Position, Laufweg, Spielstand (bestaetigt 26.09.). Faelight-Punkte
  (26.1) aus dem Lexikon beruecksichtigen.
- **Wellen-Zustand** aus den Vasallen-Punkten der Minimap: wie genau die Welle
  vorbereiten (freezen, slow push, crashen) - auch fuers Review.
- **Item-Namen absichern**: Claude-Antworten gegen die Ladenliste pruefen
  ("Schwarzer Fleischer" statt "Schwarzes Beil" kam trotz Liste vor).
- **Review per Sprache**: im Review mit dem Headset fragen (Push-to-Talk wie im
  Spiel), Antwort auch gesprochen.
- **Offene Fakten aus dem Lexikon klaeren**: Inhibitor-Respawn (5:00 in
  objektive.toml, Wiki-Auszug 3:00), TP-Abklingzeit mit Quest (300/390/420 s).

## Braucht eine Partie

- Chat-Format der Pings ablesen (der Beobachter speichert `chat_*.jpg`, sobald
  neuer Text erscheint) und Chat-Bereich + Leser daran eichen (`lage.CHAT`).
- Flash-Erkennung an echten 15-Bilder/s-Daten pruefen (`sichtungen.jsonl.gz`
  hat jede Position; Fehlalarme durch Dashes/Verdeckung zaehlen).
- Briefing, Spielakte, situative Vorwarnungen live: rechtzeitig? passend?
- Neue Stimme (Killian), Unterbrechen/Wiederholen, Notizen im Spiel pruefen.
- Review der ersten Partie mit vollem Protokoll (15/s, Leiste, Chat) ansehen:
  stimmen die Momente, sind die Lektionen belegt und hilfreich?

## Erledigt

- Review nach dem Spiel: `verlauf.py` (Zeitleiste + Momente aus Daten),
  `review.py` (Claude-Lektionen mit Beleg, Gespraech), Oberflaeche
  `python -m lolcoach review` / :8791 mit Zeitleiste, Minimap-Wiedergabe,
  Lektionen, Gespraech; automatisch nach jeder Partie - 87ebcda, 1327693
- Mitspieler-Leiste (Leben + Ult) aus dem HUD, Objective-Calls nur mit genug
  Leben, Ereignisprotokoll, Nachspielen aus dem Protokoll - 83c43d6

- Gehirn (`gehirn.py`) + Stratege (`stratege.py`): Spielakte, Briefing,
  Midgame-Plan, situative Vorwarnungen (Claude aus der Lage, sonst Standardsatz
  nach 12 s), Fragen mit Spielakte + Lexikon; Platten bis zum Turmfall - 5d59197
- Grundlagen-Lexikon `wissen/lexikon/grundlagen.md` + `saison2026.md` - 32934eb
- Minimap 15 Bilder/s, Flash an Spruengen, Chat lesen (Windows-OCR),
  Zauber-Timer mit Ansagen/Antworten/Dashboard, Bilder nur 20 min - 7bee474
- Wissensbasis Stufe 1: `lolcoach/champions.py` (173 Champions) - bf43408
- Stimme Killian (Carlos' Wahl) - 202f354; neuronale Stimmen - 9afaec7
- Unterbrechen ohne Verlust, Notizen, Teleport-Quest, Team-Zustand, Basis,
  volles Inventar, wenig Leben, Mid-Lane/Fluss - 32954ac
- Alte Minimap-Bilder aufraeumen (letzte 3 Partien), 4 Bilder/s - dcc4cee
