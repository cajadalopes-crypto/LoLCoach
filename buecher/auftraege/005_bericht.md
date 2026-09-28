# Bericht zu Auftrag 005 – Selbstprüfung mit unabhängigem Kritiker

Fertig am 28.09.2026. Der Coach wurde nicht gestartet. Die Einzelheiten stehen in `buecher/messungen.md`, Abschnitt
„Auftrag 005“. Die Klassen stehen in `005_kritik_runde1.md` und `005_kritik_runde2.md`.

## Commits

- `76e2a3b`: Runde 1, sechs Fehlerklassen behoben, 13 Szenarien, neue Protokolle, Klassen, Rückfragen
- `4d1c9b8`: Runde 2, gezählt, dazu messungen.md und OFFEN.md
- dazu der Commit mit Auftrag und Bericht

## Tests und Szenarien

- `tests/alle.py` **9 / 10**. Nur `kamera_gibt_nur_einmal_frei` scheitert, an der Umgebung (Bildschirm 7680 × 2160),
  wie in 004.
- Szenarien **163 / 167**, 2 übersprungen. Konstruierte Lagen **40 / 40**.
- Rot bleiben die Wendepunkt-Probe (3) und die Frage 9:44, beides wie nach 004.
- **13 neue Szenarien aus echten Fällen, alle zuerst rot.** Ein vierzehntes ist verworfen, weil der Kritiker irrte
  („Eklipse in 63 Sekunden“ war richtig).

## Kennzahlen: falsch je 30 min (Kritiker-Urteil)

| Partie | vorher | nach Runde 1 | nach Runde 2 | schwach vorher → nachher |
|---|---|---|---|---|
| 164326 (echt) | 11,9 | 9,8 | 9,8 | 27,3 → 12,6 |
| 173159 (echt) | 7,0 | 3,9 | 3,9 | 13,3 → 16,4 |
| 144655 (echt) | 6,2 | 3,1 | 3,1 | 15,5 → 15,5 |
| 213624 (Bot, Fragen) | 19,1 | 15,5 | 15,5 | 45,4 → 32,3 |
| 102112 (Bot) | 11,8 | 3,0 | 3,0 | 15,8 → 11,8 |

„Falsch“ gesamt: 56 → 36 Sätze. Nach Runde 2 wurde nichts mehr gebaut. Behoben (Klasse → 0 oder ein Rest mit anderer
Ursache):
- Überlegenheit übersieht Ungesehene (gefährlich, u. a. ein Tod in 173159),
- Wendepunkt-Kopf als falscher Grund,
- unmögliche Kaufzeit,
- Rückblick gegen das Wissen des Coaches,
- „Nein.“ auf Aussagen,
- geratene Objective-Gründe.

Vorsicht beim Vergleich: Vorher und nachher bewerteten verschiedene Kritiker. Eine nicht gebaute Klasse fiel von 3 auf
0, eine andere stieg von 3 auf 7.

## Offen und zu entscheiden

1. **`005_frage.md`:**
   - Warten am Inhibitor-Turm nach dem Tod (Schranke G2);
   - Rückkehr bei Belagerung (neue Regel für Buch 5, 7);
   - Baron, wenn drei Gegner ungesehen sind.
2. **Nicht gebaut, weiter falsch ≥ 2:**
   - Antwort und Ansage zählen „euch“ verschieden;
   - überlegene Turmziele wechseln sich ab;
   - FARMEN mit Vorschau, wo Back fällig ist (seit 004 hörbar);
   - Back in Gefahr oder in der Basis.
3. **Aus 004 weiter offen:** die Wendepunkt-Probe (`004_frage.md`) und der Kamera-Test.
