Guthaben: 0,00 $ (Abo-Aufrufe: 0)

# Challenger-Gehirn, Phase 0 – Was die Partien hergeben (Auftrag 029, 30.09.2026)

Werkzeuge: `werkzeuge/challenger/` (`grundlage.py` verdichtet, `bestand.py`, `ableitungen.py`, `momente.py`,
`silber_download.py`). Einzelheiten: [bestand.md](bestand.md), [feldkatalog.md](feldkatalog.md),
[ableitungen.md](ableitungen.md), [momente_roh.md](momente_roh.md). Alles ist wiederholbar und nimmt neue
Downloads mit (`python werkzeuge/challenger/bestand.py`, dann `ableitungen.py`, zusammen etwa 2 min).
Riot-Abrufe: 3 (die drei Ligalisten). Claude: keine.

## 1. Datenbestand (Stand 15:45, der Download läuft weiter)

| | |
|---|---|
| Partien geladen / gültig | 2822 / **2792** (30 heraus: Remake oder unter 15 min) |
| Patch | 16.18: 1234, 16.19: 1182, **16.17: 376** – nicht nur 16.19, wie Buch 17 sagt |
| Zeitraum, Dauer | 31.08.–30.09.; Median 26,6 min (Quartile 23,1 / 30,6) |
| Rollen, Doppelte, Zeitleiste | alle Partien mit fünf Rollen je Team; 0 Doppelte; Zeitleiste in jeder Partie |

**Spieler-Partien je Liga** (Ligalisten vom 30.09. 15:21, Stand heute, nicht zur Zeit der Partie):

| Liga | Top | Jungle | Mid | ADC | Support | Spieler |
|---|---:|---:|---:|---:|---:|---:|
| Challenger | 1718 | 1733 | 2607 | 2576 | 1394 | 300 |
| Grandmaster | 2183 | 2314 | 1902 | 1876 | 2307 | 673 |
| Master | 1652 | 1505 | 1048 | 1107 | 1842 | 1915 |
| nicht in den Listen | 31 | 32 | 27 | 25 | 41 | 118 |

Die Master-Liste liefert höchstens 10.000 Einträge. „Nicht in den Listen“ heißt also: heute unter Master oder
jenseits dieser Grenze. Für Top gibt es **5553 High-Elo-Spieler-Partien**, davon 1718 Challenger.

**Was anders ist als in Buch 17:**
- **Atakhan und `voidGator`:** Die Felder stehen in den Team-Zielen, sind aber in allen 2822 Partien 0. Es gibt kein
  Monster-Ereignis dafür. In 16.17–16.19 kommt dieses Objective in den Daten nicht vor.
- **Larven:** Jede Larve ist ein eigenes Ereignis (3 je Spawn). Bei `assistingParticipantIds` steht manchmal ein
  Gegner.
- **Leben je Minute:** Das Feld `health` ist immer gefüllt. Leben 0 heißt tot. Das prüft die Todeszeit-Formel
  unabhängig, und ohne dieses Feld stehen Tote an ihrem Todesort statt im Brunnen.
- Eine **Kauf-Zeit und die Minutenposition** liegen bis zu 8 s auseinander (99 %), gemessen an Käufen und der Minute
  danach. Jede Ableitung rechnet deshalb mit 10 s Spiel.

## 2. Feldkatalog (vollständig in [feldkatalog.md](feldkatalog.md))

- **Match:** 154 Spieler-Felder, 142 `challenges`, 12 `missions`, 9 Team-Ziele.
- **Minute** (je Spieler): Position, Gold, XP, Level, CS, 25 Werte (`championStats`, u. a. Leben und Tempo), 12
  Schadenswerte.
- **19 Ereignisarten**, je Partie etwa: 228 Käufe, 200 Wards gesetzt, 55 Kills, 54 Platten, 12 Gebäude, 8,5 Monster.

Füllquoten, die zählen:

| Feld | Füllquote |
|---|---|
| Kill-Ort | 100 % |
| Kill-Helfer | 80 % (Rest: Solo-Kills) |
| Monster-Helfer | 57 % |
| Drachen-Art (`monsterSubType`) | nur bei Drachen |
| Gebäude: Täter | 96 % (Rest: Vasallen) |

