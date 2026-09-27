# Auftrag 002 – Sofort-Fixes aus Carlos' Partie 213624 (Claude, Chat, 27.09.2026 22:10)

**Quelle:** `aufnahmen/2026-09-27_213624_notizen.md`, `_sprechtaste.log` und `_ansagen.json`. Die Partie war Riven
gegen Rumble, eine Bot-Partie (CLASSIC, 25 min, 29/1/3).

Der Coach lief dabei mit einem Zwischenstand. Er wurde um 21:36 gestartet, mitten in Qualitätsrunde 3, also ohne den
fertigen Kaufplan (R3). Prüf deshalb jeden Punkt am **heutigen** Stand, bevor du ihn umbaust.

Die Fragen per Sprechtaste (Schritt 6) und die Vorausplanung („was als Nächstes“) kommen **nicht** hier dran. Dafür
schreibe ich Buch 11. Hier geht es nur um das, was ohne Buch klar ist.

Wie immer gilt: erst das Szenario rot, dann der Fix. Während der Arbeit prüfst du nur die betroffenen Dateien, den
vollen Lauf machst du einmal am Ende.

## S1. Zahlen so sprechen, wie Spieler sie sagen

- **Gold:** „3000“ wurde „drei null null null“ vorgelesen (Carlos um 11:12). Gold wird als Zahlwort gesprochen, auf
  Hunderter gerundet: „dreitausend“, „dreitausendeinhundert“. Vermutlich ist das eine Nebenwirkung von E8
  (Uhrzeiten als Wörter). Prüf alle Zahlen-Pfade.
- **Kills:** Nie „6/0“ oder ein Schrägstrich. Eigene Bilanz: „du stehst sechs null“. Teams: „ihr führt sieben zu
  drei“.
- **Test:** Jede Satzvorlage mit Zahl durch edge-tts und Whisper zurück, dieselbe Probe wie in E8.

## S2. Stimme: englische Namen und Tempo

Carlos: „redest viel zu lange und dazu auch noch viel zu langsam … immer zu spät“. Außerdem klingen die
Champion-Namen deutsch („Rumble“, „Xin Zhao“, „Caitlyn“).

1. Erzeuge je Stimme dieselben 8 Beispielsätze mit Champion- und Item-Namen, zum Beispiel
   „Raus, zum Turm: Xin Zhao und Rumble kommen.“ Die Stimmen:
   - die heutige Stimme
   - `de-DE-FlorianMultilingualNeural`
   - `de-DE-SeraphinaMultilingualNeural`
   - jede weitere mehrsprachige deutsche Stimme, die edge-tts anbietet

   Die Stimmen kommen nach `aufnahmen/stimmproben/`, Dateiname = Stimme. **Carlos wählt.** Bis dahin bleibt die
   Stimme.
2. **Tempo:** Standard +20 % (`--tempo`, in der toml einstellbar). Die Proben gibt es in normalem und schnellem
   Tempo.
3. Ergänze in Buch 0, 9.3: PLAN höchstens 14 Wörter (bisher 18), GEFAHR höchstens 8. Kürze alle Satzvorlagen, die
   darüber liegen. Das Wichtigste steht vorn.

## S3. Flash

Carlos will **hören**, wenn ein Gegner Flash benutzt hat. Er entscheidet damit, auf wen er als Riven geht.

1. **Ansage:** Ein bestätigter Flash eines Gegners wird kurz gesagt, als eigene Kategorie INFO_FLASH:
   „Ziggs ohne Flash.“ (höchstens 4 Wörter).
   - Bestätigt heißt: Chat-Ping oder Minimap-Sprung bei einem Champion ohne eigenen Dash (Entscheidung 3 der
     Prüfung b).
   - Nicht in KAMPF. Die Ansage kommt dann 3 s nach Kampfende, wenn der Flash noch weg ist.
   - Höchstens eine je 20 s. Mehrere werden zusammengefasst: „Ziggs und Sona ohne Flash.“
2. **Antworten:** Die Antwort auf „Wie sieht's mit den Flashes aus?“ nennt jeden Gegner mit bekanntem Stand („Rumble
   ohne Flash, noch 4 Minuten“) und sagt ehrlich, von wem nichts bekannt ist.
   - Falsch war um 23:22: „Dazu hab ich keine Daten.“ Um 9:13 wusste er es noch.
   - Die Flash-Timer gehören in den Kontext, den Claude bekommt.
3. **Logik:** Fehlender Flash beim Gegner ist ein Grund **für** einen Angriff, nie dagegen. Carlos um 23:45: „Das ist
   doch extrem gut, wenn die kein Flash haben.“ Prüf den Kontext- bzw. Systemprompt für Antworten darauf und
   schreib die Regel dort ausdrücklich hinein.

