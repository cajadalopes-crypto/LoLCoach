# Auftrag 012 – Wellen-Endlosschleife, ignorierte Fragen, Timer-Fehler (Claude, Chat, 28.09.2026 20:15)

Carlos hat eine 31-min-Botpartie gespielt (`aufnahmen/2026-09-28_192113`, Riven gegen Teemo, Win). Drei klare Fehler,
kein Meinungsstreit. Das ist jetzt Priorität vor allem anderen.

## 1. Wellen-Endlosschleife

Von 133 Ansagen erwähnen 30 „Top-Welle". Ab 19:40 sagt der Coach sechsmal hintereinander „Drück/Farm die Top-Welle",
obwohl Carlos ihm jedes Mal widerspricht: die Welle steht längst leer an ihrem Nexus, kein Vasall mehr da (19:40,
19:48, 20:05, 20:19, 20:30, 20:47, 23:45 in `aufnahmen/2026-09-28_192113_bericht.md`).

- Finde in `karte.welle_druecken` / `Kern._makro_ziele` (Auftrag 010), warum das Ziel weiter kommt, wenn die eigene
  Welle 0 Vasallen hat oder schon an oder in ihrem Turm/Nexus steht. Vermutung: der Wellenstand wird beim Auslösen
  nicht frisch genug gegen `welle.py` geprüft, oder die Bedingung „≥ 3 eigene Vasallen, die zu ihnen laufen" greift
  nicht, wenn die Welle schon drin ist statt unterwegs.
- Bot-Partien pushen viel schneller als echte Gegner (Bots clearen kaum) – das ist vermutlich nie in einer echten
  Aufnahme so weit gekommen. Nimm `2026-09-28_192113` als Testfall genau für diesen Fall: leere, tief gepushte Welle.
- Wenn keine eigene Welle mehr etwas bringt, muss `_makro_ziele` das nächste Ziel mit EV suchen (Objective, andere
  Lane, Gruppe) statt stumm zu bleiben oder die tote Welle zu wiederholen.
- **Szenario** aus 192113 (19:40–20:47): darf „Top-Welle" nicht mehr sagen, während die Welle leer an ihrem Turm
  steht.

## 2. Echte Fragen werden zu „Notiert"

Fast jede Frage von Carlos in 192113 endet entweder in einer Wiederholung des letzten Satzes oder in „Notiert." ohne
Inhalt, auch wenn eine klare Frage drinsteckt, zum Beispiel:
- 14:31 „Was mache ich, wenn der Turm down ist, als Nächstes?" → Wiederholung des Turm-Rufs, keine Antwort.
- 8:04/8:17 „Kannst du auch den Jungle coachen?" → Kartenlage statt einer Antwort auf die Frage.
- 21:11 „Ich soll also zur Top-Lane, um den Bot-Drachen zu erzwingen?" → „Notiert."

**Vermutung:** Die Absichtserkennung (`fragen.py`, Buch 11) fällt auf `NOTIZ` zurück, sobald ein Satz lang ist, Wut
oder mehrere Gedanken enthält, oder Formulierungen nutzt, die nicht exakt zu den bekannten Mustern (JETZT, WARUM,
SOLL_ICH, KLAEREN …) passen.

- Geh jede Frage aus 192113 einzeln durch (`_notizen.md` und die vollen Fragen im Kern-Protokoll, nicht nur die
  kurzen Notizen). Ordne jeder eine Absicht zu, die eigentlich passt.
- Baue die Erkennung so um, dass sie die eigentliche Frage aus einem langen, wütenden Satz zieht, statt beim ersten
  Nicht-Erkennen auf `NOTIZ` zu gehen. Ein Satz mit Fluch UND Frage ist trotzdem eine Frage.
- `NOTIZ` bleibt nur für Sätze ohne erkennbare Frage (reine Beschwerde, reines Feedback).
- **Szenarien:** jede Frage aus 192113 mit einer inhaltlich richtigen Antwort, nicht „Notiert.".

## 2b. Nicht nur dieser einen Partie hinterherbauen

Bau nicht nur exakt diese 20 Fragen aus 192113 stur nach. Nimm sie als Beispiele, um die Absichtserkennung generell
robuster zu machen, und lauf danach die bestehenden Fragen-Szenarien aus den anderen acht Partien noch einmal
dagegen, damit nichts kaputtgeht.

## 3. Timer-Fehler

Bei 5:03 sagt der Coach „Drache in 30 Sekunden", das Spiel zeigte 20. Das ist ein klarer 10-Sekunden-Fehler.

- Finde die Quelle: Wird der Timer beim Formulieren des Satzes berechnet statt beim tatsächlichen Aussprechen? Killian
  braucht teils über eine Sekunde bis zum ersten Ton (siehe `stimme.py`), aber 10 Sekunden Differenz ist mehr als
  reine Sprechlatenz.
- Unit-Test: ein Objective-Timer-Satz muss zur Sprechzeit stimmen, nicht zur Berechnungszeit.

## 4. Nur prüfen: Cassiopeia „aus dem Nebel"

Bei 22:31 sagt der Coach „Cassiopeia kam aus dem Nebel, niemand hatte sie gesehen", Carlos widerspricht: er habe sie
eine Minute lang gesehen, wie sie ihn pokt. Prüf anhand der Minimap-Bilder in `2026-09-28_192113_bilder/` um
21:30–22:31, ob Cassiopeia durchgehend erkannt wurde oder ob die Verfolgung sie zwischenzeitlich verloren hat. Nur
Befund, kein Fix, außer die Ursache ist offensichtlich und klein.

## Ende

1. Szenarien zuerst rot, dann Fixes. Vollständiger Lauf über alle Protokolle am Ende, damit nichts kaputtgeht.
2. Neues Protokoll für 192113 (mit `--fragen`, falls das für Botpartien geht, sonst ohne).
3. Bericht: für jede der sechs Wellen-Wiederholungen und jede „Notiert"-Antwort aus 192113, was jetzt stattdessen
   käme.
4. Committen. Starte den Coach nicht.
