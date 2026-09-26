# Faktoren aus der Reasoning-Datei - was der Coach rechnet

Grundlage: `Reasoning/LoL Reasoning.txt` (Carlos, 50 Kapitel + zwei Zusatzlisten). Auftrag 26.09.2026:
"ALLE FAKTOREN aus der Reasoning-Datei verdrahten und den Coach damit intelligenter machen".

Legende:
- **rechnet** - fliesst in Entscheidungen und gesprochene Saetze ein (Stelle im Code)
- **teilweise** - ein Teil rechnet, der Rest fehlt (was genau)
- **nicht messbar** - der Coach kann es nicht sehen: nur Live-API + Bildschirm, kein Speicherlesen (Carlos'
  harte Grenze). Steht hier, damit niemand glaubt, es sei vergessen.

Die Datei selbst sagt: nicht 50 Checklisten, sondern ein Graph - Zustand -> Welle -> Prio -> Tempo ->
Kartenzugang -> Information -> Gegner-Vorhersage -> Aktionen -> Gegenantwort -> Erwartungswert. So ist es
gebaut: `bewertung.py` (Zustand, alles je Takt), `denker.py` (Kampf-Urteil: Faktoren addieren, Erwartungswert,
zusammenhaengender Satz, danach Gold -> Kauf -> Weg -> Wards), `entscheider.py` (Optionen mit Wert und
Sicherheit), `komponist.py` (Saetze je Anlass), `regeln.py` (wann).

## 1-3 Eigener Champion, eigene Power, Win Condition

| Faktor | Status | Wo |
|---|---|---|
| Level, Leben, Gold, Items, Item-Differenz, Lauftempo, Position, Richtung | rechnet | API + Minimap; `bewertung.bewerte`, `denker.kampf_faktoren` |
| Mana/Energie | rechnet | API `resourceValue`; Faktor "mana" (unter 25 %: "reicht kaum fuer eine Combo") |
| Ult und Faehigkeiten bereit, Beschwoererzauber-Abklingzeiten | rechnet | HUD-Leser (`hud.py`, `lage.eigene_*`) |
| Gold bis Item / Power Spike / naechstes Bauteil | rechnet | `kaufplan.py` (Lexikon-Build), `denker.kauf` inkl. Trank verkaufen |
| XP, XP bis Level | nicht messbar | die Live-API liefert kein XP, nur das Level |
| Passive, Buffs/Debuffs, Stacks, Item-Aktive | nicht messbar | nicht in der API; Bild-Erkennung waere ein eigenes Projekt |
| Level-/Item-/Leben-/Summoner-/Ult-/Wellen-/Zahlen-Vorteil | rechnet | `denker.kampf_faktoren` (relativ gewichtet), `bewertung.kraft_gegen` |
| Skalierung, Level-6-Sprung, fruehe Staerke | rechnet | `wissen/lane_kurve.toml` (173 Champions), Faktor "matchup" |
| Reichweite, Engage/Disengage, Burst/DPS | teilweise | Burst: Untergrenze seines Combos auf dich (Faktor "combo_er", alle 173 Champions aus den Spieldaten); Reichweite/Engage steckt grob in der Lane-Kurve |
| Win Condition des eigenen Champions | teilweise | Spielakte/Briefing (Claude, vor dem Spiel), Lane-Kurve |

## 4 Jeder Gegner

