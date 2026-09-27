# Bericht zu Auftrag 001 – Qualitätsrunde 3 (Prüfung 27.09. c, R1–R10)

Begonnen 27.09.2026 21:17, fertig am selben Abend. Der Coach wurde nicht gestartet. Einzelheiten stehen in
`buecher/messungen.md`, Abschnitt „Qualitätsrunde 3“.

## Commits

- `8f0b8c3` Prüfung c und Postfach
- `8e91aab` R1–R9: Schranken, stummes Kampfmodell, Kaufplan nach Carlos' Build, Back-Rufe, Gefahr, WOHIN-Kurzform,
  kleine Wellen, Rückblick; Prüfschlüssel `je_10min_max`, `kategorie_max`; Kennzahl „Schranken-Verstöße“
- `9010ee9` R10 (Fassungswechsel), Warteregel in der Basis, sieben Protokolle, messungen.md, OFFEN.md

## Tests und Szenarien

- `tests/alle.py`: **9 / 9** grün (neu: `test_kaufplan`).
- Szenarien: **86 / 86** grün in 12 Dateien, 2 übersprungen (brauchen Claude). Konstruierte Lagen **40 / 40**,
  Modus-Sollwerte **16 / 16**.
- **29 neue Szenarien, alle zuerst rot:** 26 aus R1–R9 mit 842b502, 3 aus R10 und Ziel 2 mit 8e91aab.
- Geändert, mit Begründung in messungen.md:
  - drei konstruierte Lagen (R2, R4),
  - `muss_ziel` in 133930 1516 und 140253 1025 (R6.2).

## Kennzahlen (`kennzahlen.py --nur-kern`)

| Aufnahme | ungefragt je 30 min | Fassungswechsel | Kampf-Verstöße | Schranken-Verstöße | ohne Chance | Kehrtwenden |
|---|---|---|---|---|---|---|
| 102112 | 51 | 2 | 0 | 0 | 0 | 0 |
| 133930 | 63 | 0 | 0 | 0 | 0 | 0 |
| 140253 | 56 | 0 | 0 | 0 | 0 | 0 |
| 144655 | 56 | 0 | 0 | 0 | 0 | 0 |
| 164326 | **46** (vorher 67) | 0 | 0 | 0 | 0 | 0 |
| 173159 | **52** (vorher 74) | 0 | 0 | 0 | 0 | 0 |

145702 hat nur 0,5 Minuten mit Daten und zählt nicht.

## Ziele der Prüfung c

| Ziel | Stand |
|---|---|
| 1. Alle Szenarien grün | erreicht |
| 2. Ungefragte ≤ 50 je 30 min in 164326 und 173159 | 164326 erreicht (46); **173159 nicht (52)** |
| 3. Schranken-Verstöße 0 | erreicht |
| 4. Protokolle und messungen.md | erreicht |
| R10. Fassungswechsel | 102112: zwei Wechsel, beide begründet. Sonst 0. |

## Offen und zu entscheiden

1. **173159, 52 statt 50.**
   - Der Rest ist zur Hälfte GEFAHR, fast jede Warnung vor einer anderen Gegnermenge.
   - Eine Sperre für die zweite Warnung in 15 s habe ich gemessen und zurückgenommen: 69 statt 68 Sätze, und vor
     dem Tod um 22:13 fehlte die Warnung.
   - Der nächste Hebel ist die Gefahr-Schwelle selbst (13:00 warnte bei p_tod 0,09).
   - **Entscheidung:** eichen oder die Schwelle anheben?
2. **Fassungswechsel-Kennzahl.**
   - Sie erkennt ein neues Ereignis nur an einem neuen Namen. Die zwei Wechsel in 102112 folgen je auf Kills.
   - **Entscheidung:** Soll sie Kills, Objectives und Lebensverlust als Ereignis zählen, wie die Kehrtwenden?
3. **Weiter offen:** das Kampfmodell, siehe Entscheidung 2 aus Prüfung b.
   - Stumm sind ANNEHMEN, REIN, DREHEN, BESTREITEN, TP_SPIEL.
   - Stumm sind auch DRUECKEN, MIT_GRUPPE und NEHMEN, wenn sie am Kampf hängen: 229 stumme Rufe in sechs Partien.
   - Sie sprechen erst, wenn `kampf_eichung.py` besteht.