**Was fehlt:**
- Wellen;
- Ward-Orte (Ward-Ereignisse ohne Ort);
- Nebel und Sicht;
- Abklingzeiten (nur Summen je Partie: `summonerXCasts`);
- Wege zwischen den Minuten;
- Leben im Kampf;
- der Recall selbst (nur der Kauf);
- Pings mit Zeit oder Ort (nur Summen je Partie);
- Ganks ohne Kill.

## 3. Ableitungen, je 50 Stichproben

Jede Ableitung hat eine Gegenprobe aus Daten, die sie selbst nicht benutzt. Zuerst lagen fast alle bei 95–100 %,
das war zu glatt. Deshalb läuft jetzt eine **Nullprobe** mit: dieselbe Gegenprobe mit falschem Ort bzw. falscher Zeit.
Nur wo die Nullprobe klar tiefer liegt, belegt die Gegenprobe etwas. Drei Gegenproben habe ich danach ortsgenau
gemacht (Rotation, Split, Gruppe), weil sie vorher auch mit falschem Ort zu 95 % bestanden.

| Ableitung | je Partie | Stichprobe | alle stimmig | Nullprobe | Urteil |
|---|---:|---:|---:|---:|---|
| **Gank** (Jungler am Lane-Kill, bis 14:00) | 5,6 | 44/50 | 86 % | 3 % | **trägt**. Die 6 Zweifel sind Roam-Opfer (Support stirbt mid). |
| **Kampf** (≥ 2 Kills, ≤ 15 s, ≤ 3000) | 3,9 prüfbar (12,2 gesamt) | 50/50 | 98 % | 12 % | **trägt**. Prüfbar sind nur Kämpfe ≤ 10 s neben einer vollen Minute. |
| **Rotation** (Seitenwechsel, 2 min gehalten; ohne Jungler) | 3,2 | 50/50 | 98 % | 33 % | **trägt**. Mit nur einer Minute: 39/50, die Zweifel waren Durchgänge. |
| **Split** (2 min allein in Seitenlane, ab 14:00) | 0,7 | 44/50 | 92 % | 56 % | brauchbar. Split ist selten, weil zwei Minuten allein streng sind. |
| **Gruppe** (≥ 3 in 2500, ab 8:00) | 14,9 | 45/50 | 93 % | 65 % | brauchbar. Die Positionen sind sicher, der Anlass nur grob. |
| **Todeszeit** (Formel aus `mechanik.toml`) | 55,8 | 45/50 | 89 % | 76 % | stimmt in 89 %. Die Zweifel sind Wiederbelebungen (GA, Zilean). Die Minute ist zu grob für mehr. |
| **Back** (Kauf nicht nach Tod; dazu 1 % ohne Kauf) | 67,9 Käufe, 6–7 echte Backs je Spieler | 50/50 | 100 % | 86 % | **per Spielregel sicher** (Kauf nur im Laden oder tot). Die Positions-Gegenprobe trennt nicht, weil 60 s fast jeden Weg erlauben. |
| **Umkämpftes Objective** (Kill ±30 s, ≤ 3000) | 8,6 | 37/50 | 71 % | 63 % | **schwach.** Bei 40 % „freier“ Objectives standen ≥ 3 Gegner dabei (bestritten ohne Kill). |
| **TP** (Sprung, der zu Fuß und per Recall nicht geht) | 0,5 | 29/50 | 54 % | – | **findet nur 3 % der TPs** (686 von 21.227 Einsätzen). Mit dem Tor `summonerXCasts` (nur TP-Spieler) sind etwa 79 % der Funde echt: Die Kontrollgruppe ohne TP schlägt 0,026-mal je Partie an. |

Umkämpft waren: Drachen 36 %, Baron 47 %, Herold 31 %, Larven 27 %.

**Was das für TP heißt:**
- Eine Minute reicht, um fast überall hinzulaufen. Aus den Minutenpositionen ist ein TP nur sichtbar, wenn ein Kauf
  oder ein Kill wenige Sekunden vor der Minute liegt.
