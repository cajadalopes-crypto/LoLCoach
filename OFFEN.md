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

- (nichts - alles ohne echte Partie Machbare ist erledigt)

## Als Naechstes

- (leer - neue Wuensche von Carlos kommen hierher)

## Braucht eine Partie

Alles hier ist vorbereitet und mit Aufnahmen/Generalprobe getestet - die echte
Partie ist der letzte Schritt. Nach Carlos' naechster Partie: Log, Aufnahme,
Notizen und Review durchsehen und nachschaerfen.

- Chat-Format der Pings ablesen (der Beobachter speichert `chat_*.jpg`, sobald
  neuer Text erscheint) und Chat-Bereich + Leser daran eichen (`lage.CHAT`).
- Flash-Erkennung an echten 15-Bilder/s-Daten pruefen (`sichtungen.jsonl.gz`
  hat jede Position; Fehlalarme durch Dashes/Verdeckung zaehlen).
- Wellen-Erkennung und Recall-Fenster live pruefen (in Partie 3 neunmal - passend?).
- Briefing, Spielakte, situative Vorwarnungen live: rechtzeitig? passend? Dann
  entscheiden, welche weiteren Anlaesse situativ werden (Recall-Fenster, Lane-Gegner
  tot, Jungler gesehen) - je nachdem, wie lange Claude live braucht.
- Stimme Killian, Unterbrechen/Wiederholen, Notizen, Fragen im Spiel pruefen.
- Review der ersten Partie mit vollem Protokoll (15/s, Leiste, Chat, Wellen) ansehen:
  stimmen die Momente, sind die Lektionen belegt und hilfreich?

## Erledigt

- Review per Sprache (Push-to-Talk im Review, Antwort gesprochen) - 54f7e40
- Offene Fakten: Inhibitor 5:00, Teleport-Abklingzeit nach Zeit/Level/Quest - bca57f3
- Tests fuer die Bausteine + tests/alle.py - 0eb3a7f; Doku + ANLEITUNG.md - 37cc39c

- Wellen-Zustand aus Vasallen-Punkten, Recall-Fenster, Wellen im Review - 87ccd7d
- Ward-Vorschlaege (Stelle + Anlass) - bd96a61
- Anlauf-Warnungen ("X kommt ... auf dich zu"), Port-Schutz der Server - 0341eb3
- Ult-Timer aus Chat-Pings, Level-6-Warnung mit dem Inhalt der Ult - 278f2e0
- Generalprobe ohne Spiel (`werkzeuge/generalprobe.py`) - fand Absturz, Flash-
  Fehlalarme bei stehenden Bildern, zu lange Ansagen, Meta-Gerede; alles behoben;
  Spielakte + Briefing in 22,7 s statt 46 s; Item-Namen abgesichert - cf618e1
- Champion-Lexikon: alle 173 Champions (29 ausfuehrlich, 144 kompakt) -
  34b8891 ... 5217081

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
