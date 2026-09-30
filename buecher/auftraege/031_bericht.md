Guthaben: 0,00 $ (Abo-Aufrufe: 0)

# Bericht 031 – Challenger-Gehirn, Stufe 2: Modelle und Handbuch

Der vollständige Bericht steht in `buecher/challenger/phase2_bericht.md`. Dazu:
- `handbuch.md`: 77 Aussagen, alle mit n ≥ 200 und Beleg;
- `live_merkmale.md`: welche Merkmale live verfügbar sind.

**Commit:** Auftrag 031.
- **Neu:** `werkzeuge/challenger/modelle.py`, `analyse.py`, `handbuch.py`, `gehirn.py`; die Bücher oben.
- **Geändert (meine Dateien aus 030):** `phase1.py`, `test_kein_maphack.py`, `merkmale.md`. Die zwei Entscheidungen
  und zwei Label-Fehler ließen sich nur dort beheben.
- Nichts in `lolcoach/` geändert, den Coach nicht gestartet.

**Tests:**
- **Maphack-Test:** grün (1800 in der Lane-Phase), Sabotage-Gegenprobe fällt wie verlangt durch.
- **Plausibilität:** 13 von 14 bestanden.
- Keine Coach-Tests nötig, weil kein Coach-Code geändert wurde.

**Kennzahlen (Prüfung):**

| Modell | Ergebnis | Vergleich |
|---|---|---|
| Siegchance V, Brier | 0,159 | Gold-Abstand allein 0,170 |
| Policy π, Top-1 / Top-3 | 48 % / 78 % | 33 % / 65 % |
| Aktionswert Q, MSE | 0,01868 | 0,01873; knapp, z = 3,3. In „klar“-Lagen doppelt robust bestätigt: +2,0 ± 0,3 Punkte |
| Gefahr 60 s, Log-Loss | 0,366 | 0,498 |
| Jungler-Karte, Log-Loss | 1,33 | 2,25; Top-3 78 % |
| Klarheit | klar 18,5 %, geteilt 28,6 %, unklar 52,8 % | – |
| `bewerte()` | 4,2 ms Median, 8,8 ms max | – |

**Plausibilität, Einzelheiten:**
- Durchgefallen ist nur „Ace, Baron schlägt Farmen“. Untersucht: Nach einem Ace farmt in High-Elo niemand (9 von 577).
  Das Modell rät „in die gegnerische Basis“, doppelt robust bestätigt +6,7 ± 1,9 Punkte gegenüber Baron.
- Vorher gefunden und behoben: Objective war über den Erfolg definiert, Split/Lane/Gruppe über das Überleben. Danach
  besteht „Drache schlägt Seitenwelle“ (vorher durchgefallen).

**Offen, braucht eine Entscheidung:**
1. **Gegner-Items/-Level** zeigt die Live-API nur „wie zuletzt gesehen“. Entweder V, Q und Gefahr ohne sie (Brier
   0,163, schlägt den Gold-Abstand weiter) oder mit „Stand beim letzten Sehen“ neu trainieren.
2. **Back** ist wohl überbewertet (77 % der klaren Empfehlungen), weil ein Recall ohne Kauf (Tod beim Recall) nicht
   erkennbar ist. Soll Stufe 4 Back nur mit Grund sagen, bis die Live-Recall-Erkennung da ist?
3. **Ace mit Baron:** Soll der Coach „Schluss spielen“ vor „Baron“ sagen, wie es die Daten nahelegen?

**Für Carlos:** das Handbuch lesen, [handbuch.md](../challenger/handbuch.md). Nichts zu testen.
