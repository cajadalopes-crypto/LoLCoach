# Auftrag 010 – Plan nach dem Wendepunkt (Claude, Chat, 28.09.2026 15:45)

009 ist geprüft, die gefährliche Stelle ist weg. Das Hauptthema jetzt ist der Leerlauf-Befund aus 009: Nach einem
Wendepunkt (Turm, Kill, Objective vorbei) hat der Kern oft keinen Plan mit Ziel, nur `HALTEN`. Das ist genau Carlos'
Kernwunsch aus dem 27.09.: „im Mid- und Lategame gibt es eigentlich immer was zu sagen“. Daneben drei kleinere Fixes.

## 1. Plan nach dem Wendepunkt (Hauptteil)

Aus den 6 von 10 Leerlauf-Stichproben in `messungen.md` („Auftrag 009“, Nummern 1, 2, 3, 7, 9, 10): Der Kern fällt
nach einem Wendepunkt auf `HALTEN` ohne Ziel zurück, obwohl die Lage ein Ziel hergibt (Welle drücken, zu einem toten
Gegner nachziehen, Objective vorbereiten, geordnet zurückziehen).

- Baue in `kern/fuehren.py` (oder wo `HALTEN` entsteht) eine Prüfung **nach jedem Wendepunkt**: Turm gefallen, Kill
  (eigener oder gegnerischer), Objective genommen. Läuft danach `HALTEN` an, sucht der Kern einmal aktiv nach einem
  Ziel mit positivem EV aus den bestehenden Kandidaten (Welle, nächstes Objective, Rückzug mit Grund, Nachziehen bei
  Überzahl). Gibt es keinen mit positivem EV, bleibt `HALTEN` stumm wie bisher – das ist dann richtig.
- Die zehn Beispiele aus messungen.md sind der Maßstab, nicht neu erfundene Fälle. Beispiel 1 (14:00, Mid-Welle läuft
  zu Aurora, Herold in 40 s) soll etwas wie „Drück die Mid-Welle in ihren Turm, dann zum Herold“ ergeben, nicht
  „Halten“.
- **Nicht bauen:** Ein neuer Kampf-Modus oder irgendetwas, das an der Kampf-Eichung hängt (Buch 7 ist weiter nicht
  geeicht). Es geht nur um Makro-Ziele, die schon berechnet werden können.
- **Szenarien:** Alle 6 Fälle aus den Leerlauf-Stichproben als Szenario, plus 2–3 Gegenbeispiele, in denen `HALTEN`
  stumm richtig bleibt (Rückzug/Back-Ruf noch gültig, wie die Beispiele 5, 6, 8).
- **Messung:** Leerlauf ab 14:00 in allen neun Protokollen. Ziel: deutlich unter den 51–59 % aus 009. Kein festes
  Soll, aber die Richtung muss klar sichtbar sein; wenn ein Fall nicht besser wird, kurz notieren warum.

## 2. Info ohne Folgen (Regression 1 → 6)

Die Nachzählung in 009 zeigt „Info ohne Folgen“ bei 6 statt vorher 1, zum Beispiel „Gut raus.“ oder „Aurora ohne
Flash.“ ganz ohne Ort oder Konsequenz. Das hängt vermutlich mit 1. zusammen: Ein reiner Info-Satz ohne folgenden Plan
ist selbst schon ein Fall von „kein Ziel nach dem Wendepunkt“.

- Prüf zuerst, ob Punkt 1 das von selbst behebt (Info-Satz plus Zielsatz statt Info allein).
- Bleiben danach noch Fälle übrig: Ein ungefragter Info-Satz ohne jede Handlung wird entweder mit der nächsten
  Handlung zusammengelegt oder ganz gestrichen (Buch 4, Warum-Regeln: „Info ohne Folgen 0“ gilt weiter).

## 3. 23:35: Rückzugsziel auf der falschen Lane lesbar

„Zurück unter deinen inneren Mid-Turm: zwei kommen.“ war rechnerisch richtig (der Weg dorthin ist der schnellste),
gesagt aber, während du auf der Bot-Lane standst. Das liest sich wie ein Fehler.

- Liegt das errechnete Rückzugsziel auf einer anderen Lane als der Spieler gerade steht, nennt der Satz den
  Ausgangspunkt: „Von der Bot-Lane zurück zu deinem inneren Mid-Turm: zwei kommen.“
- Szenario mit dem 101426-Fall um 23:35.

## 4. Wackelnde Einschätzung bei 102112, 25:22

Die Einschätzung „ist der Mitspieler am Objective wirklich allein“ kippte 0,5 s nach der Ansage von 0,86 auf 1,0
(„zählt als mit“). Das ist eine Kante, keine falsche Entscheidung – der Split (Mitspieler zum Objective, du zum
Turm) bleibt richtig, wenn der Mitspieler wirklich allein ist.

- Glätte die Einschätzung über ein kurzes Zeitfenster (z. B. Mittel der letzten 1–2 s) statt eines einzelnen
  Schnappschusses, damit die Ansage nicht direkt an der Kippgrenze feuert.
- Unit-Test mit den zwei Schnappschüssen aus 102112 25:22.

## 5. Nur notieren: 41 % nach schnellem Lebensverlust

29:36 „Weiter auf ihren Nexus-Turm“ bei 41 % Leben, direkt nach schnellem Lebensverlust – knapp über der 40-%-Grenze
aus R1. Das ist nah an der bekannten Verzögerung bei der Leben-Zahl (008-Nebenbefund). Nichts bauen, nur in
`OFFEN.md` mit einer Zeile vermerken: Grenze eventuell mit Sicherheitsabstand oder Lebenstrend statt Schnappschuss,
sobald Buch 2/R1 noch einmal angefasst wird.

## Ende

1. Szenarien zuerst rot, dann Fixes. Voller Lauf am Ende.
2. Neue Protokolle für 101426 und die beiden anderen mit deutlichem Leerlauf-Anteil.
3. Bericht: was besser wurde, was nicht, und ob noch eine Testpartie ansteht oder ob es noch etwas zu klären gibt.
4. Committen. Starte den Coach nicht.
