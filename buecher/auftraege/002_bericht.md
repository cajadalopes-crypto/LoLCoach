# Bericht zu Auftrag 002 – Sofort-Fixes aus Partie 213624

Fertig am 27.09.2026. Der Coach wurde nicht gestartet. Einzelheiten stehen in `buecher/messungen.md`, Abschnitt
„Auftrag 002“.

## Commits

- `323dcba`: S1–S7, sieben Protokolle neu (213624, 164326, 173159), messungen.md, OFFEN.md
- dazu dieser Bericht mit dem Auftrag

## Tests und Szenarien

- `tests/alle.py`: **10 / 10** grün. Neu ist `test_quest_tp`; `test_kern` hat zwei neue Prüfungen für Flash und Zahlen.
- Szenarien: **95 / 95** grün in 13 Dateien, 2 übersprungen (brauchen Claude). Konstruierte Lagen **40 / 40**.
- Neu ist `tests/szenarien/2026-09-27_213624.toml` mit 9 Szenarien. **8 waren mit d9fd85e rot.** Das neunte, die
  8-Wort-Grenze für Rückzüge, war schon vorher grün und bleibt als Wächter.
- 10 Stubs aus den Notizen liegen in `tests/szenarien/offen/`.
- Geändert, mit Begründung in messungen.md:
  - zwei Stellen in `test_bausteine`: Zahlen jetzt in Worten, Briefinglänge nach dem Tempo,
  - `144655` 0701 und 0449,
  - `102112` 2547.

## Kennzahlen (`kennzahlen.py --nur-kern`)

| Aufnahme | ungefragt je 30 min | davon INFO_FLASH | ohne INFO_FLASH | GEFAHR | Fassungswechsel | Schranken / Kampf / ohne Chance |
|---|---|---|---|---|---|---|
| 164326 | 48 (vorher 46) | 12 | 40 | 25 (vorher 32) | 0 | 0 / 0 / 0 |
| 173159 | 56 (vorher 52) | 9 | 49 | 30 (vorher 34) | 0 | 0 / 0 / 0 |
| 213624 | 47 | 3 | 43 | 7 | 1 (gab es schon vorher) | 0 / 0 / 0 |
| 102112, 133930, 140253, 144655 | 49 / 59 / 42 / 50 | 5 / 1 / 1 / 1 | 44 / 58 / 39 / 46 | 8 / 15 / 4 / 9 | 1 / 0 / 0 / 0 | alle 0 |

## Was jetzt anders ist

- **S1 Zahlen:**
  - Gold wird als Zahlwort gesprochen („dreitausendfünfhundert“, abgerundet). Kill-Bilanzen ohne Schrägstrich
    („sechs null“), Uhrzeiten mit der Null.
  - „3550 Gold“ las die Stimme vorher Ziffer für Ziffer, nachgewiesen mit edge-tts und Whisper
    (`werkzeuge/zahlenprobe.py`).
- **S2 Stimme:**
  - Die Proben liegen in `aufnahmen/stimmproben/`.
  - Tempo +50 %, das ist 20 % schneller als bisher.
  - PLAN hat höchstens 14 Wörter, GEFAHR höchstens 8.
- **S3 Flash:**
  - Neu ist die Ansage „Sona ohne Flash.“, in 213624 dreimal.
  - „Wie sieht's mit den Flashes aus?“ nennt jetzt alle Gegner und sagt ehrlich „weiß ich nichts“.
  - Die Regel „ohne Flash = Grund für den Angriff“ steht in allen Prompts.
- **S4 Quest-TP:**
  - Die API zeigt es nicht, Rivens Icon-Sprung schon: 5 von 5 Teleports erkannt, 0 Fehlmeldungen.
  - Das TP gilt ab 13:35 als bereit und ist nach Benutzung 390 s weg.
  - Nebenbei behoben: Ein gewähltes TP verschwand nach der Quest (`S12_SummonerTeleportUpgrade`).
- **S5 Warnungen:**
  - „Ziggs kommt“ bei klarer Überlegenheit ist weg.
  - RAUS ohne Beleg ist stumm, in 213624 viermal, darunter 1:11 und „Lass ihn, Turm!“.
  - 16:21 war kein Fehler mit toten Gegnern, siehe Punkt 1 unten.
- **S6 Gold:** Die AUC ist mit rohen und geschätzten Werten gleich 0,30. Die API-Items springen erst beim
  Wiederauftauchen, das erklärt die AUC aber nicht. Die Ursache bleibt offen, die Rufe bleiben stumm.

## Offen und zu entscheiden

1. **Zwei klar unterlegene Gegner** (16:21, Caitlyn mit 32 % und Sona): Soll S5.2 auch für zwei gelten?
2. **RAUS bei < 30 % Leben mit unbekanntem Gegnerbalken** (19:00): Soll das als Beleg reichen?
3. **Tempo:** +50 % ist meine Auslegung von „+20 %“, denn die Stimme lief schon mit +25 %. Ein Wert in `kern.toml`.
   - Carlos wählt die Stimme.
   - Killian hat etwa 0,95 s Stille je Satz, die das Tempo nicht kürzt. Abschneiden wäre der nächste Schritt.
4. **Quest-TP ab 13:35:** Die Quest war 1,5 bis 4 min früher fertig. Genauer geht es erst mit dem Quest-Platz im HUD
   (`hud.py`).
5. **Ungefragte Ansagen steigen durch INFO_FLASH:** Ohne ihn liegen 164326 und 173159 bei 40 und 49. Zählt
   INFO_FLASH zum Ziel ≤ 50?
