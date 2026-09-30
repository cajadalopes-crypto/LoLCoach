Guthaben: 0,00 $ (Abo-Aufrufe: 0)

# Bericht 032 – Challenger-Gehirn, Stufe 3a: Makro-Rechner und Regeln für alle 111 Entscheidungen

Der vollständige Bericht steht in `buecher/challenger/phase3a_bericht.md`, die Tabelle aller 111 in
`buecher/challenger/abdeckung.md`.

**Commit:** Auftrag 032.
- **Neu:** `lolcoach/makro/` (Paket), `tests/makro/`, `wissen/makro/`, `werkzeuge/challenger/abdeckung.py`,
  `ults_aus_lexikon.py`, dazu die Bücher.
- **Geändert:** meine Dateien `werkzeuge/challenger/modelle.py` und `gehirn.py` (Abschnitt 0).
- Keine bestehende Datei in `lolcoach/` geändert. Den Coach nicht gestartet.

**Tests:**
- `tests/makro/alle.py`: 4/4 grün (Rechner 11, Register 5, Entscheidungen 111, Gehirn-Korrektur 4).
- `tests/alle.py`: 11/11 grün.

**Kennzahlen:**

| | |
|---|---|
| Abdeckung | gerechnet 111/111, gesagt 111/111, getestet 111/111 – **Tor 3a erreicht**; erkannt 97/111 (+14 für 033) |
| Modelle ohne Gegner-Items/-Level | Siegchance Brier 0,163 (Gold-Abstand 0,170), Policy Top-1 48 %, Q R² 0,086 gegen 0,076 ohne Aktion |
| Back-Korrektur | Back vorn nur noch in 27 % der Lagen (vorher 77 % der klaren), immer mit Grund |
| Klarheit neu | klar 22 %, geteilt 25 %, unklar 52 %; „unklar“ gibt die häufigste High-Elo-Aktion |
| Laufzeit | `bewerte()` 4,7 ms |
| Regeln und Quellen | 32 Regeln, 30 Quellen (26 Web mit Datum), 33 Ults aus dem Lexikon |

**Widersprüche, die Daten gewinnen:**
- Trinket bis 2:50 → 2:15 (8 % der ersten Ganks davor);
- Herold wenig wert (−1,1 Punkte);
- nach einem Ace Basis vor Baron;
- Split nur mit Sicht.

**Für 033 (Wahrnehmung fehlt):**
- eigene Wards;
- Wellen der anderen Lanes;
- Busch ohne Sicht;
- Trinket-Ladungen;
- Recall des Lane-Gegners;
- TP-Stand der Gegner;
- Objective-Kopfgeld;
- Mitspieler-Flash.

Außerdem rechnet `wissen/uhren.toml` noch mit 4 s TP-Kanal statt 3 s. Die Datei habe ich nicht geändert.

**Für Carlos:** nichts zu testen.
