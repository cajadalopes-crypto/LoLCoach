Guthaben: 0,00 $ (Abo-Aufrufe: 503)

# Bericht zu Auftrag 028 – Eine Stimme, ein Plan, richtig kaufen

## **TOR NICHT ERREICHT**

Fertig am 30.09.2026. Keine Testpartie, der Coach wurde nicht gestartet, die API nicht benutzt (Sparsperre
`llm_api.freigegeben()`, 0,00 $). Die Tor-Runde per Abo lief **nicht**, weil ihre Bedingung nicht erfüllt war:
- **Soll-Liste:** 091311 82 % und 164809 80 % liegen über 75 %, 134020 aber nur bei 69 %.
- **Widersprüche laut Kritikern:** 13, 9 und 6 je Partie (Soll ≤ 1).
- **Automatisch** waren es 0, 0 und 0.
- **Sicherheit** ist 0 in allen drei Partien.

Die beiden Zählungen der Widersprüche gehen auseinander. Das automatische Maß erkennt einen Grund am Satzanfang
(„Plan geändert:“, ein Ereignis, „Stimmt. Neu:“). Die Kritiker zählen trotzdem jeden Zielwechsel binnen 30 s ohne
neue Lage, und nach ihrem Urteil trägt der Grund den Wechsel oft nicht. Ein Beispiel ist 091311 23:02–23:30:
Mid-Turm und Top-Turm im Wechsel. Das ist der Hauptbefund für 029.

## Die Maße

- **Stub** läuft auf allen 10 Testpartien (neu: 134020), mit den Messdefinitionen aus 027.
- **„027“** ist der Endstand aus dem Bericht 027 (9 Partien) und wurde nicht nachgemessen.
- **Abo** ist das Nachspiel von 091311, 134020 und 164809 (Holdout), mit Zwischenspeicher.

| Maß | Soll | 027 | 028 Stub | 028 Abo (091311 / 134020 / 164809) |
|---|---|---|---|---|
| Anweisungs-Lücke p90 (schlechteste) / längste | ≤ 20 / ≤ 35 s | 12,1 / 20,6 s | 16,2 / 37,9 s ✗ | – |
| Stillstand-Reaktion | ≥ 95 % | 95 % | 96 % (132/138) ✓ | – |
| Basis-Reaktion | ≥ 95 % | 97 % | 98 % (102/104) ✓ | – |
| Negativ allein | 0 | 0 | 0 ✓ | – |
| Hin und Her (< 5 s, 027-Maß) | 0 | 1 | 0 ✓ | 0 / 0 / 0 ✓ |
| **Widerspruch automatisch** (neu, < 20 s ohne Grund) | ≤ 1 je Partie | – | 0 in allen 10 ✓ | 0 / 0 / 0 ✓ |
| **Widerspruch Kritiker** (Median von 3) | ≤ 1 | 7–20 | – | 13 / 9 / 6 ✗ |
| **Füllsätze** automatisch | ≤ 5 % | – | 0/1942 (0 %) ✓ | 0 % / 0 % / 0 % ✓ |
| Füllsätze Kritiker | ≤ 5 % | 5–14 je Partie | – | 1 / 5 / 1 (≤ 2,3 %) ✓ |
| Kanone je 90 s (höchstens) | ≤ 1 | – | 0,35 ✓ | – |
| **Chancen genutzt** | ≥ 68 % | 53 % | 60 % (49/82) ✗ | – |
| Sicherheit | 0 | 2 (API) | 0 ✓ | 0 / 0 / 0 ✓ |
| Soll-Liste (Kritiker, Mehrheit) | ≥ 75 % für die Tor-Runde | 091311: 77 % | – | 82 % / 69 % ✗ / 80 % |
| Event-Abdeckung (Kern) | – | 83 % | 83 % | – |
| Szenarien | – | 337 / 358 | 361 / 376 | – |

