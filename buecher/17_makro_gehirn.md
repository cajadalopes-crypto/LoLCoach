# Buch 17 – Das Makro-Gehirn (Claude, Chat, 30.09.2026)

**Auftrag von Carlos (30.09.2026, 14:23–14:56, wörtlich im Kern):**
- Der Coach soll **alles Wissen**, das in den High-Elo-Partien steckt, herausziehen und in Echtzeit anwenden.
- Er soll Makro auf Challenger-Niveau beherrschen.
- **Makro ist alles außerhalb von Carlos' gelockter Kamera:** Minimap, Mitspieler, die ganze restliche Karte,
  Timer, Wellen, Sicht, TP, Roams.
- Makro-Entscheidungen „von den kleinsten bis zu den größten“, z. B. ein Ward fünf Meter weiter, weil es zu dieser
  Zeit Sinn ergibt, oder „in den nächsten 40 s die Lane pushen und hier einen Ward setzen“.
- **Mikro** (Kampf, Kombos, Positionieren im Bild) macht Carlos selbst.
- Carlos' Beispiele sind **Beispiele, keine Grenze**.

**Harte Regel: Woher das Können kommt** (Carlos, 30.09.2026 17:48)
- **Jedes Entscheidungswissen** kommt nur aus den High-Elo-Partien (Master bis Challenger) und aus recherchierten
  Regeln, die an diesen Daten geprüft sind. Entscheidungswissen heißt: was richtig ist, Werte, Schwellen, Regeln.
- **Carlos' eigene Partien** sind keine echten Spielbedingungen: schwache Gegner, und er spielt absichtlich, wie er
  will. Aus ihnen wird **kein** Entscheidungswissen gezogen, keine Schwelle geeicht und keine Regel abgeleitet.
- **Carlos' Partien dienen nur**
  - der Wahrnehmung: Minimap, HUD, Bildschirm, Bilder;
  - der Verdrahtung: spricht der Coach, wann, widerspricht er sich, Latenz;
  - der Fehlersuche: z. B. ein Elixier empfohlen, zwei Sejuanis verwechselt.

Teil A sagt, was die Partien hergeben. Teil B ist das Makro-Pflichtenheft (jede Entscheidung, klein bis groß).
Teil C sagt, wie beides in den Coach kommt und wie gemessen wird.

---

## Teil A – Was die High-Elo-Partien hergeben (vollständiger Katalog)

**Datenbestand** (`daten/riot/`):
- Partien aus EUW, Solo-Queue (420), Master bis Challenger, **Patch 16.17–16.19**. Stand 15:45: 2792 gültig, darunter
  5553 Top-Spieler-Partien, davon 1718 Challenger. Der Download läuft weiter. Die Liga je Spieler ist zugeordnet
  (Phase 0, `buecher/challenger/phase0_bericht.md`).
- **Je Partie:**
  - Match: je Spieler Champion, Rolle, Beschwörerzauber, Runen, Items, Ergebnis;
  - 127 Kennzahlen („challenges“), 13 Ping-Arten, Zauber- und Beschwörerzauber-Einsätze;
  - Team-Objectives: Drache, Larven (jede Larve ein eigenes Ereignis), Herold, Baron, Türme, Inhibitoren. Atakhan
    kommt in 16.17–16.19 nicht vor, der Wert ist überall 0.
- **Zeitleiste:**
  - jede Minute je Spieler: Position, Gold, XP, Level, CS, Jungle-CS, Werte;
  - alle Ereignisse mit Zeitstempel: Käufe, Verkäufe, Verbrauch, Skill- und Level-Aufstiege, Wards gesetzt und
    zerstört (Typ, ohne Ort), Kills (Ort, Täter, Opfer, Helfer, Schaden je Fähigkeit), Mehrfach-Kills und Aces
    (Ort), Gebäude (Ort, Lane, Typ), Platten (Ort), Epische Monster (Typ, Team, Ort, oft Helfer), Seelen,
    Kopfgelder, Spielende.

**Abgeleitet** (in allen Partien rechenbar):
- **Backs:** aus Käufen und Basis-Positionen.
- **Todes- und Respawn-Zeiten:** aus Kills und Level.
- **Kämpfe:** Kills, die zeitlich und räumlich zusammenliegen.
- **Umkämpfte Objectives:** Kills am Objective innerhalb von ±30 s.
- **Ganks:** Jungler an einem Lane-Kill beteiligt.
- **TP-Einsätze:**
  - Die Anzahl je Partie ist exakt.
  - Wann und wohin ist nur bei etwa 3 % sichtbar (Phase 0: gut 700 sichere Fälle), weil eine Minute fast jeden
    Weg erlaubt.
  - **Entschieden:** TP wird ein Rechner (Stufe 3). Die Daten dienen als Prüfung und für Grundwerte, TP ist keine
    gelernte Aktion.
- **Split:** Abstand zum eigenen Team, dazu Gebäude-Schaden.
- **Gruppieren:** mehrere Spieler einer Seite im selben Kartenbereich.

Jede Zeile unten ist ein Muster, das aus den Partien gezogen wird. Jedes wird im Coach zu **Erkennung + Kommando
mit Warum** (Teil C).

### A1. Gegner-Jungler lesen und vorhersagen
- Startseite und erste Runde: Wo steht ein Jungler um 1:30, 2:00, 2:30, 3:00 und 3:30, je nach Startseite? Daraus
  folgt die wahrscheinliche erste Gank-Seite.
- **Gank-Fenster je Lane:** Minute, Seite und die Lage davor (Lane gepusht, Laner mit wenig Leben, Level 3/4/6).
  Sichtbar sind nur Ganks mit Kill; die Jungler-Nähe zur Lane kommt aus den Positionen.
- **Folgeort:** Wo ist ein Jungler 60 s nach einem Gank, Kill, Krabbler, Buff oder Back?
- Krabbler-Zeit und Kämpfe um den Krabbler; Invades (wann, wie oft, gegen wen); Buff-Diebstahl.
- Wann Jungler vor Drache, Larven, Herold und Baron zurück in die Basis gehen, wann sie zum Objective laufen und
  wann sie auf der Gegenseite spielen.
