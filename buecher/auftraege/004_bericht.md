# Bericht zu Auftrag 004 – Überlegenheit, echte Antworten, Kampf-Eichung

Fertig am 28.09.2026. Der Coach wurde nicht gestartet. Einzelheiten stehen in `buecher/messungen.md`, Abschnitt
„Auftrag 004“.

## Commits

- `831ed03`: Teil A–D, drei Protokolle (213624 mit `--fragen`, 164326, 173159), messungen.md, OFFEN.md
- dazu der Commit mit Auftrag, Bericht und Rückfrage

## Tests und Szenarien

- **`tests/alle.py`: 9 / 10.**
  - `test_bausteine.kamera_gibt_nur_einmal_frei` scheitert an der Umgebung: Der Bildschirm ist jetzt 7680 × 2160. Er
    scheitert genauso auf dem Stand vor 004.
  - Die übrigen Bausteintests sind einzeln grün.
  - Neu ist `test_kern.keine_floskeln`.
- **Szenarien: 151 / 155** grün, 2 übersprungen. Konstruierte Lagen **40 / 40**. Fragen-Probe 213624 **50 / 51**.
- **Zuerst rot auf `2b455b3`:**
  - 8 Fragen: 1:19, 1:27, 4:04, 9:44, 9:55, 12:38, 16:31, 16:40.
  - `0944-nach-turmfall-kein-farmen`, `1621-66-prozent-mit-team` und `keine_floskeln`.
  - Der Wächter 173159 15:33 war schon grün, wie gewollt.
- **Rot bleiben:**
  - die Wendepunkt-Probe in 213624, 164326 und 173159;
  - die Frage 9:44: Im Takt des Turmfalls kennt der Kern nur FARMEN, die Turm-Option kommt 2 s später.

## Kennzahlen (vorher `2b455b3` → nachher)

| Kennzahl | Soll | 213624 | 164326 | 173159 |
|---|---|---|---|---|
| Leerlauf ab 14:00 | ≤ 10 % | 48 → 43 % | 52 → 48 % | 48 → 49 % |
| Wendepunkt-Verzug, Median ab Satzende | ≤ 3 s | 7,5 → 1,9 s | 4,3 → 2,5 s | 5,7 → 6,0 s |
| Wendepunkt-Satz später als 3 s | 0 | 18 → 15 | 29 → 29 | 25 → 26 |
| … davon stummes FARMEN ohne Vorschau | – | 8 | 18 | 20 |
| Floskeln | 0 | 9 → 0 | 0 → 0 | 0 → 0 |
| Widersprüche | 0 | 1 → 3 | 0 → 1 | 0 → 0 |
| Stichwort-Antworten | 0 | 3 → 1 | – | – |
| ungefragt ohne INFO_FLASH/WENDEPUNKT je 30 min | ≤ 50 | 24 → 44 | 37 → 46 | 51 → 53 |

**Kampf-Eichung (Teil D):** Sie besteht mit keinem Etikett (gold / koepfe / ueberlebt: Brier 0,320 / 0,309 / 0,251
gegen die Grundrate 0,249 / 0,243 / 0,135). Gold trennt mit jedem Etikett verkehrt herum (AUC 0,30 / 0,28 / 0,36).
`geeicht` bleibt `false`, die Kampfrufe sprechen nur über die Überlegenheits-Regel.

## Offen und zu entscheiden

1. **Wendepunkt-Probe:** Die meisten späten Sätze stehen hinter FARMEN ohne Vorschau. Das schweigt nach Teil A 1
   gewollt, die Probe zählt es aber als rot. Entscheidung in `004_frage.md`.
2. **Wächter 1621 umgestellt:** Bei 66 % mit zwei Mitspielern gilt jetzt die Überlegenheit, kein „Raus“ mehr. Carlos
   nannte genau diesen Ruf „gar keinen Sinn“. Bestätigung in `004_frage.md`.
3. **Kampf-Eichung:** Nächster Verdacht ist die Spielzeit (r = 0,56 mit gold_diff). Das ist nicht gemessen.
4. **Neue Widersprüche:**
   - 164326 35:00: zwei überlegene Turmziele in 15 s;
   - 213624 13:18: die Korrektur „ich bin beim Drachen“ gegen den Basis-Beobachter.
5. **Kampfrufe in der Bot-Partie:** GEFAHR steigt von 7 auf 23 (Teil B wirkt). In den echten Partien bleiben sie fast
   alle stumm.