- Die Zahl je Partie ist exakt (`summonerXCasts`, im Schnitt 3,7 je TP-Spieler). Dazu kommt `teleportTakedowns`
  (1886 Kills/Assists kurz nach TP).
- Wann und wohin ein TP ging, bleibt meist unbekannt. Für Phase 1 heißt das: TP als Aktion ist nur in einem
  Bruchteil der Fälle markierbar. Der TP-Wert muss aus diesen gut 700 sicheren Fällen plus Rechnern (Stufe 3)
  kommen, nicht aus allen 21.000.

## 4. Eine Partie, zehn Momente

**EUW1_7997574868**, Patch 16.19:
- **Ambessa** (Top, Blau, Challenger, TP) gegen Aatrox, 30:02, Sieg; 5/5/16, 19 Platten, 4 TP.
- Team-Gold +2.375 bei 10:00 und +5.123 bei 20:00.
- Eine Comeback-Partie (Camille, −7,6 k bei 22:00) habe ich verworfen, weil sie als Lehrbeispiel zu schief ist.

Markierung: **[B]** beobachtet, **[G]** geschätzt, **[U]** unbekannt. Die Kommandos sind **[G]**: mein
Coach-Urteil aus der Lage. Ein Datenmodell dafür gibt es noch nicht. Rohdaten je Moment: [momente_roh.md](momente_roh.md).

**1 · Erster Back (Lage 3:03)**
- **Lage:**
  - Ambessa hat Level 3, **84/1002 Leben** [B, Minute 3:00], 603 Gold, CS 19 zu 17.
  - Aatrox hat Level 4 [B].
  - Kills stehen 2:0 für uns (bot). Vi wurde nie gesehen [U].
- **Tat:**
  - 3:04 Solo-Kill an Aatrox [B].
  - 3:23 Back: Spitzhacke und nachfüllbarer Trank [B].
  - Um 4:00 steht sie wieder oben, zu Fuß [G, 37 s reichen].
- **Folge:** Team-Gold +1.334 → +2.828 in 2 min [B].
- **Kommando:** „Aatrox ist tot – jetzt zurück, 600 Gold sind die Spitzhacke. Zu Fuß zurück, TP aufheben.“
- **Warum:** Mit 84 Leben ist jede Welle ein Risiko. Aatrox' Todeszeit plus Weg kostet ihn mehr Welle als dich
  der Back.

**2 · Level 6 (Lage 4:22)**
- **Lage:**
  - Ambessa hat Level 5, 853/1189 Leben, Items 1475 zu 1100 Gold [B].
  - Vi und Katarina wurden 4:13 im oberen Fluss beim Kill an Sylas angesagt [B]. Jetzt sind sie [U], etwa 20 s
    entfernt [G].
- **Tat:** 4:32 zweiter Solo-Kill an Aatrox, dabei Level 6 [B].
- **Folge:** Kills 3:0 in den nächsten 30 s [B], Gold-Vorsprung +2.885 [B].
- **Kommando:** „Level 6 kommt mit dieser Welle zuerst zu dir – spiel den Kampf sofort. Danach Welle rein und raus,
  Vi war eben oben.“
- **Warum:** Dein Level-Vorteil hält nur, bis Aatrox nachzieht. Vis letzter Ort liegt im Gank-Weg.

**3 · Erster Kampf (Lage 5:36)**
- **Lage:**
  - Ambessa hat Level 6, 637 Leben, 760 Gold [B]. Aatrox ist Level 5 [B].
  - Sylas steht mid, Qiyana im eigenen Jungle unten [B, Minimap].
- **Tat:**
  - Bleibt oben [B].
  - Nimmt Platten um 6:15 und 6:51 [B], während mid 6:06–6:18 gekämpft wird (2:1 für uns) und bot 6:22–6:26
    zwei von uns sterben [B].
- **Folge:** 2 Platten [B]. Kills in 60 s 2:3 [B].
- **Kommando:** „Mid kämpft 2 gegen 2 – kein TP dafür. Du nimmst die Platte, solange Vi mid gebunden ist.“
- **Warum:** Ein TP für ein 2-gegen-2 ohne Objective lohnt nicht. Platten bis 14:00 sind sicheres Gold.

