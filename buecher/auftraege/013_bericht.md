# Bericht zu Auftrag 013 – Probe: Claude als Makro-Stratege

Fertig am 28.09.2026. Der Coach wurde nicht gestartet, am Live-Coach ist nichts geändert. Die Tabellen für Carlos
stehen in `buecher/protokolle/STRATEGE_PROBE.md`, die Einzelheiten in `buecher/messungen.md` („Auftrag 013“).

## Commits

- `19e2d67`: `werkzeuge/stratege_probe.py`, `STRATEGE_PROBE.md`, Rohdaten in `buecher/protokolle/stratege_probe/`
  (Momente, Prompts, Antworten, Blind-Vorlagen, Urteile) und messungen.md.
- Dazu kommt der Commit mit Auftrag und Bericht.

## Aufbau

- **Momente (70):**
  - 192113: 41 Fragen, die der Kern beantwortet, und 10 Wendepunkte ab 10:00.
  - 101426: 10 Leerlauf-Fenster aus 009 und 9 Wendepunkte ab 14:00.
- **Kontext:** wie live (Kopfzeile, `kern.kontext()`, Spielakte), dazu die Kern-Kandidaten mit Wert, Risiko und
  Grund sowie die Zeile R1.
- **Aufruf:** über das Abo, sonnet, gestreamt, mit vorgehaltenem Prozess wie live.
- **Zwei Läufe:**
  - Lauf 1 ist der Systemprompt STRATEGE wie im Auftrag.
  - Lauf 2 hat nur eine Änderung, eine Längenregel (≤ 25 Wörter). Grund: Lauf 1 sprach im Median 52 Wörter, rund 20 s
    Stimme. Das ist der handwerkliche Fehler, den der Auftrag als Beispiel nennt.

## Ergebnis

| | Lauf 1 | Lauf 2 (mit Längenregel) |
|---|---|---|
| **Gewinnquote Stratege** (Challenger / Carlos, ohne „gleich“) | 58 % / 65 % | **69 % / 70 %** |
| besser Stratege / Kern / gleich (Challenger) | 38 / 27 / 5 | 46 / 21 / 3 |
| besser Stratege / Kern / gleich (Carlos) | 45 / 24 / 1 | 48 / 21 / 1 |
| „falsch“ Stratege / Kern (Challenger, Carlos) | 28/5, 21/3 | 14/11, 18/11 |
| „gefährlich“ Stratege / Kern (Challenger, Carlos) | 3/1, 2/2 | 3/1, 3/1 |
| Fakten-Flags (automatisch) | 6 | 1 |
| Latenz erster Satz, Median / p90 | 1,7 / 2,8 s | **1,5 / 2,6 s** |
| Latenz ganze Antwort, Median / p90 | 5,4 / 6,8 s | 4,3 / 5,6 s |
| Abo | 70 Aufrufe in 6,5 min | 70 in 5,2 min |

Beim Abo gab es in beiden Läufen keine Grenze, keine Ablehnung und keinen Abbruch.

**Wo der Stratege gewinnt:**
- Bei Fragen (Lauf 2: 26 : 14 bzw. 28 : 12).
- An Wendepunkten (13 : 4 bzw. 14 : 5).
- Er geht auf Einwände ein, etwa „glaub dir, Top ist leer, dann Mid“.
- Er verknüpft Lagen, zum Beispiel „Rückzug, dann mit Sett und Brand zum Herold in 63 Sekunden“.

**Wo er verliert:** Er macht mehr Sachfehler als der Kern, und zwar systematisch.
- **Alte Sichtung als aktuell gelesen:** Aus „Yi vor 288 s in seiner Basis“ wurde „Yi ist seit 288 Sekunden in
  seiner Base, kein Gank-Risiko“ (9:42, von beiden Kritikern als gefährlich markiert). Dasselbe bei 7:13, 20:52 und
  24:15.
- **Unbelegte Bewegungen:** „Sett nähert sich“.
- **Unsinn im Tod:** „erst recallen“.
- **Baron zu dritt bei Todesrisiko 0,39** (20:24): ein R1-Verstoß, den mein Prüfer nicht erkannt hat.

Der automatische Faktenprüfer findet erfundene Zahlen, aber nicht diese Fehlerklasse; die fanden nur die Kritiker.

**Vorsicht beim Lesen:**
- Die Kern-Antworten waren in beiden Läufen wörtlich gleich. Trotzdem markierten die Kritiker sie einmal 3–5-mal und
  einmal 11-mal als falsch. Unterschiede unter etwa 5 Fällen sind Rauschen.
- Die Blind-Kritik ist nicht ganz blind, weil der Stil verrät, wer spricht.

## Zu entscheiden (Carlos)

1. **Richtung:** Bei Fragen und Wendepunkten gewinnt der Stratege klar, in 1,5 s bis zum ersten Satz. Er macht aber
   mehr Sachfehler, darunter gefährliche. Soll Claude das Makro übernehmen und der Kern Fakten, Sperren und
   Warnungen liefern?
2. **Falls ja,** braucht es vor einem Live-Einbau zwei Dinge:
   - eine Lage ohne Doppeldeutung, also „zuletzt gesehen vor 288 s“ statt „vor 288 s“;
   - eine harte R1-Sperre im Code, nicht nur im Prompt.

   Das wäre ein eigener Auftrag. Den Systemprompt habe ich nicht nach den Kritik-Ergebnissen angepasst.
