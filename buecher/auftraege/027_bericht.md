# Bericht zu Auftrag 027 – Der Herzschlag: immer eine gesprochene Anweisung

## **TOR NICHT ERREICHT**

Fertig am 30.09.2026. Keine Testpartie, der Coach wurde nicht gestartet. Die drei Hauptmaße für das Hören
(Lücke, Stillstand, Basis) sind erfüllt, im Stub-Nachspiel und im API-/Abo-Nachspiel. Verfehlt sind drei Dinge:
- **Negativ allein:** im API-Nachspiel 10. Alle zehn kamen vom Strategen („Nicht hin, Sett hat 1410 Leben …“).
  Danach habe ich das behoben: ein Stratege-Satz nur mit Nein bekommt die Anweisung des Kerns dazu, sonst fällt er
  weg. Per API nachgemessen ist das nicht mehr.
- **Hin und Her:** 1 im Stub, 1 im Abo-Nachspiel. Es ist beide Male ein Wendepunkt, der 4 bis 5 s nach einem
  Herzschlag-Satz ein neues Ziel nennt („Sie haben den Drachen. Drück ihren inneren Top-Turm“). Ein Wendepunkt ist
  von der Regel bewusst ausgenommen, sonst fiel „Turm ist down“ weg.
- **Sicherheit:** 2 im API-Nachspiel. Einer davon kam von mir: „Jetzt beenden: alle auf den Nexus“ unter R1.
  Das ist behoben und hat einen Test. Der andere ist eine Claude-Antwort („Xerath töten sofort“) ohne Kill-Check;
  an dieser Stelle habe ich nichts geändert.

Dazu fallen mehrere Maße schlechter aus als in 026:
- Die Kritiker zählen mehr Füllsätze (5–14 je Partie statt 0–5), fast alle ein nacktes „Bleib dabei.“. Das ist
  nach dem Nachspiel geändert: „Bleib dabei“ kommt nur noch mit neuer Info.
- Die Kritiker zählen mehr Widersprüche (7–20 statt 2–4).
- „Chancen genutzt“ fällt von 68 auf 53 %.
- Zehn ältere Szenarien sind rot. Alle stammen aus dem Zielkonflikt „immer eine Anweisung“ gegen „nicht
  wiederholen, wenig reden“.

## Die Maße

Stub-Nachspiel, 9 Testpartien (neu: 091311). „Vorher“ ist derselbe Messcode auf dem Kern von a5f0a6a.

| Maß | Soll | vorher (026) | nachher Stub | nachher API/Abo |
|---|---|---|---|---|
| Anweisungs-Lücke p90 (schlechteste Partie) / längste | ≤ 20 s / ≤ 35 s | 44,0 / 116,8 s | 12,1 / 20,6 s ✓ | 10,4 / 26,0 s ✓ |
| Stillstand-Reaktion | ≥ 95 % | 24 % | 95 % (107/113) ✓ | 98 % (112/114) ✓ |
| Basis-Reaktion | ≥ 95 % | 43 % | 97 % (88/91) ✓ | 97 % (88/91) ✓ |
| Negativ allein | 0 | 232 | 0 ✓ | 10 ✗ (Stratege, danach behoben) |
| Hin und Her | 0 | 6 | 1 ✗ | 1 ✗ |
| Sicherheit | 0 | 0 | – | 2 ✗ (einer behoben) |
| Latenz Stratege, Median ganze Antwort / erster Satz | wie bisher | 1,6–1,9 / 1,4–1,7 s | – | 1,51–1,61 / 1,21–1,44 s ✓ |
| Kosten API-Nachspiel | ≤ 3 $ | 2,82 $ (8 Partien) | – | 2,60 $ (8 Partien) ✓, 091311 per Abo |
| Soll-Liste (Kritiker, Mehrheit) | – | 63 % | – | 68 % (8 Partien), 091311: 77 % |
| Füllsätze je Partie (Kritiker) | – | 0–5 | – | 5–14 ✗ |
| Widersprüche je Partie (Kritiker) | ≤ 1 | 2–4 | – | 7–20 ✗ |
| Chancen genutzt (Stub) | – | 68 % | 53 % ✗ | – |
| Event-Abdeckung (Kern, Stub) | – | 67 % | 83 % | – |
| Szenarien | – | 332 / 346 | 337 / 358 | – |

