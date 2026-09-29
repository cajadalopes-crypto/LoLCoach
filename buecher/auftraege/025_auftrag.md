# Auftrag 025 – Buch 15: Events und lebendige Arbeitspakete, Stufe 1 (Claude, Chat, 30.09.2026 00:20)

Lies `buecher/15_lebendige_arbeitspakete.md` ganz. Er kommt direkt nach 024. **Keine Testpartien, frag Carlos nie nach
einer Partie, starte den Coach nicht.** Budget für API-Nachspiele: höchstens 4 $.

Das ist der wichtigste Umbau seit Buch 14. Er macht aus Einzelsätzen einen überwachten Strom von Anweisungen.

## 0. Events (Buch 15, Teil 0): die Grundlage für alles Weitere

Carlos (30.09. 00:06): Der Jungler-Kampf war nur ein Beispiel. Es geht um **alle denkbaren Events**, um Erkennung,
Erahnung und Abwägung, und das fast in Echtzeit.

1. **`lolcoach/kern/events.py`:** Events aus API, Minimap, HUD und den Unterschieden zwischen zwei Takten. Die
   Gruppen aus Teil 0.1, jedes Event mit Typ, Ort, Beteiligten, Zeit und Sicherheit.
   - Der Katalog ist offen. Neue Typen kommen als kleine Erkennungs-Funktion dazu.
   - Stufe 1: alle Gruppen aus 0.1 mit den im Code schon verfügbaren Daten.
2. **Erahnung (Teil 0.2),** in Stufe 1 mindestens: Kampf bahnt sich an (Objective oder Konvergenz), Gank droht, Lane-
   Gegner backt gleich, Gegner kommt aus dem Respawn zurück. Jede Erahnung mit p und ETA, **an den Aufnahmen
   geeicht**. Erahnungen unter 60 % Eintritt bei p ≥ 0,6 bleiben still.
3. **Abwägung (Teil 0.3):**
   - Je teilnehmbarem Event ein Kandidat mit Wert, Machbarkeit und „warum nicht“ für auffällige, nicht gewählte
     Events.
   - **Szenarien mit mehreren Events gleichzeitig,** Carlos' Beispiel:
     - Top-Welle pushen;
     - beim Herold-Kampf helfen (wenn Leben und Weg passen);
     - lauern, weil gleich ein Kampf kommt, statt zu backen.

     Das beste Play wird gesagt, dazu ein „warum nicht“ zum sichtbaren anderen Event.

## 1. Die vier Uhren (Buch 15, Teil 2)

- **Bauen:** `lolcoach/kern/uhren.py` mit Gefahr-Uhr, Wellen-Uhr, Objective-Uhr und Ressourcen-Uhr, in jedem Takt.
- **Wege auf der Karte** statt Luftlinie. Die Wegzeiten (Brunnen → Lanes, Lanes → Objectives) aus den Aufnahmen
  messen.
- **Wissen:** Wellenzeiten und Recall-Kanal in `wissen/` mit Quelle und Stand.
- **Unit-Tests** mit konstruierten Lagen.
- **Probe an Aufnahmen:**
  - Stimmt `T_gefahr`? Vergleich mit dem tatsächlichen Eintreffen der Gegner.
  - Stimmt die Back-Frist? Kam man nach einem Back zur berechneten Zeit ohne Vasallenverlust an?

## 2. Paket-Rahmen (Buch 15, Teil 1, 3 und 4)

- `lolcoach/kern/pakete.py`: Paket mit Typ, Ziel, Wert, Budget oder Frist, Erledigt-Prüfung und Abbruch-Prüfung
  (allgemein nach Teil 4, dazu je Typ).
- **Höchstens ein aktives Paket**, dazu ein „danach“.
- Das Plan-Objekt aus 021 geht darin auf.
- **Typen in Stufe 1:** TURM/PLATTEN, WELLE, BACK, HILFE, ROTATION, OBJECTIVE, WARTEN. Die übrigen folgen in Stufe 2.
- **Übergänge sprechen** (Teil 1):
  - Kern-Sätze für Countdown, Abbruch und Erledigt sofort, ≤ 8 Wörter;
  - Start und Planwechsel formuliert Claude mit Grund; die Vorlage des Kerns ist der Ersatz.
  - Kein Übergang geht verloren. Die Sprechsperren gelten für Füllsätze, **nicht** für Paket-Übergänge.

## 3. Chancen-Scanner (Buch 15, Teil 5)

- Ereignisse erzeugen Kandidaten mit Wert. Gewechselt wird mit Hysterese. Der Satz lautet „Planwechsel: …, weil ….
  Danach …“.
- Der Chancen-Scanner ist die Umsetzung der Event-Abwägung (Teil 0.3). **Beispielfall:** Nach einem Back unterwegs
  zur Lane kämpft der eigene Jungler in ≤ 8 s Entfernung. Dann entscheidet der Rechner (nicht „klar hinten“) über
  HILFE mit Grund. Das kommt als Szenario aus einer echten Aufnahme; wenn keine passt, als konstruierte Lage.
- **Mindestens 15 Szenarien aus echten Aufnahmen,** in denen zwei oder mehr teilnehmbare Events gleichzeitig
  auftreten. Das Soll-Play legt dort ein blinder Challenger-Kritiker fest.

## 4. Messen (Buch 15, Teil 7) auf allen Testpartien inkl. 231200

- Paket-Abdeckung, Abbruch-Reaktion, Budget-Treue, genutzte Chancen, Back-Pünktlichkeit.
- Event-Abdeckung, Erahnung (Eintrittsquote), Abwägung (blinder Kritiker) nach Buch 15, Teil 7.
- Soll-Liste und Freigabe-Tor mit dem stabilen Verfahren aus 023.
- **Budget-Treue ist Sicherheit:** Ein „N s sicher“, nach dem vor Ablauf ein Gegner in Reichweite kam, ist ein Fehler.
  Hat er zu einem Tod geführt, ist er gefährlich. Das Soll für „gefährlich“ ist 0.

## Sparsam arbeiten (Carlos: keine Zeit, kein Volumen, kein Geld vergeuden)

- **Beim Bauen:**
  - nur Unit-Tests, betroffene Szenarien und **automatische** Maße: Event-Abdeckung, Abbruch-Reaktion,
    Budget-Treue, Back-Pünktlichkeit, Paket-Abdeckung;
  - Nachspiele mit Stub oder Antwort-Zwischenspeicher, wo es geht.
- **Kritiker** (Soll-Liste mit drei Kritikern, Abwägung, Szenarien mit mehreren Events): **nur einmal am Ende**,
  alle parallel.
- **Nachbessern:** höchstens zwei Runden. Die erste stützt sich auf die automatischen Maße, die zweite nur, wenn die
  Kritiker eine klare, behebbare Lücke zeigen. Danach Bericht, auch wenn das Tor nicht erreicht ist.
- **Ist das Budget erreicht:** auf das Abo ausweichen (langsamer, aber ohne Kosten). Im Bericht steht, ob Carlos
  nachladen sollte.

## Ende

1. Unit-Tests und Szenarien zuerst rot. Schnelle Prüfung.
2. `025_bericht.md` beginnt mit „TOR ERREICHT“ oder „TOR NICHT ERREICHT“, danach alle Maße aus Teil 4 und zehn
   Beispiel-Pakete aus Nachspielen mit ihrem ganzen Lebenslauf (Start, Meilensteine, Ende).
3. Committen. Starte den Coach nicht.