- **Jungler-Karte (Modell):** aus „zuletzt gesehen“ + Zeit + Spielstand eine Wahrscheinlichkeit für jeden
  Kartenbereich.

### A2. Gefahr außerhalb des Bildes (Warnungen)
- **Todes-Karte je Rolle und Spielphase** (Kill-Orte): Wo sterben Top-Laner in Minute 2–6, 7–14, 15–25 und 25+?
- **Lagen, die tödlich enden:**
  - allein tief in der Lane;
  - X Gegner seit Y s unsichtbar;
  - „gefangen“: Tod ohne Mitspieler in der Nähe;
  - Tode beim Splitten nach Minute 25;
  - Dives unter dem eigenen und dem gegnerischen Turm.
- **Fehlende Gegner:** Wohin gehen Mid, Support und Jungler, wenn sie aus der Lane verschwinden? Belege sind Kills
  in fremden Lanes nach Minute.
- **Gegner-Spikes:** fertiges Item (Kaufzeitpunkt), Level 6, dazu Kämpfe und Dives kurz danach.
- **Gefahr-Modell:** Wahrscheinlichkeit, in den nächsten 30 s bzw. 60 s zu sterben, aus Position, Minute, fehlenden
  Gegnern, Leben (sofern bekannt) und Gold-Abstand.

### A3. Lane-Druck, Wellen-Folgen, Lane-Gegner
- **Platten:** wann sie fallen, wer sie nimmt (Laner, Herold, Larven), was sie an Siegchance bringen; Türme vor
  dem Plattenende.
- **Back-Fenster des Lane-Gegners:** Gold und Minute, in der Top-Laner typischerweise backen. Daraus folgt: „Sein
  Back ist jetzt fällig, danach hast du X s.“
- **Lane verlassen:** wann High-Elo-Top-Laner die Lane verlassen, wohin, und was es sie an CS und XP kostet.
- **Soll-Werte je Minute** für CS, Level und Gold; Vorsprung und Rückstand, und was Gewinner bei welchem Rückstand
  anders machen (umspielen statt duellieren).
- „Unsichtbare Backs“ (Kennzahl `unseenRecalls`).

### A4. Zurück in die Basis (Makro-Timing)
- Back mit wie viel Gold, in welcher Minute, nach welchem Ereignis (Crash, Kill, Platte, Objective).
- **Backs im Takt der Objectives:** Anteil der Backs 60–120 s vor Drache, Herold oder Baron, bei Gewinnern und
  Verlierern.
- Rückweg in die Lane: zu Fuß oder per TP (Sprung von der Basis in die Lane).
- Kontroll-Auge und Linse als Teil des Backs (Kauf-Ereignis).

### A5. TP
- **Einsätze je Partie und Phase:** früh, Mitte, spät (Beschwörerzauber-Einsätze).
- **Wofür:** zurück in die Lane; zu Kämpfen oder Objectives auf der anderen Seite (Sprung + Beteiligung weit weg);
  Türme verteidigen; flankieren im späten Spiel.
- **Wann ein TP den Kampf dreht:** Ausgang mit und ohne TP-Beteiligung, nach Minute, Objective, Anzahl und
  Gold-Abstand.
- **Gegner-TP:** Wie lange ist das Fenster nach seinem Einsatz, und was nutzen Gewinner darin?
- **TP-Wert (Modell):** Siegchance-Änderung durch TP jetzt, verglichen mit „bleiben“.

### A6. Objectives (Drache, Seele, Larven, Herold, Baron, Elder)
- **Zeitpunkt:** Sekunden nach dem Spawn; frei genommen oder umkämpft; Steals.
- **Wer dabei ist:** Helfer und Positionen, etwa ob der Top-Laner bei den ersten Drachen dabei ist, und wann.
- **Was vorher war:** Tote beim Gegner, Gold, Backs 60–120 s vorher, Positionen eine Minute vorher, Platten und
  Türme (Wellen-Ersatz).
- **Was nachher kommt:** Siegchance; Seelen-Rennen; Herold (wo eingesetzt, Türme damit); Baron-Buff (Türme und
  Inhibitoren in 3 min); Elder.
- **Bedingungen für einen sicheren Baron:** wie viele Gegner tot, Minute, Gold-Abstand.

### A7. Cross-Map und Tausch
- **Gleichzeitige Ereignisse** auf beiden Kartenseiten: Drache gegen Turm, Herold oder Larven.
- **Was Gewinner-Teams nehmen,** wenn sie ein Objective nicht bestreiten können, und wie viel Siegchance das rettet.

### A8. Kämpfe als Makro-Entscheidung
- **Wo und wann** Teamkämpfe passieren, nach welchem Anlass (Objective-Spawn, Item-Spike, Pick).
- **Wer gewinnt:** nach Überzahl, Gold, Level und Ort (am Objective, im Fluss, im gegnerischen Jungle).
- **Picks:** ein Gegner allein gefangen, und welches Objective danach folgt.
- **Umwandeln:** Was holen Gewinner nach einem gewonnenen Kampf (Turm, Objective, Reset)? Was kostet ein
  Kampf, der nicht umgewandelt wird?

### A9. Sicht (Zeitpunkte; Orte siehe Teil B)
- Wards je Minute und Rolle; Kontroll-Augen; Linse (Kaufzeitpunkt); zerstörte Wards.
- **Sicht vor Objectives:** Ward-Aktivität der Gewinner in den 90 s vor dem Objective, verglichen mit den
  Verlierern.
- **Sicht-Vorsprung** gegen den Lane-Gegner (`visionScoreAdvantageLaneOpponent`) und die Folge für Tode und Ganks.

### A10. Mitte und Spätphase: Seiten, Gruppe, Split, Schluss
- Wer ab Minute 14 auf welche Seite geht (Positionen); wann Teams gruppieren und nach welchem Ereignis.
- **Split:** wer splittet, was er nimmt, wann Split verliert (Tod beim Splitten, Objective auf der Gegenseite).
- Wellen und Seiten vor dem Baron; Inhibitor-Druck; Super-Vasallen.
- **Schluss:** nach einem Ace direkt auf den Nexus oder nicht; Zeit vom Ace bis zum Ende.
- **Throws:** verlorene Vorsprünge und was davor geschah.

