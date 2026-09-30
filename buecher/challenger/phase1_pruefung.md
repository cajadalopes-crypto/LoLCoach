# Pruefung der Entscheidungsmomente (Auftrag 030, Schritt 3)

## 1. Zahlen

Momente gesamt: **2.565.410** aus 3504 Partien

Aufteilung: Training 1.676.187, Pruefung Spieler 421.006, Pruefung Zeit 376.923, Pruefung beides 91.294
Liga: Challenger 895.605, Grandmaster 960.293, Master 692.205, unter Master 17.307
Anlass: Minute 444.509, Kill 866.318, eigener Tod 193.758, Respawn 170.607, Back 234.441, Gebaeude 281.511, Monster 231.581, Monster-Spawn 142.685

**Primaer-Aktion (a0) je Rolle und Phase, nur Training.** Fett = unter 200 Faelle.

| Rolle | Phase | Tot | Back | Objective | TP | Rotation | Split | Gruppe | Jungle | Lane | Warten | Unterwegs |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Top | frueh | 16.553 | 35.267 | 5.742 | 378 | 1.200 | · | 1.732 | 393 | 53.878 | 3.055 | 33.924 |
| Top | mitte | 36.816 | 31.447 | 10.447 | **112** | 6.595 | 2.746 | 8.981 | 1.730 | 3.766 | 1.819 | 32.082 |
| Top | spaet | 15.318 | 8.151 | 3.068 | **77** | 2.287 | **129** | 4.417 | 781 | 280 | 906 | 11.799 |
| Jungle | frueh | 11.978 | 33.771 | 21.006 | **26** | · | · | 13.194 | 65.043 | · | **73** | 9.383 |
| Jungle | mitte | 35.997 | 27.523 | 21.272 | **19** | · | **40** | 18.914 | 20.949 | · | 509 | 13.248 |
| Jungle | spaet | 15.685 | 7.297 | 4.907 | **20** | · | **6** | 6.606 | 4.509 | · | 665 | 7.934 |
| Mid | frueh | 13.951 | 38.890 | 5.552 | **119** | 7.092 | · | 6.913 | **173** | 51.930 | 911 | 21.317 |
| Mid | mitte | 34.668 | 32.060 | 10.294 | **74** | 7.135 | 1.288 | 10.564 | 1.141 | 2.220 | 1.910 | 29.680 |
| Mid | spaet | 15.112 | 7.721 | 3.003 | **55** | 2.054 | **39** | 4.671 | 585 | 495 | 774 | 10.217 |
| ADC | frueh | 14.978 | 35.483 | 6.643 | **158** | 2.132 | · | 7.774 | **161** | 47.814 | 3.233 | 34.588 |
| ADC | mitte | 33.333 | 31.678 | 11.369 | **27** | 8.091 | 339 | 16.852 | 2.267 | 1.041 | 3.894 | 28.312 |
| ADC | spaet | 13.236 | 8.641 | 3.704 | **17** | 2.207 | **7** | 6.020 | 1.203 | **103** | 916 | 10.161 |
| Support | frueh | 13.626 | 41.043 | 12.416 | **77** | 5.279 | · | 12.501 | **44** | 22.048 | 3.817 | 44.147 |
| Support | mitte | 28.369 | 36.451 | 13.616 | **47** | 7.903 | **6** | 19.176 | **42** | 424 | 2.154 | 30.129 |
| Support | spaet | 15.109 | 9.158 | 3.401 | **11** | 2.177 | **1** | 6.072 | **26** | **80** | 852 | 10.545 |

· = per Definition 0 (Split erst ab 14:00; Jungler haben keine Lane und rotieren per Definition nicht).
Duenne Zellen (< 200): 29: Top/mitte/TP (112); Top/spaet/TP (77); Top/spaet/Split (129); Jungle/frueh/TP (26); Jungle/frueh/Warten (73); Jungle/mitte/TP (19); Jungle/mitte/Split (40); Jungle/spaet/TP (20); Jungle/spaet/Split (6); Mid/frueh/TP (119); Mid/frueh/Jungle (173); Mid/mitte/TP (74); Mid/spaet/TP (55); Mid/spaet/Split (39); ADC/frueh/TP (158); ADC/frueh/Jungle (161); ADC/mitte/TP (27); ADC/spaet/TP (17); ADC/spaet/Split (7); ADC/spaet/Lane (103); Support/frueh/TP (77); Support/frueh/Jungle (44); Support/mitte/TP (47); Support/mitte/Split (6); Support/mitte/Jungle (42); Support/spaet/TP (11); Support/spaet/Split (1); Support/spaet/Jungle (26); Support/spaet/Lane (80)

Aktion trifft zu (alle Flags, nicht nur a0), Anteil aller Momente: Tot 18.8%, Back 23.1%, Objective 12.5%, TP 0.2%, Rotation 6.9%, Split 0.4%, Gruppe 18.7%, Jungle 15.3%, Lane 16.8%, Warten 1.5%, Unterwegs 19.6%
TP-Feld: sicher 4.985. unbekannt 519.381. kein TP-Zauber 2.041.044
Objective-Ziele: Drache 177.919, Baron 61.780, Herold 38.356, Larven 40.582, Elder 2.173

