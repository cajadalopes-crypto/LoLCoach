# Merkmals-Verzeichnis der Entscheidungsmomente (Auftrag 030)

Erzeugt von `werkzeuge/challenger/phase1.py --merkmale`. Marke: **[B]** beobachtet (Ereignis oder volle Minute), **[G]** geschaetzt (zwischen den Minuten linear, Formel, Regel), **[U]** unbekannt (kommt nicht vor: was unbekannt ist, steht gar nicht in der Lage). Gegner: nur tot + Restzeit, zuletzt gesehen (angesagtes Ereignis) oder der Lane-Gegner nahe sichtbar (<= 1200) - sonst keine Gegnerposition.

## meta (int32)

| # | Name | Bedeutung | Quelle | |
|---:|---|---|---|---|
| 0 | `partie` | Nummer der Partie (partien.json) | Datei | [B] |
| 1 | `pid` | participantId 1-10 | Match | [B] |
| 2 | `team` | 0 = Blau, 1 = Rot | Match | [B] |
| 3 | `rolle` | 0 Top, 1 Jungle, 2 Mid, 3 ADC, 4 Support | teamPosition | [B] |
| 4 | `liga` | 0 Challenger, 1 GM, 2 Master, 3 unter Master (Ligalisten 30.09.) | league-v4 | [B] |
| 5 | `zeit` | Spielsekunde des Moments | Raster | [B] |
| 6 | `anlass` | 0 Minute, 1 Kill, 2 eigener Tod, 3 Respawn, 4 Back, 5 Gebaeude, 6 Monster, 7 Monster-Spawn | Ereignisse | [B] |
| 7 | `aufteilung` | 0 Training, 1 Pruefung Spieler, 2 Pruefung Zeit, 3 beides | aufteilung.json | [B] |
| 8 | `sieg` | 1 = sein Team gewinnt | Match | [B] |
| 9 | `dauer` | Partiedauer in s | Match | [B] |

## X – Lage (float32)