| Faktor | Status | Wo |
|---|---|---|
| Position, letzte Position, Richtung, Ankunftszeit (Worst Case) | rechnet | Minimap 60/s; `bewertung._gegner_lage` |
| Level, Items, Kills/Tode, Kopfgeld | rechnet | API; `bewertung.kopfgeld`, `kill_gold` |
| Leben | teilweise | Lebensbalken im Spielbild, nur wenn er auf deinem Bildschirm ist (`lebensbalken.py`); geeicht am eigenen Balken gegen die API: 297 Bilder, 90 % innerhalb +-2 % (`werkzeuge/balken_eichen.py`) |
| Goldschaetzung / ungenutztes Gold | rechnet | `bewertung.gold_offen` (+-300), Faktor "gold_offen" |
| Flash, Teleport, globale Ults | rechnet | Minimap-Spruenge + Chat-Pings (`zauber.py`, `lage._fernsprung`); im Kampf dazu das Spielbild (`lebensbalken.Balkenspur`) - braucht eine Partie zur Pruefung |
| andere Beschwoererzauber, Ult | teilweise | nur, wenn gepingt; Ult erst ab Level 6 |
| Mana | rechnet | Manabalken unter seinem Lebensbalken (`lebensbalken.mana`), Faktor "mana_er" bei Mana-Champions |
| Q/W/E-Abklingzeiten | nicht messbar | das Spiel zeigt fremde Abklingzeiten nicht |
| Recall-Zustand aller Gegner, Wiedereinstieg nach Tod | rechnet | 7 s still, dann weg = Brunnen; nach dem Tod Brunnen - Ankunft ab dort (`lage.brunnen_seit`, `bewertung._gegner_lage`) |
| Roam-Potenzial, Position in 5/10/20 s | teilweise | Ankunft je Gegner; Verschwundener: "bis Mid noch X Sekunden" |

## 5 Jungler-Tracking

| Faktor | Status | Wo |
|---|---|---|
| Startseite, Leash, Sichtungen, letzte Richtung, Wahrscheinlichkeit je Seite | rechnet | `jungle.py` |
| bisherige Ganks (Muster) | rechnet | `jungle.gank_muster`, Entscheider "muster" |
| wann er auf deiner Seite sein kann | rechnet | `denker.jungler_prognose` (Ward-Plan) |
| Camp-Respawns, Buff-Timer, Jungle-CS/Recall | offen | Camps auf der Minimap lesen waere moeglich, nicht gebaut |

## 6-9 Welle, Prio, Recall, Tempo

| Faktor | Status | Wo |
|---|---|---|
| Vasallen je Seite, Front, wer schiebt, alle drei Lanes | rechnet | `welle.py` (Minimap) |
| Prio je Lane | rechnet | `bewertung.prio_aus_welle` |
| Kanonen-Timing (2026-Takt) | rechnet | `entscheider.wellen_spawns`, `naechste_kanone` |
| Recall-Fenster (Welle crasht), Recall mit Kauf, Objective danach | rechnet | `regeln._recall_fenster`, Entscheider back_*, `denker.lane_tot_plan` |
| gegnerisches Item-Timing | rechnet | `gold_offen` |
| Nah-/Fernkampf-Vasallen, Wellen-Projektion 10/20/40 s | teilweise | Minimap unterscheidet die Vasallen nicht; Crash nur als Fenster |

## 10-13 Karte, Sicht, Information, Absicht

| Faktor | Status | Wo |
|---|---|---|
| alle Positionen, Tuerme, Platten, Objectives | rechnet | Minimap, Events, Platten-Ziffern (`platten.py`); Verbuendete unter anderen Icons/im Brunnen gehalten (`lage._verbuendete_halten`, 88-100 % statt 57-94 %) |
| wer kann dich erreichen, wer nicht (plausibel) | rechnet | `bewertung.bedrohung/plausibel`, `regeln._tief_ohne_sicht` |
| Ward-Vorschlag mit Zweck (Objective, Jungler-Weg) | rechnet | `regeln._ward`, `denker.ward_plan` |
| eigene/gegnerische Wards, Kontroll-Augen auf der Karte | offen | Ward-Icons der Minimap; ein erster Versuch fand sie neben Champion-Icons und Vasallen schwer unterscheidbar |
| Absicht (Gank, Recall, Objective) | teilweise | Jungler-Gank-Seite, Recall des Lane-Gegners, Gegner an der Grube |

## 14-19 Objectives, Cross-Map, Gold, XP, Kill-Druck, Kampf

