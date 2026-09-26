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

- **Champion-Lexikon** (Agent): `wissen/lexikon/champions/*.md` - Riven, Camille,
  Graves ausfuehrlich mit Matchups, dann die haeufigsten Top-Gegner.

## Als Naechstes

- **Die Partie genauestens verstehen + Review nach dem Spiel (Carlos, 26.09.,
  hoechste Prioritaet)**: "Ich will nach einem Spiel mit dir reden koennen und
  dass du mir sagst, wo ich was falsch gemacht habe - kein denkloser AI-Slop,
  sondern was mich wirklich voranbringt." Umsetzung:
  - Spielverstaendnis: aus Aufnahme + Sichtungen + Chat + HUD eine Zeitleiste
    der Partie mit Momenten (Kaempfe, Tode, Objectives, Gold-Schwuenge,
    Positionen aller zur jeweiligen Zeit, Wellen-/Lane-Zustand, Zauber-Timer).
  - Momente mit Bild: Minimap-Bild und Lage zu jedem Schluesselmoment sichern
    (auch ueber die 20-min-Grenze hinaus, nur diese Momente).
  - Review-Oberflaeche: Zeitleiste + Minimap-Wiedergabe + Momentkarten; zu
    jedem Fehler: was passiert ist, warum es falsch war, was stattdessen -
    belegt mit Daten, nicht geraten.
  - Gespraech nach dem Spiel: im Review Fragen stellen (Text oder Sprache),
    Antworten mit Gehirn + Zeitleiste der Partie, auf Momente verweisen.
  - Qualitaet: nur Aussagen, die die Daten stuetzen; jede Lektion mit
    Spielzeit, Beleg und konkreter Alternative; wenige, dafuer wichtige Punkte.

- **Gehirn weiter ausbauen**: Bericht (Post-Game-Analyse) mit Spielakte und
  Lexikon; Regeln nutzen Fakten aus dem Gehirn (Ult-Cooldowns der Gegner,
  Spikes: "Urgot hat Level 6 - seine Ult richtet unter 25 % hin"); weitere
  Anlaesse situativ machen (Recall-Fenster, Lane-Gegner tot, Jungler gesehen),
  sobald die erste Partie zeigt, wie lange Claude live braucht.
- **Spielakte schneller**: 35 s gemessen (Quelle 17 000 Zeichen). Kuerzere Quelle,
  oder schon in der Champion-Auswahl/im Ladebildschirm anfangen (Client-API
  kennt die Champions frueher), damit das Briefing vor der ersten Welle (0:30) kommt.
- **Leben der Mitspieler aus dem HUD** (Portraets ueber der Minimap): kein
  "Baron jetzt", wenn die eigenen Leute kein Leben haben (Partie 3, 25:27).
- **Anlauf-Warnungen Mid-/Lategame**: "Vex kommt von unten auf dich zu" beim
  Splitpushen (Richtung aus dem Verfolger).
- **Ward-Vorschlaege**: "du laeufst gerade am Tri-Bush vorbei, setz ein Ward",
  passend zu Position, Laufweg, Spielstand (bestaetigt 26.09.). Faelight-Punkte
  (26.1) aus dem Lexikon beruecksichtigen.
- **Wellen-Zustand** aus den Vasallen-Punkten der Minimap: wie genau die Welle
  vorbereiten (freezen, slow push, crashen).
- **Kampfanalyse im Bericht**: welcher Kampf hat das Spiel gedreht, warum.
- **Ult-Timer** aus Chat-Pings und Cooldowns der Wissensbasis.
- **Champion-Lexikon erweitern** auf alle Champions (blockweise, Agent).
- **Item-Namen absichern**: Claude-Antworten gegen die Ladenliste pruefen
  ("Schwarzer Fleischer" statt "Schwarzes Beil" kam trotz Liste vor).
- **Bericht mit Minimap**: Jungler-Pfad, wo war der Jungler bei jedem Tod.
- **Offene Fakten aus dem Lexikon klaeren**: Inhibitor-Respawn (5:00 in
  objektive.toml, Wiki-Auszug 3:00), TP-Abklingzeit mit Quest (300/390/420 s).

## Braucht eine Partie

- Chat-Format der Pings ablesen (der Beobachter speichert `chat_*.jpg`, sobald
  neuer Text erscheint) und Chat-Bereich + Leser daran eichen (`lage.CHAT`).
- Flash-Erkennung an echten 15-Bilder/s-Daten pruefen (`sichtungen.jsonl.gz`
  hat jede Position; Fehlalarme durch Dashes/Verdeckung zaehlen).
- Briefing, Spielakte, situative Vorwarnungen live: rechtzeitig? passend?
- Neue Stimme (Killian), Unterbrechen/Wiederholen, Notizen im Spiel pruefen.
- Nachspielen aus `sichtungen.jsonl.gz` (15/s statt 1/s) - Sprung-Erkennung
  offline wiederholbar machen, sobald die erste Partie so ein Protokoll hat.

## Erledigt

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