**Momente je Rolle und Bereich** (wo steht der Spieler im Moment):

| Rolle | basis_blau | basis_rot | top | mid | bot | fluss_oben | fluss_unten | jungle_blau_oben | jungle_blau_unten | jungle_rot_oben | jungle_rot_unten |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Top | 16.845 | 17.232 | 224.426 | 52.411 | 36.731 | 62.062 | 26.627 | 21.651 | 16.090 | 21.007 | 16.457 |
| Jungle | 15.037 | 14.919 | 17.528 | 113.402 | 19.321 | 59.082 | 68.744 | 51.230 | 49.126 | 48.329 | 52.604 |
| Mid | 17.593 | 17.716 | 28.629 | 247.747 | 42.673 | 34.377 | 46.538 | 18.261 | 21.012 | 17.337 | 23.228 |
| ADC | 18.515 | 18.384 | 11.074 | 136.813 | 182.893 | 22.305 | 60.489 | 12.346 | 17.918 | 12.007 | 19.646 |
| Support | 21.113 | 20.645 | 10.806 | 120.968 | 100.542 | 39.408 | 92.738 | 20.879 | 33.853 | 20.472 | 35.624 |

**Objective-Zustand (Entscheidung 3):**

| Monster | frei | bestritten | umkaempft |
|---|---:|---:|---:|
| Drache | 7518 (60%) | 364 (3%) | 4594 (37%) |
| Elder | 49 (42%) | 0 (0%) | 67 (58%) |
| Larven | 7563 (72%) | 95 (1%) | 2854 (27%) |
| Herold | 2170 (67%) | 63 (2%) | 982 (31%) |
| Baron | 1921 (52%) | 65 (2%) | 1717 (46%) |

## 2. 30 Momente gegen die Rohdaten

Eigener schlichter Leser der Riot-JSON (nicht der Verdichter). Feld stimmt / geprueft:

back_60 30/30 · gold_60 17/17 · itemwert 30/30 · kills_gegner 30/30 · kills_wir 30/30 · kills_wir_60 30/30 · level 30/30 · pos_minute 17/17 · sieg 30/30 · tot_minute 17/17 · tuerme_wir 30/30

Dasselbe an 300 Momenten: back_60 300/300 · gold_60 167/167 · itemwert 300/300 · kills_gegner 300/300 · kills_wir 300/300 · kills_wir_60 300/300 · level 300/300 · pos_minute 169/169 · sieg 300/300 · tot_minute 169/169 · tuerme_wir 300/300

Hinweis: `tot_minute` ist zur vollen Minute per Bau gleich (die Todeszeit wird an den Minuten mit Leben 0/>0 gekappt); dazwischen gilt die Formel.

