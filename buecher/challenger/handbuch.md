# Challenger-Handbuch (aus den Daten, Auftrag 031)

Grundlage: 4761 High-Elo-Partien (EUW, Master bis Challenger, 16.17-16.19), 3.494.522 Entscheidungsmomente. Nur Aussagen mit n >= 200 und klarem Signal (|z| >= 3). **Beschreibend** = was in den Partien passiert (keine Ursache); **kausal geschaetzt** = doppelt robust auf zurueckgelegten Partien; **Modell** = Messung eines Modells auf der Pruefung.

## A1. Gegner-Jungler lesen

- Zuletzt vor 0-15 s gesehen: Der Gegner-Jungler ist noch auf derselben Kartenseite (oben/mid/unten) in 71 % der Faelle. _(n = 861.925; beschreibend)_  
  Kommando: „Jungler eben unten gesehen – oben hast du jetzt Luft.“
- Zuletzt vor 45-60 s gesehen: Der Gegner-Jungler ist noch auf derselben Kartenseite (oben/mid/unten) in 31 % der Faelle. _(n = 262.187; beschreibend)_  
  Kommando: „Jungler vor 50 s unten gesehen – das ist alt, rechne oben mit ihm.“
- Zuletzt vor 90-120 s gesehen: Der Gegner-Jungler ist noch auf derselben Kartenseite (oben/mid/unten) in 33 % der Faelle. _(n = 221.366; beschreibend)_  
  Kommando: „Jungler vor 50 s unten gesehen – das ist alt, rechne oben mit ihm.“
- Die Jungler-Karte trifft den Bereich des lebenden Gegner-Junglers mit ihren drei wahrscheinlichsten Bereichen in 78 % (Verteilung je Minute allein: Top-1 14 %, Modell Top-1 42 %). _(n = 1.121.045; Modell, Pruefung)_  
  Kommando: „Jungler wahrscheinlich im roten Jungle oben oder am Fluss – Ward dort, bevor du pushst.“
- Lane-Phase: Ist der Gegner-Jungler seit ueber 60 s nicht gesehen, stirbt ein Laner in den naechsten 60 s in 16 % der Faelle; wurde er eben (< 20 s) auf der anderen Kartenseite gesehen, in 17 %. Eine Sichtung auf der anderen Seite macht die Lane also NICHT sicherer - gesehen wird er in den Daten nur bei Kills, also dort, wo gekaempft wird (Carlos sieht ihn live oefter). _(n = 120.883, |z| 6; beschreibend)_  
  Kommando: „Jungler auf der anderen Seite gesehen heisst nicht sicher – Welle trotzdem nahe am Turm.“

## A2. Gefahr ausserhalb des Bildes

- Ab 25:00 allein in einer Seitenlane, drei oder mehr Gegner unbekannt: Wer dort 60 s allein weitersplittet, stirbt in 73 % der Faelle; wer die Seite verlaesst (zum Team, Back, Grube), in 23 %. _(n = 575, |z| 24; beschreibend)_  
  Kommando: „Drei fehlen – raus aus der Seitenlane, zurueck zum Team.“
- Lane-Phase mit unter 30 % Leben: Wer in der Lane bleibt, stirbt in 60 s in 11 % der Faelle; wer backt, in 2 %. _(n = 19.605, |z| 35; beschreibend)_  
  Kommando: „30 % Leben – Welle unter den Turm, dann Back.“

## A3. Lane-Druck und Lane-Gegner

- Bei 10:00 20+ CS vorn gegen den Lane-Gegner: Siegquote 61 % (Laner ohne Support). _(n = 3.658, |z| 14; beschreibend)_  
  Kommando: „20 CS vorn – dein Vorsprung ist echt, jetzt nicht verschenken.“