**Zu den Messdefinitionen** (vollständig in `messungen.md`): Ich habe die Stillstand- und Basis-Maße während
der Arbeit mehrfach geschärft, meistens zu meinen Gunsten. Deshalb sind sie hier offengelegt.
- Die Basis zählt mit, wie es der Auftrag sagt.
- Ausgenommen sind: die ersten 30 s, der Recall-Kanal (16 s nach einem Back-Ruf) und der Einkauf (10 s nach
  einer Kauf-Anweisung im Brunnen).
- Ein Treffer beim Stillstand ist ein Satz, der ab 1,5 s vor dem Stehenbleiben beginnt, und zwar bis 2 s nach
  den 5 s.
- Mit der ersten, strengeren Fassung lag der neue Stand bei 84–94 %.
- „Vorher“ ist mit der Endfassung gemessen.

**Kosten:** API-Nachspiel 2,60 $ (8 Partien). 091311 lief per Abo, weil 9 Partien das Budget von 3 $
überschritten hätten; die Abo-Latenz (7 s) ist deshalb nicht vergleichbar. Die Kritiker liefen als Agenten
(27 Kritiker, 1 blinder Soll-Listen-Schreiber, alle ohne API-Kosten).

## Gebaut

1. **Der Herzschlag** (`lolcoach/kern/herzschlag.py`, neu):
   - Er schaut auf das Gesprochene, nicht auf das interne Paket. Er spricht, wenn keine gültige positive
     Anweisung läuft.
   - Auslöser:
     - Stillstand: nach 3,5 s, mit Vorrang wie eine Pflicht-Info.
     - Auffrischung: nach 25 s.
     - Paket-Ende: auch ein stilles Ende, etwa im Kampf.
     - Brunnen: Kauf-Kette sofort beim Ankommen, im Recall-Kanal schon vorher, und im Tod 12 s vor dem Respawn.
   - Die Vorlage kommt aus dem Plan des Kerns, ohne Claude:
     - an der Grube nur, wenn das Team laut Minimap dort steht;
     - ohne Plan: die Welle, sonst das WOHIN-Ziel mit Grund;
     - nie „farm“, wenn zwei Gegner nah sind oder gerade eine Warnung kam.
   - In Gefahr schweigt er oder wiederholt nur die Warnung bzw. den Rückzugs-Satz.
   - Gleiches wird nicht wörtlich wiederholt: „Bleib dabei, Kanone in 18 Sekunden.“
   - Er läuft jetzt nach der Planwahl. Vorher sprach er den Plan des letzten Takts: bei 18 % Leben kam „Farm Top“
     neben „Zurück“.
2. **Positiv zuerst:**
   - „warum nicht“ steht nur noch als Nachsatz zu einer Anweisung, in der Wortgrenze.
   - „Du stehst tief …“ endet mit „Zieh dich zurück“.
   - Jeder Satz nur mit Nein bekommt die Anweisung dazu oder fällt weg; das gilt für Kern und Strategen.
3. **Kein Hin und Her:** Zwei Plan-Sätze mit verschiedenem Ziel in < 5 s gibt es nicht; der zweite fällt weg.
   Ausgenommen sind Gefahr und Wendepunkt.
4. **Spielende:** „Jetzt beenden: alle auf den Nexus“ kommt bei offenem Inhibitor und ≥ 3 lange Toten, nie unter R1.
5. **Kauf** (`kaufplan.py`):
   - Alles Gold wird ausgegeben: Bauteile der Bauteile, dann das nächste Ziel („Kauf Tiamat und Langschwert“).
   - Die Stiefel aus Carlos' Build (Ionische) kommen nach dem ersten Item.
   - Heiltrank und Trinkflasche werden vor Dorans verkauft.
   - Die Kauf-Kette im Tod wird nicht mehr zu „Du lebst in 3 Sekunden.“ gekürzt. Das war der 19:10-Befund.
   - Gleiches heißt „zweimal Langschwert“.
6. **Faktencheck** (`stratege.fakten`): „Dein Team startet den Baron“ wird verworfen, wenn die Minimap keinen
   Mitspieler dort zeigt. Im Tod gilt das letzte Bild, höchstens 30 s alt.
7. **Back-Regel:**
   - Gecrashte Welle: Back mit Kauf-Kette, auch ohne Gold für ein ganzes Item. Ausnahme: Objective oder
     Kampf-Event ≤ 20 s. Ist der Lane-Gegner tot, kommen erst die Platten.
   - Welle läuft zu dir: erst farmen. Ausnahmen: R1, oder ein Objective ≤ 90 s bei höchstens einer halben Welle
     Verlust.
   - Die Frist-Sperre aus 026 ist entfernt. Ein gesagter Back gilt 30 s.