### A11. Spielstand und Siegbedingung
- **Siegchance-Modell je Minute,** nur aus Merkmalen, die Carlos im Spiel sieht: Items → Gold, Level, Kills, CS,
  Türme, Drachen, Tote.
- **Wert jedes Ereignisses** je Minute in Siegchance-Punkten: Turm, Drache, Larven, Herold, Baron, Kill, Tod.
- **Team-Aufstellung** (Klassen) → Siegchance nach Spieldauer. Daraus folgt: „Ihr skaliert, nichts erzwingen“ oder
  „Ihr müsst jetzt spielen“.
- **Kopfgelder und Comeback:** wann das zurückliegende Team Objective-Kopfgelder holt.

### A12. Team und Kommunikation
- **Pings** (13 Arten): wann High-Elo-Spieler „Gegner fehlt“, „Sicht nötig“ und „auf dem Weg“ pingen. Der Coach
  sagt Carlos, **was er pingen soll**: „Ping Bot: Jungler auf dem Weg.“
- **Mitspieler-Zustand** (Tote, Respawn, Rückweg) als Go oder No-Go für Objectives.

### A13. Kaufen, nur als Makro-Teil
- Kontroll-Augen je Back, Linse-Zeitpunkt, Kauf-Kette je Gold, Stiefel je Gegnerteam, Elixiere nur am Ende.

### Gelernte Modelle (Überblick)
Sie decken alles ab, was wir nicht selbst benennen. Jedes wird an zurückgelegten Partien geprüft.

| Modell | Frage | Nutzung im Coach |
|---|---|---|
| Siegchance | Wie steht das Spiel? | Wert jeder Aktion, Siegbedingung |
| Challenger-Kompass | Wo ist ein High-Elo-Spieler in deiner Rolle in 60 s, in dieser Lage? | „Geh jetzt X“ mit Vergleich |
| Jungler-Karte | Wo ist der Gegner-Jungler jetzt? | Warnungen, Ward-Zeitpunkte, Plays |
| Gefahr | Wie wahrscheinlich stirbst du in 30 s bzw. 60 s? | Rückzug, Sicht zuerst |
| Objective | Wer nimmt das nächste Objective, wann? | Vorbereiten, Tausch |
| Kampf | Wer gewinnt diesen Kampf (Anzahl, Gold, Level, Ort)? | Nimm oder lass ihn, als Makro-Rahmen |
| TP-Wert | Bringt TP jetzt mehr als bleiben? | TP-Kommandos |

### Was nicht in den Partien steht (für niemanden)
- Wellenstände;
- genaue Laufwege zwischen den Minuten (nur eine Position je Minute);
- Ward-Orte;
- Nebel und Sicht;
- Ult- und Zauber-Abklingzeiten im Spiel;
- Ganks ohne Kill;
- Absichten.

Das füllen drei Dinge: der Coach liest die Minimap live (Wellen aller Lanes, eigene Wards, Gegner); Teil B mit
Challenger-Makro-Wissen (Ward-Orte je Minute, Wellenregeln, TP-Regeln); die Rechner (Ankunftszeiten, Wellenkosten,
Überzahl).

---

## Entscheidungen zu Phase 0 (Claude/Chat, 30.09.2026 16:00)

1. **Lane-Gegner in der Lage:** ja, wenn er höchstens 1200 neben dem Spieler steht. So ist es fast wie im Spiel:
   Carlos sieht ihn auf dem Bildschirm. Die Angabe wird als „nahe sichtbar“ markiert.
2. **TP:** Rechner in Stufe 3; die Daten liefern nur Prüfung und Grundwerte (siehe oben).
3. **Objective-Zustand, dreistufig:**
   - **frei;**
   - **bestritten:** ≥ 3 Gegner ≤ 3000 an der Grube, Position auf den Zeitpunkt des Objectives interpoliert, ohne
     Kill;
   - **umkämpft:** Kill ±30 s, ≤ 3000.
4. Buch 17 ist hiermit korrigiert: Patch, Atakhan, Larven, TP.

**Kein Silber/Gold-Vergleich** (Carlos, 30.09.2026 15:54). `werkzeuge/challenger/silber_download.py` bleibt
ungenutzt.

## Teil B – Makro-Pflichtenheft (Claude/Chat, 30.09.2026)

**Was hier steht:** jede Makro-Entscheidung, die ein Challenger trifft, von der kleinsten (welcher Busch, 3 s Umweg für
Info) bis zur größten (Baron, Spiel beenden).
- Makro ist alles außerhalb von Carlos' gelockter Kamera.
- Mikro (Trades, Kombos, Positionieren im Bild) ist nicht drin.

**Pflicht je Eintrag, vier Häkchen:**
1. **Erkannt:** Der Auslöser ist live erkennbar.
2. **Gerechnet:** Die Grundlage liefert eine Zahl oder eine Regel.
3. **Gesagt:** ein Kommando „Tu X, weil Y, danach Z“; „Warte“ ist ein Kommando.
4. **Getestet:** ein Szenario oder eine Prüfung an Daten.

**Abdeckung: 100 %.** Kein Eintrag bleibt ohne Häkchen.

**Grundlage:**
- **D:** Daten und Modelle aus Stufe 2 (Siegchance, Aktionswert, Policy, Jungler-Karte, Gefahr, Ketten).
- **R:** Challenger-Regel. Recherchiert, mit Stand in `wissen/`, gegen D geprüft, wo möglich.
- **M:** live aus Minimap, HUD oder Live-API.
- **Re:** Rechner aus Stufe 3 (Ankunftszeiten, Wellenkosten, Überzahl, TP).

Zeiten und Zahlen, die mit dem Patch wechseln (Spawn-Timer, TP-Abklingzeit, Kanonenwellen), stehen nie im Code,
sondern in `wissen/` mit Stand.

### B1. Sicht und Information (die kleinsten Entscheidungen)