- Bei 10:00 20+ CS hinten gegen den Lane-Gegner: Siegquote 39 % (Laner ohne Support). _(n = 3.311, |z| 14; beschreibend)_  
  Kommando: „20 CS hinten – umspielen statt duellieren: Welle unter deinem Turm halten.“

## A4. Zurueck in die Basis

- Top: Median-Gold beim Betreten des Ladens (5:00-20:00, Tasche + gerade gekaufte Items) 866 (Mitte der Haelfte: 625-1200). _(n = 38.078; beschreibend)_  
  Kommando: „850 Gold – das ist dein Back-Moment.“
- Jungle: Median-Gold beim Betreten des Ladens (5:00-20:00, Tasche + gerade gekaufte Items) 1100 (Mitte der Haelfte: 765-1492). _(n = 33.627; beschreibend)_  
  Kommando: „1100 Gold – das ist dein Back-Moment.“
- Mid: Median-Gold beim Betreten des Ladens (5:00-20:00, Tasche + gerade gekaufte Items) 867 (Mitte der Haelfte: 650-1200). _(n = 42.566; beschreibend)_  
  Kommando: „850 Gold – das ist dein Back-Moment.“
- ADC: Median-Gold beim Betreten des Ladens (5:00-20:00, Tasche + gerade gekaufte Items) 1015 (Mitte der Haelfte: 725-1379). _(n = 37.618; beschreibend)_  
  Kommando: „1000 Gold – das ist dein Back-Moment.“
- Support: Median-Gold beim Betreten des Ladens (5:00-20:00, Tasche + gerade gekaufte Items) 601 (Mitte der Haelfte: 442-800). _(n = 43.139; beschreibend)_  
  Kommando: „600 Gold – das ist dein Back-Moment.“
- Drache, Top: In den 120 s davor ist der Spieler des verlierenden Teams in 18 % der Momente tot, beim nehmenden in 13 %. _(n = 94.520, |z| 30; beschreibend)_  
  Kommando: „Drache kommt – jetzt nichts riskieren, erst Back, dann zur Grube.“
- Drache, Jungle: In den 120 s davor ist der Spieler des verlierenden Teams in 19 % der Momente tot, beim nehmenden in 9 %. _(n = 93.573, |z| 62; beschreibend)_  
  Kommando: „Drache kommt – jetzt nichts riskieren, erst Back, dann zur Grube.“
- Drache, Mid: In den 120 s davor ist der Spieler des verlierenden Teams in 18 % der Momente tot, beim nehmenden in 12 %. _(n = 95.505, |z| 39; beschreibend)_  
  Kommando: „Drache kommt – jetzt nichts riskieren, erst Back, dann zur Grube.“
- Drache, ADC: In den 120 s davor ist der Spieler des verlierenden Teams in 18 % der Momente tot, beim nehmenden in 12 %. _(n = 94.724, |z| 41; beschreibend)_  
  Kommando: „Drache kommt – jetzt nichts riskieren, erst Back, dann zur Grube.“
- Drache, Support: In den 120 s davor ist der Spieler des verlierenden Teams in 17 % der Momente tot, beim nehmenden in 11 %. _(n = 95.601, |z| 40; beschreibend)_  
  Kommando: „Drache kommt – jetzt nichts riskieren, erst Back, dann zur Grube.“
- Baron, Top: In den 120 s davor ist der Spieler des verlierenden Teams in 27 % der Momente tot, beim nehmenden in 14 %. _(n = 28.105, |z| 38; beschreibend)_  
  Kommando: „Baron kommt – jetzt nichts riskieren, erst Back, dann zur Grube.“
- Baron, Jungle: In den 120 s davor ist der Spieler des verlierenden Teams in 30 % der Momente tot, beim nehmenden in 10 %. _(n = 27.904, |z| 60; beschreibend)_  
  Kommando: „Baron kommt – jetzt nichts riskieren, erst Back, dann zur Grube.“
