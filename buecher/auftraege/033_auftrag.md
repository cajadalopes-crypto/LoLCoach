# Auftrag 033 – Challenger-Gehirn, Stufe 3b: Wahrnehmung für die 14 offenen Entscheidungen (Claude, Chat, 30.09.2026 18:15)

**Guthaben: 0 $.** Keine Testpartien, starte den Coach nicht.
- 028 und 032 sind fertig; 033 darf **bestehende Dateien in `lolcoach/` ändern**.
- Alle Tests (`tests/alle.py`, `tests/makro/alle.py`) und Szenarien bleiben grün.

**Harte Regel (Buch 17, `CLAUDE.md`):** Carlos' Aufnahmen und Bilder sind hier erlaubt, **nur für das Sehen**. Kein
Entscheidungswissen daraus.

**Grundlage:**
- `buecher/17_makro_gehirn.md`, Teil B, „Was der Coach live sehen muss“;
- `buecher/challenger/abdeckung.md`, Abschnitt „Wahrnehmung fehlt → 033“;
- `lolcoach/makro/wahrnehmung.py`.

## 1. Die acht fehlenden Eingaben

| Eingabe | Für | Weg (Vorschlag, du prüfst) |
|---|---|---|
| **Wellen aller drei Lanes** | W11, W14, M6 | `welle.py` liest heute nur die eigene Lane: auf alle Lanes erweitern. Front, Größe, Richtung, gecrasht, prallt zurück |
| **Eigene Wards** (Ort, Ablauf, zerstört) | S10, S12, S14, T4, M5 | Ward-Symbole auf der Minimap, dazu der Kauf- und Setz-Zeitpunkt |
| **Busch ohne Sicht** | S11 | Busch-Orte (Karte) + Nebel der Minimap (dunkler = keine Sicht) |
| **Trinket-Ladungen** | S13 | HUD, Trinket-Feld (Zahl, Abklingzeit) |
| **Recall des Lane-Gegners** | B5 | Machbarkeit prüfen: Spielbild (Recall-Kanal), Verschwinden ohne Busch, danach neue Items im Scoreboard |
| **TP-Stand der Gegner** | T9 | TP-Sprung auf der Minimap, TP-Kanal am Ziel, Chat-Pings, Abklingzeit aus `wissen/` |
| **Objective-Kopfgeld** | O12 | Markierung auf der Minimap bzw. Objective-Symbolen |
| **Beschwörerzauber der Mitspieler** (Flash) | P2 | Machbarkeit prüfen: HUD bzw. Scoreboard, sonst Chat |

**Für jede Eingabe gilt:**
- Treffsicherheit an **beschrifteten Bildern** aus Carlos' Aufnahmen messen, mindestens 50 Stichproben, Treffer und
  Fehlalarme getrennt.
- **Ist sie nicht verlässlich** (Treffer < 90 % oder Fehlalarme > 5 %), wird sie nicht geraten: Die Entscheidung
  schweigt ohne sie. Das steht in `wahrnehmung.py` und im Bericht.
- **Laufzeit:** Der Beobachter-Takt bleibt im heutigen Rahmen (Minimap 60 Bilder/s). Neue Leser laufen so oft wie
  nötig, nicht öfter.

## Zeit sparen

- **Reihenfolge nach Wert:** zuerst die Wellen aller Lanes (Kern des Makro), dann eigene Wards, dann der TP-Stand der
  Gegner. Danach der Rest.
- **Zeitbox für die fünf kleinen Eingaben** (Busch ohne Sicht, Trinket, Recall des Lane-Gegners, Kopfgeld,
  Mitspieler-Flash): höchstens 30 min je Eingabe.
  - Ist sie bis dahin nicht verlässlich, gilt „nicht verlässlich“: Die Entscheidung schweigt, weiter zur nächsten.
  - Diese Eingaben brauchen 30 Stichproben statt 50.
- **Vorhandenes wiederverwenden:** die beschrifteten Wellenbilder in `buecher/wellen_eichung/` und die Leser in
  `minimap.py`, `welle.py`, `hud.py`, `zauber.py`.
- **Kein Nachspiel per Abo, keine Kritiker.** Hier geht es nur ums Sehen.
- **Tests:** Während der Arbeit nur die betroffenen Tests, am Ende einmal alles.

## 2. Reste aus 028

1. **Inventar gegen Wiederholungskäufe:** Stahlkappen wurden 32:30 in 134020 empfohlen, obwohl gekauft (14:51).
   Jede Kauf-Empfehlung prüft das Inventar, auch die Stiefel-Stufe.
2. **Satzbug** „Jetzt, wo Baron in 34 Sekunden aufgetaucht ist“ (091311, 19:24).
3. **Elixier-Regel aus den High-Elo-Daten:**
   - Wann kaufen Master+ Elixiere (Anzahl fertiger Items, freie Plätze, Minute)?
   - Bis das steht, gilt die Übergangsregel aus 028: fünf fertige Items plus freier Platz, nie mitten im Spiel.
4. **Szenario 2302** an den früheren Back anpassen.
5. **TP-Kanal:** `wissen/uhren.toml` rechnet noch mit 4 s. Laut Recherche aus 032 sind es seit Patch 25.S1.1 3 s.
   Prüfen und mit Stand korrigieren.

## Ende

- **`buecher/challenger/phase3b_bericht.md`:**
  - Zeile 1: „Guthaben: 0,00 $ (Abo-Aufrufe: N)“;
  - je Eingabe: Weg, Treffsicherheit, Fehlalarme, Laufzeit, verlässlich ja/nein;
  - die neue Abdeckung („erkannt“ x/111);
  - die Reste aus 028.
- Knapp. Committen. Starte den Coach nicht.
