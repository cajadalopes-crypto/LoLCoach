# Buch 14 – Bauplan: Lagebild, Kampfrechner, Gehirn mit Plan (29.09.2026)

Entschieden mit Carlos am 29.09.2026. Er hat einen Claude-API-Schlüssel und einen Riot-Entwickler-Schlüssel angelegt,
beide liegen in `geheim/` (nie committen, nie ausgeben, nie loggen). **Keine Testpartien. Geprüft wird an Aufnahmen
und an Riot-Partiedaten.**

## Warum neu aufstellen

Augen, Ohren, Stimme und Aufzeichnung bleiben. Das Gehirn war bisher ein Regelwerk, dem ein Stratege aufgesetzt wurde,
und das hat vier Folgen:
- starre Sätze („Drück die Top-Welle“);
- Hin und Her zwischen Kern und Stratege;
- dünne Lage für Claude;
- 2 bis 7 s Latenz über das Abo.

Die Probe aus 013/014 zeigt, dass Claude mit guter Lage im Blindvergleich 70–80 % gewinnt. Deshalb gilt:

- **Claude ist das Gehirn:** Plan, Makro, Antworten, Kampfempfehlung.
- **Der Kern ist Reflex und Wächter:**
  - Sofortwarnungen, Jungler- und Flash-Meldungen, Timer;
  - die harte Prüfung jedes Satzes (`stratege.pruefe`);
  - Ersatz, wenn die API ausfällt.
- **Rechnen statt raten:** Kampf, Gold, Timer und Wege rechnet Code exakt. Claude bekommt die Ergebnisse, nicht nur
  Rohdaten.

## Schritt A – Lagebild und schnelle Anbindung

1. **`lolcoach/welt.py`:** Ein Lagebild je Takt aus den bestehenden Modulen (bewertung, lage, kartenlage, zeitleiste,
   kaufplan, teamplan), als eine Quelle für Kern und Claude.
   - **Je Spieler (10):** Champion, Rolle, Level, Items (Gegner: zuletzt gesehen), Leben (wenn sichtbar), Flash, TP und
     Ult mit Timer, soweit bekannt. Dazu der Ort: „jetzt sichtbar …“ oder „zuletzt gesehen vor N s …, vermutlich …“.
   - **Karte:** stehende Türme und Inhibitoren, Objectives (API-Ereignisse und Minimap-Symbole aus 018), Wellen aller
     drei Lanes.
   - **Timer:** Objective-Spawns, Respawns, Baron- und Drachen-Buffs.
   - **Stärke:** Gold- und Level-Differenz, Item-Spikes, Siegbedingung aus dem Teamplan.
2. **Text für Claude:**
   - kompakt und eindeutig, höchstens ~1500 Tokens;
   - feste Reihenfolge, damit der Zwischenspeicher greift;
   - dazu ein Block „seit dem letzten Aufruf“ mit den Ereignissen der letzten 30 s.
3. **`lolcoach/llm_api.py`:** Claude über die API (anthropic-SDK).
   - Streaming; Zwischenspeicher für System und Wissen.
   - Schlüssel aus `geheim/claude_api_key.txt`.
   - **Modelle:** die aktuellen IDs aus der offiziellen Modellübersicht (platform.claude.com/docs), ein schnelles
     (Haiku) und ein starkes (Sonnet). Welches wofür, entscheidet die Messung.
   - **Kostenzähler je Partie:** `aufnahmen/<partie>_kosten.json`.
   - **Ersatz:** das Abo über die Kommandozeile, wenn der Schlüssel fehlt oder die API ausfällt.
4. **Messen an Aufnahmen** (Nachspiel wie in 016):
   - Latenz bis zum ersten ganzen Satz, Ziel Median ≤ 1,5 s;
   - Kosten je 30 min;
   - Treffer der blinden Soll-Liste (017) mit altem und neuem Lagebild.

## Schritt B – Kampfrechner

1. **Fähigkeitswerte aller Champions** aus einer strukturierten Quelle, zuerst Meraki Analytics `lolstaticdata`
   prüfen, sonst CommunityDragon.
   - Ablage in `wissen/faehigkeiten/` mit Patch-Stand.
   - Abgleich mit den Wiki-Werten in `combo.py` für Riven, Camille und Graves. Sie müssen übereinstimmen.