| Nr | Entscheidung | Auslöser | Grundlage | Beispiel-Kommando |
|---|---|---|---|---|
| S1 | Erster Trinket: **welcher Busch** | vor dem ersten Gank-Fenster, Startseite des Gegner-Junglers | D (Jungler-Karte), R | „Trinket in den Fluss-Busch, nicht in den Tri: Er hat unten begonnen und kommt über den Fluss.“ |
| S2 | Trinket **halten** statt sofort setzen | Gank-Fenster noch nicht offen | D, R | „Halte den Trinket bis 2:50, vorher kann er nicht da sein.“ |
| S3 | **Welle schieben, um warden zu können** | Ward nötig, Welle nicht gecrasht | M (Welle), Re | „Drück die Welle in den nächsten 20 s rein, dann Ward in den Tri. Sonst kostet dich der Ward Farm.“ |
| S4 | **Tiefer Ward** zum Jungler-Tracken (Raptoren, Krug, Buff-Eingang) | Welle drin, Lane-Gegner back oder tot, Jungler weit weg | D, M, R | „Aatrox ist back: 5 s rein, Ward an ihren Krug-Eingang, dann raus.“ |
| S5 | **Umweg für Info** (Eingang, Busch auf dem Weg) | Rückweg oder Rotation, Jungler unbekannt | D, Re | „Lauf durch ihren Raptoren-Eingang, 3 s Umweg: dann weißt du, ob er oben ist.“ |
| S6 | Kontroll-Auge: **kaufen und wohin** | jeder Back mit Gold, Auge nicht gesetzt | D (Käufe), R | „Kontroll-Auge mitnehmen, in den Fluss-Busch: Er gankt dich zweimal von dort.“ |
| S7 | **Linse** statt gelbem Trinket | Rolle, Minute, Objective-Phase | D (Kauf-Zeitpunkte), R | „Tausch beim Back auf Linse: Herold kommt, du räumst die Grube.“ |
| S8 | **Sicht vor dem Objective** (Eingänge, Grube) | 90–60 s vor Spawn | D (Ketten), R | „Drache in 75 s: Ward den Eingang auf ihrer Seite, dann Welle.“ |
| S9 | **Räumen vor dem Objective** | 45–30 s vor Spawn, Linse bereit | R | „Linse jetzt an der Grube: Ihr Ward muss weg, bevor ihr startet.“ |
| S10 | **Flanken-Ward** vor dem Split | Split geplant, Seite ohne Sicht | D (Split-Tode), R | „Bevor du Bot drückst: Ward an ihren Blau-Eingang, sonst stirbst du ohne Warnung.“ |
| S11 | **Kein Face-Check** | unbekannter Busch, ≥ 2 Gegner unbekannt | D (Gefahr), M | „Nicht in den Busch: drei fehlen. Erst Ward oder Linse.“ |
| S12 | **Sicht abgelaufen** oder zerstört | eigener Ward weg (Minimap) | M, R | „Dein Tri-Ward ist weg: neu setzen, bevor du vorgehst.“ |
| S13 | **Trinket-Ladungen nicht verfallen lassen** | Ladungen voll | M (HUD), R | „Zwei Ladungen voll: einen Ward jetzt in den Fluss.“ |
| S14 | **Ward für einen Mitspieler** oder ein Objective auf seiner Seite | Mitspieler oder Objective ohne Sicht | M, R | „Setz den Ward an die Larven: Vi geht gleich hin.“ |

### B2. Gegner-Jungler, fehlende Gegner, Warnungen

| Nr | Entscheidung | Auslöser | Grundlage | Beispiel-Kommando |
|---|---|---|---|---|
| J1 | **Startseite** ableiten | erste Sichtung, Kills, Scoreboard-CS | D (Jungler-Karte) | „Er ist um 1:40 unten gesehen worden: Blau-Start, erster Gank eher Bot.“ |
| J2 | **Gank-Fenster** vorwarnen | Minute, Seite, Welle vorn | D (Gank-Muster), M | „Gank-Fenster jetzt: Welle zurückziehen lassen, bis er gesehen wird.“ |
| J3 | **Freifenster** nutzen | Jungler auf der anderen Seite gesehen | D, Re | „Er ist Bot: 35 s Ruhe. Welle rein, Platte holen.“ |
| J4 | **Unbekannt und du weit vorn** | Jungler > 30 s nicht gesehen | D (Gefahr), M | „Er ist seit 40 s weg und du stehst tief: zurück zur Mitte der Lane.“ |
| J5 | **Mehrere fehlen** (MIA) | ≥ 2 Gegner unbekannt, Minute, Ort | D (Gefahr), M | „Mid und Jungler fehlen seit 15 s: zurück zum Turm, Bot anpingen.“ |
| J6 | **Lane-Gegner fehlt** (Roam oder Back) | Lane-Gegner nicht mehr sichtbar | M, D | „Aatrox ist weg: Ping Mid. Du crashst die Welle und holst die Platte.“ |
| J7 | **Gegner-TP genutzt** | TP-Sprung gesehen oder Chat | M, R | „Tryndamere hat TP benutzt: Für Minuten kein Flank von ihm. Jetzt kannst du Bot helfen.“ |
| J8 | **Gegner-Flash weg** | Flash-Timer | M | „Brand ohne Flash für 4 min: Ping Mid, Kill-Fenster für euren Jungler.“ |
| J9 | **Globale oder lange Ults** der Gegner ab Level 6 | Champion-Wissen, Level | R, M | „Pantheon ist Level 6: Sein R kann auf dich fallen, nicht tief ohne Sicht.“ |
| J10 | **Gegner-Spike** (Level 6, Item fertig) | Scoreboard und Level | D, M | „Tryndamere hat sein erstes Item: Jetzt keinen Seitenkampf allein.“ |
| J11 | **Frühes Invade** | Level 1–2, Gegner fehlen am Start | D, R | „Vier von ihnen fehlen: Bleib am Busch bei eurem Buff, bis Vi ihn hat.“ |
| J12 | **Konter-Gank** | eigener Jungler bei dir, Gegner-Jungler in der Nähe | Re, D (Kampf) | „Vi ist bei dir, ihr Jungler kommt: Bleib, dann 2 gegen 2 mit Level-Vorteil.“ |
| J13 | **Krabbler** | Krabbler-Zeit, Jungler beider Seiten | D, Re | „Krabbler oben: Welle rein, dann hin. Mit dir gewinnt Vi den Fluss.“ |
| J14 | **Dive-Gefahr** | 2–3 Gegner nahe, Welle klein, wenig Leben | D (Gefahr), Re | „Drei kommen und deine Welle ist weg: Raus hinter den Turm, nicht ins Tor stellen.“ |