**4 · Erste Larven (Lage 7:46)**
- **Lage:**
  - Ambessa steht im oberen Fluss, 1120 Leben, 911 Gold [B].
  - Die Mitspieler sind alle auf der Drachenseite [B, Minimap]. Die Gegner wurden zuletzt 6:09–6:26 mid und bot
    gesehen [B].
- **Tat:** Geht zurück in die Lane, keine Ereignisse [B]. Unten ein großer Kampf 7:57–8:11 (3:4) [B].
- **Folge:**
  - Vi nimmt 8:46 eine Larve [B], Qiyana 8:57/8:59 die zwei anderen [B].
  - Gold-Vorsprung bleibt etwa +2.300 [B].
- **Kommando:** „Dein Team ist unten, die Larven stehen oben. Welle schieben, dann an den Larven-Eingang: Wenn Vi
  kommt, bist du die Überzahl.“
- **Warum:** Das nächste Objective liegt auf deiner Seite, der Jungler braucht dich dort. Eine geschobene Welle
  kostet dich dabei nichts.
- **[U]:** Ob Ambessa Sicht setzte, verraten die Daten nicht. Ward-Orte fehlen.

**5 · Erster Drache (Lage 9:10)**
- **Lage:**
  - Ambessa steht oben, Level 9, **1575 Gold** [B]. Aatrox ist Level 8, Items 1750 zu 2175 Gold [B].
  - Bard ist unten, Qiyana nach den Larven oben [B].
- **Tat:**
  - Bleibt oben [B].
  - Nach dem Drachen (10:10, **wir** [B]) Back 10:19: Eklipse [B], zu Fuß zurück bis 11:00 [G].
- **Folge:** Drache für uns, Kills 2:2 in 2 min [B].
- **Kommando:** „Drache unten ist zu weit für dich. Halt die Welle, bis er fällt, dann Back mit 2000 Gold –
  Eklipse.“
- **Warum:** Der Weg Top → Drache dauert etwa 45 s [G]. Bot und Jungler nehmen ihn allein. Dein Back fällt in das
  ruhige Fenster danach.

**6 · TP (Lage 11:24; sicher erkannt)**
- **Lage:**
  - Ambessa steht oben, Level 10, 239 Gold, 1744 Leben [B]. Aatrox hat 2950 Gold Items, sie 4250 [B].
  - Der nächste Drache kommt etwa 15:10 [G, 5 min nach 10:10].
- **Tat:**
  - 11:49 Back: Ruf des Henkers [B].
  - **TP zurück in die Toplane** (11:49 → 12:00 unmöglich zu Fuß) [B+G].
  - 12:05 Platte, 12:18 Kill an Aatrox [B].
- **Folge:** Gold-Vorsprung +2.496 → +3.544 [B].
- **Kommando:** „Kauf den Heilungsschnitt gegen Aatrox und TP zurück – die Platten sind bis 14:00 mehr wert als
  ein TP-Zug nach unten.“
- **Warum:** Kein Objective bis etwa 15:10, dann ist TP wieder bereit [G: Abklingzeit nicht in den Daten].
  Heilungsschnitt macht deine Duelle gegen ihn sicher.

**7 · Erster Turm (Lage 13:00)**
- **Lage:** Ambessa ist Level 11 gegen 9, Items 5900 zu 2950 Gold, volles Leben [B]. Vi wurde zuletzt 8:59 gesehen
  [B], jetzt [U].
- **Tat:** 13:45 letzte Platte und Turm (erster Turm der Partie), 13:47 Kill an Aatrox [B].
- **Folge:** Kills in 60 s 1:4 [B]: Katarina holt 13:36–13:47 unten vier Kills, während oben der Turm
  fällt.
- **Kommando:** „Du bist zwei Level und 3000 Gold vorne – Turm jetzt, vor 14:00.“
- **Warum:** Ab 14:00 gibt es keine Platten mehr. Der Turm ist das größte Gold, das du allein holen kannst.
- **[U]:** Warum der Kampf unten begann, zeigen die Daten nicht.

