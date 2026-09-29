# Auftrag 024 – Lebendige Arbeitspakete und was die Udyr-Partie zeigt (Claude, Chat, 30.09.2026 00:05)

Direkt nach 023. **Keine Testpartien, frag Carlos nie nach einer Partie, starte den Coach nicht.** Budget für
API-Nachspiele: höchstens 5 $.

Carlos hat von sich aus gespielt: `aufnahmen/2026-09-29_231200` (Riven Top gegen Udyr, Botpartie, 34 min). Der Coach
lief auf dem sauberen Stand von 022 (gestartet 23:10:54, 023 begann erst 23:20). Diese Partie wird eine neue
Testpartie. Ihre Notizen sind Pflichtenheft.

## 1. Lebendige Arbeitspakete: eigener Auftrag

Die Arbeitspakete (Carlos' Notizen 18:37 und 29:39 und seine Nachricht vom 30.09. 00:00) sind jetzt ein eigenes Buch
(`buecher/15_lebendige_arbeitspakete.md`) und ein eigener Auftrag (025). **Hier nicht bauen.** Dieser Auftrag liefert
die Grundlagen, die 025 braucht: Tod und Respawn aus der API, eine richtige Anwesenheit der Lane-Gegner und
TP-Timer.

**Events (Buch 15, Teil 0):** Die Fixes in 2 bis 4 bitte gleich als **Event-Quellen** bauen, also als klare
Funktionen, die ein Event liefern (Typ, Ort, Beteiligte, Zeit, Sicherheit). 025 hängt sie dann nur noch in
`kern/events.py` ein:
- Tod und Respawn aus `isDead` und `respawnTimer`;
- Lane-Gegner anwesend, weg oder zurück;
- Flash, TP und Quest-TP verbraucht oder wieder bereit.

## 2. Tot oder lebendig: die API statt eigener Timer (größter Faktenfehler der Partie)

- **2:57:** Der Coach sagte „Jetzt, wo Xerath tot ist“. Laut API lebte Xerath seit ~2:55 wieder.
- **7:56:** „Gragas tot“. Laut API lebte Gragas die ganze Zeit (`isDead = false`).
- 8:11 Carlos: „Mit den Todes-Timern bist du richtig von der Zeit ab.“

**Die Live-API liefert für alle zehn Spieler `isDead` und `respawnTimer`** (in der Aufnahme geprüft). Das ist die
Wahrheit, die auch der Spieler auf der Anzeigetafel sieht.

- **Fix:** Tod und Respawn überall aus `isDead`/`respawnTimer` statt aus eigener Rechnung, in Lagebild, Kern,
  Stratege und Fenstern.
- **`pruefe`:** Verwirft jeden Satz, der einen lebenden Champion „tot“ nennt oder umgekehrt, mit der Lage zur
  Sprechzeit.
- **Szenarien:** 2:57, 7:56.

## 3. Lane-Gegner „weg“, obwohl er da ist

5:56 „Udyr ist weg“. Carlos stand mit ihm auf der Lane (6:16).

- Prüf, warum. Vermutung: Das Symbol überdeckt sich auf der Minimap mit Riven. „Weg“ nur, wenn er ≥ N s nicht
  gesehen wurde **und** nicht im Kampf mit dir war (Schaden, Nähe laut Bild) **und** nicht verdeckt sein kann.
- **Szenario** 5:56.

## 4. TP der Gegner und dein Quest-TP

- **5:19:** Ein gegnerischer TP war auf der Minimap zu sehen. Der Coach soll sagen, wer TP benutzt hat, z. B.
  „Udyr TP weg“, und den Timer führen wie beim Flash. Die TP-Erkennung gibt es für das Quest-TP schon, also
  erweitern.
- **Quest-Belohnung** (unbegrenzter Teleport des Toplaners, Notiz 29:39):
  - in Lagebild und Wissensblock aufnehmen: „Du hast Quest-TP, Abklingzeit …“;
  - der Stratege plant damit, z. B. „Top-Welle crashen, dann per TP zum Drachen“.
  - Wirkung und Abklingzeit aus `wissen/` mit Stand. Nicht aus dem Gedächtnis; gibt es keinen Beleg, bitte im
    Bericht nachfragen.

## 5. Fragen in Notizen, Kaufen, Satzfehler

1. **„Notiz …“ mit Frage** (11:03 „Notiz, ich bin im Shop, was kaufe ich?“, Antwort war „Notiert.“): Enthält eine
   Notiz eine Frage, wird sie beantwortet **und** notiert.
2. **Volles Inventar mit viel Gold** (32:20, ~5000 Gold: „Nichts zu kaufen: alle sechs Plätze voll“):
   - Bauteile im Inventar zu fertigen Items verbinden (das braucht keinen Platz);
   - bei Bedarf eins verkaufen (Dorans, Stiefel ausbauen);
   - der Satz nennt das konkrete fertige Item.
   - Gehortetes Gold über 2000 in der Basis ist ein Fehler, den der Coach verhindern muss.
3. **Kaufrat auf der Lane** (3:22/3:33): „Kaufen“ nur in der Basis oder im Back-Ruf. Prüfen, woher der Satz kam.
4. **Kaputter Satz** (8:14): „Jetzt, wo Aus der Basis aufgetaucht ist: Aus der Basis: Farm Top …“. Den Satzbau mit
   „Jetzt, wo …“ reparieren und prüfen, dass nur echte Ereignisse eingesetzt werden. Unit-Test.
5. **Reset-Grund** (7:51): Sagt der Coach „kein Back“, nennt er den Grund. Hat er keinen, ist Back mit Gold für ein
   Item die Voreinstellung.

## 6. Tempo und Kosten (falls 023 das nicht schon geschafft hat)

- **Die Partie:** Median 2,4 s bis zum ganzen Satz, Carlos empfand das als langsam (6:16). Die Kosten lagen bei
  0,91 $ für 34 min, Soll ≤ 0,50 $ je 30 min (167 Haiku-Aufrufe, 480 000 Eingabe-Tokens ohne Zwischenspeicher, dazu 4
  Sonnet-Aufrufe).
- **Prüfen:** wofür Sonnet lief (Briefing?).
- **Ziel:** ≤ 1,5 s bis zum ersten Satz, ≤ 0,50 $ je 30 min.

## Ende (sparsam: 024 ist Grundlage, gemessen wird das Tor erst am Ende von 025)

1. **231200 als Testpartie aufnehmen:** Szenarien aus allen Notizen.
2. **Prüfen ohne Kritiker und ohne volles Tor:**
   - Unit-Tests;
   - betroffene Szenarien, am Ende einmal alle, parallel;
   - **ein** API-Nachspiel von 231200, um die Fixes Satz für Satz zu prüfen (tot oder lebendig, Udyr weg, TP, Kauf,
     Notiz-Fragen, Satzbau) und die Sicherheit (0 / 0 / 0).
3. **Budget für API-Nachspiele:** höchstens 1 $.
4. `024_bericht.md`, committen, Kostenstand. Starte den Coach nicht.