| # | Name | Bedeutung | Quelle | |
|---:|---|---|---|---|
| 0 | `minute` | Spielzeit in Minuten | Uhr | [B] |
| 1 | `x` | eigene Position x | Minute, dazwischen linear | [G] |
| 2 | `y` | eigene Position y | Minute, dazwischen linear | [G] |
| 3 | `bereich` | Kartenbereich (0-10, s. BEREICHE) | aus x, y | [G] |
| 4 | `zone` | 0 Basis, 1 oben, 2 mid, 3 unten | aus x, y | [G] |
| 5 | `in_eigener_lane` | steht in der Lane seiner Rolle | aus x, y | [G] |
| 6 | `abst_brunnen` | Abstand zum eigenen Brunnen | aus x, y | [G] |
| 7 | `abst_eigener_turm` | Abstand zum naechsten stehenden eigenen Turm | x, y + Gebaeude-Ereignisse | [G] |
| 8 | `abst_gegner_turm` | Abstand zum naechsten stehenden gegnerischen Turm | x, y + Gebaeude-Ereignisse | [G] |
| 9 | `abst_drache` | Abstand zur Drachengrube | aus x, y | [G] |
| 10 | `abst_baron` | Abstand zur Baron-/Herold-/Larvengrube | aus x, y | [G] |
| 11 | `tot` | gerade tot | Kills + Todeszeit-Formel | [B] |
| 12 | `respawn_rest` | Sekunden bis zur Wiederbelebung (0 = lebt) | Formel, an den Minuten (Leben 0/>0) gekappt | [G] |
| 13 | `level` | eigenes Level | LEVEL_UP | [B] |
| 14 | `cs` | eigene CS (Vasallen + Monster) | Minute, dazwischen linear | [G] |
| 15 | `gold_tasche` | Gold in der Tasche | Minute + verdientes Gold - Kaeufe | [G] |
| 16 | `itemwert` | Wert der Items (Scoreboard) | Kaeufe/Verkaeufe/Verbrauch + Preise Data Dragon | [B] |
| 17 | `leben_anteil` | Leben / max. Leben | letzte volle Minute | [G] |
| 18 | `hat_tp` | Teleport als Beschwoererzauber | Match | [B] |
| 19 | `seit_back` | Sekunden seit dem letzten Ladenbesuch (Back oder Tod) | Kaeufe | [B] |
| 20 | `mit_lebend` | lebende Mitspieler (ohne dich) | Kills + Formel | [B] |
| 21 | `mit_nah` | lebende Mitspieler <= 2500 bei dir | Minimap | [G] |
| 22 | `mit_abstand` | mittlerer Abstand der lebenden Mitspieler | Minimap | [G] |
| 23 | `mit1_x` | Mitspieler 1 (nach Rolle, ohne dich): x (NaN = tot) | Minimap | [G] |
| 24 | `mit1_y` | Mitspieler 1 (nach Rolle, ohne dich): y (NaN = tot) | Minimap | [G] |
| 25 | `mit2_x` | Mitspieler 2 (nach Rolle, ohne dich): x (NaN = tot) | Minimap | [G] |
| 26 | `mit2_y` | Mitspieler 2 (nach Rolle, ohne dich): y (NaN = tot) | Minimap | [G] |
| 27 | `mit3_x` | Mitspieler 3 (nach Rolle, ohne dich): x (NaN = tot) | Minimap | [G] |
| 28 | `mit3_y` | Mitspieler 3 (nach Rolle, ohne dich): y (NaN = tot) | Minimap | [G] |
| 29 | `mit4_x` | Mitspieler 4 (nach Rolle, ohne dich): x (NaN = tot) | Minimap | [G] |
| 30 | `mit4_y` | Mitspieler 4 (nach Rolle, ohne dich): y (NaN = tot) | Minimap | [G] |
| 31 | `kills_wir` | Kills (dein Team) | Ereignis | [B] |
| 32 | `kills_gegner` | Kills (Gegner) | Ereignis | [B] |
| 33 | `tuerme_wir` | zerstoerte Tuerme (dein Team) | Ereignis | [B] |
| 34 | `tuerme_gegner` | zerstoerte Tuerme (Gegner) | Ereignis | [B] |
| 35 | `inhibs_offen_wir` | gerade offene gegnerische Inhibitoren (dein Team) | Ereignis + 5 min | [B] |
| 36 | `inhibs_offen_gegner` | gerade offene gegnerische Inhibitoren (Gegner) | Ereignis + 5 min | [B] |
| 37 | `platten_wir` | Platten (dein Team) | Ereignis | [B] |
| 38 | `platten_gegner` | Platten (Gegner) | Ereignis | [B] |
| 39 | `drachen_wir` | Drachen (ohne Elder) (dein Team) | Ereignis | [B] |
| 40 | `drachen_gegner` | Drachen (ohne Elder) (Gegner) | Ereignis | [B] |
| 41 | `seele_wir` | Drachenseele (4 Drachen) (dein Team) | Ereignis | [B] |
| 42 | `seele_gegner` | Drachenseele (4 Drachen) (Gegner) | Ereignis | [B] |
| 43 | `larven_wir` | Larven (dein Team) | Ereignis | [B] |
| 44 | `larven_gegner` | Larven (Gegner) | Ereignis | [B] |
| 45 | `herold_wir` | Herolde (dein Team) | Ereignis | [B] |
| 46 | `herold_gegner` | Herolde (Gegner) | Ereignis | [B] |
| 47 | `baron_wir` | Barone (dein Team) | Ereignis | [B] |
| 48 | `baron_gegner` | Barone (Gegner) | Ereignis | [B] |
| 49 | `elder_wir` | Elder (dein Team) | Ereignis | [B] |
| 50 | `elder_gegner` | Elder (Gegner) | Ereignis | [B] |
| 51 | `baron_buff_wir` | Rest-Sekunden Baron-Buff (dein Team) | Ereignis + 180 s | [G] |
| 52 | `baron_buff_gegner` | Rest-Sekunden Baron-Buff (Gegner) | Ereignis + 180 s | [G] |
| 53 | `elder_buff_wir` | Rest-Sekunden Elder-Buff (dein Team) | Ereignis + 150 s | [G] |
| 54 | `elder_buff_gegner` | Rest-Sekunden Elder-Buff (Gegner) | Ereignis + 150 s | [G] |
| 55 | `itemwert_team_wir` | Item-Wert des Teams (dein Team) | Scoreboard | [B] |
| 56 | `itemwert_team_gegner` | Item-Wert des Teams (Gegner) | Scoreboard | [B] |
| 57 | `level_team_wir` | Level-Summe des Teams (dein Team) | Scoreboard | [B] |
| 58 | `level_team_gegner` | Level-Summe des Teams (Gegner) | Scoreboard | [B] |
| 59 | `cs_team_wir` | CS-Summe des Teams (dein Team) | Scoreboard (Minute, linear) | [G] |
| 60 | `cs_team_gegner` | CS-Summe des Teams (Gegner) | Scoreboard (Minute, linear) | [G] |
| 61 | `tote_wir` | gerade tote Spieler (dein Team) | Scoreboard | [B] |
| 62 | `tote_gegner` | gerade tote Spieler (Gegner) | Scoreboard | [B] |
| 63 | `diff_itemwert_team` | Item-Wert wir - Gegner | Scoreboard | [B] |
| 64 | `diff_level_team` | Level-Summe wir - Gegner | Scoreboard | [B] |
| 65 | `diff_itemwert_lane` | dein Item-Wert - Lane-Gegner | Scoreboard | [B] |
| 66 | `diff_level_lane` | dein Level - Lane-Gegner | Scoreboard | [B] |
| 67 | `diff_cs_lane` | deine CS - Lane-Gegner | Scoreboard (Minute, linear) | [G] |
| 68 | `lg_nahe_sichtbar` | Lane-Gegner lebt und steht <= 1200 neben dir ("nahe sichtbar"); bis 14:00, beide in der Lane der Rolle: <= 1800 | Minute, linear | [G] |
| 69 | `lg_x` | Lane-Gegner x, nur wenn nahe sichtbar, sonst NaN | Minute, linear | [G] |
| 70 | `lg_y` | Lane-Gegner y, nur wenn nahe sichtbar, sonst NaN | Minute, linear | [G] |
| 71 | `geg0_tot` | Gegner Top: tot | Scoreboard | [B] |
| 72 | `geg0_respawn` | Gegner Top: Rest-Sekunden tot | Formel | [G] |
| 73 | `geg0_gesehen_x` | Gegner Top: zuletzt gesehen x (NaN = nie) | angesagtes Ereignis mit Ort | [B] |
| 74 | `geg0_gesehen_y` | Gegner Top: zuletzt gesehen y | angesagtes Ereignis mit Ort | [B] |
| 75 | `geg0_gesehen_alter` | Gegner Top: Sekunden seit zuletzt gesehen (NaN = nie) | angesagtes Ereignis | [B] |
| 76 | `geg1_tot` | Gegner Jungle: tot | Scoreboard | [B] |
| 77 | `geg1_respawn` | Gegner Jungle: Rest-Sekunden tot | Formel | [G] |
| 78 | `geg1_gesehen_x` | Gegner Jungle: zuletzt gesehen x (NaN = nie) | angesagtes Ereignis mit Ort | [B] |
| 79 | `geg1_gesehen_y` | Gegner Jungle: zuletzt gesehen y | angesagtes Ereignis mit Ort | [B] |
| 80 | `geg1_gesehen_alter` | Gegner Jungle: Sekunden seit zuletzt gesehen (NaN = nie) | angesagtes Ereignis | [B] |
| 81 | `geg2_tot` | Gegner Mid: tot | Scoreboard | [B] |
| 82 | `geg2_respawn` | Gegner Mid: Rest-Sekunden tot | Formel | [G] |
| 83 | `geg2_gesehen_x` | Gegner Mid: zuletzt gesehen x (NaN = nie) | angesagtes Ereignis mit Ort | [B] |
| 84 | `geg2_gesehen_y` | Gegner Mid: zuletzt gesehen y | angesagtes Ereignis mit Ort | [B] |
| 85 | `geg2_gesehen_alter` | Gegner Mid: Sekunden seit zuletzt gesehen (NaN = nie) | angesagtes Ereignis | [B] |
| 86 | `geg3_tot` | Gegner ADC: tot | Scoreboard | [B] |
| 87 | `geg3_respawn` | Gegner ADC: Rest-Sekunden tot | Formel | [G] |
| 88 | `geg3_gesehen_x` | Gegner ADC: zuletzt gesehen x (NaN = nie) | angesagtes Ereignis mit Ort | [B] |
| 89 | `geg3_gesehen_y` | Gegner ADC: zuletzt gesehen y | angesagtes Ereignis mit Ort | [B] |
| 90 | `geg3_gesehen_alter` | Gegner ADC: Sekunden seit zuletzt gesehen (NaN = nie) | angesagtes Ereignis | [B] |
| 91 | `geg4_tot` | Gegner Support: tot | Scoreboard | [B] |
| 92 | `geg4_respawn` | Gegner Support: Rest-Sekunden tot | Formel | [G] |
| 93 | `geg4_gesehen_x` | Gegner Support: zuletzt gesehen x (NaN = nie) | angesagtes Ereignis mit Ort | [B] |
| 94 | `geg4_gesehen_y` | Gegner Support: zuletzt gesehen y | angesagtes Ereignis mit Ort | [B] |
| 95 | `geg4_gesehen_alter` | Gegner Support: Sekunden seit zuletzt gesehen (NaN = nie) | angesagtes Ereignis | [B] |
| 96 | `drache_da` | Drache/Elder: steht jetzt | Timer (wissen/objektive.toml) + Kills | [G] |
| 97 | `drache_bis` | Drache/Elder: Sekunden bis zum Spawn (-1 = kommt nicht mehr) | Timer (wissen/objektive.toml) + Kills | [G] |
| 98 | `larven_da` | Larven: steht jetzt | Timer (wissen/objektive.toml) + Kills | [G] |
| 99 | `larven_bis` | Larven: Sekunden bis zum Spawn (-1 = kommt nicht mehr) | Timer (wissen/objektive.toml) + Kills | [G] |
| 100 | `herold_da` | Herold: steht jetzt | Timer (wissen/objektive.toml) + Kills | [G] |
| 101 | `herold_bis` | Herold: Sekunden bis zum Spawn (-1 = kommt nicht mehr) | Timer (wissen/objektive.toml) + Kills | [G] |
| 102 | `baron_da` | Baron: steht jetzt | Timer (wissen/objektive.toml) + Kills | [G] |
| 103 | `baron_bis` | Baron: Sekunden bis zum Spawn (-1 = kommt nicht mehr) | Timer (wissen/objektive.toml) + Kills | [G] |
| 104 | `drache_ist_elder` | als Naechstes kommt der Elder | Drachen-Kills | [B] |

