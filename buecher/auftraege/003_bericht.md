# Bericht zu Auftrag 003 – Buch 11 (Führen) und Schritt 6 (Fragen)

Fertig am 27.09.2026. Der Coach wurde nicht gestartet. Einzelheiten stehen in `buecher/messungen.md`, Abschnitt
„Auftrag 003 / Schritt 6“.

## Commits

- `35cc616`: Teil A, Buch 11 (Zeitleiste, `danach`, WENDEPUNKT/FENSTER/VORSCHAU, Optionen), Schritt 6 (Fragen über den
  Kern), Kennzahlen, Szenarien, drei Protokolle, messungen.md, OFFEN.md
- dazu der Commit mit Bericht, Auftrag und Buch 11 (`buecher/11_fuehren.md`)

## Tests und Szenarien

- `tests/alle.py`: **10 / 10** grün. Neu in `test_kern`: `zwei_klar_unterlegene`.
- Szenarien: **150 / 153** grün in 14 Dateien, 2 übersprungen (brauchen Claude). Konstruierte Lagen **40 / 40**.
- **58 neue Szenarien, 57 zuerst rot** mit 6a97391. Der 58. ist ein Wächter für die 70-%-Grenze.
  - **Fragen-Probe:** alle 51 Fragen und Notizen aus 213624, vorher **0 / 51**, jetzt **51 / 51**.
- **Rot:** die Wendepunkt-Probe in 213624, 164326 und 173159 (s. unten).

## Kennzahlen (vorher 6a97391 → nachher, gleiche Messwerkzeuge)

| Kennzahl | Soll | 213624 | 164326 | 173159 |
|---|---|---|---|---|
| Leerlauf ab 14:00 | ≤ 10 % | 51 → 48 % | 60 → 52 % | 52 → 48 % |
| Wendepunkte ohne Satz in 60 s | – | 5 → 0 | 14 → 0 | 3 → 3 |
| Wendepunkt-Satz später als 3 s | 0 | 4 | 12 | 11 |
| Widersprüche | 0 | 1 → 1 | 0 → 0 | 0 → 0 |
| Stichwort-Antworten | 0 | 7 → 3 | – | – |
| Antworten ohne / mit Claude | – | 9 / 42 → 46 / 5 | – | – |
| Antwortzeit ohne Claude | ≤ 1 s | < 1 ms (offline) | – | – |
| ungefragt ohne INFO_FLASH/WENDEPUNKT je 30 min | ≤ 50 | 39 → 24 | 41 → 37 | 50 → 51 |

- **Stille um die Sätze:** Die 8 Stimmproben-Sätze dauern jetzt 17,0 s statt 29,5 s. Der erste hörbare Ton kommt
  nach 0,27 s statt 0,61 s.
- **Stimme:** Killian mit +25 %, wie Carlos gewählt hat.

## Offen und zu entscheiden

1. **Leerlauf bleibt um 50 % (Soll ≤ 10 %).**
   - Im Mid-Game hängen Turm- und Objective-Handlungen am ungeeichten Kampfmodell und sind stumm (Entscheidung 2).
     Übrig bleibt „Farm die Welle“, ein stummer Plan.
   - Gefragt nennt der Coach die Option jetzt mit „unsicher“.
   - **Entscheidung:** Soll ein solcher Plan auch ungefragt als „unsicher“ gesagt werden, bis die Kampf-Eichung
     besteht? Das würde den Leerlauf deutlich senken.
2. **Wendepunkt-Probe:** Nach Turmfall, Objective oder dem Verlassen der Basis kommt der Satz meist, aber oft erst nach
   4–10 s.
   - Ursachen: Er wartet hinter einem laufenden Satz, eine GEFAHR geht vor, mehrere Strukturen fallen in wenigen
     Sekunden (höchstens einer je 8 s), und der Schutzplan bleibt still.
   - **Entscheidung:** Darf ein WENDEPUNKT einen laufenden PLAN-Satz unterbrechen?
3. **`danach`** ist eine Projektion auf die Kandidaten dieses Takts, keine neue Rechnung aus einer projizierten Lage
   (Abweichung 1). Dadurch gibt es oft kein `danach`, vor allem in der Lane.
4. **Offen in OFFEN.md:** das Quest-Feld V im HUD, damit das Quest-TP schon vor 13:35 als bereit gilt.