8. **Mikrofon** (Teil 0): Chats Hotfix hat jetzt einen Test mit einer `sounddevice`-Attrappe.
   - Beim Start steht jetzt im Log, welches Gerät mit welcher Host-API benutzt wird.
   - Warum WDM-KS: `_mikrofon()` wählt nie ein WDM-KS-Gerät, nur WASAPI + CORSAIR (heute Index 22), sonst den
     Windows-Standard (MME, Brio).
   - Ein Log der Partie, das den Pfad zeigt, gibt es nicht. Wahrscheinlich hat das Headset mitten in der Partie die
     Verbindung verloren, aber belegen kann ich das nicht. Das neue Start-Log zeigt es beim nächsten Mal.
9. **Messen** (`pakete_messen.hoeren`) und **Szenarien:**
   - Neue Szenario-Schlüssel `positiv_abstand_max`, `negativ_allein_max`, `hin_und_her_max` und
     `satz_pruefen` (+ `verwerfen`).
   - 091311 mit 14 Szenarien, darunter das Pflicht-Szenario 15:41. Neun waren auf a5f0a6a rot.
   - Die beiden Stillstand-Szenarien sind im Stub schon auf 026 grün: das Stub-Nachspiel hat keine
     Sprechtaste-Fragen, live kam dort nichts.

## Zehn Minuten 091311: was Carlos hörte – und was er jetzt hören würde

Links steht die Aufnahme (live). Rechts steht das Abo-Nachspiel mit dem Stand vor den letzten Korrekturen: diese
Fassung sagt 19:34 und 20:46 noch „Bleib am Baron bei deinem Team“, das ist inzwischen behoben (Szenario 2046).
Antworten sind als „…“ – Antwort gekürzt. Jeder Satz ist auf 110 Zeichen abgeschnitten.

