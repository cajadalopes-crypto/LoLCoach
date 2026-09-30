# Buch 15 – Events und lebendige Arbeitspakete (30.09.2026)

Begriff von Carlos (29.09.2026): Jeder Satz, der eine Handlung verlangt, ist ein **Arbeitspaket**. Der Coach wirft es
nicht nur hin. Er **beobachtet es in Echtzeit** und sagt sofort, wenn es erledigt ist, abgebrochen werden muss oder
ein besseres Play auftaucht. Dann folgt direkt das nächste Paket mit Grund.

So entsteht ein ständiger Strom hochwertiger Anweisungen statt Füllsätzen. Das frühere Maß „nervt nicht“ hat genau
diesen Strom abgewürgt. Es ist abgelöst.

Ein Paket ist kein fester Satz. Es ist ein **laufendes Stück Rechnung**, das in jedem Takt neu bewertet wird.

## 0. Events: Erkennung, Erahnung, Abwägung (Carlos, 30.09.2026 00:06)

**Begriff im Projekt:** Ein **Event** ist alles, was im Spiel stattfindet oder gleich stattfinden kann. Der
Jungler-Kampf war nur ein Beispiel. Gemeint sind **alle denkbaren Events**. Der Coach denkt in drei Schritten, fast
in Echtzeit:

1. **Event-Erkennung:** Was passiert gerade? (API, Minimap, HUD, Chat und Unterschiede zwischen zwei Takten)
2. **Event-Erahnung:** Was passiert gleich, mit welcher Wahrscheinlichkeit und wann?
3. **Event-Abwägung:** An welchen Events könntest du teilnehmen, und was bringt am meisten? Das beste Play wird
   gesagt. Ist ein sichtbares Event nicht das beste, sagt er auch, **warum nicht**: „Du siehst den Kampf am Herold,
   wir crashen trotzdem erst die Welle: 7 Vasallen, und du wärst erst in 12 s dort.“

Aus der Abwägung entsteht das **Arbeitspaket** (Teil 1 bis 4), das dann lebt, bis ein neues Event es erledigt,
abbricht oder ersetzt.

### 0.1 Event-Katalog (offen, wächst mit jeder Aufnahme)

| Gruppe | Beispiele (erkannt ● / erahnt ◐) |
|---|---|
| **Kampf** | ● Mitspieler kämpft irgendwo (1 gegen 1, 2 gegen 2, Gank läuft, Teamkampf) · ◐ Kampf bahnt sich an (beide Teams laufen auf denselben Ort, Objective bald da) |
| **Tod / Respawn** | ● Gegner oder Mitspieler tot (API `isDead`) · ◐ bald zurück (`respawnTimer`) |
| **Zauber** | ● Flash, TP oder Ult eines Gegners verbraucht · ◐ kommt bald wieder |
| **Objective** | ● spawnt, wird angegriffen, genommen · ◐ Spawn bald, Gegner machen es gleich |
| **Struktur** | ● Turm niedrig, fällt, Platten fallen · ◐ Plattenzeit endet |
| **Welle** | ● crasht, Kanone, Freeze bricht, Welle läuft in deinen Turm · ◐ in N s am Turm |
| **Position** | ● Gegner gesehen, fehlt, roamt, backt, steht in deinem Jungle · ◐ Gank droht (Gefahr-Uhr), Jungler vermutlich auf Seite X |
| **Ressourcen** | ● Item- oder Level-Spike (du, Gegner), Gold für ein Item · ◐ Spike in N s |
| **Team** | ● Mitspieler backt, roamt, ist in Gefahr, wartet auf dich · ◐ braucht gleich Hilfe |
| **Zeit** | ● feste Zeiten (Plattenende, Spawns, Wellen-Takt) |

Jedes Event hat: **Typ · Ort · Beteiligte · Zeit oder ETA · Sicherheit (erkannt) bzw. Wahrscheinlichkeit
(erahnt)**.

### 0.2 Event-Erahnung

- **Beispiele:**
  - „Kampf am Drachen in ~20 s“: beide Jungler bewegen sich dorthin, der Drache spawnt, Bot-Prio ist unklar.
  - „Gank oben“: Jungler 40 s unsichtbar, zuletzt oben gesehen, deine Welle vorgeschoben.
  - „Lane-Gegner backt gleich“: wenig Leben oder viel Gold, Welle gerade gecrasht.
- **Wahrscheinlichkeit und Zeitpunkt** aus einfachen, prüfbaren Regeln, gemessen an den Aufnahmen. Eine
  Erahnung ist gut, wenn Events mit p ≥ 0,6 in ≥ 60 % der Fälle eintreten.
- **Erlaubt „lauern“ statt „back“,** wenn ein Kampf sehr wahrscheinlich ist und du dafür gut stehst.