## aktion (int16)

| # | Name | Bedeutung | Quelle | |
|---:|---|---|---|---|
| 0 | `a0` | Aktion der naechsten 60 s (Code aus AKTIONEN, Vorrang in dieser Reihenfolge) | Regeln Phase 0 | [G] |
| 1 | `a1` | Aktion 60-120 s | Regeln Phase 0 | [G] |
| 2 | `a2` | Aktion 120-180 s | Regeln Phase 0 | [G] |
| 3 | `a3` | Aktion 180-240 s | Regeln Phase 0 | [G] |
| 4 | `flags` | Bit je Aktion, die in den naechsten 60 s zutrifft (mehrere moeglich) | Regeln Phase 0 | [G] |
| 5 | `ziel` | bei Objective: 1 Drache, 2 Baron, 3 Herold, 4 Larven, 5 Elder; bei Rotation: Zielzone 1-3 | Regeln | [G] |
| 6 | `ziel_zustand` | bei Objective-Kill: 0 frei, 1 bestritten, 2 umkaempft; -1 = Spawn/kein Kill | Entscheidung 3 | [G] |
| 7 | `tp` | 1 = TP sicher erkannt, -1 = TP unbekannt (hat TP), 0 = hat kein TP | Positionssprung, Phase 0 | [G] |
| 8 | `wohin` | Ort am Ende des Fensters bzw. des ersten eigenen Ereignisses darin (Code aus WOHIN) | Minute/Ereignis | [G] |
| 9 | `wohin_mit` | dort bei Mitspieler (Rolle 1-5, 0 = allein) | Minimap | [G] |

