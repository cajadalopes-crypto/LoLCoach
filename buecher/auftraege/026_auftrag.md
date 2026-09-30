# Auftrag 026 – Buch 15, Stufe 1 fertig machen (Claude, Chat, 30.09.2026 07:50)

Grundlage ist `025_bericht.md` (TOR NICHT ERREICHT). **Keine Testpartien, frag Carlos nie nach einer Partie, starte den
Coach nicht.**

Gebaut wird nur, was die **automatischen** Maße aus 025 verfehlen. Die kosten nichts und laufen in 45 s
(`werkzeuge/pakete_messen.py`). Während des Bauens werden nur sie gemessen. Kritiker und API-Nachspiel gibt es **einmal
am Ende**. API-Budget: höchstens 3,50 $, danach das Abo.

## 1. Back nach der Back-Frist (Back-Pünktlichkeit 58 % → ≥ 80 %)

- **Aufgabe:** Die Wellen-Uhr rechnet die Frist schon, der Kern nutzt sie aber noch nicht.
- **BACK-Paket aus der Frist:**
  - rechtzeitig vorher ansagen: „In 10 s Welle rein, dann Back: pünktlich zur Kanone um 9:30“;
  - „Back jetzt“ zur Frist;
  - mit Kette (Kauf, Rückweg über TP oder Quest-TP, wenn bereit).
- **Messen:** Jeden verpassten Fall aus `pakete_messen.py` einzeln begründen.

## 2. Abbruch-Reaktion (82 % → ≥ 95 %)

- **Fehlende Gründe ergänzen:**
  - „Partner in anderem Kampf“;
  - „Überzahl aus der Gefahr-Uhr“ (auch Unsichtbare, die ankommen können).
- **Jeden verpassten oder zu späten Abbruch** (> 2 s) einzeln zuordnen: fehlender Grund, Sprechplan oder
  Erkennung. Dann beheben.

## 3. Budget-Treue (Fehler 13 % → ≤ 5 %, gefährlich bleibt 0)

- **Jeden Fehlerfall** („N s sicher“, aber ein Gegner kam früher in Reichweite) einzeln ansehen. War er unsichtbar zu
  optimistisch? Weg oder Tempo falsch? Flash nicht eingerechnet? Respawn falsch?
- **Weg-Lücken** (Bot, Mid-blau, Lane → Grube fehlen in den Aufnahmen): Die Karte ist punktsymmetrisch. Also aus den
  gemessenen Wegen spiegeln (Top-blau ↔ Bot-rot usw.) und in `wissen/wege.toml` als „gespiegelt“ kennzeichnen.
- **Lieber zu vorsichtig:** Die Marge darf wachsen, wenn die Fehlerquote anders nicht sinkt. Der Preis ist
  „Paket-Abdeckung“, die höchstens auf 85 % fallen darf.

## 4. Pakete ansagen (angesagt 55 %)

- **Befund:** 94 % der Zeit gibt es ein aktives Paket, angesagt wurden aber nur 55 % davon.
- **Regel:** Jeder Paket-Start wird gesagt, spätestens 2 s nach Beginn: kurz vom Kern oder formuliert von Claude.
- **Ausnahme:** Ein Paket, das nur das vorige fortsetzt (gleiches Ziel).

## 5. Eine Stimme (Widersprüche 1–7 → ≤ 1)

- **„Warum nicht“ und „X kämpft: nicht hin“:** Diese Sätze des Kerns kennen den aktiven Plan von Claude und
  widersprechen ihm nie. Soll der Plan kippen, geht das nur über das Paket (Planwechsel mit „Jetzt, wo …“).
- **Jeden Widerspruch** aus den 025-Protokollen zuordnen und schließen (z. B. 120049 24:08/24:26).

## 6. Event-Abdeckung (59 % → ≥ 85 %) und Chancen (56 % → ≥ 70 %)

- **Liste der verpassten Events** aus `pakete_messen.py`, nach Typ gezählt.
- Die **häufigsten fünf Typen** zuerst schließen, jeweils mit Szenario aus einer echten Aufnahme.
- **Chancen:** Nach dem HILFE-Scanner kommen auch diese Chancen:
  - Gegner tot oder im Back → Platten;
  - Jungler weit weg gesehen → freie Seite;
  - Flash weg mit Kill-Check → Druck;
  - Objective offen mit Prio.

## 7. Messung fair machen

Den Kritikern in die Anweisung schreiben: **Übergänge eines Pakets** sind **keine Füllsätze**, wenn sie eine neue
Info oder Handlung enthalten. Dazu zählen Countdown, Abbruch mit Grund, „Kampf vorbei → nächstes Ziel“ und „warum
nicht“ mit Grund. Nur leere Bestätigungen zählen als Füllsatz.

## 8. Gank-Erahnung (trifft 8 %, still)

Nur wenn Zeit bleibt: eine neue Regel aus Jungler-Startseite, Clear-Zeit und letzter Sichtung, an den Aufnahmen
geeicht. Sonst bleibt sie still. Nicht erzwingen.

## Ende

1. Nach jeder Änderung `pakete_messen.py` (automatisch, gratis).
2. **Einmal am Ende:** ein API-Nachspiel aller 8 Testpartien und die Kritiker (3 je Partie, Mehrheit), parallel.
3. `026_bericht.md` beginnt mit „TOR ERREICHT“ oder „TOR NICHT ERREICHT“, dazu die Tabelle aus 025 mit Spalte
   „vorher / nachher“ und Kosten. Committen. Starte den Coach nicht.