- Baron, Mid: In den 120 s davor ist der Spieler des verlierenden Teams in 27 % der Momente tot, beim nehmenden in 14 %. _(n = 28.227, |z| 39; beschreibend)_  
  Kommando: „Baron kommt – jetzt nichts riskieren, erst Back, dann zur Grube.“
- Baron, ADC: In den 120 s davor ist der Spieler des verlierenden Teams in 25 % der Momente tot, beim nehmenden in 11 %. _(n = 27.972, |z| 43; beschreibend)_  
  Kommando: „Baron kommt – jetzt nichts riskieren, erst Back, dann zur Grube.“
- Baron, Support: In den 120 s davor ist der Spieler des verlierenden Teams in 26 % der Momente tot, beim nehmenden in 13 %. _(n = 28.305, |z| 41; beschreibend)_  
  Kommando: „Baron kommt – jetzt nichts riskieren, erst Back, dann zur Grube.“

## A5. TP

- TP ist aus den Minuten-Positionen nur selten zeitlich erkennbar: 6946 sichere TP-Momente gegen 710977 Momente 'TP unbekannt'. Der TP-Wert kommt deshalb in Stufe 3 aus dem Rechner, nicht aus diesen Daten. _(n = 6.946; beschreibend)_  
  Kommando: „(kein TP-Kommando aus den Daten – Stufe 3)“

## A6. Objectives

- Drache, Top: In den 120 s vor dem Monster steht das Team, das es nimmt, in 12 % der Momente an der Grube; das Team, das es verliert, in 7 %. _(n = 94.520, |z| 39; beschreibend)_  
  Kommando: „Drache in einer Minute – jetzt hin, nicht erst beim Spawn.“
- Drache, Jungle: In den 120 s vor dem Monster steht das Team, das es nimmt, in 51 % der Momente an der Grube; das Team, das es verliert, in 14 %. _(n = 93.573, |z| 186; beschreibend)_  
  Kommando: „Drache in einer Minute – jetzt hin, nicht erst beim Spawn.“
- Drache, Mid: In den 120 s vor dem Monster steht das Team, das es nimmt, in 18 % der Momente an der Grube; das Team, das es verliert, in 10 %. _(n = 95.505, |z| 54; beschreibend)_  
  Kommando: „Drache in einer Minute – jetzt hin, nicht erst beim Spawn.“
- Drache, ADC: In den 120 s vor dem Monster steht das Team, das es nimmt, in 22 % der Momente an der Grube; das Team, das es verliert, in 9 %. _(n = 94.724, |z| 78; beschreibend)_  
  Kommando: „Drache in einer Minute – jetzt hin, nicht erst beim Spawn.“
- Drache, Support: In den 120 s vor dem Monster steht das Team, das es nimmt, in 28 % der Momente an der Grube; das Team, das es verliert, in 15 %. _(n = 95.601, |z| 68; beschreibend)_  
  Kommando: „Drache in einer Minute – jetzt hin, nicht erst beim Spawn.“
- Baron, Top: In den 120 s vor dem Monster steht das Team, das es nimmt, in 31 % der Momente an der Grube; das Team, das es verliert, in 13 %. _(n = 28.105, |z| 54; beschreibend)_  
  Kommando: „Baron in einer Minute – jetzt hin, nicht erst beim Spawn.“
- Baron, Jungle: In den 120 s vor dem Monster steht das Team, das es nimmt, in 45 % der Momente an der Grube; das Team, das es verliert, in 14 %. _(n = 27.904, |z| 87; beschreibend)_  
  Kommando: „Baron in einer Minute – jetzt hin, nicht erst beim Spawn.“
- Baron, Mid: In den 120 s vor dem Monster steht das Team, das es nimmt, in 31 % der Momente an der Grube; das Team, das es verliert, in 13 %. _(n = 28.227, |z| 55; beschreibend)_  
  Kommando: „Baron in einer Minute – jetzt hin, nicht erst beim Spawn.“