## folge (float32)

| # | Name | Bedeutung | Quelle | |
|---:|---|---|---|---|
| 0 | `gold_30` | eigenes verdientes Gold in 30 s | Minute, linear | [G] |
| 1 | `xp_30` | eigene XP in 30 s | Minute, linear | [G] |
| 2 | `teamgold_30` | Aenderung Team-Gold-Abstand in 30 s | Minute, linear | [G] |
| 3 | `tod_30` | du stirbst in 30 s | Kill | [B] |
| 4 | `kills_wir_30` | Kills deines Teams in 30 s | Kill | [B] |
| 5 | `kills_gegner_30` | Kills des Gegners in 30 s | Kill | [B] |
| 6 | `platten_wir_30` | Platten deines Teams in 30 s | Ereignis | [B] |
| 7 | `platten_gegner_30` | Platten des Gegners in 30 s | Ereignis | [B] |
| 8 | `gebaeude_wir_30` | Tuerme/Inhibitoren deines Teams in 30 s | Ereignis | [B] |
| 9 | `gebaeude_gegner_30` | Tuerme/Inhibitoren des Gegners in 30 s | Ereignis | [B] |
| 10 | `obj_wir_30` | Monster deines Teams in 30 s (Larve einzeln) | Ereignis | [B] |
| 11 | `obj_gegner_30` | Monster des Gegners in 30 s | Ereignis | [B] |
| 12 | `gold_60` | eigenes verdientes Gold in 60 s | Minute, linear | [G] |
| 13 | `xp_60` | eigene XP in 60 s | Minute, linear | [G] |
| 14 | `teamgold_60` | Aenderung Team-Gold-Abstand in 60 s | Minute, linear | [G] |
| 15 | `tod_60` | du stirbst in 60 s | Kill | [B] |
| 16 | `kills_wir_60` | Kills deines Teams in 60 s | Kill | [B] |
| 17 | `kills_gegner_60` | Kills des Gegners in 60 s | Kill | [B] |
| 18 | `platten_wir_60` | Platten deines Teams in 60 s | Ereignis | [B] |
| 19 | `platten_gegner_60` | Platten des Gegners in 60 s | Ereignis | [B] |
| 20 | `gebaeude_wir_60` | Tuerme/Inhibitoren deines Teams in 60 s | Ereignis | [B] |
| 21 | `gebaeude_gegner_60` | Tuerme/Inhibitoren des Gegners in 60 s | Ereignis | [B] |
| 22 | `obj_wir_60` | Monster deines Teams in 60 s (Larve einzeln) | Ereignis | [B] |
| 23 | `obj_gegner_60` | Monster des Gegners in 60 s | Ereignis | [B] |
| 24 | `gold_120` | eigenes verdientes Gold in 120 s | Minute, linear | [G] |
| 25 | `xp_120` | eigene XP in 120 s | Minute, linear | [G] |
| 26 | `teamgold_120` | Aenderung Team-Gold-Abstand in 120 s | Minute, linear | [G] |
| 27 | `tod_120` | du stirbst in 120 s | Kill | [B] |
| 28 | `kills_wir_120` | Kills deines Teams in 120 s | Kill | [B] |
| 29 | `kills_gegner_120` | Kills des Gegners in 120 s | Kill | [B] |
| 30 | `platten_wir_120` | Platten deines Teams in 120 s | Ereignis | [B] |
| 31 | `platten_gegner_120` | Platten des Gegners in 120 s | Ereignis | [B] |
| 32 | `gebaeude_wir_120` | Tuerme/Inhibitoren deines Teams in 120 s | Ereignis | [B] |
| 33 | `gebaeude_gegner_120` | Tuerme/Inhibitoren des Gegners in 120 s | Ereignis | [B] |
| 34 | `obj_wir_120` | Monster deines Teams in 120 s (Larve einzeln) | Ereignis | [B] |
| 35 | `obj_gegner_120` | Monster des Gegners in 120 s | Ereignis | [B] |

