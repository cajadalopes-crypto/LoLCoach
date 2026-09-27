# Auftrag 004 – Das Gehirn im Mid-Game: Überlegenheit, echte Antworten, Kampf-Eichung (Claude, Chat, 28.09.2026 00:20)

Ich habe das neue Protokoll von 213624 mit allen Antworten gelesen.

**Was jetzt funktioniert:** die Maschinerie. Wendepunkte, Zeitleiste und Fragen laufen über den Kern, in 0 ms.

**Was noch nicht funktioniert:** der Inhalt im Mid-Game.

- Die häufigste Antwort ist „Farm deine Top-Welle, bis sich etwas öffnet.“ Sie kommt auch, wenn Carlos 29/1 steht,
  alle Gegner tot sind (16:35) oder er mit seinem Team an der Drachengrube steht (13:13, 13:18).
- „Danach rechne ich neu.“ (16:42) ist eine Floskel.
- WARUM-Fragen gehen an der Frage vorbei:
  - 1:22 „Warum soll ich raus zum Turm?“ → „Turm ist gerade keine Option.“
  - 12:41 „Warum bist du dir so sicher, dass der Drache noch lebt?“ → „Zum Drachen: ihr seid drei.“
- Korrekturen werden überhört: 4:05 „Der ist jetzt bei mir oben.“ → „Farm deine Top-Welle.“

So würde ich das nicht freigeben. Ein Challenger sagt einem 29/1-Riven nicht „farm, bis sich etwas öffnet“. Er sagt:
„Du bist Level 17 gegen 12: nimm den inneren Turm, Rumble ist 40 Sekunden tot, danach Drache mit Team.“

## Teil A – Entscheidungen zu 003_bericht.md

1. **Kein ungefragtes „unsicher“.** Ein Coach, der ständig „unsicher“ sagt, hilft niemandem. Stattdessen gilt:
   - **Überlegenheits-Regel (Teil B).** Wo die Überlegenheit robust belegt ist, sprechen die Kampf-Optionen ohne
     Kampfmodell.
   - **Pläne mit Fenster** (das Ziel fällt vor dem ersten Verteidiger) sprechen wie bisher.
   - **Bleibt nur FARMEN,** wird es nur mit Vorschau gesagt, nie allein. Beispiel: „Farm Top, Drache in 70 Sekunden,
     dann zur Gruppe.“ Ohne ein Ereignis in der Zeitleiste in ≤ 90 s ist FARMEN still, wie vorher.
   - **Auf direkte Fragen** darf die beste Kampf-Option mit „unsicher“ genannt werden. Ungefragt nicht.
2. **Kein Unterbrechen durch Wendepunkte.** Das Stottern von vorgestern war genau das. Stattdessen:
   - Ein Wendepunkt-Satz stellt sich vor alle wartenden PLAN-Sätze.
   - Wartende Sätze, die durch den Wendepunkt ungültig werden, fallen weg.
   - Fallen mehrere Türme in 10 s, wird daraus **ein** Satz: „Zwei Türme down: …“.
   - Die Messung zählt ab dem Ende des laufenden Satzes. Soll ≤ 3 s danach.

## Teil B – Überlegenheits-Regel (bis die Kampf-Eichung besteht)

**Robust klar überlegen** gegen eine Gegnergruppe G, die in `fenster_s` am Ort sein kann (Schätzung aus Buch 7, 3.2
bei veralteten Werten). Es gilt alles davon:

- Eure Köpfe ≥ ihre Köpfe (Mitspieler in `fenster_s` zählen mit).
- Dein Leben ≥ 60 %.
- **Und eins davon:**
  - Du liegst vor jedem Gegner in G ≥ 3 Level.
  - Du liegst vor jedem Gegner in G ≥ 2 Level **und** ≥ 2000 Item-Gold.
  - Eure Köpfe ≥ ihre + 2.

**Robust klar unterlegen:** spiegelbildlich.

**Wirkung:**

- Klar überlegen: `DRUECKEN`, `MIT_GRUPPE`, `NEHMEN`, `BESTREITEN`, `ANNEHMEN` und `REIN` sprechen, auch ohne Fenster.
  Der Grund nennt die Überlegenheit („Level 17 gegen 12“, „ihr seid vier gegen zwei“).
