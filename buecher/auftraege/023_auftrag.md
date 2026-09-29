# Auftrag 023 – Stabile Messung, eine Stimme, Pflicht-Infos, Tempo (Claude, Chat, 29.09.2026 23:10)

Direkt nach 022. **Keine Testpartien, frag Carlos nie nach einer Partie, starte den Coach nicht.** Budget für
API-Nachspiele: höchstens 5 $. Die Sparregeln aus 021 gelten.

Grundlage ist `021_bericht.md`, TOR NICHT ERREICHT. Gebaut wird nur, was diese Lücken schließt, in dieser Reihenfolge.

## 1. Messung stabil machen (zuerst, sonst sehen wir keinen Fortschritt)

1. **Soll-Listen einfrieren:** Für alle 7 Partien (4 bekannte, 3 neue) die bestehenden Soll-Listen einmal bereinigen
   und dann **nicht mehr neu erzeugen**.
   - Raus kommen Punkte, die den harten Regeln widersprechen (Trade oder All-in ohne Kill-Check, Level-Vergleich mit
     All-in) oder die der Coach nicht sehen kann.
   - Jede Streichung mit Grund in `messungen.md`.
2. **Urteile per Mehrheit:** Jede Minute wird von **drei** frischen Kritikern beurteilt, gezählt wird die Mehrheit.
   Die Übereinstimmung der Kritiker kommt in den Bericht.
   - Wo sich zwei nicht einig sind, liest ein vierter nur diese Minute.
3. **Vorher-Wert neu messen:** Den Stand nach 021 einmal mit dem neuen Verfahren messen. Das ist der ehrliche
   Ausgangswert.

## 2. Pflicht-Infos zuverlässig (Soll ≥ 95 %, bisher Flash 88–89, Jungler 84–89, Lane-Gegner weg 43–58 %)

- Jeden verpassten Fall einzeln ansehen: Wurde er nicht erkannt, verdrängt (Sprechplan, Sperre), oder war er falsch
  definiert?
- **Pflicht-Infos haben Vorrang:** Sie sind kurz (≤ 5 Wörter) und dürfen einen Plan-Satz unterbrechen oder direkt
  danach kommen. Eine Sperre darf sie nie ganz verschlucken, höchstens um ≤ 3 s verschieben.
- **„Lane-Gegner weg“:** Die Definition gegen die Aufnahmen prüfen (Back, Roam, Tod, zu lange ohne Sicht) und die
  Fälle zählen, die ein Coach sagen würde.
- **Rückschritte aus 021 zuerst:** 192113 19:11 (Teemos Flash nicht gesagt), 133448 1:47–3:13 (Stille).

## 3. Eine Stimme (Widersprüche ≤ 1 je Partie, bisher 1–7)

- Jeden Widerspruch aus den 021-Protokollen einzeln zuordnen: Kern-Warnung, Plan-Satz, Antwort auf eine Frage,
  Anlass. Welche zwei widersprachen sich, und warum?
- **Regel:** Jeder Satz mit Handlung läuft über den **einen** aktiven Plan, auch Antworten auf Fragen.
  - Eine Antwort bestätigt den Plan oder ändert ihn ausdrücklich („Jetzt, wo …“).
  - Macht eine Warnung den Plan unmöglich, **ersetzt** sie ihn (der Plan wird neu gesetzt). Es gibt keine zweite
    Stimme daneben.
- **Doppelte Anlässe binnen 10 s** werden zusammengefasst, nicht nacheinander gesprochen.

## 4. Tempo (ganzer Satz ≤ 2 s Median, bisher 2,3–2,5)

- Der Wissensblock (~5000 Tokens) nur für Plan-Wechsel und Fragen. Häufige kurze Anlässe (Lane, Info-Folgen) bekommen
  einen kurzen Prompt.
- Den Zwischenspeicher-Treffer je Aufruf messen und sicherstellen.
- Bis zum ersten gesprochenen Satz messen, nicht nur bis zum ganzen.

## 5. Tor neu messen (mit dem stabilen Verfahren)

Das Tor aus 021 bleibt, gemessen auf beiden Mengen. Es wird höchstens zwei Runden nachgebessert, nur mit der
bekannten Menge.

Der Bericht beginnt mit „**TOR ERREICHT**“ oder „**TOR NICHT ERREICHT**“. Darunter stehen für jede Größe drei
Werte: der Wert nach 021 im alten Verfahren, der Wert nach 021 im neuen Verfahren und der Wert nach 023.

## 6. Aufnahmen kleiner (Entscheidung zu 022: ja, aber ohne Risiko)

Je Partie bleiben ~46 MB, davon 34 MB die Aufnahme (`.jsonl.gz`). Als xz wären es laut 022 ~0,5 MB.

- **Live bleibt gzip:** Beim Schreiben während des Spiels ändert sich nichts, also keine zusätzliche CPU-Last im
  Spiel.
- **Umwandeln:** `aufraeumen.py` wandelt nach der Partie alle Aufnahmen **außer den letzten drei** in `.jsonl.xz` um
  (`lzma` aus der Standardbibliothek). Das gilt auch für die Testpartien, nachdem die Leser umgestellt sind.
- **Eine Lesefunktion für alle Werkzeuge**, die beide Formate öffnet (gz und xz). Alle Stellen, die Aufnahmen lesen,
  gehen darüber (suchen mit `grep -rn "jsonl.gz"`).
- **Vorher prüfen:** An zwei Aufnahmen umwandeln. Nachspiel und Szenarien müssen dasselbe Ergebnis liefern wie vorher,
  Satz für Satz.
- **Im Bericht:** Größe des Projektordners vorher und nachher, MB je Partie.

## Ende

`023_bericht.md`, committen, Kostenstand. Starte den Coach nicht.