**Offengelegt:**
- **Lücke:** Die längste Lücke ist schlechter als in 027. Es sind 37,9 s in 133448 und 34,0 s in 101426; in 027
  waren es 20,6 s. Das habe ich nicht mehr untersucht. Vermutlich hält der Herzschlag jetzt öfter still, weil sich
  eine Anweisung nur mit Neuem wiederholen darf.
- **Messdefinitionen:**
  - Die Definitionen aus 027 sind unverändert.
  - Neu ist das Maß Widerspruch in `hoeren()`. Es erkennt einen Grund wie `herzschlag.wechsel_grund`. Ein
    „Back jetzt“ zählt dabei als haltendes Ziel, ein „…, dann back“ nicht (`halte_ziel`).
  - Neu ist auch das Maß Füllsätze (`FUELL`).
  - Neu ist das Maß Sicherheit, genau wie im Abo-Nachspiel.
- **Code-Stände der Nachspiele:**
  - Abo 091311 und 164809 liefen auf 464fe8f, 134020 auf c467d30. 134020 lief zweimal: im ersten Lauf fehlte
    wegen eines NameError die TP-Antwort.
  - Danach kamen noch zwei kleine Korrekturen, nur im Stub und in den Szenarien geprüft: 3048
    (Jungler-Sichtung) und c99add7 („Plan geändert. Nicht zu …“).
- **Abo-Aufrufe:** 503 in dieser Sitzung. Die meisten kommen aus den drei Nachspielen und einem abgebrochenen
  ersten Lauf, den ich nach einem letzten Fix neu gestartet habe.
- **Agenten:** 9 Kritiker und 1 blinder Soll-Listen-Schreiber für 134020. Die neue Soll-Liste
  `soll_023/soll_2026-09-30_134020.json` hat 78 Aussagen aus der LAGE ohne Coach-Text.

## Gebaut (Commits)

**Teil 0 (04241aa, b6377df, 513157f):**
- **Reste committet.**
- **Sparsperre:**
  - Die API läuft nur mit `LOLCOACH_API=1`, das nur `Coach starten.cmd` setzt.
  - Die Nachspiel-Werkzeuge löschen die Variable.
  - Neu ist `werkzeuge/guthaben.py`, dazu `test_sparsam`.
- **Review entfernt,** mit OFFEN-Zeile: wiederherstellbar aus b6377df.

**Teil 1 und 2 (72ea066):**
- **Ein Plan für alle Quellen.** Ein Wechsel binnen 20 s gibt es nur mit Grund. Der Kern hält sich daran, und
  das Sprech-Tor prüft es beim Sprechen noch einmal.
- **Der Schiedsrichter** sieht die gesprochenen Sätze jeder Quelle.
- **Keine internen Etiketten mehr** als Ereignis („Jetzt, wo Plan:“). „Jetzt, wo du gefragt hast“ heißt jetzt
  „Neu:“.
- **Keine Entschuldigungen:** statt „Mein Fehler“ jetzt „Stimmt. Neu: …“.
- **Kein „Bleib dabei“ mehr.** Eine Anweisung kommt nur mit Neuem wieder: dem nächsten Schritt, einem Countdown
  ≤ 10 s oder einem nahen Objective. Wer steht, hört „Los: …“.
- **Kanone** kommt nur als Countdown vor dem Back.

**Teil 1.3 und 3 (5b80e91):**
- **Kein Doppel binnen 10 s** aus irgendeiner Quelle.
- **Kill-Check beim Sprechen, für jede Quelle.**
  - Der Fehler: Die Antwort „Xerath töten sofort“ (231200 26:25) wurde beim Fragen geprüft. Damals hielt der
    Kill (26:23–26:25). Gesprochen wurde sie 3,5 s später, als er nicht mehr hielt, und Antworten gingen ohne
    zweite Prüfung an die Stimme.
  - Jetzt prüft das Sprech-Tor (`kern.unsicher_jetzt`) Kern, Herzschlag, Events und Stratege.
  - Antworten prüfen `sprache._sicher` und `kern.sichere_antwort`: der unsichere Satz fällt, an seine Stelle kommt
    „Kein sicherer Kill mehr.“
  - Das Nachspiel spricht Antworten wie live erst im Takt danach.
  - Das Szenario `antwort_sprechen` war auf 72ea066 rot.