- Baron, ADC: In den 120 s vor dem Monster steht das Team, das es nimmt, in 40 % der Momente an der Grube; das Team, das es verliert, in 11 %. _(n = 27.972, |z| 82; beschreibend)_  
  Kommando: „Baron in einer Minute – jetzt hin, nicht erst beim Spawn.“
- Baron, Support: In den 120 s vor dem Monster steht das Team, das es nimmt, in 37 % der Momente an der Grube; das Team, das es verliert, in 15 %. _(n = 28.305, |z| 61; beschreibend)_  
  Kommando: „Baron in einer Minute – jetzt hin, nicht erst beim Spawn.“
- Drache: frei genommen 60 %, bestritten ohne Kill 3 %, umkaempft (Kill +-30 s) 37 %. _(n = 16.967; beschreibend)_  
  Kommando: „Drache: rechne in jedem zweiten bis dritten Fall mit Kampf – vorher Leben und Ult pruefen.“
- Baron: frei genommen 53 %, bestritten ohne Kill 2 %, umkaempft (Kill +-30 s) 46 %. _(n = 5.036; beschreibend)_  
  Kommando: „Baron: rechne in jedem zweiten bis dritten Fall mit Kampf – vorher Leben und Ult pruefen.“

## A7. Cross-Map und Tausch

- Gegner nimmt einen Drachen frei: Holt das andere Team in dieser Minute mindestens einen Turm (oder zwei Platten), aendert sich sein Gold-Abstand um -25; ohne Tausch um -439. _(n = 2.322, |z| 20; beschreibend)_  
  Kommando: „Drache ist weg – dafuer jetzt Turm oben, nicht hinterherlaufen.“

## A8. Kaempfe als Makro-Entscheidung

- Nach gewonnenen Kaempfen holt das Team in den 60 s danach im Schnitt 0.60 Gebaeude, 2.56 Platten und 0.32 Monster. _(n = 18.837; beschreibend)_  
  Kommando: „Zwei tot bei ihnen – Turm oder Monster, sofort.“
- Wer nach einem Kill zwei Gegner mehr tot hat, gewinnt die naechsten 30 s mit +0.18 Kills; bei Gleichstand -0.00. _(n = 189.972, |z| 38; beschreibend)_  
  Kommando: „Zwei mehr – jetzt ist der Moment, weiterzuspielen.“

## A9. Sicht

- Top: Wards gesetzt je 30 min – Gewinner 10.6, Verlierer 10.1 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 6; beschreibend)_  
  Kommando: „Ward jetzt, bevor du weiter vorgehst.“
- ADC: Wards gesetzt je 30 min – Gewinner 9.9, Verlierer 9.3 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 8; beschreibend)_  
  Kommando: „Ward jetzt, bevor du weiter vorgehst.“
- Support: Wards gesetzt je 30 min – Gewinner 40.9, Verlierer 39.1 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 8; beschreibend)_  
  Kommando: „Ward jetzt, bevor du weiter vorgehst.“
- Top: Kontroll-Augen gesetzt je 30 min – Gewinner 1.0, Verlierer 0.8 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 6; beschreibend)_  
  Kommando: „Ward jetzt, bevor du weiter vorgehst.“
- Jungle: Kontroll-Augen gesetzt je 30 min – Gewinner 2.3, Verlierer 2.1 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 3; beschreibend)_  
  Kommando: „Ward jetzt, bevor du weiter vorgehst.“
- Mid: Kontroll-Augen gesetzt je 30 min – Gewinner 1.1, Verlierer 1.0 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 3; beschreibend)_  
  Kommando: „Ward jetzt, bevor du weiter vorgehst.“
- ADC: Kontroll-Augen gesetzt je 30 min – Gewinner 1.0, Verlierer 0.7 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 9; beschreibend)_  
  Kommando: „Ward jetzt, bevor du weiter vorgehst.“
