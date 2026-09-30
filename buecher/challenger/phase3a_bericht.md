Guthaben: 0,00 $ (Abo-Aufrufe: 0)

# Challenger-Gehirn, Stufe 3a – Makro-Rechner und Regeln für alle 111 Entscheidungen (Auftrag 032, 30.09.2026)

**Neu:**
- `lolcoach/makro/` als neues Paket: Lage, Kommando, Wahrnehmung, Rechner, Regeln, 111 Entscheidungen, Vorrang;
- `tests/makro/`;
- `wissen/makro/`: Quellen, Patchwerte, Regeln, Ults;
- `werkzeuge/challenger/abdeckung.py` und `ults_aus_lexikon.py`.

**Geändert (eigene Dateien aus 031):** `werkzeuge/challenger/modelle.py` und `gehirn.py`, für Abschnitt 0.

An bestehenden Dateien in `lolcoach/` ist nichts geändert, dort wird nur importiert (`bewertung`, `kern.uhren`,
`wissen`).

**Tests:**

| Lauf | Ergebnis |
|---|---|
| `tests/makro/alle.py` | 4/4 grün: Rechner 11/11, Register 5/5, Entscheidungen 111/111, Gehirn-Korrektur 4/4 |
| `tests/alle.py` des Coaches | 11/11 grün |

## 0. Entscheidungen zu Stufe 2, umgesetzt

**1. Modelle ohne Gegner-Items und -Level**, neu trainiert. Heraus ist das ganze Gegner-Scoreboard aus Items, Level
und CS, also genau die Menge, die in 031 gemessen wurde. Alle Modelle schlagen ihren Vergleich weiter.

| Modell (Prüfung) | 031 (mit) | **032 (ohne)** | Vergleich |
|---|---:|---:|---:|
| Siegchance V, Brier / Log-Loss | 0,159 / 0,477 | **0,163 / 0,488** | Gold-Abstand (im Spiel unsichtbar) 0,170 / 0,508 |
| ↳ Brier 0–10 / 10–20 / 20–30 / 30+ min | 0,208 / 0,149 / 0,115 / 0,133 | **0,210 / 0,152 / 0,122 / 0,141** | 0,213 / 0,159 / 0,133 / 0,180 |
| Policy π, Top-1 / Top-3 | 48,0 / 78,4 % | **48,0 / 78,4 %** | 32,9 / 64,5 % |
| Aktionswert Q, R² (ohne Aktion: Q0) | 0,078 (0,075) | **0,086 (0,076)** | „jede Aktion gleich“ = Q0 |
| Gefahr 60 s, Log-Loss | 0,366 | **0,366** | Minute + Ort 0,498 |
| Jungler-Karte, Log-Loss / Top-3 | 1,333 / 78 % | **1,343 / 78 %** | 2,247 |

- **Klarheit**, neu geeicht: δ = 0,47 Punkte; klar 22,3 %, geteilt 25,3 %, unklar 52,4 %.
- **Gegenprobe „klar“:** Die empfohlene Aktion bringt +1,9 ± 0,26 Punkte Siegchance, doppelt robust auf der Prüfung.
- **Plausibilität:** 14 von 15. Durchgefallen ist wie in 031 „Ace: Baron schlägt Farmen“, weil nach einem Ace
  niemand farmt (Abschnitt 0.3).

**2. Back nur mit Grund** (`gehirn.back_gruende`, Regel `wissen/makro/regeln.toml [back_gruende]`):
- **Gründe:** Welle gecrasht, Leben unter 35 %, Gold für ein Bauteil (Kaufplan oder Median-Back-Gold der Rolle aus
  dem Handbuch), Objective in 60–120 s, Lane-Gegner backt.
- **Ohne Grund** rutscht Back hinter die nächste Aktion.
- **Wirkung an 2000 Prüf-Lagen:** Back vorn nur noch in 27 % (vorher 77 % der klaren Empfehlungen), jedes Mal mit
  Grund.

**3. Nach einem Ace:**
- Das Modell rankt nach einem Ace „in die gegnerische Basis“ vorn.
- Die Entscheidung M8 prüft mit `rechner.schluss_moeglich` den Weg gegen den ersten Respawn.
- Reicht die Zeit bis zum Inhibitor oder Nexus, heißt es **Schluss**, sonst **Baron**.

**4. „Unklar“ heißt nie Schweigen:** `bewerte()` stellt dann an die erste Stelle, was High-Elo-Spieler hier am
häufigsten tun, mit Ziel. Z3 macht daraus das Kommando.

**Laufzeit:** `bewerte()` braucht 4,7 ms (Median).

## 1. Rechner (`lolcoach/makro/rechner.py`, 11 Tests)

| Rechner | Grundlage |
|---|---|
| Ankunft (auch ab Brunnen und Brunnen → Lane) | `bewertung.abstand`/`WEGFAKTOR`, `kern.uhren.brunnen_lane`, Tempo 365 aus `wissen/wege.toml` |
| Wellenwert, Wellenkosten nach Stand, Rückprall-Fenster, Crash-Dauer | `wissen/mechanik.toml`, `wissen/wellen.toml`, `wissen/makro/patchwerte.toml` |
| Überzahl zum Zeitpunkt T (Respawns, Ankünfte, unbekannte Gegner als „möglich“) | Rechnung |
| Zeitfenster: Lane-Gegner tot/back, Jungler-Untergrenze aus der letzten Sichtung | Rechnung |
| TP: Abklingzeit, Ankunft (Kanal 3 s + Anflug), Urteil (zu spät, erst crashen, Gegner-TP, Wert gegen Bleiben) | Wiki Teleport, Patch 26.19 |
| Roam-Wert (Gewinn minus Wellen in Siegchance-Punkten) | eigene Messung: 8,7 Punkte je 1000 Gold bei 10:00, 4,9 bei 25:00 |
| Rückwärtsplanung 90/60/30 s | Regel O7 |
| Schluss nach dem Ace (Weg + Zerstören gegen den ersten Respawn) | Regel `baron_nach_ace` |
| Todeskosten | `bewertung.todeszeit` |