**Teil 6 (6a77fbd, danach c467d30):**
- **Kaufplan:**
  - Ohne eigenen Build gilt der Build aus der Spielakte. Das Lexikon zählt jetzt bis „Situativ“ und liest
    „Jak'Sho, der Proteaner“ ganz.
  - Stiefel der Stufe 2 richten sich nach dem Gegnerteam, mit Grund („gegen Tryndamere und Miss Fortune: ihre
    Auto-Angriffe“), und kommen spätestens nach dem ersten fertigen Item.
  - Der Back-Ruf nennt die ganze Kette („Kauf Bamis Glutstein für Sonnenfeuer-Ägide, Kettenweste und
    Rubinkristall“).
  - Übriges Gold geht in den Build oder in ein Kontroll-Auge.
- **Elixier – Abweichung vom Wortlaut, bitte bestätigen:**
  - Der Auftrag sagt „nur mit sechs fertigen Items“.
  - 183125 36:47 ging es mit sechs Items aber nicht zu kaufen (Szenario 3543, Auftrag 018).
  - Umgesetzt ist deshalb: fertiger Build (fünf fertige Items), ein freier Platz, ab Level 9. Mitten im Spiel nie.
- **Sonderregeln je Champion** stehen in `wissen/sonderregeln.toml` und wirken im Kern.
  - Ornn backt nur für Leben und hört „Kauf gleich hier, ohne Back: …“.
  - Kein Vorback und kein „Back zum Kaufen“ im Stratege: `stratege.pruefe` verwirft es, und es steht im Kontext.
- **Sperren** (`kern/einspruch.py`): Carlos' Widerspruch sperrt alle Stimmen.
  - „Kein Elixier“ gilt für den Rest der Partie, „freezen“ bis Tod, Back oder 2 min, „kauf kein X“ ebenso.
  - Die Sperren stehen im Stratege-Kontext, und `stratege.pruefe` verwirft solche Sätze.
- **Namensvettern:**
  - Ein Minimap-Icon, das im selben Bild für beide Teams steht, gehört dem Team, das zuletzt dort war. Das
    betraf 4083 Bilder.
  - Reißt die Spur ab (12:31), wird die Sichtung zurückgeordnet.
  - Gesprochen wird „ihre Sejuani“ oder „eure Sejuani“, für jede Quelle; auch der Stratege-Prompt sagt es.
- **Antwort zuerst:** „Teleport oder laufen?“ bekommt die Wahl mit Grund, dann den Plan. „Passt ohne Verkauf:
  …“ antwortet auf „kein Platz“.
- **Spielende:** „Jetzt beenden“ nur, wenn mindestens zwei Mitspieler an ihrem Nexus stehen (und nicht unter R1).

**Regressionen der Szenarien und Nachschliff (315ee63, 464fe8f, c467d30, c99add7):**
- **warum-nicht:** Es nimmt nur einen Plan, der noch bindet, und wechselt ein veraltetes Ziel mit Grund hörbar
  (102112 34:53). Der Kopf des Satzes muss eine Handlung sein.
- **Back-Ruf:** „Back jetzt“ gilt bis zu einer Gefahr oder einer Frage (Szenario 2302). Ein Back-Ruf wiederholt
  sich binnen 120 s nicht.
- **Wechsel mit Grund:** „Plan geändert“ zählt ab dem Ursprung des Plans. Ein begründeter Wechsel wartet 5 s nach
  dem letzten Plan-Satz, statt wegzufallen; damit ist Hin und Her 0.
- **Herzschlag:** Der Grund einer Anweisung kommt höchstens alle 180 s, dazwischen nur die Handlung. Die volle
  Jungler-Sichtung ersetzt die bloße.

## Teil 2: die zehn Alt-Szenarien