- Support: Kontroll-Augen gesetzt je 30 min – Gewinner 7.4, Verlierer 6.3 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 10; beschreibend)_  
  Kommando: „Ward jetzt, bevor du weiter vorgehst.“
- Mid: Wards zerstoert je 30 min – Gewinner 2.9, Verlierer 2.6 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 4; beschreibend)_  
  Kommando: „Ward jetzt, bevor du weiter vorgehst.“
- ADC: Wards zerstoert je 30 min – Gewinner 4.4, Verlierer 3.8 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 8; beschreibend)_  
  Kommando: „Ward jetzt, bevor du weiter vorgehst.“
- Support: Wards zerstoert je 30 min – Gewinner 8.5, Verlierer 8.2 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 3; beschreibend)_  
  Kommando: „Ward jetzt, bevor du weiter vorgehst.“
- Top: Sichtwert je 30 min – Gewinner 27.1, Verlierer 26.0 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 5; beschreibend)_  
  Kommando: „Ward jetzt, bevor du weiter vorgehst.“
- Jungle: Sichtwert je 30 min – Gewinner 32.9, Verlierer 30.5 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 8; beschreibend)_  
  Kommando: „Ward jetzt, bevor du weiter vorgehst.“
- Mid: Sichtwert je 30 min – Gewinner 23.5, Verlierer 22.3 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 5; beschreibend)_  
  Kommando: „Ward jetzt, bevor du weiter vorgehst.“
- ADC: Sichtwert je 30 min – Gewinner 23.8, Verlierer 22.0 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 8; beschreibend)_  
  Kommando: „Ward jetzt, bevor du weiter vorgehst.“
- Support: Sichtwert je 30 min – Gewinner 94.9, Verlierer 89.5 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 12; beschreibend)_  
  Kommando: „Ward jetzt, bevor du weiter vorgehst.“

## A10. Seiten, Gruppe, Split

_Keine Aussage mit n >= 200 und klarem Signal._

## A11. Spielstand und Siegbedingung

- Baron (20-30): die Siegchance des nehmenden Teams steigt um +3.2 Punkte (Siegchance-Modell, 40 s vorher gegen 40 s nachher). _(n = 4.222, |z| 21; Modell V)_  
  Kommando: „Baron ist 3 Punkte Siegchance wert – dafuer lohnt ein Kampf.“
- Baron (ab 30:00): die Siegchance des nehmenden Teams steigt um +4.2 Punkte (Siegchance-Modell, 40 s vorher gegen 40 s nachher). _(n = 634, |z| 8; Modell V)_  
  Kommando: „Baron ist 4 Punkte Siegchance wert – dafuer lohnt ein Kampf.“
- Drache (20-30): die Siegchance des nehmenden Teams steigt um +1.4 Punkte (Siegchance-Modell, 40 s vorher gegen 40 s nachher). _(n = 4.627, |z| 9; Modell V)_  
  Kommando: „Drache bringt nur 1.4 Punkte – nehmen, wenn es ohne grosses Risiko geht.“
- Drache (vor 20:00): die Siegchance des nehmenden Teams steigt um +4.3 Punkte (Siegchance-Modell, 40 s vorher gegen 40 s nachher). _(n = 10.968, |z| 56; Modell V)_  
  Kommando: „Drache ist 4 Punkte Siegchance wert – dafuer lohnt ein Kampf.“
- Herold (vor 20:00): die Siegchance des nehmenden Teams steigt um -1.1 Punkte (Siegchance-Modell, 40 s vorher gegen 40 s nachher). _(n = 3.876, |z| 9; Modell V)_  
  Kommando: „Herold ist wenig wert (-1.1 Punkte) – dafuer nichts riskieren, der Turm danach zaehlt.“
- Bei 20:00 3000+ Item-Gold vorn: Siegquote 79 %. _(n = 8.374, |z| 30; beschreibend)_  
  Kommando: „Wir sind vorn – nichts erzwingen, Sicht und Objectives.“
