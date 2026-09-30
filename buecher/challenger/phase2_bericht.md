Guthaben: 0,00 $ (Abo-Aufrufe: 0)

# Challenger-Gehirn, Stufe 2 – Modelle und Handbuch (Auftrag 031, 30.09.2026)

**Neue Werkzeuge** in `werkzeuge/challenger/`:
- `modelle.py`: Training;
- `analyse.py`: Plausibilität, Klarheit, Ketten;
- `handbuch.py`: das Handbuch aus den Daten;
- `gehirn.py`: die Schnittstelle für Stufe 4.

**Ergebnisse:**
- `daten/challenger/modelle/`: Modelle, `messung.json`, `analyse.json`, `klarheit.json`;
- [handbuch.md](handbuch.md): das Handbuch;
- [live_merkmale.md](live_merkmale.md): welche Merkmale live verfügbar sind.

Gerechnet wurde mit LightGBM auf der CPU (niedrige Priorität). Ein Durchlauf trainiert alle Modelle in etwa 14 min.
Die GPU war nicht nötig.

## 0. Die zwei Entscheidungen aus 030 und zwei Fehler, die die Prüfungen fanden

**Umgesetzt**, dann die Momente neu gebaut:
- **„Unterwegs“ hat ein Ziel:** der Ort am Ende des 60-s-Fensters bzw. des ersten eigenen Ereignisses darin, als
  Zone, Grube oder gegnerische Basis. Dazu der Mitspieler dort. Das gilt als `wohin`/`wohin_mit` für jede Aktion.
- **„Nahe sichtbar“:** in der Lane-Phase 1800, sonst 1200. Die Trefferquote in der eigenen Lane vor 14:00 steigt von
  **31 % auf 44 %**. Der Maphack-Test ist angepasst und grün, die Sabotage-Gegenprobe fällt wie verlangt durch.

**Zwei Fehler in den Aktions-Labels.** Die Prüfungen fanden sie, danach wurden die Momente neu gebaut und alle
Modelle neu trainiert:
1. **Objective war über den Erfolg definiert** („Monster fällt, du bist dabei“). Der Aktionswert maß dann
   „Baron bekommen“, nicht „zum Baron gehen“: In zehn von zehn Datengruppen gewann Baron.
   - **Neu:** Du stehst an der Grube, solange das Monster offen ist oder in dem Moment, in dem es fällt, egal welches
     Team es nimmt.
2. **Split, Lane, Gruppe, Rotation und Jungle verlangten, dass du am Fensterende noch lebst.** Wer beim Splitten
   starb, hieß „Unterwegs“, und Q fand „Split schlägt Back“ (Survivor-Bias).
   - **Neu:** Das Fenster endet beim Tod, es zählt der letzte Ort davor. „Tot“ heißt nur noch: jetzt schon tot.

Alle Zahlen unten sind nach diesen Korrekturen gemessen.

**Datenbasis:** 3.494.522 Momente aus 4761 Partien. Training 2,37 Mio., Prüfung 1,12 Mio. (Prüfspieler und
Prüfzeit, fest seit 030). 28 Aktionen mit Ziel, zum Beispiel `Objective:Drache`, `Rotation:oben`,
`Unterwegs:gegn. Basis`.

## 1. Die Modelle, gemessen auf der Prüfung

| Modell | Messung | Modell | Vergleich (muss schlagen) | |
|---|---|---:|---:|---|
| **Siegchance V** | Brier / Log-Loss / Kalibrierfehler | **0,159** / 0,477 / 0,013 | Gold-Abstand allein: 0,170 / 0,508 / 0,022 | ✔ |
| ↳ je Minute | Brier 0–10 / 10–20 / 20–30 / 30+ | 0,208 / 0,149 / 0,115 / 0,133 | 0,213 / 0,159 / 0,133 / 0,180 | ✔ in allen vier |
| **Policy π** (28 Aktionen, Gewicht C3/GM2/M1) | Top-1 / Top-3 | **48,0 %** / 78,4 % | häufigste je Rolle+Minute: 32,9 % / 64,5 % | ✔ |
| ↳ je Rolle (Top-1) | Top/Jgl/Mid/ADC/Sup | 47 / 52 / 49 / 46 / 45 % | 34 / 33 / 35 / 31 / 32 % | ✔ |
| **Aktionswert Q** (Siegchance-Änderung 120 s) | MSE | 0,01868 | „jede Aktion gleich“ (Q0): 0,01873 | ✔ knapp (z = 3,3), s. u. |
| **Gefahr** Tod in 30 s | Log-Loss / Brier / Kal. | **0,189** / 0,057 / 0,004 | Minute + Ort: 0,313 / 0,087 / 0,002 | ✔ |
| **Gefahr** Tod in 60 s | Log-Loss / Brier / Kal. | **0,366** / 0,115 / 0,006 | Minute + Ort: 0,498 / 0,160 / 0,003 | ✔ |
| **Jungler-Karte** (11 Bereiche + tot) | Log-Loss | **1,33** (lebend 1,58) | Verteilung je Minute: 2,25 (2,34) | ✔ |
| ↳ lebender Jungler | Top-1 / Top-3 | 42 % / 78 % | 14 % Top-1 | ✔ |