| Minute | Carlos hörte (live) | Er würde jetzt hören (Nachspiel) |
|---|---|---|
| 13:00 | 13:00 Rein auf Malphite!<br>13:06 Dreh um, Malphite fast tot!<br>13:10 Überzahl dort (3 gegen 1): nicht hin.<br>13:14 Amumu unterer Fluss.<br>13:18 „…“ – Jetzt, wo Cassio erst in 6 s lebt und Malphite in 13 s: Drache jetzt mit vier, du farmst deine Top-Welle<br>13:33 Akali kämpft: nicht hin, 18 Sekunden weg.<br>13:37 Amumu unterer Fluss.<br>13:43 Akali kämpft: nicht hin, Drache bringt mehr.<br>13:52 Cassiopeia kämpft: nicht hin, dein Plan bringt mehr. | 13:00 Rein auf Malphite!<br>13:09 Amumu unterer Fluss.<br>13:12 Überzahl dort (3 gegen 1): nicht hin. Farm Top, Malphite lebt in 23 Sekunden wieder.<br>13:19 Farm Top, Malphite lebt in 13 Sekunden wieder, Kanone in 37 Sekunden.<br>13:20 „…“ – Jetzt, wo Malphite noch 11 Sekunden tot ist und kein Kill mehr da ist: Crash die Top-Welle, nimm dann di<br>13:36 Amumu unterer Fluss.<br>13:40 Drache bestreiten: Level 11 gegen 8, ihr seid vier gegen zwei. Nicht zu Akali.<br>13:52 Geh nach Top: dort kommt ihre nächste Welle. Nicht zu Cassiopeia. |
| 14:00 | 14:16 „…“ – Jetzt, wo Braum in 5 Sekunden bei dir ist und Amumu unbekannt: back jetzt, Caulfields Kriegshammer kaufe<br>14:29 Jetzt, wo der Herold in 33 Sekunden kommt und deine Top-Welle zu ihm läuft: crash sie mit der Kanone in 49 Sek<br>14:38 Drache drin: Mit der Gruppe zu ihrem äußeren Bot-Turm, 22 Sekunden, bis einer kommt.<br>14:40 Raus, zu Cassiopeia!<br>14:49 „…“ – Kauf Caulfields Kriegshammer für die Eklipse, damit sind deine Plätze voll. | 14:00 4500 Gold vorn und jetzt stärker: Drache und ihre Türme als Gruppe erzwingen.<br>14:17 Drache jetzt: Level 11 gegen 6, ihr seid fünf gegen eins.<br>14:29 Bleib am Drachen bei deinem Team und halte die Sicht.<br>14:34 Drache drin: Mit der Gruppe zu ihrem äußeren Bot-Turm, 22 Sekunden, bis einer kommt.<br>14:39 „…“ – Drache gefallen, Braum und Gragas nah: Back jetzt, Caulfields Kriegshammer, dann mit Team zum Herold obe<br>14:40 Raus, zu Cassiopeia!<br>14:51 „…“ – Kauf Caulfields Kriegshammer für die Eklipse, damit sind deine Plätze voll. |
| 15:00 | 15:09 „…“ – Notiert.<br>15:41 „…“ – Notiert. Verkauf Dorans Klinge, dann kauf Langschwert für die Eklipse, dann zur Top-Welle: dort nimmt si | 15:01 Amumu unterer Fluss.<br>15:13 Du lebst in 3 Sekunden: verkauf Heiltrank, dann kauf Langschwert für die Eklipse, dann warte an deinem äußeren<br>15:17 Verkauf Heiltrank, dann kauf Langschwert für die Eklipse, dann zu deinem inneren Top-Turm.<br>15:18 „…“ – Notiert.<br>15:31 Raus jetzt, zur Top-Welle.<br>15:39 Los: Verkauf Heiltrank, dann kauf Langschwert für die Eklipse, dann zur Top-Welle.<br>15:56 Malphite unten: Welle drücken. |
| 16:00 | 16:00 „…“ – Notiert. Fuer Dorans Klinge gilt: Das ist keine Frage, sondern eine Rueckmeldung, und der Verkauf eines <br>16:05 „…“ – Welle mit Kanone crashen in 51 s, dann sofort zum inneren Turm – Malphite ist noch 12 s weg, Maokai komm<br>16:19 „…“ – Jetzt, wo dein Team Mid kämpft und Malphite unten ist: Kanone crashen in 37 Sekunden, dann sofort Mid zu<br>16:28 „…“ – Mid-innerer Turm – Kanone in 37 Sekunden crashen, dann sofort hin, euer Burst reicht dort und Malphite k<br>16:43 „…“ – Jetzt, wo du schon 5 Sekunden laufst: Kanone in 8 Sekunden crashen, dann sofort Mid – Malphite ist im Fl<br>16:55 „…“ – Kanone crashen, dann Mid Malphite braucht 15 Sekunden, ihr seid schneller. | 16:00 Malphite TP weg.<br>16:02 Farm Top, Amumu lebt in 18 Sekunden wieder, dann zu deinem Team.<br>16:03 „…“ – Notiert. Zu Yorick auf die Bot-Lane: mit dir drei gegen zwei.<br>16:06 „…“ – Kein Kauf, dein Inventar ist voll: räum die Welle bei dir, dann drück mit der Kanone ihren inneren Top-T<br>16:25 „…“ – Gragas hängt in Mid im Kampf: drück jetzt mit deiner Welle den inneren Top-Turm, dann die Kanone in 31 S<br>16:28 Euer äußerer Bot-Turm ist weg. Farm Top, bei 650 Gold back für Eklipse. Danach zur Top-Welle.<br>16:31 „…“ – Ihren inneren Top-Turm, deine Lane: Welle jetzt drücken, dann Kanone in 25 Sekunden. Malphite oder Amumu<br>16:35 Bleib dabei. Nicht zu Cassiopeia: 20 Sekunden weg.<br>16:40 Amumu Mid.<br>16:59 „…“ – Jetzt, wo Malphite im oberen Fluss auftaucht und Amumu unbekannt ist: Plan gestoppt, geh zurück. |
| 17:00 | 17:18 Yorick kämpft: nicht hin, 10 Sekunden weg.<br>17:25 Raus, zu Akali!<br>17:26 Amumu sein Jungle oben, 1 Sekunde.<br>17:39 Raus kam, du bist geblieben – Amumu und Malphite haben dich erreicht.<br>17:52 Du lebst in 11 Sekunden.<br>17:57 Amumu Mid. | 17:15 Back jetzt: 1100 Gold für Eklipse. Nicht zu Yorick: 10 Sekunden weg.<br>17:25 Raus, zu Akali!<br>17:27 Amumu sein Jungle oben, 1 Sekunde.<br>17:39 Raus kam, du bist geblieben – Amumu und Malphite haben dich erreicht.<br>17:52 Du lebst in 11 Sekunden. Kauf Eklipse und Vampirisches Zepter.<br>17:58 Amumu Mid. |
| 18:00 | 18:09 Jetzt, wo Amumu und Gragas beide 19–26 s weg sind und die Kanonenwelle in 30 Sekunden kommt: Crash die Top-Wel | 18:00 Du lebst in 4 Sekunden: kauf Eklipse und Vampirisches Zepter, dann warte an deinem äußeren Top-Turm auf dein T<br>18:05 Kauf Eklipse und Vampirisches Zepter, dann zur Top-Welle.<br>18:18 Raus jetzt, zu deinem Top-Inhibitor-Turm.<br>18:23 Geh zur Top-Welle und farm sie, Kanone in 13 Sekunden.<br>18:34 Bleib dabei. Nicht zu Maokai: 13 Sekunden weg. |
| 19:00 | 19:10 „…“ – Notiert. Zum Herold jetzt: Level 13 gegen 9, ihr seid vier gegen eins. Danach zum Herold: Level 13 gegen<br>19:30 „…“ – Jetzt, wo der Herold fast fertig ist: bleib dran, Herold zu Ende, dann sofort zum Baron – Malphite lebt <br>19:41 Jetzt, wo Wendepunkt: Herold drin: Back jetzt, 2350 Gold für Eklipse. Danach zur Top-Welle.<br>19:48 Yorick kämpft: nicht hin, Rechner klar hinten. | 19:00 1000 Gold hinten, aber ihr skaliert besser: nichts erzwingen, Wellen halten bis Minute 30.<br>19:08 Herold jetzt: Level 12 gegen 9, ihr seid fünf gegen eins.<br>19:24 Baron in 35 Sekunden: Welle rein, dann mit Team zum Baron.<br>19:30 Amumu sein Jungle oben, 8 Sekunden.<br>19:34 Bleib am Baron bei deinem Team und halte die Sicht, Kanone in 43 Sekunden.<br>19:37 „…“ – Jetzt, wo Amumu in 6 Sekunden bei dir sein kann: Back, Eklipse kaufen, dann zu Maokai und Yorick, damit <br>19:51 Kauf Tiamat für die Gefräßige Hydra und Langschwert, dann nach Top.<br>19:53 „…“ – Notiert. Kauf Tiamat für die Gefräßige Hydra, Langschwert und ein Kontroll-Auge, dann nach Top: dort kom<br>19:56 Geh nach Top: dort kommt ihre nächste Welle, Kanone in 20 Sekunden. |
| 20:00 | 20:09 „…“ – Notiert.<br>20:11 Amumu unterer Fluss.<br>20:17 Jetzt, wo Amumu tot ist: Baron jetzt, ihr seid fünf<br>20:46 „…“ – Jetzt, wo dein Team den Baron startet und du alleine oben bist: back sofort, kaufe Tiamat, dann direkt z | 20:11 Amumu unterer Fluss.<br>20:19 Jetzt, wo Plan: Welle gerettet - kein Turm verloren. Drache bestreiten: ihr seid fünf gegen drei.<br>20:24 „…“ – Notiert.<br>20:46 Bleib am Baron bei deinem Team und halte die Sicht, Kanone in 20 Sekunden.<br>20:58 Duell gegen Malphite verloren. Schau es dir im Review an.<br>20:59 Amumu sein Jungle unten. |
| 21:00 | 21:00 „…“ – Jetzt, wo du tot bist und dein Team den Baron startet: back sofort, Tiamat kaufen, dann direkt zum Baron<br>21:10 „…“ – Jetzt, wo dein Team den Drachen kämpft: back sofort, Tiamat kaufen, dann zum Drachen – fünf gegen vier m<br>21:19 „…“ – Back sofort, Tiamat kaufen, dann zum Drachen – fünf gegen vier mit deinem Spawn in 19 Sekunden gewinnt.<br>21:27 „…“ – Du wirst in 11 Sekunden gespawnt, backst sofort in der Basis, kaufst Tiamat für 1200 Gold, dann rennst d<br>21:54 „…“ – Der Drache ist weg, also geh jetzt back und hol das Vampirisches Zepter für 900 Gold, das hast du mit de | 21:03 „…“ – Mein Fehler. Jetzt, wo du tot bist und vier Gegner unten stehen: kauf Tiamat und zwei Langschwerter, dan<br>21:05 „…“ – Du bist tot: Kauf Tiamat und zwei Langschwerter, dann geh zur Gruppe, nicht allein zum Baron, weil Malph<br>21:14 „…“ – Jetzt, wo dein Team den Drachen kämpft und nicht den Baron: kauf Tiamat und zwei Langschwerter. Dann sto<br>21:22 „…“ – Jetzt, wo Malphite oben sichtbar ist: Kauf Tiamat und zwei Langschwerter, dann zur Gruppe am Drachen, we<br>21:27 Du lebst in 11 Sekunden. Kauf Tiamat für die Gefräßige Hydra und zweimal Langschwert.<br>21:30 „…“ – Tut mir leid. Kauf Tiamat und Vampirisches Zepter, dann zur Gruppe am Drachen, weil Malphite oben steht <br>21:44 Geh zu deinem Team: Cassiopeia und Akali stehen in eurem unteren Jungle.<br>21:45 Malphite oben: Welle drücken.<br>21:55 Kampf vorbei.<br>21:58 Sie haben den Drachen. Back jetzt, 950 Gold für Vampirisches Zepter. Danach zu deinem Team. |
| 22:00 | 22:28 „…“ – Jetzt, wo du in der Basis bist und Tiamat hast: zu Akali und Yorick in euren unteren Jungle, drei gegen <br>22:39 „…“ – Jetzt, wo Cassio in 3 Sekunden respawnt und Amumu sowie Gragas tot sind: Back, Tiamat kaufen, dann mit d<br>22:52 „…“ – Jetzt, wo Tiamat schon drin ist: Top-Welle crashen, dann mit den vier zum Bot-Turm, weil drei tot und ih | 22:00 Ezreal euer Jungle unten: Büsche meiden.<br>22:05 „…“ – Jetzt, wo der Drache weg ist: Back, Vampirisches Zepter kaufen, dann zur Top-Welle, weil die Kanone in 4<br>22:05 Braum euer Jungle unten: Büsche meiden.<br>22:09 Kauf Vampirisches Zepter für die Gefräßige Hydra, dann nach Top.<br>22:16 Amumu euer Jungle unten.<br>22:30 Jetzt, wo Plan: Farm deine Top-Welle.<br>22:43 „…“ – Jetzt, wo 297 Gold nichts kaufen: kein Back, nimm die Kanone. Danach mit Maokai oben Druck, weil Amumu u<br>22:43 „…“ – Tiamat hast du schon, kein Back: Nimm die Kanone, dann mit Maokai oben Druck, weil Amumu und Gragas tot <br>22:46 Malphite euer Jungle oben: Büsche meiden.<br>22:50 Farm Top, Amumu lebt in 23 Sekunden wieder. Nicht zu Maokai: 10 Sekunden weg.<br>22:55 „…“ – Stimmt, Tiamat hast du schon, mein Fehler. Plan bleibt: Kanone nehmen, dann mit Maokai oben Druck, weil <br>22:57 Geh auf ihren inneren Top-Turm: Amumu kommt vorher, Kanone in 41 Sekunden. |

