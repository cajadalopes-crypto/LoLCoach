# Merkmale des Gehirns: was live verfügbar ist (Auftrag 031, Abschnitt 5)

Quellen live:
- **API:** Live Client Data API (`lolcoach/liveapi.py`, `zustand.py`);
- **Minimap:** Tracker in `minimap.py` und `lage.py`;
- **HUD:** `hud.py`;
- **abgeleitet:** der Coach rechnet es aus Ereignissen und Timern.

Die Namen der Merkmale stehen in [merkmale.md](merkmale.md). Für `gehirn.bewerte()` heißt ein fehlendes Merkmal
NaN. LightGBM rechnet damit weiter, die Aussage wird aber unsicherer.

| Merkmal(e) | live | Quelle | Anmerkung / Ersatz |
|---|---|---|---|
| `minute` | ja | API `gameTime` | |
| `x`, `y`, `bereich`, `zone`, `in_eigener_lane`, alle `abst_*` | ja | Minimap (eigenes Icon) | Die Türme für `abst_*turm` kommen aus den API-Ereignissen `TurretKilled`. |
| `tot`, `respawn_rest` | ja | API `isDead`, `respawnTimer` | live **genauer** als im Training (dort Formel, an Minuten gekappt) |
| `level`, `cs`, `gold_tasche`, `leben_anteil` | ja | API `activePlayer` / `allPlayers` | |
| `itemwert` (eigener) | ja | API-Items, Preise aus Data Dragon | |
| `hat_tp` | ja | API `summonerSpells` | |
| `seit_back` | ja | abgeleitet | Der Coach erkennt die Basis schon (`bereich = basis_eigen`). |
| `mit_lebend`, Tote je Team | ja | API `isDead` | |
| `mit_nah`, `mit_abstand`, `mit1..4_x/y` | ja | Minimap (Mitspieler immer sichtbar) | Verdeckte Icons fehlen; dann NaN. |
| `kills_*`, `tuerme_*`, `inhibs_offen_*`, `drachen_*`, `seele_*`, `larven_*`, `herold_*`, `baron_*`, `elder_*` | ja | API-Ereignisse (`ChampionKill`, `TurretKilled`, `InhibKilled`/`InhibRespawned`, `DragonKill`, `HordeKill`, `HeraldKill`, `BaronKill`) | |
| `baron_buff_*`, `elder_buff_*` | ja | abgeleitet (Kill + 180/150 s) | |
| `platten_*` | teilweise | **nicht in der API**; Minimap-Plattenleser (`platten.py`) | Ersatz: Platten-Ziffer der Minimap. Fällt sie aus, NaN. |
| `itemwert_team_wir`, `level_team_wir`, `cs_team_wir` | ja | API `allPlayers` (eigenes Team) | |
| **`itemwert_team_gegner`, `level_team_gegner`, `diff_itemwert_*`, `diff_level_*`** | **nur veraltet** | API `allPlayers`: Gegner-Items und -Level stehen dort nur **so, wie sie zuletzt gesehen wurden** (belegt in `lage.py`, Kha'Zix 144655: bis 3:34 „Stufe 1, 0 Items“) | Im Training stehen die **echten** Werte. Live liegen sie tiefer. **Das Risiko ist gemessen**, siehe Bericht, Abschnitt „Probleme“. **Ersatz:** in Stufe 3 die Gegner-Werte im Training auf „Stand beim letzten Sehen“ setzen, oder das Modell ohne sie nehmen. |
| `cs_team_gegner`, `diff_cs_lane` | wahrscheinlich veraltet | API `scores.creepScore` | Wird im Spiel geprüft. Bis dahin gilt dieselbe Vorsicht wie bei den Items. |
| `geg*_tot`, `geg*_respawn` | ja | API `isDead`, `respawnTimer` (alle Spieler) | |
| `geg*_gesehen_x/y/alter` | ja, aber **anders** | Minimap-Sichtungen (`lage.Lagebild.zuletzt`) | Im Training kommen sie **nur aus angesagten Ereignissen mit Ort** (Kill, Turm, Monster). Die Kill-Ereignisse der API tragen **keinen Ort**. Live sieht der Coach Gegner öfter (jede Minimap-Sichtung), das Alter ist also meist kleiner als im Training. **Ersatz:** live auch Minimap-Sichtungen nehmen, das ist näher an der Wahrheit. In Stufe 3 prüfen, ob das Modell dann zu sicher wird. Sonst live nur Sichtungen an Kill-Orten zählen. |
| `lg_nahe_sichtbar`, `lg_x/y` | ja | Minimap-Sichtung des Lane-Gegners ≤ 1200 (in der Lane-Phase ≤ 1800) | Live besser: Er ist auf dem Bildschirm. Das Spielbild ist im Coach noch nicht ausgewertet. |
| `drache_*`, `larven_*`, `herold_*`, `baron_*` (Timer), `drache_ist_elder` | ja | abgeleitet aus Ereignissen + `wissen/objektive.toml` | wie `kern/uhren` |
| `rolle`, `seite` | ja | API `position`, `team` | |
| `anlass` | ja | abgeleitet: welches Ereignis den Aufruf auslöst (0 = Takt) | |

**Nicht im Gehirn, weil in keinen Daten:**
- Wellenstände;
- Ward-Orte;
- Nebel;
- Abklingzeiten (Flash, TP, Ults).

Diese Lücken füllen die Rechner in Stufe 3 (Buch 17, Teil C).
