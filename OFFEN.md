# Offen - Wuensche von Carlos, Stand und Reihenfolge

Jeder Punkt stammt aus Carlos' Rueckmeldungen (Sprachnotizen im Spiel, Chat).
Erledigtes wandert nach unten mit Commit.

## In Arbeit

- **Wissensbasis Stufe 1**: jeder Champion aus Data Dragon (Faehigkeiten,
  Cooldowns je Rang, Reichweiten, Klassen), Items, Runen, Beschwoererzauber -
  je Patch automatisch, deutsch. Wird in jede Claude-Frage und das Briefing
  gegeben (eigener Champion, Lane-Gegner, alle zehn kurz).
- **Minimap mit 10-20 Bildern/s**: Desktop-Duplizierung statt GDI, Verfolgung
  im Umkreis statt Vollsuche. Positionen je Bild, Bilder 1/s, nur 20 min.
- **Flash an Spruengen erkennen**: Sprung ~15 px in einem Bild = Flash;
  Dashes laufen ueber mehrere Bilder. Champions mit Blink als unsicher markieren.
  Timer 5 min (minus Zauber-Tempo aus Items/Runen, wenn bekannt).
- **Chat lesen (unten links)**: Windows-Texterkennung; "Urgot Blitz" usw. aus
  Pings -> Timer fuer Flash, Zuenden, Teleport, ... Vor einem Kampf ansagen:
  "Urgot hat kein Flash, du kannst rein".

## Als Naechstes

- **Situative Anweisungen statt Standardsaetze**: Regel entscheidet WANN,
  Claude formuliert WAS aus der echten Lage (Position, Leben, Gold, Welle,
  Jungler) - fuer alles mit Vorlauf (Objective-Vorbereitung, Recall-Fenster).
  "Ich wuensche mir sehr viel Individualitaet beim Coach."
- **Briefing zu Spielbeginn**: Win-Condition, Matchup (wann traden, Spikes),
  Build gegen Lane-Gegner und gegnerisches Team, Plan. Nach der Lane-Phase:
  "was ist ab jetzt mein Job".
- **Leben der Mitspieler aus dem HUD** (Portraets ueber der Minimap): kein
  "Baron jetzt", wenn die eigenen Leute kein Leben haben (Partie 3, 25:27).
- **Anlauf-Warnungen im Mid-/Lategame**: "Vex kommt von unten auf dich zu",
  wenn du splitpushst.
- **Ward-Vorschlaege**: "du laeufst gerade am Tri-Bush vorbei, setz ein Ward" -
  passend zu Position, Laufweg und Spielstand.
- **Wellen-Zustand** aus den Vasallen-Punkten der Minimap: wie genau die Welle
  vorbereiten (freezen, slow push, crashen), nicht nur "vorbereiten".
- **Kampfanalyse im Bericht**: welcher Teamfight hat das Spiel gedreht, warum.
- **Ult-Timer**: aus Chat-Pings und Cooldowns der Wissensbasis.

## Erledigt

- Stimme natuerlich (neuronal, Conrad) - 9afaec7
- Unterbrechen ohne Verlust, Notizen, Teleport-Quest, Team-Zustand, Basis,
  volles Inventar, wenig Leben, Mid-Lane/Fluss - 32954ac
- Alte Minimap-Bilder aufraeumen (letzte 3 Partien), 4 Bilder/s - dcc4cee