### B3. Wellen (live aus der Minimap, alle Lanes)

| Nr | Entscheidung | Auslöser | Grundlage | Beispiel-Kommando |
|---|---|---|---|---|
| W1 | **Freeze oder Push** | Wellenstand, Jungler, Objective, Back-Plan | M, R, D | „Freeze an deinem Turm: Er ist allein vorn, Vi kommt in 20 s.“ |
| W2 | **Langsam aufbauen, dann crashen** vor dem Back | Back geplant, nächste Kanone | M, Re | „Zwei Wellen aufbauen, mit der Kanone crashen, dann Back: Du verlierst nichts.“ |
| W3 | **Crash → Back** | Welle gecrasht, Gold, Leben | M, D (Back) | „Welle ist drin: Jetzt Back, Kette …“ |
| W4 | **Crash → Fenster** nutzen (Roam, Ward, Invade) | Welle drin, sie prallt in X s zurück | M, Re | „Deine Welle prallt in 25 s zurück: 25 s für Ward oder Mid.“ |
| W5 | **Warten auf die zurückprallende Welle** | Welle läuft zu dir | M, Re | „Warte 10 s am Turm: Die Welle kommt zu dir, dann erst TP.“ |
| W6 | **Welle vor dem Objective** | 90–60 s vor Spawn | D (Ketten), M | „Drache in 80 s: Welle jetzt rein, damit du frei bist.“ |
| W7 | **Welle vor TP oder Roam crashen** | TP oder Roam geplant | M, Re | „Erst crashen (6 s), dann TP, sonst frisst ihr Turm 8 Vasallen.“ |
| W8 | **Welle retten oder Objective** | Welle am eigenen Turm, Objective gleichzeitig | Re, D (Wert) | „Lass die Welle, der Drache ist mehr wert: 90 Gold gegen 5 % Siegchance.“ |
| W9 | **Nicht zu tief drücken** | Jungler unbekannt, kein Back geplant | D (Gefahr), M | „Stopp an ihrem Turm: Er ist unbekannt, und du willst nicht backen.“ |
| W10 | **Nach Kill oder Tod des Lane-Gegners** | Gegner tot | D (Umwandlung), M | „Er ist 20 s tot: Welle crashen, zwei Platten, dann Back.“ |
| W11 | **Seitenwelle holen**, Mitte und Spätphase | Welle kommt, Sicht, Gegner-Positionen | D (Gefahr), M | „Bot-Welle holen, nur bis zur Flussmitte: Drei sind unbekannt.“ |
| W12 | **Große Welle stapeln** für Turm oder Dive | Turm schwach, Gegner back | M, Re | „Zwei Wellen stapeln, dann mit Vi auf den Turm.“ |
| W13 | **Welle aufgeben** | Kampf oder Objective wichtiger | Re, D | „Lass die Welle und geh: Das Objective ist in 20 s.“ |
| W14 | **Wellen der anderen Lanes** für Prio-Aussagen | Minimap, Bot und Mid | M | „Bot-Welle läuft zu ihnen: Bot kann nicht zum Drachen, kein Drache jetzt.“ |

### B4. Back und Einkauf (Makro-Teil)

| Nr | Entscheidung | Auslöser | Grundlage | Beispiel-Kommando |
|---|---|---|---|---|
| B1 | **Wann Back** | Crash, Kill, Gold für Spike, Leben | D (Back-Muster, Q), M | „Back jetzt: Welle drin, 1300 Gold, das ist Bamis und Kettenweste.“ |
| B2 | **Back im Takt des Objectives** | 120–60 s vor Spawn | D (Ketten) | „Back jetzt, dann bist du 20 s vor dem Drachen voll da.“ |
| B3 | **Back verschieben** | Welle kommt, Gegner tot, Objective jetzt | D (Q), M | „Noch nicht back: Er ist tot, erst die zwei Platten.“ |
| B4 | **Back wegen Leben oder Mana** | Leben niedrig, Gegner nah | D (Gefahr) | „Mit 25 % Leben in dieses Fenster nicht: Back.“ |
| B5 | **Back zusammen mit dem Lane-Gegner** | Gegner geht back | M, R | „Er backt: Du auch, sofort, dann verliert keiner eine Welle.“ |
| B6 | **Rückweg: zu Fuß oder TP** | Wellengröße, Turm in Gefahr, TP später nötig | Re, D | „Zu Fuß zurück, halte den TP: Drache in 2 min.“ |
| B7 | **Kauf-Kette** mit ganzem Gold, Kontroll-Auge und Stiefeln | im Brunnen oder tot | D (Käufe), R | „Kauf Bamis, Kettenweste und Kontroll-Auge, dann Top.“ |
| B8 | **Nach Respawn:** Kauf und Ziel | Respawn | D, Re | „Du lebst in 10 s: Kette …, dann direkt zum Fluss oben.“ |
| B9 | **Sonderregeln je Champion** (etwa Ornn kauft ohne Back) | Champion | R (Lexikon) | „Kauf direkt in der Lane, kein Back nötig.“ |

### B5. TP (Rechner)