- Bei 20:00 3000+ Item-Gold hinten: Siegquote 21 %. _(n = 8.279, |z| 30; beschreibend)_  
  Kommando: „Wir liegen hinten – auf Picks und Gegner-Fehler spielen, keine 50:50-Kaempfe.“
- Das Siegchance-Modell (nur Wissbares) liegt im Brier bei 0.163; der echte Gold-Abstand allein (im Spiel unsichtbar) bei 0.170. _(n = 1.121.045; Modell, Pruefung)_  
  Kommando: „Siegchance jetzt 62 % – ihr seid vorn, aber nicht sicher.“

## A12. Team und Kommunikation

- Top: 'Auf dem Weg'-Pings je 30 min – Gewinner 15.4, Verlierer 13.0 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 6; beschreibend)_  
  Kommando: „Ping Bot: Jungler fehlt.“
- Jungle: 'Auf dem Weg'-Pings je 30 min – Gewinner 38.2, Verlierer 31.9 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 8; beschreibend)_  
  Kommando: „Ping Bot: Jungler fehlt.“
- Mid: 'Auf dem Weg'-Pings je 30 min – Gewinner 20.8, Verlierer 17.3 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 7; beschreibend)_  
  Kommando: „Ping Bot: Jungler fehlt.“
- ADC: 'Auf dem Weg'-Pings je 30 min – Gewinner 18.5, Verlierer 15.0 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 7; beschreibend)_  
  Kommando: „Ping Bot: Jungler fehlt.“
- Support: 'Auf dem Weg'-Pings je 30 min – Gewinner 27.0, Verlierer 20.8 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 9; beschreibend)_  
  Kommando: „Ping Bot: Jungler fehlt.“

## A13. Kaufen (Makro-Teil)

- Top: gekaufte Kontroll-Augen je 30 min – Gewinner 1.2, Verlierer 0.9 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 5; beschreibend)_  
  Kommando: „Kontroll-Auge mitnehmen.“
- ADC: gekaufte Kontroll-Augen je 30 min – Gewinner 1.2, Verlierer 0.8 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 9; beschreibend)_  
  Kommando: „Kontroll-Auge mitnehmen.“
- Support: gekaufte Kontroll-Augen je 30 min – Gewinner 12.0, Verlierer 11.1 (gepaart je Partie; beschreibend, nicht Ursache). _(n = 2.170, |z| 6; beschreibend)_  
  Kommando: „Kontroll-Auge mitnehmen.“

## Q. Aus dem Aktionswert (doppelt robust, je Aktionspaar der staerkste Fund)

- Gegner-Jungler vor < 15 s gesehen: Objective:Baron schlaegt Lane: +1.5 Punkte Siegchance in 120 s (doppelt robust, Pruefung, 4326 Partien). _(n = 93.897, |z| 10; kausal geschaetzt (DR))_  
  Kommando: „Baron statt Lane.“
- mind. 2 von uns tot: Back schlaegt Warten: +3.0 Punkte Siegchance in 120 s (doppelt robust, Pruefung, 4002 Partien). _(n = 35.450, |z| 8; kausal geschaetzt (DR))_  
  Kommando: „Back statt Warten.“
- Team 3000+ Items vorn: Gruppe schlaegt Lane: +2.2 Punkte Siegchance in 120 s (doppelt robust, Pruefung, 3560 Partien). _(n = 53.020, |z| 8; kausal geschaetzt (DR))_  
  Kommando: „Gruppe statt Lane.“
- Herold steht: Objective:Drache schlaegt Lane: +1.5 Punkte Siegchance in 120 s (doppelt robust, Pruefung, 3777 Partien). _(n = 23.909, |z| 5; kausal geschaetzt (DR))_  
  Kommando: „Drache statt Lane.“

_Verworfen (n < 200 oder kein klares Signal): 27 Aussagen._