| Partie | Rolle | Zeit | Anlass | Bereich | Kills | Level | Aktion 60 s | Folge | Rohdaten |
|---|---|---|---|---|---|---|---|---|---|
| EUW1_7990749537 | Top | 2:00 | Minute | fluss_oben | 2:1 | L2 | Lane | 60 s: Kills 0:1, Gold 320, Tod | ok |
| EUW1_7989149675 | Support | 22:00 | Minute | jungle_rot_unten | 20:23 | L10 | Objective | 60 s: Kills 1:3, Gold 740, Tod | ok |
| EUW1_7996323894 | ADC | 4:00 | Minute | bot | 1:3 | L3 | Objective | 60 s: Kills 0:0, Gold 429 | ok |
| EUW1_7996624239 | Mid | 16:00 | Minute | top | 7:10 | L11 | Gruppe | 60 s: Kills 1:0, Gold 377 | ok |
| EUW1_7998260947 | Top | 26:00 | Minute | basis_rot | 31:29 | L17 | Tot | 60 s: Kills 2:0, Gold 170 | ok |
| EUW1_7979162686 | ADC | 16:00 | Minute | mid | 17:11 | L10 | Tot | 60 s: Kills 2:3, Gold 364, Tod | ok |
| EUW1_7984402629 | Support | 11:00 | Minute | mid | 13:10 | L6 | Rotation | 60 s: Kills 0:0, Gold 277 | ok |
| EUW1_7997521543 | Top | 6:00 | Minute | top | 4:3 | L6 | Unterwegs | 60 s: Kills 0:1, Gold 183, Tod | ok |
| EUW1_7985259386 | Jungle | 18:00 | Minute | jungle_rot_oben | 8:17 | L11 | Tot | 60 s: Kills 2:1, Gold 261 | ok |
| EUW1_7998346458 | Jungle | 3:00 | Minute | fluss_unten | 0:0 | L4 | Back | 60 s: Kills 0:0, Gold 183 | ok |
| EUW1_7989112300 | Top | 26:00 | Minute | mid | 23:21 | L16 | Unterwegs | 60 s: Kills 2:2, Gold 1375, Tod | ok |
| EUW1_7977795391 | ADC | 9:00 | Minute | bot | 7:8 | L6 | TP | 60 s: Kills 2:2, Gold 565, Tod | ok |
| EUW1_7985035168 | Mid | 13:00 | Minute | mid | 12:9 | L10 | Back | 60 s: Kills 1:1, Gold 340 | ok |
| EUW1_7982415072 | Top | 3:00 | Minute | top | 0:3 | L3 | Warten | 60 s: Kills 0:0, Gold 498 | ok |
| EUW1_7994077070 | Mid | 30:00 | Minute | mid | 35:28 | L18 | Unterwegs | 60 s: Kills 0:0, Gold 122 | ok |
| EUW1_7996870367 | Jungle | 28:23 | Kill | mid | 29:23 | L16 | Objective | 60 s: Kills 1:0, Gold 498 | ok |
| EUW1_7997799479 | Top | 28:38 | eigener Tod | jungle_rot_unten | 30:31 | L17 | Tot | 60 s: Kills 0:1, Gold 501 | ok |
| EUW1_7986055817 | Top | 17:41 | Gebaeude | bot | 20:19 | L11 | Unterwegs | 60 s: Kills 2:0, Gold 332 | ok |
| EUW1_7991478201 | Jungle | 5:00 | Monster-Spawn | jungle_blau_oben | 1:5 | L4 | Back | 60 s: Kills 0:0, Gold 431 | ok |
| EUW1_7990438105 | Support | 25:12 | Gebaeude | jungle_rot_unten | 23:34 | L11 | Tot | 60 s: Kills 0:0, Gold 449 | ok |
| EUW1_7978212617 | ADC | 3:41 | Kill | bot | 3:0 | L4 | Gruppe | 60 s: Kills 0:1, Gold 393 | ok |
| EUW1_7999432833 | Jungle | 13:00 | Kill | mid | 14:4 | L10 | Jungle | 60 s: Kills 0:0, Gold 547 | ok |
| EUW1_7976210976 | ADC | 16:16 | Kill | mid | 16:10 | L10 | Unterwegs | 60 s: Kills 0:0, Gold 974 | ok |
| EUW1_7993068769 | Top | 36:09 | eigener Tod | mid | 35:38 | L18 | Tot | Ende | ok |
| EUW1_7998233341 | Top | 33:21 | Gebaeude | basis_blau | 46:34 | L20 | Unterwegs | Ende | ok |
| EUW1_7981263541 | ADC | 18:30 | Kill | jungle_rot_unten | 18:8 | L11 | Back | 60 s: Kills 1:1, Gold 686 | ok |
| EUW1_7983085371 | ADC | 11:28 | Monster | bot | 1:8 | L8 | Unterwegs | 60 s: Kills 1:0, Gold 697 | ok |
| EUW1_7997082460 | Top | 25:22 | Back | mid | 24:17 | L15 | Tot | 60 s: Kills 2:4, Gold 518, Tod | ok |
| EUW1_7978276769 | ADC | 5:21 | Kill | bot | 3:4 | L4 | Back | 60 s: Kills 0:0, Gold 316 | ok |
| EUW1_7993206606 | ADC | 21:33 | Respawn | jungle_rot_oben | 13:21 | L13 | Back | 60 s: Kills 0:0, Gold 455 | ok |

## 3. Nullprobe je Aktions-Label (300 Partien)

Quote = Anteil der Momente mit diesem Label, bei denen dieselbe Regel auch mit falschem Ort oder falscher Zeit zutrifft. Klar unter 100 % = das Label haengt an Ort/Zeit des Moments.

| Aktion | Momente | Nullprobe | Quote |
|---|---:|---|---:|
| Tot | 24.174 | Zeit | 26% |
| Back | 38.993 | Zeit | 28% |
| Objective | 20.725 | Ort | 10% |
| TP | 301 | Zeit | 0% |
| Rotation | 10.698 | Zeit | 13% |
| Split | 652 | Ort | 12% |
| Gruppe | 27.706 | Ort | 36% |
| Jungle (Laner) | 2.222 | Zeit | 18% |
| Lane | 34.210 | Lane | 0% |
| Warten | 2.201 | Zeit | 3% |
| Unterwegs | 29.927 | Zeit | 22% |
| Jungle (Jungler) | 23.776 | Zeit | 69% |

## 4. Kein Maphack

`test_kein_maphack.py`. 30 Partien. 21.461 Lagen: Spalten verletzt 0. Lane-Gegner-Ort weiter als 1200 0. Zufallspositionen kamen in 2.934 Lagen bei lg_* an (der Test sieht also etwas). **BESTANDEN**. Sabotage-Gegenprobe (Jungler-Position in eine Spalte geschrieben): 3.269 von 3.269 Lagen verletzt. Test faellt durch (richtig).