| Szenario | Beschwerde | Entscheidung | jetzt |
|---|---|---|---|
| 0137-schutzplan-sparsam | derselbe 22-Wort-Satz achtmal | Wiederholung: Regel bleibt | grün |
| 1204-kein-spitzhacke-dauerton | „Gold für Spitzhacke“ zwölf Minuten | Wiederholung: Regel bleibt | grün |
| back-dauerton (164326) | 11 Back-Rufe, meist ignoriert | „zu viel reden“: umgeschrieben auf `ohne_neues_max` (Back ohne neue Info binnen 120 s rot) | grün |
| back-dauerton (173159) | 12 Back-Rufe | ebenso umgeschrieben | grün |
| wohin-kurz (164326) | „dort nimmt sie sonst niemand“ 8–12 Mal | Wiederholung: Regel bleibt | **rot** (2: einmal als „Plan geändert: …“, einmal im warum-nicht) |
| 1247-ziel-nicht-noch-einmal | „Zum Drachen“, 12 s später „Dann Drachen“ | Wiederholung: Regel bleibt | grün |
| 1453-herold-ein-satz | ein langer Satz aus drei Teilen | „zu viel reden“: `ansagen_max 1` → `ohne_neues_max` | grün |
| 0806-kein-back-gegner-kommen | Back, obwohl Gegner kommen | Verbote bleiben; `ansagen_max 2` → `ohne_neues_max` | grün |
| s23-plan-hoechstens-14 | „redest zu lange … immer zu spät“ | Satzlänge, kein Zu-viel-Reden: Regel bleibt | **rot** (18-Wort-Sätze mit „Los:“ und zwei Teilen) |
| a4-lagebild-ungefragt | ungefragtes Lagebild fehlt | Inhalt, kein Zu-viel-Reden: Regel bleibt | **rot** (das Lagebild kommt nur in Stille, der Herzschlag lässt keine) |

Die weiteren Szenarien:
- Neu rot gegenüber 027 ist nur **2302-back-gilt-still**. Der Back kommt jetzt 22:25, früher als in 027
  (22:52); 37 s später kommt der Drache-Wendepunkt. Die Prämisse des Szenarios gibt es damit nicht mehr, die
  Back-Regel selbst hat einen Test.
- Die übrigen Roten sind dieselben wie in 027: m-Szenarien „mehrere Events“, `wendepunkt-ansage` und
  0944-erster-tower.

## 091311, 13:00–23:00: 027 neben 028 (Abo-Nachspiel, nur geänderte Zeilen)

