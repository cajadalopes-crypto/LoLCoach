# Abdeckung der 111 Makro-Entscheidungen (Auftrag 032)

Erzeugt von `werkzeuge/challenger/abdeckung.py` aus dem Register (`lolcoach/makro/entscheidungen/`) und den Tests (`tests/makro/`). Die Haekchen sind gemessen, nicht behauptet.

| | erkannt | gerechnet | gesagt | getestet |
|---|---:|---:|---:|---:|
| **Stand** | 105/111 (+6 fuer 033) | **111/111** | **111/111** | **111/111** |

**Tor 3a** (gerechnet, gesagt, getestet je 111/111): **ERREICHT**. 'Erkannt' gilt fuer alle ausser den mit 033 markierten (Wahrnehmung fehlt).

## Wahrnehmung fehlt -> Auftrag 033

- **busch_sicht** (Busch vor dir ohne Sicht - Minimap-Nebel zu grob, nicht gebaut): S11
- **ward_weg** (Minimap: eigener Ward weg - wem er gehoert und 'weg' 6-14 % falsch (Icon/Text darueber)): S12
- **gegner_recall** (Recall des Lane-Gegners - 18 von 36 erkannten bestaetigt (Items/Basis)): B5
- **tp_stand_gegner** (TP-Stand der Gegner - 10 Spruenge in 10 Partien erkannt, Treffer nicht messbar): T9
- **kopfgeld** (Objective-Kopfgeld - Goldrand an Tuermen lesbar, Bedeutung nicht belegt, API ohne Ereignis): O12
- **mitspieler_zauber** (Blitz der Mitspieler - HUD zeigt ihn nicht, Chat: 0 von 50 Blitz-Pings): P2

## Alle 111

Spalten: Nr, Entscheidung, Grundlage (Buch 17), erkannt, gerechnet, gesagt, getestet, fehlende Wahrnehmung, Kommando der feuernden Testlage.

