# Bericht zu Auftrag 016 – Pflichtenheft 133448: sagen, was er sieht, Ketten statt Schweigen

Fertig am 29.09.2026. Es gab keine Testpartie, der Coach wurde nicht gestartet. Gemessen wurde nur an den drei
Aufnahmen, nachgespielt durch den Live-Weg:
- mit echtem Strategen über das Abo,
- mit Carlos' Fragen zur echten Zeit.

„Vorher“ ist derselbe Lauf auf `edcf583`. Einzelheiten stehen in `buecher/messungen.md` („Auftrag 016“).

## Commits

Code, Tests, Szenarien, Werkzeug, Protokolle und Probe-Daten liegen in einem Commit, Auftrag und Bericht in einem
zweiten (siehe `git log`).

## Abdeckung, vorher → nachher

| Partie | Flash | Jungler ≥ 20 s | Backs mit Kette | Back-Rufe mit Kette | Stille Lane | Sicherheit |
|---|---|---|---|---|---|---|
| 133448 | 2/8 → **8/8** | 2/10 → **10/10** | 3/4 → **4/4** | 0/5 → **6/6** | 67 → **43 s** | 2 → **0** |
| 192113 | 5/7 → **7/7** | 0/14 → **14/14** | 5/10 → **9/10** | 0/5 → **7/7** | 52 → **36 s** | 5 → **0** |
| 101426 | 5/6 → **6/6** | 2/19 → **18/19** | 4/10 → **8/10** | 1/8 → **13/13** | 137 → **35 s** | 1 → **0** |

- **Soll erreicht:** Flash 100 %, Jungler ≥ 90 %, Stille ≤ 45 s, Sicherheit 0.
- **Soll verfehlt:** Backs mit Kette in 2 von 3 Partien (Ziel oder Kauf fehlt, 3 Fälle).
- **Sicherheit** heißt: 0 Vorwärts-Sätze unter R1, 0 Angriffsrufe ohne Kill-Check, 0 innere Begriffe. Die Prüfung gilt
  jetzt auch für den Kern: „Rein auf Poppy!“ ohne Kill wird nur noch stumm protokolliert.
- **Protokolle:** `buecher/protokolle/NACHSPIEL_2026-09-29_133448.md`, `NACHSPIEL_2026-09-28_192113.md`,
  `NACHSPIEL_2026-09-28_101426.md`. Sie gehen Minute für Minute durch, mit Lage, Fragen und Notizen.

## Kritik

Beide Kritiker lasen den Lauf vor der letzten Kill-Sperre.
- **Carlos-Kritiker:**
  - Von 26 Notizen sind 5 erfüllt, 14 teils und 7 nicht.
  - Zufrieden wäre Carlos in etwa einem Drittel der Minuten.
  - Urteil: „Takt stimmt, Inhalt noch nicht“.
- **Challenger-Kritiker:** 2–3 gefährliche Sätze je Partie, fast alle Kampfrufe des Kerns ohne Kill. Die sind jetzt
  gesperrt.

## Tests

- Szenarien **305 / 309**, 3 übersprungen. Rot sind nur die alten Fälle (3× Wendepunkt-Probe, 0944).
- `tests/alle.py` 10 / 10, konstruierte Lagen 40 / 40.
- Die neuen Unit-Tests sind auf `edcf583` rot: Alle fünf Sätze aus 133448 kamen dort durch.
- **Angepasst, weil sie Stille verlangten:** `0455-sona-ohne-flash`, `1037-flash-ohne-ort` (jetzt Pflicht).
- **Angepasst an die neue Form:** `0841` („Flash weg“) und `1012` (erst das Kontroll-Auge stellen).
- **Wortgrenze:** +6 Wörter für einen Back-Ruf mit Kette.

## Offen

- **Inhalt statt Takt:**
  - Top-Wellen-Reflex, obwohl ADC und Support dort farmen.
  - Kauffehler („noch 225 Gold bis Axiombogen“ direkt nach dem Kauf, „nichts zu kaufen“ bei 4130 Gold).
  - Kern und Antwort widersprechen sich in weniger als 10 s.
  - Wiederholungen.
  - Carlos' konkrete Wünsche wie „hilf Volibear“, Freeze oder 1 gegen 1 bekommen nur „Notiert.“.
- **Latenz:** Der erste gültige Stratege-Satz kommt im Median nach 6–7 s. Die Kette wird bis zum Satzende gehalten,
  an Wendepunkten spricht deshalb oft der Kern-Ersatz.
- **Sprechmenge:** 87–111 ungefragte Sätze je 30 min, vorher 54–80. Laut Auftrag ist das kein Hauptmaß mehr, aber
  darüber wird zu entscheiden sein.