**Zum Vergleich für V:** Der echte Gold-Abstand ist im Spiel **nicht** sichtbar. V schlägt ihn nur mit Wissbarem.

**Ehrlich zu Q:**
- Die Aktion erklärt nur einen kleinen Teil der Siegchance-Änderung in 120 s (R² 0,078 gegen 0,075 ohne Aktion). Das
  meiste steckt in der Lage.
- Der Gewinn ist klein, aber nicht Zufall: z = 3,3 über 4341 Partien.
- Der Nutzen zeigt sich beim Vergleich zweier Aktionen in derselben Lage. Nach Klarheit (Abschnitt 2) bestätigt die
  doppelt robuste Schätzung auf der Prüfung: Wo Q „klar“ sagt, bringt die empfohlene Aktion **+2,0 Punkte**
  Siegchance gegenüber der zweitbesten (± 0,28).

**Methode für „ähnliche Lagen“:** Q ist ein Outcome-Modell mit der ganzen Lage (105 Merkmale). Aktionseffekte in
Lage-Gruppen werden doppelt robust (AIPW) geschätzt, mit π als Neigung (auf 0,02 geklemmt) und Unsicherheit über
Partien.
- **Unsicher**, wo High-Elo-Spieler eine Aktion praktisch nie wählen: Q extrapoliert dann (s. Prüfung 3).
- **Schutz im Gehirn:** Empfohlen wird nur, was π mit mindestens 2 % sieht.

## Plausibilitätsprüfungen (Prüfung, fließen nicht ins Training)

| # | Prüfung | n | Modell | doppelt robust | |
|---|---|---:|---|---|---|
| 1 | Wenig Leben (< 30 %), Gegner nah, in der Lane: Back schlägt Bleiben | 4157 | +1,5 Punkte, 99 % der Lagen | +0,3 ± 0,9 (nicht signifikant) | ✔ |
| 1b | … Bleiben ist gefährlicher (Tod in 60 s) | 4157 | 17,1 % gegen 1,2 % | – | ✔ |
| 2 | Ace, Baron steht: Baron schlägt Farmen | 577 | −1,2 Punkte, 27 % | – | ✘ **durchgefallen** |
| 3 | Split allein ab 25:00, ≥ 3 Gegner unbekannt: hohes Todesrisiko | 1253 | 65 % Tod in 60 s (Gruppe: 18 %; Grundrate 24 %; tatsächlich beim Split: 68 %) | – | ✔ |
| 4 | Drache in ≤ 60 s, ≥ 2 Mitspieler dort: Drache schlägt Seitenwelle | 12.326 | +0,9 Punkte, 84 % | – | ✔ (vor der Korrektur ✘) |
| 5–14 | aus den Daten gefunden (je Lage-Gruppe der stärkste doppelt robuste Effekt, \|z\| ≥ 3) | 11 k–94 k | 10 von 10 bestanden | +1,5 bis +3,6 Punkte | ✔ |

**Prüfung 2, untersucht (die Prüfung ist nicht geändert):**
- Nach einem Ace mit stehendem Baron farmen High-Elo-Spieler praktisch nie: Lane 1, Jungle 8 von 577 Fällen.
- Sie backen (232), laufen in die gegnerische Basis (145) oder zum Baron (53).
- Q(Farmen) ist dort also geraten, eine Extrapolation ohne Daten.
- Doppelt robust schlägt „in die gegnerische Basis“ den Baron um 6,7 Punkte (± 1,9).
- Das Gehirn empfiehlt in diesen Lagen „gegn. Basis“ (205), Back (166), Mid (104) und Baron nur 12-mal. Nie
  empfiehlt es Farmen, denn π < 2 % schließt es aus.
- **Das Modell sagt also nicht „farmen“, sondern „Schluss spielen statt Baron“.** Ob das ein Challenger-Coach auch so
  sagen würde, ist eine Frage für das Pflichtenheft.

**Prüfung 3:** Sie fiel zuerst durch einen Fehler in **meinem Prüfcode** (Mittelwert über NaN). Der Fehler ist
behoben, das Kriterium ist gleich geblieben.