### 0.3 Event-Abwägung

- **Je Event, an dem du teilnehmen kannst, ein Kandidat mit Wert in GE:**
  - Wert = Nutzen × Wahrscheinlichkeit − Risiko (`p_tod` × Todeskosten) − Opportunitätskosten (verlorene
    Vasallen, Platten, Zeit);
  - Machbarkeit: Ankunft vor dem Event, Leben, Mana, Abklingzeiten, R1.
- **Bestes Play:** der höchste Wert. Gewechselt wird nur mit Hysterese (Teil 5).
- **„Warum nicht“-Satz:** Ist ein auffälliges Event (sichtbarer Kampf, Objective) nicht das beste Play, sagt der
  Coach das einmal kurz mit dem entscheidenden Grund.
- **Liegen zwei Kandidaten knapp beieinander** (< Hysterese): Claude wägt ab und nennt beide Optionen mit Grund.
- **Echtzeit:**
  - Der Kern erkennt Events und rechnet die Kandidaten in jedem Takt.
  - Claude wird nur bei einem echten Wechsel oder einer knappen Wahl gefragt.
  - Abbrüche und Countdowns spricht der Kern sofort.

## 1. Lebenslauf eines Pakets (jeder Übergang wird gesprochen)

```
vorgeschlagen → AKTIV → (Meilenstein …) → ERLEDIGT        → nächstes Paket
                      ↘ Budget läuft ab → RAUS/ZURÜCK    → nächstes Paket
                      ↘ ungültig        → ABGEBROCHEN    → nächstes Paket
                      ↘ besseres Play   → ERSETZT        → neues Paket
```

- **Start:** Ziel, Budget oder Frist und der entscheidende Grund. Beispiel: „Drück den Turm: 12 Sekunden sicher, eine
  Platte drin.“
- **Meilenstein:** „Platte. Noch 6 Sekunden, eine geht noch.“
- **Countdown**, nur bei Zeitbudget, höchstens zweimal: „Noch 5 Sekunden.“
- **Budget abgelaufen:** „Raus jetzt: Udyr in 6 Sekunden bei dir. Back, dann Axiombogen.“
- **Abgebrochen:** „Herold weg: nicht hin. Stattdessen Mid-Welle.“
- **Ersetzt:** „Planwechsel: Ekko kämpft mit Udyr oben, du bist in 4 Sekunden da: hilf. Danach Top-Welle.“
- **Erledigt:** „Turm fällt. Jetzt Back: 1400 Gold für Axiombogen, pünktlich zur Welle um 9:30.“

Stille gibt es nur, wenn ein Paket normal läuft und nichts passiert. Jeder Satz ist ein Übergang, **kein Satz ohne
Substanz**.

## 2. Die vier Uhren (Kern, deterministisch, jeder Takt)

Pakete leben von Zahlen, die der Kern exakt und schnell rechnet. Claude rechnet sie nicht, er bekommt sie.

### 2.1 Gefahr-Uhr: „Wie lange bin ich hier sicher?“

- **Frühester Angriff `T_gefahr`:** das Minimum über alle Gegner.
  - **Sichtbar:** Weg zu dir ÷ Tempo.
  - **Unsichtbar:** Letzte Sichtung plus die Zeit seither ergibt den Bereich, den er erreicht haben kann (Wege auf der
    Karte, nicht Luftlinie). Daraus die früheste Ankunft; das kann 0 sein.
  - **Tot:** `respawnTimer` aus der API plus der Weg vom Brunnen.
  - **Im Back:** Kanal-Ende plus der Weg vom Brunnen.
- **Flucht `T_flucht`:** Zeit bis zur Sicherheit, also dem nächsten stehenden eigenen Turm oder einer
  Mitspieler-Gruppe. Flash zählt als Bonus, wenn er bereit ist.
- **Sicheres Fenster** = `T_gefahr − T_flucht − Marge` (Marge 2 s, in `wissen/`).
- **Ausgabe:** „sicher noch N s“ und dazu, **wer** die Gefahr ist.

### 2.2 Wellen-Uhr: „Wann muss ich wo sein?“

- **Spawn-Plan** (Minion-Wiki, Stand prüfen):
  - ab 0:30 alle 30 s, ab 14:00 alle 25 s, ab 30:00 alle 20 s;
  - Kanone: erste in Welle 3 (1:30), vor 14:00 jede dritte Welle, 14:00–25:00 jede zweite, ab 25:00 jede;
  - Vasallen-Tempo 350–450 je nach Minute.
- **Beobachteter Stand** (`welle.py`): Wo trifft die nächste Welle auf deinen Turm? Wie viele Vasallen verlierst du,
  wenn du fehlst?