| Faktor | Status | Wo |
|---|---|---|
| Spawn-Timer, Seele, wer ist zuerst da, Zahlen, Flash/Ult weg, Gold, Carry | rechnet | `bewertung.Kampflage`, `komponist.gegner_am_objective` |
| Cross-Map ("zu weit fuer dich: Druck auf deiner Seite") | rechnet | `komponist.vorwarnung/obj_dazu/jungler_spaet` |
| Kill-Gold nach Level, erstes Blut, Kopfgeld, Platten 120 | rechnet | `wissen/mechanik.toml`, `bewertung.kill_gold` |
| Kill-Wahrscheinlichkeit, Bedingungen | rechnet | `denker.urteil` (Summe, logistisch), Faktoren im Satz |
| Schaden in Zahlen: voller Combo + Zuenden gegen sein Leben, Turmschuesse | rechnet | `combo.py` (Riven, Camille, Graves: Wiki-Werte 26.15-26.19, Raenge und AD aus der API, bereit laut HUD, seine Ruestung), `rechnung.py` (Max-Leben, Zuenden, Turm); alle anderen: `faehigkeiten.py` (Formeln aller 173 Champions aus CommunityDragon, Schadensart aus dem Tooltip) als Untergrenze - zaehlt nur, wenn sie schon reicht; Grundwerte aus den Spieldaten (Data Dragon: AD-Wachstum 0) |
| Kampf 1v1 bis 5v5 | rechnet | `kraft_gegen` (Level, Items, Leben, Mitspieler in 1500) |

## 20-26 Faehigkeiten, Summoner, Ults, Matchup, Comp, Win Condition, Seite

| Faktor | Status | Wo |
|---|---|---|
| Flash-/TP-Tracking mit Rueckkehrzeit | rechnet | `zauber.py`, gesprochen "bis 12 39" |
| Ult-Tracking (eigene, Mitspieler, gegnerische) | teilweise | eigene/Mitspieler per HUD; Gegner nur per Ping/Minimap |
| Matchup (kurz/mittel/lang), Zone | rechnet | `lane_kurve.toml`, Faktoren "matchup", "zone" |
| Faehigkeiten-Interaktionen, Konter-Wissen je Champion | teilweise | Lexikon fuer Claude (Fragen, Briefing); live der passende Tipp aus "Gegen diesen Champion" (1459 Tipps, 173 Champions) je Lage einmal (`denker.tipp`) - Faehigkeitsschaden nicht gerechnet |
| Team-Comp, Win Conditions | teilweise | Briefing (Claude); Carry je Team (`bewertung.carry`) |
| Seiten-Lane / Split | rechnet | Entscheider "seite", "seite_nicht" |

## 27-33 Tod, Risiko, Umkehrbarkeit, Reihenfolge, Vorhersage, Gegenantwort, Information

| Faktor | Status | Wo |
|---|---|---|
| Todeswert: Todeszeit, Kopfgeld, Objective waehrenddessen | rechnet | `komponist.todespreis` |
| Risiko/Ertrag (Erwartungswert) | rechnet | `denker.erwartung`: kein Kill, wenn dein Tod mehr kostet |
| Umkehrbarkeit | teilweise | kein Dive-Rat mehr (Live 11:00/11:08) |
| Reihenfolge | rechnet | Kill -> Gold -> Kauf -> Welle -> back -> Wards -> Objective; Kanone vor Objective |
| Gegenantwort | rechnet | wer kann mitkommen ("allein schlaegst du Vi - aber mit Kassadin ...") |
| Informationswert | rechnet | Wards dort, wo die naechste Entscheidung faellt |

## 34-50 Kontrolle, Position, Gelaende, Turm, Zeit, Seite, Denial, Umwandlung, Effizienz, Kosten, Spieler

| Faktor | Status | Wo |
|---|---|---|
| Turm-Zustand (Platten, Stufe, gefallen) | rechnet | Events + Minimap-Ziffern; Turm-Leben nicht messbar |
| Position (tief, unter Turm, Weg zum Turm) | rechnet | `bewertung` (tiefe, zum_turm) |
| Spielzeit/Phase, Todeszeiten | rechnet | ueberall (Lane-Phase bis 14:00, `todeszeit`) |
| Ressourcen-Umwandlung, Aktions-Effizienz | rechnet | Aufbruch-Satz: Kauf + Kontroll-Auge + Wards auf dem Weg |
| Gelaende, Blast Cones, Pflanzen | nicht messbar | nicht aus Minimap/API |
| Spieler-Faktor (Tode kurz hintereinander, Profil) | teilweise | Reset-Plan nach zwei Toden, `profil.py` |
| Spieltheorie (Bluff, Fake-Recall) | nicht messbar | |
| Muster (Gank-Muster) | teilweise | Gank-Muster ja, Recall-Muster nein |
| Entscheidungsgeschwindigkeit | rechnet | alles gerechnet, keine Claude-Wartezeit im Spiel; Stimme Satz fuer Satz |