| Nr | Entscheidung | Auslöser | Grundlage | Beispiel-Kommando |
|---|---|---|---|---|
| T1 | **TP zurück in die Lane** oder aufheben | nach dem Back: Welle groß, Platten, Turm in Gefahr, Objective bald | Re, D | „TP zurück: 2 Wellen laufen auf deinen Turm. Drache ist erst in 3 min.“ |
| T2 | **TP zu Kampf oder Objective** auf der anderen Seite | Kampf oder Objective in ≤ 30 s, Ankunft, Überzahl, Welle | Re, D (Kampf, Q) | „Welle rein (6 s), dann TP Bot auf den Ward: 5 gegen 4, ihr Top hat kein TP.“ |
| T3 | **TP halten** für das Objective | Objective in 60–120 s, TP bereit | Re, D | „Nicht TP für die Lane: Du brauchst ihn in 80 s am Drachen.“ |
| T4 | **TP-Flanke** in der Spätphase | Kampf geplant, Ward oder Vasall hinter dem Gegner | Re, R | „Wenn sie Baron anfangen: TP hinter sie auf den Ward im Busch.“ |
| T5 | **TP zur Verteidigung** | Turm fällt, Gegner zu zweit, du bist weit | Re | „TP auf den Mid-Turm: Sonst fällt er in 15 s.“ |
| T6 | **Konter-TP** | Gegner-Top TPt zu einem Kampf | M, Re | „Tryndamere TPt Bot: Du auch, sonst 4 gegen 5.“ |
| T7 | **TP-Ziel wählen** | sicherer Ward, Vasall oder Turm | Re, M | „TP auf den Vasallen hinten, nicht auf den Ward im Fluss: Dort steht Leona.“ |
| T8 | **Nicht TPen** (zu spät, verloren, Welle zu teuer) | Kampf endet vor Ankunft, Unterzahl | Re, D | „Kein TP: Der Kampf ist vorbei, bevor du ankommst.“ |
| T9 | **TP-Stand** beider Tops in jeder Entscheidung | eigener TP (HUD), Gegner-TP (Timer) | M | „Du hast TP, er nicht: Jetzt ist dein Fenster für ein Bot-Play.“ |

### B6. Roams und Rotationen zu Fuß

| Nr | Entscheidung | Auslöser | Grundlage | Beispiel-Kommando |
|---|---|---|---|---|
| R1 | **Roam Mid** | Welle drin, Mid-Gegner schwach oder ohne Flash, Weg frei | Re, D (Q) | „Welle drin, Brand ohne Flash: Über den Fluss Mid, 12 s.“ |
| R2 | **Zum Fluss oder Krabbler** für den eigenen Jungler | Jungler dort, Prio | Re, D | „Vi geht zum Krabbler: Welle rein, dann hin.“ |
| R3 | **Zu den Larven oder zum Herold** | Objective oben, Prio | D (Ketten), Re | „Larven in 40 s: Welle rein, dann an den Eingang.“ |
| R4 | **Zum Drachen zu Fuß** | Prio, Zeit reicht | Re, D | „Zu Fuß schaffst du es in 38 s. Der Drache startet in 45 s: los.“ |
| R5 | **Roam abbrechen** | Ziel weg, Welle kommt, Gefahr | M, Re | „Abbrechen: Brand ist zurück, deine Welle läuft zu dir.“ |
| R6 | **Rotation nach Turmverlust** | eigener oder gegnerischer Außenturm fällt | D (Rotation) | „Dein Top-Turm ist weg: Mid-Welle mit Sylas, dann Herold.“ |
| R7 | **Weg wählen** | Ziel, bekannte Gegner, Sicht | D (Todes-Karte), Re | „Durch euren Jungle, nicht durch den Fluss: Dort fehlen zwei.“ |
| R8 | **Roam-Kosten** gegen Nutzen | CS- und XP-Verlust gegen Gewinn | Re, D (Q) | „Nicht roamen: Du verlierst 2 Wellen, Mid gewinnt nur einen Flash.“ |
| R9 | **Mit dem Jungler invaden** | Gegner-Jungler auf der anderen Seite | D, Re | „Er ist Bot: Mit Vi in ihren oberen Jungle, Krug und Raptoren.“ |
| R10 | **Gegner-Camp nehmen** (Top) | Welle drin, sicher, Camp da | R, M | „Ihre Krug sind da und die Welle ist drin: 10 s, 100 Gold, dann zurück.“ |

### B7. Objectives

| Nr | Entscheidung | Auslöser | Grundlage | Beispiel-Kommando |
|---|---|---|---|---|
| O1 | **Drache: bestreiten, geben oder tauschen** | Spawn, Anzahl, Prio, Ankunft, Siegchance | D (Q, Objective), Re | „Gib den Drachen: Ihr seid 3 gegen 5 und spät dran. Nimm dafür Top-Turm.“ |
| O2 | **Larven** | Spawn, Seite, Prio | D, Re | „Larven mit Vi: Du hast Prio, ihr Top ist back.“ |
| O3 | **Herold: nehmen und wo einsetzen** | Spawn; danach Ziel-Turm | D (Herold-Türme), R | „Herold in Mid einsetzen: Der Turm hat nur 40 %.“ |
| O4 | **Baron: Bedingungen** | Tote, Sicht, Wellen, Minute | D (Q, Ketten) | „Zwei von ihnen 30 s tot, Seitenwellen drücken: Baron jetzt.“ |
| O5 | **Baron abbrechen** | Gegner kommen, Leben, Smite | Re, M | „Baron abbrechen: Vier kommen, er hat noch 40 %.“ |
| O6 | **Elder oder Seele:** alles darauf | Seele oder Elder offen | D, R | „Seelen-Drache: Alles dahin, das entscheidet.“ |
| O7 | **Setup-Kette 90/60/30 s** | Timer | D (Ketten), R | „90 s: Welle. 60 s: Back. 30 s: Sicht. Dann Grube.“ |
| O8 | **Steal-Gefahr** | Gegner-Jungler nah, Smite | M, R | „Nicht unter 1500 kloppen ohne Vi: Ihr Jungler lauert.“ |
| O9 | **Nach dem Objective:** nächstes Ziel | Objective genommen | D (Umwandlung) | „Drache drin: Mit Gruppe auf ihren Bot-Turm, 22 s, bis einer kommt.“ |
| O10 | **Cross-Map-Tausch** | Gegner am Objective, ihr zu spät | D (Tausch) | „Sie sind am Drachen: Top-Turm und Larven, das ist mehr wert.“ |
| O11 | **Aufgeben und sicher zurück** | Unterzahl, zu spät | D (Gefahr) | „Zu spät, nicht reinlaufen: Welle holen, nächster Drache.“ |
| O12 | **Objective-Kopfgeld** (Comeback) | Kopfgeld aktiv | D, M | „Ihr habt Kopfgeld auf dem Drachen: Das ist euer Weg zurück.“ |