- Klar unterlegen: Diese Handlungen sind aus.
- Dazwischen: wie heute, also nur mit Fenster.
- **Turm-Dives** bleiben unter Buch 7, Kapitel 6.

**Szenarien aus 213624** (Bot-Partie, nur Verdrahtung):

- 9:44 und 9:55: Nach dem Turmfall nennt der Satz ein Ziel **außer** Farmen, zum Beispiel den nächsten Turm oder den
  Drachen mit Team. Prüfung: darf_nicht_sagen „bis sich etwas öffnet“.
- 16:35 und 16:42: „alle tot“ bzw. „nachdem der Tower tot ist“. Die Antwort nennt ein Strukturziel.

Dazu ein **Wächter aus einer echten Partie (CLASSIC)**: Bei unklarer Lage (nicht klar überlegen) bleiben Kampfrufe
stumm. Die Stelle suchst du in 173159 und begründest sie.

## Teil C – Antworten, die die Frage beantworten

1. **WARUM ohne ausdrückliches Ziel** meint die **letzte gesprochene Ansage**, nicht den aktuellen Plan.
   - Die Antwort nennt deren Grund („Raus kam, weil Xin 90 Sekunden fehlte.“).
   - Sieht der Kern die Lage jetzt anders, sagt er das offen: „Das war zu vorsichtig: Rumble war schwächer.“
   - Dafür merkt sich jede gesprochene Ansage ihren Grund und ihre Merkmale (für 60 s).
2. **Aussagen von Carlos sind Korrekturen** (Buch 11, 5.6):
   - „Der ist jetzt bei mir oben“ setzt die Sichtung des zuletzt genannten Gegners.
   - „Alle sind tot“ ist ein Abgleich mit den Toten. Stimmt es, geht es mit Plan weiter, sonst mit ehrlicher
     Richtigstellung.
   - „Ich bin beim Drachen“ setzt den Ort.
   - Die Antwort kommt aus der korrigierten Lage.
3. **Floskeln sind verboten:** „bis sich etwas öffnet“, „Danach rechne ich neu“, „Turm ist gerade keine Option“ (ohne
   Grund). Test über alle Satzbausteine.
4. **Die Frage beantworten.** „Warum bist du dir so sicher, dass …?“ ist eine Frage nach der Gewissheit. Die Antwort
   sagt, was der Kern weiß und was nicht: „Sicher nicht: ich sehe die Grube nicht. Dein Team steht aber dort, also
   hin.“ Neue Absicht `GEWISSHEIT`.
5. **An der Grube mit Team** („was mache ich jetzt?“ um 13:13) kommt nie „Farm Top“. Dann gilt das Objective oder,
   mit Grund, dass es ohne dich läuft.

Szenarien: Die Fragen 1:22, 1:30, 4:05, 12:41, 13:13, 13:18, 16:35 und 16:42 aus 213624 bekommen die Prüfung
darf_nicht_sagen der Floskeln, dazu `muss_nennen_eins` nach Absicht.

## Teil D – Kampf-Eichung: Verdacht auf ein Fehler-Etikett

Gold zeigt verkehrt herum (AUC 0,30). Mein Verdacht ist das **Etikett**. „Gewonnen“ misst heute Kill-Gold eigener
Kills minus eigener Tode. Liegt Carlos weit vorn, sind seine Tode teuer (Kopfgeld, Shutdown) und seine Kills billig.
Dann hängt „verloren“ gerade am Gold-Vorsprung.

1. Etikett neu: **Köpfe** (eigene Kills − eigene Tode in der Episode). Bei Gleichstand gilt die Probe als offen.
   Zweites Etikett: „du hast überlebt und mindestens einer von ihnen nicht“.
2. Rechne AUC je Merkmal und Brier für beide Etiketten. Ergebnis und Fallzahlen (nur `bots = false`) kommen nach
   messungen.md.
3. Besteht die Eichung damit, gilt Buch 7, 3.3, und die Kampfrufe sprechen wieder, nach Buch 7, Kapitel 5. Die
   Überlegenheits-Regel bleibt als Untergrenze.

## Ende

1. Neue Protokolle für 213624 (mit `--fragen`), 164326 und 173159.
2. messungen.md, Abschnitt „Auftrag 004“: die Leerlauf-, Wendepunkt- und Floskel-Zahlen vorher und nachher.
3. Committen und `004_bericht.md` im Format aus `README.md` schreiben.
4. Starte den Coach nicht.