| Minute | 027 (nur dort) | 028 (nur dort) |
|---|---|---|
| 13 | 13:19 Farm Top, Malphite lebt in 13 s wieder, Kanone in 37 Sekunden.<br>13:20 Antwort: Jetzt, wo Malphite noch 11 s tot ist …: Crash die Top-Welle | 13:19 Farm Top, Malphite lebt in 21 s wieder.<br>13:20 Antwort: Bleib auf Top und farm die Welle, denn der Fluss ist 20 s weg …<br>13:52 Plan geändert: Geh nach Top … Nicht zu Cassiopeia. |
| 14 | 14:39 Antwort: … Back jetzt, Caulfields Kriegshammer … | 14:39 Antwort: Ja, ich sag's, du spielst. Bleib bei Maokai und Cassiopeia am Drachen … |
| 16 | 16:06 Antwort: Kein Kauf, dein Inventar ist voll …<br>16:35 Bleib dabei. Nicht zu Cassiopeia: 20 Sekunden weg.<br>16:59 Antwort: Jetzt, wo Malphite … auftaucht …: Plan gestoppt … | 16:02 Ihr Top hat kein TP bis 20:05: Zu Cassiopeia und Yorick auf die Bot-Lane …<br>16:06 Antwort: Langschwert bleibt, es ist ein Bauteil.<br>16:25 Antwort: Ja, bleib oben: Nimm jetzt die Welle am Turm, weil Malphite unten ohne TP ist.<br>16:59 Antwort: Stimmt, der Plan hat sich geändert: Die Kanone kommt erst in 47 s … |
| 17 | 17:15 Back jetzt: 1100 Gold für Eklipse. … | 17:13 Back jetzt: Kauf Eklipse und Langschwert. … |
| 18 | 18:23 … farm sie, Kanone in 13 Sekunden.<br>18:34 Bleib dabei. Nicht zu Maokai: 13 Sekunden weg. | 18:23 Geh zur Top-Welle und farm sie.<br>18:34 Geh zur Top-Welle und farm sie. Nicht zu Maokai: 13 Sekunden weg. |
| 19 | 19:34 Bleib am Baron …, Kanone in 43 Sekunden.<br>19:37 Antwort: Jetzt, wo Amumu …: Back, Eklipse kaufen …<br>19:56 Geh nach Top …, Kanone in 20 Sekunden. | **19:24 Jetzt, wo Baron in 34 Sekunden aufgetaucht ist: Baron in 32 Sekunden: …** (Satzfehler, offen)<br>19:37 Antwort: Nein, der Herold lebt noch und verschwindet um 19:45. Bleib am Baron … |
| 20 | 20:19 Jetzt, wo Plan: Welle gerettet … Drache bestreiten …<br>20:46 Bleib am Baron …, Kanone in 20 Sekunden.<br>20:58 Duell … verloren. Schau es dir im Review an. | 20:22 Drache bestreiten: ihr seid fünf gegen zwei.<br>20:50 Los: Geh nach Top: dort kommt ihre nächste Welle. |
| 21 | 21:03 Antwort: Mein Fehler. …<br>21:30 Antwort: Tut mir leid. …<br>21:58 Sie haben den Drachen. Back jetzt, 950 Gold für Vampirisches Zepter. … | 21:03 Antwort: Stimmt. Neu: Malphite stand oben. Kauf Tiamat und zwei Langschwerter …<br>21:05 Antwort: Nein, nicht allein Baron: Malphite war vor 7 s im oberen Fluss …<br>21:14 Antwort: Stimmt, dein Team will den Drachen, kein Baron.<br>21:30 Antwort: Nein, der Plan bleibt: … |
| 22 | 22:30 Jetzt, wo Plan: Farm deine Top-Welle.<br>22:43 Antwort: Jetzt, wo 297 Gold nichts kaufen: …<br>22:55 Antwort: Stimmt, Tiamat hast du schon, mein Fehler. … | 22:30 Farm deine Top-Welle.<br>22:43 Antwort: Nein, kein Back, es gibt nichts zu kaufen. …<br>22:55 Antwort: Stimmt, Tiamat ist drin; das Langschwert kaufst du erst beim nächsten Back. … |

13:00–23:00: 80 Sätze in 027, 76 in 028. Weg sind:
- „Bleib dabei“,
- „Mein Fehler“ und „Tut mir leid“,
- „Jetzt, wo Plan:“,
- der Review-Hinweis,
- die Kanone als Beiwort.

Antworten beginnen mit Ja, Nein oder „Stimmt.“.

## 134020: jede Notiz-Stelle, live neben jetzt (Abo-Nachspiel 028)