## obj (int32)

| # | Name | Bedeutung | Quelle | |
|---:|---|---|---|---|
| 0 | `partie` | Nummer |  | [B] |
| 1 | `zeit` | Sekunde des Kills |  | [B] |
| 2 | `art` | 1-5 wie ziel |  | [B] |
| 3 | `team` | 0 Blau, 1 Rot, -1 neutral |  | [B] |
| 4 | `zustand` | 0 frei, 1 bestritten, 2 umkaempft | Entscheidung 3 | [G] |
| 5 | `kills` | Kills +-30 s, <= 3000 |  | [B] |
| 6 | `gegner_nah` | Gegner des Nehmers <= 3000 (Position interpoliert) |  | [G] |

## verdeckt (float32) – NIE Lage, nur Vergleich/Ziel

| # | Name | Bedeutung | Quelle | |
|---:|---|---|---|---|
| 0 | `teamgold_diff` | echter Team-Gold-Abstand (im Spiel NICHT sichtbar - nur Vergleich) | Minute, linear | [G] |
| 1 | `jgl_bereich` | wo der Gegner-Jungler wirklich ist (Bereich 0-10, 11 = tot) - nur Ziel der Jungler-Karte | Minute, linear | [G] |

## Codes

- AKTIONEN: 0 Tot, 1 Back, 2 Objective, 3 TP, 4 Rotation, 5 Split, 6 Gruppe, 7 Jungle, 8 Lane, 9 Warten, 10 Unterwegs (-1 = keine Regel, z. B. kurz tot)
- BEREICHE: 0 basis_blau, 1 basis_rot, 2 top, 3 mid, 4 bot, 5 fluss_oben, 6 fluss_unten, 7 jungle_blau_oben, 8 jungle_blau_unten, 9 jungle_rot_oben, 10 jungle_rot_unten
- ANLAESSE: 0 Minute, 1 Kill, 2 eigener Tod, 3 Respawn, 4 Back, 5 Gebaeude, 6 Monster, 7 Monster-Spawn
- MONSTER (ziel): 0 –, 1 Drache, 2 Baron, 3 Herold, 4 Larven, 5 Elder
- WOHIN (wohin; bei Unterwegs auch ziel): 0 –, 1 eigene Basis, 2 Toplane, 3 Midlane, 4 Botlane, 5 Drachengrube, 6 Barongrube, 7 eigener Jungle oben, 8 eigener Jungle unten, 9 gegn. Jungle oben, 10 gegn. Jungle unten, 11 Fluss oben, 12 Fluss unten, 13 gegn. Basis

