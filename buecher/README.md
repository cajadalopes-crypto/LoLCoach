# Bücher für den LoLCoach

Diese Bücher machen aus dem Coach einen, der Situationen versteht. Sie sind für Claude Code geschrieben, das
danach programmiert, und werden in dieser Reihenfolge gelesen und umgesetzt.

| Buch | Thema | Stand |
|---|---|---|
| **0** | [Der Entscheidungskern](00_entscheidungskern.md): Modus, Plan, Wert, Sprechen, Messen, Umbauplan | fertig (27.09.2026) |
| 1 | Welle | kommt nach Schritt 2 |
| 3 | Recall, Tempo, Kauf | kommt nach Schritt 2 |
| 2 | Lane: Trading und Top-Matchups | kommt in Schritt 3 |
| 4 | Jungler-Wahrscheinlichkeit und Sicht | kommt in Schritt 3 |
| 5 | Mid-Game als Toplaner | kommt vor Schritt 4 |
| 6 | Objectives 2026 | kommt vor Schritt 5 |
| 7 | Kampf und Teamfight | kommt vor Schritt 5 |
| 8–10 | Riven, Camille, Graves | danach |
| 11 | Wie ein Coach lehrt (Review) | vor Schritt 7 |

## Ablauf je Schritt

1. **Carlos → Claude Code:** „Lies `buecher/00_entscheidungskern.md` und setze Schritt N um. Halte dich an
   Kapitel 0.“
2. **Claude Code:** setzt um, misst, trägt in `buecher/messungen.md` ein, committet und sagt Carlos, was er
   testen soll.
3. **Carlos:** spielt echte Partien (gern `--stumm`) und hält Momente per Sprechtaste mit „Notiz …“ fest.
4. **Carlos → Claude (Chat):** „Schritt N ist durch“. Claude liest `messungen.md`, die neuen Aufnahmen und
   Notizen, beschriftet die offenen Szenarien und schreibt das nächste Buch.

## Szenarien

Sollwerte liegen in `tests/szenarien/`. Stubs aus Carlos' Notizen liegen in `tests/szenarien/offen/`, bis
sie beschriftet sind. Jede Beschwerde wird zuerst ein Szenario, danach folgt die Änderung am Modell
(Buch 0, Kapitel 0 und 12).
