# Auftrag 005 – Kritik, Runde 1

Drei Kritiker-Agenten, ohne Code, in der Rolle „Challenger-Toplaner (Riven-Main) und Coach“. Sie bekamen die
Protokolle nach Auftrag 004 (`16e579b`), Carlos' Notizen aus 213624 und die drei Prüfungen vom 27.09. Die Urteile je
Satz liegen im Scratchpad (`k005_r1/urteile_*.jsonl`), die Zählung steht unten.

## Zählung

| Partie | min | ok | schwach | falsch | schwach je 30 min | falsch je 30 min |
|---|---|---|---|---|---|---|
| 164326 (echt) | 42,8 | 40 | 39 | 17 | 27,3 | 11,9 |
| 173159 (echt) | 38,3 | 54 | 17 | 9 | 13,3 | 7,0 |
| 144655 (echt) | 9,7 | 9 | 5 | 2 | 15,5 | 6,2 |
| 213624 (Bot, mit Fragen) | 25,1 | 42 | 38 | 16 | 45,4 | 19,1 |
| 102112 (Bot) | 30,4 | 48 | 16 | 12 | 15,8 | 11,8 |

## Klassen nach Ursache (nur „falsch“ gezählt; Beispiele mit Partie und Zeit)

| # | Klasse | falsch | Beispiele | Entscheidung |
|---|---|---|---|---|
| 1 | **Überlegenheit übersieht Ungesehene** (gefährlich) | 3 | 173159 28:52 „Nimm den Kampf: Level 17 gegen 14.“, Tod 29:03; 164326 28:58 „Rein auf Lux!“; 164326 21:01 „Baron jetzt: … drei gegen eins“ | **behoben** (`p_da_min` 0,3 → 0,1). 21:01 bleibt nach der Regel (drei gegen zwei, zwei Level + Gold), s. `005_frage.md` |
| 2 | **Wendepunkt-Kopf als falscher Grund** | 9 | 213624 14:29 „Euer Turm ist weg: Drück den inneren Top-Turm …“; 164326 22:17 „Euer Turm ist weg: Verkauf Dorans Klinge …“; 102112 27:51 „Turm ist down: Back. Danach back.“; 164326 30:48 „Drache weg: Farm Top …“ | **behoben**: Ein Verlust der anderen Seite ist eine eigene Nachricht mit Lane („Euer Bot-Turm ist weg. Drück …“). „Danach“ wiederholt nie den Plan |
| 3 | **Unmögliche Kaufzeit** | 1 (von 2) | 164326 0:19 „Caulfields Kriegshammer in 41 Sekunden kaufbar“ bei 0 Gold | **behoben**: Startgold, Kopfgeld und Platten zählen nicht als Einkommen. 8:24 („Eklipse in 63 Sekunden“) war richtig: 330 Gold fehlten, 5,2 Gold/s |
| 4 | **Rückblick gegen das Wissen des Coaches** | 3 | 173159 35:13 „Kai'Sa kam aus dem Nebel“, sie stand gerade in ihrer Basis auf; 144655 9:23 „Kha'Zix kam aus dem Nebel“, 8:33 angesagt | **behoben** (2): Wer ≤ 60 s angesagt war oder ≤ 20 s wiederbelebt ist, kam nicht aus dem Nebel. 213624 19:12 ist eine andere Vorlage, einzeln |
| 5 | **„Nein.“ auf eine Aussage** | 2 | 213624 20:00 und 21:03 „Notiert. Nein. …“ („Dann kann ich als Riven …“ ist keine Frage) | **behoben**: Die innere Frage braucht ein „?“ oder ein Fragewort vorn, nur „soll ich“ darf mitten im Satz stehen |
| 6 | **Geratener Objective-Grund, widerspricht der Ansage** | 4 | 213624 10:54 „Drache lohnt gerade nicht: zu weit oder zu wenige …“, 6 s später „Drache bestreiten, fünf gegen zwei“; 11:38; 12:56 „Keins von beiden … Jetzt: Drache mit Malzahar“ | **behoben**: Die Antwort nennt, was der Kern weiß (Weg, wer von euch dort ist), und der gehaltene Plan zählt als Option |
| 7 | **Warten am Inhibitor-Turm nach dem Tod** | 3 | 144655 1:59 „… bleib am Inhibitor-Turm: Gangplank war zuletzt oben.“; 173159 23:11; 164326 12:59 | **nicht gebaut**: Das ist der Sicherheits-Rückfall G2 (`wohin_p_tod_max`). Lockern hieße eine Schranke lockern → `005_frage.md` |
| 8 | **Top-Welle statt Team bei Ältestem oder Belagerung** | 3 | 173159 28:22 „Dann Top-Welle.“, Ältester in 18 s; 36:50 „Zwei eurer Türme weg: Dann Top-Welle.“; 37:06 | **nicht gebaut**: VERTEIDIGEN gilt nach Buch 5, 7 nur in der Nähe. Eine Rückkehr zur Basis wäre eine neue Regel → `005_frage.md` |
| 9 | **Back ohne Ereignis kippt den Plan** | 4 | 164326 39:49 „Back jetzt: 1500 Gold im Beutel.“ 34 s nach „Baron bestreiten“; 213624 23:35; 102112 24:44 | **nicht gebaut**: Die Ursachen sind verschieden (ein Objective-Plan fällt weg, das Kaufziel ist erreicht, ein Kampf endet). Es gibt keinen gemeinsamen Fix, Runde 2 zählt nach |
| 10 | **Turmziel springt im Late-Game** | 3 | 164326 35:00 → 35:15 (Mid-Inhibitor → innerer Bot-Turm); 41:49; 42:09 | **nicht gebaut**: Das sind überlegene Turmziele mit ähnlichem EV, die Hysterese (150 GE) hält sie nicht. Runde 2 zählt nach |
| 11 | *Kritiker irrt:* „Level 20 gibt es nicht“ | 4 | 102112 34:42, 36:01, 36:51, 38:24 | Die Top-Quest hebt das Level-Cap auf 20 (messungen, Auftrag 002, S4) |
| 12 | *Kritiker irrt:* „Caulfields gegen seinen Build“ | 4 | 164326 10:50, 18:22, 20:49, 22:17 | Caulfields ist Bauteil von Axiombogen, Eklipse und Hydra (ddragon 16.19). Die Goldangaben rechnen mit vorhandenen Bauteilen |
| – | Einzelfälle (je 1) | 11 | 213624 17:11 „Back jetzt“ in der Basis; 5:05 Spielplan-Frage; 9:49/9:57 (Frage im Takt des Turmfalls, s. 004) | unter der Schwelle |

**„Schwach“ (115)** verteilt sich auf Floskel (24, meist „Dann Top.“ / „Dann Top-Welle.“), Grund passt nicht (18),
Wiederholung (14), Ziel fehlt (10) und Zahl ohne Nutzen (7). Nach dem Auftrag wird schwach nur gezählt, nicht gebaut.

## Szenarien (alle zuerst rot auf `16e579b`)

- 173159: `2852-ungesehene-zaehlen`, `3513-respawn-nicht-nebel`
- 164326: `2858-rein-mit-ungesehenen`, `0019-kaufbar-unmoeglich`, `2217-euer-turm-kein-grund`
- 144655: `0923-gewarnt-nicht-nebel`
- 213624: `1429-euer-turm-kein-grund`
- 102112: `2751-back-danach-back`
- 213624, Fragen: `2000-notiz-kein-nein`, `2103-notiz-kein-nein`, `1054-drache-nicht-geraten`, `1138-drache-nicht-geraten`
- Verworfen: `0824-kaufbar-unmoeglich`. Er war rot, aber der Kritiker irrte (s. Klasse 3).