- **Back-Frist:**
  - `T_back_spätestens` = Ankunft der nächsten wichtigen Welle am eigenen Turm − (Recall-Kanal + Einkauf + Weg vom
    Brunnen zur Lane).
  - Die Wege werden aus Karte und eigenem Tempo gerechnet. Den Recall-Kanal aus `wissen/` nehmen, nicht aus dem
    Gedächtnis.
  - Quest-TP und TP verkürzen den Rückweg.
- **Ausgabe:** „Back spätestens um mm:ss, sonst verlierst du die Kanonenwelle.“

### 2.3 Objective-Uhr

- Spawn und Leben (API und Minimap-Symbol).
- Ankunftszeit eures Teams und der Gegner.
- Prio: Sind ihre Lanes gepusht, tot oder im Back?

### 2.4 Ressourcen-Uhr

- Leben und Mana samt Trend.
- Gold bis zum nächsten Spike.
- Flash, TP und Ult bei dir und bei den Gegnern (wenn bekannt), Quest-TP.
- Tod und Respawn **nur aus der API** (`isDead`, `respawnTimer`).

## 3. Katalog der Pakete

Jedes Paket hat: **Ziel · Wert (GE) · Budget oder Frist · Erledigt · Abbruch (eigene Gründe) · Chancen, die es
ersetzen dürfen · Sätze**.

| Paket | Budget / Frist | Erledigt | Abbruch (zusätzlich zu Teil 4) | Beispiel-Start |
|---|---|---|---|---|
| **TURM / PLATTEN** | min(sicheres Fenster, Back-Frist, Rückkehr des Lane-Gegners) | Platte oder Turm fällt | Welle weg (Turm schießt dich), Gegner-Laner zurück | „Drück den Turm: 12 s sicher, eine Platte drin.“ |
| **WELLE** (Freeze / Slow Push / Crash) | bis zum Wellenziel | Welle am Ziel | Jungler-Gefahr bei vorgeschobener Welle | „Crash die Kanonenwelle, dann Back: Udyr ist 30 s tot.“ |
| **BACK** (mit Kette) | Back-Frist | angekommen und eingekauft | Kanal gestört, Gegner in Sicht, besserer Moment in ≤ 5 s | „Back jetzt: Axiombogen, dann Top, pünktlich um 9:30.“ |
| **HILFE** (Mitspieler kämpft) | Ankunft ≤ 8 s, bevor der Kampf entschieden ist | Kampf vorbei | Rechner „klar hinten“, Kampf schon verloren oder gewonnen | „Ekko kämpft mit Udyr oben, du bist in 4 s da: hilf.“ |
| **ROTATION** (zu Lane, Gruppe, Seite) | Ankunft vor dem Zweck | angekommen | Zweck weg (Welle geholt, Gruppe tot) | „Geh Mid: Welle 5 gegen 1, Lissandra ist tot.“ |
| **OBJECTIVE** (vorbereiten, nehmen, bestreiten, abgeben) | Spawn oder Fenster | genommen oder abgegeben | Objective weg, eigene Leute tot, Gegner-Überzahl, keine Prio | „Drache in 60 s: Welle crashen, back, dann Pit mit Ekko.“ |
| **VERTEIDIGEN** (Turm, Welle abfangen) | bis die Gefahr weg ist | Turm steht, Welle geholt | aussichtslos (Rechner „klar hinten“ und Tod droht) | „Fang die Welle am inneren Turm, Udyr allein: halten.“ |
| **WARTEN / HALTEN** | nur mit Ende („bis Udyr gesehen“, „bis die Welle da ist“) | Ende erreicht | besseres Play | „Unter dem Turm halten, bis Gragas auftaucht, dann Platte.“ |
| **KAUF / RESPAWN** | im Laden | gekauft, unterwegs | – | „Du lebst in 12 s: Axiombogen, dann per TP Top.“ |

## 4. Abbruch-Gründe für alle Pakete (Kern prüft jeden Takt)

1. **Gefahr:** sicheres Fenster < 0.
2. **Leben:** unter R1, oder der Verlust in den letzten 3 s reicht für einen Tod in den nächsten 3 s.
3. **Ziel weg:** Objective genommen, Turm gefallen, Ziel tot oder geflohen.
4. **Partner weg:** Mitspieler, mit dem das Paket geplant ist, tot, zurück oder in einem anderen Kampf.
5. **Überzahl am Ziel** (sichtbar oder aus der Gefahr-Uhr).
6. **Frist verpasst:** Der Weg reicht nicht mehr.
7. **Eigener Tod oder Kampf:** Dann übernehmen Kampf- und Tod-Regeln.
8. **Überholt:** Ein anderes Paket ist nun deutlich mehr wert (Teil 5).

Weitere Gründe darf jeder Pakettyp ergänzen. Die Liste ist offen und wird aus jeder Aufnahme mit „hätte abbrechen
müssen“ erweitert.