**Die zehn Datenfunde sind einseitig:** Sieben davon sind „Back schlägt Warten“ (+2,3 bis +3,6 Punkte). Die übrigen
drei:
- „Team 3000 vorn: Gruppe schlägt Lane“ (+1,5);
- „Herold steht: Drache schlägt Lane“ (+1,9);
- „Leben < 35 %: Baron schlägt Lane“ (+2,1; auffällig, s. Probleme).

## 2. Klarheit

- **Schwelle δ:** Sie ist auf der Prüfung festgelegt als kleinster Wert-Abstand zwischen bester und zweitbester
  Aktion, ab dem die doppelt robuste Schätzung den Vorsprung für diesen und alle größeren Abstände bestätigt
  (95 %-Grenze > 0). Das ergibt **δ = 0,74 Punkte**.
- **π-Schwellen:** klar ab π ≥ 15 %, geteilt ab 8 % für beide.

| | klar | geteilt | unklar |
|---|---:|---:|---:|
| alle | **18,5 %** | 28,6 % | 52,8 % |
| Top / Jungle / Mid / ADC / Support | 27 / 19 / 15 / 17 / 15 % | 22 / 39 / 22 / 27 / 35 % | 51 / 43 / 63 / 56 / 50 % |

**Gegenprobe „klar“:**
- Die empfohlene Aktion bringt +2,0 ± 0,3 Punkte gegenüber der zweiten (doppelt robust).
- High-Elo-Spieler taten sie in 47 %.

**Häufigste Empfehlungen:**
- **klar:** Back 77 %, Gruppe 11 %, gegn. Basis 6 %.
- **geteilt:** Back/Gruppe, Back/Drache, Back/Lane.
- **Unklar**, weil die Info fehlt, meldet `lage_info()`: Ort des Gegner-Junglers unsicher (Entropie der Jungler-Karte
  > 0,7), TP-Abklingzeit.

## 3. Ketten und Umwandlung (`analyse.json` → `ketten`)

**120 s vor dem Objective**, Team, das es nimmt, gegen Team, das es verliert:

| | an der Grube | tot | Back |
|---|---|---|---|
| Drache, Top | 12 % / 7 % | 13 % / 18 % | 25 % / 22 % |
| Drache, Jungler | **51 % / 14 %** | 9 % / 19 % | – |
| Baron, Top | **31 % / 13 %** | 14 % / 27 % | 30 % / 17 % |

**Nach einem gewonnenen Kampf** (Kill, ≥ 2 Gegner mehr tot; n = 18.837):
- **Getan:** Back 44 %, Gruppe 8 %, Drache 6 %.
- **Folge in 60 s:** 0,60 Gebäude, 2,56 Platten, 0,32 Monster.
- Die doppelt robusten Werte je Aktion liegen alle bei −0,3 bis −1,2 Punkten und unterscheiden sich kaum.
- Nach dem Kampf fällt die Siegchance im Mittel leicht zurück, weil der Kampf-Vorteil schon im Wert steckt. Eine
  klare beste Umwandlung zeigen die Daten nicht.

**Häufigste Ketten** (a0 > a1 > a2, Siegchance-Änderung 180 s, Siegquote):

| Rolle | Ketten |
|---|---|
| Top | `Lane > Back > Lane` (17 k, +2,3, 52 %); `Back > Unterwegs > Back` (+3,3, 59 %) |
| Jungler | `Objective > Objective > Back` (12 k, +6,1, 64 %); `Objective > Back > Jungle` (+4,3, 61 %) |
| Support | `Back > Objective > Back` (14 k, +5,4, 63 %) |

Das ist Stoff für die Rückwärtsplanung in Stufe 3.

## 4. Die zehn stärksten Handbuch-Aussagen

Aus [handbuch.md](handbuch.md): 77 Aussagen, 26 verworfen, weil n < 200 oder kein klares Signal.

1. Ab 25:00 allein in der Seitenlane, ≥ 3 Gegner unbekannt: Wer 60 s weitersplittet, stirbt in **73 %**, wer die
   Seite verlässt, in 23 % (n = 575, |z| 24). *„Drei fehlen – raus aus der Seitenlane.“*
2. Lane-Phase unter 30 % Leben: In der Lane bleiben heißt **11 %** Tod in 60 s, Back 2 % (n = 19.605, |z| 35).
   *„30 % Leben – Welle unter den Turm, dann Back.“*
3. Baron: In den 120 s davor steht das nehmende Team 31–45 % der Momente an der Grube, das verlierende 11–15 %; tot
   ist es 10–14 % gegen 25–30 % (|z| 38–87). *„Baron in einer Minute – jetzt hin.“*