**8 · Herold (Lage 14:33)**
- **Lage:**
  - Toplane-Turm ist weg, 1175 Gold, Level 13 [B].
  - KogMaw ist tot (22 s) [B]. Katarina und Alistar wurden 13:47 im roten Jungle unten gesehen [B].
- **Tat:**
  - **Rotiert mid:** Platten 14:44–14:54 und Mid-Turm 15:04 zusammen mit Sylas [B].
  - Assists 15:09 und 15:14 [B], dann Herold 15:33 für **uns** [B].
- **Folge:** Gold-Vorsprung +2.084 → +4.567 in 2 min [B].
- **Kommando:** „Oben ist nichts mehr zu holen – geh mid, nimm mit Sylas den Turm, dann zum Herold.“
- **Warum:** Nach dem ersten Turm drückt eine Seitenwelle nur noch bis Turm 2. Mid öffnet die Karte und liegt auf
  dem Weg zum Herold.

**9 · Baron (Lage 20:17)**
- **Lage:**
  - Ambessa ist **tot, noch 8 s** [G, Formel]. Alistar ist tot, Sylas auch [B].
  - Türme 4:0, Items 9100 zu 5700 [B].
- **Tat:** Nach dem Respawn über den oberen Fluss, 20:53 Assist mid, **21:17 beim Baron** [B].
- **Folge:** Baron für uns, Kills 6:2 in 2 min, der Gegner holt einen Höllendrachen [B].
- **Kommando:** „Du lebst in 8 s – nicht auf eine Seite, direkt zum oberen Fluss. Nach dem nächsten Pick: Baron.“
- **Warum:** Bei 4:0 Türmen und einem toten Alistar ist der Baron das Ziel. Ohne dich ist er nicht sicher.

**10 · Schluss (Lage 28:22)**
- **Lage:**
  - 28:03 fällt der Mid-Inhibitor [B].
  - Katarina ist noch 10 s tot, Alistar 6 s. Qiyana und Bard leben in 0–2 s wieder [B].
  - Der Baron steht wieder seit 27:17 [G, 6 min nach 21:17].
- **Tat:** Geht mit dem Team aus der Basis in den oberen Fluss [B]. 29:37–29:51 Kampf dort: Ace [B], Ende 30:02 [B].
- **Folge:** Sieg.
- **Kommando:** „Inhib ist weg, die Toten kommen im Brunnen zurück – raus. Supervasallen drücken mid für euch. Ihr
  geht zu fünft zum Baron-Fluss.“
- **Warum:** Drei gegen drei vor dem Nexus wird in 10 s drei gegen fünf. Der Kampf am Baron nach einem Inhibitor
  entscheidet die Partie. Das Ace kam genau dort.

**Was die zehn Momente zeigen:**
- **Lage → Tat → Folge ist aus den Daten lesbar,** mit einem Fenster von einer Minute. Das Kommando daraus zu
  formulieren ist machbar.
- **Wo das Wissen fehlt:**
  - Sicht und Wards;
  - der genaue Weg;
  - ob TP bereit war;
  - wo der Lane-Gegner steht. Im Spiel sieht Carlos ihn meist, die Daten nennen ihn aber nur „zuletzt gesehen“ an
    Kills.

## 5. Entwurf für Phase 1

**Lage-Merkmale (nur Wissbares), je Spieler und Entscheidungszeitpunkt** (jede volle Minute plus jedes Ereignis):
- **Uhr:** Minute, Phase, Timer aller Objectives (Spawn aus den Ereignissen), Plattenende.
- **Du:**
  - Ort (Bereich und Abstand zu Turm/Brunnen), Leben %, Level, CS, Gold in der Tasche;
  - Item-Wert, Tod und Respawn;
  - TP vorhanden, Einsätze bisher (die Bereitschaft [U] schätzt ein Rechner).
- **Team:** Orte (Minimap), Leben, Level, Tote mit Respawn, Gruppe oder verteilt.
- **Scoreboard:** Item-Wert, Level, CS und Kills aller zehn Spieler; Türme, Platten, Drachen, Seelen-Stand, Larven,
  Herold, Baron.