### B8. Kämpfe als Makro (ob und wann, nicht wie)

| Nr | Entscheidung | Auslöser | Grundlage | Beispiel-Kommando |
|---|---|---|---|---|
| K1 | **Kampf annehmen oder ablehnen** | Anzahl, Gold, Level, Ort, Spikes, Tote | D (Kampf, Q) | „Nicht kämpfen: 4 gegen 5, Katarina lebt in 5 s.“ |
| K2 | **Warten auf den Mitspieler** | Respawn oder Ankunft in X s | Re | „Warte 8 s auf Vi, dann 5 gegen 4.“ |
| K3 | **Zum Kampf laufen oder nicht** | Ankunft gegen Kampfdauer | Re | „Nicht hinlaufen: Du bist in 25 s da, der Kampf dauert 10.“ |
| K4 | **Nach dem Sieg: umwandeln** | Kampf gewonnen, Tote | D (Umwandlung) | „Drei tot: Baron jetzt, danach Mid-Inhibitor.“ |
| K5 | **Nach der Niederlage: retten** | Kampf verloren | D, M | „Ihr habt verloren: Welle am Mid-Turm halten, nicht nachlaufen.“ |
| K6 | **Pick-Chance melden** | Gegner allein gesehen | M, D | „Ezreal allein Bot-Seite: Ping und mit Vi hin, 15 s.“ |
| K7 | **Nicht allein sterben** | Split, Info fehlt, Minute (lange Todeszeit) | D (Gefahr, Todes-Kosten) | „Minute 28, 40 s Todeszeit: Nicht allein tiefer als Flussmitte.“ |

### B9. Mitte und Spätphase: Seiten, Gruppe, Split, Schluss

| Nr | Entscheidung | Auslöser | Grundlage | Beispiel-Kommando |
|---|---|---|---|---|
| M1 | **Lane-Zuordnung** nach dem Plattenende oder Türmen | 14:00, Türme | D (Rotation) | „Plattenende: Du nimmst Bot-Seite, ADC geht Mid.“ |
| M2 | **Split:** ob, welche Seite, wie tief | Siegbedingung, Sicht, TP, Gegner-Positionen | D (Split, Gefahr, Q) | „Split Bot bis zu ihrem Turm, nicht weiter: TP bereit für Baron.“ |
| M3 | **Split verlassen** | Objective in 45 s, Team kämpft | D, Re | „Split abbrechen: Baron in 45 s, lauf jetzt.“ |
| M4 | **Gruppe Mid** | Siegbedingung, Spikes, Wellen | D | „Zu viert Mid, du bleibst Seite: Das zieht zwei zu dir.“ |
| M5 | **1-3-1 oder 1-4** | Team-Aufstellung | D, R | „Ihr seid stärker verteilt: 1-3-1, du Top.“ |
| M6 | **Seitenwellen vor Baron oder Drache** | 60 s vor Spawn | D (Ketten), M | „Beide Seitenwellen drücken, dann Baron.“ |
| M7 | **Inhibitor-Druck** | Inhibitor offen, Respawn-Timer | D, M | „Ihr Bot-Inhibitor ist weg: Bot-Seite halten, die Super-Vasallen machen Druck.“ |
| M8 | **Spiel beenden** | Ace oder viele Tote, Nexus offen, nicht unter R1 | D (Schluss), Re | „Drei tot, 30 s: Nexus jetzt. Per TP, wenn bereit.“ |
| M9 | **Basis verteidigen** | Gegner mit Baron oder Super-Vasallen | D, M | „Nicht raus: Wellen im Tor clearen, warten auf ihren Fehler.“ |
| M10 | **Todes-Kosten beachten** | Minute, Todeszeit, Objective offen | D (Todes-Kosten) | „Ein Tod jetzt kostet Baron und Inhibitor: sicher spielen.“ |

### B10. Spielstand und Siegbedingung

| Nr | Entscheidung | Auslöser | Grundlage | Beispiel-Kommando |
|---|---|---|---|---|
| V1 | **Siegbedingung** ansagen und wechseln | Team-Aufstellung, Spielstand, Minute | D (Siegchance je Dauer) | „Ihr skaliert besser: nichts erzwingen vor Minute 25.“ |
| V2 | **Vorsprung umwandeln** | Siegchance hoch | D (Q) | „Ihr seid 70 % vorne: Objectives, keine Kämpfe ohne Grund.“ |
| V3 | **Rückstand spielen** | Siegchance niedrig | D (Q) | „Hinten: Wellen halten, Sicht, auf ihren Fehler warten.“ |
| V4 | **Eigenes Spike-Fenster** | Items oder Level des eigenen Teams | D | „Euer Spike ist jetzt: In den nächsten 2 min Drache erzwingen.“ |
| V5 | **Gegner-Spike abwarten** | Items oder Level der Gegner | D | „Ihr Spike ist jetzt: Nicht kämpfen, Wellen und Sicht.“ |

### B11. Team und Kommunikation (Carlos pingt, der Coach sagt, was)

| Nr | Entscheidung | Auslöser | Grundlage | Beispiel-Kommando |
|---|---|---|---|---|
| P1 | **Ping-Vorschlag** | Jungler oder MIA-Info für andere Lanes | M, D | „Ping Bot: Jungler auf dem Weg.“ |
| P2 | **Mitspieler Go/No-Go** | Leben, Flash, Ult der Mitspieler (HUD) | M | „Corki ohne Flash, 30 %: Drache erst nach seinem Back.“ |
| P3 | **Hilfe für einen Mitspieler** | Mitspieler angegriffen, Ankunft, Überzahl | Re, D | „Vi kämpft oben: Du bist in 4 s da, 2 gegen 1, geh.“ |
| P4 | **Mitspieler tot** | Tote im eigenen Team | D (Gefahr, Objective) | „Zwei von euch tot: Kein Objective, sicher halten.“ |