Patch-Werte liegen nur in `wissen/`, mit Stand.

## 2. Regeln mit Recherche (`wissen/makro/`)

- **32 Regeln** (`sicht.toml`, `regeln.toml`), jede mit Quelle und Datum.
- **30 Quellen** (`quellen.toml`):
  - 26 aus dem Netz: Wiki, riftpatchnotes, nerfplz (Aug. 2026), dodge.gg (2026), mobatrainer (Patch 26.13),
    Mobalytics, LoL Theory, WeCoach, metabot, esports.net; alle abgerufen am 30.09.2026;
  - dazu das Lexikon und 3 eigene Messungen.
- **Ults** (`ults.toml`): 33 Champions mit globaler oder langer Ult, aus dem Lexikon erzeugt (`ults_aus_lexikon.py`).
- Alle Entscheidungen mit Grundlage R haben eine Regel (Test `test_r_hat_regel`).

## 3./4. Alle 111 Entscheidungen und die Abdeckung

Die Tabelle aller 111 steht in [abdeckung.md](abdeckung.md). Sie ist aus dem Register und den Tests erzeugt, nicht von
Hand.

| erkannt | gerechnet | gesagt | getestet |
|---:|---:|---:|---:|
| 97/111 (+14 für 033) | **111/111** | **111/111** | **111/111** |

**Tor 3a: ERREICHT.**

**So ist jede Entscheidung gebaut:**
- eine reine Funktion `MakroLage → Kommando | None` mit Auslöser (Live-Eingaben), Rechnung (D/Re/R, geprüft) und
  Kommando „Tu X: weil Y. Danach Z.“;
- dazu je eine konstruierte Lage, in der sie feuern muss, und eine, in der sie schweigen muss.

**Sprachtest:**
- Kein Kommando enthält interne Begriffe wie Gehirn, Policy, Aktionswert, Lage oder Klarheit.
- Beim Durchlesen aller 111 Sätze habe ich Doppelungen („Danach danach“), falsche Fälle („am Drache“) und „jetzt
  Lane“ gefunden und behoben.
- Zwei Logikfehler waren dabei:
  - K2 sagte „Warte“, obwohl es danach immer noch Unterzahl war.
  - O1 sagte bei 4 gegen 5 „bestreiten“.

**Vorrang** (`vorrang.py`): Gefahr, dann Objective-Kette, dann der Rest nach Wert.

## Widersprüche zwischen Daten und Regeln (die Daten gewinnen)

1. **Trinket halten bis 2:50** (Beispiel in Buch 17): 8 % der ersten Top-Ganks fallen vor 2:50, 5 % vor 2:17
   (n = 2467). Die Regel S2 hält nur bis 2:15.
2. **Herold „wertvoll“** laut Quellen: Das Siegchance-Modell misst −0,7 Punkte (031) bzw. −1,1 Punkte (032, ohne Gegnerwerte), n = 3876. Die Regel O3 sagt,
   dass der Turm danach zählt, nicht der Herold.
3. **Baron nach einem Ace** laut Quellen: Die Daten sagen „in die Basis“ ist +6,7 ± 1,9 Punkte besser als Baron.
   Umgesetzt als Rechner-Prüfung Schluss gegen Baron.
4. **Split** laut Quellen „Druck, wenn stark im 1v1“: Die Daten zeigen 73 % Tod in 60 s, wenn allein weitergesplittet
   wird, während drei Gegner unbekannt sind. Die Regeln S10, M2 und K7 verlangen deshalb Sicht und bekannte Gegner.
   Das ist eine Einschränkung, kein Gegensatz.
5. **Intern, nicht Daten gegen Regel:** `wissen/uhren.toml` rechnet mit `tp_s = 6` (4 s Kanal). Seit 25.S1.1 ist der
   Kanal 3 s lang. Die Datei ist bestehend und von mir nicht geändert; der Makro-Rechner nutzt die 3 s aus
   `wissen/makro/patchwerte.toml`.

## Die Liste für 033 (Wahrnehmung fehlt)

| Wahrnehmung | Entscheidungen |
|---|---|
| **Eigene Wards** (Minimap: Ort, Ablauf, zerstört) | S10, S12, S14, T4, M5 |
| **Wellen der anderen Lanes** (Minimap) | W11, W14, M6 |
| **Busch ohne Sicht vor dir** (Spielbild) | S11 |
| **Trinket-Ladungen** (HUD) | S13 |
| **Recall des Lane-Gegners** (Spielbild/Minimap) | B5; dazu der Back-Grund „Lane-Gegner backt“ |
| **TP-Stand der Gegner** (heute nur nach gesehenem Sprung) | T9 |
| **Objective-Kopfgeld** (Minimap-Markierung) | O12 |
| **Beschwörerzauber der Mitspieler** (HUD) | P2, Teil Flash; Leben ist live |

Alle 14 sind gebaut und mit konstruierter Eingabe getestet. Sie feuern, sobald 033 die Eingabe liefert.

**Für Stufe 4 offen:**
- `MakroLage` aus den Live-Quellen füllen, einmal je Takt;
- das Gehirn mit Kontext aufrufen (Welle, Kaufplan, Recall);
- `vorrang.ordnen` an die eine Stimme übergeben.