2. **`lolcoach/kampf_rechner.py`:**
   - **Eingabe:** Verbündete und Gegner an einem Ort.
   - **Rechnung:** Burst je Champion aus Rängen, Items und Level gegen Leben, Rüstung und MR.
   - **Bekannte Abklingzeiten:** Flash und Ult aus HUD, Mitspieler-Leiste und Sichtungen. Unbekanntes gilt beim Gegner
     als bereit.
   - **Ergebnis:** wer wen in welcher Zeit tötet; Urteil „klar vorn / knapp / klar hinten“ mit den zwei
     entscheidenden Zahlen.
3. **Eichung an Riot-Daten** (Match-V5, Entwickler-Schlüssel aus `geheim/riot_key.txt`, Grenzen 20/s und 100/2 min
   einhalten):
   - **Daten:** einige tausend Partien aus hohem Elo (Challenger, Grandmaster, Master in EUW), nur die Zeitleisten.
   - **Kämpfe:** Häufungen von Kills (≤ 15 s, ≤ 2000 Einheiten). Dazu der Stand der Minute davor: Level, Items, Gold,
     Orte.
   - **Frage:** Sagt der Rechner den Sieger richtig?
   - **Tor:** In „klar vorn“ und „klar hinten“ muss er ≥ 80 % treffen. Erst dann darf das Gehirn Kämpfe ansagen.
     „Knapp“ bleibt eine Option ohne Befehl.
   - **Grenzen offen nennen:** Die Zeitleiste hat kein Leben zu Kampfbeginn und keine Abklingzeiten.
   - Der Schlüssel läuft alle 24 h ab. Braucht es einen neuen, steht das im Bericht, damit ich es Carlos sage.

## Schritt C – Gehirn mit Plan

1. **Plan-Objekt**, von Claude geführt:
   - Inhalt: Ziel, nächste Schritte, Grund, gültig bis, Abbruch-Bedingungen.
   - Neu gefasst wird er nur bei Ereignissen: Wendepunkt, Sichtung, Kampf in der Nähe, Objective in 60 s oder 40 s,
     Back, Respawn.
   - Der Schiedsrichter aus 017 bleibt: Ohne Lageänderung gibt es keine Kehrtwende.
2. **Wissen je Partie** (als zwischengespeicherter Block):
   - Makro-Regeln aus Buch 13 und `wissen/`;
   - für die zehn Champions dieser Partie Powerspikes und Matchup-Notizen aus dem Lexikon;
   - Carlos' Build.
3. **Kampfansagen** nur über den Kampfrechner und nur für geeichte Urteile.
   - **Klar vorn:** „Nehmt den Kampf: ihr macht 2400 in 3 s, Kog'Maw hat 1600 Leben und kein Flash.“
   - **Knapp:** zwei Optionen mit Grund.
4. **Kern:** Sofortmeldungen, Wächter (`pruefe`, R1, Kill-Check), Ersatz.
5. **Messen:** alle Aufnahmen mit blinder Soll-Liste ≥ 80 %, Sicherheit 0 / 0 / 0, Latenz, Kosten. Die Kritiker
   arbeiten blind.

## Begriff: Lebendige Arbeitspakete (Carlos, 29.09.2026)

Die To-dos, die der Coach gibt, heißen im Projekt **lebendige Arbeitspakete**. Der Coach sagt sie nicht nur an. Er
überwacht sie in jedem Takt und meldet sofort, wenn eines erledigt ist, ungültig wird (Objective weg, Team tot,
Gegnerüberzahl) oder ein besseres Play auftaucht. Dann gibt er direkt das nächste Paket mit Grund (Auftrag 024).

## Reihenfolge der Aufträge

017 (läuft) → 019 = Schritt A → 018 (Befunde aus der Graves-Partie, ergänzt das Lagebild) → 020 = Schritt B → 021 = Schritt C.

Nach jedem Schritt liest Claude (Chat) den Bericht und die Nachspiele, bevor der nächste freigegeben wird.