- **Gegner:**
  - tot mit Restzeit;
  - „zuletzt gesehen“ (Ort und Alter) aus angesagten Ereignissen;
  - **der Lane-Gegner zusätzlich, wenn er innerhalb der Sichtweite (etwa 1200) steht.** Das ist eine Annäherung an
    „auf dem Bildschirm“ – offene Frage 1.
- **Unterschiede:** Gold, Level und Items gegen den Lane-Gegner und Team gegen Team (nur aus Scoreboard-Werten).

**Aktionen (beobachtbar) mit Erkennungsregel für die nächsten 60 s:**
- **Lane halten:** in der eigenen Lane, CS +≥ 4.
- **Back:** Ladenbesuch ohne Tod.
- **Zu Objective X:** ≤ 3000 an der Grube innerhalb von ±60 s um Spawn oder Kill.
- **Rotation zu Lane Y:** Zonenwechsel, 2 min gehalten.
- **Gruppe:** ≥ 3 in 2500.
- **Split:** 2 min allein in der Seitenlane.
- **Jungle:** Jungle-CS +, im Jungle.
- **TP:** nur die sicheren Fälle.
- **Warten:** im Bereich geblieben, CS < 4, kein Ereignis.

Unklar bleibt „TP oder nicht“. Das bekommt das Label „unbekannt“ und wird nicht als „kein TP“ gewertet.

**Folge-Maße nach 30/60/120 s:**
- **Gold:** eigenes Gold und XP, Team-Gold-Abstand (Minute, interpoliert = [G]).
- **Ereignisse:** Kills für und gegen, Tod ja/nein, Platten, Türme, Objectives für und gegen.
- **Am Ende:** die Siegchance-Änderung aus dem Siegchance-Modell (Phase 2) und der Sieg.

**Training und Prüfung:**
- **Nach Zeit:** Prüfung sind die letzten 20 % (ab 27.09. 18:00, etwa 560 Partien).
- **Nach Spielern:** 20 % der PUUIDs (fest per Hash) sind Prüfspieler. Ihre eigenen Entscheidungen fehlen im
  Training.
- **Der Spieler-Pool ist klein.** Von 4490 Spieler-Partien nach dem Stichtag sind nur 321 von Spielern, die vorher
  nie vorkamen. Nur nach Zeit zu teilen würde also dieselben Spieler prüfen.
- Ein Patch-Wechsel (16.20) wird eine eigene Prüfung.

**Silber und Gold:** `werkzeuge/challenger/silber_download.py` ist gebaut und **nicht gestartet**.
- **Quelle:** `league-exp-v4`, SILVER und GOLD, Divisionen I–IV, je 3 Seiten, etwa 4900 Spieler, je 5 Partien, Ziel
  5000.
- **Ablage:** `daten/riot_silbergold/`, die High-Elo-Daten bleiben rein.
- **Geprüft:** kompiliert, `--trocken` läuft ohne Abruf.
- **Carlos startet ihn,** am besten nach dem laufenden 20.000er-Download (gleicher Schlüssel, gleiche Grenzen).

```bash
python werkzeuge\challenger\silber_download.py
```

## 6. Offene Fragen

1. **Lane-Gegner in der Lage:** Darf Phase 1 seine Position nehmen, wenn er ≤ 1200 neben dem Spieler steht
   („sichtbar“)? Ohne das kennt die Lage ihn nur von Kills. Das ist zu wenig für Lane-Entscheidungen, mit dieser
   Regel ist es fast wie im Spiel.
2. **TP:** Soll TP in Phase 1 als eigene Aktion gelernt werden (nur etwa 700 sichere Fälle)? Oder erst in Stufe 3
   als Rechner (TP-Wert), mit den Daten nur als Prüfung?
3. **Umkämpft:** Soll ein Objective schon als bestritten gelten, wenn ≥ 3 Gegner in der Minute davor oder danach
   an der Grube standen? 40 % der „freien“ sind so.
4. **Buch 17, Teil A:** Atakhan streichen, Patch „16.17–16.19“ statt „16.19“, Larven je Stück. Soll ich das im
   Buch ändern? Es ist nicht meine Datei, deshalb habe ich es nicht getan.