## Aktionsregeln (Fenster = die naechsten 60 s)

- **Fenster und Tod (031):** stirbt der Spieler im Fenster, endet es mit dem Tod - alle Orts-Regeln nehmen den letzten Ort davor. Keine Aktion setzt Ueberleben voraus (sonst misst der Aktionswert Glueck).
- **Tot:** nur wer jetzt schon tot ist.
- **Back:** ein Ladenbesuch beginnt (Kauf, nicht bis 45 s nach dem Tod).
- **Objective (hingehen, 031):** du stehst <= 3000 an der Grube, waehrend dort ein Monster offen ist - bei +60, wenn es dann steht (auch frisch gespawnt), oder in dem Moment, in dem es faellt, egal welches Team es nimmt. `ziel` = Monster, `ziel_zustand` = frei/bestritten/umkaempft (nur wenn es im Fenster faellt).
- **TP:** Positionssprung, der zu Fuss und per Recall nicht geht (Phase 0, Stufe sicher). Sonst `tp` = -1 (unbekannt), nie "kein TP", ausser der Spieler hat keinen TP.
- **Rotation:** Zone (oben/mid/unten) bei +60 anders als jetzt und bei +120 noch dieselbe; nicht Jungler, nicht Basis, lebend. `ziel` = neue Zone.
- **Split:** ab 14:00, bei +30 und +60 allein in derselben Seitenlane (Mitspieler >= 5000, >= 3 draussen).
- **Gruppe:** bei +60 mind. zwei lebende Mitspieler <= 2500, nicht in der Basis.
- **Jungle:** Monster-CS +2.
- **Lane:** bei +30 und +60 in der Lane der Rolle und CS +3 (Support ohne CS).
- **Warten:** lebt, bleibt im selben Bereich (<= 2500 bewegt), an keinem Kill/Gebaeude/Monster beteiligt, keine andere Regel.
- **Unterwegs:** lebt, keine Regel trifft (laeuft, kaempft ohne Objective). Stirbt er im Fenster, ist das Folge, nicht Aktion. `ziel` = WOHIN-Code (Entscheidung 031/0.1).
- **wohin / wohin_mit** (jede Aktion): Ort am Ende des Fensters bzw. des ersten eigenen Ereignisses darin (Kill, Tod, Gebaeude, Platte, Monster); Grube = <= 2000 an Drache/Baron; dazu der naechste Mitspieler <= 2500.
- `a0` = erste zutreffende in der Reihenfolge Tot, Back, Objective, TP, Rotation, Split, Gruppe, Jungle, Lane, Warten, Unterwegs; `flags` hat alle.