4. Drache, Jungler: 51 % gegen 14 % an der Grube in den 120 s davor (|z| 186).
5. Bei 20:00 3000+ Item-Gold vorn: Siegquote **79 %**, hinten 21 % (n ≈ 8 k).
6. Bei 10:00 20+ CS vorn: Siegquote 61 %, hinten 39 % (n ≈ 3,5 k).
7. Gegner nimmt einen Drachen frei: Mit Turm oder zwei Platten als Tausch ändert sich der Gold-Abstand um −25, ohne
   Tausch um −439 (n = 2322, |z| 20). *„Drache ist weg – dafür jetzt Turm oben.“*
8. Info zum Jungler ist nach 45 s alt: Er ist noch auf derselben Kartenseite in 71 % (< 15 s), 31 % (45–60 s) und
   33 % (90–120 s).
9. Wert in Siegchance (Modell V): Drache vor 20:00 **+4,3**, Baron 20–30 min **+4,1**, Drache 20–30 min +2,2, Herold
   −0,7 Punkte.
10. Beim Back (5:00–20:00, Gold beim Betreten des Ladens): Top/Mid etwa 870, ADC 1015, Jungler 1100, Support 600.

## 5. Schnittstelle für Stufe 4

`gehirn.Gehirn().bewerte(lage)` liefert eine Liste von
`(Aktion, Ziel, Wert in Punkten, p_highelo, Gefahr 60 s, Klarheit, Grund-Stichworte)`. Dazu gibt `lage_info()`
Siegchance, Jungler-Karte und fehlende Info zurück.

**Laufzeit** (CPU, ein Faden): Median **4,2 ms**, p95 6,7 ms, max 8,8 ms (Ziel < 20 ms).
- Die exakten LightGBM-Beiträge für die Gründe kosteten 40 ms und flogen raus.
- **Ersatz:** 16 lesbare Kernmerkmale, jedes einzeln auf den Median gesetzt. Grund ist, was den Vorsprung am meisten
  trägt.

**Live-Verfügbarkeit** jedes Merkmals mit Ersatz: [live_merkmale.md](live_merkmale.md).

## Probleme

1. **Gegner-Items und -Level sind live nur „wie zuletzt gesehen“.** Belegt in `lolcoach/lage.py`. Im Training stehen
   die echten Werte.
   - **Gemessen:** V ohne diese Merkmale hat Brier 0,1627 statt 0,1590. Es schlägt den Gold-Abstand (0,170) weiter.
   - **Vorschlag für Stufe 3/4:** entweder V, Q und Gefahr ohne sie, oder im Training auf „Stand beim letzten Sehen“.
     `V_ohne_gegnerwerte.txt` liegt bereit.
2. **„Zuletzt gesehen“ ist live reicher als im Training.** Live kommt jede Minimap-Sichtung, im Training nur Ereignisse
   mit Ort. Das Alter ist live kleiner. Das muss in Stufe 3 geprüft werden.
3. **Back ist vermutlich überbewertet** (77 % der klaren Empfehlungen). Back wird über den Kauf erkannt; wer beim
   Recall stirbt, zählt nicht als Back. Diesen Rest-Survivor-Bias kann ich aus Minuten-Daten nicht entfernen.
   - **Nicht die Ursache:** Der V-Sprung beim Kauf selbst ist klein (+0,4 Punkte).
   - **Live erkennbar:** Recall-Versuche (8 s stehen, HUD). Bis dahin sollte Stufe 4 Back nur mit Grund (Gold,
     Leben, Timer) sagen.
4. **Q trennt Aktionen nur schwach** (R²-Gewinn 0,3 Punkte). Der Wert der Empfehlung ist in „klar“-Lagen belegt
   (+2,0 Punkte), in „geteilt“ und „unklar“ nicht. Deshalb ist „unklar“ mit 53 % ehrlich hoch.
5. **Seltsame Datenfunde:**
   - „Leben < 35 %: Baron schlägt Lane“ ist wahrscheinlich eine Verwechslung der Lage (wer tief im Spiel mit wenig
     Leben am Baron steht, ist oft beim eigenen Baron).
   - „Herold senkt die Siegchance um 0,7“ ist ebenfalls auffällig.
   - Beide sind markiert, keiner ist ins Handbuch als Kommando übernommen, außer als Q-Fund mit Kennzeichnung.
6. **Wo die Daten fehlen:** TP (6.946 sichere Momente) und Split spät außer bei Top. Dort gibt es keine eigenen
   Aussagen.
7. **Veraltete Datei:** `phase1_pruefung.md` aus 030 beschreibt den alten Stand der Labels und ist nicht neu erzeugt.
   Der Maphack-Test läuft auf dem neuen Stand (grün).