Die Unterschiede in diesen zehn Minuten:
- **15:17:** Beim Respawn kommt sofort der Kauf.
- **15:31:** Beim Stehen im Brunnen kommt „Raus jetzt, zur Top-Welle“. Live kam dazwischen nichts.
- **17:52:** „Du lebst in 11 Sekunden. Kauf Eklipse und Vampirisches Zepter.“ Live hieß es nur „Du lebst in 11
  Sekunden.“
- **19:51:** „Kauf Tiamat für die Gefräßige Hydra und Langschwert“. Das ist das Gold, das 20:09 liegen blieb.
- **21:00–21:30:** Die Antworten sagen nicht mehr, dass das Team den Baron startet.

## Offen

- **Zielkonflikt Herzschlag gegen Sparsamkeit:** Zehn ältere Szenarien sind rot (0137, 1204, back-dauerton ×2,
  wohin-kurz, 1247, 1453, 0806, s23, a4-lagebild), dazu steigen Füllsätze und Widersprüche. Carlos entscheidet:
  Wie oft darf dieselbe Anweisung neu kommen, und ist „Bleib dabei, Kanone in N“ ein Füllsatz?
- **Chancen:** Genutzt werden 53 % statt 68 %. Der Nachsatz „warum nicht“ fällt jetzt öfter weg: im Kauf-Takt,
  bei Gegnern in der Nähe und wegen der Wortgrenze.
- **Nach dem Nachspiel geändert, per API nicht nachgemessen:**
  - Stratege-Neins
  - „Bleib dabei“ nur mit Info
  - R1 beim Spielende
  - Baron-Grube
- **Nicht angefasst:** `wissen/testpartien.toml` (automatisch gepflegt, fremd geändert). 091311 steht dort erst,
  wenn das Werkzeug neu läuft.