| Nr | Entscheidung | Grundl. | erkannt | gerechnet | gesagt | getestet | Wahrnehmung fehlt | Kommando (Testlage) |
|---|---|---|:-:|:-:|:-:|:-:|---|---|
| S1 | Erster Trinket: welcher Busch | D,R | ✔ | ✔ | ✔ | ✔ | – | Trinket in den Fluss-Busch: er hat auf der anderen Seite begonnen und kommt ueber den Fluss. |
| S2 | Trinket halten statt sofort setzen | D,R | ✔ | ✔ | ✔ | ✔ | – | Halte den Trinket bis 2:15 min Spielzeit – vorher kommt der erste Gank praktisch nie (unter 5 % der Faelle). Danach setz ihn in den Busch, aus dem er kommt. |
| S3 | Welle schieben, um warden zu koennen | M,Re | ✔ | ✔ | ✔ | ✔ | – | Drueck die Welle in den naechsten 20 s rein: sonst kostet dich der Ward Farm. Danach Ward in den Tri-Busch. |
| S4 | Tiefer Ward zum Jungler-Tracken | D,M,R | ✔ | ✔ | ✔ | ✔ | – | 5 s rein, Ward an ihren Krug-Eingang: Aatrox ist tot und ihr Jungler ist weit weg. Sofort raus. |
| S5 | Umweg fuer Info | D,Re | ✔ | ✔ | ✔ | ✔ | – | Lauf durch ihren Raptoren-Eingang, 3 s Umweg: dann weisst du, ob ihr Jungler oben ist. |
| S6 | Kontroll-Auge: kaufen und wohin | D,R | ✔ | ✔ | ✔ | ✔ | – | Kontroll-Auge mitnehmen: in den Tri-Busch: von dort kommen die Ganks. |
| S7 | Linse statt gelbem Trinket | D,R | ✔ | ✔ | ✔ | ✔ | – | Tausch beim Back auf Linse: Herold kommt, du raeumst die Grube. |
| S8 | Sicht vor dem Objective | D,R | ✔ | ✔ | ✔ | ✔ | – | Larven in 70 s: Ward den Eingang auf ihrer Seite – wer vorher Sicht hat, bekommt das Monster. Danach Welle. |
| S9 | Raeumen vor dem Objective | R | ✔ | ✔ | ✔ | ✔ | – | Linse jetzt an der Drachengrube: ihr Ward muss weg, bevor ihr startet. |
| S10 | Flanken-Ward vor dem Split | D,R | ✔ | ✔ | ✔ | ✔ | – | Bevor du drueckst: Ward an ihren Jungle-Eingang zu deiner Seite – sonst stirbst du ohne Warnung (allein splitten ohne Info endet oft tot). |
| S11 | Kein Face-Check | D,M | 033 | ✔ | ✔ | ✔ | busch_sicht | Nicht in den Busch: 2 fehlen. Erst Ward oder Linse. |
| S12 | Sicht abgelaufen oder zerstoert | M,R | 033 | ✔ | ✔ | ✔ | ward_weg | Dein Ward im Tri-Busch ist weg: neu setzen – ohne ihn siehst du keinen Gank. Erst dann wieder vorgehen. |
| S13 | Trinket-Ladungen nicht verfallen lassen | M,R | ✔ | ✔ | ✔ | ✔ | – | Einen Ward jetzt in den Fluss: beide Ladungen sind voll, sonst verfaellt eine. |
| S14 | Ward fuer einen Mitspieler oder ein Objective | M,R | ✔ | ✔ | ✔ | ✔ | – | Setz den Ward an die Larven: Vi geht gleich hin und hat dort keine Sicht. |
| J1 | Startseite ableiten | D | ✔ | ✔ | ✔ | ✔ | – | Er ist oben gesehen worden: Start auf der oberen Seite, erster Gank eher Top. |
| J2 | Gank-Fenster vorwarnen | D,M | ✔ | ✔ | ✔ | ✔ | – | Gank-Fenster jetzt: Welle zurueckziehen lassen – ihr Jungler ist unbekannt und deine Welle steht vorn. Erst wieder nach vorn, wenn er gesehen wird. |
| J3 | Freifenster nutzen | D,Re | ✔ | ✔ | ✔ | ✔ | – | Er ist Bot: 43 s Ruhe – so lange braucht er zu dir. Danach Welle rein, Platte holen. |
| J4 | Jungler unbekannt und du weit vorn | D,M | ✔ | ✔ | ✔ | ✔ | – | Zurueck zur Mitte der Lane: ihr Jungler ist seit 50 s weg und du stehst tief. |
| J5 | Mehrere fehlen (MIA) | D,M | ✔ | ✔ | ✔ | ✔ | – | Zurueck zum Turm: LeeSin und Brand fehlen seit mindestens 15 s. Danach Bot anpingen. |
| J6 | Lane-Gegner fehlt (Roam oder Back) | M,D | ✔ | ✔ | ✔ | ✔ | – | Aatrox ist weg: Ping Mid – er roamt oder backt. Danach Welle crashen und die Platte holen. |
| J7 | Gegner-TP genutzt | M,R | ✔ | ✔ | ✔ | ✔ | – | Aatrox hat TP benutzt: fuer 4:38 min kein Flank von ihm. Jetzt kannst du auf der anderen Seite helfen. |
| J8 | Gegner-Flash weg | M | ✔ | ✔ | ✔ | ✔ | – | Brand ohne Flash fuer 3:20 min: Ping – Kill-Fenster fuer euren Jungler. |
| J9 | Globale oder lange Ults der Gegner | R,M | ✔ | ✔ | ✔ | ✔ | – | Nicht tief ohne Sicht: Pantheon ist Level 7: seine weite Ult kann dich erreichen. |
| J10 | Gegner-Spike | D,M | ✔ | ✔ | ✔ | ✔ | – | Aatrox hat seinen Spike: Level oder Item eben fertig. Jetzt keinen Seitenkampf allein. |
| J11 | Fruehes Invade | D,R | ✔ | ✔ | ✔ | ✔ | – | Bleib am Busch bei eurem Buff: 5 von ihnen fehlen: sie koennten invaden. Bis euer Jungler ihn hat. |
| J12 | Konter-Gank | Re,D | ✔ | ✔ | ✔ | ✔ | – | Bleib: Vi ist bei dir, ihr Jungler kommt – 2 gegen 2. |
| J13 | Krabbler | D,Re | ✔ | ✔ | ✔ | ✔ | – | Krabbler oben: Welle rein, dann hin (13 s) – mit dir gewinnt Vi den Fluss. |
| J14 | Dive-Gefahr | D,Re | ✔ | ✔ | ✔ | ✔ | – | Raus hinter den Turm: 2 kommen und deine Welle ist weg. Nicht ins Tor stellen. |
| W1 | Freeze oder Push | M,R,D | ✔ | ✔ | ✔ | ✔ | – | Freeze an deinem Turm: nur letzte Treffer – er muss nach vorn, um zu farmen, Vi kommt in 16 s. |
| W2 | Langsam aufbauen, dann crashen vor dem Back | M,Re | ✔ | ✔ | ✔ | ✔ | – | 2 Wellen aufbauen, mit der Kanone crashen: dann verlierst du beim Back nichts. Danach Back. |
| W3 | Crash -> Back | M,D | ✔ | ✔ | ✔ | ✔ | – | Welle ist drin: jetzt Back – 1000 Gold. Danach Kauf-Kette. |
| W4 | Crash -> Fenster nutzen | M,Re | ✔ | ✔ | ✔ | ✔ | – | Deine Welle prallt in 25 s zurueck: 25 s fuer Ward oder Mid. |
| W5 | Warten auf die zurueckprallende Welle | M,Re | ✔ | ✔ | ✔ | ✔ | – | Warte 10 s am Turm: die Welle kommt zu dir. Erst dann TP. |
| W6 | Welle vor dem Objective | D,M | ✔ | ✔ | ✔ | ✔ | – | Drache in 80 s: Welle jetzt rein – damit du frei bist. |
| W7 | Welle vor TP oder Roam crashen | M,Re | ✔ | ✔ | ✔ | ✔ | – | Erst crashen (6 s), dann Roam: sonst frisst ihr Turm deine Welle (etwa 43 Gold). |
| W8 | Welle retten oder Objective | Re,D | ✔ | ✔ | ✔ | ✔ | – | Lass die Welle: der Drache ist mehr wert: 145 Gold gegen 3.0 Punkte Siegchance. |
| W9 | Nicht zu tief druecken | D,M | ✔ | ✔ | ✔ | ✔ | – | Stopp vor ihrem Turm: ihr Jungler ist unbekannt und du willst nicht backen. |
| W10 | Nach Kill oder Tod des Lane-Gegners | D,M | ✔ | ✔ | ✔ | ✔ | – | Er ist 25 s tot: Welle crashen, 2 Platten – du hast 57 s, bis er zurueck ist. Danach Back. |
| W11 | Seitenwelle holen (Mitte und Spaet) | D,M | ✔ | ✔ | ✔ | ✔ | – | Bot-Welle holen, bis vor ihren Turm: sie laeuft auf euren Turm. |
| W12 | Grosse Welle stapeln fuer Turm oder Dive | M,Re | ✔ | ✔ | ✔ | ✔ | – | Zwei Wellen stapeln: ihr Turm ist schwach und Aatrox ist weg. Danach mit Vi auf den Turm. |
| W13 | Welle aufgeben | Re,D | ✔ | ✔ | ✔ | ✔ | – | Lass die Welle und geh: der Drache ist in 15 s. |
| W14 | Wellen der anderen Lanes fuer Prio | M | ✔ | ✔ | ✔ | ✔ | – | Kein Drache jetzt: die Bot-Welle laeuft auf euren Turm: euer Bot kann nicht weg. Erst wenn Bot die Welle hat. |
| B1 | Wann Back | D,M | ✔ | ✔ | ✔ | ✔ | – | Back jetzt: Welle drin, 1000 Gold fuer dein naechstes Bauteil. |
| B2 | Back im Takt des Objectives | D | ✔ | ✔ | ✔ | ✔ | – | Back jetzt: dann bist du 57 s vor dem Drachen voll da. Direkt zur Grube. |
| B3 | Back verschieben | D,M | ✔ | ✔ | ✔ | ✔ | – | Noch nicht back: Aatrox ist 20 s tot. Erst Welle und Platten, dann Back. |
| B4 | Back wegen Leben oder Mana | D | ✔ | ✔ | ✔ | ✔ | – | Back: mit 20 % Leben und Gegnern in der Naehe ist jeder Moment ein Risiko. |
| B5 | Back zusammen mit dem Lane-Gegner | M,R | 033 | ✔ | ✔ | ✔ | gegner_recall | Du auch, sofort: Aatrox backt: dann verliert keiner eine Welle. |
| B6 | Rueckweg: zu Fuss oder TP | Re,D | ✔ | ✔ | ✔ | ✔ | – | Zu Fuss zurueck (32 s), halte den TP: der Drache kommt in 2:00 min. |
| B7 | Kauf-Kette | D,R | ✔ | ✔ | ✔ | ✔ | – | Kauf dein naechstes Bauteil und Kontroll-Auge: du hast 1200 Gold. Danach zurueck in die Lane. |
| B8 | Nach Respawn: Kauf und Ziel | D,Re | ✔ | ✔ | ✔ | ✔ | – | Du lebst in 8 s: Kauf-Kette – dann direkt in die Lane. |
| B9 | Sonderregeln je Champion | R | ✔ | ✔ | ✔ | ✔ | – | Kauf direkt in der Lane: Ornn braucht dafuer keinen Back. |
| T1 | TP zurueck in die Lane oder aufheben | Re,D | ✔ | ✔ | ✔ | ✔ | – | TP zurueck: mehrere Wellen laufen auf deinen Turm (etwa 76 Gold) und kein Monster steht an. TP ist in 4:48 min wieder da. |
| T2 | TP zu Kampf oder Objective auf der anderen Seite | Re,D | ✔ | ✔ | ✔ | ✔ | – | Welle rein (6 s), dann TP zum Kampf: 4 gegen 3, du bist in 12 s da, rechtzeitig da. |
| T3 | TP halten fuer das Objective | Re,D | ✔ | ✔ | ✔ | ✔ | – | Nicht TP fuer die Lane: du brauchst ihn in 1:30 min am Drachen (Abklingzeit 4:48 min). |
| T4 | TP-Flanke in der Spaetphase | Re,R | ✔ | ✔ | ✔ | ✔ | – | Wenn sie anfangen: TP auf den Ward Flanke hinter Baron – von hinten trifft deine Ankunft ihre Hinterleute. |
| T5 | TP zur Verteidigung | Re | ✔ | ✔ | ✔ | ✔ | – | TP auf den Mid-Turm: sonst faellt er in 15 s. |
| T6 | Konter-TP | M,Re | ✔ | ✔ | ✔ | ✔ | – | Du auch: TP dorthin – Aatrox TPt zum Kampf, sonst 3 gegen 4. |
| T7 | TP-Ziel waehlen | Re,M | ✔ | ✔ | ✔ | ✔ | – | TP auf den Vasallen hinten, nicht auf den Ward im Fluss: dort steht Leona. |
| T8 | Nicht TPen | Re,D | ✔ | ✔ | ✔ | ✔ | – | Kein TP: zu spaet: der Kampf ist vorbei, bevor du ankommst. Danach TP fuer den naechsten Kampf halten. |
| T9 | TP-Stand beider Tops | M | 033 | ✔ | ✔ | ✔ | tp_stand_gegner | Du hast TP, er nicht: noch 3:20 min: jetzt ist dein Fenster fuer ein Play auf der anderen Seite. |
| R1 | Roam Mid | Re,D | ✔ | ✔ | ✔ | ✔ | – | Ueber den Fluss Mid (25 s): Welle drin, Brand ohne Flash. |
| R2 | Zum Fluss oder Krabbler fuer den eigenen Jungler | Re,D | ✔ | ✔ | ✔ | ✔ | – | Zum Fluss (13 s): Vi ist dort und braucht dich. Dann zurueck an die Welle. |
| R3 | Zu den Larven oder zum Herold | D,Re | ✔ | ✔ | ✔ | ✔ | – | An den Eingang der Larven (13 s): Larven in 30 s. |
| R4 | Zum Drachen zu Fuss | Re,D | ✔ | ✔ | ✔ | ✔ | – | Zum Drachen, los: zu Fuss schaffst du es in 10 s, er startet in 45 s. |
| R5 | Roam abbrechen | M,Re | ✔ | ✔ | ✔ | ✔ | – | Abbrechen: Brand ist nicht mehr da. Danach zurueck an deine Welle. |
| R6 | Rotation nach Turmverlust | D | ✔ | ✔ | ✔ | ✔ | – | Dein Top-Turm ist weg: Mid-Welle mit Sylas – in der Seitenlane druecken sie jetzt bis Turm 2. |
| R7 | Weg waehlen | D,Re | ✔ | ✔ | ✔ | ✔ | – | Durch euren Jungle, nicht durch den Fluss: 2 Gegner fehlen. |
| R8 | Roam-Kosten gegen Nutzen | Re,D | ✔ | ✔ | ✔ | ✔ | – | Nicht roamen: du verlierst etwa 119 Gold an Wellen, der Gewinn ist kleiner. |
| R9 | Mit dem Jungler invaden | D,Re | ✔ | ✔ | ✔ | ✔ | – | Mit Vi in ihren oberen Jungle: ihr Jungler ist auf der anderen Seite. Danach Krug und Raptoren, dann zurueck. |
| R10 | Gegner-Camp nehmen | R,M | ✔ | ✔ | ✔ | ✔ | – | Ihre Krug: 10 s, dann zurueck – die Welle ist drin und ihr Jungler ist weit weg. |
| O1 | Drache: bestreiten, geben oder tauschen | D,Re | ✔ | ✔ | ✔ | ✔ | – | Drache nur mit Sicht und allen dort: ihr seid 4 gegen 5. Sonst geben und tauschen. |
| O2 | Larven | D,Re | ✔ | ✔ | ✔ | ✔ | – | Larven mit Vi: du hast Prio. |
| O3 | Herold: nehmen und wo einsetzen | D,R | ✔ | ✔ | ✔ | ✔ | – | Herold in Mid einsetzen: der Turm dort hat nur noch 1 Platte - der Herold allein ist wenig wert, der Turm danach viel. |
| O4 | Baron: Bedingungen | D | ✔ | ✔ | ✔ | ✔ | – | Baron jetzt: 2 von ihnen mindestens 30 s tot. Danach Seitenwellen und Tuerme. |
| O5 | Baron abbrechen | Re,M | ✔ | ✔ | ✔ | ✔ | – | Baron abbrechen: 4 kommen. Danach raus Richtung eurer Seite. |
| O6 | Elder oder Seele: alles darauf | D,R | ✔ | ✔ | ✔ | ✔ | – | Elder in 30 s: alles dahin – das entscheidet die Partie. |
| O7 | Setup-Kette 90/60/30 s | D,R | ✔ | ✔ | ✔ | ✔ | – | Drache in 75 s: Welle rein – so bist du rechtzeitig und voll da. In 15 s Back. |
| O8 | Steal-Gefahr | M,R | ✔ | ✔ | ✔ | ✔ | – | Nicht unter 1500 kloppen ohne Vis Smite: ihr Jungler lauert. |
| O9 | Nach dem Objective: naechstes Ziel | D | ✔ | ✔ | ✔ | ✔ | – | Drache drin: jetzt auf ihren naechsten Turm – bis einer von ihnen zurueck ist. |
| O10 | Cross-Map-Tausch | D | ✔ | ✔ | ✔ | ✔ | – | Sie sind am Drachen: Turm auf der anderen Seite – ein Tausch rettet das meiste (ohne Tausch verliert ihr im Schnitt 439 Gold, mit 25). |
| O11 | Aufgeben und sicher zurueck | D | ✔ | ✔ | ✔ | ✔ | – | Zu spaet, nicht reinlaufen: 1 gegen 4. Danach Welle holen, naechstes Monster. |
| O12 | Objective-Kopfgeld | D,M | 033 | ✔ | ✔ | ✔ | kopfgeld | Ihr habt Kopfgeld auf dem Drachen: das ist euer Weg zurueck (bis 1000 Gold extra). |
| K1 | Kampf annehmen oder ablehnen | D | ✔ | ✔ | ✔ | ✔ | – | Nicht kaempfen: 1 gegen 2. |
| K2 | Warten auf den Mitspieler | Re | ✔ | ✔ | ✔ | ✔ | – | Warte 11 s auf Vi: dann 2 gegen 2. |
| K3 | Zum Kampf laufen oder nicht | Re | ✔ | ✔ | ✔ | ✔ | – | Nicht hinlaufen: du bist in 37 s da, der Kampf dauert 10 s. Danach nimm stattdessen Welle oder Turm. |
| K4 | Nach dem Sieg: umwandeln | D | ✔ | ✔ | ✔ | ✔ | – | 2 tot: Baron jetzt – ein gewonnener Kampf ohne Gebaeude oder Monster ist verschenkt. Danach Reset. |
| K5 | Nach der Niederlage: retten | D,M | ✔ | ✔ | ✔ | ✔ | – | Nicht nachlaufen: Welle am naechsten Turm halten – ihr habt den Kampf verloren, sie sind in Ueberzahl. Warten, bis eure Toten zurueck sind. |
| K6 | Pick-Chance melden | M,D | ✔ | ✔ | ✔ | ✔ | – | Brand allein: Ping und mit Vi hin – du bist in 16 s da. |
| K7 | Nicht allein sterben | D | ✔ | ✔ | ✔ | ✔ | – | Nicht allein tiefer als die Flussmitte: 53 s Todeszeit und 3 fehlen. |
| M1 | Lane-Zuordnung nach Plattenende oder Tuermen | D | ✔ | ✔ | ✔ | ✔ | – | Plattenende: du bleibst Top-Seite – die Seitenwelle dort gehoert dir, der ADC geht Mid. |
| M2 | Split: ob, welche Seite, wie tief | D | ✔ | ✔ | ✔ | ✔ | – | Split bis zu ihrem Turm, nicht weiter: sie muessen dir jemanden schicken. Sofort weg, wenn drei fehlen. |
| M3 | Split verlassen | D,Re | ✔ | ✔ | ✔ | ✔ | – | Split abbrechen, lauf jetzt: Baron in 40 s. |
| M4 | Gruppe Mid | D | ✔ | ✔ | ✔ | ✔ | – | Geh Mid zur Gruppe: 4 von euch stehen dort, allein bist du das leichtere Ziel. |
| M5 | 1-3-1 oder 1-4 | D,R | ✔ | ✔ | ✔ | ✔ | – | 1-3-1, du Top: du bist staerker als dein Gegner und hast Sicht an der Flanke. |
| M6 | Seitenwellen vor Baron oder Drache | D,M | ✔ | ✔ | ✔ | ✔ | – | Top und Bot-Welle druecken: dann Baron: sie muessen die Wellen holen. |
| M7 | Inhibitor-Druck | D,M | ✔ | ✔ | ✔ | ✔ | – | Ihr Bot-Inhibitor ist weg: die andere Seite halten – die Super-Vasallen machen dort Druck fuer euch. |
| M8 | Spiel beenden | D,Re | ✔ | ✔ | ✔ | ✔ | – | 3 tot: Mid-Inhibitor jetzt – ihr seid 27 s vor dem ersten Respawn fertig. |
| M9 | Basis verteidigen | D,M | ✔ | ✔ | ✔ | ✔ | – | Nicht raus: Wellen im Tor clearen – sie haben den Baron. Danach auf ihren Fehler warten. |
| M10 | Todes-Kosten beachten | D | ✔ | ✔ | ✔ | ✔ | – | Sicher spielen: ein Tod jetzt kostet 53 s und Baron. |
| V1 | Siegbedingung ansagen und wechseln | D | ✔ | ✔ | ✔ | ✔ | – | Nichts erzwingen vor Minute 25: ihr skaliert besser. |
| V2 | Vorsprung umwandeln | D | ✔ | ✔ | ✔ | ✔ | – | Objectives, keine Kaempfe ohne Grund: ihr steht bei 72 % Siegchance. |
| V3 | Rueckstand spielen | D | ✔ | ✔ | ✔ | ✔ | – | Wellen halten, Sicht, auf ihren Fehler warten: ihr steht bei 25 % Siegchance. Danach keine 50:50-Kaempfe. |
| V4 | Eigenes Spike-Fenster | D | ✔ | ✔ | ✔ | ✔ | – | In den naechsten 2 min ein Monster erzwingen: euer Spike ist jetzt. |
| V5 | Gegner-Spike abwarten | D | ✔ | ✔ | ✔ | ✔ | – | Nicht kaempfen: Wellen und Sicht – ihr Spike ist jetzt. |
| P1 | Ping-Vorschlag | M,D | ✔ | ✔ | ✔ | ✔ | – | Ping Bot: Jungler auf dem Weg – LeeSin ist eben auf ihrer Seite aufgetaucht. |
| P2 | Mitspieler Go/No-Go | M | 033 | ✔ | ✔ | ✔ | mitspieler_zauber | Drache erst nach dem Back von Varus: Varus 30 % Leben. |
| P3 | Hilfe fuer einen Mitspieler | Re,D | ✔ | ✔ | ✔ | ✔ | – | Geh: Vi kaempft, du bist in 4 s da: 2 gegen 1. |
| P4 | Mitspieler tot | D | ✔ | ✔ | ✔ | ✔ | – | Kein Objective, sicher halten: 2 von euch sind tot. In 20 s seid ihr wieder komplett. |
| Z1 | Warte X s auf Welle, Respawn, TP oder Sicht | Re,D | ✔ | ✔ | ✔ | ✔ | – | Warte 8 s: dann ist Varus zurueck, erst dann Drache. |
| Z2 | Fenster ansagen | Re,D | ✔ | ✔ | ✔ | ✔ | – | Du hast 62 s: Aatrox ist tot. Danach Welle und Platten, dann Back. |
| Z3 | Nichts tun ist richtig (Klarheit unklar) | D | ✔ | ✔ | ✔ | ✔ | – | Bleib an der Welle: keine Option ist klar besser, das tun High-Elo-Spieler hier am haeufigsten. Bis ihr mehr wisst. |
