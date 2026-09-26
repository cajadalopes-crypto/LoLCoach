# OFFEN - alle Aufgaben, nichts bleibt liegen

> **GRUNDSATZ AGENTEN (Carlos, 26.09.2026, verbindlich):**
> Agenten nur, wenn sie WIRKLICH effizient sind. Kein Kaltstart-Mist, keine
> vergeudeten Tokens, kein verschwendetes Nutzungsguthaben. Ein Agent lohnt sich
> nur fuer abgeschlossene Arbeit mit klarer Grenze (eigene Dateien, eigenes Thema),
> die er ohne langes Einlesen schafft - hier gut moeglich: frisches Projekt, flache
> Struktur, CLAUDE.md + OFFEN.md reichen als Einstieg. Alles, was Kontext aus
> dem laufenden Gespraech braucht oder Dateien anderer beruehrt: selbst machen.
> Ein laufender Agent wird fortgesetzt (SendMessage), nicht neu gestartet.

Arbeitsweise: Jeder Wunsch aus Carlos' Rueckmeldungen (Chat, Sprachnotizen im
Spiel, `aufnahmen/*_notizen.md`) landet hier. Abgearbeitet wird von oben nach
unten, allein oder mit Agenten nach obigem Grundsatz. Erledigtes wandert mit
Commit nach unten. Was eine echte Partie braucht, steht unter "Braucht Partie".

## In Arbeit

- **Champion-Lexikon** (Agent): `wissen/lexikon/champions/*.md` - Riven, Camille,
  Graves ausfuehrlich mit Matchups, dann die haeufigsten Top-Gegner.

## Als Naechstes

- **Das Gehirn (hoechste Prioritaet nach dem Lexikon)**: "Es ist dein Gehirn -
  ein absoluter Top-Challenger. Extrem wichtig: das Wissen jederzeit flexibel
  nutzen." `lolcoach/gehirn.py`:
  - Spielakte zu Spielbeginn: aus Lexikon + Steckbriefen der zehn Champions
    verdichtet Claude einmal, was in DIESER Partie zaehlt (Matchup, Spikes,
    Cooldowns, Win-Conditions, Gefahren) - ~1500 Tokens, liegt im Speicher.
  - Bei jeder Claude-Anfrage (Frage, situative Anweisung, Briefing, Bericht):
    Spielakte + passende Lexikon-Abschnitte (nach Stichworten der Lage/Frage)
    + Live-Lage (Positionen, Timer, Leben, Gold, Items).
  - Regeln duerfen Fakten daraus nutzen (Ult-Cooldowns, Spikes, Blinks).
- **Situative Anweisungen statt Standardsaetze**: Regel entscheidet WANN,
  Claude formuliert WAS aus der echten Lage (Position, Leben, Gold, Welle,
  Jungler, Timer) - fuer alles mit Vorlauf. "Sehr viel Individualitaet."
- **Briefing zu Spielbeginn** (Win-Condition, Matchup, Build gegen Lane und Team,
  Plan) und nach der Lane-Phase ("was ist ab jetzt mein Job").
- **Leben der Mitspieler aus dem HUD** (Portraets ueber der Minimap): kein
  "Baron jetzt", wenn die eigenen Leute kein Leben haben (Partie 3, 25:27).
- **Anlauf-Warnungen Mid-/Lategame**: "Vex kommt von unten auf dich zu" beim
  Splitpushen (Richtung aus dem Verfolger).
- **Ward-Vorschlaege**: "du laeufst gerade am Tri-Bush vorbei, setz ein Ward",
  passend zu Position, Laufweg, Spielstand (bestaetigt 26.09.).
- **Wellen-Zustand** aus den Vasallen-Punkten der Minimap: wie genau die Welle
  vorbereiten (freezen, slow push, crashen).
- **Kampfanalyse im Bericht**: welcher Kampf hat das Spiel gedreht, warum.
- **Ult-Timer** aus Chat-Pings und Cooldowns der Wissensbasis.
- **Champion-Lexikon erweitern** auf alle Champions (blockweise, Agent).
- **Item-Namen absichern**: Claude-Antworten gegen die Ladenliste pruefen
  ("Schwarzer Fleischer" statt "Schwarzes Beil" kam trotz Liste vor).
- **Bericht mit Minimap**: Jungler-Pfad, wo war der Jungler bei jedem Tod.

## Braucht eine Partie

- Chat-Format der Pings ablesen (der Beobachter speichert `chat_*.jpg`, sobald
  neuer Text erscheint) und Chat-Bereich + Leser daran eichen (`lage.CHAT`).
- Flash-Erkennung an echten 15-Bilder/s-Daten pruefen (`sichtungen.jsonl.gz`
  hat jede Position; Fehlalarme durch Dashes/Verdeckung zaehlen).
- Neue Stimme (Killian), Unterbrechen/Wiederholen, Notizen im Spiel pruefen.
- Nachspielen aus `sichtungen.jsonl.gz` (15/s statt 1/s) - Sprung-Erkennung
  offline wiederholbar machen, sobald die erste Partie so ein Protokoll hat.

## Erledigt

- Gehirn (`gehirn.py`) + Stratege (`stratege.py`): Spielakte zu Spielbeginn,
  gesprochenes Briefing, Midgame-Plan nach der Lane-Phase, situative
  Vorwarnungen (Claude formuliert aus der Lage, sonst Standardsatz nach 12 s),
  Fragen mit Spielakte + Lexikon. Platten bis zum Turmfall (26.1). - siehe Commit "Gehirn"
- Grundlagen-Lexikon `wissen/lexikon/grundlagen.md` + `saison2026.md` - 32934eb

- Minimap 15 Bilder/s (dxcam, Verfolger im Umkreis 6 ms/Bild), Flash an
  Spruengen, Chat lesen (Windows-OCR), Zauber-Timer mit Ansagen/Antworten/
  Dashboard, Bilder nur 20 min - siehe Commit "Flash-Timer"
- Wissensbasis Stufe 1: `lolcoach/champions.py` (173 Champions) - bf43408

- Stimme Killian (Carlos' Wahl) - 202f354; neuronale Stimmen - 9afaec7
- Unterbrechen ohne Verlust, Notizen, Teleport-Quest, Team-Zustand, Basis,
  volles Inventar, wenig Leben, Mid-Lane/Fluss - 32954ac
- Alte Minimap-Bilder aufraeumen (letzte 3 Partien), 4 Bilder/s - dcc4cee