## 5. Chancen-Scanner: besseres Play erkennen (Umsetzung der Event-Abwägung, Teil 0.3)

**Ereignisse** erzeugen Kandidaten-Pakete mit Wert:
- ein Mitspieler kämpft in der Nähe (Carlos' Beispiel: Jungler gegen Jungler);
- ein Gegner stirbt, backt oder roamt;
- ein Flash ist weg (mit Kill-Check);
- ein Objective öffnet sich mit Prio;
- ihr Jungler wird weit weg gesehen (freie Seite);
- ein Turm steht niedrig;
- eine Welle kippt.

**Wechsel**, wenn der Wert des Kandidaten − Wert des aktiven Pakets > Schwelle (Hysterese, Start 150 GE, in `wissen/`)
**und** Ankunft und Sicherheit passen.

**Satz:** „Planwechsel: …, weil …. Danach …“, damit das alte Ziel nicht verloren geht.

**Wert in Gold-Äquivalent (GE)** mit dem bestehenden Wertsystem (`kern/wert.py`, Buch 6): Gold, XP, Objective-Werte,
Platten und Vasallen minus Risiko (`p_tod` × Todeskosten) minus Zeit.

## 6. Wer macht was

- **Kern, sofort und exakt:**
  - die vier Uhren, Budgets und Fristen;
  - Abbruch- und Erledigt-Prüfung;
  - Kandidaten mit Wert.
  - Er spricht Countdown, Abbruch und Erledigt **selbst**, weil das in Sekundenbruchteilen kommen muss (≤ 8 Wörter).
- **Claude (Stratege):**
  - wählt zwischen knappen Kandidaten;
  - formuliert Start und Planwechsel mit Grund (≤ 25 Wörter);
  - beantwortet Fragen mit Bezug auf das aktive Paket.
  - Er bekommt die Uhren als Zahlen.
  - Fällt er aus, gilt die Kern-Vorlage.
- **`pruefe`** bleibt der Wächter: R1, Kill-Check, Fakten, tot oder lebendig, innere Begriffe.

## 7. Messen an Aufnahmen (ohne Testpartie)

| Maß | Wie | Soll |
|---|---|---|
| Paket-Abdeckung | Anteil der Zeit, in der du lebst und nicht im Kampf bist, mit aktivem Paket | ≥ 90 % |
| Abbruch-Reaktion | Ungültig-Ereignisse in der Aufnahme (Wahrheit aus API und Bild), gesprochen in ≤ 2 s | ≥ 95 % |
| Budget-Treue (Sicherheit) | Jedes „N s sicher“: Kam in N s ein Gegner in Reichweite? | Fehler ≤ 5 %, gefährliche 0 |
| Chancen genutzt | Gelegenheiten in der Aufnahme (z. B. Mitspieler-Kampf ≤ 8 s entfernt, nicht „klar hinten“): vom Coach vorgeschlagen? | ≥ 70 % |
| Back-Pünktlichkeit | Nach einem Back-Ruf des Coachs: Vasallen am eigenen Turm verloren? | 0 in ≥ 80 % |
| Event-Abdeckung | Wichtige Events der Aufnahme (Wahrheit aus API und Bild): Hat der Coach sie aufgegriffen (Handlung oder „warum nicht“)? | ≥ 85 % |
| Erahnung | Erahnte Events mit p ≥ 0,6: Wie viele traten ein? | ≥ 60 % |
| Abwägung | Ein blinder Challenger-Kritiker sieht die Kandidaten der Minute. War das gewählte Play das beste oder gleichwertig? | ≥ 75 % |
| Soll-Liste (023, stabil) | wie bisher | Tor aus 021 |

## 8. Wissen (mit Stand, nie aus dem Gedächtnis)

Diese Werte kommen nach `wissen/` mit Quelle und Stand, geprüft an Aufnahmen:
- Wellenzeiten und Kanonen (Minion-Wiki);
- Recall-Kanal;
- Wege Brunnen → Lanes und Lane → Objectives (aus Aufnahmen gemessen);
- Plattenregeln und Plattengold;
- Quest-TP;
- Respawn aus der API statt aus einer Formel.

## Quellen

- League of Legends Wiki, Minion (Wellenzeiten, Kanonen, Tempo): https://wiki.leagueoflegends.com/en-us/Minion
- Dignitas, Lane Priority Guide: https://dignitas.gg/articles/the-pro-unspoken-rule-of-league-a-lane-priority-guide
- LoL Theory, Wave Management: https://blog.loltheory.gg/wave-management-league-of-legends/
- Carlos' Notizen aus 231200 (18:37, 29:39) und seine Nachrichten vom 30.09.2026 00:00 und 00:06 (Events)