## S4. Teleport aus der Top-Quest

Carlos: „Du planst nie meinen Teleport ein, den ich durch meine Toplane-Quest bekomme.“ Riven spielt Blitz und
Entzünden, das TP kommt aus der Quest (`saison2026.md`: spätestens 13:35; Quest-TP 390 s).

1. **Messen:** Woran ist in den Aufnahmen zu sehen, dass die Quest fertig ist und das Quest-TP bereit ist?
   - Ein HUD-Platz der Quest, API-Felder, Ereignisse.
   - Woran erkennt man eine Benutzung? Rivens eigenes Icon springt beim Teleport.
   - Der Befund kommt nach messungen.md.
2. **Umbau:** `tp_in` berücksichtigt das Quest-TP. Wo die Wahrnehmung nicht reicht, gilt: ab Quest-Ende bereit, nach
   einem erkannten Teleport 390 s weg. Damit greifen die TP-Regeln aus Buch 5, Kapitel 5 und Buch 6, 4.7.

## S5. Falsche Warnungen in 213624

1. **16:21:** „Raus zu deinem Mid-Tier-1-Turm: Caitlyn und Sona kommen.“ Carlos um 16:31: „Alle sind tot. Warum sagst
   du, ich soll zurückgehen?“ Prüf, ob tote Gegner (bzw. solche, die gerade gestorben sind) als ankommend zählten, und
   behebe das.
2. **Ein einzelner Gegner ist keine Gefahr, wenn du ihn klar überragst.** Das verallgemeinert R5 über den Lane-Gegner
   hinaus.
   - Beispiele: 15:15, 17:32, 21:37 „Ziggs kommt“, als Riven 20+ Kills hatte.
   - Kein GEFAHR, wenn genau ein Gegner kommt, dein Leben ≥ 60 % ist und du ≥ 2 Level **und** ≥ 1500 Item-Gold vor ihm
     liegst. Die Gegnerwerte werden dabei nach Buch 7, 3.2 geschätzt, wenn sie veraltet sind.
3. **RAUS im Kampf nur mit robustem Beleg, bis die Kampf-Eichung besteht.**
   - Beispiel: 1:11 und 1:17, zweimal „Raus, zum Turm!“ in einem Level-1/2-Kampf, den Riven gewann.
   - Robust heißt: Sie sind in `kampf_radius` ≥ 1 mehr als ihr, **oder** dein Leben liegt unter 30 % und ist niedriger
     als das des nächsten Gegners (Balken).
   - Sonst bleibt RAUS stumm, wie REIN.

## S6. Warum das Gold verkehrt herum wirkt (AUC 0,30)

**Verdacht:** Die Gegner-Items sind Stand der letzten Sichtung (Buch 7, Nebenbefund). Gegner, die aus dem Nebel
kommen, sehen dann ärmer aus, als sie sind, und genau solche Kämpfe gehen verloren.

1. Rechne `kampf_eichung.py` noch einmal mit der Schätzung aus Buch 7, 3.2 (`unsichtbar_s`, `level_abschlag`,
   `item_anteil`).
2. Mach den Back-Test aus Buch 7, Nebenbefund: Ändern sich die API-Items eines Gegners während eines Backs, den man
   nicht sieht?
3. Die Zahlen kommen nach messungen.md. Die Rufe bleiben stumm, bis die Eichung besteht.

## S7. Szenarien aus 213624

1. `werkzeuge/szenario_aus_notizen.py` für 213624 ausführen. Die Stubs gehören nach `tests/szenarien/offen/`.
2. Dazu kommen konkrete Szenarien für S1, S3 und S5 in `tests/szenarien/2026-09-27_213624.toml` (`bots = true`). Sie
   prüfen nur Verdrahtung und Form, geeicht wird an Bot-Kämpfen nichts.
3. Trag Carlos' Wünsche aus der Partie in `OFFEN.md` ein:
   - Vorausplanung und nächste Schritte
   - Fragen werden nicht beantwortet
   - Aussprache
   - Tempo
   - Flash
   - Quest-TP
   - Zahlen

   Bei jedem steht, welcher Auftrag bzw. welches Buch ihn abdeckt.

## Ende

Die neuen Protokolle schreibst du für 213624, 164326 und 173159, messungen.md bekommt den Abschnitt „Auftrag 002“.
Dann committest du und schreibst `002_bericht.md` im Format aus `README.md`. Starte den Coach nicht. Stimmproben
erzeugen ist erlaubt, das ist kein Coach-Start.