### B12. Warten mit Grund und Zeitfenster

| Nr | Entscheidung | Auslöser | Grundlage | Beispiel-Kommando |
|---|---|---|---|---|
| Z1 | **Warte X s** auf Welle, Respawn, TP oder Sicht | ein Grund liegt vor, der bald wegfällt | Re, D | „Warte 10 s, dann …“ |
| Z2 | **Fenster ansagen** | Gegner tot oder back, Jungler weit weg | Re, D | „Du hast 30 s: zwei Platten, dann Back.“ |
| Z3 | **Nichts tun ist richtig** (Klarheit „unklar“) | keine klare Option | D (Klarheit) | „Bleib an der Welle, bis Vi auftaucht: Ohne ihn ist jede Seite ein Risiko.“ |

### Was der Coach dafür live sehen muss (Stufe 3 und 4 prüfen jedes)

- **Minimap:**
  - alle sichtbaren Champions mit Team-Ring;
  - eigene Wards;
  - Vasallen-Wellen **aller** Lanes;
  - Türme, Objective-Symbole, TP-Sprünge.
- **HUD:** Leben, Ult und Beschwörerzauber der Mitspieler; eigene Q, W, E, R, D, F; Trinket-Ladungen.
- **Live-API:**
  - Items, Level, KDA und CS aller zehn (Scoreboard);
  - Ereignisse, Uhr, eigenes Gold, eigene Beschwörerzauber, Kontroll-Auge im Inventar.
- **Chat:** Flash- und TP-Pings.

**Fehlt noch:** Wellen aller Lanes (heute nur die eigene), Trinket-Ladungen, zuverlässiger TP-Stand. Das kommt in
Stufe 3.

**Zahl:** 111 Entscheidungen in 12 Bereichen. Neue kommen dazu, wenn Carlos, die Daten oder die Recherche eine
finden; gestrichen wird keine.


## Entscheidungen zu Stufe 2 (Claude/Chat, 30.09.2026 17:45)

1. **Keine Gegner-Items und -Level als Merkmale.** Live zeigt die API sie nur so, wie sie zuletzt gesehen wurden.
   Die Modelle werden ohne sie trainiert (Siegchance 0,163, schlägt den Gold-Abstand weiter).
2. **Back wird nur mit Grund gesagt.** Back steht nur dann im Kommando, wenn das Modell Back sagt **und** ein Grund
   aus Regel oder Rechner vorliegt: Welle gecrasht, Leben niedrig, Gold für ein Spike-Bauteil, Objective-Takt oder
   der Lane-Gegner geht selbst zurück. Hintergrund: Back ist in den Daten überbewertet; wer beim Recall stirbt, ist
   nicht erkennbar.
3. **Nach einem Ace entscheidet das Modell in der Lage;** der Rechner prüft die Wege gegen die Respawns. Reicht die
   Zeit bis Inhibitor oder Nexus, heißt es „Spiel schließen“, sonst Baron.
4. **Klarheit im Spiel (Stufe 4):**
   - klar: Kommando;
   - geteilt: zwei Optionen;
   - **unklar: das, was High-Elo hier am häufigsten tut (Policy), plus Regeln und Rechner.** Nie Schweigen.

## Teil C – Roadmap (festgelegt mit Carlos, 30.09.2026 15:15)

Jede Stufe hat ein Tor. Die nächste beginnt erst, wenn das Tor erreicht ist. Die Entwicklung kostet 0 $ Guthaben
(Sparprotokoll).

| Stufe | Auftrag | Was passiert | Tor |
|---|---|---|---|
| 0a | 028 | Eine Stimme: Widersprüche, Füllsätze, Kauf-Fehler, Carlos' Korrekturen, Spiegel-Champions, Review raus, Guthaben-Sperre | Widerspruch ≤ 1 je Partie, Füllsätze ≤ 5 %, Sicherheit 0 |
| 0b | 029 | Phase 0: Datenprüfung, Liga je Spieler, geprüfte Ableitungen, 10 Entscheidungsmomente zum Lesen | Carlos hält die 10 Momente für plausibel |
| 0c | Chat | Teil B: Makro-Pflichtenheft, jede Makro-Entscheidung von klein bis groß | Carlos segnet die Übersicht ab |
| 1 | 030 | Datenbasis: alle Partien → Entscheidungsmomente (Lage nur Wissbares → Aktion → Folge 30/60/120 s + Sieg) | Zahlen je Rolle und Bereich, Stichproben stimmig |
| 2 | 031 | Modelle: Siegchance, Aktionswert, Challenger-Policy, Jungler-Karte, Gefahr, TP-Wert, Konsens; lesbares Challenger-Handbuch | An zurückgelegten Partien: Siegchance kalibriert, Entscheider schlägt „immer farmen“ und den heutigen Kern klar |
| 3a | 032 | Rechner und Regeln für alle 111 Entscheidungen aus Teil B: TP-, Roam-, Objective- und Wellen-Rechner, Zeitfenster, Rückwärtsplanung, recherchierte Regeln (Ward-Orte und -Zeiten usw.); läuft parallel zu 028 | Je Entscheidung gerechnet, gesagt und getestet: 111/111 |
| 3b | 033 | Wahrnehmung, nach 028: Wellen aller Lanes aus der Minimap, Trinket-Ladungen, TP-Stand (eigener und Gegner) | „Erkannt“ 111/111 |
| 4 | 034 | Einbau: Entscheider im Kern (jede Sekunde), Claude nur Sprache, Kommando „Tu X, weil Y, danach Z“, Warten als Kommando; der alte Kern entscheidet nicht mehr, er bleibt nur als Sicherheits-Sperre | **Können:** Challenger-Treue an zurückgelegten High-Elo-Partien. **Verdrahtung** an Carlos' Aufnahmen: Wahrnehmung, Lücke, Widerspruch, Latenz |
| 5 | 035 | Abnahme: volle Messung per Abo | „TOR ERREICHT“, danach entscheidet Carlos über eine Partie |

**Danach:**
- Carlos' Notizen werden Szenarien und Korrekturen.
- Neuer Patch: neue Partien laden, Modelle neu trainieren.