## Zusatzlisten (Ende der Datei)

Die zweite und dritte Liste wiederholen die Kapitel oben (Oekonomie, Map, Comp, Champion-States, Welle, Risiko,
Mentales, Makro, Mechanik, Meta, Soft-Faktoren). Neu darin und nicht messbar: Tilt/Mentales des Gegners,
Kommunikation, Ping/Latenz, Patch-Meta, Smurf-Wahrscheinlichkeit. Die sechs Fragen am Ende ("Wer ist staerker?
Wer ist zuerst da? Was sehen wir nicht? Welche Welle verlieren wir? Was bekommt der Gegner? Was gewinnen wir
nach dem Play?") beantwortet das Kampf-Urteil (`denker.urteil` + `fenster_satz`) je Ansage.

## Nachgemessen (Nacht 26./27.09., an 5 aufgenommenen Partien, je mit Wahrheit aus der API oder dem Bild)

| Groesse | Wahrheit | Ergebnis | Werkzeug |
|---|---|---|---|
| Lebensbalken im Bild | eigenes Leben (API) | 90 % innerhalb +-2 % (nach Eichung 78 px) | `balken_eichen.py` |
| Minimap: wer ist wer | Sichtprobe von Hand | 30 Icons, 0 Verwechslungen | - |
| Minimap: Ringfarbe | eigenes Team blau / Gegner rot | 0,17-0,43 % falsch (Einzel-Champions) | `minimap_ringprobe.py` |
| Minimap: eigenes Icon | Kamerarahmen | 99,3-99,7 % im Rahmen | `kamera_rahmen.py` |
| Flash (eigener) auf der Minimap | HUD | 2 von 7, 0 Fehlalarme (im Kampf liegt das Icon unter dem Gegner) | - |
| Jungler-Prognose | naechste Sichtung | 44/60 richtig, Brier 0,183 (Raten 0,250) | `jungler_prognose.py` |
| Gegner-Ankunft "fruehestens" | Strecken zwischen Sichtungen | vorher 19 % schneller als gerechnet -> jetzt 90 % gedeckt | `gegner_tempo.py` |
| Kill-Gold | Goldsprung beim eigenen Kill | vorher Median -118 -> jetzt +2 (80 % in 65) | `kill_gold.py` |
| Gegner-Gold (ungenutzt) | seine Einkaeufe | Jungler/Support vorher -475/-298 -> je Rolle -90..+47 | - |
| Max-Leben (Gegner) | eigenes maxHealth | vorher -6 % -> jetzt Median 1,00 (Leben-Rune) | - |
| Ruestung / Magieresistenz | eigene Werte | Median 1,00 | - |
| Todeszeit | respawnTimer | Median -0,2 s | - |
| Kampf-Urteil | Kill/Tod in 20 s | kill 22 -> 9 Kills, 0 Tode; kill_schnell 7 -> 5, 0 Tode | (scratchpad) |
| Minimap: Position des Taeters | Ereignisse (Drache/Larven/Turm: Ort; Kill: beim Opfer) | 10 Partien, 174 Ereignisse mit Sichtung: 3 falsch - alle mit Code vor 17:42 am 26.09. (Geister-Icon klebte an Teemo, heute nicht mehr: `minimap.finde` findet dort nichts); seit 19:45 0 falsch | `minimap_ereignisprobe.py` |
| Minimap: eigene Position | lebend, ausserhalb der ersten Minute | 194524 8,2 %, 212105 4,9 % der Takte ohne (Brunnen, vor 0fdab75); 235433 0,6 % | (scratchpad) |
| Stimme: erster Ton | Wanduhr ab Abgabe | live 0,63 s -> stumm gemessen 0,19-0,29 s (Streaming, WASAPI), 0,01 s vorbereitet | `stimmprobe.py`, `verzoegerung_live.py` |
