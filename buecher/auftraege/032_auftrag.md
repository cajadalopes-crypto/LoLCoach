# Auftrag 032 – Challenger-Gehirn, Stufe 3a: Makro-Rechner und Regeln für alle 111 Entscheidungen (Claude, Chat, 30.09.2026 17:45)

**Guthaben: 0 $.** Keine Testpartien, starte den Coach nicht.

**Darf parallel zu 028 laufen.** Daher gilt:
- **Nur neue Dateien** in `lolcoach/makro/` (neues Paket), `tests/makro/`, `wissen/makro/`, `werkzeuge/challenger/`
  und `buecher/challenger/`.
- An bestehenden Dateien in `lolcoach/` nichts ändern. Importieren ist erlaubt.
- Nur die eigenen Pfade committen.

**Grundlage:**
- `buecher/17_makro_gehirn.md`: Teil B (111 Entscheidungen), „Entscheidungen zu Stufe 2“ und Teil C (Stufe 3a);
- `buecher/challenger/phase2_bericht.md`, `handbuch.md`, `werkzeuge/challenger/gehirn.py`.

## 0. Entscheidungen zu Stufe 2 umsetzen (`werkzeuge/challenger/`)

1. **Modelle ohne Gegner-Items und -Level** neu trainieren (Siegchance, Aktionswert, Policy, Gefahr). Die neuen
   Zahlen kommen in den Bericht.
2. **Back-Korrektur** in `gehirn.bewerte()`: Back nur mit einem Grund aus Regel oder Rechner (Liste in Buch 17).
3. **Nach einem Ace:** Das Modell entscheidet, der Rechner prüft Weg gegen Respawns (Punkt 1 unten).
4. **Klarheit „unklar“** gibt die häufigste High-Elo-Aktion (Policy) mit Ziel zurück, nie „nichts“.

## 1. Rechner (`lolcoach/makro/rechner.py`, reine Funktionen, jede mit Tests)

- **Ankunftszeit** von A nach B: Wege über die Karte, Lauftempo aus dem Spiel. Vorhandenes aus `lolcoach/kern`
  benutzen, nicht nachbauen.
- **Wellenkosten:** Gold und XP, die du verlierst, wenn du X s weg bist, nach Wellenstand.
- **Überzahl zum Zeitpunkt T:** Respawns, Ankünfte, bekannte und unbekannte Gegner.
- **Zeitfenster:** Welle prallt zurück in X s; Gegner tot oder back X s; Jungler auf der anderen Seite X s.
- **TP-Rechner:** Kanalzeit, Ziel (Turm, Vasall, Ward), Ankunft gegen Kampf- oder Objective-Zeit, Welle vorher
  crashen, Gegner-TP-Stand, Wert gegen „bleiben“ (Aktionswert aus `gehirn`).
- **Roam-Wert:** Kosten (Wellen) gegen Gewinn (Aktionswert, Kampf-Modell).
- **Rückwärtsplanung** eines Objectives (90/60/30 s): welche Schritte jetzt, aus den Ketten aus 031.
- Patch-Werte (TP-Abklingzeit, Spawn-Timer, Kanonenwellen) nur aus `wissen/` mit Stand.

## 2. Regeln mit Recherche (`wissen/makro/*.toml`)

Jede Entscheidung mit Grundlage **R** in Teil B braucht eine Regel:
- **Recherche im Netz:** Challenger- und Coach-Quellen, aktueller Patch soweit möglich. Pro Regel mindestens eine
  Quelle mit Datum.
- **Ward-Orte und -Zeiten** für Top, je nach Startseite des Gegner-Junglers und Minute; Kontroll-Auge; Linse.
- **Wellen:** Freeze, Aufbau, Crash, Zurückprallen.
- **TP:** Lane, Kampf, Flanke, Verteidigung, halten.
- **Objective-Aufbau;** Split und 1-3-1; globale und lange Ults (Champion-Liste aus dem Lexikon).
- **Gegen die Daten prüfen,** wo das geht (Handbuch, Modelle). Widersprechen die Daten einer Regel, gewinnen die
  Daten; der Widerspruch kommt in den Bericht.

## 3. Alle 111 Entscheidungen (`lolcoach/makro/entscheidungen/`)

Je Nummer aus Teil B (S1 … Z3):
- **Auslöser:** welche Live-Eingaben (Minimap, HUD, Live-API, Chat).
- **Rechnung:** D über `gehirn.bewerte()`, Re über die Rechner, R über `wissen/makro`.
- **Kommando-Vorlage:** „Tu X, weil Y, danach Z“. Warten ist ein Kommando. Keine internen Begriffe.
- **Test in `tests/makro/`** mit konstruierter Lage: Die Entscheidung feuert, wenn sie soll, und schweigt, wenn sie
  nicht soll.

Fehlt eine Live-Eingabe noch (Wellen aller Lanes, Trinket-Ladungen, TP-Stand), wird die Entscheidung trotzdem
gebaut und mit konstruierter Eingabe getestet. Sie bekommt die Markierung „Wahrnehmung fehlt → 033“.

**Vorrang**, wenn mehrere Entscheidungen feuern:
- Gefahr zuerst, dann die Objective-Kette, dann der Rest nach Wert.
- Festhalten in `lolcoach/makro/vorrang.py`.
- Die eine Stimme selbst baut Stufe 4 (034).

## 4. Abdeckung (`buecher/challenger/abdeckung.md`)

- 111 Zeilen mit vier Häkchen: erkannt, gerechnet, gesagt, getestet. Dazu die Spalte „Wahrnehmung fehlt“.
- **Tor 3a:** gerechnet, gesagt und getestet jeweils **111/111**.
- „Erkannt“ gilt für alle, außer den für 033 markierten.

## Ende

- **`buecher/challenger/phase3a_bericht.md`:**
  - Zeile 1: „Guthaben: 0,00 $ (Abo-Aufrufe: N)“;
  - die neuen Modellzahlen (Abschnitt 0);
  - Abdeckung, Rechner-Tests, Zahl der Quellen;
  - Widersprüche zwischen Daten und Regeln;
  - die Liste für 033 (fehlende Wahrnehmung).
- Knapp. Committen, nur eigene Dateien. Starte den Coach nicht.