| Notiz | live gehört | jetzt |
|---|---|---|
| 1:14 Dorans Schild | Back jetzt: Dorans Schild holen, dann Top zurück … | Back jetzt: 25 Prozent Leben. (Der Stratege schlug Dorans diesmal nicht vor; käme es, verwirft `stratege.pruefe` es mit „hast du schon“ – Szenario 0114, im Nachspiel so bei 7:23 „Rubinkristall hast du schon“) |
| 2:29 TP oder laufen | Du lebst in 7 s: kauf Rubinkristall … dann lauf … | Lauf zum äußeren Top-Turm; Tryndamere war vor 7 s im oberen Fluss … (Stratege). Der Kern antwortet „Laufen: in 35 s bist du an deinem Turm, TP hast du nicht.“ |
| 2:58 „Jetzt, wo du gefragt hast“ | Jetzt, wo du gefragt hast: Los: Zurück nach Top … | Raus jetzt, nach Top. |
| 3:17–3:56 Freeze | dreimal „crash“ | Stimmt. Neu: Freeze, nichts drücken; lasthitte nur die Kanone am Turm … / Ja, … also freeze am Turm … |
| 7:55 ganze Kette | Back jetzt, Bamis Glutstein kaufen … / Kauf Sonnenfeuer-Ägide | Kauf Bamis Glutstein für Sonnenfeuer-Ägide, Kettenweste und Rubinkristall. |
| 12:41 Sejuani Flussmitte | Sejuani Flussmitte. | (keine Sejuani-Meldung; das Icon war die eigene) |
| 12:56–14:01 Back Dornenpanzer, keine Stiefel | Back jetzt: 1000 Gold für Dornenpanzer. / … Kauf Elixier des Metalls … | Back jetzt: 21 Prozent Leben … / Kauf gleich hier, ohne Back: Beschichtete Stahlkappen und Dornenpanzer. |
| 14:51 Stiefel, Elixier | Notiert. | Kauf gleich hier, ohne Back: Nullmagie-Mantel. |
| 16:20–20:03 kein Elixier | Kauf Elixier des Metalls (19:33) / Du hast recht – … | der Coach sagt in der ganzen Partie kein „Elixier“ mehr (nur Carlos' Fragen enthalten das Wort) |
| 18:35 „wieder nur Scheiße“ | Jetzt, wo du in der Basis bist: Zum Drachen … / Bleib am Drachen …, Kanone in 12 s | Kauf Kaenischer Rookern und ein Kontroll-Auge, dann zum Drachen: ihr seid drei. / Drache weg: nicht hin. / Bleib am Drachen … |
| 22:02 Kanone / 22:17, 25:05, 32:31 Elixier | Kauf Elixier des Metalls. (dreimal) | Stimmt, die Kanone ist nur Beifang, nicht das Ziel. Kein Elixier. |
| 27:36 warum keine Chance | Jetzt, wo du tot bist …: Du lebst in 34 s … | Doch, ihr habt Chance: 41 zu 24 Kills, 6950 Gold vorn. Nach dem Respawn Jak'Sho kaufen … |
| 29:20–30:20 Spielende | Jetzt beenden / Back jetzt / Jetzt beenden + Raus jetzt / Geh auf ihren Nexus / Zurück / Zurück | Jetzt, wo alle fünf tot sind: drück … / Ihr Nexus jetzt … / Nein, bleib: schlag jetzt den Nexus … / Raus jetzt: Leona ist da. / **Geh nach Top …** / Stopp – zurück … (kein „Jetzt beenden“ mehr, aber noch nicht ruhig) |

Die 17 Szenarien aus den Notizen sind alle grün; auf 5b80e91, vor Teil 6, waren 9 davon rot. Die TP-Notizen
2:57 und 11:55 stehen für 029 in `tests/szenarien/offen/2026-09-30_134020_tp.toml`.

## Offen / für 029

- **Widersprüche:** Kritiker und automatisches Maß gehen auseinander (siehe oben). Das automatische Maß müsste
  strenger werden, oder der Kern müsste weniger wechseln, auch mit Grund.
- **Chancen 60 %** statt ≥ 68 %. Am häufigsten fehlt der Nachsatz, wenn der Kern-Plan gerade wechselt; einen
  veralteten Plan hat der Kern dafür nicht mehr.
- **Längste Lücke** 37,9 s (133448).
- **Satzfehler 19:24** „Jetzt, wo Baron in 34 Sekunden aufgetaucht ist“: Ein Zeitsatz wird zum Ereignis.
- **Spielende 134020** 30:04 „Geh nach Top“ zwischen Nexus und Rückzug.
- **Stiefel:** 134020 32:30 „Kauf Beschichtete Stahlkappen“, obwohl Carlos sie um 14:51 selbst gekauft hatte.
  Nicht geprüft.
- **Elixier-Regel** (Abweichung oben): bitte bestätigen.
